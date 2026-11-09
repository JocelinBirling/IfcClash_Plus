#include "GeometryProvider.h"

#include "../sources/IfcClashTree.h"

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

// ---------------------------------------------------------------- Variant::ViewMesh

void GeometryProvider::prepare_meshes(const std::vector<ElementKey>& keys, Variant variant) {
    if (variant != Variant::ViewMesh) {
        primary_->prepare(keys, variant);
        return;
    }
    if (!cache_) return;
    std::vector<ElementKey> missing;
    {
        std::lock_guard<std::mutex> lock(view_mutex_);
        for (const auto& key : keys) {
            if (!view_meshes_.count(key) && cache_->covers(key)) missing.push_back(key);
        }
    }
    if (missing.empty()) return;
    auto meshes = cache_->stored_meshes(missing, threads_);
    std::lock_guard<std::mutex> lock(view_mutex_);
    for (size_t i = 0; i < missing.size(); ++i) view_meshes_.emplace(missing[i], std::move(meshes[i]));
}

std::shared_ptr<const Mesh> GeometryProvider::mesh(const ElementKey& key, Variant variant) {
    if (variant != Variant::ViewMesh) return primary_->mesh(key, variant);
    {
        std::lock_guard<std::mutex> lock(view_mutex_);
        auto it = view_meshes_.find(key);
        if (it != view_meshes_.end()) return it->second;
    }
    prepare_meshes({key}, Variant::ViewMesh);  // not prepared in batch: alone
    std::lock_guard<std::mutex> lock(view_mutex_);
    auto it = view_meshes_.find(key);
    return it != view_meshes_.end() ? it->second : nullptr;
}

TriangleClashService* GeometryProvider::view_clash() {
    std::lock_guard<std::mutex> lock(view_mutex_);
    if (!view_clash_) view_clash_ = std::make_unique<IfcClashTree>();
    return view_clash_.get();
}

std::shared_ptr<const Mesh> GeometryProvider::view_clash_mesh(const ElementKey& key) {
    {
        std::lock_guard<std::mutex> lock(view_mutex_);
        auto it = view_clash_meshes_.find(key);
        if (it != view_clash_meshes_.end()) return it->second;
    }
    std::shared_ptr<Mesh> out;
    if (auto world = mesh(key, Variant::ViewMesh)) {
        if (auto native = primary_->triangulation_native(key, *world)) {
            out = std::make_shared<Mesh>();
            out->native = std::move(native);
        }
    }
    std::lock_guard<std::mutex> lock(view_mutex_);
    return view_clash_meshes_.emplace(key, std::move(out)).first->second;
}

}  // namespace ifcclash
