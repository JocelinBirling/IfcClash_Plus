// The one-object rules of Rules.py: Area, TopOrBottomSurface, LateralSurface,
// ProjectedSurface, ObbHigh, ObbLength, Orientation. Each one follows its
// Python compute() step by step, on the same IfcOpenShell geometry variant.
// The bounds are open (strict comparisons), as in Python today.
#include "AllRules.h"

#include "../geometry/Geos.h"
#include "../geometry/Obb.h"

#include <gp_Dir.hxx>

#include <cmath>

namespace ifcclash {

namespace {

constexpr double kRadToDeg = 180.0 / M_PI;  // math.degrees
const std::vector<std::string> kWideNarrow{"Wide", "Narrow"};

Point3 xyz(const gp_XYZ& v) { return {v.X(), v.Y(), v.Z()}; }

// ---------------------------------------------------------------- Area
struct AreaParams {
    double volume_min = 0.0;  // the serialized key names of the Python rule
    double volume_max = 100.0;
};

class Area final : public ElementRule<AreaParams> {
public:
    bool parallel_safe() const override { return true; }
    Level narrow_level() const override { return Level::Mesh; }
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto mesh = e.mesh();
        if (!mesh) return v;
        const double area = geometry::mesh_area(mesh->local_verts, mesh->faces);  // get_area
        v.status = params().volume_min < area && area < params().volume_max;
        v.measures.set(Measure::Area, area);
        return v;
    }
};

// ---------------------------------------------------------------- TopOrBottomSurface
struct TopOrBottomParams {
    double surface_min = 0.0;
    double surface_max = 100.0;
    std::string top_or_bot_method = "Top";
};

class TopOrBottomSurface final : public ElementRule<TopOrBottomParams> {
public:
    bool parallel_safe() const override { return true; }
    Level narrow_level() const override { return Level::Mesh; }
    std::vector<Variant> narrow_variants() const override { return {Variant::MeshWorld}; }
    Variant base_variant() const override { return Variant::MeshWorld; }
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto mesh = e.mesh(Variant::MeshWorld);
        if (!mesh) return v;
        const geometry::Vec3 direction{0.0, 0.0, params().top_or_bot_method == "Top" ? 1.0 : -1.0};
        geometry::Geos geos;
        const auto& verts = mesh->local_verts;  // get_vertices: the iterator output (world here)
        const auto faces = geometry::extreme_faces(verts, mesh->faces, direction, geos);
        double area = 0.0;
        for (int t : faces) {
            area += geometry::triangle_area(geometry::vertex(verts, mesh->faces[3 * t]),
                                            geometry::vertex(verts, mesh->faces[3 * t + 1]),
                                            geometry::vertex(verts, mesh->faces[3 * t + 2]));
        }
        v.status = params().surface_min < area && area < params().surface_max;
        if (!v.status) return v;
        v.measures.set(Measure::Area, area);
        for (int t : faces) {
            const FaceData face = geometry::triangle_face_data(geometry::vertex(verts, mesh->faces[3 * t]),
                                                               geometry::vertex(verts, mesh->faces[3 * t + 1]),
                                                               geometry::vertex(verts, mesh->faces[3 * t + 2]));
            v.faces.push_back({face, face});  // a one-object rule pairs each face with itself
        }
        return v;
    }
};

// ---------------------------------------------------------------- Lateral / Projected surface
struct DirectionalSurfaceParams {
    double surface_min = 0.0;
    double surface_max = 100.0;
    std::array<double, 3> direction{0.0, 0.0, 1.0};
};

class LateralSurface final : public ElementRule<DirectionalSurfaceParams> {
public:
    bool parallel_safe() const override { return true; }
    Level narrow_level() const override { return Level::Mesh; }
    std::vector<Variant> narrow_variants() const override { return {Variant::MeshWorld}; }
    Variant base_variant() const override { return Variant::MeshWorld; }
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto mesh = e.mesh(Variant::MeshWorld);
        if (!mesh) return v;
        const double area = geometry::side_area(mesh->local_verts, mesh->faces, params().direction, 45.0);
        v.status = params().surface_min < area && area < params().surface_max;
        v.measures.set(Measure::Area, area);
        return v;
    }
};

class ProjectedSurface final : public ElementRule<DirectionalSurfaceParams> {
public:
    bool parallel_safe() const override { return true; }
    Level narrow_level() const override { return Level::Mesh; }
    std::vector<Variant> narrow_variants() const override { return {Variant::MeshWorld}; }
    Variant base_variant() const override { return Variant::MeshWorld; }
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto mesh = e.mesh(Variant::MeshWorld);
        if (!mesh) return v;
        geometry::Geos geos;
        const double area = geometry::footprint_area(mesh->local_verts, mesh->faces, params().direction, geos);
        v.status = params().surface_min < area && area < params().surface_max;
        v.measures.set(Measure::Area, area);
        return v;
    }
};

// ---------------------------------------------------------------- ObbHigh / ObbLength
struct ObbHighParams {
    double length_min = 0.0;
    double length_max = 100.0;
};

class ObbHigh final : public ElementRule<ObbHighParams> {
public:
    bool parallel_safe() const override { return true; }
    std::vector<Variant> narrow_variants() const override { return {Variant::BrepWorld}; }
    Variant base_variant() const override { return Variant::BrepWorld; }
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto brep = e.meshed_brep();
        if (!brep) return v;
        const Bnd_OBB& obb = brep->obb;
        const auto corners = geometry::obb_corners(obb);
        double min_z = corners[0].Z(), max_z = corners[0].Z();
        for (const auto& c : corners) {
            min_z = std::min(min_z, c.Z());
            max_z = std::max(max_z, c.Z());
        }
        const double value = max_z - min_z;
        v.status = params().length_min < value && value < params().length_max;
        if (!v.status) return v;
        v.measures.set(Measure::Offset, value);
        v.source_obbs.push_back(geometry::obb_data(obb, "object"));
        return v;
    }
};

struct ObbLengthParams {
    double length_min = 0.0;
    double length_max = 100.0;
    std::string direction_method = "Wide";
};

class ObbLength final : public ElementRule<ObbLengthParams> {
public:
    bool parallel_safe() const override { return true; }
    std::vector<Variant> narrow_variants() const override { return {Variant::BrepWorld}; }
    Variant base_variant() const override { return Variant::BrepWorld; }
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto brep = e.meshed_brep();
        if (!brep) return v;
        const Bnd_OBB& obb = brep->obb;
        // The vertical axis of the box is its most vertical axis (first max).
        const double half[3] = {obb.XHSize(), obb.YHSize(), obb.ZHSize()};
        const double vert[3] = {std::abs(obb.XDirection().Z()), std::abs(obb.YDirection().Z()),
                                std::abs(obb.ZDirection().Z())};
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
        v.source_obbs.push_back(geometry::obb_data(obb, "object"));
        return v;
    }
};

// ---------------------------------------------------------------- Orientation
struct OrientationParams {
    std::array<double, 3> orientation{0.0, 0.0, 1.0};
    std::string orientation_type = "Parrallel";
    std::string direction_method = "Wide";
    double angular_tolerance = 0.1;  // passed to gp_Dir::IsParallel (radians), as in Python
};

class Orientation final : public ElementRule<OrientationParams> {
public:
    bool parallel_safe() const override { return true; }
    std::vector<Variant> narrow_variants() const override { return {Variant::BrepWorld}; }
    Variant base_variant() const override { return Variant::BrepWorld; }
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto brep = e.meshed_brep();
        if (!brep) return v;
        const auto& o = params().orientation;
        const gp_Dir expected(o[0], o[1], o[2]);
        const Bnd_OBB& obb = brep->obb;
        const gp_Dir dir1 = geometry::two_main_directions(obb, params().direction_method).first;
        const gp_Pnt center = geometry::shape_center(brep->shape);  // after the meshing, as in Python
        const bool parallel = expected.IsParallel(dir1, params().angular_tolerance);
        v.status = params().orientation_type == "Parrallel" ? parallel : !parallel;
        if (!v.status) return v;
        v.measures.set(Measure::Angle, dir1.Angle(expected) * kRadToDeg);
        const Point3 c{center.X(), center.Y(), center.Z()};
        v.axes.push_back({c, xyz(dir1.XYZ()), 0.5, std::string("obb")});
        v.axes.push_back({c, xyz(expected.XYZ()), 0.5, std::string("expected")});
        return v;
    }
};

}  // namespace

RuleSpec spec_area() {
    return RuleSpec::element<Area>(
        "Area", "Area", {Slot::Source}, "Flags every source whose area is inside ]volume_min, volume_max[.",
        {param(&AreaParams::volume_min, "volume_min").doc("Minimum area").unit(Unit::SquareMetre),
         param(&AreaParams::volume_max, "volume_max").doc("Maximum area").unit(Unit::SquareMetre)});
}

RuleSpec spec_top_or_bottom_surface() {
    return RuleSpec::element<TopOrBottomSurface>(
        "TopOrBottomSurface", "Top Or Bottom Surface", {Slot::Source},
        "Flags a source whose top (or bottom) face area is inside the bounds.",
        {param(&TopOrBottomParams::surface_min, "surface_min").doc("Minimum surface").unit(Unit::SquareMetre),
         param(&TopOrBottomParams::surface_max, "surface_max").doc("Maximum surface").unit(Unit::SquareMetre),
         param(&TopOrBottomParams::top_or_bot_method, "top_or_bot_method").doc("Which extreme face").values({"Top", "Bottom"})});
}

RuleSpec spec_lateral_surface() {
    return RuleSpec::element<LateralSurface>(
        "LateralSurface", "Lateral Surface", {Slot::Source},
        "Flags a source whose lateral surface is inside the bounds.",
        {param(&DirectionalSurfaceParams::surface_min, "surface_min").doc("Minimum surface").unit(Unit::SquareMetre),
         param(&DirectionalSurfaceParams::surface_max, "surface_max").doc("Maximum surface").unit(Unit::SquareMetre),
         param(&DirectionalSurfaceParams::direction, "direction").doc("Measurement direction")});
}

RuleSpec spec_projected_surface() {
    return RuleSpec::element<ProjectedSurface>(
        "ProjectedSurface", "Projected Surface", {Slot::Source},
        "Flags a source whose projected surface is inside the bounds.",
        {param(&DirectionalSurfaceParams::surface_min, "surface_min").doc("Minimum surface").unit(Unit::SquareMetre),
         param(&DirectionalSurfaceParams::surface_max, "surface_max").doc("Maximum surface").unit(Unit::SquareMetre),
         param(&DirectionalSurfaceParams::direction, "direction").doc("Projection direction")});
}

RuleSpec spec_obb_high() {
    return RuleSpec::element<ObbHigh>(
        "ObbHigh", "Obb High", {Slot::Source}, "Flags a source whose OBB height is inside ]length_min, length_max[.",
        {param(&ObbHighParams::length_min, "length_min").doc("Minimum height").unit(Unit::Metre),
         param(&ObbHighParams::length_max, "length_max").doc("Maximum height").unit(Unit::Metre)});
}

RuleSpec spec_obb_length() {
    return RuleSpec::element<ObbLength>(
        "ObbLength", "Obb Length", {Slot::Source}, "Flags a source whose OBB length is inside ]length_min, length_max[.",
        {param(&ObbLengthParams::length_min, "length_min").doc("Minimum length").unit(Unit::Metre),
         param(&ObbLengthParams::length_max, "length_max").doc("Maximum length").unit(Unit::Metre),
         param(&ObbLengthParams::direction_method, "direction_method").doc("OBB axis choice").values(kWideNarrow)});
}

RuleSpec spec_orientation() {
    return RuleSpec::element<Orientation>(
        "Orientation", "Orientation", {Slot::Source},
        "Flags a source whose orientation matches (or not) the reference direction.",
        {param(&OrientationParams::orientation, "orientation").doc("Reference direction"),
         param(&OrientationParams::orientation_type, "orientation_type").doc("Relation to the direction").values({"Parrallel", "Perpendicular"}),
         param(&OrientationParams::direction_method, "direction_method").doc("OBB axis choice").values(kWideNarrow),
         param(&OrientationParams::angular_tolerance, "angular_tolerance").doc("Angular tolerance (gp_Dir::IsParallel)")});
}

}  // namespace ifcclash
