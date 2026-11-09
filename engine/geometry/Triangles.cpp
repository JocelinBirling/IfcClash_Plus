#include "Triangles.h"

#include "../core/Errors.h"
#include "Faces.h"
#include "Numpy.h"

#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_MakePolygon.hxx>
#include <gp_Pnt.hxx>

#include <algorithm>
#include <cmath>
#include <limits>
#include <map>
#include <set>

namespace ifcclash::geometry {

namespace {

const double kAlignmentCosine = std::cos(45.0 * M_PI / 180.0);  // FACE_ALIGNMENT_COSINE
constexpr double kExtremeTolerance = 0.001;                      // FACE_EXTREME_TOLERANCE

using np::cross;
using np::dot;   // 1-D a @ b
using np::norm;  // np.linalg.norm of a 1-D vector
using np::sub;

V3 preset(const std::string& name) { return name == "Top" ? V3{0.0, 0.0, 1.0} : V3{0.0, 0.0, -1.0}; }

}  // namespace

FaceSelection FaceSelection::parse(const Json& selection) {
    FaceSelection out;
    if (selection.is_null() || (selection.is_string() && selection.get<std::string>().empty())) return out;
    if (!selection.is_object()) throw ConfigError("A FaceSelection must be a dictionary");
    for (auto it = selection.begin(); it != selection.end(); ++it) {
        const std::string& key = it.key();
        const Json& v = it.value();
        if (key == "min_surface" || key == "max_surface") {
            if (v.is_null()) continue;
            if (!v.is_number() || v.is_boolean() || v.get<double>() < 0)
                throw ConfigError(key + " must be a positive number (m2)");
            (key == "min_surface" ? out.min_surface : out.max_surface) = v.get<double>();
        } else if (key == "orientation") {
            if (v.is_null()) continue;
            if (v.is_string()) {
                const auto s = v.get<std::string>();
                if (s != "Top" && s != "Bottom" && s != "Side")
                    throw ConfigError("orientation preset must be 'Top', 'Bottom' or 'Side'");
                out.orientation = s;
            } else if (v.is_array() && v.size() == 3) {
                V3 d{v[0].get<double>(), v[1].get<double>(), v[2].get<double>()};
                const double n = norm(d);
                if (n < 1e-12) throw ConfigError("orientation vector must be non-zero");
                out.orientation = V3{d[0] / n, d[1] / n, d[2] / n};
            } else {
                throw ConfigError("orientation must be 'Top', 'Bottom', 'Side' or a 3D vector");
            }
        } else if (key == "extreme_faces") {
            if (v.is_null()) continue;
            if (!v.is_boolean()) throw ConfigError("extreme_faces must be a boolean");
            out.extreme_faces = v.get<bool>();
        } else if (key == "materials") {
            if (v.is_null()) continue;
            if (!v.is_array()) throw ConfigError("materials must be a list of names");
            std::vector<std::string> names;
            for (const auto& n : v) {
                if (!n.is_string()) throw ConfigError("materials must be a list of names");
                names.push_back(n.get<std::string>());
            }
            out.materials = names;
        } else if (key == "interior_exterior") {
            if (!v.is_null()) throw ConfigError("interior_exterior is specified but not implemented in V1");
        } else {
            throw ConfigError("Unknown FaceSelection key '" + key + "'");
        }
    }
    return out;
}

std::vector<Triangle3> select_faces(const std::vector<double>& verts, const std::vector<int>& faces,
                                    const FaceSelection& selection, const std::vector<std::string>& material_names) {
    const size_t n = faces.size() / 3;
    std::vector<Triangle3> triangles(n);
    std::vector<V3> normals(n);
    std::vector<double> magnitudes(n);
    std::vector<char> kept(n), valid(n);
    for (size_t t = 0; t < n; ++t) {
        for (int k = 0; k < 3; ++k) {
            const size_t i = 3 * static_cast<size_t>(faces[3 * t + k]);
            triangles[t][k] = {verts[i], verts[i + 1], verts[i + 2]};
        }
        normals[t] = cross(sub(triangles[t][1], triangles[t][0]), sub(triangles[t][2], triangles[t][0]));
        magnitudes[t] = np::row_norm(normals[t]);
        valid[t] = kept[t] = magnitudes[t] > 1e-12;
        const double area = 0.5 * magnitudes[t];
        if (selection.min_surface && !(area > *selection.min_surface)) kept[t] = 0;
        if (selection.max_surface && !(area < *selection.max_surface)) kept[t] = 0;
    }
    auto unit = [&](size_t t) {
        return valid[t] ? V3{normals[t][0] / magnitudes[t], normals[t][1] / magnitudes[t], normals[t][2] / magnitudes[t]}
                        : V3{0.0, 0.0, 0.0};
    };
    std::optional<V3> direction;
    bool side = false;
    if (const auto* s = std::get_if<std::string>(&selection.orientation)) {
        if (*s == "Side") side = true;
        else direction = preset(*s);
    } else if (const auto* d = std::get_if<V3>(&selection.orientation)) {
        direction = *d;
    }
    if (direction) {
        for (size_t t = 0; t < n; ++t)
            if (!(np::matvec(unit(t), *direction) > kAlignmentCosine)) kept[t] = 0;
    }
    if (side) {
        for (size_t t = 0; t < n; ++t)
            if (!(std::abs(unit(t)[2]) <= kAlignmentCosine)) kept[t] = 0;
    }
    if (selection.extreme_faces && direction) {
        // clash_utils.extreme_triangles(direction, 0.001, FACE_ALIGNMENT_COSINE)
        const V3 dir = [&] {
            const double m = norm(*direction);
            return V3{(*direction)[0] / m, (*direction)[1] / m, (*direction)[2] / m};
        }();
        std::vector<size_t> candidates;
        for (size_t t = 0; t < n; ++t)
            if (np::matvec(unit(t), dir) > kAlignmentCosine && valid[t]) candidates.push_back(t);
        std::set<std::array<V3, 3>> extreme;
        if (!candidates.empty()) {
            std::vector<double> projections;
            for (size_t t : candidates) {
                const auto& tr = triangles[t];
                const V3 mean{(tr[0][0] + tr[1][0] + tr[2][0]) / 3.0, (tr[0][1] + tr[1][1] + tr[2][1]) / 3.0,
                              (tr[0][2] + tr[1][2] + tr[2][2]) / 3.0};
                projections.push_back(np::matvec(mean, dir));
            }
            const double top = *std::max_element(projections.begin(), projections.end());
            for (size_t k = 0; k < candidates.size(); ++k)
                if (projections[k] >= top - kExtremeTolerance) extreme.insert(triangles[candidates[k]]);
        }
        for (size_t t = 0; t < n; ++t)
            if (!extreme.count(triangles[t])) kept[t] = 0;
    }
    if (selection.materials && !selection.materials->empty()) {
        bool match = false;
        for (const auto& m : material_names)
            match = match || std::find(selection.materials->begin(), selection.materials->end(), m) !=
                                 selection.materials->end();
        if (!match) std::fill(kept.begin(), kept.end(), 0);
    }
    std::vector<Triangle3> out;
    for (size_t t = 0; t < n; ++t)
        if (kept[t]) out.push_back(triangles[t]);
    return out;
}

std::pair<V3, double> triangle_data(const Triangle3& t) {
    V3 normal = cross(sub(t[1], t[0]), sub(t[2], t[0]));
    const double magnitude = norm(normal);
    if (magnitude > 1e-12) normal = {normal[0] / magnitude, normal[1] / magnitude, normal[2] / magnitude};
    return {normal, 0.5 * magnitude};
}

std::array<V3, 3> triangle_key(const Triangle3& t) {
    std::array<V3, 3> k = t;
    std::sort(k.begin(), k.end());
    return k;
}

bool triangles_share_geometry(const Triangle3& a, const Triangle3& b) {
    for (const auto& p : a)
        for (const auto& q : b)
            if (p == q) return true;
    return false;
}

namespace {

bool segment_crosses_triangle_strictly(const V3& p0, const V3& p1, const Triangle3& tri) {
    const V3 direction = sub(p1, p0);
    const V3 e1 = sub(tri[1], tri[0]), e2 = sub(tri[2], tri[0]);
    const V3 pvec = cross(direction, e2);
    const double det = dot(e1, pvec);
    if (std::abs(det) < 1e-14) return false;
    const double inv = 1.0 / det;
    const V3 tvec = sub(p0, tri[0]);
    const double u = inv * dot(tvec, pvec);
    if (!(0.0 < u && u < 1.0)) return false;
    const V3 qvec = cross(tvec, e1);
    const double v = inv * dot(direction, qvec);
    if (!(0.0 < v && v < 1.0)) return false;
    const double t = inv * dot(e2, qvec);
    return 0.0 < t && t < 1.0;
}

TopoDS_Shape triangle_face(const Triangle3& t) {
    BRepBuilderAPI_MakePolygon polygon;
    for (const auto& p : t) polygon.Add(gp_Pnt(p[0], p[1], p[2]));
    polygon.Close();
    if (!polygon.IsDone()) return {};
    BRepBuilderAPI_MakeFace face(polygon.Wire());
    if (!face.IsDone()) return {};
    return face.Face();
}

}  // namespace

bool triangles_cross_properly(const Triangle3& a, const Triangle3& b) {
    for (int i = 0; i < 3; ++i) {
        if (segment_crosses_triangle_strictly(a[i], a[(i + 1) % 3], b)) return true;
        if (segment_crosses_triangle_strictly(b[i], b[(i + 1) % 3], a)) return true;
    }
    return false;
}

double triangle_penetration_depth(const Triangle3& a, const Triangle3& b) {
    double depth = 0.0;
    for (const auto* pair : {&a, &b}) {
        const Triangle3& tri = *pair;
        const Triangle3& other = pair == &a ? b : a;
        V3 normal = cross(sub(other[1], other[0]), sub(other[2], other[0]));
        const double n = norm(normal);
        if (n < 1e-12) continue;
        normal = {normal[0] / n, normal[1] / n, normal[2] / n};
        for (const auto& v : tri) depth = std::max(depth, std::abs(dot(sub(v, other[0]), normal)));
    }
    return depth;
}

double distance_between_triangles(const Triangle3& a, const Triangle3& b) {
    const TopoDS_Shape fa = triangle_face(a), fb = triangle_face(b);
    if (fa.IsNull() || fb.IsNull()) return std::numeric_limits<double>::infinity();
    return shape_distance(fa, fb);
}

double triangles_bbox_distance(const Triangle3& a, const Triangle3& b) {
    V3 delta;
    for (int k = 0; k < 3; ++k) {
        const double amin = std::min({a[0][k], a[1][k], a[2][k]}), amax = std::max({a[0][k], a[1][k], a[2][k]});
        const double bmin = std::min({b[0][k], b[1][k], b[2][k]}), bmax = std::max({b[0][k], b[1][k], b[2][k]});
        delta[k] = std::max(std::max(amin - bmax, bmin - amax), 0.0);
    }
    return norm(delta);
}

std::pair<V3, V3> triangles_bounds(const std::vector<Triangle3>& triangles) {
    V3 lo{std::numeric_limits<double>::infinity(), std::numeric_limits<double>::infinity(),
          std::numeric_limits<double>::infinity()};
    V3 hi{-lo[0], -lo[1], -lo[2]};
    for (const auto& t : triangles)
        for (const auto& p : t)
            for (int k = 0; k < 3; ++k) {
                lo[k] = std::min(lo[k], p[k]);
                hi[k] = std::max(hi[k], p[k]);
            }
    return {lo, hi};
}

std::vector<FaceFailure> run_face_checks(const Triangle3& a, const Triangle3& b, const FaceChecks& c) {
    std::vector<FaceFailure> failures;
    if (c.distance) {
        if (c.max_distance && triangles_bbox_distance(a, b) > *c.max_distance) {
            // a search radius: farther pairs are not checked
        } else if (c.two_objects && c.min_distance && triangles_bbox_distance(a, b) >= *c.min_distance) {
            // TwoObjectsFace: the exact distance is at least the bbox one
        } else {
            const bool adjacent = !c.two_objects && triangles_share_geometry(a, b);
            if (!(c.skip_adjacent && adjacent)) {
                const double measured = distance_between_triangles(a, b);
                if (c.min_distance && measured < *c.min_distance) failures.push_back({Measure::Distance, measured});
            }
        }
    }
    if (c.intersection && triangles_cross_properly(a, b)) {
        const double depth = triangle_penetration_depth(a, b);
        if (depth > c.intersection_tolerance) failures.push_back({Measure::PenetrationDepth, depth});
    }
    if (c.orientation) {
        const V3 na = triangle_data(a).first, nb = triangle_data(b).first;
        const double d = std::min(1.0, std::max(-1.0, dot(na, nb)));
        const double measured = std::acos(d) * (180.0 / M_PI);
        if (std::abs(measured - *c.angle) > c.angle_tolerance) failures.push_back({Measure::Angle, measured});
    }
    return failures;
}

FaceData face_rule_data(const Triangle3& t) {
    const auto [normal, area] = triangle_data(t);
    FaceData f;
    f.normal = normal;
    f.area = area;
    f.triangles.push_back(t);
    return f;
}

}  // namespace ifcclash::geometry
