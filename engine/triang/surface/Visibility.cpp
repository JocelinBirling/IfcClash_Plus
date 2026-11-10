#include "Visibility.h"

#include "../kernels/TriangleTests.h"
#include "../spatial/BoxTree.h"

#include <gp_Pnt.hxx>

#include <cmath>
#include <limits>

namespace ifcclash::triang {

namespace {

P3 sub(const P3& a, const P3& b) { return {a[0] - b[0], a[1] - b[1], a[2] - b[2]}; }
double dot(const P3& a, const P3& b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
P3 cross(const P3& a, const P3& b) {
    return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
}
double cross2(const P2& o, const P2& a, const P2& b) {
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0]);
}

}  // namespace

std::vector<int> visible_triangles(const std::vector<double>& verts, const std::vector<int>& faces, double side) {
    auto vtx = [&](int i) { return P3{verts[3 * size_t(i)], verts[3 * size_t(i) + 1], verts[3 * size_t(i) + 2]}; };
    const size_t n = faces.size() / 3;
    // The non-vertical triangles, their plane (z = f(x, y)) and boxes.
    struct Tri {
        P3 a, b, c, normal;
        int index;
    };
    std::vector<Tri> tris;
    std::vector<Bnd_Box> boxes;
    double z_lo = std::numeric_limits<double>::infinity(), z_hi = -z_lo;
    for (size_t t = 0; t < n; ++t) {
        const P3 a = vtx(faces[3 * t]), b = vtx(faces[3 * t + 1]), c = vtx(faces[3 * t + 2]);
        const P3 normal = cross(sub(b, a), sub(c, a));
        const double len = std::sqrt(dot(normal, normal));
        if (len < 1e-14 || std::abs(normal[2]) / len <= 1e-6) continue;  // vertical: seen edge-on
        Bnd_Box box;
        for (const P3* p : {&a, &b, &c}) {
            box.Add(gp_Pnt((*p)[0], (*p)[1], (*p)[2]));
            z_lo = std::min(z_lo, (*p)[2]);
            z_hi = std::max(z_hi, (*p)[2]);
        }
        tris.push_back({a, b, c, normal, static_cast<int>(t)});
        boxes.push_back(box);
    }
    const BoxTree tree(boxes);
    constexpr double kCover = 1e-6;  // a coplanar duplicate does not cover
    auto covered = [&](size_t self, const P3& q) {
        Bnd_Box column;
        column.Update(q[0], q[1], side > 0 ? q[2] : z_lo - 1.0, q[0], q[1], side > 0 ? z_hi + 1.0 : q[2]);
        bool hit = false;
        tree.query(column, [&](int j) {
            if (static_cast<size_t>(j) == self) return true;
            const Tri& u = tris[size_t(j)];
            const P2 p{q[0], q[1]};
            const P2 a{u.a[0], u.a[1]}, b{u.b[0], u.b[1]}, c{u.c[0], u.c[1]};
            const double d0 = cross2(a, b, p), d1 = cross2(b, c, p), d2 = cross2(c, a, p);
            const bool inside = (d0 >= -1e-12 && d1 >= -1e-12 && d2 >= -1e-12) ||
                                (d0 <= 1e-12 && d1 <= 1e-12 && d2 <= 1e-12);
            if (!inside) return true;
            const double z = u.a[2] - (u.normal[0] * (q[0] - u.a[0]) + u.normal[1] * (q[1] - u.a[1])) / u.normal[2];
            if (side * (z - q[2]) > kCover) {
                hit = true;
                return false;
            }
            return true;
        });
        return hit;
    };
    std::vector<int> out;
    for (size_t k = 0; k < tris.size(); ++k) {
        const Tri& t = tris[k];
        const P3 g{(t.a[0] + t.b[0] + t.c[0]) / 3, (t.a[1] + t.b[1] + t.c[1]) / 3, (t.a[2] + t.b[2] + t.c[2]) / 3};
        bool seen = !covered(k, g);
        for (const P3* v : {&t.a, &t.b, &t.c}) {
            if (seen) break;
            const P3 q{g[0] + 0.8 * ((*v)[0] - g[0]), g[1] + 0.8 * ((*v)[1] - g[1]), g[2] + 0.8 * ((*v)[2] - g[2])};
            seen = !covered(k, q);
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

bool point_covered(const TriMesh& mesh, size_t self, double x, double y, double z, double side) {
    constexpr double kCover = 1e-6;
    double x0, y0, z0, x1, y1, z1;
    mesh.bounds().Get(x0, y0, z0, x1, y1, z1);
    Bnd_Box column;
    column.Update(x, y, side > 0 ? z : z0 - 1.0, x, y, side > 0 ? z1 + 1.0 : z);
    bool hit = false;
    const P2 p{x, y};
    mesh.tree().query(column, [&](int j) {
        if (static_cast<size_t>(j) == self) return true;
        const P3& n = mesh.normal(size_t(j));
        if (std::abs(n[2]) <= 1e-6) return true;  // vertical: no plan area
        P3 a, b, c;
        mesh.corners(size_t(j), a, b, c);
        const P2 pa{a[0], a[1]}, pb{b[0], b[1]}, pc{c[0], c[1]};
        const double d0 = cross2(pa, pb, p), d1 = cross2(pb, pc, p), d2 = cross2(pc, pa, p);
        const bool inside = (d0 >= -1e-12 && d1 >= -1e-12 && d2 >= -1e-12) || (d0 <= 1e-12 && d1 <= 1e-12 && d2 <= 1e-12);
        if (!inside) return true;
        const double zu = a[2] - (n[0] * (x - a[0]) + n[1] * (y - a[1])) / n[2];
        if (side * (zu - z) > kCover) {
            hit = true;
            return false;
        }
        return true;
    });
    return hit;
}

}  // namespace ifcclash::triang
