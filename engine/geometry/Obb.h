// IfcClash_Plus engine — the OBB of CustomOBB.py (Custom_OBB), on OCCT Bnd_OBB.
#pragma once

#include "../core/Result.h"

#include <Bnd_Box.hxx>
#include <Bnd_OBB.hxx>
#include <TopoDS_Shape.hxx>
#include <gp_Dir.hxx>
#include <gp_Pnt.hxx>
#include <gp_XYZ.hxx>

#include <array>
#include <string>
#include <utility>

namespace ifcclash::geometry {

// CustomOBB.create_obb_from_TopoDs_Shape: meshes the shape
// (BRepMesh_IncrementalMesh(0.01, relative=False, 0.5), as Python does: it
// MODIFIES the shape) then BRepBndLib::AddOBB(shape, True, True, True),
// rebuilt through gp_Dir as Custom_OBB(center, x_dir, ...) does.
Bnd_OBB obb_of_shape(const TopoDS_Shape& shape);

// Custom_OBB.get_corners: center +- the directed half sizes, in the Python
// order (sx, sy, sz in -1, +1).
std::array<gp_XYZ, 8> obb_corners(const Bnd_OBB& obb);

// Custom_OBB.get_two_main_direction_OBB_shape(wide_or_narrow, only_check_xy)
// ("Narrow" — case sensitive — sorts the sizes downward, as in Python).
std::pair<gp_Dir, gp_Dir> two_main_directions(const Bnd_OBB& obb, const std::string& wide_or_narrow,
                                              bool only_check_xy = true);

// Custom_OBB.to_data(label)
ObbData obb_data(const Bnd_OBB& obb, const std::optional<std::string>& label);

// A change of the OBB operations: a length, or a percentage ("50%").
struct ObbChange {
    double value = 0.0;
    bool percent = false;  // value is then the ratio (50% -> 0.5)
};

// Custom_OBB(center, x_dir, y_dir, z_dir, x_h, y_h, z_h)
Bnd_OBB make_obb(const gp_Pnt& center, const gp_Dir& x, const gp_Dir& y, const gp_Dir& z, double hx, double hy,
                 double hz);
// Custom_OBB.detach_top_by_extrude / detach_bottom_by_extrude
Bnd_OBB detach_by_extrude(const Bnd_OBB& obb, const ObbChange& change, bool top);
// Custom_OBB.extend_up / extend_down
Bnd_OBB extend_vertically(const Bnd_OBB& obb, const ObbChange& change, bool up);
// Custom_OBB.expand_sides (in place; the numeric branch uses ZHSize as in
// Python)
void expand_sides(Bnd_OBB& obb, const ObbChange& change);
// Custom_OBB.detach_side_by_extrude
Bnd_OBB detach_side_by_extrude(const Bnd_OBB& obb, const gp_Dir& direction, double distance);
// Custom_OBB.to_TopoDS_Solid
TopoDS_Shape obb_solid(const Bnd_OBB& obb);
// The axis-aligned box of the 8 corners (a broad volume containing the OBB).
Bnd_Box obb_aabb(const Bnd_OBB& obb);

// RuleCheck._shape_center: the center of the Bnd_Box of the shape.
gp_Pnt shape_center(const TopoDS_Shape& shape);

}  // namespace ifcclash::geometry
