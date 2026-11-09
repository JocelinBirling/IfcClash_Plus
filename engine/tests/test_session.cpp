// End-to-end tests of a Session on the calibrated test models.
// CubeA_Intersect_CubeB_10cm.ifc: CubeA (#2787) and CubeB (#2765), 1 m cubes
// overlapping by 10 cm.
#include "api/Engine.h"

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

using namespace ifcclash;
using Catch::Approx;

namespace {

const std::filesystem::path kModel =
    std::filesystem::path(IFCCLASH_REPO_DIR) / "IFC_Test_Model/IFC_Model/CubeA_Intersect_CubeB_10cm.ifc";
constexpr int kCubeA = 2787;
constexpr int kCubeB = 2765;

SessionOptions quiet_options() {
    SessionOptions o;
    o.geometry_cache = CachePolicy::Off;
    return o;
}

RunRequest pair_request(const std::string& rule, Json params = Json::object()) {
    RunRequest r;
    r.rule_type = rule;
    r.params = std::move(params);
    r.selections.source = {{0, {}, {kCubeA}}};
    r.selections.target = {{0, {}, {kCubeB}}};
    return r;
}

}  // namespace

TEST_CASE("Session: Volume of the 1 m cubes", "[session]") {
    Session session({kModel}, quiet_options());
    RunRequest r;
    r.rule_type = "Volume";
    r.params = Json{{"volume_min", 0.5}, {"volume_max", 1.5}};
    r.selections.source = {{0, {}, {kCubeA, kCubeB}}};
    const RunResult result = session.run(r);
    REQUIRE(result.results.size() == 2);
    for (const auto& record : result.results) {
        CHECK_FALSE(record.target.has_value());
        CHECK(record.measures.get(Measure::Volume).value() == Approx(1.0).epsilon(1e-6));
    }
    // Sorted by (file, GlobalId).
    CHECK(result.results[0].source < result.results[1].source);
}

TEST_CASE("Session: selection by GlobalId and unknown ids", "[session]") {
    Session session({kModel}, quiet_options());
    RunRequest r;
    r.rule_type = "Volume";
    r.selections.source = {{0, {"0FsnxVQcv6U9Or9sItIXN$", "doesNotExist0000000000"}, {}}};
    const RunResult result = session.run(r);
    REQUIRE(result.results.size() == 1);
    CHECK(result.results[0].source.entity_id == kCubeA);
    bool unknown = false;
    for (const auto& d : result.diagnostics.entries) unknown = unknown || d.code == "unknown_global_id";
    CHECK(unknown);
}

TEST_CASE("Session: Collision flags the overlapping cubes, with and without prefilter", "[session]") {
    Session session({kModel}, quiet_options());
    RunRequest r = pair_request("Collision");
    const RunResult on = session.run(r);
    REQUIRE(on.results.size() == 1);
    CHECK(on.results[0].source.entity_id == kCubeA);
    CHECK(on.results[0].target->entity_id == kCubeB);
    CHECK(on.results[0].points.size() == 1);

    r.prefilter = false;
    const RunResult off = session.run(r);
    REQUIRE(off.results.size() == 1);
    CHECK(to_json(off.results[0]) == to_json(on.results[0]));
}

TEST_CASE("Session: Clearance and Intersection", "[session]") {
    Session session({kModel}, quiet_options());
    CHECK(session.run(pair_request("Clearance", Json{{"clearance", 0.05}})).results.size() == 1);
    CHECK(session.run(pair_request("Intersection", Json{{"tolerance", 0.01}})).results.size() == 1);
    // An element is never tested against itself.
    RunRequest self = pair_request("Collision");
    self.selections.target = self.selections.source;
    CHECK(session.run(self).results.empty());
}

TEST_CASE("Session: configuration errors raise before computing", "[session]") {
    Session session({kModel}, quiet_options());
    CHECK_THROWS_AS(session.run(pair_request("NotARule")), ConfigError);
    CHECK_THROWS_AS(session.run(pair_request("Clearance", Json{{"clearance", -0.1}})), ConfigError);
    CHECK_THROWS_AS(Session({"/no/such/file.ifc"}, quiet_options()), ConfigError);

    SessionOptions require = quiet_options();
    require.geometry_cache = CachePolicy::Require;
    CHECK_THROWS_AS(Session({kModel}, require), ConfigError);
}

TEST_CASE("Session: cancellation and evaluate_pairs", "[session]") {
    Session session({kModel}, quiet_options());
    CancelToken token;
    token.cancel();
    ProgressSink sink;
    CHECK_THROWS_AS(session.run(pair_request("Collision"), token, sink), Cancelled);

    RunRequest r = pair_request("Collision");
    const std::vector<KeyPair> pairs{{ElementKey{0, kCubeA, ""}, ElementKey{0, kCubeB, ""}}};
    const RunResult result = session.evaluate_pairs(r, pairs);
    REQUIRE(result.results.size() == 1);
    CHECK(result.results[0].source.global_id == "0FsnxVQcv6U9Or9sItIXN$");
}
