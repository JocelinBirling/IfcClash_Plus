"""
Test suite for RuleFolder.

A RuleFolder contains rules or other folders, and runs its content only
if its activation rule is satisfied:
- no activation rule: the content always runs;
- SelectFacet: the content runs when the facet selects elements;
- BooleanRule: the content runs when the boolean tree evaluates to True.
Anything else as activation_rule raises a TypeError.
"""

import unittest
import sys
sys.path.insert(0, './ifcclash_plus')

from Rules import Collision, Volume
from RuleClass import SelectFacet, RuleFile, RuleFolder, SelectRule
from booleanrule import AndRule, BooleanLeaf
from ifctester import ids


class TestRuleFolderInitialization(unittest.TestCase):
    """Test the default attributes of a RuleFolder."""

    def test_initialization(self):
        folder = RuleFolder()
        self.assertEqual(folder.id, "AZE")
        self.assertIsNone(folder.activation_rule)
        self.assertEqual(folder.activation_case, "ALLTRUE")
        self.assertEqual(folder.contains, [])


class TestRuleFolderActivation(unittest.TestCase):
    """Test every activation case of check_Activation_Rule."""

    def setUp(self):
        """Set up test fixtures."""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

    def _select_facet(self, entity_name):
        select = SelectFacet()
        select.applicability = [ids.Entity(name=entity_name)]
        return select

    def _build_rule_file(self, activation=None, contains=None):
        """Build a RuleFile with one folder containing a Collision rule.

        The Collision between doors and slabs of the Architecture model
        finds 24 results, so a folder that runs produces 24 results.
        """
        self.folder = RuleFolder()
        self.folder.activation_rule = activation
        self.rule = Collision(
            self._select_facet("IFCDOOR"),
            self._select_facet("IFCSLAB"),
            allow_touching=False,
        )
        self.folder.contains = (
            [self.rule] if contains is None else contains
        )

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [self.folder]
        return rule_file

    def test_no_activation_rule(self):
        """Without activation rule the content always runs."""
        rule_file = self._build_rule_file()
        rule_file.run()

        self.assertTrue(self.folder.check_Activation_Rule())
        self.assertEqual(len(self.rule.result), 24)

    def test_activation_with_SelectFacet(self):
        """The content runs when the facet selects elements, even when the
        facet is not shared with a rule of the folder."""
        rule_file = self._build_rule_file(activation=self._select_facet("IFCWINDOW"))
        rule_file.run()

        self.assertTrue(self.folder.check_Activation_Rule())
        self.assertEqual(len(self.rule.result), 24)

    def test_no_activation_with_empty_SelectFacet(self):
        """The content does not run when the facet selects nothing, and
        folder.run() returns False."""
        rule_file = self._build_rule_file(
            activation=self._select_facet("IFCBOILER")  # not in the model
        )
        rule_file.run()

        self.assertFalse(self.folder.check_Activation_Rule())
        self.assertEqual(len(self.rule.result), 0)

        # The folder itself reports that it did not run
        self.assertFalse(self.folder.run())

    def test_activation_with_BooleanLeaf(self):
        """The content runs when the BooleanLeaf evaluates to True."""
        volume_rule = Volume(
            self._select_facet("IFCDOOR"), volume_min=0.0, volume_max=1e12
        )
        rule_file = self._build_rule_file(activation=BooleanLeaf(volume_rule))
        rule_file.run()

        self.assertTrue(self.folder.check_Activation_Rule())
        self.assertEqual(len(self.rule.result), 24)

    def test_no_activation_with_false_BooleanRule(self):
        """The content does not run when the boolean tree is False.
        The AndRule wraps two rules: one with results, one without."""
        rule_with_results = Volume(
            self._select_facet("IFCDOOR"), volume_min=0.0, volume_max=1e12
        )
        rule_without_results = Volume(
            self._select_facet("IFCWALLSTANDARDCASE"),
            volume_min=0.0,
            volume_max=0.0,
        )
        rule_file = self._build_rule_file(
            activation=AndRule(rule_with_results, rule_without_results)
        )
        rule_file.run()

        self.assertFalse(self.folder.check_Activation_Rule())
        self.assertEqual(len(self.rule.result), 0)

    def test_activation_with_true_BooleanRule(self):
        """The content runs when the boolean tree is True."""
        rule_with_results = Volume(
            self._select_facet("IFCDOOR"), volume_min=0.0, volume_max=1e12
        )
        rule_file = self._build_rule_file(activation=AndRule(rule_with_results))
        rule_file.run()

        self.assertTrue(self.folder.check_Activation_Rule())
        self.assertEqual(len(self.rule.result), 24)

    def test_raw_rule_activation_raises(self):
        """activation_rule only accepts a SelectFacet or a BooleanRule."""
        rule_file = self._build_rule_file(
            activation=Volume(
                self._select_facet("IFCDOOR"), volume_min=0.0, volume_max=1e12
            )
        )
        with self.assertRaises(TypeError):
            rule_file.run()

    def test_SelectRule_activation_raises(self):
        """A SelectRule is not a valid activation rule."""
        select_rule = SelectRule()
        select_rule.rule = Volume(
            self._select_facet("IFCDOOR"), volume_min=0.0, volume_max=1e12
        )
        rule_file = self._build_rule_file(activation=select_rule)
        with self.assertRaises(TypeError):
            rule_file.run()


class TestRuleFolderStructure(unittest.TestCase):
    """Test the composition of folders and the file information."""

    def setUp(self):
        """Set up test fixtures."""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

    def _select_facet(self, entity_name):
        select = SelectFacet()
        select.applicability = [ids.Entity(name=entity_name)]
        return select

    def test_nested_folders(self):
        """A folder can contain another folder, each with its own
        activation rule."""
        inner_rule = Collision(
            self._select_facet("IFCDOOR"),
            self._select_facet("IFCSLAB"),
            allow_touching=False,
        )
        inner_folder = RuleFolder()
        inner_folder.activation_rule = self._select_facet("IFCDOOR")
        inner_folder.contains = [inner_rule]

        outer_rule = Volume(
            self._select_facet("IFCDOOR"), volume_min=0.0, volume_max=1e12
        )
        outer_folder = RuleFolder()
        outer_folder.contains = [outer_rule, inner_folder]

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [outer_folder]
        rule_file.run()

        self.assertEqual(len(outer_rule.result), 14)
        self.assertEqual(len(inner_rule.result), 24)

    def test_nested_folder_not_activated(self):
        """The content of an inner folder does not run when its own
        activation rule is False."""
        inner_rule = Collision(
            self._select_facet("IFCDOOR"),
            self._select_facet("IFCSLAB"),
            allow_touching=False,
        )
        inner_folder = RuleFolder()
        inner_folder.activation_rule = self._select_facet("IFCBOILER")
        inner_folder.contains = [inner_rule]

        outer_rule = Volume(
            self._select_facet("IFCDOOR"), volume_min=0.0, volume_max=1e12
        )
        outer_folder = RuleFolder()
        outer_folder.contains = [outer_rule, inner_folder]

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [outer_folder]
        rule_file.run()

        # The outer rule ran, the inner folder content did not
        self.assertEqual(len(outer_rule.result), 14)
        self.assertEqual(len(inner_rule.result), 0)

    def test_update_file_info_reaches_everything(self):
        """The files reach the rules of the folder and the activation
        facet, even when it is not shared with a contained rule."""
        rule = Collision(
            self._select_facet("IFCDOOR"),
            self._select_facet("IFCSLAB"),
            allow_touching=False,
        )
        activation_facet = self._select_facet("IFCWINDOW")

        folder = RuleFolder()
        folder.activation_rule = activation_facet
        folder.contains = [rule]

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [folder]
        rule_file.load_file()
        rule_file.update_file_info()

        self.assertEqual(len(rule_file.list_ifc_file), 1)
        self.assertEqual(len(rule.select_source.list_ifc_file), 1)
        self.assertEqual(len(rule.select_target.list_ifc_file), 1)
        self.assertEqual(len(activation_facet.list_ifc_file), 1)

    def test_update_file_info_reaches_boolean_activation_rules(self):
        """The files reach the rules referenced by a boolean activation."""
        activation_rule = Volume(
            self._select_facet("IFCDOOR"), volume_min=0.0, volume_max=1e12
        )
        folder = RuleFolder()
        folder.activation_rule = AndRule(activation_rule)

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [folder]
        rule_file.load_file()
        rule_file.update_file_info()

        self.assertEqual(len(activation_rule.select_source.list_ifc_file), 1)


if __name__ == "__main__":
    unittest.main()
