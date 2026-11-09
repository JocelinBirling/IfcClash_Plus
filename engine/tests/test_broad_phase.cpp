#include "pipeline/BroadPhase.h"

#include <catch2/catch_test_macros.hpp>

#include <random>

using namespace ifcclash;

namespace {

Bnd_Box box(double x0, double y0, double z0, double x1, double y1, double z1) {
    Bnd_Box b;
    b.Update(x0, y0, z0, x1, y1, z1);
    return b;
}

bool overlap(const Bnd_Box& a, const Bnd_Box& b) { return !a.IsOut(b); }

}  // namespace

TEST_CASE("overlapping_pairs on a small case", "[broad]") {
    std::vector<Bnd_Box> a{box(0, 0, 0, 1, 1, 1), box(5, 5, 5, 6, 6, 6), Bnd_Box()};
    std::vector<Bnd_Box> b{box(1, 0, 0, 2, 1, 1),  // touching a[0]
                           box(0.5, 0.5, 0.5, 5.5, 5.5, 5.5), box(10, 10, 10, 11, 11, 11)};
    const auto pairs = overlapping_pairs(a, b);
    const std::vector<std::pair<int, int>> expected{{0, 0}, {0, 1}, {1, 1}};
    CHECK(pairs == expected);
    CHECK(overlapping_pairs({}, b).empty());
}

TEST_CASE("overlapping_pairs matches the brute force", "[broad]") {
    std::mt19937 rng(42);
    std::uniform_real_distribution<double> pos(0.0, 50.0), size(0.1, 4.0);
    auto random_boxes = [&](int n) {
        std::vector<Bnd_Box> out;
        for (int i = 0; i < n; ++i) {
            const double x = pos(rng), y = pos(rng), z = pos(rng);
            out.push_back(box(x, y, z, x + size(rng), y + size(rng), z + size(rng)));
        }
        return out;
    };
    const auto a = random_boxes(300);
    const auto b = random_boxes(250);

    std::vector<std::pair<int, int>> brute;
    for (int i = 0; i < 300; ++i)
        for (int j = 0; j < 250; ++j)
            if (overlap(a[i], b[j])) brute.emplace_back(i, j);

    CHECK(overlapping_pairs(a, b) == brute);
}
