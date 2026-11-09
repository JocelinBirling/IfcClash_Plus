#include "Registry.h"

#include "../rules/AllRules.h"

#include <stdexcept>

namespace ifcclash {

void Registry::add(RuleSpec spec) {
    const std::string type = spec.type;
    if (specs_.count(type)) throw std::logic_error("rule registered twice: " + type);
    specs_.emplace(type, std::move(spec));
    order_.push_back(type);
}

const RuleSpec& Registry::find(const std::string& type) const {
    auto it = specs_.find(type);
    if (it == specs_.end()) throw ConfigError("rule type not implemented by the C++ engine: " + type);
    return it->second;
}

Json Registry::catalogue_json() const {
    Json rules = Json::array();
    for (const auto& type : order_) rules.push_back(specs_.at(type).to_json());
    return Json{{"rules", std::move(rules)}};
}

void register_all_rules(Registry& registry) {
    // One line per rule (migration order of the SPEC).
    registry.add(spec_volume());
    registry.add(spec_intersection());
    registry.add(spec_clearance());
    registry.add(spec_collision());
    registry.add(spec_area());
    registry.add(spec_top_or_bottom_surface());
    registry.add(spec_lateral_surface());
    registry.add(spec_projected_surface());
    registry.add(spec_obb_high());
    registry.add(spec_obb_length());
    registry.add(spec_orientation());
    registry.add(spec_above());
    registry.add(spec_below());
    registry.add(spec_obb_above());
    registry.add(spec_obb_below());
    registry.add(spec_obb_front_and_back());
    registry.add(spec_obb_custom());
    registry.add(spec_angle_between());
    registry.add(spec_clearance_axis_to_axis());
    registry.add(spec_intersection2());
    registry.add(spec_one_object_face());
    registry.add(spec_two_objects_face());
    registry.add(spec_surface_recover());
    registry.add(spec_clearance_for_doors());
    registry.add(spec_ray_check());
    registry.add(spec_direct_view());
    registry.add(spec_free_space());
    registry.add(spec_alignement());
}

const Registry& default_registry() {
    static const Registry registry = [] {
        Registry r;
        register_all_rules(r);
        return r;
    }();
    return registry;
}

}  // namespace ifcclash
