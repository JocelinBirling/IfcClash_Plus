"""
Test suite for the produce_select method of the rules.

produce_select returns a dict {ifc_file: [elements]}:
- passed=True: the elements of the results with status True;
- passed=False: the elements of the input selection that went through
  the rule but produced no result.

A RuleCheckTwoObjects rule (Clearance) is tested for the source and the
target with True and False (4 tests). A RuleCheckOneObject rule (Volume)
is tested for the source only (2 tests): a one object rule has no
target.

For every case, the partition of the selection is checked: the unique
elements in the results plus the absent elements equal the total size
of the input selection.

Reference quantities on Ifc_Model/Ifc2x3_Duplex_Architecture.ifc:
- Clearance(walls, furnishings, 0.5): 152 results, 56 walls selected,
  61 furnishing elements selected, 42 walls and 47 furnishings in the
  results;
- Volume(walls, 0.0, 1.0): 26 results, 56 walls selected.
"""

import unittest
import sys
sys.path.insert(0, './ifcclash_plus')

from Rules import Clearance, Volume
from RuleClass import SelectFacet, RuleFile
from ifctester import ids


class TestProduceSelectTwoObjects(unittest.TestCase):
    """Test produce_select on a two objects rule: source and target,
    with True and False."""

    def setUp(self):
        """Set up test fixtures."""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

        wall_select = SelectFacet()
        wall_select.applicability = [ids.Entity(name="IFCWALLSTANDARDCASE")]
        furnishing_select = SelectFacet()
        furnishing_select.applicability = [ids.Entity(name="IFCFURNISHINGELEMENT")]

        self.rule = Clearance(
            source=wall_select,
            target=furnishing_select,
            clearance=0.5
        )

    def _run(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [self.rule]
        rule_file.run()

    def _produce_select(self, element="source", passed=True):
        """produce_select takes no parameter: the configuration is set
        on the rule (as a SelectRule does), then the method is called."""
        self.rule.element_to_pass = element
        self.rule.element_state_to_pass = passed
        return self.rule.produce_select()

    def _count(self, select_dict):
        return sum(len(elements) for elements in select_dict.values())

    def _count_unique(self, select_dict):
        all_elements = []
        for elements in select_dict.values():
            all_elements = all_elements + elements
        return len(set(all_elements))

    def _selection_size(self, select):
        return sum(len(elements) for elements in select.dict_elements.values())

    def test_source_passed_True(self):
        """Sources of the results with status True: the 42 walls found
        in the 152 clearance results, each returned only once."""
        self._run()
        source_in_results = self._produce_select("source", True)

        self.assertEqual(self._count(source_in_results), 42)
        for elements in source_in_results.values():
            for element in elements:
                self.assertEqual(element.is_a(), "IfcWallStandardCase")

    def test_source_passed_False(self):
        """Sources of the selection absent from the results: the 56
        walls minus the 42 walls found in the results."""
        self._run()
        source_in_results = self._produce_select("source", True)
        source_absent = self._produce_select("source", False)

        self.assertEqual(self._count(source_absent), 14)
        for elements in source_absent.values():
            for element in elements:
                self.assertEqual(element.is_a(), "IfcWallStandardCase")

        # Every source of the selection is in the results or absent
        self.assertEqual(
            self._count_unique(source_in_results)
            + self._count(source_absent),
            self._selection_size(self.rule.select_source),
        )

    def test_target_passed_True(self):
        """Targets of the results with status True: the 47 furnishing
        elements found in the 152 clearance results, each returned only
        once."""
        self._run()
        target_in_results = self._produce_select("target", True)

        self.assertEqual(self._count(target_in_results), 47)
        for elements in target_in_results.values():
            for element in elements:
                self.assertEqual(element.is_a(), "IfcFurnishingElement")

    def test_target_passed_False(self):
        """Targets of the selection absent from the results: the 61
        furnishing elements minus the 47 found in the results."""
        self._run()
        target_in_results = self._produce_select("target", True)
        target_absent = self._produce_select("target", False)

        self.assertEqual(self._count(target_absent), 14)
        for elements in target_absent.values():
            for element in elements:
                self.assertEqual(element.is_a(), "IfcFurnishingElement")

        # Every target of the selection is in the results or absent
        self.assertEqual(
            self._count_unique(target_in_results)
            + self._count(target_absent),
            self._selection_size(self.rule.select_target),
        )


class TestProduceSelectOneObject(unittest.TestCase):
    """Test produce_select on a one object rule: source only."""

    def setUp(self):
        """Set up test fixtures."""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

        wall_select = SelectFacet()
        wall_select.applicability = [ids.Entity(name="IFCWALLSTANDARDCASE")]

        self.rule = Volume(
            source=wall_select,
            volume_min=0.0,
            volume_max=1.0
        )

    def _run(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [self.rule]
        rule_file.run()

    def _produce_select(self, passed=True):
        """produce_select takes no parameter: the configuration is set
        on the rule (as a SelectRule does), then the method is called.
        A one object rule only has source elements."""
        self.rule.element_state_to_pass = passed
        return self.rule.produce_select()

    def _count(self, select_dict):
        return sum(len(elements) for elements in select_dict.values())

    def _count_unique(self, select_dict):
        all_elements = []
        for elements in select_dict.values():
            all_elements = all_elements + elements
        return len(set(all_elements))

    def _selection_size(self, select):
        return sum(len(elements) for elements in select.dict_elements.values())

    def test_source_passed_True(self):
        """Sources of the results with status True: the 26 walls with a
        volume below 1.0."""
        self._run()
        source_in_results = self._produce_select(True)

        self.assertEqual(self._count(source_in_results), 26)
        for elements in source_in_results.values():
            for element in elements:
                self.assertEqual(element.is_a(), "IfcWallStandardCase")

    def test_source_passed_False(self):
        """Sources of the selection absent from the results: the 56
        walls minus the 26 walls in the results."""
        self._run()
        source_in_results = self._produce_select(True)
        source_absent = self._produce_select(False)

        self.assertEqual(self._count(source_absent), 30)
        for elements in source_absent.values():
            for element in elements:
                self.assertEqual(element.is_a(), "IfcWallStandardCase")

        # Every source of the selection is in the results or absent
        self.assertEqual(
            self._count_unique(source_in_results)
            + self._count(source_absent),
            self._selection_size(self.rule.select_source),
        )


if __name__ == "__main__":
    unittest.main()
