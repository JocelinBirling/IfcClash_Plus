"""The registry dispatch (SPEC Separation moteur/gestion): one flat
JSON rule declaration — the canonical format of serialize_rule_check,
which gathers everything under one same rule — drives the compute of
the rule.

Arbitration recorded in the SPEC: the JSON declaration stays flat,
one rule object carries the selects, the engine parameters AND the
management configuration at the same level. The engine/management
separation lives in the code only: the dispatch extracts the engine
part and calls compute(), the ResultPipeline reads the management
part.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_registry_dispatch.py -v
"""
import json
import os
import sys
import unittest

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell
from ifctester import ids

from registry import compute_from_config, engine_params
from Rules import Above
from RuleClass import SelectFacet
from serialization import serialize_rule_check

MODEL_DIR = "IFC_Test_Model/IFC_Model"


def _select(name):
    select = SelectFacet()
    select.applicability = [ids.Attribute(name="Name", value=name)]
    return select


class TestEngineParams(unittest.TestCase):
    def test_engine_params_of_above(self):
        """The catalogue declares the engine parameters of a rule:
        the flat keys of its JSON declaration that feed the named
        compute() call."""
        self.assertEqual(engine_params("Above"), ["above_type", "tolerance"])

    def test_unknown_rule_type_raises(self):
        with self.assertRaises(KeyError):
            engine_params("NotARule")


class TestFlatDeclaration(unittest.TestCase):
    """One rule in JSON gathers engine + management + selects, at the
    same level of the flat declaration."""

    def test_flat_declaration_gathers_everything(self):
        rule = Above(_select("CubeB"), _select("CubeA"), "Above_MaxToMin", 1.0)
        rule.select_exception = "Same_IfcSystem"
        rule.select_criticity = [_select("CubeA")]
        rule.select_actor = [_select("CubeB")]

        config = serialize_rule_check(rule)

        # The engine part, the selects and the management
        # configuration: same rule, same level.
        for key in (
            "type",
            "above_type",          # engine
            "tolerance",           # engine
            "select_source",      # input preparation
            "select_target",
            "select_exception",    # management
            "select_criticity",    # management
            "select_actor",        # management
        ):
            self.assertIn(key, config)
        self.assertEqual(config["type"], "Above")

        # The whole declaration is JSON (the on-disk canonical form).
        round_trip = json.loads(json.dumps(config))
        self.assertEqual(round_trip["above_type"], "Above_MaxToMin")


class TestComputeFromConfig(unittest.TestCase):
    """The dispatch: flat declaration -> named compute call."""

    @classmethod
    def setUpClass(cls):
        cls.file = ifcopenshell.open(os.path.join(MODEL_DIR, "CubeA_Above_CubeB_1m.ifc"))

    @staticmethod
    def _element(file, name):
        matches = [e for e in file.by_type("IfcProduct") if e.Name == name]
        assert matches, f"no element named {name!r}"
        return matches[0]

    def test_declaration_drives_the_compute(self):
        rule = Above(_select("CubeB"), _select("CubeA"), "Above_MaxToMin", 1.0)
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        sources = [self._element(self.file, "CubeB")]
        targets = [self._element(self.file, "CubeA")]
        results = compute_from_config(config, sources, targets)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source.Name, "CubeB")
        self.assertEqual(results[0].target.Name, "CubeA")

    def test_declaration_with_management_config_still_computes(self):
        """The management keys of the flat declaration are ignored by
        the dispatch: they belong to the pipeline."""
        rule = Above(_select("CubeB"), _select("CubeA"), "Above_MaxToMin", 1.0)
        rule.select_exception = "Same_IfcSystem"
        rule.select_criticity = [_select("CubeA")]
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        sources = [self._element(self.file, "CubeB")]
        targets = [self._element(self.file, "CubeA")]
        results = compute_from_config(config, sources, targets)
        self.assertEqual(len(results), 1)

    def test_unmigrated_rule_raises(self):
        """A rule type without a compute cannot be dispatched. Every
        rule being migrated at the end of the deployment, a class
        still waiting for its compute is simulated by removing the
        compute of the class for the duration of the call."""
        rule = Above(_select("CubeB"), _select("CubeA"), "Above_MaxToMin", 1.0)
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        compute = Above.compute
        del Above.compute
        try:
            with self.assertRaises(NotImplementedError):
                compute_from_config(
                    config,
                    [self._element(self.file, "CubeB")],
                    [self._element(self.file, "CubeA")],
                )
        finally:
            Above.compute = compute


if __name__ == "__main__":
    unittest.main()
