#include "RuleSpec.h"

namespace ifcclash {

const char* family_name(Family f) {
    switch (f) {
        case Family::OneObjectRule: return "OneObjectRule";
        case Family::TwoObjectRule: return "TwoObjectRule";
        case Family::ComplexRule: return "ComplexRule";
    }
    return "?";
}

const char* slot_name(Slot s) {
    switch (s) {
        case Slot::Source: return "source";
        case Slot::Target: return "target";
        case Slot::Context: return "context";
    }
    return "?";
}

const char* unit_name(Unit u) {
    switch (u) {
        case Unit::None: return "";
        case Unit::Metre: return "m";
        case Unit::SquareMetre: return "m2";
        case Unit::CubicMetre: return "m3";
        case Unit::Degree: return "deg";
    }
    return "";
}

namespace detail {

void bad_param(const std::string& name, const std::string& why) {
    throw ConfigError("parameter '" + name + "': " + why);
}

double as_number(const std::string& name, const Json& v) {
    if (!v.is_number() || v.is_boolean()) bad_param(name, "expected a number");
    return v.get<double>();
}

void check_bounds(const ParamDesc& d, double value) {
    if (d.min && value < *d.min) bad_param(d.name, "below the minimum " + std::to_string(*d.min));
    if (d.max && value > *d.max) bad_param(d.name, "above the maximum " + std::to_string(*d.max));
}

}  // namespace detail

Json ParamDesc::to_json() const {
    Json out{{"name", name}, {"kind", kind}, {"default", default_value}, {"doc", doc}};
    if (!values.empty()) out["values"] = values;
    if (unit != Unit::None) out["unit"] = unit_name(unit);
    if (min) out["min"] = *min;
    if (max) out["max"] = *max;
    if (nullable) out["nullable"] = true;
    return out;
}

std::unique_ptr<RuleBase> RuleSpec::create(const Json& parameters) const {
    if (!parameters.is_null() && !parameters.is_object()) {
        throw ConfigError("rule " + type + ": the parameters must be an object");
    }
    auto rule = make_rule_();
    void* typed = params_of_(*rule);
    if (parameters.is_object()) {
        for (auto it = parameters.begin(); it != parameters.end(); ++it) {
            const ParamDesc* desc = nullptr;
            for (const auto& p : params) {
                if (p.name == it.key()) desc = &p;
            }
            if (!desc) throw ConfigError("rule " + type + ": unknown parameter '" + it.key() + "'");
            desc->assign(typed, it.value());
        }
    }
    rule->setup();
    return rule;
}

Json RuleSpec::to_json() const {
    Json slot_list = Json::array();
    for (auto s : slots) slot_list.push_back(slot_name(s));
    Json param_list = Json::array();
    for (const auto& p : params) param_list.push_back(p.to_json());
    return Json{{"type", type},       {"label", label},           {"family", family_name(family)},
                {"doc", doc},         {"slots", std::move(slot_list)}, {"params", std::move(param_list)}};
}

}  // namespace ifcclash
