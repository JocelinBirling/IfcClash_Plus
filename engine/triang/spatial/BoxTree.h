// IfcClash_Plus engine — a BVH on axis-aligned boxes (engine/triang/spatial).
#pragma once

#include <Bnd_Box.hxx>

#include <array>
#include <functional>
#include <memory>
#include <vector>

namespace ifcclash::triang {

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
    // visit(index) for every box crossed by the segment [p, q] (slab test,
    // boxes grown by `margin`); stops when it returns false.
    void query_segment(const std::array<double, 3>& p, const std::array<double, 3>& q, double margin,
                       const std::function<bool(int)>& visit) const;
    bool empty() const { return empty_; }

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
    bool empty_ = true;
};

}  // namespace ifcclash::triang
