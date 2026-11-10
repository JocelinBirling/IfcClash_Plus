// The context rules of Rules.py: Ray_Check and DirectView (pairs + context)
// and FreeSpace (elements + context). The context is given once to the rule
// (setup_context), which builds its read-only index of it.
#include "AllRules.h"
#include "ContextRules.h"

#include "../geometry/Faces.h"
#include "../geometry/Geos.h"
#include "../geometry/Numpy.h"
#include "../sources/IfcRayTree.h"

#include <BRepAlgoAPI_Common.hxx>
#include <BRepBndLib.hxx>
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <BRepPrimAPI_MakeBox.hxx>
#include <BRep_Tool.hxx>
#include <Poly_Triangulation.hxx>
#include <TopExp_Explorer.hxx>
#include <TopLoc_Location.hxx>
#include <TopoDS.hxx>

#include <algorithm>
#include <cmath>
#include <limits>

namespace ifcclash {

namespace {

namespace np = geometry::np;
using V3 = std::array<double, 3>;

// The bounds center of the world triangulation (Ray_Check._get_elements_centers)
std::optional<V3> mesh_center(const Mesh& m) {
    if (m.local_verts.empty()) return std::nullopt;
    V3 lo{1e300, 1e300, 1e300}, hi{-1e300, -1e300, -1e300};
    for (size_t i = 0; i + 2 < m.local_verts.size(); i += 3)
        for (int k = 0; k < 3; ++k) {
            lo[k] = std::min(lo[k], m.local_verts[i + k]);
            hi[k] = std::max(hi[k], m.local_verts[i + k]);
        }
    return V3{(lo[0] + hi[0]) / 2.0, (lo[1] + hi[1]) / 2.0, (lo[2] + hi[2]) / 2.0};
}

// Does the segment cross the box (slab test)? A conservative prefilter of
// the exact OCC test.
bool segment_hits_box(const V3& a, const V3& b, const Bnd_Box& box) {
    if (box.IsVoid()) return false;
    double lo[3], hi[3];
    box.Get(lo[0], lo[1], lo[2], hi[0], hi[1], hi[2]);
    double t0 = 0.0, t1 = 1.0;
    for (int k = 0; k < 3; ++k) {
        const double d = b[k] - a[k];
        if (std::abs(d) < 1e-15) {
            if (a[k] < lo[k] || a[k] > hi[k]) return false;
            continue;
        }
        double ta = (lo[k] - a[k]) / d, tb = (hi[k] - a[k]) / d;
        if (ta > tb) std::swap(ta, tb);
        t0 = std::max(t0, ta);
        t1 = std::min(t1, tb);
        if (t0 > t1) return false;
    }
    return true;
}

// clash_utils.segment_hits_shape
bool segment_hits_shape(const V3& a, const V3& b, const TopoDS_Shape& shape, double tolerance = 1e-7) {
    const TopoDS_Shape edge = BRepBuilderAPI_MakeEdge(gp_Pnt(a[0], a[1], a[2]), gp_Pnt(b[0], b[1], b[2])).Edge();
    return geometry::shape_distance(edge, shape) <= tolerance;
}

// ================================================================ Ray_Check

struct RayCheckParams {
    double max_ray_length = 1.0;
};

struct Obstacle {
    ElementKey key;
    TopoDS_Shape shape;
    Bnd_Box box;
};

class RayCheck final : public PairRule<RayCheckParams> {
public:
    Variant base_variant() const override { return Variant::MeshWorld; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    bool needs_element_data() const override { return true; }
    bool uses_context() const override { return true; }

    void setup_context(const std::vector<ElementKey>& context, GeometryProvider& provider) override {
        provider.prepare_meshes(context, Variant::BrepWorld);
        for (const auto& key : context) {
            auto shape = provider.brep(key);
            if (!shape) continue;
            Obstacle o{key, *shape, {}};
            BRepBndLib::AddOptimal(o.shape, o.box, false, false);
            o.box = geometry::inflate(o.box, 0.01);
            obstacles_.push_back(std::move(o));
        }
    }

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role) const override {
        const auto mesh = e.mesh(Variant::MeshWorld);
        if (!mesh) return nullptr;
        auto c = mesh_center(*mesh);
        return c ? std::make_shared<V3>(*c) : nullptr;
    }

    // Two centers within max_ray_length overlap as cubes of half that length.
    Bnd_Box broad_volume(const ElementGeometry& e, Role) const override {
        const V3& c = e.as<V3>();
        const double h = params().max_ray_length / 2.0 + 1e-9;
        Bnd_Box b;
        b.Update(c[0] - h, c[1] - h, c[2] - h, c[0] + h, c[1] + h, c[2] + h);
        return b;
    }

    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override {
        const V3& a = s.as<V3>();
        const V3& b = t.as<V3>();
        const double distance = np::norm(np::sub(b, a));
        Verdict v;
        if (distance == 0 || distance > params().max_ray_length) return v;
        for (const auto& o : obstacles_) {
            if (o.key == s.key || o.key == t.key) continue;
            if (!segment_hits_box(a, b, o.box)) continue;
            if (segment_hits_shape(a, b, o.shape)) return v;  // blocked
        }
        v.status = true;
        v.measures.set(Measure::Distance, distance);
        v.points.push_back({a, b, std::string("ray")});
        return v;
    }

private:
    std::vector<Obstacle> obstacles_;
};

// ================================================================ DirectView



constexpr double kR2Alpha = 0.7548776662466927;
constexpr double kR2Beta = 0.5698402909980532;

std::pair<double, double> r2_sequence(long index) {
    return {std::fmod((index + 1) * kR2Alpha, 1.0), std::fmod((index + 1) * kR2Beta, 1.0)};
}

V3 sample_point_in_triangle(const Triangle3& t, long index) {
    auto [u, v] = r2_sequence(index);
    if (u + v > 1.0) {
        u = 1.0 - u;
        v = 1.0 - v;
    }
    const double w = 1.0 - u - v;
    return {w * t[0][0] + u * t[1][0] + v * t[2][0], w * t[0][1] + u * t[1][1] + v * t[2][1],
            w * t[0][2] + u * t[1][2] + v * t[2][2]};
}

// numpy pairwise_sum (np.sum of a contiguous float64 array)
double pairwise_sum(const double* a, size_t n) {
    if (n < 8) {
        double res = 0.0;
        for (size_t i = 0; i < n; ++i) res += a[i];
        return res;
    }
    if (n <= 128) {
        double r[8];
        for (int k = 0; k < 8; ++k) r[k] = a[k];
        size_t i = 8;
        for (; i < n - (n % 8); i += 8)
            for (int k = 0; k < 8; ++k) r[k] += a[i + k];
        double res = ((r[0] + r[1]) + (r[2] + r[3])) + ((r[4] + r[5]) + (r[6] + r[7]));
        for (; i < n; ++i) res += a[i];
        return res;
    }
    size_t n2 = n / 2;
    n2 -= n2 % 8;
    return pairwise_sum(a, n2) + pairwise_sum(a + n2, n - n2);
}

// clash_utils.plan_ray_counts
std::vector<int> plan_ray_counts(const std::vector<double>& areas, int ray_count) {
    std::vector<int> counts(areas.size(), 0);
    if (ray_count <= 0 || areas.empty()) return counts;
    double total = 0.0;
    for (double a : areas) total += a;
    const int n = static_cast<int>(areas.size());
    if (total <= 0.0) {
        const int base = ray_count / n;
        std::fill(counts.begin(), counts.end(), base);
        for (int i = 0; i < ray_count - base * n; ++i) counts[i] += 1;
        return counts;
    }
    std::vector<double> rem(areas.size());
    int sum = 0;
    for (int i = 0; i < n; ++i) {
        const double share = ray_count * areas[i] / total;
        counts[i] = static_cast<int>(std::floor(share));
        rem[i] = share - counts[i];
        sum += counts[i];
    }
    std::vector<int> order(n);
    for (int i = 0; i < n; ++i) order[i] = i;
    std::sort(order.begin(), order.end(), [&](int a, int b) { return rem[a] != rem[b] ? rem[a] > rem[b] : a < b; });
    for (int i = 0; i < ray_count - sum; ++i) counts[order[i % n]] += 1;
    return counts;
}

}  // namespace

void DirectView::setup() {
    const auto& p = params();
    if (p.ray_source != "Both" && p.ray_source != "Source" && p.ray_source != "Target")
        throw ConfigError("ray_source must be 'Both', 'Source' or 'Target'");
    if (p.ray_count < 1) throw ConfigError("ray_count must be an integer >= 1");
    if (!(0.0 <= p.threshold && p.threshold <= 100.0)) throw ConfigError("threshold must be between 0% and 100%");
    if (p.max_distance && *p.max_distance <= 0) throw ConfigError("max_distance must be None or a positive number");
}


void DirectView::setup_context(const std::vector<ElementKey>& context, GeometryProvider& provider) {
    auto* service = provider.ray_trees();
    if (!service) throw ConfigError("DirectView needs the IFC source (IfcOpenShell ray tree)");
    tree_ = service->build_ray_tree(context);
}


std::shared_ptr<const void> DirectView::element_data(const ElementGeometry& e, Role) const {
    const auto mesh = e.mesh(Variant::MeshWorld);
    if (!mesh || mesh->faces.empty()) return nullptr;
    auto data = std::make_shared<ViewMesh>();
    const auto& v = mesh->local_verts;
    for (size_t t = 0; t + 2 < mesh->faces.size(); t += 3) {
        Triangle3 tr;
        for (int k = 0; k < 3; ++k) {
            const size_t i = 3 * static_cast<size_t>(mesh->faces[t + k]);
            tr[k] = {v[i], v[i + 1], v[i + 2]};
            data->box.Add(gp_Pnt(v[i], v[i + 1], v[i + 2]));
        }
        data->triangles.push_back(tr);
    }
    V3 sum{0, 0, 0};
    const size_t n = v.size() / 3;
    for (size_t i = 0; i < n; ++i)
        for (int k = 0; k < 3; ++k) sum[k] += v[3 * i + k];
    data->centroid = {sum[0] / n, sum[1] / n, sum[2] / n};
    return data;
}


Bnd_Box DirectView::broad_volume(const ElementGeometry& e, Role role) const {
    const double reach = role == Role::Source ? params().max_distance.value_or(0.0) : 0.0;
    return geometry::inflate(e.as<ViewMesh>().box, reach + 1e-6);
}


Verdict DirectView::narrow_test(const ElementGeometry& s, const ElementGeometry& t) const {
    const auto& sm = s.as<ViewMesh>();
    const auto& tm = t.as<ViewMesh>();
    std::vector<std::pair<const ViewMesh*, const ViewMesh*>> emitters;
    if (params().ray_source == "Both") emitters = {{&sm, &tm}, {&tm, &sm}};
    else if (params().ray_source == "Source") emitters = {{&sm, &tm}};
    else emitters = {{&tm, &sm}};
    const int planned = params().ray_count * static_cast<int>(emitters.size());
    const double threshold = params().threshold / 100.0;
    int hits = 0, casts = 0;
    RaycastBlock block;
    bool decided = false;
    for (const auto& [emitter, receiver] : emitters) {
        if (decided) break;
        for (const auto& [origin, aim] : pair_rays(*emitter, *receiver)) {
            // clash_utils.direct_view_early_stop
            const int remaining = planned - casts;
            if (static_cast<double>(hits + remaining) / planned < threshold ||
                static_cast<double>(hits) / planned >= threshold) {
                decided = true;
                break;
            }
            const bool touched = cast_ray(origin, aim);
            casts += 1;
            if (touched) {
                hits += 1;
                block.hit_segments.emplace_back(origin, aim);
            } else {
                block.blocked_segments.emplace_back(origin, aim);
            }
        }
    }
    const double ratio = casts > 0 ? static_cast<double>(hits) / casts : 0.0;
    Verdict v;
    if (!(ratio >= threshold)) return v;
    v.status = true;
    v.measures.set(Measure::HitRatio, ratio);
    block.planned = planned;
    block.cast = casts;
    block.hit = hits;
    v.raycast = std::move(block);
    return v;
}


// DirectView._faces_toward
std::vector<Triangle3> DirectView::faces_toward(const ViewMesh& mesh, const V3& other) {
    std::vector<Triangle3> out;
    for (const auto& t : mesh.triangles) {
        const V3 n = np::cross(np::sub(t[1], t[0]), np::sub(t[2], t[0]));
        const double m = np::row_norm(n);
        if (!(m > 1e-12)) continue;
        const V3 u{n[0] / m, n[1] / m, n[2] / m};
        const V3 center{(t[0][0] + t[1][0] + t[2][0]) / 3.0, (t[0][1] + t[1][1] + t[2][1]) / 3.0,
                        (t[0][2] + t[1][2] + t[2][2]) / 3.0};
        if (np::einsum_rowdot(u, np::sub(other, center)) > 0.0) out.push_back(t);
    }
    return out;
}


std::vector<double> DirectView::areas_of(const std::vector<Triangle3>& faces) {
    std::vector<double> out;
    for (const auto& t : faces) out.push_back(0.5 * np::row_norm(np::cross(np::sub(t[1], t[0]), np::sub(t[2], t[0]))));
    return out;
}


// DirectView._pair_rays
std::vector<std::pair<DirectView::V3, DirectView::V3>> DirectView::pair_rays(const ViewMesh& emitter, const ViewMesh& receiver) const {
    std::vector<std::pair<V3, V3>> rays;
    const auto ef = faces_toward(emitter, receiver.centroid);
    const auto rf = faces_toward(receiver, emitter.centroid);
    if (ef.empty() || rf.empty()) return rays;
    const auto counts = plan_ray_counts(areas_of(ef), params().ray_count);
    const auto ra = areas_of(rf);
    const double total = pairwise_sum(ra.data(), ra.size());
    long index = 0;
    for (size_t f = 0; f < ef.size(); ++f) {
        for (int c = 0; c < counts[f]; ++c) {
            const V3 origin = sample_point_in_triangle(ef[f], index);
            const double u = r2_sequence(index).first * total;
            double cumulative = 0.0;
            const Triangle3* receiving = &rf.back();
            for (size_t k = 0; k < rf.size(); ++k) {
                cumulative += ra[k];
                if (u <= cumulative) {
                    receiving = &rf[k];
                    break;
                }
            }
            const V3 aim = sample_point_in_triangle(*receiving, index + 1000007);
            index += 1;
            rays.emplace_back(origin, aim);
        }
    }
    return rays;
}


// DirectView._cast_ray
bool DirectView::cast_ray(const V3& origin, const V3& aim) const {
    const V3 vec = np::sub(aim, origin);
    const double length = np::norm(vec);
    if (length < 1e-9) return true;
    if (params().max_distance && length > *params().max_distance) return false;
    const V3 dir{vec[0] / length, vec[1] / length, vec[2] / length};
    return !blocked(origin, dir, length);
}

bool DirectView::blocked(const V3& origin, const V3& dir, double length) const {
    return tree_->hits(origin, dir, length) != 0;
}

namespace {

// ================================================================ FreeSpace

struct FreeSpaceParams {
    double diameter = 1.5;
    std::optional<double> height = 2.0;
};

struct ObstacleSlab {
    TopoDS_Shape shape;
    double bounds[4];  // x_min, y_min, x_max, y_max
    double z_min, z_max;
};

constexpr double kMeshFraction = 25.0;
constexpr double kTouchEpsilon = 1e-9;

class FreeSpace final : public ElementRule<FreeSpaceParams> {
public:
    Level narrow_level() const override { return Level::Mesh; }
    // Every source is checked, even without geometry (it is then flagged).
    Variant base_variant() const override { return Variant::MeshWorld; }
    std::vector<Variant> narrow_variants() const override { return {Variant::MeshWorld}; }
    bool uses_context() const override { return true; }

    void setup() override {
        if (params().diameter <= 0) throw ConfigError("diameter must be a positive number (m)");
        if (!params().height || *params().height <= 0) throw ConfigError("height is mandatory (m)");
    }

    void setup_context(const std::vector<ElementKey>& context, GeometryProvider& provider) override {
        provider.prepare_meshes(context, Variant::BrepWorld);
        for (const auto& key : context) {
            auto shape = provider.brep(key);
            if (!shape) continue;
            ObstacleSlab o;
            o.shape = *shape;
            Bnd_Box box;
            BRepBndLib::Add(o.shape, box);
            double x0, y0, z0, x1, y1, z1;
            box.Get(x0, y0, z0, x1, y1, z1);
            o.bounds[0] = x0;
            o.bounds[1] = y0;
            o.bounds[2] = x1;
            o.bounds[3] = y1;
            o.z_min = z0;
            o.z_max = z1;
            obstacles_.push_back(std::move(o));
        }
    }

    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict flagged;
        flagged.status = true;  // no free placement: a result without measure
        geometry::Geos geos;
        const auto mesh = e.mesh(Variant::MeshWorld);
        if (!mesh || mesh->faces.empty()) return flagged;
        double z_base = 0.0;
        auto footprint = lowest_footprint(*mesh, geos, z_base);
        if (geos.is_empty(footprint)) return flagged;
        return placement_found(footprint, z_base, geos) ? Verdict{} : flagged;
    }

private:
    // clash_utils.lowest_footprint
    static geometry::Geos::Geom lowest_footprint(const Mesh& mesh, const geometry::Geos& geos, double& z_min) {
        const auto& v = mesh.local_verts;
        z_min = std::numeric_limits<double>::infinity();
        for (size_t i = 2; i < v.size(); i += 3) z_min = std::min(z_min, v[i]);
        std::vector<Triangle3> triangles;
        std::vector<double> cz;
        for (size_t t = 0; t + 2 < mesh.faces.size(); t += 3) {
            Triangle3 tr;
            for (int k = 0; k < 3; ++k) {
                const size_t i = 3 * static_cast<size_t>(mesh.faces[t + k]);
                tr[k] = {v[i], v[i + 1], v[i + 2]};
            }
            triangles.push_back(tr);
            cz.push_back((tr[0][2] + tr[1][2] + tr[2][2]) / 3.0);
        }
        std::vector<size_t> lowest;
        for (size_t t = 0; t < triangles.size(); ++t)
            if (cz[t] <= z_min + 0.001) lowest.push_back(t);
        if (lowest.empty()) {
            std::vector<size_t> order(triangles.size());
            for (size_t i = 0; i < order.size(); ++i) order[i] = i;
            std::stable_sort(order.begin(), order.end(), [&](size_t a, size_t b) { return cz[a] < cz[b]; });
            for (size_t i = 0; i < std::min<size_t>(2, order.size()); ++i) lowest.push_back(order[i]);
        }
        std::vector<geometry::Geos::Geom> polygons;
        for (size_t t : lowest) {
            const auto& tr = triangles[t];
            auto poly = geos.polygon({{tr[0][0], tr[0][1], 0}, {tr[1][0], tr[1][1], 0}, {tr[2][0], tr[2][1], 0}}, 2);
            if (!geos.is_empty(poly)) polygons.push_back(std::move(poly));
        }
        if (polygons.empty()) return geometry::Geos::Geom(nullptr, geometry::Geos::Deleter{geos.context()});
        return geos.union_all(polygons);
    }

    // FreeSpace._obstacle_slab_footprint
    geometry::Geos::Geom slab_footprint(const ObstacleSlab& o, const double box[4], double z_base,
                                        const geometry::Geos& geos) const {
        geometry::Geos::Geom none(nullptr, geometry::Geos::Deleter{geos.context()});
        const double z_low = z_base + kTouchEpsilon;
        const double z_high = z_base + *params().height - kTouchEpsilon;
        if (z_high <= z_low) return none;
        const TopoDS_Shape slab = BRepPrimAPI_MakeBox(gp_Pnt(box[0], box[1], z_low), gp_Pnt(box[2], box[3], z_high)).Shape();
        BRepAlgoAPI_Common common(o.shape, slab);
        common.Build();
        if (!common.IsDone()) return none;
        const TopoDS_Shape clipped = common.Shape();
        if (clipped.IsNull()) return none;
        const double deflection = (params().diameter / 2.0) / kMeshFraction;
        BRepMesh_IncrementalMesh(clipped, deflection).Perform();
        std::vector<geometry::Geos::Geom> triangles;
        for (TopExp_Explorer ex(clipped, TopAbs_FACE); ex.More(); ex.Next()) {
            TopLoc_Location location;
            const Handle(Poly_Triangulation) tri = BRep_Tool::Triangulation(TopoDS::Face(ex.Current()), location);
            if (tri.IsNull()) continue;
            const gp_Trsf trsf = location.Transformation();
            for (int i = 1; i <= tri->NbTriangles(); ++i) {
                int n[3];
                tri->Triangle(i).Get(n[0], n[1], n[2]);
                std::vector<std::array<double, 3>> pts;
                for (int k = 0; k < 3; ++k) {
                    const gp_Pnt p = tri->Node(n[k]).Transformed(trsf);
                    pts.push_back({p.X(), p.Y(), 0.0});
                }
                auto poly = geos.polygon(pts, 2);
                if (!geos.is_empty(poly)) triangles.push_back(std::move(poly));
            }
        }
        if (triangles.empty()) return none;
        return geos.union_all(triangles);
    }

    // FreeSpace._search_placement, the verdict part: is there a center left?
    bool placement_found(const geometry::Geos::Geom& footprint, double z_base, const geometry::Geos& geos) const {
        const double radius = params().diameter / 2.0;
        auto center_region = geos.buffer(footprint, -radius);
        if (geos.is_empty(center_region)) return false;
        const auto b = geos.bounds(footprint);
        const double pad = radius + 0.1;
        const double box[4] = {b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad};
        const double z_top = z_base + *params().height;
        for (const auto& o : obstacles_) {
            if (o.bounds[2] < box[0] || o.bounds[0] > box[2] || o.bounds[3] < box[1] || o.bounds[1] > box[3]) continue;
            if (o.z_max < z_base + kTouchEpsilon || o.z_min > z_top - kTouchEpsilon) continue;
            auto projection = slab_footprint(o, box, z_base, geos);
            if (geos.is_empty(projection)) continue;
            auto blocked = geos.buffer(projection, radius - kTouchEpsilon);
            center_region = geos.difference(center_region, blocked);
            if (geos.is_empty(center_region)) return false;
        }
        return true;
    }

    std::vector<ObstacleSlab> obstacles_;
};

}  // namespace

RuleSpec spec_ray_check() {
    return RuleSpec::pair<RayCheck>(
        "Ray_Check", "Ray Check", {Slot::Source, Slot::Target, Slot::Context},
        "Flags the source/target pairs whose center-to-center ray is free of context elements.",
        {param(&RayCheckParams::max_ray_length, "max_ray_length").doc("Maximum ray length").unit(Unit::Metre)});
}

RuleSpec spec_direct_view() {
    return RuleSpec::pair<DirectView>(
        "DirectView", "Direct View", {Slot::Source, Slot::Target, Slot::Context},
        "Flags the pairs that see each other (hit ratio of the rays at least the threshold).",
        {param(&DirectViewParams::ray_source, "ray_source").doc("Where the rays start").values({"Source", "Target", "Both"}),
         param(&DirectViewParams::ray_count, "ray_count").doc("Number of rays per pair"),
         param(&DirectViewParams::threshold, "threshold").doc("Visibility threshold (%)"),
         param(&DirectViewParams::max_distance, "max_distance").doc("Maximum distance").unit(Unit::Metre)});
}

RuleSpec spec_free_space() {
    return RuleSpec::element<FreeSpace>(
        "FreeSpace", "Free Space", {Slot::Source, Slot::Context},
        "Flags the sources where no free cylinder (diameter x height) fits among the context elements.",
        {param(&FreeSpaceParams::diameter, "diameter").doc("Free space diameter").unit(Unit::Metre),
         param(&FreeSpaceParams::height, "height").doc("Free space height").unit(Unit::Metre)});
}

}  // namespace ifcclash
