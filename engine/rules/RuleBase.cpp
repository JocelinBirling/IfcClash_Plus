#include "RuleBase.h"

#include "../geometry/Faces.h"
#include "../geometry/Obb.h"

#include <cstdio>

namespace ifcclash {

std::shared_ptr<const ElementGeometry::MeshedBrep> ElementGeometry::meshed_brep() const {
    auto data = provider_->derived(key, "meshed_brep", [this]() -> std::shared_ptr<const void> {
        auto shape = provider_->brep(key);
        if (!shape) return nullptr;
        auto out = std::make_shared<MeshedBrep>();
        out->shape = *shape;
        out->obb = geometry::obb_of_shape(out->shape);  // meshes the shape
        return out;
    });
    return std::static_pointer_cast<const MeshedBrep>(data);
}

std::shared_ptr<const std::vector<TopoDS_Face>> ElementGeometry::visible_faces(const gp_Dir& view) const {
    char tag[128];
    std::snprintf(tag, sizeof tag, "visible_faces %.17g %.17g %.17g", view.X(), view.Y(), view.Z());
    auto data = provider_->derived(key, tag, [this, view]() -> std::shared_ptr<const void> {
        auto brep = meshed_brep();  // the faces of the meshed shape, as in Python
        if (!brep) return nullptr;
        return std::make_shared<const std::vector<TopoDS_Face>>(geometry::visible_faces(brep->shape, view));
    });
    return std::static_pointer_cast<const std::vector<TopoDS_Face>>(data);
}

static ResultRecord standard_report(const Verdict& verdict) {
    ResultRecord record;
    static_cast<InfoBlocks&>(record) = static_cast<const InfoBlocks&>(verdict);
    record.status = verdict.status;
    record.flags = verdict.flags;
    return record;
}

ResultRecord ElementRuleBase::report(const Verdict& verdict) const { return standard_report(verdict); }

ResultRecord PairRuleBase::report(const Verdict& verdict) const { return standard_report(verdict); }

ResultRecord SetRuleBase::report(const Verdict& verdict) const { return standard_report(verdict); }

std::vector<Verdict> PairRuleBase::narrow_batch(const std::vector<GeometryPair>& pairs) const {
    std::vector<Verdict> out;
    out.reserve(pairs.size());
    for (const auto& [s, t] : pairs) out.push_back(narrow_test(*s, *t));
    return out;
}

Bnd_Box PairRuleBase::broad_volume(const ElementGeometry& e, Role) const {
    return geometry::inflate(e.boxes.aabb, e.boxes.uncertainty);
}

Bnd_OBB PairRuleBase::mid_volume(const ElementGeometry& e, Role) const {
    return geometry::inflate(e.boxes.obb, e.boxes.uncertainty);
}

}  // namespace ifcclash
