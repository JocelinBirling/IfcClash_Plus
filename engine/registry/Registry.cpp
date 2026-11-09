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
