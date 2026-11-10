#include "TriangRules.h"

#include "../../registry/Registry.h"

namespace ifcclash::triang {

void register_triang_rules(Registry& registry) {
    registry.add(spec_intersection_triang());
    registry.add(spec_clearance_triang());
    registry.add(spec_collision_triang());
    registry.add(spec_volume_triang());
    registry.add(spec_area_triang());
    registry.add(spec_top_or_bottom_surface_triang());
    registry.add(spec_lateral_surface_triang());
    registry.add(spec_projected_surface_triang());
    registry.add(spec_above_triang());
    registry.add(spec_below_triang());
    registry.add(spec_obb_above_triang());
    registry.add(spec_obb_below_triang());
    registry.add(spec_obb_front_and_back_triang());
    registry.add(spec_obb_custom_triang());
    registry.add(spec_obb_high_triang());
    registry.add(spec_obb_length_triang());
    registry.add(spec_orientation_triang());
    registry.add(spec_angle_between_triang());
    registry.add(spec_alignement_triang());
    registry.add(spec_clearance_axis_to_axis_triang());
    registry.add(spec_surface_recover_triang());
    registry.add(spec_ray_check_triang());
    registry.add(spec_direct_view_triang());
    registry.add(spec_one_object_face_triang());
    registry.add(spec_two_objects_face_triang());
    registry.add(spec_free_space_triang());
}

}  // namespace ifcclash::triang
