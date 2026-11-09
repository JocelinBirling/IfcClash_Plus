// IfcClash_Plus engine — the exact triangle clash queries of IfcOpenShell.
//
// Intersection, Clearance and Collision are, in Python, queries of the
// IfcOpenShell clash tree (backend "opencascade.trianglebvh") fed with the
// triangulated elements of the iterator. For a strict parity the C++ narrow
// phase asks the very same tree, one pair at a time: the engine's broad and
// mid phases only remove pairs that the tree would reject anyway (its own
// 1e-3 box margins and OBB tests), the verdict and the measures come from the
// same code as in Python.
#pragma once

#include "../core/ElementKey.h"
#include "../core/Geometry.h"
#include "../core/Result.h"

#include <memory>
#include <mutex>
#include <optional>
#include <unordered_set>
#include <vector>

namespace ifcopenshell::geom {
class tree;
}

namespace ifcclash {

struct TriangleClash {
    int clash_type = -1;  // 0 protrusion, 1 pierce, 2 collision, 3 clearance
    double distance = 0.0;
    Point3 source_point{};  // restored to the (source, target) order
    Point3 target_point{};
};

// One candidate pair of a batch query.
struct ClashPair {
    const ElementKey* source;
    const Mesh* source_mesh;
    const ElementKey* target;
    const Mesh* target_mesh;
};

enum class ClashQuery { Intersection, Collision, Clearance };

struct ClashQueryParams {
    ClashQuery query = ClashQuery::Collision;
    double value = 0.0;  // tolerance / clearance
    bool flag = false;   // check_all / allow_touching
};

class TriangleClashService {
public:
    virtual ~TriangleClashService() = default;

    // One tree query for a whole batch of candidate pairs (the tree runs
    // its own threads): the verdict of each pair, aligned with `pairs`.
    // Identical to the per-pair queries below: a pair the tree tests in the
    // reversed orientation (both elements on both sides) is re-queried in
    // the candidate orientation.
    virtual std::vector<std::optional<TriangleClash>> batch(const std::vector<ClashPair>& pairs,
                                                            const ClashQueryParams& params) = 0;
    // Clashes found by a batch query outside of its candidate pairs: a pair
    // the prefilters removed although it clashes. Must stay 0.
    virtual size_t clashes_outside_candidates() const = 0;

    virtual std::optional<TriangleClash> intersection(const ElementKey& s, const Mesh& ms,
                                                      const ElementKey& t, const Mesh& mt,
                                                      double tolerance, bool check_all) = 0;
    virtual std::optional<TriangleClash> collision(const ElementKey& s, const Mesh& ms,
                                                   const ElementKey& t, const Mesh& mt,
                                                   bool allow_touching) = 0;
    virtual std::optional<TriangleClash> clearance(const ElementKey& s, const Mesh& ms,
                                                   const ElementKey& t, const Mesh& mt,
                                                   double clearance, bool check_all) = 0;
};

// The tree is filled lazily: only the elements that reach the narrow phase
// are added (building the triangle BVH of an element is not free).
class IfcClashTree final : public TriangleClashService {
public:
    IfcClashTree();
    ~IfcClashTree() override;

    std::optional<TriangleClash> intersection(const ElementKey& s, const Mesh& ms,
                                              const ElementKey& t, const Mesh& mt,
                                              double tolerance, bool check_all) override;
    std::optional<TriangleClash> collision(const ElementKey& s, const Mesh& ms,
                                           const ElementKey& t, const Mesh& mt,
                                           bool allow_touching) override;
    std::optional<TriangleClash> clearance(const ElementKey& s, const Mesh& ms,
                                           const ElementKey& t, const Mesh& mt,
                                           double clearance, bool check_all) override;

    std::vector<std::optional<TriangleClash>> batch(const std::vector<ClashPair>& pairs,
                                                    const ClashQueryParams& params) override;
    size_t clashes_outside_candidates() const override { return outside_; }

private:
    size_t outside_ = 0;
    void ensure(const ElementKey& key, const Mesh& mesh);

    std::unique_ptr<ifcopenshell::geom::tree> tree_;
    std::unordered_set<ElementKey, ElementKeyHash> added_;
    std::mutex mutex_;
};

}  // namespace ifcclash
