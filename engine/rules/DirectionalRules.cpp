// The directional two-object rules of Rules.py: Above, Below (extreme faces)
// and OBB_Above, OBB_Below, OBB_Front_And_Back, OBB_Custom (detection zones
// built from the OBB of the source).
//
// Their Python engines loop over sources x targets with an OBB prefilter
// (zone OBB of the source vs object OBB of the target), without skipping an
// element tested against itself. The C++ phases reproduce that prefilter:
//  - element data: the OBB / zones / extreme faces of every element, built
//    once on its B-Rep (as elements_extrem_data / elements_obb_data);
//  - broad: the axis-aligned boxes of those OBBs (they contain the OBBs, so
//    two overlapping OBBs always overlap here);
//  - mid: the very IsOut test of the Python loop;
//  - narrow: the exact test of the Python loop.
#include "AllRules.h"

#include "../geometry/Faces.h"
#include "../geometry/Obb.h"

#include <BRepIntCurveSurface_Inter.hxx>
#include <gp_Lin.hxx>

namespace ifcclash {

namespace {

constexpr double kBroadMargin = 1e-6;  // float rounding of the corner boxes

Bnd_Box broad_of(const Bnd_OBB& obb) { return geometry::inflate(geometry::obb_aabb(obb), kBroadMargin); }

Candidate obb_prefilter(const Bnd_OBB& zone, const Bnd_OBB& target) {
    return zone.IsOut(target) ? Candidate::Rejected : Candidate::Kept;
}

// A rule working on the B-Rep of its elements, with derived data.
template <class Params>
class BrepPairRule : public PairRule<Params> {
public:
    Variant base_variant() const override { return Variant::BrepWorld; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    bool needs_element_data() const override { return true; }
    bool skip_self() const override { return false; }
    bool parallel_safe() const override { return true; }  // element_data: B-Rep, OBB and faces only
};

// ================================================================ Above / Below

struct ExtremData {
    TopoDS_Shape shape;
    Bnd_OBB object_obb;
    Bnd_OBB zone_obb;  // sources only
    std::vector<TopoDS_Face> faces;
};

// Rules.above_below_directions: the extreme faces of each side.
gp_Dir side_direction(const std::string& type, Role role) {
    if (role == Role::Source) return type.find("MinTo") != std::string::npos ? gp_Dir(0, 0, -1) : gp_Dir(0, 0, 1);
    return type.find("ToMin") != std::string::npos ? gp_Dir(0, 0, -1) : gp_Dir(0, 0, 1);
}

struct AboveParams {
    std::string above_type = "Above_MaxToMax";
    double tolerance = 0.1;
};
struct BelowParams {
    std::string below_type = "Below_MaxToMax";
    double tolerance = 0.1;
};

// Rules._make_extrem_result
Verdict extrem_verdict(const ExtremData& s, const ExtremData& t, const TopoDS_Face& source_face,
                       const TopoDS_Face& target_face, const Point3& source_point, const Point3& target_point,
                       double distance, const std::string& label) {
    Verdict v;
    v.status = true;
    v.measures.set(Measure::Distance, distance);
    v.points.push_back({source_point, target_point, label});
    v.faces.push_back({geometry::extrem_face_data(source_face), geometry::extrem_face_data(target_face)});
    v.source_obbs.push_back(geometry::obb_data(s.object_obb, std::string("object")));
    v.source_obbs.push_back(geometry::obb_data(s.zone_obb, std::string("zone")));
    v.target_obbs.push_back(geometry::obb_data(t.object_obb, std::string("object")));
    return v;
}

template <class Params>
class ExtremRule : public BrepPairRule<Params> {
public:
    explicit ExtremRule(bool above) : above_(above) {}

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override {
        // The shape meshed by its OBB, then its visible faces, as in Python;
        // both kept in the Session (shared with the other runs and rules).
        const auto brep = e.meshed_brep();
        if (!brep) return nullptr;
        auto data = std::make_shared<ExtremData>();
        data->shape = brep->shape;
        data->object_obb = brep->obb;
        data->faces = *e.visible_faces(side_direction(type(), role));
        if (role == Role::Source) {
            data->zone_obb = geometry::detach_by_extrude(data->object_obb, {tolerance(), false}, above_);
        }
        return data;
    }

    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override {
        const auto& d = e.as<ExtremData>();
        return broad_of(role == Role::Source ? d.zone_obb : d.object_obb);
    }
    Bnd_OBB mid_volume(const ElementGeometry& e, Role role) const override {
        const auto& d = e.as<ExtremData>();
        return role == Role::Source ? d.zone_obb : d.object_obb;
    }
    Candidate mid_test(const Bnd_OBB& zone, const Bnd_OBB& target) const override {
        return obb_prefilter(zone, target);
    }

    Verdict narrow_test(const ElementGeometry& source, const ElementGeometry& target) const override {
        const auto& s = source.as<ExtremData>();
        const auto& t = target.as<ExtremData>();
        // The zone prefilter of the Python loop is part of the rule (the rays
        // would reach far faces): repeated here, independent of the engine
        // prefilters.
        if (s.zone_obb.IsOut(t.object_obb)) return {};
        const auto check = geometry::check_extrem_face_distance(s.faces, t.faces, tolerance(), above_);
        const std::string label = above_ ? "above" : "below";
        if (check.side == geometry::ExtremCheck::Side::RightSide) {
            const auto& d = *check.details;
            return extrem_verdict(s, t, d.source_face, d.target_face, d.source_point, d.target_point, d.distance,
                                  label);
        }
        if (check.side == geometry::ExtremCheck::Side::TooFar) return {};
        // Need_More_Check: a ray cast from each candidate point must hit a
        // source extreme face (down for Above, up for Below).
        const gp_Dir ray_dir(0, 0, above_ ? -1.0 : 1.0);
        for (const auto& source_face : s.faces) {
            for (const auto& candidate : check.candidates) {
                BRepIntCurveSurface_Inter inter;
                inter.Init(source_face, gp_Lin(candidate.point, ray_dir), 1e-7);
                if (inter.More()) {
                    const gp_Pnt p = inter.Pnt();
                    const gp_Pnt q = candidate.point;
                    return extrem_verdict(s, t, source_face, candidate.target_face, {p.X(), p.Y(), p.Z()},
                                          {q.X(), q.Y(), q.Z()}, candidate.distance, "ray");
                }
            }
        }
        return {};
    }

private:
    const std::string& type() const;
    double tolerance() const { return this->params().tolerance; }
    bool above_;
};

template <>
const std::string& ExtremRule<AboveParams>::type() const { return params().above_type; }
template <>
const std::string& ExtremRule<BelowParams>::type() const { return params().below_type; }

class Above final : public ExtremRule<AboveParams> {
public:
    Above() : ExtremRule<AboveParams>(true) {}
};
class Below final : public ExtremRule<BelowParams> {
public:
    Below() : ExtremRule<BelowParams>(false) {}
};

// ================================================================ OBB zone rules

struct Zone {
    Bnd_OBB obb;
    TopoDS_Shape solid;
};

struct ZoneData {
    TopoDS_Shape shape;
    Bnd_OBB object_obb;      // targets: the object; sources: the base OBB
    std::vector<Zone> zones;  // sources only
};

Verdict zone_verdict(double distance, const Zone& zone, const Bnd_OBB& source_obb, const Bnd_OBB& target_obb) {
    Verdict v;
    v.status = true;
    v.measures.set(Measure::Distance, distance);
    v.source_obbs.push_back(geometry::obb_data(zone.obb, std::string("zone")));
    v.source_obbs.push_back(geometry::obb_data(source_obb, std::string("object")));
    v.target_obbs.push_back(geometry::obb_data(target_obb, std::string("object")));
    return v;
}

template <class Params>
class ZoneRule : public BrepPairRule<Params> {
public:
    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override {
        const auto brep = e.meshed_brep();
        if (!brep) return nullptr;
        auto data = std::make_shared<ZoneData>();
        data->shape = brep->shape;
        data->object_obb = brep->obb;
        if (role == Role::Source) {
            for (const Bnd_OBB& zone : zones(data->shape, data->object_obb)) {
                data->zones.push_back({zone, geometry::obb_solid(zone)});
            }
        }
        return data;
    }

    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override {
        const auto& d = e.as<ZoneData>();
        if (role == Role::Target) return broad_of(d.object_obb);
        Bnd_Box box;
        for (const auto& z : d.zones) box.Add(broad_of(z.obb));
        return box;
    }

    // One verdict per zone touched (Python: one result per zone and target).
    bool multi_verdicts() const override { return true; }
    std::vector<Verdict> narrow_multi(const ElementGeometry& source, const ElementGeometry& target) const override {
        const auto& s = source.as<ZoneData>();
        const auto& t = target.as<ZoneData>();
        std::vector<Verdict> out;
        for (const auto& zone : s.zones) {
            if (zone.obb.IsOut(t.object_obb)) continue;
            const double distance = geometry::shape_distance(zone.solid, t.shape);
            if (distance <= 1e-6) out.push_back(zone_verdict(distance, zone, s.object_obb, t.object_obb));
        }
        return out;
    }
    Verdict narrow_test(const ElementGeometry& source, const ElementGeometry& target) const override {
        auto all = narrow_multi(source, target);
        return all.empty() ? Verdict{} : all.front();
    }

protected:
    virtual std::vector<Bnd_OBB> zones(const TopoDS_Shape& shape, const Bnd_OBB& obb) const = 0;
};

struct ObbZoneParams {
    double tolerance = 1.0;
};

class ObbAbove final : public ZoneRule<ObbZoneParams> {
protected:
    std::vector<Bnd_OBB> zones(const TopoDS_Shape&, const Bnd_OBB& obb) const override {
        return {geometry::detach_by_extrude(obb, {params().tolerance, false}, true)};
    }
};

class ObbBelow final : public ZoneRule<ObbZoneParams> {
protected:
    std::vector<Bnd_OBB> zones(const TopoDS_Shape&, const Bnd_OBB& obb) const override {
        return {geometry::detach_by_extrude(obb, {params().tolerance, false}, false)};
    }
};

struct FrontBackParams {
    double tolerance = 0.1;
    std::string direction_method = "Wide";
};

class ObbFrontAndBack final : public ZoneRule<FrontBackParams> {
protected:
    std::vector<Bnd_OBB> zones(const TopoDS_Shape&, const Bnd_OBB& obb) const override {
        const auto [front, back] = geometry::two_main_directions(obb, params().direction_method, true);
        return {geometry::detach_side_by_extrude(obb, front, params().tolerance),
                geometry::detach_side_by_extrude(obb, back, params().tolerance)};
    }
};

struct CustomParams {
    std::vector<std::string> list_of_modifications;
};

// Rules._modification_value: "name:value", a percentage kept as such.
geometry::ObbChange modification_value(const std::string& modification) {
    const auto colon = modification.find(':');
    if (colon == std::string::npos) {
        throw ConfigError("OBB_Custom: modification '" + modification + "' has no ':value'");
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

class ObbCustom final : public ZoneRule<CustomParams> {
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

    std::vector<Bnd_OBB> zones(const TopoDS_Shape& shape, const Bnd_OBB& base) const override {
        Bnd_OBB obb = base;
        std::vector<Bnd_OBB> out;
        for (const auto& m : params().list_of_modifications) {
            auto has = [&](const char* name) { return m.find(name) != std::string::npos; };
            if (has("expand_sides")) {
                // Python assigns the None returned by expand_sides (and then
                // fails): the intended in-place expansion is applied here.
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
                // Python recomputes the OBB of the (already meshed) shape:
                // the same box as `base`. The shared shape is not touched.
                out.push_back(obb);
                obb = base;
            }
        }
        out.push_back(obb);
        return out;
    }
};

const std::vector<std::string> kAboveTypes{"Above_MinToMax", "Above_MinToMin", "Above_MaxToMin", "Above_MaxToMax"};
const std::vector<std::string> kBelowTypes{"Below_MinToMax", "Below_MinToMin", "Below_MaxToMin", "Below_MaxToMax"};

}  // namespace

RuleSpec spec_above() {
    return RuleSpec::pair<Above>(
        "Above", "Above", {Slot::Source, Slot::Target},
        "Flags the pairs whose target sits above the source, per the bounding method.",
        {param(&AboveParams::above_type, "above_type").doc("Bounding method").values(kAboveTypes),
         param(&AboveParams::tolerance, "tolerance").doc("Tolerance").unit(Unit::Metre)});
}

RuleSpec spec_below() {
    return RuleSpec::pair<Below>(
        "Below", "Below", {Slot::Source, Slot::Target},
        "Flags the pairs whose target sits below the source, per the bounding method.",
        {param(&BelowParams::below_type, "below_type").doc("Bounding method").values(kBelowTypes),
         param(&BelowParams::tolerance, "tolerance").doc("Tolerance").unit(Unit::Metre)});
}

RuleSpec spec_obb_above() {
    return RuleSpec::pair<ObbAbove>(
        "OBB_Above", "OBB Above", {Slot::Source, Slot::Target},
        "Flags a target penetrating the detection band extruded above the source OBB.",
        {param(&ObbZoneParams::tolerance, "tolerance").doc("Height of the detection band above the source").unit(Unit::Metre)});
}

RuleSpec spec_obb_below() {
    return RuleSpec::pair<ObbBelow>(
        "OBB_Below", "OBB Below", {Slot::Source, Slot::Target},
        "Flags a target penetrating the detection band extruded below the source OBB.",
        {param(&ObbZoneParams::tolerance, "tolerance").doc("Height of the detection band below the source").unit(Unit::Metre)});
}

RuleSpec spec_obb_front_and_back() {
    return RuleSpec::pair<ObbFrontAndBack>(
        "OBB_Front_And_Back", "OBB Front And Back", {Slot::Source, Slot::Target},
        "Flags a target penetrating the detection bands in front of and behind the source.",
        {param(&FrontBackParams::tolerance, "tolerance").doc("Depth of the detection bands").unit(Unit::Metre),
         param(&FrontBackParams::direction_method, "direction_method").doc("Front direction").values({"Wide", "Narrow"})});
}

RuleSpec spec_obb_custom() {
    return RuleSpec::pair<ObbCustom>(
        "OBB_Custom", "OBB Custom", {Slot::Source, Slot::Target},
        "Flags a target penetrating custom detection zones around the source.",
        {param(&CustomParams::list_of_modifications, "list_of_modifications")
             .doc("Zone modifications, one per line (ex. 'detach_top_by_extrude:0.5', 'NEW_OBB')")});
}

}  // namespace ifcclash
