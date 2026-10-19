"""
Test suite for the AbsoluteOrRelativeChecking class of RuleClass.py
(the Must rules of doc/Rule.md): the run loop, the number and quantity
measurements on GroupResult fixtures, the operation with the SOURCE
and TARGET keywords, and the run_abs_or_rel wiring of the two rule
base classes.

The check groups the results of its rule through run: the classic
grouping of the rule (run_grouping, driven by select_grouping) when it
has one, one group per source object by default otherwise.

The type selects the measurement: "_Number" counts the elements of
the sets, "_Quantity" sums a property over them. The measured sets
fill source_number and target_number, then the operation — written
with the SOURCE and TARGET keywords — is evaluated as the verdict of
the group: a relative operation relates the two sets
("SOURCE=2*TARGET"), an absolute one compares a single set against a
requirement ("TARGET>=2"). The quantity tests need real IFC entities
to read a property: the three elements of the in-memory fixture each
carry a Pset_Test/Value of 2.5 (no geometry).

Execution (from the repository root):
    python -m pytest tests/test_structure_AbsoluteOrRelativeChecking.py -v
"""
import sys
import unittest

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell
import ifcopenshell.api

from RuleClass import (
    AbsoluteOrRelativeChecking,
    ClashResultOneObject,
    ClashResultTwoObjects,
    GroupResult,
    SelectFacet,
)
from Rules import Intersection, Volume
from tests.test_structure_ResultShape import assert_result_shape



def make_group(nb_source=0, nb_target=0):
    """A GroupResult with nb_source source results and nb_target
    target results; plain strings stand for the IFC entities."""
    group = GroupResult()
    for index in range(nb_source):
        group.add_source(
            ClashResultOneObject(source=f"source_{index}", state=True)
        )
    for index in range(nb_target):
        group.add_target(
            ClashResultTwoObjects(
                source=f"source_{index}", target=f"target_{index}", state=True
            )
        )
    return group


_ELEMENTS = None
# The opened files stay alive: an ifcopenshell >= 0.9 entity no longer
# keeps its file alive, the cached elements would dangle without it.
_ELEMENTS_FILE = None


def ifc_elements():
    """Three IfcBuildingElementProxy of an in-memory file, each with a
    Pset_Test/Value property of 2.5. Built once, no geometry needed."""
    global _ELEMENTS, _ELEMENTS_FILE
    if _ELEMENTS is None:
        file = ifcopenshell.api.run("project.create_file")
        ifcopenshell.api.run(
            "root.create_entity", file, ifc_class="IfcProject", name="P"
        )
        elements = []
        for index in range(3):
            element = ifcopenshell.api.run(
                "root.create_entity",
                file,
                ifc_class="IfcBuildingElementProxy",
                name=f"E{index}",
            )
            pset = ifcopenshell.api.run(
                "pset.add_pset", file, product=element, name="Pset_Test"
            )
            ifcopenshell.api.run(
                "pset.edit_pset", file, pset=pset, properties={"Value": 2.5}
            )
            elements.append(element)
        _ELEMENTS_FILE = file
        _ELEMENTS = elements
    return _ELEMENTS


_TEXT_ELEMENTS = None
_TEXT_ELEMENTS_FILE = None


def ifc_text_elements():
    """Three IfcBuildingElementProxy whose property values are not
    plain numbers: a number written as a string, pure text, and an
    element without the property."""
    global _TEXT_ELEMENTS, _TEXT_ELEMENTS_FILE
    if _TEXT_ELEMENTS is None:
        file = ifcopenshell.api.run("project.create_file")
        ifcopenshell.api.run(
            "root.create_entity", file, ifc_class="IfcProject", name="P"
        )
        elements = []
        for name, value in (("E_str", "1.5"), ("E_text", "Béton"), ("E_none", None)):
            element = ifcopenshell.api.run(
                "root.create_entity",
                file,
                ifc_class="IfcBuildingElementProxy",
                name=name,
            )
            if value is not None:
                pset = ifcopenshell.api.run(
                    "pset.add_pset", file, product=element, name="Pset_Text"
                )
                ifcopenshell.api.run(
                    "pset.edit_pset", file, pset=pset, properties={"Value": value}
                )
            elements.append(element)
        _TEXT_ELEMENTS_FILE = file
        _TEXT_ELEMENTS = elements
    return _TEXT_ELEMENTS


class SpyChecking(AbsoluteOrRelativeChecking):
    """A check recording the groups its run loop evaluates."""

    def __init__(self):
        super().__init__("Absolute_Number")
        self.evaluated = []

    def eval_check(self, groupresult):
        self.evaluated.append(groupresult)
        return groupresult


class MeasureSpy(AbsoluteOrRelativeChecking):
    """A check recording which measurement the type selects."""

    def __init__(self, type_name):
        super().__init__(type_name)
        self.called = []

    def number(self, groupresult):
        self.called.append("number")
        return super().number(groupresult)

    def quantity(self, groupresult):
        self.called.append("quantity")
        return super().quantity(groupresult)


class TestBase(unittest.TestCase):
    """The constructor, the type validation and the run loop."""

    def test_defaults(self):
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        self.assertEqual(check.type, "Absolute_Number")
        # The measured numbers of the current group.
        self.assertIsNone(check.source_number)
        self.assertIsNone(check.target_number)
        # The comparison with the SOURCE and TARGET keywords.
        self.assertIsNone(check.operation)
        # The quantity measurement fields.
        self.assertIsNone(check.quantity_pset)
        self.assertIsNone(check.quantity_prop)

    def test_type_is_stored(self):
        for type_name in (
            "Absolute_Number",
            "Absolute_Quantity",
            "Relative_Number",
            "Relative_Quantity",
        ):
            with self.subTest(type_name=type_name):
                check = AbsoluteOrRelativeChecking(type_name)
                self.assertEqual(check.type, type_name)

    def test_invalid_type_raises(self):
        for bad_type in ("Foo_Number", "Number", "", None, 42):
            with self.subTest(bad_type=bad_type):
                with self.assertRaises(ValueError):
                    AbsoluteOrRelativeChecking(bad_type)

    def test_run_evaluates_every_group_once(self):
        # The check groups the results of the rule: without a
        # select_grouping, one group per source object.
        rule = Volume(SelectFacet(), 0, 10)
        rule.result = [
            ClashResultOneObject(source=element, state=True)
            for element in ifc_elements()
        ]
        check = SpyChecking()
        check.run(rule)
        self.assertEqual(check.evaluated, rule.grouped_result)
        self.assertEqual(len(check.evaluated), 3)

    def test_run_on_a_rule_without_result_evaluates_nothing(self):
        rule = Volume(SelectFacet(), 0, 10)
        rule.result = []
        check = SpyChecking()
        check.run(rule)
        self.assertEqual(check.evaluated, [])


class TestMeasurements(unittest.TestCase):
    """The number and quantity measurements of the two sets."""

    def test_number_counts_both_sets(self):
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.number(make_group(nb_source=3, nb_target=2))
        self.assertEqual(check.source_number, 3)
        self.assertEqual(check.target_number, 2)

    def test_number_on_an_empty_group_is_zero(self):
        check = AbsoluteOrRelativeChecking("Relative_Number")
        check.number(GroupResult())
        self.assertEqual(check.source_number, 0)
        self.assertEqual(check.target_number, 0)

    def test_quantity_sums_the_property_of_both_sets(self):
        check = AbsoluteOrRelativeChecking("Absolute_Quantity")
        check.quantity_pset = "Pset_Test"
        check.quantity_prop = "Value"
        group = GroupResult()
        elements = ifc_elements()
        for element in elements[:2]:
            group.add_source(ClashResultOneObject(source=element, state=True))
        group.add_target(
            ClashResultTwoObjects(source=elements[2], target=elements[2], state=True)
        )
        check.quantity(group)
        self.assertAlmostEqual(check.source_number, 5.0)
        self.assertAlmostEqual(check.target_number, 2.5)

    def test_quantity_with_a_missing_property_counts_zero(self):
        check = AbsoluteOrRelativeChecking("Absolute_Quantity")
        check.quantity_pset = "Pset_Other"
        check.quantity_prop = "Value"
        group = GroupResult()
        for element in ifc_elements():
            group.add_source(ClashResultOneObject(source=element, state=True))
        check.quantity(group)
        self.assertAlmostEqual(check.source_number, 0.0)

    def test_quantity_with_a_number_written_as_a_string(self):
        # "1.5" is parsed as a number and summed.
        check = AbsoluteOrRelativeChecking("Absolute_Quantity")
        check.quantity_pset = "Pset_Text"
        check.quantity_prop = "Value"
        group = GroupResult()
        for element in ifc_text_elements():
            group.add_source(ClashResultOneObject(source=element, state=True))
        check.quantity(group)
        # "1.5" is parsed, "Béton" and the missing property count 0.
        self.assertAlmostEqual(check.source_number, 1.5)

    def test_to_number_accepts_any_storage(self):
        to_number = AbsoluteOrRelativeChecking._to_number
        self.assertAlmostEqual(to_number(2.5), 2.5)
        self.assertAlmostEqual(to_number(2), 2.0)
        self.assertAlmostEqual(to_number("1.5"), 1.5)
        self.assertAlmostEqual(to_number(" 2.5 "), 2.5)
        self.assertAlmostEqual(to_number("-1.5"), -1.5)
        # Pure text and an empty value cannot be converted: they
        # count 0.
        self.assertEqual(to_number("Béton"), 0.0)
        self.assertEqual(to_number(""), 0.0)
        self.assertEqual(to_number("2.5 m"), 0.0)
        self.assertEqual(to_number("2,5"), 0.0)
        self.assertEqual(to_number(None), 0.0)
        self.assertEqual(to_number(True), 1.0)

    def test_quantity_without_a_configured_property_counts_zero(self):
        # Without a quantity_pset / quantity_prop, nothing can be
        # measured: both sets count 0 instead of failing.
        check = AbsoluteOrRelativeChecking("Absolute_Quantity")
        group = GroupResult()
        for element in ifc_elements():
            group.add_source(ClashResultOneObject(source=element, state=True))
        check.quantity(group)
        self.assertEqual(check.source_number, 0.0)
        self.assertEqual(check.target_number, 0.0)


class TestTypeDispatch(unittest.TestCase):
    """The measurement selected by eval_check from the type name:
    Number (the element counts of the sets) or Quantity (the summed
    property over them)."""

    def test_number_type_counts_the_elements(self):
        check = MeasureSpy("Absolute_Number")
        check.operation = "TARGET>=2"
        check.eval_check(make_group(2, 1))
        self.assertEqual(check.called, ["number"])

    def test_quantity_type_sums_the_property(self):
        check = MeasureSpy("Relative_Quantity")
        check.quantity_pset = "Pset_Test"
        check.quantity_prop = "Value"
        check.operation = "SOURCE>=TARGET"
        group = GroupResult()
        elements = ifc_elements()
        for element in elements[:2]:
            group.add_source(ClashResultOneObject(source=element, state=True))
        group.add_target(
            ClashResultTwoObjects(source=elements[2], target=elements[2], state=True)
        )
        check.eval_check(group)
        self.assertEqual(check.called, ["quantity"])


class TestAbsoluteCheck(unittest.TestCase):
    """The absolute operation: a single measured set of the group
    compared against a requirement ("TARGET>=3" measures the target
    set of the group, "SOURCE>=3" its source set)."""

    @staticmethod
    def target_group(elements):
        """A group whose target set holds the elements."""
        group = GroupResult()
        for element in elements:
            group.add_target(
                ClashResultTwoObjects(source="focused", target=element, state=True)
            )
        return group

    @staticmethod
    def source_group(elements):
        """A group whose source set holds the elements."""
        group = GroupResult()
        for element in elements:
            group.add_source(ClashResultOneObject(source=element, state=True))
        return group

    def test_number_measures_the_targets_of_the_group(self):
        # "Each source must have at least 3 targets": the group holds
        # 1 source and 3 targets, 3 >= 3 is True.
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "TARGET>=3"
        group = make_group(nb_source=1, nb_target=3)
        check.eval_check(group)
        self.assertEqual(check.target_number, 3)
        self.assertTrue(group.abs_or_rel_check)

    def test_number_below_the_requirement(self):
        # "Each source must have at least 3 targets": 2 >= 3 is False.
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "TARGET>=3"
        group = make_group(nb_source=1, nb_target=2)
        check.eval_check(group)
        self.assertFalse(group.abs_or_rel_check)

    def test_number_measures_the_sources_of_the_group(self):
        # "Each target must relate to exactly 3 sources": 3 == 3 is
        # True.
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "SOURCE==3"
        group = make_group(nb_source=3, nb_target=1)
        check.eval_check(group)
        self.assertEqual(check.source_number, 3)
        self.assertTrue(group.abs_or_rel_check)

    def test_quantity_sums_the_targets_of_the_group(self):
        # Three elements at 2.5 each in the target set: 7.5 >= 5 is
        # True, the sum is really accumulated.
        check = AbsoluteOrRelativeChecking("Absolute_Quantity")
        check.quantity_pset = "Pset_Test"
        check.quantity_prop = "Value"
        check.operation = "TARGET>=5"
        group = self.target_group(ifc_elements())
        check.eval_check(group)
        self.assertAlmostEqual(check.target_number, 7.5)
        self.assertTrue(group.abs_or_rel_check)

    def test_quantity_below_the_requirement(self):
        check = AbsoluteOrRelativeChecking("Absolute_Quantity")
        check.quantity_pset = "Pset_Test"
        check.quantity_prop = "Value"
        check.operation = "TARGET>=8"
        group = self.target_group(ifc_elements())
        check.eval_check(group)
        self.assertFalse(group.abs_or_rel_check)

    def test_quantity_sums_the_sources_of_the_group(self):
        # The property is summed over the source set of the group.
        check = AbsoluteOrRelativeChecking("Absolute_Quantity")
        check.quantity_pset = "Pset_Test"
        check.quantity_prop = "Value"
        check.operation = "SOURCE>=5"
        group = self.source_group(ifc_elements())
        check.eval_check(group)
        self.assertAlmostEqual(check.source_number, 7.5)
        self.assertTrue(group.abs_or_rel_check)

    def test_quantity_on_non_numeric_values_reaches_the_comparison(self):
        # A number written as a string is measured, the pure text
        # counts 0: 1.5 >= 1 is True.
        check = AbsoluteOrRelativeChecking("Absolute_Quantity")
        check.quantity_pset = "Pset_Text"
        check.quantity_prop = "Value"
        check.operation = "TARGET>=1"
        group = self.target_group(ifc_text_elements())
        check.eval_check(group)
        self.assertAlmostEqual(check.target_number, 1.5)
        self.assertTrue(group.abs_or_rel_check)

    def test_one_object_group_measures_its_own_set(self):
        # A group holding a single set (a one object rule) measures
        # that set: its own property.
        check = AbsoluteOrRelativeChecking("Absolute_Quantity")
        check.quantity_pset = "Pset_Test"
        check.quantity_prop = "Value"
        check.operation = "SOURCE>=2"
        group = self.source_group(ifc_elements()[:1])
        check.eval_check(group)
        self.assertAlmostEqual(check.source_number, 2.5)
        self.assertTrue(group.abs_or_rel_check)

    def test_run_checks_every_group(self):
        # The run() loop reaches the comparison of every group: the
        # first source holds two targets (2 >= 2 is True), the second
        # one (1 >= 2 is False).
        rule = Intersection(SelectFacet(), SelectFacet())
        elements = ifc_elements()
        rule.result = [
            ClashResultTwoObjects(
                source=elements[0], target=elements[1], state=True
            ),
            ClashResultTwoObjects(
                source=elements[0], target=elements[2], state=True
            ),
            ClashResultTwoObjects(
                source=elements[1], target=elements[2], state=True
            ),
        ]
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "TARGET>=2"
        check.run(rule)
        self.assertTrue(rule.grouped_result[0].abs_or_rel_check)
        self.assertFalse(rule.grouped_result[1].abs_or_rel_check)


class TestRelativeOperation(unittest.TestCase):
    """The relative operation: the source set of the group against its
    target set, both named in the operation."""

    def test_number_compares_both_sets(self):
        # "At least twice more sources than targets": 3 >= 2*2 is
        # False, the relation is not reached.
        check = AbsoluteOrRelativeChecking("Relative_Number")
        check.operation = "SOURCE>=2*TARGET"
        group = make_group(nb_source=3, nb_target=2)
        check.eval_check(group)
        self.assertFalse(group.abs_or_rel_check)

    def test_number_compares_both_sets_passing(self):
        # "At least as many sources as targets": 3 >= 2 is True.
        check = AbsoluteOrRelativeChecking("Relative_Number")
        check.operation = "SOURCE>=TARGET"
        group = make_group(nb_source=3, nb_target=2)
        check.eval_check(group)
        self.assertTrue(group.abs_or_rel_check)

    def test_number_below_the_relation(self):
        # "At least as many sources as targets": 1 >= 2 is False.
        check = AbsoluteOrRelativeChecking("Relative_Number")
        check.operation = "SOURCE>=TARGET"
        group = make_group(nb_source=1, nb_target=2)
        check.eval_check(group)
        self.assertFalse(group.abs_or_rel_check)

    def test_number_with_an_operation_on_the_target_side(self):
        # "The source count must be at least half the target count":
        # 2 >= 4/2 is True.
        check = AbsoluteOrRelativeChecking("Relative_Number")
        check.operation = "SOURCE>=TARGET/2"
        group = make_group(nb_source=2, nb_target=4)
        check.eval_check(group)
        self.assertTrue(group.abs_or_rel_check)

    def test_quantity_relates_the_two_sums(self):
        # The summed property of the source set against the target
        # set: 5.0 >= 2.5 is True.
        check = AbsoluteOrRelativeChecking("Relative_Quantity")
        check.quantity_pset = "Pset_Test"
        check.quantity_prop = "Value"
        check.operation = "SOURCE>=TARGET"
        group = GroupResult()
        elements = ifc_elements()
        for element in elements[:2]:
            group.add_source(ClashResultOneObject(source=element, state=True))
        group.add_target(
            ClashResultTwoObjects(source=elements[2], target=elements[2], state=True)
        )
        check.eval_check(group)
        self.assertAlmostEqual(check.source_number, 5.0)
        self.assertAlmostEqual(check.target_number, 2.5)
        self.assertTrue(group.abs_or_rel_check)


class TestMustRuleWiring(unittest.TestCase):
    """The run_abs_or_rel entry points of the two rule base classes:
    the check groups the results through the grouping of the rule
    (run_grouping, driven by select_grouping), or by source when the
    rule has no grouping, then checks every group."""

    def test_no_check_returns_none(self):
        rule_one = Volume(SelectFacet(), 0, 10)
        rule_two = Intersection(SelectFacet(), SelectFacet())
        self.assertIsNone(rule_one.run_abs_or_rel())
        self.assertIsNone(rule_two.run_abs_or_rel())

    def test_one_object_checks_one_group_per_source(self):
        # Without a select_grouping, the default grouping: each source
        # object forms its own group, checked separately.
        rule = Volume(SelectFacet(), 0, 10)
        rule.result = [
            ClashResultOneObject(source=element, state=True)
            for element in ifc_elements()
        ]
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "SOURCE>=1"
        rule.abs_or_rel_check = check

        self.assertTrue(rule.run_abs_or_rel())
        self.assertEqual(len(rule.grouped_result), 3)
        self.assertTrue(all(group.abs_or_rel_check for group in rule.grouped_result))

    def test_one_object_uses_the_classic_grouping_of_the_rule(self):
        # With a select_grouping, the Must check groups through the
        # classic grouping of the rule: an entity grouping gives one
        # group per entity class holding the three sources.
        rule = Volume(SelectFacet(), 0, 10)
        rule.result = [
            ClashResultOneObject(source=element, state=True)
            for element in ifc_elements()
        ]
        rule.select_grouping = "ENTITY"
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "SOURCE>=3"
        rule.abs_or_rel_check = check

        self.assertTrue(rule.run_abs_or_rel())
        # One group per entity class: the three elements share one.
        self.assertEqual(len(rule.grouped_result), 1)
        group = rule.grouped_result[0]
        self.assertEqual(len(group.source_set), 3)
        self.assertTrue(group.abs_or_rel_check)

    def test_two_objects_checks_one_group_per_source(self):
        # Without a select_grouping, the default grouping: one group
        # per source object, the targets of its results in the target
        # set of the group, measured by the check.
        rule = Intersection(SelectFacet(), SelectFacet())
        elements = ifc_elements()
        rule.result = [
            ClashResultTwoObjects(
                source=elements[0], target=elements[1], state=True
            ),
            ClashResultTwoObjects(
                source=elements[0], target=elements[2], state=True
            ),
        ]
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "TARGET==2"
        rule.abs_or_rel_check = check

        self.assertTrue(rule.run_abs_or_rel())
        self.assertEqual(len(rule.grouped_result), 1)
        group = rule.grouped_result[0]
        self.assertEqual(group.source_set, {elements[0]})
        self.assertEqual(group.target_set, {elements[1], elements[2]})
        self.assertTrue(group.abs_or_rel_check)

    def test_two_objects_target_grouping_groups_by_target(self):
        # A target grouping of the rule (select_grouping "TARGET"):
        # one group per target object, the sources of its results in
        # the source set of the group, measured by the operation
        # naming the source side.
        rule = Intersection(SelectFacet(), SelectFacet())
        elements = ifc_elements()
        rule.result = [
            ClashResultTwoObjects(
                source=elements[0], target=elements[2], state=True
            ),
            ClashResultTwoObjects(
                source=elements[1], target=elements[2], state=True
            ),
        ]
        rule.select_grouping = "TARGET"
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "SOURCE==2"
        rule.abs_or_rel_check = check

        self.assertTrue(rule.run_abs_or_rel())
        self.assertEqual(len(rule.grouped_result), 1)
        group = rule.grouped_result[0]
        self.assertEqual(group.target_set, {elements[2]})
        self.assertEqual(group.source_set, {elements[0], elements[1]})
        self.assertTrue(group.abs_or_rel_check)

    def test_one_object_without_select_grouping_defaults_to_the_source(self):
        # Without a select_grouping, the check falls back to the
        # grouping by source: one group per source object.
        rule = Volume(SelectFacet(), 0, 10)
        rule.result = [
            ClashResultOneObject(source=element, state=True)
            for element in ifc_elements()
        ]
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "SOURCE>=1"
        rule.abs_or_rel_check = check

        self.assertTrue(rule.run_abs_or_rel())
        self.assertEqual(len(rule.grouped_result), 3)
        self.assertTrue(all(group.abs_or_rel_check for group in rule.grouped_result))

    def test_two_objects_entity_grouping_measures_each_group_side(self):
        # An entity grouping on a two objects rule fills one side per
        # group (the sources in the source class group, the targets
        # in the target class group); here every element shares one
        # class, so a single group holds both sets, and the check
        # focused on the target measures its source set.
        rule = Intersection(SelectFacet(), SelectFacet())
        elements = ifc_elements()
        rule.result = [
            ClashResultTwoObjects(
                source=elements[0], target=elements[1], state=True
            ),
            ClashResultTwoObjects(
                source=elements[0], target=elements[2], state=True
            ),
        ]
        rule.select_grouping = "ENTITY"
        check = AbsoluteOrRelativeChecking("Absolute_Number")
        check.operation = "SOURCE==1"
        rule.abs_or_rel_check = check

        self.assertTrue(rule.run_abs_or_rel())
        # One group per entity class of the results, here a single one
        # (every element is an IfcBuildingElementProxy), holding both
        # sets.
        self.assertEqual(len(rule.grouped_result), 1)
        group = rule.grouped_result[0]
        self.assertEqual(group.source_set, {elements[0]})
        self.assertEqual(group.target_set, {elements[1], elements[2]})
        # The operation measures the source set of the group.
        self.assertEqual(check.source_number, 1)
        self.assertTrue(group.abs_or_rel_check)

    def test_two_objects_uses_the_classic_grouping_of_the_rule(self):
        # Same as the one object rule: the select_grouping of the
        # rule (here an entity grouping) drives the Must check
        # grouping, one group per entity class of the results.
        rule = Intersection(SelectFacet(), SelectFacet())
        elements = ifc_elements()
        rule.result = [
            ClashResultTwoObjects(
                source=elements[0], target=elements[1], state=True
            ),
            ClashResultTwoObjects(
                source=elements[2], target=elements[1], state=True
            ),
        ]
        rule.select_grouping = "ENTITY"
        rule.abs_or_rel_check = AbsoluteOrRelativeChecking("Absolute_Number")

        self.assertTrue(rule.run_abs_or_rel())
        self.assertEqual(len(rule.grouped_result), 1)
        group = rule.grouped_result[0]
        self.assertEqual(group.source_set, {elements[0], elements[2]})
        self.assertEqual(group.target_set, {elements[1]})


if __name__ == "__main__":
    unittest.main()
