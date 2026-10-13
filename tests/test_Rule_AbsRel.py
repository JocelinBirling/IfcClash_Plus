"""
Test suite for the Must rules (AbsoluteOrRelativeChecking) on the
Duplex architecture model: the windows of the spaces.

The pairing rule is a Clearance with a tolerance of 0.10 (a window
sits in the thickness of its wall, flush with the volume of the space
it lights, less than a centimeter away) between the windows (source)
and the spaces (target). The pairing is then exact: a window never
belongs to a neighbor space, nor to a space on another floor.

The Must check groups by target (the rule grouping, select_grouping
"TARGET", produces one group per space): the operation names the
measured set, here the source set (the windows of the space):
- each space must have at least 2 windows (Absolute_Number,
  "SOURCE>=2");
- in each space, the summed PSet_Revit_Type_Dimensions.Height of its
  windows must be above 3 m (Absolute_Quantity, "SOURCE>3").

A third test uses the entity grouping of the rule (select_grouping
"ENTITY"): the classic grouping produces the groups instead, and each
group measures its own non empty set.

The expected verdicts are the ones of the model: 8 spaces hold at
least one flush window; the two single window spaces (A103, B103)
fail both checks (a single window is at most 2.42 m high), the six
others pass them. The 13 spaces without any flush window produce no
result, so no group: a Must rule only checks the objects appearing
in the results of its rule.

The pairing rule runs once per class (setUpClass); every test applies
its own check through run_abs_or_rel, which regroups the results, so
the tests do not depend on each other.

Execution (from the repository root):
    python -m pytest tests/test_Rule_AbsRel.py -v
"""
import sys
import unittest

sys.path.insert(0, "./ifcclash_plus")

from ifcopenshell.util.element import get_pset

from Rules import Clearance
from RuleClass import AbsoluteOrRelativeChecking, RuleFile, SelectFacet
from ifctester import ids


class TestMustRuleOnArchitectureModel(unittest.TestCase):
    """The windows of the spaces of the Duplex architecture model."""

    MODEL = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

    # The pairing tolerance: a window is flush with the volume of the
    # space it lights (the measured distances are below a
    # centimeter, so any tolerance from 0.10 cm to 10 cm gives the
    # same pairing).
    CLEARANCE = 0.1

    # The spaces holding a single flush window: they fail both
    # checks.
    SINGLE_WINDOW_SPACES = {"A103", "B103"}

    # Some spaces without any flush window (A101 and R301 only have
    # windows at a larger distance, which belong to other spaces):
    # they produce no result, so no group.
    SPACES_WITHOUT_FLUSH_WINDOW = {"A101", "A104", "B104", "R301"}

    @classmethod
    def setUpClass(cls):
        # The pairing rule: one result per (window, space) pair, the
        # window flush with the space volume. The Must check groups
        # by target (the spaces): one group per space, its windows in
        # the source set. It runs in the Final state: a Display_Result
        # state would open a viewer window and block the suite.
        source = SelectFacet()
        source.applicability = [ids.Entity(name="IFCWINDOW")]
        target = SelectFacet()
        target.applicability = [ids.Entity(name="IFCSPACE")]

        cls.rule = Clearance(source, target, clearance=cls.CLEARANCE)
        # The Must check groups by target: one group per space, its
        # windows in the source set.
        cls.rule.select_grouping = "TARGET"

        rule_file = RuleFile()
        rule_file.list_ifc_path = [cls.MODEL]
        rule_file.contains = [cls.rule]
        rule_file.run()

    @staticmethod
    def group_name(group):
        """The name of the (single) space of one group: the groups
        are keyed by target (one group per space)."""
        return next(iter(group.target_set)).Name

    def window_height(self, window):
        """The Height of a window, in meters (the model stores real
        numbers in PSet_Revit_Type_Dimensions)."""
        return get_pset(
            window, name="PSet_Revit_Type_Dimensions", prop="Height"
        )

    def apply_check(self, check):
        """Group the results by target (one group per space) and check
        every group."""
        self.rule.abs_or_rel_check = check
        self.assertTrue(self.rule.run_abs_or_rel())
        return self.rule.grouped_result

    def verdicts(self, groups):
        """The failing and passing space names of the checked groups."""
        failing = {
            self.group_name(group)
            for group in groups
            if not group.abs_or_rel_check
        }
        passing = {
            self.group_name(group)
            for group in groups
            if group.abs_or_rel_check
        }
        return failing, passing

    def test_the_pairing_rule_produces_one_group_per_space(self):
        # 8 spaces have at least one flush window, each group holds
        # exactly one space.
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        groups = self.apply_check(check)
        self.assertEqual(len(groups), 8)
        for group in groups:
            self.assertEqual(len(group.target_set), 1)

        # The spaces without a flush window produce no result, so no
        # group: a Must rule only checks the objects appearing in
        # the results of its rule.
        names = {self.group_name(group) for group in groups}
        for name in self.SPACES_WITHOUT_FLUSH_WINDOW:
            self.assertNotIn(name, names)

    def test_each_space_has_at_least_two_windows(self):
        # "Each space must have at least 2 windows": one group per
        # space, its windows (the source set) counted.
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "SOURCE>=2"

        groups = self.apply_check(check)
        failing, passing = self.verdicts(groups)

        # The two single window spaces fail, the six others pass.
        self.assertEqual(failing, self.SINGLE_WINDOW_SPACES)
        self.assertEqual(len(passing), 6)
        self.assertEqual(len(failing | passing), 8)

        # A failing group really holds a single window, a passing one
        # at least two.
        for group in groups:
            if self.group_name(group) in self.SINGLE_WINDOW_SPACES:
                self.assertEqual(len(group.source_set), 1)
            else:
                self.assertGreaterEqual(len(group.source_set), 2)

    def test_the_summed_window_height_of_each_space_is_above_three(self):
        # "In each space, the summed Height of the windows must be
        # above 3 m": one group per space, the property summed over
        # its windows (the source set).
        check = AbsoluteOrRelativeChecking("Absolute_Quantity")
        check.quantity_pset = "PSet_Revit_Type_Dimensions"
        check.quantity_prop = "Height"
        check.operation = "SOURCE>3"

        groups = self.apply_check(check)
        failing, passing = self.verdicts(groups)

        # A single window is at most 2.42 m high: the same two single
        # window spaces fail, the six others pass.
        self.assertEqual(failing, self.SINGLE_WINDOW_SPACES)
        self.assertEqual(len(passing), 6)

        # The verdicts match the heights of the model: an independent
        # sum over the windows of every group.
        for group in groups:
            height_sum = sum(
                self.window_height(window) for window in group.source_set
            )
            self.assertEqual(group.abs_or_rel_check, height_sum > 3)

    def test_a_single_window_space_measures_the_height_of_its_window(self):
        # A103 holds one single window of 2.2 m: the measured quantity
        # is its height, and the comparison against 3 fails.
        check = AbsoluteOrRelativeChecking("Absolute_Quantity")
        check.quantity_pset = "PSet_Revit_Type_Dimensions"
        check.quantity_prop = "Height"
        check.operation = "SOURCE>3"

        groups = self.apply_check(check)
        group = next(
            one
            for one in groups
            if self.group_name(one) == "A103"
        )
        self.assertEqual(len(group.source_set), 1)

        window = next(iter(group.source_set))
        self.assertAlmostEqual(self.window_height(window), 2.2)
        self.assertFalse(group.abs_or_rel_check)

    def test_each_space_has_at_least_two_windows_print_result(self):
        # The same check as test_each_space_has_at_least_two_windows,
        # printing the verdict of every group: a view of what the Must
        # rule produces on the model.
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "SOURCE>=2"

        groups = self.apply_check(check)
        for group in sorted(groups, key=self.group_name):
            verdict = "OK" if group.abs_or_rel_check else "FAIL"
            print(
                f"{verdict} {self.group_name(group)}: "
                f"{len(group.source_set)} window(s)"
            )

        failing, passing = self.verdicts(groups)
        self.assertEqual(failing, self.SINGLE_WINDOW_SPACES)
        self.assertEqual(len(passing), 6)

    def test_by_grouping_checks_the_entity_classes_of_the_pairing(self):
        # The entity grouping of the rule (select_grouping "ENTITY"):
        # one group per entity class of the results — the windows on
        # the source side, the spaces on the target side — and each
        # group measures its own non empty set: the operation adds
        # both sides.
        source = SelectFacet()
        source.applicability = [ids.Entity(name="IFCWINDOW")]
        target = SelectFacet()
        target.applicability = [ids.Entity(name="IFCSPACE")]

        rule = Clearance(source, target, clearance=self.CLEARANCE)
        rule.select_grouping = "ENTITY"
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "SOURCE+TARGET>=2"
        rule.abs_or_rel_check = check

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.MODEL]
        rule_file.contains = [rule]
        rule_file.run()

        groups = rule.grouped_result
        self.assertEqual(len(groups), 2)

        by_side = {}
        for group in groups:
            if group.source_set:
                by_side["window"] = group
            else:
                by_side["space"] = group

        # The window group holds the 22 distinct windows of the
        # pairing, the space group the 8 spaces: both pass >= 2.
        self.assertEqual(len(by_side["window"].source_set), 22)
        self.assertTrue(by_side["window"].abs_or_rel_check)
        self.assertEqual(len(by_side["space"].target_set), 8)
        self.assertTrue(by_side["space"].abs_or_rel_check)

    def test_group_result_content_after_a_full_must_rule_run(self):
        # The real Must path: the check is set BEFORE the run, the
        # grouping and the check happen in manage_result at the end of
        # the rule run. Every group carries its space (the group key,
        # target), its windows (the source set), the pairing results
        # of the group and its verdict.
        source = SelectFacet()
        source.applicability = [ids.Entity(name="IFCWINDOW")]
        target = SelectFacet()
        target.applicability = [ids.Entity(name="IFCSPACE")]

        rule = Clearance(source, target, clearance=self.CLEARANCE)
        # The Must path: group by target (one group per space), its
        # windows measured through the SOURCE keyword.
        rule.select_grouping = "TARGET"
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "SOURCE>=2"
        rule.abs_or_rel_check = check

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.MODEL]
        rule_file.contains = [rule]
        rule_file.run()

        groups = rule.grouped_result
        self.assertEqual(len(groups), 8)

        by_name = {}
        for group in groups:
            # One space per group (the group key), one pairing
            # result per window of the group.
            self.assertEqual(len(group.target_set), 1)
            space = next(iter(group.target_set))
            by_name[space.Name] = group
            self.assertEqual(len(group.source_set), len(group.result_group))
            for one_result in group.result_group:
                self.assertIn(one_result.source, group.source_set)
                self.assertEqual(one_result.target, space)

        # The verdicts of the model, straight from the rule run.
        self.assertEqual(
            {
                name
                for name, group in by_name.items()
                if not group.abs_or_rel_check
            },
            self.SINGLE_WINDOW_SPACES,
        )

        # The A102 group really holds its two windows and its two
        # pairing results.
        a102 = by_name["A102"]
        self.assertEqual(len(a102.source_set), 2)
        self.assertEqual(len(a102.result_group), 2)
        self.assertTrue(a102.abs_or_rel_check)


if __name__ == "__main__":
    unittest.main()
