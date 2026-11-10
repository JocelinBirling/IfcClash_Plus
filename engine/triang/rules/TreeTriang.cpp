// IfcClash_Plus engine — the _triang rules of the IfcOpenShell clash tree
// (engine/triang/rules): Intersection_triang.
//
// The algorithm of Intersection (protrusion, then piercing, beyond the
// tolerance), fed with Variant::Triangles (.ifcview or IFC triangulation, per
// SessionOptions::triangle_source) in a tree of its own, apart from the tree of
// the IFC triangles. Same parameters and result blocks as Intersection.
#include "Common.h"

#include "../../registry/RuleSpec.h"
#include "../../rules/TreeClashRules.h"
#include "../../sources/IfcClashTree.h"

namespace ifcclash {

namespace {

using triang::kFloatMargin;

// The narrow phase of the tree rules on the triangles: one query per batch
// on the tree of the triangles (GeometryProvider::view_clash).
std::vector<Verdict> view_tree_batch(const std::vector<PairRuleBase::GeometryPair>& pairs,
                                     const ClashQueryParams& query_params) {
    std::vector<Verdict> out(pairs.size());
    if (pairs.empty()) return out;
    GeometryProvider& provider = pairs.front().first->provider();
    std::vector<std::shared_ptr<const Mesh>> keep;
    std::vector<ClashPair> query;
    std::vector<size_t> where;
    for (size_t n = 0; n < pairs.size(); ++n) {
        auto ms = provider.view_clash_mesh(pairs[n].first->key);
        auto mt = provider.view_clash_mesh(pairs[n].second->key);
        if (!ms || !mt) continue;
        query.push_back({&pairs[n].first->key, ms.get(), &pairs[n].second->key, mt.get()});
        where.push_back(n);
        keep.push_back(std::move(ms));
        keep.push_back(std::move(mt));
    }
    if (query.empty()) return out;
    const auto clashes = provider.view_clash()->batch(query, query_params);
    for (size_t k = 0; k < clashes.size(); ++k) out[where[k]] = tree_rules::verdict_of(clashes[k]);
    return out;
}

// A tree rule on the triangles: the margins of the tree (on the boxes of the
// triangles), the query of the original rule.
template <class Params>
class TreeTriang : public PairRule<Params> {
public:
    Level narrow_level() const override { return Level::Mesh; }
    PairSymmetry symmetry() const override { return PairSymmetry::Unordered; }
    Variant base_variant() const override { return Variant::Triangles; }
    std::vector<Variant> narrow_variants() const override { return {}; }

    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override {
        return geometry::inflate(e.boxes.aabb, tree_rules::kTreeMargin + kFloatMargin + extend(role));
    }
    Bnd_OBB mid_volume(const ElementGeometry& e, Role role) const override {
        return geometry::inflate(e.boxes.obb, tree_rules::kTreeMargin + kFloatMargin + extend(role));
    }
    Candidate mid_test(const Bnd_OBB& a, const Bnd_OBB& b) const override {
        return tree_rules::obbs_overlap(a, b) ? Candidate::Kept : Candidate::Rejected;
    }
    std::vector<Verdict> narrow_batch(const std::vector<PairRuleBase::GeometryPair>& pairs) const override {
        return view_tree_batch(pairs, query());
    }
    // One tree query for every candidate pair: the tree tests every element
    // of one side against every element of the other, so batches of 4096
    // pairs would find the pairs of the other batches and count them as
    // clashes outside the candidates (a false prefilter_lost_clash).
    bool narrow_whole_run() const override { return true; }
    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override {
        return narrow_batch({{&s, &t}}).front();
    }

protected:
    virtual ClashQueryParams query() const = 0;
    // Only the source is extended (Clearance: by the clearance).
    virtual double extend(Role) const { return 0.0; }
};

// ================================================================ Intersection_triang

struct IntersectionTriangParams {
    double tolerance = 0.1;  // m
};

class IntersectionTriang final : public TreeTriang<IntersectionTriangParams> {
protected:
    ClashQueryParams query() const override { return {ClashQuery::Intersection, params().tolerance, true}; }
};

// ================================================================ Clearance_triang

struct ClearanceTriangParams {
    double clearance = 0.05;  // m
    bool check_all = false;
};

class ClearanceTriang final : public TreeTriang<ClearanceTriangParams> {
protected:
    ClashQueryParams query() const override {
        return {ClashQuery::Clearance, params().clearance, params().check_all};
    }
    double extend(Role role) const override { return role == Role::Source ? params().clearance : 0.0; }
};

// ================================================================ Collision_triang

struct CollisionTriangParams {
    bool allow_touching = false;
};

class CollisionTriang final : public TreeTriang<CollisionTriangParams> {
protected:
    ClashQueryParams query() const override { return {ClashQuery::Collision, 0.0, params().allow_touching}; }
};

}  // namespace

RuleSpec spec_intersection_triang() {
    return RuleSpec::pair<IntersectionTriang>(
        "Intersection_triang", "Intersection (triangles)", {Slot::Source, Slot::Target},
        "Intersection on the triangles (.ifcview or IFC triangulation): the pairs whose shapes intersect within "
        "the tolerance.",
        {param(&IntersectionTriangParams::tolerance, "tolerance").doc("Intersection tolerance").unit(Unit::Metre)});
}

RuleSpec spec_clearance_triang() {
    return RuleSpec::pair<ClearanceTriang>(
        "Clearance_triang", "Clearance (triangles)", {Slot::Source, Slot::Target},
        "Clearance on the triangles: the pairs closer than the clearance.",
        {param(&ClearanceTriangParams::clearance, "clearance").doc("Minimum required clearance").unit(Unit::Metre).min(0.0),
         param(&ClearanceTriangParams::check_all, "check_all").doc("Check all the pairs, not only the closest")});
}

RuleSpec spec_collision_triang() {
    return RuleSpec::pair<CollisionTriang>(
        "Collision_triang", "Collision (triangles)", {Slot::Source, Slot::Target},
        "Collision on the triangles: the pairs of colliding shapes; touching may be allowed.",
        {param(&CollisionTriangParams::allow_touching, "allow_touching").doc("Allow face contact")});
}

}  // namespace ifcclash
