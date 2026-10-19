"""
Test file for save_results_to_json: the JSON archive of all the results
produced by the rules of a run RuleFile.
"""

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, './ifcclash_plus')

from ifctester import ids

from booleanrule import BooleanLeaf
from RuleClass import (
    AbsoluteOrRelativeChecking,
    RuleFile,
    RuleFolder,
    SelectFacet,
)
from Rules import Intersection, Volume
from serialization import save_results_to_json, results_to_json


class TestSaveResultsToJson(unittest.TestCase):
    """The results archive of a run RuleFile."""

    def setUp(self):
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
        self.model_name = os.path.basename(self.ifc_path)
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def _save(self, rule_file, filename="results.json"):
        """Save the results to a JSON file and load the file back."""
        filepath = os.path.join(self.temp_dir.name, filename)
        save_results_to_json(rule_file, filepath)
        with open(filepath, encoding="utf-8") as handle:
            return json.load(handle)

    def test_produce_results_file(self):
        """A run RuleFile produces a results file on disk, loadable and
        complete: models, configuration, per-rule configuration,
        results with GUID and model name."""
        wall_select = SelectFacet()
        wall_select.applicability = [ids.Entity(name="IFCWALLSTANDARDCASE")]

        furniture_select = SelectFacet()
        furniture_select.applicability = [ids.Entity(name="IFCFURNISHINGELEMENT")]

        rule_file = RuleFile()
        rule_file.id = "rf_1"
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [Intersection(wall_select, furniture_select, 0.01)]
        rule_file.run()

        filepath = os.path.join(self.temp_dir.name, "results.json")
        save_results_to_json(rule_file, filepath)

        # The file exists on disk and is not empty.
        self.assertTrue(os.path.isfile(filepath))
        self.assertGreater(os.path.getsize(filepath), 0)

        with open(filepath, encoding="utf-8") as handle:
            data = json.load(handle)

        self.assertEqual(data["type"], "RuleFileResults")
        self.assertEqual(
            data["models"], [{"name": self.model_name, "path": self.ifc_path}]
        )

        # The configuration of the RuleFile travels with the results.
        configuration = data["configuration"]
        self.assertEqual(configuration["id"], "rf_1")
        self.assertEqual(configuration["list_ifc_path"], [self.ifc_path])
        self.assertEqual(len(configuration["contains"]), 1)

        rules = data["rules"]
        self.assertEqual(len(rules), 1)
        rule = rules[0]
        self.assertEqual(rule["rule_type"], "Intersection")
        self.assertEqual(len(rule["results"]), 1)

        # Each rule carries its own configuration.
        rule_configuration = rule["configuration"]
        self.assertEqual(rule_configuration["type"], "Intersection")
        self.assertEqual(rule_configuration["tolerance"], 0.01)
        self.assertIn("select_source", rule_configuration)
        self.assertIn("select_target", rule_configuration)

        result = rule["results"][0]
        self.assertTrue(result["status"])
        for ref in (result["source"], result["target"]):
            self.assertIn("global_id", ref)
            self.assertEqual(ref["model"], self.model_name)
            self.assertIn("step_id", ref)
            self.assertIn("ifc_type", ref)

    def test_folder_rules_and_grouped_results(self):
        wall_select = SelectFacet()
        wall_select.applicability = [ids.Entity(name="IFCWALLSTANDARDCASE")]

        volume_rule = Volume(wall_select, 0, 100)
        volume_rule.select_grouping = "ENTITY"

        folder = RuleFolder()
        folder.contains = [volume_rule]

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [folder]
        rule_file.run()

        data = self._save(rule_file)

        # The rules of the folders are flattened in run order.
        self.assertEqual(len(data["rules"]), 1)
        rule = data["rules"][0]
        self.assertEqual(rule["rule_type"], "Volume")
        self.assertGreater(len(rule["results"]), 0)
        self.assertEqual(rule["results"][0]["source"]["model"], self.model_name)

        # The per-rule configuration of a rule inside a folder.
        self.assertEqual(rule["configuration"]["type"], "Volume")
        self.assertEqual(rule["configuration"]["volume_min"], 0)
        self.assertEqual(rule["configuration"]["volume_max"], 100)
        self.assertEqual(rule["configuration"]["select_grouping"], "ENTITY")

        # The ENTITY grouping produced groups with their element sets.
        self.assertIn("grouped", rule)
        self.assertGreater(len(rule["grouped"]), 0)
        for group in rule["grouped"]:
            self.assertGreater(len(group["sources"]), 0)
            self.assertGreater(group["result_count"], 0)
            self.assertEqual(
                group["sources"][0]["model"], self.model_name
            )

    def _wall_furniture_rule_file(self):
        """A RuleFile with the one known wall/furniture clash of the
        Duplex model (source wall, target bed): one result per run."""
        wall_select = SelectFacet()
        wall_select.applicability = [ids.Entity(name="IFCWALLSTANDARDCASE")]

        furniture_select = SelectFacet()
        furniture_select.applicability = [ids.Entity(name="IFCFURNISHINGELEMENT")]

        rule = Intersection(wall_select, furniture_select, 0.01)

        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]
        rule_file.contains = [rule]
        return rule_file

    def test_exception_invalidates_results(self):
        # The exception rule of the leaf runs on the pair of each
        # result: the pair intersects, so it produces a result.
        # - "have_no_result": the exception does not apply, the result
        #   keeps its status.
        # - "have_result": the exception applies, the status becomes
        #   False (invalidated in place, not removed).
        rule_file = self._wall_furniture_rule_file()
        rule_file.contains[0].select_exception = BooleanLeaf(
            Intersection(None, None, 0.01), "have_no_result"
        )
        rule_file.run()
        data = self._save(rule_file)

        result = data["rules"][0]["results"][0]
        self.assertTrue(result["status"])
        self.assertIn("select_exception", data["rules"][0]["configuration"])

        rule_file = self._wall_furniture_rule_file()
        rule_file.contains[0].select_exception = BooleanLeaf(
            Intersection(None, None, 0.01), "have_result"
        )
        rule_file.run()
        data = self._save(rule_file)

        # The invalidated result is still exported, with status False.
        results = data["rules"][0]["results"]
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["status"])
        self.assertIn("global_id", results[0]["source"])
        self.assertEqual(results[0]["target"]["model"], self.model_name)

    def test_must_rule_verdicts(self):
        # A Must check consumes the individual results: the results of
        # the rule become one ClashResultComplex per group, passing or
        # failing as a whole.
        rule_file = self._wall_furniture_rule_file()
        rule_file.contains[0].abs_or_rel_check = AbsoluteOrRelativeChecking(
            "Absolute_Number"
        )
        rule_file.contains[0].abs_or_rel_check.operation = "TARGET>=1"
        rule_file.run()
        data = self._save(rule_file)

        rule = data["rules"][0]
        self.assertEqual(len(rule["results"]), 1)
        verdict = rule["results"][0]
        self.assertTrue(verdict["status"])
        # The complex result carries the two sets of the group.
        self.assertGreater(len(verdict["sources"]), 0)
        self.assertGreater(len(verdict["targets"]), 0)
        self.assertEqual(verdict["sources"][0]["model"], self.model_name)
        # The groups are exported with their element sets.
        self.assertIn("grouped", rule)
        # The per-rule configuration carries the Must check.
        check = rule["configuration"]["abs_or_rel_check"]
        self.assertEqual(check["check_type"], "Absolute_Number")
        self.assertEqual(check["operation"], "TARGET>=1")

        # The same check failing: the group has 1 target, TARGET>=2 is
        # False, the verdict of the group is False.
        rule_file = self._wall_furniture_rule_file()
        rule_file.contains[0].abs_or_rel_check = AbsoluteOrRelativeChecking(
            "Absolute_Number"
        )
        rule_file.contains[0].abs_or_rel_check.operation = "TARGET>=2"
        rule_file.run()
        data = self._save(rule_file)

        verdict = data["rules"][0]["results"][0]
        self.assertFalse(verdict["status"])
        self.assertGreater(len(verdict["targets"]), 0)

    def test_criticity_and_actor_are_exported(self):
        rule_file = self._wall_furniture_rule_file()
        rule = rule_file.contains[0]

        criticity_select = SelectFacet()
        criticity_select.classification_name = "High"
        criticity_select.applicability = [ids.Entity(name="IFCWALLSTANDARDCASE")]
        rule.select_criticity = [criticity_select]

        actor_select = SelectFacet()
        actor_select.classification_name = "Architect"
        actor_select.applicability = [ids.Entity(name="IFCWALLSTANDARDCASE")]
        rule.select_actor = [actor_select]

        rule_file.run()
        data = self._save(rule_file)

        result = data["rules"][0]["results"][0]
        # The source (a wall) is classified, the target (furniture) is not.
        self.assertEqual(result["criticity"], ["High"])
        self.assertEqual(result["actor"], ["Architect"])
        # The classifications are part of the per-rule configuration.
        configuration = data["rules"][0]["configuration"]
        self.assertEqual(len(configuration["select_criticity"]), 1)
        self.assertEqual(len(configuration["select_actor"]), 1)

    def test_results_to_json_before_run(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]

        data = results_to_json(rule_file)

        self.assertEqual(data["rules"], [])
        self.assertEqual(
            data["models"], [{"name": self.model_name, "path": self.ifc_path}]
        )


if __name__ == "__main__":
    unittest.main()
