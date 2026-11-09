// Intersection — flags the intersecting source/target pairs, within the
// tolerance (Rules.Intersection: tree.clash_intersection_many, check_all=True).
#include "AllRules.h"
#include "TreeClashRules.h"

namespace ifcclash {

namespace {

struct IntersectionParams {
    double tolerance = 0.1;  // m
};

class Intersection final : public PairRule<IntersectionParams> {
public:
    Level narrow_level() const override { return Level::Mesh; }
    PairSymmetry symmetry() const override { return PairSymmetry::Unordered; }

    Bnd_Box broad_volume(const ElementGeometry& e, Role) const override {
        return geometry::inflate(e.boxes.aabb, e.boxes.uncertainty + tree_rules::kTreeMargin);
    }

    Bnd_OBB mid_volume(const ElementGeometry& e, Role) const override {
        return geometry::inflate(e.boxes.obb, e.boxes.uncertainty + tree_rules::kTreeMargin);
    }

    Candidate mid_test(const Bnd_OBB& a, const Bnd_OBB& b) const override {
        return tree_rules::obbs_overlap(a, b) ? Candidate::Kept : Candidate::Rejected;
    }

    std::vector<Verdict> narrow_batch(const std::vector<GeometryPair>& pairs) const override {
        return tree_rules::narrow_batch(pairs, {ClashQuery::Intersection, params().tolerance, true});
    }

    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override {
        const auto ms = s.mesh();
        const auto mt = t.mesh();
        if (!ms || !mt) return {};
        return tree_rules::verdict_of(
            tree_rules::service(s).intersection(s.key, *ms, t.key, *mt, params().tolerance, true));
    }
};

}  // namespace

RuleSpec spec_intersection() {
    return RuleSpec::pair<Intersection>(
        "Intersection", "Intersection", {Slot::Source, Slot::Target},
        "Flags the pairs whose shapes intersect within the tolerance.",
        {param(&IntersectionParams::tolerance, "tolerance").doc("Intersection tolerance").unit(Unit::Metre)});
}

}  // namespace ifcclash
