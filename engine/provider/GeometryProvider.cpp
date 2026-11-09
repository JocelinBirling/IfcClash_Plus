#include "GeometryProvider.h"

namespace ifcclash {

GeometryProvider::GeometryProvider(std::unique_ptr<GeometrySource> primary,
                                   std::unique_ptr<GeometrySource> cache)
    : primary_(std::move(primary)), cache_(std::move(cache)) {}

void GeometryProvider::prepare(const std::vector<ElementKey>& keys) {
    // The boxes come from the cache when it covers the element; the primary
    // source converts the rest in one batch.
    if (!cache_) {
        primary_->prepare(keys);
        return;
    }
    std::vector<ElementKey> missing;
    for (const auto& key : keys) {
        if (!cache_->covers(key)) missing.push_back(key);
    }
    cache_->prepare(keys);
    primary_->prepare(missing);
}

std::optional<ElementBoxes> GeometryProvider::boxes(const ElementKey& key) {
    ++box_requests_;
    if (cache_ && cache_->covers(key)) {
        if (auto b = cache_->boxes(key)) {
            ++cache_hits_;
            return b;
        }
    }
    return primary_->boxes(key);  // per-element fallback on the IFC
}

std::shared_ptr<const Mesh> GeometryProvider::mesh(const ElementKey& key) {
    return primary_->mesh(key);  // narrow phase: the reference source, always
}

std::optional<TopoDS_Shape> GeometryProvider::brep(const ElementKey& key) {
    return primary_->brep(key);
}

TriangleClashService* GeometryProvider::triangle_clash() {
    return primary_->triangle_clash();
}

}  // namespace ifcclash
