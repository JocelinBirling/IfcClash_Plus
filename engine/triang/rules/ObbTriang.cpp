// IfcClash_Plus engine — the _triang rules built on the OBB of the triangles
// (engine/triang/rules): ObbHigh, ObbLength, Orientation, AngleBetween,
// Alignement.
//
// Same parameters, same tests and same result blocks as the original rules;
// the OBB is the optimal box of the vertices of the triangles (tri_obb) instead
// of the optimal box of the B-Rep meshed at 0.01 m, and the centre is the
// centre of the box of the triangles instead of the one of the meshed B-Rep.
#include "Common.h"

#include "../../registry/RuleSpec.h"
#include "../../rules/Alignement.h"

#include <gp_Dir.hxx>

#include <cctype>
#include <cmath>

namespace ifcclash {

namespace {

using namespace triang;

constexpr double kRadToDeg = 180.0 / M_PI;
const std::vector<std::string> kWideNarrow{"Wide", "Narrow"};

Point3 xyz(const gp_XYZ& v) { return {v.X(), v.Y(), v.Z()}; }

// ---------------------------------------------------------------- ObbHigh_triang
struct ObbHighParams {
    double length_min = 0.0;
    double length_max = 100.0;
};

class ObbHighTriang final : public TriElementRule<ObbHighParams> {
public:
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto obb = tri_obb(e);
        if (!obb) return v;
        const auto corners = geometry::obb_corners(*obb);
        double min_z = corners[0].Z(), max_z = corners[0].Z();
        for (const auto& c : corners) {
            min_z = std::min(min_z, c.Z());
            max_z = std::max(max_z, c.Z());
        }
        const double value = max_z - min_z;
        v.status = params().length_min < value && value < params().length_max;
        if (!v.status) return v;
        v.measures.set(Measure::Offset, value);
        v.source_obbs.push_back(geometry::obb_data(*obb, "object"));
        return v;
    }
};

// ---------------------------------------------------------------- ObbLength_triang
struct ObbLengthParams {
    double length_min = 0.0;
    double length_max = 100.0;
    std::string direction_method = "Wide";
};

class ObbLengthTriang final : public TriElementRule<ObbLengthParams> {
public:
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto obb = tri_obb(e);
        if (!obb) return v;
        // The vertical axis of the box is its most vertical axis (first max).
        const double half[3] = {obb->XHSize(), obb->YHSize(), obb->ZHSize()};
        const double vert[3] = {std::abs(obb->XDirection().Z()), std::abs(obb->YDirection().Z()),
                                std::abs(obb->ZDirection().Z())};
        int height_axis = 0;
        for (int i = 1; i < 3; ++i)
            if (vert[i] > vert[height_axis]) height_axis = i;
        std::vector<double> plan;
        for (int i = 0; i < 3; ++i)
            if (i != height_axis) plan.push_back(2.0 * half[i]);
        std::string method = params().direction_method;
        for (auto& c : method) c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        const double value = method == "wide" ? std::max(plan[0], plan[1]) : std::min(plan[0], plan[1]);
        v.status = params().length_min < value && value < params().length_max;
        if (!v.status) return v;
        v.measures.set(Measure::Offset, value);
        v.source_obbs.push_back(geometry::obb_data(*obb, "object"));
        return v;
    }
};

// ---------------------------------------------------------------- Orientation_triang
struct OrientationParams {
    std::array<double, 3> orientation{0.0, 0.0, 1.0};
    std::string orientation_type = "Parrallel";
    std::string direction_method = "Wide";
    double angular_tolerance = 0.1;  // gp_Dir::IsParallel (radians), as the original
};

class OrientationTriang final : public TriElementRule<OrientationParams> {
public:
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto obb = tri_obb(e);
        const auto center = box_center(e);
        if (!obb || !center) return v;
        const auto& o = params().orientation;
        const gp_Dir expected(o[0], o[1], o[2]);
        const gp_Dir dir1 = geometry::two_main_directions(*obb, params().direction_method).first;
        const bool parallel = expected.IsParallel(dir1, params().angular_tolerance);
        v.status = params().orientation_type == "Parrallel" ? parallel : !parallel;
        if (!v.status) return v;
        v.measures.set(Measure::Angle, dir1.Angle(expected) * kRadToDeg);
        v.axes.push_back({*center, xyz(dir1.XYZ()), 0.5, std::string("obb")});
        v.axes.push_back({*center, xyz(expected.XYZ()), 0.5, std::string("expected")});
        return v;
    }
};

// ---------------------------------------------------------------- AngleBetween_triang
struct AngleParams {
    std::string direction_method_for_source = "Wide";
    std::string direction_method_for_target = "Wide";
    double angle_difference = 0.0;
    double angle_tolerance = 0.0;
};

struct Axis {
    gp_Dir direction;
    Point3 center;
};

class AngleBetweenTriang final : public TriPairRule<AngleParams> {
public:
    BroadMode broad_mode() const override { return BroadMode::AllPairs; }  // no spatial locality
    bool skip_self() const override { return false; }

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override {
        const auto obb = tri_obb(e);
        const auto center = box_center(e);
        if (!obb || !center) return nullptr;
        const auto& method =
            role == Role::Source ? params().direction_method_for_source : params().direction_method_for_target;
        return std::make_shared<const Axis>(Axis{geometry::two_main_directions(*obb, method).first, *center});
    }

    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override {
        const auto& a = s.as<Axis>();
        const auto& b = t.as<Axis>();
        const double angle = a.direction.Angle(b.direction) * kRadToDeg;
        double diff = std::abs(angle - params().angle_difference);
        diff = std::min(diff, 360 - diff);
        Verdict v;
        v.status = diff <= params().angle_tolerance;
        if (!v.status) return v;
        v.measures.set(Measure::Angle, angle);
        auto axis = [](const Axis& d, const char* label) {
            return AxisData{d.center, xyz(d.direction.XYZ()), 0.5, std::string(label)};
        };
        v.axes.push_back(axis(a, "source"));
        v.axes.push_back(axis(b, "target"));
        return v;
    }
};

// ---------------------------------------------------------------- Alignement_triang
// The grouping of Alignement, on the OBB of the triangles.
class AlignementTriang final : public Alignement {
public:
    Level narrow_level() const override { return Level::Mesh; }
    Variant base_variant() const override { return Variant::Triangles; }
    std::vector<Variant> narrow_variants() const override { return {}; }

protected:
    std::optional<Bnd_OBB> element_obb(const ElementGeometry& e) const override { return tri_obb(e); }
};

}  // namespace

RuleSpec spec_obb_high_triang() {
    return RuleSpec::element<ObbHighTriang>(
        "ObbHigh_triang", "Obb High (triangles)", {Slot::Source},
        "ObbHigh on the triangles: flags a source whose OBB height is inside ]length_min, length_max[.",
        {param(&ObbHighParams::length_min, "length_min").doc("Minimum height").unit(Unit::Metre),
         param(&ObbHighParams::length_max, "length_max").doc("Maximum height").unit(Unit::Metre)});
}

RuleSpec spec_obb_length_triang() {
    return RuleSpec::element<ObbLengthTriang>(
        "ObbLength_triang", "Obb Length (triangles)", {Slot::Source},
        "ObbLength on the triangles: flags a source whose OBB length is inside ]length_min, length_max[.",
        {param(&ObbLengthParams::length_min, "length_min").doc("Minimum length").unit(Unit::Metre),
         param(&ObbLengthParams::length_max, "length_max").doc("Maximum length").unit(Unit::Metre),
         param(&ObbLengthParams::direction_method, "direction_method").doc("OBB axis choice").values(kWideNarrow)});
}

RuleSpec spec_orientation_triang() {
    return RuleSpec::element<OrientationTriang>(
        "Orientation_triang", "Orientation (triangles)", {Slot::Source},
        "Orientation on the triangles: flags a source whose orientation matches (or not) the reference direction.",
        {param(&OrientationParams::orientation, "orientation").doc("Reference direction"),
         param(&OrientationParams::orientation_type, "orientation_type")
             .doc("Relation to the direction")
             .values({"Parrallel", "Perpendicular"}),
         param(&OrientationParams::direction_method, "direction_method").doc("OBB axis choice").values(kWideNarrow),
         param(&OrientationParams::angular_tolerance, "angular_tolerance")
             .doc("Angular tolerance (gp_Dir::IsParallel)")});
}

RuleSpec spec_angle_between_triang() {
    return RuleSpec::pair<AngleBetweenTriang>(
        "AngleBetween_triang", "Angle Between (triangles)", {Slot::Source, Slot::Target},
        "AngleBetween on the triangles: flags the pairs whose angle between the source and target OBB axes is "
        "angle_difference within angle_tolerance.",
        {param(&AngleParams::direction_method_for_source, "direction_method_for_source")
             .doc("Source OBB axis")
             .values(kWideNarrow),
         param(&AngleParams::direction_method_for_target, "direction_method_for_target")
             .doc("Target OBB axis")
             .values(kWideNarrow),
         param(&AngleParams::angle_difference, "angle_difference").doc("Expected angle (degrees)"),
         param(&AngleParams::angle_tolerance, "angle_tolerance").doc("Angle tolerance (degrees)")});
}

RuleSpec spec_alignement_triang() {
    return RuleSpec::set<AlignementTriang>(
        "Alignement_triang", "Alignement (triangles)", {Slot::Source},
        "Alignement on the triangles: flags the elements that are not part of an aligned group of at least "
        "min_group elements.",
        {param(&AlignementParams::axis, "axis").doc("Axis (empty = auto)").values({"", "Vertical", "Horizontal"}),
         param(&AlignementParams::alignment_type, "alignment_type").doc("Alignment type").values({"Line", "Plane"}),
         param(&AlignementParams::tolerance, "tolerance").doc("Tolerance").unit(Unit::Metre),
         param(&AlignementParams::min_group, "min_group").doc("Minimum group size")});
}

}  // namespace ifcclash
