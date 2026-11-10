// IfcClash_Plus engine — the per-element data of the _triang rules, derived
// from the triangles once and kept for the whole Session
// (engine/triang/derived). Every rule of a RuleFile shares them: the second
// rule asking for the OBB or the seen triangles of an element pays nothing.
//
// The tags of GeometryProvider::derived are prefixed "tri_"; the triangle
// source is fixed for the Session, so it is not part of the tags.
#pragma once

#include "../../rules/RuleBase.h"
#include "../mesh/TriMesh.h"

#include <Bnd_OBB.hxx>

#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace ifcclash::triang {

// Typed access to GeometryProvider::derived.
template <class T>
std::shared_ptr<const T> derived(const ElementGeometry& e, const std::string& tag,
                                 const std::function<std::shared_ptr<const T>()>& compute) {
    auto data = e.provider().derived(e.key, tag, [&]() -> std::shared_ptr<const void> { return compute(); });
    return std::static_pointer_cast<const T>(data);
}

// The world triangles of the element (Variant::Triangles: .ifcview or IFC,
// per SessionOptions::triangle_source). nullptr: no triangle.
std::shared_ptr<const Mesh> triangles(const ElementGeometry& e);

// The welded, consistently wound mesh (TriMesh). nullptr: no triangle.
std::shared_ptr<const TriMesh> tri_mesh(const ElementGeometry& e);

// The optimal OBB of the vertices (Bnd_OBB::ReBuild, optimal mode: the
// method of the original rules on their 0.01 m mesh).
std::optional<Bnd_OBB> tri_obb(const ElementGeometry& e);

// How the seen triangles are found (engine/triang/surface).
enum class SeenMethod {
    Sampled,  // visible_triangles: 4 sampled points per triangle
    Auto,     // visible_triangles_auto: sampled under 200 triangles, height map above
};
// The triangles of tri_mesh() seen from above (side +1) or below (side -1),
// ascending indices in tri_mesh(). nullptr: no triangle.
std::shared_ptr<const std::vector<int>> seen_triangles(const ElementGeometry& e, double side,
                                                       SeenMethod method = SeenMethod::Auto);

}  // namespace ifcclash::triang
