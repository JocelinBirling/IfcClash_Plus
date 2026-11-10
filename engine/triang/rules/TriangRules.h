// IfcClash_Plus engine — the _triang rules (engine/triang/rules): the rules of
// the registry computed on triangles only (Variant::Triangles: the .ifcview or
// the IFC triangulation, per SessionOptions::triangle_source).
#pragma once

#include "../../registry/RuleSpec.h"

namespace ifcclash {

class Registry;

// TreeTriang.cpp
RuleSpec spec_intersection_triang();
RuleSpec spec_clearance_triang();
RuleSpec spec_collision_triang();
// SurfaceTriang.cpp
RuleSpec spec_volume_triang();
RuleSpec spec_area_triang();
RuleSpec spec_top_or_bottom_surface_triang();
RuleSpec spec_lateral_surface_triang();
RuleSpec spec_projected_surface_triang();
// DirectionalTriang.cpp
RuleSpec spec_above_triang();
RuleSpec spec_below_triang();
RuleSpec spec_obb_above_triang();
RuleSpec spec_obb_below_triang();
RuleSpec spec_obb_front_and_back_triang();
RuleSpec spec_obb_custom_triang();
// SkinTriang.cpp
RuleSpec spec_clearance_axis_to_axis_triang();
RuleSpec spec_surface_recover_triang();
// ContextTriang.cpp
RuleSpec spec_ray_check_triang();
RuleSpec spec_direct_view_triang();
// FaceTriang.cpp, ContextTriang.cpp (FreeSpace)
RuleSpec spec_one_object_face_triang();
RuleSpec spec_two_objects_face_triang();
RuleSpec spec_free_space_triang();
// ObbTriang.cpp
RuleSpec spec_obb_high_triang();
RuleSpec spec_obb_length_triang();
RuleSpec spec_orientation_triang();
RuleSpec spec_angle_between_triang();
RuleSpec spec_alignement_triang();

namespace triang {
// Adds every _triang rule to the registry (TriangRules.cpp).
void register_triang_rules(Registry& registry);
}  // namespace triang

}  // namespace ifcclash
