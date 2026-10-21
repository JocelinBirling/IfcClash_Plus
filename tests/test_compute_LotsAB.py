"""The compute contract of the A/B lots of the migration (SPEC
Separation moteur/gestion), tested directly — entity lists and named
parameters in, raw results out: ObbHigh, ObbLength, LateralSurface,
ProjectedSurface (one-object) and OBB_Front_And_Back (two-objects).

These rules had NO test before their migration: the expectations below
were calibrated empirically on IFC_Test_Model/IFC_Model (the OCCT
defaults leave a small noise on the OBB measures, hence the deltas).
The 45-degree tilted cuboid documents the world-coordinate fix of
LateralSurface/ProjectedSurface (SPEC point 3): its side area toward
+Z is 0 (no face within the cone) while its projected area is the
tilted footprint.

OBB_Front_And_Back keeps its KNOWN DEFECT (Rapport.md): the side
clash of the tilted cuboid is missed — the pre-existing red adapter
test is unchanged, the behavior is preserved as is.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_LotsAB.py -v
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell

from Rules import (
    ObbHigh,
    ObbLength,
    LateralSurface,
    ProjectedSurface,
    OBB_Front_And_Back,
)
from RuleClass import SelectFacet, RuleFile, ClashResultOneObject
from registry import compute_from_config, engine_params
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape

MODEL_DIR = "IFC_Test_Model/IFC_Model"
CUBE_MODEL = os.path.join(MODEL_DIR, "CubeA_NextTo_CubeB_1m.ifc")


def select_by_name(name):
    from ifctester import ids

    select = SelectFacet()
    select.applicability = [ids.Attribute(name="Name", value=name)]
    return select


class _CubeModelMixin(unittest.TestCase):
    """The multi-object cube model: a unit cube, standing and fallen
    cuboids, a thin wall and a 45-degree tilted cuboid."""

    @classmethod
    def setUpClass(cls):
        # ifcopenshell 0.9: an entity does not keep its file alive.
        cls.file = ifcopenshell.open(CUBE_MODEL)

    def _element(self, name):
        matches = [e for e in self.file.by_type("IfcProduct") if e.Name == name]
        self.assertTrue(matches, f"no element named {name!r}")
        return matches[0]


class TestComputeObbHigh(_CubeModelMixin):
    """The compute contract of ObbHigh: the OBB height, measured as
    the Z span of the corners (the OCCT axis order is arbitrary)."""

    def _compute(self, name, length_min, length_max):
        rule = ObbHigh(None, length_min, length_max)
        return rule.compute([self._element(name)], length_min, length_max)

    def test_measured_heights(self):
        """CubeA: 1 m. CuboidA (standing): ~4 m. FallenCuboidA: ~1 m.
        WallA (0.1 m thick, 3 m high): ~3 m."""
        cases = {"CubeA": 1.0, "CuboidA": 4.0, "FallenCuboidA": 1.0, "WallA": 3.0}
        for name, expected in cases.items():
            results = self._compute(name, -1e9, 1e9)
            self.assertEqual(len(results), 1, name)
            result = results[0]
            self.assertIsInstance(result, ClashResultOneObject)
            self.assertEqual(result.source.Name, name)
            self.assertAlmostEqual(result.info.offset, expected, delta=1e-2)
            # The OBB itself travels in the info blocks.
            self.assertEqual(len(result.info.source_obbs), 1)
            self.assertEqual(result.info.source_obbs[0].label, "object")
            self.assertEqual(result.info.validate(), [])
        assert_result_shape(
            SimpleNamespace(result=self._compute("CuboidA", -1e9, 1e9))
        )

    def test_bounds_are_open(self):
        """The bounds are open: 1 m is inside ]0.5, 1.5[, outside
        ]1.1, 1.5[ and outside ]0.5, 0.9[ (the bounds stay clear of
        the OCCT noise on the measure)."""
        self.assertEqual(len(self._compute("CubeA", 0.5, 1.5)), 1)
        self.assertEqual(self._compute("CubeA", 1.1, 1.5), [])
        self.assertEqual(self._compute("CubeA", 0.5, 0.9), [])

    def test_compute_is_pure_of_management_and_display(self):
        rule = ObbHigh(None, 0.5, 1.5)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = self._compute("CubeA", 0.5, 1.5)

        self.assertEqual(len(results), 1)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)

    def test_element_without_geometry_is_skipped(self):
        rule = ObbHigh(None, -1e9, 1e9)
        storey = self.file.by_type("IfcBuildingStorey")[0]
        self.assertEqual(rule.compute([storey], -1e9, 1e9), [])

    def test_display_states_emit_all_geometries(self):
        """Display_Input: the OBB of EVERY source comes out and the
        result list does not (the engine is not run). Display_Result:
        every OBB AND the results. Two sources whose verdicts differ:
        both geometries come out in both display states."""
        sources = [self._element("CubeA"), self._element("CuboidA")]

        rule = ObbHigh(None, 0.5, 1.5, state="Display_Input")
        results = rule.compute(sources, 0.5, 1.5)
        self.assertEqual(results, [])
        self.assertEqual(len(rule.display_items), 2)
        for item in rule.display_items:
            self.assertEqual(item.category, "obb")
            self.assertEqual(item.color, (0.5, 0, 1))
            self.assertAlmostEqual(item.transparency, 0.2)

        rule = ObbHigh(None, 0.5, 1.5, state="Display_Result")
        results = rule.compute(sources, 0.5, 1.5)
        # Only CubeA passes the bounds, but BOTH OBBs are drawn.
        self.assertEqual(len(results), 1)
        self.assertEqual(len(rule.display_items), 2)


class TestComputeObbLength(_CubeModelMixin):
    """The compute contract of ObbLength: the widest (or narrowest) of
    the two non-vertical OBB axes."""

    def _compute(self, name, length_min, length_max, method):
        rule = ObbLength(None, length_min, length_max, method)
        return rule.compute([self._element(name)], length_min, length_max, method)

    def test_measured_dimensions(self):
        """CuboidA (2 x 1 x 4 standing): wide 2, narrow 1. FallenCuboidA
        (lying): wide 4, narrow 2. WallA (3 x 0.1 x 3): wide 3,
        narrow 0.1."""
        cases = {
            "CuboidA": (2.0, 1.0),
            "FallenCuboidA": (4.0, 2.0),
            "WallA": (3.0, 0.1),
        }
        for name, (wide, narrow) in cases.items():
            results = self._compute(name, -1e9, 1e9, "Wide")
            self.assertEqual(len(results), 1, name)
            self.assertAlmostEqual(results[0].info.offset, wide, delta=1e-2)

            results = self._compute(name, -1e9, 1e9, "Narrow")
            self.assertEqual(len(results), 1, name)
            self.assertAlmostEqual(results[0].info.offset, narrow, delta=1e-2)
            self.assertEqual(results[0].info.validate(), [])

    def test_bounds_are_open(self):
        """CuboidA wide is ~1.999 m (OCCT noise): inside ]1.5, 2.5[,
        outside ]2.0, 2.5[ and outside ]1.0, 1.5[."""
        self.assertEqual(len(self._compute("CuboidA", 1.5, 2.5, "Wide")), 1)
        self.assertEqual(self._compute("CuboidA", 2.0, 2.5, "Wide"), [])
        self.assertEqual(self._compute("CuboidA", 1.0, 1.5, "Wide"), [])

    def test_display_states_emit_all_geometries(self):
        """Display_Input: the OBB of EVERY source comes out and the
        result list does not. Display_Result: every OBB AND the
        results."""
        sources = [self._element("CubeA"), self._element("CuboidA")]

        rule = ObbLength(None, -1e9, 1e9, "Wide", state="Display_Input")
        results = rule.compute(sources, -1e9, 1e9, "Wide")
        self.assertEqual(results, [])
        self.assertEqual(len(rule.display_items), 2)
        for item in rule.display_items:
            self.assertEqual(item.category, "obb")
            self.assertEqual(item.color, (0.5, 0, 1))
            self.assertAlmostEqual(item.transparency, 0.2)

        rule = ObbLength(None, -1e9, 1e9, "Wide", state="Display_Result")
        results = rule.compute(sources, -1e9, 1e9, "Wide")
        self.assertEqual(len(results), 2)
        self.assertEqual(len(rule.display_items), 2)


class TestComputeLateralSurface(_CubeModelMixin):
    """The compute contract of LateralSurface: the area of the faces
    within the 45-degree cone of the direction — in WORLD coordinates
    (the local-coordinates bug fixed by the migration, SPEC point 3)."""

    def _compute(self, name, surface_min, surface_max, direction=(0.0, 0.0, 1.0)):
        rule = LateralSurface(None, surface_min, surface_max, direction)
        return rule.compute(
            [self._element(name)], surface_min, surface_max, direction
        )

    def test_measured_areas(self):
        """CubeA: 1 m2 (the top face). CuboidA standing: ~2 m2. The
        45-degree tilted cuboid: 0 (no face within the cone of +Z) —
        the world-coordinates fix of the migration."""
        cases = {"CubeA": 1.0, "CuboidA": 2.0, "45CuboidA": 0.0}
        for name, expected in cases.items():
            results = self._compute(name, -1e9, 1e9)
            self.assertEqual(len(results), 1, name)
            result = results[0]
            self.assertEqual(result.source.Name, name)
            self.assertAlmostEqual(result.info.area, expected, delta=1e-2)
            self.assertEqual(result.info.validate(), [])
        assert_result_shape(SimpleNamespace(result=self._compute("CubeA", -1e9, 1e9)))

    def test_bounds_are_open(self):
        self.assertEqual(len(self._compute("CubeA", 0.5, 1.5)), 1)
        self.assertEqual(self._compute("CubeA", 1.0, 1.5), [])
        self.assertEqual(self._compute("CubeA", 0.5, 1.0), [])


class TestComputeProjectedSurface(_CubeModelMixin):
    """The compute contract of ProjectedSurface: the footprint area
    toward the direction, in WORLD coordinates (bug fixed by the
    migration, SPEC point 3)."""

    def _compute(self, name, surface_min, surface_max, direction=(0.0, 0.0, 1.0)):
        rule = ProjectedSurface(None, surface_min, surface_max, direction)
        return rule.compute(
            [self._element(name)], surface_min, surface_max, direction
        )

    def test_measured_areas(self):
        """CubeA: 1 m2. FallenCuboidA (lying): ~8 m2. The 45-degree
        tilted cuboid: ~7.06 m2, the tilted footprint — the
        world-coordinates fix of the migration."""
        cases = {"CubeA": 1.0, "FallenCuboidA": 8.0, "45CuboidA": 7.06}
        for name, expected in cases.items():
            results = self._compute(name, -1e9, 1e9)
            self.assertEqual(len(results), 1, name)
            self.assertAlmostEqual(results[0].info.area, expected, delta=1e-2)
            self.assertEqual(results[0].info.validate(), [])

    def test_bounds_are_open(self):
        self.assertEqual(len(self._compute("CubeA", 0.5, 1.5)), 1)
        self.assertEqual(self._compute("CubeA", 1.0, 1.5), [])


class TestComputeObbFrontAndBack(unittest.TestCase):
    """The compute contract of OBB_Front_And_Back: the detection bands
    detached on the two plan sides of the source OBB.

    The known defect is preserved (Rapport.md): the side clash of the
    tilted cuboid is missed — do not fix it here."""

    @classmethod
    def setUpClass(cls):
        cls.files = {
            model: ifcopenshell.open(os.path.join(MODEL_DIR, model))
            for model in (
                "CubeB_InFrontOf_CuboidA_50cm.ifc",
                "SuzanneB_Behind_SuzanneA.ifc",
            )
        }

    @classmethod
    def tearDownClass(cls):
        cls.files.clear()

    def _element(self, model, name):
        matches = [
            e for e in self.files[model].by_type("IfcProduct") if e.Name == name
        ]
        self.assertTrue(matches, f"no element named {name!r} in {model}")
        return matches[0]

    def _compute(self, model, source, target, tolerance, method="Wide"):
        rule = OBB_Front_And_Back(None, None, tolerance, method)
        return rule.compute(
            [self._element(model, source)],
            [self._element(model, target)],
            tolerance,
            method,
        )

    def test_cube_in_front_of_cuboid(self):
        """A cube 50 cm in front of the cuboid: caught by the 1 m deep
        band, ignored by a 0.5 m one."""
        results = self._compute(
            "CubeB_InFrontOf_CuboidA_50cm.ifc", "CuboidA", "CubeB", 1.0
        )
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertEqual(result.source.Name, "CuboidA")
        self.assertEqual(result.target.Name, "CubeB")
        self.assertLessEqual(result.info.distance, 1e-6)
        # The touched band, the source object and the target object.
        labels = {obb.label for obb in result.info.source_obbs}
        self.assertEqual(labels, {"object", "zone"})
        self.assertEqual(
            {obb.label for obb in result.info.target_obbs}, {"object"}
        )
        self.assertEqual(result.info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

        self.assertEqual(
            self._compute(
                "CubeB_InFrontOf_CuboidA_50cm.ifc", "CuboidA", "CubeB", 0.5
            ),
            [],
        )

    def test_suzanne_behind(self):
        """SuzanneB behind SuzanneA: caught by a 0.3 m band, ignored
        by 0.1 m (whatever the method)."""
        results = self._compute(
            "SuzanneB_Behind_SuzanneA.ifc", "SuzanneB", "SuzanneA", 0.3
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source.Name, "SuzanneB")
        self.assertEqual(results[0].target.Name, "SuzanneA")

        for method in ("Wide", "Narrow"):
            self.assertEqual(
                self._compute(
                    "SuzanneB_Behind_SuzanneA.ifc",
                    "SuzanneB",
                    "SuzanneA",
                    0.1,
                    method,
                ),
                [],
            )

    def test_compute_is_pure_of_management_and_display(self):
        rule = OBB_Front_And_Back(None, None, 1.0, "Wide")
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = self._compute(
            "CubeB_InFrontOf_CuboidA_50cm.ifc", "CuboidA", "CubeB", 1.0
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)

    def test_display_states_emit_all_zone_geometries(self):
        """Display_Input: the TWO detection bands of the source come
        out and the result list does not (the engine is not run).
        Display_Result: the two bands AND the results — the bug of the
        single drawn OBB, fixed (one item per band, per source)."""
        model = "CubeB_InFrontOf_CuboidA_50cm.ifc"
        sources = [self._element(model, "CuboidA")]
        targets = [self._element(model, "CubeB")]

        rule = OBB_Front_And_Back(None, None, 1.0, "Wide", state="Display_Input")
        results = rule.compute(sources, targets, 1.0, "Wide")
        self.assertEqual(results, [])
        self.assertEqual(len(rule.display_items), 2)
        for item in rule.display_items:
            self.assertEqual(item.category, "obb")
            self.assertEqual(item.color, (0.5, 0, 1))
            self.assertAlmostEqual(item.transparency, 0.2)

        rule = OBB_Front_And_Back(None, None, 1.0, "Wide", state="Display_Result")
        results = rule.compute(sources, targets, 1.0, "Wide")
        self.assertEqual(len(results), 1)
        self.assertEqual(len(rule.display_items), 2)


class TestComputeLotsABDispatch(unittest.TestCase):
    """The flat JSON declarations drive the computes through the
    registry dispatch."""

    def test_engine_params(self):
        self.assertEqual(engine_params("ObbHigh"), ["length_min", "length_max"])
        self.assertEqual(
            engine_params("ObbLength"),
            ["length_min", "length_max", "direction_method"],
        )
        self.assertEqual(
            engine_params("LateralSurface"),
            ["surface_min", "surface_max", "direction"],
        )
        self.assertEqual(
            engine_params("ProjectedSurface"),
            ["surface_min", "surface_max", "direction"],
        )
        self.assertEqual(
            engine_params("OBB_Front_And_Back"),
            ["tolerance", "direction_method"],
        )

    def test_declaration_drives_obb_high(self):
        file = ifcopenshell.open(CUBE_MODEL)
        elements = {e.Name: e for e in file.by_type("IfcProduct")}

        rule = ObbHigh(select_by_name("CuboidA"), 0.5, 5.0)
        config = json.loads(json.dumps(serialize_rule_check(rule)))
        results = compute_from_config(config, [elements["CuboidA"]])
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].info.offset, 4.0, delta=1e-2)

    def test_declaration_drives_lateral_surface(self):
        file = ifcopenshell.open(CUBE_MODEL)
        elements = {e.Name: e for e in file.by_type("IfcProduct")}

        rule = LateralSurface(
            select_by_name("CubeA"), 0.5, 1.5, (0.0, 0.0, 1.0)
        )
        config = json.loads(json.dumps(serialize_rule_check(rule)))
        results = compute_from_config(config, [elements["CubeA"]])
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].info.area, 1.0, delta=1e-2)


class TestComputeLotsABThroughAdapter(unittest.TestCase):
    """The migration adapters (run + RuleFile) produce the RuleOutput
    of the pipeline (SPEC): one integration node per rule."""

    def test_obb_high_rule_output(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [CUBE_MODEL]
        rule = ObbHigh(select_by_name("CuboidA"), 0.5, 5.0)
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        self.assertEqual(len(rule.result), 1)
        self.assertIsNotNone(rule.output)
        self.assertIs(rule.output.results, rule.result)

    def test_lateral_surface_rule_output(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [CUBE_MODEL]
        rule = LateralSurface(
            select_by_name("45CuboidA"), -1e9, 1e9, (0.0, 0.0, 1.0)
        )
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        # The tilted cuboid carries no face within the cone of +Z.
        self.assertEqual(len(rule.result), 1)
        self.assertAlmostEqual(rule.result[0].info.area, 0.0, delta=1e-2)

    def test_obb_front_and_back_rule_output(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [
            os.path.join(MODEL_DIR, "CubeB_InFrontOf_CuboidA_50cm.ifc")
        ]
        rule = OBB_Front_And_Back(
            select_by_name("CuboidA"), select_by_name("CubeB"), 1.0, "Wide"
        )
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        self.assertEqual(len(rule.result), 1)
        self.assertIsNotNone(rule.output)
        self.assertIs(rule.output.results, rule.result)


if __name__ == "__main__":
    unittest.main()
