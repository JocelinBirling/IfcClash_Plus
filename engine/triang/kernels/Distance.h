// IfcClash_Plus engine — distances and segment tests on triangles
// (engine/triang/kernels): no allocation, no OCCT shape.
#pragma once

#include "TriangleTests.h"

namespace ifcclash::triang {

// The closest point of triangle (a, b, c) to p (Ericson, Real-Time Collision
// Detection 5.1.5).
P3 closest_point_on_triangle(const P3& p, const P3& a, const P3& b, const P3& c);

// The closest points of segments [p1, q1] and [p2, q2] (Ericson 5.1.9);
// returns the squared distance.
double closest_points_of_segments(const P3& p1, const P3& q1, const P3& p2, const P3& q2, P3& c1, P3& c2);

// Whether the segment [p, q] meets the triangle (a, b, c), its edges and the
// segment ends included within `eps` (barycentric and parametric slack).
// On a hit, t is the parameter of the hit point along [p, q] (0 at p).
bool segment_hits_triangle(const P3& p, const P3& q, const P3& a, const P3& b, const P3& c, double eps, double& t);

// The distance between two triangles and its closest points (0 when they
// meet: then pa == pb is a point of both).
double triangle_distance(const P3& a, const P3& b, const P3& c, const P3& d, const P3& e, const P3& f, P3& pa, P3& pb);

}  // namespace ifcclash::triang
