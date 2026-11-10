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

// Where the _triang rules (engine/triang) read their triangles
// (Variant::Triangles).
enum class TriangleSource {
    Auto,     // the .ifcview when it holds the element, else the IFC triangulation
    IfcView,  // the .ifcview only: a file without accepted .ifcview is an error,
              // an element missing from it is skipped (diagnostic not_in_ifcview)
    Ifc,      // the IFC triangulation (world coordinates) only
};

inline TriangleSource triangle_source_from_string(const std::string& s) {
    if (s == "auto") return TriangleSource::Auto;
    if (s == "ifcview") return TriangleSource::IfcView;
    if (s == "ifc") return TriangleSource::Ifc;
    throw ConfigError("unknown triangle_source '" + s + "' (expected auto, ifcview or ifc)");
}

}  // namespace ifcclash
