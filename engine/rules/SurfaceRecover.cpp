// SurfaceRecover of Rules.py: the contact area between the facing extreme
// faces of two elements (a coating, a slab on a beam), against a covering
// interval. The 2D polygon work goes through GEOS, as shapely does.
#include "AllRules.h"
#include "SurfaceRecover.h"

#include "../geometry/Faces.h"
#include "../geometry/Geos.h"
#include "../geometry/Numpy.h"
#include "../geometry/Obb.h"

#include <BRepExtrema_DistShapeShape.hxx>
#include <gp_Vec.hxx>

#include <cmath>
#include <limits>

namespace ifcclash {

namespace {

using V3 = std::array<double, 3>;
V3 sub(const V3& a, const V3& b) { return {a[0] - b[0], a[1] - b[1], a[2] - b[2]}; }
V3 neg(const V3& a) { return {-a[0], -a[1], -a[2]}; }
V3 cross(const V3& a, const V3& b) {
    return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
}
// numpy forms: 1-D a @ b and norm; matrix rows go through np::matvec / row_norm
double dot(const V3& a, const V3& b) { return geometry::np::dot(a, b); }
double norm(const V3& a) { return geometry::np::norm(a); }
V3 unit(const V3& a) {
    const double n = norm(a);
    return {a[0] / n, a[1] / n, a[2] / n};
}
V3 mean3(const Triangle3& t) {
    return {(t[0][0] + t[1][0] + t[2][0]) / 3.0, (t[0][1] + t[1][1] + t[2][1]) / 3.0, (t[0][2] + t[1][2] + t[2][2]) / 3.0};
}

const double kPairingCosine = -std::cos(25.0 * M_PI / 180.0);
const double kAlignedCosine = std::cos(45.0 * M_PI / 180.0);

// clash_utils.extreme_triangles
std::vector<Triangle3> extreme_triangles(const std::vector<double>& verts, const std::vector<int>& faces, V3 direction,
                                         double tolerance, double alignment) {
    direction = unit(direction);
    std::vector<Triangle3> triangles;
    std::vector<double> projections;
    for (size_t t = 0; 3 * t + 2 < faces.size(); ++t) {
        Triangle3 tr;
        for (int k = 0; k < 3; ++k) {
            const size_t i = 3 * static_cast<size_t>(faces[3 * t + k]);
            tr[k] = {verts[i], verts[i + 1], verts[i + 2]};
        }
        const V3 n = cross(sub(tr[1], tr[0]), sub(tr[2], tr[0]));
        const double m = geometry::np::row_norm(n);
        if (!(m > 1e-12)) continue;
        if (!(geometry::np::matvec(V3{n[0] / m, n[1] / m, n[2] / m}, direction) > alignment)) continue;
        triangles.push_back(tr);
        projections.push_back(geometry::np::matvec(mean3(tr), direction));
    }
    if (triangles.empty()) return {};
    const double top = *std::max_element(projections.begin(), projections.end());
    std::vector<Triangle3> out;
    for (size_t k = 0; k < triangles.size(); ++k)
        if (projections[k] >= top - tolerance) out.push_back(triangles[k]);
    return out;
}

// clash_utils.triangles_projected_area
double projected_area(const std::vector<Triangle3>& triangles, V3 direction) {
    if (triangles.empty()) return 0.0;
    direction = unit(direction);
    double total = 0.0;
    for (const auto& t : triangles)
        total += 0.5 * std::abs(geometry::np::matvec(cross(sub(t[1], t[0]), sub(t[2], t[0])), direction));
    return total;
}

// clash_utils._plane_basis
std::pair<V3, V3> plane_basis(const V3& d) {
    V3 helper{1.0, 0.0, 0.0};
    if (std::abs(dot(d, helper)) > 0.9) helper = {0.0, 1.0, 0.0};
    const V3 u = unit(cross(d, helper));
    return {u, cross(d, u)};
}

// clash_utils.contact_polygons_between_triangle_sets
std::pair<double, std::vector<Triangle3>> contact_polygons(const std::vector<Triangle3>& a, const std::vector<Triangle3>& b,
                                                           V3 direction, double tolerance, double pairing,
                                                           const geometry::Geos& geos) {
    std::vector<Triangle3> contact;
    if (a.empty() || b.empty()) return {0.0, contact};
    direction = unit(direction);
    const auto [u, v] = plane_basis(direction);
    auto normals = [](const std::vector<Triangle3>& ts, std::vector<V3>& n, std::vector<double>& m) {
        for (const auto& t : ts) {
            n.push_back(cross(sub(t[1], t[0]), sub(t[2], t[0])));
            m.push_back(geometry::np::row_norm(n.back()));
        }
    };
    std::vector<V3> na, nb;
    std::vector<double> ma, mb;
    normals(a, na, ma);
    normals(b, nb, mb);
    std::vector<double> pa, pb;
    for (const auto& t : a) pa.push_back(geometry::np::matvec(mean3(t), direction));
    for (const auto& t : b) pb.push_back(geometry::np::matvec(mean3(t), direction));
    auto to_2d = [&](const Triangle3& t) {
        std::vector<std::array<double, 3>> pts;
        for (const auto& p : t) pts.push_back({dot(p, u), dot(p, v), 0.0});
        return geos.polygon(pts, 2);
    };
    double total = 0.0;
    for (size_t i = 0; i < a.size(); ++i) {
        if (ma[i] < 1e-12) continue;
        auto poly_a = to_2d(a[i]);
        if (geos.is_empty(poly_a)) continue;
        for (size_t j = 0; j < b.size(); ++j) {
            if (mb[j] < 1e-12) continue;
            const V3 ua{na[i][0] / ma[i], na[i][1] / ma[i], na[i][2] / ma[i]};
            const V3 ub{nb[j][0] / mb[j], nb[j][1] / mb[j], nb[j][2] / mb[j]};
            if (dot(ua, ub) > pairing) continue;
            if (std::abs(pa[i] - pb[j]) > tolerance) continue;
            auto poly_b = to_2d(b[j]);
            if (geos.is_empty(poly_b)) continue;
            auto inter = geos.intersection(poly_a, poly_b);
            if (geos.is_empty(inter)) continue;
            const double area = geos.area(inter);
            total += area;
            if (area <= 1e-12) continue;
            const double height = 0.5 * (pa[i] + pb[j]);
            for (const auto& ring : geos.exterior_rings(inter)) {  // _fan_triangulation
                for (size_t k = 1; k + 2 < ring.size() + 0 && k < ring.size() - 2; ++k) {
                    const auto& p0 = ring[0];
                    const auto& p1 = ring[k];
                    const auto& p2 = ring[k + 1];
                    const double v1x = p1[0] - p0[0], v1y = p1[1] - p0[1];
                    const double v2x = p2[0] - p0[0], v2y = p2[1] - p0[1];
                    if (std::abs(v1x * v2y - v1y * v2x) <= 1e-12) continue;
                    Triangle3 t;
                    const std::array<double, 2>* pts[3] = {&p0, &p1, &p2};
                    for (int c = 0; c < 3; ++c) {
                        const auto& q = *pts[c];
                        for (int k3 = 0; k3 < 3; ++k3) t[c][k3] = q[0] * u[k3] + q[1] * v[k3] + height * direction[k3];
                    }
                    contact.push_back(t);
                }
            }
        }
    }
    return {total, contact};
}

// Custom_OBB.min_distance_to_obb (the min of the separating gaps, 0 when no
// axis separates).
double obb_min_distance(const Bnd_OBB& a, const Bnd_OBB& b) {
    auto project = [](const Bnd_OBB& o, const gp_Vec& axis) {
        const gp_XYZ c = o.Center();
        const double cp = c.X() * axis.X() + c.Y() * axis.Y() + c.Z() * axis.Z();
        const double r = o.XHSize() * std::abs(axis.Dot(gp_Vec(o.XDirection()))) +
                         o.YHSize() * std::abs(axis.Dot(gp_Vec(o.YDirection()))) +
                         o.ZHSize() * std::abs(axis.Dot(gp_Vec(o.ZDirection())));
        return std::make_pair(cp - r, cp + r);
    };
    auto gap = [&](const gp_Vec& axis) {
        const auto s = project(a, axis), o = project(b, axis);
        if (s.second < o.first) return o.first - s.second;
        if (o.second < s.first) return s.first - o.second;
        return -std::numeric_limits<double>::infinity();
    };
    const gp_Vec sa[3] = {gp_Vec(a.XDirection()), gp_Vec(a.YDirection()), gp_Vec(a.ZDirection())};
    const gp_Vec oa[3] = {gp_Vec(b.XDirection()), gp_Vec(b.YDirection()), gp_Vec(b.ZDirection())};
    double best = std::numeric_limits<double>::infinity();
    bool overlap = false;
    auto consider = [&](const gp_Vec& axis) {
        const double d = gap(axis);
        if (d > 0) best = std::min(best, d);
        else overlap = true;
    };
    for (const auto& x : sa) consider(x);
    for (const auto& x : oa) consider(x);
    for (const auto& x : sa)
        for (const auto& y : oa) {
            gp_Vec c = x.Crossed(y);
            if (c.Magnitude() > 1e-6) {
                c.Normalize();
                consider(c);
            }
        }
    if (overlap && best == std::numeric_limits<double>::infinity()) return 0.0;
    return std::max(0.0, best);
}


std::optional<Covering> parse_covering(const Json& v, const char* name) {
    if (v.is_null()) return std::nullopt;
    if (v.is_number() && !v.is_boolean()) return Covering{false, v.get<double>()};
    if (v.is_string()) {
        const auto s = v.get<std::string>();
        if (!s.empty() && s.back() == '%') {
            try {
                return Covering{true, std::stod(s.substr(0, s.size() - 1))};
            } catch (const std::exception&) {
            }
        }
    }
    // The parsed form of the Python rule attribute: ("absolute" | "relative", value)
    if (v.is_array() && v.size() == 2 && v[0].is_string() && v[1].is_number()) {
        const auto kind = v[0].get<std::string>();
        if (kind == "absolute" || kind == "relative") return Covering{kind == "relative", v[1].get<double>()};
    }
    throw ConfigError(std::string(name) + " must be a number (m2) or a string ending with '%'");
}

}  // namespace

void SurfaceRecover::setup() {
    const auto& d = params().direction;
    if (d.is_string() && d.get<std::string>() == "Auto") {
        auto_ = true;
    } else if (d.is_string() && d.get<std::string>() == "Top") {
        direction_ = {0.0, 0.0, 1.0};
    } else if (d.is_string() && d.get<std::string>() == "Bottom") {
        direction_ = {0.0, 0.0, -1.0};
    } else if (d.is_array() && d.size() == 3 && d[0].is_number() && d[1].is_number() && d[2].is_number()) {
        V3 v{d[0].get<double>(), d[1].get<double>(), d[2].get<double>()};
        const double n = norm(v);
        if (!(n > 1e-12)) throw ConfigError("direction must be 'Auto', 'Top', 'Bottom' or a 3D vector");
        // The Python rule normalizes once (its attribute, already unit
        // when it comes from it).
        direction_ = std::abs(n - 1.0) > 1e-12 ? V3{v[0] / n, v[1] / n, v[2] / n} : v;
    } else {
        throw ConfigError("direction must be 'Auto', 'Top', 'Bottom' or a 3D vector");
    }
    if (params().reference != "Source" && params().reference != "Target")
        throw ConfigError("reference must be 'Source' or 'Target'");
    if (params().tolerance < 0) throw ConfigError("tolerance must be a positive number");
    min_ = parse_covering(params().min_covering, "min_covering");
    max_ = parse_covering(params().max_covering, "max_covering");
}


std::shared_ptr<const void> SurfaceRecover::element_data(const ElementGeometry& e, Role) const {
    const auto brep = e.meshed_brep();
    const auto mesh = e.mesh(Variant::MeshWorld);
    if (!brep || !mesh || mesh->faces.empty()) return nullptr;
    auto data = std::make_shared<RecoverData>();
    data->occ = brep->shape;
    data->obb = brep->obb;
    data->box = geometry::obb_aabb(data->obb);
    data->verts = mesh->local_verts;
    data->faces = mesh->faces;
    V3 sum{0, 0, 0};
    const size_t n = data->verts.size() / 3;
    for (size_t i = 0; i < n; ++i)
        for (int k = 0; k < 3; ++k) sum[k] += data->verts[3 * i + k];
    data->centroid = {sum[0] / n, sum[1] / n, sum[2] / n};
    return data;
}


// The OBB contains the meshed B-Rep; the exact shape stays within the
// 0.01 mesh deflection of it: the tolerance plus that margin keeps every
// pair the Python prefilters keep.
Bnd_Box SurfaceRecover::broad_volume(const ElementGeometry& e, Role role) const {
    return geometry::inflate(e.as<RecoverData>().box, (role == Role::Source ? params().tolerance : 0.0) + 0.02);
}


Verdict SurfaceRecover::narrow_test(const ElementGeometry& source, const ElementGeometry& target) const {
    const auto& s = source.as<RecoverData>();
    const auto& t = target.as<RecoverData>();
    const double tolerance = params().tolerance;
    Verdict verdict;
    if (obb_min_distance(s.obb, t.obb) > tolerance) return verdict;
    std::optional<V3> ps, pt;
    const double distance = skin_distance(s, t, ps, pt);
    if (distance > tolerance) return verdict;

    std::optional<V3> pair_direction;
    if (auto_) {
        if (ps && pt) {
            const V3 vec{(*pt)[0] - (*ps)[0], (*pt)[1] - (*ps)[1], (*pt)[2] - (*ps)[2]};
            const double n = norm(vec);
            if (!(n < 1e-9)) pair_direction = V3{vec[0] / n, vec[1] / n, vec[2] / n};
        }
        if (!pair_direction) {
            const V3 vec = sub(t.centroid, s.centroid);
            const double n = norm(vec);
            if (!(n < 1e-9)) pair_direction = V3{vec[0] / n, vec[1] / n, vec[2] / n};
        }
        if (!pair_direction) return verdict;
    } else {
        pair_direction = direction_;
    }
    const V3 dir = *pair_direction;
    const auto st = extreme_triangles(s.verts, s.faces, dir, tolerance, kAlignedCosine);
    const auto tt = extreme_triangles(t.verts, t.faces, neg(dir), tolerance, kAlignedCosine);
    if (st.empty() || tt.empty()) return verdict;
    double smax = -std::numeric_limits<double>::infinity(), tmin = std::numeric_limits<double>::infinity();
    for (const auto& tr : st) smax = std::max(smax, geometry::np::matvec(mean3(tr), dir));
    for (const auto& tr : tt) tmin = std::min(tmin, geometry::np::matvec(mean3(tr), dir));
    if (std::abs(smax - tmin) > tolerance) return verdict;

    geometry::Geos geos;
    const auto [contact_area, contact] = contact_polygons(st, tt, dir, tolerance, kPairingCosine, geos);
    const double reference_area = projected_area(params().reference == "Source" ? st : tt, dir);
    std::optional<double> ratio;
    if (reference_area > 1e-12) ratio = 100.0 * contact_area / reference_area;

    // clash_utils.covering_out_of_bounds
    bool out = false;
    for (const auto& [bound, lower] : {std::make_pair(min_, true), std::make_pair(max_, false)}) {
        if (!bound || out) continue;
        if (bound->relative && !ratio) {
            out = true;
            continue;
        }
        const double value = bound->relative ? *ratio : contact_area;
        if (lower && value < bound->value) out = true;
        if (!lower && value > bound->value) out = true;
    }
    if (!out) return verdict;

    verdict.status = true;
    verdict.measures.set(Measure::ContactArea, contact_area);
    if (ratio) verdict.measures.set(Measure::Ratio, *ratio / 100.0);
    verdict.measures.set(Measure::Distance, distance);
    FaceData fs, ft;
    fs.normal = dir;
    fs.area = projected_area(st, dir);
    fs.triangles = contact;
    ft.normal = neg(dir);
    ft.area = projected_area(tt, neg(dir));
    ft.triangles = contact;
    verdict.faces.push_back({fs, ft});
    return verdict;
}

double SurfaceRecover::skin_distance(const RecoverData& s, const RecoverData& t, std::optional<V3>& ps,
                                    std::optional<V3>& pt) const {
    BRepExtrema_DistShapeShape dist;
    dist.LoadS1(s.occ);
    dist.LoadS2(t.occ);
    dist.Perform();
    if (dist.NbSolution() >= 1) {
        const gp_Pnt a = dist.PointOnShape1(1), b = dist.PointOnShape2(1);
        ps = V3{a.X(), a.Y(), a.Z()};
        pt = V3{b.X(), b.Y(), b.Z()};
    }
    return dist.Value();
}


RuleSpec spec_surface_recover() {
    return RuleSpec::pair<SurfaceRecover>(
        "SurfaceRecover", "Surface Recover", {Slot::Source, Slot::Target},
        "Checks that the target surface is covered by the source (ex. a coating).",
        {param(&SurfaceRecoverParams::direction, "direction").doc("Recovery direction: Auto, Top, Bottom or a vector"),
         param(&SurfaceRecoverParams::reference, "reference").doc("Reference surface").values({"Source", "Target"}),
         param(&SurfaceRecoverParams::tolerance, "tolerance").doc("Tolerance").unit(Unit::Metre),
         param(&SurfaceRecoverParams::min_covering, "min_covering").doc("Minimum covering: an area (m2) or a percentage ('50%')"),
         param(&SurfaceRecoverParams::max_covering, "max_covering").doc("Maximum covering: an area (m2) or a percentage ('50%')")});
}

}  // namespace ifcclash
