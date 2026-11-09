// IfcClash_Plus engine — the IfcOpenShell ray tree (backend
// "opencascade.brep", select_ray) used by DirectView, as in Python
// (clash_utils.make_ray_tree / add_elements_to_ray_tree).
#pragma once

#include "../core/ElementKey.h"
#include "../core/Result.h"

#include <memory>
#include <vector>

namespace ifcclash {

class RayTree {
public:
    virtual ~RayTree() = default;
    // len(tree.select_ray(origin, direction, length))
    virtual size_t hits(const Point3& origin, const Point3& direction, double length) const = 0;
};

class RayTreeService {
public:
    virtual ~RayTreeService() = default;
    // A fresh tree holding these elements (B-Rep, world coordinates).
    virtual std::unique_ptr<RayTree> build_ray_tree(const std::vector<ElementKey>& keys) = 0;
};

}  // namespace ifcclash
