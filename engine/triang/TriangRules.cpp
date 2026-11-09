// IfcClash_Plus engine — the _triang rules: Intersection, Above and
// OBB_Above computed on the triangles of the .ifcview only (engine/triang).
//
// Same parameters and same result blocks as the original rules; the
// geometry is the .ifcview tessellation (quantized, see ViewTriangles.h)
// instead of the IFC conversion, so a pair at the edge of a threshold may
// differ from the original rule. No IFC geometry is ever converted: the IFC
// is read only to resolve the selections.
//
//  - Intersection_triang: the IfcOpenShell clash tree (the algorithm of
//    Intersection: protrusion, then piercing, beyond the tolerance), fed
//    with the .ifcview triangles in a tree of its own.
//  - Above_triang: the target sits above the source when, somewhere in
//    plan, a source triangle seen from the source side (from above for
//    Max, from below for Min) and a target triangle seen from the target
//    side overlap with a vertical gap target - source in [0, tolerance].
//    "Seen" is tested by covering, not by the winding: many IFC meshes
//    (Revit MEP) are wound inwards, the .ifcview keeps that winding. Prefilter of Above:
//    the band extruded above the source OBB must meet the target OBB.
//  - OBB_Above_triang: a target triangle meets the band extruded above
//    the source OBB (OBB_Above: distance band - target <= 1e-6).
//  The OBBs are the optimal boxes of the .ifcview vertices (the method of
//  OBB_Above on its 0.01 m mesh), kept in the Session.
#include "TriangleTests.h"

#include "../geometry/MeshMeasures.h"
#include "../geometry/Obb.h"
#include "../registry/RuleSpec.h"
#include "../rules/RuleBase.h"
#include "../rules/TreeClashRules.h"
#include "../sources/IfcClashTree.h"

#include <cmath>
#include <limits>
#include <optional>

namespace ifcclash {

namespace {

using triang::P3;

// The .ifcview boxes contain the decoded vertices (same placement, the local
// AABB bounds the quantized positions): only the double rounding to absorb.
constexpr double kFloatMargin = 1e-6;

std::shared_ptr<const Mesh> view_mesh(const ElementGeometry& e) { return e.mesh(Variant::ViewMesh); }

// The optimal OBB of the .ifcview vertices of an element, kept in the
// Session (shared by Above_triang and OBB_Above_triang, by every run).
std::optional<Bnd_OBB> view_obb(const ElementGeometry& e) {
    auto data = e.provider().derived(e.key, "view_obb", [&e]() -> std::shared_ptr<const void> {
        const auto mesh = view_mesh(e);
        if (!mesh || mesh->world_verts.empty()) return nullptr;
        return std::make_shared<const Bnd_OBB>(triang::optimal_obb(mesh->world_verts));
    });
    if (!data) return std::nullopt;
    return *std::static_pointer_cast<const Bnd_OBB>(data);
}

P3 vertex(const Mesh& m, int i) {
    return {m.world_verts[3 * size_t(i)], m.world_verts[3 * size_t(i) + 1], m.world_verts[3 * size_t(i) + 2]};
}

Point3 point(const P3& p) { return {p[0], p[1], p[2]}; }

// ================================================================ Intersection_triang

struct IntersectionTriangParams {
    double tolerance = 0.1;  // m
};

class IntersectionTriang final : public PairRule<IntersectionTriangParams> {
public:
    Level narrow_level() const override { return Level::Mesh; }
    PairSymmetry symmetry() const override { return PairSymmetry::Unordered; }
    Variant base_variant() const override { return Variant::ViewMesh; }
    std::vector<Variant> narrow_variants() const override { return {Variant::ViewMesh}; }

    // The margins of the tree (Intersection), on the .ifcview boxes.
    Bnd_Box broad_volume(const ElementGeometry& e, Role) const override {
        return geometry::inflate(e.boxes.aabb, tree_rules::kTreeMargin + kFloatMargin);
    }
    Bnd_OBB mid_volume(const ElementGeometry& e, Role) const override {
        return geometry::inflate(e.boxes.obb, tree_rules::kTreeMargin + kFloatMargin);
    }
    Candidate mid_test(const Bnd_OBB& a, const Bnd_OBB& b) const override {
        return tree_rules::obbs_overlap(a, b) ? Candidate::Kept : Candidate::Rejected;
    }

    std::vector<Verdict> narrow_batch(const std::vector<GeometryPair>& pairs) const override {
        std::vector<Verdict> out(pairs.size());
        if (pairs.empty()) return out;
        GeometryProvider& provider = pairs.front().first->provider();
        std::vector<std::shared_ptr<const Mesh>> keep;
        std::vector<ClashPair> query;
        std::vector<size_t> where;
        for (size_t n = 0; n < pairs.size(); ++n) {
            auto ms = provider.view_clash_mesh(pairs[n].first->key);
            auto mt = provider.view_clash_mesh(pairs[n].second->key);
            if (!ms || !mt) continue;
            query.push_back({&pairs[n].first->key, ms.get(), &pairs[n].second->key, mt.get()});
            where.push_back(n);
            keep.push_back(std::move(ms));
            keep.push_back(std::move(mt));
        }
        if (query.empty()) return out;
        const auto clashes =
            provider.view_clash()->batch(query, {ClashQuery::Intersection, params().tolerance, true});
        for (size_t k = 0; k < clashes.size(); ++k) out[where[k]] = tree_rules::verdict_of(clashes[k]);
        return out;
    }

    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override {
        return narrow_batch({{&s, &t}}).front();
    }
};

// ================================================================ Above_triang

struct AboveTriangParams {
    std::string above_type = "Above_MaxToMax";
    double tolerance = 0.1;  // m
    // m: two faces count as superposed when they overlap in plan or are
    // within this horizontal distance (Above aligns its points to 1e-3).
    // Negative: they must overlap by that much (robustness checks).
    double plan_tolerance = 0.001;
};

// Rules.above_below_directions: the side looked at, +1 (up, Max) or -1
// (down, Min).
double side_of(const std::string& type, Role role) {
    if (role == Role::Source) return type.find("MinTo") != std::string::npos ? -1.0 : 1.0;
    return type.find("ToMin") != std::string::npos ? -1.0 : 1.0;
}

struct ExtremTriangles {
    std::shared_ptr<const Mesh> mesh;
    Bnd_OBB obb;
    Bnd_OBB zone;                // sources: the band above the OBB
    std::vector<int> triangles;  // the triangles facing the side
    std::vector<Bnd_Box> boxes;  // their boxes
    std::unique_ptr<triang::BoxTree> tree;  // targets: on the boxes
};

// The triangles of an element seen from above / below, kept in the Session.
std::vector<int> visible_triangles_of(const ElementGeometry& e, const Mesh& mesh, double side) {
    auto data = e.provider().derived(e.key, side > 0 ? "view_visible_up" : "view_visible_down",
                                     [&mesh, side]() -> std::shared_ptr<const void> {
                                         return std::make_shared<const std::vector<int>>(
                                             triang::visible_triangles(mesh.world_verts, mesh.faces, side));
                                     });
    return *std::static_pointer_cast<const std::vector<int>>(data);
}

// The height of the plane of a triangle above (x, y).
double plane_z(const P3& a, const P3& n, double x, double y) {
    return a[2] - (n[0] * (x - a[0]) + n[1] * (y - a[1])) / n[2];
}

struct GapHit {
    double distance;
    P3 source;
    P3 target;
};

// Where the two triangles overlap in plan, the vertical gap target -
// source is linear: its extremes sit at the vertices of the overlap
// polygon. A hit when its range meets [0, tolerance]; the point reported is
// the smallest gap in range (or where it crosses 0).
std::optional<GapHit> vertical_gap(const P3& a, const P3& b, const P3& c, const P3& d, const P3& e, const P3& f,
                                   double tolerance, double plan_tolerance) {
    constexpr double eps = 1e-9;
    const auto poly = triang::clip_triangles_xy(a, b, c, d, e, f, plan_tolerance);
    if (poly.empty()) return std::nullopt;
    const P3 ns{(b[1] - a[1]) * (c[2] - a[2]) - (b[2] - a[2]) * (c[1] - a[1]),
                (b[2] - a[2]) * (c[0] - a[0]) - (b[0] - a[0]) * (c[2] - a[2]),
                (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])};
    const P3 nt{(e[1] - d[1]) * (f[2] - d[2]) - (e[2] - d[2]) * (f[1] - d[1]),
                (e[2] - d[2]) * (f[0] - d[0]) - (e[0] - d[0]) * (f[2] - d[2]),
                (e[0] - d[0]) * (f[1] - d[1]) - (e[1] - d[1]) * (f[0] - d[0])};
    std::vector<double> gaps(poly.size());
    double gmin = std::numeric_limits<double>::infinity(), gmax = -gmin;
    for (size_t i = 0; i < poly.size(); ++i) {
        gaps[i] = plane_z(d, nt, poly[i][0], poly[i][1]) - plane_z(a, ns, poly[i][0], poly[i][1]);
        gmin = std::min(gmin, gaps[i]);
        gmax = std::max(gmax, gaps[i]);
    }
    if (gmax < -eps || gmin > tolerance + eps) return std::nullopt;
    auto at = [&](double x, double y, double gap) {
        const double zs = plane_z(a, ns, x, y);
        return GapHit{std::max(0.0, gap), {x, y, zs}, {x, y, plane_z(d, nt, x, y)}};
    };
    // The smallest gap in [0, tolerance] at a vertex...
    std::optional<size_t> best;
    for (size_t i = 0; i < poly.size(); ++i) {
        if (gaps[i] >= -eps && gaps[i] <= tolerance + eps && (!best || gaps[i] < gaps[*best])) best = i;
    }
    if (best) return at(poly[*best][0], poly[*best][1], gaps[*best]);
    // ... else the gap crosses 0 inside an edge (the faces cross).
    for (size_t i = 0; i < poly.size(); ++i) {
        const size_t j = (i + 1) % poly.size();
        if ((gaps[i] < 0) != (gaps[j] < 0)) {
            const double t = gaps[i] / (gaps[i] - gaps[j]);
            return at(poly[i][0] + t * (poly[j][0] - poly[i][0]), poly[i][1] + t * (poly[j][1] - poly[i][1]), 0.0);
        }
    }
    return std::nullopt;
}

class AboveTriang final : public PairRule<AboveTriangParams> {
public:
    Variant base_variant() const override { return Variant::ViewMesh; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    std::vector<Variant> data_variants() const override { return {Variant::ViewMesh}; }
    bool needs_element_data() const override { return true; }
    bool skip_self() const override { return false; }    // as Above (N x M loops)
    bool parallel_safe() const override { return true; }  // element_data: .ifcview triangles only

    void setup() override {
        if (params().tolerance < 0) throw ConfigError("tolerance must be a positive number (m)");
    }

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override {
        auto mesh = view_mesh(e);
        const auto obb = view_obb(e);
        if (!mesh || !obb) return nullptr;
        auto data = std::make_shared<ExtremTriangles>();
        data->mesh = mesh;
        data->obb = *obb;
        if (role == Role::Source) data->zone = geometry::detach_by_extrude(*obb, {params().tolerance, false}, true);
        // The triangles seen from the side (Above: the faces its vertical
        // rays hit first), whatever their winding.
        const double side = side_of(params().above_type, role);
        data->triangles = visible_triangles_of(e, *mesh, side);
        for (int t : data->triangles) {
            Bnd_Box box;
            for (int k = 0; k < 3; ++k) {
                const P3 p = vertex(*mesh, mesh->faces[3 * size_t(t) + k]);
                box.Add(gp_Pnt(p[0], p[1], p[2]));
            }
            data->boxes.push_back(box);
        }
        if (role == Role::Target) data->tree = std::make_unique<triang::BoxTree>(data->boxes);
        return data;
    }

    // The band grown by the plan tolerance: an object touching it in plan
    // (a space bounded by the face of a wall) stays a candidate.
    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override {
        const auto& d = e.as<ExtremTriangles>();
        return geometry::inflate(geometry::obb_aabb(role == Role::Source ? d.zone : d.obb),
                                 kFloatMargin + (role == Role::Source ? params().plan_tolerance : 0.0));
    }
    Bnd_OBB mid_volume(const ElementGeometry& e, Role role) const override {
        const auto& d = e.as<ExtremTriangles>();
        return role == Role::Source ? geometry::inflate(d.zone, params().plan_tolerance) : d.obb;
    }
    Candidate mid_test(const Bnd_OBB& zone, const Bnd_OBB& target) const override {
        return zone.IsOut(target) ? Candidate::Rejected : Candidate::Kept;
    }

    Verdict narrow_test(const ElementGeometry& source, const ElementGeometry& target) const override {
        const auto& s = source.as<ExtremTriangles>();
        const auto& t = target.as<ExtremTriangles>();
        // The prefilter of Above is part of the rule (grown by the plan
        // tolerance, as the face test).
        if (geometry::inflate(s.zone, params().plan_tolerance).IsOut(t.obb) || !t.tree) return {};
        const double tol = params().tolerance;
        std::optional<GapHit> hit;
        int hit_s = -1, hit_t = -1;
        for (size_t k = 0; k < s.triangles.size() && !hit; ++k) {
            const int ts = s.triangles[k];
            const P3 a = vertex(*s.mesh, s.mesh->faces[3 * ts]);
            const P3 b = vertex(*s.mesh, s.mesh->faces[3 * ts + 1]);
            const P3 c = vertex(*s.mesh, s.mesh->faces[3 * ts + 2]);
            double x0, y0, z0, x1, y1, z1;
            s.boxes[k].Get(x0, y0, z0, x1, y1, z1);
            const double grow = params().plan_tolerance;
            const double reach = std::max(grow, 0.0);
            Bnd_Box query;  // a target triangle from 0 to tol above this one
            query.Update(x0 - reach, y0 - reach, z0, x1 + reach, y1 + reach, z1 + tol);
            t.tree->query(query, [&](int j) {
                const int tt = t.triangles[j];
                const P3 d = vertex(*t.mesh, t.mesh->faces[3 * tt]);
                const P3 e = vertex(*t.mesh, t.mesh->faces[3 * tt + 1]);
                const P3 f = vertex(*t.mesh, t.mesh->faces[3 * tt + 2]);
                if (auto g = vertical_gap(a, b, c, d, e, f, tol, grow)) {
                    hit = g;
                    hit_s = ts;
                    hit_t = tt;
                    return false;
                }
                return true;
            });
        }
        if (!hit) return {};
        Verdict v;
        v.status = true;
        v.measures.set(Measure::Distance, hit->distance);
        v.points.push_back({point(hit->source), point(hit->target), std::string("above")});
        auto face = [](const Mesh& m, int tri) {
            return geometry::triangle_face_data(vertex(m, m.faces[3 * tri]), vertex(m, m.faces[3 * tri + 1]),
                                                vertex(m, m.faces[3 * tri + 2]));
        };
        v.faces.push_back({face(*s.mesh, hit_s), face(*t.mesh, hit_t)});
        v.source_obbs.push_back(geometry::obb_data(s.obb, std::string("object")));
        v.source_obbs.push_back(geometry::obb_data(s.zone, std::string("zone")));
        v.target_obbs.push_back(geometry::obb_data(t.obb, std::string("object")));
        return v;
    }
};

// ================================================================ OBB_Above_triang

struct ObbAboveTriangParams {
    double tolerance = 1.0;  // m: height of the band above the source
    // m: a target triangle within this distance of the band touches it
    // (OBB_Above: distance <= 1e-6 on the exact B-Rep; the .ifcview
    // positions are quantized to ~0.1 mm). Negative: it must enter the band
    // by that much (robustness checks).
    double contact_tolerance = 0.001;
};

struct BandData {
    std::shared_ptr<const Mesh> mesh;
    Bnd_OBB obb;
    Bnd_OBB zone;     // sources
    Bnd_Box zone_box;  // sources: its AABB (cheap triangle rejection)
};

class ObbAboveTriang final : public PairRule<ObbAboveTriangParams> {
public:
    Variant base_variant() const override { return Variant::ViewMesh; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    std::vector<Variant> data_variants() const override { return {Variant::ViewMesh}; }
    bool needs_element_data() const override { return true; }
    bool skip_self() const override { return false; }    // as OBB_Above (N x M loops)
    bool parallel_safe() const override { return true; }  // element_data: .ifcview triangles only

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override {
        auto mesh = view_mesh(e);
        const auto obb = view_obb(e);
        if (!mesh || !obb) return nullptr;
        auto data = std::make_shared<BandData>();
        data->mesh = mesh;
        data->obb = *obb;
        if (role == Role::Source) {
            data->zone = geometry::detach_by_extrude(*obb, {params().tolerance, false}, true);
            data->zone_box = geometry::inflate(geometry::obb_aabb(data->zone), params().contact_tolerance);
        }
        return data;
    }

    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override {
        const auto& d = e.as<BandData>();
        return geometry::inflate(geometry::obb_aabb(role == Role::Source ? d.zone : d.obb),
                                 kFloatMargin + (role == Role::Source ? params().contact_tolerance : 0.0));
    }
    Bnd_OBB mid_volume(const ElementGeometry& e, Role role) const override {
        const auto& d = e.as<BandData>();
        return role == Role::Source ? geometry::inflate(d.zone, params().contact_tolerance) : d.obb;
    }
    Candidate mid_test(const Bnd_OBB& zone, const Bnd_OBB& target) const override {
        return zone.IsOut(target) ? Candidate::Rejected : Candidate::Kept;
    }

    Verdict narrow_test(const ElementGeometry& source, const ElementGeometry& target) const override {
        const auto& s = source.as<BandData>();
        const auto& t = target.as<BandData>();
        if (geometry::inflate(s.zone, params().contact_tolerance).IsOut(t.obb)) return {};
        const Mesh& m = *t.mesh;
        const size_t n = m.faces.size() / 3;
        double x0, y0, z0, x1, y1, z1;
        s.zone_box.Get(x0, y0, z0, x1, y1, z1);
        for (size_t k = 0; k < n; ++k) {
            const P3 a = vertex(m, m.faces[3 * k]);
            const P3 b = vertex(m, m.faces[3 * k + 1]);
            const P3 c = vertex(m, m.faces[3 * k + 2]);
            if (std::max({a[0], b[0], c[0]}) < x0 || std::min({a[0], b[0], c[0]}) > x1 ||
                std::max({a[1], b[1], c[1]}) < y0 || std::min({a[1], b[1], c[1]}) > y1 ||
                std::max({a[2], b[2], c[2]}) < z0 || std::min({a[2], b[2], c[2]}) > z1)
                continue;
            if (!triang::triangle_meets_obb(a, b, c, s.zone, params().contact_tolerance)) continue;
            // OBB_Above: the band meets the target (distance 0).
            Verdict v;
            v.status = true;
            v.measures.set(Measure::Distance, 0.0);
            v.source_obbs.push_back(geometry::obb_data(s.zone, std::string("zone")));
            v.source_obbs.push_back(geometry::obb_data(s.obb, std::string("object")));
            v.target_obbs.push_back(geometry::obb_data(t.obb, std::string("object")));
            return v;
        }
        return {};
    }
};

const std::vector<std::string> kAboveTypes{"Above_MinToMax", "Above_MinToMin", "Above_MaxToMin", "Above_MaxToMax"};

}  // namespace

RuleSpec spec_intersection_triang() {
    return RuleSpec::pair<IntersectionTriang>(
        "Intersection_triang", "Intersection (triangles .ifcview)", {Slot::Source, Slot::Target},
        "Intersection on the triangles of the .ifcview only (no IFC conversion): the pairs whose shapes intersect "
        "within the tolerance.",
        {param(&IntersectionTriangParams::tolerance, "tolerance").doc("Intersection tolerance").unit(Unit::Metre)});
}

RuleSpec spec_above_triang() {
    return RuleSpec::pair<AboveTriang>(
        "Above_triang", "Above (triangles .ifcview)", {Slot::Source, Slot::Target},
        "Above on the triangles of the .ifcview only: the pairs whose target faces sit 0 to tolerance above the "
        "source faces, per the bounding method.",
        {param(&AboveTriangParams::above_type, "above_type").doc("Bounding method").values(kAboveTypes),
         param(&AboveTriangParams::tolerance, "tolerance").doc("Tolerance").unit(Unit::Metre),
         param(&AboveTriangParams::plan_tolerance, "plan_tolerance")
             .doc("Horizontal distance under which two faces count as superposed")
             .unit(Unit::Metre)});
}

RuleSpec spec_obb_above_triang() {
    return RuleSpec::pair<ObbAboveTriang>(
        "OBB_Above_triang", "OBB Above (triangles .ifcview)", {Slot::Source, Slot::Target},
        "OBB_Above on the triangles of the .ifcview only: a target triangle meets the band extruded above the "
        "source OBB.",
        {param(&ObbAboveTriangParams::tolerance, "tolerance")
             .doc("Height of the detection band above the source")
             .unit(Unit::Metre),
         param(&ObbAboveTriangParams::contact_tolerance, "contact_tolerance")
             .doc("Distance under which a target touches the band")
             .unit(Unit::Metre)});
}

}  // namespace ifcclash
