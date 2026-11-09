#include "MeshMeasures.h"

#include "Numpy.h"

#include <NCollection_Array1.hxx>
#include <gp_Pnt.hxx>

#include <cmath>
#include <optional>

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

namespace {

Vec3 sub(const Vec3& a, const Vec3& b) { return {a[0] - b[0], a[1] - b[1], a[2] - b[2]}; }
Vec3 cross(const Vec3& a, const Vec3& b) {
    return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
}
double dot(const Vec3& a, const Vec3& b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
double norm(const Vec3& a) { return std::sqrt(dot(a, a)); }
Vec3 normalized(const Vec3& a) {
    const double n = norm(a);
    return {a[0] / n, a[1] / n, a[2] / n};
}

// The unit normal of triangle t (numpy: cross / norm(axis=1); a degenerate
// triangle gives NaN, which fails every ">" filter as in numpy).
Vec3 unit_normal(const std::vector<double>& verts, const std::vector<int>& faces, size_t t) {
    const Vec3 p0 = vertex(verts, faces[3 * t]);
    const Vec3 c = cross(sub(vertex(verts, faces[3 * t + 1]), p0), sub(vertex(verts, faces[3 * t + 2]), p0));
    return np::div(c, np::row_norm(c));
}

}  // namespace

double triangle_area(const Vec3& p0, const Vec3& p1, const Vec3& p2) {
    return 0.5 * np::norm(cross(sub(p1, p0), sub(p2, p0)));
}

FaceData triangle_face_data(const Vec3& p0, const Vec3& p1, const Vec3& p2) {
    const Vec3 c = cross(sub(p1, p0), sub(p2, p0));
    const double n = np::norm(c);
    FaceData face;
    face.normal = n > 0.0 ? Vec3{c[0] / n, c[1] / n, c[2] / n} : Vec3{0.0, 0.0, 0.0};
    face.area = n / 2.0;
    face.triangles.push_back({p0, p1, p2});
    return face;
}

double mesh_area(const std::vector<double>& verts, const std::vector<int>& faces) {
    double total = 0.0;
    for (size_t t = 0; t + 2 < faces.size(); t += 3) {
        total += norm(cross(sub(vertex(verts, faces[t + 1]), vertex(verts, faces[t])),
                            sub(vertex(verts, faces[t + 2]), vertex(verts, faces[t])))) /
                 2;
    }
    return total;
}

double side_area(const std::vector<double>& verts, const std::vector<int>& faces, Vec3 direction,
                 double angle_degrees) {
    direction = np::unit(direction);
    const double acceptable = std::cos(angle_degrees * M_PI / 180.0) + 0.01;
    std::vector<int> kept;
    for (size_t t = 0; 3 * t + 2 < faces.size(); ++t) {
        if (np::matvec(unit_normal(verts, faces, t), direction) > acceptable) {
            kept.insert(kept.end(), faces.begin() + 3 * t, faces.begin() + 3 * t + 3);
        }
    }
    return mesh_area(verts, kept);
}

double footprint_area(const std::vector<double>& verts, const std::vector<int>& faces, Vec3 direction,
                      const Geos& geos) {
    direction = np::unit(direction);
    std::vector<size_t> kept;
    for (size_t t = 0; 3 * t + 2 < faces.size(); ++t) {
        if (np::matvec(unit_normal(verts, faces, t), direction) > 0.01) kept.push_back(t);
    }
    // Flatten along the direction, then the 2D basis of get_footprint_area.
    const Vec3 d = np::unit(direction);
    Vec3 a = d;
    if (!(std::abs(a[2] - 1.0) <= 0.01 + 1e-5 * 1.0)) {  // not np.isclose(a[2], 1.0, atol=0.01)
        a[2] += 0.01;
    } else {
        a = {1.0, 0.0, 0.0};
    }
    Vec3 b = cross(d, a);
    b = np::unit(b);
    const Vec3 c = cross(d, b);
    auto to2d = [&](int index) {
        Vec3 v = vertex(verts, index);
        const double k = np::dot(v, direction);
        v = {v[0] - k * direction[0], v[1] - k * direction[1], v[2] - k * direction[2]};
        return std::array<double, 3>{np::dot(v, b), np::dot(v, c), 0.0};
    };
    std::vector<Geos::Geom> polygons;
    for (size_t t : kept) {
        polygons.push_back(geos.polygon({to2d(faces[3 * t]), to2d(faces[3 * t + 1]), to2d(faces[3 * t + 2])}, 2));
    }
    return geos.union_area(polygons);
}

std::vector<int> extreme_faces(const std::vector<double>& verts, const std::vector<int>& faces, Vec3 direction,
                               const Geos& geos) {
    constexpr double kMinCoverage = 0.99;
    direction = np::unit(direction);
    std::vector<int> filtered;
    for (size_t t = 0; 3 * t + 2 < faces.size(); ++t) {
        if (np::matvec(unit_normal(verts, faces, t), direction) > 0.1) filtered.push_back(static_cast<int>(t));
    }
    struct Face {
        std::array<Vec3, 3> p;
        Geos::Geom polygon;
        double z_avg;
        double area;
    };
    std::vector<Face> list;
    list.reserve(filtered.size());
    for (int t : filtered) {
        Face f;
        for (int k = 0; k < 3; ++k) f.p[k] = vertex(verts, faces[3 * t + k]);
        f.polygon = geos.polygon({f.p[0], f.p[1], f.p[2]}, 3);
        f.z_avg = (f.p[0][2] + f.p[1][2] + f.p[2][2]) / 3;
        f.area = geos.area(f.polygon);
        list.push_back(std::move(f));
    }
    std::vector<int> out;
    for (size_t i = 0; i < list.size(); ++i) {
        double covered = 0.0;
        for (size_t j = 0; j < list.size(); ++j) {
            if (list[i].p == list[j].p) continue;  // shapely ==: identical coordinates
            if (direction[2] == -1 && list[i].z_avg < list[j].z_avg) continue;
            if (direction[2] == 1 && list[i].z_avg > list[j].z_avg) continue;
            covered += geos.intersection_area(list[i].polygon, list[j].polygon) / list[i].area;
        }
        if (kMinCoverage < covered) continue;
        out.push_back(filtered[i]);
    }
    return out;
}

}  // namespace ifcclash::geometry
