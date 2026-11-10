// IfcClash_Plus engine — the directional _triang rules (engine/triang/rules):
// Above, Below (seen triangles) and OBB_Above, OBB_Below, OBB_Front_And_Back,
// OBB_Custom (detection zones built from the OBB of the source).
//
// Same parameters and same result blocks as the original rules, plus one
// contact tolerance each: the triangles are a tessellation (the .ifcview is
// also quantized to ~0.1 mm), so a contact cannot be an exact 0.
//
//  - Above_triang / Below_triang: the target sits above (below) the source
//    when, somewhere in plan, a source triangle seen from the source side and
//    a target triangle seen from the target side overlap with a vertical gap
//    in [0, tolerance] (target - source for Above, source - target for
//    Below). "Seen" is a covering test, not the winding (many IFC meshes are
//    wound inwards): the sampled test under 200 triangles, the height map
//    above (visible_triangles_auto). The gap is linear over the plan overlap
//    of two triangles: the region where it lies in [0, tolerance] is a
//    convex polygon, exact over the whole overlap (the original looks only
//    at the closest points of the faces, then casts one ray). A triangle may
//    be seen only in part: the point kept must be seen on both sides
//    (point_covered), tried from the smallest gap.
//    Prefilter of the original: the band extruded above (below) the source
//    OBB must meet the target OBB.
//  - OBB_*_triang: a target triangle meets a detection zone of the source
//    (separating axes, exact), one verdict per zone met. The zones are those
//    of the original rules, built on the OBB of the triangles.
#include "Common.h"

#include "../../registry/RuleSpec.h"
#include "../kernels/TriangleTests.h"
#include "../surface/Visibility.h"

#include <cmath>
#include <limits>
#include <optional>

namespace ifcclash {

namespace {

using namespace triang;

const std::vector<std::string> kAboveTypes{"Above_MinToMax", "Above_MinToMin", "Above_MaxToMin", "Above_MaxToMax"};
const std::vector<std::string> kBelowTypes{"Below_MinToMax", "Below_MinToMin", "Below_MaxToMin", "Below_MaxToMax"};

// ================================================================ Above / Below

// plan_tolerance, m: two faces count as superposed when they overlap in plan
// or are within this horizontal distance (the original aligns its points to
// 1e-3). Negative: they must overlap by that much (robustness checks).
struct AboveTriangParams {
    std::string above_type = "Above_MaxToMax";
    double tolerance = 0.1;  // m
    double plan_tolerance = 0.001;
    const std::string& type() const { return above_type; }
};
struct BelowTriangParams {
    std::string below_type = "Below_MaxToMax";
    double tolerance = 0.1;  // m
    double plan_tolerance = 0.001;
    const std::string& type() const { return below_type; }
};

// Rules.above_below_directions: the side looked at, +1 (up, Max) or -1
// (down, Min). "MinTo" / "ToMin" read the same in the Below types.
double side_of(const std::string& type, Role role) {
    if (role == Role::Source) return type.find("MinTo") != std::string::npos ? -1.0 : 1.0;
    return type.find("ToMin") != std::string::npos ? -1.0 : 1.0;
}

struct ExtremTriangles {
    std::shared_ptr<const TriMesh> mesh;
    Bnd_OBB obb;
    Bnd_OBB zone;                           // sources: the band above (below) the OBB
    std::shared_ptr<const std::vector<int>> triangles;  // seen from the side
    std::vector<Bnd_Box> boxes;             // their boxes
    std::unique_ptr<BoxTree> tree;          // targets: on the boxes
};

// The height of the plane of a triangle above (x, y).
double plane_z(const P3& a, const P3& n, double x, double y) {
    return a[2] - (n[0] * (x - a[0]) + n[1] * (y - a[1])) / n[2];
}

struct GapHit {
    double distance;
    P3 lower;  // on the lower triangle
    P3 upper;  // on the upper triangle
};

// The candidate points of a pair of triangles, smallest gap first: where the
// two overlap in plan (the upper one grown by plan_tolerance) and the
// vertical gap upper - lower lies in [0, tolerance]. The gap is linear over
// the overlap: that region is the overlap polygon clipped by the lines
// gap = 0 and gap = tolerance, a convex polygon. Candidates: its vertices
// pulled toward its centroid by 1 mm at most (off the edges, where the
// covering tests are ambiguous), then its centroid.
std::vector<GapHit> gap_candidates(const P3& a, const P3& b, const P3& c, const P3& d, const P3& e, const P3& f,
                                   double tolerance, double plan_tolerance) {
    constexpr double eps = 1e-9;
    auto poly = clip_triangles_xy(a, b, c, d, e, f, plan_tolerance);
    if (poly.empty()) return {};
    const P3 nl{(b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]),
                (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]),
                (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])};
    const P3 nu{(e[1] - d[1]) * (f[2] - d[2]) - (e[2] - d[2]) * (f[1] - d[1]),
                (e[2] - d[2]) * (f[0] - d[0]) - (e[0] - d[0]) * (f[2] - d[2]),
                (e[0] - d[0]) * (f[1] - d[1]) - (e[1] - d[1]) * (f[0] - d[0])};
    if (nl[2] == 0.0 || nu[2] == 0.0) return {};  // vertical: no plan area
    auto zl = [&](double x, double y) { return plane_z(a, nl, x, y); };
    auto zu = [&](double x, double y) { return plane_z(d, nu, x, y); };
    auto gap = [&](const P2& p) { return zu(p[0], p[1]) - zl(p[0], p[1]); };
    // Clip by gap >= 0 and gap <= tolerance (Sutherland-Hodgman on a linear
    // function).
    auto clip = [&](const std::vector<P2>& in, auto&& value) {
        std::vector<P2> out;
        for (size_t i = 0; i < in.size(); ++i) {
            const P2& cur = in[i];
            const P2& prev = in[(i + in.size() - 1) % in.size()];
            const double vc = value(cur), vp = value(prev);
            if (vc >= -eps) {
                if (vp < -eps) {
                    const double t = vp / (vp - vc);
                    out.push_back({prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])});
                }
                out.push_back(cur);
            } else if (vp >= -eps) {
                const double t = vp / (vp - vc);
                out.push_back({prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1])});
            }
        }
        return out;
    };
    poly = clip(poly, [&](const P2& p) { return gap(p); });
    if (poly.empty()) return {};
    poly = clip(poly, [&](const P2& p) { return tolerance - gap(p); });
    if (poly.empty()) return {};
    P2 g{0, 0};
    for (const P2& p : poly) g = {g[0] + p[0], g[1] + p[1]};
    g = {g[0] / double(poly.size()), g[1] / double(poly.size())};
    std::vector<GapHit> out;
    auto add = [&](const P2& p) {
        out.push_back({std::max(0.0, gap(p)), {p[0], p[1], zl(p[0], p[1])}, {p[0], p[1], zu(p[0], p[1])}});
    };
    for (const P2& p : poly) {
        const double len = std::hypot(g[0] - p[0], g[1] - p[1]);
        const double t = len > 0 ? std::min(0.01, 1e-3 / len) : 0.0;
        add({p[0] + t * (g[0] - p[0]), p[1] + t * (g[1] - p[1])});
    }
    add(g);
    std::stable_sort(out.begin(), out.end(), [](const GapHit& x, const GapHit& y) { return x.distance < y.distance; });
    return out;
}

template <class Params>
class ExtremTriang : public TriPairRule<Params> {
public:
    explicit ExtremTriang(bool above) : above_(above) {}
    bool skip_self() const override { return false; }  // as the original (N x M loops)

    void setup() override {
        if (this->params().tolerance < 0) throw ConfigError("tolerance must be a positive number (m)");
    }

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override {
        auto mesh = tri_mesh(e);
        const auto obb = tri_obb(e);
        if (!mesh || !obb) return nullptr;
        auto data = std::make_shared<ExtremTriangles>();
        data->mesh = mesh;
        data->obb = *obb;
        if (role == Role::Source)
            data->zone = geometry::detach_by_extrude(*obb, {this->params().tolerance, false}, above_);
        data->triangles = seen_triangles(e, side_of(this->params().type(), role));
        if (!data->triangles) return nullptr;
        for (int t : *data->triangles) data->boxes.push_back(mesh->box(size_t(t)));
        if (role == Role::Target) data->tree = std::make_unique<BoxTree>(data->boxes);
        return data;
    }

    // The band grown by the plan tolerance: an object touching it in plan
    // (a space bounded by the face of a wall) stays a candidate.
    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override {
        const auto& d = e.as<ExtremTriangles>();
        return geometry::inflate(geometry::obb_aabb(role == Role::Source ? d.zone : d.obb),
                                 kFloatMargin + (role == Role::Source ? reach() : 0.0));
    }
    Bnd_OBB mid_volume(const ElementGeometry& e, Role role) const override {
        const auto& d = e.as<ExtremTriangles>();
        return role == Role::Source ? geometry::inflate(d.zone, reach()) : d.obb;
    }
    Candidate mid_test(const Bnd_OBB& zone, const Bnd_OBB& target) const override {
        return zone.IsOut(target) ? Candidate::Rejected : Candidate::Kept;
    }

    Verdict narrow_test(const ElementGeometry& source, const ElementGeometry& target) const override {
        const auto& s = source.as<ExtremTriangles>();
        const auto& t = target.as<ExtremTriangles>();
        // The prefilter of the original is part of the rule (grown by the
        // plan tolerance, as the face test).
        if (geometry::inflate(s.zone, reach()).IsOut(t.obb) || !t.tree) return {};
        const double tol = this->params().tolerance;
        const double grow = this->params().plan_tolerance;
        const double side_s = side_of(this->params().type(), Role::Source);
        const double side_t = side_of(this->params().type(), Role::Target);
        std::optional<GapHit> hit;
        int hit_s = -1, hit_t = -1;
        for (size_t k = 0; k < s.triangles->size() && !hit; ++k) {
            const int ts = (*s.triangles)[k];
            P3 a, b, c;
            s.mesh->corners(size_t(ts), a, b, c);
            double x0, y0, z0, x1, y1, z1;
            s.boxes[k].Get(x0, y0, z0, x1, y1, z1);
            Bnd_Box query;  // a target triangle from 0 to tol above (below) this one
            if (above_) query.Update(x0 - reach(), y0 - reach(), z0, x1 + reach(), y1 + reach(), z1 + tol);
            else query.Update(x0 - reach(), y0 - reach(), z0 - tol, x1 + reach(), y1 + reach(), z1);
            t.tree->query(query, [&](int j) {
                const int tt = (*t.triangles)[size_t(j)];
                P3 d, e, f;
                t.mesh->corners(size_t(tt), d, e, f);
                // Above: the target is the upper triangle; Below: the source.
                const auto candidates =
                    above_ ? gap_candidates(a, b, c, d, e, f, tol, grow) : gap_candidates(d, e, f, a, b, c, tol, grow);
                for (const GapHit& g : candidates) {
                    // A point really seen on both sides: the triangles may be
                    // seen only in part.
                    const P3& ps = above_ ? g.lower : g.upper;
                    const P3& pt = above_ ? g.upper : g.lower;
                    if (point_covered(*s.mesh, size_t(ts), ps[0], ps[1], ps[2], side_s)) continue;
                    if (point_covered(*t.mesh, size_t(tt), pt[0], pt[1], pt[2], side_t)) continue;
                    hit = g;
                    hit_s = ts;
                    hit_t = tt;
                    return false;
                }
                return true;
            });
        }
        if (!hit) return {};
        const P3& ps = above_ ? hit->lower : hit->upper;
        const P3& pt = above_ ? hit->upper : hit->lower;
        Verdict v;
        v.status = true;
        v.measures.set(Measure::Distance, hit->distance);
        v.points.push_back({point(ps), point(pt), std::string(above_ ? "above" : "below")});
        auto face = [](const TriMesh& m, int tri) {
            P3 a, b, c;
            m.corners(size_t(tri), a, b, c);
            return geometry::triangle_face_data({a[0], a[1], a[2]}, {b[0], b[1], b[2]}, {c[0], c[1], c[2]});
        };
        v.faces.push_back({face(*s.mesh, hit_s), face(*t.mesh, hit_t)});
        v.source_obbs.push_back(geometry::obb_data(s.obb, std::string("object")));
        v.source_obbs.push_back(geometry::obb_data(s.zone, std::string("zone")));
        v.target_obbs.push_back(geometry::obb_data(t.obb, std::string("object")));
        return v;
    }

private:
    double reach() const { return std::max(this->params().plan_tolerance, 0.0); }
    bool above_;
};

class AboveTriang final : public ExtremTriang<AboveTriangParams> {
public:
    AboveTriang() : ExtremTriang<AboveTriangParams>(true) {}
};
class BelowTriang final : public ExtremTriang<BelowTriangParams> {
public:
    BelowTriang() : ExtremTriang<BelowTriangParams>(false) {}
};

// ================================================================ OBB zone rules

struct ZoneTriangles {
    std::shared_ptr<const TriMesh> mesh;
    Bnd_OBB obb;                 // the object
    std::vector<Bnd_OBB> zones;  // sources only
};

template <class Params>
class ZoneTriang : public TriPairRule<Params> {
public:
    bool skip_self() const override { return false; }  // as the original (N x M loops)

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override {
        auto mesh = tri_mesh(e);
        const auto obb = tri_obb(e);
        if (!mesh || !obb) return nullptr;
        auto data = std::make_shared<ZoneTriangles>();
        data->mesh = mesh;
        data->obb = *obb;
        if (role == Role::Source) data->zones = zones(*obb);
        return data;
    }

    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override {
        const auto& d = e.as<ZoneTriangles>();
        if (role == Role::Target) return geometry::inflate(geometry::obb_aabb(d.obb), kFloatMargin);
        Bnd_Box box;
        for (const auto& z : d.zones) box.Add(geometry::obb_aabb(z));
        return geometry::inflate(box, kFloatMargin + reach());
    }
    // One zone: the zone against the target OBB (the prefilter of the
    // original). Several zones: kept, each zone is tested in the narrow phase.
    Bnd_OBB mid_volume(const ElementGeometry& e, Role role) const override {
        const auto& d = e.as<ZoneTriangles>();
        if (role == Role::Target) return d.obb;
        return d.zones.size() == 1 ? geometry::inflate(d.zones.front(), reach()) : Bnd_OBB();
    }
    Candidate mid_test(const Bnd_OBB& zone, const Bnd_OBB& target) const override {
        if (zone.IsVoid()) return Candidate::Kept;
        return zone.IsOut(target) ? Candidate::Rejected : Candidate::Kept;
    }

    // One verdict per zone met (the original: one result per zone and target).
    bool multi_verdicts() const override { return true; }
    std::vector<Verdict> narrow_multi(const ElementGeometry& source, const ElementGeometry& target) const override {
        const auto& s = source.as<ZoneTriangles>();
        const auto& t = target.as<ZoneTriangles>();
        const double contact = contact_tolerance();
        std::vector<Verdict> out;
        for (const Bnd_OBB& zone : s.zones) {
            if (geometry::inflate(zone, reach()).IsOut(t.obb)) continue;
            const Bnd_Box query = geometry::inflate(geometry::obb_aabb(zone), reach() + kFloatMargin);
            bool met = false;
            t.mesh->tree().query(query, [&](int k) {
                P3 a, b, c;
                t.mesh->corners(size_t(k), a, b, c);
                if (!triangle_meets_obb(a, b, c, zone, contact)) return true;
                met = true;
                return false;
            });
            if (!met) continue;
            Verdict v;
            v.status = true;
            v.measures.set(Measure::Distance, 0.0);  // the zone meets the target
            v.source_obbs.push_back(geometry::obb_data(zone, std::string("zone")));
            v.source_obbs.push_back(geometry::obb_data(s.obb, std::string("object")));
            v.target_obbs.push_back(geometry::obb_data(t.obb, std::string("object")));
            out.push_back(std::move(v));
        }
        return out;
    }
    Verdict narrow_test(const ElementGeometry& source, const ElementGeometry& target) const override {
        auto all = narrow_multi(source, target);
        return all.empty() ? Verdict{} : all.front();
    }

protected:
    virtual std::vector<Bnd_OBB> zones(const Bnd_OBB& obb) const = 0;
    double contact_tolerance() const { return this->params().contact_tolerance; }
    double reach() const { return std::max(contact_tolerance(), 0.0); }
};

// m: a target triangle within this distance of a zone touches it (the
// original: distance <= 1e-6 on the B-Rep; the triangles are a tessellation,
// the .ifcview is quantized to ~0.1 mm). Negative: it must enter the zone by
// that much (robustness checks).
constexpr double kContactTolerance = 0.001;

struct ObbZoneParams {
    double tolerance = 1.0;  // m: height of the band
    double contact_tolerance = kContactTolerance;
};

class ObbAboveTriang final : public ZoneTriang<ObbZoneParams> {
protected:
    std::vector<Bnd_OBB> zones(const Bnd_OBB& obb) const override {
        return {geometry::detach_by_extrude(obb, {params().tolerance, false}, true)};
    }
};

class ObbBelowTriang final : public ZoneTriang<ObbZoneParams> {
protected:
    std::vector<Bnd_OBB> zones(const Bnd_OBB& obb) const override {
        return {geometry::detach_by_extrude(obb, {params().tolerance, false}, false)};
    }
};

struct FrontBackParams {
    double tolerance = 0.1;
    std::string direction_method = "Wide";
    double contact_tolerance = kContactTolerance;
};

class ObbFrontAndBackTriang final : public ZoneTriang<FrontBackParams> {
protected:
    std::vector<Bnd_OBB> zones(const Bnd_OBB& obb) const override {
        const auto [front, back] = geometry::two_main_directions(obb, params().direction_method, true);
        return {geometry::detach_side_by_extrude(obb, front, params().tolerance),
                geometry::detach_side_by_extrude(obb, back, params().tolerance)};
    }
};

struct CustomParams {
    std::vector<std::string> list_of_modifications;
    double contact_tolerance = kContactTolerance;
};

// Rules._modification_value: "name:value", a percentage kept as such.
geometry::ObbChange modification_value(const std::string& modification) {
    const auto colon = modification.find(':');
    if (colon == std::string::npos) {
        throw ConfigError("OBB_Custom_triang: modification '" + modification + "' has no ':value'");
    }
    std::string value = modification.substr(colon + 1);
    const auto next = value.find(':');
    if (next != std::string::npos) value = value.substr(0, next);  // split(":")[1]
    if (!value.empty() && value.back() == '%') {
        value.pop_back();
        return {std::stod(value) / 100.0, true};
    }
    return {std::stod(value), false};
}

class ObbCustomTriang final : public ZoneTriang<CustomParams> {
public:
    void setup() override {
        // Fail on a bad declaration before any computation.
        for (const auto& m : params().list_of_modifications) {
            if (m.find("NEW_OBB") == std::string::npos && is_known(m)) modification_value(m);
        }
    }

protected:
    static bool is_known(const std::string& m) {
        for (const char* name : {"expand_sides", "detach_top_by_extrude", "detach_bottom_by_extrude", "extend_up",
                                 "extend_down"}) {
            if (m.find(name) != std::string::npos) return true;
        }
        return false;
    }

    // The zones of OBB_Custom, applied to the OBB of the triangles.
    std::vector<Bnd_OBB> zones(const Bnd_OBB& base) const override {
        Bnd_OBB obb = base;
        std::vector<Bnd_OBB> out;
        for (const auto& m : params().list_of_modifications) {
            auto has = [&](const char* name) { return m.find(name) != std::string::npos; };
            if (has("expand_sides")) {
                geometry::expand_sides(obb, modification_value(m));
                continue;
            }
            if (has("detach_top_by_extrude")) {
                obb = geometry::detach_by_extrude(obb, modification_value(m), true);
                continue;
            }
            if (has("detach_bottom_by_extrude")) {
                obb = geometry::detach_by_extrude(obb, modification_value(m), false);
                continue;
            }
            if (has("extend_up")) {
                obb = geometry::extend_vertically(obb, modification_value(m), true);
                continue;
            }
            if (has("extend_down")) {
                obb = geometry::extend_vertically(obb, modification_value(m), false);
                continue;
            }
            if (has("NEW_OBB")) {
                out.push_back(obb);
                obb = base;
            }
        }
        out.push_back(obb);
        return out;
    }
};

}  // namespace

RuleSpec spec_above_triang() {
    return RuleSpec::pair<AboveTriang>(
        "Above_triang", "Above (triangles)", {Slot::Source, Slot::Target},
        "Above on the triangles: the pairs whose target faces sit 0 to tolerance above the source faces, per the "
        "bounding method.",
        {param(&AboveTriangParams::above_type, "above_type").doc("Bounding method").values(kAboveTypes),
         param(&AboveTriangParams::tolerance, "tolerance").doc("Tolerance").unit(Unit::Metre),
         param(&AboveTriangParams::plan_tolerance, "plan_tolerance")
             .doc("Horizontal distance under which two faces count as superposed")
             .unit(Unit::Metre)});
}

RuleSpec spec_below_triang() {
    return RuleSpec::pair<BelowTriang>(
        "Below_triang", "Below (triangles)", {Slot::Source, Slot::Target},
        "Below on the triangles: the pairs whose target faces sit 0 to tolerance below the source faces, per the "
        "bounding method.",
        {param(&BelowTriangParams::below_type, "below_type").doc("Bounding method").values(kBelowTypes),
         param(&BelowTriangParams::tolerance, "tolerance").doc("Tolerance").unit(Unit::Metre),
         param(&BelowTriangParams::plan_tolerance, "plan_tolerance")
             .doc("Horizontal distance under which two faces count as superposed")
             .unit(Unit::Metre)});
}

RuleSpec spec_obb_above_triang() {
    return RuleSpec::pair<ObbAboveTriang>(
        "OBB_Above_triang", "OBB Above (triangles)", {Slot::Source, Slot::Target},
        "OBB_Above on the triangles: a target triangle meets the band extruded above the source OBB.",
        {param(&ObbZoneParams::tolerance, "tolerance").doc("Height of the detection band above the source").unit(Unit::Metre),
         param(&ObbZoneParams::contact_tolerance, "contact_tolerance")
             .doc("Distance under which a target touches the band")
             .unit(Unit::Metre)});
}

RuleSpec spec_obb_below_triang() {
    return RuleSpec::pair<ObbBelowTriang>(
        "OBB_Below_triang", "OBB Below (triangles)", {Slot::Source, Slot::Target},
        "OBB_Below on the triangles: a target triangle meets the band extruded below the source OBB.",
        {param(&ObbZoneParams::tolerance, "tolerance").doc("Height of the detection band below the source").unit(Unit::Metre),
         param(&ObbZoneParams::contact_tolerance, "contact_tolerance")
             .doc("Distance under which a target touches the band")
             .unit(Unit::Metre)});
}

RuleSpec spec_obb_front_and_back_triang() {
    return RuleSpec::pair<ObbFrontAndBackTriang>(
        "OBB_Front_And_Back_triang", "OBB Front And Back (triangles)", {Slot::Source, Slot::Target},
        "OBB_Front_And_Back on the triangles: a target triangle meets the detection bands in front of and behind "
        "the source.",
        {param(&FrontBackParams::tolerance, "tolerance").doc("Depth of the detection bands").unit(Unit::Metre),
         param(&FrontBackParams::direction_method, "direction_method").doc("Front direction").values({"Wide", "Narrow"}),
         param(&FrontBackParams::contact_tolerance, "contact_tolerance")
             .doc("Distance under which a target touches a band")
             .unit(Unit::Metre)});
}

RuleSpec spec_obb_custom_triang() {
    return RuleSpec::pair<ObbCustomTriang>(
        "OBB_Custom_triang", "OBB Custom (triangles)", {Slot::Source, Slot::Target},
        "OBB_Custom on the triangles: a target triangle meets a custom detection zone around the source.",
        {param(&CustomParams::list_of_modifications, "list_of_modifications")
             .doc("Zone modifications, one per line (ex. 'detach_top_by_extrude:0.5', 'NEW_OBB')"),
         param(&CustomParams::contact_tolerance, "contact_tolerance")
             .doc("Distance under which a target touches a zone")
             .unit(Unit::Metre)});
}

}  // namespace ifcclash
