"""
Test file for RuleFile class functionality.

This file contains various test cases to verify the correct behavior of the RuleFile class,
including loading IFC files, adding rules, executing checks, and managing results.
"""

import unittest
import ifcopenshell
import sys
sys.path.insert(0, './ifcclash_plus')
from Rules import  Intersection, Above,Below ,OBB_Above,Clearance,Collision,OBB_Below, AngleBetween,Volume,Ray_Check
from RuleClass import SelectFacet,RuleFile,ClashResultOneObject,ClashResultTwoObjects,RuleFolder,SelectRule
from booleanrule import BooleanLeaf
from ifctester import ids
import os


class TestRuleFileBasic(unittest.TestCase):
    """Test basic RuleFile functionalities."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_ifc_path = None
        # Try to find an example IFC file in the repository
        possible_paths = [
            "/home/jocelin/Documents/05 - Programmation/IfcClash_Plus/Ifc_Model/Ifc2x3_Duplex_Architecture_with_suzanne.ifc",
            "/home/jocelin/Documents/05 - Programmation/IfcClash_Plus/Ifc_Model/Ifc2x3_Duplex_MEP.ifc",
        ]
        for path in possible_paths:
            if os.path.exists(path):
                self.test_ifc_path = path
                break
        

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, '_temp_ifc_file') and self._temp_ifc_file:
            os.remove(self._temp_ifc_file)

    def test_RuleFile_initialization(self):
        """Test RuleFile can be initialized."""
        rule_file = RuleFile()
        self.assertIsInstance(rule_file, RuleFile)
        self.assertEqual(rule_file.list_ifc_path, [])
        self.assertEqual(rule_file.list_ifc_file, [])
        self.assertEqual(rule_file.contains, [])


    def test_RuleFile_load_file(self):
        """Test RuleFile can load IFC files."""
        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.test_ifc_path]
        rule_file.load_file()
        
        self.assertEqual(len(rule_file.list_ifc_file), 1)
        self.assertIsNotNone(rule_file.list_ifc_file[0])

    def test_RuleFile_update_file_info(self):
        """Test RuleFile can update file info in contained rules."""
        rule_file = RuleFile()
        possible_paths = [
            "/home/jocelin/Documents/05 - Programmation/IfcClash_Plus/Ifc_Model/Ifc2x3_Duplex_Architecture.ifc",
            "/home/jocelin/Documents/05 - Programmation/IfcClash_Plus/Ifc_Model/Ifc2x3_Duplex_MEP.ifc",
        ]
        rule_file.list_ifc_path=possible_paths


        rule_file.load_file()
        
        # Create a SelectFacet
        from ifctester.facet import Facet, Entity
        
        # Create a simple select
        from ifcclash_plus.Rules import Collision

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCSLAB")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule_collision=Collision(first_select,second_select)
                
        rule_file.contains = [rule_collision]
        rule_file.update_file_info()


        for rule in rule_file.contains:
            self.assertEqual(len(rule.select_source.list_ifc_file), 2)
            self.assertEqual(len(rule.select_target.list_ifc_file), 2)
            self.assertEqual(len(rule.select_source.list_ifc_path), 2)
            self.assertEqual(len(rule.select_target.list_ifc_path), 2)


class TestRuleFileWithRules(unittest.TestCase):
    """Test RuleFile with actual rules."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_ifc_path = None
        possible_paths = [
            "/home/jocelin/Documents/05 - Programmation/IfcClash_Plus/Ifc_Model/Ifc2x3_Duplex_Architecture.ifc",
            "/home/jocelin/Documents/05 - Programmation/IfcClash_Plus/Ifc_Model/Ifc2x3_Duplex_MEP.ifc",
        ]

        self.test_ifc_path=possible_paths


    def test_RuleFile_with_multiple_rules(self):
        """Test RuleFile can handle multiple rules."""
        rule_file = RuleFile()
        rule_file.list_ifc_path = self.test_ifc_path
        
        # Create multiple rules
        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCDOOR")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule1 = Volume(source=first_select, volume_min=0.0, volume_max=1000.0)
        rule2 = Collision(source=first_select, target=second_select, allow_touching=False)
        
        rule_file.contains = [rule1, rule2]
        
        rule_file.run()


        
        self.assertEqual(len(rule_file.contains[0].result), 56)
        self.assertEqual(len(rule_file.contains[1].result), 7)


    def test_RuleFile_with_Folder(self):
        """Test RuleFile can contain folders."""

        rule_file = RuleFile()
        rule_file.list_ifc_path = self.test_ifc_path

        folder=RuleFolder()
        
        # Create multiple rules
        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCDOOR")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule1 = Volume(source=first_select, volume_min=0.0, volume_max=1000.0)
        rule2 = Collision(source=first_select, target=second_select, allow_touching=False)

        folder.contains=[rule1, rule2]
        
        rule_file.contains = [folder]
        
        rule_file.run()


        
        self.assertEqual(len(rule_file.contains[0].contains[0].result), 56)
        self.assertEqual(len(rule_file.contains[0].contains[1].result), 7)

    def test_RuleFile_with_Folder_activation_rule(self):
        """Test RuleFile can contain folders."""

        rule_file = RuleFile()
        rule_file.list_ifc_path = self.test_ifc_path

        folder=RuleFolder()
        
        # Create multiple rules
        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCDOOR")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule1 = Volume(source=first_select, volume_min=0.0, volume_max=1000.0)
        rule2 = Collision(source=first_select, target=second_select, allow_touching=False)

        folder.contains=[rule2]
        # activation_rule only accepts a SelectFacet or a BooleanRule
        folder.activation_rule=BooleanLeaf(rule1)
        
        rule_file.contains = [folder]
        
        rule_file.run()

        self.assertEqual(len(rule_file.contains[0].contains[0].result), 7)

    def test_RuleFile_with_Folder_activation_facet(self):
        """Test RuleFile can contain folders."""

        rule_file = RuleFile()
        rule_file.list_ifc_path = self.test_ifc_path

        folder=RuleFolder()
        
        # Create multiple rules
        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCDOOR")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule1 = Volume(source=first_select, volume_min=0.0, volume_max=1000.0)
        rule2 = Collision(source=first_select, target=second_select, allow_touching=False)

        folder.contains=[rule2]
        folder.activation_rule=first_select
        
        rule_file.contains = [folder]
        
        rule_file.run()

        self.assertEqual(len(rule_file.contains[0].contains[0].result), 7)

class TestRuleFileWithSelectRule(unittest.TestCase):
    """
    Test rules containing another selection rule (SelectRule) in their
    source or target. Each test checks the four produce_select cases:
    sources passed=True, sources passed=False, targets passed=True and
    targets passed=False. The passed=True quantities are the same as the
    result quantities of the rule unit tests in test_Rule_TwoObjects.py,
    and for every case: elements in the results + elements absent from
    the results = total size of the input selection.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

    def _select_facet(self, entity_name):
        facet = ids.Entity(name=entity_name)
        select = SelectFacet()
        select.applicability = [facet]
        return select

    def _select_rule(self, entity_name):
        # A SelectRule containing a Volume rule with wide bounds:
        # every element of the facet passes the rule, so the produced
        # selection contains the same elements as the facet alone.
        select_rule = SelectRule()
        select_rule.rule = Volume(
            source=self._select_facet(entity_name),
            volume_min=0.0,
            volume_max=1e12,
        )
        return select_rule

    def _count_elements(self, select_dict):
        return sum(len(elements) for elements in select_dict.values())

    def _count_unique_elements(self, select_dict):
        all_elements = []
        for elements in select_dict.values():
            all_elements = all_elements + elements
        return len(set(all_elements))

    def _count_selection(self, select):
        return sum(len(elements) for elements in select.dict_elements.values())

    def _assert_produce_select_quantities(
        self, rule, source_true, source_false, target_true, target_false
    ):
        source_in_results = rule.produce_select(element="source", passed=True)
        source_absent = rule.produce_select(element="source", passed=False)
        target_in_results = rule.produce_select(element="target", passed=True)
        target_absent = rule.produce_select(element="target", passed=False)

        self.assertEqual(self._count_elements(source_in_results), source_true)
        self.assertEqual(self._count_elements(source_absent), source_false)
        self.assertEqual(self._count_elements(target_in_results), target_true)
        self.assertEqual(self._count_elements(target_absent), target_false)

        # Every element of the input selection is either in the results
        # or absent from them.
        self.assertEqual(
            self._count_unique_elements(source_in_results)
            + self._count_elements(source_absent),
            self._count_selection(rule.select_source),
        )
        self.assertEqual(
            self._count_unique_elements(target_in_results)
            + self._count_elements(target_absent),
            self._count_selection(rule.select_target),
        )

    def test_SelectRule_inside_Collision(self):
        """Collision with both selects produced by a SelectRule.
        Same quantity as test_collision_rule: 24 results, all passed.
        Every door collides with a slab, so no source is absent."""
        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        door_select_rule = self._select_rule("IFCDOOR")
        slab_select_rule = self._select_rule("IFCSLAB")

        rule = Collision(
            source=door_select_rule, target=slab_select_rule, allow_touching=False
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

        self.assertEqual(len(rule.result), 24)
        for result in rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)
        self._assert_produce_select_quantities(rule, 24, 0, 24, 7)

    def test_SelectRule_inside_Clearance(self):
        """Clearance with the source produced by a SelectRule.
        Same quantity as test_clearance_rule: 152 results, all passed."""
        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        wall_select_rule = self._select_rule("IFCWALLSTANDARDCASE")
        furnishing_select = self._select_facet("IFCFURNISHINGELEMENT")

        rule = Clearance(
            source=wall_select_rule, target=furnishing_select, clearance=0.5
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

        self.assertEqual(len(rule.result), 152)
        for result in rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)
        self._assert_produce_select_quantities(rule, 152, 14, 152, 14)

    def test_SelectRule_inside_Intersection(self):
        """Intersection with the source produced by a SelectRule.
        Same quantity as test_intersection_rule: 1 result, all passed."""
        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        wall_select_rule = self._select_rule("IFCWALLSTANDARDCASE")
        furnishing_select = self._select_facet("IFCFURNISHINGELEMENT")

        rule = Intersection(
            source=wall_select_rule, target=furnishing_select, tolerance=0.01
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

        self.assertEqual(len(rule.result), 1)
        for result in rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)
        self._assert_produce_select_quantities(rule, 1, 55, 1, 60)

    def test_SelectRule_inside_Ray_Check(self):
        """Ray_Check with the source produced by a SelectRule.
        Same quantity as test_ray_check_rule: 21 results, all passed."""
        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        door_select_rule = self._select_rule("IFCDOOR")
        furnishing_select = self._select_facet("IFCFURNISHINGELEMENT")

        context_facet = ids.Entity(
            name=ids.Restriction(
                options={"enumeration": ["IFCWALLSTANDARDCASE", "IFCSLAB"]}
            )
        )
        context_select = SelectFacet()
        context_select.applicability = [context_facet]

        rule = Ray_Check(
            source=door_select_rule,
            target=furnishing_select,
            context=context_select,
            max_ray_length=5,
            state="Final",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

        self.assertEqual(len(rule.result), 21)
        for result in rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)
        self._assert_produce_select_quantities(rule, 21, 1, 21, 44)


class TestRuleFileProperties(unittest.TestCase):
    """Test RuleFile properties and attributes."""

    def test_RuleFile_id(self):
        """Test RuleFile id property."""
        rule_file = RuleFile()
        rule_file.id = "test_rule_file"
        self.assertEqual(rule_file.id, "test_rule_file")

    def test_RuleFile_path_to_save(self):
        """Test RuleFile path_to_save property."""
        rule_file = RuleFile()
        rule_file.path_to_save = "/tmp/test_output.xml"
        self.assertEqual(rule_file.path_to_save, "/tmp/test_output.xml")


if __name__ == "__main__":
    unittest.main()
