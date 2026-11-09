#include "RuleBase.h"

namespace ifcclash {

static ResultRecord standard_report(const Verdict& verdict) {
    ResultRecord record;
    record.status = verdict.status;
    record.measures = verdict.measures;
    record.points = verdict.points;
    record.flags = verdict.flags;
    return record;
}

ResultRecord ElementRuleBase::report(const Verdict& verdict) const { return standard_report(verdict); }

ResultRecord PairRuleBase::report(const Verdict& verdict) const { return standard_report(verdict); }

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
