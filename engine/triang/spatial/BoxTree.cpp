#include "BoxTree.h"

#include <BVH_BoxSet.hxx>

#include <algorithm>
#include <cmath>
#include <stack>

namespace ifcclash::triang {

struct BoxTree::Impl {
    BVH_BoxSet<double, 3, int> set;
};

BoxTree::BoxTree(const std::vector<Bnd_Box>& boxes) : impl_(std::make_unique<Impl>()) {
    for (int i = 0; i < static_cast<int>(boxes.size()); ++i) {
        if (boxes[i].IsVoid()) continue;
        double x0, y0, z0, x1, y1, z1;
        boxes[i].Get(x0, y0, z0, x1, y1, z1);
        impl_->set.Add(i, BVH_Box<double, 3>(BVH_Vec3d(x0, y0, z0), BVH_Vec3d(x1, y1, z1)));
        empty_ = false;
    }
    if (!empty_) impl_->set.Build();
}

BoxTree::~BoxTree() = default;
BoxTree::BoxTree(BoxTree&&) noexcept = default;
BoxTree& BoxTree::operator=(BoxTree&&) noexcept = default;

void BoxTree::query(const Bnd_Box& q, const std::function<bool(int)>& visit) const {
    if (empty_ || q.IsVoid()) return;
    double qx0, qy0, qz0, qx1, qy1, qz1;
    q.Get(qx0, qy0, qz0, qx1, qy1, qz1);
    const auto& bvh = impl_->set.BVH();
    std::stack<int> stack;
    stack.push(0);
    while (!stack.empty()) {
        const int i = stack.top();
        stack.pop();
        const auto& lo = bvh->MinPoint(i);
        const auto& hi = bvh->MaxPoint(i);
        if (lo.x() > qx1 || hi.x() < qx0 || lo.y() > qy1 || hi.y() < qy0 || lo.z() > qz1 || hi.z() < qz0) continue;
        if (bvh->IsOuter(i)) {
            for (int j = bvh->BegPrimitive(i); j <= bvh->EndPrimitive(i); ++j) {
                const auto box = impl_->set.Box(j);
                const auto& bl = box.CornerMin();
                const auto& bh = box.CornerMax();
                if (bl.x() > qx1 || bh.x() < qx0 || bl.y() > qy1 || bh.y() < qy0 || bl.z() > qz1 || bh.z() < qz0)
                    continue;
                if (!visit(impl_->set.Element(j))) return;
            }
        } else {
            stack.push(bvh->Child<0>(i));
            stack.push(bvh->Child<1>(i));
        }
    }
}

namespace {

bool segment_meets_box(const std::array<double, 3>& p, const std::array<double, 3>& q, const double lo[3],
                       const double hi[3]) {
    double t0 = 0.0, t1 = 1.0;
    for (int k = 0; k < 3; ++k) {
        const double d = q[k] - p[k];
        if (std::abs(d) < 1e-300) {
            if (p[k] < lo[k] || p[k] > hi[k]) return false;
            continue;
        }
        double ta = (lo[k] - p[k]) / d, tb = (hi[k] - p[k]) / d;
        if (ta > tb) std::swap(ta, tb);
        t0 = std::max(t0, ta);
        t1 = std::min(t1, tb);
        if (t0 > t1) return false;
    }
    return true;
}

}  // namespace

void BoxTree::query_segment(const std::array<double, 3>& p, const std::array<double, 3>& q, double margin,
                            const std::function<bool(int)>& visit) const {
    if (empty_) return;
    const auto& bvh = impl_->set.BVH();
    std::stack<int> stack;
    stack.push(0);
    while (!stack.empty()) {
        const int i = stack.top();
        stack.pop();
        const auto& lo = bvh->MinPoint(i);
        const auto& hi = bvh->MaxPoint(i);
        const double l[3] = {lo.x() - margin, lo.y() - margin, lo.z() - margin};
        const double h[3] = {hi.x() + margin, hi.y() + margin, hi.z() + margin};
        if (!segment_meets_box(p, q, l, h)) continue;
        if (bvh->IsOuter(i)) {
            for (int j = bvh->BegPrimitive(i); j <= bvh->EndPrimitive(i); ++j) {
                const auto box = impl_->set.Box(j);
                const auto& bl = box.CornerMin();
                const auto& bh = box.CornerMax();
                const double l2[3] = {bl.x() - margin, bl.y() - margin, bl.z() - margin};
                const double h2[3] = {bh.x() + margin, bh.y() + margin, bh.z() + margin};
                if (!segment_meets_box(p, q, l2, h2)) continue;
                if (!visit(impl_->set.Element(j))) return;
            }
        } else {
            stack.push(bvh->Child<0>(i));
            stack.push(bvh->Child<1>(i));
        }
    }
}

}  // namespace ifcclash::triang
