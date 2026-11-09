// Clearance — flags the pairs closer than the required clearance
// (Rules.Clearance: tree.clash_clearance_many).
#include "AllRules.h"
#include "TreeClashRules.h"

namespace ifcclash {

namespace {

struct ClearanceParams {
    double clearance = 0.05;  // m: the only place where the default is written
    bool check_all = false;
};

class Clearance final : public PairRule<ClearanceParams> {
public:
    Level narrow_level() const override { return Level::Mesh; }
    PairSymmetry symmetry() const override { return PairSymmetry::Unordered; }

    // Only the source is extended by the clearance (the tree extends one
    // side too): the overlap condition is the same.
    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override {
        const double extend = role == Role::Source ? params().clearance : 0.0;
        return geometry::inflate(e.boxes.aabb, e.boxes.uncertainty + tree_rules::kTreeMargin + extend);
    }

    Bnd_OBB mid_volume(const ElementGeometry& e, Role role) const override {
        const double extend = role == Role::Source ? params().clearance : 0.0;
        return geometry::inflate(e.boxes.obb, e.boxes.uncertainty + tree_rules::kTreeMargin + extend);
    }

    Candidate mid_test(const Bnd_OBB& a, const Bnd_OBB& b) const override {
        return tree_rules::obbs_overlap(a, b) ? Candidate::Kept : Candidate::Rejected;
    }

    std::vector<Verdict> narrow_batch(const std::vector<GeometryPair>& pairs) const override {
        return tree_rules::narrow_batch(pairs, {ClashQuery::Clearance, params().clearance, params().check_all});
    }

    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override {
        const auto ms = s.mesh();
        const auto mt = t.mesh();
        if (!ms || !mt) return {};
        return tree_rules::verdict_of(tree_rules::service(s).clearance(s.key, *ms, t.key, *mt, params().clearance,
                                                                       params().check_all));
    }
};

}  // namespace

RuleSpec spec_clearance() {
    return RuleSpec::pair<Clearance>(
        "Clearance", "Clearance", {Slot::Source, Slot::Target}, "Flags the pairs closer than the clearance.",
        {param(&ClearanceParams::clearance, "clearance").doc("Minimum required clearance").unit(Unit::Metre).min(0.0),
         param(&ClearanceParams::check_all, "check_all").doc("Check all the pairs, not only the closest")});
}

}  // namespace ifcclash
