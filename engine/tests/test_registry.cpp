#include "api/Engine.h"
#include "registry/Registry.h"

#include <catch2/catch_test_macros.hpp>

using namespace ifcclash;

TEST_CASE("the catalogue lists the C++ rules with their defaults", "[registry]") {
    const Json catalogue = Json::parse(catalogue_json());
    REQUIRE(catalogue["rules"].size() >= 4);
    CHECK(catalogue["result_schema_version"] == kResultSchemaVersion);

    const Json& clearance = catalogue["rules"][2];
    CHECK(clearance["type"] == "Clearance");
    CHECK(clearance["family"] == "TwoObjectRule");
    CHECK(clearance["slots"] == Json::array({"source", "target"}));
    CHECK(clearance["params"][0]["name"] == "clearance");
    CHECK(clearance["params"][0]["kind"] == "float");
    CHECK(clearance["params"][0]["default"] == 0.05);
    CHECK(clearance["params"][0]["unit"] == "m");
    CHECK(clearance["params"][1]["name"] == "check_all");
    CHECK(clearance["params"][1]["kind"] == "bool");
    CHECK(clearance["params"][1]["default"] == false);
}

TEST_CASE("the RuleSpec validates before any computation", "[registry]") {
    const Registry& registry = default_registry();
    const RuleSpec& clearance = registry.find("Clearance");

    CHECK(clearance.create(Json::object()) != nullptr);
    CHECK(clearance.create(Json{{"clearance", 0.2}, {"check_all", true}}) != nullptr);
    CHECK(clearance.create(Json{{"clearance", 1}}) != nullptr);  // an int is a valid float

    CHECK_THROWS_AS(clearance.create(Json{{"clearence", 0.2}}), ConfigError);    // typo
    CHECK_THROWS_AS(clearance.create(Json{{"clearance", "0.2"}}), ConfigError);  // type
    CHECK_THROWS_AS(clearance.create(Json{{"clearance", -1.0}}), ConfigError);   // min
    CHECK_THROWS_AS(clearance.create(Json{{"clearance", nullptr}}), ConfigError);
    CHECK_THROWS_AS(clearance.create(Json{{"check_all", 1}}), ConfigError);
    CHECK_THROWS_AS(registry.find("NotARule"), ConfigError);
}
