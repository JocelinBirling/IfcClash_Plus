// IfcClash_Plus engine — the triangle helpers of the face rules
// (clash_utils.py: FaceSelection, triangle pair tests).
#pragma once

#include "../core/Result.h"

#include <optional>
#include <string>
#include <variant>
#include <vector>

namespace ifcclash::geometry {

using V3 = std::array<double, 3>;

// A validated FaceSelection dictionary (clash_utils.validate_face_selection);
// throws ConfigError on an invalid one.
struct FaceSelection {
    std::optional<double> min_surface, max_surface;
    // none | "Top" | "Bottom" | "Side" | a unit vector
    std::variant<std::monostate, std::string, V3> orientation;
    bool extreme_faces = false;
    std::optional<std::vector<std::string>> materials;

    static FaceSelection parse(const Json& selection);
};

// clash_utils.select_faces: the selected triangles, in face order.
std::vector<Triangle3> select_faces(const std::vector<double>& verts, const std::vector<int>& faces,
                                    const FaceSelection& selection, const std::vector<std::string>& material_names);

// _triangle_data: (unit normal, area)
std::pair<V3, double> triangle_data(const Triangle3& t);
// clash_utils._triangle_key (vertices sorted)
std::array<V3, 3> triangle_key(const Triangle3& t);
bool triangles_share_geometry(const Triangle3& a, const Triangle3& b);
bool triangles_cross_properly(const Triangle3& a, const Triangle3& b);
double triangle_penetration_depth(const Triangle3& a, const Triangle3& b);
// via OpenCascade faces (BRepExtrema), +inf when a face cannot be built
double distance_between_triangles(const Triangle3& a, const Triangle3& b);
double triangles_bbox_distance(const Triangle3& a, const Triangle3& b);
// the AABB of a triangle list (min, max)
std::pair<V3, V3> triangles_bounds(const std::vector<Triangle3>& triangles);

// One failed face check (FACE_CHECK_MEASURES: distance -> distance,
// intersection -> penetration_depth, orientation -> angle).
struct FaceFailure {
    Measure measure;
    double value;
};

// The configuration of the face checks (OneObjectFace / TwoObjectsFace).
struct FaceChecks {
    bool distance = false;
    std::optional<double> min_distance, max_distance;
    bool skip_adjacent = true;      // OneObjectFace only
    bool two_objects = false;       // TwoObjectsFace: the min_distance bbox shortcut
    bool intersection = false;
    double intersection_tolerance = 0.0;
    bool orientation = false;
    std::optional<double> angle;
    double angle_tolerance = 0.0;
};
std::vector<FaceFailure> run_face_checks(const Triangle3& a, const Triangle3& b, const FaceChecks& checks);
// The FaceData of one triangle as the face rules pose it.
FaceData face_rule_data(const Triangle3& t);

}  // namespace ifcclash::geometry
