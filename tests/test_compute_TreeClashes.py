"""The compute contract of the BVH tree rules (SPEC Separation
moteur/gestion): Intersection, Clearance and Collision, tested
directly — lists of entities and named parameters in, raw results
out — no RuleFile, no Select, no pipeline, no IFC loading inside
the rule.

The clash tree (opencascade.trianglebvh, ifcopenshell 0.9) is built
by the engine itself at each compute, fed with the two entity lists.
Each verdict carries the distance and the contact point pair of the
tree in its info blocks, with the source/target sides restored.

Calibrated cases (see test_Rule_IFC_Test_Model.py):
- CubeA_Intersect_CubeB_10cm: a true volumetric intersection;
- CubeA_Intersect_CubeB_1mm: only Collision sees the 1 mm penetration
  (the Intersection blindness is a documented bug);
- UshapeA_NoTouch_CubeB: actual distance 0.5 m.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_TreeClashes.py -v
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell

from registry import compute_from_config, engine_params
from Rules import Clearance, Collision, Intersection
from RuleClass import ClashResultTwoObjects, RuleFile, SelectFacet
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape

MODEL_DIR = "IFC_Test_Model/IFC_Model"


class TestComputeTreeClashes(unittest.TestCase):
    """The compute contract: entities + named parameters."""

    @classmethod
    def setUpClass(cls):
        # ifcopenshell 0.9: an entity does not keep its file alive,
        # the opened files are cached next to their elements.
        cls.files = {}

    def _elements(self, model, *names):
        if model not in self.files:
            self.files[model] = ifcopenshell.open(os.path.join(MODEL_DIR, model))
        file = self.files[model]
        found = []
        for name in names:
            matches = [e for e in file.by_type("IfcProduct") if e.Name == name]
            assert matches, f"{model}: no element named {name!r}"
            found.append(matches[0])
        return found

    def test_intersection_detected(self):
        rule = Intersection(None, None)
        sources, targets = self._elements("CubeA_Intersect_CubeB_10cm.ifc", "CubeA", "CubeB")
        results = rule.compute([sources], [targets], 0.1)

        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertTrue(result.status)
        # The tree mixes the sides: the compute restores them.
        self.assertEqual(result.source.Name, "CubeA")
        self.assertEqual(result.target.Name, "CubeB")

    def test_intersection_blind_to_1mm(self):
        # [calibrated bug] the 1 mm penetration is not seen by the
        # tree intersection query (Collision sees it).
        rule = Intersection(None, None)
        sources, targets = self._elements("CubeA_Intersect_CubeB_1mm.ifc", "CubeA", "CubeB")
        self.assertEqual(rule.compute([sources], [targets], 0.1), [])

    def test_collision_sees_1mm(self):
        rule = Collision(None, None)
        sources, targets = self._elements("CubeA_Intersect_CubeB_1mm.ifc", "CubeA", "CubeB")
        results = rule.compute([sources], [targets], False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source.Name, "CubeA")
        self.assertEqual(results[0].target.Name, "CubeB")

    def test_clearance_violation_and_respect(self):
        rule = Clearance(None, None)
        sources, targets = self._elements("UshapeA_NoTouch_CubeB.ifc", "UshapeA", "CubeB")
        # Actual distance 0.5 m: 1 mm of required clearance is fine.
        self.assertEqual(rule.compute([sources], [targets], 0.001), [])
        # 1 m of required clearance is violated.
        results = rule.compute([sources], [targets], 1.0)
        self.assertEqual(len(results), 1)

    def test_info_blocks_of_a_verdict(self):
        """The verdict carries the distance and the contact point pair
        of the tree, sides restored (the points follow the source and
        the target)."""
        rule = Intersection(None, None)
        sources, targets = self._elements("CubeA_Intersect_CubeB_10cm.ifc", "CubeA", "CubeB")
        results = rule.compute([sources], [targets], 0.1)

        info = results[0].info
        self.assertIsNotNone(info.distance)
        self.assertEqual(len(info.source_points), 1)
        self.assertEqual(len(info.target_points), 1)
        self.assertEqual(info.source_points[0].number, info.target_points[0].number)
        for entry in info.source_points + info.target_points:
            self.assertEqual(len(entry.point), 3)

        self.assertEqual(info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_compute_is_pure_of_management_and_display(self):
        rule = Clearance(None, None)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        sources, targets = self._elements(
            "CubeA_Intersect_CubeB_10cm.ifc", "CubeA", "CubeB"
        )
        results = rule.compute([sources], [targets], 0.05)

        self.assertEqual(len(results), 1)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)

    def test_element_without_geometry_is_skipped(self):
        rule = Collision(None, None)
        sources, targets = self._elements(
            "CubeA_Intersect_CubeB_10cm.ifc", "My Storey", "CubeB"
        )
        self.assertEqual(rule.compute([sources], [targets], False), [])


class TestComputeTreeClashesDispatch(unittest.TestCase):
    """The flat JSON declarations drive the computes through the
    registry dispatch."""

    @staticmethod
    def _select(name):
        from ifctester import ids

        select = SelectFacet()
        select.applicability = [ids.Attribute(name="Name", value=name)]
        return select

    def test_engine_params(self):
        self.assertEqual(engine_params("Intersection"), ["tolerance"])
        self.assertEqual(engine_params("Clearance"), ["clearance", "check_all"])
        self.assertEqual(engine_params("Collision"), ["allow_touching"])

    def test_declaration_drives_collision(self):
        file = ifcopenshell.open(os.path.join(MODEL_DIR, "CubeA_Intersect_CubeB_1mm.ifc"))
        rule = Collision(self._select("CubeA"), self._select("CubeB"), False)
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        sources = [[e for e in file.by_type("IfcProduct") if e.Name == "CubeA"][0]]
        targets = [[e for e in file.by_type("IfcProduct") if e.Name == "CubeB"][0]]
        results = compute_from_config(config, sources, targets)
        self.assertEqual(len(results), 1)


class TestComputeTreeClashesThroughAdapter(unittest.TestCase):
    """The migration adapter (run + RuleFile) produces the RuleOutput
    of the pipeline (SPEC): one integration node."""

    def test_rule_output_after_rule_file_run(self):
        from ifctester import ids

        def select(name):
            s = SelectFacet()
            s.applicability = [ids.Attribute(name="Name", value=name)]
            return s

        rule_file = RuleFile()
        rule_file.list_ifc_path = [
            os.path.join(MODEL_DIR, "CubeA_Intersect_CubeB_10cm.ifc")
        ]
        rule = Intersection(select("CubeA"), select("CubeB"), 0.1)
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        self.assertEqual(len(rule.result), 1)
        self.assertIsNotNone(rule.output)
        self.assertIs(rule.output.results, rule.result)


if __name__ == "__main__":
    unittest.main()
