from __future__ import annotations

from typing import List

import ifcopenshell
from ifctester import ids
from ifctester.facet import (
    Facet,
    Entity,
    Property,
    Attribute,
    Classification,
    PartOf,
    Material,
)
from typing import Literal, TypedDict, Union

from abc import abstractmethod

from ifctester.facet import Entity, Attribute
import ifcopenshell.geom
import time
from ifcclash.ifcclash import ClashSource
import multiprocessing
import numpy as np
import ifcopenshell.util.placement
from copy import deepcopy, copy
from ifcopenshell.util.element import get_pset
import random



#For displaying
from OCC.Core.AIS import AIS_Shape
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Display.SimpleGui import init_display

from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCC.Core.gp import gp_Pnt, gp_XYZ
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Face
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Shell, topods
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing
from OCC.Core.TopAbs import TopAbs_SHELL
import math
from OCC.Core.gp import gp_Ax3, gp_Pnt, gp_Dir, gp_Trsf, gp_XYZ, gp_Vec
from OCC.Core.BRepGProp import BRepGProp_Face
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge
from OCC.Core.TopoDS import TopoDS_Shell, TopoDS_Face
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.BRepBndLib import brepbndlib

class RuleFile:
    def __init__(self):
        self.id: str = ""
        self.list_ifc_path: list[str] = []
        self.list_ifc_file: list[ifcopenshell.file] = []
        self.contains: list = []  # Union of folder or Rule

        self.path_to_save: str = None

    def run(self): 
        self.load_file()
        self.update_file_info()

        for rulecheck_or_folder in self.contains:
            rulecheck_or_folder.run()

    def update_file_info(self):
        for rule_or_file in self.contains:
            rule_or_file.update_file_info(self.list_ifc_path, self.list_ifc_file)

    def load_file(self):
        #@todo improve the load_file()
        #This function is used to dispatch the list of ifc_file path to every rule.
        for path in self.list_ifc_path:
            self.list_ifc_file.append(ifcopenshell.open(path))


class RuleFolder:
    def __init__(self):
        self.id: str = "AZE"
        self.activation_rule: Select = None
        self.activation_case: str = "ALLTRUE"
        self.contains: list = []  # Union of folder or Rule

    def check_Activation_Rule(self):

        if self.activation_rule is None:
            return True
        if type(self.activation_rule) is SelectFacet:
            self.activation_rule.run()
            self.activation_rule.create_list_of_element()
            number_of_elements=len(self.activation_rule.list_of_elements)
            if number_of_elements>0:
                return True
        else: #For the case with a SelectRule
            self.activation_rule.run()
            number_of_elements=len(self.activation_rule.result)
            if number_of_elements>0:
                return True     
        return False



    def run(self):
        if self.check_Activation_Rule():
            for rulecheck_or_folder in self.contains:
                rulecheck_or_folder.run()
        else:
            return False

    def update_file_info(self, files_path, files):
        for rule_or_file in self.contains:
            rule_or_file.update_file_info(files_path, files)


class Select:
    def __init__(self):
        self.id: str = "AZE"
        self.list_ifc_path: list[str] = []
        self.list_ifc_file: list[ifcopenshell.file] = []
        self.dict_elements: dict = {}
        self.list_of_elements: list[ifcopenshell.entity_instance] = []

    def run(self):
        pass

    def initialize_dict(self):
        Dict = dict()
        for onefile in self.list_ifc_file:
            Dict[onefile] = None
        self.dict_elements = Dict

    def create_list_of_element(self):
        for onefile in self.list_ifc_file:
            self.list_of_elements = self.dict_elements[onefile] + self.list_of_elements

class SelectFacet(Select):
    def __init__(self, ClassificationType="Facet"):
        super().__init__()
        self.type: str = ClassificationType
        self.applicability: List[Facet] = []
        self.classification_name: str = ""

    def run(self):
        self.initialize_dict()

        result=[]
        for onefile in self.list_ifc_file:
            for one_applicability in self.applicability:
                if self.dict_elements[onefile] is None:
                    if isinstance(one_applicability,Attribute): #Attribute need to have a list where Entity doesn't need to
                        result = one_applicability.filter(onefile,onefile.by_type("IfcProduct"))
                    else:
                        result = one_applicability.filter(onefile)
                    self.dict_elements[onefile] = result
                else:
                    self.dict_elements[onefile] = one_applicability.filter(
                        onefile, self.dict_elements[onefile]
                    )

    def update_file_info(self, files_path, files):
        self.list_ifc_path = files_path
        self.list_ifc_file = files


class SelectRule(Select):
    def __init__(self):
        super().__init__()
        from RuleClass import RuleCheck

        self.type: str = "Rule"
        self.rule: RuleCheck
        self.action_type: str = 1

        # can be
        # 1 - Select source in the list => Only one implemented
        # 2 - Select source not in the list
        # 3 - Select target in the list
        # 4 - Select target not in the list

    def run(self, state="Select", element="source", passed=True):
        # element: "source" or "target", only for a two objects rule
        # passed: True to pick elements of the results with status True,
        #         False to pick elements of the input selection that
        #         went through the rule but produced no result.
        # The run() of the rules takes no argument, the state is set on the rule.
        from RuleClass import RuleCheckOneObject

        self.rule.state = state
        self.rule.run()

        if isinstance(self.rule, RuleCheckOneObject):
            # A one object rule only has source elements
            self.dict_elements = self.rule.produce_select(passed=passed)
        else:
            self.dict_elements = self.rule.produce_select(
                element=element, passed=passed
            )

    def update_file_info(self, files_path, files):
        self.list_ifc_path = files_path
        self.list_ifc_file = files
        self.rule.update_file_info(files_path, files)


@abstractmethod
class RuleCheck:
    def __init__(self, state,source):
        self.id: str = None
        self.state:str = state
        self.type: str = None

        self.tree: list = None

        self.result: list[ClashResult] = []

        self.result_fail_source: list[ifcopenshell.entity_instance] = []

        self.select_source: Select = source
        self.select_grouping: SelectFacet | str = None
        self.select_criticity: list[SelectFacet] = []
        self.select_actor: list[SelectFacet] = []
        self.abs_or_rel_check: AbsoluteOrRelativeChecking = None

        self.grouped_result: list[GroupResult] = []

    def add_to_tree(self, Select, type_of_tree):
        for ifc_file in Select.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=Select.dict_elements[ifc_file],
            )
 
            if iterator.initialize():
                while True:
                    if type_of_tree == "BVH":
                        self.tree.add_element(iterator.get())
                    if type_of_tree == "UB":
                        self.tree.add_element(iterator.get_native())

                    shape = iterator.get()
                    if not iterator.next():
                        break

    def add_OneObject_to_tree(self, Object, type_of_tree):
        iterator = ifcopenshell.geom.iterator(
            self.geom_settings,
            Object.file,
            multiprocessing.cpu_count(),
            include=[Object],
        )

        assert iterator.initialize()
        while True:
            if type_of_tree == "BVH":
                self.tree.add_element(iterator.get())
            if type_of_tree == "UB":
                self.tree.add_element(iterator.get_native())

            shape = iterator.get()
            if not iterator.next():
                break

    def to_bcf():
        print("Reuse Ifcopenshell")

    def _add_obb_to_display(self,geom,color):
        the_color= Quantity_Color(color[0], color[1], color[2], Quantity_TOC_RGB)
        compound = geom.to_TopoDS_Compound()
        ais_shape = AIS_Shape(compound)
        ais_shape.SetColor(the_color)
        ais_shape.SetTransparency(0.2)
        self.display.Context.Display(ais_shape, True)

    def _add_face_to_display(self,geom,color):
        the_color= Quantity_Color(color[0], color[1], color[2], Quantity_TOC_RGB)
        ais_shape = AIS_Shape(geom)
        ais_shape.SetColor(the_color)
        ais_shape.SetTransparency(0.2)
        self.display.Context.Display(ais_shape, True)

    def _add_gp_Dir_to_display(self,geom,dir,color):

        def edge_from_point_dir(point, direction, length):
            """Arête partant de `point`, dans `direction`, de longueur `length`."""
            end = point.Translated(gp_Vec(direction).Multiplied(length))
            return BRepBuilderAPI_MakeEdge(point, end).Edge()        
        bbox = Bnd_Box()
        brepbndlib.Add(geom, bbox)
        
        corner_min = bbox.CornerMin()
        corner_max = bbox.CornerMax()
        
        center = gp_Pnt(
            (corner_min.X() + corner_max.X()) / 2.0,
            (corner_min.Y() + corner_max.Y()) / 2.0,
            (corner_min.Z() + corner_max.Z()) / 2.0
        )

        vector_to_print=edge_from_point_dir(center,dir,0.5)



        the_color= Quantity_Color(color[0], color[1], color[2], Quantity_TOC_RGB)
        ais_shape = AIS_Shape(vector_to_print)
        ais_shape.SetColor(the_color)
        ais_shape.SetTransparency(0.2)
        self.display.Context.Display(ais_shape, True)

class RuleCheckOneObject(RuleCheck):
    def __init__(self,state, source):
        super().__init__(state,source)
        # To remember exception has no need in One Object because you can chains the rule to get the same result.

    def produce_select(self, passed=True):
        # passed: True to pick elements of the results with status True,
        #         False to pick elements of the input selection that
        #         went through the rule but produced no result.
        # A one object rule only has source elements.
        dict_return = {}

        if passed:
            for oneresult in self.result:
                if oneresult.status:
                    if oneresult.source.file in dict_return:
                        dict_return[oneresult.source.file].append(oneresult.source)
                    else:
                        dict_return[oneresult.source.file] = [oneresult.source]

            return dict_return

        # Elements of the input selection absent from the results
        # The entity_instance equality is value based, so a set of elements
        # works even if the file wrappers of the results are different
        # from the ones of the selection.
        elements_in_results = set()
        for oneresult in self.result:
            elements_in_results.add(oneresult.source)

        for ifc_file, elements in self.select_source.dict_elements.items():
            if not elements:
                continue
            absent = [
                one_element
                for one_element in elements
                if one_element not in elements_in_results
            ]
            if absent:
                dict_return[ifc_file] = absent

        return dict_return

    def run_grouping(self):

        def grouping_by_entity(self):
            group_dict = {}
            for result in self.result:
                unique_value = result.source.is_a()
                if unique_value not in group_dict:
                    thegroupresult = GroupResult()
                    thegroupresult.add_source(result)
                    group_dict[unique_value] = thegroupresult
                else:
                    group_dict[unique_value].add_source(result)

            for key in group_dict:
                self.grouped_result.append(group_dict[key])

        def grouping_by_property(self):
            group_dict = {}
            for result in self.result:
                unique_value = get_pset(
                    result.source,
                    name=self.select_grouping.propertySet,
                    prop=self.select_grouping.baseName,
                )
                unique_value = str(unique_value)
                if unique_value not in group_dict:
                    thegroupresult = GroupResult()
                    thegroupresult.add_source(result)
                    group_dict[unique_value] = thegroupresult
                else:
                    group_dict[unique_value].add_source(result)

            for key in group_dict:
                self.grouped_result.append(group_dict[key])

        def grouping_by_attribute(self):
            group_dict = {}
            for result in self.result:
                unique_value = result.source.get_info()
                unique_value = unique_value[self.select_grouping.name]
                unique_value = str(unique_value)
                if unique_value not in group_dict:
                    thegroupresult = GroupResult()
                    thegroupresult.add_source(result)
                    group_dict[unique_value] = thegroupresult
                else:
                    group_dict[unique_value].add_source(result)

            for key in group_dict:
                self.grouped_result.append(group_dict[key])

        def grouping_by_part_of(self):
            print("TODO PART OF")
            ...

        def grouping_by_material(self):
            print("TODO MATERIAL")
            ...

        def grouping_by_classification(self):
            print("TODO CLASSIFICATION")
            ...

        def grouping_by_closeness(self):
            print("TODO CLOSENESS")
            ...  # reuse function of IfcClash

        if self.select_grouping is None:
            return 0

        if self.select_grouping == "ENTITY":
            grouping_by_entity(self)

        if isinstance(self.select_grouping, Property):
            grouping_by_property(self)

        if isinstance(self.select_grouping, Attribute):
            grouping_by_attribute(self)

        if isinstance(self.select_grouping, PartOf):
            grouping_by_part_of(self)

        if isinstance(self.select_grouping, Material):
            grouping_by_material(self)

        if self.select_grouping == "CLOSENESS":
            grouping_by_closeness(self)

        if isinstance(self.select_grouping, Classification):
            grouping_by_classification(self)

    def run_criticity(self):
        if self.select_criticity == []:
            return None

        for one_criticity in self.select_criticity:
            one_criticity.run()
            one_criticity.create_list_of_element()

        for oneresult in self.result:
            for one_criticity in self.select_criticity:
                if oneresult.source in one_criticity.list_of_elements:
                    oneresult.criticity.append(one_criticity.classification_name)

    def run_actor(self):
        if self.select_actor == []:
            return None

        for result in self.result:
            filter_flag = True
            for Facet in self.select_actor.applicability:
                ListFiltering = Facet.filter(
                    ifc_file=result.source.file, elements=result.source
                )

                if ListFiltering == []:
                    filter_flag = False
                    break

            if filter_flag:
                result.actor.append(self.select_actor.classification_name)

    def run_abs_or_rel(self):
        if self.abs_or_rel_check is None:
            return None

        self.abs_or_rel_check.run()

        return True

    def manage_result(self):

        self.run_criticity()
        self.run_actor()

        # Only one is possible, it either grouping or must. Not both of them
        if self.run_abs_or_rel() is None:
            self.run_grouping()

    def update_file_info(self, files_path, files):
        self.select_source.update_file_info(files_path, files)

        for one_select_criticity in self.select_criticity:
            one_select_criticity.update_file_info(files_path, files)

        for one_select_actor in self.select_actor:
            one_select_actor.update_file_info(files_path, files)


    def _display_input_generic(self):
        def add_to_display(entity,geom_settings,color):
            shape=ifcopenshell.geom.create_shape(geom_settings,entity)
            geom=shape.geometry

            ais_shape=AIS_Shape(geom)

            ais_shape.SetColor(color)
            ais_shape.SetTransparency(0.9)
            self.display.Context.Display(ais_shape, True)


        self.display, self.start_display, add_menu, add_function = init_display()


        geom_settings = ifcopenshell.geom.settings()
        geom_settings.set("USE_PYTHON_OPENCASCADE", True)

        blue_color= Quantity_Color(0, 0, 1, Quantity_TOC_RGB)


        for ifc_file in self.select_source.dict_elements.keys():

            list_of_elements=self.select_source.dict_elements[ifc_file]
            for element in list_of_elements:
                add_to_display(element,geom_settings,blue_color)

    def _display_result_generic(self):
        # Imports for center calculation and edge display
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib
        from OCC.Core.gp import gp_Pnt

        def add_to_display(display,entity,geom_settings,color):
            shape=ifcopenshell.geom.create_shape(geom_settings,entity)
            geom=shape.geometry

            ais_shape=AIS_Shape(geom)

            ais_shape.SetColor(color)
            ais_shape.SetTransparency(0.9)
            display.Context.Display(ais_shape, True)
            return display

        def get_random_color():
            R=random.randrange(1,255,1)/256
            V=random.randrange(1,255,1)/256
            B=random.randrange(1,255,1)/256
            color = Quantity_Color(R, V, B, Quantity_TOC_RGB)
            return color

        def get_entity_center(entity, geom_settings):
            """Calculate the center of an IFC entity's bounding box"""
            shape = ifcopenshell.geom.create_shape(geom_settings, entity)
            geom = shape.geometry
            
            bbox = Bnd_Box()
            brepbndlib.Add(geom, bbox)
            
            corner_min = bbox.CornerMin()
            corner_max = bbox.CornerMax()
            
            center = gp_Pnt(
                (corner_min.X() + corner_max.X()) / 2.0,
                (corner_min.Y() + corner_max.Y()) / 2.0,
                (corner_min.Z() + corner_max.Z()) / 2.0
            )
            return center

        def display_edge(display, p1, p2,edge_color):
            """Display an edge between two gp_Pnt points"""
            edge = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
            ais_edge = AIS_Shape(edge)
            
            ais_edge.SetColor(edge_color)
            ais_edge.SetTransparency(0.0)
            
            display.Context.Display(ais_edge, True)

        self.display, self.start_display, add_menu, add_function = init_display()


        geom_settings = ifcopenshell.geom.settings()
        geom_settings.set("USE_PYTHON_OPENCASCADE", True)

        neutral_color = Quantity_Color(1, 0, 0, Quantity_TOC_RGB)

        for clash in self.result:
            self.display=add_to_display(self.display,clash.source,geom_settings,neutral_color)




    def _display_result_specific(self):
        pass


    def display_result(self):

        self._display_result_generic()
        self._display_result_specific()

        self.display.FitAll()
        self.start_display()


class RuleCheckTwoObjects(RuleCheck):
    def __init__(self,state, source, target):
        super().__init__(state,source)
        self.select_target: Select = target
        self.select_exception: list[SelectRule] = []
        self.result_fail_target: list[ifcopenshell.entity_instance] = []

    def produce_select(self, element="source", passed=True):
        # element: "source" or "target"
        # passed: True to pick elements of the results with status True,
        #         False to pick elements of the input selection that
        #         went through the rule but produced no result.
        if element not in ("source", "target"):
            raise ValueError(
                f"element must be 'source' or 'target', got '{element}'"
            )

        dict_return = {}

        if passed:
            for oneresult in self.result:
                if oneresult.status == passed:
                    the_element = getattr(oneresult, element)
                    if the_element is None:
                        continue
                    if the_element.file in dict_return:
                        dict_return[the_element.file].append(the_element)
                    else:
                        dict_return[the_element.file] = [the_element]

            return dict_return

        # Elements of the input selection absent from the results
        selection = (
            self.select_source if element == "source" else self.select_target
        )
        # The entity_instance equality is value based, so a set of elements
        # works even if the file wrappers of the results are different
        # from the ones of the selection.
        elements_in_results = set()
        for oneresult in self.result:
            the_element = getattr(oneresult, element)
            if the_element is not None:
                elements_in_results.add(the_element)

        for ifc_file, elements in selection.dict_elements.items():
            if not elements:
                continue
            absent = [
                one_element
                for one_element in elements
                if one_element not in elements_in_results
            ]
            if absent:
                dict_return[ifc_file] = absent

        return dict_return

    def run_grouping(self):
        def grouping_by_entity(self):
            group_dict = {}
            for result in self.result:
                # Source grouping
                unique_value = result.source.is_a()
                if unique_value not in group_dict:
                    thegroupresult = GroupResult()
                    thegroupresult.add_source(result)
                    group_dict[unique_value] = thegroupresult
                else:
                    group_dict[unique_value].add_source(result)

                # Target grouping
                unique_value = result.target.is_a()
                if unique_value not in group_dict:
                    thegroupresult = GroupResult()
                    thegroupresult.add_target(result)
                    group_dict[unique_value] = thegroupresult
                else:
                    group_dict[unique_value].add_target(result)

            for key in group_dict:
                self.grouped_result.append(group_dict[key])

        def grouping_by_property(self):
            group_dict = {}
            for result in self.result:
                # Source grouping
                unique_value = get_pset(
                    result.source,
                    name=self.select_grouping.propertySet,
                    prop=self.select_grouping.baseName,
                )
                unique_value = str(unique_value)

                if unique_value not in group_dict:
                    thegroupresult = GroupResult()
                    thegroupresult.add_source(result)
                    group_dict[unique_value] = thegroupresult
                else:
                    group_dict[unique_value].add_source(result)

                # Target grouping
                unique_value = get_pset(
                    result.target,
                    name=self.select_grouping.propertySet,
                    prop=self.select_grouping.baseName,
                )
                unique_value = str(unique_value)
                if unique_value not in group_dict:
                    thegroupresult = GroupResult()
                    thegroupresult.add_target(result)
                    group_dict[unique_value] = thegroupresult
                else:
                    group_dict[unique_value].add_target(result)

            for key in group_dict:
                self.grouped_result.append(group_dict[key])

        def grouping_by_attribute(self):
            group_dict = {}
            for result in self.result:
                # Source
                unique_value = result.source.get_info()
                unique_value = unique_value[self.select_grouping.name]
                unique_value = str(unique_value)
                if unique_value not in group_dict:
                    thegroupresult = GroupResult()
                    thegroupresult.add_source(result)
                    group_dict[unique_value] = thegroupresult
                else:
                    group_dict[unique_value].add_source(result)

                # Target
                unique_value = result.target.get_info()
                unique_value = unique_value[self.select_grouping.name]
                unique_value = str(unique_value)

                if unique_value not in group_dict:
                    thegroupresult = GroupResult()
                    thegroupresult.add_target(result)
                    group_dict[unique_value] = thegroupresult
                else:
                    group_dict[unique_value].add_target(result)

            for key in group_dict:
                self.grouped_result.append(group_dict[key])
            ...

        def grouping_by_part_of(self):
            print("TODO")
            # @todo Grouping by part of for 2 objects rules
            ...

        def grouping_by_material(self):
            print("TODO")
            # @todo Grouping by material for 2 objects rules

        def grouping_by_classification(self):
            print("TODO CLASSIFICATION")
            ...

        def grouping_by_closeness(self):
            print("TODO")
            # @todo Grouping by closeness for 2 objects rules, reuse IfcClash

        def grouping_by_object(self):
            group_dict = {}
            for result in self.result:
                if self.select_grouping == "SOURCE":
                    unique_value = result.source
                if self.select_grouping == "TARGET":
                    unique_value = result.target

                if unique_value not in group_dict:
                    thegroupresult = GroupResult()
                    thegroupresult.add_source_and_target(result)
                    group_dict[unique_value] = thegroupresult
                else:
                    group_dict[unique_value].add_source_and_target(result)

            for key in group_dict:
                self.grouped_result.append(group_dict[key])

        if self.select_grouping is None:
            return 0

        if self.select_grouping == "ENTITY":
            grouping_by_entity(self)

        if isinstance(self.select_grouping, Property):
            grouping_by_property(self)

        if isinstance(self.select_grouping, Attribute):
            grouping_by_attribute(self)

        if isinstance(self.select_grouping, PartOf):
            grouping_by_part_of(self)

        if isinstance(self.select_grouping, Material):
            grouping_by_material(self)

        if self.select_grouping == "CLOSENESS":
            grouping_by_closeness(self)

        if isinstance(self.select_grouping, Classification):
            grouping_by_classification(self)
        
        if self.select_grouping == "SOURCE" or self.select_grouping == "TARGET":
            grouping_by_object(self)

    def run_criticity(self):
        if self.select_criticity == []:
            return None

        for one_criticity in self.select_criticity:
            one_criticity.run()
            one_criticity.create_list_of_element()

        for oneresult in self.result:
            for one_criticity in self.select_criticity:
                if oneresult.source in one_criticity.list_of_elements:
                    oneresult.criticity.append(one_criticity.classification_name)
                if oneresult.target in one_criticity.list_of_elements:
                    oneresult.criticity.append(one_criticity.classification_name)

    def run_actor(self):
        if self.select_actor == []:
            return None

        for one_actor in self.select_actor:
            one_actor.run()
            one_actor.create_list_of_element()

        for oneresult in self.result:
            for one_actor in self.select_actor:
                if oneresult.source in one_actor.list_of_elements:
                    oneresult.actor.append(one_actor.classification_name)
                if oneresult.target in one_actor.list_of_elements:
                    oneresult.actor.append(one_actor.classification_name)

    def run_exception(self):
        #@todo include a relation exception, if on same ifcsystem, them can be excluded.
        for one_rule_result in self.result:
            for exception_rule in self.select_exception:
                exception_rule.rule.select_source = one_rule_result.source
                exception_rule.rule.select_target = one_rule_result.target

                exception_rule.rule.run(state="Exception")

                if exception_rule.rule.result == []:
                    one_rule_result.state = False
                    break
                else:
                    if exception_rule.rule.result[0].status:
                        continue
                    else:
                        one_rule_result.state = False
                        break

    def run_abs_or_rel(self):
        if self.abs_or_rel_check is None:
            return None

        self.run_grouping(self.abs_or_rel_check.groupby_method)

        self.abs_or_rel_check.run(self.grouped_result)

        return True

    def update_file_info(self, files_path, files):
        self.select_source.update_file_info(files_path, files)
        self.select_target.update_file_info(files_path, files)

        for one_select_criticity in self.select_criticity:
            one_select_criticity.update_file_info(files_path, files)

        for one_select_actor in self.select_actor:
            one_select_actor.update_file_info(files_path, files)

        for one_select_exception in self.select_exception:
            one_select_exception.update_file_info(files_path, files)

    def manage_result(self):
        self.run_exception()

        self.run_criticity()
        self.run_actor()

        # Only one is possible, it either grouping or must. Not both of them
        if self.run_abs_or_rel() is None:
            self.run_grouping()

    def _display_result_generic(self):
        # Imports for center calculation and edge display
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib
        from OCC.Core.gp import gp_Pnt

        def add_to_display(display,entity,geom_settings,color):
            shape=ifcopenshell.geom.create_shape(geom_settings,entity)
            geom=shape.geometry

            ais_shape=AIS_Shape(geom)

            ais_shape.SetColor(color)
            ais_shape.SetTransparency(0.9)
            display.Context.Display(ais_shape, True)
            return display

        def get_random_color():
            R=random.randrange(1,255,1)/256
            V=random.randrange(1,255,1)/256
            B=random.randrange(1,255,1)/256
            color = Quantity_Color(R, V, B, Quantity_TOC_RGB)
            return color

        def get_entity_center(entity, geom_settings):
            """Calculate the center of an IFC entity's bounding box"""
            shape = ifcopenshell.geom.create_shape(geom_settings, entity)
            geom = shape.geometry
            
            bbox = Bnd_Box()
            brepbndlib.Add(geom, bbox)
            
            corner_min = bbox.CornerMin()
            corner_max = bbox.CornerMax()
            
            center = gp_Pnt(
                (corner_min.X() + corner_max.X()) / 2.0,
                (corner_min.Y() + corner_max.Y()) / 2.0,
                (corner_min.Z() + corner_max.Z()) / 2.0
            )
            return center

        def display_edge(display, p1, p2,edge_color):
            """Display an edge between two gp_Pnt points"""
            edge = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
            ais_edge = AIS_Shape(edge)
            
            ais_edge.SetColor(edge_color)
            ais_edge.SetTransparency(0.0)
            
            display.Context.Display(ais_edge, True)

        self.display, self.start_display, add_menu, add_function = init_display()


        geom_settings = ifcopenshell.geom.settings()
        geom_settings.set("USE_PYTHON_OPENCASCADE", True)

        neutral_color= Quantity_Color(0, 0, 0.5, Quantity_TOC_RGB)
        source_set= set()

        for clash in self.result:
            self.display=add_to_display(self.display,clash.target,geom_settings,neutral_color)
            source_set.add(clash.source)

        dict_of_source_color={}
        for source in source_set:
            random_color=get_random_color()
            dict_of_source_color[source]=random_color
            self.display=add_to_display(self.display,source,geom_settings,random_color)

        # Display edges between centers of clashing pairs
        for clash in self.result:
            center_source = get_entity_center(clash.source, geom_settings)
            center_target = get_entity_center(clash.target, geom_settings)
            display_edge(self.display, center_source, center_target,dict_of_source_color[clash.source])



    def _display_result_specific(self):
        pass

    def display_result(self):

        self._display_result_generic()
        self._display_result_specific()

        self.display.FitAll()
        self.start_display()

    def _display_input_generic(self):

        # Imports for center calculation and edge display
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib
        from OCC.Core.gp import gp_Pnt

        def add_to_display(entity,geom_settings,color):
            shape=ifcopenshell.geom.create_shape(geom_settings,entity)
            geom=shape.geometry

            ais_shape=AIS_Shape(geom)

            ais_shape.SetColor(color)
            ais_shape.SetTransparency(0.9)
            self.display.Context.Display(ais_shape, True)


        self.display, self.start_display, add_menu, add_function = init_display()


        geom_settings = ifcopenshell.geom.settings()
        geom_settings.set("USE_PYTHON_OPENCASCADE", True)

        blue_color= Quantity_Color(0, 0, 1, Quantity_TOC_RGB)
        green_color= Quantity_Color(0, 1, 0, Quantity_TOC_RGB)


        for ifc_file in self.select_source.dict_elements.keys():

            list_of_elements=self.select_source.dict_elements[ifc_file]
            for element in list_of_elements:
                add_to_display(element,geom_settings,blue_color)

        for ifc_file in self.select_target.dict_elements.keys():
            list_of_elements=self.select_target.dict_elements[ifc_file]
            for element in list_of_elements:
                add_to_display(element,geom_settings,green_color)






    def _display_input_specific(self):
        pass




class RuleCheckComplex(RuleCheck):
    def __init__(self):
        super().__init__()
        select_target: Select = None
        select_context_A: Select = None
        select_context_B: Select = None
        select_context_C: Select = None


####======= Absolute or Relative Checking
ABSOLUTEORRELATIVECHECK_TYPE = Literal[
    "Absolute_Number", "Relative_Quantity", "Absolute_Quantity", "Relative_Number"
]


@abstractmethod
class AbsoluteOrRelativeChecking:
    def __init__(self, type: ABSOLUTEORRELATIVECHECK_TYPE):
        self.type = type
        self.groupby_method: str = (
            "source"  # In futur, it could be grouped by different means
        )

    def run(self, list_of_result: list[GroupResult]):
        for onegroupresult in list_of_result:
            self.eval_check(onegroupresult)


class AbsoluteChecking(AbsoluteOrRelativeChecking):
    def __init__(self, type: ABSOLUTEORRELATIVECHECK_TYPE):
        super().__init__(self, type)
        self.type = type

        self.focus: str = "source"  # source or target
        self.element_number = None
        self.operation: str = ""
        self.aim: float = 0

        self.quantity_pset: str = None
        self.quantity_prop: str = None

    def number(self, groupresult: GroupResult):
        if self.focus == "source":
            self.element_number = len(groupresult.source_set)
        else:
            self.element_number = len(groupresult.target_set)

    def quantity(self, groupresult: GroupResult):
        if self.focus == "source":
            list = list(groupresult.source_set)
        else:
            list = list(groupresult.sourcetarget_set_set)

        for entity in list:
            # @todo Finish properly the property extraction with all the edge case, we must have at the end a working float to be compared
            value = get_pset(entity, name=self.quantity_pset, prop=self.quantity_prop)
            self.element_number = +value

    def eval_check(self, groupresult: GroupResult):
        if "Quantity" in self.type:
            self.quantity()
        if "Number" in self.type:
            self.number()

        operation_string = (
            str(self.element_number) + str(self.operation) + str(self.aim)
        )

        groupresult.abs_or_rel_check = eval(operation_string)

        return groupresult


class RelativeChecking(AbsoluteOrRelativeChecking):
    def __init__(self, type: ABSOLUTEORRELATIVECHECK_TYPE):
        super().__init__(self, type)
        self.type = type
        self.source_operation: str = ""
        self.operation: str = ""
        self.target_operation: str = ""

    def number(self, groupresult: GroupResult):
        self.source_number = len(groupresult.source_set)
        self.target_number = len(groupresult.target_set)

    def quantity(self, groupresult: GroupResult):
        source_list = list(groupresult.source_set)
        target_list = list(groupresult.target_set)

        for entity in source_list:
            # @todo Finish properly the property extraction with all the edge case, we must have at the end a working float to be compared
            value = get_pset(entity, name=self.quantity_pset, prop=self.quantity_prop)
            self.source_number = +value

        for entity in target_list:
            # @todo Finish properly the property extraction with all the edge case, we must have at the end a working float to be compared
            value = get_pset(entity, name=self.quantity_pset, prop=self.quantity_prop)
            self.target_number = +value

    def eval_check(self, groupresult: GroupResult):
        if "Quantity" in self.type:
            self.quantity()
        if "Number" in self.type:
            self.number()

        source_string = str(groupresult.number_of_source) + self.source_operation
        target_string = str(groupresult.number_of_target) + self.target_operation

        source_quantity = eval(source_string)
        target_quantity = eval(target_string)

        operation_string = str(source_quantity) + self.operation + str(target_quantity)

        groupresult.abs_or_rel_check = eval(operation_string)

        return groupresult


# ==== Clash Result
class ClashResult:
    def __init__(self, source, state, type="OneObjectResult"):
        self.id: str
        self.type: str = type
        self.source: ifcopenshell.entity_instance = source

        self.status: bool = state
        self.criticity: list[str] = []
        self.actor: list[str] = []

        self.point1: tuple()  # @todo Validate the info to export from the clash
        self.point2: tuple()  # To validate, list of point


class ClashResultOneObject(ClashResult):
    def __init__(self, source, state):
        super().__init__(source, state)


class ClashResultTwoObjects(ClashResult):
    def __init__(self, source, target, state, type="TwoObjectsResult"):
        super().__init__(source, state, type)
        self.target: ifcopenshell.entity_instance = target


class ClashResultComplex(ClashResult):
    def __init__(self):
        super().__init__()
        self.target: ifcopenshell.entity_instance = None
        self.context: ifcopenshell.entity_instance = None


# ====== Group Result
class GroupResult:
    def __init__(self, type="GroupResult"):
        self.id: str
        self.type: str = type
        self.result_group: list[ClashResult] = []
        self.source_set: set(ifcopenshell.entity_instance) = set()
        self.target_set: set(ifcopenshell.entity_instance) = set()
        self.abs_or_rel_check = None

    def add_source(self, clash_result: ClashResult):
        self.result_group.append(clash_result)
        self.source_set.add(clash_result.source)

    def add_target(self, clash_result: ClashResult):
        self.result_group.append(clash_result)
        self.target_set.add(clash_result.target)

    def add_source_and_target(self, clash_result: ClashResult):
        self.result_group.append(clash_result)
        self.target_set.add(clash_result.target)
        self.source_set.add(clash_result.source)
