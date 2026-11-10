// IfcClash_Plus engine — elementary tests on triangles (engine/triang/kernels):
// no allocation in the hot paths, no OCCT shape, no notion of rule.
#pragma once

#include <Bnd_OBB.hxx>

#include <array>
#include <vector>

namespace ifcclash::triang {

using P3 = std::array<double, 3>;
using P2 = std::array<double, 2>;

// Whether a triangle meets an oriented box, the box grown by `margin` on
// every side (shrunk when negative) (separating axis theorem, 13 axes: the 3 box axes, the
// triangle normal and the 9 edge x axis products). Exact up to rounding.
bool triangle_meets_obb(const P3& a, const P3& b, const P3& c, const Bnd_OBB& obb, double margin);

// The convex polygon common to the first triangle and the second one grown
// by `grow` on every edge (shrunk when negative), both projected on XY (Sutherland-Hodgman), empty
// when they do not overlap. A shared edge gives a degenerate polygon.
std::vector<P2> clip_triangles_xy(const P3& a1, const P3& b1, const P3& c1, const P3& a2, const P3& b2,
                                  const P3& c2, double grow = 0.0);

}  // namespace ifcclash::triang
