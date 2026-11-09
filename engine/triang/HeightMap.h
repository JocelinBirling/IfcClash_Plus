// IfcClash_Plus engine — the rasterized height map of a mesh: a z-buffer
// seen from above or from below, with the triangle that wins each cell
// (engine/triang).
#pragma once

#include <cstddef>
#include <vector>

namespace ifcclash::triang {

struct HeightMapOptions {
    // Cell side, in model units (meter). The grid is refined when the mesh
    // would get fewer than `min_side` cells along its longest plan side (a
    // small fitting), and coarsened when it would need more than `max_side`.
    double cell = 0.01;
    int min_side = 64;
    int max_side = 1024;
};

// A z-buffer on a regular XY grid. The sample of a cell is its centre:
// the cell (i, j) samples (x0 + (i + 0.5) * cell, y0 + (j + 0.5) * cell).
struct HeightMap {
    double x0 = 0.0, y0 = 0.0, cell = 0.0;
    int nx = 0, ny = 0;
    double side = 1.0;     // +1: seen from above (max z), -1: from below (min z)
    std::vector<double> z;  // nx * ny, row major (j * nx + i); NaN when empty
    std::vector<int> id;    // the winning triangle (faces / 3), -1 when empty

    bool empty() const { return nx == 0 || ny == 0; }
    size_t index(int i, int j) const { return size_t(j) * size_t(nx) + size_t(i); }
};

// The height map of a mesh seen from `side` (+1 above, -1 below): every
// cell keeps the highest (lowest) z of the non-vertical triangles that
// contain its centre, and the triangle giving it. Independent of the
// winding. Cost: the number of triangles plus the number of covered cells.
HeightMap height_map(const std::vector<double>& verts, const std::vector<int>& faces, double side,
                     const HeightMapOptions& options = {});

// The triangles seen from above (side +1) or from below (side -1), from the
// height map: a triangle is seen when, at one of the cell centres it
// contains, no other triangle is beyond it (1e-6 tolerance: a coplanar
// duplicate does not hide). A triangle too small to contain a cell centre
// is tested at its centroid against the winners of the 3 x 3 cells around
// it. Same contract as visible_triangles; indices of triangles (faces / 3),
// ascending.
std::vector<int> visible_triangles_raster(const std::vector<double>& verts, const std::vector<int>& faces,
                                          double side, const HeightMapOptions& options = {});

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
