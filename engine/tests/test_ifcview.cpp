// The optional .ifcview source (SPEC "Tests": robustness of the cache and
// invariance of the results with respect to the source of the boxes).
#include "api/Engine.h"

#include <catch2/catch_test_macros.hpp>

#include <chrono>
#include <cstring>
#include <fstream>

using namespace ifcclash;
namespace fs = std::filesystem;

namespace {

const fs::path kRepo(IFCCLASH_REPO_DIR);
const fs::path kModel = kRepo / "IFC_Test_Model/IFC_Model/CubeA_Intersect_CubeB_10cm.ifc";
// .ifcview v19 produced by BonsaiViewer (outside the repository: the test
// is skipped when it is missing).
const fs::path kSamples = "/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main";

fs::path scratch() {
    auto dir = fs::temp_directory_path() / "ifcclash_ifcview_tests";
    fs::create_directories(dir);
    return dir;
}

// A copy of the test model with a .ifcview of the given content next to it.
fs::path model_with_view(const std::string& name, const std::string& content, bool view_older) {
    const auto dir = scratch() / name;
    fs::create_directories(dir);
    const auto ifc = dir / "model.ifc";
    fs::copy_file(kModel, ifc, fs::copy_options::overwrite_existing);
    std::ofstream(dir / "model.ifcview", std::ios::binary) << content;
    const auto now = fs::file_time_type::clock::now();
    fs::last_write_time(ifc, now);
    fs::last_write_time(dir / "model.ifcview", view_older ? now - std::chrono::hours(1) : now + std::chrono::hours(1));
    return ifc;
}

bool has(const Diagnostics& d, const std::string& code) {
    for (const auto& e : d.entries)
        if (e.code == code) return true;
    return false;
}

SessionOptions with(CachePolicy policy) {
    SessionOptions o;
    o.geometry_cache = policy;
    return o;
}

}  // namespace

TEST_CASE("missing .ifcview: Auto falls back on the IFC, Require raises", "[ifcview]") {
    Session session({kModel}, with(CachePolicy::Auto));
    CHECK(has(session.diagnostics(), "ifcview_missing"));
    CHECK_THROWS_AS(Session({kModel}, with(CachePolicy::Require)), ConfigError);
}

TEST_CASE("corrupted .ifcview is rejected", "[ifcview]") {
    const auto ifc = model_with_view("corrupted", "not an ifcview at all", false);
    Session session({ifc}, with(CachePolicy::Auto));
    CHECK(has(session.diagnostics(), "ifcview_rejected"));
    CHECK_THROWS_AS(Session({ifc}, with(CachePolicy::Require)), ConfigError);

    // Wrong version: a valid magic, version 6.
    std::string v6(20, '\0');
    const uint32_t head[3] = {0x49465657u, 6u, 0x01020304u};
    std::memcpy(v6.data(), head, sizeof head);
    const auto old_format = model_with_view("version6", v6, false);
    CHECK(has(Session({old_format}, with(CachePolicy::Auto)).diagnostics(), "ifcview_rejected"));
}

TEST_CASE(".ifcview older than the IFC is rejected unless trusted", "[ifcview]") {
    const auto ifc = model_with_view("older", "garbage", true);
    Session session({ifc}, with(CachePolicy::Auto));
    bool older = false;
    for (const auto& e : session.diagnostics().entries)
        older = older || (e.code == "ifcview_rejected" && e.message.find("older") != std::string::npos);
    CHECK(older);
}

TEST_CASE("results do not depend on the source of the boxes (Duplex .ifcview)", "[ifcview]") {
    const auto arch = kSamples / "Ifc2x3_Duplex_Architecture.ifc";
    const auto mech = kSamples / "Ifc2x3_Duplex_Mechanical.ifc";
    if (!fs::exists(arch.parent_path() / "Ifc2x3_Duplex_Architecture.ifcview") ||
        !fs::exists(mech.parent_path() / "Ifc2x3_Duplex_Mechanical.ifcview")) {
        SKIP("Duplex .ifcview not available on this machine");
    }
    Session ifc_only({arch, mech}, with(CachePolicy::Off));
    Session cached({arch, mech}, with(CachePolicy::Require));
    REQUIRE(has(cached.diagnostics(), "ifcview_accepted"));

    // Every product of each file (ids from a Volume run on the IFC session).
    RunRequest all;
    all.rule_type = "Volume";
    all.params = Json{{"volume_min", -1.0}, {"volume_max", 1e12}};
    std::vector<int> ids0, ids1;
    for (uint32_t f = 0; f < 2; ++f) {
        // GlobalIds are unknown here: select by a wide id range resolved by the source.
        FileSelection sel{f, {}, {}};
        for (int id = 1; id < 60000; ++id) sel.entity_ids.push_back(id);
        all.selections.source = {sel};
        Diagnostics quiet;
        for (const auto& r : ifc_only.run(all).results) (f == 0 ? ids0 : ids1).push_back(r.source.entity_id);
    }
    REQUIRE_FALSE(ids0.empty());
    REQUIRE_FALSE(ids1.empty());

    for (const char* rule : {"Intersection", "Clearance", "Collision"}) {
        RunRequest r;
        r.rule_type = rule;
        r.selections.source = {{0, {}, ids0}};
        r.selections.target = {{1, {}, ids1}};
        const RunResult a = ifc_only.run(r);
        const RunResult b = cached.run(r);
        INFO(rule);
        REQUIRE(a.results.size() == b.results.size());
        for (size_t i = 0; i < a.results.size(); ++i) CHECK(to_json(a.results[i]) == to_json(b.results[i]));
        CHECK_FALSE(has(b.diagnostics, "prefilter_lost_clash"));
    }
}
