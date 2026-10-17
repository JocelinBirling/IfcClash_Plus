"""
Test suite for the boolean rules of booleanrule.py.

Two levels:
- unit tests with fake rules (any object with a result list, the module
  is duck typed), covering every mode of BooleanLeaf, the composites
  AndRule / OrRule / NotRule and the rules() iterator;
- integration tests with real rules run on the IFC model, where a
  boolean tree is evaluated after a RuleFile.run().
"""

import unittest
import sys
sys.path.insert(0, './ifcclash_plus')

from Rules import Collision, Volume
from RuleClass import SelectFacet, RuleFile
from booleanrule import (
    BooleanRule, BooleanLeaf, AndRule, OrRule, NotRule,
)
from ifctester import ids


class FakeResult:
    """Duck typed ClashResult: only the status is read."""

    def __init__(self, status):
        self.status = status


class FakeRule:
    """Duck typed RuleCheck: only the result list is read."""

    def __init__(self, number_of_results):
        self.result = [FakeResult(True) for _ in range(number_of_results)]


class TestBooleanLeaf(unittest.TestCase):
    """Test every mode of BooleanLeaf."""

    def test_have_result(self):
        self.assertTrue(BooleanLeaf(FakeRule(2), "have_result").evaluate())
        self.assertFalse(BooleanLeaf(FakeRule(0), "have_result").evaluate())

    def test_have_no_result(self):
        self.assertTrue(BooleanLeaf(FakeRule(0), "have_no_result").evaluate())
        self.assertFalse(BooleanLeaf(FakeRule(2), "have_no_result").evaluate())

    def test_have_more(self):
        rule = FakeRule(3)
        self.assertTrue(BooleanLeaf(rule, "have_more", 2).evaluate())
        self.assertFalse(BooleanLeaf(rule, "have_more", 3).evaluate())

    def test_have_more_or_equals(self):
        rule = FakeRule(3)
        self.assertTrue(BooleanLeaf(rule, "have_more_or_equals", 3).evaluate())
        self.assertFalse(BooleanLeaf(rule, "have_more_or_equals", 4).evaluate())

    def test_have_less(self):
        rule = FakeRule(3)
        self.assertTrue(BooleanLeaf(rule, "have_less", 4).evaluate())
        self.assertFalse(BooleanLeaf(rule, "have_less", 3).evaluate())

    def test_have_less_or_equals(self):
        rule = FakeRule(3)
        self.assertTrue(BooleanLeaf(rule, "have_less_or_equals", 3).evaluate())
        self.assertFalse(BooleanLeaf(rule, "have_less_or_equals", 2).evaluate())

    def test_equals(self):
        rule = FakeRule(3)
        self.assertTrue(BooleanLeaf(rule, "equals", 3).evaluate())
        self.assertFalse(BooleanLeaf(rule, "equals", 5).evaluate())

    def test_value_as_string_is_tolerated(self):
        self.assertTrue(BooleanLeaf(FakeRule(3), "equals", "3").evaluate())
        self.assertFalse(BooleanLeaf(FakeRule(3), "equals", "5").evaluate())

    def test_default_mode_is_have_result(self):
        leaf = BooleanLeaf(FakeRule(1))
        self.assertEqual(leaf.mode, "have_result")
        self.assertTrue(leaf.evaluate())

    def test_unknown_mode_raises(self):
        with self.assertRaises(ValueError):
            BooleanLeaf(FakeRule(1), "is_valid")

    def test_quantity_mode_without_value_raises(self):
        for mode in BooleanLeaf.QUANTITY_MODES:
            with self.assertRaises(ValueError):
                BooleanLeaf(FakeRule(1), mode)

    def test_rules_yields_the_rule(self):
        rule = FakeRule(1)
        leaf = BooleanLeaf(rule)
        self.assertEqual(list(leaf.rules()), [rule])


class TestComposites(unittest.TestCase):
    """Test AndRule, OrRule, NotRule with raw rules and nesting."""

    def setUp(self):
        self.rule_with_results = FakeRule(2)
        self.rule_without_results = FakeRule(0)

    def test_AndRule_with_raw_rules(self):
        rule = AndRule(self.rule_with_results, self.rule_with_results)
        self.assertTrue(rule.evaluate())
        rule = AndRule(self.rule_with_results, self.rule_without_results)
        self.assertFalse(rule.evaluate())

    def test_AndRule_empty_is_True(self):
        self.assertTrue(AndRule().evaluate())

    def test_OrRule_with_raw_rules(self):
        rule = OrRule(self.rule_without_results, self.rule_with_results)
        self.assertTrue(rule.evaluate())
        rule = OrRule(self.rule_without_results, self.rule_without_results)
        self.assertFalse(rule.evaluate())

    def test_OrRule_empty_is_False(self):
        self.assertFalse(OrRule().evaluate())

    def test_NotRule_with_raw_rule(self):
        self.assertFalse(NotRule(self.rule_with_results).evaluate())
        self.assertTrue(NotRule(self.rule_without_results).evaluate())

    def test_nested_composites(self):
        # (R & R) | R_empty -> True
        rule = OrRule(
            AndRule(self.rule_with_results, self.rule_with_results),
            self.rule_without_results,
        )
        self.assertTrue(rule.evaluate())

        # not not R -> True
        self.assertTrue(NotRule(NotRule(self.rule_with_results)).evaluate())

        # not (R & R_empty) -> True
        self.assertTrue(
            NotRule(AndRule(self.rule_with_results, self.rule_without_results)).evaluate()
        )

    def test_mode_applies_to_raw_children(self):
        # have_no_result on both children
        rule = AndRule(
            self.rule_without_results, self.rule_without_results,
            mode="have_no_result",
        )
        self.assertTrue(rule.evaluate())

        rule = AndRule(
            self.rule_with_results, self.rule_without_results,
            mode="have_no_result",
        )
        self.assertFalse(rule.evaluate())

    def test_existing_boolean_rule_child_is_kept(self):
        leaf = BooleanLeaf(self.rule_with_results, "equals", 2)
        rule = AndRule(leaf, self.rule_with_results)
        self.assertIs(rule.children[0], leaf)

    def test_invalid_child_raises(self):
        for build in (
            lambda: AndRule(self.rule_with_results, 42),
            lambda: OrRule("not a rule"),
            lambda: NotRule(None),
        ):
            with self.assertRaises(TypeError):
                build()

    def test_rules_iterates_every_leaf(self):
        rule = OrRule(
            AndRule(self.rule_with_results, self.rule_without_results),
            self.rule_with_results,
        )
        leaves = list(rule.rules())
        self.assertEqual(len(leaves), 3)
        self.assertIn(self.rule_with_results, leaves)
        self.assertIn(self.rule_without_results, leaves)

    def test_base_class_rules_is_empty(self):
        self.assertEqual(list(BooleanRule().rules()), [])


class TestBooleanRuleIntegration(unittest.TestCase):
    """Evaluate boolean trees over real rules run on the IFC model."""

    def setUp(self):
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

    def _select_facet(self, entity_name):
        select = SelectFacet()
        select.applicability = [ids.Entity(name=entity_name)]
        return select

    def test_boolean_tree_over_real_rules(self):
        # R1: every door has a volume -> 14 results
        # R2: doors collide with slabs -> 24 results
        # R3: no wall has a volume between 0 and 0 -> 0 result
        r1 = Volume(
            self._select_facet("IFCDOOR"), volume_min=0.0, volume_max=1e12
        )
        r2 = Collision(
            self._select_facet("IFCDOOR"),
            self._select_facet("IFCSLAB"),
            allow_touching=False,
        )
        r3 = Volume(
            self._select_facet("IFCWALLSTANDARDCASE"),
            volume_min=0.0,
            volume_max=0.0,
        )

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [r1, r2, r3]
        rule_file.run()

        # (R1 & R2) | R3 -> True
        self.assertTrue(OrRule(AndRule(r1, r2), r3).evaluate())

        # R1 & R3 -> False (R3 has no result)
        self.assertFalse(AndRule(r1, r3).evaluate())

        # not R3 -> True
        self.assertTrue(NotRule(r3).evaluate())

        # Quantity modes on a real rule: R2 found 24 collisions
        self.assertTrue(BooleanLeaf(r2, "have_more", 20).evaluate())
        self.assertTrue(BooleanLeaf(r2, "equals", len(r2.result)).evaluate())
        self.assertFalse(BooleanLeaf(r2, "have_less", 20).evaluate())

        # The tree references the three rules
        tree = OrRule(AndRule(r1, r2), r3)
        self.assertEqual(len(list(tree.rules())), 3)


if __name__ == "__main__":
    unittest.main()
