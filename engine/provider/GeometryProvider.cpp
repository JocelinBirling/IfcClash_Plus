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

// ---------------------------------------------------------------- Variant::Triangles

void GeometryProvider::prepare_meshes(const std::vector<ElementKey>& keys, Variant variant) {
    if (variant != Variant::Triangles) {
        primary_->prepare(keys, variant);
        return;
    }
    std::vector<ElementKey> from_view, from_ifc;
    {
        std::lock_guard<std::mutex> lock(view_mutex_);
        for (const auto& key : keys) {
            if (view_meshes_.count(key)) continue;
            if (triangles_from_view(key)) from_view.push_back(key);
            else if (triangle_source_ != TriangleSource::IfcView) from_ifc.push_back(key);
        }
    }
    std::vector<std::shared_ptr<const Mesh>> view;
    if (!from_view.empty()) view = cache_->stored_meshes(from_view, threads_);
    std::vector<std::shared_ptr<const Mesh>> ifc;
    if (!from_ifc.empty()) {
        primary_->prepare(from_ifc, Variant::MeshWorld);  // one conversion batch
        for (const auto& key : from_ifc) {
            auto m = primary_->mesh(key, Variant::MeshWorld);
            ifc.push_back(m && !m->faces.empty() ? std::move(m) : nullptr);
        }
    }
    std::lock_guard<std::mutex> lock(view_mutex_);
    for (size_t i = 0; i < from_view.size(); ++i) view_meshes_.emplace(from_view[i], std::move(view[i]));
    for (size_t i = 0; i < from_ifc.size(); ++i) view_meshes_.emplace(from_ifc[i], std::move(ifc[i]));
}

std::shared_ptr<const Mesh> GeometryProvider::mesh(const ElementKey& key, Variant variant) {
    if (variant != Variant::Triangles) return primary_->mesh(key, variant);
    {
        std::lock_guard<std::mutex> lock(view_mutex_);
        auto it = view_meshes_.find(key);
        if (it != view_meshes_.end()) return it->second;
    }
    prepare_meshes({key}, Variant::Triangles);  // not prepared in batch: alone
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
    if (auto world = mesh(key, Variant::Triangles)) {
        if (auto native = primary_->triangulation_native(key, *world)) {
            out = std::make_shared<Mesh>();
            out->native = std::move(native);
        }
    }
    std::lock_guard<std::mutex> lock(view_mutex_);
    return view_clash_meshes_.emplace(key, std::move(out)).first->second;
}

}  // namespace ifcclash
