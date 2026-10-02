"""
Boolean composition of rules.

This module combines the results of several rules with boolean logic.
As in the rest of the project, the classes are created and populated
directly with the rule objects: (R1 & R2) | R3 is written

    rule = OrRule(AndRule(collision_rule, clearance_rule), volume_rule)
    rule_file.run()
    rule.evaluate()

A child of a composite can be either a RuleCheck or another BooleanRule,
so composites can be nested into each other.

A BooleanRule tree is evaluated AFTER the rules it references have been
executed (typically via RuleFile.run()): evaluate() only reads the
results, it never computes geometry.

A rule is converted into a boolean according to a mode:

- "have_result": True if the rule produced at least one result.
- "have_no_result": True if the rule produced no result.
- "have_more" / "have_more_or_equals": True if the number of results is
  greater than (or equal to) value.
- "have_less" / "have_less_or_equals": True if the number of results is
  less than (or equal to) value.
- "equals": True if the number of results is exactly value.

The modes comparing to a quantity require the value parameter.

A leaf can also evaluate a single ClashResultTwoObjects with
evaluate_result: the rule of the leaf is created empty (without source
and without target) and, for each result given, the source and the
target of the rule become the elements of the result. The rule runs on
this pair and the leaf returns True if the exception applies to this
pair. This is the mechanism to evaluate an exception rule result by
result.
"""

from abc import abstractmethod
from typing import TYPE_CHECKING, Iterator, List

if TYPE_CHECKING:
    from RuleClass import RuleCheck


class BooleanRule:
    """Abstract base for every boolean node."""

    @abstractmethod
    def evaluate(self) -> bool:
        """Return the boolean value of the node."""

    def rules(self) -> Iterator["RuleCheck"]:
        """Iterate over every RuleCheck leaf of the tree."""
        return iter(())


class BooleanLeaf(BooleanRule):
    """A single RuleCheck seen as a boolean.

    mode (see module docstring):
    - "have_result" / "have_no_result": presence of results.
    - "have_more", "have_more_or_equals", "have_less", "have_less_or_equals",
      "equals": compare the number of results with value.
    """

    MODES = ("have_result", "have_no_result", "have_more","have_less","have_more_or_equals","have_less_or_equals","equals")
    QUANTITY_MODES = ("have_more", "have_less", "have_more_or_equals", "have_less_or_equals", "equals")

    def __init__(self, rule: "RuleCheck", mode: str = "have_result", value:str|None = None):
        if mode not in self.MODES:
            raise ValueError(
                f"mode must be one of {self.MODES}, got '{mode}'"
            )
        if mode in self.QUANTITY_MODES and value is None:
            raise ValueError(
                f"mode '{mode}' requires a value"
            )
        self.rule = rule
        self.mode = mode
        self.value=value

    def evaluate(self) -> bool:
        return self._evaluate_number_of_results(len(self.rule.result))

    def evaluate_result(self, result) -> bool:
        """Evaluate the rule on the pair of elements of a result.

        The rule of the leaf is created empty, without source and
        without target: for the given ClashResultTwoObjects, the source
        and the target of the rule become the elements of the result.
        The rule runs on this pair and the leaf returns True if the
        exception applies to this pair, False otherwise.
        """
        # Deferred import: RuleClass imports this module
        from RuleClass import Select

        source_select = Select()
        source_select.dict_elements = {result.source.file: [result.source]}
        source_select.list_ifc_file = [result.source.file]
        self.rule.select_source = source_select

        if hasattr(self.rule, "select_target") and result.target is not None:
            target_select = Select()
            target_select.dict_elements = {result.target.file: [result.target]}
            target_select.list_ifc_file = [result.target.file]
            self.rule.select_target = target_select

        # The rule is run on this pair only, its previous results are dropped
        self.rule.result = []
        self.rule.run()

        return self._evaluate_number_of_results(len(self.rule.result))

    def _evaluate_number_of_results(self, number_of_results: int) -> bool:
        if self.mode == "have_result":
            return number_of_results > 0

        if self.mode == "have_no_result":
            return number_of_results == 0

        value = int(self.value)

        if self.mode == "have_more":
            return number_of_results > value

        if self.mode == "have_more_or_equals":
            return number_of_results >= value

        if self.mode == "have_less":
            return number_of_results < value

        if self.mode == "have_less_or_equals":
            return number_of_results <= value

        # "equals"
        return number_of_results == value

    def rules(self) -> Iterator["RuleCheck"]:
        yield self.rule


def _to_boolean_node(child, mode: str) -> BooleanRule:
    """Wrap a raw rule into a BooleanLeaf, keep composites as they are."""
    if isinstance(child, BooleanRule):
        return child
    if hasattr(child, "result"):
        return BooleanLeaf(child, mode)
    raise TypeError(
        f"Children must be a RuleCheck or a BooleanRule, got {type(child)}"
    )


class AndRule(BooleanRule):
    """True if every child evaluates to True. True if empty.

    The children are rules (RuleCheck) or other BooleanRule.
    mode applies to every direct rule child.
    """

    def __init__(self, *children, mode: str = "have_result"):
        self.children: List[BooleanRule] = [
            _to_boolean_node(child, mode) for child in children
        ]

    def evaluate(self) -> bool:
        return all(child.evaluate() for child in self.children)

    def rules(self) -> Iterator["RuleCheck"]:
        for child in self.children:
            yield from child.rules()


class OrRule(BooleanRule):
    """True if at least one child evaluates to True. False if empty.

    The children are rules (RuleCheck) or other BooleanRule.
    mode applies to every direct rule child.
    """

    def __init__(self, *children, mode: str = "have_result"):
        self.children: List[BooleanRule] = [
            _to_boolean_node(child, mode) for child in children
        ]

    def evaluate(self) -> bool:
        return any(child.evaluate() for child in self.children)

    def rules(self) -> Iterator["RuleCheck"]:
        for child in self.children:
            yield from child.rules()


class NotRule(BooleanRule):
    """Inverts its child. The child is a rule (RuleCheck) or a BooleanRule."""

    def __init__(self, child, mode: str = "have_result"):
        self.child: BooleanRule = _to_boolean_node(child, mode)

    def evaluate(self) -> bool:
        return not self.child.evaluate()

    def rules(self) -> Iterator["RuleCheck"]:
        yield from self.child.rules()
