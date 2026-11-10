// The _triang rules (engine/triang): the .ifcview triangles only.
//
// The Duplex cases need the .ifcview v19 produced by BonsaiViewer next to
// the IfcSampleFiles (outside the repository): skipped when missing.
// Execution: ./build/engine/engine_tests "[triang]"
#include "api/Engine.h"
#include "triang/kernels/TriangleTests.h"
#include "triang/mesh/Obb.h"
#include "triang/mesh/TriMesh.h"
#include "triang/spatial/Proximity.h"
#include "triang/surface/Visibility.h"

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

SessionOptions with(CachePolicy policy, const std::string& triangles = "auto") {
    SessionOptions o;
    o.geometry_cache = policy;
    o.triangle_source = triangles;
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

// The pair rules, with the parameters of the parity cases.
const std::vector<std::pair<std::string, Json>> kRules{
    {"Intersection_triang", Json{{"tolerance", 0.002}}},
    {"Above_triang", Json{{"above_type", "Above_MaxToMin"}, {"tolerance", 1.0}}},
    {"Below_triang", Json{{"below_type", "Below_MinToMax"}, {"tolerance", 1.0}}},
    {"OBB_Above_triang", Json{{"tolerance", 1.0}}},
    {"OBB_Below_triang", Json{{"tolerance", 1.0}}},
    {"OBB_Front_And_Back_triang", Json{{"tolerance", 0.5}, {"direction_method", "Wide"}}},
    {"OBB_Custom_triang",
     Json{{"list_of_modifications", Json::array({"detach_top_by_extrude:0.5", "NEW_OBB", "extend_down:50%"})}}},
    {"AngleBetween_triang", Json{{"direction_method_for_source", "Wide"},
                                 {"direction_method_for_target", "Wide"},
                                 {"angle_difference", 90.0},
                                 {"angle_tolerance", 5.0}}},
    {"Clearance_triang", Json{{"clearance", 0.5}, {"check_all", true}}},
    {"Collision_triang", Json{{"allow_touching", false}}},
    {"ClearanceAxisToAxis_triang", Json{{"mode", "MinDistance"},
                                        {"min_distance", 0.2},
                                        {"max_distance", 5.0},
                                        {"tolerance", 0.01},
                                        {"linearity_ratio", 1.5},
                                        {"on_non_linear", "Fallback"},
                                        {"parallel_tolerance", 5.0},
                                        {"search_radius", 2.0}}},
    {"SurfaceRecover_triang", Json{{"direction", "Auto"},
                                   {"reference", "Source"},
                                   {"tolerance", 0.001},
                                   {"min_covering", nullptr},
                                   {"max_covering", Json::array({"relative", 80.0})}}},
    {"Ray_Check_triang", Json{{"max_ray_length", 5.0}}},
    {"TwoObjectsFace_triang", Json{{"source_face_selection", Json{{"orientation", "Top"}, {"extreme_faces", true}}},
                                   {"target_face_selection", Json{{"orientation", "Bottom"}}},
                                   {"distance", true},
                                   {"min_distance", 0.3},
                                   {"intersection", true}}},
};

// The one-object and set rules.
const std::vector<std::pair<std::string, Json>> kOneRules{
    {"ObbHigh_triang", Json{{"length_min", 0.0}, {"length_max", 1e9}}},
    {"ObbLength_triang", Json{{"length_min", 0.0}, {"length_max", 1e9}, {"direction_method", "Narrow"}}},
    {"Orientation_triang", Json{{"orientation", Json::array({0.0, 0.0, 1.0})},
                                {"orientation_type", "Perpendicular"},
                                {"direction_method", "Wide"},
                                {"angular_tolerance", 0.1}}},
    {"Alignement_triang", Json{{"axis", nullptr}, {"alignment_type", "Plane"}, {"tolerance", 0.05}, {"min_group", 3}}},
    {"Volume_triang", Json{{"volume_min", 0.0}, {"volume_max", 1e9}}},
    {"Area_triang", Json{{"volume_min", 0.0}, {"volume_max", 1e9}}},
    {"TopOrBottomSurface_triang", Json{{"surface_min", 0.0}, {"surface_max", 1e9}, {"top_or_bot_method", "Top"}}},
    {"LateralSurface_triang",
     Json{{"surface_min", 0.0}, {"surface_max", 1e9}, {"direction", Json::array({0.0, 1.0, 0.0})}}},
    {"ProjectedSurface_triang",
     Json{{"surface_min", 0.0}, {"surface_max", 1e9}, {"direction", Json::array({0.0, 0.0, 1.0})}}},
    {"OneObjectFace_triang", Json{{"face_a_selection", Json{{"orientation", "Top"}, {"extreme_faces", true}}},
                                  {"face_b_selection", Json{{"orientation", "Bottom"}, {"extreme_faces", true}}},
                                  {"skip_adjacent", true},
                                  {"distance", true},
                                  {"min_distance", 0.5},
                                  {"intersection", true}}},
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

TEST_CASE("TriMesh: weld, winding repair, closed test", "[triang]") {
    // A unit box, every face given with its own 4 vertices (no sharing, as
    // an unwelded triangulation) and every other triangle reversed.
    std::vector<double> v0;
    std::vector<int> f0;
    add_box(v0, f0, 0, 0, 0, 1, 1, 1);
    std::vector<double> v;
    std::vector<int> f;
    for (size_t t = 0; t < f0.size() / 3; ++t) {
        const int o = static_cast<int>(v.size() / 3);
        for (int k = 0; k < 3; ++k) {
            const int i = f0[3 * t + size_t(k)];
            v.insert(v.end(), {v0[3 * size_t(i)], v0[3 * size_t(i) + 1], v0[3 * size_t(i) + 2]});
        }
        if (t % 2) f.insert(f.end(), {o, o + 2, o + 1});
        else f.insert(f.end(), {o, o + 1, o + 2});
    }
    const triang::TriMesh m(v, f);
    CHECK(m.vertex_count() == 8);
    CHECK(m.triangle_count() == 12);
    CHECK(m.closed());
    CHECK(m.components() == 1);
    CHECK_THAT(m.volume(), Catch::Matchers::WithinAbs(1.0, 1e-12));
    CHECK_THAT(m.total_area(), Catch::Matchers::WithinAbs(6.0, 1e-12));
    // Outward normals: the top triangles point up.
    for (size_t t = 0; t < m.triangle_count(); ++t) {
        triang::P3 a, b, c;
        m.corners(t, a, b, c);
        if (a[2] == 1 && b[2] == 1 && c[2] == 1) CHECK(m.normal(t)[2] > 0.99);
        if (a[2] == 0 && b[2] == 0 && c[2] == 0) CHECK(m.normal(t)[2] < -0.99);
    }
    // The BVH finds the triangles near the top corner.
    Bnd_Box q;
    q.Update(0.9, 0.9, 0.9, 1.1, 1.1, 1.1);
    int hits = 0;
    m.tree().query(q, [&](int) { return ++hits, true; });
    CHECK(hits > 0);

    // The box without its top: open.
    std::vector<int> open(f0.begin(), f0.end());
    open.erase(open.begin() + 6, open.begin() + 12);  // triangles 2-3 (top)
    const triang::TriMesh o(v0, open);
    CHECK_FALSE(o.closed());
    CHECK(o.triangle_count() == 10);

    // Two boxes touching along an edge (the edge used by 4 triangles once
    // welded), the second one wound inwards: paired around the edge, both
    // wound outwards, closed.
    std::vector<double> w;
    std::vector<int> g;
    add_box(w, g, 0, 0, 0, 1, 1, 1);
    add_box(w, g, 1, 1, 0, 2, 2, 1);
    for (size_t t = 12; t < 24; ++t) std::swap(g[3 * t + 1], g[3 * t + 2]);
    const triang::TriMesh two(w, g);
    CHECK(two.closed());
    CHECK_THAT(two.volume(), Catch::Matchers::WithinAbs(2.0, 1e-12));
    for (size_t t = 0; t < two.triangle_count(); ++t) {
        triang::P3 a, b, c;
        two.corners(t, a, b, c);
        if (a[2] == 1 && b[2] == 1 && c[2] == 1) CHECK(two.normal(t)[2] > 0.99);
    }

    // The same pair turned about the shared edge (the vertical line x = y
    // = 1), every 15 degrees: wherever the angular order starts, each box
    // keeps its own faces (paired by their source indices first), the
    // volume is that of both boxes (a pairing across the empty wedge turned
    // one inside out: 2 - 2 = 0 at some angles).
    for (int step = 0; step < 24; ++step) {
        const double ang = step * M_PI / 12.0, ca = std::cos(ang), sa = std::sin(ang);
        std::vector<double> r = w;
        for (size_t i = 0; i < r.size(); i += 3) {
            const double x = r[i] - 1.0, y = r[i + 1] - 1.0;
            r[i] = 1.0 + ca * x - sa * y;
            r[i + 1] = 1.0 + sa * x + ca * y;
        }
        // Exactly the same position for the shared edge in both boxes.
        for (size_t i = 0; i < r.size(); i += 3)
            if (w[i] == 1.0 && w[i + 1] == 1.0) r[i] = 1.0, r[i + 1] = 1.0;
        const triang::TriMesh turned(r, g);
        INFO("turned by " << step * 15 << " degrees");
        CHECK(turned.closed());
        CHECK_THAT(turned.volume(), Catch::Matchers::WithinAbs(2.0, 1e-9));
    }

    // A collapsed triangle is dropped.
    const triang::TriMesh d(std::vector<double>{0, 0, 0, 1, 0, 0, 1, 0, 0}, std::vector<int>{0, 1, 2});
    CHECK(d.triangle_count() == 0);
}

TEST_CASE("distances and segments on triangles", "[triang]") {
    using namespace triang;
    std::vector<double> v;
    std::vector<int> f;
    add_box(v, f, 0, 0, 0, 1, 1, 1);
    const TriMesh a(v, f);
    std::vector<double> w;
    std::vector<int> g;
    add_box(w, g, 1.5, 0.2, 0.3, 2, 0.8, 0.6);  // 0.5 m beside a
    const TriMesh b(w, g);
    const MeshDistance d = mesh_distance(a, b);
    CHECK_THAT(d.distance, Catch::Matchers::WithinAbs(0.5, 1e-12));
    CHECK_THAT(d.a[0], Catch::Matchers::WithinAbs(1.0, 1e-12));
    CHECK_THAT(d.b[0], Catch::Matchers::WithinAbs(1.5, 1e-12));
    // Crossing boxes: 0.
    std::vector<double> x;
    std::vector<int> h;
    add_box(x, h, 0.5, 0.5, 0.5, 1.5, 1.5, 1.5);
    CHECK(mesh_distance(a, TriMesh(x, h)).distance == 0.0);
    // Beyond the cutoff: a distance above it.
    CHECK(mesh_distance(a, b, 0.1).distance > 0.1);

    // A segment through the box is blocked, one beside it is not; an owner
    // left out does not block.
    TriangleSoup soup;
    soup.add(7, a);
    soup.build();
    auto any = [](int) { return true; };
    CHECK(soup.segment_blocked({-1, 0.5, 0.5}, {2, 0.5, 0.5}, 1e-9, 0.0, any));
    CHECK_FALSE(soup.segment_blocked({-1, 2.5, 0.5}, {2, 2.5, 0.5}, 1e-9, 0.0, any));
    CHECK_FALSE(soup.segment_blocked({-1, 0.5, 0.5}, {2, 0.5, 0.5}, 1e-9, 0.0, [](int o) { return o != 7; }));
    // Ends on the surface: the hits at the ends are skipped.
    CHECK_FALSE(soup.segment_blocked({1, 0.5, 0.5}, {3, 0.5, 0.5}, 1e-9, 1e-6, any));
}

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

TEST_CASE("triangle_source='ifcview' needs an accepted .ifcview", "[triang]") {
    Session session({kModel}, with(CachePolicy::Off, "ifcview"));
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

TEST_CASE("triangle_source: an unknown value is a configuration error", "[triang]") {
    CHECK_THROWS_AS(Session({kModel}, with(CachePolicy::Off, "mesh")), ConfigError);
}

TEST_CASE("TriMesh: two parts welded along an edge, SampleCastle walls", "[triang]") {
    // Two walls of SampleCastle made of parts touching along an edge
    // (coplanar faces on one side of it in the .ifcview): their repaired
    // volume is the volume of the IFC triangulation (the original Volume,
    // 0.33773 and 0.04270 m3), on both triangle sources; a pairing across
    // the empty wedge turned one part inside out (0.25245, 0.02205).
    const fs::path castle = kSamples / "Ifc2x3_SampleCastle.ifc";
    const fs::path view = kSamples / "Ifc2x3_SampleCastle.ifcview";
    if (!fs::exists(castle) || !fs::exists(view)) SKIP("SampleCastle not available");
    const std::vector<std::pair<int, double>> walls{{833578, 0.337728836654}, {875825, 0.042701357640}};
    for (const char* source : {"ifcview", "ifc"}) {
        SessionOptions o = with(std::string(source) == "ifc" ? CachePolicy::Off : CachePolicy::Require, source);
        if (std::string(source) == "ifcview") o.ifcview_paths = {view.string()};
        Session session({castle}, o);
        for (const auto& [id, volume] : walls) {
            const auto [v, f] = session.triangles(0, id);
            const triang::TriMesh m(v, f);
            INFO(source << " #" << id);
            CHECK(m.closed());
            CHECK_THAT(m.volume(), Catch::Matchers::WithinAbs(volume, 1e-5));
        }
    }
}

TEST_CASE("triangle_source='auto' without .ifcview: the IFC triangulation", "[triang]") {
    Session session({kModel}, with(CachePolicy::Off, "auto"));
    RunRequest r;
    r.rule_type = "Intersection_triang";
    r.params = Json{{"tolerance", 0.002}};
    r.selections.source = {everything(0)};
    r.selections.target = {everything(0)};
    const RunResult result = session.run(r);
    CHECK(result.stats.triangles_from_view == 0);
    CHECK(result.stats.triangles_from_ifc > 0);
    CHECK_FALSE(result.results.empty());  // the two cubes intersect by 10 cm
    // The same with triangle_source='ifc'.
    Session ifc({kModel}, with(CachePolicy::Off, "ifc"));
    CHECK(pairs_of(ifc.run(r)) == pairs_of(result));
}

TEST_CASE("the _triang rules on the Duplex: .ifcview only, prefilters only remove", "[triang]") {
    if (!duplex_views()) SKIP("Duplex .ifcview not available on this machine");
    Session session({kArch, kMech}, with(CachePolicy::Require, "ifcview"));
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
        CHECK(on.stats.triangles_from_ifc == 0);
    }
    for (const auto& [type, params] : kOneRules) {
        RunRequest r;
        r.rule_type = type;
        r.params = params;
        r.selections.source = {everything(0), everything(1)};
        INFO(type);
        const RunResult result = session.run(r);
        CHECK_FALSE(result.results.empty());
        CHECK(result.stats.triangles_from_ifc == 0);
    }
    // Not one IFC element triangulated by the _triang rules.
    CHECK(session.ifc_conversions() == 0);
}

TEST_CASE("Below_triang mirrors Above_triang", "[triang]") {
    if (!duplex_views()) SKIP("Duplex .ifcview not available on this machine");
    Session session({kArch, kMech}, with(CachePolicy::Require, "ifcview"));
    RunRequest above;
    above.rule_type = "Above_triang";
    above.params = Json{{"above_type", "Above_MaxToMin"}, {"tolerance", 1.0}};
    above.selections.source = {everything(0)};
    above.selections.target = {everything(1)};
    RunRequest below;
    below.rule_type = "Below_triang";
    below.params = Json{{"below_type", "Below_MinToMax"}, {"tolerance", 1.0}};
    below.selections.source = {everything(1)};
    below.selections.target = {everything(0)};
    const RunResult a = session.run(above), b = session.run(below);
    // Above(S, T) and Below(T, S) measure the same gap on the same faces; only
    // the prefilter of the originals differs (the band above S against the
    // band below T, on tilted OBBs), so the two sets nearly coincide.
    auto reversed = pairs_of(b);
    for (auto& p : reversed) std::swap(p.first, p.second);
    std::sort(reversed.begin(), reversed.end());
    const auto direct = pairs_of(a);
    std::vector<std::pair<int, int>> common;
    std::set_intersection(direct.begin(), direct.end(), reversed.begin(), reversed.end(), std::back_inserter(common));
    INFO(direct.size() << " Above pairs, " << reversed.size() << " Below pairs, " << common.size() << " common");
    CHECK(common.size() >= 0.9 * std::max(direct.size(), reversed.size()));
}

TEST_CASE("the _triang rules on the Duplex: 'auto' completes the .ifcview with the IFC", "[triang]") {
    if (!duplex_views()) SKIP("Duplex .ifcview not available on this machine");
    Session view({kArch, kMech}, with(CachePolicy::Require, "ifcview"));
    Session automatic({kArch, kMech}, with(CachePolicy::Require, "auto"));
    RunRequest r;
    r.rule_type = "OBB_Above_triang";
    r.params = Json{{"tolerance", 1.0}};
    r.selections.source = {everything(0)};
    r.selections.target = {everything(1)};
    const RunResult a = view.run(r);
    const RunResult b = automatic.run(r);
    CHECK(b.stats.triangles_from_view == a.stats.triangles_from_view);
    CHECK(b.stats.triangles_from_ifc > 0);  // the elements missing from the .ifcview (openings...)
    CHECK_FALSE(has(b.diagnostics, "not_in_ifcview"));
    // Every pair of the .ifcview run is still there.
    const auto pa = pairs_of(a), pb = pairs_of(b);
    CHECK(std::includes(pb.begin(), pb.end(), pa.begin(), pa.end()));
}

TEST_CASE("the _triang rules: the results do not depend on the threads", "[triang]") {
    if (!duplex_views()) SKIP("Duplex .ifcview not available on this machine");
    SessionOptions one = with(CachePolicy::Require, "ifcview");
    one.rule_threads = 1;
    SessionOptions many = with(CachePolicy::Require, "ifcview");
    many.rule_threads = 0;
    Session s1({kArch, kMech}, one), s2({kArch, kMech}, many);
    for (const auto& [type, params] : kRules) {
        RunRequest r;
        r.rule_type = type;
        r.params = params;
        r.selections.source = {everything(0)};
        r.selections.target = {everything(1)};
        INFO(type);
        const RunResult a = s1.run(r), b = s2.run(r);
        CHECK(pairs_of(a) == pairs_of(b));
        REQUIRE(a.results.size() == b.results.size());
        for (size_t k = 0; k < a.results.size(); ++k) CHECK(to_json(a.results[k]) == to_json(b.results[k]));
    }
}
