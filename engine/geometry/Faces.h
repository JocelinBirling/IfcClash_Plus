// IfcClash_Plus engine — OCC face helpers of clash_utils.py (pure geometry).
#pragma once

#include "../core/Result.h"

#include <TopoDS_Face.hxx>
#include <TopoDS_Shape.hxx>
#include <gp_Dir.hxx>
#include <gp_Pnt.hxx>

#include <optional>
#include <vector>

namespace ifcclash::geometry {

// clash_utils.get_face_normal (None for a degenerate parametrisation)
std::optional<gp_Dir> face_normal(const TopoDS_Face& face);
// clash_utils.get_face_area
double face_area(const TopoDS_Face& face);
// clash_utils.face_triangles: meshes the face in place (0.01, parallel) and
// returns its triangles (nodes NOT moved by the face location, as in Python).
std::vector<Triangle3> face_triangles(const TopoDS_Face& face, double linear_deflection = 0.01);
// Rules._extrem_face_data
FaceData extrem_face_data(const TopoDS_Face& face);

// clash_utils.get_faces_visible_from_direction_with_plane (defaults: 45 deg,
// plane at 100, size factor 1, 50 x 50 rays): the faces first hit by the
// rays, in the order of their first hit (dict order in Python, faces
// compared with IsEqual as pythonocc does).
std::vector<TopoDS_Face> visible_faces(const TopoDS_Shape& shape, const gp_Dir& direction);

// clash_utils.check_extrem_face_distance
struct ExtremCandidate {
    gp_Pnt point;
    TopoDS_Face source_face;
    TopoDS_Face target_face;
    double distance = 0.0;
};
struct ExtremDetails {
    TopoDS_Face source_face;
    TopoDS_Face target_face;
    Point3 source_point{};
    Point3 target_point{};
    double distance = 0.0;
};
struct ExtremCheck {
    enum class Side { RightSide, TooFar, NeedMoreCheck } side = Side::TooFar;
    std::optional<ExtremDetails> details;
    std::vector<ExtremCandidate> candidates;
};
ExtremCheck check_extrem_face_distance(const std::vector<TopoDS_Face>& source_faces,
                                       const std::vector<TopoDS_Face>& target_faces, double tolerance,
                                       bool above);

// The minimal distance between two shapes (BRepExtrema_DistShapeShape).
double shape_distance(const TopoDS_Shape& a, const TopoDS_Shape& b);

}  // namespace ifcclash::geometry
