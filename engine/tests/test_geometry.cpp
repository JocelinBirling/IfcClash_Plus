#include "geometry/MeshMeasures.h"

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

#include <gp_Pnt.hxx>

using namespace ifcclash;
using Catch::Approx;

namespace {

// Unit cube [0,1]^3, 12 outward triangles.
void unit_cube(std::vector<double>& v, std::vector<int>& f) {
    v = {0, 0, 0, 1, 0, 0, 1, 1, 0, 0, 1, 0, 0, 0, 1, 1, 0, 1, 1, 1, 1, 0, 1, 1};
    f = {0, 2, 1, 0, 3, 2, 4, 5, 6, 4, 6, 7, 0, 1, 5, 0, 5, 4,
         1, 2, 6, 1, 6, 5, 2, 3, 7, 2, 7, 6, 3, 0, 4, 3, 4, 7};
}

}  // namespace

TEST_CASE("mesh_volume of a unit cube", "[geometry]") {
    std::vector<double> v;
    std::vector<int> f;
    unit_cube(v, f);
    CHECK(geometry::mesh_volume(v, f) == Approx(1.0).epsilon(1e-12));

    // abs(): an inward-oriented cube has the same volume (get_volume).
    for (size_t i = 0; i < f.size(); i += 3) std::swap(f[i + 1], f[i + 2]);
    CHECK(geometry::mesh_volume(v, f) == Approx(1.0).epsilon(1e-12));
}

TEST_CASE("inflate accumulates, unlike Bnd_Box::Enlarge", "[geometry]") {
    std::vector<double> v;
    std::vector<int> f;
    unit_cube(v, f);
    const Bnd_Box box = geometry::aabb_of(v);
    const Bnd_Box twice = geometry::inflate(geometry::inflate(box, 0.1), 0.2);
    double x0, y0, z0, x1, y1, z1;
    twice.Get(x0, y0, z0, x1, y1, z1);
    CHECK(x0 == Approx(-0.3));
    CHECK(x1 == Approx(1.3));
    CHECK(geometry::inflate(Bnd_Box(), 1.0).IsVoid());
}

TEST_CASE("obb_of contains every vertex", "[geometry]") {
    std::vector<double> v;
    std::vector<int> f;
    unit_cube(v, f);
    const Bnd_OBB obb = geometry::obb_of(v);
    REQUIRE_FALSE(obb.IsVoid());
    for (size_t i = 0; i < v.size(); i += 3) {
        CHECK_FALSE(geometry::inflate(obb, 1e-9).IsOut(gp_Pnt(v[i], v[i + 1], v[i + 2])));
    }
    CHECK(geometry::obb_of({}).IsVoid());
}
