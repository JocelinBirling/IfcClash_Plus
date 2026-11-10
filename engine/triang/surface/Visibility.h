// IfcClash_Plus engine — the triangles of a mesh seen from above or from
// below (engine/triang/surface): the sampled test, and the choice between it
// and the height map (HeightMap.h) by mesh size.
#pragma once

#include "../mesh/TriMesh.h"
#include "HeightMap.h"

#include <cstddef>
#include <vector>

namespace ifcclash::triang {

// The triangles of a mesh seen from above (side +1) or from below (side
// -1): the non-vertical triangles of which one sample point (the centroid,
// or a point near a corner) is covered by no other triangle of the mesh on
// that side. Independent of the winding (many IFC meshes are wound
// inwards): the triangulated counterpart of the faces the vertical rays of
// Above hit first. Indices of triangles (faces / 3).
std::vector<int> visible_triangles(const std::vector<double>& verts, const std::vector<int>& faces, double side);

// Whether the point (x, y, z), on triangle `self` of the mesh, is covered from
// `side` (+1 above, -1 below) by another non-vertical triangle of the mesh:
// one containing (x, y) in plan and beyond z by more than 1e-6 (a coplanar
// duplicate does not cover). The point-level form of the seen triangles: a
// triangle partly seen has covered points.
bool point_covered(const TriMesh& mesh, size_t self, double x, double y, double z, double side);

// Mesh size from which visible_triangles_auto switches to the height map:
// below it the sampled test is cheaper (its cost follows the triangles, the
// height map's the cells). Measured on the Duplex Architecture +
// Mechanical (doc/benchmark_extreme_faces.md): the total time is flat
// between 120 and 300 triangles, minimal around 200.
constexpr size_t kHeightMapFromTriangles = 200;

// The triangles seen from `side`: visible_triangles (4 sampled points per
// triangle) under `from_triangles` triangles, visible_triangles_raster
// (height map) from it on. Indices of triangles, ascending.
std::vector<int> visible_triangles_auto(const std::vector<double>& verts, const std::vector<int>& faces,
                                        double side, size_t from_triangles = kHeightMapFromTriangles,
                                        const HeightMapOptions& options = {});

}  // namespace ifcclash::triang
