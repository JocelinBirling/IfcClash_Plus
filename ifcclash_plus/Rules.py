from RuleClass import (
    RuleCheckOneObject,
    RuleCheckTwoObjects,
    ClashResultOneObject,
    ClashResultTwoObjects,
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
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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
            self.display.FitAll()
            self.start_display()
            return 0
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
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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
            self.display.FitAll()
            self.start_display()
            return 0
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

    def run(self):
        if self.top_or_bot_method == "Top":
            direction = (0.0, 0.0, 1)
        if self.top_or_bot_method == "Bottom":
            direction = (0.0, 0.0, -1)

        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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

                    if self.state == "Display_Input":
                        for face in result["extrem_faces"]:
                            self._add_face_to_display(face, (1, 0, 0))

                    if self.surface_min < area < self.surface_max:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
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
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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
            self.display.FitAll()
            self.start_display()
            return 0
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
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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
            self.display.FitAll()
            self.start_display()
            return 0
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
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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

                    if self.state == "Display_Input":
                        self._add_obb_to_display(obb, (1, 0, 0))

                    if self.length_min < value_to_check < self.length_max:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
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
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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

                    if self.state == "Display_Input":
                        self._add_obb_to_display(obb, (1, 0, 0))

                    x_size = obb.XHSize() * 2
                    y_size = obb.YHSize() * 2
                    z_size = obb.ZHSize() * 2

                    # Identifier les deux faces les plus larges ou étroites
                    # On compare les dimensions pour déterminer les faces larges ou étroites
                    # dimensions = {"X": x_size, "Y": y_size, "Z": z_size}
                    dimensions = {
                        "X": x_size,
                        "Y": y_size,
                    }  # I don't wan to get the high of the object. But i am not sure that Z is the height. @todo check that Z is always the height of an object.

                    # Trouver les deux dimensions les plus grandes ou les plus petites
                    sorted_dimensions = sorted(
                        dimensions.items(),
                        key=lambda item: item[1],
                        reverse=(self.direction_method == "wide"),
                    )

                    # Les deux faces les plus larges ou étroites sont les deux premières dimensions
                    value_to_check = sorted_dimensions[0][1]

                    if self.length_min < value_to_check < self.length_max:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
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

        self.select_source.run()
        if self.state == "Display_Input":
            self._display_input_generic()

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

                    if self.state == "Display_Input":
                        self._add_gp_Dir_to_display(geom, dir1, (1, 0, 0))
                        self._add_gp_Dir_to_display(geom, occ_orientation, (0, 1, 0))

                    if self.direction_method == "Parrallel":
                        check_direction = is_parrallel
                    elif self.direction_method == "Perpendicular":
                        check_direction = not is_parrallel

                    if check_direction:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
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
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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
                    if self.state == "Display_Input":
                        self._add_gp_Dir_to_display(geom, direction, (1, 0, 0))

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
                    if self.state == "Display_Input":
                        self._add_gp_Dir_to_display(geom, direction, (1, 0, 0))
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
            self.display.FitAll()
            self.start_display()
            return 0

        self.end_rule_action()


class Intersection(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance=0.1, state="Final"):
        super().__init__(state, source, target)
        self.type = "Intersection"
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        source_elements = []
        target_elements = []

        if self.state == "Display_Input":
            self._display_input_generic()

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
            a_file = ifcopenshell.file.from_pointer(result.a.file_pointer())
            a__object = a_file.by_id(result.a.id_)

            b__file = ifcopenshell.file.from_pointer(result.b.file_pointer())
            b_object = b__file.by_id(result.b.id_)

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
            self.display.FitAll()
            self.start_display()
            return 0
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
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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
            a_file = ifcopenshell.file.from_pointer(result.a.file_pointer())
            a__object = a_file.by_id(result.a.id_)

            b__file = ifcopenshell.file.from_pointer(result.b.file_pointer())
            b_object = b__file.by_id(result.b.id_)

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
            self.display.FitAll()
            self.start_display()
            return 0
        self.end_rule_action()


class Collision(RuleCheckTwoObjects):
    def __init__(self, source, target, allow_touching=False, state="Final"):
        super().__init__(state, source, target)
        self.type = "Collision"
        self.allow_touching = allow_touching
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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
            a_file = ifcopenshell.file.from_pointer(result.a.file_pointer())
            a__object = a_file.by_id(result.a.id_)

            b__file = ifcopenshell.file.from_pointer(result.b.file_pointer())
            b_object = b__file.by_id(result.b.id_)

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
            self.display.FitAll()
            self.start_display()
            return 0
        self.end_rule_action()


class Ray_Check(RuleCheckTwoObjects):
    def __init__(self, source, target, context, max_ray_length, state="Final"):
        super().__init__(state, source, target)
        self.type = "RayCheck"
        self.select_context: Select = context
        self.max_ray_length: float = max_ray_length
        self.geom_settings = ifcopenshell.geom.settings()

    def display_result(self):
        # Ray_Check also displays its context elements
        self._display_result_generic()
        self._display_context()

        self.display.FitAll()
        self.start_display()

    def _display_context(self):

        # Imports for center calculation and edge display
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib
        from OCC.Core.gp import gp_Pnt
        from OCC.Core.AIS import AIS_Shape
        from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
        from OCC.Display.SimpleGui import init_display

        def add_to_display(entity, geom_settings, color):
            shape = ifcopenshell.geom.create_shape(geom_settings, entity)
            geom = shape.geometry

            ais_shape = AIS_Shape(geom)

            ais_shape.SetColor(color)
            ais_shape.SetTransparency(0.9)
            self.display.Context.Display(ais_shape, True)

        geom_settings = ifcopenshell.geom.settings()
        geom_settings.set("USE_PYTHON_OPENCASCADE", True)

        grey = Quantity_Color(0.5, 0.5, 0.5, Quantity_TOC_RGB)

        for element in self.select_context.list_of_elements:
            add_to_display(element, geom_settings, grey)

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

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        self.select_context.list_ifc_path = self.select_source.list_ifc_path
        self.select_context.list_ifc_file = self.select_source.list_ifc_file
        self.select_context.run()

        self.select_source.create_list_of_element()
        self.select_target.create_list_of_element()
        self.select_context.create_list_of_element()

        if self.state == "Display_Input":
            self._display_input_generic()
            self._display_context()

        self.add_to_tree(self.select_context, "UB")

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

                results = self.tree.select_ray(
                    source_position, direction, length=distance
                )

                # A ray_element has: distance, dot_product, instance,
                # normal, position, ray_distance, style_index
                # The clash appears when the source and the target are in
                # direct view: no context object stands between them.
                in_direct_view = True
                for result in results:
                    result_file = ifcopenshell.file.from_pointer(
                        result.instance.file_pointer()
                    )
                    result_object = result_file.by_id(result.instance.id_)

                    # The source and the target never block their own ray
                    if result_object == source or result_object == target:
                        continue

                    # A context object stands between the source and the target
                    in_direct_view = False
                    break

                if in_direct_view:
                    self.result.append(
                        ClashResultTwoObjects(source=source, target=target, state=True)
                    )

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
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
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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

                    extrem_faces = (
                        clash_utils.get_faces_visible_from_direction_with_plane(
                            shape=geom, direction=source_direction
                        )
                    )
                    if self.state == "Display_Input":
                        for face in extrem_faces["visible_faces"]:
                            self._add_face_to_display(face, (1, 0, 0))

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

                    if self.state == "Display_Input":
                        for face in extrem_faces["visible_faces"]:
                            self._add_face_to_display(face, (1, 0, 0))

                    dict = {
                        "entity": entity,
                        "extrem_faces": extrem_faces["visible_faces"],
                        "obb": obb,
                    }
                    targets_data.append(dict)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
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

                for source_face in source_geom:
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
                    for i in range(1, dist_tool.NbSolution()):
                        pt_source = dist_tool.PointOnShape1(i)
                        pt_target = dist_tool.PointOnShape2(i)

                        if pt_source.Z() > pt_target.Z():
                            continue

                        if pt_source.X() - pt_target.X() < 1e-3:
                            if pt_source.Y() - pt_target.Y() < 1e-3:
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
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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
                    if self.state == "Display_Input":
                        for face in extrem_faces["visible_faces"]:
                            self._add_face_to_display(face, (1, 0, 0))

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
                    if self.state == "Display_Input":
                        for face in extrem_faces["visible_faces"]:
                            self._add_face_to_display(face, (1, 0, 0))

                    dict = {
                        "entity": entity,
                        "extrem_faces": extrem_faces["visible_faces"],
                        "obb": obb,
                    }
                    targets_data.append(dict)

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0

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

                for source_face in source_geom:
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
                    for i in range(1, dist_tool.NbSolution()):
                        pt_source = dist_tool.PointOnShape1(i)
                        pt_target = dist_tool.PointOnShape2(i)

                        if pt_source.Z() < pt_target.Z():
                            continue

                        if pt_source.X() - pt_target.X() < 1e-3:
                            if pt_source.Y() - pt_target.Y() < 1e-3:
                                dict_to_return["is_below"] = "Right_Below"
                                return dict_to_return

                        dict_to_return["list_of_point_on_target"].append(pt_target)

        if dict_to_return["list_of_point_on_target"] == []:
            dict_to_return["is_below"] = "Too_Far"
        else:
            dict_to_return["is_below"] = "Need_More_Check"

        return dict_to_return

    def _display_input_specific(self):
        from OCC.Core.AIS import AIS_Shape
        from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

        settings = ifcopenshell.geom.settings()
        settings.set("USE_WORLD_COORDS", True)

        color = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )
            color = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry

                    obb = create_obb_from_TopoDs_Shape(geom)
                    clash_obb = obb.detach_top_by_extrude(self.tolerance)
                    compound = clash_obb.to_TopoDS_Solid()

                    ais_shape = AIS_Shape(compound)
                    ais_shape.SetColor(color)
                    ais_shape.SetTransparency(0.2)
                    self.display.Context.Display(ais_shape, True)

                    if not iterator.next():
                        break


class Template(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance=0.1, state="Final"):
        super().__init__(state, source, target)
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings(USE_WORLD_COORDS=False)

    def run(self):

        if self.state == "Display_Input":
            self._display_input_generic()

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0

        self.end_rule_action()


class OBB_Above(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance, state="Final"):
        super().__init__(state, source, target)
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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

                    if self.state == "Display_Input":
                        self._add_obb_to_display(clash_obb)

                    compound = clash_obb.to_TopoDS_Solid()
                    source_geoms.append(
                        {"entity": entity, "geom": compound, "obb": clash_obb}
                    )

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
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
                    self.result.append(result)
        self.end_rule_action()

    def _display_input_specific(self):
        from OCC.Core.AIS import AIS_Shape
        from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

        settings = ifcopenshell.geom.settings()
        settings.set("USE_WORLD_COORDS", True)

        color = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )
            color = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry

                    obb = create_obb_from_TopoDs_Shape(geom)
                    clash_obb = obb.detach_top_by_extrude(self.tolerance)
                    compound = clash_obb.to_TopoDS_Solid()

                    ais_shape = AIS_Shape(compound)
                    ais_shape.SetColor(color)
                    ais_shape.SetTransparency(0.2)
                    self.display.Context.Display(ais_shape, True)

                    if not iterator.next():
                        break


class OBB_Below(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance, state="Final"):
        super().__init__(state, source, target)
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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

                    if self.state == "Display_Input":
                        self._add_obb_to_display(clash_obb)

                    compound = clash_obb.to_TopoDS_Solid()
                    source_geoms.append(
                        {"entity": entity, "geom": compound, "obb": clash_obb}
                    )

                    if not iterator.next():
                        break
        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
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
                    self.result.append(result)
        self.end_rule_action()

    def _display_input_specific(self):
        from OCC.Core.AIS import AIS_Shape
        from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

        settings = ifcopenshell.geom.settings()
        settings.set("USE_WORLD_COORDS", True)

        color = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )
            color = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry

                    obb = create_obb_from_TopoDs_Shape(geom)
                    clash_obb = obb.detach_bottom_by_extrude(self.tolerance)
                    compound = clash_obb.to_TopoDS_Solid()

                    ais_shape = AIS_Shape(compound)
                    ais_shape.SetColor(color)
                    ais_shape.SetTransparency(0.2)
                    self.display.Context.Display(ais_shape, True)

                    if not iterator.next():
                        break


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
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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

                    if self.state == "Display_Input":
                        color = (1, 0, 0)
                        self._add_obb_to_display(clash_obb_1, color)
                        self._add_obb_to_display(clash_obb_2, color)

                    compound_1 = clash_obb_1.to_TopoDS_Solid()
                    compound_2 = clash_obb_2.to_TopoDS_Solid()
                    source_obbs.append(
                        {"entity": entity, "geom": compound_1, "obb": clash_obb_1}
                    )
                    source_obbs.append(
                        {"entity": entity, "geom": compound_2, "obb": clash_obb_2}
                    )

                    if not iterator.next():
                        break

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0

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
                    self.result.append(result)

        self.end_rule_action()

    def _display_input_specific(self):
        from OCC.Core.AIS import AIS_Shape
        from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

        settings = ifcopenshell.geom.settings()
        settings.set("USE_WORLD_COORDS", True)

        color = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )
            color = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry

                    obb = create_obb_from_TopoDs_Shape(geom)
                    # obb =create_obb_with_fixed_z(geom)
                    main_directions = obb.get_two_main_direction_OBB_shape(
                        self.direction_method
                    )
                    clash_obb_1 = obb.detach_side_by_extrude(
                        main_directions[0], self.tolerance
                    )
                    clash_obb_2 = obb.detach_side_by_extrude(
                        main_directions[1], self.tolerance
                    )

                    compound_1 = clash_obb_1.to_TopoDS_Solid()
                    compound_2 = clash_obb_2.to_TopoDS_Solid()

                    ais_shape = AIS_Shape(compound_1)
                    ais_shape.SetColor(color)
                    ais_shape.SetTransparency(0.2)
                    self.display.Context.Display(ais_shape, True)

                    ais_shape = AIS_Shape(compound_2)
                    ais_shape.SetColor(color)
                    ais_shape.SetTransparency(0.2)
                    self.display.Context.Display(ais_shape, True)

                    if not iterator.next():
                        break


class OBB_Custom(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance, state="Final"):
        super().__init__(state, source, target)
        self.list_of_modifications: list[str] = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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

                    for clash_obb in self._create_list_of_obb(geom):
                        compound = clash_obb.to_TopoDS_Solid()
                        source_geoms.append(
                            {"entity": entity, "geom": compound, "obb": clash_obb}
                        )

                        if self.state == "Display_Input":
                            color = (1, 0, 0)
                            self._add_obb_to_display(clash_obb, color)

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
            self.display.FitAll()
            self.start_display()
            return 0

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
                    self.result.append(result)
        self.end_rule_action()

    def _create_list_of_obb(self, geom):

        # expand_sides
        # detach_top_by_extrude
        # detach_bottom_by_extrude
        # extend_up
        # extend_down
        # NEW_OBB
        obb = create_obb_from_TopoDs_Shape(geom)  # Why not use

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

    The alignment is tested on the main axis of the OBB of each object,
    not on points. A single global element (a fitted line or plane) is
    least-squares fitted on all the objects: the group gathers the objects
    whose offset stays within the tolerance. If the group has at least
    Min_Group members the alignment is valid and the objects outside the
    group clash, otherwise no valid alignment exists and all the objects
    clash. See doc/ComplexRules/Alignement.md.
    """

    # An axis within 45 degrees of the global Z counts as vertical when
    # the orientation is auto-detected.
    VERTICAL_COSINE = math.cos(math.radians(45))

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
        self.select_source.run()

        if self.state == "Display_Input":
            self._display_input_generic()

        objects = self._collect_axis_data()

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0

        offsets = self._compute_offsets(objects)
        self.alignment = self._build_alignment_info(objects, offsets)

        clash_flags = clash_utils.alignment_clash_flags(
            offsets, self.tolerance, self.min_group
        )
        for one_object, clash, offset in zip(objects, clash_flags, offsets):
            if clash:
                result = ClashResultOneObject(source=one_object["entity"], state=True)
                result.offset = offset
                self.result.append(result)

        self.end_rule_action()

    def _collect_axis_data(self):
        """The main axis of the OBB of each selected object.

        The main axis is the OBB axis with the largest half size. The axis
        segment (center +/- main direction * main half size) carries the
        geometric data of the alignment.
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
                    obb.XDirection(),
                    obb.YDirection(),
                    obb.ZDirection(),
                ]
                half_sizes = [obb.XHSize(), obb.YHSize(), obb.ZHSize()]

                main_index = max(range(3), key=lambda i: half_sizes[i])
                main_direction = directions[main_index]
                objects.append(
                    {
                        "entity": entity,
                        "center": np.array(
                            [center.X(), center.Y(), center.Z()]
                        ),
                        "main_axis": np.array(
                            [
                                main_direction.X(),
                                main_direction.Y(),
                                main_direction.Z(),
                            ]
                        ),
                        "half_main": half_sizes[main_index],
                    }
                )

                if not iterator.next():
                    break

        return objects

    def _detect_orientation(self, objects):
        """Dominant orientation of the set, used when axis is None.

        An object votes vertical when its main axis is within 45 degrees
        of the global Z. A tie goes to Vertical.
        """
        vertical_votes = sum(
            1
            for one_object in objects
            if abs(one_object["main_axis"][2]) >= self.VERTICAL_COSINE
        )
        if vertical_votes >= len(objects) - vertical_votes:
            return "Vertical"
        return "Horizontal"

    def _compute_offsets(self, objects):
        """Offset of each object to the globally fitted element.

        Vertical (and Horizontal with a Plane fit): the plan projections of
        the objects are fitted on one common least-squares line, the fitted
        plane of the facade case being the vertical extrusion of that line.
        The offset of an object is the plan distance between its projected
        center and the fitted line.

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

        if orientation == "Vertical" or self.alignment_type == "Plane":
            plan_points = [one_object["center"][:2] for one_object in objects]
            line_origin, line_direction = clash_utils.least_squares_line_2d(
                plan_points
            )
            self._fitted = {
                "element": "Line" if orientation == "Vertical" else "Plane",
                "origin": line_origin,
                "direction": line_direction,
            }
            return [
                clash_utils.point_line_distance(point, line_origin, line_direction)
                for point in plan_points
            ]

        # Horizontal, Line: collinear axes in 3D
        segments = [
            [
                one_object["center"] - one_object["main_axis"] * one_object["half_main"],
                one_object["center"] + one_object["main_axis"] * one_object["half_main"],
            ]
            for one_object in objects
        ]
        all_endpoints = [endpoint for segment in segments for endpoint in segment]
        line_origin, line_direction = clash_utils.least_squares_line_3d(
            all_endpoints
        )
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

    def _build_alignment_info(self, objects, offsets):
        """The alignment found: the fitted element and its member objects.

        Returns None when the set is empty. The members are the objects of
        the group (offset within the tolerance), not only the clashing ones.
        """
        if not objects:
            return None

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
class SurfaceRecover(RuleCheckTwoObjects):
    """Check that the contact surface between two objects covers an
    expected value, defined by a min and a max.

    Only pairs whose distance is below the tolerance are analyzed: pairs
    not in contact produce no result. The extreme faces of the two objects
    along the direction are paired, the contact area is the sum of the
    disjoint contact zones (quasi coplanar triangles at a distance below
    the tolerance), and a clash is raised when the covering value is
    outside [Min_Covering, Max_Covering]. See doc/2ObjectsRules/SurfaceRecover.md.
    """

    # Two facing triangles are paired when their normals are opposite
    # within 25 degrees.
    PAIRING_COSINE = -math.cos(math.radians(25))

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
                np.asarray(direction, dtype=float)
                / np.linalg.norm(direction)
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
                            "centroid": np.asarray(vertices, dtype=float).mean(
                                axis=0
                            ),
                        }
                    )
                    if not iterator.next():
                        break

        return elements

    def run(self):
        self.select_source.run()
        self.select_target.run()

        if self.state == "Display_Input":
            self._display_input_generic()

        sources = self._collect_geometry(self.select_source)
        targets = self._collect_geometry(self.select_target)

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0

        for source in sources:
            for target in targets:
                # The OBB prefilter keeps the pairs whose bounding boxes
                # are within the tolerance, the exact distance is checked
                # afterwards.
                if (
                    source["obb"].min_distance_to_obb(target["obb"])
                    > self.tolerance
                ):
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
                )
                target_triangles = clash_utils.extreme_triangles(
                    target["vertices"],
                    target["faces"],
                    -direction,
                    tolerance=self.tolerance,
                )

                contact_area = clash_utils.contact_area_between_triangle_sets(
                    source_triangles,
                    target_triangles,
                    direction,
                    tolerance=self.tolerance,
                    pairing_cosine=self.PAIRING_COSINE,
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
                    result.distance_between = distance
                    result.surface_contact_area = contact_area
                    result.ratio = ratio
                    result.source_face = {
                        "normal": tuple(float(v) for v in direction),
                        "area": clash_utils.triangles_projected_area(
                            source_triangles, direction
                        ),
                    }
                    result.target_face = {
                        "normal": tuple(float(-v) for v in direction),
                        "area": clash_utils.triangles_projected_area(
                            target_triangles, -direction
                        ),
                    }
                    self.result.append(result)

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
    are transparent to their own rays. The hit ratio over the rays
    actually cast must reach the Threshold, otherwise the pair clashes.
    See doc/2ObjectsRules/DirectView.md.

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
            raise ValueError(
                f"threshold must be a percentage, got {threshold!r}"
            )
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
        self.max_distance = (
            float(max_distance) if max_distance is not None else None
        )

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
                vertices = np.asarray(
                    get_vertices(shape.geometry), dtype=float
                )
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
        emitter_faces = self._faces_toward(
            emitter_mesh, receiver_mesh["centroid"]
        )
        receiver_faces = self._faces_toward(
            receiver_mesh, emitter_mesh["centroid"]
        )

        if len(emitter_faces) == 0 or len(receiver_faces) == 0:
            return

        emitter_areas = 0.5 * np.linalg.norm(
            np.cross(
                emitter_faces[:, 1] - emitter_faces[:, 0],
                emitter_faces[:, 2] - emitter_faces[:, 0],
            ),
            axis=1,
        )
        counts = clash_utils.plan_ray_counts(
            list(emitter_areas), self.ray_count
        )

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
        self.select_source.run()
        self.select_target.run()

        # The context needs the same files as the source to be able to run.
        self.select_context.list_ifc_path = self.select_source.list_ifc_path
        self.select_context.list_ifc_file = self.select_source.list_ifc_file
        self.select_context.run()

        if self.state == "Display_Input":
            self._display_input_generic()

        self.tree = ifcopenshell.geom.tree()
        self.add_to_tree(self.select_context, "UB")

        source_meshes = self._collect_meshes(self.select_source)
        target_meshes = self._collect_meshes(self.select_target)

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0

        if self.ray_source == "Both":
            emitters_of = lambda source_mesh, target_mesh: [
                (source_mesh, target_mesh),
                (target_mesh, source_mesh),
            ]
        elif self.ray_source == "Source":
            emitters_of = lambda source_mesh, target_mesh: [
                (source_mesh, target_mesh)
            ]
        else:
            emitters_of = lambda source_mesh, target_mesh: [
                (target_mesh, source_mesh)
            ]

        threshold_fraction = self.threshold / 100.0

        for source_entity, source_mesh in source_meshes.items():
            for target_entity, target_mesh in target_meshes.items():
                if source_entity == target_entity:
                    continue

                planned = self.ray_count * len(
                    emitters_of(source_mesh, target_mesh)
                )
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

                hit_ratio = 100.0 * hits / casts if casts > 0 else 0.0
                if hit_ratio < self.threshold:
                    result = ClashResultTwoObjects(
                        source=source_entity,
                        target=target_entity,
                        state=True,
                    )
                    result.hit_ratio = hit_ratio
                    result.rays_cast = casts
                    result.rays_planned = planned
                    result.hit_segments = hit_segments
                    result.blocked_segments = blocked_segments
                    self.result.append(result)

        self.end_rule_action()
class OneObjectFace(RuleCheckOneObject):
    """Run face-level checks within a single object.

    The faces of group A and group B are selected with two
    FaceSelection dictionaries (the schema of the FaceCheck family),
    every face of A is paired with every face of B, and each pair must
    pass all the enabled checks: distance (min/max, adjacent faces
    skipped on demand), intersection (crossing deeper than a tolerance)
    and orientation (angle between the normals). One clash is raised per
    pair per failed check. See doc/1ObjectsRules/OneObjectFace.md.
    """

    def __init__(
        self,
        source,
        face_a_selection=None,
        face_b_selection=None,
        distance=False,
        min=None,
        max=None,
        skip_adjacent=True,
        intersection=False,
        intersection_tolerance=None,
        orientation=False,
        angle=None,
        angle_tolerance=None,
        state="Final",
    ):
        super().__init__(state, source)
        self.type = "OneObjectFace"

        self.face_a_selection = clash_utils.validate_face_selection(
            face_a_selection
        )
        self.face_b_selection = clash_utils.validate_face_selection(
            face_b_selection
        )

        if not (distance or intersection or orientation):
            raise ValueError(
                "OneObjectFace needs at least one enabled check: "
                "distance, intersection or orientation"
            )

        if distance:
            for bound_name, bound_value in (("min", min), ("max", max)):
                if bound_value is not None and (
                    not isinstance(bound_value, (int, float))
                    or bound_value < 0
                ):
                    raise ValueError(
                        f"{bound_name} must be a positive number (m), "
                        f"got {bound_value!r}"
                    )
            if min is not None and max is not None and min > max:
                raise ValueError(f"min ({min}) must not exceed max ({max})")
            if not isinstance(skip_adjacent, bool):
                raise ValueError(
                    f"skip_adjacent must be a boolean, got {skip_adjacent!r}"
                )
        self.distance = distance
        self.min = float(min) if min is not None else None
        self.max = float(max) if max is not None else None
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
            if (
                not isinstance(angle_tolerance, (int, float))
                or angle_tolerance < 0
            ):
                raise ValueError(
                    "angle_tolerance must be a positive number (degrees), "
                    f"got {angle_tolerance!r}"
                )
        self.orientation = orientation
        self.angle = float(angle) if angle is not None else None
        self.angle_tolerance = float(angle_tolerance) if angle_tolerance is not None else 0.0

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
            adjacent = clash_utils.triangles_share_geometry(triangle_a, triangle_b)
            if not (self.skip_adjacent and adjacent):
                measured = clash_utils.distance_between_triangles(
                    triangle_a, triangle_b
                )
                if self.min is not None and measured < self.min:
                    failures.append(("distance", measured))
                elif self.max is not None and measured > self.max:
                    failures.append(("distance", measured))

        if self.intersection:
            if clash_utils.triangles_cross_properly(triangle_a, triangle_b):
                depth = clash_utils.triangle_penetration_depth(
                    triangle_a, triangle_b
                )
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
        self.select_source.run()

        if self.state == "Display_Input":
            self._display_input_generic()

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
                vertices = np.asarray(
                    get_vertices(shape.geometry), dtype=float
                )
                faces = np.asarray(get_faces(shape.geometry))
                if len(faces) > 0:
                    material_names = clash_utils.get_element_material_names(
                        entity
                    )
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

                    self._check_pairs(entity, group_a, group_b)

                if not iterator.next():
                    break

        if self.state == "Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
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
                    result.check = check
                    result.value = value
                    normal_a, area_a = self._triangle_data(triangle_a)
                    normal_b, area_b = self._triangle_data(triangle_b)
                    result.face_a = {
                        "normal": tuple(float(v) for v in normal_a),
                        "area": float(area_a),
                    }
                    result.face_b = {
                        "normal": tuple(float(v) for v in normal_b),
                        "area": float(area_b),
                    }
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
                not isinstance(dimension_value, (int, float))
                or dimension_value <= 0
            ):
                raise ValueError(
                    f"{dimension_name} must be None or a positive number, "
                    f"got {dimension_value!r}"
                )
        if not isinstance(tolerance, (int, float)) or tolerance < 0:
            raise ValueError(
                f"tolerance must be a positive number, got {tolerance!r}"
            )

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
            vertices = np.asarray(
                get_vertices(shape.geometry), dtype=float
            )
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

        Each zone is a dict: leaf, side ("Front"/"Back"), shape
        ("Arc"/"Rectangle"), dimensions and the OpenCascade solid.
        """
        origin, x_axis, y_axis, z_axis = clash_utils.get_local_placement_axes(
            door
        )
        width, thickness, door_height = self._door_dimensions(door)

        operation = clash_utils.parse_door_operation(
            clash_utils.get_door_operation_type(door)
        )
        leaves = self.leaves if self.leaves is not None else operation["leaves"]
        leaf_width = width / leaves if leaves > 0 else width

        zone_width = self.width if self.width is not None else leaf_width
        zone_depth = self.depth if self.depth is not None else leaf_width
        zone_height = (
            self.height if self.height is not None else max(door_height, 0.0)
        )

        zones = []

        def add_rectangle(side_sign, side, leaf):
            zones.append(
                {
                    "leaf": leaf,
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
                    leaf_origin = origin + x_axis * (
                        (leaf_index - 1) * leaf_width
                    )
                else:
                    leaf_origin = origin + x_axis * (
                        (leaf_index - 1) * leaf_width
                    )
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
        self.select_source.run()
        self.select_target.run()

        if self.state == "Display_Input":
            self._display_input_generic()

        targets = self._collect_targets()

        for ifc_file in self.select_source.dict_elements.keys():
            for door in self.select_source.dict_elements[ifc_file] or []:
                zones = self._build_zones(door)

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
                        result.penetration_depth = depth
                        result.zone = {
                            "shape": zone["shape"],
                            "side": zone["side"],
                            "leaf": zone["leaf"],
                            "width": zone["width"],
                            "depth": zone["depth"],
                            "height": zone["height"],
                        }
                        self.result.append(result)

        self.end_rule_action()
class FreeSpace(RuleCheckOneObject):
    """Check whether a cylinder of free space of a given diameter and
    height can be found in a room.

    The cylinder must fit entirely inside the footprint of each source
    object (its lowest face is the floor) and must not intersect any
    Context object (touching is allowed). A regular grid of candidates
    covers the footprint, refined locally around the best node; the
    first free placement wins. A clash is raised for each source where
    no free placement is found. See doc/ComplexRules/FreeSpace.md.
    """

    # The grid step is a fraction of the diameter; the refinement step
    # is a fraction of the grid step.
    GRID_FRACTION = 4.0
    REFINEMENT_FRACTION = 4.0

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
        """The OCC shape of each context object."""
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
                    obstacles.append({"entity": entity, "occ": shape.geometry})
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

    def _is_free(self, x, y, z_base, footprint, obstacles):
        """A placement is free when the cylinder fits inside the
        footprint and does not intersect any obstacle (touching
        allowed: an intersection needs a positive volume)."""
        radius = self.diameter / 2.0
        disk = shapely.Point(x, y).buffer(radius, quad_segs=32)
        if not footprint.contains(disk):
            return None, None

        cylinder = clash_utils.cylinder_solid(x, y, z_base, radius, self.height)
        for obstacle in obstacles:
            dist_tool = BRepExtrema_DistShapeShape()
            dist_tool.LoadS1(cylinder)
            dist_tool.LoadS2(obstacle["occ"])
            dist_tool.Perform()
            if dist_tool.Value() > 0:
                continue
            if clash_utils.shapes_intersect_volume(cylinder, obstacle["occ"]) > 1e-9:
                return None, None

        margin = self._placement_margin(cylinder, disk, footprint, obstacles)
        return (x, y), margin

    def _search_placement(self, footprint, z_base, obstacles):
        """Grid search then local refinement; the first free placement
        wins. Returns None when no free placement exists."""
        radius = self.diameter / 2.0
        min_x, min_y, max_x, max_y = footprint.bounds

        step = self.diameter / self.GRID_FRACTION
        best_score = None
        best_node = None

        # The grid starts at radius from the walls: the tangent
        # placements (touching allowed) are candidates like the others.
        x = min_x + radius
        while x <= max_x - radius + 1e-9:
            y = min_y + radius
            while y <= max_y - radius + 1e-9:
                found, margin = self._is_free(x, y, z_base, footprint, obstacles)
                if found is not None:
                    return found, margin

                # Score the failing node: the distance of the disk
                # center to the footprint boundary (candidates to
                # refine around).
                score = footprint.boundary.distance(shapely.Point(x, y))
                if best_score is None or score > best_score:
                    best_score = score
                    best_node = (x, y)
                y += step
            x += step

        if best_node is None:
            return None, None

        # Local refinement around the best node.
        fine = step / self.REFINEMENT_FRACTION
        center_x, center_y = best_node
        for x in np.arange(center_x - step, center_x + step + fine / 2.0, fine):
            for y in np.arange(center_y - step, center_y + step + fine / 2.0, fine):
                if footprint.boundary.distance(shapely.Point(x, y)) <= radius:
                    # Deep inside the footprint is already covered by
                    # the grid pass.
                    continue
                found, margin = self._is_free(x, y, z_base, footprint, obstacles)
                if found is not None:
                    return found, margin

        return None, None

    def run(self):
        self.select_source.run()

        self.select_context.list_ifc_path = self.select_source.list_ifc_path
        self.select_context.list_ifc_file = self.select_source.list_ifc_file
        self.select_context.run()

        if self.state == "Display_Input":
            self._display_input_generic()

        obstacles = self._collect_context()

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
                    vertices = np.asarray(
                        get_vertices(shape.geometry), dtype=float
                    )
                    faces = np.asarray(get_faces(shape.geometry))
                    footprint, z_base = clash_utils.lowest_footprint(
                        vertices, faces
                    )

                if footprint.is_empty:
                    # No footprint: no placement can be evaluated.
                    self.result.append(
                        ClashResultOneObject(source=source, state=True)
                    )
                    continue

                found, margin = self._search_placement(
                    footprint, z_base, obstacles
                )
                if found is None:
                    self.result.append(
                        ClashResultOneObject(source=source, state=True)
                    )
                else:
                    self.placements[source] = {
                        "position": (found[0], found[1], z_base),
                        "margin": margin,
                    }

        self.end_rule_action()
