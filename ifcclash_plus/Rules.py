from RuleClass import (
    RuleCheckOneObject,
    RuleCheckTwoObjects,
    ClashResultOneObject,
    ClashResultTwoObjects,
    Select,
)
import ifcopenshell
import multiprocessing
import clash_utils
import shapely
from ifcopenshell.util.shape import (
    get_vertices,
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
from OCC.Core.gp import gp_Ax3, gp_Pnt, gp_Dir, gp_Trsf, gp_XYZ, gp_Vec,gp_Lin
import ifcopenshell.util.shape
from construct_display_function import create_makepolygon_with_dir
from OCC.Core.BRepIntCurveSurface import BRepIntCurveSurface_Inter


DIRECTION_METHOD = Literal["Wide", "Narrow"]


# ===========One Object Rule
class Volume(RuleCheckOneObject):
    from ifcopenshell.util.shape import get_volume

    def __init__(self, source, volume_min, volume_max,state="Final"):
        super().__init__(state,source)
        self.type = "Volume"
        self.volume_max: float = volume_max
        self.volume_min: float = volume_min
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state=="Display_Input":
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


        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
        if self.state=="Display_Result":
            self.display_result()
        
        if self.state == "Final":
            self.manage_result()
        else:
            self.produce_select()


class Area(RuleCheckOneObject):
    from ifcopenshell.util.shape import get_area

    def __init__(self, source, volume_min, volume_max,state="Final"):
        super().__init__(state,source)
        self.type = "Area"
        self.volume_max: float = volume_max
        self.volume_min: float = volume_min
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state=="Display_Input":
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
                    else:  # @todo How do deal with failed OneRule ?
                        ...
                        # result = ClashResultOneObject(source=entity, state=False)
                        # self.result.append(result)
                    if not iterator.next():
                        break

        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
        if self.state=="Display_Result":
            self.display_result()

        if self.state == "Final":
            self.manage_result()
        else:
            self.produce_select()


TOP_OR_BOT = Literal["Top", "Bottom"]


class TopOrBottomSurface(RuleCheckOneObject):
    def __init__(self, source, surface_min, surface_max, top_or_bot: TOP_OR_BOT,state="Final"):
        super().__init__(state,source)
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

        if self.state=="Display_Input":
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

                    area=result["total_area"]

                    if self.state=="Display_Input":
                        for face in result["extrem_faces"]:
                            self._add_face_to_display(face,(1,0,0))

                    if self.surface_min < area < self.surface_max:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)

                    if not iterator.next():
                        break


        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
        if self.state=="Display_Result":
            self.display_result()

        if self.state == "Final":
            self.manage_result()
        else:
            self.produce_select()


class LateralSurface(RuleCheckOneObject):
    def __init__(self, source, surface_min, surface_max, direction,state="Final"):
        super().__init__(state,source)
        self.type = "LateralSurface"
        self.surface_max: float = surface_max
        self.surface_min: float = surface_min
        self.direction: float = direction
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):  # @todo Check if the result is trustworthy
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state=="Display_Input":
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


        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
        if self.state=="Display_Result":
            self.display_result()
        if self.state == "Final":
            self.manage_result()
        else:
            self.produce_select()


class ProjectedSurface(RuleCheckOneObject):
    def __init__(self, source, surface_min, surface_max, direction,state="Final"):
        super().__init__(state,source)
        self.type = "Projected"
        self.surface_max: float = surface_max
        self.surface_min: float = surface_min
        self.direction: float = direction
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):  # @todo Check if the result is trustworthy
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state=="Display_Input":
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



        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
        if self.state=="Display_Result":
            self.display_result()

        if self.state == "Final":
            self.manage_result()
        else:
            self.produce_select()


class ObbHigh(RuleCheckOneObject):
    def __init__(self, source, length_min, length_max,state="Final"):
        super().__init__(state,source)
        self.type = "ObbHigh"
        self.length_max: float = length_max
        self.length_min: float = length_min
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):  
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state=="Display_Input":
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
                    corners=obb.get_corners()
                    min_z=corners[0].Z()
                    max_z=corners[0].Z()

                    for corner in corners:
                        min_z = min(min_z, corner.Z())
                        max_z = max(max_z, corner.Z())
                        
                    value_to_check=max_z-min_z

                    if self.state=="Display_Input":
                        self._add_obb_to_display(obb,(1,0,0))
                        


                    if self.length_min < value_to_check < self.length_max:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)
                    else:
                        self.result_fail_source.append(entity)

                    if not iterator.next():
                        break


        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
        if self.state=="Display_Result":
            self.display_result()

        if self.state == "Final":
            self.manage_result()
        else:
            self.produce_select()

class ObbLength(RuleCheckOneObject):
    def __init__(self, source, length_min, length_max,method: DIRECTION_METHOD,state="Final"):
        super().__init__(state,source)
        self.type = "ObbLength"
        self.length_max: float = length_max
        self.length_min: float = length_min
        self.direction_method = method
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        if self.state=="Display_Input":
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

                    if self.state=="Display_Input":
                        self._add_obb_to_display(obb,(1,0,0))

                    x_size = obb.XHSize() * 2
                    y_size = obb.YHSize() * 2
                    z_size = obb.ZHSize() * 2

                    # Identifier les deux faces les plus larges ou étroites
                    # On compare les dimensions pour déterminer les faces larges ou étroites
                    #dimensions = {"X": x_size, "Y": y_size, "Z": z_size}
                    dimensions = {"X": x_size, "Y": y_size} #I don't wan to get the high of the object. But i am not sure that Z is the height. @todo check that Z is always the height of an object.

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



        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
        if self.state=="Display_Result":
            self.display_result()

        if self.state == "Final":
            self.manage_result()
        else:
            self.produce_select()


ORIENTATION_TYPE = Literal["Parrallel", "Perpendicular"]


class Orientation(RuleCheckOneObject):
    def __init__(
        self,
        source,
        orientation,
        orientation_type: ORIENTATION_TYPE,
        direction_method: DIRECTION_METHOD,
        angular_tolerance: float = 0.1,
        state="Final"
    ):
        # @todo We can set an East, North, etc orientation to check
        super().__init__(state,source)
        self.type = "Orientation"
        self.orientation: tuple[float, float, float] = orientation
        self.orientation_type: ORIENTATION_TYPE = orientation_type
        self.direction_method: DIRECTION_METHOD = direction_method
        self.angular_tolerance: float = angular_tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):

        self.select_source.run()
        if self.state=="Display_Input":
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

                    if self.state=="Display_Input":
                        self._add_gp_Dir_to_display(geom,dir1,(1,0,0))
                        self._add_gp_Dir_to_display(geom,occ_orientation,(0,1,0))

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


        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
        if self.state=="Display_Result":
            self.display_result()

        if self.state == "Final":
            self.manage_result()
        else:
            self.produce_select()


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
        state="Final"):
        super().__init__(state,source, target)
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

        if self.state=="Display_Input":
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
                    if self.state=="Display_Input":
                        self._add_gp_Dir_to_display(geom,direction,(1,0,0))

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
                    if self.state=="Display_Input":
                        self._add_gp_Dir_to_display(geom,direction,(1,0,0))
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

        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0

        if self.state=="Display_Result":
            self.display_result()

        if self.state == "Final":
            self.manage_result()

        if self.state == "Select":
            self.produce_select()



class Intersection(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance=0.1,state="Final"):
        super().__init__(state,source, target)
        self.type = "Intersection"
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):
        self.tree = ifcopenshell.geom.tree()

        source_elements = []
        target_elements = []

        if self.state=="Display_Input":
            self._display_input_generic()


        if self.state == "Final" or self.state == "Select":
            self.select_source.run()
            self.select_target.run()

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

        if self.state == "Exception":
            self.add_OneObject_to_tree(self.select_source, "BVH")
            self.add_OneObject_to_tree(self.select_target, "BVH")
            source_elements.append(self.select_source)
            target_elements.append(self.select_target)

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
        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
        if self.state=="Display_Result":
            self.display_result()

        if self.state == "Final":
            self.manage_result()

        if self.state == "Select":
            self.produce_select()


class Clearance(RuleCheckTwoObjects):
    # @todo create a max distance for clearance
    def __init__(self, source, target, clearance=0.05,state="Final"):
        super().__init__(state,source, target)

        self.type = "Clearance"
        self.geom_settings = ifcopenshell.geom.settings()
        self.clearance: float = clearance
        self.check_all: bool = False

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state=="Display_Input":
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
        
        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0        
        if self.state=="Display_Result":
            self.display_result()
        if self.state == "Final":
            self.manage_result()

        if self.state == "Select":
            self.produce_select()


class Collision(RuleCheckTwoObjects):
    def __init__(self, source, target, allow_touching=False,state="Final"):
        super().__init__(state,source, target)
        self.type = "Collision"
        self.allow_touching = False
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state=="Display_Input":
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

        if self.state == "Final":
            self.manage_result()

        if self.state == "Select":
            self.produce_select()


class Ray_Check(RuleCheckTwoObjects):
    def __init__(self, source, target, context, max_ray_length,state="Final"):
        super().__init__(state,source, target)
        self.type = "RayCheck"
        self.select_context: Select = context
        self.max_ray_length: float = max_ray_length
        self.geom_settings = ifcopenshell.geom.settings()
        # self.geom_settings=ifcopenshell.geom.settings(USE_WORLD_COORDS=True)

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state=="Display_Input":
            self._display_input_generic()


        # Watch out, we need to manually store the file info in the contect. It's not done when the RuleFile begin.
        # @todo improve this in order to update every select in every rule
        self.select_context.list_ifc_path = self.select_source.list_ifc_path
        self.select_context.list_ifc_file = self.select_source.list_ifc_file
        self.select_context.run()

        self.add_to_tree(self.select_context, "UB")
        # self.add_to_tree(self.select_source, "UB")
        # self.add_to_tree(self.select_target, "UB")

        self.select_source.create_list_of_element()
        self.select_target.create_list_of_element()
        self.select_context.create_list_of_element()

        for source in self.select_source.list_of_elements:
            for target in self.select_target.list_of_elements:
                source_position = clash_utils.get_XYZ_placement(source)
                target_position = clash_utils.get_XYZ_placement(target)
                source_array = np.array(source_position)
                target_array = np.array(target_position)

                direction = target_array - source_array

                distance = np.linalg.norm(direction)
                if distance == 0:
                    # It's the same object
                    continue

                direction = tuple(direction.flatten())
                direction = (
                    float(direction[0] / distance),
                    float(direction[1] / distance),
                    float(direction[2] / distance),
                )

                results = self.tree.select_ray(
                    source_position, direction, length=distance
                )

                number = 0
                for result in results:
                    """
                    distance: Any
                    dot_product: Any
                    instance: Any
                    normal: Any
                    position: Any
                    ray_distance: Any
                    style_index: Any
                    """
                    result_object = result.instance.file_.by_id(result.instance.id())
                    # the ray is not working properly. Something is off.

                    # The clash will append when we can detect two object that are in direct view.

                    # print(result_object,target)
                    if result_object == target:
                        print(target)

        # self.tree.select_ray()
        # @todo Finish Ray Check
        print("Not working, must be defined")

    def Coherence_Check(self):
        # @todo delete this function, but keep the logic of raycheck.

        # I do not respect the parameter consistency, Select should contains a list of object, but here it's only one element.

        self.tree = ifcopenshell.geom.tree()
        # self.geom_settings=ifcopenshell.geom.settings(USE_WORLD_COORDS=True)
        self.Select_Context_Element.run()

        self.add_OneObject_to_tree(self.Select_Source, "UB")
        self.add_OneObject_to_tree(self.Select_Target, "UB")

        self.add_to_tree(self.Select_Context_Element, "UB")

        source_position = clash_utils.get_XYZ_placement(self.Select_Source)
        target_position = clash_utils.get_XYZ_placement(self.Select_Target)
        source_array = np.array(source_position)
        target_array = np.array(target_position)

        direction = target_array - source_array
        distance = np.linalg.norm(direction)
        direction = tuple(direction.flatten())
        direction = (
            float(direction[0] / distance),
            float(direction[1] / distance),
            float(direction[2] / distance),
        )

        results = self.tree.select_ray(source_position, direction, length=distance)
        """
        distance: Any
        dot_product: Any
        instance: Any
        normal: Any
        position: Any
        ray_distance: Any
        style_index: Any
        """

        for result in results:
            Object = result.instance.file_.by_id(result.instance.id())

            if Object == self.Select_Source:
                continue

            if Object == self.Select_Target:
                print("OK")
                return True

            if Object != self.Select_Target:
                print("Error", Object)
                return False


ABOVE_TYPE = Literal[
    "Above_MinToMax", "Above_MinToMin", "Above_MaxToMin", "Above_MaxToMax"
]

BELOW_TYPE = Literal[
    "Below_MinToMax", "Below_MinToMin", "Below_MaxToMin", "Below_MaxToMax"
]


class Above(RuleCheckTwoObjects):
    def __init__(self, source, target, above_type: ABOVE_TYPE, tolerance=0.1,state="Final"):
        super().__init__(state,source, target)
        self.type = above_type
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state=="Display_Input":
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
                    if self.state=="Display_Input":
                        for face in extrem_faces["visible_faces"]:
                            self._add_face_to_display(face,(1,0,0))
                    

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

                    if self.state=="Display_Input":
                        for face in extrem_faces["visible_faces"]:
                            self._add_face_to_display(face,(1,0,0))
                    
                    dict = {
                        "entity": entity,
                        "extrem_faces": extrem_faces["visible_faces"],
                        "obb": obb,
                    }
                    targets_data.append(dict)

                    if not iterator.next():
                        break
        
        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0
        # Check if part of extrem faces are close to each other
        for source in sources_data:
            flag_is_above=False
            source_globalid=str(source["entity"].GlobalId)


            for target in targets_data:
                target_globalid=(target["entity"].GlobalId)
                

                if source["obb"].IsOut(target["obb"]):
  
                    continue

                source_geom = source["extrem_faces"]
                target_geom = target["extrem_faces"]
                
                result=self._check_distance(source_geom,target_geom)

                if result["is_above"]=="Right_Above":
                    self.result.append(
                            ClashResultTwoObjects(
                                source=source["entity"],
                                target=target["entity"],
                                state=True,
                            ))
                    continue
                if result["is_above"]=="Too_Far":
                    continue


                for source_face in source_geom:
                    for point_on_target in result["list_of_point_on_target"]:

                        bottom_direction=gp_Dir(0.0, 0.0, -1.0)
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
                            ))
                            break
                        

        if self.state=="Display_Result":
            self.display_result()

        if self.state == "Final":
            self.manage_result()

        if self.state == "Select":
            self.produce_select()


    def _check_distance(self,list_of_source_face,list_of_target_face):
        dict_to_return={"is_above":None,"list_of_point_on_target":[]}
        for source_face in list_of_source_face:
            for target_face in list_of_target_face:
                
                dist_tool = BRepExtrema_DistShapeShape()
                dist_tool.LoadS1(source_face)
                dist_tool.LoadS2(target_face)
                dist_tool.Perform()
                distance = dist_tool.Value()

                # If they touch (distance <= tolerance), it's close enough to check if the face is exactly above.
                if distance <= self.tolerance:
                    
                    #We check if the target point is exactly above the source point. 
                    for i in range(1,dist_tool.NbSolution()):
                        pt_source=dist_tool.PointOnShape1(i)
                        pt_target=dist_tool.PointOnShape2(i)

                        if pt_source.Z()>pt_target.Z():
                            continue

                        if pt_source.X()-pt_target.X()<1e-3:
                            if pt_source.Y()-pt_target.Y()<1e-3: 
                                dict_to_return["is_above"]="Right_Above"
                                return dict_to_return
 

                        dict_to_return["list_of_point_on_target"].append(pt_target)

        if dict_to_return["list_of_point_on_target"]==[]:
            dict_to_return["is_above"]="Too_Far"
        else:
            dict_to_return["is_above"]="Need_More_Check"


        return dict_to_return

class Below(RuleCheckTwoObjects):
    def __init__(self, source, target, below_type: BELOW_TYPE, tolerance=0.1,state="Final"):
        super().__init__(state,source, target)
        self.type = below_type
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state=="Display_Input":
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
                    if self.state=="Display_Input":
                        for face in extrem_faces["visible_faces"]:
                            self._add_face_to_display(face,(1,0,0))
                    

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
                    if self.state=="Display_Input":
                        for face in extrem_faces["visible_faces"]:
                            self._add_face_to_display(face,(1,0,0))
                    
                    dict = {
                        "entity": entity,
                        "extrem_faces": extrem_faces["visible_faces"],
                        "obb": obb,
                    }
                    targets_data.append(dict)

                    if not iterator.next():
                        break

        if self.state=="Display_Input":
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
                
                result=self._check_distance(source_geom,target_geom)

                if result["is_below"]=="Right_Below":
                    self.result.append(
                            ClashResultTwoObjects(
                                source=source["entity"],
                                target=target["entity"],
                                state=True,
                            ))
                    continue
                if result["is_below"]=="Too_Far":
                    continue


                for source_face in source_geom:
                    for point_on_target in result["list_of_point_on_target"]:

                        bottom_direction=gp_Dir(0.0, 0.0, 1.0)
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
                            ))
                            break
                        

        if self.state=="Display_Result":
            self.display_result()
        if self.state == "Final":
            self.manage_result()

        if self.state == "Select":
            self.produce_select()

    def _check_distance(self,list_of_source_face,list_of_target_face):
        dict_to_return={"is_below":None,"list_of_point_on_target":[]}
        for source_face in list_of_source_face:
            for target_face in list_of_target_face:
                
                dist_tool = BRepExtrema_DistShapeShape()
                dist_tool.LoadS1(source_face)
                dist_tool.LoadS2(target_face)
                dist_tool.Perform()
                distance = dist_tool.Value()

                # If they touch (distance <= tolerance), it's close enough to check if the face is exactly above.
                if distance <= self.tolerance:
                    
                    #We check if the target point is exactly above the source point. 
                    for i in range(1,dist_tool.NbSolution()):
                        pt_source=dist_tool.PointOnShape1(i)
                        pt_target=dist_tool.PointOnShape2(i)

                        if pt_source.Z()<pt_target.Z():
                            continue

                        if pt_source.X()-pt_target.X()<1e-3:
                            if pt_source.Y()-pt_target.Y()<1e-3: 
                                dict_to_return["is_below"]="Right_Below"
                                return dict_to_return
 

                        dict_to_return["list_of_point_on_target"].append(pt_target)

        if dict_to_return["list_of_point_on_target"]==[]:
            dict_to_return["is_below"]="Too_Far"
        else:
            dict_to_return["is_below"]="Need_More_Check"


        return dict_to_return

    def _display_input_specific(self):
        from OCC.Core.AIS import AIS_Shape
        from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

        settings = ifcopenshell.geom.settings()
        settings.set("USE_WORLD_COORDS", True)

        color= Quantity_Color(1, 0, 0, Quantity_TOC_RGB)


        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )
            color= Quantity_Color(1, 0, 0, Quantity_TOC_RGB)
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
    def __init__(self, source, target, tolerance=0.1,state="Final"):
        super().__init__(state,source, target)
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings(USE_WORLD_COORDS=False)

    def run(self):

        if self.state=="Display_Input":
            self._display_input_generic()



        if self.state=="Display_Input":
            self.display.FitAll()
            self.start_display()
            return 0

        if self.state=="Display_Result":
            self.display_result()
        if self.state == "Final":
            self.manage_result()

        if self.state == "Select":
            self.produce_select()

class OBB_Above(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance,state="Final"):
        super().__init__(state,source, target)
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state=="Display_Input":
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

                    if self.state=="Display_Input":
                        self._add_obb_to_display(clash_obb)
                    
                    compound = clash_obb.to_TopoDS_Solid()
                    source_geoms.append(
                        {"entity": entity, "geom": compound, "obb": clash_obb}
                    )

                    if not iterator.next():
                        break
        
        if self.state=="Display_Input":
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
                        state=False,
                    )
                    self.result.append(result)
        if self.state=="Display_Result":
            self.display_result()
        if self.state == "Final":
            self.manage_result()

        if self.state == "Select":
            self.produce_select()

    def _display_input_specific(self):
        from OCC.Core.AIS import AIS_Shape
        from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

        settings = ifcopenshell.geom.settings()
        settings.set("USE_WORLD_COORDS", True)

        color= Quantity_Color(1, 0, 0, Quantity_TOC_RGB)


        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )
            color= Quantity_Color(1, 0, 0, Quantity_TOC_RGB)
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
    def __init__(self, source, target, tolerance,state="Final"):
        super().__init__(state,source, target)
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state=="Display_Input":
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

                    if self.state=="Display_Input":
                        self._add_obb_to_display(clash_obb)


                    compound = clash_obb.to_TopoDS_Solid()
                    source_geoms.append(
                        {"entity": entity, "geom": compound, "obb": clash_obb}
                    )

                    if not iterator.next():
                        break
        if self.state=="Display_Input":
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
                        state=False,
                    )
                    self.result.append(result)
        if self.state=="Display_Result":
            self.display_result()
        if self.state == "Final":
            self.manage_result()

        if self.state == "Select":
            self.produce_select()

    def _display_input_specific(self):
        from OCC.Core.AIS import AIS_Shape
        from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

        settings = ifcopenshell.geom.settings()
        settings.set("USE_WORLD_COORDS", True)

        color= Quantity_Color(1, 0, 0, Quantity_TOC_RGB)


        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )
            color= Quantity_Color(1, 0, 0, Quantity_TOC_RGB)
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
    def __init__(self, source, target, tolerance, method: DIRECTION_METHOD,state="Final"):
        super().__init__(state,source, target)
        self.tolerance: float = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)
        self.direction_method = method

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state=="Display_Input":
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
                    obb = create_obb_from_TopoDs_Shape(geom) #It's the old way, but it can create face that are toward Z.
                    #obb =create_obb_with_fixed_z(geom)

                    main_directions = obb.get_two_main_direction_OBB_shape(
                        self.direction_method,True
                    )

                    clash_obb_1 = obb.detach_side_by_extrude(
                        main_directions[0], self.tolerance
                    )
                    clash_obb_2 = obb.detach_side_by_extrude(
                        main_directions[1], self.tolerance
                    )

                    if self.state=="Display_Input":
                            color=(1,0,0)
                            self._add_obb_to_display(clash_obb_1,color)
                            self._add_obb_to_display(clash_obb_2,color)

                    compound_1 = clash_obb_1.to_TopoDS_Solid()
                    compound_2 = clash_obb_2.to_TopoDS_Solid()
                    source_obbs.append({"entity": entity, "geom": compound_1,"obb":clash_obb_1})
                    source_obbs.append({"entity": entity, "geom": compound_2,"obb":clash_obb_2})

                    if not iterator.next():
                        break

        if self.state=="Display_Input":
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
                    target_geoms.append({"entity": entity, "geom": geom,"obb":obb})

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
                        state=False,
                    )
                    self.result.append(result)


        if self.state=="Display_Result":
            self.display_result()
        if self.state == "Final":
            self.manage_result()

        if self.state == "Select":
            self.produce_select()

    def _display_input_specific(self):
        from OCC.Core.AIS import AIS_Shape
        from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB

        settings = ifcopenshell.geom.settings()
        settings.set("USE_WORLD_COORDS", True)

        color= Quantity_Color(1, 0, 0, Quantity_TOC_RGB)


        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )
            color= Quantity_Color(1, 0, 0, Quantity_TOC_RGB)
            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry

                    obb = create_obb_from_TopoDs_Shape(geom)
                    #obb =create_obb_with_fixed_z(geom)
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
    def __init__(self, source, target, tolerance,state="Final"):
        super().__init__(state,source, target)
        self.list_of_modifications: list[str] = tolerance
        self.geom_settings = ifcopenshell.geom.settings()
        self.geom_settings.set(self.geom_settings.USE_PYTHON_OPENCASCADE, True)

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        if self.state=="Display_Input":
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
                        
                        if self.state=="Display_Input":
                            color=(1,0,0)
                            self._add_obb_to_display(clash_obb,color)


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

        if self.state=="Display_Input":
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
                        state=False,
                    )
                    self.result.append(result)
        if self.state=="Display_Result":
            self.display_result()
        if self.state == "Final":
            self.manage_result()

        if self.state == "Select":
            self.produce_select()



    def _create_list_of_obb(self,geom):

        #expand_sides
        #detach_top_by_extrude
        #detach_bottom_by_extrude
        #extend_up
        #extend_down
        #NEW_OBB
        obb = create_obb_from_TopoDs_Shape(geom)  # Why not use

        list_of_obb=[]

        for one_modification in self.list_of_modifications:

            if "expand_sides" in one_modification:
                value=one_modification.split(":")[1]
                obb=obb.expand_sides(value)
                continue

            if "detach_top_by_extrude" in one_modification:
                value=one_modification.split(":")[1]
                obb=obb.detach_top_by_extrude(value)
                continue

            if "detach_bottom_by_extrude" in one_modification:
                value=one_modification.split(":")[1]
                obb=obb.detach_bottom_by_extrude(value)
                continue

            if "extend_up" in one_modification:
                value=one_modification.split(":")[1]
                obb=obb.extend_up(value)
                continue

            if "extend_down" in one_modification:
                value=one_modification.split(":")[1]
                obb=obb.extend_down(value)
                continue
            
            if "NEW_OBB" in one_modification:
                list_of_obb.append(obb)
                obb = create_obb_from_TopoDs_Shape(geom)  
            

        list_of_obb.append(obb)

        return list_of_obb


# ===== Complex Rule
