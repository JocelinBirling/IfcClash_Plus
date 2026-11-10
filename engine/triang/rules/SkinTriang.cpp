// IfcClash_Plus engine — the _triang rules measured skin to skin
// (engine/triang/rules): ClearanceAxisToAxis, SurfaceRecover.
//
// The logic of the original rules is reused as is (rules/AxisRules.h,
// rules/SurfaceRecover.h); only the geometry changes:
//  - the OBB is the optimal box of the vertices of the triangles (tri_obb);
//  - the skin distance (the Fallback of ClearanceAxisToAxis, the contact of
//    SurfaceRecover) is the triangle to triangle distance, branch and bound
//    on the BVH (mesh_distance) instead of BRepExtrema on the meshed B-Reps;
//  - SurfaceRecover selects its extreme triangles by their normal: it reads
//    the TriMesh, whose winding is repaired and turned outwards.
#include "Common.h"

#include "../../registry/RuleSpec.h"
#include "../../rules/AxisRules.h"
#include "../../rules/SurfaceRecover.h"
#include "../spatial/Proximity.h"

namespace ifcclash {

namespace {

using namespace triang;

// ================================================================ ClearanceAxisToAxis_triang

class ClearanceAxisToAxisTriang final : public ClearanceAxisToAxis {
public:
    Level narrow_level() const override { return Level::Mesh; }
    Variant base_variant() const override { return Variant::Triangles; }
    std::vector<Variant> narrow_variants() const override { return {}; }

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role) const override {
        const auto mesh = tri_mesh(e);
        const auto obb = tri_obb(e);
        if (!mesh || !obb) return nullptr;
        auto data = std::make_shared<LongAxis>();
        long_axis(*obb, *data);
        data->skin = mesh;
        data->box = mesh->bounds();
        return data;
    }

protected:
    double skin_distance(const LongAxis& s, const LongAxis& t, std::optional<std::array<double, 3>>& ps,
                         std::optional<std::array<double, 3>>& pt) const override {
        const auto& a = *std::static_pointer_cast<const TriMesh>(s.skin);
        const auto& b = *std::static_pointer_cast<const TriMesh>(t.skin);
        const MeshDistance d = mesh_distance(a, b);
        ps = d.a;
        pt = d.b;
        return d.distance;
    }
};

// ================================================================ SurfaceRecover_triang

class SurfaceRecoverTriang final : public SurfaceRecover {
public:
    Level narrow_level() const override { return Level::Mesh; }
    Variant base_variant() const override { return Variant::Triangles; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    std::vector<Variant> data_variants() const override { return {}; }

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role) const override {
        const auto mesh = tri_mesh(e);
        const auto obb = tri_obb(e);
        if (!mesh || !obb) return nullptr;
        auto data = std::make_shared<RecoverData>();
        data->skin = mesh;
        data->obb = *obb;
        data->box = geometry::obb_aabb(*obb);
        data->verts = mesh->verts();
        data->faces = mesh->faces();
        V3 sum{0, 0, 0};
        const size_t n = mesh->vertex_count();
        for (size_t i = 0; i < n; ++i)
            for (int k = 0; k < 3; ++k) sum[size_t(k)] += data->verts[3 * i + size_t(k)];
        data->centroid = {sum[0] / double(n), sum[1] / double(n), sum[2] / double(n)};
        return data;
    }

protected:
    double skin_distance(const RecoverData& s, const RecoverData& t, std::optional<V3>& ps,
                         std::optional<V3>& pt) const override {
        const auto& a = *std::static_pointer_cast<const TriMesh>(s.skin);
        const auto& b = *std::static_pointer_cast<const TriMesh>(t.skin);
        // Only the pairs within the tolerance go on: the search stops beyond.
        const MeshDistance d = mesh_distance(a, b, params().tolerance);
        ps = d.a;
        pt = d.b;
        return d.distance;
    }
};

}  // namespace

RuleSpec spec_clearance_axis_to_axis_triang() {
    return RuleSpec::pair<ClearanceAxisToAxisTriang>(
        "ClearanceAxisToAxis_triang", "Clearance Axis To Axis (triangles)", {Slot::Source, Slot::Target},
        "ClearanceAxisToAxis on the triangles: axis to axis, the pairs of linear elements closer than "
        "min_distance and each source farther than max_distance from its nearest target.",
        {param(&AxisToAxisParams::mode, "mode").doc("Distance mode").values({"Perpendicular", "MinDistance"}),
         param(&AxisToAxisParams::min_distance, "min_distance").doc("Minimum distance").unit(Unit::Metre),
         param(&AxisToAxisParams::max_distance, "max_distance").doc("Maximum distance").unit(Unit::Metre),
         param(&AxisToAxisParams::tolerance, "tolerance").doc("Distance tolerance").unit(Unit::Metre),
         param(&AxisToAxisParams::linearity_ratio, "linearity_ratio").doc("Linearity ratio"),
         param(&AxisToAxisParams::on_non_linear, "on_non_linear")
             .doc("Non linear elements")
             .values({"Skip", "Fallback"}),
         param(&AxisToAxisParams::parallel_tolerance, "parallel_tolerance")
             .doc("Parallelism tolerance")
             .unit(Unit::Degree),
         param(&AxisToAxisParams::search_radius, "search_radius").doc("Neighbour search radius").unit(Unit::Metre)});
}

RuleSpec spec_surface_recover_triang() {
    return RuleSpec::pair<SurfaceRecoverTriang>(
        "SurfaceRecover_triang", "Surface Recover (triangles)", {Slot::Source, Slot::Target},
        "SurfaceRecover on the triangles: checks that the target surface is covered by the source (ex. a "
        "coating).",
        {param(&SurfaceRecoverParams::direction, "direction").doc("Recovery direction: Auto, Top, Bottom or a vector"),
         param(&SurfaceRecoverParams::reference, "reference").doc("Reference surface").values({"Source", "Target"}),
         param(&SurfaceRecoverParams::tolerance, "tolerance").doc("Tolerance").unit(Unit::Metre),
         param(&SurfaceRecoverParams::min_covering, "min_covering")
             .doc("Minimum covering: an area (m2) or a percentage ('50%')"),
         param(&SurfaceRecoverParams::max_covering, "max_covering")
             .doc("Maximum covering: an area (m2) or a percentage ('50%')")});
}

}  // namespace ifcclash
