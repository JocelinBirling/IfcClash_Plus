"""
Test file for SelectFacet and SelectRule class functionality.

This file contains various test cases to verify the correct behavior of SelectFacet
and SelectRule classes for filtering and selecting IFC elements.
"""

import unittest
import os
import tempfile
import sys

import ifcopenshell
from ifcopenshell.api import run

sys.path.insert(0, './ifcclash_plus')

from RuleClass import SelectFacet, SelectRule, RuleFile, RuleFolder, AbsoluteChecking
from Rules import Select, Volume, Area,Intersection
from booleanrule import BooleanLeaf, OrRule
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
from serialization import (
    save_configuration_to_json,
    save_to_json,
    create_configuration_from_rule_file,
    load_configuration_from_json,
    apply_configuration_to_rule_file,
    load_from_json,
    serialize_rule_file,
)

class TestSerialization(unittest.TestCase):
    """Test basic SelectFacet functionalities."""

    def setUp(self):
        """Set up test fixtures"""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
        self.ifc_file = ifcopenshell.open(self.ifc_path)

    def test_save_and_load_rule(self):
        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        intersection_rule = Intersection(first_select, second_select, 0.01) 

        OneRuleFile.contains=[intersection_rule]

        config = create_configuration_from_rule_file(OneRuleFile)
        save_configuration_to_json(config, "complex_configuration.json")
        print("Complex configuration saved to complex_configuration.json")


        loaded_config = load_configuration_from_json("complex_configuration.json")
        loaded_rule_file = RuleFile()
        apply_configuration_to_rule_file(loaded_rule_file, loaded_config)

        loaded_rule_file.run()

        self.assertEqual(len(loaded_rule_file.contains[0].result), 1)


class TestSerializationRoundTrip(unittest.TestCase):
    """Round-trip tests: serialize, save, load, then compare or run."""

    def setUp(self):
        """Set up test fixtures"""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def _roundtrip(self, rule_file):
        """Save a RuleFile to a JSON file and load it back."""
        filepath = os.path.join(self.temp_dir.name, "config.json")
        save_to_json(rule_file, filepath)
        return load_from_json(filepath)

    def _build_full_rule_file(self):
        """Build a RuleFile using every serializable feature:
        grouping, criticity, actor, BooleanLeaf exception, SelectRule
        chaining, absolute checking and a folder with a boolean activation.
        """
        wall_select = SelectFacet()
        wall_select.applicability = [ids.Entity(name="IFCWALLSTANDARDCASE")]

        furniture_select = SelectFacet()
        furniture_select.applicability = [ids.Entity(name="IFCFURNISHINGELEMENT")]

        # Volume rule with grouping, criticity and actor
        volume_rule = Volume(wall_select, 0, 100)
        volume_rule.select_grouping = "ENTITY"

        criticity_select = SelectFacet()
        criticity_select.classification_name = "High"
        criticity_select.applicability = [ids.Entity(name="IFCWALLSTANDARDCASE")]
        volume_rule.select_criticity = [criticity_select]

        actor_select = SelectFacet()
        actor_select.classification_name = "Architect"
        actor_select.applicability = [ids.Entity(name="IFCWALLSTANDARDCASE")]
        volume_rule.select_actor = [actor_select]

        # Intersection with a BooleanLeaf exception
        intersection_rule = Intersection(wall_select, furniture_select, 0.01)
        exception_rule = Intersection(None, None, 0.01)
        intersection_rule.select_exception = BooleanLeaf(
            exception_rule, "have_no_result"
        )

        # Absolute checking on the intersection rule
        abs_check = AbsoluteChecking("Absolute_Number")
        abs_check.focus = "source"
        abs_check.operation = ">="
        abs_check.aim = 1
        intersection_rule.abs_or_rel_check = abs_check

        # SelectRule chaining the volume rule
        select_from_volume = SelectRule()
        select_from_volume.rule = volume_rule
        select_from_volume.element_to_pass = "source"
        select_from_volume.element_state_to_pass = False
        area_rule = Area(select_from_volume, 0, 100)

        # Folder activated by a boolean rule
        folder = RuleFolder()
        folder.id = "folder_1"
        folder.activation_case = "ANYTRUE"
        folder.activation_rule = OrRule(volume_rule, intersection_rule)
        folder.contains = [area_rule]

        rule_file = RuleFile()
        rule_file.id = "rf_1"
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [intersection_rule, folder]
        return rule_file

    def test_full_roundtrip_is_identical(self):
        rule_file = self._build_full_rule_file()
        original_data = serialize_rule_file(rule_file)

        loaded = self._roundtrip(rule_file)
        loaded_data = serialize_rule_file(loaded)

        self.assertEqual(loaded_data, original_data)

    def test_boolean_leaf_exception_roundtrip(self):
        rule_file = self._build_full_rule_file()
        loaded = self._roundtrip(rule_file)

        loaded_intersection = loaded.contains[0]
        exception = loaded_intersection.select_exception
        self.assertIsInstance(exception, BooleanLeaf)
        self.assertEqual(exception.mode, "have_no_result")
        self.assertIsNone(exception.value)
        self.assertIsInstance(exception.rule, Intersection)
        self.assertEqual(exception.rule.tolerance, 0.01)
        self.assertIsNone(exception.rule.select_source)
        self.assertIsNone(exception.rule.select_target)

    def test_folder_activation_boolean_roundtrip(self):
        rule_file = self._build_full_rule_file()
        loaded = self._roundtrip(rule_file)

        folder = loaded.contains[1]
        self.assertIsInstance(folder, RuleFolder)
        self.assertEqual(folder.id, "folder_1")
        self.assertEqual(folder.activation_case, "ANYTRUE")

        activation = folder.activation_rule
        self.assertIsInstance(activation, OrRule)
        children = list(activation.children)
        self.assertEqual(len(children), 2)
        self.assertIsInstance(children[0], BooleanLeaf)
        self.assertEqual(children[0].mode, "have_result")
        self.assertIsInstance(children[0].rule, Volume)
        self.assertEqual(children[0].rule.volume_min, 0)
        self.assertEqual(children[0].rule.volume_max, 100)
        self.assertIsInstance(children[1].rule, Intersection)

    def test_select_rule_roundtrip(self):
        rule_file = self._build_full_rule_file()
        loaded = self._roundtrip(rule_file)

        area_rule = loaded.contains[1].contains[0]
        self.assertIsInstance(area_rule, Area)

        select_rule = area_rule.select_source
        self.assertIsInstance(select_rule, SelectRule)
        self.assertEqual(select_rule.element_to_pass, "source")
        self.assertFalse(select_rule.element_state_to_pass)
        self.assertIsInstance(select_rule.rule, Volume)
        self.assertEqual(select_rule.rule.select_grouping, "ENTITY")
        self.assertEqual(
            select_rule.rule.select_criticity[0].classification_name, "High"
        )
        self.assertEqual(
            select_rule.rule.select_actor[0].classification_name, "Architect"
        )

    def test_abs_or_rel_roundtrip(self):
        rule_file = self._build_full_rule_file()
        loaded = self._roundtrip(rule_file)

        check = loaded.contains[0].abs_or_rel_check
        self.assertIsInstance(check, AbsoluteChecking)
        self.assertEqual(check.type, "Absolute_Number")
        self.assertEqual(check.focus, "source")
        self.assertEqual(check.operation, ">=")
        self.assertEqual(check.aim, 1)

    def test_string_exception_roundtrip(self):
        wall_select = SelectFacet()
        wall_select.applicability = [ids.Entity(name="IFCWALLSTANDARDCASE")]
        furniture_select = SelectFacet()
        furniture_select.applicability = [ids.Entity(name="IFCFURNISHINGELEMENT")]

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        intersection_rule = Intersection(wall_select, furniture_select, 0.01)
        intersection_rule.select_exception = "Same_IfcSystem"
        rule_file.contains = [intersection_rule]

        loaded = self._roundtrip(rule_file)
        loaded_rule = loaded.contains[0]
        self.assertEqual(loaded_rule.select_exception, "Same_IfcSystem")

    def test_loaded_rule_file_runs(self):
        wall_select = SelectFacet()
        wall_select.applicability = [ids.Entity(name="IFCWALLSTANDARDCASE")]
        furniture_select = SelectFacet()
        furniture_select.applicability = [ids.Entity(name="IFCFURNISHINGELEMENT")]

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        intersection_rule = Intersection(wall_select, furniture_select, 0.01)
        intersection_rule.select_exception = "Same_IfcSystem"
        rule_file.contains = [intersection_rule]

        loaded = self._roundtrip(rule_file)
        loaded.run()

        self.assertEqual(len(loaded.contains[0].result), 1)



if __name__ == "__main__":
    unittest.main()
