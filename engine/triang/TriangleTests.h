// IfcClash_Plus engine — the geometric tests of the _triang rules, on
// triangles (engine/triang).
#pragma once

#include <Bnd_Box.hxx>
#include <Bnd_OBB.hxx>

#include <array>
#include <functional>
#include <memory>
#include <vector>

namespace ifcclash::triang {

using P3 = std::array<double, 3>;
using P2 = std::array<double, 2>;

// Whether a triangle meets an oriented box, the box grown by `margin` on
// every side (shrunk when negative) (separating axis theorem, 13 axes: the 3 box axes, the
// triangle normal and the 9 edge x axis products). Exact up to rounding.
bool triangle_meets_obb(const P3& a, const P3& b, const P3& c, const Bnd_OBB& obb, double margin);

// The convex polygon common to the first triangle and the second one grown
// by `grow` on every edge (shrunk when negative), both projected on XY (Sutherland-Hodgman), empty
// when they do not overlap. A shared edge gives a degenerate polygon.
std::vector<P2> clip_triangles_xy(const P3& a1, const P3& b1, const P3& c1, const P3& a2, const P3& b2,
                                  const P3& c2, double grow = 0.0);

// A BVH on axis-aligned boxes (OCCT BVH_BoxSet): the boxes met by a query
// box, by their index at insertion.
class BoxTree {
public:
    explicit BoxTree(const std::vector<Bnd_Box>& boxes);
    ~BoxTree();
    BoxTree(BoxTree&&) noexcept;
    BoxTree& operator=(BoxTree&&) noexcept;
    // visit(index) for every box overlapping `query`; stops when it
    // returns false.
    void query(const Bnd_Box& query, const std::function<bool(int)>& visit) const;
    bool empty() const { return empty_; }

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
    bool empty_ = true;
};

// The triangles of a mesh seen from above (side +1) or from below (side
// -1): the non-vertical triangles of which one sample point (the centroid,
// or a point near a corner) is covered by no other triangle of the mesh on
// that side. Independent of the winding (many IFC meshes are wound
// inwards): the triangulated counterpart of the faces the vertical rays of
// Above hit first. Indices of triangles (faces / 3).
std::vector<int> visible_triangles(const std::vector<double>& verts, const std::vector<int>& faces, double side);

// The tightest oriented box of a point set (OCCT Bnd_OBB::ReBuild, optimal
// mode: the method of BRepBndLib::AddOBB on a triangulation).
Bnd_OBB optimal_obb(const std::vector<double>& xyz);

}  // namespace ifcclash::triang
