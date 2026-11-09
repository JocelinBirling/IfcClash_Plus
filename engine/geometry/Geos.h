// IfcClash_Plus engine — a thin RAII layer on the GEOS C API.
//
// GEOS is the library under shapely: calling it directly gives the Python
// engine's polygon results (intersections, unions, areas) bit for bit, which
// Clipper2 would not (SPEC "Parité Clipper2 / shapely").
#pragma once

#include <array>
#include <memory>
#include <vector>

typedef struct GEOSContextHandle_HS* GEOSContextHandle_t;
typedef struct GEOSGeom_t GEOSGeometry;

namespace ifcclash::geometry {

class Geos {
public:
    Geos();
    ~Geos();
    Geos(const Geos&) = delete;
    Geos& operator=(const Geos&) = delete;

    struct Deleter {
        GEOSContextHandle_t ctx;
        void operator()(GEOSGeometry* g) const;
    };
    using Geom = std::unique_ptr<GEOSGeometry, Deleter>;

    // shapely.Polygon(points): a closed ring (the first point repeated).
    // `dims` is 2 or 3 (a 3D polygon keeps its Z; areas and intersections
    // are planar, as in shapely).
    Geom polygon(const std::vector<std::array<double, 3>>& points, int dims = 3) const;

    double area(const Geom& g) const;
    // a.intersection(b).area
    double intersection_area(const Geom& a, const Geom& b) const;
    // shapely.ops.unary_union(polygons).area (GeometryCollection + unary union);
    // consumes the geometries.
    double union_area(std::vector<Geom>& geometries) const;
    // shapely.ops.unary_union(polygons), consumed.
    Geom union_all(std::vector<Geom>& geometries) const;
    Geom intersection(const Geom& a, const Geom& b) const;
    Geom difference(const Geom& a, const Geom& b) const;
    bool is_empty(const Geom& g) const;
    // shapely buffer (round caps and joins, quad_segs=16 by default)
    Geom buffer(const Geom& g, double width, int quad_segs = 16) const;
    // shapely bounds: (minx, miny, maxx, maxy)
    std::array<double, 4> bounds(const Geom& g) const;
    Geom clone(const Geom& g) const;
    // The exterior rings (x, y) of the polygons of a geometry, recursing in
    // collections (the parts of _fan_triangulation); other parts skipped.
    std::vector<std::vector<std::array<double, 2>>> exterior_rings(const Geom& g) const;
    GEOSContextHandle_t context() const { return ctx_; }

private:
    GEOSContextHandle_t ctx_;
};

}  // namespace ifcclash::geometry
