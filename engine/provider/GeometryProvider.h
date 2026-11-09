// IfcClash_Plus engine — the GeometryProvider (SPEC "Sources de géométrie").
//
// Picks the source per level and per element:
//   broad / mid phases  boxes()          cache source when valid, else the primary
//   narrow phase        mesh() / brep()  the primary source, always
// so the result never depends on the source, only the time does.
#pragma once

#include "../core/Result.h"
#include "../sources/GeometrySource.h"

#include <memory>
#include <optional>
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
    void prepare_meshes(const std::vector<ElementKey>& keys) { primary_->prepare(keys); }

    bool has_cache() const { return cache_ != nullptr; }
    // How many boxes came from the cache since the last reset (statistics).
    size_t cache_hits() const { return cache_hits_; }
    size_t box_requests() const { return box_requests_; }

    std::optional<ElementBoxes> boxes(const ElementKey& key);
    std::shared_ptr<const Mesh> mesh(const ElementKey& key);
    std::optional<TopoDS_Shape> brep(const ElementKey& key);
    TriangleClashService* triangle_clash();

private:
    std::unique_ptr<GeometrySource> primary_;
    std::unique_ptr<GeometrySource> cache_;
    size_t cache_hits_ = 0;
    size_t box_requests_ = 0;
};

}  // namespace ifcclash
