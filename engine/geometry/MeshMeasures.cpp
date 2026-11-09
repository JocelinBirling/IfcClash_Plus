#include "MeshMeasures.h"

#include <NCollection_Array1.hxx>
#include <gp_Pnt.hxx>

#include <cmath>

namespace ifcclash::geometry {

double mesh_volume(const std::vector<double>& verts, const std::vector<int>& faces) {
    // Same operations, same order as ifcopenshell.util.shape.get_volume
    // (signed_triangle_volume then abs(sum(volumes))): bit-for-bit parity.
    double sum = 0.0;
    for (size_t i = 0; i + 2 < faces.size(); i += 3) {
        const double* p1 = &verts[3 * static_cast<size_t>(faces[i])];
        const double* p2 = &verts[3 * static_cast<size_t>(faces[i + 1])];
        const double* p3 = &verts[3 * static_cast<size_t>(faces[i + 2])];
        const double v321 = p3[0] * p2[1] * p1[2];
        const double v231 = p2[0] * p3[1] * p1[2];
        const double v312 = p3[0] * p1[1] * p2[2];
        const double v132 = p1[0] * p3[1] * p2[2];
        const double v213 = p2[0] * p1[1] * p3[2];
        const double v123 = p1[0] * p2[1] * p3[2];
        sum += (1.0 / 6.0) * (-v321 + v231 + v312 - v132 - v213 + v123);
    }
    return std::abs(sum);
}

Bnd_Box aabb_of(const std::vector<double>& verts) {
    Bnd_Box box;
    for (size_t i = 0; i + 2 < verts.size(); i += 3) {
        box.Add(gp_Pnt(verts[i], verts[i + 1], verts[i + 2]));
    }
    return box;
}

Bnd_OBB obb_of(const std::vector<double>& verts) {
    Bnd_OBB obb;
    const int n = static_cast<int>(verts.size() / 3);
    if (n == 0) return obb;
    NCollection_Array1<gp_Pnt> points(1, n);
    for (int i = 0; i < n; ++i) {
        points.SetValue(i + 1, gp_Pnt(verts[3 * i], verts[3 * i + 1], verts[3 * i + 2]));
    }
    obb.ReBuild(points);
    return obb;
}

Bnd_Box inflate(const Bnd_Box& box, double gap) {
    // Bnd_Box::Enlarge keeps max(gap, tol): it does not add up. The corners
    // are rebuilt instead, so that successive inflations accumulate.
    if (box.IsVoid() || gap <= 0.0) return box;
    double x0, y0, z0, x1, y1, z1;
    box.Get(x0, y0, z0, x1, y1, z1);  // includes the current gap
    Bnd_Box out;
    out.Update(x0 - gap, y0 - gap, z0 - gap, x1 + gap, y1 + gap, z1 + gap);
    return out;
}

Bnd_OBB inflate(const Bnd_OBB& box, double gap) {
    Bnd_OBB out = box;
    if (!out.IsVoid() && gap > 0.0) out.Enlarge(gap);
    return out;
}

}  // namespace ifcclash::geometry
