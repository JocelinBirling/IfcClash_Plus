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
from dataclasses import dataclass

from booleanrule import BooleanRule, BooleanLeaf

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


# For displaying
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
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeFace,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeEdge,
)
from OCC.Core.TopoDS import TopoDS_Shell, TopoDS_Face
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.BRepBndLib import brepbndlib


# ==== Display geometry registry
DISPLAY_CATEGORY = Literal[
    "axis", "face", "obb", "zone", "context", "segment", "point"
]

DISPLAY_CATEGORIES = (
    "axis",
    "face",
    "obb",
    "zone",
    "context",
    "segment",
    "point",
)


@dataclass
class DisplayItem:
    """One auxiliary geometry produced by a rule, kept for display.

    The shape is either a TopoDS_Shape (or a custom OBB, converted to
    its compound at display time), or a lightweight representation
    converted by RuleCheck._item_shape: an ("edge", start, end) tuple,
    a ("face", corners) tuple, an ("axis", center, direction, length)
    tuple. The element, when set, links the item to its IFC entity for
    a per-result coloring.
    """

    category: DISPLAY_CATEGORY
    shape: object
    color: tuple = (1, 0, 0)
    transparency: float = 0.6
    element: object = None


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
        # @todo improve the load_file()
        # This function is used to dispatch the list of ifc_file path to every rule.
        for path in self.list_ifc_path:
            self.list_ifc_file.append(ifcopenshell.open(path))


class RuleFolder:
    def __init__(self):
        self.id: str = "AZE"
        self.activation_rule: SelectFacet | BooleanRule = None
        self.activation_case: str = "ALLTRUE"
        self.contains: list = []  # Union of folder or Rule

    def check_Activation_Rule(self):

        if self.activation_rule is None:
            return True

        if type(self.activation_rule) is SelectFacet:
            self.activation_rule.run()
            self.activation_rule.create_list_of_element()
            number_of_elements = len(self.activation_rule.list_of_elements)
            return number_of_elements > 0

        if isinstance(self.activation_rule, BooleanRule):
            # The rules referenced by the boolean tree are run first,
            # then the tree is evaluated.
            for one_rule in self.activation_rule.rules():
                one_rule.state = "Final"
                one_rule.run()
            return self.activation_rule.evaluate()

        raise TypeError(
            "activation_rule must be a SelectFacet or a BooleanRule, "
            f"got {type(self.activation_rule)}"
        )

    def run(self):
        if self.check_Activation_Rule():
            for rulecheck_or_folder in self.contains:
                rulecheck_or_folder.run()
        else:
            return False

    def update_file_info(self, files_path, files):
        # The activation rule also needs the files to be able to run,
        # even when it is not shared with a rule of the folder.
        # An activation_rule of another type is rejected at run,
        # in check_Activation_Rule.
        if isinstance(self.activation_rule, BooleanRule):
            for one_rule in self.activation_rule.rules():
                one_rule.update_file_info(files_path, files)
        elif type(self.activation_rule) is SelectFacet:
            self.activation_rule.update_file_info(files_path, files)

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

        # The facets other than Entity need a list of elements to filter
        FACETS_REQUIRING_ELEMENTS = (
            Attribute,
            Property,
            Classification,
            PartOf,
            Material,
        )

        result = []
        for onefile in self.list_ifc_file:
            for one_applicability in self.applicability:
                if self.dict_elements[onefile] is None:
                    if isinstance(one_applicability, FACETS_REQUIRING_ELEMENTS):
                        result = one_applicability.filter(
                            onefile, onefile.by_type("IfcProduct")
                        )
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
        self.element_to_pass: str = "source"  # by default, can be changed
        self.element_state_to_pass: bool = True  # by defaut

    def run(self, state="Select"):
        # element_to_pass: "source" or "target", only for a two objects rule
        # element_state_to_pass: True to pick elements of the results with
        #     status True, False to pick elements of the input selection
        #     that went through the rule but produced no result.
        # The SelectRule holds the data of the selection and gives it to
        # the rule before calling produce_select, which takes no parameter.
        # The run() of the rules takes no argument, the state is set on the rule.
        self.rule.state = state
        self.rule.run()

        self.rule.element_to_pass = self.element_to_pass
        self.rule.element_state_to_pass = self.element_state_to_pass
        self.dict_elements = self.rule.produce_select()

    def update_file_info(self, files_path, files):
        self.list_ifc_path = files_path
        self.list_ifc_file = files
        self.rule.update_file_info(files_path, files)


@abstractmethod
class RuleCheck:
    # The relation exceptions, usable as select_exception
    EXCEPTION_METHOD = ("Same_IfcSystem", "Same_Building", "Same_Storey", "Same_Space")

    def __init__(self, state, source):
        self.id: str = None
        self.state: str = state
        self.type: str = None

        self.tree: list = None

        self.result: list[ClashResult] = []

        self.result_fail_source: list[ifcopenshell.entity_instance] = []

        self.select_exception: BooleanLeaf | str | None = None

        self.select_source: Select = source
        self.select_grouping: SelectFacet | str = None
        self.select_criticity: list[SelectFacet] = []
        self.select_actor: list[SelectFacet] = []
        self.abs_or_rel_check: AbsoluteOrRelativeChecking = None

        # Configuration of produce_select, given by a SelectRule before
        # the call. element_to_pass is only used by a two objects rule.
        self.element_to_pass: str = "source"
        self.element_state_to_pass: bool = True

        self.grouped_result: list[GroupResult] = []

        # The individual results kept aside by the Must check
        # (AbsoluteOrRelativeChecking): the check replaces result by
        # its group results, and keeps them only so it can run again
        # on the same rule.
        self.result_before_abs_or_rel: list[ClashResult] = []

        # The display geometry registry: filled during run() as a
        # by-product of the computation, read by the generic display.
        self.display_items: list[DisplayItem] = []
        self.display_options: dict[DISPLAY_CATEGORY, bool] = {
            category: True for category in DISPLAY_CATEGORIES
        }
        self.keep_display_items: bool = True

    def end_rule_action(self):
        self.run_exception()

        if self.state == "Display_Input":
            self._display_input_generic()
            self.display.FitAll()
            self.start_display()
            return
        if self.state == "Display_Result":
            self.display_result()
        if self.state == "Final":
            self.manage_result()
            if not self.keep_display_items:
                # The registry is a temporary by-product: free the
                # memory on the big models when it is not kept.
                self.display_items.clear()
        if self.state == "Select":
            self.produce_select()

    def run_exception(self):
        def exception_same_ifcsystem(result) -> bool:
            """Return True when the source and the target of a result belong
            to the same IfcSystem.

            This is a relation exception: two objects of the same system
            are allowed to be in clash, the result can be excluded.
            """
            source = result.source
            target = result.target

            if source is None or target is None:
                return False

            source_systems = _get_ifcsystem_set(source)
            target_systems = _get_ifcsystem_set(target)

            return len(source_systems & target_systems) > 0

        @staticmethod
        def _get_ifcsystem_set(element):
            """The IfcSystems containing the element.

            An element belongs to an IfcSystem through an
            IfcRelAssignsToGroup relationship, reachable with the inverse
            attribute HasAssignments of the element.
            """
            systems = set()

            for assignment in element.HasAssignments:
                if assignment.is_a("IfcRelAssignsToGroup"):
                    group = assignment.RelatingGroup
                    if group is not None and group.is_a("IfcSystem"):
                        systems.add(group)
            return systems

        def exception_same_building(self, result) -> bool:
            ...
            # @todo do exception for same building, with 2 objects, it's tricky...

        def exception_same_storey(self, result) -> bool:
            ...
            # @todo do exception for same storey, with 2 objects, it's tricky...

        def exception_same_space(self, result) -> bool:
            ...
            # @todo do exception for same space, with 2 objects, it's tricky...

        # The exception is a BooleanLeaf evaluated result by result: the
        # rule of the leaf runs on the pair of elements of the result
        # and the result is invalidated when the exception applies.
        if self.select_exception == None:
            return

        if isinstance(self.select_exception, BooleanLeaf):
            for one_result in self.result:
                if self.select_exception.evaluate_result(one_result):
                    one_result.status = False

        if self.select_exception in self.EXCEPTION_METHOD and isinstance(
            self, RuleCheckTwoObjects
        ):
            if self.select_exception == "Same_IfcSystem":
                for one_result in self.result:
                    if exception_same_ifcsystem(one_result):
                        one_result.status = False

            if self.select_exception == "Same_Building":
                exception_same_building()

            if self.select_exception == "Same_Storey":
                exception_same_storey()

            if self.select_exception == "Same_Space":
                exception_same_space()

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

    def group_by_source(self):
        """The default Must check grouping: one group per source
        object, the targets of its results in the target set of the
        group."""
        group_dict = {}
        for result in self.result:
            key = result.source
            if key is None:
                continue
            if key not in group_dict:
                group_dict[key] = GroupResult()
            if getattr(result, "target", None) is not None:
                group_dict[key].add_source_and_target(result)
            else:
                group_dict[key].add_source(result)

        self.grouped_result = list(group_dict.values())

    # ---- Display geometry registry
    def register_display_item(
        self,
        category: DISPLAY_CATEGORY,
        shape,
        color: tuple = (1, 0, 0),
        transparency: float = 0.6,
        element=None,
    ):
        """Add one auxiliary geometry to the registry of the rule."""
        if category not in DISPLAY_CATEGORIES:
            raise ValueError(
                f"category must be one of {DISPLAY_CATEGORIES}, got '{category}'"
            )
        self.display_items.append(
            DisplayItem(
                category=category,
                shape=shape,
                color=color,
                transparency=transparency,
                element=element,
            )
        )

    def available_display_categories(self) -> set:
        """The categories actually present in the registry."""
        return {item.category for item in self.display_items}

    @staticmethod
    def _display_point(value):
        """A gp_Pnt from a gp_Pnt or a 3-value sequence."""
        if isinstance(value, gp_Pnt):
            return value
        return gp_Pnt(float(value[0]), float(value[1]), float(value[2]))

    @staticmethod
    def _display_dir(value):
        """A gp_Dir from a gp_Dir or a 3-value sequence."""
        if isinstance(value, gp_Dir):
            return value
        return gp_Dir(float(value[0]), float(value[1]), float(value[2]))

    @staticmethod
    def _shape_center(shape):
        """The center of the bounding box of a TopoDS shape."""
        bbox = Bnd_Box()
        brepbndlib.Add(shape, bbox)
        corner_min = bbox.CornerMin()
        corner_max = bbox.CornerMax()
        return gp_Pnt(
            (corner_min.X() + corner_max.X()) / 2.0,
            (corner_min.Y() + corner_max.Y()) / 2.0,
            (corner_min.Z() + corner_max.Z()) / 2.0,
        )

    def _item_shape(self, item: DisplayItem):
        """The TopoDS_Shape of one registry item.

        A TopoDS_Shape is displayed as is, a custom OBB is converted to
        its compound; the lightweight representations are converted
        here, at display time only: ("edge", start, end),
        ("face", corners) and ("axis", center, direction, length).
        """
        shape = item.shape

        if isinstance(shape, TopoDS_Shape):
            return shape

        if hasattr(shape, "to_TopoDS_Compound"):
            return shape.to_TopoDS_Compound()

        if isinstance(shape, tuple) and shape:
            kind, data = shape[0], shape[1:]
            if kind == "edge":
                start, end = data
                return BRepBuilderAPI_MakeEdge(
                    self._display_point(start), self._display_point(end)
                ).Edge()
            if kind == "axis":
                center = self._display_point(data[0])
                direction = self._display_dir(data[1])
                length = data[2] if len(data) > 2 else 0.5
                end = center.Translated(gp_Vec(direction).Multiplied(length))
                return BRepBuilderAPI_MakeEdge(center, end).Edge()
            if kind == "face":
                corners = data[0]
                polygon = BRepBuilderAPI_MakePolygon(*[
                    self._display_point(corner) for corner in corners
                ])
                polygon.Close()
                return BRepBuilderAPI_MakeFace(polygon.Wire()).Face()
            if kind == "entity":
                # An IFC entity: the shape is created at display time
                # only, as for the objects of the selections.
                geom_settings = ifcopenshell.geom.settings()
                geom_settings.set("USE_PYTHON_OPENCASCADE", True)
                return ifcopenshell.geom.create_shape(geom_settings, data[0]).geometry

        raise TypeError(f"Unsupported display item shape: {type(shape)}")

    def _display_registered_items(self):
        """The registry items, filtered by display_options."""
        for item in self.display_items:
            if not self.display_options.get(item.category, True):
                continue
            ais_shape = AIS_Shape(self._item_shape(item))
            ais_shape.SetColor(
                Quantity_Color(item.color[0], item.color[1], item.color[2], Quantity_TOC_RGB)
            )
            ais_shape.SetTransparency(item.transparency)
            self.display.Context.Display(ais_shape, True)


class RuleCheckOneObject(RuleCheck):
    def __init__(self, state, source):
        super().__init__(state, source)
        # To remember exception has no need in One Object because you can chains the rule to get the same result.

    def produce_select(self):
        # element_state_to_pass: True to pick elements of the results
        #     with status True, False to pick elements of the input
        #     selection that went through the rule but produced no result.
        # A one object rule only has source elements.
        # An element appearing in several results is returned only once.
        dict_return = {}

        if self.element_state_to_pass:
            elements_already_added = set()
            for oneresult in self.result:
                if oneresult.status:
                    the_element = oneresult.source
                    if the_element in elements_already_added:
                        continue
                    elements_already_added.add(the_element)
                    if the_element.file in dict_return:
                        dict_return[the_element.file].append(the_element)
                    else:
                        dict_return[the_element.file] = [the_element]

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

        # The Must check groups the results of the rule itself: its
        # classic grouping (run_grouping, driven by select_grouping),
        # or one group per source object when it has no grouping (a
        # one object rule has no target).
        self.abs_or_rel_check.run(self)

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
        def add_to_display(entity, geom_settings, color):
            shape = ifcopenshell.geom.create_shape(geom_settings, entity)
            geom = shape.geometry

            ais_shape = AIS_Shape(geom)

            ais_shape.SetColor(color)
            ais_shape.SetTransparency(0.9)
            self.display.Context.Display(ais_shape, True)

        self.display, self.start_display, add_menu, add_function = init_display()

        geom_settings = ifcopenshell.geom.settings()
        geom_settings.set("USE_PYTHON_OPENCASCADE", True)

        blue_color = Quantity_Color(0, 0, 1, Quantity_TOC_RGB)

        for ifc_file in self.select_source.dict_elements.keys():
            list_of_elements = self.select_source.dict_elements[ifc_file]
            for element in list_of_elements:
                add_to_display(element, geom_settings, blue_color)

        # The geometries registered during run(), by category.
        self._display_registered_items()

    def _result_color_map(self):
        """The display color of every source object of the selection:
        True for red (the object appears in the results), False for
        green."""
        clashing_sources = set()
        for clash in self.result:
            clashing_sources.add(clash.source)

        color_map = {}
        for elements in self.select_source.dict_elements.values():
            for element in elements or []:
                color_map[element] = element in clashing_sources
        return color_map

    def _display_result_generic(self):
        def add_to_display(display, entity, geom_settings, color):
            shape = ifcopenshell.geom.create_shape(geom_settings, entity)
            geom = shape.geometry

            ais_shape = AIS_Shape(geom)

            ais_shape.SetColor(color)
            ais_shape.SetTransparency(0.9)
            display.Context.Display(ais_shape, True)
            return display

        self.display, self.start_display, add_menu, add_function = init_display()

        geom_settings = ifcopenshell.geom.settings()
        geom_settings.set("USE_PYTHON_OPENCASCADE", True)

        green_color = Quantity_Color(0, 0.75, 0, Quantity_TOC_RGB)
        red_color = Quantity_Color(0.75, 0, 0, Quantity_TOC_RGB)

        # Every source object is green, the ones appearing in the
        # results are red. A one object rule has no pair to link.
        for entity, is_clashing in self._result_color_map().items():
            self.display = add_to_display(
                self.display,
                entity,
                geom_settings,
                red_color if is_clashing else green_color,
            )

    def display_result(self):

        self._display_result_generic()
        self._display_registered_items()

        self.display.FitAll()
        self.start_display()


class RuleCheckTwoObjects(RuleCheck):
    def __init__(self, state, source, target):
        super().__init__(state, source)
        self.select_target: Select = target
        self.result_fail_target: list[ifcopenshell.entity_instance] = []

    def produce_select(self):
        # element_to_pass: "source" or "target"
        # element_state_to_pass: True to pick elements of the results
        #     with status True, False to pick elements of the input
        #     selection that went through the rule but produced no result.
        # An element appearing in several results is returned only once.
        if self.element_to_pass not in ("source", "target"):
            raise ValueError(
                f"element_to_pass must be 'source' or 'target', got '{self.element_to_pass}'"
            )

        dict_return = {}

        if self.element_state_to_pass:
            elements_already_added = set()
            for oneresult in self.result:
                if oneresult.status:
                    the_element = getattr(oneresult, self.element_to_pass)
                    if the_element is None:
                        continue
                    if the_element in elements_already_added:
                        continue
                    elements_already_added.add(the_element)
                    if the_element.file in dict_return:
                        dict_return[the_element.file].append(the_element)
                    else:
                        dict_return[the_element.file] = [the_element]

            return dict_return

        # Elements of the input selection absent from the results
        selection = (
            self.select_source
            if self.element_to_pass == "source"
            else self.select_target
        )
        # The entity_instance equality is value based, so a set of elements
        # works even if the file wrappers of the results are different
        # from the ones of the selection.
        elements_in_results = set()
        for oneresult in self.result:
            the_element = getattr(oneresult, self.element_to_pass)
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

    def run_abs_or_rel(self):
        if self.abs_or_rel_check is None:
            return None

        # The Must check groups the results of the rule itself: its
        # classic grouping (run_grouping, driven by select_grouping),
        # or one group per source object when it has no grouping.
        self.abs_or_rel_check.run(self)

        return True

    def update_file_info(self, files_path, files):
        self.select_source.update_file_info(files_path, files)
        self.select_target.update_file_info(files_path, files)

        for one_select_criticity in self.select_criticity:
            one_select_criticity.update_file_info(files_path, files)

        for one_select_actor in self.select_actor:
            one_select_actor.update_file_info(files_path, files)

        # select_exception is a BooleanLeaf: its rule receives the
        # elements of the pairs at the evaluation, it needs no file.

    def manage_result(self):
        self.run_criticity()
        self.run_actor()

        # Only one is possible, it either grouping or must. Not both of them
        if self.run_abs_or_rel() is None:
            self.run_grouping()

    def _result_color_map(self):
        """The display color of every source and target object of the
        two selections: True for red (the object appears in the
        results), False for green."""
        clashing_objects = set()
        for clash in self.result:
            clashing_objects.add(clash.source)
            clashing_objects.add(clash.target)

        color_map = {}
        for select in (self.select_source, self.select_target):
            for elements in select.dict_elements.values():
                for element in elements or []:
                    color_map[element] = element in clashing_objects
        return color_map

    def _result_pairs(self):
        """The unique (source, target) pairs of the results, in order of
        first appearance."""
        pairs = []
        seen = set()
        for clash in self.result:
            pair = (clash.source, clash.target)
            if pair in seen:
                continue
            seen.add(pair)
            pairs.append(pair)
        return pairs

    def _pair_colors(self, pairs):
        """One distinct random color per pair, so that every clash pair
        can be followed visually."""
        colors = {}
        for pair in pairs:
            red = random.randrange(1, 255, 1) / 256
            green = random.randrange(1, 255, 1) / 256
            blue = random.randrange(1, 255, 1) / 256
            colors[pair] = Quantity_Color(red, green, blue, Quantity_TOC_RGB)
        return colors

    def _display_result_generic(self):
        # Imports for center calculation and edge display
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib
        from OCC.Core.gp import gp_Pnt

        def add_to_display(display, entity, geom_settings, color):
            shape = ifcopenshell.geom.create_shape(geom_settings, entity)
            geom = shape.geometry

            ais_shape = AIS_Shape(geom)

            ais_shape.SetColor(color)
            ais_shape.SetTransparency(0.9)
            display.Context.Display(ais_shape, True)
            return display

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
                (corner_min.Z() + corner_max.Z()) / 2.0,
            )
            return center

        def display_edge(display, p1, p2, edge_color):
            """Display an edge between two gp_Pnt points"""
            edge = BRepBuilderAPI_MakeEdge(p1, p2).Edge()
            ais_edge = AIS_Shape(edge)

            ais_edge.SetColor(edge_color)
            ais_edge.SetTransparency(0.0)

            display.Context.Display(ais_edge, True)

        self.display, self.start_display, add_menu, add_function = init_display()

        geom_settings = ifcopenshell.geom.settings()
        geom_settings.set("USE_PYTHON_OPENCASCADE", True)

        green_color = Quantity_Color(0, 0.75, 0, Quantity_TOC_RGB)
        red_color = Quantity_Color(0.75, 0, 0, Quantity_TOC_RGB)

        # Every source and target object is green, the ones appearing
        # in the results are red.
        for entity, is_clashing in self._result_color_map().items():
            self.display = add_to_display(
                self.display,
                entity,
                geom_settings,
                red_color if is_clashing else green_color,
            )

        # One colored line per result pair, between the bounding box
        # centers of the two objects.
        pairs = self._result_pairs()
        pair_colors = self._pair_colors(pairs)
        for pair in pairs:
            source, target = pair
            center_source = get_entity_center(source, geom_settings)
            center_target = get_entity_center(target, geom_settings)
            display_edge(
                self.display,
                center_source,
                center_target,
                pair_colors[pair],
            )

    def display_result(self):

        self._display_result_generic()
        self._display_registered_items()

        self.display.FitAll()
        self.start_display()

    def _display_input_generic(self):

        # Imports for center calculation and edge display
        from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
        from OCC.Core.Bnd import Bnd_Box
        from OCC.Core.BRepBndLib import brepbndlib
        from OCC.Core.gp import gp_Pnt

        def add_to_display(entity, geom_settings, color):
            shape = ifcopenshell.geom.create_shape(geom_settings, entity)
            geom = shape.geometry

            ais_shape = AIS_Shape(geom)

            ais_shape.SetColor(color)
            ais_shape.SetTransparency(0.9)
            self.display.Context.Display(ais_shape, True)

        self.display, self.start_display, add_menu, add_function = init_display()

        geom_settings = ifcopenshell.geom.settings()
        geom_settings.set("USE_PYTHON_OPENCASCADE", True)

        blue_color = Quantity_Color(0, 0, 1, Quantity_TOC_RGB)
        orange = Quantity_Color(1, 0.45, 0, Quantity_TOC_RGB)

        for ifc_file in self.select_source.dict_elements.keys():
            list_of_elements = self.select_source.dict_elements[ifc_file]
            for element in list_of_elements:
                add_to_display(element, geom_settings, blue_color)

        for ifc_file in self.select_target.dict_elements.keys():
            list_of_elements = self.select_target.dict_elements[ifc_file]
            for element in list_of_elements:
                add_to_display(element, geom_settings, orange)

        # The geometries registered during run(), by category.
        self._display_registered_items()


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


class AbsoluteOrRelativeChecking:
    """The Must rule: an absolute or relative check of the number of
    elements or of a summed property, per group of results.

    The type selects the measurement: it ends with "Number" (the
    check counts the elements of the sets) or with "Quantity" (the
    check sums the property quantity_pset / quantity_prop over the
    elements of the sets). The measured sets of a group fill
    source_number and target_number.

    The operation is the comparison of the check, written with the
    SOURCE and TARGET keywords: they are replaced by the measured
    numbers of the group, then the operation is evaluated as the
    verdict of the group. A relative check relates the two sets
    ("SOURCE=2*TARGET"), an absolute check compares one set against
    a requirement ("TARGET<=2").

    The grouping comes from the rule: its classic grouping
    (run_grouping, driven by select_grouping) produces the groups, or
    one group per source object when the rule has no grouping.

    The check is a rule in itself: once every group is evaluated,
    the results of the rule are its verdicts — one ClashResultComplex
    per group, carrying the elements of the two sets of the group
    and passing or failing as a whole. The individual results are
    consumed, the elements of a group can no longer be taken apart.
    """

    def __init__(self, type: ABSOLUTEORRELATIVECHECK_TYPE):
        if not isinstance(type, str) or not type.startswith(("Absolute", "Relative")):
            raise ValueError(
                f"type must start with 'Absolute' or 'Relative', got {type!r}"
            )
        self.type = type

        # The measured numbers of the current group, filled by
        # number() or quantity() and used by eval_check().
        self.source_number = None
        self.target_number = None

        # The comparison with the SOURCE and TARGET keywords, e.g.
        # "SOURCE=2*TARGET" or "TARGET<=2".
        self.operation: str = None

        # The quantity measurement.
        self.quantity_pset: str = None
        self.quantity_prop: str = None

    def run(self, rule):
        """The check of the results of a rule, grouped by the
        grouping of the rule: run_grouping (driven by
        select_grouping), or one group per source object when the
        rule has no grouping (or its grouping produces no group).

        The check is a rule in itself: the evaluated groups become
        the results of the rule, one ClashResultComplex per group
        carrying the elements of its two sets and passing or failing
        as a whole. The individual results are consumed — kept aside
        on the rule only so the check can run again on it — the
        elements of a group can no longer be taken apart."""
        if any(
            isinstance(oneresult, ClashResultComplex) for oneresult in rule.result
        ):
            # The results were already consumed by a previous check
            # of the same rule: group again from the individual
            # results kept aside.
            rule.result = list(rule.result_before_abs_or_rel)
        else:
            rule.result_before_abs_or_rel = list(rule.result)

        rule.grouped_result = []
        rule.run_grouping()
        if not rule.grouped_result:
            rule.group_by_source()

        for onegroupresult in rule.grouped_result:
            self.eval_check(onegroupresult)

        rule.result = [
            ClashResultComplex(
                sources=onegroupresult.source_set,
                targets=onegroupresult.target_set,
                state=onegroupresult.abs_or_rel_check,
            )
            for onegroupresult in rule.grouped_result
        ]

    def number(self, groupresult: GroupResult):
        """The element counts of the two sets of the group."""
        self.source_number = len(groupresult.source_set)
        self.target_number = len(groupresult.target_set)

    @staticmethod
    def _to_number(value):
        """A property value as a float, whatever its storage.

        A number is used as is, a number written as a string ("2.5")
        is parsed, anything else (None, pure text) counts as 0: it
        cannot be measured.
        """
        if value is None:
            return 0.0
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def quantity(self, groupresult: GroupResult):
        """The summed property values of the two sets of the group.

        The values come in any form — a number, a number written as a
        string or pure text — see _to_number: the unmeasurable values
        count 0, the check never fails on a value. Without a
        quantity_pset / quantity_prop, nothing can be measured: both
        sets count 0.
        """
        if not self.quantity_pset or not self.quantity_prop:
            self.source_number = 0.0
            self.target_number = 0.0
            return

        source_total = 0.0
        for entity in groupresult.source_set:
            value = get_pset(entity, name=self.quantity_pset, prop=self.quantity_prop)
            source_total += self._to_number(value)
        self.source_number = source_total

        target_total = 0.0
        for entity in groupresult.target_set:
            value = get_pset(entity, name=self.quantity_pset, prop=self.quantity_prop)
            target_total += self._to_number(value)
        self.target_number = target_total

    def _measure(self, groupresult: GroupResult):
        """The measurement selected by the type: number or quantity."""
        if "Quantity" in self.type:
            self.quantity(groupresult)
        else:
            self.number(groupresult)

    def eval_check(self, groupresult: GroupResult):
        """The verdict of the group: the operation with the SOURCE and
        TARGET keywords replaced by the measured numbers of the group.

        A relative operation compares the two sets ("SOURCE=2*TARGET"),
        an absolute one only names the measured set ("TARGET<=2").
        """
        self._measure(groupresult)

        operation_string = (
            str(self.operation)
            .replace("SOURCE", str(self.source_number))
            .replace("TARGET", str(self.target_number))
        )

        groupresult.abs_or_rel_check = eval(operation_string)

        return groupresult


# ==== Clash Result
class ClashResult:
    def __init__(self, source, state, type="OneObjectResult"):
        # @todo ClashResult, complete all the data.
        self.id: str
        self.type: str = type
        self.source: ifcopenshell.entity_instance = source
        self.rule_name: str = None

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
        self.distance_between: float = None
        self.penetration_depth: float = None
        self.volume_intersection: float = None
        self.volume_ratio: float = None
        self.containement_ratio: float = None
        self.surface_contact_area: float = None
        self.penetration_direction: float = None
        self.clearance_violated_volume: float = None


class ClashResultComplex(ClashResult):
    """The result of a Must check (AbsoluteOrRelativeChecking): the
    verdict of one evaluated group. The group is the result, an
    atomic whole: sources and targets carry the elements of its two
    sets (the measured set as sources, the others as targets), they
    can no longer be taken apart."""


    #This result is used as well in the AbsOrRelCheck. 
    #I should not inherit from ClashResult. Clash_Result is linked to OneObject and TwoObject way to much.

    def __init__(self, sources, targets, state, type="ComplexResult"):
        super().__init__(None, state, type)
        self.sources: list[ifcopenshell.entity_instance] = list(sources)
        self.targets: list[ifcopenshell.entity_instance] = list(targets)
        self.context: list[ifcopenshell.entity_instance] = None


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

class ResultAnalyze:
    def __init__(self):
        self.id: str
        self.type: str = type
        self.result_group: list[ClashResult] = []
        self.source_set: set(ifcopenshell.entity_instance) = set()
        self.target_set: set(ifcopenshell.entity_instance) = set()
        self.abs_or_rel_check = None


class BCF_Subject:
    def __init__(self):
        self.id: str
        self.type: str = type

    def add_result_to_subject():
        ...
    def remove_result_to_subject():
        ...
    def create_new_subjet():
        ...
