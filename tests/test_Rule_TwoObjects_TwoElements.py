"""
Test suite for every RuleCheckTwoObjects rule with only two objects:
exactly one source element and one target element.

Each rule is run twice:
- with a pair of elements known to match the rule (extracted from the
  full-selection runs of test_Rule_TwoObjects.py), expecting exactly
  one result on the right pair of elements;
- with a pair of elements without any relationship, expecting no result.

The selections contain exactly one element each, selected by GlobalId.
"""

import unittest
import sys
sys.path.insert(0, './ifcclash_plus')

from Rules import (
    Intersection, Clearance, Collision, AngleBetween, Ray_Check,
    Above, Below, OBB_Above, OBB_Below, OBB_Front_And_Back, OBB_Custom,
)
from RuleClass import SelectFacet, RuleFile, ClashResultTwoObjects
from ifctester import ids


# Pairs of elements known to match each rule (GlobalId of the model
# Ifc_Model/Ifc2x3_Duplex_Architecture.ifc)
COLLISION_SOURCE = "2OBrcmyk58NupXoVOHUvPL"        # IfcDoor
COLLISION_TARGET = "2OBrcmyk58NupXoVOHUt5W"        # IfcSlab

INTERSECTION_SOURCE = "2O2Fr$t4X7Zf8NOew3FLQD"     # IfcWallStandardCase
INTERSECTION_TARGET = "2OBrcmyk58NupXoVOHUtI8"     # IfcFurnishingElement

CLEARANCE_SOURCE = "1aj$VJZFn2TxepZUBcKpvt"        # IfcWallStandardCase
CLEARANCE_TARGET = "2gRXFgjRn2HPE$YoDLX0mp"        # IfcFurnishingElement

ANGLE_BETWEEN_SOURCE = "2O2Fr$t4X7Zf8NOew3FLQD"     # IfcWallStandardCase
ANGLE_BETWEEN_TARGET = "1hOSvn6df7F8_7GcBWlSDm"    # IfcDoor

RAY_CHECK_SOURCE = "1hOSvn6df7F8_7GcBWlRGQ"        # IfcDoor
RAY_CHECK_TARGET = "2OBrcmyk58NupXoVOHUvqu"        # IfcFurnishingElement

ABOVE_SOURCE = "0iEHWY1$XA8eQeeULq4j7w"            # IfcFurnishingElement
ABOVE_TARGET = "1hOSvn6df7F8_7GcBWlRrM"            # IfcSlab

BELOW_SOURCE = "1hOSvn6df7F8_7GcBWlRqU"            # IfcSlab
BELOW_TARGET = "0iEHWY1$XA8eQeeULq4jOM"            # IfcFurnishingElement

OBB_ABOVE_SOURCE = "0iEHWY1$XA8eQeeULq4jQJ"        # IfcFurnishingElement
OBB_ABOVE_TARGET = "1hOSvn6df7F8_7GcBWlRqU"        # IfcSlab

OBB_BELOW_SOURCE = "1hOSvn6df7F8_7GcBWlSXO"        # IfcWindow
OBB_BELOW_TARGET = "1hOSvn6df7F8_7GcBWlRqU"        # IfcSlab

FRONT_AND_BACK_SOURCE = "1hOSvn6df7F8_7GcBWlS8Z"  # IfcDoor
FRONT_AND_BACK_TARGET = "2gRXFgjRn2HPE$YoDLX0vP"  # IfcFurnishingElement

OBB_CUSTOM_SOURCE = "2O2Fr$t4X7Zf8NOew3FK80"       # IfcWallStandardCase
OBB_CUSTOM_TARGET = "1hOSvn6df7F8_7GcBWlR72"       # IfcWindow

# Two elements without any relationship, used as the no-match case
UNRELATED_SOURCE = "2OBrcmyk58NupXoVOHUvPL"        # IfcDoor on one side of the house
UNRELATED_TARGET = "0iEHWY1$XA8eQeeULq4jOM"        # IfcFurnishingElement on the other side

OBB_CUSTOM_MODIFICATIONS = [
    "detach_top_by_extrude:10%", "NEW_OBB", "detach_bottom_by_extrude:10%"
]


class TestRulesTwoObjectsTwoElements(unittest.TestCase):
    """
    Every RuleCheckTwoObjects rule must work with only two objects:
    one source element and one target element.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

    def _one_element_select(self, global_id):
        """A selection containing exactly one element, by GlobalId."""
        select = SelectFacet()
        select.applicability = [ids.Attribute(name="GlobalId", value=global_id)]
        return select

    def _context_select(self):
        context_facet = ids.Entity(
            name=ids.Restriction(
                options={"enumeration": ["IFCWALLSTANDARDCASE", "IFCSLAB"]}
            )
        )
        context_select = SelectFacet()
        context_select.applicability = [context_facet]
        return context_select

    def _run(self, rule):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [rule]
        rule_file.run()

        # The source and the target selections contain exactly one element
        for select in (rule.select_source, rule.select_target):
            number_of_elements = sum(
                len(elements) for elements in select.dict_elements.values()
            )
            self.assertEqual(number_of_elements, 1)

    def _assert_single_match(self, rule, source_global_id, target_global_id):
        """The rule found exactly one result, on the right pair."""
        self.assertEqual(len(rule.result), 1)
        result = rule.result[0]
        self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertTrue(result.status)
        self.assertEqual(result.source.GlobalId, source_global_id)
        self.assertEqual(result.target.GlobalId, target_global_id)

    def _assert_no_match(self, rule):
        self.assertEqual(len(rule.result), 0)

    def test_Intersection(self):
        """Intersection with one wall and one furnishing element."""
        rule = Intersection(
            self._one_element_select(INTERSECTION_SOURCE),
            self._one_element_select(INTERSECTION_TARGET),
            tolerance=0.01,
        )
        self._run(rule)
        self._assert_single_match(rule, INTERSECTION_SOURCE, INTERSECTION_TARGET)

        rule = Intersection(
            self._one_element_select(UNRELATED_SOURCE),
            self._one_element_select(UNRELATED_TARGET),
            tolerance=0.01,
        )
        self._run(rule)
        self._assert_no_match(rule)

    def test_Clearance(self):
        """Clearance between one wall and one furnishing element."""
        rule = Clearance(
            self._one_element_select(CLEARANCE_SOURCE),
            self._one_element_select(CLEARANCE_TARGET),
            clearance=0.5,
        )
        self._run(rule)
        self._assert_single_match(rule, CLEARANCE_SOURCE, CLEARANCE_TARGET)

        rule = Clearance(
            self._one_element_select(UNRELATED_SOURCE),
            self._one_element_select(UNRELATED_TARGET),
            clearance=0.5,
        )
        self._run(rule)
        self._assert_no_match(rule)

    def test_Collision(self):
        """Collision between one door and one slab."""
        rule = Collision(
            self._one_element_select(COLLISION_SOURCE),
            self._one_element_select(COLLISION_TARGET),
            allow_touching=False,
        )
        self._run(rule)
        self._assert_single_match(rule, COLLISION_SOURCE, COLLISION_TARGET)

        rule = Collision(
            self._one_element_select(UNRELATED_SOURCE),
            self._one_element_select(UNRELATED_TARGET),
            allow_touching=False,
        )
        self._run(rule)
        self._assert_no_match(rule)

    def test_AngleBetween(self):
        """AngleBetween between one wall and one door."""
        rule = AngleBetween(
            self._one_element_select(ANGLE_BETWEEN_SOURCE),
            self._one_element_select(ANGLE_BETWEEN_TARGET),
            direction_method_for_source="Wide",
            direction_method_for_target="Wide",
            angle_difference=0.0,
            angle_tolerance=1.0,
        )
        self._run(rule)
        self._assert_single_match(rule, ANGLE_BETWEEN_SOURCE, ANGLE_BETWEEN_TARGET)

        rule = AngleBetween(
            self._one_element_select(UNRELATED_SOURCE),
            self._one_element_select(UNRELATED_TARGET),
            direction_method_for_source="Wide",
            direction_method_for_target="Wide",
            angle_difference=0.0,
            angle_tolerance=1.0,
        )
        self._run(rule)
        self._assert_no_match(rule)

    def test_Ray_Check(self):
        """Ray_Check from one door toward one furnishing element.
        The context stays a facet selection, only the source and the
        target are single objects."""
        rule = Ray_Check(
            self._one_element_select(RAY_CHECK_SOURCE),
            self._one_element_select(RAY_CHECK_TARGET),
            self._context_select(),
            max_ray_length=5,
        )
        self._run(rule)
        self._assert_single_match(rule, RAY_CHECK_SOURCE, RAY_CHECK_TARGET)

        rule = Ray_Check(
            self._one_element_select(UNRELATED_SOURCE),
            self._one_element_select(UNRELATED_TARGET),
            self._context_select(),
            max_ray_length=5
        )
        self._run(rule)
        self._assert_no_match(rule)

    def test_Above(self):
        """Above with one furnishing element and one slab."""
        rule = Above(
            self._one_element_select(ABOVE_SOURCE),
            self._one_element_select(ABOVE_TARGET),
            above_type="Above_MaxToMin",
            tolerance=0.85,
        )
        self._run(rule)
        self._assert_single_match(rule, ABOVE_SOURCE, ABOVE_TARGET)

        rule = Above(
            self._one_element_select(UNRELATED_SOURCE),
            self._one_element_select(UNRELATED_TARGET),
            above_type="Above_MaxToMin",
            tolerance=0.85,
        )
        self._run(rule)
        self._assert_no_match(rule)

    def test_Below(self):
        """Below with one slab and one furnishing element."""
        rule = Below(
            self._one_element_select(BELOW_SOURCE),
            self._one_element_select(BELOW_TARGET),
            below_type="Below_MinToMax",
            tolerance=0.81,
        )
        self._run(rule)
        self._assert_single_match(rule, BELOW_SOURCE, BELOW_TARGET)

        rule = Below(
            self._one_element_select(UNRELATED_SOURCE),
            self._one_element_select(UNRELATED_TARGET),
            below_type="Below_MinToMax",
            tolerance=0.81,
        )
        self._run(rule)
        self._assert_no_match(rule)

    def test_OBB_Above(self):
        """OBB_Above with one furnishing element and one slab."""
        rule = OBB_Above(
            self._one_element_select(OBB_ABOVE_SOURCE),
            self._one_element_select(OBB_ABOVE_TARGET),
            tolerance=0.81,
        )
        self._run(rule)
        self._assert_single_match(rule, OBB_ABOVE_SOURCE, OBB_ABOVE_TARGET)

        rule = OBB_Above(
            self._one_element_select(UNRELATED_SOURCE),
            self._one_element_select(UNRELATED_TARGET),
            tolerance=0.81,
        )
        self._run(rule)
        self._assert_no_match(rule)

    def test_OBB_Below(self):
        """OBB_Below with one window and one slab."""
        rule = OBB_Below(
            self._one_element_select(OBB_BELOW_SOURCE),
            self._one_element_select(OBB_BELOW_TARGET),
            tolerance=0.1,
        )
        self._run(rule)
        self._assert_single_match(rule, OBB_BELOW_SOURCE, OBB_BELOW_TARGET)

        rule = OBB_Below(
            self._one_element_select(UNRELATED_SOURCE),
            self._one_element_select(UNRELATED_TARGET),
            tolerance=0.1,
        )
        self._run(rule)
        self._assert_no_match(rule)

    def test_OBB_Front_And_Back(self):
        """OBB_Front_And_Back with one door and one furnishing element."""
        rule = OBB_Front_And_Back(
            self._one_element_select(FRONT_AND_BACK_SOURCE),
            self._one_element_select(FRONT_AND_BACK_TARGET),
            tolerance=1.0,
            method="Wide",
        )
        self._run(rule)
        self._assert_single_match(rule, FRONT_AND_BACK_SOURCE, FRONT_AND_BACK_TARGET)

        rule = OBB_Front_And_Back(
            self._one_element_select(UNRELATED_SOURCE),
            self._one_element_select(UNRELATED_TARGET),
            tolerance=1.0,
            method="Wide",
        )
        self._run(rule)
        self._assert_no_match(rule)

    def test_OBB_Custom(self):
        """OBB_Custom with one wall and one window."""
        rule = OBB_Custom(
            self._one_element_select(OBB_CUSTOM_SOURCE),
            self._one_element_select(OBB_CUSTOM_TARGET),
            OBB_CUSTOM_MODIFICATIONS,
        )
        self._run(rule)
        self._assert_single_match(rule, OBB_CUSTOM_SOURCE, OBB_CUSTOM_TARGET)

        rule = OBB_Custom(
            self._one_element_select(UNRELATED_SOURCE),
            self._one_element_select(UNRELATED_TARGET),
            OBB_CUSTOM_MODIFICATIONS,
        )
        self._run(rule)
        self._assert_no_match(rule)


if __name__ == "__main__":
    unittest.main()
