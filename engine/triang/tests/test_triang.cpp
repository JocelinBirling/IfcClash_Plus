// The _triang rules (engine/triang): the .ifcview triangles only.
//
// The Duplex cases need the .ifcview v19 produced by BonsaiViewer next to
// the IfcSampleFiles (outside the repository): skipped when missing.
// Execution: ./build/engine/engine_tests "[triang]"
#include "api/Engine.h"
#include "triang/HeightMap.h"
#include "triang/TriangleTests.h"

#include <catch2/catch_test_macros.hpp>
#include <catch2/matchers/catch_matchers_floating_point.hpp>

#include <algorithm>
#include <filesystem>

using namespace ifcclash;
namespace fs = std::filesystem;

namespace {

const fs::path kRepo(IFCCLASH_REPO_DIR);
const fs::path kModel = kRepo / "IFC_Test_Model/IFC_Model/CubeA_Intersect_CubeB_10cm.ifc";
const fs::path kSamples = "/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main";
const fs::path kArch = kSamples / "Ifc2x3_Duplex_Architecture.ifc";
const fs::path kMech = kSamples / "Ifc2x3_Duplex_Mechanical.ifc";

bool duplex_views() {
    return fs::exists(kSamples / "Ifc2x3_Duplex_Architecture.ifcview") &&
           fs::exists(kSamples / "Ifc2x3_Duplex_Mechanical.ifcview");
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

// Every STEP id 1..60000 of a file: the source resolves the products.
FileSelection everything(uint32_t file) {
    FileSelection sel{file, {}, {}};
    for (int id = 1; id < 60000; ++id) sel.entity_ids.push_back(id);
    return sel;
}

std::vector<std::pair<int, int>> pairs_of(const RunResult& r) {
    std::vector<std::pair<int, int>> out;
    for (const auto& x : r.results) out.emplace_back(x.source.entity_id, x.target ? x.target->entity_id : -1);
    std::sort(out.begin(), out.end());
    return out;
}

const std::vector<std::pair<std::string, Json>> kRules{
    {"Intersection_triang", Json{{"tolerance", 0.002}}},
    {"Above_triang", Json{{"above_type", "Above_MaxToMin"}, {"tolerance", 1.0}}},
    {"OBB_Above_triang", Json{{"tolerance", 1.0}}},
};

}  // namespace

// ---------------------------------------------------------------- geometry

TEST_CASE("triangle against an oriented box", "[triang]") {
    Bnd_OBB box(gp_Pnt(0, 0, 0), gp_Dir(1, 0, 0), gp_Dir(0, 1, 0), gp_Dir(0, 0, 1), 1, 1, 1);
    using triang::triangle_meets_obb;
    CHECK(triangle_meets_obb({0, 0, 0}, {5, 0, 0}, {0, 5, 0}, box, 0));        // a vertex inside
    CHECK(triangle_meets_obb({-5, -5, 0}, {5, -5, 0}, {0, 5, 0}, box, 0));     // the box inside the triangle
    CHECK_FALSE(triangle_meets_obb({0, 0, 2}, {5, 0, 2}, {0, 5, 2}, box, 0));  // above
    CHECK(triangle_meets_obb({0, 0, 1.0000005}, {5, 0, 1.0000005}, {0, 5, 1.0000005}, box, 1e-6));
    CHECK_FALSE(triangle_meets_obb({1.5, 1.5, -1}, {3, 1.5, -1}, {1.5, 3, 1}, box, 0));  // beside the corner
}

TEST_CASE("plan overlap of two triangles", "[triang]") {
    using triang::clip_triangles_xy;
    CHECK(clip_triangles_xy({0, 0, 0}, {2, 0, 0}, {0, 2, 0}, {0, 0, 1}, {2, 0, 1}, {0, 2, 1}).size() >= 3);
    CHECK(clip_triangles_xy({0, 0, 0}, {1, 0, 0}, {0, 1, 0}, {5, 5, 1}, {6, 5, 1}, {5, 6, 1}).empty());
    // A vertical target triangle has no plan area.
    CHECK(clip_triangles_xy({0, 0, 0}, {1, 0, 0}, {0, 1, 0}, {0, 0, 0}, {1, 0, 0}, {0, 0, 1}).empty());
}

namespace {

// An axis-aligned box as 12 triangles appended to (verts, faces).
void add_box(std::vector<double>& verts, std::vector<int>& faces, double x0, double y0, double z0, double x1,
             double y1, double z1) {
    const int o = static_cast<int>(verts.size() / 3);
    for (int k = 0; k < 8; ++k) {
        verts.insert(verts.end(), {k & 1 ? x1 : x0, k & 2 ? y1 : y0, k & 4 ? z1 : z0});
    }
    const int q[6][4] = {{0, 1, 3, 2}, {4, 5, 7, 6}, {0, 1, 5, 4}, {2, 3, 7, 6}, {0, 2, 6, 4}, {1, 3, 7, 5}};
    for (const auto& f : q) faces.insert(faces.end(), {o + f[0], o + f[1], o + f[2], o + f[0], o + f[2], o + f[3]});
}

}  // namespace

TEST_CASE("height map: the triangles seen from above and below", "[triang]") {
    using triang::visible_triangles;
    using triang::visible_triangles_raster;
    std::vector<double> v;
    std::vector<int> f;
    add_box(v, f, 0, 0, 0, 1, 1, 1);               // triangles 0..11, bottom 0-1, top 2-3
    add_box(v, f, -0.5, -0.5, 2, 1.5, 1.5, 3);     // triangles 12..23, bottom 12-13, top 14-15
    // From above: only the top of the large upper box.
    CHECK(visible_triangles_raster(v, f, +1) == std::vector<int>{14, 15});
    // From below: both bottoms (the upper one shows as a ring).
    CHECK(visible_triangles_raster(v, f, -1) == std::vector<int>{0, 1, 12, 13});
    // Same answer as the sampled coverage test.
    auto sorted = [](std::vector<int> x) {
        std::sort(x.begin(), x.end());
        return x;
    };
    CHECK(sorted(visible_triangles(v, f, +1)) == visible_triangles_raster(v, f, +1));
    CHECK(sorted(visible_triangles(v, f, -1)) == visible_triangles_raster(v, f, -1));

    // A coarse grid (forced by max_side) keeps the answer.
    triang::HeightMapOptions coarse;
    coarse.max_side = 4;
    CHECK(visible_triangles_raster(v, f, +1, coarse) == std::vector<int>{14, 15});

    const triang::HeightMap map = triang::height_map(v, f, +1);
    REQUIRE_FALSE(map.empty());
    CHECK(map.nx == 200);
    CHECK(map.ny == 200);
    const size_t centre = map.index(100, 100);
    CHECK(map.z[centre] == 3.0);
    CHECK((map.id[centre] == 14 || map.id[centre] == 15));
}

TEST_CASE("visible triangles: the method follows the mesh size", "[triang]") {
    using triang::visible_triangles_auto;
    // A box under a slab that hides all of its top but a 5 cm band along
    // x = 1: the band holds none of the 4 sampled points of the two top
    // triangles (the nearest is at x = 0.933), but many cell centres.
    std::vector<double> v;
    std::vector<int> f;
    add_box(v, f, 0, 0, 0, 1, 1, 1);                 // top: triangles 2-3
    add_box(v, f, -0.1, -0.1, 2, 0.95, 1.1, 2.1);    // 24 triangles in all
    auto has_top = [](const std::vector<int>& x) {
        return std::count(x.begin(), x.end(), 2) + std::count(x.begin(), x.end(), 3) > 0;
    };
    const auto sampled = visible_triangles_auto(v, f, +1);    // 24 < 200: sampled
    const auto raster = visible_triangles_auto(v, f, +1, 24);  // 24 >= 24: height map
    CHECK_FALSE(has_top(sampled));
    CHECK(has_top(raster));
    CHECK(sampled == triang::visible_triangles(v, f, +1));
    CHECK(raster == triang::visible_triangles_raster(v, f, +1));
}

TEST_CASE("height map: triangles smaller than a cell", "[triang]") {
    using triang::visible_triangles_raster;
    // A 1 mm triangle alone, 1 cm cells: seen at its centroid.
    std::vector<double> v{0, 0, 0, 0.001, 0, 0, 0, 0.001, 0};
    std::vector<int> f{0, 1, 2};
    CHECK(visible_triangles_raster(v, f, +1) == std::vector<int>{0});
    // Under a large triangle: hidden from above, seen from below.
    v.insert(v.end(), {-1, -1, 1, 2, -1, 1, -1, 2, 1});
    f.insert(f.end(), {3, 4, 5});
    CHECK(visible_triangles_raster(v, f, +1) == std::vector<int>{1});
    CHECK(visible_triangles_raster(v, f, -1) == std::vector<int>{0, 1});
}

// ---------------------------------------------------------------- the rules

TEST_CASE("a _triang rule needs an accepted .ifcview", "[triang]") {
    Session session({kModel}, with(CachePolicy::Off));
    for (const auto& [type, params] : kRules) {
        RunRequest r;
        r.rule_type = type;
        r.params = params;
        r.selections.source = {everything(0)};
        r.selections.target = {everything(0)};
        INFO(type);
        CHECK_THROWS_AS(session.run(r), ConfigError);
    }
}

TEST_CASE("the _triang rules on the Duplex: .ifcview only, prefilters only remove", "[triang]") {
    if (!duplex_views()) SKIP("Duplex .ifcview not available on this machine");
    Session session({kArch, kMech}, with(CachePolicy::Require));
    REQUIRE(has(session.diagnostics(), "ifcview_accepted"));
    for (const auto& [type, params] : kRules) {
        RunRequest r;
        r.rule_type = type;
        r.params = params;
        r.selections.source = {everything(0)};
        r.selections.target = {everything(1)};
        const RunResult on = session.run(r);
        r.prefilter = false;
        const RunResult off = session.run(r);
        INFO(type << ": " << on.stats.summary());
        CHECK_FALSE(on.results.empty());
        CHECK(pairs_of(on) == pairs_of(off));
        CHECK_FALSE(has(on.diagnostics, "prefilter_lost_clash"));
    }
    // Not one IFC element triangulated by the three rules.
    CHECK(session.ifc_conversions() == 0);
}
