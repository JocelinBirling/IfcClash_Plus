// IfcClash_Plus engine — pure geometry algorithms on meshes and boxes.
// No notion of IFC nor of rules (SPEC "Organisation du code").
#pragma once

#include <Bnd_Box.hxx>
#include <Bnd_OBB.hxx>

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

}  // namespace ifcclash::geometry
