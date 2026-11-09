// IfcClash_Plus engine — RuleSpec: the single source of a rule's description
// (SPEC "Registre des règles").
//
// A parameter is declared once, next to its field, through a pointer to
// member: a typo does not compile, and the name used by the JSON, the
// catalogue and the struct is the same by construction. The default value
// is the one of the struct (the only place where it is written).
#pragma once

#include "../core/Errors.h"
#include "../core/Result.h"
#include "../rules/RuleBase.h"

#include <array>
#include <functional>
#include <memory>
#include <optional>
#include <string>
#include <type_traits>
#include <vector>

namespace ifcclash {

enum class Family { OneObjectRule, TwoObjectRule, ComplexRule };
enum class Slot { Source, Target, Context };
enum class Unit { None, Metre, SquareMetre, CubicMetre, Degree };

const char* family_name(Family f);
const char* slot_name(Slot s);
const char* unit_name(Unit u);

struct ParamDesc {
    std::string name;
    std::string kind;  // float, int, bool, string, enum, direction (catalogue editor kinds)
    std::string doc;
    Unit unit = Unit::None;
    Json default_value;
    std::optional<double> min, max;
    std::vector<std::string> values;  // enum
    bool nullable = false;
    // Validates the JSON value and writes it into the params struct.
    std::function<void(void* params, const Json& value)> assign;

    Json to_json() const;
};

namespace detail {

template <class T> struct is_optional : std::false_type {};
template <class T> struct is_optional<std::optional<T>> : std::true_type {};
template <class T> struct value_of { using type = T; };
template <class T> struct value_of<std::optional<T>> { using type = T; };

[[noreturn]] void bad_param(const std::string& name, const std::string& why);
double as_number(const std::string& name, const Json& v);
void check_bounds(const ParamDesc& d, double value);

template <class T>
Json default_to_json(const T& value) {
    if constexpr (is_optional<T>::value) {
        return value ? Json(*value) : Json(nullptr);
    } else {
        return Json(value);
    }
}

template <class T>
const char* kind_of() {
    using V = typename value_of<T>::type;
    if constexpr (std::is_same_v<V, bool>) return "bool";
    else if constexpr (std::is_integral_v<V>) return "int";
    else if constexpr (std::is_floating_point_v<V>) return "float";
    else if constexpr (std::is_same_v<V, std::string>) return "string";
    else if constexpr (std::is_same_v<V, std::array<double, 3>>) return "direction";
    else static_assert(sizeof(V) == 0, "unsupported parameter type");
}

template <class V>
V convert(const ParamDesc& d, const Json& v) {
    if constexpr (std::is_same_v<V, bool>) {
        if (!v.is_boolean()) bad_param(d.name, "expected a boolean");
        return v.get<bool>();
    } else if constexpr (std::is_integral_v<V>) {
        if (!v.is_number_integer()) bad_param(d.name, "expected an integer");
        const auto value = v.get<long long>();
        check_bounds(d, static_cast<double>(value));
        return static_cast<V>(value);
    } else if constexpr (std::is_floating_point_v<V>) {
        const double value = as_number(d.name, v);
        check_bounds(d, value);
        return static_cast<V>(value);
    } else if constexpr (std::is_same_v<V, std::string>) {
        if (!v.is_string()) bad_param(d.name, "expected a string");
        auto s = v.get<std::string>();
        if (!d.values.empty()) {
            bool ok = false;
            for (const auto& allowed : d.values) ok = ok || allowed == s;
            if (!ok) bad_param(d.name, "'" + s + "' is not one of the allowed values");
        }
        return s;
    } else {
        static_assert(std::is_same_v<V, std::array<double, 3>>);
        if (!v.is_array() || v.size() != 3) bad_param(d.name, "expected three numbers (x, y, z)");
        return {as_number(d.name, v[0]), as_number(d.name, v[1]), as_number(d.name, v[2])};
    }
}

}  // namespace detail

template <class P, class T>
class ParamBuilder {
public:
    ParamBuilder(T P::*member, std::string name) {
        desc_.name = std::move(name);
        desc_.kind = detail::kind_of<T>();
        desc_.nullable = detail::is_optional<T>::value;
        desc_.default_value = detail::default_to_json(P{}.*member);
        member_ = member;
    }

    ParamBuilder& doc(std::string text) { desc_.doc = std::move(text); return *this; }
    ParamBuilder& unit(Unit u) { desc_.unit = u; return *this; }
    ParamBuilder& min(double v) { desc_.min = v; return *this; }
    ParamBuilder& max(double v) { desc_.max = v; return *this; }
    ParamBuilder& values(std::vector<std::string> allowed) {
        desc_.values = std::move(allowed);
        desc_.kind = "enum";
        return *this;
    }

    operator ParamDesc() const {
        ParamDesc d = desc_;
        auto member = member_;
        // The validation reads a copy of the description (bounds, values).
        ParamDesc check = desc_;
        check.assign = nullptr;
        d.assign = [member, check](void* params, const Json& value) {
            auto& field = static_cast<P*>(params)->*member;
            if constexpr (detail::is_optional<T>::value) {
                if (value.is_null()) {
                    field = std::nullopt;
                    return;
                }
                field = detail::convert<typename T::value_type>(check, value);
            } else {
                if (value.is_null()) detail::bad_param(check.name, "null is not allowed");
                field = detail::convert<T>(check, value);
            }
        };
        return d;
    }

private:
    ParamDesc desc_;
    T P::*member_ = nullptr;
};

template <class P, class T>
ParamBuilder<P, T> param(T P::*member, std::string name) {
    return ParamBuilder<P, T>(member, std::move(name));
}

class RuleSpec {
public:
    std::string type;
    std::string label;
    Family family = Family::OneObjectRule;
    std::vector<Slot> slots;
    std::string doc;
    PipelineKind pipeline = PipelineKind::Element;
    std::vector<ParamDesc> params;

    // Fills the typed parameters from the JSON declaration, validates them
    // (types, bounds, enum values, nullable) and calls setup(): a bad
    // configuration raises ConfigError before any computation. Unknown keys
    // are an error too.
    std::unique_ptr<RuleBase> create(const Json& parameters) const;

    // The catalogue entry, in the format of the Python registry.
    Json to_json() const;

    template <class R>
    static RuleSpec element(std::string type, std::string label, std::vector<Slot> slots, std::string doc,
                            std::vector<ParamDesc> params) {
        return make<R>(std::move(type), std::move(label), Family::OneObjectRule, PipelineKind::Element,
                       std::move(slots), std::move(doc), std::move(params));
    }

    template <class R>
    static RuleSpec pair(std::string type, std::string label, std::vector<Slot> slots, std::string doc,
                         std::vector<ParamDesc> params) {
        return make<R>(std::move(type), std::move(label), Family::TwoObjectRule, PipelineKind::Pair,
                       std::move(slots), std::move(doc), std::move(params));
    }

private:
    std::function<std::unique_ptr<RuleBase>()> make_rule_;
    std::function<void*(RuleBase&)> params_of_;

    template <class R>
    static RuleSpec make(std::string type, std::string label, Family family, PipelineKind pipeline,
                         std::vector<Slot> slots, std::string doc, std::vector<ParamDesc> params) {
        RuleSpec spec;
        spec.type = std::move(type);
        spec.label = std::move(label);
        spec.family = family;
        spec.pipeline = pipeline;
        spec.slots = std::move(slots);
        spec.doc = std::move(doc);
        spec.params = std::move(params);
        spec.make_rule_ = [] { return std::unique_ptr<RuleBase>(new R()); };
        spec.params_of_ = [](RuleBase& rule) -> void* { return &static_cast<R&>(rule).mutable_params(); };
        return spec;
    }
};

}  // namespace ifcclash
