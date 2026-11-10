#include "Slices.h"

#include "../mesh/TriMesh.h"

#include <algorithm>
#include <cstdint>
#include <unordered_map>

namespace ifcclash::triang {

std::vector<P3> clip_triangle_z(const P3& a, const P3& b, const P3& c, double z0, double z1) {
    std::vector<P3> poly{a, b, c};
    auto clip = [](const std::vector<P3>& in, double h, bool keep_above) {
        std::vector<P3> out;
        auto inside = [&](const P3& p) { return keep_above ? p[2] >= h : p[2] <= h; };
        for (size_t i = 0; i < in.size(); ++i) {
            const P3& cur = in[i];
            const P3& prev = in[(i + in.size() - 1) % in.size()];
            const bool ic = inside(cur), ip = inside(prev);
            if (ic != ip) {
                const double t = (h - prev[2]) / (cur[2] - prev[2]);
                out.push_back({prev[0] + t * (cur[0] - prev[0]), prev[1] + t * (cur[1] - prev[1]), h});
            }
            if (ic) out.push_back(cur);
        }
        return out;
    };
    poly = clip(poly, z0, true);
    if (poly.size() < 3) return {};
    poly = clip(poly, z1, false);
    if (poly.size() < 3) return {};
    return poly;
}

std::vector<std::vector<P2>> section_loops(const TriMesh& mesh, double h) {
    // A vertex exactly on the plane is moved above it by a hair (symbolic
    // perturbation): every crossing then cuts two edges, never a vertex.
    auto above = [&](int v) { return mesh.vertex(v)[2] >= h; };
    auto edge_key = [](int a, int b) {
        const auto lo = static_cast<uint32_t>(std::min(a, b)), hi = static_cast<uint32_t>(std::max(a, b));
        return (uint64_t(lo) << 32) | hi;
    };
    auto cut = [&](int a, int b) -> P2 {
        const P3 p = mesh.vertex(a), q = mesh.vertex(b);
        const double t = (q[2] == p[2]) ? 0.5 : (h - p[2]) / (q[2] - p[2]);
        return {p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])};
    };
    // Segments between two cut edges; adjacency edge -> the segments using it.
    struct Segment {
        uint64_t e0, e1;
    };
    std::vector<Segment> segments;
    std::unordered_map<uint64_t, P2> points;
    std::unordered_map<uint64_t, std::vector<size_t>> by_edge;
    const auto& f = mesh.faces();
    for (size_t t = 0; t < mesh.triangle_count(); ++t) {
        const int v[3] = {f[3 * t], f[3 * t + 1], f[3 * t + 2]};
        std::vector<uint64_t> cuts;
        for (int k = 0; k < 3; ++k) {
            const int a = v[k], b = v[(k + 1) % 3];
            if (above(a) == above(b)) continue;
            const uint64_t key = edge_key(a, b);
            cuts.push_back(key);
            points.emplace(key, cut(a, b));
        }
        if (cuts.size() != 2) continue;
        by_edge[cuts[0]].push_back(segments.size());
        by_edge[cuts[1]].push_back(segments.size());
        segments.push_back({cuts[0], cuts[1]});
    }
    // Chain the segments into loops.
    std::vector<char> used(segments.size(), 0);
    std::vector<std::vector<P2>> loops;
    for (size_t s0 = 0; s0 < segments.size(); ++s0) {
        if (used[s0]) continue;
        used[s0] = 1;
        std::vector<P2> loop{points[segments[s0].e0]};
        const uint64_t start = segments[s0].e0;
        uint64_t edge = segments[s0].e1;
        while (edge != start) {
            loop.push_back(points[edge]);
            size_t next = segments.size();
            for (size_t s : by_edge[edge]) {
                if (!used[s]) {
                    next = s;
                    break;
                }
            }
            if (next == segments.size()) break;  // open chain (open mesh)
            used[next] = 1;
            edge = segments[next].e0 == edge ? segments[next].e1 : segments[next].e0;
        }
        if (loop.size() >= 3) loops.push_back(std::move(loop));
    }
    return loops;
}

}  // namespace ifcclash::triang
