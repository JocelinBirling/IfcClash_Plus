"""The ResultPipeline (SPEC Separation moteur/gestion), tested on a
fake rule: the step order per state and the RuleOutput contents.

The pipeline delegates to the management methods of the rule during
the migration; the fakes below record the calls, the assertions
check the orchestration only. The steps themselves (exception,
criticity, actor, grouping, abs_or_rel) stay covered by the
structure tests of RuleClass.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_structure_ResultPipeline.py -v
"""
import sys
import unittest

sys.path.insert(0, "./ifcclash_plus")

from pipeline import ResultPipeline, RuleOutput


class FakeResult:
    """A result surface for the Select step (pipeline.selection_of)."""

    def __init__(self, source, status=True):
        self.source = source
        self.status = status


class FakeFile:
    """The file of a fake element."""

    def __init__(self, name):
        self.name = name


class FakeElement:
    """A fake entity instance."""

    def __init__(self, file, name):
        self.file = file
        self.name = name


class FakeRule:
    """The management surface of a rule, recording every call."""

    def __init__(self, state, results=None, grouped=None):
        self.state = state
        self.result = results if results is not None else []
        self.grouped_result = grouped or []
        self.calls = []
        # The Select step configuration (pipeline.selection_of reads
        # it off the rule, as a SelectRule poses it).
        self.element_to_pass = "source"
        self.element_state_to_pass = True
        self.select_source = None

    def run_exception(self):
        self.calls.append("exception")

    def manage_result(self):
        self.calls.append("manage_result")


class TestResultPipeline(unittest.TestCase):
    def test_final_runs_exception_then_manage_result(self):
        rule = FakeRule("Final", results=[1, 2], grouped=[3])
        output = ResultPipeline(rule).apply()

        self.assertEqual(rule.calls, ["exception", "manage_result"])
        self.assertIsInstance(output, RuleOutput)
        self.assertIs(output.results, rule.result)
        self.assertEqual(output.results, [1, 2])
        self.assertEqual(output.groups, [3])
        self.assertIsNone(output.selection)

    def test_select_runs_exception_then_selection_of(self):
        """The Select step (pipeline.selection_of, the former
        produce_select) reads the results of the rule."""
        ifc_file = FakeFile("IfcFile")
        element = FakeElement(ifc_file, "element")
        rule = FakeRule("Select", results=[FakeResult(element)])
        output = ResultPipeline(rule).apply()

        self.assertEqual(rule.calls, ["exception"])
        self.assertEqual(output.selection, {ifc_file: [element]})
        self.assertIsNone(output.groups)

    def test_display_runs_exception_only(self):
        for state in ("Display_Input", "Display_Result"):
            rule = FakeRule(state)
            output = ResultPipeline(rule).apply()

            self.assertEqual(rule.calls, ["exception"], state)
            self.assertIsNone(output.selection, state)
            self.assertIsNone(output.groups, state)

    def test_empty_grouping_gives_no_groups(self):
        rule = FakeRule("Final")
        output = ResultPipeline(rule).apply()

        self.assertEqual(output.results, [])
        self.assertIsNone(output.groups)


if __name__ == "__main__":
    unittest.main()
