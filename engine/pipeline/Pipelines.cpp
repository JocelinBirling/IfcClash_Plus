#include "Pipelines.h"

#include "BroadPhase.h"
#include "../sources/IfcClashTree.h"

#include <algorithm>
#include <chrono>
#include <optional>
#include <set>
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

// ---------------------------------------------------------------- elements

std::vector<ResultRecord> ElementPipeline::run(const ElementRuleBase& rule, const std::vector<ElementKey>& elements,
                                               RunContext& ctx) {
    const auto t_start = Clock::now();
    ctx.provider.prepare(unique_keys(elements));

    std::vector<ElementBoxes> boxes;
    const std::vector<ElementKey> keys = with_geometry(elements, ctx, boxes);
    ctx.provider.prepare_meshes(keys);
    // The geometry conversion (IfcOpenShell iterator): usually the bulk of
    // a cold run, shown apart from the phases.
    ctx.stats.phases.push_back({"convert", unique_keys(elements).size(), keys.size(), seconds_since(t_start)});
    ctx.cancel.throw_if_cancelled();

    const auto t_narrow = Clock::now();
    std::vector<ResultRecord> results;
    for (size_t i = 0; i < keys.size(); ++i) {
        tick(ctx, "narrow", i, keys.size());
        ElementGeometry element(keys[i], boxes[i], ctx.provider);
        const Verdict verdict = rule.narrow_test(element);
        if (!verdict.status) continue;
        ResultRecord record = rule.report(verdict);
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
    ctx.provider.prepare_meshes(survivors);
    if (ctx.provider.has_cache()) {
        ctx.stats.phases.push_back({"convert_narrow", survivors.size(), survivors.size(), seconds_since(t0)});
    }
    const auto t_narrow = Clock::now();  // the narrow time excludes the conversion

    auto* clash = ctx.provider.triangle_clash();
    const size_t outside_before = clash ? clash->clashes_outside_candidates() : 0;

    // Batches: cancellation and progress between them.
    constexpr size_t kBatch = 4096;
    for (size_t first = 0; first < pairs.size(); first += kBatch) {
        ctx.cancel.throw_if_cancelled();
        ctx.progress.report("narrow", first, pairs.size());
        const size_t last = std::min(pairs.size(), first + kBatch);
        std::vector<PairRuleBase::GeometryPair> batch;
        batch.reserve(last - first);
        for (size_t n = first; n < last; ++n) {
            batch.emplace_back(&gs[static_cast<size_t>(pairs[n].first)], &gt[static_cast<size_t>(pairs[n].second)]);
        }
        const std::vector<Verdict> verdicts = rule.narrow_batch(batch);
        for (size_t k = 0; k < batch.size(); ++k) {
            if (!verdicts[k].status) continue;
            ResultRecord record = rule.report(verdicts[k]);
            record.source = batch[k].first->key;
            record.target = batch[k].second->key;
            results.push_back(std::move(record));
        }
    }
    ctx.stats.phases.push_back({"narrow", pairs.size(), results.size(), seconds_since(t_narrow)});

    if (clash && clash->clashes_outside_candidates() != outside_before) {
        ctx.diagnostics.add(Severity::Error, "prefilter_lost_clash",
                            std::to_string(clash->clashes_outside_candidates() - outside_before) +
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
    ctx.provider.prepare(unique_keys(all));

    PairInputs in;
    in.keys_s = with_geometry(sources, ctx, in.boxes_s);
    in.keys_t = with_geometry(targets, ctx, in.boxes_t);
    ctx.stats.phases.push_back({"convert", unique_keys(all).size(), in.keys_s.size() + in.keys_t.size(),
                                seconds_since(t_start)});
    const auto gs = geometries(in.keys_s, in.boxes_s, ctx.provider);
    const auto gt = geometries(in.keys_t, in.boxes_t, ctx.provider);
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
        if (ks == kt) continue;
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
    ctx.provider.prepare(unique_keys(all));

    std::vector<ElementKey> ks, kt;
    std::vector<ElementBoxes> bs, bt;
    for (const auto& [s, t] : pairs) {
        if (s == t) continue;
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
    const auto gs = geometries(ks, bs, ctx.provider);
    const auto gt = geometries(kt, bt, ctx.provider);

    std::vector<std::pair<int, int>> candidates;
    for (int n = 0; n < static_cast<int>(gs.size()); ++n) {
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
