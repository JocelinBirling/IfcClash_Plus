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

std::shared_ptr<const void> GeometryProvider::derived(const ElementKey& key, const std::string& tag,
                                                      const std::function<std::shared_ptr<const void>()>& compute) {
    {
        std::lock_guard<std::mutex> lock(derived_mutex_);
        auto& entries = derived_[tag];
        auto it = entries.find(key);
        if (it != entries.end()) return it->second;
    }
    auto value = compute();
    std::lock_guard<std::mutex> lock(derived_mutex_);
    return derived_[tag].emplace(key, std::move(value)).first->second;
}

}  // namespace ifcclash
