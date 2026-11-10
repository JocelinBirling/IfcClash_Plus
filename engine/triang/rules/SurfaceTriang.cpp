// IfcClash_Plus engine — the _triang measures of one element
// (engine/triang/rules): Volume, Area, TopOrBottomSurface, LateralSurface,
// ProjectedSurface.
//
// The original rules already work on a triangulation, but trust its winding:
// LateralSurface and ProjectedSurface keep the triangles whose normal points
// along the direction, TopOrBottomSurface starts from the same filter, and
// many IFC meshes are wound inwards (Revit MEP). On the TriMesh (welded,
// winding made consistent and turned outwards) and on the seen triangles
// (a covering test), the _triang rules do not depend on the winding:
//  - Volume_triang: the volume of the TriMesh (exact for a closed mesh);
//  - Area_triang: its area;
//  - TopOrBottomSurface_triang: the faces of the original (extreme_faces:
//    turned up / down, not covered by a higher one) on the repaired mesh;
//  - LateralSurface_triang: the area of the triangles whose outward normal is
//    within 45° of the direction (the criterion of the original);
//  - ProjectedSurface_triang: the area of the union of the projections of
//    every triangle not seen edge-on (the projection of a solid is that of
//    its front faces; taking them all needs no normal).
// Same parameters and result blocks as the original rules.
#include "Common.h"

#include "../../geometry/Geos.h"
#include "../../geometry/MeshMeasures.h"
#include "../../registry/RuleSpec.h"

#include <cmath>

namespace ifcclash {

namespace {

using namespace triang;

// ---------------------------------------------------------------- Volume_triang
struct VolumeParams {
    double volume_min = 0.0;    // m3
    double volume_max = 100.0;  // m3
};

class VolumeTriang final : public TriElementRule<VolumeParams> {
public:
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto mesh = tri_mesh(e);
        if (!mesh) return v;
        const double volume = mesh->volume();
        v.status = params().volume_min < volume && volume < params().volume_max;
        v.measures.set(Measure::Volume, volume);
        return v;
    }
};

// ---------------------------------------------------------------- Area_triang
struct AreaParams {
    double volume_min = 0.0;  // the serialized key names of the original rule
    double volume_max = 100.0;
};

class AreaTriang final : public TriElementRule<AreaParams> {
public:
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto mesh = tri_mesh(e);
        if (!mesh) return v;
        const double area = mesh->total_area();
        v.status = params().volume_min < area && area < params().volume_max;
        v.measures.set(Measure::Area, area);
        return v;
    }
};

// ---------------------------------------------------------------- TopOrBottomSurface_triang
struct TopOrBottomParams {
    double surface_min = 0.0;
    double surface_max = 100.0;
    std::string top_or_bot_method = "Top";
};

geometry::Vec3 corner(const TriMesh& m, size_t t, int k) {
    const P3 p = m.vertex(m.faces()[3 * t + size_t(k)]);
    return {p[0], p[1], p[2]};
}

class TopOrBottomSurfaceTriang final : public TriElementRule<TopOrBottomParams> {
public:
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto mesh = tri_mesh(e);
        if (!mesh) return v;
        // The selection of the original (extreme_faces: turned to the side,
        // normal component > 0.1, and not covered at 99 % by a higher
        // triangle turned the same way), on the repaired mesh: the normals
        // no longer depend on the IFC winding. Neither a sampled test (a
        // triangle partly covered, a sill under a frame) nor the height map
        // (steep sides counted whole) gives the same faces.
        const double side = params().top_or_bot_method == "Top" ? 1.0 : -1.0;
        geometry::Geos geos;
        const std::vector<int> kept = geometry::extreme_faces(mesh->verts(), mesh->faces(), {0.0, 0.0, side}, geos);
        const auto* seen = &kept;
        double area = 0.0;
        for (int t : *seen) area += mesh->area(size_t(t));
        v.status = params().surface_min < area && area < params().surface_max;
        if (!v.status) return v;
        v.measures.set(Measure::Area, area);
        for (int t : *seen) {
            const FaceData face =
                geometry::triangle_face_data(corner(*mesh, size_t(t), 0), corner(*mesh, size_t(t), 1),
                                             corner(*mesh, size_t(t), 2));
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

class LateralSurfaceTriang final : public TriElementRule<DirectionalSurfaceParams> {
public:
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto mesh = tri_mesh(e);
        if (!mesh) return v;
        // The criterion of the original, on the repaired (outward) winding.
        const double area = geometry::side_area(mesh->verts(), mesh->faces(), params().direction, 45.0);
        v.status = params().surface_min < area && area < params().surface_max;
        v.measures.set(Measure::Area, area);
        return v;
    }
};

class ProjectedSurfaceTriang final : public TriElementRule<DirectionalSurfaceParams> {
public:
    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto mesh = tri_mesh(e);
        if (!mesh) return v;
        const auto& d = params().direction;
        const double len = std::sqrt(d[0] * d[0] + d[1] * d[1] + d[2] * d[2]);
        if (len == 0.0) return v;
        // Every triangle not seen edge-on, turned to face the direction: the
        // footprint of the original then keeps them all.
        std::vector<int> faces;
        faces.reserve(mesh->faces().size());
        for (size_t t = 0; t < mesh->triangle_count(); ++t) {
            const P3& n = mesh->normal(t);
            const double c = (n[0] * d[0] + n[1] * d[1] + n[2] * d[2]) / len;
            const int a = mesh->faces()[3 * t], b = mesh->faces()[3 * t + 1], cc = mesh->faces()[3 * t + 2];
            if (c > 0.01) faces.insert(faces.end(), {a, b, cc});
            else if (c < -0.01) faces.insert(faces.end(), {a, cc, b});
        }
        geometry::Geos geos;
        const double area = geometry::footprint_area(mesh->verts(), faces, d, geos);
        v.status = params().surface_min < area && area < params().surface_max;
        v.measures.set(Measure::Area, area);
        return v;
    }
};

}  // namespace

RuleSpec spec_volume_triang() {
    return RuleSpec::element<VolumeTriang>(
        "Volume_triang", "Volume (triangles)", {Slot::Source},
        "Volume on the triangles: flags every source whose volume is inside ]volume_min, volume_max[.",
        {param(&VolumeParams::volume_min, "volume_min").doc("Minimum volume").unit(Unit::CubicMetre),
         param(&VolumeParams::volume_max, "volume_max").doc("Maximum volume").unit(Unit::CubicMetre)});
}

RuleSpec spec_area_triang() {
    return RuleSpec::element<AreaTriang>(
        "Area_triang", "Area (triangles)", {Slot::Source},
        "Area on the triangles: flags every source whose area is inside ]volume_min, volume_max[.",
        {param(&AreaParams::volume_min, "volume_min").doc("Minimum area").unit(Unit::SquareMetre),
         param(&AreaParams::volume_max, "volume_max").doc("Maximum area").unit(Unit::SquareMetre)});
}

RuleSpec spec_top_or_bottom_surface_triang() {
    return RuleSpec::element<TopOrBottomSurfaceTriang>(
        "TopOrBottomSurface_triang", "Top Or Bottom Surface (triangles)", {Slot::Source},
        "TopOrBottomSurface on the triangles: flags a source whose area seen from above (below) is inside the "
        "bounds.",
        {param(&TopOrBottomParams::surface_min, "surface_min").doc("Minimum surface").unit(Unit::SquareMetre),
         param(&TopOrBottomParams::surface_max, "surface_max").doc("Maximum surface").unit(Unit::SquareMetre),
         param(&TopOrBottomParams::top_or_bot_method, "top_or_bot_method")
             .doc("Which extreme face")
             .values({"Top", "Bottom"})});
}

RuleSpec spec_lateral_surface_triang() {
    return RuleSpec::element<LateralSurfaceTriang>(
        "LateralSurface_triang", "Lateral Surface (triangles)", {Slot::Source},
        "LateralSurface on the triangles: flags a source whose lateral surface is inside the bounds.",
        {param(&DirectionalSurfaceParams::surface_min, "surface_min").doc("Minimum surface").unit(Unit::SquareMetre),
         param(&DirectionalSurfaceParams::surface_max, "surface_max").doc("Maximum surface").unit(Unit::SquareMetre),
         param(&DirectionalSurfaceParams::direction, "direction").doc("Measurement direction")});
}

RuleSpec spec_projected_surface_triang() {
    return RuleSpec::element<ProjectedSurfaceTriang>(
        "ProjectedSurface_triang", "Projected Surface (triangles)", {Slot::Source},
        "ProjectedSurface on the triangles: flags a source whose projected surface is inside the bounds.",
        {param(&DirectionalSurfaceParams::surface_min, "surface_min").doc("Minimum surface").unit(Unit::SquareMetre),
         param(&DirectionalSurfaceParams::surface_max, "surface_max").doc("Maximum surface").unit(Unit::SquareMetre),
         param(&DirectionalSurfaceParams::direction, "direction").doc("Projection direction")});
}

}  // namespace ifcclash
