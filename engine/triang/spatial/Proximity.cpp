#include "Proximity.h"

#include <gp_Pnt.hxx>

#include <algorithm>
#include <cmath>
#include <numeric>

namespace ifcclash::triang {

MeshDistance mesh_distance(const TriMesh& a, const TriMesh& b, double cutoff) {
    MeshDistance out;
    if (!a.triangle_count() || !b.triangle_count()) return out;
    // An upper bound to start: two vertices, one on each surface.
    const P3 va = a.vertex(a.faces()[0]), vb = b.vertex(b.faces()[0]);
    double best = std::sqrt((va[0] - vb[0]) * (va[0] - vb[0]) + (va[1] - vb[1]) * (va[1] - vb[1]) +
                            (va[2] - vb[2]) * (va[2] - vb[2]));
    out = {best, va, vb};
    // The triangles of a, nearest to the box of b first.
    std::vector<std::pair<double, size_t>> order;
    order.reserve(a.triangle_count());
    for (size_t t = 0; t < a.triangle_count(); ++t) order.push_back({a.box(t).Distance(b.bounds()), t});
    std::sort(order.begin(), order.end());
    for (const auto& [lower, t] : order) {
        if (lower > best || best == 0.0) break;
        if (lower > cutoff) break;
        Bnd_Box query = a.box(t);
        query.Enlarge(best);
        P3 a0, a1, a2;
        a.corners(t, a0, a1, a2);
        b.tree().query(query, [&](int u) {
            if (a.box(t).Distance(b.box(size_t(u))) > best) return true;
            P3 b0, b1, b2;
            b.corners(size_t(u), b0, b1, b2);
            P3 pa, pb;
            const double d = triangle_distance(a0, a1, a2, b0, b1, b2, pa, pb);
            if (d < best) {
                best = d;
                out = {d, pa, pb};
            }
            return best > 0.0;
        });
    }
    return out;
}

void TriangleSoup::add(int owner, const TriMesh& mesh) {
    for (size_t t = 0; t < mesh.triangle_count(); ++t) {
        P3 a, b, c;
        mesh.corners(t, a, b, c);
        corners_.insert(corners_.end(), {a, b, c});
        owners_.push_back(owner);
        boxes_.push_back(mesh.box(t));
    }
}

void TriangleSoup::build() { tree_ = std::make_unique<BoxTree>(boxes_); }

}  // namespace ifcclash::triang
