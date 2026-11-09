#include "HeightMap.h"

#include "TriangleTests.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace ifcclash::triang {

namespace {

// A coplanar duplicate, or a neighbour sharing the cell centre on an edge,
// does not hide: only a triangle beyond by more than this does.
constexpr double kCover = 1e-6;

// One non-vertical triangle: its XY corners and its plane z = f(x, y).
struct Tri {
    double ax, ay, az, bx, by, cx, cy;
    double nx, ny, nz;  // normal (any winding)
    double xmin, xmax, ymin, ymax;
    int index;  // triangle number in faces / 3

    double z_at(double x, double y) const { return az - (nx * (x - ax) + ny * (y - ay)) / nz; }

    // Whether (x, y) lies in the XY projection, edges included.
    bool contains(double x, double y) const {
        auto cross2 = [](double ox, double oy, double px, double py, double qx, double qy) {
            return (px - ox) * (qy - oy) - (py - oy) * (qx - ox);
        };
        const double d0 = cross2(ax, ay, bx, by, x, y);
        const double d1 = cross2(bx, by, cx, cy, x, y);
        const double d2 = cross2(cx, cy, ax, ay, x, y);
        constexpr double e = 1e-12;
        return (d0 >= -e && d1 >= -e && d2 >= -e) || (d0 <= e && d1 <= e && d2 <= e);
    }
};

std::vector<Tri> non_vertical(const std::vector<double>& verts, const std::vector<int>& faces) {
    const size_t n = faces.size() / 3;
    std::vector<Tri> tris;
    tris.reserve(n);
    for (size_t t = 0; t < n; ++t) {
        const double* a = &verts[3 * size_t(faces[3 * t])];
        const double* b = &verts[3 * size_t(faces[3 * t + 1])];
        const double* c = &verts[3 * size_t(faces[3 * t + 2])];
        const double ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2];
        const double vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
        const double nx = uy * vz - uz * vy, ny = uz * vx - ux * vz, nz = ux * vy - uy * vx;
        const double len = std::sqrt(nx * nx + ny * ny + nz * nz);
        if (len < 1e-14 || std::abs(nz) / len <= 1e-6) continue;  // vertical: seen edge-on
        Tri tri{a[0], a[1], a[2], b[0], b[1], c[0], c[1], nx, ny, nz, 0, 0, 0, 0, static_cast<int>(t)};
        tri.xmin = std::min({a[0], b[0], c[0]});
        tri.xmax = std::max({a[0], b[0], c[0]});
        tri.ymin = std::min({a[1], b[1], c[1]});
        tri.ymax = std::max({a[1], b[1], c[1]});
        tris.push_back(tri);
    }
    return tris;
}

// Calls visit(i, j, z) for every cell whose centre lies in the triangle,
// row by row (scanline: the exact X span of the triangle on the row of
// centres). visit returns false to stop.
template <class Visit>
void rasterize(const HeightMap& map, const Tri& t, Visit&& visit) {
    const double inv = 1.0 / map.cell;
    constexpr double tiny = 1e-9;  // in cells: a centre on an edge is inside
    const int j0 = std::max(0, int(std::ceil((t.ymin - map.y0) * inv - 0.5 - tiny)));
    const int j1 = std::min(map.ny - 1, int(std::floor((t.ymax - map.y0) * inv - 0.5 + tiny)));
    const double px[3] = {t.ax, t.bx, t.cx};
    const double py[3] = {t.ay, t.by, t.cy};
    for (int j = j0; j <= j1; ++j) {
        const double y = map.y0 + (j + 0.5) * map.cell;
        double lo = std::numeric_limits<double>::infinity(), hi = -lo;
        for (int k = 0; k < 3; ++k) {
            const double x1 = px[k], y1 = py[k], x2 = px[(k + 1) % 3], y2 = py[(k + 1) % 3];
            const double ylo = std::min(y1, y2), yhi = std::max(y1, y2);
            const double slack = tiny * map.cell;
            if (y < ylo - slack || y > yhi + slack) continue;
            if (y2 == y1) {
                lo = std::min({lo, x1, x2});
                hi = std::max({hi, x1, x2});
            } else {
                const double s = std::clamp((y - y1) / (y2 - y1), 0.0, 1.0);
                const double x = x1 + s * (x2 - x1);
                lo = std::min(lo, x);
                hi = std::max(hi, x);
            }
        }
        if (lo > hi) continue;
        const int i0 = std::max(0, int(std::ceil((lo - map.x0) * inv - 0.5 - tiny)));
        const int i1 = std::min(map.nx - 1, int(std::floor((hi - map.x0) * inv - 0.5 + tiny)));
        for (int i = i0; i <= i1; ++i) {
            const double x = map.x0 + (i + 0.5) * map.cell;
            if (!visit(i, j, t.z_at(x, y))) return;
        }
    }
}

HeightMap empty_grid(const std::vector<Tri>& tris, double side, const HeightMapOptions& options) {
    HeightMap map;
    map.side = side >= 0 ? 1.0 : -1.0;
    if (tris.empty()) return map;
    double xmin = tris[0].xmin, xmax = tris[0].xmax, ymin = tris[0].ymin, ymax = tris[0].ymax;
    for (const Tri& t : tris) {
        xmin = std::min(xmin, t.xmin);
        xmax = std::max(xmax, t.xmax);
        ymin = std::min(ymin, t.ymin);
        ymax = std::max(ymax, t.ymax);
    }
    const double extent = std::max(xmax - xmin, ymax - ymin);
    const int max_side = std::max(1, options.max_side);
    double cell = options.cell > 0 ? options.cell : 0.01;
    if (options.min_side > 0 && extent > 0) cell = std::min(cell, extent / options.min_side);
    map.cell = std::max(cell, extent / max_side);
    if (!(map.cell > 0)) map.cell = options.cell > 0 ? options.cell : 0.01;  // a single point in plan
    map.x0 = xmin;
    map.y0 = ymin;
    map.nx = std::clamp(int(std::ceil((xmax - xmin) / map.cell)), 1, max_side);
    map.ny = std::clamp(int(std::ceil((ymax - ymin) / map.cell)), 1, max_side);
    map.z.assign(size_t(map.nx) * size_t(map.ny), std::numeric_limits<double>::quiet_NaN());
    map.id.assign(map.z.size(), -1);
    return map;
}

// Fills the z-buffer; counts the cells of each triangle (index in tris).
void fill(HeightMap& map, const std::vector<Tri>& tris, std::vector<int>* cells) {
    const double s = map.side;
    for (size_t k = 0; k < tris.size(); ++k) {
        int count = 0;
        rasterize(map, tris[k], [&](int i, int j, double z) {
            const size_t c = map.index(i, j);
            if (map.id[c] < 0 || s * z > s * map.z[c]) {
                map.z[c] = z;
                map.id[c] = int(k);
            }
            ++count;
            return true;
        });
        if (cells) (*cells)[k] = count;
    }
}

}  // namespace

HeightMap height_map(const std::vector<double>& verts, const std::vector<int>& faces, double side,
                     const HeightMapOptions& options) {
    const std::vector<Tri> tris = non_vertical(verts, faces);
    HeightMap map = empty_grid(tris, side, options);
    if (map.empty()) return map;
    fill(map, tris, nullptr);
    for (int& w : map.id) {
        if (w >= 0) w = tris[size_t(w)].index;  // triangle numbers of the mesh
    }
    return map;
}

std::vector<int> visible_triangles_raster(const std::vector<double>& verts, const std::vector<int>& faces,
                                          double side, const HeightMapOptions& options) {
    const std::vector<Tri> tris = non_vertical(verts, faces);
    HeightMap map = empty_grid(tris, side, options);
    if (map.empty()) return {};
    std::vector<int> cells(tris.size(), 0);
    fill(map, tris, &cells);
    const double s = map.side;
    // A triangle that wins a cell is seen: no second rasterization for it.
    std::vector<char> won(tris.size(), 0);
    for (int w : map.id) {
        if (w >= 0) won[size_t(w)] = 1;
    }

    std::vector<int> out;
    for (size_t k = 0; k < tris.size(); ++k) {
        const Tri& t = tris[k];
        bool seen = won[k] != 0;
        if (!seen && cells[k] > 0) {
            // Ties: a coplanar duplicate loses the cells but is seen too.
            // Seen at one of its cell centres: nothing beyond it there.
            rasterize(map, t, [&](int i, int j, double z) {
                const size_t c = map.index(i, j);
                if (map.id[c] == int(k) || s * (z - map.z[c]) >= -kCover) {
                    seen = true;
                    return false;
                }
                return true;
            });
        } else if (!seen) {
            // Smaller than a cell: its centroid against the winners around.
            const double gx = (t.ax + t.bx + t.cx) / 3.0, gy = (t.ay + t.by + t.cy) / 3.0;
            const double gz = t.z_at(gx, gy);
            const int ci = std::clamp(int(std::floor((gx - map.x0) / map.cell)), 0, map.nx - 1);
            const int cj = std::clamp(int(std::floor((gy - map.y0) / map.cell)), 0, map.ny - 1);
            seen = true;
            for (int dj = -1; dj <= 1 && seen; ++dj) {
                for (int di = -1; di <= 1 && seen; ++di) {
                    const int i = ci + di, j = cj + dj;
                    if (i < 0 || j < 0 || i >= map.nx || j >= map.ny) continue;
                    const int w = map.id[map.index(i, j)];
                    if (w < 0 || w == int(k)) continue;
                    const Tri& u = tris[size_t(w)];
                    if (u.contains(gx, gy) && s * (u.z_at(gx, gy) - gz) > kCover) seen = false;
                }
            }
        }
        if (seen) out.push_back(t.index);
    }
    return out;
}

std::vector<int> visible_triangles_auto(const std::vector<double>& verts, const std::vector<int>& faces,
                                        double side, size_t from_triangles, const HeightMapOptions& options) {
    if (faces.size() / 3 < from_triangles) return visible_triangles(verts, faces, side);
    return visible_triangles_raster(verts, faces, side, options);
}

}  // namespace ifcclash::triang
