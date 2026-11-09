// IfcClash_Plus engine — the GeometryProvider (SPEC "Sources de géométrie").
//
// Picks the source per level and per element:
//   broad / mid phases  boxes()          cache source when valid, else the primary
//   narrow phase        mesh() / brep()  the primary source, always
// so the result never depends on the source, only the time does.
#pragma once

#include "../core/Result.h"
#include "../sources/GeometrySource.h"

#include <functional>
#include <map>
#include <memory>
#include <mutex>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace ifcclash {

class GeometryProvider {
public:
    // `primary` is the reference source (IfcSource, or ViewerSource inside
    // BonsaiViewer). `cache` is the optional fast source of the boxes
    // (IfcViewSource, migration step 6).
    explicit GeometryProvider(std::unique_ptr<GeometrySource> primary,
                              std::unique_ptr<GeometrySource> cache = nullptr);

    GeometrySource& primary() { return *primary_; }

    // Before the broad phase: the boxes of these elements. Only the elements
    // the cache does not cover are converted by the primary source.
    void prepare(const std::vector<ElementKey>& keys);
    // Before the narrow phase: the meshes / B-Reps of the elements that
    // survived the prefilters, converted in one batch.
    void prepare_meshes(const std::vector<ElementKey>& keys, Variant variant = Variant::MeshLocal) {
        primary_->prepare(keys, variant);
    }

    bool has_cache() const { return cache_ != nullptr; }
    // How many boxes came from the cache since the last reset (statistics).
    size_t cache_hits() const { return cache_hits_; }
    size_t box_requests() const { return box_requests_; }

    std::optional<ElementBoxes> boxes(const ElementKey& key);
    std::shared_ptr<const Mesh> mesh(const ElementKey& key);
    std::shared_ptr<const Mesh> mesh(const ElementKey& key, Variant variant) { return primary_->mesh(key, variant); }
    std::optional<TopoDS_Shape> brep(const ElementKey& key);
    TriangleClashService* triangle_clash();

    // Per-element data derived from the geometry and kept for the whole
    // Session (the meshed B-Rep and its OBB, the visible faces...): computed
    // once, shared by the rules and by the runs. `tag` names the data and
    // every parameter it depends on. A nullptr result is kept too (no
    // geometry). Thread-safe: the computation runs outside the lock; two
    // threads asking for the same missing entry may both compute it, the
    // first stored wins (the computations are deterministic).
    std::shared_ptr<const void> derived(const ElementKey& key, const std::string& tag,
                                        const std::function<std::shared_ptr<const void>()>& compute);
    IfcQueries* ifc_queries() { return primary_->ifc_queries(); }
    RayTreeService* ray_trees() { return primary_->ray_trees(); }

private:
    std::unique_ptr<GeometrySource> primary_;
    std::unique_ptr<GeometrySource> cache_;
    size_t cache_hits_ = 0;
    size_t box_requests_ = 0;
    std::mutex derived_mutex_;
    std::map<std::string, std::unordered_map<ElementKey, std::shared_ptr<const void>, ElementKeyHash>> derived_;
};

}  // namespace ifcclash
