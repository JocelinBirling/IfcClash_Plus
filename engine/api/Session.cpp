#include "Engine.h"

#include "../pipeline/Pipelines.h"
#include "../provider/GeometryProvider.h"
#include "../registry/Registry.h"
#include "../sources/IfcSource.h"
#include "../sources/ifcview/IfcViewSource.h"

#include <unordered_set>

namespace ifcclash {

namespace {

class NullProgress final : public ProgressSink {};

// The optional .ifcview source of the boxes (SPEC "Politique et
// validation"): Off -> none; Auto -> the files found and accepted, the
// others fall back on the IFC with a diagnostic; Require -> every file must
// have an accepted .ifcview, else ConfigError.
std::unique_ptr<GeometrySource> make_cache(const std::vector<std::filesystem::path>& ifc_paths,
                                           const SessionOptions& options, Diagnostics& diagnostics) {
    if (options.write_cache) {
        diagnostics.add(Severity::Warning, "write_cache_unavailable",
                        "write_cache is ignored: this build cannot write .ifcview files yet");
    }
    if (options.geometry_cache == CachePolicy::Off) return nullptr;
    if (!options.ifcview_paths.empty() && options.ifcview_paths.size() != ifc_paths.size()) {
        throw ConfigError("ifcview_paths must give one entry per IFC file (empty string = look for it)");
    }

    std::vector<IfcViewFile> files;
    for (uint32_t i = 0; i < ifc_paths.size(); ++i) {
        std::filesystem::path view;
        if (!options.ifcview_paths.empty() && !options.ifcview_paths[i].empty()) {
            view = options.ifcview_paths[i];
            if (!std::filesystem::exists(view)) {
                throw ConfigError(".ifcview not found: " + view.string());
            }
        } else {
            view = IfcViewSource::locate(ifc_paths[i], options.cache_dir);
        }
        if (view.empty()) {
            if (options.geometry_cache == CachePolicy::Require) {
                throw ConfigError("geometry_cache='require': no .ifcview for " + ifc_paths[i].string());
            }
            diagnostics.add(Severity::Info, "ifcview_missing",
                            ifc_paths[i].filename().string() + ": no .ifcview, boxes from the IFC");
            continue;
        }
        files.push_back({i, ifc_paths[i], view});
    }
    if (files.empty()) return nullptr;

    IfcViewOptions view_options;
    view_options.freshness = freshness_from_string(options.ifcview_freshness);
    view_options.linear_deflection = options.ifcview_linear_deflection;
    auto source = std::make_unique<IfcViewSource>(files, view_options, diagnostics);
    if (options.geometry_cache == CachePolicy::Require && source->accepted_files() != files.size()) {
        throw ConfigError("geometry_cache='require': a .ifcview was rejected (see the diagnostics)");
    }
    if (source->accepted_files() == 0) return nullptr;
    return source;
}

}  // namespace

Session::Session(std::vector<std::filesystem::path> ifc_paths, SessionOptions options) : options_(std::move(options)) {
    if (ifc_paths.empty()) throw ConfigError("a session needs at least one IFC file");
    auto cache = make_cache(ifc_paths, options_, session_diagnostics_);
    IfcSourceOptions source_options;
    source_options.iterator_threads = options_.iterator_threads;
    auto source = std::make_unique<IfcSource>(ifc_paths, source_options);
    ifc_ = source.get();
    provider_ = std::make_unique<GeometryProvider>(std::move(source), std::move(cache));
}

Session::Session(std::unique_ptr<GeometrySource> source, SessionOptions options) : options_(std::move(options)) {
    if (!source) throw ConfigError("a session needs a geometry source");
    ifc_ = dynamic_cast<IfcSource*>(source.get());
    provider_ = std::make_unique<GeometryProvider>(std::move(source));
}

Session::~Session() = default;

size_t Session::file_count() const { return ifc_ ? ifc_->file_count() : 0; }

std::vector<ElementKey> Session::resolve(const std::vector<FileSelection>& selection, Diagnostics& diagnostics) {
    if (!ifc_) throw ConfigError("selection resolution needs an IFC source");
    std::vector<ElementKey> keys;
    std::unordered_set<ElementKey, ElementKeyHash> seen;
    for (const auto& file : selection) {
        auto by_id = ifc_->resolve_entity_ids(file.file_index, file.entity_ids, diagnostics);
        auto by_gid = ifc_->resolve_global_ids(file.file_index, file.global_ids, diagnostics);
        for (auto* list : {&by_id, &by_gid}) {
            for (auto& key : *list) {
                if (seen.insert(key).second) keys.push_back(std::move(key));
            }
        }
    }
    return keys;
}

std::optional<ElementKey> Session::resolve_key(const ElementKey& partial, Diagnostics& diagnostics) {
    if (!ifc_) throw ConfigError("selection resolution needs an IFC source");
    return ifc_->resolve(partial, diagnostics);
}

void Session::fill_display(const RunRequest& request, const std::vector<ElementKey>& inputs, RunResult& result) {
    if (request.mode == RunMode::Verdicts) return;
    if (request.mode == RunMode::InputsOnly) {
        for (const auto& key : inputs) {
            auto mesh = provider_->mesh(key);
            if (!mesh) continue;
            result.display.items.push_back({"input", key, mesh->world_verts, mesh->faces});
        }
        return;
    }
    // VerdictsAndDisplay: the contact / closest point pairs as segments.
    for (const auto& record : result.results) {
        for (const auto& p : record.points) {
            DisplayItem item{"segment", record.source, {}, {0, 1}};
            item.vertices = {p.source[0], p.source[1], p.source[2], p.target[0], p.target[1], p.target[2]};
            result.display.items.push_back(std::move(item));
        }
    }
}

RunResult Session::run(const RunRequest& request) {
    CancelToken never;
    NullProgress quiet;
    return run(request, never, quiet);
}

RunResult Session::run(const RunRequest& request, const CancelToken& cancel, ProgressSink& progress) {
    const RuleSpec& spec = default_registry().find(request.rule_type);
    // Configuration first: an invalid parameter raises before any work.
    std::unique_ptr<RuleBase> rule = spec.create(request.params);

    RunResult result;
    result.stats.rule = request.rule_type;
    result.diagnostics = session_diagnostics_;

    const auto sources = resolve(request.selections.source, result.diagnostics);
    const auto targets = resolve(request.selections.target, result.diagnostics);
    if (!request.selections.context.empty()) {
        result.diagnostics.add(Severity::Warning, "context_ignored",
                               request.rule_type + " takes no context selection: ignored");
    }

    RunContext ctx{*provider_, cancel, progress, result.diagnostics, result.stats, request.prefilter};
    const size_t hits_before = provider_->cache_hits();
    const size_t requests_before = provider_->box_requests();

    if (request.mode == RunMode::InputsOnly) {
        std::vector<ElementKey> inputs = sources;
        inputs.insert(inputs.end(), targets.begin(), targets.end());
        provider_->prepare(inputs);
        fill_display(request, inputs, result);
        return result;
    }

    switch (rule->kind()) {
        case PipelineKind::Element:
            if (!targets.empty()) {
                result.diagnostics.add(Severity::Warning, "target_ignored",
                                       request.rule_type + " is a one-object rule: the target selection is ignored");
            }
            result.results = ElementPipeline::run(static_cast<const ElementRuleBase&>(*rule), sources, ctx);
            break;
        case PipelineKind::Pair:
            result.results = PairPipeline::run(static_cast<const PairRuleBase&>(*rule), sources, targets, ctx);
            break;
        case PipelineKind::Context:
        case PipelineKind::Set:
            throw ConfigError(request.rule_type + ": pipeline not implemented yet");
    }

    if (provider_->has_cache()) {
        result.diagnostics.add(Severity::Info, "ifcview_boxes",
                               std::to_string(provider_->cache_hits() - hits_before) + " of " +
                                   std::to_string(provider_->box_requests() - requests_before) +
                                   " boxes from the .ifcview");
    }
    fill_display(request, {}, result);
    return result;
}

RunResult Session::evaluate_pairs(const RunRequest& request, const std::vector<KeyPair>& pairs) {
    const RuleSpec& spec = default_registry().find(request.rule_type);
    std::unique_ptr<RuleBase> rule = spec.create(request.params);
    if (rule->kind() != PipelineKind::Pair) {
        throw ConfigError("evaluate_pairs needs a two-object rule, " + request.rule_type + " is not one");
    }

    RunResult result;
    result.stats.rule = request.rule_type;
    result.diagnostics = session_diagnostics_;

    std::vector<KeyPair> resolved;
    resolved.reserve(pairs.size());
    for (const auto& [s, t] : pairs) {
        auto ks = resolve_key(s, result.diagnostics);
        auto kt = resolve_key(t, result.diagnostics);
        if (ks && kt) resolved.emplace_back(std::move(*ks), std::move(*kt));
    }

    CancelToken never;
    NullProgress quiet;
    RunContext ctx{*provider_, never, quiet, result.diagnostics, result.stats, request.prefilter};
    result.results = PairPipeline::evaluate(static_cast<const PairRuleBase&>(*rule), resolved, ctx);
    fill_display(request, {}, result);
    return result;
}

std::string catalogue_json() {
    Json catalogue = default_registry().catalogue_json();
    catalogue["engine_version"] = kEngineVersion;
    catalogue["result_schema_version"] = kResultSchemaVersion;
    return catalogue.dump();
}

}  // namespace ifcclash
