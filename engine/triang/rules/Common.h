// IfcClash_Plus engine — what the _triang rules share (engine/triang/rules).
//
// A _triang rule reads Variant::Triangles only: the .ifcview triangles or the
// IFC triangulation, per SessionOptions::triangle_source. It never asks for a
// B-Rep nor for another mesh variant, so with triangle_source "ifcview" no IFC
// geometry is converted at all.
#pragma once

#include "../../core/Result.h"
#include "../../geometry/Obb.h"
#include "../../rules/RuleBase.h"
#include "../derived/ElementData.h"

#include <Bnd_OBB.hxx>

namespace ifcclash::triang {

// The .ifcview boxes contain the decoded vertices (same placement, the local
// AABB bounds the quantized positions); the boxes computed on the triangles
// contain them exactly: only the double rounding to absorb.
inline constexpr double kFloatMargin = 1e-6;

inline Point3 point(const P3& p) { return {p[0], p[1], p[2]}; }

// The centre of the axis-aligned box of the triangles (the original rules:
// geometry::shape_center, the box of the meshed B-Rep).
inline std::optional<Point3> box_center(const ElementGeometry& e) {
    const auto mesh = tri_mesh(e);
    if (!mesh) return std::nullopt;
    double x0, y0, z0, x1, y1, z1;
    mesh->bounds().Get(x0, y0, z0, x1, y1, z1);
    return Point3{(x0 + x1) / 2.0, (y0 + y1) / 2.0, (z0 + z1) / 2.0};
}

// One-object rule on the triangles.
template <class Params>
class TriElementRule : public ElementRule<Params> {
public:
    Level narrow_level() const override { return Level::Mesh; }
    Variant base_variant() const override { return Variant::Triangles; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    bool parallel_safe() const override { return true; }  // triangles and their derived data only
};

// Two-object rule on the triangles, with per-element data, a narrow phase
// spread over the threads, and no self skip (the original directional rules
// test an element against itself).
template <class Params>
class TriPairRule : public PairRule<Params> {
public:
    Level narrow_level() const override { return Level::Mesh; }
    Variant base_variant() const override { return Variant::Triangles; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    bool needs_element_data() const override { return true; }
    bool parallel_safe() const override { return true; }    // element_data: triangles only
    bool parallel_narrow() const override { return true; }  // narrow_test: element data only
};

}  // namespace ifcclash::triang
