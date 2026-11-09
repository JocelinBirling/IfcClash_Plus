#include "IfcClashTree.h"

#include "../core/Errors.h"

#include <ifcgeom/element.h>
#include <ifcgeom/tree.h>
#include <ifcgeom/tree_registry.h>

#include <cstdio>
#include <cstdlib>
#include <algorithm>
#include <map>
#include <set>
#include <stdexcept>
#include <vector>

namespace ifcclash {

namespace {

constexpr const char* kBackend = "opencascade.trianglebvh";  // clash_utils.CLASH_TREE_BACKEND

const ifcopenshell::geom::triangulation_element& native_of(const Mesh& mesh) {
    if (!mesh.native) {
        throw std::logic_error("IfcClashTree: the mesh carries no IfcOpenShell element");
    }
    return *static_cast<const ifcopenshell::geom::triangulation_element*>(mesh.native.get());
}

// One pair through the many-query of the tree, sides restored as in
// Rules._tree_clash_results: the tree may swap a and b, p1 belongs to a.
std::optional<TriangleClash> restore(const std::vector<ifcopenshell::geom::clash>& clashes,
                                     const express::base& source) {
    if (clashes.empty()) return std::nullopt;
    const auto& c = clashes.front();
    TriangleClash out;
    out.clash_type = c.clash_type;
    out.distance = c.distance;
    if (c.a == source) {
        out.source_point = c.p1;
        out.target_point = c.p2;
    } else {
        out.source_point = c.p2;
        out.target_point = c.p1;
    }
    return out;
}

struct BasePairLess {
    bool operator()(const std::pair<express::base, express::base>& x,
                    const std::pair<express::base, express::base>& y) const {
        if (x.first < y.first) return true;
        if (y.first < x.first) return false;
        return x.second < y.second;
    }
};

}  // namespace

IfcClashTree::IfcClashTree() : tree_(ifcopenshell::geom::trees::construct(kBackend)) {
    if (!tree_) throw ConfigError(std::string("IfcOpenShell tree backend not available: ") + kBackend);
}

IfcClashTree::~IfcClashTree() = default;

void IfcClashTree::ensure(const ElementKey& key, const Mesh& mesh) {
    if (added_.count(key)) return;
    // add_element only reads the element (it copies the triangles into its
    // own BVH); the const_cast follows the non-const signature of the API.
    auto& element = const_cast<ifcopenshell::geom::triangulation_element&>(native_of(mesh));
    tree_->add_element(&element);
    added_.insert(key);
}

std::optional<TriangleClash> IfcClashTree::intersection(const ElementKey& s, const Mesh& ms,
                                                        const ElementKey& t, const Mesh& mt,
                                                        double tolerance, bool check_all) {
    std::lock_guard<std::mutex> lock(mutex_);
    ensure(s, ms);
    ensure(t, mt);
    const express::base a = native_of(ms).product();
    const express::base b = native_of(mt).product();
    return restore(tree_->clash_intersection_many({a}, {b}, tolerance, check_all), a);
}

std::optional<TriangleClash> IfcClashTree::collision(const ElementKey& s, const Mesh& ms,
                                                     const ElementKey& t, const Mesh& mt,
                                                     bool allow_touching) {
    std::lock_guard<std::mutex> lock(mutex_);
    ensure(s, ms);
    ensure(t, mt);
    const express::base a = native_of(ms).product();
    const express::base b = native_of(mt).product();
    return restore(tree_->clash_collision_many({a}, {b}, allow_touching), a);
}

std::optional<TriangleClash> IfcClashTree::clearance(const ElementKey& s, const Mesh& ms,
                                                     const ElementKey& t, const Mesh& mt,
                                                     double clearance, bool check_all) {
    std::lock_guard<std::mutex> lock(mutex_);
    ensure(s, ms);
    ensure(t, mt);
    const express::base a = native_of(ms).product();
    const express::base b = native_of(mt).product();
    return restore(tree_->clash_clearance_many({a}, {b}, clearance, check_all), a);
}

std::vector<std::optional<TriangleClash>> IfcClashTree::batch(const std::vector<ClashPair>& pairs,
                                                              const ClashQueryParams& params) {
    std::vector<std::optional<TriangleClash>> out(pairs.size());
    if (pairs.empty()) return out;

    std::vector<express::base> set_a, set_b;
    // (source, target) -> candidate index; the tree answers in either
    // orientation. Explicit comparator: in C++20 std::pair compares through a
    // synthesized operator<=>, and express::base converts implicitly to bool
    // — every pair would compare equal.
    std::map<std::pair<express::base, express::base>, size_t, BasePairLess> index;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        std::set<express::base> seen_a, seen_b;
        for (size_t n = 0; n < pairs.size(); ++n) {
            const auto& p = pairs[n];
            ensure(*p.source, *p.source_mesh);
            ensure(*p.target, *p.target_mesh);
            const express::base a = native_of(*p.source_mesh).product();
            const express::base b = native_of(*p.target_mesh).product();
            if (seen_a.insert(a).second) set_a.push_back(a);
            if (seen_b.insert(b).second) set_b.push_back(b);
            index.emplace(std::make_pair(a, b), n);
        }

        std::vector<ifcopenshell::geom::clash> clashes;
        switch (params.query) {
            case ClashQuery::Intersection:
                clashes = tree_->clash_intersection_many(set_a, set_b, params.value, params.flag);
                break;
            case ClashQuery::Collision:
                clashes = tree_->clash_collision_many(set_a, set_b, params.flag);
                break;
            case ClashQuery::Clearance:
                clashes = tree_->clash_clearance_many(set_a, set_b, params.value, params.flag);
                break;
        }

        std::vector<size_t> reversed;
        for (const auto& c : clashes) {
            auto direct = index.find({c.a, c.b});
            auto swapped = index.find({c.b, c.a});
            if (direct == index.end() && swapped == index.end()) {
                ++outside_;  // a clash the prefilters removed
                continue;
            }
            // The tree tests an unordered pair once. When it is a candidate in
            // the tree orientation, keep it; otherwise (only possible when
            // both elements sit on both sides) the measures belong to the
            // reversed test: re-query the pair alone, in its own orientation.
            if (direct != index.end()) {
                out[direct->second] = restore({c}, direct->first.first);
            } else {
                reversed.push_back(swapped->second);
            }
        }
        for (size_t n : reversed) {
            const auto& p = pairs[n];
            const express::base a = native_of(*p.source_mesh).product();
            const express::base b = native_of(*p.target_mesh).product();
            switch (params.query) {
                case ClashQuery::Intersection:
                    out[n] = restore(tree_->clash_intersection_many({a}, {b}, params.value, params.flag), a);
                    break;
                case ClashQuery::Collision:
                    out[n] = restore(tree_->clash_collision_many({a}, {b}, params.flag), a);
                    break;
                case ClashQuery::Clearance:
                    out[n] = restore(tree_->clash_clearance_many({a}, {b}, params.value, params.flag), a);
                    break;
            }
        }
    }
    return out;
}

}  // namespace ifcclash
