"""The compute contract of TwoObjectsFace (SPEC Separation moteur/
gestion), tested directly — entity lists and the named parameters in,
raw results out.

The model is the one of the unit suite: two unit cubes 2 m apart
("Near" at the origin, "Far" translated by (3, 0, 0)), and two plates
that go through each other ("PlateX" and "PlateY", the crossed skins
split over two objects).

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_TwoObjectsFace.py -v
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell

from Rules import TwoObjectsFace
from RuleClass import SelectFacet, RuleFile, ClashResultTwoObjects
from registry import compute_from_config, engine_params
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape
from tests.test_UnitRule_TwoObjectsFace import make_model


def select_by_name(name):
    from ifctester import ids

    select = SelectFacet()
    select.applicability = [ids.Attribute(name="Name", value=name)]
    return select


def toward_target():
    """The faces of Near oriented toward Far (+X)."""
    return {"orientation": (1.0, 0.0, 0.0)}


def toward_source():
    """The faces of Far oriented toward Near (-X)."""
    return {"orientation": (-1.0, 0.0, 0.0)}


class TestComputeTwoObjectsFace(unittest.TestCase):
    """The compute contract of TwoObjectsFace: two lists + the named
    parameters (the two FaceSelection dictionaries included)."""

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.mkdtemp()
        cls.model = os.path.join(cls._temp_dir, "two_objects_face.ifc")
        make_model(cls.model)
        # ifcopenshell 0.9: an entity does not keep its file alive.
        cls.file = ifcopenshell.open(cls.model)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls._temp_dir, True)

    def _element(self, name):
        matches = [e for e in self.file.by_type("IfcProduct") if e.Name == name]
        self.assertTrue(matches, f"no element named {name!r}")
        return matches[0]

    def _compute(self, source="Near", target="Far", **parameters):
        # A valid instance for the geometry settings: the checks
        # travel as the named parameters of the compute, the instance
        # config is not read by the engine.
        rule = TwoObjectsFace(None, None, distance=True, min_distance=0.1)
        return rule.compute(
            [self._element(source)],
            [self._element(target)],
            parameters.get("source_face_selection"),
            parameters.get("target_face_selection"),
            parameters.get("distance", False),
            parameters.get("min_distance"),
            parameters.get("max_distance"),
            parameters.get("intersection", False),
            parameters.get("intersection_tolerance"),
            parameters.get("orientation", False),
            parameters.get("angle"),
            parameters.get("angle_tolerance"),
        )

    def test_distance_below_min_clashes(self):
        """The facing side faces are 2 m apart: a required 2.10 m
        fails, one verdict per face pair (4)."""
        results = self._compute(
            source_face_selection=toward_target(),
            target_face_selection=toward_source(),
            distance=True,
            min_distance=2.10,
            max_distance=10,
        )
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertIsInstance(result, ClashResultTwoObjects)
            self.assertTrue(result.status)
            self.assertEqual(result.source.Name, "Near")
            self.assertEqual(result.target.Name, "Far")
            self.assertEqual(result.info.primary_measure, "distance")
            self.assertAlmostEqual(
                result.info.measure(result.info.primary_measure), 2.0, places=6
            )
            self.assertAlmostEqual(
                result.info.source_faces[0].face.area, 0.5, places=6
            )
            self.assertAlmostEqual(
                result.info.target_faces[0].face.area, 0.5, places=6
            )
            self.assertAlmostEqual(
                result.info.source_faces[0].face.normal[0], 1.0, places=6
            )
            self.assertAlmostEqual(
                result.info.target_faces[0].face.normal[0], -1.0, places=6
            )
            self.assertEqual(result.info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_distance_within_bounds_no_clash(self):
        results = self._compute(
            source_face_selection=toward_target(),
            target_face_selection=toward_source(),
            distance=True,
            min_distance=1.5,
            max_distance=2.5,
        )
        self.assertEqual(results, [])

    def test_whole_target_distance_min(self):
        """Without a target face selection, the source faces are
        checked against all the faces of the target: 19 pairs hold a
        closest approach at exactly 2 m, the others are farther and
        pass."""
        results = self._compute(
            source_face_selection=toward_target(),
            distance=True,
            min_distance=2.10,
            max_distance=10,
        )
        self.assertEqual(len(results), 19)
        for result in results:
            self.assertEqual(result.info.primary_measure, "distance")
            self.assertAlmostEqual(
                result.info.measure(result.info.primary_measure), 2.0, places=6
            )

    def test_intersection_checks(self):
        """Disjoint objects do not intersect; the crossed skins of two
        plates do, tolerated by a depth tolerance above the
        penetration."""
        results = self._compute(intersection=True)
        self.assertEqual(results, [])

        results = self._compute(
            "PlateX", "PlateY", intersection=True, intersection_tolerance=0.001
        )
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertEqual(result.source.Name, "PlateX")
            self.assertEqual(result.target.Name, "PlateY")
            self.assertEqual(result.info.primary_measure, "penetration_depth")
            self.assertGreater(
                result.info.measure(result.info.primary_measure), 0.001
            )

        results = self._compute(
            "PlateX", "PlateY", intersection=True, intersection_tolerance=10.0
        )
        self.assertEqual(results, [])

    def test_orientation_checks(self):
        """The facing side faces have opposite normals: 180 passes, 0
        fails with the measured angle."""
        parameters = {
            "source_face_selection": toward_target(),
            "target_face_selection": toward_source(),
            "orientation": True,
            "angle_tolerance": 10,
        }
        results = self._compute(angle=180, **parameters)
        self.assertEqual(results, [])

        results = self._compute(angle=0, angle_tolerance=5, **{
            "source_face_selection": toward_target(),
            "target_face_selection": toward_source(),
            "orientation": True,
        })
        self.assertEqual(len(results), 4)
        self.assertEqual(
            {result.info.primary_measure for result in results}, {"angle"}
        )
        for result in results:
            self.assertAlmostEqual(
                result.info.measure(result.info.primary_measure), 180.0, places=6
            )

    def test_same_element_not_checked_against_itself(self):
        """The same element in the two lists is skipped."""
        results = self._compute(
            source="PlateX",
            target="PlateX",
            intersection=True,
            intersection_tolerance=0.001,
        )
        self.assertEqual(results, [])

    def test_compute_is_pure_of_management_and_display(self):
        rule = TwoObjectsFace(None, None, distance=True, min_distance=0.1)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = self._compute(
            source_face_selection=toward_target(),
            target_face_selection=toward_source(),
            distance=True,
            min_distance=2.10,
        )

        self.assertEqual(len(results), 4)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)

    def test_compute_registers_no_display_item(self):
        """The compute passes register=False to _collect_faces: the
        selected faces are registered by the adapter only."""
        rule = TwoObjectsFace(None, None, distance=True, min_distance=0.1)
        self._compute(
            source_face_selection=toward_target(),
            target_face_selection=toward_source(),
            distance=True,
            min_distance=2.10,
        )
        self.assertEqual(rule.display_items, [])

    def test_element_without_geometry_is_skipped(self):
        rule = TwoObjectsFace(None, None, distance=True, min_distance=0.1)
        project = self.file.by_type("IfcProject")[0]
        results = rule.compute(
            [project],
            [self._element("Far")],
            None,
            None,
            True,
            0.1,
            None,
            False,
            None,
            False,
            None,
            None,
        )
        self.assertEqual(results, [])


class TestComputeTwoObjectsFaceDispatch(unittest.TestCase):
    """The flat JSON declarations drive the compute through the
    registry dispatch."""

    def test_engine_params(self):
        self.assertEqual(
            engine_params("TwoObjectsFace"),
            [
                "source_face_selection",
                "target_face_selection",
                "distance",
                "min_distance",
                "max_distance",
                "intersection",
                "intersection_tolerance",
                "orientation",
                "angle",
                "angle_tolerance",
            ],
        )

    def test_declaration_drives_the_compute(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, True)
        model = os.path.join(temp_dir, "two_objects_face.ifc")
        make_model(model)
        file = ifcopenshell.open(model)
        elements = {e.Name: e for e in file.by_type("IfcProduct")}

        rule = TwoObjectsFace(
            select_by_name("Near"),
            select_by_name("Far"),
            source_face_selection=toward_target(),
            target_face_selection=toward_source(),
            distance=True,
            min_distance=2.10,
        )
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        results = compute_from_config(
            config, [elements["Near"]], [elements["Far"]]
        )
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].info.primary_measure, "distance")


class TestComputeTwoObjectsFaceThroughAdapter(unittest.TestCase):
    """The migration adapter (run + RuleFile) produces the RuleOutput
    of the pipeline (SPEC): one integration node."""

    def test_rule_output_after_rule_file_run(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, True)
        model = os.path.join(temp_dir, "two_objects_face.ifc")
        make_model(model)

        rule_file = RuleFile()
        rule_file.list_ifc_path = [model]
        rule = TwoObjectsFace(
            select_by_name("Near"),
            select_by_name("Far"),
            source_face_selection=toward_target(),
            target_face_selection=toward_source(),
            distance=True,
            min_distance=2.10,
        )
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        self.assertEqual(len(rule.result), 4)
        self.assertIsNotNone(rule.output)
        self.assertIs(rule.output.results, rule.result)


if __name__ == "__main__":
    unittest.main()
