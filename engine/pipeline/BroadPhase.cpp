#include "BroadPhase.h"

#include <BVH_BoxSet.hxx>
#include <BVH_Traverse.hxx>

#include <algorithm>
#include <memory>

namespace ifcclash {

namespace {

using BoxSet = BVH_BoxSet<double, 3, int>;
using Vec = BVH_Vec3d;

std::unique_ptr<BoxSet> make_set(const std::vector<Bnd_Box>& boxes) {
    auto set = std::make_unique<BoxSet>();
    set->SetSize(boxes.size());
    for (int i = 0; i < static_cast<int>(boxes.size()); ++i) {
        if (boxes[i].IsVoid()) continue;
        double x0, y0, z0, x1, y1, z1;
        boxes[i].Get(x0, y0, z0, x1, y1, z1);
        set->Add(i, BVH_Box<double, 3>(Vec(x0, y0, z0), Vec(x1, y1, z1)));
    }
    set->Build();
    return set;
}

class OverlapCollector : public BVH_PairTraverse<double, 3, BoxSet> {
public:
    std::vector<std::pair<int, int>> pairs;

    bool RejectNode(const Vec& min1, const Vec& max1, const Vec& min2, const Vec& max2,
                    double&) const override {
        return disjoint(min1, max1, min2, max2);
    }

    bool Accept(const int i1, const int i2) override {
        // The leaves hold one box each, but a leaf node box is the union of
        // its primitives: test the primitives themselves.
        const auto& b1 = myBVHSet1->Box(i1);
        const auto& b2 = myBVHSet2->Box(i2);
        if (disjoint(b1.CornerMin(), b1.CornerMax(), b2.CornerMin(), b2.CornerMax())) return false;
        pairs.emplace_back(myBVHSet1->Element(i1), myBVHSet2->Element(i2));
        return true;
    }

private:
    static bool disjoint(const Vec& min1, const Vec& max1, const Vec& min2, const Vec& max2) {
        return min1.x() > max2.x() || min2.x() > max1.x() || min1.y() > max2.y() || min2.y() > max1.y() ||
               min1.z() > max2.z() || min2.z() > max1.z();
    }
};

}  // namespace

std::vector<std::pair<int, int>> overlapping_pairs(const std::vector<Bnd_Box>& a,
                                                   const std::vector<Bnd_Box>& b) {
    auto set_a = make_set(a);
    auto set_b = make_set(b);
    if (set_a->Size() == 0 || set_b->Size() == 0) return {};

    OverlapCollector collector;
    collector.SetBVHSets(set_a.get(), set_b.get());
    collector.Select();

    std::sort(collector.pairs.begin(), collector.pairs.end());
    collector.pairs.erase(std::unique(collector.pairs.begin(), collector.pairs.end()), collector.pairs.end());
    return std::move(collector.pairs);
}

}  // namespace ifcclash
