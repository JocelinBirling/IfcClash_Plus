"""The compute contract of Intersection2 (SPEC Separation moteur/
gestion), tested directly — entity lists and named parameters in, raw
results out.

Intersection2 is the PURE PythonOCC alternative engine to Intersection
(no ifcopenshell BVH tree): the element meshes are sewn into solids
(clash_utils.mesh_to_solid), the pairs are guarded by a bounding-box
prefilter, then an exact OCCT boolean common flags the pairs with a
strictly positive overlap volume. The tolerance is the MINIMUM
OVERLAP VOLUME (m3), 0.0 = any positive overlap.

Calibrated on IFC_Test_Model/IFC_Model — the detection matches the
Intersection tree on every model, and fixes its two documented bugs:
the 1mm penetration IS flagged (the tree misses it, Rapport.md) and
the perfect-coincidence pair IS flagged (the tree misses it). A pure
face contact (no volume) is not flagged.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_Intersection2.py -v
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell

from Rules import Intersection2
from RuleClass import SelectFacet, RuleFile, ClashResultTwoObjects
from registry import compute_from_config, engine_params
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape

MODEL_DIR = "IFC_Test_Model/IFC_Model"


def select_by_name(name):
    from ifctester import ids

    select = SelectFacet()
    select.applicability = [ids.Attribute(name="Name", value=name)]
    return select


class TestComputeIntersection2(unittest.TestCase):
    """The compute contract of Intersection2: two lists + the named
    parameters (the tolerance is a minimum overlap volume in m3)."""

    @classmethod
    def setUpClass(cls):
        cls.models = {
            "overlap10": "CubeA_Intersect_CubeB_10cm.ifc",
            "overlap1mm": "CubeA_Intersect_CubeB_1mm.ifc",
            "touchface": "CubeA_TouchFace_CubeB.ifc",
            "sameplace": "CubeA_SamePlace_CubeB.ifc",
            "cylinderslab": "CylinderA_Intersect_SlabA.ifc",
            "inside": "CubeA_Inside_BigCubeA.ifc",
        }
        # ifcopenshell 0.9: an entity does not keep its file alive.
        cls.files = {
            key: ifcopenshell.open(os.path.join(MODEL_DIR, model))
            for key, model in cls.models.items()
        }

    @classmethod
    def tearDownClass(cls):
        cls.files.clear()

    def _element(self, key, name):
        matches = [
            e for e in self.files[key].by_type("IfcProduct") if e.Name == name
        ]
        self.assertTrue(matches, f"no element named {name!r} in {key}")
        return matches[0]

    def _compute(self, key, source, target, tolerance=0.0):
        rule = Intersection2(None, None)
        return rule.compute(
            [self._element(key, source)],
            [self._element(key, target)],
            tolerance,
        )

    def test_volumetric_overlap_detected(self):
        """A 0.1 m corner overlap: one verdict carrying the overlap
        volume (nominal), the zero distance and the overlap center."""
        results = self._compute("overlap10", "CubeA", "CubeB")
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertTrue(result.status)
        self.assertEqual(result.source.Name, "CubeA")
        self.assertEqual(result.target.Name, "CubeB")

        info = result.info
        # The common of the two cubes: a 0.1 x 0.1 x 0.1 corner.
        self.assertAlmostEqual(info.volume, 0.001, delta=1e-4)
        self.assertEqual(info.volume_intersection, info.volume)
        self.assertEqual(info.distance, 0.0)
        # The center of the overlap, as a labeled point pair.
        self.assertEqual(len(info.source_points), 1)
        self.assertEqual(info.source_points[0].label, "overlap_center")
        self.assertAlmostEqual(
            info.source_points[0].point[0], 0.45, delta=0.01
        )

        self.assertEqual(info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_1mm_penetration_detected(self):
        """A 1mm corner penetration: a tiny but positive overlap
        volume — the BVH tree of Intersection MISSES this pair
        (documented, Rapport.md), the PythonOCC engine flags it."""
        results = self._compute("overlap1mm", "CubeA", "CubeB")
        self.assertEqual(len(results), 1)
        volume = results[0].info.volume
        self.assertGreater(volume, 0.0)
        self.assertLess(volume, 1e-6)

    def test_face_contact_no_result(self):
        """Two cubes touching by a face: no overlap volume, no
        verdict (the tree agrees)."""
        results = self._compute("touchface", "CubeA", "CubeB")
        self.assertEqual(results, [])

    def test_perfect_coincidence_detected(self):
        """Two exactly overlapping cubes: the full common volume —
        the BVH tree MISSES this pair, the PythonOCC engine flags
        it."""
        results = self._compute("sameplace", "CubeA", "CubeB")
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].info.volume, 1.0, delta=1e-3)

    def test_cylinder_and_slab(self):
        """A cylinder crossing a slab: a positive overlap volume."""
        results = self._compute("cylinderslab", "CylinderA", "SlabA")
        self.assertEqual(len(results), 1)
        self.assertGreater(results[0].info.volume, 0.3)
        self.assertEqual(results[0].info.validate(), [])

    def test_containment_detected(self):
        """A cube fully inside a bigger cube: the common volume is
        the volume of the small cube."""
        results = self._compute("inside", "CubeA", "BigCubeA")
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].info.volume, 1.0, delta=1e-3)

    def test_tolerance_is_a_minimum_overlap_volume(self):
        """The tolerance (m3) filters the negligible overlaps: a
        0.001 m3 overlap passes a 0.0 threshold, not a 0.5 one; the
        1.0 m3 containment passes both."""
        self.assertEqual(len(self._compute("overlap10", "CubeA", "CubeB", 0.0)), 1)
        self.assertEqual(len(self._compute("overlap10", "CubeA", "CubeB", 0.5)), 0)
        self.assertEqual(len(self._compute("inside", "CubeA", "BigCubeA", 0.5)), 1)

    def test_compute_is_pure_of_management_and_display(self):
        rule = Intersection2(None, None)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = self._compute("overlap10", "CubeA", "CubeB")

        self.assertEqual(len(results), 1)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)

    def test_element_without_geometry_is_skipped(self):
        rule = Intersection2(None, None)
        project = self.files["overlap10"].by_type("IfcProject")[0]
        results = rule.compute(
            [project],
            [self._element("overlap10", "CubeB")],
            0.0,
        )
        self.assertEqual(results, [])


class TestComputeIntersection2Dispatch(unittest.TestCase):
    """The flat JSON declarations drive the compute through the
    registry dispatch."""

    def test_engine_params(self):
        self.assertEqual(engine_params("Intersection2"), ["tolerance"])

    def test_declaration_drives_the_compute(self):
        file = ifcopenshell.open(
            os.path.join(MODEL_DIR, "CubeA_Intersect_CubeB_10cm.ifc")
        )
        elements = {e.Name: e for e in file.by_type("IfcProduct")}

        rule = Intersection2(select_by_name("CubeA"), select_by_name("CubeB"))
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        results = compute_from_config(config, [elements["CubeA"]], [elements["CubeB"]])
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].info.volume, 0.001, delta=1e-4)


class TestComputeIntersection2ThroughAdapter(unittest.TestCase):
    """The migration adapter (run + RuleFile) produces the RuleOutput
    of the pipeline (SPEC): one integration node."""

    def test_rule_output_after_rule_file_run(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [
            os.path.join(MODEL_DIR, "CubeA_Intersect_CubeB_10cm.ifc")
        ]
        rule = Intersection2(select_by_name("CubeA"), select_by_name("CubeB"))
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        self.assertEqual(len(rule.result), 1)
        self.assertIsNotNone(rule.output)
        self.assertIs(rule.output.results, rule.result)


if __name__ == "__main__":
    unittest.main()
