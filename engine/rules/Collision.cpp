// Collision — flags the colliding pairs; a face contact may be allowed
// (Rules.Collision: tree.clash_collision_many).
#include "AllRules.h"
#include "TreeClashRules.h"

namespace ifcclash {

namespace {

struct CollisionParams {
    bool allow_touching = false;
};

class Collision final : public PairRule<CollisionParams> {
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
        return tree_rules::narrow_batch(pairs, {ClashQuery::Collision, 0.0, params().allow_touching});
    }

    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override {
        const auto ms = s.mesh();
        const auto mt = t.mesh();
        if (!ms || !mt) return {};
        return tree_rules::verdict_of(
            tree_rules::service(s).collision(s.key, *ms, t.key, *mt, params().allow_touching));
    }
};

}  // namespace

RuleSpec spec_collision() {
    return RuleSpec::pair<Collision>(
        "Collision", "Collision", {Slot::Source, Slot::Target},
        "Flags the pairs of colliding shapes; touching may be allowed.",
        {param(&CollisionParams::allow_touching, "allow_touching").doc("Allow face contact")});
}

}  // namespace ifcclash
