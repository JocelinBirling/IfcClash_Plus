#include "TriMesh.h"

#include <gp_Pnt.hxx>

#include <algorithm>
#include <cmath>
#include <cstring>
#include <deque>
#include <map>
#include <tuple>
#include <unordered_map>

namespace ifcclash::triang {

namespace {

// Bit pattern of a coordinate, -0.0 folded on +0.0 (exact weld).
uint64_t bits(double x) {
    if (x == 0.0) x = 0.0;
    uint64_t b;
    std::memcpy(&b, &x, sizeof b);
    return b;
}

struct VertexKey {
    uint64_t x, y, z;
    bool operator==(const VertexKey& o) const { return x == o.x && y == o.y && z == o.z; }
};
struct VertexKeyHash {
    size_t operator()(const VertexKey& k) const {
        size_t h = std::hash<uint64_t>()(k.x);
        h ^= std::hash<uint64_t>()(k.y) + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2);
        h ^= std::hash<uint64_t>()(k.z) + 0x9e3779b97f4a7c15ULL + (h << 6) + (h >> 2);
        return h;
    }
};

uint64_t edge_key(int a, int b) {
    const auto lo = static_cast<uint32_t>(std::min(a, b)), hi = static_cast<uint32_t>(std::max(a, b));
    return (uint64_t(lo) << 32) | hi;
}

}  // namespace

TriMesh::TriMesh(const Mesh& mesh) : TriMesh(mesh.world_verts, mesh.faces) {}

TriMesh::TriMesh(std::vector<double> verts, std::vector<int> faces) {
    // ---- Weld (exact positions) and drop the collapsed triangles
    std::unordered_map<VertexKey, int, VertexKeyHash> index;
    std::vector<int> remap(verts.size() / 3);
    for (size_t v = 0; v < remap.size(); ++v) {
        const VertexKey k{bits(verts[3 * v]), bits(verts[3 * v + 1]), bits(verts[3 * v + 2])};
        auto [it, fresh] = index.emplace(k, static_cast<int>(verts_.size() / 3));
        remap[v] = it->second;
        if (fresh) verts_.insert(verts_.end(), {verts[3 * v] == 0.0 ? 0.0 : verts[3 * v],
                                                verts[3 * v + 1] == 0.0 ? 0.0 : verts[3 * v + 1],
                                                verts[3 * v + 2] == 0.0 ? 0.0 : verts[3 * v + 2]});
    }
    faces_.reserve(faces.size());
    std::vector<int> raw;  // the source indices of each kept triangle
    raw.reserve(faces.size());
    for (size_t t = 0; t + 2 < faces.size(); t += 3) {
        const int a = faces[t], b = faces[t + 1], c = faces[t + 2];
        if (a < 0 || b < 0 || c < 0 || size_t(a) >= remap.size() || size_t(b) >= remap.size() ||
            size_t(c) >= remap.size())
            continue;
        const int ra = remap[size_t(a)], rb = remap[size_t(b)], rc = remap[size_t(c)];
        if (ra == rb || rb == rc || ra == rc) continue;
        faces_.insert(faces_.end(), {ra, rb, rc});
        raw.insert(raw.end(), {a, b, c});
    }
    build(raw);
}

// Whether a point is inside the triangles, by the parity of the crossings of
// a ray (a fixed direction off every axis; the winding is not read).
bool TriMesh::inside_by_parity(const P3& p) const {
    const P3 d{0.5773502691896258 + 1.3e-4, 0.5773502691896258 - 2.1e-4, 0.5773502691896258 + 0.7e-4};
    int crossings = 0;
    for (size_t t = 0; t < triangle_count(); ++t) {
        const P3 a = vertex(faces_[3 * t]), b = vertex(faces_[3 * t + 1]), c = vertex(faces_[3 * t + 2]);
        const P3 e1{b[0] - a[0], b[1] - a[1], b[2] - a[2]}, e2{c[0] - a[0], c[1] - a[1], c[2] - a[2]};
        const P3 h{d[1] * e2[2] - d[2] * e2[1], d[2] * e2[0] - d[0] * e2[2], d[0] * e2[1] - d[1] * e2[0]};
        const double det = e1[0] * h[0] + e1[1] * h[1] + e1[2] * h[2];
        if (std::abs(det) < 1e-300) continue;
        const P3 q{p[0] - a[0], p[1] - a[1], p[2] - a[2]};
        const double u = (q[0] * h[0] + q[1] * h[1] + q[2] * h[2]) / det;
        if (u < 0 || u > 1) continue;
        const P3 r{q[1] * e1[2] - q[2] * e1[1], q[2] * e1[0] - q[0] * e1[2], q[0] * e1[1] - q[1] * e1[0]};
        const double v = (d[0] * r[0] + d[1] * r[1] + d[2] * r[2]) / det;
        if (v < 0 || u + v > 1) continue;
        if ((e2[0] * r[0] + e2[1] * r[1] + e2[2] * r[2]) / det > 0) ++crossings;
    }
    return crossings % 2 == 1;
}

void TriMesh::build(const std::vector<int>& raw_faces) {
    const size_t n = triangle_count();

    // ---- Edges: the triangles using each undirected edge, with the direction
    // they run it in (+1: lo -> hi).
    struct Use {
        int tri;
        int dir;
    };
    std::unordered_map<uint64_t, std::vector<Use>> edges;
    edges.reserve(n * 2);
    for (size_t t = 0; t < n; ++t) {
        for (int k = 0; k < 3; ++k) {
            const int a = faces_[3 * t + size_t(k)], b = faces_[3 * t + size_t((k + 1) % 3)];
            edges[edge_key(a, b)].push_back({static_cast<int>(t), a < b ? 1 : -1});
        }
    }

    // ---- The triangle facing each use across its edge. Two uses: each other.
    // An even number above two (parts touching along an edge, welded):
    //  - first the uses that shared the edge in the source, by the same
    //    vertex indices before the weld: the topology the author gave (two
    //    boxes touching along an edge: each box keeps its own faces);
    //  - the others in angular order around the edge, paired with their
    //    neighbour (a triangle soup carries no topology). Two faces next to
    //    each other bound a wedge: inside a solid, or the empty space between
    //    two; the start of the pairing decides which, so this is the fallback
    //    only (paired across the empty wedge, two solids join into one sheet
    //    and one of them turns inside out).
    // An odd number: no pairing (a border).
    std::unordered_map<uint64_t, std::vector<int>> mates;
    mates.reserve(edges.size());
    for (const auto& [key, uses] : edges) {
        std::vector<int> mate(uses.size(), -1);
        if (uses.size() == 2) {
            mate = {1, 0};
        } else if (uses.size() > 2 && uses.size() % 2 == 0) {
            const int lo = int(key >> 32), hi = int(key & 0xffffffffu);
            if (!raw_faces.empty()) {
                // The source edge of each use: its two corners before the weld.
                auto raw_edge = [&](size_t t) {
                    int r[2], m = 0;
                    for (int k = 0; k < 3 && m < 2; ++k) {
                        const int v = faces_[3 * t + size_t(k)];
                        if (v == lo || v == hi) r[m++] = raw_faces[3 * t + size_t(k)];
                    }
                    return std::make_pair(std::min(r[0], r[1]), std::max(r[0], r[1]));
                };
                for (size_t i = 0; i < uses.size(); ++i) {
                    if (mate[i] >= 0) continue;
                    const auto ei = raw_edge(size_t(uses[i].tri));
                    size_t found = uses.size(), count = 0;
                    for (size_t j = 0; j < uses.size(); ++j)
                        if (j != i && raw_edge(size_t(uses[j].tri)) == ei) {
                            ++count;
                            if (mate[j] < 0) found = j;
                        }
                    if (count == 1 && found < uses.size()) {  // exactly one source partner
                        mate[i] = int(found);
                        mate[found] = int(i);
                    }
                }
            }
            std::vector<size_t> left;
            for (size_t i = 0; i < uses.size(); ++i)
                if (mate[i] < 0) left.push_back(i);
            const P3 a = vertex(lo), b = vertex(hi);
            P3 u{b[0] - a[0], b[1] - a[1], b[2] - a[2]};
            const double len = std::sqrt(u[0] * u[0] + u[1] * u[1] + u[2] * u[2]);
            if (len > 0 && left.size() >= 2 && left.size() % 2 == 0) {
                for (double& x : u) x /= len;
                // A frame (e1, e2) normal to the edge.
                P3 e1 = std::abs(u[0]) < 0.9 ? P3{1, 0, 0} : P3{0, 1, 0};
                const double d = e1[0] * u[0] + e1[1] * u[1] + e1[2] * u[2];
                e1 = {e1[0] - d * u[0], e1[1] - d * u[1], e1[2] - d * u[2]};
                const double l1 = std::sqrt(e1[0] * e1[0] + e1[1] * e1[1] + e1[2] * e1[2]);
                for (double& x : e1) x /= l1;
                const P3 e2{u[1] * e1[2] - u[2] * e1[1], u[2] * e1[0] - u[0] * e1[2], u[0] * e1[1] - u[1] * e1[0]};
                // (angle, tie, use): two coplanar faces on the same side of
                // the edge (two parts in a step) share an angle; the tie
                // puts first the one closing the wedge before it (its normal
                // pointing to the growing angle), then the one opening the
                // next: the source winding, read only for such a tie.
                struct Around {
                    double angle;
                    int tie;
                    int use;
                    bool operator<(const Around& o) const {
                        if (std::abs(angle - o.angle) > 1e-9) return angle < o.angle;
                        return tie < o.tie;
                    }
                };
                std::vector<Around> order;
                for (size_t i : left) {
                    const size_t t = size_t(uses[i].tri);
                    int third = faces_[3 * t];
                    for (int k = 0; k < 3; ++k) {
                        const int v = faces_[3 * t + size_t(k)];
                        if (v != lo && v != hi) third = v;
                    }
                    const P3 c = vertex(third);
                    const P3 w{c[0] - a[0], c[1] - a[1], c[2] - a[2]};
                    const double angle = std::atan2(w[0] * e2[0] + w[1] * e2[1] + w[2] * e2[2],
                                                    w[0] * e1[0] + w[1] * e1[1] + w[2] * e1[2]);
                    const P3 p0 = vertex(faces_[3 * t]), p1 = vertex(faces_[3 * t + 1]), p2 = vertex(faces_[3 * t + 2]);
                    const P3 x1{p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]}, x2{p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]};
                    const P3 nrm{x1[1] * x2[2] - x1[2] * x2[1], x1[2] * x2[0] - x1[0] * x2[2], x1[0] * x2[1] - x1[1] * x2[0]};
                    const P3 tangent{-std::sin(angle) * e1[0] + std::cos(angle) * e2[0],
                                     -std::sin(angle) * e1[1] + std::cos(angle) * e2[1],
                                     -std::sin(angle) * e1[2] + std::cos(angle) * e2[2]};
                    const double side = nrm[0] * tangent[0] + nrm[1] * tangent[1] + nrm[2] * tangent[2];
                    order.push_back({angle, side > 0 ? 0 : 1, int(i)});
                }
                std::sort(order.begin(), order.end());
                // Which wedges are matter: the one between the first two
                // faces is tested, a point just off the middle of the edge
                // on its bisector, inside the mesh by the parity of a ray
                // (no winding needed). Matter: pair (0, 1), (2, 3)...;
                // empty: (1, 2), (3, 4)... and the last with the first.
                const double phi = (order[0].angle + order[1].angle) / 2.0;
                const double step = 1e-3 * len;
                const P3 p{(a[0] + b[0]) / 2 + step * (std::cos(phi) * e1[0] + std::sin(phi) * e2[0]),
                           (a[1] + b[1]) / 2 + step * (std::cos(phi) * e1[1] + std::sin(phi) * e2[1]),
                           (a[2] + b[2]) / 2 + step * (std::cos(phi) * e1[2] + std::sin(phi) * e2[2])};
                const size_t start = inside_by_parity(p) ? 0 : 1;
                const size_t m = order.size();
                for (size_t i = 0; i < m; i += 2) {
                    const int x = order[(start + i) % m].use, y = order[(start + i + 1) % m].use;
                    mate[size_t(x)] = y;
                    mate[size_t(y)] = x;
                }
            }
        }
        mates.emplace(key, std::move(mate));
    }

    // ---- Consistent winding, component by component (breadth first over the
    // paired uses).
    std::vector<int> component(n, -1);
    std::vector<char> flipped(n, 0);
    auto flip = [&](size_t t) { std::swap(faces_[3 * t + 1], faces_[3 * t + 2]); };
    auto direction = [&](size_t t, int a, int b) {  // +1 when t runs a -> b
        for (int k = 0; k < 3; ++k) {
            if (faces_[3 * t + size_t(k)] == a && faces_[3 * t + size_t((k + 1) % 3)] == b) return 1;
        }
        return -1;
    };
    components_ = 0;
    for (size_t seed = 0; seed < n; ++seed) {
        if (component[seed] >= 0) continue;
        const int id = components_++;
        std::deque<size_t> queue{seed};
        component[seed] = id;
        while (!queue.empty()) {
            const size_t t = queue.front();
            queue.pop_front();
            for (int k = 0; k < 3; ++k) {
                const int a = faces_[3 * t + size_t(k)], b = faces_[3 * t + size_t((k + 1) % 3)];
                const uint64_t key = edge_key(a, b);
                const auto& uses = edges[key];
                const auto& mate = mates[key];
                int partner = -1;
                for (size_t i = 0; i < uses.size(); ++i) {
                    if (size_t(uses[i].tri) == t && mate[i] >= 0) partner = uses[size_t(mate[i])].tri;
                }
                if (partner < 0) continue;  // border: no propagation
                const size_t u = size_t(partner);
                if (component[u] >= 0) continue;
                component[u] = id;
                // Consistent: u runs the shared edge b -> a.
                if (direction(u, a, b) == 1) flip(u);
                queue.push_back(u);
            }
        }
    }

    // ---- Outwards. A closed component: positive signed volume about its own
    // centroid (exact). An open one (a patch cut off by non-manifold edges, or
    // a surface): positive signed volume about the centroid of the whole
    // element, i.e. its faces turned away from the element.
    auto tetra = [](const P3& o, const P3& a, const P3& b, const P3& c) {
        const double ax = a[0] - o[0], ay = a[1] - o[1], az = a[2] - o[2];
        const double bx = b[0] - o[0], by = b[1] - o[1], bz = b[2] - o[2];
        const double cx = c[0] - o[0], cy = c[1] - o[1], cz = c[2] - o[2];
        return (ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)) / 6.0;
    };
    const size_t nc = size_t(components_);
    std::vector<char> component_closed(nc, 1);
    for (const auto& [key, uses] : edges) {
        const auto& mate = mates[key];
        for (size_t i = 0; i < uses.size(); ++i) {
            if (mate[i] < 0) component_closed[size_t(component[size_t(uses[i].tri)])] = 0;
        }
    }
    std::vector<P3> centre(nc, P3{0, 0, 0});
    std::vector<double> count(nc, 0.0), signed_volume(nc, 0.0);
    P3 global{0, 0, 0};
    double global_count = 0.0;
    for (size_t t = 0; t < n; ++t) {
        for (int k = 0; k < 3; ++k) {
            const P3 p = vertex(faces_[3 * t + size_t(k)]);
            for (int d = 0; d < 3; ++d) {
                centre[size_t(component[t])][d] += p[d];
                global[d] += p[d];
            }
        }
        count[size_t(component[t])] += 3;
        global_count += 3;
    }
    for (int d = 0; d < 3; ++d) global[d] /= std::max(1.0, global_count);
    for (size_t c = 0; c < nc; ++c) {
        if (!component_closed[c]) {
            centre[c] = global;
            continue;
        }
        for (int d = 0; d < 3; ++d) centre[c][d] /= std::max(1.0, count[c]);
    }
    for (size_t t = 0; t < n; ++t) {
        P3 a, b, c;
        corners(t, a, b, c);
        signed_volume[size_t(component[t])] += tetra(centre[size_t(component[t])], a, b, c);
    }
    for (size_t t = 0; t < n; ++t) {
        if (signed_volume[size_t(component[t])] < 0) flip(t);
    }
    // The volume: the closed components exactly; with open ones, the signed
    // volume of the whole repaired mesh about the element centroid
    // (indicative).
    volume_ = 0.0;
    bool all_closed = true;
    for (size_t c = 0; c < nc; ++c) all_closed = all_closed && component_closed[c];
    if (all_closed) {
        for (size_t c = 0; c < nc; ++c) volume_ += std::abs(signed_volume[c]);
    } else {
        for (size_t t = 0; t < n; ++t) {
            P3 a, b, c;
            corners(t, a, b, c);
            volume_ += tetra(global, a, b, c);
        }
        volume_ = std::abs(volume_);
    }

    // ---- Closed: every use of every edge paired with a use running it in
    // the opposite direction.
    closed_ = n > 0;
    for (const auto& [key, uses] : edges) {
        const auto& mate = mates[key];
        const int lo = int(key >> 32), hi = int(key & 0xffffffffu);
        for (size_t i = 0; i < uses.size() && closed_; ++i) {
            if (mate[i] < 0 || direction(size_t(uses[i].tri), lo, hi) ==
                                   direction(size_t(uses[size_t(mate[i])].tri), lo, hi))
                closed_ = false;
        }
        if (!closed_) break;
    }

    // ---- Per-triangle data
    normals_.resize(n);
    areas_.resize(n);
    boxes_.resize(n);
    total_area_ = 0.0;
    bounds_.SetVoid();
    for (size_t t = 0; t < n; ++t) {
        P3 a, b, c;
        corners(t, a, b, c);
        const double ux = b[0] - a[0], uy = b[1] - a[1], uz = b[2] - a[2];
        const double vx = c[0] - a[0], vy = c[1] - a[1], vz = c[2] - a[2];
        P3 nn{uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx};
        const double len = std::sqrt(nn[0] * nn[0] + nn[1] * nn[1] + nn[2] * nn[2]);
        areas_[t] = 0.5 * len;
        total_area_ += areas_[t];
        normals_[t] = len > 0 ? P3{nn[0] / len, nn[1] / len, nn[2] / len} : P3{0, 0, 0};
        for (const P3* p : {&a, &b, &c}) boxes_[t].Add(gp_Pnt((*p)[0], (*p)[1], (*p)[2]));
        bounds_.Add(boxes_[t]);
    }
}

const BoxTree& TriMesh::tree() const {
    std::call_once(tree_once_, [this]() { tree_ = std::make_unique<BoxTree>(boxes_); });
    return *tree_;
}

}  // namespace ifcclash::triang
