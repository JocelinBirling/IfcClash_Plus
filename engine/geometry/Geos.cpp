#include "Geos.h"

#include <geos_c.h>

#include <stdexcept>

namespace ifcclash::geometry {

Geos::Geos() : ctx_(GEOS_init_r()) {
    if (!ctx_) throw std::runtime_error("GEOS context could not be created");
}

Geos::~Geos() { GEOS_finish_r(ctx_); }

void Geos::Deleter::operator()(GEOSGeometry* g) const {
    if (g) GEOSGeom_destroy_r(ctx, g);
}

Geos::Geom Geos::polygon(const std::vector<std::array<double, 3>>& points, int dims) const {
    const unsigned n = static_cast<unsigned>(points.size());
    GEOSCoordSequence* seq = GEOSCoordSeq_create_r(ctx_, n + 1, dims);
    for (unsigned i = 0; i <= n; ++i) {
        const auto& p = points[i % n];
        GEOSCoordSeq_setX_r(ctx_, seq, i, p[0]);
        GEOSCoordSeq_setY_r(ctx_, seq, i, p[1]);
        if (dims == 3) GEOSCoordSeq_setZ_r(ctx_, seq, i, p[2]);
    }
    GEOSGeometry* ring = GEOSGeom_createLinearRing_r(ctx_, seq);
    if (!ring) throw std::runtime_error("GEOS: invalid ring");
    return Geom(GEOSGeom_createPolygon_r(ctx_, ring, nullptr, 0), Deleter{ctx_});
}

double Geos::area(const Geom& g) const {
    double a = 0.0;
    if (g) GEOSArea_r(ctx_, g.get(), &a);
    return a;
}

Geos::Geom Geos::intersection(const Geom& a, const Geom& b) const {
    return Geom(GEOSIntersection_r(ctx_, a.get(), b.get()), Deleter{ctx_});
}

Geos::Geom Geos::difference(const Geom& a, const Geom& b) const {
    return Geom(GEOSDifference_r(ctx_, a.get(), b.get()), Deleter{ctx_});
}

double Geos::intersection_area(const Geom& a, const Geom& b) const {
    return area(intersection(a, b));
}

Geos::Geom Geos::union_all(std::vector<Geom>& geometries) const {
    std::vector<GEOSGeometry*> raw;
    raw.reserve(geometries.size());
    for (auto& g : geometries) raw.push_back(g.release());
    GEOSGeometry* collection = GEOSGeom_createCollection_r(ctx_, GEOS_GEOMETRYCOLLECTION, raw.data(),
                                                           static_cast<unsigned>(raw.size()));
    geometries.clear();
    Geom owned(collection, Deleter{ctx_});
    return Geom(GEOSUnaryUnion_r(ctx_, owned.get()), Deleter{ctx_});
}

double Geos::union_area(std::vector<Geom>& geometries) const { return area(union_all(geometries)); }

static void collect_rings(GEOSContextHandle_t ctx, const GEOSGeometry* g,
                          std::vector<std::vector<std::array<double, 2>>>& out) {
    const int type = GEOSGeomTypeId_r(ctx, g);
    if (type == GEOS_POLYGON) {
        const GEOSGeometry* ring = GEOSGetExteriorRing_r(ctx, g);
        const GEOSCoordSequence* seq = GEOSGeom_getCoordSeq_r(ctx, ring);
        unsigned n = 0;
        GEOSCoordSeq_getSize_r(ctx, seq, &n);
        std::vector<std::array<double, 2>> points(n);
        for (unsigned i = 0; i < n; ++i) {
            GEOSCoordSeq_getX_r(ctx, seq, i, &points[i][0]);
            GEOSCoordSeq_getY_r(ctx, seq, i, &points[i][1]);
        }
        out.push_back(std::move(points));
        return;
    }
    if (type == GEOS_MULTIPOLYGON || type == GEOS_GEOMETRYCOLLECTION) {
        const int parts = GEOSGetNumGeometries_r(ctx, g);
        for (int i = 0; i < parts; ++i) collect_rings(ctx, GEOSGetGeometryN_r(ctx, g, i), out);
    }
}

std::vector<std::vector<std::array<double, 2>>> Geos::exterior_rings(const Geom& g) const {
    std::vector<std::vector<std::array<double, 2>>> out;
    if (g) collect_rings(ctx_, g.get(), out);
    return out;
}

Geos::Geom Geos::buffer(const Geom& g, double width, int quad_segs) const {
    return Geom(GEOSBufferWithStyle_r(ctx_, g.get(), width, quad_segs, GEOSBUF_CAP_ROUND, GEOSBUF_JOIN_ROUND, 5.0),
                Deleter{ctx_});
}

std::array<double, 4> Geos::bounds(const Geom& g) const {
    std::array<double, 4> b{0, 0, 0, 0};
    GEOSGeom_getXMin_r(ctx_, g.get(), &b[0]);
    GEOSGeom_getYMin_r(ctx_, g.get(), &b[1]);
    GEOSGeom_getXMax_r(ctx_, g.get(), &b[2]);
    GEOSGeom_getYMax_r(ctx_, g.get(), &b[3]);
    return b;
}

Geos::Geom Geos::clone(const Geom& g) const { return Geom(GEOSGeom_clone_r(ctx_, g.get()), Deleter{ctx_}); }

bool Geos::is_empty(const Geom& g) const { return !g || GEOSisEmpty_r(ctx_, g.get()) == 1; }

}  // namespace ifcclash::geometry
