"""OBB_Above.compute() and OBB_Below.compute() tested directly (SPEC
Separation moteur/gestion): lists of entities and named parameters
in, raw results out — no RuleFile, no Select, no pipeline, no IFC
loading inside the rule.

The two rules share one engine (_compute_obb_zone_penetration): they
differ only by the side of the extrusion of the detection zone. The
semantic cases mirror TestOBB_Above / TestOBB_Below of
test_Rule_IFC_Test_Model.py (the adapter stays covered there).

The zone of OBB_Above(CubeB, CubeA, 1.0) on the cube model: CubeB
top z=0.5, zone up to 1.5, CubeA starts at 1.5 — tolerance 1.0
covers it, 0.1 is too short. A tolerance BELOW the gap detects
nothing: the rule flags a target penetrating the band, NOT a target
farther than the band (see Rapport.md §2, OBB_Above).

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_OBB_Above_Below.py -v
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell
from ifctester import ids

from registry import compute_from_config, engine_params
from Rules import OBB_Above, OBB_Below
from RuleClass import ClashResultTwoObjects, RuleFile, SelectFacet
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape

MODEL_DIR = "IFC_Test_Model/IFC_Model"


class TestComputeOBBZone(unittest.TestCase):
    """The compute contract of the two OBB zone rules."""

    def setUp(self):
        self.files = {}

    def _element(self, model, name):
        if model not in self.files:
            self.files[model] = ifcopenshell.open(os.path.join(MODEL_DIR, model))
        file = self.files[model]
        matches = [e for e in file.by_type("IfcProduct") if e.Name == name]
        self.assertTrue(matches, f"{model}: no element named {name!r}")
        return matches[0]

    def _compute(self, rule, model, source, target, tolerance):
        sources = [self._element(model, source)]
        targets = [self._element(model, target)]
        return rule.compute(sources, targets, tolerance)

    def test_obb_above_within_band(self):
        rule = OBB_Above(None, None, 1.0)
        results = self._compute(rule, "CubeA_Above_CubeB_1m.ifc", "CubeB", "CubeA", 1.0)
        self.assertEqual(len(results), 1)

    def test_obb_above_too_short_band(self):
        # The band stops at z=1.4, CubeA starts at 1.5: nothing.
        rule = OBB_Above(None, None, 0.1)
        results = self._compute(rule, "CubeA_Above_CubeB_1m.ifc", "CubeB", "CubeA", 0.1)
        self.assertEqual(results, [])

    def test_obb_below_within_band(self):
        rule = OBB_Below(None, None, 1.0)
        results = self._compute(rule, "CubeA_Below_CubeB_1m.ifc", "CubeB", "CubeA", 1.0)
        self.assertEqual(len(results), 1)

    def test_obb_below_too_short_band(self):
        rule = OBB_Below(None, None, 0.1)
        results = self._compute(rule, "CubeA_Below_CubeB_1m.ifc", "CubeB", "CubeA", 0.1)
        self.assertEqual(results, [])

    def test_result_type_and_pair(self):
        rule = OBB_Above(None, None, 1.0)
        results = self._compute(rule, "CubeA_Above_CubeB_1m.ifc", "CubeB", "CubeA", 1.0)
        result = results[0]
        self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertTrue(result.status)
        self.assertEqual(result.source.Name, "CubeB")
        self.assertEqual(result.target.Name, "CubeA")

    def test_info_blocks_of_a_verdict(self):
        """The verdict carries its display data: the measured distance
        and the OBBs of the pair — the source detection zone and
        object, the target object."""
        rule = OBB_Above(None, None, 1.0)
        results = self._compute(rule, "CubeA_Above_CubeB_1m.ifc", "CubeB", "CubeA", 1.0)
        info = results[0].info

        # The target touches the zone: the measured distance is zero.
        self.assertIsNotNone(info.distance)
        self.assertLessEqual(info.distance, 1e-6)

        # The OBBs: zone + object on the source side, object on the
        # target side.
        source_labels = {obb.label for obb in info.source_obbs}
        target_labels = {obb.label for obb in info.target_obbs}
        self.assertEqual(source_labels, {"object", "zone"})
        self.assertEqual(target_labels, {"object"})
        zone_obbs = [obb for obb in info.source_obbs if obb.label == "zone"]
        self.assertEqual(len(zone_obbs), 1)
        # The zone is the band DETACHED above the source: its height
        # is the tolerance (half size 0.5 for a 1.0 band) and its
        # center sits above the center of the source object OBB.
        object_obbs = [obb for obb in info.source_obbs if obb.label == "object"]
        self.assertAlmostEqual(zone_obbs[0].half_sizes[2], 0.5, delta=0.01)
        self.assertGreater(zone_obbs[0].center[2], object_obbs[0].center[2])

        # The whole contract: exportable and faultless.
        self.assertEqual(info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_compute_is_pure_of_management_and_display(self):
        rule = OBB_Above(None, None, 1.0)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = self._compute(rule, "CubeA_Above_CubeB_1m.ifc", "CubeB", "CubeA", 1.0)

        self.assertEqual(len(results), 1)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)

    def test_element_without_geometry_is_skipped(self):
        rule = OBB_Above(None, None, 1.0)
        sources = [self._element("CubeA_Above_CubeB_1m.ifc", "My Storey")]
        targets = [self._element("CubeA_Above_CubeB_1m.ifc", "CubeA")]
        self.assertEqual(rule.compute(sources, targets, 1.0), [])

    def test_display_states_emit_all_zone_geometries(self):
        """Display_Input: the detection zone of EVERY source comes out
        and the result list does not (the engine is not run).
        Display_Result: every zone AND the results. One item per
        source, on both rules (the side only flips the extrusion)."""
        for rule_class, model in (
            (OBB_Above, "CubeA_Above_CubeB_1m.ifc"),
            (OBB_Below, "CubeA_Below_CubeB_1m.ifc"),
        ):
            sources = [self._element(model, "CubeB")]
            targets = [self._element(model, "CubeA")]

            rule = rule_class(None, None, 1.0, state="Display_Input")
            results = rule.compute(sources, targets, 1.0)
            self.assertEqual(results, [])
            self.assertEqual(len(rule.display_items), 1)
            item = rule.display_items[0]
            self.assertEqual(item.category, "obb")
            self.assertEqual(item.color, (0.5, 0, 1))
            self.assertAlmostEqual(item.transparency, 0.2)
            self.assertEqual(item.element.Name, "CubeB")

            rule = rule_class(None, None, 1.0, state="Display_Result")
            results = rule.compute(sources, targets, 1.0)
            self.assertEqual(len(results), 1)
            self.assertEqual(len(rule.display_items), 1)


class TestComputeOBBZoneDispatch(unittest.TestCase):
    """The flat JSON declarations drive the computes through the
    registry dispatch."""

    @classmethod
    def setUpClass(cls):
        # ifcopenshell 0.9: an entity does not keep its file alive,
        # the opened files are cached next to their elements.
        cls.files = {}

    @staticmethod
    def _select(name):
        select = SelectFacet()
        select.applicability = [ids.Attribute(name="Name", value=name)]
        return select

    def _elements(self, model, *names):
        """One LIST of one entity per name: the compute contract
        takes entity lists, not single entities."""
        if model not in self.files:
            self.files[model] = ifcopenshell.open(os.path.join(MODEL_DIR, model))
        file = self.files[model]
        found = []
        for name in names:
            matches = [e for e in file.by_type("IfcProduct") if e.Name == name]
            assert matches, f"{model}: no element named {name!r}"
            found.append([matches[0]])
        return found

    def test_engine_params(self):
        self.assertEqual(engine_params("OBB_Above"), ["tolerance"])
        self.assertEqual(engine_params("OBB_Below"), ["tolerance"])

    def test_declaration_drives_obb_above(self):
        rule = OBB_Above(self._select("CubeB"), self._select("CubeA"), 1.0)
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        sources, targets = self._elements("CubeA_Above_CubeB_1m.ifc", "CubeB", "CubeA")
        results = compute_from_config(config, sources, targets)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source.Name, "CubeB")
        self.assertEqual(results[0].target.Name, "CubeA")

    def test_declaration_drives_obb_below(self):
        rule = OBB_Below(self._select("CubeB"), self._select("CubeA"), 1.0)
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        sources, targets = self._elements("CubeA_Below_CubeB_1m.ifc", "CubeB", "CubeA")
        results = compute_from_config(config, sources, targets)
        self.assertEqual(len(results), 1)


class TestComputeOBBZoneThroughAdapter(unittest.TestCase):
    """The migration adapter (run + RuleFile) produces the RuleOutput
    of the pipeline (SPEC): one integration node per rule."""

    @staticmethod
    def _select(name):
        select = SelectFacet()
        select.applicability = [ids.Attribute(name="Name", value=name)]
        return select

    def test_rule_output_after_rule_file_run(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [os.path.join(MODEL_DIR, "CubeA_Above_CubeB_1m.ifc")]
        rule = OBB_Above(self._select("CubeB"), self._select("CubeA"), 1.0)
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        self.assertEqual(len(rule.result), 1)
        self.assertIsNotNone(rule.output)
        self.assertIs(rule.output.results, rule.result)


if __name__ == "__main__":
    unittest.main()
