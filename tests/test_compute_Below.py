"""Below.compute() tested directly (SPEC Separation moteur/gestion):
lists of entities and named parameters in, raw results out — no
RuleFile, no Select, no pipeline, no IFC loading inside the rule.

The semantic cases mirror TestBelow of test_Rule_IFC_Test_Model.py
(the adapter stays covered there); this file covers the engine
contract of the rule: purity, the verdicts and the info blocks, and
the registry dispatch of the flat JSON declaration.

Semantic order: below_type "Below_MinToMax" = bottom face of the
source vs top face of the target (target below the source). The
models of IFC_Test_Model are one shared object set: CubeA sits 1 m
below CubeB (z -0.5-0.5 vs 1.5-2.5), SuzanneA 0.9156 m below SlabA.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_Below.py -v
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell
from ifctester import ids

from registry import compute_from_config
from Rules import Below
from RuleClass import ClashResultTwoObjects, RuleFile, SelectFacet
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape

MODEL_DIR = "IFC_Test_Model/IFC_Model"


class TestComputeBelow(unittest.TestCase):
    """The compute contract of Below: entities + named parameters."""

    def setUp(self):
        self.rule = Below(None, None, "Below_MinToMax")
        self.files = {}

    def _element(self, model, name):
        if model not in self.files:
            self.files[model] = ifcopenshell.open(os.path.join(MODEL_DIR, model))
        file = self.files[model]
        matches = [e for e in file.by_type("IfcProduct") if e.Name == name]
        self.assertTrue(matches, f"{model}: no element named {name!r}")
        return matches[0]

    def _compute(self, model, source, target, below_type="Below_MinToMax", tolerance=1.0):
        sources = [self._element(model, source)]
        targets = [self._element(model, target)]
        return self.rule.compute(sources, targets, below_type, tolerance)

    def test_cube_below_within_tolerance(self):
        results = self._compute("CubeA_Below_CubeB_1m.ifc", "CubeB", "CubeA", tolerance=1.0)
        self.assertEqual(len(results), 1)

    def test_cube_below_too_far(self):
        # The face-to-face gap is 1.0 m: 0.1 is too short.
        results = self._compute("CubeA_Below_CubeB_1m.ifc", "CubeB", "CubeA", tolerance=0.1)
        self.assertEqual(results, [])

    def test_suzanne_below_slab(self):
        # Min distance 0.9156 m between the extrem faces.
        results = self._compute("SuzanneA_Below_SlabA.ifc", "SlabA", "SuzanneA", tolerance=1.0)
        self.assertEqual(len(results), 1)

    def test_result_type_and_pair(self):
        results = self._compute("CubeA_Below_CubeB_1m.ifc", "CubeB", "CubeA", tolerance=1.0)
        result = results[0]
        self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertTrue(result.status)
        self.assertEqual(result.source.Name, "CubeB")
        self.assertEqual(result.target.Name, "CubeA")

    def test_info_blocks_of_a_verdict(self):
        """The verdict carries its display data: the measured
        distance, the point pair, the triangulated extrem face pair
        and the OBBs (object + detection zone on the source side)."""
        results = self._compute("CubeA_Below_CubeB_1m.ifc", "CubeB", "CubeA", tolerance=1.0)
        info = results[0].info

        # The nominal measure: the distance of the verdict pair.
        self.assertIsNotNone(info.distance)
        self.assertAlmostEqual(info.distance, 1.0, delta=0.05)

        # The point pair of the verdict.
        self.assertEqual(len(info.source_points), 1)
        self.assertEqual(len(info.target_points), 1)
        self.assertEqual(info.source_points[0].number, info.target_points[0].number)

        # The extrem face pair, triangulated. Below_MinToMax looks at
        # the BOTTOM faces of the source: their normals point down.
        self.assertTrue(info.source_faces)
        self.assertTrue(info.target_faces)
        self.assertEqual(info.source_faces[0].number, info.target_faces[0].number)
        for entry in info.source_faces + info.target_faces:
            self.assertGreater(entry.face.area, 0.0)
            self.assertTrue(entry.face.triangles, "the faces must be triangulated")
        source_normal = info.source_faces[0].face.normal
        self.assertAlmostEqual(source_normal[2], -1.0, delta=0.01)

        # The OBBs of the two elements, the source zone included.
        source_labels = {obb.label for obb in info.source_obbs}
        target_labels = {obb.label for obb in info.target_obbs}
        self.assertEqual(source_labels, {"object", "zone"})
        self.assertEqual(target_labels, {"object"})

        # The whole contract: exportable and faultless.
        self.assertEqual(info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_compute_is_pure_of_management_and_display(self):
        """compute returns its results: rule.result, the display
        registry and rule.output stay untouched."""
        self.rule.result.append("sentinel")
        self.rule.display_items.append("sentinel")

        results = self._compute("CubeA_Below_CubeB_1m.ifc", "CubeB", "CubeA", tolerance=1.0)

        self.assertEqual(len(results), 1)
        self.assertEqual(self.rule.result, ["sentinel"])
        self.assertEqual(self.rule.display_items, ["sentinel"])
        self.assertIsNone(self.rule.output)

    def test_sources_and_targets_from_several_files(self):
        """One flat list of entities can span several files: compute
        groups them per file (entity.file) and pairs across the
        files. The same model opened twice gives two file objects at
        the same coordinates: the target is found once per file."""
        path = os.path.join(MODEL_DIR, "CubeA_Below_CubeB_1m.ifc")
        file_a = ifcopenshell.open(path)
        file_b = ifcopenshell.open(path)
        self.assertIsNot(file_a, file_b)

        sources = [
            [e for e in file_a.by_type("IfcProduct") if e.Name == "CubeB"][0]
        ]
        targets = [
            [e for e in file_a.by_type("IfcProduct") if e.Name == "CubeA"][0],
            [e for e in file_b.by_type("IfcProduct") if e.Name == "CubeA"][0],
        ]
        results = self.rule.compute(sources, targets, "Below_MinToMax", 1.0)

        self.assertEqual(len(results), 2)
        target_files = {result.target.file for result in results}
        self.assertEqual(target_files, {file_a, file_b})

    def test_element_without_geometry_is_skipped(self):
        """The spatial structure (a storey) has no own geometry: as
        with the plain-settings iterator, it produces no verdict."""
        sources = [self._element("CubeA_Below_CubeB_1m.ifc", "My Storey")]
        targets = [self._element("CubeA_Below_CubeB_1m.ifc", "CubeA")]
        results = self.rule.compute(sources, targets, "Below_MinToMax", 1.0)
        self.assertEqual(results, [])


class TestComputeBelowDispatch(unittest.TestCase):
    """The flat JSON declaration of Below drives its compute through
    the registry dispatch."""

    def test_declaration_drives_the_compute(self):
        def select(name):
            select = SelectFacet()
            select.applicability = [ids.Attribute(name="Name", value=name)]
            return select

        rule = Below(select("CubeB"), select("CubeA"), "Below_MinToMax", 1.0)
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        file = ifcopenshell.open(os.path.join(MODEL_DIR, "CubeA_Below_CubeB_1m.ifc"))
        sources = [e for e in file.by_type("IfcProduct") if e.Name == "CubeB"]
        targets = [e for e in file.by_type("IfcProduct") if e.Name == "CubeA"]

        results = compute_from_config(config, sources, targets)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source.Name, "CubeB")
        self.assertEqual(results[0].target.Name, "CubeA")


class TestComputeBelowThroughAdapter(unittest.TestCase):
    """The migration adapter (run + RuleFile) produces the
    RuleOutput of the pipeline (SPEC): one integration node."""

    def test_rule_output_after_rule_file_run(self):
        def select(name):
            select = SelectFacet()
            select.applicability = [ids.Attribute(name="Name", value=name)]
            return select

        rule_file = RuleFile()
        rule_file.list_ifc_path = [os.path.join(MODEL_DIR, "CubeA_Below_CubeB_1m.ifc")]
        rule = Below(select("CubeB"), select("CubeA"), "Below_MinToMax", 1.0)
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        self.assertEqual(len(rule.result), 1)
        self.assertIsNotNone(rule.output)
        self.assertIs(rule.output.results, rule.result)
        self.assertEqual(len(rule.output.results), 1)


if __name__ == "__main__":
    unittest.main()
