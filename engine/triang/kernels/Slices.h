// IfcClash_Plus engine — horizontal slabs and sections of triangle meshes
// (engine/triang/kernels): the plan footprint of the part of a mesh between
// two heights, as polygons (FreeSpace_triang).
#pragma once

#include "TriangleTests.h"

#include <vector>

namespace ifcclash::triang {

class TriMesh;

// The part of triangle (a, b, c) between the heights z0 and z1 (z0 < z1),
// as a convex polygon in 3D (Sutherland-Hodgman on the two planes); empty
// when the triangle lies outside.
std::vector<P3> clip_triangle_z(const P3& a, const P3& b, const P3& c, double z0, double z1);

// The section of a mesh by the plane z = h: the closed loops (in plan) formed
// by the segments where its triangles cross the plane, chained through the
// mesh edges they cut. Only meaningful on a closed mesh. A triangle lying in
// the plane or touching it at a vertex only adds no segment.
std::vector<std::vector<P2>> section_loops(const TriMesh& mesh, double h);

}  // namespace ifcclash::triang
