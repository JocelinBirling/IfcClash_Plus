from RuleClass import (
    RuleCheckOneObject,
    RuleCheckTwoObjects,
    ClashResultOneObject,
    ClashResultTwoObjects,
    RaycastData,
    ZoneData,
    Select,
)
import ifcopenshell
import multiprocessing
import math
import clash_utils
import shapely
from ifcopenshell.util.shape import (
    get_vertices,
    get_faces,
)
import numpy as np
from typing import Literal
from CustomOBB import (
    create_obb_from_TopoDs_Shape_via_pca,
    create_obb_with_free_z,
    create_obb_with_fixed_z,
    create_obb_from_TopoDs_Shape,
)
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape, BRepExtrema_ExtFF
import ifcopenshell.util.placement
from OCC.Core.gp import gp_Ax3, gp_Pnt, gp_Dir, gp_Trsf, gp_XYZ, gp_Vec, gp_Lin
import ifcopenshell.util.shape
from construct_display_function import create_makepolygon_with_dir
from OCC.Core.BRepIntCurveSurface import BRepIntCurveSurface_Inter


DIRECTION_METHOD = Literal["Wide", "Narrow"]


# ===========One Object Rule
class Volume(RuleCheckOneObject):
    from ifcopenshell.util.shape import get_volume

    def __init__(self, source, volume_min, volume_max, state="Final"):
        super().__init__(state, source)
        self.type = "Volume"
        self.volume_max: float = volume_max
        self.volume_min: float = volume_min
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    volume = ifcopenshell.util.shape.get_volume(geom)
                    entity = ifc_file.by_id(shape.id)
                    if self.volume_min < volume < self.volume_max:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)
                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


class Area(RuleCheckOneObject):
    from ifcopenshell.util.shape import get_area

    def __init__(self, source, volume_min, volume_max, state="Final"):
        super().__init__(state, source)
        self.type = "Area"
        self.volume_max: float = volume_max
        self.volume_min: float = volume_min
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    area = ifcopenshell.util.shape.get_area(geom)
                    entity = ifc_file.by_id(shape.id)
                    if self.volume_min < area < self.volume_max:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


TOP_OR_BOT = Literal["Top", "Bottom"]


class TopOrBottomSurface(RuleCheckOneObject):
    def __init__(
        self, source, surface_min, surface_max, top_or_bot: TOP_OR_BOT, state="Final"
    ):
        super().__init__(state, source)
        self.type = top_or_bot + "Surface"
        self.surface_max: float = surface_max
        self.surface_min: float = surface_min
        self.top_or_bot_method: TOP_OR_BOT = top_or_bot
        self.geom_settings = ifcopenshell.geom.settings()
        # The extreme faces are registered in the display registry:
        # they must be in world coordinates, like the displayed
        # objects, otherwise the surface is offset by the element
        # placement.
        self.geom_settings.set(self.geom_settings.USE_WORLD_COORDS, True)

    def run(self):
        self.display_items.clear()
        if self.top_or_bot_method == "Top":
            direction = (0.0, 0.0, 1)
        if self.top_or_bot_method == "Bottom":
            direction = (0.0, 0.0, -1)

        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.id)
                    result = clash_utils.get_extreme_faces_with_area(
                        geom, direction=direction
                    )

                    area = result["total_area"]

                    # The extreme faces, kept in the display registry.
                    # get_extreme_faces_with_area returns vertex indices,
                    # not displayable shapes: they are converted to the
                    # lightweight corner triangle, displayable by
                    # _item_shape.
                    vertices = get_vertices(geom)
                    for face in result["extrem_faces"]:
                        corners = tuple(vertices[face])
                        self.register_display_item(
                            "face", ("face", corners), (0.5,0,1), 0.2, element=entity
                        )

                    if self.surface_min < area < self.surface_max:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


class LateralSurface(RuleCheckOneObject):
    def __init__(self, source, surface_min, surface_max, direction, state="Final"):
        super().__init__(state, source)
        self.type = "LateralSurface"
        self.surface_max: float = surface_max
        self.surface_min: float = surface_min
        self.direction: float = direction
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):  # @todo Check if the result is trustworthy
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.id)
                    area = ifcopenshell.util.shape.get_side_area(
                        geom, direction=self.direction, angle=45
                    )

                    if self.surface_min < area < self.surface_max:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


class ProjectedSurface(RuleCheckOneObject):
    def __init__(self, source, surface_min, surface_max, direction, state="Final"):
        super().__init__(state, source)
        self.type = "Projected"
        self.surface_max: float = surface_max
        self.surface_min: float = surface_min
        self.direction: float = direction
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):  # @todo Check if the result is trustworthy
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.id)
                    area = ifcopenshell.util.shape.get_footprint_area(
                        geom, direction=self.direction
                    )

                    if self.surface_min < area < self.surface_max:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


class ObbHigh(RuleCheckOneObject):
    def __init__(self, source, length_min, length_max, state="Final"):
        super().__init__(state, source)
        self.type = "ObbHigh"
        self.length_max: float = length_max
        self.length_min: float = length_min
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.display_items.clear()
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)
                    obb = create_obb_from_TopoDs_Shape(geom)
                    corners = obb.get_corners()
                    min_z = corners[0].Z()
                    max_z = corners[0].Z()

                    for corner in corners:
                        min_z = min(min_z, corner.Z())
                        max_z = max(max_z, corner.Z())

                    value_to_check = max_z - min_z

                    # The OBB, kept in the display registry.
                    self.register_display_item(
                        "obb", obb, (0.5,0,1), 0.2, element=entity
                    )

                    if self.length_min < value_to_check < self.length_max:
                        result = ClashResultOneObject(source=entity, state=True)
                        result.info.add_source_obb(obb.to_data("object"))
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


class ObbLength(RuleCheckOneObject):
    def __init__(
        self, source, length_min, length_max, method: DIRECTION_METHOD, state="Final"
    ):
        super().__init__(state, source)
        self.type = "ObbLength"
        self.length_max: float = length_max
        self.length_min: float = length_min
        self.direction_method = method
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.display_items.clear()
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)
                    obb = create_obb_from_TopoDs_Shape(geom)

                    # The OBB, kept in the display registry.
                    self.register_display_item(
                        "obb", obb, (0.5,0,1), 0.2, element=entity
                    )

                    # L'axe vertical de la boite est son axe le plus
                    # vertical : l'ordre des axes de l'OBB est arbitraire
                    # dans le calcul OCC, l'axe Z n'est pas toujours la
                    # hauteur. Les deux autres axes portent les dimensions
                    # de plan de l'objet.
                    half_sizes = [obb.XHSize(), obb.YHSize(), obb.ZHSize()]
                    verticality = [
                        abs(obb.XDirection().Z()),
                        abs(obb.YDirection().Z()),
                        abs(obb.ZDirection().Z()),
                    ]
                    height_axis = max(range(3), key=lambda i: verticality[i])
                    plan_sizes = [
                        2.0 * half_sizes[i] for i in range(3) if i != height_axis
                    ]

                    # La plus grande (wide) ou la plus petite (narrow) des
                    # deux dimensions de plan. @todo Un objet incliné à
                    # environ 45 degrés n'a pas d'axe vertical net : le
                    # choix de l'axe hauteur reste arbitraire.
                    if self.direction_method.lower() == "wide":
                        value_to_check = max(plan_sizes)
                    else:
                        value_to_check = min(plan_sizes)

                    if self.length_min < value_to_check < self.length_max:
                        result = ClashResultOneObject(source=entity, state=True)
                        result.info.add_source_obb(obb.to_data("object"))
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


ORIENTATION_TYPE = Literal["Parrallel", "Perpendicular"]


class Orientation(RuleCheckOneObject):
    def __init__(
        self,
        source,
        orientation,
        orientation_type: ORIENTATION_TYPE,
        direction_method: DIRECTION_METHOD,
        angular_tolerance: float = 0.1,
        state="Final",
    ):
        # @todo We can set an East, North, etc orientation to check
        super().__init__(state, source)
        self.type = "Orientation"
        self.orientation: tuple[float, float, float] = orientation
        self.orientation_type: ORIENTATION_TYPE = orientation_type
        self.direction_method: DIRECTION_METHOD = direction_method
        self.angular_tolerance: float = angular_tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.display_items.clear()
        self.select_source.run()

        occ_orientation = gp_Dir(
            self.orientation[0], self.orientation[1], self.orientation[2]
        )

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)
                    obb = create_obb_from_TopoDs_Shape(geom)
                    dir1, dir2 = obb.get_two_main_direction_OBB_shape(
                        self.direction_method
                    )

                    is_parrallel = occ_orientation.IsParallel(
                        dir1, self.angular_tolerance
                    )

                    # The main direction of the OBB and the expected
                    # orientation, kept in the display registry.
                    center = self._shape_center(geom)
                    self.register_display_item(
                        "axis", ("axis", center, dir1, 0.5), (0.5,0,1), 0.2,
                        element=entity,
                    )
                    self.register_display_item(
                        "axis",
                        ("axis", center, occ_orientation, 0.5),
                        (0, 1, 0),
                        0.2,
                        element=entity,
                    )

                    if self.orientation_type == "Parrallel":
                        check_direction = is_parrallel
                    elif self.orientation_type == "Perpendicular":
                        check_direction = not is_parrallel

                    if check_direction:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


# ===== Two Objects Rule


class AngleBetween(RuleCheckTwoObjects):
    def __init__(
        self,
        source,
        target,
        direction_method_for_source: DIRECTION_METHOD,
        direction_method_for_target: DIRECTION_METHOD,
        angle_difference: float,
        angle_tolerance: float,
        state="Final",
    ):
        super().__init__(state, source, target)
        self.type = "AngleBetween"
        self.direction_method_for_source: DIRECTION_METHOD = direction_method_for_source
        self.direction_method_for_target: DIRECTION_METHOD = direction_method_for_target
        self.angle_difference: float = angle_difference
        self.angle_tolerance: float = angle_tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def _get_object_main_direction(self, geom, method):
        """Get the main direction of an object from its OBB using the specified method"""
        obb = create_obb_from_TopoDs_Shape(geom)
        dir1, dir2 = obb.get_two_main_direction_OBB_shape(method)
        return dir1

    def _calculate_angle_between_dir(self, dir1: gp_Dir, dir2: gp_Dir):
        """Calculate angle in degrees between two gp_Dir vectors and check if it matches the target angle within tolerance"""
        # Use OCC's Angle() method which returns angle in radians
        angle_rad = dir1.Angle(dir2)
        angle_deg = np.degrees(angle_rad)

        # Handle circular nature of angles and find smallest difference
        angle_diff = abs(angle_deg - self.angle_difference)
        angle_diff = min(angle_diff, 360 - angle_diff)

        return angle_diff <= self.angle_tolerance

    def run(self):
        self.display_items.clear()
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()
        self.select_target.run()

        # Collect source objects with their main directions
        source_objects = []
        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)
                    direction = self._get_object_main_direction(
                        geom, self.direction_method_for_source
                    )
                    source_objects.append({"entity": entity, "direction": direction})

                    # The main direction of the object, kept in the
                    # display registry.
                    self.register_display_item(
                        "axis",
                        ("axis", self._shape_center(geom), direction, 0.5),
                        (0.5,0,1),
                        0.2,
                        element=entity,
                    )

                    if not iterator.next():
                        break

        # Collect target objects with their main directions
        target_objects = []
        for ifc_file in self.select_target.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_target.dict_elements[ifc_file],
            )
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)
                    direction = self._get_object_main_direction(
                        geom, self.direction_method_for_target
                    )
                    target_objects.append({"entity": entity, "direction": direction})

                    # The main direction of the object, kept in the
                    # display registry.
                    self.register_display_item(
                        "axis",
                        ("axis", self._shape_center(geom), direction, 0.5),
                        (0.5,0,1),
                        0.2,
                        element=entity,
                    )
                    if not iterator.next():
                        break

        # Check all pairs for angle matches
        for source_obj in source_objects:
            for target_obj in target_objects:
                if self._calculate_angle_between_dir(
                    source_obj["direction"], target_obj["direction"]
                ):
                    result = ClashResultTwoObjects(
                        source=source_obj["entity"],
                        target=target_obj["entity"],
                        state=True,
                    )
                    self.result.append(result)

        if self.state == "Display_Input":
            return self.end_rule_action()

        self.end_rule_action()


class Intersection(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance=0.1, state="Final"):
        super().__init__(state, source, target)
        self.type = "Intersection"
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()
        self.select_target.run()

        source_elements = []
        target_elements = []

        self.add_to_tree(self.select_source, "BVH")
        self.add_to_tree(self.select_target, "BVH")

        for file in self.select_source.dict_elements.keys():
            list = self.select_source.dict_elements[file]
            for element in list:
                source_elements.append(element)

        for file in self.select_target.dict_elements.keys():
            list = self.select_target.dict_elements[file]
            for element in list:
                target_elements.append(element)

        temp_result = self.tree.clash_intersection_many(
            source_elements,
            target_elements,
            tolerance=self.tolerance,
            check_all=True,
        )

        list_result = []  # I need to do that to avoid reusing the same result result in the different intersection.

        # @todo make a proper integration, how to deal with extra data ? (Point of entry, distance, etc...)
        for result in temp_result:
            # ifcopenshell >= 0.9: a and b are entity wrappers owned by
            # the tree, re-resolved through the file for stability.
            a__object = clash_utils.clash_entity(result.a)
            b_object = clash_utils.clash_entity(result.b)

            # source and target are mixed up.
            if a__object in source_elements:
                source_object = a__object
                target_object = b_object
            else:
                source_object = b_object
                target_object = a__object

            list_result.append(
                ClashResultTwoObjects(
                    source=source_object, target=target_object, state=True
                )
            )

        self.result = list_result
        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


class Clearance(RuleCheckTwoObjects):
    # @todo create a max distance for clearance
    def __init__(self, source, target, clearance=0.05, state="Final"):
        super().__init__(state, source, target)

        self.type = "Clearance"
        self.geom_settings = ifcopenshell.geom.settings()
        self.clearance: float = clearance
        self.check_all: bool = False

    def run(self):
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()
        self.select_target.run()

        self.select_source.create_list_of_element()
        self.select_target.create_list_of_element()

        self.add_to_tree(self.select_source, "BVH")
        self.add_to_tree(self.select_target, "BVH")

        temp_result = self.tree.clash_clearance_many(
            self.select_source.list_of_elements,
            self.select_target.list_of_elements,
            clearance=self.clearance,
            check_all=self.check_all,
        )

        self.result = []  # I need to do that to avoid reusing the same result result in the different intersection.

        # @todo make a proper integration, how to deal with extra data ? (Point of entry, distance, etc...)
        for result in temp_result:
            # ifcopenshell >= 0.9: a and b are entity wrappers owned by
            # the tree, re-resolved through the file for stability.
            a__object = clash_utils.clash_entity(result.a)
            b_object = clash_utils.clash_entity(result.b)

            # source and target are mixed up.
            if a__object in self.select_source.list_of_elements:
                source_object = a__object
                target_object = b_object
            else:
                source_object = b_object
                target_object = a__object

            self.result.append(
                ClashResultTwoObjects(
                    source=source_object, target=target_object, state=True
                )
            )

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


class ClearanceAxisToAxis(RuleCheckTwoObjects):
    """Check the axis-to-axis distance of two linear objects against an
    interval.

    The axis of an object is the long dimension of its OBB passing
    through the centroid, truncated at the OBB extents: the support
    segment of a linear object (pipe, duct, cable tray run). The rule
    measures the distance between the two axes and clashes when the
    measured distance leaves the interval [min, max] widened by the
    tolerance: "too close" and "too far" (coverage holes) alike.

    Two measurement modes. Perpendicular: the offset between the
    support lines of two objects running side by side (a fixed
    spacing of a tray bundle) — the offset is only meaningful for
    quasi-parallel axes, so a non-parallel pair automatically falls
    back to the minimum distance between the finite segments.
    MinDistance: always the minimum distance between the segments,
    which covers the lateral misalignment of a connection and the
    end-to-end gap of two runs butted end to end.

    An object whose OBB is not slender enough (linearity ratio below
    linearity_ratio, e.g. an elbow) is not linear: the pair is
    skipped, or measured skin to skin (the Fallback of on_non_linear)
    and the result then carries the degraded flag.

    This is the axis counterpart of Clearance, which measures skin to
    skin: the execution dimensions and the regulatory spacings of a
    network are expressed axis to axis, whatever the diameters. The
    directional condition (parallelism) is not tested here: combine
    it with AngleBetween through an exception for a full coaxiality.
    See doc/2ObjectsRules/ClearanceAxisToAxis.md.
    """

    def __init__(
        self,
        source,
        target,
        mode="Perpendicular",
        min_distance=None,
        max_distance=None,
        tolerance=0.0,
        linearity_ratio=10.0,
        on_non_linear="Skip",
        parallel_tolerance=1.0,
        state="Final",
    ):
        super().__init__(state, source, target)
        self.type = "ClearanceAxisToAxis"

        if mode not in ("Perpendicular", "MinDistance"):
            raise ValueError(
                f"mode must be 'Perpendicular' or 'MinDistance', got {mode!r}"
            )
        for bound_name, bound_value in (
            ("min_distance", min_distance),
            ("max_distance", max_distance),
        ):
            if bound_value is not None and (
                not isinstance(bound_value, (int, float)) or bound_value < 0
            ):
                raise ValueError(
                    f"{bound_name} must be None or a positive number (m), "
                    f"got {bound_value!r}"
                )
        if min_distance is None and max_distance is None:
            raise ValueError("at least one of min_distance or max_distance must be set")
        if (
            min_distance is not None
            and max_distance is not None
            and min_distance > max_distance
        ):
            raise ValueError(
                f"min_distance ({min_distance}) must not exceed "
                f"max_distance ({max_distance})"
            )
        if not isinstance(tolerance, (int, float)) or tolerance < 0:
            raise ValueError(
                f"tolerance must be a positive number (m), got {tolerance!r}"
            )
        if not isinstance(linearity_ratio, (int, float)) or linearity_ratio < 1.0:
            raise ValueError(
                f"linearity_ratio must be a number >= 1, got {linearity_ratio!r}"
            )
        if on_non_linear not in ("Skip", "Fallback"):
            raise ValueError(
                f"on_non_linear must be 'Skip' or 'Fallback', got {on_non_linear!r}"
            )
        if (
            not isinstance(parallel_tolerance, (int, float))
            or not 0.0 < parallel_tolerance <= 90.0
        ):
            raise ValueError(
                f"parallel_tolerance must be in (0, 90] degrees, "
                f"got {parallel_tolerance!r}"
            )

        self.mode = mode
        self.min_distance = float(min_distance) if min_distance is not None else None
        self.max_distance = float(max_distance) if max_distance is not None else None
        self.tolerance = float(tolerance)
        self.linearity_ratio = float(linearity_ratio)
        self.on_non_linear = on_non_linear
        self.parallel_tolerance = float(parallel_tolerance)

        # The axes and the fallback distances come from the world
        # TopoDS shapes of the objects.
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set("USE_WORLD_COORDS", True)
        self.geom_settings.set("USE_PYTHON_OPENCASCADE", True)

    def _collect_axes(self, select):
        """The axis data of every selected object.

        Each object carries its entity, its TopoDS shape (for the
        skin-to-skin fallback) and the center, the unit direction, the
        half length and the linearity ratio of its OBB long axis.
        """
        objects = []
        for ifc_file in select.dict_elements.keys():
            included = select.dict_elements[ifc_file]
            if not included:
                continue

            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=included,
            )
            if not iterator.initialize():
                continue

            while True:
                shape = iterator.get()
                geom = shape.geometry
                entity = ifc_file.by_id(shape.data.id)
                obb = create_obb_from_TopoDs_Shape(geom)
                center, direction, half_length, thickness = clash_utils.obb_long_axis(
                    obb
                )
                objects.append(
                    {
                        "entity": entity,
                        "geom": geom,
                        "center": center,
                        "direction": direction,
                        "half_length": half_length,
                        "linearity": (
                            2.0 * half_length / thickness
                            if thickness > 1e-9
                            else float("inf")
                        ),
                    }
                )
                if not iterator.next():
                    break

        return objects

    def _outside_interval(self, distance):
        """Whether a measured distance leaves the interval widened by
        the tolerance."""
        if (
            self.min_distance is not None
            and distance < self.min_distance - self.tolerance
        ):
            return True
        if (
            self.max_distance is not None
            and distance > self.max_distance + self.tolerance
        ):
            return True
        return False

    @staticmethod
    def _skin_distance(geom_1, geom_2):
        """The classical skin-to-skin distance between two shapes, with
        the closest point of each shape."""
        distance_tool = BRepExtrema_DistShapeShape(geom_1, geom_2)
        distance_tool.Perform()
        if distance_tool.IsDone() and distance_tool.NbSolution() >= 1:
            point_1 = distance_tool.PointOnShape1(1)
            point_2 = distance_tool.PointOnShape2(1)
            return (
                float(distance_tool.Value()),
                (point_1.X(), point_1.Y(), point_1.Z()),
                (point_2.X(), point_2.Y(), point_2.Z()),
            )
        return float(distance_tool.Value()), None, None

    def run(self):
        self.display_items.clear()
        self.select_source.run()
        self.select_target.run()

        source_objects = self._collect_axes(self.select_source)
        target_objects = self._collect_axes(self.select_target)

        # The support segments (the axes), kept in the display
        # registry: center +/- direction * half length.
        for objects, color in (
            (source_objects, (0.5,0,1)),
            (target_objects, (0.5,0,1)),
        ):
            for one_object in objects:
                direction = one_object["direction"]
                self.register_display_item(
                    "axis",
                    (
                        "edge",
                        one_object["center"] - direction * one_object["half_length"],
                        one_object["center"] + direction * one_object["half_length"],
                    ),
                    color,
                    0.2,
                    element=one_object["entity"],
                )

        for source_obj in source_objects:
            for target_obj in target_objects:
                if source_obj["entity"] == target_obj["entity"]:
                    continue

                linear = (
                    source_obj["linearity"] >= self.linearity_ratio
                    and target_obj["linearity"] >= self.linearity_ratio
                )

                angle = clash_utils.axis_angle(
                    source_obj["direction"], target_obj["direction"]
                )

                if linear:
                    if (
                        self.mode == "Perpendicular"
                        and angle <= self.parallel_tolerance
                    ):
                        distance, source_point, target_point = (
                            clash_utils.parallel_line_offset_closest(
                                source_obj["center"],
                                source_obj["direction"],
                                target_obj["center"],
                                target_obj["direction"],
                            )
                        )
                        source_point = tuple(float(v) for v in source_point)
                        target_point = tuple(float(v) for v in target_point)
                        mode_used = "Perpendicular"
                    else:
                        # The support segment spans the full OBB
                        # extent of the axis: center ± half length.
                        distance, source_point, target_point = (
                            clash_utils.segment_segment_closest(
                                source_obj["center"]
                                - source_obj["direction"] * source_obj["half_length"],
                                source_obj["center"]
                                + source_obj["direction"] * source_obj["half_length"],
                                target_obj["center"]
                                - target_obj["direction"] * target_obj["half_length"],
                                target_obj["center"]
                                + target_obj["direction"] * target_obj["half_length"],
                            )
                        )
                        source_point = tuple(float(v) for v in source_point)
                        target_point = tuple(float(v) for v in target_point)
                        mode_used = "MinDistance"
                    degraded = False
                elif self.on_non_linear == "Skip":
                    continue
                else:
                    distance, source_point, target_point = self._skin_distance(
                        source_obj["geom"], target_obj["geom"]
                    )
                    mode_used = "Fallback"
                    degraded = True

                if self._outside_interval(distance):
                    result = ClashResultTwoObjects(
                        source=source_obj["entity"],
                        target=target_obj["entity"],
                        state=True,
                    )
                    result.info.distance = distance  # m — mesure nominale
                    result.info.angle = angle  # deg — mesure secondaire
                    if source_point is not None and target_point is not None:
                        result.info.add_point_pair(source_point, target_point)
                    result.info.axis_mode = mode_used
                    result.info.axis_degraded = degraded
                    self.result.append(result)

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


class Collision(RuleCheckTwoObjects):
    def __init__(self, source, target, allow_touching=False, state="Final"):
        super().__init__(state, source, target)
        self.type = "Collision"
        self.allow_touching = allow_touching
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()
        self.select_target.run()

        self.select_source.create_list_of_element()
        self.select_target.create_list_of_element()

        self.add_to_tree(self.select_source, "BVH")
        self.add_to_tree(self.select_target, "BVH")

        temp_result = self.tree.clash_collision_many(
            self.select_source.list_of_elements,
            self.select_target.list_of_elements,
            allow_touching=self.allow_touching,
        )

        self.result = []

        for result in temp_result:
            # ifcopenshell >= 0.9: a and b are entity wrappers owned by
            # the tree, re-resolved through the file for stability.
            a__object = clash_utils.clash_entity(result.a)
            b_object = clash_utils.clash_entity(result.b)

            # source and target are mixed up.
            if a__object in self.select_source.list_of_elements:
                source_object = a__object
                target_object = b_object
            else:
                source_object = b_object
                target_object = a__object

            self.result.append(
                ClashResultTwoObjects(
                    source=source_object, target=target_object, state=True
                )
            )

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


class Ray_Check(RuleCheckTwoObjects):
    def __init__(self, source, target, context, max_ray_length, state="Final"):
        super().__init__(state, source, target)
        self.type = "RayCheck"
        self.select_context: Select = context
        self.max_ray_length: float = max_ray_length
        self.geom_settings = ifcopenshell.geom.settings()

    def _get_elements_centers(self, select: Select, geom_settings):
        """Compute the center of the bounding box of each selected element,
        in world coordinates, as a dict {entity: (x, y, z)}"""
        centers = {}
        for ifc_file in select.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=select.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    verts = np.array(shape.geometry.verts).reshape(-1, 3)
                    entity = ifc_file.by_id(shape.id)
                    centers[entity] = (verts.min(axis=0) + verts.max(axis=0)) / 2.0
                    if not iterator.next():
                        break
        return centers

    def _context_shapes(self):
        """The OCC shape of every context element, in world
        coordinates, keyed by entity.

        The elements without geometry are skipped, as the geometry
        iterator skipped them.
        """
        shapes = {}
        shape_settings = ifcopenshell.geom.settings()
        shape_settings.set("USE_PYTHON_OPENCASCADE", True)

        for elements in self.select_context.dict_elements.values():
            for element in elements or []:
                try:
                    shape = ifcopenshell.geom.create_shape(shape_settings, element)
                except Exception:
                    continue
                shapes[element] = shape.geometry
        return shapes

    def _segment_blocked(self, start, end, source, target, context_shapes):
        """True when a context object (other than the two objects of
        the pair) touches or crosses the start-end segment.

        The blocking test is an exact segment intersection against
        the context shapes: on ifcopenshell 0.9.0, tree.select_ray can
        no longer resolve the hit entity (upstream issue #9755).
        """
        for entity, shape in context_shapes.items():
            if entity == source or entity == target:
                # The source and the target never block their own ray
                continue
            if clash_utils.segment_hits_shape(start, end, shape):
                return True
        return False

    def run(self):
        self.display_items.clear()
        self.select_source.run()
        self.select_target.run()

        self.select_context.list_ifc_path = self.select_source.list_ifc_path
        self.select_context.list_ifc_file = self.select_source.list_ifc_file
        self.select_context.run()

        # The context elements, kept in the display registry.
        for elements in self.select_context.dict_elements.values():
            for element in elements or []:
                self.register_display_item(
                    "context", ("entity", element), (0.5, 0.5, 0.5), 0.9
                )

        self.select_source.create_list_of_element()
        self.select_target.create_list_of_element()
        self.select_context.create_list_of_element()

        # The context shapes in world coordinates, for the blocking
        # test of each ray.
        context_shapes = self._context_shapes()

        # The ray is cast between the centers of the objects, not between
        # their placement origins: the origins often lie on the floor plane,
        # where select_ray cannot detect the context faces grazed by the ray
        # (faces coplanar with the ray, intersections on face edges).
        center_settings = ifcopenshell.geom.settings()
        center_settings.set(center_settings.USE_WORLD_COORDS, True)
        source_centers = self._get_elements_centers(self.select_source, center_settings)
        target_centers = self._get_elements_centers(self.select_target, center_settings)

        for source in self.select_source.list_of_elements:
            for target in self.select_target.list_of_elements:
                if source == target:
                    # It's the same object
                    continue

                if source not in source_centers or target not in target_centers:
                    # One of the objects has no geometry
                    continue

                source_position = tuple(float(x) for x in source_centers[source])
                target_position = tuple(float(x) for x in target_centers[target])
                direction = np.array(target_position) - np.array(source_position)
                distance = np.linalg.norm(direction)

                if distance == 0:
                    # It's the same object
                    continue

                if distance > self.max_ray_length:
                    # The two objects are too far away from each other
                    continue

                direction = (
                    float(direction[0] / distance),
                    float(direction[1] / distance),
                    float(direction[2] / distance),
                )

                # The clash appears when the source and the target are in
                # direct view: no context object stands between them.
                if self._segment_blocked(
                    source_position,
                    target_position,
                    source,
                    target,
                    context_shapes,
                ):
                    continue

                self.result.append(
                    ClashResultTwoObjects(source=source, target=target, state=True)
                )

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()


ABOVE_TYPE = Literal[
    "Above_MinToMax", "Above_MinToMin", "Above_MaxToMin", "Above_MaxToMax"
]

BELOW_TYPE = Literal[
    "Below_MinToMax", "Below_MinToMin", "Below_MaxToMin", "Below_MaxToMax"
]


class Above(RuleCheckTwoObjects):
    def __init__(
        self, source, target, above_type: ABOVE_TYPE, tolerance=0.1, state="Final"
    ):
        super().__init__(state, source, target)
        self.type = above_type
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.display_items.clear()
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()
        self.select_target.run()

        sources_data = []
        targets_data = []

        if "MinTo" in self.type:
            source_direction = gp_Dir(0.0, 0.0, -1.0)
        else:
            source_direction = gp_Dir(0.0, 0.0, 1.0)

        if "ToMin" in self.type:
            target_direction = gp_Dir(0.0, 0.0, -1.0)
        else:
            target_direction = gp_Dir(0.0, 0.0, 1.0)

        # Check the extrem face of the source
        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)

                    obb = create_obb_from_TopoDs_Shape(geom)
                    clash_obb = obb.detach_top_by_extrude(self.tolerance)

                    #@todo Implement a fonction to determine the number of faces that are toward the direction. We need to have at least the same number of ray.

                    extrem_faces = (
                        clash_utils.get_faces_visible_from_direction_with_plane(
                            shape=geom, direction=source_direction
                        )
                    )

                    # The extreme faces, kept in the display registry.
                    for face in extrem_faces["visible_faces"]:
                        self.register_display_item(
                            "face", face, (0.5,0,1), 0.2, element=entity
                        )

                    dict = {
                        "entity": entity,
                        "extrem_faces": extrem_faces["visible_faces"],
                        "obb": clash_obb,
                    }
                    sources_data.append(dict)

                    if not iterator.next():
                        break

        # Check the extrem face of the target
        for ifc_file in self.select_target.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_target.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)

                    obb = create_obb_from_TopoDs_Shape(geom)
                    extrem_faces = (
                        clash_utils.get_faces_visible_from_direction_with_plane(
                            shape=geom, direction=target_direction
                        )
                    )

                    # The extreme faces, kept in the display registry.
                    for face in extrem_faces["visible_faces"]:
                        self.register_display_item(
                            "face", face, (0.5,0,1), 0.2, element=entity
                        )

                    dict = {
                        "entity": entity,
                        "extrem_faces": extrem_faces["visible_faces"],
                        "obb": obb,
                    }
                    targets_data.append(dict)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()
        # Check if part of extrem faces are close to each other
        for source in sources_data:
            flag_is_above = False
            source_globalid = str(source["entity"].GlobalId)

            for target in targets_data:
                target_globalid = target["entity"].GlobalId

                if source["obb"].IsOut(target["obb"]):
                    continue

                source_geom = source["extrem_faces"]
                target_geom = target["extrem_faces"]

                result = self._check_distance(source_geom, target_geom)

                if result["is_above"] == "Right_Above":
                    self.result.append(
                        ClashResultTwoObjects(
                            source=source["entity"],
                            target=target["entity"],
                            state=True,
                        )
                    )
                    continue
                if result["is_above"] == "Too_Far":
                    continue

                pair_detected = False
                for source_face in source_geom:
                    if pair_detected:
                        break
                    for point_on_target in result["list_of_point_on_target"]:
                        bottom_direction = gp_Dir(0.0, 0.0, -1.0)
                        ray = gp_Lin(point_on_target, bottom_direction)

                        # Trouver les intersections avec la shape
                        inter = BRepIntCurveSurface_Inter()
                        inter.Init(source_face, ray, 1e-7)

                        if inter.More():
                            self.result.append(
                                ClashResultTwoObjects(
                                    source=source["entity"],
                                    target=target["entity"],
                                    state=True,
                                )
                            )
                            pair_detected = True
                            break

        self.end_rule_action()

    def _check_distance(self, list_of_source_face, list_of_target_face):
        dict_to_return = {"is_above": None, "list_of_point_on_target": []}
        for source_face in list_of_source_face:
            for target_face in list_of_target_face:
                dist_tool = BRepExtrema_DistShapeShape()
                dist_tool.LoadS1(source_face)
                dist_tool.LoadS2(target_face)
                dist_tool.Perform()
                distance = dist_tool.Value()

                # If they touch (distance <= tolerance), it's close enough to check if the face is exactly above.
                if distance <= self.tolerance:
                    # We check if the target point is exactly above the source point.
                    # OCC solutions are indexed from 1 to NbSolution() inclusive.
                    for i in range(1, dist_tool.NbSolution() + 1):
                        pt_source = dist_tool.PointOnShape1(i)
                        pt_target = dist_tool.PointOnShape2(i)

                        if pt_source.Z() > pt_target.Z():
                            continue

                        if abs(pt_source.X() - pt_target.X()) < 1e-3:
                            if abs(pt_source.Y() - pt_target.Y()) < 1e-3:
                                dict_to_return["is_above"] = "Right_Above"
                                return dict_to_return

                        dict_to_return["list_of_point_on_target"].append(pt_target)

        if dict_to_return["list_of_point_on_target"] == []:
            dict_to_return["is_above"] = "Too_Far"
        else:
            dict_to_return["is_above"] = "Need_More_Check"

        return dict_to_return


class Below(RuleCheckTwoObjects):
    def __init__(
        self, source, target, below_type: BELOW_TYPE, tolerance=0.1, state="Final"
    ):
        super().__init__(state, source, target)
        self.type = below_type
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.display_items.clear()
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()
        self.select_target.run()

        sources_data = []
        targets_data = []

        if "MinTo" in self.type:
            source_direction = gp_Dir(0.0, 0.0, -1.0)
        else:
            source_direction = gp_Dir(0.0, 0.0, 1.0)

        if "ToMin" in self.type:
            target_direction = gp_Dir(0.0, 0.0, -1.0)
        else:
            target_direction = gp_Dir(0.0, 0.0, 1.0)

        # Check the extrem face of the source
        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)

                    obb = create_obb_from_TopoDs_Shape(geom)
                    clash_obb = obb.detach_bottom_by_extrude(self.tolerance)

                    extrem_faces = (
                        clash_utils.get_faces_visible_from_direction_with_plane(
                            shape=geom, direction=source_direction
                        )
                    )

                    # The extreme faces, kept in the display registry.
                    for face in extrem_faces["visible_faces"]:
                        self.register_display_item(
                            "face", face, (0.5,0,1), 0.2, element=entity
                        )

                    dict = {
                        "entity": entity,
                        "extrem_faces": extrem_faces["visible_faces"],
                        "obb": clash_obb,
                    }
                    sources_data.append(dict)

                    if not iterator.next():
                        break

        # Check the extrem face of the target
        for ifc_file in self.select_target.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_target.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)

                    obb = create_obb_from_TopoDs_Shape(geom)
                    extrem_faces = (
                        clash_utils.get_faces_visible_from_direction_with_plane(
                            shape=geom, direction=target_direction
                        )
                    )

                    # The extreme faces, kept in the display registry.
                    for face in extrem_faces["visible_faces"]:
                        self.register_display_item(
                            "face", face, (0.5,0,1), 0.2, element=entity
                        )

                    dict = {
                        "entity": entity,
                        "extrem_faces": extrem_faces["visible_faces"],
                        "obb": obb,
                    }
                    targets_data.append(dict)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()

        # Check if part of extrem faces are close to each other
        for source in sources_data:
            for target in targets_data:
                if source["obb"].IsOut(target["obb"]):
                    continue

                source_geom = source["extrem_faces"]
                target_geom = target["extrem_faces"]

                result = self._check_distance(source_geom, target_geom)

                if result["is_below"] == "Right_Below":
                    self.result.append(
                        ClashResultTwoObjects(
                            source=source["entity"],
                            target=target["entity"],
                            state=True,
                        )
                    )
                    continue
                if result["is_below"] == "Too_Far":
                    continue

                pair_detected = False
                for source_face in source_geom:
                    if pair_detected:
                        break
                    for point_on_target in result["list_of_point_on_target"]:
                        bottom_direction = gp_Dir(0.0, 0.0, 1.0)
                        ray = gp_Lin(point_on_target, bottom_direction)

                        # Trouver les intersections avec la shape
                        inter = BRepIntCurveSurface_Inter()
                        inter.Init(source_face, ray, 1e-7)

                        if inter.More():
                            self.result.append(
                                ClashResultTwoObjects(
                                    source=source["entity"],
                                    target=target["entity"],
                                    state=True,
                                )
                            )
                            pair_detected = True
                            break

        self.end_rule_action()

    def _check_distance(self, list_of_source_face, list_of_target_face):
        dict_to_return = {"is_below": None, "list_of_point_on_target": []}
        for source_face in list_of_source_face:
            for target_face in list_of_target_face:
                dist_tool = BRepExtrema_DistShapeShape()
                dist_tool.LoadS1(source_face)
                dist_tool.LoadS2(target_face)
                dist_tool.Perform()
                distance = dist_tool.Value()

                # If they touch (distance <= tolerance), it's close enough to check if the face is exactly above.
                if distance <= self.tolerance:
                    # We check if the target point is exactly above the source point.
                    for i in range(1, dist_tool.NbSolution()+1):
                        pt_source = dist_tool.PointOnShape1(i)
                        pt_target = dist_tool.PointOnShape2(i)

                        if pt_source.Z() < pt_target.Z():
                            continue

                        if abs(pt_source.X() - pt_target.X()) < 1e-3:
                            if abs(pt_source.Y() - pt_target.Y()) < 1e-3:
                                dict_to_return["is_below"] = "Right_Below"
                                return dict_to_return

                        dict_to_return["list_of_point_on_target"].append(pt_target)

        if dict_to_return["list_of_point_on_target"] == []:
            dict_to_return["is_below"] = "Too_Far"
        else:
            dict_to_return["is_below"] = "Need_More_Check"

        return dict_to_return



class Template(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance=0.1, state="Final"):
        super().__init__(state, source, target)
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings(USE_WORLD_COORDS=False)

    def run(self):
        self.end_rule_action()


class OBB_Above(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance, state="Final"):
        super().__init__(state, source, target)
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.display_items.clear()
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()
        self.select_target.run()

        # Create OBBs for source objects (these serve as detection zones)
        source_geoms = []
        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)

                    # Create OBB for the source object (detection zone)
                    obb = create_obb_from_TopoDs_Shape(geom)  # Why not use
                    clash_obb = obb.detach_top_by_extrude(self.tolerance)

                    # The detection zone, kept in the display registry.
                    self.register_display_item(
                        "obb", clash_obb, (0.5,0,1), 0.2, element=entity
                    )

                    compound = clash_obb.to_TopoDS_Solid()
                    source_geoms.append(
                        {
                            "entity": entity,
                            "geom": compound,
                            "obb": clash_obb,
                            "base_obb": obb,
                        }
                    )

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()
        # Get target geometries
        target_geoms = []
        for ifc_file in self.select_target.dict_elements.keys():
            # self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE,True)
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_target.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)
                    obb = create_obb_from_TopoDs_Shape(geom)
                    target_geoms.append({"entity": entity, "geom": geom, "obb": obb})

                    if not iterator.next():
                        break

        # Check for clashes between source OBBs (detection zones) and target geometries
        for source_data in source_geoms:
            for target_data in target_geoms:
                if source_data["obb"].IsOut(target_data["obb"]):
                    continue

                source_geom = source_data["geom"]
                target_geom = target_data["geom"]

                # Calculate distance between OBB and geometry
                dist_tool = BRepExtrema_DistShapeShape()
                dist_tool.LoadS1(source_geom)
                dist_tool.LoadS2(target_geom)
                dist_tool.Perform()
                distance = dist_tool.Value()

                # If they touch (distance <= tolerance) and target is above source, it's a clash
                if distance <= 1e-6:
                    result = ClashResultTwoObjects(
                        source=source_data["entity"],
                        target=target_data["entity"],
                        state=True,
                    )
                    result.info.add_source_obb(source_data["obb"].to_data("zone"))
                    result.info.add_source_obb(
                        source_data["base_obb"].to_data("object")
                    )
                    result.info.add_target_obb(target_data["obb"].to_data("object"))
                    self.result.append(result)
        self.end_rule_action()



class OBB_Below(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance, state="Final"):
        super().__init__(state, source, target)
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.display_items.clear()
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()
        self.select_target.run()

        # Create OBBs for source objects (these serve as detection zones)
        source_geoms = []
        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)

                    # Create OBB for the source object (detection zone)
                    obb = create_obb_from_TopoDs_Shape(geom)
                    clash_obb = obb.detach_bottom_by_extrude(self.tolerance)

                    # The detection zone, kept in the display registry.
                    self.register_display_item(
                        "obb", clash_obb, (0.5,0,1), 0.2, element=entity
                    )

                    compound = clash_obb.to_TopoDS_Solid()
                    source_geoms.append(
                        {
                            "entity": entity,
                            "geom": compound,
                            "obb": clash_obb,
                            "base_obb": obb,
                        }
                    )

                    if not iterator.next():
                        break
        if self.state == "Display_Input":
            return self.end_rule_action()
        # Get target geometries
        target_geoms = []
        for ifc_file in self.select_target.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_target.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)
                    obb = create_obb_from_TopoDs_Shape(geom)
                    target_geoms.append({"entity": entity, "geom": geom, "obb": obb})

                    if not iterator.next():
                        break

        # Check for clashes between source OBBs (detection zones) and target geometries
        for source_data in source_geoms:
            for target_data in target_geoms:
                if source_data["obb"].IsOut(target_data["obb"]):
                    continue

                the_source_geom = source_data["geom"]
                the_target_geom = target_data["geom"]

                # Calculate distance between OBB and geometry
                dist_tool = BRepExtrema_DistShapeShape()
                dist_tool.LoadS1(the_source_geom)
                dist_tool.LoadS2(the_target_geom)
                dist_tool.Perform()
                distance = dist_tool.Value()

                # If they touch (distance <= tolerance), it's a clash.
                if distance <= 1e-6:
                    result = ClashResultTwoObjects(
                        source=source_data["entity"],
                        target=target_data["entity"],
                        state=True,
                    )
                    result.info.add_source_obb(source_data["obb"].to_data("zone"))
                    result.info.add_source_obb(
                        source_data["base_obb"].to_data("object")
                    )
                    result.info.add_target_obb(target_data["obb"].to_data("object"))
                    self.result.append(result)
        self.end_rule_action()



class OBB_Front_And_Back(RuleCheckTwoObjects):
    def __init__(
        self, source, target, tolerance, method: DIRECTION_METHOD, state="Final"
    ):
        super().__init__(state, source, target)
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)
        self.direction_method = method

    def run(self):
        self.display_items.clear()
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()
        self.select_target.run()

        # Create OBBs for source objects (these serve as detection zones)
        source_obbs = []
        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)

                    # Create OBB for the source object (detection zone)
                    obb = create_obb_from_TopoDs_Shape(
                        geom
                    )  # It's the old way, but it can create face that are toward Z.
                    # obb =create_obb_with_fixed_z(geom)

                    main_directions = obb.get_two_main_direction_OBB_shape(
                        self.direction_method, True
                    )

                    clash_obb_1 = obb.detach_side_by_extrude(
                        main_directions[0], self.tolerance
                    )
                    clash_obb_2 = obb.detach_side_by_extrude(
                        main_directions[1], self.tolerance
                    )

                    # The detection zones, kept in the display registry.
                    self.register_display_item(
                        "obb", clash_obb_1, (0.5,0,1), 0.2, element=entity
                    )
                    self.register_display_item(
                        "obb", clash_obb_2, (0.5,0,1), 0.2, element=entity
                    )

                    compound_1 = clash_obb_1.to_TopoDS_Solid()
                    compound_2 = clash_obb_2.to_TopoDS_Solid()
                    source_obbs.append(
                        {
                            "entity": entity,
                            "geom": compound_1,
                            "obb": clash_obb_1,
                            "base_obb": obb,
                        }
                    )
                    source_obbs.append(
                        {
                            "entity": entity,
                            "geom": compound_2,
                            "obb": clash_obb_2,
                            "base_obb": obb,
                        }
                    )

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()

        # Get target geometries
        target_geoms = []
        for ifc_file in self.select_target.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_target.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)
                    obb = create_obb_from_TopoDs_Shape(geom)
                    target_geoms.append({"entity": entity, "geom": geom, "obb": obb})

                    if not iterator.next():
                        break

        # Check for clashes between source OBBs (detection zones) and target geometries
        for source_data in source_obbs:
            for target_data in target_geoms:
                if source_data["obb"].IsOut(target_data["obb"]):
                    continue
                # Calculate distance between OBB and geometry
                dist_tool = BRepExtrema_DistShapeShape()
                dist_tool.LoadS1(source_data["geom"])
                dist_tool.LoadS2(target_data["geom"])
                dist_tool.Perform()
                distance = dist_tool.Value()

                # If they touch (distance <= tolerance) and target is above source, it's a clash
                if distance <= 1e-6:
                    result = ClashResultTwoObjects(
                        source=source_data["entity"],
                        target=target_data["entity"],
                        state=True,
                    )
                    result.info.add_source_obb(source_data["obb"].to_data("zone"))
                    result.info.add_source_obb(
                        source_data["base_obb"].to_data("object")
                    )
                    result.info.add_target_obb(target_data["obb"].to_data("object"))
                    self.result.append(result)

        self.end_rule_action()



class OBB_Custom(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance, state="Final"):
        super().__init__(state, source, target)
        self.list_of_modifications: list[str] = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.display_items.clear()
        self.tree = clash_utils.make_clash_tree()
        self.select_source.run()
        self.select_target.run()

        # Create OBBs for source objects (these serve as detection zones)
        source_geoms = []
        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)

                    base_obb = create_obb_from_TopoDs_Shape(geom)
                    for clash_obb in self._create_list_of_obb(geom, base_obb):
                        compound = clash_obb.to_TopoDS_Solid()
                        source_geoms.append(
                            {
                                "entity": entity,
                                "geom": compound,
                                "obb": clash_obb,
                                "base_obb": base_obb,
                            }
                        )

                        # The detection zones, kept in the display
                        # registry.
                        self.register_display_item(
                            "obb", clash_obb, (0.5,0,1), 0.2, element=entity
                        )

                    if not iterator.next():
                        break

        # Get target geometries
        target_geoms = []
        for ifc_file in self.select_target.dict_elements.keys():
            # self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE,True)
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_target.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.data.id)
                    obb = create_obb_from_TopoDs_Shape(geom)
                    target_geoms.append({"entity": entity, "geom": geom, "obb": obb})

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            return self.end_rule_action()

        # Check for clashes between source OBBs (detection zones) and target geometries
        for source_data in source_geoms:
            for target_data in target_geoms:
                if source_data["obb"].IsOut(target_data["obb"]):
                    continue

                source_geom = source_data["geom"]
                target_geom = target_data["geom"]

                # Calculate distance between OBB and geometry
                dist_tool = BRepExtrema_DistShapeShape()
                dist_tool.LoadS1(source_geom)
                dist_tool.LoadS2(target_geom)
                dist_tool.Perform()
                distance = dist_tool.Value()

                # If they touch (distance <= tolerance) and target is above source, it's a clash
                if distance <= 1e-6:
                    result = ClashResultTwoObjects(
                        source=source_data["entity"],
                        target=target_data["entity"],
                        state=True,
                    )
                    result.info.add_source_obb(source_data["obb"].to_data("zone"))
                    result.info.add_source_obb(
                        source_data["base_obb"].to_data("object")
                    )
                    result.info.add_target_obb(target_data["obb"].to_data("object"))
                    self.result.append(result)
        self.end_rule_action()

    def _create_list_of_obb(self, geom, base_obb=None):

        # expand_sides
        # detach_top_by_extrude
        # detach_bottom_by_extrude
        # extend_up
        # extend_down
        # NEW_OBB
        obb = (
            base_obb
            if base_obb is not None
            else create_obb_from_TopoDs_Shape(geom)
        )

        list_of_obb = []

        for one_modification in self.list_of_modifications:
            if "expand_sides" in one_modification:
                value = one_modification.split(":")[1]
                obb = obb.expand_sides(value)
                continue

            if "detach_top_by_extrude" in one_modification:
                value = one_modification.split(":")[1]
                obb = obb.detach_top_by_extrude(value)
                continue

            if "detach_bottom_by_extrude" in one_modification:
                value = one_modification.split(":")[1]
                obb = obb.detach_bottom_by_extrude(value)
                continue

            if "extend_up" in one_modification:
                value = one_modification.split(":")[1]
                obb = obb.extend_up(value)
                continue

            if "extend_down" in one_modification:
                value = one_modification.split(":")[1]
                obb = obb.extend_down(value)
                continue

            if "NEW_OBB" in one_modification:
                list_of_obb.append(obb)
                obb = create_obb_from_TopoDs_Shape(geom)

        list_of_obb.append(obb)

        return list_of_obb


# ===== Complex Rule
class Alignement(RuleCheckOneObject):
    """Check that the objects of a set are aligned.

    The alignment is tested on the length axis of the OBB of each object
    (the largest non-vertical axis: the object is taken along its
    length, its plan projection is the largest possible), not on
    points. The rule searches the alignment groups of the set:
    each group gathers the objects lying on one common fitted line (or
    plane), an object being allowed to belong to several groups. A group
    with at least Min_Group members is a valid alignment, and an object
    belonging to no valid group raises a clash. A single global element
    is still fitted on the whole set, only to report the offset of the
    clashing objects (a guidance value for the correction).
    See doc/ComplexRules/Alignement.md.
    """

    # An axis within 45 degrees of the global Z counts as vertical when
    # the orientation is auto-detected.
    VERTICAL_COSINE = math.cos(math.radians(45))

    # A footprint is directional when its length reaches this multiple
    # of its width. A compact footprint (a column) carries no plan
    # direction: it projects as a point.
    FOOTPRINT_ELONGATION = 2.0

    def __init__(
        self,
        source,
        axis=None,
        alignment_type="Plane",
        tolerance=None,
        min_group=3,
        state="Final",
    ):
        super().__init__(state, source)
        self.type = "Alignement"

        if axis not in (None, "Vertical", "Horizontal"):
            raise ValueError(
                f"axis must be None, 'Vertical' or 'Horizontal', got '{axis}'"
            )
        if alignment_type not in ("Line", "Plane"):
            raise ValueError(
                f"alignment_type must be 'Line' or 'Plane', got '{alignment_type}'"
            )
        if tolerance is None or not isinstance(tolerance, (int, float)):
            raise ValueError("tolerance is mandatory and must be a number (in meter)")
        if tolerance < 0:
            raise ValueError(f"tolerance must be positive, got {tolerance}")
        if not isinstance(min_group, int) or min_group < 1:
            raise ValueError(f"min_group must be an integer >= 1, got {min_group}")

        self.axis = axis
        self.alignment_type = alignment_type
        self.tolerance = float(tolerance)
        self.min_group = int(min_group)
        self.alignment = None
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.display_items.clear()
        self.select_source.run()

        objects = self._collect_axis_data()
        offsets = self._compute_offsets(objects)
        groups = self._compute_groups(objects)
        self.alignment = self._build_alignment_info(objects, offsets, groups)

        # The fitted element of every valid group (the clash detection
        # zone), kept in the display registry.
        for shape, transparency in self._fitted_zone_shapes(objects, groups):
            self.register_display_item("zone", shape, (0.5,0,1), transparency)

        if self.state == "Display_Input":
            return self.end_rule_action()

        for one_object, clash, offset in zip(
            objects, self._clash_flags(objects, groups), offsets
        ):
            if clash:
                result = ClashResultOneObject(source=one_object["entity"], state=True)
                result.info.offset = offset  # m — mesure nominale
                self.result.append(result)

        self.end_rule_action()

    def _collect_axis_data(self):
        """The length axis of the OBB of each selected object.

        The object is taken along its length: the main axis is the
        largest horizontal OBB axis when the footprint is elongated, so
        the plan projection of the object is the largest possible (its
        length segment, never a point). A compact footprint (a column)
        carries no plan direction: the object keeps its largest axis
        and projects as a point. The largest axis whatever its
        orientation is kept for the orientation vote (a tall object
        still votes vertical), and the world Z half extent lets the
        displayed planes span the full height of their objects. The
        axis segment (center +/- length direction * length half size)
        carries the geometric data of the alignment.
        """
        objects = []
        for ifc_file in self.select_source.dict_elements.keys():
            elements = self.select_source.dict_elements[ifc_file]
            if not elements:
                continue

            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=elements,
            )
            if not iterator.initialize():
                continue

            while True:
                shape = iterator.get()
                entity = ifc_file.by_id(shape.data.id)

                obb = create_obb_from_TopoDs_Shape(shape.geometry)
                center = obb.Center()
                directions = [
                    np.array(
                        [
                            direction.X(),
                            direction.Y(),
                            direction.Z(),
                        ]
                    )
                    for direction in (
                        obb.XDirection(),
                        obb.YDirection(),
                        obb.ZDirection(),
                    )
                ]
                half_sizes = [obb.XHSize(), obb.YHSize(), obb.ZHSize()]

                # The object is taken along its length: the largest
                # horizontal axis, when the footprint is elongated (a
                # wall: its plan projection is the largest possible
                # and directional). A compact footprint (a column)
                # carries no plan direction: the object keeps its
                # largest axis and projects as a point in the plan.
                horizontal = sorted(
                    (
                        index
                        for index in range(3)
                        if abs(directions[index][2]) < self.VERTICAL_COSINE
                    ),
                    key=lambda i: half_sizes[i],
                    reverse=True,
                )
                largest_index = max(range(3), key=lambda i: half_sizes[i])
                if (
                    len(horizontal) >= 2
                    and half_sizes[horizontal[0]]
                    >= self.FOOTPRINT_ELONGATION * half_sizes[horizontal[1]]
                ):
                    main_index = horizontal[0]
                else:
                    main_index = largest_index

                # The world Z half extent of the OBB (the support of
                # the box on the vertical axis).
                half_height = sum(
                    abs(directions[index][2]) * half_sizes[index]
                    for index in range(3)
                )

                objects.append(
                    {
                        "entity": entity,
                        "center": np.array([center.X(), center.Y(), center.Z()]),
                        "main_axis": directions[main_index],
                        "half_main": half_sizes[main_index],
                        "largest_axis": directions[largest_index],
                        "half_height": half_height,
                    }
                )

                if not iterator.next():
                    break

        return objects

    def _detect_orientation(self, objects):
        """Dominant orientation of the set, used when axis is None.

        An object votes vertical when its largest OBB axis is within 45
        degrees of the global Z (the main axis is the length axis and is
        never vertical). A tie goes to Vertical.
        """
        vertical_votes = sum(
            1
            for one_object in objects
            if abs(one_object["largest_axis"][2]) >= self.VERTICAL_COSINE
        )
        if vertical_votes >= len(objects) - vertical_votes:
            return "Vertical"
        return "Horizontal"

    def _compute_offsets(self, objects):
        """Offset of each object to the globally fitted element.

        This global fit does not decide the clashes (the groups of
        _compute_groups do): the offset of a clashing object is a
        guidance value for the correction.

        Vertical: the plan projections of the objects are fitted on one
        common least-squares line. The offset of an object is the plan
        distance between its projected center and the fitted line.

        Horizontal with a Plane fit: the axis segments are fitted on one
        common free least-squares plane. The offset of an object is the
        largest distance of its endpoints to the fitted plane.

        Horizontal with a Line fit: the axes must be collinear in 3D. The
        fitted line is least-squares fitted on the endpoints of the axis
        segments, the offset of an object is the largest distance of its
        endpoints to the fitted line.
        """
        if not objects:
            return []

        orientation = self.axis
        if orientation is None:
            orientation = self._detect_orientation(objects)
        self._orientation = orientation

        if orientation == "Vertical":
            plan_points = [one_object["center"][:2] for one_object in objects]
            line_origin, line_direction = clash_utils.least_squares_line_2d(plan_points)
            self._fitted = {
                "element": "Line",
                "origin": line_origin,
                "direction": line_direction,
            }
            return [
                clash_utils.point_line_distance(point, line_origin, line_direction)
                for point in plan_points
            ]

        segments = self._axis_segments(objects)
        if self.alignment_type == "Plane":
            all_endpoints = [endpoint for segment in segments for endpoint in segment]
            plane_origin, plane_normal = clash_utils.least_squares_plane_3d(
                all_endpoints
            )
            self._fitted = {
                "element": "Plane",
                "origin": plane_origin,
                "direction": plane_normal,
            }
            return [
                max(
                    clash_utils.point_plane_distance(
                        endpoint, plane_origin, plane_normal
                    )
                    for endpoint in segment
                )
                for segment in segments
            ]

        # Horizontal, Line: collinear axes in 3D
        all_endpoints = [endpoint for segment in segments for endpoint in segment]
        line_origin, line_direction = clash_utils.least_squares_line_3d(all_endpoints)
        self._fitted = {
            "element": "Line",
            "origin": line_origin,
            "direction": line_direction,
        }
        return [
            max(
                clash_utils.point_line_distance(endpoint, line_origin, line_direction)
                for endpoint in segment
            )
            for segment in segments
        ]

    def _axis_segments(self, objects):
        """The main axis segment (start, end) of each object."""
        return [
            (
                one_object["center"]
                - one_object["main_axis"] * one_object["half_main"],
                one_object["center"]
                + one_object["main_axis"] * one_object["half_main"],
            )
            for one_object in objects
        ]

    def _compute_groups(self, objects):
        """The alignment groups of the set (see clash_utils).

        An object may belong to several groups. Vertical: the groups are
        built on the plan projections of the objects, the main axis of
        an object being projected to a point when it stands vertical.
        Horizontal with a Plane fit: the groups are the sets of objects
        lying in one common free plane, a level (at most 1 degree
        from the horizontal — floor planes, landings; the alignment
        of horizontal objects is about levels, an inclined ramp is
        not a level alignment). Horizontal with a Line
        fit: the groups are built on the 3D axis segments.
        """
        if not objects:
            return []

        if self._orientation == "Vertical":
            points = [one_object["center"][:2] for one_object in objects]
            directions = []
            for one_object in objects:
                axis = one_object["main_axis"]
                if abs(axis[2]) >= self.VERTICAL_COSINE:
                    # Vertical main axis: the plan projection is a point.
                    directions.append(None)
                else:
                    plan_axis = np.asarray(axis[:2], dtype=float)
                    directions.append(plan_axis / np.linalg.norm(plan_axis))
            return clash_utils.plan_alignment_groups(points, directions, self.tolerance)

        segments = self._axis_segments(objects)
        directions = [one_object["main_axis"] for one_object in objects]
        if self.alignment_type == "Plane":
            return clash_utils.coplanar_alignment_groups(
                segments, directions, self.tolerance
            )
        return clash_utils.collinear_alignment_groups(
            segments, directions, self.tolerance
        )

    def _clash_flags(self, objects, groups):
        """A clash when the object belongs to no valid alignment group.

        A valid group has at least Min_Group members. Min_Group = 1
        makes every single object a valid alignment: no clash.
        """
        if self.min_group <= 1:
            return [False] * len(objects)

        passing = set()
        for group in groups:
            if len(group) >= self.min_group:
                passing.update(group)
        return [index not in passing for index in range(len(objects))]

    def _fit_group_element(self, objects, indices):
        """The fitted element of one alignment group.

        Returns (element, position, direction): for the Vertical
        orientation, the line along the common axis of the member walls
        through the centroid of their projected centers (the
        least-squares line on the centers when no member carries an
        axis: columns), the least-squares plane on the axis segments
        for a Plane fit (the least-squares line when the segments are
        collinear within the tolerance — the alignment is then a line),
        the least-squares line on the axis segments for a Line fit.
        """
        segments = self._axis_segments(objects)

        if self._orientation == "Vertical":
            points = [objects[index]["center"][:2] for index in indices]
            # The group members are parallel walls: the fitted line runs
            # along their common axis direction, not along the spread
            # of their centers. Stacked walls (one facade piece per
            # storey) have coincident plan projections: a PCA on the
            # centers would return a meaningless numerical direction.
            # The PCA stays for groups of point projections only
            # (columns: no member carries an axis).
            axes = [
                objects[index]["main_axis"][:2]
                for index in indices
                if abs(objects[index]["main_axis"][2]) < self.VERTICAL_COSINE
            ]
            if axes:
                reference = np.asarray(axes[0], dtype=float)
                aligned = [
                    np.asarray(axis, dtype=float)
                    if float(np.asarray(axis, dtype=float) @ reference) >= 0
                    else -np.asarray(axis, dtype=float)
                    for axis in axes
                ]
                direction = np.mean(aligned, axis=0)
                direction = direction / np.linalg.norm(direction)
                position = np.mean(np.asarray(points, dtype=float), axis=0)
            else:
                position, direction = clash_utils.least_squares_line_2d(points)
            return "Line", position, direction

        endpoints = [endpoint for index in indices for endpoint in segments[index]]

        if self.alignment_type == "Plane":
            line_origin, line_direction = clash_utils.least_squares_line_3d(endpoints)
            collinear = all(
                clash_utils.point_line_distance(endpoint, line_origin, line_direction)
                <= self.tolerance
                for endpoint in endpoints
            )
            if collinear:
                return "Line", line_origin, line_direction
            position, direction = clash_utils.least_squares_plane_3d(endpoints)
            return "Plane", position, direction

        position, direction = clash_utils.least_squares_line_3d(endpoints)
        return "Line", position, direction

    def _build_alignment_info(self, objects, offsets, groups):
        """The alignment found: the largest valid group and its fitted
        element (direction = the line direction, or the plane normal
        for a Plane fit).

        Returns None when the set is empty. When no valid group exists,
        the global least-squares fit is reported, with the objects whose
        offset stays within the tolerance.
        """
        if not objects:
            return None

        valid_groups = [group for group in groups if len(group) >= self.min_group]
        if valid_groups:
            best = max(valid_groups, key=len)
            members = [objects[index]["entity"] for index in best]
            element, position, direction = self._fit_group_element(objects, best)
            return {
                "orientation": self._orientation,
                "element": element,
                "direction": direction,
                "position": position,
                "members": members,
            }

        members = [
            one_object["entity"]
            for one_object, offset in zip(objects, offsets)
            if offset <= self.tolerance
        ]
        return {
            "orientation": self._orientation,
            "element": self._fitted["element"],
            "direction": self._fitted["direction"],
            "position": self._fitted["origin"],
            "members": members,
        }

    def _fitted_zone_shapes(self, objects, groups):
        """The fitted element of every valid alignment group (the clash
        detection zones), as display shapes.

        The fitted plane (a Plane fit) is a rectangle spanning the
        member objects, the fitted line (a Line fit) an edge, the
        fitted plan line of the Vertical orientation its vertical
        extrusion. Groups sharing the same element appear once; the
        global fit is returned alone when no valid group exists.

        Returns (shape, transparency) pairs, the shape a
        ("face", corners) or ("edge", start, end) tuple for the
        display registry.
        """
        if not objects:
            return []

        # One fitted element per valid group, or the global fit alone
        # when no group is valid.
        valid_groups = [group for group in groups if len(group) >= self.min_group]
        if valid_groups:
            elements = [
                (self._fit_group_element(objects, group), group)
                for group in valid_groups
            ]
        else:
            elements = [
                (
                    (
                        self.alignment["element"],
                        self.alignment["position"],
                        self.alignment["direction"],
                    ),
                    None,
                )
            ]

        def canonical(direction):
            """A direction with a stable sign, for the deduplication."""
            vector = np.asarray(direction, dtype=float)
            for value in vector:
                if abs(value) > 1e-9:
                    if value < 0:
                        vector = -vector
                    break
            return vector

        # The same fitted element shared by several groups (a pair and
        # the group it extends to) appears once. The signature of an
        # element: its direction, and its position reduced to its
        # invariant — the offset along the normal for a plane, the
        # component perpendicular to the direction for a line.
        displayed = {}
        for (element, position, direction), group in elements:
            position = np.asarray(position, dtype=float)
            vector = canonical(direction)
            if element == "Plane":
                offset = np.array([float(position @ vector)])
            else:
                offset = position - float(position @ vector) * vector
            key = (
                element,
                tuple(np.round(vector, 2)),
                tuple(np.round(offset, 2)),
            )
            if key in displayed:
                continue
            displayed[key] = (element, position, vector, group)

        def span(values, margin=0.25):
            """The extent of a coordinate, padded to stay visible."""
            low, high = min(values), max(values)
            if high - low < 1e-6:
                return low - margin, high + margin
            return low, high

        shapes = []
        for element, position, direction, group in displayed.values():
            if group is None:
                # The global fit spans the objects within the tolerance.
                zone_objects = [
                    one_object
                    for one_object in objects
                    if one_object["entity"] in self.alignment["members"]
                ] or objects
            else:
                zone_objects = [objects[index] for index in group]

            # The element spans the axis segments of its member objects.
            endpoints = [
                endpoint
                for one_object in zone_objects
                for endpoint in (
                    one_object["center"]
                    - one_object["main_axis"] * one_object["half_main"],
                    one_object["center"]
                    + one_object["main_axis"] * one_object["half_main"],
                )
            ]

            if element == "Plane":
                helper = np.array([1.0, 0.0, 0.0])
                if abs(float(direction @ helper)) > 0.9:
                    helper = np.array([0.0, 1.0, 0.0])
                axis_u = np.cross(direction, helper)
                axis_u = axis_u / np.linalg.norm(axis_u)
                axis_v = np.cross(direction, axis_u)
                us = [float((e - position) @ axis_u) for e in endpoints]
                vs = [float((e - position) @ axis_v) for e in endpoints]
                min_u, max_u = span(us)
                min_v, max_v = span(vs)
                shapes.append(
                    (
                        (
                            "face",
                            [
                                position + axis_u * min_u + axis_v * min_v,
                                position + axis_u * max_u + axis_v * min_v,
                                position + axis_u * max_u + axis_v * max_v,
                                position + axis_u * min_u + axis_v * max_v,
                            ],
                        ),
                        0.6,
                    )
                )
            elif self._orientation == "Vertical":
                # The fitted plan line, as its vertical extrusion. The
                # plane is as large as possible: it spans the length
                # segments of its members along the line, and their
                # full height on the vertical axis.
                ts = [
                    float((endpoint[:2] - position) @ direction)
                    for endpoint in endpoints
                ]
                zs = []
                for one_object in zone_objects:
                    zs.append(
                        float(one_object["center"][2] - one_object["half_height"])
                    )
                    zs.append(
                        float(one_object["center"][2] + one_object["half_height"])
                    )
                min_t, max_t = span(ts)
                min_z, max_z = span(zs)

                def plan_point(t, z):
                    return np.array(
                        [
                            position[0] + direction[0] * t,
                            position[1] + direction[1] * t,
                            z,
                        ]
                    )

                shapes.append(
                    (
                        (
                            "face",
                            [
                                plan_point(min_t, min_z),
                                plan_point(max_t, min_z),
                                plan_point(max_t, max_z),
                                plan_point(min_t, max_z),
                            ],
                        ),
                        0.6,
                    )
                )
            else:
                # The fitted 3D line, as an edge.
                ts = [
                    float((endpoint - position) @ direction) for endpoint in endpoints
                ]
                min_t, max_t = span(ts)
                shapes.append(
                    (
                        (
                            "edge",
                            position + direction * min_t,
                            position + direction * max_t,
                        ),
                        0.0,
                    )
                )

        return shapes



class SurfaceRecover(RuleCheckTwoObjects):
    """Check that the contact surface between two objects covers an
    expected value, defined by a min and a max.

    Only pairs whose distance is below the tolerance AND whose extreme
    faces face each other within the tolerance along the direction are
    analyzed: pairs not in contact produce no result, and so do pairs
    whose extreme faces do not face each other (e.g. crossing objects):
    they are not support pairs. The extreme faces of the two objects
    along the direction are paired, the contact area is the sum of the
    disjoint contact zones (quasi coplanar triangles at a distance below
    the tolerance), and a clash is raised when the covering value is
    outside [Min_Covering, Max_Covering]. See doc/2ObjectsRules/SurfaceRecover.md.
    """

    # Two facing triangles are paired when their normals are opposite
    # within 25 degrees.
    PAIRING_COSINE = -math.cos(math.radians(25))

    # A face is a contact candidate when its normal is aligned with
    # the direction within 45 degrees.
    ALIGNED_COSINE = math.cos(math.radians(45))

    def __init__(
        self,
        source,
        target,
        direction="Auto",
        reference="Source",
        tolerance=0.001,
        min_covering=None,
        max_covering=None,
        state="Final",
    ):
        super().__init__(state, source, target)
        self.type = "SurfaceRecover"

        if direction == "Auto":
            self.direction = "Auto"
        elif direction == "Top":
            self.direction = (0.0, 0.0, 1.0)
        elif direction == "Bottom":
            self.direction = (0.0, 0.0, -1.0)
        elif (
            hasattr(direction, "__len__")
            and len(direction) == 3
            and all(isinstance(value, (int, float)) for value in direction)
            and np.linalg.norm(direction) > 1e-12
        ):
            self.direction = tuple(
                np.asarray(direction, dtype=float) / np.linalg.norm(direction)
            )
        else:
            raise ValueError(
                "direction must be 'Auto', 'Top', 'Bottom' or a 3D vector, "
                f"got {direction!r}"
            )

        if reference not in ("Source", "Target"):
            raise ValueError(
                f"reference must be 'Source' or 'Target', got '{reference}'"
            )
        if not isinstance(tolerance, (int, float)) or tolerance < 0:
            raise ValueError(f"tolerance must be a positive number, got {tolerance}")

        self.reference = reference
        self.tolerance = float(tolerance)
        self.min_covering = self._parse_covering(min_covering, "min_covering")
        self.max_covering = self._parse_covering(max_covering, "max_covering")

        # OpenCascade shapes for the distance and the OBB prefilter.
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)
        # Triangulated meshes in world coordinates for the contact area.
        self.mesh_settings = ifcopenshell.geom.settings()
        self.mesh_settings.set("USE_WORLD_COORDS", True)

    @staticmethod
    def _parse_covering(value, parameter_name):
        """A covering bound: None, an absolute area (float, in m2) or a
        relative value (string ending with %)."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return ("absolute", float(value))
        if isinstance(value, str) and value.endswith("%"):
            try:
                return ("relative", float(value[:-1]))
            except ValueError:
                pass
        raise ValueError(
            f"{parameter_name} must be a number (m2) or a string ending "
            f"with '%', got {value!r}"
        )

    def _collect_geometry(self, select):
        """OCC shape, OBB and triangulated mesh of each selected element."""
        elements = []
        for ifc_file in select.dict_elements.keys():
            included = select.dict_elements[ifc_file]
            if not included:
                continue

            occ_shapes = {}
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=included,
            )
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    entity = ifc_file.by_id(shape.data.id)
                    occ_shapes[entity.id()] = shape.geometry
                    if not iterator.next():
                        break

            iterator = ifcopenshell.geom.iterator(
                self.mesh_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=included,
            )
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    entity = ifc_file.by_id(shape.id)
                    occ_shape = occ_shapes.get(entity.id())
                    if occ_shape is None:
                        if not iterator.next():
                            break
                        continue

                    vertices = get_vertices(shape.geometry)
                    faces = get_faces(shape.geometry)
                    if len(faces) == 0:
                        if not iterator.next():
                            break
                        continue

                    elements.append(
                        {
                            "entity": entity,
                            "occ": occ_shape,
                            "obb": create_obb_from_TopoDs_Shape(occ_shape),
                            "vertices": np.asarray(vertices, dtype=float),
                            "faces": np.asarray(faces),
                            "centroid": np.asarray(vertices, dtype=float).mean(axis=0),
                        }
                    )
                    if not iterator.next():
                        break

        return elements

    def run(self):
        self.display_items.clear()
        self.select_source.run()
        self.select_target.run()

        sources = self._collect_geometry(self.select_source)
        targets = self._collect_geometry(self.select_target)

        if self.state == "Display_Input":
            return self.end_rule_action()

        for source in sources:
            for target in targets:
                # The OBB prefilter keeps the pairs whose bounding boxes
                # are within the tolerance, the exact distance is checked
                # afterwards.
                if source["obb"].min_distance_to_obb(target["obb"]) > self.tolerance:
                    continue

                dist_tool = BRepExtrema_DistShapeShape()
                dist_tool.LoadS1(source["occ"])
                dist_tool.LoadS2(target["occ"])
                dist_tool.Perform()
                distance = dist_tool.Value()

                # Pairs not in contact produce no result.
                if distance > self.tolerance:
                    continue

                if self.direction == "Auto":
                    direction = self._auto_direction(dist_tool)
                    if direction is None:
                        # Touching or overlapping objects: the closest
                        # points coincide, fall back on the centroids.
                        direction = self._centroid_direction(source, target)
                    if direction is None:
                        continue
                else:
                    direction = np.asarray(self.direction, dtype=float)

                source_triangles = clash_utils.extreme_triangles(
                    source["vertices"],
                    source["faces"],
                    direction,
                    tolerance=self.tolerance,
                    alignment_cosine=self.ALIGNED_COSINE,
                )
                target_triangles = clash_utils.extreme_triangles(
                    target["vertices"],
                    target["faces"],
                    -direction,
                    tolerance=self.tolerance,
                    alignment_cosine=self.ALIGNED_COSINE,
                )

                # The extreme faces must face each other: when the two
                # extreme planes are farther apart than the tolerance
                # along the direction (e.g. a wall crossing a slab),
                # the pair is not a support pair and produces no
                # result, whatever the bounds.
                if len(source_triangles) == 0 or len(target_triangles) == 0:
                    continue
                source_plane = source_triangles.mean(axis=1) @ direction
                target_plane = target_triangles.mean(axis=1) @ direction
                if abs(source_plane.max() - target_plane.min()) > self.tolerance:
                    continue

                contact_area, contact_triangles = (
                    clash_utils.contact_polygons_between_triangle_sets(
                        source_triangles,
                        target_triangles,
                        direction,
                        tolerance=self.tolerance,
                        pairing_cosine=self.PAIRING_COSINE,
                    )
                )

                if self.reference == "Source":
                    reference_triangles = source_triangles
                else:
                    reference_triangles = target_triangles
                reference_area = clash_utils.triangles_projected_area(
                    reference_triangles, direction
                )

                ratio = None
                if reference_area > 1e-12:
                    ratio = 100.0 * contact_area / reference_area

                if clash_utils.covering_out_of_bounds(
                    contact_area,
                    ratio,
                    self.min_covering,
                    self.max_covering,
                ):
                    result = ClashResultTwoObjects(
                        source=source["entity"],
                        target=target["entity"],
                        state=True,
                    )
                    result.info.contact_area = contact_area  # m2 — nominale
                    if ratio is not None:
                        # Stocké en 0..1 (vocabulaire) ; les bornes du
                        # check restent en pourcentage.
                        result.info.ratio = ratio / 100.0
                    result.info.distance = distance  # m
                    contact_triangles_data = [
                        tuple(tuple(float(c) for c in vertex) for vertex in triangle)
                        for triangle in contact_triangles
                    ]
                    result.info.add_face_pair(
                        (   # face de la source : (normal, area, triangles)
                            tuple(float(v) for v in direction),
                            clash_utils.triangles_projected_area(
                                source_triangles, direction
                            ),
                            contact_triangles_data,
                        ),
                        (   # face de la target
                            tuple(float(-v) for v in direction),
                            clash_utils.triangles_projected_area(
                                target_triangles, -direction
                            ),
                            contact_triangles_data,
                        ),
                    )
                    self.result.append(result)

                    # The contact surfaces of the clash, kept in the
                    # display registry (one face per contact triangle).
                    for triangle in contact_triangles:
                        self.register_display_item(
                            "face",
                            ("face", [tuple(vertex) for vertex in triangle]),
                            (1, 0.5, 0),
                            0.0,
                            element=source["entity"],
                        )

        self.end_rule_action()

    @staticmethod
    def _auto_direction(dist_tool):
        """Direction of the check derived from the pair itself: the vector
        from the closest point of the source to the closest point of the
        target.

        Returns None when the direction cannot be derived (the closest
        points coincide, e.g. for touching or overlapping objects).
        """
        if dist_tool.NbSolution() < 1:
            return None
        point_source = dist_tool.PointOnShape1(1)
        point_target = dist_tool.PointOnShape2(1)
        vector = np.array(
            [
                point_target.X() - point_source.X(),
                point_target.Y() - point_source.Y(),
                point_target.Z() - point_source.Z(),
            ]
        )
        norm = np.linalg.norm(vector)
        if norm < 1e-9:
            return None
        return vector / norm

    @staticmethod
    def _centroid_direction(source, target):
        """Fallback direction for touching pairs: the vector between the
        mesh centroids of the two objects.

        Returns None when the centroids coincide.
        """
        vector = target["centroid"] - source["centroid"]
        norm = np.linalg.norm(vector)
        if norm < 1e-9:
            return None
        return vector / norm


class DirectView(RuleCheckTwoObjects):
    """Determine if the direct view between two objects is free, by
    casting rays between them.

    Only the faces oriented toward the other object emit or receive rays,
    and only the Context objects block a ray: the source and the target
    are transparent to their own rays. A clash is raised for the pairs
    whose hit ratio over the rays actually cast reaches the Threshold:
    the rays pass between the two objects, the direct view is
    established. See doc/2ObjectsRules/DirectView.md.

    This rule tests the mutual geometric visibility: no direction of
    view, no field of view, no viewing cone.
    """

    def __init__(
        self,
        source,
        target,
        context,
        ray_source="Source",
        ray_count=10,
        threshold="100%",
        max_distance=None,
        state="Final",
    ):
        super().__init__(state, source, target)
        self.type = "DirectView"
        self.select_context: Select = context

        if ray_source not in ("Both", "Source", "Target"):
            raise ValueError(
                f"ray_source must be 'Both', 'Source' or 'Target', got '{ray_source}'"
            )
        if not isinstance(ray_count, int) or ray_count < 1:
            raise ValueError(f"ray_count must be an integer >= 1, got {ray_count}")
        if not (isinstance(threshold, str) and threshold.endswith("%")):
            raise ValueError(
                f"threshold must be a string ending with '%', got {threshold!r}"
            )
        try:
            threshold_value = float(threshold[:-1])
        except ValueError:
            raise ValueError(f"threshold must be a percentage, got {threshold!r}")
        if not 0.0 <= threshold_value <= 100.0:
            raise ValueError(
                f"threshold must be between 0% and 100%, got {threshold!r}"
            )
        if max_distance is not None and (
            not isinstance(max_distance, (int, float)) or max_distance <= 0
        ):
            raise ValueError(
                f"max_distance must be None or a positive number, got {max_distance}"
            )

        self.ray_source = ray_source
        self.ray_count = ray_count
        self.threshold = threshold_value
        self.max_distance = float(max_distance) if max_distance is not None else None

        # The context goes into the ray tree (triangulated, world coords).
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set("USE_WORLD_COORDS", True)
        # The emitting and receiving faces come from the world meshes.
        self.mesh_settings = ifcopenshell.geom.settings()
        self.mesh_settings.set("USE_WORLD_COORDS", True)

    def _collect_meshes(self, select):
        """The triangulated world mesh of each selected element."""
        meshes = {}
        for ifc_file in select.dict_elements.keys():
            included = select.dict_elements[ifc_file]
            if not included:
                continue

            iterator = ifcopenshell.geom.iterator(
                self.mesh_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=included,
            )
            if not iterator.initialize():
                continue

            while True:
                shape = iterator.get()
                entity = ifc_file.by_id(shape.id)
                vertices = np.asarray(get_vertices(shape.geometry), dtype=float)
                faces = np.asarray(get_faces(shape.geometry))
                if len(faces) > 0:
                    triangles = vertices[faces]
                    meshes[entity] = {
                        "triangles": triangles,
                        "centroid": vertices.mean(axis=0),
                    }
                if not iterator.next():
                    break

        return meshes

    @staticmethod
    def _faces_toward(mesh, other_centroid):
        """The triangles of a mesh whose normal faces the other object."""
        triangles = mesh["triangles"]
        v1 = triangles[:, 1] - triangles[:, 0]
        v2 = triangles[:, 2] - triangles[:, 0]
        normals = np.cross(v1, v2)
        magnitudes = np.linalg.norm(normals, axis=1)
        centers = triangles.mean(axis=1)

        facing = np.zeros(len(triangles), dtype=bool)
        valid = magnitudes > 1e-12
        if valid.any():
            unit_normals = normals[valid] / magnitudes[valid, np.newaxis]
            directions = other_centroid - centers[valid]
            facing[valid] = np.einsum("ij,ij->i", unit_normals, directions) > 0.0
        return triangles[facing]

    @staticmethod
    def _pick_receiving_face(receiver_faces, areas, total_area, index):
        """Deterministic area-weighted choice of the receiving face."""
        u = clash_utils.r2_sequence(index)[0] * total_area
        cumulative = 0.0
        for face, area in zip(receiver_faces, areas):
            cumulative += area
            if u <= cumulative:
                return face
        return receiver_faces[-1]

    def _pair_rays(self, emitter_mesh, receiver_mesh):
        """The (origin, aim) ray pairs of one emitting object.

        The rays are spread over the emitting faces proportionally to
        their area, each aimed at a sampled point of a receiving face
        (area-weighted). The sampling is deterministic (R2 sequence).
        """
        emitter_faces = self._faces_toward(emitter_mesh, receiver_mesh["centroid"])
        receiver_faces = self._faces_toward(receiver_mesh, emitter_mesh["centroid"])

        if len(emitter_faces) == 0 or len(receiver_faces) == 0:
            return

        emitter_areas = 0.5 * np.linalg.norm(
            np.cross(
                emitter_faces[:, 1] - emitter_faces[:, 0],
                emitter_faces[:, 2] - emitter_faces[:, 0],
            ),
            axis=1,
        )
        counts = clash_utils.plan_ray_counts(list(emitter_areas), self.ray_count)

        receiver_areas = 0.5 * np.linalg.norm(
            np.cross(
                receiver_faces[:, 1] - receiver_faces[:, 0],
                receiver_faces[:, 2] - receiver_faces[:, 0],
            ),
            axis=1,
        )
        receiver_total = float(receiver_areas.sum())

        index = 0
        for face, count in zip(emitter_faces, counts):
            for _ in range(count):
                origin = clash_utils.sample_point_in_triangle(face, index)
                receiving_face = self._pick_receiving_face(
                    receiver_faces, receiver_areas, receiver_total, index
                )
                # The aim point uses a shifted index: the origin and the
                # aim samples are decorrelated, so the rays cover the two
                # objects instead of pairing identical sample positions.
                aim = clash_utils.sample_point_in_triangle(
                    receiving_face, index + 1_000_007
                )
                index += 1
                yield origin, aim

    def _cast_ray(self, origin, aim):
        """True when the ray touches, i.e. no context object stands
        between the origin and the aim point."""
        vector = aim - origin
        length = np.linalg.norm(vector)

        if length < 1e-9:
            # The faces touch: nothing can stand in a zero-length ray.
            return True

        if self.max_distance is not None and length > self.max_distance:
            # The ray stops before the target: a miss.
            return False

        direction = vector / length
        hits = self.tree.select_ray(
            tuple(float(v) for v in origin),
            tuple(float(v) for v in direction),
            length=float(length),
        )
        return len(hits) == 0

    def run(self):
        self.display_items.clear()
        self.select_source.run()
        self.select_target.run()

        # The context needs the same files as the source to be able to run.
        self.select_context.list_ifc_path = self.select_source.list_ifc_path
        self.select_context.list_ifc_file = self.select_source.list_ifc_file
        self.select_context.run()

        # The context objects (the obstacles of the view), kept in the
        # display registry.
        for elements in self.select_context.dict_elements.values():
            for element in elements or []:
                self.register_display_item(
                    "context", ("entity", element), (0.5, 0.5, 0.5), 0.85
                )

        self.tree = clash_utils.make_ray_tree()
        self.add_to_tree(self.select_context, "UB")

        source_meshes = self._collect_meshes(self.select_source)
        target_meshes = self._collect_meshes(self.select_target)

        if self.state == "Display_Input":
            return self.end_rule_action()

        if self.ray_source == "Both":
            emitters_of = lambda source_mesh, target_mesh: [
                (source_mesh, target_mesh),
                (target_mesh, source_mesh),
            ]
        elif self.ray_source == "Source":
            emitters_of = lambda source_mesh, target_mesh: [(source_mesh, target_mesh)]
        else:
            emitters_of = lambda source_mesh, target_mesh: [(target_mesh, source_mesh)]

        threshold_fraction = self.threshold / 100.0

        for source_entity, source_mesh in source_meshes.items():
            for target_entity, target_mesh in target_meshes.items():
                if source_entity == target_entity:
                    continue

                planned = self.ray_count * len(emitters_of(source_mesh, target_mesh))
                hits = 0
                casts = 0
                hit_segments = []
                blocked_segments = []
                decision = None

                for emitter, receiver in emitters_of(source_mesh, target_mesh):
                    if decision is not None:
                        break
                    for origin, aim in self._pair_rays(emitter, receiver):
                        decision = clash_utils.direct_view_early_stop(
                            hits, casts, planned, threshold_fraction
                        )
                        if decision is not None:
                            break

                        touched = self._cast_ray(origin, aim)
                        casts += 1
                        if touched:
                            hits += 1
                            hit_segments.append((origin, aim))
                        else:
                            blocked_segments.append((origin, aim))

                hit_ratio = hits / casts if casts > 0 else 0.0
                # The sense of the rule is inverted: the pair clashes
                # when the rays pass between the two objects, i.e. when
                # the hit ratio reaches the Threshold (the direct view
                # is established). A fully occluded pair produces no
                # result.
                if hit_ratio >= threshold_fraction:
                    result = ClashResultTwoObjects(
                        source=source_entity,
                        target=target_entity,
                        state=True,
                    )
                    result.info.hit_ratio = hit_ratio  # 0..1 — nominale
                    result.info.raycast = RaycastData(
                        planned=planned,
                        cast=casts,
                        hit=hits,  # hit_ratio = hit / cast
                        hit_segments=[
                            (tuple(float(c) for c in origin), tuple(float(c) for c in aim))
                            for origin, aim in hit_segments
                        ],
                        blocked_segments=[
                            (tuple(float(c) for c in origin), tuple(float(c) for c in aim))
                            for origin, aim in blocked_segments
                        ],
                    )
                    self.result.append(result)

                    # The rays actually cast, kept in the display
                    # registry: green when the ray reached the other
                    # object, red when a context object blocked it.
                    for origin, aim in hit_segments:
                        self.register_display_item(
                            "segment",
                            ("edge", origin, aim),
                            (0, 1, 0),
                            0.0,
                            element=source_entity,
                        )
                    for origin, aim in blocked_segments:
                        self.register_display_item(
                            "segment",
                            ("edge", origin, aim),
                            (0.5,0,1),
                            0.0,
                            element=source_entity,
                        )

        self.end_rule_action()


class OneObjectFace(RuleCheckOneObject):
    """Run face-level checks within a single object.

    The faces of group A and group B are selected with two
    FaceSelection dictionaries (the schema of the FaceCheck family),
    every face of A is paired with every face of B, and each pair must
    pass all the enabled checks: distance (a pair closer than
    min_distance fails; max_distance is a search radius, a pair
    farther apart is not checked; adjacent faces skipped on demand),
    intersection (crossing deeper
    than a tolerance)
    and orientation (angle between the normals). One clash is raised per
    pair per failed check. In the display, the faces of group A are
    blue and the faces of group B orange; the other faces of the object
    are not registered, the object keeps its own display color. See
    doc/1ObjectsRules/OneObjectFace.md.
    """

    def __init__(
        self,
        source: Select,
        face_a_selection: dict | None = None,
        face_b_selection: dict | None = None,
        distance: bool = False,
        min_distance: float | None = None,
        max_distance: float | None = None,
        skip_adjacent: bool = True,
        intersection: bool = False,
        intersection_tolerance: float | None = None,
        orientation: bool = False,
        angle: float | None = None,
        angle_tolerance: float | None = None,
        state: str = "Final",
    ) -> None:
        super().__init__(state, source)
        self.type = "OneObjectFace"

        self.face_a_selection = clash_utils.validate_face_selection(face_a_selection)
        self.face_b_selection = clash_utils.validate_face_selection(face_b_selection)

        if not (distance or intersection or orientation):
            raise ValueError(
                "OneObjectFace needs at least one enabled check: "
                "distance, intersection or orientation"
            )

        if distance:
            for bound_name, bound_value in (
                ("min_distance", min_distance),
                ("max_distance", max_distance),
            ):
                if bound_value is not None and (
                    not isinstance(bound_value, (int, float)) or bound_value < 0
                ):
                    raise ValueError(
                        f"{bound_name} must be a positive number (m), "
                        f"got {bound_value!r}"
                    )
            if (
                min_distance is not None
                and max_distance is not None
                and min_distance > max_distance
            ):
                raise ValueError(
                    f"min_distance ({min_distance}) must not exceed "
                    f"max_distance ({max_distance})"
                )
            if not isinstance(skip_adjacent, bool):
                raise ValueError(
                    f"skip_adjacent must be a boolean, got {skip_adjacent!r}"
                )
        self.distance = distance
        self.min_distance = float(min_distance) if min_distance is not None else None
        self.max_distance = float(max_distance) if max_distance is not None else None
        self.skip_adjacent = skip_adjacent if distance else True

        if intersection:
            if intersection_tolerance is None:
                intersection_tolerance = 0.0
            if (
                not isinstance(intersection_tolerance, (int, float))
                or intersection_tolerance < 0
            ):
                raise ValueError(
                    "intersection_tolerance must be a positive number (m), "
                    f"got {intersection_tolerance!r}"
                )
        self.intersection = intersection
        self.intersection_tolerance = (
            float(intersection_tolerance)
            if intersection and intersection_tolerance is not None
            else 0.0
        )

        if orientation:
            if not isinstance(angle, (int, float)) or not 0.0 <= angle <= 180.0:
                raise ValueError(
                    f"angle is mandatory (degrees in [0, 180]) when the "
                    f"orientation check is enabled, got {angle!r}"
                )
            if angle_tolerance is None:
                angle_tolerance = 0.0
            if not isinstance(angle_tolerance, (int, float)) or angle_tolerance < 0:
                raise ValueError(
                    "angle_tolerance must be a positive number (degrees), "
                    f"got {angle_tolerance!r}"
                )
        self.orientation = orientation
        self.angle = float(angle) if angle is not None else None
        self.angle_tolerance = (
            float(angle_tolerance) if angle_tolerance is not None else 0.0
        )

        # Triangulated world meshes only: no OpenCascade shape needed
        # except for the distance between two triangles.
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set("USE_WORLD_COORDS", True)

    @staticmethod
    def _triangle_data(triangle):
        """The normal (unit) and the area of a triangle."""
        v1 = triangle[1] - triangle[0]
        v2 = triangle[2] - triangle[0]
        normal = np.cross(v1, v2)
        magnitude = np.linalg.norm(normal)
        if magnitude > 1e-12:
            normal = normal / magnitude
        return normal, 0.5 * magnitude

    def _run_checks(self, triangle_a, triangle_b):
        """The failed checks of one pair, as (check, value) tuples."""
        failures = []

        if self.distance:
            if (
                self.max_distance is not None
                and clash_utils.triangles_bbox_distance(triangle_a, triangle_b)
                > self.max_distance
            ):
                # max_distance is a search radius: a pair farther
                # apart than max_distance is not checked at all.
                pass
            else:
                adjacent = clash_utils.triangles_share_geometry(triangle_a, triangle_b)
                if not (self.skip_adjacent and adjacent):
                    measured = clash_utils.distance_between_triangles(
                        triangle_a, triangle_b
                    )
                    if self.min_distance is not None and measured < self.min_distance:
                        failures.append(("distance", measured))

        if self.intersection:
            if clash_utils.triangles_cross_properly(triangle_a, triangle_b):
                depth = clash_utils.triangle_penetration_depth(triangle_a, triangle_b)
                if depth > self.intersection_tolerance:
                    failures.append(("intersection", depth))

        if self.orientation:
            normal_a, _ = self._triangle_data(triangle_a)
            normal_b, _ = self._triangle_data(triangle_b)
            dot = float(np.clip(normal_a @ normal_b, -1.0, 1.0))
            measured = math.degrees(math.acos(dot))
            if abs(measured - self.angle) > self.angle_tolerance:
                failures.append(("orientation", measured))

        return failures

    def run(self):
        self.display_items.clear()
        self.select_source.run()

        for ifc_file in self.select_source.dict_elements.keys():
            included = self.select_source.dict_elements[ifc_file]
            if not included:
                continue

            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=included,
            )
            if not iterator.initialize():
                continue

            while True:
                shape = iterator.get()
                entity = ifc_file.by_id(shape.id)
                vertices = np.asarray(get_vertices(shape.geometry), dtype=float)
                faces = np.asarray(get_faces(shape.geometry))
                if len(faces) > 0:
                    material_names = clash_utils.get_element_material_names(entity)
                    group_a = clash_utils.select_faces(
                        vertices,
                        faces,
                        self.face_a_selection,
                        material_names,
                    )
                    group_b = clash_utils.select_faces(
                        vertices,
                        faces,
                        self.face_b_selection,
                        material_names,
                    )

                    # The faces of the two groups, kept in the display
                    # registry: the faces of group A in blue, the
                    # faces of group B in orange. The other faces of
                    # the object are not registered: the object keeps
                    # its own display color (red/green in
                    # Display_Result, blue in Display_Input).
                    for triangle in group_a:
                        self.register_display_item(
                            "face",
                            ("face", [tuple(vertex) for vertex in triangle]),
                            (0, 0, 1),
                            0.0,
                            element=entity,
                        )
                    for triangle in group_b:
                        self.register_display_item(
                            "face",
                            ("face", [tuple(vertex) for vertex in triangle]),
                            (1, 0.45, 0),
                            0.0,
                            element=entity,
                        )

                    self._check_pairs(entity, group_a, group_b)

                if not iterator.next():
                    break

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()

    def _check_pairs(self, entity, group_a, group_b):
        """Every face of A against every face of B, each pair once,
        self-pairs skipped, one clash per pair per failed check."""
        seen_pairs = set()
        for triangle_a in group_a:
            key_a = clash_utils._triangle_key(triangle_a)
            for triangle_b in group_b:
                key_b = clash_utils._triangle_key(triangle_b)
                if key_a == key_b:
                    # A face paired with itself is skipped.
                    continue

                pair_key = (key_a, key_b) if key_a <= key_b else (key_b, key_a)
                if pair_key in seen_pairs:
                    continue
                seen_pairs.add(pair_key)

                for check, value in self._run_checks(triangle_a, triangle_b):
                    result = ClashResultOneObject(source=entity, state=True)
                    clash_utils.apply_check_measure(result.info, check, value)
                    normal_a, area_a = self._triangle_data(triangle_a)
                    normal_b, area_b = self._triangle_data(triangle_b)
                    result.info.add_face_pair(
                        (   # face A de l'élément source
                            tuple(float(v) for v in normal_a),
                            float(area_a),
                            [tuple(tuple(float(c) for c in vertex) for vertex in triangle_a)],
                        ),
                        (   # face B du même élément
                            tuple(float(v) for v in normal_b),
                            float(area_b),
                            [tuple(tuple(float(c) for c in vertex) for vertex in triangle_b)],
                        ),
                    )
                    self.result.append(result)



class TwoObjectsFace(RuleCheckTwoObjects):
    """Run face-level checks between two object sets (the FaceCheck
    family).

    The faces of the source objects are selected with
    Source_Face_Selection. The target provides what they are checked
    against: the faces selected by Target_Face_Selection when it is
    provided, the whole target objects (all their faces) when it is
    omitted. Every source face is paired with every target face, and
    each pair must pass all the enabled checks: distance (a pair closer
    than min_distance fails; max_distance is a search radius, a pair
    farther apart is not checked), intersection (crossing deeper than a
    tolerance) and orientation (angle between the normals). One clash is
    raised per pair per failed check. See
    doc/2ObjectsRules/TwoObjectsFace.md. In the display, the selected
    source faces are blue and the selected target faces orange, as in
    OneObjectFace; the other faces of the objects are not registered,
    the objects keep their own display color.

    Unlike OneObjectFace there is no skip_adjacent: two faces of two
    different objects never share a mesh vertex, and two objects that
    touch are exactly what a face-level clearance check must report.
    """

    def __init__(
        self,
        source,
        target,
        source_face_selection: dict | None = None,
        target_face_selection: dict | None = None,
        distance: bool = False,
        min_distance: float | None = None,
        max_distance: float | None = None,
        intersection: bool = False,
        intersection_tolerance: float | None = None,
        orientation: bool = False,
        angle: float | None = None,
        angle_tolerance: float | None = None,
        state: str = "Final",
    ) -> None:
        super().__init__(state, source, target)
        self.type = "TwoObjectsFace"

        self.source_face_selection = clash_utils.validate_face_selection(
            source_face_selection
        )
        self.target_face_selection = clash_utils.validate_face_selection(
            target_face_selection
        )

        if not (distance or intersection or orientation):
            raise ValueError(
                "TwoObjectsFace needs at least one enabled check: "
                "distance, intersection or orientation"
            )

        if distance:
            for bound_name, bound_value in (
                ("min_distance", min_distance),
                ("max_distance", max_distance),
            ):
                if bound_value is not None and (
                    not isinstance(bound_value, (int, float)) or bound_value < 0
                ):
                    raise ValueError(
                        f"{bound_name} must be a positive number (m), "
                        f"got {bound_value!r}"
                    )
            if (
                min_distance is not None
                and max_distance is not None
                and min_distance > max_distance
            ):
                raise ValueError(
                    f"min_distance ({min_distance}) must not exceed "
                    f"max_distance ({max_distance})"
                )
        self.distance = distance
        self.min_distance = float(min_distance) if min_distance is not None else None
        self.max_distance = float(max_distance) if max_distance is not None else None

        if intersection:
            if intersection_tolerance is None:
                intersection_tolerance = 0.0
            if (
                not isinstance(intersection_tolerance, (int, float))
                or intersection_tolerance < 0
            ):
                raise ValueError(
                    "intersection_tolerance must be a positive number (m), "
                    f"got {intersection_tolerance!r}"
                )
        self.intersection = intersection
        self.intersection_tolerance = (
            float(intersection_tolerance)
            if intersection and intersection_tolerance is not None
            else 0.0
        )

        if orientation:
            if not isinstance(angle, (int, float)) or not 0.0 <= angle <= 180.0:
                raise ValueError(
                    f"angle is mandatory (degrees in [0, 180]) when the "
                    f"orientation check is enabled, got {angle!r}"
                )
            if angle_tolerance is None:
                angle_tolerance = 0.0
            if not isinstance(angle_tolerance, (int, float)) or angle_tolerance < 0:
                raise ValueError(
                    "angle_tolerance must be a positive number (degrees), "
                    f"got {angle_tolerance!r}"
                )
        self.orientation = orientation
        self.angle = float(angle) if angle is not None else None
        self.angle_tolerance = (
            float(angle_tolerance) if angle_tolerance is not None else 0.0
        )

        # Triangulated world meshes only: no OpenCascade shape needed
        # except for the distance between two triangles.
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set("USE_WORLD_COORDS", True)

    @staticmethod
    def _triangle_data(triangle):
        """The normal (unit) and the area of a triangle."""
        v1 = triangle[1] - triangle[0]
        v2 = triangle[2] - triangle[0]
        normal = np.cross(v1, v2)
        magnitude = np.linalg.norm(normal)
        if magnitude > 1e-12:
            normal = normal / magnitude
        return normal, 0.5 * magnitude

    def _run_checks(self, triangle_a, triangle_b):
        """The failed checks of one pair, as (check, value) tuples."""
        failures = []

        if self.distance:
            if (
                self.max_distance is not None
                and clash_utils.triangles_bbox_distance(triangle_a, triangle_b)
                > self.max_distance
            ):
                # max_distance is a search radius: a pair farther
                # apart than max_distance is not checked at all.
                pass
            elif (
                self.min_distance is not None
                and clash_utils.triangles_bbox_distance(triangle_a, triangle_b)
                >= self.min_distance
            ):
                # The bounding boxes are already far enough apart:
                # the exact distance cannot be below the bound.
                pass
            else:
                measured = clash_utils.distance_between_triangles(
                    triangle_a, triangle_b
                )
                if self.min_distance is not None and measured < self.min_distance:
                    failures.append(("distance", measured))

        if self.intersection:
            if clash_utils.triangles_cross_properly(triangle_a, triangle_b):
                depth = clash_utils.triangle_penetration_depth(triangle_a, triangle_b)
                if depth > self.intersection_tolerance:
                    failures.append(("intersection", depth))

        if self.orientation:
            normal_a, _ = self._triangle_data(triangle_a)
            normal_b, _ = self._triangle_data(triangle_b)
            dot = float(np.clip(normal_a @ normal_b, -1.0, 1.0))
            measured = math.degrees(math.acos(dot))
            if abs(measured - self.angle) > self.angle_tolerance:
                failures.append(("orientation", measured))

        return failures

    def _collect_faces(self, select, selection, color):
        """The selected faces of each element of a selection, in world
        coordinates, as (entity, triangles) pairs. An empty selection
        selects all the faces of the element. Every selected face is
        kept in the display registry with the given color, as in
        OneObjectFace: the other faces of the object are not
        registered, the object keeps its own display color."""
        element_faces = []
        for ifc_file in select.dict_elements.keys():
            included = select.dict_elements[ifc_file]
            if not included:
                continue

            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=included,
            )
            if not iterator.initialize():
                continue

            while True:
                shape = iterator.get()
                entity = ifc_file.by_id(shape.id)
                vertices = np.asarray(get_vertices(shape.geometry), dtype=float)
                faces = np.asarray(get_faces(shape.geometry))
                if len(faces) > 0:
                    material_names = clash_utils.get_element_material_names(entity)
                    triangles = clash_utils.select_faces(
                        vertices,
                        faces,
                        selection,
                        material_names,
                    )
                    if len(triangles) > 0:
                        element_faces.append((entity, triangles))
                        # The selected faces, kept in the display
                        # registry, in the color of their group (blue
                        # for the source, orange for the target, as in
                        # OneObjectFace).
                        for triangle in triangles:
                            self.register_display_item(
                                "face",
                                ("face", [tuple(vertex) for vertex in triangle]),
                                color,
                                0.0,
                                element=entity,
                            )

                if not iterator.next():
                    break

        return element_faces

    def run(self):
        self.display_items.clear()
        self.select_source.run()
        self.select_target.run()

        source_elements = self._collect_faces(
            self.select_source, self.source_face_selection, (0, 0, 1)
        )
        target_elements = self._collect_faces(
            self.select_target, self.target_face_selection, (1, 0.45, 0)
        )

        for source_entity, source_triangles in source_elements:
            for target_entity, target_triangles in target_elements:
                if source_entity == target_entity:
                    # An element is not checked against itself, even
                    # when both selections contain it.
                    continue
                self._check_pairs(
                    source_entity,
                    source_triangles,
                    target_entity,
                    target_triangles,
                )

        if self.state == "Display_Input":
            return self.end_rule_action()
        self.end_rule_action()

    def _check_pairs(
        self, source_entity, source_triangles, target_entity, target_triangles
    ):
        """Every source face against every target face, one clash per
        pair per failed check."""
        for triangle_a in source_triangles:
            for triangle_b in target_triangles:
                for check, value in self._run_checks(triangle_a, triangle_b):
                    result = ClashResultTwoObjects(
                        source=source_entity,
                        target=target_entity,
                        state=True,
                    )
                    clash_utils.apply_check_measure(result.info, check, value)
                    normal_a, area_a = self._triangle_data(triangle_a)
                    normal_b, area_b = self._triangle_data(triangle_b)
                    result.info.add_face_pair(
                        (   # face de la source
                            tuple(float(v) for v in normal_a),
                            float(area_a),
                            [tuple(tuple(float(c) for c in vertex) for vertex in triangle_a)],
                        ),
                        (   # face de la target
                            tuple(float(v) for v in normal_b),
                            float(area_b),
                            [tuple(tuple(float(c) for c in vertex) for vertex in triangle_b)],
                        ),
                    )
                    self.result.append(result)


class ClearanceForDoors(RuleCheckTwoObjects):
    """Ensure that nothing obstructs the doors: a clearance zone is
    built for each door (the leaf sweep, or a rectangle), and any
    target object penetrating a zone by more than the tolerance raises
    a clash. See doc/2ObjectsRules/ClearanceForDoors.md.

    V1 of the swing detection reads the OperationType (IfcDoorType via
    IsTypedBy, IfcDoorPanelProperties via IsDefinedBy); the Curve2D
    geometry method is not implemented: without a usable operation
    type, the rule falls back on conservative rectangles on both
    sides.
    """

    def __init__(
        self,
        source,
        target,
        zone_shape="Arc",
        sides="Swing",
        leaves=None,
        width=None,
        depth=None,
        height=None,
        tolerance=0.001,
        state="Final",
    ):
        super().__init__(state, source, target)
        self.type = "ClearanceForDoors"

        if zone_shape not in ("Arc", "Rectangle"):
            raise ValueError(
                f"zone_shape must be 'Arc' or 'Rectangle', got '{zone_shape}'"
            )
        if sides not in ("Swing", "Both", "Front", "Back"):
            raise ValueError(
                f"sides must be 'Swing', 'Both', 'Front' or 'Back', got '{sides}'"
            )
        if leaves is not None and (not isinstance(leaves, int) or leaves < 1):
            raise ValueError(f"leaves must be None or an integer >= 1, got {leaves}")
        for dimension_name, dimension_value in (
            ("width", width),
            ("depth", depth),
            ("height", height),
        ):
            if dimension_value is not None and (
                not isinstance(dimension_value, (int, float)) or dimension_value <= 0
            ):
                raise ValueError(
                    f"{dimension_name} must be None or a positive number, "
                    f"got {dimension_value!r}"
                )
        if not isinstance(tolerance, (int, float)) or tolerance < 0:
            raise ValueError(f"tolerance must be a positive number, got {tolerance!r}")

        self.zone_shape = zone_shape
        self.sides = sides
        self.leaves = leaves
        self.width = float(width) if width is not None else None
        self.depth = float(depth) if depth is not None else None
        self.height = float(height) if height is not None else None
        self.tolerance = float(tolerance)

        # OpenCascade shapes for the zone checks, world meshes for the
        # door dimensions and the target vertices.
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)
        self.local_settings = ifcopenshell.geom.settings()
        self.world_settings = ifcopenshell.geom.settings()
        self.world_settings.set("USE_WORLD_COORDS", True)

    def _door_dimensions(self, door):
        """The width, thickness and height of the door, from its local
        mesh (width along the local X axis, height along Z)."""
        for ifc_file in self.select_source.dict_elements.keys():
            if door.file != ifc_file:
                continue
            iterator = ifcopenshell.geom.iterator(
                self.local_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=[door],
            )
            if not iterator.initialize():
                break
            shape = iterator.get()
            vertices = np.asarray(get_vertices(shape.geometry), dtype=float)
            return (
                float(vertices[:, 0].max() - vertices[:, 0].min()),
                float(vertices[:, 1].max() - vertices[:, 1].min()),
                float(vertices[:, 2].max() - vertices[:, 2].min()),
            )
        return (0.0, 0.0, 0.0)

    def _collect_targets(self):
        """The OCC shape and the world vertices of each target object."""
        targets = []
        for ifc_file in self.select_target.dict_elements.keys():
            included = self.select_target.dict_elements[ifc_file]
            if not included:
                continue

            occ_shapes = {}
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=included,
            )
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    entity = ifc_file.by_id(shape.data.id)
                    occ_shapes[entity.id()] = shape.geometry
                    if not iterator.next():
                        break

            iterator = ifcopenshell.geom.iterator(
                self.world_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=included,
            )
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    entity = ifc_file.by_id(shape.id)
                    occ_shape = occ_shapes.get(entity.id())
                    if occ_shape is not None:
                        targets.append(
                            {
                                "entity": entity,
                                "occ": occ_shape,
                                "vertices": np.asarray(
                                    get_vertices(shape.geometry), dtype=float
                                ),
                            }
                        )
                    if not iterator.next():
                        break

        return targets

    def _build_zones(self, door):
        """The clearance zones of one door.

        Each zone is a dict: leaf, leaf_type (the door OperationType),
        side ("Front"/"Back"), shape ("Arc"/"Rectangle"), dimensions
        and the OpenCascade solid.
        """
        origin, x_axis, y_axis, z_axis = clash_utils.get_local_placement_axes(door)
        width, thickness, door_height = self._door_dimensions(door)

        operation_type = clash_utils.get_door_operation_type(door)
        operation = clash_utils.parse_door_operation(operation_type)
        # Le type de vantail porté par le résultat (ZoneData.leaf) :
        # l'OperationType IFC, ou le mécanisme déduit si absent.
        leaf_type = operation_type if operation_type else operation["mechanism"]
        leaves = self.leaves if self.leaves is not None else operation["leaves"]
        leaf_width = width / leaves if leaves > 0 else width

        zone_width = self.width if self.width is not None else leaf_width
        zone_depth = self.depth if self.depth is not None else leaf_width
        zone_height = self.height if self.height is not None else max(door_height, 0.0)

        zones = []

        def add_rectangle(side_sign, side, leaf):
            zones.append(
                {
                    "leaf": leaf,
                    "leaf_type": leaf_type,
                    "side": side,
                    "shape": "Rectangle",
                    "width": zone_width,
                    "depth": zone_depth,
                    "height": zone_height,
                    "solid": clash_utils.make_box_zone(
                        origin,
                        x_axis,
                        y_axis,
                        z_axis,
                        zone_width,
                        zone_depth,
                        zone_height,
                        side_sign,
                    ),
                }
            )

        def add_arc(hinge, leaf):
            zones.append(
                {
                    "leaf": leaf,
                    "leaf_type": leaf_type,
                    "side": "Front",
                    "shape": "Arc",
                    "width": zone_width,
                    "depth": zone_width,
                    "height": zone_height,
                    "solid": clash_utils.make_arc_zone(
                        hinge,
                        x_axis,
                        y_axis,
                        z_axis,
                        zone_width,
                        zone_height,
                    ),
                }
            )

        if operation["mechanism"] == "sliding":
            # A sliding door cannot sweep: rectangles of passage. The
            # "Swing" side of a sliding door is both sides (V1
            # convention: the passage through the opening).
            if self.sides in ("Swing", "Both"):
                add_rectangle(1.0, "Front", 1)
                add_rectangle(-1.0, "Back", 1)
            elif self.sides == "Front":
                add_rectangle(1.0, "Front", 1)
            else:
                add_rectangle(-1.0, "Back", 1)
            return zones

        if operation["mechanism"] == "swing" and self.zone_shape == "Arc":
            # The leaves sweep toward the front (local +Y).
            for leaf_index, hinge_side in enumerate(operation["hinges"], start=1):
                if hinge_side == "left":
                    hinge = origin
                else:
                    hinge = origin + x_axis * width
                if self.sides in ("Swing", "Both", "Front"):
                    add_arc(hinge, leaf_index)
                if self.sides in ("Both", "Back"):
                    add_rectangle(-1.0, "Back", leaf_index)
            return zones

        if operation["mechanism"] == "swing" and self.zone_shape == "Rectangle":
            # Rectangles in front of each leaf.
            for leaf_index, hinge_side in enumerate(operation["hinges"], start=1):
                if hinge_side == "left":
                    leaf_origin = origin + x_axis * ((leaf_index - 1) * leaf_width)
                else:
                    leaf_origin = origin + x_axis * ((leaf_index - 1) * leaf_width)
                if self.sides in ("Swing", "Both", "Front"):
                    add_rectangle(1.0, "Front", leaf_index)
                if self.sides in ("Both", "Back"):
                    add_rectangle(-1.0, "Back", leaf_index)
            # Rectangle zones span the opening, not one per leaf: keep
            # the front rectangle single by deduplicating on the side.
            deduplicated = []
            seen = set()
            for zone in zones:
                key = (zone["side"], round(zone["width"], 9))
                if key in seen:
                    continue
                seen.add(key)
                deduplicated.append(zone)
            return deduplicated

        # No determined direction: conservative rectangles on both
        # sides, whatever Sides says.
        add_rectangle(1.0, "Front", 1)
        add_rectangle(-1.0, "Back", 1)
        return zones

    def run(self):
        self.display_items.clear()
        self.select_source.run()
        self.select_target.run()

        targets = self._collect_targets()

        for ifc_file in self.select_source.dict_elements.keys():
            for door in self.select_source.dict_elements[ifc_file] or []:
                zones = self._build_zones(door)

                # The clearance zones (the clash detection zones), kept
                # in the display registry.
                for zone in zones:
                    self.register_display_item(
                        "zone", zone["solid"], (0.5,0,1), 0.6, element=door
                    )

                for target in targets:
                    worst = None
                    for zone in zones:
                        dist_tool = BRepExtrema_DistShapeShape()
                        dist_tool.LoadS1(target["occ"])
                        dist_tool.LoadS2(zone["solid"])
                        dist_tool.Perform()
                        if dist_tool.Value() > 0:
                            # No contact with this zone.
                            continue

                        depth = clash_utils.max_penetration_depth(
                            zone["solid"], target["vertices"]
                        )
                        if depth > self.tolerance and (
                            worst is None or depth > worst[0]
                        ):
                            worst = (depth, zone)

                    if worst is not None:
                        depth, zone = worst
                        result = ClashResultTwoObjects(
                            source=door, target=target["entity"], state=True
                        )
                        result.info.penetration_depth = depth  # m — nominale
                        result.info.zone = ZoneData(
                            side=zone["side"],
                            leaf=zone["leaf_type"],
                            width=zone["width"],  # m
                            depth=zone["depth"],  # m
                            height=zone["height"],  # m
                        )
                        self.result.append(result)

        self.end_rule_action()


class FreeSpace(RuleCheckOneObject):
    """Check whether a cylinder of free space of a given diameter and
    height can be found in a room.

    The cylinder must fit entirely inside the footprint of each source
    object (its lowest face is the floor) and must not intersect any
    Context object (touching is allowed). The free placements are the
    region of the footprint eroded by the cylinder radius, minus the
    obstacles projected in the height slab of the cylinder (each
    projection grown by the radius). A placement exists as soon as
    this region is not empty; the reported placement is the point of
    the region with the largest clearance. A clash is raised for each
    source where no free placement is found. See
    doc/ComplexRules/FreeSpace.md.
    """

    # The mesh deflection of the obstacle projections is a fraction of
    # the cylinder radius; the touch epsilon keeps the tangential
    # placements (touching allowed) free.
    MESH_FRACTION = 25.0
    TOUCH_EPSILON = 1e-9

    def __init__(self, source, context, diameter=1.50, height=None, state="Final"):
        super().__init__(state, source)
        self.type = "FreeSpace"
        self.select_context: Select = context

        if not isinstance(diameter, (int, float)) or diameter <= 0:
            raise ValueError(
                f"diameter must be a positive number (m), got {diameter!r}"
            )
        if not isinstance(height, (int, float)) or height <= 0:
            raise ValueError(f"height is mandatory (m), got {height!r}")

        self.diameter = float(diameter)
        self.height = float(height)
        self.placements = {}

        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)
        self.mesh_settings = ifcopenshell.geom.settings()
        self.mesh_settings.set("USE_WORLD_COORDS", True)

    def _collect_context(self):
        """The OCC shape of each context object, with its bounding box
        (to pre-filter the obstacles of each source)."""
        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib

        obstacles = []
        for ifc_file in self.select_context.dict_elements.keys():
            included = self.select_context.dict_elements[ifc_file]
            if not included:
                continue
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=included,
            )
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    entity = ifc_file.by_id(shape.data.id)
                    box = Bnd_Box()
                    brepbndlib.Add(shape.geometry, box)
                    x_min, y_min, z_min, x_max, y_max, z_max = box.Get()
                    obstacles.append(
                        {
                            "entity": entity,
                            "occ": shape.geometry,
                            "bounds": (x_min, y_min, x_max, y_max),
                            "z_min": z_min,
                            "z_max": z_max,
                        }
                    )
                    if not iterator.next():
                        break
        return obstacles

    def _placement_margin(self, cylinder, disk, footprint, obstacles):
        """The shortest distance from the placed cylinder to the
        obstacles and to the footprint boundary. Touching is 0."""
        margin = footprint.boundary.distance(disk)
        for obstacle in obstacles:
            dist_tool = BRepExtrema_DistShapeShape()
            dist_tool.LoadS1(cylinder)
            dist_tool.LoadS2(obstacle["occ"])
            dist_tool.Perform()
            margin = min(margin, dist_tool.Value())
        return float(margin)

    def _obstacle_slab_footprint(self, obstacle, box, z_base):
        """The 2D projection of the part of an obstacle that lies in
        the height slab of the cylinder (a shapely polygon, possibly
        empty): the zone where an obstacle has a positive volume inside
        the cylinder."""
        from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common
        from OCC.Core.BRep import BRep_Tool
        from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
        from OCC.Core.TopAbs import TopAbs_FACE
        from OCC.Core.TopExp import TopExp_Explorer
        from OCC.Core.TopLoc import TopLoc_Location

        z_low = z_base + self.TOUCH_EPSILON
        z_high = z_base + self.height - self.TOUCH_EPSILON
        if z_high <= z_low:
            return shapely.Polygon()

        x_min, y_min, x_max, y_max = box
        slab = BRepPrimAPI_MakeBox(
            gp_Pnt(x_min, y_min, z_low), gp_Pnt(x_max, y_max, z_high)
        ).Shape()
        common = BRepAlgoAPI_Common(obstacle["occ"], slab)
        common.Build()
        if not common.IsDone():
            return shapely.Polygon()
        clipped = common.Shape()
        if clipped is None or clipped.IsNull():
            return shapely.Polygon()

        deflection = (self.diameter / 2.0) / self.MESH_FRACTION
        BRepMesh_IncrementalMesh(clipped, deflection).Perform()

        triangles = []
        explorer = TopExp_Explorer(clipped, TopAbs_FACE)
        while explorer.More():
            face = explorer.Current()
            location = TopLoc_Location()
            triangulation = BRep_Tool.Triangulation(face, location)
            if triangulation is not None:
                transform = location.Transformation()
                nodes = [
                    triangulation.Node(i).Transformed(transform)
                    for i in range(1, triangulation.NbNodes() + 1)
                ]
                for i in range(1, triangulation.NbTriangles() + 1):
                    a, b, c = triangulation.Triangle(i).Get()
                    triangle = shapely.Polygon(
                        [
                            (nodes[a - 1].X(), nodes[a - 1].Y()),
                            (nodes[b - 1].X(), nodes[b - 1].Y()),
                            (nodes[c - 1].X(), nodes[c - 1].Y()),
                        ]
                    )
                    if not triangle.is_empty:
                        triangles.append(triangle)
            explorer.Next()

        if not triangles:
            return shapely.Polygon()
        return shapely.union_all(triangles)

    def _search_placement(self, footprint, z_base, obstacles):
        """The free placements are the region of the footprint eroded
        by the cylinder radius, minus the obstacle projections of the
        height slab grown by the radius. The reported placement is the
        point of the region with the largest clearance. Returns None
        when no free placement exists."""
        radius = self.diameter / 2.0
        center_region = footprint.buffer(-radius)
        if center_region.is_empty:
            return None, None

        min_x, min_y, max_x, max_y = footprint.bounds
        # The projection box: an obstacle part farther than the radius
        # from the footprint cannot block a placement.
        pad = radius + 0.1
        box = (min_x - pad, min_y - pad, max_x + pad, max_y + pad)
        z_top = z_base + self.height
        for obstacle in obstacles:
            ox_min, oy_min, ox_max, oy_max = obstacle["bounds"]
            if ox_max < box[0] or ox_min > box[2] or oy_max < box[1] or oy_min > box[3]:
                continue
            if (
                obstacle["z_max"] < z_base + self.TOUCH_EPSILON
                or obstacle["z_min"] > z_top - self.TOUCH_EPSILON
            ):
                continue
            projection = self._obstacle_slab_footprint(obstacle, box, z_base)
            if projection.is_empty:
                continue
            # Grown by the radius, shrunk by the touch epsilon: the
            # tangential placements (touching allowed) stay free.
            blocked = projection.buffer(radius - self.TOUCH_EPSILON)
            center_region = center_region.difference(blocked)
            if center_region.is_empty:
                return None, None

        # The placement with the largest clearance: binary search the
        # deepest erosion that keeps a non-empty region.
        low, high = 0.0, max(max_x - min_x, max_y - min_y) / 2.0
        for _ in range(20):
            middle = (low + high) / 2.0
            if center_region.buffer(-middle).is_empty:
                high = middle
            else:
                low = middle
        point = center_region.buffer(-low).representative_point()

        disk = shapely.Point(point.x, point.y).buffer(radius, quad_segs=32)
        cylinder = clash_utils.cylinder_solid(
            point.x, point.y, z_base, radius, self.height
        )
        margin = self._placement_margin(cylinder, disk, footprint, obstacles)
        return (point.x, point.y), margin

    def run(self):
        self.display_items.clear()
        self.select_source.run()

        self.select_context.list_ifc_path = self.select_source.list_ifc_path
        self.select_context.list_ifc_file = self.select_source.list_ifc_file
        self.select_context.run()

        obstacles = self._collect_context()

        # The context objects (the obstacles of the free space search),
        # kept in the display registry.
        for obstacle in obstacles:
            self.register_display_item(
                "context",
                obstacle["occ"],
                (0.5, 0.5, 0.5),
                0.85,
                element=obstacle["entity"],
            )

        for ifc_file in self.select_source.dict_elements.keys():
            for source in self.select_source.dict_elements[ifc_file] or []:
                iterator = ifcopenshell.geom.iterator(
                    self.mesh_settings,
                    ifc_file,
                    multiprocessing.cpu_count(),
                    include=[source],
                )
                footprint, z_base = shapely.Polygon(), 0.0
                if iterator.initialize():
                    shape = iterator.get()
                    vertices = np.asarray(get_vertices(shape.geometry), dtype=float)
                    faces = np.asarray(get_faces(shape.geometry))
                    footprint, z_base = clash_utils.lowest_footprint(vertices, faces)

                if footprint.is_empty:
                    # No footprint: no placement can be evaluated.
                    self.result.append(ClashResultOneObject(source=source, state=True))
                    continue

                found, margin = self._search_placement(footprint, z_base, obstacles)
                if found is None:
                    self.result.append(ClashResultOneObject(source=source, state=True))
                    # No free placement: the probe stays at the center
                    # of the footprint in the display registry.
                    center = footprint.representative_point()
                    probe_position = (center.x, center.y)
                else:
                    self.placements[source] = {
                        "position": (found[0], found[1], z_base),
                        "margin": margin,
                    }
                    probe_position = found

                # The probe cylinder (the clash detection zone), kept
                # in the display registry.
                self.register_display_item(
                    "zone",
                    clash_utils.cylinder_solid(
                        probe_position[0],
                        probe_position[1],
                        z_base,
                        self.diameter / 2.0,
                        self.height,
                    ),
                    (0.5,0,1),
                    0.6,
                    element=source,
                )

        self.end_rule_action()

