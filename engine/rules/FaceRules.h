// IfcClash_Plus engine — OneObjectFace and TwoObjectsFace (Rules.py),
// declared here so that a variant can read its triangles elsewhere
// (OneObjectFace_triang, TwoObjectsFace_triang, engine/triang: the repaired
// triangles instead of the world triangulation).
#pragma once

#include "RuleBase.h"
#include "../geometry/Triangles.h"

#include <Bnd_Box.hxx>

#include <memory>
#include <optional>
#include <vector>

namespace ifcclash {

struct OneFaceParams {
    Json face_a_selection = Json::object();
    Json face_b_selection = Json::object();
    bool distance = false;
    std::optional<double> min_distance, max_distance;
    bool skip_adjacent = true;
    bool intersection = false;
    std::optional<double> intersection_tolerance;
    bool orientation = false;
    std::optional<double> angle, angle_tolerance;
};

class OneObjectFace : public ElementRule<OneFaceParams> {
public:
    Level narrow_level() const override { return Level::Mesh; }
    Variant base_variant() const override { return Variant::MeshWorld; }
    std::vector<Variant> narrow_variants() const override { return {Variant::MeshWorld}; }
    bool multi_verdicts() const override { return true; }

    void setup() override;
    Verdict narrow_test(const ElementGeometry& e) const override;
    std::vector<Verdict> narrow_multi(const ElementGeometry& e) const override;

protected:
    // The triangles the faces are selected from (Mesh::local_verts /
    // faces): the world triangulation.
    virtual std::shared_ptr<const Mesh> face_mesh(const ElementGeometry& e) const;

private:
    geometry::FaceSelection a_, b_;
    geometry::FaceChecks checks_;
};

struct TwoFaceParams {
    Json source_face_selection = Json::object();
    Json target_face_selection = Json::object();
    bool distance = false;
    std::optional<double> min_distance, max_distance;
    bool intersection = false;
    std::optional<double> intersection_tolerance;
    bool orientation = false;
    std::optional<double> angle, angle_tolerance;
};

struct SelectedFaces {
    std::vector<Triangle3> triangles;
    Bnd_Box box;
};

class TwoObjectsFace : public PairRule<TwoFaceParams> {
public:
    Level narrow_level() const override { return Level::Mesh; }
    Variant base_variant() const override { return Variant::MeshWorld; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    bool needs_element_data() const override { return true; }
    bool multi_verdicts() const override { return true; }
    // A failed orientation has no spatial locality: every pair is checked.
    BroadMode broad_mode() const override { return checks_.orientation ? BroadMode::AllPairs : BroadMode::Spatial; }

    void setup() override;
    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override;
    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override;
    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override;
    std::vector<Verdict> narrow_multi(const ElementGeometry& s, const ElementGeometry& t) const override;

protected:
    // The triangles the faces are selected from: the world triangulation.
    virtual std::shared_ptr<const Mesh> face_mesh(const ElementGeometry& e) const;

private:
    geometry::FaceSelection source_, target_;
    geometry::FaceChecks checks_;
};

}  // namespace ifcclash
