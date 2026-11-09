// IfcClash_Plus engine — the .ifcview cache policy (SPEC "Politique et validation").
#pragma once

#include "../core/Errors.h"

#include <string>

namespace ifcclash {

enum class CachePolicy {
    Off,      // IFC only
    Auto,     // .ifcview when valid, IFC otherwise (with a warning)
    Require,  // .ifcview mandatory: an error when it is missing or rejected
};

inline CachePolicy cache_policy_from_string(const std::string& s) {
    if (s == "off") return CachePolicy::Off;
    if (s == "auto") return CachePolicy::Auto;
    if (s == "require") return CachePolicy::Require;
    throw ConfigError("unknown geometry_cache '" + s + "' (expected off, auto or require)");
}

}  // namespace ifcclash
