// IfcClash_Plus engine — distances between triangle meshes and segment
// queries on triangle sets (engine/triang/spatial), through the BVHs.
#pragma once

#include "../kernels/Distance.h"
#include "../mesh/TriMesh.h"
#include "BoxTree.h"

#include <Bnd_Box.hxx>

#include <limits>
#include <memory>
#include <vector>

namespace ifcclash::triang {

struct MeshDistance {
    double distance = std::numeric_limits<double>::infinity();
    P3 a{0, 0, 0}, b{0, 0, 0};  // the closest points, on each mesh
};

// The distance between two triangle meshes (their surfaces: 0 when they
// meet), with its closest points. Branch and bound on the triangle BVH of
// `b`. Beyond `cutoff` the search stops early and returns a distance above
// it (the points are then those of the best pair seen).
MeshDistance mesh_distance(const TriMesh& a, const TriMesh& b,
                           double cutoff = std::numeric_limits<double>::infinity());

// The triangles of several elements in one BVH (the context of a rule): a
// segment test against all of them, owner by owner.
class TriangleSoup {
public:
    // Adds the triangles of one owner (any int id).
    void add(int owner, const TriMesh& mesh);
    void build();
    bool empty() const { return owners_.empty(); }
    // Whether the segment [p, q] meets a triangle whose owner passes
    // `accept`, within eps; hits closer than `skip` to either end ignored
    // (the ends of a ray lie on surfaces).
    template <class Accept>
    bool segment_blocked(const P3& p, const P3& q, double eps, double skip, Accept&& accept) const;
    // Every owner whose triangles meet the segment.
    size_t triangle_count() const { return owners_.size(); }

private:
    std::vector<P3> corners_;  // 3 per triangle
    std::vector<int> owners_;
    std::vector<Bnd_Box> boxes_;
    std::unique_ptr<BoxTree> tree_;
};

template <class Accept>
bool TriangleSoup::segment_blocked(const P3& p, const P3& q, double eps, double skip, Accept&& accept) const {
    if (!tree_) return false;
    const double dx = q[0] - p[0], dy = q[1] - p[1], dz = q[2] - p[2];
    const double len = std::sqrt(dx * dx + dy * dy + dz * dz);
    const double t_skip = len > 0 ? skip / len : 0.0;
    bool blocked = false;
    tree_->query_segment(p, q, eps, [&](int k) {
        if (!accept(owners_[size_t(k)])) return true;
        double t = 0.0;
        const size_t i = 3 * size_t(k);
        if (!segment_hits_triangle(p, q, corners_[i], corners_[i + 1], corners_[i + 2], eps, t)) return true;
        if (t < t_skip || t > 1.0 - t_skip) return true;
        blocked = true;
        return false;
    });
    return blocked;
}

}  // namespace ifcclash::triang
