#include "Distance.h"

#include <algorithm>
#include <cmath>
#include <limits>

namespace ifcclash::triang {

namespace {

P3 sub(const P3& a, const P3& b) { return {a[0] - b[0], a[1] - b[1], a[2] - b[2]}; }
P3 add(const P3& a, const P3& b) { return {a[0] + b[0], a[1] + b[1], a[2] + b[2]}; }
P3 mul(const P3& a, double k) { return {a[0] * k, a[1] * k, a[2] * k}; }
double dot(const P3& a, const P3& b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
P3 cross(const P3& a, const P3& b) {
    return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
}
double dist2(const P3& a, const P3& b) {
    const P3 d = sub(a, b);
    return dot(d, d);
}

}  // namespace

P3 closest_point_on_triangle(const P3& p, const P3& a, const P3& b, const P3& c) {
    const P3 ab = sub(b, a), ac = sub(c, a), ap = sub(p, a);
    const double d1 = dot(ab, ap), d2 = dot(ac, ap);
    if (d1 <= 0 && d2 <= 0) return a;
    const P3 bp = sub(p, b);
    const double d3 = dot(ab, bp), d4 = dot(ac, bp);
    if (d3 >= 0 && d4 <= d3) return b;
    const double vc = d1 * d4 - d3 * d2;
    if (vc <= 0 && d1 >= 0 && d3 <= 0) return add(a, mul(ab, d1 / (d1 - d3)));
    const P3 cp = sub(p, c);
    const double d5 = dot(ab, cp), d6 = dot(ac, cp);
    if (d6 >= 0 && d5 <= d6) return c;
    const double vb = d5 * d2 - d1 * d6;
    if (vb <= 0 && d2 >= 0 && d6 <= 0) return add(a, mul(ac, d2 / (d2 - d6)));
    const double va = d3 * d6 - d5 * d4;
    if (va <= 0 && (d4 - d3) >= 0 && (d5 - d6) >= 0)
        return add(b, mul(sub(c, b), (d4 - d3) / ((d4 - d3) + (d5 - d6))));
    const double denom = va + vb + vc;
    if (denom == 0.0) return a;  // degenerate
    const double v = vb / denom, w = vc / denom;
    return add(a, add(mul(ab, v), mul(ac, w)));
}

double closest_points_of_segments(const P3& p1, const P3& q1, const P3& p2, const P3& q2, P3& c1, P3& c2) {
    const P3 d1 = sub(q1, p1), d2 = sub(q2, p2), r = sub(p1, p2);
    const double a = dot(d1, d1), e = dot(d2, d2), f = dot(d2, r);
    constexpr double eps = 1e-24;
    double s = 0.0, t = 0.0;
    if (a <= eps && e <= eps) {
        c1 = p1;
        c2 = p2;
        return dist2(c1, c2);
    }
    if (a <= eps) {
        t = std::clamp(f / e, 0.0, 1.0);
    } else {
        const double c = dot(d1, r);
        if (e <= eps) {
            s = std::clamp(-c / a, 0.0, 1.0);
        } else {
            const double b = dot(d1, d2), denom = a * e - b * b;
            s = denom != 0.0 ? std::clamp((b * f - c * e) / denom, 0.0, 1.0) : 0.0;
            t = (b * s + f) / e;
            if (t < 0.0) {
                t = 0.0;
                s = std::clamp(-c / a, 0.0, 1.0);
            } else if (t > 1.0) {
                t = 1.0;
                s = std::clamp((b - c) / a, 0.0, 1.0);
            }
        }
    }
    c1 = add(p1, mul(d1, s));
    c2 = add(p2, mul(d2, t));
    return dist2(c1, c2);
}

bool segment_hits_triangle(const P3& p, const P3& q, const P3& a, const P3& b, const P3& c, double eps, double& t) {
    // Moller-Trumbore on the segment direction, with slack.
    const P3 dir = sub(q, p);
    const P3 e1 = sub(b, a), e2 = sub(c, a);
    const P3 h = cross(dir, e2);
    const double det = dot(e1, h);
    const double scale = std::sqrt(dot(e1, e1) * dot(e2, e2)) * std::sqrt(dot(dir, dir));
    if (std::abs(det) <= 1e-14 * std::max(scale, 1e-300)) {
        // Parallel: a hit only if the segment lies in the plane and crosses
        // the triangle; tested as the distance between the segment and the
        // triangle edges / inside.
        P3 c1, c2;
        const double tol2 = eps * eps;
        double best = std::numeric_limits<double>::infinity();
        double best_t = 0.0;
        const P3* v[3] = {&a, &b, &c};
        for (int k = 0; k < 3; ++k) {
            const double d = closest_points_of_segments(p, q, *v[k], *v[(k + 1) % 3], c1, c2);
            if (d < best) {
                best = d;
                const double len2 = dot(dir, dir);
                best_t = len2 > 0 ? dot(sub(c1, p), dir) / len2 : 0.0;
            }
        }
        const P3 cp = closest_point_on_triangle(p, a, b, c);
        if (dist2(cp, p) <= tol2) {
            t = 0.0;
            return true;
        }
        if (best <= tol2) {
            t = best_t;
            return true;
        }
        return false;
    }
    const double inv = 1.0 / det;
    const P3 s = sub(p, a);
    const double u = dot(s, h) * inv;
    const P3 qv = cross(s, e1);
    const double v = dot(dir, qv) * inv;
    const double tt = dot(e2, qv) * inv;
    const double len = std::sqrt(dot(dir, dir));
    const double te = len > 0 ? eps / len : eps;  // eps in length along the segment
    const double l1 = std::sqrt(dot(e1, e1)), l2 = std::sqrt(dot(e2, e2));
    const double ue = l1 > 0 ? eps / l1 : eps, ve = l2 > 0 ? eps / l2 : eps;
    if (u < -ue || v < -ve || u + v > 1.0 + std::max(ue, ve)) return false;
    if (tt < -te || tt > 1.0 + te) return false;
    t = std::clamp(tt, 0.0, 1.0);
    return true;
}

double triangle_distance(const P3& a, const P3& b, const P3& c, const P3& d, const P3& e, const P3& f, P3& pa, P3& pb) {
    // Meeting: an edge of one crosses the other.
    const P3* t1[3] = {&a, &b, &c};
    const P3* t2[3] = {&d, &e, &f};
    double t = 0.0;
    for (int k = 0; k < 3; ++k) {
        if (segment_hits_triangle(*t1[k], *t1[(k + 1) % 3], d, e, f, 0.0, t)) {
            const P3 dir = sub(*t1[(k + 1) % 3], *t1[k]);
            pa = pb = add(*t1[k], mul(dir, t));
            return 0.0;
        }
        if (segment_hits_triangle(*t2[k], *t2[(k + 1) % 3], a, b, c, 0.0, t)) {
            const P3 dir = sub(*t2[(k + 1) % 3], *t2[k]);
            pa = pb = add(*t2[k], mul(dir, t));
            return 0.0;
        }
    }
    // Apart: the minimum of the 9 edge pairs and the 6 vertex / triangle pairs.
    double best = std::numeric_limits<double>::infinity();
    P3 c1, c2;
    for (int i = 0; i < 3; ++i) {
        for (int j = 0; j < 3; ++j) {
            const double d2 = closest_points_of_segments(*t1[i], *t1[(i + 1) % 3], *t2[j], *t2[(j + 1) % 3], c1, c2);
            if (d2 < best) {
                best = d2;
                pa = c1;
                pb = c2;
            }
        }
    }
    for (int i = 0; i < 3; ++i) {
        const P3 q = closest_point_on_triangle(*t1[i], d, e, f);
        const double d2 = dist2(*t1[i], q);
        if (d2 < best) {
            best = d2;
            pa = *t1[i];
            pb = q;
        }
        const P3 r = closest_point_on_triangle(*t2[i], a, b, c);
        const double d3 = dist2(*t2[i], r);
        if (d3 < best) {
            best = d3;
            pa = r;
            pb = *t2[i];
        }
    }
    return std::sqrt(best);
}

}  // namespace ifcclash::triang
