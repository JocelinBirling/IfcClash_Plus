#include "Pipelines.h"

#include "BroadPhase.h"
#include "../core/Errors.h"
#include "../sources/IfcClashTree.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <exception>
#include <mutex>
#include <optional>
#include <set>
#include <thread>
#include <unordered_set>

namespace ifcclash {

namespace {

using Clock = std::chrono::steady_clock;

double seconds_since(Clock::time_point t0) {
    return std::chrono::duration<double>(Clock::now() - t0).count();
}

void tick(RunContext& ctx, std::string_view phase, size_t done, size_t total) {
    if (done % kCheckEvery == 0) {
        ctx.cancel.throw_if_cancelled();
        ctx.progress.report(phase, done, total);
    }
}

// body(i) for every i in [0, n), on up to ctx.threads threads (the calling
// thread included) when `parallel`, else in order on the calling thread.
// Each body writes its result at its index: the output does not depend on
// the scheduling. The progress is reported and the cancellation checked
// by the calling thread (the progress sink may call back into Python); the
// other threads only stop on cancellation. The first exception of a body
// is rethrown once every thread has stopped.
template <class Body>
void for_each_element(size_t n, bool parallel, RunContext& ctx, std::string_view phase, Body&& body) {
    const size_t workers = parallel ? std::min<size_t>(std::max(1u, ctx.threads), n) : 1;
    if (workers <= 1) {
        for (size_t i = 0; i < n; ++i) {
            tick(ctx, phase, i, n);
            body(i);
        }
        return;
    }
    std::atomic<size_t> next{0}, done{0};
    std::atomic<bool> stop{false};
    std::exception_ptr error;
    std::mutex error_mutex;
    auto work = [&](bool caller) {
        size_t own = 0;
        while (!stop.load(std::memory_order_relaxed)) {
            const size_t i = next.fetch_add(1);
            if (i >= n) return;
            try {
                if (caller) {
                    if (own++ % 4 == 0) {
                        ctx.cancel.throw_if_cancelled();
                        ctx.progress.report(phase, done.load(), n);
                    }
                } else if (ctx.cancel.cancelled()) {
                    throw Cancelled();
                }
                body(i);
            } catch (...) {
                std::lock_guard<std::mutex> lock(error_mutex);
                if (!error) error = std::current_exception();
                stop.store(true);
                return;
            }
            done.fetch_add(1);
        }
    };
    std::vector<std::thread> pool;
    pool.reserve(workers - 1);
    for (size_t w = 1; w < workers; ++w) pool.emplace_back(work, false);
    work(true);
    for (auto& t : pool) t.join();
    if (error) std::rethrow_exception(error);
}

std::vector<ElementKey> unique_keys(const std::vector<ElementKey>& keys) {
    std::vector<ElementKey> out;
    std::unordered_set<ElementKey, ElementKeyHash> seen;
    for (const auto& k : keys) {
        if (seen.insert(k).second) out.push_back(k);
    }
    return out;
}

// Ordered key of a pair, for the Unordered symmetry.
std::pair<ElementKey, ElementKey> unordered(const ElementKey& a, const ElementKey& b) {
    return (b < a) ? std::make_pair(b, a) : std::make_pair(a, b);
}

}  // namespace

std::vector<ElementKey> with_geometry(const std::vector<ElementKey>& keys, RunContext& ctx,
                                      std::vector<ElementBoxes>& boxes_out) {
    std::vector<ElementKey> out;
    boxes_out.clear();
    for (const auto& key : unique_keys(keys)) {
        auto boxes = ctx.provider.boxes(key);
        if (!boxes || boxes->aabb.IsVoid()) {
            ctx.diagnostics.add(Severity::Info, "no_geometry",
                                "#" + std::to_string(key.entity_id) + " " + key.global_id +
                                    " has no computable geometry: skipped",
                                key);
            continue;
        }
        out.push_back(key);
        boxes_out.push_back(*boxes);
    }
    return out;
}

// The input elements of a rule. On MeshLocal (the default) the raw boxes
// decide which elements have geometry; on another base variant the elements
// are converted in that variant only (no useless triangulation) and keep
// void boxes: the rule derives its volumes from its element data.
// The inputs of a rule on the .ifcview triangles (engine/triang): only the
// elements the .ifcview holds, with its boxes; no IFC geometry is converted.
// A file without accepted .ifcview is a configuration error; an element
// missing from an accepted one is skipped with a diagnostic.
static std::vector<ElementKey> view_inputs(const std::vector<ElementKey>& keys, RunContext& ctx,
                                           std::vector<ElementBoxes>& boxes_out) {
    std::vector<ElementKey> out;
    boxes_out.clear();
    for (const auto& key : unique_keys(keys)) {
        if (!ctx.provider.cache_accepts_file(key.file_index)) {
            throw ConfigError("this rule reads the triangles of the .ifcview: none was accepted for file " +
                              std::to_string(key.file_index) +
                              " (missing, older than the IFC or unreadable: see the session diagnostics; "
                              "geometry_cache must not be 'off')");
        }
        if (!ctx.provider.cache_covers(key)) {
            ctx.diagnostics.add(Severity::Warning, "not_in_ifcview",
                                "#" + std::to_string(key.entity_id) + " " + key.global_id +
                                    " is not in the .ifcview: skipped",
                                key);
            continue;
        }
        auto boxes = ctx.provider.boxes(key);  // covered: the .ifcview boxes
        if (!boxes || boxes->aabb.IsVoid()) continue;
        out.push_back(key);
        boxes_out.push_back(*boxes);
    }
    return out;
}

static std::vector<ElementKey> rule_inputs(Variant base, const std::vector<ElementKey>& keys, RunContext& ctx,
                                           std::vector<ElementBoxes>& boxes_out) {
    if (base == Variant::MeshLocal) return with_geometry(keys, ctx, boxes_out);
    if (base == Variant::ViewMesh) return view_inputs(keys, ctx, boxes_out);
    std::vector<ElementKey> out = unique_keys(keys);
    ctx.provider.prepare_meshes(out, base);
    boxes_out.assign(out.size(), ElementBoxes{});
    return out;
}

// ---------------------------------------------------------------- elements

std::vector<ResultRecord> ElementPipeline::run(const ElementRuleBase& rule, const std::vector<ElementKey>& elements,
                                               RunContext& ctx) {
    const auto t_start = Clock::now();
    if (rule.base_variant() == Variant::MeshLocal) ctx.provider.prepare(unique_keys(elements));

    std::vector<ElementBoxes> boxes;
    const std::vector<ElementKey> keys = rule_inputs(rule.base_variant(), elements, ctx, boxes);
    for (Variant variant : rule.narrow_variants()) ctx.provider.prepare_meshes(keys, variant);
    // The geometry conversion (IfcOpenShell iterator): usually the bulk of
    // a cold run, shown apart from the phases.
    ctx.stats.phases.push_back({"convert", unique_keys(elements).size(), keys.size(), seconds_since(t_start)});
    ctx.cancel.throw_if_cancelled();

    const auto t_narrow = Clock::now();
    std::vector<std::vector<Verdict>> verdicts_of(keys.size());
    for_each_element(keys.size(), rule.parallel_safe(), ctx, "narrow", [&](size_t i) {
        ElementGeometry element(keys[i], boxes[i], ctx.provider);
        verdicts_of[i] =
            rule.multi_verdicts() ? rule.narrow_multi(element) : std::vector<Verdict>{rule.narrow_test(element)};
    });
    std::vector<ResultRecord> results;
    for (size_t i = 0; i < keys.size(); ++i) {
        for (const Verdict& verdict : verdicts_of[i]) {
            if (!verdict.status) continue;
            ResultRecord record = rule.report(verdict);
            record.source = keys[i];
            record.target.reset();
            results.push_back(std::move(record));
        }
    }
    ctx.stats.phases.push_back({"narrow", keys.size(), results.size(), seconds_since(t_narrow)});

    sort_results(results);
    ctx.stats.total_seconds = seconds_since(t_start);
    return results;
}

// ---------------------------------------------------------------- sets

std::vector<ResultRecord> SetPipeline::run(const SetRuleBase& rule, const std::vector<ElementKey>& elements,
                                           RunContext& ctx) {
    const auto t_start = Clock::now();
    if (rule.base_variant() == Variant::MeshLocal) ctx.provider.prepare(unique_keys(elements));
    std::vector<ElementBoxes> boxes;
    const std::vector<ElementKey> keys = rule_inputs(rule.base_variant(), elements, ctx, boxes);
    for (Variant variant : rule.narrow_variants()) ctx.provider.prepare_meshes(keys, variant);
    ctx.stats.phases.push_back({"convert", unique_keys(elements).size(), keys.size(), seconds_since(t_start)});
    ctx.cancel.throw_if_cancelled();

    const auto t_narrow = Clock::now();
    std::vector<ElementGeometry> geoms;
    geoms.reserve(keys.size());
    for (size_t i = 0; i < keys.size(); ++i) geoms.emplace_back(keys[i], boxes[i], ctx.provider);
    const std::vector<Verdict> verdicts = rule.narrow_set(geoms);
    std::vector<ResultRecord> results;
    for (size_t i = 0; i < verdicts.size() && i < keys.size(); ++i) {
        if (!verdicts[i].status) continue;
        ResultRecord record = rule.report(verdicts[i]);
        record.source = keys[i];
        record.target.reset();
        results.push_back(std::move(record));
    }
    ctx.stats.phases.push_back({"narrow", keys.size(), results.size(), seconds_since(t_narrow)});
    sort_results(results);
    ctx.stats.total_seconds = seconds_since(t_start);
    return results;
}

// ---------------------------------------------------------------- pairs

namespace {

struct PairInputs {
    std::vector<ElementKey> keys_s, keys_t;
    std::vector<ElementBoxes> boxes_s, boxes_t;
};

class MidCache {
public:
    MidCache(const PairRuleBase& rule, const std::vector<ElementGeometry>& geoms, Role role)
        : rule_(rule), geoms_(geoms), role_(role), volumes_(geoms.size()) {}
    const Bnd_OBB& operator[](size_t i) {
        if (!volumes_[i]) volumes_[i] = rule_.mid_volume(geoms_[i], role_);  // once per element
        return *volumes_[i];
    }

private:
    const PairRuleBase& rule_;
    const std::vector<ElementGeometry>& geoms_;
    Role role_;
    std::vector<std::optional<Bnd_OBB>> volumes_;
};

std::vector<ElementGeometry> geometries(const std::vector<ElementKey>& keys, const std::vector<ElementBoxes>& boxes,
                                        GeometryProvider& provider) {
    std::vector<ElementGeometry> out;
    out.reserve(keys.size());
    for (size_t i = 0; i < keys.size(); ++i) out.emplace_back(keys[i], boxes[i], provider);
    return out;
}

// The element data of the rule, derived once per element and role; the
// elements without data are dropped (the Python engines skip them).
std::vector<ElementGeometry> with_element_data(const PairRuleBase& rule, std::vector<ElementGeometry> geoms, Role role,
                                               RunContext& ctx) {
    if (!rule.needs_element_data()) return geoms;
    std::vector<ElementGeometry> out;
    out.reserve(geoms.size());
    for_each_element(geoms.size(), rule.parallel_safe(), ctx, "element_data",
                     [&](size_t i) { geoms[i].data = rule.element_data(geoms[i], role); });
    for (const auto& g : geoms) {
        if (g.data) out.push_back(g);
    }
    return out;
}

void narrow_pairs(const PairRuleBase& rule, const std::vector<std::pair<int, int>>& pairs,
                  const std::vector<ElementGeometry>& gs, const std::vector<ElementGeometry>& gt, RunContext& ctx,
                  std::vector<ResultRecord>& results) {
    const auto t0 = Clock::now();
    // The geometry of the survivors only, in one conversion batch (with a
    // .ifcview, the rejected elements are never converted).
    std::vector<ElementKey> needed;
    for (const auto& [i, j] : pairs) {
        needed.push_back(gs[static_cast<size_t>(i)].key);
        needed.push_back(gt[static_cast<size_t>(j)].key);
    }
    const auto survivors = unique_keys(needed);
    for (Variant variant : rule.narrow_variants()) ctx.provider.prepare_meshes(survivors, variant);
    if (ctx.provider.has_cache()) {
        ctx.stats.phases.push_back({"convert_narrow", survivors.size(), survivors.size(), seconds_since(t0)});
    }
    const auto t_narrow = Clock::now();  // the narrow time excludes the conversion

    auto* clash = ctx.provider.triangle_clash();
    auto outside = [&ctx, clash]() {
        size_t n = clash ? clash->clashes_outside_candidates() : 0;
        if (auto* view = ctx.provider.view_clash_if_any()) n += view->clashes_outside_candidates();
        return n;
    };
    const size_t outside_before = outside();

    // Batches: cancellation and progress between them.
    const size_t kBatch = rule.narrow_whole_run() ? std::max<size_t>(pairs.size(), 1) : 4096;
    for (size_t first = 0; first < pairs.size(); first += kBatch) {
        ctx.cancel.throw_if_cancelled();
        ctx.progress.report("narrow", first, pairs.size());
        const size_t last = std::min(pairs.size(), first + kBatch);
        std::vector<PairRuleBase::GeometryPair> batch;
        batch.reserve(last - first);
        for (size_t n = first; n < last; ++n) {
            batch.emplace_back(&gs[static_cast<size_t>(pairs[n].first)], &gt[static_cast<size_t>(pairs[n].second)]);
        }
        auto emit = [&](const Verdict& verdict, size_t k) {
            if (!verdict.status) return;
            ResultRecord record = rule.report(verdict);
            record.source = batch[k].first->key;
            record.target = batch[k].second->key;
            results.push_back(std::move(record));
        };
        if (rule.multi_verdicts()) {
            for (size_t k = 0; k < batch.size(); ++k) {
                for (const Verdict& verdict : rule.narrow_multi(*batch[k].first, *batch[k].second)) emit(verdict, k);
            }
        } else {
            const std::vector<Verdict> verdicts = rule.narrow_batch(batch);
            for (size_t k = 0; k < batch.size(); ++k) emit(verdicts[k], k);
        }
    }
    ctx.stats.phases.push_back({"narrow", pairs.size(), results.size(), seconds_since(t_narrow)});

    if (outside() != outside_before) {
        ctx.diagnostics.add(Severity::Error, "prefilter_lost_clash",
                            std::to_string(outside() - outside_before) +
                                " clash(es) found outside the candidate pairs: a prefilter is not conservative");
    }
}

}  // namespace

std::vector<ResultRecord> PairPipeline::run(const PairRuleBase& rule, const std::vector<ElementKey>& sources,
                                            const std::vector<ElementKey>& targets, RunContext& ctx) {
    const auto t_start = Clock::now();

    // One conversion pass for both lists.
    std::vector<ElementKey> all = sources;
    all.insert(all.end(), targets.begin(), targets.end());
    const Variant base = rule.base_variant();
    if (base == Variant::MeshLocal) ctx.provider.prepare(unique_keys(all));
    else ctx.provider.prepare_meshes(unique_keys(all), base);

    PairInputs in;
    in.keys_s = rule_inputs(base, sources, ctx, in.boxes_s);
    in.keys_t = rule_inputs(base, targets, ctx, in.boxes_t);
    for (Variant variant : rule.data_variants()) ctx.provider.prepare_meshes(unique_keys(all), variant);
    std::unordered_map<ElementKey, int, ElementKeyHash> ranks;
    for (const auto& key : unique_keys(all)) ranks.emplace(key, static_cast<int>(ranks.size()));
    auto ranked = [&](std::vector<ElementGeometry> geoms) {
        for (auto& g : geoms) g.rank = ranks[g.key];
        return geoms;
    };
    const auto gs = with_element_data(rule, ranked(geometries(in.keys_s, in.boxes_s, ctx.provider)), Role::Source, ctx);
    const auto gt = with_element_data(rule, ranked(geometries(in.keys_t, in.boxes_t, ctx.provider)), Role::Target, ctx);
    ctx.stats.phases.push_back({"convert", unique_keys(all).size(), gs.size() + gt.size(), seconds_since(t_start)});
    ctx.cancel.throw_if_cancelled();

    // ---- Broad phase
    const auto t_broad = Clock::now();
    const size_t all_pairs = gs.size() * gt.size();
    std::vector<std::pair<int, int>> raw;
    const bool spatial = ctx.prefilter && rule.broad_mode() == BroadMode::Spatial;
    if (spatial) {
        std::vector<Bnd_Box> vs, vt;
        vs.reserve(gs.size());
        vt.reserve(gt.size());
        for (const auto& g : gs) vs.push_back(rule.broad_volume(g, Role::Source));
        for (const auto& g : gt) vt.push_back(rule.broad_volume(g, Role::Target));
        raw = overlapping_pairs(vs, vt);
    } else {
        raw.reserve(all_pairs);
        for (int i = 0; i < static_cast<int>(gs.size()); ++i)
            for (int j = 0; j < static_cast<int>(gt.size()); ++j) raw.emplace_back(i, j);
    }

    // An element is never tested against itself; an Unordered rule tests a
    // pair met twice only once (first met in source order).
    std::vector<std::pair<int, int>> candidates;
    candidates.reserve(raw.size());
    std::set<std::pair<ElementKey, ElementKey>> seen;
    for (const auto& [i, j] : raw) {
        const auto& ks = gs[static_cast<size_t>(i)].key;
        const auto& kt = gt[static_cast<size_t>(j)].key;
        if (ks == kt && rule.skip_self()) continue;
        if (rule.symmetry() == PairSymmetry::Unordered && !seen.insert(unordered(ks, kt)).second) continue;
        candidates.emplace_back(i, j);
    }
    if (spatial) ctx.stats.phases.push_back({"broad", all_pairs, candidates.size(), seconds_since(t_broad)});
    ctx.cancel.throw_if_cancelled();

    // ---- Mid phase
    if (ctx.prefilter) {
        const auto t_mid = Clock::now();
        MidCache ms(rule, gs, Role::Source), mt(rule, gt, Role::Target);
        std::vector<std::pair<int, int>> kept;
        kept.reserve(candidates.size());
        for (size_t n = 0; n < candidates.size(); ++n) {
            tick(ctx, "mid", n, candidates.size());
            const auto [i, j] = candidates[n];
            if (rule.mid_test(ms[static_cast<size_t>(i)], mt[static_cast<size_t>(j)]) == Candidate::Kept)
                kept.emplace_back(i, j);
        }
        ctx.stats.phases.push_back({"mid", candidates.size(), kept.size(), seconds_since(t_mid)});
        candidates = std::move(kept);
    }
    ctx.cancel.throw_if_cancelled();

    // ---- Narrow phase
    std::vector<ResultRecord> results;
    narrow_pairs(rule, candidates, gs, gt, ctx, results);

    sort_results(results);
    ctx.stats.total_seconds = seconds_since(t_start);
    return results;
}

std::vector<ResultRecord> PairPipeline::evaluate(const PairRuleBase& rule, const std::vector<KeyPair>& pairs,
                                                 RunContext& ctx) {
    const auto t_start = Clock::now();
    std::vector<ElementKey> all;
    for (const auto& [s, t] : pairs) {
        all.push_back(s);
        all.push_back(t);
    }
    const Variant base = rule.base_variant();
    if (base == Variant::MeshLocal) ctx.provider.prepare(unique_keys(all));
    else ctx.provider.prepare_meshes(unique_keys(all), base);

    std::vector<ElementKey> ks, kt;
    std::vector<ElementBoxes> bs, bt;
    for (const auto& [s, t] : pairs) {
        if (s == t && rule.skip_self()) continue;
        if (base != Variant::MeshLocal) {
            ks.push_back(s);
            kt.push_back(t);
            bs.emplace_back();
            bt.emplace_back();
            continue;
        }
        auto b1 = ctx.provider.boxes(s);
        auto b2 = ctx.provider.boxes(t);
        if (!b1 || !b2 || b1->aabb.IsVoid() || b2->aabb.IsVoid()) {
            ctx.diagnostics.add(Severity::Info, "no_geometry", "pair skipped: an element has no geometry",
                                b1 ? t : s);
            continue;
        }
        ks.push_back(s);
        kt.push_back(t);
        bs.push_back(*b1);
        bt.push_back(*b2);
    }
    auto gs = geometries(ks, bs, ctx.provider);
    auto gt = geometries(kt, bt, ctx.provider);
    std::vector<bool> usable(gs.size(), true);
    if (rule.needs_element_data()) {
        for (size_t n = 0; n < gs.size(); ++n) {
            gs[n].data = rule.element_data(gs[n], Role::Source);
            gt[n].data = rule.element_data(gt[n], Role::Target);
            usable[n] = gs[n].data && gt[n].data;
        }
    }

    std::vector<std::pair<int, int>> candidates;
    for (int n = 0; n < static_cast<int>(gs.size()); ++n) {
        if (!usable[static_cast<size_t>(n)]) continue;
        if (ctx.prefilter) {
            if (rule.broad_mode() == BroadMode::Spatial &&
                rule.broad_volume(gs[n], Role::Source).IsOut(rule.broad_volume(gt[n], Role::Target)))
                continue;
            if (rule.mid_test(rule.mid_volume(gs[n], Role::Source), rule.mid_volume(gt[n], Role::Target)) ==
                Candidate::Rejected)
                continue;
        }
        candidates.emplace_back(n, n);
    }
    ctx.stats.phases.push_back({"prefilter", gs.size(), candidates.size(), seconds_since(t_start)});

    std::vector<ResultRecord> results;
    narrow_pairs(rule, candidates, gs, gt, ctx, results);
    sort_results(results);
    ctx.stats.total_seconds = seconds_since(t_start);
    return results;
}

}  // namespace ifcclash
