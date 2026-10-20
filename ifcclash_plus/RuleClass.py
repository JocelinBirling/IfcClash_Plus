from __future__ import annotations

from typing import List

import ifcopenshell
import uuid
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
from typing import Literal, NamedTuple, TypedDict, Union

from abc import abstractmethod
from dataclasses import dataclass

from booleanrule import BooleanRule, BooleanLeaf
from pipeline import ResultPipeline, RuleOutput

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
            self.list_of_elements = (
                list(self.dict_elements.get(onefile) or []) + self.list_of_elements
            )


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
                # ifctester >= 0.9 compares the name of an Entity facet
                # case-sensitively against the uppercased IFC classes
                # (its IFC2X3 filter branch): the entity names are
                # case-insensitive in IDS, they are normalized here.
                if (
                    isinstance(one_applicability, Entity)
                    and isinstance(one_applicability.name, str)
                    and one_applicability.name != one_applicability.name.upper()
                ):
                    one_applicability.name = one_applicability.name.upper()

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
        self.select_grouping: SelectFacet | str = None #This select Grouping should produce a Complex Result. Is it still usefull ? (Let this to the viewer)
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

        # The output of the ResultPipeline (results, selection,
        # groups), produced by end_rule_action.
        self.output: RuleOutput = None

        # The display geometry registry: filled during run() as a
        # by-product of the computation, read by the generic display.
        self.display_items: list[DisplayItem] = []
        self.display_options: dict[DISPLAY_CATEGORY, bool] = {
            category: True for category in DISPLAY_CATEGORIES
        }
        self.keep_display_items: bool = True

    def end_rule_action(self):
        # The management steps (exception, criticity, actor,
        # grouping/must, select) live in the ResultPipeline, outside
        # of the rule computation (SPEC Separation moteur/gestion).
        # The state routing below stays on the rule until the
        # orchestrator migration.
        self.output = ResultPipeline(self).apply()

        if self.state == "Display_Input":
            self._display_input_generic()
            self.display.FitAll()
            self.start_display()
            return
        if self.state == "Display_Result":
            self.display_result()
        if self.state == "Final":
            if not self.keep_display_items:
                # The registry is a temporary by-product: free the
                # memory on the big models when it is not kept.
                self.display_items.clear()

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
        """Add the elements of a selection to self.tree.

        ifcopenshell >= 0.9 has typed tree backends: "BVH" feeds the
        clash tree (opencascade.trianglebvh) with the triangulation
        elements of a plain settings iterator, "UB" feeds the ray tree
        (opencascade.brep) with the native brep elements of a
        Python-OCC settings iterator (which also implies world
        coordinates).
        """
        if type_of_tree == "BVH":
            tree_settings = ifcopenshell.geom.settings()
        else:
            tree_settings = ifcopenshell.geom.settings()
            tree_settings.set("USE_PYTHON_OPENCASCADE", True)

        for ifc_file, elements in Select.dict_elements.items():
            if not elements:
                continue
            iterator = ifcopenshell.geom.iterator(
                tree_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=elements,
            )

            if not iterator.initialize():
                continue
            while True:
                if type_of_tree == "BVH":
                    self.tree.add_element(iterator.get())
                else:
                    self.tree.add_element(iterator.get_native())

                if not iterator.next():
                    break

    def add_OneObject_to_tree(self, Object, type_of_tree):
        if type_of_tree == "BVH":
            tree_settings = ifcopenshell.geom.settings()
        else:
            tree_settings = ifcopenshell.geom.settings()
            tree_settings.set("USE_PYTHON_OPENCASCADE", True)

        iterator = ifcopenshell.geom.iterator(
            tree_settings,
            Object.file,
            multiprocessing.cpu_count(),
            include=[Object],
        )

        assert iterator.initialize()
        while True:
            if type_of_tree == "BVH":
                self.tree.add_element(iterator.get())
            else:
                self.tree.add_element(iterator.get_native())

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


# ==== Result Info
class PointEntry(NamedTuple):
    """Une entrée de source_points / target_points."""

    number: int  # le numéro de paire
    point: tuple  # (x, y, z)
    label: str | None = None  # libre (ex. "entry"/"exit")


class FaceData(NamedTuple):
    """Une face d'une paire, côté source ou target."""

    normal: tuple  # unitaire, (x, y, z)
    area: float  # m2
    triangles: list = []  # triangles d'origine (3 points chacun) ou []


class FaceEntry(NamedTuple):
    """Une entrée de source_faces / target_faces."""

    number: int  # le numéro de paire
    face: FaceData


class ObbData(NamedTuple):
    """Un OBB porté par le résultat (objet propre ou zone de détection)."""

    center: tuple  # (x, y, z)
    axes: tuple  # 3 directions orthonormées, chacune (x, y, z)
    half_sizes: tuple  # 3 demi-tailles (m)
    label: str | None = None  # libre ("object", "zone"...)


class RaycastData(NamedTuple):
    """DirectView : le détail du lancer de rayons — provenance : une seule
    règle (DirectView). Les consommateurs ne lisent que hit_ratio
    (hit / cast) ; les segments servent à l'affichage."""

    planned: int  # rayons prévus
    cast: int  # rayons effectivement lancés
    hit: int  # rayons ayant touché l'autre objet
    hit_segments: list = []  # segments origine->but, chaque segment : 2 points
    blocked_segments: list = []


class ZoneData(NamedTuple):
    """ClearanceForDoors : la zone de dégagement balayée par le
    bloc-porte — provenance : une seule règle (ClearanceForDoors).
    Le solide OCC reste dans le registre d'affichage ; ces seules
    dimensions sérialisables suffisent à le reconstruire."""

    side: str  # côté du bloc-porte (ex. "Front")
    leaf: str  # type de vantail (ex. "SingleSwingLeft")
    width: float  # largeur balayée (m)
    depth: float  # profondeur (m)
    height: float  # hauteur (m)


# La forme sérialisable du contrat (voir to_dict) : c'est elle que
# consomment la sérialisation, le futur C++ et la feuille de test.
RESULT_SHAPE = {
    # measure : une entrée par mesure posée, la clé = le nom de la
    # mesure, dans l'ordre de pose (la première = nominale)
    "measure": {
        "distance": {"value": float},
    },
    "points": [
        {
            "number": int,  # le numéro de paire
            "source": tuple,  # POINT : (x, y, z)
            "target": tuple,  # POINT
            "label": str,  # optionnel, libre
        },
    ],
    "faces": [
        {
            "number": int,  # le numéro de paire
            "source": {
                "normal": tuple,  # POINT
                "area": float,
                "triangles": list,
            },
            "target": {"normal": tuple, "area": float, "triangles": list},
        },
    ],
    "volumes": {
        "intersection": float,  # m3
        "ratio": float,  # 0..1
        "containment": float,  # 0..1
        "clearance_violated": float,  # m3
    },
    "obbs": {
        # deux listes indépendantes, non appariées
        "source": [
            {
                "center": tuple,  # POINT
                "axes": list,  # [POINT, POINT, POINT]
                "half_sizes": tuple,
                "label": str,  # optionnel
            },
        ],
        "target": [dict],
    },
    # -- Les blocs propres à une règle : présents seulement si posés,
    #    documentés dans la classe (fonctionnement + provenance) ;
    #    les consommateurs génériques les ignorent.
    "axis": {  # ClearanceAxisToAxis
        "mode": str,
        "degraded": bool,
    },
    "raycast": {  # DirectView
        "planned": int,
        "cast": int,
        "hit": int,  # hit_ratio = hit / cast
        "hit_segments": list,  # [(POINT, POINT)]
        "blocked_segments": list,  # [(POINT, POINT)]
    },
    "zone": {  # ClearanceForDoors
        "side": str,
        "leaf": str,
        "width": float,  # m
        "depth": float,  # m
        "height": float,  # m
    },
}


class ResultInfo:
    """Toutes les données qu'une règle attache à un résultat, hors noyau
    commun.

    Les mesures scalaires sont des attributs déclarés (vocabulaire de la
    table des mesures, doc/specification_ResultData.md section 4) :
    ``info.distance = 0.42``. Les structures sont des listes de
    NamedTuple — des tuples : l'append direct d'un tuple nu reste
    valide. Aucun contrôle à l'écriture ni pendant la run — le contrat
    est vérifié aux tests par validate(). La plupart des propriétés
    restent vides la plupart du temps — la classe existe aussi pour
    porter les méthodes qui dispatchent selon le contenu du résultat.

    Les blocs propres à une seule règle sont des attributs déclarés
    comme les autres (pas de dict) :

    - ``axis_mode`` / ``axis_degraded`` (str / bool | None) — le mode
      de calcul de l'axe et son caractère dégradé ; produit par
      ClearanceAxisToAxis uniquement.
    - ``raycast`` (RaycastData | None) — le détail du lancer de rayons ;
      produit par DirectView uniquement.
    - ``zone`` (ZoneData | None) — la zone de dégagement du bloc-porte ;
      produite par ClearanceForDoors uniquement.
    """

    # Le vocabulaire des mesures — pour en ajouter une : déclarer
    # l'attribut dans __init__, l'ajouter ici et à RESULT_SHAPE.
    MEASURE_ATTRIBUTES = frozenset(
        {
            "distance",
            "penetration_depth",
            "contact_area",
            "ratio",
            "offset",
            "hit_ratio",
            "angle",
        }
    )

    def __init__(self):
        # Ordre de pose des mesures (suivi interne pour la nominale) :
        # posé en premier pour que __setattr__ puisse le lire.
        self._measure_order: list[str] = []

        # -- Les mesures scalaires : attributs déclarés, None = non
        #    mesurée. La première mesure POSÉE (non None) est la mesure
        #    nominale du résultat. L'unité est portée par le
        #    vocabulaire (section 4), la donnée est un float nu.
        self.distance: float | None = None  # m
        self.penetration_depth: float | None = None  # m
        self.contact_area: float | None = None  # m2
        self.ratio: float | None = None  # 0..1
        self.offset: float | None = None  # m
        self.hit_ratio: float | None = None  # 0..1
        self.angle: float | None = None  # deg

        # -- Les points de contact / proximité, appariés PAR NUMÉRO :
        #    l'entrée n° N de source_points répond à l'entrée n° N de
        #    target_points. Le numéro est posé par add_point_pair ;
        #    validate() contrôle qu'aucun numéro n'est orphelin.
        self.source_points: list[PointEntry] = []
        self.target_points: list[PointEntry] = []

        # -- Les faces, appariées PAR NUMÉRO : la face n° N de
        #    source_faces est vérifiée contre la face n° N de
        #    target_faces. Le numéro est posé par add_face_pair. Pour
        #    une règle mono-objet, les deux côtés de la paire portent
        #    sur le même élément (le source).
        self.source_faces: list[FaceEntry] = []
        self.target_faces: list[FaceEntry] = []

        # -- Les mesures volumiques : attributs scalaires, None = non
        #    mesurée.
        self.volume_intersection: float | None = None  # m3
        self.volume_ratio: float | None = None  # 0..1, relatif au plus petit
        self.containment_ratio: float | None = None  # 0..1
        self.clearance_violated_volume: float | None = None  # m3

        # -- Les OBB, NON appariés : deux listes indépendantes (un
        #    élément peut porter son propre OBB et ses zones de
        #    détection, distinguées par label). ObbData est complet :
        #    le solide OCC se reconstruit depuis ses seules données.
        self.source_obbs: list[ObbData] = []
        self.target_obbs: list[ObbData] = []

        # -- Les données propres à une seule règle (voir docstring).
        self.axis_mode: str | None = None  # "Perpendicular" | "MinDistance" | "Fallback"
        self.axis_degraded: bool | None = None  # True si fallback géométrique
        self.raycast: RaycastData | None = None  # DirectView
        self.zone: ZoneData | None = None  # ClearanceForDoors

    def __setattr__(self, name, value):
        # Écriture suivie, silencieuse : aucune validation, aucune
        # alarme — seulement l'ordre de pose des mesures (une pose à
        # None retire la mesure de l'ordre).
        if name in self.MEASURE_ATTRIBUTES:
            order = self.__dict__.get("_measure_order")
            if order is not None:
                if value is None:
                    if name in order:
                        order.remove(name)
                elif name not in order:
                    order.append(name)
        object.__setattr__(self, name, value)

    # ---- L'écriture des listes (append n'est pas intercepté)
    def add_point_pair(self, source, target, label=None) -> int:
        """Pose le numéro N sur les deux côtés, retourne N.

        Coerce l'entrée nue : PointEntry(N, tuple(source), label)."""
        number = len(self.source_points) + 1
        self.source_points.append(PointEntry(number, tuple(source), label))
        self.target_points.append(PointEntry(number, tuple(target), label))
        return number

    def add_face_pair(self, source_face, target_face) -> int:
        """Pose le numéro N sur les deux côtés, retourne N.

        Coerce via FaceData(*source_face) : un tuple nu passe tel quel,
        aucune forme d'appel à changer dans les règles."""
        number = len(self.source_faces) + 1
        self.source_faces.append(
            FaceEntry(number, FaceData(*source_face))
        )
        self.target_faces.append(
            FaceEntry(number, FaceData(*target_face))
        )
        return number

    def add_source_obb(self, obb) -> None:
        """Coerce via ObbData(*obb)."""
        self.source_obbs.append(ObbData(*obb))

    def add_target_obb(self, obb) -> None:
        """Coerce via ObbData(*obb)."""
        self.target_obbs.append(ObbData(*obb))

    # ---- Lecture
    @property
    def primary_measure(self) -> str | None:
        """Le nom de la mesure nominale (première posée), None sinon."""
        return self._measure_order[0] if self._measure_order else None

    def measure(self, check) -> float | None:
        """La valeur de la mesure demandée, None si non posée."""
        return getattr(self, check, None)

    @property
    def has_volumes(self) -> bool:
        """Vrai si au moins un attribut volumique est renseigné."""
        return any(
            getattr(self, name) is not None
            for name in (
                "volume_intersection",
                "volume_ratio",
                "containment_ratio",
                "clearance_violated_volume",
            )
        )

    # ---- Contrôle (aux tests uniquement)
    def validate(self) -> list[str]:
        """Passe de contrôle de tout le contenu : mesures posées
        numériques, points 3D, faces et OBB bien formés (y compris les
        appends directs), numéros de paires appariés — aucun numéro
        orphelin d'un seul côté —, blocs propres à une règle bien
        formés. Retourne la liste des fautes, sans effet de bord :
        appelée par la feuille de test, jamais pendant la run. Les
        champs NamedTuple nomment le fautif dans la faute
        (``faces[2].face.area: str != float``) au lieu d'un index."""

        def is_number(value):
            return isinstance(value, (int, float)) and not isinstance(value, bool)

        def point_fault(path, value):
            if not isinstance(value, tuple) or len(value) != 3:
                return [f"{path}: {type(value).__name__} != 3-tuple"]
            for coordinate in value:
                if not is_number(coordinate):
                    return [f"{path}: {type(coordinate).__name__} != number"]
            return []

        def points_fault(path, value):
            return point_fault(f"{path}.point", value)

        faults = []

        # Les mesures posées doivent être numériques.
        for name in self.MEASURE_ATTRIBUTES:
            value = getattr(self, name)
            if value is not None and not is_number(value):
                faults.append(f"{name}: {type(value).__name__} != number")

        # Les points : structure PointEntry et appariement par numéro.
        for attribute in ("source_points", "target_points"):
            for index, entry in enumerate(getattr(self, attribute)):
                path = f"{attribute}[{index}]"
                if not isinstance(entry, tuple) or len(entry) != 3:
                    faults.append(f"{path}: {type(entry).__name__} != PointEntry")
                    continue
                if not isinstance(entry[0], int) or isinstance(entry[0], bool):
                    faults.append(f"{path}.number: {type(entry[0]).__name__} != int")
                faults.extend(points_fault(path, entry[1]))
                if entry[2] is not None and not isinstance(entry[2], str):
                    faults.append(f"{path}.label: {type(entry[2]).__name__} != str")
        source_numbers = {
            entry[0] for entry in self.source_points if isinstance(entry, tuple)
        }
        target_numbers = {
            entry[0] for entry in self.target_points if isinstance(entry, tuple)
        }
        for orphan in sorted(source_numbers ^ target_numbers):
            faults.append(f"points: orphan pair number {orphan}")

        # Les faces : structure FaceEntry/FaceData et appariement.
        def face_data_faults(path, face):
            if not isinstance(face, tuple) or len(face) != 3:
                return [f"{path}: {type(face).__name__} != FaceData"]
            faults_ = point_fault(f"{path}.normal", face[0])
            if not is_number(face[1]):
                faults_.append(f"{path}.area: {type(face[1]).__name__} != float")
            if not isinstance(face[2], list):
                faults_.append(f"{path}.triangles: {type(face[2]).__name__} != list")
            else:
                for triangle_index, triangle in enumerate(face[2]):
                    triangle_path = f"{path}.triangles[{triangle_index}]"
                    if not isinstance(triangle, tuple) or len(triangle) != 3:
                        faults_.append(
                            f"{triangle_path}: {type(triangle).__name__} != triangle"
                        )
                        continue
                    for vertex in triangle:
                        faults_.extend(point_fault(triangle_path, vertex))
            return faults_

        for attribute in ("source_faces", "target_faces"):
            for index, entry in enumerate(getattr(self, attribute)):
                path = f"{attribute}[{index}]"
                if not isinstance(entry, tuple) or len(entry) != 2:
                    faults.append(f"{path}: {type(entry).__name__} != FaceEntry")
                    continue
                if not isinstance(entry[0], int) or isinstance(entry[0], bool):
                    faults.append(f"{path}.number: {type(entry[0]).__name__} != int")
                faults.extend(face_data_faults(f"{path}.face", entry[1]))
        source_face_numbers = {
            entry[0] for entry in self.source_faces if isinstance(entry, tuple)
        }
        target_face_numbers = {
            entry[0] for entry in self.target_faces if isinstance(entry, tuple)
        }
        for orphan in sorted(source_face_numbers ^ target_face_numbers):
            faults.append(f"faces: orphan pair number {orphan}")

        # Les OBB : structure ObbData, demi-tailles positives.
        for attribute in ("source_obbs", "target_obbs"):
            for index, entry in enumerate(getattr(self, attribute)):
                path = f"{attribute}[{index}]"
                if not isinstance(entry, tuple) or len(entry) != 4:
                    faults.append(f"{path}: {type(entry).__name__} != ObbData")
                    continue
                faults.extend(point_fault(f"{path}.center", entry[0]))
                if not isinstance(entry[1], tuple) or len(entry[1]) != 3:
                    faults.append(f"{path}.axes: {type(entry[1]).__name__} != 3-tuple")
                else:
                    for axis_index, axis in enumerate(entry[1]):
                        faults.extend(
                            point_fault(f"{path}.axes[{axis_index}]", axis)
                        )
                if (
                    not isinstance(entry[2], tuple)
                    or len(entry[2]) != 3
                    or not all(is_number(size) for size in entry[2])
                ):
                    faults.append(
                        f"{path}.half_sizes: {type(entry[2]).__name__} != 3 numbers"
                    )
                elif any(size < 0 for size in entry[2]):
                    faults.append(f"{path}.half_sizes: negative")
                if entry[3] is not None and not isinstance(entry[3], str):
                    faults.append(f"{path}.label: {type(entry[3]).__name__} != str")

        # Les blocs propres à une règle.
        if self.axis_mode is not None and not isinstance(self.axis_mode, str):
            faults.append(f"axis_mode: {type(self.axis_mode).__name__} != str")
        if self.axis_degraded is not None and not isinstance(
            self.axis_degraded, bool
        ):
            faults.append(f"axis_degraded: {type(self.axis_degraded).__name__} != bool")

        if self.raycast is not None:
            raycast = self.raycast
            if not isinstance(raycast, tuple) or len(raycast) != 5:
                faults.append(f"raycast: {type(raycast).__name__} != RaycastData")
            else:
                for name in ("planned", "cast", "hit"):
                    value = raycast[RaycastData._fields.index(name)]
                    if not isinstance(value, int) or isinstance(value, bool):
                        faults.append(
                            f"raycast.{name}: {type(value).__name__} != int"
                        )
                for name, position in (("hit_segments", 3), ("blocked_segments", 4)):
                    segments = raycast[position]
                    if not isinstance(segments, list):
                        faults.append(
                            f"raycast.{name}: {type(segments).__name__} != list"
                        )
                        continue
                    for segment_index, segment in enumerate(segments):
                        segment_path = f"raycast.{name}[{segment_index}]"
                        if not isinstance(segment, tuple) or len(segment) != 2:
                            faults.append(
                                f"{segment_path}: {type(segment).__name__} != segment"
                            )
                            continue
                        faults.extend(point_fault(f"{segment_path}[0]", segment[0]))
                        faults.extend(point_fault(f"{segment_path}[1]", segment[1]))

        if self.zone is not None:
            zone = self.zone
            if not isinstance(zone, tuple) or len(zone) != 5:
                faults.append(f"zone: {type(zone).__name__} != ZoneData")
            else:
                for name in ("side", "leaf"):
                    value = zone[ZoneData._fields.index(name)]
                    if not isinstance(value, str):
                        faults.append(f"zone.{name}: {type(value).__name__} != str")
                for name in ("width", "depth", "height"):
                    value = zone[ZoneData._fields.index(name)]
                    if not is_number(value):
                        faults.append(
                            f"zone.{name}: {type(value).__name__} != float"
                        )

        return faults

    # ---- La frontière d'export
    def to_dict(self) -> dict:
        """La forme sérialisable du contrat (RESULT_SHAPE) : c'est ici,
        et ici seulement, que les attributs et tuples deviennent des
        dicts. Les entrées sont appariées par leur numéro de paire ;
        un bloc absent n'est pas posé (une règle remplit ce qu'elle
        mesure)."""
        data = {}

        if self._measure_order:
            data["measure"] = {
                name: {"value": getattr(self, name)} for name in self._measure_order
            }

        source_points = {entry.number: entry for entry in self.source_points}
        target_points = {entry.number: entry for entry in self.target_points}
        points = []
        for number in sorted(source_points):
            target_entry = target_points.get(number)
            if target_entry is None:
                continue
            source_entry = source_points[number]
            point = {
                "number": number,
                "source": source_entry.point,
                "target": target_entry.point,
            }
            label = source_entry.label or target_entry.label
            if label is not None:
                point["label"] = label
            points.append(point)
        if points:
            data["points"] = points

        source_faces = {entry.number: entry for entry in self.source_faces}
        target_faces = {entry.number: entry for entry in self.target_faces}
        faces = []
        for number in sorted(source_faces):
            target_entry = target_faces.get(number)
            if target_entry is None:
                continue
            faces.append(
                {
                    "number": number,
                    "source": source_faces[number].face._asdict(),
                    "target": target_entry.face._asdict(),
                }
            )
        if faces:
            data["faces"] = faces

        volumes = {
            name: getattr(self, attribute)
            for name, attribute in (
                ("intersection", "volume_intersection"),
                ("ratio", "volume_ratio"),
                ("containment", "containment_ratio"),
                ("clearance_violated", "clearance_violated_volume"),
            )
            if getattr(self, attribute) is not None
        }
        if volumes:
            data["volumes"] = volumes

        def obb_dict(obb):
            if not hasattr(obb, "_asdict"):
                # Un append direct de tuple nu reste valide.
                obb = ObbData(*obb)
            export = obb._asdict()
            if export["label"] is None:
                del export["label"]
            # Le contrat exporte les axes en liste.
            export["axes"] = list(export["axes"])
            return export

        obbs = {}
        if self.source_obbs:
            obbs["source"] = [obb_dict(obb) for obb in self.source_obbs]
        if self.target_obbs:
            obbs["target"] = [obb_dict(obb) for obb in self.target_obbs]
        if obbs:
            data["obbs"] = obbs

        if self.axis_mode is not None or self.axis_degraded is not None:
            data["axis"] = {"mode": self.axis_mode, "degraded": self.axis_degraded}

        if self.raycast is not None:
            raycast = self.raycast
            if not hasattr(raycast, "_asdict"):
                # Un tuple nu posé directement reste valide.
                raycast = RaycastData(*raycast)
            data["raycast"] = {
                "planned": raycast.planned,
                "cast": raycast.cast,
                "hit": raycast.hit,
                "hit_segments": list(raycast.hit_segments),
                "blocked_segments": list(raycast.blocked_segments),
            }

        if self.zone is not None:
            zone = self.zone
            if not hasattr(zone, "_asdict"):
                # Un tuple nu posé directement reste valide.
                zone = ZoneData(*zone)
            data["zone"] = zone._asdict()

        return data


VALIDATION_STATUS = Literal[
    "Validate", "Undetermined", "", "Refuse"
]

# ==== Clash Result
class ClashResult:
    def __init__(self, source, state, type="ClashResult"):
        # @todo ClashResult, complete all the data.
        self.id: str = str(uuid.uuid4())
        self.type: str = type
        self.source: ifcopenshell.entity_instance = source
        self.rule_name: str = None

        self.status: bool = state
        self.criticity: list[str] = []
        self.actor: list[str] = []

        # Toutes les données hors noyau commun portées par le résultat.
        self.info: ResultInfo = ResultInfo()


        self.validation_status: ABSOLUTEORRELATIVECHECK_TYPE = VALIDATION_STATUS


class ClashResultOneObject(ClashResult):
    def __init__(self, source, state):
        super().__init__(source, state)


class ClashResultTwoObjects(ClashResult):
    def __init__(self, source, target, state, type="TwoObjectsResult"):
        super().__init__(source, state, type)
        self.target: ifcopenshell.entity_instance = target


class ClashResultComplex:
    """The result of a Must check (AbsoluteOrRelativeChecking): the
    verdict of one evaluated group. The group is the result, an
    atomic whole: sources and targets carry the elements of its two
    sets (the measured set as sources, the others as targets), they
    can no longer be taken apart.

    Independent from ClashResult: the verdict of a group of
    elements, not of one object or one pair. It carries the common
    result core (id, type, status, criticity, actor) but its
    elements are lists, and it has no single source attribute."""

    def __init__(self, sources, targets, state, type="ComplexResult"):
        self.id: str = str(uuid.uuid4())
        self.type: str = type
        self.sources: list[ifcopenshell.entity_instance] = list(sources)
        self.targets: list[ifcopenshell.entity_instance] = list(targets)
        self.context: list[ifcopenshell.entity_instance] = None

        self.status: bool = state
        self.criticity: list[str] = []
        self.actor: list[str] = []

        # Le noyau commun porte aussi la classe des données du résultat.
        self.info: ResultInfo = ResultInfo()


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
