#include "TriangleTests.h"

#include <BVH_BoxSet.hxx>
#include <TColgp_Array1OfPnt.hxx>
#include <gp_Pnt.hxx>

#include <algorithm>
#include <cmath>
#include <limits>
#include <stack>

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

struct BoxTree::Impl {
    BVH_BoxSet<double, 3, int> set;
};

BoxTree::BoxTree(const std::vector<Bnd_Box>& boxes) : impl_(std::make_unique<Impl>()) {
    for (int i = 0; i < static_cast<int>(boxes.size()); ++i) {
        if (boxes[i].IsVoid()) continue;
        double x0, y0, z0, x1, y1, z1;
        boxes[i].Get(x0, y0, z0, x1, y1, z1);
        impl_->set.Add(i, BVH_Box<double, 3>(BVH_Vec3d(x0, y0, z0), BVH_Vec3d(x1, y1, z1)));
        empty_ = false;
    }
    if (!empty_) impl_->set.Build();
}

BoxTree::~BoxTree() = default;
BoxTree::BoxTree(BoxTree&&) noexcept = default;
BoxTree& BoxTree::operator=(BoxTree&&) noexcept = default;

void BoxTree::query(const Bnd_Box& q, const std::function<bool(int)>& visit) const {
    if (empty_ || q.IsVoid()) return;
    double qx0, qy0, qz0, qx1, qy1, qz1;
    q.Get(qx0, qy0, qz0, qx1, qy1, qz1);
    const auto& bvh = impl_->set.BVH();
    std::stack<int> stack;
    stack.push(0);
    while (!stack.empty()) {
        const int i = stack.top();
        stack.pop();
        const auto& lo = bvh->MinPoint(i);
        const auto& hi = bvh->MaxPoint(i);
        if (lo.x() > qx1 || hi.x() < qx0 || lo.y() > qy1 || hi.y() < qy0 || lo.z() > qz1 || hi.z() < qz0) continue;
        if (bvh->IsOuter(i)) {
            for (int j = bvh->BegPrimitive(i); j <= bvh->EndPrimitive(i); ++j) {
                const auto box = impl_->set.Box(j);
                const auto& bl = box.CornerMin();
                const auto& bh = box.CornerMax();
                if (bl.x() > qx1 || bh.x() < qx0 || bl.y() > qy1 || bh.y() < qy0 || bl.z() > qz1 || bh.z() < qz0)
                    continue;
                if (!visit(impl_->set.Element(j))) return;
            }
        } else {
            stack.push(bvh->Child<0>(i));
            stack.push(bvh->Child<1>(i));
        }
    }
}

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

Bnd_OBB optimal_obb(const std::vector<double>& xyz) {
    Bnd_OBB obb;
    const int n = static_cast<int>(xyz.size() / 3);
    if (n == 0) return obb;
    TColgp_Array1OfPnt points(1, n);
    for (int i = 0; i < n; ++i) points.SetValue(i + 1, gp_Pnt(xyz[3 * i], xyz[3 * i + 1], xyz[3 * i + 2]));
    obb.ReBuild(points, nullptr, true);
    return obb;
}

}  // namespace ifcclash::triang
