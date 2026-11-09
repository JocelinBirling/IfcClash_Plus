// IfcClash_Plus engine — the registry of the C++ rules.
//
// Explicit registration (register_all_rules), not static objects: in a
// static library the linker may drop them, and the rule would vanish
// without an error.
#pragma once

#include "RuleSpec.h"

#include <map>
#include <string>

namespace ifcclash {

class Registry {
public:
    void add(RuleSpec spec);
    // Throws ConfigError for an unknown type.
    const RuleSpec& find(const std::string& type) const;
    bool has(const std::string& type) const { return specs_.count(type) != 0; }
    // { "rules": [ <catalogue entry>, ... ] } in registration order.
    Json catalogue_json() const;

private:
    std::map<std::string, RuleSpec> specs_;
    std::vector<std::string> order_;
};

void register_all_rules(Registry& registry);

// The process-wide registry, filled on first use.
const Registry& default_registry();

}  // namespace ifcclash
