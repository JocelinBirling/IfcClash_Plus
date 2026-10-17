"""
Test file for SelectFacet and SelectRule class functionality.

This file contains various test cases to verify the correct behavior of
SelectFacet and SelectRule classes for filtering and selecting IFC
elements.

- SelectFacet is tested on a small temporary IFC file created with the
  ifcopenshell API (no geometry is needed for the facet filters).
- SelectRule is tested on the Duplex model, because running its inner
  rule requires elements with geometry.
"""

import unittest
import os
import tempfile
import sys

import ifcopenshell
from ifcopenshell.api import run

sys.path.insert(0, './ifcclash_plus')

from RuleClass import SelectFacet, SelectRule, RuleFile
from Rules import Volume, Area, Collision
from ifctester import ids
from ifctester.facet import (
    Entity,
    Property,
    Attribute,
    Classification,
    Material,
)


class TestSelectFacetBasic(unittest.TestCase):
    """Test basic SelectFacet functionalities on a temporary IFC file."""

    def setUp(self):
        """Set up test fixtures with a minimal IFC file."""
        self.test_ifc_path = self._create_temp_ifc()

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, '_temp_ifc_file') and self._temp_ifc_file:
            os.remove(self._temp_ifc_file)

    def _create_temp_ifc(self):
        """Create a temporary IFC file with various entities for testing."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.ifc', delete=False)
        temp_file.close()
        self._temp_ifc_file = temp_file.name

        file = ifcopenshell.file(schema="IFC4")

        # Spatial structure
        run("root.create_entity", file, ifc_class="IfcProject", name="Test Project")
        run("root.create_entity", file, ifc_class="IfcSite", name="Test Site")
        run("root.create_entity", file, ifc_class="IfcBuilding", name="Test Building")
        run("root.create_entity", file, ifc_class="IfcBuildingStorey", name="Level 1")
        run("root.create_entity", file, ifc_class="IfcBuildingStorey", name="Level 2")

        # Products
        run("root.create_entity", file, ifc_class="IfcWall", name="Wall 1")
        run("root.create_entity", file, ifc_class="IfcWall", name="Wall 2")
        door1 = run("root.create_entity", file, ifc_class="IfcDoor", name="Door 1")
        run("root.create_entity", file, ifc_class="IfcDoor", name="Door 2")

        # A property set on Door 1
        pset = run("pset.add_pset", file, product=door1, name="Test Property")
        run("pset.edit_pset", file, pset=pset, properties={"Width": 1.0, "Height": 2.5})

        file.write(temp_file.name)
        return temp_file.name

    def _make_select(self, applicability):
        """A SelectFacet with its file loaded, ready to run."""
        select = SelectFacet()
        select.applicability = applicability
        select.list_ifc_path = [self.test_ifc_path]
        select.list_ifc_file = [ifcopenshell.open(self.test_ifc_path)]
        return select

    def _count_elements(self, select):
        return sum(
            len(elements) for elements in select.dict_elements.values()
        )

    def test_SelectFacet_initialization(self):
        """Test SelectFacet can be initialized."""
        classification_type = "Test Classification"
        select_facet = SelectFacet(ClassificationType=classification_type)

        self.assertIsInstance(select_facet, SelectFacet)
        self.assertEqual(select_facet.type, classification_type)
        self.assertEqual(select_facet.applicability, [])

        # Default initialization
        select_facet = SelectFacet()
        self.assertEqual(select_facet.type, "Facet")
        self.assertEqual(select_facet.dict_elements, {})

    def test_SelectFacet_with_Entity_facet(self):
        """Test SelectFacet with an Entity facet."""
        select_facet = self._make_select([Entity(name="IFCWALL")])
        select_facet.run()

        self.assertEqual(self._count_elements(select_facet), 2)
        for elements in select_facet.dict_elements.values():
            for element in elements:
                self.assertEqual(element.is_a(), "IfcWall")

    def test_SelectFacet_with_Attribute_facet(self):
        """Test SelectFacet with an Attribute facet."""
        select_facet = self._make_select([Attribute(name="Name", value="Wall 1")])
        select_facet.run()

        self.assertEqual(self._count_elements(select_facet), 1)

    def test_SelectFacet_with_Property_facet(self):
        """Test SelectFacet with a Property facet. The Test Property pset
        with the Width property is on Door 1."""
        select_facet = self._make_select(
            [Property(propertySet="Test Property", baseName="Width")]
        )
        select_facet.run()

        self.assertEqual(self._count_elements(select_facet), 1)

    def test_SelectFacet_with_Classification_facet(self):
        """Test SelectFacet with a Classification facet. The temporary
        file has no classification, so nothing is selected."""
        select_facet = self._make_select(
            [Classification(system="Test Classification System", value="Test Value")]
        )
        select_facet.run()

        self.assertEqual(self._count_elements(select_facet), 0)

    def test_SelectFacet_with_Material_facet(self):
        """Test SelectFacet with a Material facet. The temporary file has
        no material, so nothing is selected."""
        select_facet = self._make_select([Material(value="Concrete")])
        select_facet.run()

        self.assertEqual(self._count_elements(select_facet), 0)

    def test_SelectFacet_with_multiple_facets(self):
        """Test SelectFacet with several facets: they are applied one
        after the other, Entity first then Attribute."""
        select_facet = self._make_select(
            [Entity(name="IFCWALL"), Attribute(name="Name", value="Wall 1")]
        )
        select_facet.run()

        self.assertEqual(self._count_elements(select_facet), 1)

    def test_SelectFacet_update_file_info(self):
        """Test SelectFacet can update file info."""
        select_facet = SelectFacet()

        files = [ifcopenshell.open(self.test_ifc_path)]
        select_facet.update_file_info([self.test_ifc_path], files)

        self.assertEqual(select_facet.list_ifc_path, [self.test_ifc_path])
        self.assertEqual(select_facet.list_ifc_file, files)

    def test_SelectFacet_create_list_of_element(self):
        """Test SelectFacet can create a flat list of elements."""
        select_facet = self._make_select([Entity(name="IFCWALL")])
        select_facet.run()
        select_facet.create_list_of_element()

        self.assertIsInstance(select_facet.list_of_elements, list)
        self.assertEqual(len(select_facet.list_of_elements), 2)


class TestSelectRuleBasic(unittest.TestCase):
    """Test basic SelectRule functionalities.

    The Duplex model is used, because running the rule of a SelectRule
    requires elements with geometry."""

    def setUp(self):
        """Set up test fixtures."""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

    def _select_facet(self, entity_name):
        select = SelectFacet()
        select.applicability = [ids.Entity(name=entity_name)]
        return select

    def test_SelectRule_initialization(self):
        """Test SelectRule can be initialized."""
        volume_rule = Volume(
            source=SelectFacet(), volume_min=0.0, volume_max=100.0
        )

        select_rule = SelectRule()
        select_rule.rule = volume_rule

        self.assertIsInstance(select_rule, SelectRule)
        self.assertEqual(select_rule.type, "Rule")
        self.assertEqual(select_rule.rule, volume_rule)
        self.assertEqual(select_rule.dict_elements, {})

    def test_SelectRule_run(self):
        """Test SelectRule runs its rule and fills dict_elements with
        the rule results. The Volume rule passes the 14 doors of the
        Duplex model."""
        volume_rule = Volume(
            source=self._select_facet("IFCDOOR"),
            volume_min=0.0,
            volume_max=1e12,
        )
        select_rule = SelectRule()
        select_rule.rule = volume_rule

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [select_rule]
        rule_file.run()

        # One file in the dict, with the 14 doors that passed the rule
        self.assertEqual(len(select_rule.dict_elements), 1)
        self.assertEqual(self._count(select_rule), 14)
        for elements in select_rule.dict_elements.values():
            for element in elements:
                self.assertEqual(element.is_a(), "IfcDoor")

    def test_SelectRule_run_in_a_rule(self):
        """Test SelectRule used as the source of another rule: the outer
        rule receives the elements produced by the inner rule."""
        volume_rule = Volume(
            source=self._select_facet("IFCDOOR"),
            volume_min=0.0,
            volume_max=1e12,
        )
        select_rule = SelectRule()
        select_rule.rule = volume_rule

        collision_rule = Collision(
            source=select_rule,
            target=self._select_facet("IFCSLAB"),
            allow_touching=False,
        )

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [collision_rule]
        rule_file.run()

        # Same quantity as a Collision directly on doors and slabs
        self.assertEqual(len(collision_rule.result), 24)

    def test_SelectRule_update_file_info(self):
        """Test SelectRule update_file_info reaches its own attributes
        and the select of its rule."""
        volume_rule = Volume(
            source=SelectFacet(), volume_min=0.0, volume_max=100.0
        )
        select_rule = SelectRule()
        select_rule.rule = volume_rule

        files_path = [self.ifc_path]
        files = []

        select_rule.update_file_info(files_path, files)

        self.assertEqual(select_rule.list_ifc_path, files_path)
        self.assertEqual(select_rule.list_ifc_file, files)
        self.assertEqual(select_rule.rule.select_source.list_ifc_path, files_path)
        self.assertEqual(select_rule.rule.select_source.list_ifc_file, files)

    def _count(self, select_rule):
        return sum(
            len(elements) for elements in select_rule.dict_elements.values()
        )


class TestSelectFacetAndSelectRuleIntegration(unittest.TestCase):
    """Test integration of SelectFacet and SelectRule with RuleFile."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_ifc_path = self._create_temp_ifc()

    def tearDown(self):
        """Clean up test fixtures."""
        if hasattr(self, '_temp_ifc_file') and self._temp_ifc_file:
            os.remove(self._temp_ifc_file)

    def _create_temp_ifc(self):
        """Create a temporary IFC file for testing."""
        temp_file = tempfile.NamedTemporaryFile(suffix='.ifc', delete=False)
        temp_file.close()
        self._temp_ifc_file = temp_file.name

        file = ifcopenshell.file(schema="IFC4")
        run("root.create_entity", file, ifc_class="IfcProject", name="Test Project")
        run("root.create_entity", file, ifc_class="IfcBuilding", name="Test Building")
        run("root.create_entity", file, ifc_class="IfcWall", name="Wall 1")
        run("root.create_entity", file, ifc_class="IfcWall", name="Wall 2")

        file.write(temp_file.name)
        return temp_file.name

    def test_RuleFile_with_SelectFacet(self):
        """Test RuleFile gives its files to a contained SelectFacet."""
        select_facet = SelectFacet()
        select_facet.applicability = [Entity(name="IFCWALL")]

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.test_ifc_path]
        rule_file.contains = [select_facet]

        rule_file.load_file()
        rule_file.update_file_info()

        self.assertEqual(len(rule_file.contains), 1)
        self.assertEqual(len(rule_file.list_ifc_file), 1)
        self.assertEqual(len(select_facet.list_ifc_file), 1)

    def test_RuleFile_with_SelectRule(self):
        """Test RuleFile gives its files to the rule of a contained
        SelectRule."""
        area_rule = Area(source=SelectFacet(), volume_min=0.0, volume_max=100.0)
        select_rule = SelectRule()
        select_rule.rule = area_rule

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.test_ifc_path]
        rule_file.contains = [select_rule]

        rule_file.load_file()
        rule_file.update_file_info()

        self.assertEqual(len(rule_file.contains), 1)
        self.assertEqual(len(select_rule.list_ifc_file), 1)
        self.assertEqual(len(select_rule.rule.select_source.list_ifc_file), 1)

    def test_SelectFacet_chaining(self):
        """Test several SelectFacet filters: one per entity type and one
        per attribute, on the same temporary file."""
        select_facet1 = SelectFacet()
        select_facet1.applicability = [Entity(name="IFCWALL")]

        select_facet2 = SelectFacet()
        select_facet2.applicability = [Attribute(name="Name", value="Wall 1")]

        for select_facet in (select_facet1, select_facet2):
            select_facet.list_ifc_path = [self.test_ifc_path]
            select_facet.list_ifc_file = [ifcopenshell.open(self.test_ifc_path)]
            select_facet.run()

        count1 = sum(
            len(elements) for elements in select_facet1.dict_elements.values()
        )
        count2 = sum(
            len(elements) for elements in select_facet2.dict_elements.values()
        )
        self.assertEqual(count1, 2)
        self.assertEqual(count2, 1)


if __name__ == "__main__":
    unittest.main()
