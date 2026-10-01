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

from RuleClass import SelectFacet, SelectRule, RuleFile
from Rules import Select, Volume, Area,Intersection
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
from serialization import save_configuration_to_json,save_to_json,create_configuration_from_rule_file,load_configuration_from_json,apply_configuration_to_rule_file

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



if __name__ == "__main__":
    unittest.main()
