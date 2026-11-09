// IfcClash_Plus engine — pure geometry algorithms on meshes and boxes.
// No notion of IFC nor of rules (SPEC "Organisation du code").
#pragma once

#include "../core/Result.h"
#include "Geos.h"

#include <Bnd_Box.hxx>
#include <Bnd_OBB.hxx>

#include <array>
#include <vector>

namespace ifcclash::geometry {

// Volume enclosed by a triangulation, the exact counterpart of
// ifcopenshell.util.shape.get_volume: the same signed-tetrahedron formula,
// the same summation order, abs() of the sum. Volumes of non-manifold
// geometry are unpredictable (as in Python).
double mesh_volume(const std::vector<double>& verts, const std::vector<int>& faces);

// Axis-aligned box of a flat x, y, z vertex list (empty list -> void box).
Bnd_Box aabb_of(const std::vector<double>& verts);

// Oriented box of a flat x, y, z vertex list (OCCT Bnd_OBB::ReBuild).
Bnd_OBB obb_of(const std::vector<double>& verts);

// Copies inflated by `gap` on every side (a void box stays void).
Bnd_Box inflate(const Bnd_Box& box, double gap);
Bnd_OBB inflate(const Bnd_OBB& box, double gap);

// ---- ifcopenshell.util.shape counterparts (same filters, same formulas;
// the numpy sums are pairwise, these are sequential: equal to ~1e-15).
using Vec3 = std::array<double, 3>;

// get_area
double mesh_area(const std::vector<double>& verts, const std::vector<int>& faces);
// get_side_area(direction=..., angle=...)
double side_area(const std::vector<double>& verts, const std::vector<int>& faces, Vec3 direction,
                 double angle_degrees);
// get_footprint_area(direction=...): the shapely union of the projected
// faces, through GEOS.
double footprint_area(const std::vector<double>& verts, const std::vector<int>& faces, Vec3 direction,
                      const Geos& geos);

// clash_utils.get_extreme_faces: the indices (triangle numbers) of the
// faces toward `direction` not covered (>= 99 %) by a face beyond them.
std::vector<int> extreme_faces(const std::vector<double>& verts, const std::vector<int>& faces, Vec3 direction,
                               const Geos& geos);
// 0.5 * |(p1 - p0) x (p2 - p0)|, numpy order
double triangle_area(const Vec3& p0, const Vec3& p1, const Vec3& p2);
// clash_utils.triangle_face_data
FaceData triangle_face_data(const Vec3& p0, const Vec3& p1, const Vec3& p2);

inline Vec3 vertex(const std::vector<double>& verts, int index) {
    const size_t i = 3 * static_cast<size_t>(index);
    return {verts[i], verts[i + 1], verts[i + 2]};
}

}  // namespace ifcclash::geometry
