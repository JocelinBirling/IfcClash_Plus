// AngleBetween, ClearanceAxisToAxis and Intersection2 of Rules.py.
#include "AllRules.h"

#include "../geometry/Faces.h"
#include "../geometry/Numpy.h"
#include "../geometry/Obb.h"

#include <BRepAlgoAPI_Common.hxx>
#include <BRepBndLib.hxx>
#include <BRepBuilderAPI_MakeSolid.hxx>
#include <BRepBuilderAPI_Sewing.hxx>
#include <BRepExtrema_DistShapeShape.hxx>
#include <BRepGProp.hxx>
#include <BRep_Builder.hxx>
#include <GProp_GProps.hxx>
#include <TopExp_Explorer.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Compound.hxx>

#include <cmath>
#include <limits>
#include <set>
#include <unordered_map>

namespace ifcclash {

namespace {

constexpr double kRadToDeg = 180.0 / M_PI;
using V3 = std::array<double, 3>;

V3 v_add(const V3& a, const V3& b) { return {a[0] + b[0], a[1] + b[1], a[2] + b[2]}; }
V3 v_sub(const V3& a, const V3& b) { return {a[0] - b[0], a[1] - b[1], a[2] - b[2]}; }
V3 v_mul(const V3& a, double k) { return {a[0] * k, a[1] * k, a[2] * k}; }
// np.dot / np.linalg.norm on 1-D vectors, in the numpy rounding
double v_dot(const V3& a, const V3& b) { return geometry::np::dot(a, b); }
double v_norm(const V3& a) { return std::sqrt(v_dot(a, a)); }

// ================================================================ AngleBetween

struct AngleParams {
    std::string direction_method_for_source = "Wide";
    std::string direction_method_for_target = "Wide";
    double angle_difference = 0.0;
    double angle_tolerance = 0.0;
};

struct AxisData {
    gp_Dir direction;
    gp_Pnt center;
};

class AngleBetween final : public PairRule<AngleParams> {
public:
    Variant base_variant() const override { return Variant::BrepWorld; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    BroadMode broad_mode() const override { return BroadMode::AllPairs; }  // no spatial locality
    bool skip_self() const override { return false; }
    bool needs_element_data() const override { return true; }
    bool parallel_safe() const override { return true; }  // element_data: B-Rep geometry only

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override {
        const auto brep = e.meshed_brep();
        if (!brep) return nullptr;
        const Bnd_OBB& obb = brep->obb;
        const auto& method =
            role == Role::Source ? params().direction_method_for_source : params().direction_method_for_target;
        auto data = std::make_shared<AxisData>();
        data->direction = geometry::two_main_directions(obb, method).first;
        data->center = geometry::shape_center(brep->shape);
        return data;
    }

    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override {
        const auto& a = s.as<AxisData>();
        const auto& b = t.as<AxisData>();
        const double angle = a.direction.Angle(b.direction) * kRadToDeg;
        double diff = std::abs(angle - params().angle_difference);
        diff = std::min(diff, 360 - diff);
        Verdict v;
        v.status = diff <= params().angle_tolerance;
        if (!v.status) return v;
        v.measures.set(Measure::Angle, angle);
        auto axis = [](const AxisData& d, const char* label) {
            return ifcclash::AxisData{{d.center.X(), d.center.Y(), d.center.Z()},
                                      {d.direction.X(), d.direction.Y(), d.direction.Z()},
                                      0.5,
                                      std::string(label)};
        };
        v.axes.push_back(axis(a, "source"));
        v.axes.push_back(axis(b, "target"));
        return v;
    }
};

// ================================================================ ClearanceAxisToAxis

struct AxisToAxisParams {
    std::string mode = "Perpendicular";
    std::optional<double> min_distance;
    std::optional<double> max_distance;
    double tolerance = 0.0;
    double linearity_ratio = 10.0;
    std::string on_non_linear = "Skip";
    double parallel_tolerance = 1.0;
    std::optional<double> search_radius;  // m; beyond it a pair is not a neighbour
};

struct LongAxis {
    TopoDS_Shape shape;
    Bnd_Box box;
    V3 center;
    V3 direction;
    double half_length = 0.0;
    double linearity = 0.0;
};

// clash_utils.obb_long_axis
void long_axis(const Bnd_OBB& obb, LongAxis& out) {
    const gp_XYZ c = obb.Center();
    out.center = {c.X(), c.Y(), c.Z()};
    struct Cand {
        double h;
        V3 d;
    };
    std::vector<Cand> cands{{obb.XHSize(), {obb.XDirection().X(), obb.XDirection().Y(), obb.XDirection().Z()}},
                            {obb.YHSize(), {obb.YDirection().X(), obb.YDirection().Y(), obb.YDirection().Z()}},
                            {obb.ZHSize(), {obb.ZDirection().X(), obb.ZDirection().Y(), obb.ZDirection().Z()}}};
    std::stable_sort(cands.begin(), cands.end(), [](const Cand& a, const Cand& b) { return a.h > b.h; });
    out.half_length = cands[0].h;
    V3 d = cands[0].d;
    const double thickness = 2.0 * cands[1].h;
    const double n = v_norm(d);
    if (n > 0.0) d = {d[0] / n, d[1] / n, d[2] / n};
    out.direction = d;
    out.linearity = thickness > 1e-9 ? 2.0 * out.half_length / thickness : std::numeric_limits<double>::infinity();
}

double axis_angle(const V3& a, const V3& b) {
    const double cosine = std::min(1.0, std::max(-1.0, std::abs(v_dot(a, b))));
    return std::acos(cosine) * kRadToDeg;
}

struct Closest {
    double distance;
    V3 p1, p2;
};

// clash_utils._same_sense: d2 turned to the sense of d1 (the sign of an OBB
// axis is arbitrary; the bisector must be taken on one sense).
V3 same_sense(const V3& d1, const V3& d2) { return v_dot(d1, d2) < 0.0 ? v_mul(d2, -1.0) : d2; }

V3 common_direction(const V3& d1, const V3& d2) {
    const V3 common = v_add(d1, same_sense(d1, d2));
    const double n = v_norm(common);
    return n < 1e-12 ? d1 : V3{common[0] / n, common[1] / n, common[2] / n};
}

Closest parallel_line_offset_closest(const V3& c1, const V3& d1, const V3& c2, const V3& d2) {
    const V3 common = common_direction(d1, d2);
    const V3 delta = v_sub(c2, c1);
    const V3 p1 = v_add(c1, v_mul(common, v_dot(delta, common)));
    const double offset = v_norm(v_sub(delta, v_mul(common, v_dot(delta, common))));
    return {offset, p1, c2};
}

// clash_utils.axial_overlap: the length over which two quasi-parallel
// segments face each other (<= 0: they do not).
double axial_overlap(const V3& c1, const V3& d1, double h1, const V3& c2, const V3& d2, double h2) {
    const V3 common = common_direction(d1, d2);
    const double p1 = v_dot(c1, common), p2 = v_dot(c2, common);
    const double e1 = h1 * std::abs(v_dot(d1, common)), e2 = h2 * std::abs(v_dot(d2, common));
    return std::min(p1 + e1, p2 + e2) - std::max(p1 - e1, p2 - e2);
}

Closest segment_segment_closest(const V3& p1, const V3& e1, const V3& p2, const V3& e2) {
    const V3 d1 = v_sub(e1, p1), d2 = v_sub(e2, p2), delta = v_sub(p1, p2);
    const double l1 = v_dot(d1, d1), l2 = v_dot(d2, d2);
    constexpr double eps = 1e-12;
    double s = 0.0, t = 0.0;
    if (l1 <= eps && l2 <= eps) return {v_norm(delta), p1, p2};
    if (l1 <= eps) {
        t = std::min(1.0, std::max(0.0, v_dot(d2, delta) / l2));
    } else if (l2 <= eps) {
        s = std::min(1.0, std::max(0.0, -v_dot(d1, delta) / l1));
    } else {
        const double d12 = v_dot(d1, d2), dot1 = v_dot(d1, delta), dot2 = v_dot(d2, delta);
        const double den = l1 * l2 - d12 * d12;
        s = den > eps ? std::min(1.0, std::max(0.0, (d12 * dot2 - dot1 * l2) / den)) : 0.0;
        t = (d12 * s + dot2) / l2;
        if (t < 0.0) {
            t = 0.0;
            s = std::min(1.0, std::max(0.0, -dot1 / l1));
        } else if (t > 1.0) {
            t = 1.0;
            s = std::min(1.0, std::max(0.0, (d12 - dot1) / l1));
        }
    }
    const V3 c1 = v_add(p1, v_mul(d1, s)), c2 = v_add(p2, v_mul(d2, t));
    return {v_norm(v_sub(c1, c2)), c1, c2};
}

ifcclash::AxisData support_axis(const LongAxis& a, const char* label) {
    const V3 start = v_sub(a.center, v_mul(a.direction, a.half_length));
    return {start, a.direction, 2.0 * a.half_length, std::string(label)};
}

struct AxisMeasure {
    double distance = 0.0;
    double angle = 0.0;
    std::optional<V3> source_point, target_point;
    std::string mode;
    bool degraded = false;
};

class ClearanceAxisToAxis final : public PairRule<AxisToAxisParams> {
public:
    Variant base_variant() const override { return Variant::BrepWorld; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    // A distance OUTSIDE the interval is flagged: a far pair can be a
    // result (max_distance), so no spatial prefilter.
    BroadMode broad_mode() const override { return BroadMode::AllPairs; }
    bool needs_element_data() const override { return true; }
    bool parallel_safe() const override { return true; }  // element_data: B-Rep geometry only
    // The nearest target of each source and the unordered pairs: a verdict
    // depends on the other pairs of the run.
    bool narrow_whole_run() const override { return true; }

    void setup() override {
        const auto& p = params();
        if (p.min_distance && *p.min_distance < 0) throw ConfigError("min_distance must be None or a positive number (m)");
        if (p.max_distance && *p.max_distance < 0) throw ConfigError("max_distance must be None or a positive number (m)");
        if (!p.min_distance && !p.max_distance) throw ConfigError("at least one of min_distance or max_distance must be set");
        if (p.min_distance && p.max_distance && *p.min_distance > *p.max_distance)
            throw ConfigError("min_distance must not exceed max_distance");
        if (p.tolerance < 0) throw ConfigError("tolerance must be a positive number (m)");
        if (p.linearity_ratio < 1.0) throw ConfigError("linearity_ratio must be a number >= 1");
        if (!(p.parallel_tolerance > 0.0 && p.parallel_tolerance <= 90.0))
            throw ConfigError("parallel_tolerance must be in (0, 90] degrees");
        if (p.search_radius && *p.search_radius < 0)
            throw ConfigError("search_radius must be None or a positive number (m)");
    }

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role) const override {
        const auto brep = e.meshed_brep();
        if (!brep) return nullptr;
        auto data = std::make_shared<LongAxis>();
        data->shape = brep->shape;
        long_axis(brep->obb, *data);
        BRepBndLib::Add(data->shape, data->box);  // bounds the skin (Fallback radius test)
        return data;
    }

    // One pair alone (exceptions): it is its source's only, so nearest, pair.
    Verdict narrow_test(const ElementGeometry& source, const ElementGeometry& target) const override {
        const auto m = measure(source.as<LongAxis>(), target.as<LongAxis>());
        if (!m) return {};
        return verdict(*m, source.as<LongAxis>(), target.as<LongAxis>(), true);
    }

    // Rules.ClearanceAxisToAxis.compute: 1. the measure of every concerned
    // pair; 2. the nearest target of each source (ties within 1e-9 m: the
    // first in candidate order); 3. "too close" on every pair, "too far" on
    // the nearest one, each unordered pair once (its first orientation).
    std::vector<Verdict> narrow_batch(const std::vector<GeometryPair>& pairs) const override {
        std::vector<std::optional<AxisMeasure>> measures(pairs.size());
        for (size_t i = 0; i < pairs.size(); ++i) {
            measures[i] = measure(pairs[i].first->as<LongAxis>(), pairs[i].second->as<LongAxis>());
        }
        std::unordered_map<ElementKey, double, ElementKeyHash> best;
        for (size_t i = 0; i < pairs.size(); ++i) {
            if (!measures[i]) continue;
            auto [it, fresh] = best.emplace(pairs[i].first->key, measures[i]->distance);
            if (!fresh) it->second = std::min(it->second, measures[i]->distance);
        }
        std::unordered_map<ElementKey, size_t, ElementKeyHash> nearest;
        for (size_t i = 0; i < pairs.size(); ++i) {
            if (!measures[i]) continue;
            const ElementKey& s = pairs[i].first->key;
            if (!nearest.count(s) && measures[i]->distance <= best.at(s) + 1e-9) nearest.emplace(s, i);
        }
        std::vector<Verdict> out(pairs.size());
        std::set<std::pair<ElementKey, ElementKey>> reported;
        for (size_t i = 0; i < pairs.size(); ++i) {
            if (!measures[i]) continue;
            const ElementKey& s = pairs[i].first->key;
            const ElementKey& t = pairs[i].second->key;
            Verdict v = verdict(*measures[i], pairs[i].first->as<LongAxis>(), pairs[i].second->as<LongAxis>(),
                                nearest.at(s) == i);
            if (!v.status) continue;
            if (!reported.insert(t < s ? std::make_pair(t, s) : std::make_pair(s, t)).second) continue;
            out[i] = std::move(v);
        }
        return out;
    }

private:
    // Rules.ClearanceAxisToAxis._measure: nullopt = the pair is not concerned.
    std::optional<AxisMeasure> measure(const LongAxis& s, const LongAxis& t) const {
        const auto& p = params();
        const bool linear = s.linearity >= p.linearity_ratio && t.linearity >= p.linearity_ratio;
        AxisMeasure m;
        m.angle = axis_angle(s.direction, t.direction);
        if (linear) {
            Closest c;
            if (p.mode == "Perpendicular" && m.angle <= p.parallel_tolerance) {
                if (axial_overlap(s.center, s.direction, s.half_length, t.center, t.direction, t.half_length) <= 1e-6)
                    return std::nullopt;  // not side by side
                c = parallel_line_offset_closest(s.center, s.direction, t.center, t.direction);
                m.mode = "Perpendicular";
            } else {
                c = segment_segment_closest(v_sub(s.center, v_mul(s.direction, s.half_length)),
                                            v_add(s.center, v_mul(s.direction, s.half_length)),
                                            v_sub(t.center, v_mul(t.direction, t.half_length)),
                                            v_add(t.center, v_mul(t.direction, t.half_length)));
                m.mode = "MinDistance";
            }
            m.distance = c.distance;
            m.source_point = c.p1;
            m.target_point = c.p2;
            m.degraded = false;
        } else if (p.on_non_linear == "Skip") {
            return std::nullopt;
        } else {
            // The boxes bound the skins: beyond the radius, the exact
            // (costly) distance cannot come back inside it.
            if (p.search_radius && s.box.Distance(t.box) > *p.search_radius) return std::nullopt;
            BRepExtrema_DistShapeShape tool(s.shape, t.shape);
            tool.Perform();
            m.distance = tool.Value();
            if (tool.IsDone() && tool.NbSolution() >= 1) {
                const gp_Pnt a = tool.PointOnShape1(1), b = tool.PointOnShape2(1);
                m.source_point = V3{a.X(), a.Y(), a.Z()};
                m.target_point = V3{b.X(), b.Y(), b.Z()};
            }
            m.mode = "Fallback";
            m.degraded = true;
        }
        if (p.search_radius && m.distance > *p.search_radius) return std::nullopt;
        return m;
    }

    Verdict verdict(const AxisMeasure& m, const LongAxis& s, const LongAxis& t, bool is_nearest) const {
        const auto& p = params();
        const bool too_close = p.min_distance && m.distance < *p.min_distance - p.tolerance;
        const bool too_far = p.max_distance && is_nearest && m.distance > *p.max_distance + p.tolerance;
        Verdict v;
        v.status = too_close || too_far;
        if (!v.status) return v;
        v.measures.set(Measure::Distance, m.distance);
        v.measures.set(Measure::Angle, m.angle);
        if (m.source_point && m.target_point) v.points.push_back({*m.source_point, *m.target_point, std::nullopt});
        v.axis = AxisBlock{m.mode, m.degraded};
        v.axes.push_back(support_axis(s, "source"));
        v.axes.push_back(support_axis(t, "target"));
        return v;
    }
};

// ================================================================ Intersection2

struct Intersection2Params {
    double tolerance = 0.0;  // m3: minimum overlap volume
};

struct SolidData {
    TopoDS_Shape solid;
    Bnd_Box box;
    Bnd_OBB obb;
};

// clash_utils.mesh_to_solid
TopoDS_Shape mesh_to_solid(const TopoDS_Shape& shape, double tolerance = 1e-3) {
    BRepBuilderAPI_Sewing sewing(tolerance);
    for (TopExp_Explorer ex(shape, TopAbs_FACE); ex.More(); ex.Next()) sewing.Add(ex.Current());
    sewing.Perform();
    const TopoDS_Shape sewn = sewing.SewedShape();
    std::vector<TopoDS_Shell> shells;
    for (TopExp_Explorer ex(sewn, TopAbs_SHELL); ex.More(); ex.Next()) shells.push_back(TopoDS::Shell(ex.Current()));
    if (shells.empty()) return sewn;
    BRep_Builder builder;
    TopoDS_Compound compound;
    builder.MakeCompound(compound);
    for (const auto& shell : shells) builder.Add(compound, BRepBuilderAPI_MakeSolid(shell).Solid());
    return compound;
}

class Intersection2 final : public PairRule<Intersection2Params> {
public:
    Variant base_variant() const override { return Variant::BrepWorld; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    bool needs_element_data() const override { return true; }
    bool parallel_safe() const override { return true; }  // element_data: B-Rep geometry only

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role) const override {
        auto shape = e.brep();
        if (!shape) return nullptr;
        auto data = std::make_shared<SolidData>();
        data->solid = mesh_to_solid(*shape);
        BRepBndLib::Add(data->solid, data->box);
        BRepBndLib::AddOBB(data->solid, data->obb, false, false, false);
        return data;
    }

    // The bounding-box prefilter of the Python engine (Bnd_Box then Bnd_OBB).
    Bnd_Box broad_volume(const ElementGeometry& e, Role) const override { return e.as<SolidData>().box; }
    Bnd_OBB mid_volume(const ElementGeometry& e, Role) const override { return e.as<SolidData>().obb; }
    Candidate mid_test(const Bnd_OBB& a, const Bnd_OBB& b) const override {
        return a.IsOut(b) ? Candidate::Rejected : Candidate::Kept;
    }

    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override {
        // The common of the pair, called in the order the Python engine
        // meets the elements (its unordered pair is sorted by that order).
        const bool s_first = s.rank < t.rank;
        const auto& a = (s_first ? s : t).as<SolidData>();
        const auto& b = (s_first ? t : s).as<SolidData>();
        // The box prefilter of the Python engine is part of the rule (the
        // common of open meshes can carry a volume far away): repeated here,
        // so the verdict does not depend on the engine prefilters.
        if (a.box.IsOut(b.box) || a.obb.IsOut(b.obb)) return {};
        BRepAlgoAPI_Common common(a.solid, b.solid);
        common.Build();
        Verdict v;
        if (!common.IsDone()) return v;
        const TopoDS_Shape shape = common.Shape();
        if (shape.IsNull()) return v;
        GProp_GProps props;
        BRepGProp::VolumeProperties(shape, props);
        const double volume = props.Mass();
        if (volume <= params().tolerance) return v;
        const gp_Pnt c = props.CentreOfMass();
        v.status = true;
        v.measures.set(Measure::Volume, volume);
        v.volumes.intersection = volume;
        v.measures.set(Measure::Distance, 0.0);
        v.points.push_back({{c.X(), c.Y(), c.Z()}, {c.X(), c.Y(), c.Z()}, std::string("overlap_center")});
        return v;
    }
};

}  // namespace

RuleSpec spec_angle_between() {
    const std::vector<std::string> wn{"Wide", "Narrow"};
    return RuleSpec::pair<AngleBetween>(
        "AngleBetween", "Angle Between", {Slot::Source, Slot::Target},
        "Flags the pairs whose angle between the source and target axes matches the expected difference.",
        {param(&AngleParams::direction_method_for_source, "direction_method_for_source").doc("Source OBB axis").values(wn),
         param(&AngleParams::direction_method_for_target, "direction_method_for_target").doc("Target OBB axis").values(wn),
         param(&AngleParams::angle_difference, "angle_difference").doc("Expected angle difference").unit(Unit::Degree),
         param(&AngleParams::angle_tolerance, "angle_tolerance").doc("Angle tolerance").unit(Unit::Degree)});
}

RuleSpec spec_clearance_axis_to_axis() {
    return RuleSpec::pair<ClearanceAxisToAxis>(
        "ClearanceAxisToAxis", "Clearance Axis To Axis", {Slot::Source, Slot::Target},
        "Flags, axis to axis, the pairs of linear elements closer than min_distance and each source farther "
        "than max_distance from its nearest target.",
        {param(&AxisToAxisParams::mode, "mode").doc("Distance mode").values({"Perpendicular", "MinDistance"}),
         param(&AxisToAxisParams::min_distance, "min_distance").doc("Minimum distance").unit(Unit::Metre),
         param(&AxisToAxisParams::max_distance, "max_distance").doc("Maximum distance").unit(Unit::Metre),
         param(&AxisToAxisParams::tolerance, "tolerance").doc("Distance tolerance").unit(Unit::Metre),
         param(&AxisToAxisParams::linearity_ratio, "linearity_ratio").doc("Linearity ratio"),
         param(&AxisToAxisParams::on_non_linear, "on_non_linear").doc("Non linear elements").values({"Skip", "Fallback"}),
         param(&AxisToAxisParams::parallel_tolerance, "parallel_tolerance").doc("Parallelism tolerance").unit(Unit::Degree),
         param(&AxisToAxisParams::search_radius, "search_radius").doc("Neighbour search radius").unit(Unit::Metre)});
}

RuleSpec spec_intersection2() {
    return RuleSpec::pair<Intersection2>(
        "Intersection2", "Intersection 2", {Slot::Source, Slot::Target},
        "Flags the pairs with a positive overlap volume (OCCT boolean common).",
        {param(&Intersection2Params::tolerance, "tolerance").doc("Minimum overlap volume").unit(Unit::CubicMetre)});
}

}  // namespace ifcclash
