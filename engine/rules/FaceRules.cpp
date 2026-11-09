// OneObjectFace and TwoObjectsFace of Rules.py: face-level checks
// (distance, intersection, orientation) between selected triangles; one
// verdict per face pair per failed check.
#include "AllRules.h"

#include "../geometry/Triangles.h"
#include "../sources/IfcQueries.h"

#include <set>

namespace ifcclash {

namespace {

using geometry::FaceChecks;
using geometry::FaceSelection;

std::vector<std::string> materials_of(const ElementGeometry& e) {
    auto* q = e.provider().ifc_queries();
    return q ? q->material_names(e.key) : std::vector<std::string>{};
}

Verdict failure_verdict(const geometry::FaceFailure& f, const Triangle3& a, const Triangle3& b) {
    Verdict v;
    v.status = true;
    v.measures.set(f.measure, f.value);
    v.faces.push_back({geometry::face_rule_data(a), geometry::face_rule_data(b)});
    return v;
}

// The constructor checks of the Python rules (ValueError -> ConfigError).
void validate_checks(const char* rule, bool distance, std::optional<double> min_d, std::optional<double> max_d,
                     bool intersection, std::optional<double> tol, bool orientation, std::optional<double> angle,
                     std::optional<double> angle_tol) {
    const std::string name(rule);
    if (!(distance || intersection || orientation))
        throw ConfigError(name + " needs at least one enabled check: distance, intersection or orientation");
    if (distance) {
        if (min_d && *min_d < 0) throw ConfigError("min_distance must be a positive number (m)");
        if (max_d && *max_d < 0) throw ConfigError("max_distance must be a positive number (m)");
        if (min_d && max_d && *min_d > *max_d) throw ConfigError("min_distance must not exceed max_distance");
    }
    if (intersection && tol && *tol < 0) throw ConfigError("intersection_tolerance must be a positive number (m)");
    if (orientation) {
        if (!angle || !(0.0 <= *angle && *angle <= 180.0))
            throw ConfigError("angle is mandatory (degrees in [0, 180]) when the orientation check is enabled");
        if (angle_tol && *angle_tol < 0) throw ConfigError("angle_tolerance must be a positive number (degrees)");
    }
}

// ================================================================ OneObjectFace

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

class OneObjectFace final : public ElementRule<OneFaceParams> {
public:
    Level narrow_level() const override { return Level::Mesh; }
    Variant base_variant() const override { return Variant::MeshWorld; }
    std::vector<Variant> narrow_variants() const override { return {Variant::MeshWorld}; }
    bool multi_verdicts() const override { return true; }

    void setup() override {
        const auto& p = params();
        a_ = FaceSelection::parse(p.face_a_selection);
        b_ = FaceSelection::parse(p.face_b_selection);
        validate_checks("OneObjectFace", p.distance, p.min_distance, p.max_distance, p.intersection,
                        p.intersection_tolerance, p.orientation, p.angle, p.angle_tolerance);
        checks_.distance = p.distance;
        checks_.min_distance = p.min_distance;
        checks_.max_distance = p.max_distance;
        checks_.skip_adjacent = p.distance ? p.skip_adjacent : true;
        checks_.intersection = p.intersection;
        checks_.intersection_tolerance = p.intersection ? p.intersection_tolerance.value_or(0.0) : 0.0;
        checks_.orientation = p.orientation;
        checks_.angle = p.angle;
        checks_.angle_tolerance = p.angle_tolerance.value_or(0.0);
    }

    Verdict narrow_test(const ElementGeometry& e) const override {
        auto all = narrow_multi(e);
        return all.empty() ? Verdict{} : all.front();
    }

    std::vector<Verdict> narrow_multi(const ElementGeometry& e) const override {
        std::vector<Verdict> out;
        const auto mesh = e.mesh(Variant::MeshWorld);
        if (!mesh || mesh->faces.empty()) return out;
        const auto materials = materials_of(e);
        const auto group_a = geometry::select_faces(mesh->local_verts, mesh->faces, a_, materials);
        const auto group_b = geometry::select_faces(mesh->local_verts, mesh->faces, b_, materials);
        std::set<std::pair<std::array<geometry::V3, 3>, std::array<geometry::V3, 3>>> seen;
        for (const auto& ta : group_a) {
            const auto ka = geometry::triangle_key(ta);
            for (const auto& tb : group_b) {
                const auto kb = geometry::triangle_key(tb);
                if (ka == kb) continue;  // a face paired with itself
                if (!seen.insert(ka <= kb ? std::make_pair(ka, kb) : std::make_pair(kb, ka)).second) continue;
                for (const auto& f : geometry::run_face_checks(ta, tb, checks_)) out.push_back(failure_verdict(f, ta, tb));
            }
        }
        return out;
    }

private:
    FaceSelection a_, b_;
    FaceChecks checks_;
};

// ================================================================ TwoObjectsFace

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

class TwoObjectsFace final : public PairRule<TwoFaceParams> {
public:
    Level narrow_level() const override { return Level::Mesh; }
    Variant base_variant() const override { return Variant::MeshWorld; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    bool needs_element_data() const override { return true; }
    bool multi_verdicts() const override { return true; }
    // A failed orientation has no spatial locality: every pair is checked.
    BroadMode broad_mode() const override { return checks_.orientation ? BroadMode::AllPairs : BroadMode::Spatial; }

    void setup() override {
        const auto& p = params();
        source_ = FaceSelection::parse(p.source_face_selection);
        target_ = FaceSelection::parse(p.target_face_selection);
        validate_checks("TwoObjectsFace", p.distance, p.min_distance, p.max_distance, p.intersection,
                        p.intersection_tolerance, p.orientation, p.angle, p.angle_tolerance);
        checks_.two_objects = true;
        checks_.distance = p.distance;
        checks_.min_distance = p.min_distance;
        checks_.max_distance = p.max_distance;
        checks_.intersection = p.intersection;
        checks_.intersection_tolerance = p.intersection ? p.intersection_tolerance.value_or(0.0) : 0.0;
        checks_.orientation = p.orientation;
        checks_.angle = p.angle;
        checks_.angle_tolerance = p.angle_tolerance.value_or(0.0);
    }

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override {
        const auto mesh = e.mesh(Variant::MeshWorld);
        if (!mesh || mesh->faces.empty()) return nullptr;
        auto data = std::make_shared<SelectedFaces>();
        data->triangles =
            geometry::select_faces(mesh->local_verts, mesh->faces, role == Role::Source ? source_ : target_, materials_of(e));
        if (data->triangles.empty()) return nullptr;  // Python: elements without selected faces are skipped
        const auto [lo, hi] = geometry::triangles_bounds(data->triangles);
        data->box.Update(lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]);
        return data;
    }

    // A distance failure needs a bbox distance below min_distance; an
    // intersection needs crossing triangles.
    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override {
        const double reach = (role == Role::Source && checks_.distance && checks_.min_distance) ? *checks_.min_distance : 0.0;
        return geometry::inflate(e.as<SelectedFaces>().box, reach + 1e-7);
    }

    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override {
        auto all = narrow_multi(s, t);
        return all.empty() ? Verdict{} : all.front();
    }

    std::vector<Verdict> narrow_multi(const ElementGeometry& s, const ElementGeometry& t) const override {
        std::vector<Verdict> out;
        for (const auto& ta : s.as<SelectedFaces>().triangles)
            for (const auto& tb : t.as<SelectedFaces>().triangles)
                for (const auto& f : geometry::run_face_checks(ta, tb, checks_)) out.push_back(failure_verdict(f, ta, tb));
        return out;
    }

private:
    FaceSelection source_, target_;
    FaceChecks checks_;
};

}  // namespace

RuleSpec spec_one_object_face() {
    return RuleSpec::element<OneObjectFace>(
        "OneObjectFace", "One Object Face", {Slot::Source},
        "Face check of one element against itself (distance, intersection, orientation).",
        {param(&OneFaceParams::face_a_selection, "face_a_selection").doc("First face selection (empty = all)"),
         param(&OneFaceParams::face_b_selection, "face_b_selection").doc("Second face selection (empty = all)"),
         param(&OneFaceParams::distance, "distance").doc("Measure the distance"),
         param(&OneFaceParams::min_distance, "min_distance").doc("Minimum distance").unit(Unit::Metre),
         param(&OneFaceParams::max_distance, "max_distance").doc("Maximum distance").unit(Unit::Metre),
         param(&OneFaceParams::skip_adjacent, "skip_adjacent").doc("Skip adjacent faces"),
         param(&OneFaceParams::intersection, "intersection").doc("Check the intersection"),
         param(&OneFaceParams::intersection_tolerance, "intersection_tolerance").doc("Intersection tolerance").unit(Unit::Metre),
         param(&OneFaceParams::orientation, "orientation").doc("Check the orientation"),
         param(&OneFaceParams::angle, "angle").doc("Angle").unit(Unit::Degree),
         param(&OneFaceParams::angle_tolerance, "angle_tolerance").doc("Angle tolerance").unit(Unit::Degree)});
}

RuleSpec spec_two_objects_face() {
    return RuleSpec::pair<TwoObjectsFace>(
        "TwoObjectsFace", "Two Objects Face", {Slot::Source, Slot::Target},
        "Face check of the source faces against the target faces.",
        {param(&TwoFaceParams::source_face_selection, "source_face_selection").doc("Source face selection (empty = all)"),
         param(&TwoFaceParams::target_face_selection, "target_face_selection").doc("Target face selection (empty = all)"),
         param(&TwoFaceParams::distance, "distance").doc("Measure the distance"),
         param(&TwoFaceParams::min_distance, "min_distance").doc("Minimum distance").unit(Unit::Metre),
         param(&TwoFaceParams::max_distance, "max_distance").doc("Maximum distance").unit(Unit::Metre),
         param(&TwoFaceParams::intersection, "intersection").doc("Check the intersection"),
         param(&TwoFaceParams::intersection_tolerance, "intersection_tolerance").doc("Intersection tolerance").unit(Unit::Metre),
         param(&TwoFaceParams::orientation, "orientation").doc("Check the orientation"),
         param(&TwoFaceParams::angle, "angle").doc("Angle").unit(Unit::Degree),
         param(&TwoFaceParams::angle_tolerance, "angle_tolerance").doc("Angle tolerance").unit(Unit::Degree)});
}

}  // namespace ifcclash
