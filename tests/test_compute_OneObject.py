"""The compute contract of the first migrated one-object rules
(SPEC Separation moteur/gestion): Volume, Area, TopOrBottomSurface
and Orientation, tested directly — lists of entities and named
parameters in, raw results out — no RuleFile, no Select, no
pipeline, no IFC loading inside the rule.

The reference object is CubeB of the cube model: a 1 m cube
(volume 1 m3, area 6 m2, top face 1 m2) whose OBB "Wide" main
direction is (0, -1, 0) — 90 deg from the vertical axis.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_OneObject.py -v
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell

from registry import compute_from_config, engine_params
from Rules import Area, Orientation, TopOrBottomSurface, Volume
from RuleClass import ClashResultOneObject
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape

MODEL = "IFC_Test_Model/IFC_Model/CubeA_Above_CubeB_1m.ifc"


class TestComputeOneObject(unittest.TestCase):
    """The compute contract: entities + named parameters."""

    @classmethod
    def setUpClass(cls):
        # ifcopenshell 0.9: an entity does not keep its file alive,
        # the opened file is cached next to its elements.
        cls.file = ifcopenshell.open(MODEL)

    def _cube(self):
        matches = [e for e in self.file.by_type("IfcProduct") if e.Name == "CubeB"]
        self.assertTrue(matches, "no element named CubeB")
        return [matches[0]]

    def test_volume_within_bounds(self):
        rule = Volume(None, 0.5, 1.5)
        results = rule.compute(self._cube(), 0.5, 1.5)
        self.assertEqual(len(results), 1)
        self.assertIsInstance(results[0], ClashResultOneObject)
        self.assertTrue(results[0].status)
        self.assertAlmostEqual(results[0].info.volume, 1.0, delta=0.05)

    def test_volume_out_of_bounds(self):
        rule = Volume(None, 0.0, 0.5)
        results = rule.compute(self._cube(), 0.0, 0.5)
        self.assertEqual(results, [])

    def test_area_within_bounds(self):
        rule = Area(None, 5.5, 6.5)
        results = rule.compute(self._cube(), 5.5, 6.5)
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].info.area, 6.0, delta=0.1)

    def test_area_out_of_bounds(self):
        rule = Area(None, 0.0, 5.0)
        results = rule.compute(self._cube(), 0.0, 5.0)
        self.assertEqual(results, [])

    def test_top_surface_within_bounds(self):
        rule = TopOrBottomSurface(None, 0.5, 1.5, "Top")
        results = rule.compute(self._cube(), 0.5, 1.5, "Top")
        self.assertEqual(len(results), 1)
        info = results[0].info

        # The measured top surface of the 1 m cube.
        self.assertAlmostEqual(info.area, 1.0, delta=0.05)

        # The extreme faces, triangulated and self-paired (a
        # one-object rule pairs each face with itself).
        self.assertTrue(info.source_faces)
        self.assertEqual(
            [e.number for e in info.source_faces],
            [e.number for e in info.target_faces],
        )
        for entry in info.source_faces:
            self.assertTrue(entry.face.triangles, "the faces must be triangulated")

        self.assertEqual(info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_bottom_surface_within_bounds(self):
        rule = TopOrBottomSurface(None, 0.5, 1.5, "Bottom")
        results = rule.compute(self._cube(), 0.5, 1.5, "Bottom")
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].info.area, 1.0, delta=0.05)

    def test_surface_out_of_bounds(self):
        rule = TopOrBottomSurface(None, 0.5, 1.5, "Top")
        results = rule.compute(self._cube(), 0.0, 0.5, "Top")
        self.assertEqual(results, [])

    def test_orientation_perpendicular(self):
        # The OBB "Wide" main direction of the cube is (0, -1, 0):
        # 90 deg from the vertical, perpendicular within 0.1 rad.
        rule = Orientation(None, (0, 0, 1), "Perpendicular", "Wide")
        results = rule.compute(
            self._cube(), (0, 0, 1), "Perpendicular", "Wide", 0.1
        )
        self.assertEqual(len(results), 1)
        info = results[0].info

        # The measured angle between the OBB direction and the
        # expected orientation, in degrees.
        self.assertAlmostEqual(info.angle, 90.0, delta=1.0)

        # The two axes of the check, at the geometry center.
        labels = [axis.label for axis in info.axes]
        self.assertEqual(labels, ["obb", "expected"])
        self.assertAlmostEqual(info.axes[0].direction[2], 0.0, delta=0.01)
        self.assertAlmostEqual(info.axes[1].direction[2], 1.0, delta=0.01)

        self.assertEqual(info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_orientation_parrallel_fails(self):
        rule = Orientation(None, (0, 0, 1), "Parrallel", "Wide")
        results = rule.compute(
            self._cube(), (0, 0, 1), "Parrallel", "Wide", 0.1
        )
        self.assertEqual(results, [])

    def test_compute_is_pure_of_management_and_display(self):
        rule = Volume(None, 0.5, 1.5)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = rule.compute(self._cube(), 0.5, 1.5)

        self.assertEqual(len(results), 1)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)

    def test_element_without_geometry_is_skipped(self):
        storey = [e for e in self.file.by_type("IfcProduct") if e.Name == "My Storey"]
        rule = Volume(None, 0.5, 1.5)
        self.assertEqual(rule.compute(storey, 0.5, 1.5), [])


class TestComputeOneObjectDispatch(unittest.TestCase):
    """The flat JSON declarations drive the computes through the
    registry dispatch."""

    @classmethod
    def setUpClass(cls):
        cls.file = ifcopenshell.open(MODEL)

    def _cube(self):
        return [[e for e in self.file.by_type("IfcProduct") if e.Name == "CubeB"][0]]

    def test_engine_params(self):
        self.assertEqual(engine_params("Volume"), ["volume_min", "volume_max"])
        self.assertEqual(engine_params("Area"), ["volume_min", "volume_max"])
        self.assertEqual(
            engine_params("TopOrBottomSurface"),
            ["surface_min", "surface_max", "top_or_bot_method"],
        )
        self.assertEqual(
            engine_params("Orientation"),
            ["orientation", "orientation_type", "direction_method", "angular_tolerance"],
        )

    def test_declaration_drives_volume(self):
        rule = Volume(None, 0.5, 1.5)
        config = json.loads(json.dumps(serialize_rule_check(rule)))
        results = compute_from_config(config, self._cube())
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].info.volume, 1.0, delta=0.05)


if __name__ == "__main__":
    unittest.main()
