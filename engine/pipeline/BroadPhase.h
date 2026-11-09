// IfcClash_Plus engine — the broad phase: AABB overlap through an OCCT BVH.
//
// BVH_BoxSet + BVH_PairTraverse (the pattern of IfcGeomTree). The tree is
// rebuilt for every rule, from the volumes the rule derives (broad_volume):
// O(n log n), negligible next to the narrow phase.
#pragma once

#include <Bnd_Box.hxx>

#include <utility>
#include <vector>

namespace ifcclash {

// Index pairs (i in a, j in b) whose boxes overlap (touching counts as an
// overlap). Void boxes are never paired. The pairs are sorted.
std::vector<std::pair<int, int>> overlapping_pairs(const std::vector<Bnd_Box>& a,
                                                   const std::vector<Bnd_Box>& b);

}  // namespace ifcclash
