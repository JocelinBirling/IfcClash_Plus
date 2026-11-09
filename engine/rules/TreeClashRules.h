// IfcClash_Plus engine — what Intersection, Clearance and Collision share.
//
// Their verdict is the IfcOpenShell clash tree query (sources/IfcClashTree),
// as in Python. The engine phases in front of it must never remove a pair
// the tree would flag:
//  - broad: the tree pairs two elements when their AABBs, inflated by 1e-3
//    each (plus the clearance on one side), overlap. The broad volumes use
//    the same margins, so the phase removes nothing the tree would test.
//  - mid: a flagged pair has truly interacting geometries (penetration,
//    contact, or distance below the clearance); the OBBs contain the
//    geometries, so they overlap once inflated by the same distance. The
//    1e-3 margin absorbs the rounding of the OBB construction.
#pragma once

#include "RuleBase.h"
#include "../sources/IfcClashTree.h"

#include <stdexcept>

namespace ifcclash::tree_rules {

inline constexpr double kTreeMargin = 1e-3;

inline TriangleClashService& service(const ElementGeometry& e) {
    auto* s = e.provider().triangle_clash();
    if (!s) throw std::runtime_error("this rule needs the IFC source (IfcOpenShell clash tree)");
    return *s;
}

inline Verdict verdict_of(const std::optional<TriangleClash>& clash) {
    Verdict v;
    if (!clash) return v;
    v.status = true;
    v.measures.set(Measure::Distance, clash->distance);
    v.points.push_back({clash->source_point, clash->target_point, std::nullopt});
    return v;
}

// The batched narrow phase of the tree rules: one tree query per batch.
inline std::vector<Verdict> narrow_batch(const std::vector<PairRuleBase::GeometryPair>& pairs,
                                         const ClashQueryParams& params) {
    std::vector<Verdict> out(pairs.size());
    if (pairs.empty()) return out;
    std::vector<std::shared_ptr<const Mesh>> keep;  // meshes alive during the query
    std::vector<ClashPair> query;
    std::vector<size_t> where;
    for (size_t n = 0; n < pairs.size(); ++n) {
        auto ms = pairs[n].first->mesh();
        auto mt = pairs[n].second->mesh();
        if (!ms || !mt) continue;
        query.push_back({&pairs[n].first->key, ms.get(), &pairs[n].second->key, mt.get()});
        where.push_back(n);
        keep.push_back(std::move(ms));
        keep.push_back(std::move(mt));
    }
    if (query.empty()) return out;
    const auto clashes = service(*pairs.front().first).batch(query, params);
    for (size_t k = 0; k < clashes.size(); ++k) out[where[k]] = verdict_of(clashes[k]);
    return out;
}

inline bool obbs_overlap(const Bnd_OBB& a, const Bnd_OBB& b) { return !a.IsOut(b); }

}  // namespace ifcclash::tree_rules
