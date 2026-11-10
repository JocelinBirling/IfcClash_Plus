#include "TriangleTests.h"

#include <algorithm>
#include <cmath>

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

bool triangle_meets_obb(const P3& a, const P3& b, const P3& c, const Bnd_OBB& obb, double margin) {
    // The triangle in the frame of the box: then an AABB test.
    const gp_XYZ o = obb.Center();
    const P3 axes[3] = {{obb.XDirection().X(), obb.XDirection().Y(), obb.XDirection().Z()},
                        {obb.YDirection().X(), obb.YDirection().Y(), obb.YDirection().Z()},
                        {obb.ZDirection().X(), obb.ZDirection().Y(), obb.ZDirection().Z()}};
    const double h[3] = {obb.XHSize() + margin, obb.YHSize() + margin, obb.ZHSize() + margin};
    if (h[0] < 0 || h[1] < 0 || h[2] < 0) return false;  // shrunk to nothing
    const P3 center{o.X(), o.Y(), o.Z()};
    P3 v[3];
    const P3* src[3] = {&a, &b, &c};
    for (int i = 0; i < 3; ++i) {
        const P3 d = sub(*src[i], center);
        v[i] = {dot(d, axes[0]), dot(d, axes[1]), dot(d, axes[2])};
    }
    // 1. The box axes.
    for (int k = 0; k < 3; ++k) {
        const double lo = std::min({v[0][k], v[1][k], v[2][k]});
        const double hi = std::max({v[0][k], v[1][k], v[2][k]});
        if (lo > h[k] || hi < -h[k]) return false;
    }
    // 2. The triangle normal.
    const P3 e[3] = {sub(v[1], v[0]), sub(v[2], v[1]), sub(v[0], v[2])};
    const P3 n = cross(e[0], e[1]);
    {
        const double r = h[0] * std::abs(n[0]) + h[1] * std::abs(n[1]) + h[2] * std::abs(n[2]);
        const double s = dot(n, v[0]);
        if (std::abs(s) > r) return false;
    }
    // 3. The 9 products of an edge with a box axis.
    for (int i = 0; i < 3; ++i) {
        for (int k = 0; k < 3; ++k) {
            P3 unit{0, 0, 0};
            unit[k] = 1.0;
            const P3 axis = cross(e[i], unit);
            if (std::abs(axis[0]) + std::abs(axis[1]) + std::abs(axis[2]) < 1e-15) continue;
            const double p0 = dot(axis, v[0]), p1 = dot(axis, v[1]), p2 = dot(axis, v[2]);
            const double r = h[0] * std::abs(axis[0]) + h[1] * std::abs(axis[1]) + h[2] * std::abs(axis[2]);
            if (std::min({p0, p1, p2}) > r || std::max({p0, p1, p2}) < -r) return false;
        }
    }
    return true;
}

std::vector<P2> clip_triangles_xy(const P3& a1, const P3& b1, const P3& c1, const P3& a2, const P3& b2,
                                  const P3& c2, double grow) {
    std::vector<P2> poly{{a1[0], a1[1]}, {b1[0], b1[1]}, {c1[0], c1[1]}};
    P2 clip[3] = {{a2[0], a2[1]}, {b2[0], b2[1]}, {c2[0], c2[1]}};
    // Counter-clockwise clip triangle; a degenerate one (vertical face) has
    // no area to overlap.
    const double area = cross2(clip[0], clip[1], clip[2]);
    if (std::abs(area) < 1e-14) return {};
    if (area < 0) std::swap(clip[1], clip[2]);
    // Inclusive test, grown: a point within `grow` of the clip edge is inside
    // (a negative `grow` shrinks the clip triangle).
    const double eps = grow != 0.0 ? grow : 1e-12;
    for (int k = 0; k < 3 && !poly.empty(); ++k) {
        const P2& p = clip[k];
        const P2& q = clip[(k + 1) % 3];
        const double len = std::hypot(q[0] - p[0], q[1] - p[1]);
        auto side = [&](const P2& x) { return cross2(p, q, x) / len; };
        std::vector<P2> next;
        for (size_t i = 0; i < poly.size(); ++i) {
            const P2& cur = poly[i];
            const P2& prev = poly[(i + poly.size() - 1) % poly.size()];
            const double sc = side(cur), sp = side(prev);
            const bool in_c = sc >= -eps, in_p = sp >= -eps;
            if (in_c) {
                if (!in_p) {
                    const double t = sp / (sp - sc);
                    next.push_back({prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])});
                }
                next.push_back(cur);
            } else if (in_p) {
                const double t = sp / (sp - sc);
                next.push_back({prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])});
            }
        }
        poly = std::move(next);
    }
    return poly;
}

}  // namespace ifcclash::triang
