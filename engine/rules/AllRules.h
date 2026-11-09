// IfcClash_Plus engine — one function per rule: its RuleSpec (rules/<Rule>.cpp).
#pragma once

#include "../registry/RuleSpec.h"

namespace ifcclash {

RuleSpec spec_volume();
// engine/triang: the rules on the .ifcview triangles only
RuleSpec spec_intersection_triang();
RuleSpec spec_above_triang();
RuleSpec spec_obb_above_triang();
RuleSpec spec_intersection();
RuleSpec spec_clearance();
RuleSpec spec_collision();
RuleSpec spec_area();
RuleSpec spec_top_or_bottom_surface();
RuleSpec spec_lateral_surface();
RuleSpec spec_projected_surface();
RuleSpec spec_obb_high();
RuleSpec spec_obb_length();
RuleSpec spec_orientation();
RuleSpec spec_above();
RuleSpec spec_below();
RuleSpec spec_obb_above();
RuleSpec spec_obb_below();
RuleSpec spec_obb_front_and_back();
RuleSpec spec_obb_custom();
RuleSpec spec_angle_between();
RuleSpec spec_clearance_axis_to_axis();
RuleSpec spec_intersection2();
RuleSpec spec_one_object_face();
RuleSpec spec_two_objects_face();
RuleSpec spec_surface_recover();
RuleSpec spec_clearance_for_doors();
RuleSpec spec_ray_check();
RuleSpec spec_direct_view();
RuleSpec spec_free_space();
RuleSpec spec_alignement();

}  // namespace ifcclash
