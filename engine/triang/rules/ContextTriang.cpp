// IfcClash_Plus engine — the _triang context rules (engine/triang/rules):
// Ray_Check, DirectView, FreeSpace.
//
// The context is one triangle BVH of all the context elements
// (TriangleSoup), built once per run; a ray is a segment tested against it
// (Moller-Trumbore with slack), instead of an OCCT distance between an edge
// and each obstacle B-Rep (Ray_Check) or the IfcOpenShell ray tree on the
// B-Reps (DirectView).
//  - Ray_Check_triang: the original rule, centers from the box of the
//    triangles; obstacles = the context elements other than the pair.
//  - DirectView_triang: the original rule (rules/ContextRules.h), its rays
//    drawn on the repaired triangles (TriMesh: outward winding, so the
//    "faces toward the other object" do not depend on the IFC winding).
//  - FreeSpace_triang: the original search of a free cylinder, the obstacle
//    footprints from the triangles: each obstacle triangle clipped to the
//    height band (clip_triangle_z), projected, plus the sections of the
//    obstacle at the band limits (section_loops: a wall crossing the band
//    has vertical faces only, its footprint comes from its sections).
#include "Common.h"

#include "../../registry/RuleSpec.h"
#include "../../rules/ContextRules.h"
#include "../../geometry/Geos.h"
#include "../kernels/Slices.h"
#include "../spatial/Proximity.h"

#include <cmath>
#include <limits>
#include <unordered_map>

namespace ifcclash {

namespace {

using namespace triang;

// The context: one triangle BVH, owners numbered in context order.
struct Context {
    TriangleSoup soup;
    std::unordered_map<ElementKey, int, ElementKeyHash> owner;

    void build(const std::vector<ElementKey>& keys, GeometryProvider& provider) {
        provider.prepare_meshes(keys, Variant::Triangles);
        const ElementBoxes none;
        for (const auto& key : keys) {
            if (owner.count(key)) continue;
            const ElementGeometry g(key, none, provider);
            const auto mesh = tri_mesh(g);
            if (!mesh) continue;
            const int id = static_cast<int>(owner.size());
            owner.emplace(key, id);
            soup.add(id, *mesh);
        }
        soup.build();
    }
    int id_of(const ElementKey& key) const {
        auto it = owner.find(key);
        return it == owner.end() ? -1 : it->second;
    }
};

// ================================================================ Ray_Check_triang

struct RayCheckParams {
    double max_ray_length = 1.0;
};

class RayCheckTriang final : public TriPairRule<RayCheckParams> {
public:
    bool uses_context() const override { return true; }

    void setup_context(const std::vector<ElementKey>& context, GeometryProvider& provider) override {
        context_.build(context, provider);
    }

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role) const override {
        const auto c = box_center(e);
        return c ? std::make_shared<const Point3>(*c) : nullptr;
    }

    // Two centers within max_ray_length overlap as cubes of half that length.
    Bnd_Box broad_volume(const ElementGeometry& e, Role) const override {
        const Point3& c = e.as<Point3>();
        const double h = params().max_ray_length / 2.0 + 1e-9;
        Bnd_Box b;
        b.Update(c[0] - h, c[1] - h, c[2] - h, c[0] + h, c[1] + h, c[2] + h);
        return b;
    }

    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override {
        const Point3& a = s.as<Point3>();
        const Point3& b = t.as<Point3>();
        const double distance = std::sqrt((b[0] - a[0]) * (b[0] - a[0]) + (b[1] - a[1]) * (b[1] - a[1]) +
                                          (b[2] - a[2]) * (b[2] - a[2]));
        Verdict v;
        if (distance == 0 || distance > params().max_ray_length) return v;
        const int ids = context_.id_of(s.key), idt = context_.id_of(t.key);
        // The original: an obstacle within 1e-7 of the segment blocks it.
        if (context_.soup.segment_blocked(a, b, 1e-7, 0.0, [&](int owner) { return owner != ids && owner != idt; }))
            return v;
        v.status = true;
        v.measures.set(Measure::Distance, distance);
        v.points.push_back({a, b, std::string("ray")});
        return v;
    }

private:
    Context context_;
};

// ================================================================ DirectView_triang

class DirectViewTriang final : public DirectView {
public:
    Level narrow_level() const override { return Level::Mesh; }
    Variant base_variant() const override { return Variant::Triangles; }
    bool parallel_safe() const override { return true; }    // element_data: triangles only
    bool parallel_narrow() const override { return true; }  // narrow_test: element data and the context

    void setup_context(const std::vector<ElementKey>& context, GeometryProvider& provider) override {
        context_.build(context, provider);
    }

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role) const override {
        const auto mesh = tri_mesh(e);
        if (!mesh) return nullptr;
        auto data = std::make_shared<ViewMesh>();
        data->triangles.reserve(mesh->triangle_count());
        for (size_t t = 0; t < mesh->triangle_count(); ++t) {
            P3 a, b, c;
            mesh->corners(t, a, b, c);
            data->triangles.push_back({point(a), point(b), point(c)});
        }
        data->box = mesh->bounds();
        V3 sum{0, 0, 0};
        const size_t n = mesh->vertex_count();
        for (size_t i = 0; i < n; ++i)
            for (int k = 0; k < 3; ++k) sum[size_t(k)] += mesh->verts()[3 * i + size_t(k)];
        data->centroid = {sum[0] / double(n), sum[1] / double(n), sum[2] / double(n)};
        return data;
    }

protected:
    // Any context triangle on the ray (the ends lie on the surfaces of the
    // pair: hits within 1e-6 m of them are ignored).
    bool blocked(const V3& origin, const V3& dir, double length) const override {
        const P3 end{origin[0] + dir[0] * length, origin[1] + dir[1] * length, origin[2] + dir[2] * length};
        return context_.soup.segment_blocked(origin, end, 1e-9, 1e-6, [](int) { return true; });
    }

private:
    Context context_;
};

// ================================================================ FreeSpace_triang

struct FreeSpaceParams {
    double diameter = 1.5;
    std::optional<double> height = 2.0;
};

constexpr double kTouchEpsilon = 1e-9;

class FreeSpaceTriang final : public TriElementRule<FreeSpaceParams> {
public:
    bool uses_context() const override { return true; }

    void setup() override {
        if (params().diameter <= 0) throw ConfigError("diameter must be a positive number (m)");
        if (!params().height || *params().height <= 0) throw ConfigError("height is mandatory (m)");
    }

    void setup_context(const std::vector<ElementKey>& context, GeometryProvider& provider) override {
        provider.prepare_meshes(context, Variant::Triangles);
        const ElementBoxes none;
        for (const auto& key : context) {
            const ElementGeometry g(key, none, provider);
            if (auto mesh = tri_mesh(g)) obstacles_.push_back(std::move(mesh));
        }
    }

    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict flagged;
        flagged.status = true;  // no free placement: a result without measure
        geometry::Geos geos;
        const auto mesh = tri_mesh(e);
        if (!mesh) return flagged;
        double z_base = 0.0;
        auto footprint = lowest_footprint(*mesh, geos, z_base);
        if (geos.is_empty(footprint)) return flagged;
        return placement_found(footprint, z_base, geos) ? Verdict{} : flagged;
    }

private:
    // clash_utils.lowest_footprint: the union of the plan projections of the
    // lowest triangles (centroid within 1 mm of the lowest point).
    static geometry::Geos::Geom lowest_footprint(const TriMesh& mesh, const geometry::Geos& geos, double& z_min) {
        double x0, y0, x1, y1, z1;
        mesh.bounds().Get(x0, y0, z_min, x1, y1, z1);
        std::vector<std::pair<double, size_t>> cz;
        for (size_t t = 0; t < mesh.triangle_count(); ++t) {
            P3 a, b, c;
            mesh.corners(t, a, b, c);
            cz.push_back({(a[2] + b[2] + c[2]) / 3.0, t});
        }
        std::vector<size_t> lowest;
        for (const auto& [z, t] : cz)
            if (z <= z_min + 0.001) lowest.push_back(t);
        if (lowest.empty()) {
            std::stable_sort(cz.begin(), cz.end(), [](const auto& a, const auto& b) { return a.first < b.first; });
            for (size_t i = 0; i < std::min<size_t>(2, cz.size()); ++i) lowest.push_back(cz[i].second);
        }
        std::vector<geometry::Geos::Geom> polygons;
        for (size_t t : lowest) {
            P3 a, b, c;
            mesh.corners(t, a, b, c);
            auto poly = geos.polygon({{a[0], a[1], 0}, {b[0], b[1], 0}, {c[0], c[1], 0}}, 2);
            if (!geos.is_empty(poly)) polygons.push_back(std::move(poly));
        }
        if (polygons.empty()) return geometry::Geos::Geom(nullptr, geometry::Geos::Deleter{geos.context()});
        return geos.union_all(polygons);
    }

    // The plan footprint of the part of an obstacle between two heights.
    geometry::Geos::Geom slab_footprint(const TriMesh& o, const double box[4], double z_low, double z_high,
                                        const geometry::Geos& geos) const {
        std::vector<geometry::Geos::Geom> parts;
        for (size_t t = 0; t < o.triangle_count(); ++t) {
            double bx0, by0, bz0, bx1, by1, bz1;
            o.box(t).Get(bx0, by0, bz0, bx1, by1, bz1);
            if (bx1 < box[0] || bx0 > box[2] || by1 < box[1] || by0 > box[3] || bz1 < z_low || bz0 > z_high) continue;
            P3 a, b, c;
            o.corners(t, a, b, c);
            const auto poly = clip_triangle_z(a, b, c, z_low, z_high);
            if (poly.size() < 3) continue;
            double area2 = 0.0;
            for (size_t i = 0; i < poly.size(); ++i) {
                const P3& p = poly[i];
                const P3& q = poly[(i + 1) % poly.size()];
                area2 += p[0] * q[1] - q[0] * p[1];
            }
            if (std::abs(area2) <= 1e-12) continue;  // seen edge-on
            std::vector<std::array<double, 3>> pts;
            for (const P3& p : poly) pts.push_back({p[0], p[1], 0.0});
            auto g = geos.polygon(pts, 2);
            if (!geos.is_empty(g)) parts.push_back(std::move(g));
        }
        // The sections at the band limits (even-odd over their loops).
        for (const double h : {z_low, z_high}) {
            geometry::Geos::Geom region(nullptr, geometry::Geos::Deleter{geos.context()});
            for (const auto& loop : section_loops(o, h)) {
                std::vector<std::array<double, 3>> pts;
                for (const P2& p : loop) pts.push_back({p[0], p[1], 0.0});
                auto g = geos.buffer(geos.polygon(pts, 2), 0.0);  // repair a self-touching ring
                if (geos.is_empty(g)) continue;
                if (!region || geos.is_empty(region)) {
                    region = std::move(g);
                    continue;
                }
                auto inter = geos.intersection(region, g);
                std::vector<geometry::Geos::Geom> both;
                both.push_back(geos.clone(region));
                both.push_back(geos.clone(g));
                region = geos.difference(geos.union_all(both), inter);
            }
            if (region && !geos.is_empty(region)) parts.push_back(std::move(region));
        }
        if (parts.empty()) return geometry::Geos::Geom(nullptr, geometry::Geos::Deleter{geos.context()});
        return geos.union_all(parts);
    }

    // FreeSpace._search_placement, the verdict part: is there a center left?
    bool placement_found(const geometry::Geos::Geom& footprint, double z_base, const geometry::Geos& geos) const {
        const double radius = params().diameter / 2.0;
        auto center_region = geos.buffer(footprint, -radius);
        if (geos.is_empty(center_region)) return false;
        const auto b = geos.bounds(footprint);
        const double pad = radius + 0.1;
        const double box[4] = {b[0] - pad, b[1] - pad, b[2] + pad, b[3] + pad};
        const double z_low = z_base + kTouchEpsilon;
        const double z_high = z_base + *params().height - kTouchEpsilon;
        if (z_high <= z_low) return true;
        for (const auto& o : obstacles_) {
            double x0, y0, z0, x1, y1, z1;
            o->bounds().Get(x0, y0, z0, x1, y1, z1);
            if (x1 < box[0] || x0 > box[2] || y1 < box[1] || y0 > box[3]) continue;
            if (z1 < z_low || z0 > z_high) continue;
            auto projection = slab_footprint(*o, box, z_low, z_high, geos);
            if (!projection || geos.is_empty(projection)) continue;
            auto blocked = geos.buffer(projection, radius - kTouchEpsilon);
            center_region = geos.difference(center_region, blocked);
            if (geos.is_empty(center_region)) return false;
        }
        return true;
    }

    std::vector<std::shared_ptr<const TriMesh>> obstacles_;
};

}  // namespace

RuleSpec spec_ray_check_triang() {
    return RuleSpec::pair<RayCheckTriang>(
        "Ray_Check_triang", "Ray Check (triangles)", {Slot::Source, Slot::Target, Slot::Context},
        "Ray_Check on the triangles: flags the source/target pairs whose center-to-center ray is free of context "
        "elements.",
        {param(&RayCheckParams::max_ray_length, "max_ray_length").doc("Maximum ray length").unit(Unit::Metre)});
}

RuleSpec spec_direct_view_triang() {
    return RuleSpec::pair<DirectViewTriang>(
        "DirectView_triang", "Direct View (triangles)", {Slot::Source, Slot::Target, Slot::Context},
        "DirectView on the triangles: flags the pairs that see each other (hit ratio of the rays at least the "
        "threshold).",
        {param(&DirectViewParams::ray_source, "ray_source").doc("Where the rays start").values({"Source", "Target", "Both"}),
         param(&DirectViewParams::ray_count, "ray_count").doc("Number of rays per pair"),
         param(&DirectViewParams::threshold, "threshold").doc("Visibility threshold (%)"),
         param(&DirectViewParams::max_distance, "max_distance").doc("Maximum distance").unit(Unit::Metre)});
}

RuleSpec spec_free_space_triang() {
    return RuleSpec::element<FreeSpaceTriang>(
        "FreeSpace_triang", "Free Space (triangles)", {Slot::Source, Slot::Context},
        "FreeSpace on the triangles: flags the sources where no free cylinder (diameter x height) fits among the "
        "context elements.",
        {param(&FreeSpaceParams::diameter, "diameter").doc("Free space diameter").unit(Unit::Metre),
         param(&FreeSpaceParams::height, "height").doc("Free space height").unit(Unit::Metre)});
}

}  // namespace ifcclash
