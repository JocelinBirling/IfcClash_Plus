#include "ElementData.h"

#include "../mesh/Obb.h"
#include "../surface/Visibility.h"

namespace ifcclash::triang {

std::shared_ptr<const Mesh> triangles(const ElementGeometry& e) {
    auto m = e.mesh(Variant::Triangles);
    return m && !m->faces.empty() ? m : nullptr;
}

std::shared_ptr<const TriMesh> tri_mesh(const ElementGeometry& e) {
    return derived<TriMesh>(e, "tri_mesh", [&e]() -> std::shared_ptr<const TriMesh> {
        const auto m = triangles(e);
        if (!m) return nullptr;
        auto t = std::make_shared<const TriMesh>(*m);
        return t->triangle_count() ? t : nullptr;
    });
}

std::optional<Bnd_OBB> tri_obb(const ElementGeometry& e) {
    auto obb = derived<Bnd_OBB>(e, "tri_obb", [&e]() -> std::shared_ptr<const Bnd_OBB> {
        const auto m = triangles(e);
        if (!m || m->world_verts.empty()) return nullptr;
        return std::make_shared<const Bnd_OBB>(optimal_obb(m->world_verts));
    });
    if (!obb) return std::nullopt;
    return *obb;
}

std::shared_ptr<const std::vector<int>> seen_triangles(const ElementGeometry& e, double side, SeenMethod method) {
    const std::string tag = std::string("tri_seen_") + (side > 0 ? "up" : "down") +
                            (method == SeenMethod::Sampled ? "_sampled" : "_auto");
    return derived<std::vector<int>>(e, tag, [&]() -> std::shared_ptr<const std::vector<int>> {
        const auto mesh = tri_mesh(e);
        if (!mesh) return nullptr;
        return std::make_shared<const std::vector<int>>(
            method == SeenMethod::Sampled ? visible_triangles(mesh->verts(), mesh->faces(), side)
                                          : visible_triangles_auto(mesh->verts(), mesh->faces(), side));
    });
}

}  // namespace ifcclash::triang
