// IfcClash_Plus engine — the _triang face rules (engine/triang/rules):
// OneObjectFace, TwoObjectsFace.
//
// The logic of the original rules is reused as is (rules/FaceRules.h): face
// selection (orientation Top / Bottom / Side / vector, surface bounds,
// extreme faces, materials) and the checks (distance, intersection,
// orientation) between triangles. Only the triangles change: the TriMesh
// (welded, winding repaired and turned outwards), so a selection by
// orientation does not depend on the winding of the IFC triangulation.
#include "Common.h"

#include "../../registry/RuleSpec.h"
#include "../../rules/FaceRules.h"

namespace ifcclash {

namespace {

using namespace triang;

// The TriMesh as a Mesh (the face rules read Mesh::local_verts / faces),
// kept in the Session.
std::shared_ptr<const Mesh> face_mesh_of(const ElementGeometry& e) {
    return derived<Mesh>(e, "tri_face_mesh", [&e]() -> std::shared_ptr<const Mesh> {
        const auto mesh = tri_mesh(e);
        if (!mesh) return nullptr;
        auto m = std::make_shared<Mesh>();
        m->local_verts = mesh->verts();
        m->world_verts = mesh->verts();
        m->faces = mesh->faces();
        return m;
    });
}

class OneObjectFaceTriang final : public OneObjectFace {
public:
    Variant base_variant() const override { return Variant::Triangles; }
    std::vector<Variant> narrow_variants() const override { return {}; }

protected:
    std::shared_ptr<const Mesh> face_mesh(const ElementGeometry& e) const override { return face_mesh_of(e); }
};

class TwoObjectsFaceTriang final : public TwoObjectsFace {
public:
    Variant base_variant() const override { return Variant::Triangles; }
    std::vector<Variant> narrow_variants() const override { return {}; }

protected:
    std::shared_ptr<const Mesh> face_mesh(const ElementGeometry& e) const override { return face_mesh_of(e); }
};

}  // namespace

RuleSpec spec_one_object_face_triang() {
    return RuleSpec::element<OneObjectFaceTriang>(
        "OneObjectFace_triang", "One Object Face (triangles)", {Slot::Source},
        "OneObjectFace on the triangles: face check of one element against itself (distance, intersection, "
        "orientation).",
        {param(&OneFaceParams::face_a_selection, "face_a_selection").doc("First face selection (empty = all)"),
         param(&OneFaceParams::face_b_selection, "face_b_selection").doc("Second face selection (empty = all)"),
         param(&OneFaceParams::distance, "distance").doc("Measure the distance"),
         param(&OneFaceParams::min_distance, "min_distance").doc("Minimum distance").unit(Unit::Metre),
         param(&OneFaceParams::max_distance, "max_distance").doc("Maximum distance").unit(Unit::Metre),
         param(&OneFaceParams::skip_adjacent, "skip_adjacent").doc("Skip adjacent faces"),
         param(&OneFaceParams::intersection, "intersection").doc("Check the intersection"),
         param(&OneFaceParams::intersection_tolerance, "intersection_tolerance")
             .doc("Intersection tolerance")
             .unit(Unit::Metre),
         param(&OneFaceParams::orientation, "orientation").doc("Check the orientation"),
         param(&OneFaceParams::angle, "angle").doc("Angle").unit(Unit::Degree),
         param(&OneFaceParams::angle_tolerance, "angle_tolerance").doc("Angle tolerance").unit(Unit::Degree)});
}

RuleSpec spec_two_objects_face_triang() {
    return RuleSpec::pair<TwoObjectsFaceTriang>(
        "TwoObjectsFace_triang", "Two Objects Face (triangles)", {Slot::Source, Slot::Target},
        "TwoObjectsFace on the triangles: face check of the source faces against the target faces.",
        {param(&TwoFaceParams::source_face_selection, "source_face_selection")
             .doc("Source face selection (empty = all)"),
         param(&TwoFaceParams::target_face_selection, "target_face_selection")
             .doc("Target face selection (empty = all)"),
         param(&TwoFaceParams::distance, "distance").doc("Measure the distance"),
         param(&TwoFaceParams::min_distance, "min_distance").doc("Minimum distance").unit(Unit::Metre),
         param(&TwoFaceParams::max_distance, "max_distance").doc("Maximum distance").unit(Unit::Metre),
         param(&TwoFaceParams::intersection, "intersection").doc("Check the intersection"),
         param(&TwoFaceParams::intersection_tolerance, "intersection_tolerance")
             .doc("Intersection tolerance")
             .unit(Unit::Metre),
         param(&TwoFaceParams::orientation, "orientation").doc("Check the orientation"),
         param(&TwoFaceParams::angle, "angle").doc("Angle").unit(Unit::Degree),
         param(&TwoFaceParams::angle_tolerance, "angle_tolerance").doc("Angle tolerance").unit(Unit::Degree)});
}

}  // namespace ifcclash
