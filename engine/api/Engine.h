// IfcClash_Plus engine — the public API (the only public header: the Python
// script through the bindings, BonsaiViewer directly).
//
// A Session lives for one RuleFile: parsed files, GeometryProvider and cache.
// Python opens it once, then runs the rules one by one.
#pragma once

#include "../core/Control.h"
#include "../core/ElementKey.h"
#include "../core/Errors.h"
#include "../core/Result.h"
#include "../provider/CachePolicy.h"

#include <filesystem>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace ifcclash {

class GeometryProvider;
class GeometrySource;
class IfcSource;

inline constexpr const char* kEngineVersion = "0.1.0";

struct SessionOptions {
    CachePolicy geometry_cache = CachePolicy::Auto;
    std::optional<std::filesystem::path> cache_dir;  // default: next to the IFC
    // Explicit .ifcview per IFC (same order as the IFC paths, empty = look
    // for it). Overrides cache_dir.
    std::vector<std::filesystem::path> ifcview_paths;
    // "mtime" (default) | "trust" | "reject" (see sources/ifcview).
    std::string ifcview_freshness = "mtime";
    // Linear deflection assumed for a .ifcview without manifest (uncertainty).
    double ifcview_linear_deflection = 0.01;   // m
    bool write_cache = false;
    int iterator_threads = 0;  // 0 = hardware concurrency
};

// The elements of one file picked by a slot (from the IDS selection in
// Python). GlobalIds are the exchange key; entity ids, when given, are exact
// (the Python backend sends both lists' union).
struct FileSelection {
    uint32_t file_index = 0;
    std::vector<std::string> global_ids;
    std::vector<int> entity_ids;
};

struct Selections {
    std::vector<FileSelection> source, target, context;
};

struct RunRequest {
    std::string rule_type;
    Json params = Json::object();  // engine keys only (catalogue)
    Selections selections;
    RunMode mode = RunMode::Verdicts;
    bool prefilter = true;  // debug: false disables the broad and mid phases
};

class Session {
public:
    Session(std::vector<std::filesystem::path> ifc_paths, SessionOptions options = {});
    // BonsaiViewer: a source built on the data already loaded by the viewer.
    Session(std::unique_ptr<GeometrySource> source, SessionOptions options = {});
    ~Session();
    Session(const Session&) = delete;
    Session& operator=(const Session&) = delete;

    RunResult run(const RunRequest& request, const CancelToken& cancel, ProgressSink& progress);
    RunResult run(const RunRequest& request);

    // Exceptions: one rule evaluated on a batch of pairs, in one call (a
    // pair is given by file_index + entity_id or file_index + global_id).
    RunResult evaluate_pairs(const RunRequest& request, const std::vector<KeyPair>& pairs);

    size_t file_count() const;
    // Session-level diagnostics (cache policy...), repeated in every run.
    const Diagnostics& diagnostics() const { return session_diagnostics_; }

private:
    std::vector<ElementKey> resolve(const std::vector<FileSelection>& selection, Diagnostics& diagnostics);
    std::optional<ElementKey> resolve_key(const ElementKey& partial, Diagnostics& diagnostics);
    void fill_display(const RunRequest& request, const std::vector<ElementKey>& inputs, RunResult& result);

    SessionOptions options_;
    IfcSource* ifc_ = nullptr;  // owned by the provider when the session reads IFC files
    std::unique_ptr<GeometryProvider> provider_;
    Diagnostics session_diagnostics_;
};

// The catalogue of the rules implemented in C++ (type, family, slots,
// params, defaults, bounds, units, doc), as JSON text.
std::string catalogue_json();

}  // namespace ifcclash
