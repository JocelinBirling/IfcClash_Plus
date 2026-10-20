"""The compute contract of OneObjectFace (SPEC Separation moteur/
gestion), tested directly — one entity list and the named parameters
in, raw results out.

The model is the one of the unit suite: a unit cube (12 triangles) and
a "crossed" element made of two plates that go through each other (a
self-intersecting skin), generated with the ifcopenshell API.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_OneObjectFace.py -v
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

from Rules import OneObjectFace
from RuleClass import SelectFacet, RuleFile, ClashResultOneObject
from registry import compute_from_config, engine_params
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape
from tests.test_UnitRule_OneObjectFace import make_model


def select_by_name(name):
    from ifctester import ids

    select = SelectFacet()
    select.applicability = [ids.Attribute(name="Name", value=name)]
    return select


def bottom_selection():
    return {"orientation": "Bottom", "extreme_faces": True}


def top_selection():
    return {"orientation": "Top", "extreme_faces": True}


class TestComputeOneObjectFace(unittest.TestCase):
    """The compute contract of OneObjectFace: one list + the named
    parameters (the two FaceSelection dictionaries included)."""

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.mkdtemp()
        cls.model = os.path.join(cls._temp_dir, "one_object_face.ifc")
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

    def _compute(self, entity_name="Cube", **parameters):
        # A valid instance for the geometry settings: the checks
        # travel as the named parameters of the compute, the instance
        # config is not read by the engine.
        rule = OneObjectFace(None, distance=True, min_distance=0.1)
        return rule.compute(
            [self._element(entity_name)],
            parameters.get("face_a_selection"),
            parameters.get("face_b_selection"),
            parameters.get("distance", False),
            parameters.get("min_distance"),
            parameters.get("max_distance"),
            parameters.get("skip_adjacent", True),
            parameters.get("intersection", False),
            parameters.get("intersection_tolerance"),
            parameters.get("orientation", False),
            parameters.get("angle"),
            parameters.get("angle_tolerance"),
        )

    def test_distance_below_min_clashes(self):
        """The free height of the cube is 1 m: a required 2.10 m fails,
        one verdict per face pair (4)."""
        results = self._compute(
            face_a_selection=bottom_selection(),
            face_b_selection=top_selection(),
            distance=True,
            min_distance=2.10,
        )
        self.assertEqual(len(results), 4)
        for result in results:
            self.assertIsInstance(result, ClashResultOneObject)
            self.assertTrue(result.status)
            self.assertEqual(result.source.Name, "Cube")
            self.assertEqual(result.info.primary_measure, "distance")
            self.assertAlmostEqual(
                result.info.measure(result.info.primary_measure), 1.0, places=6
            )
            self.assertAlmostEqual(
                result.info.source_faces[0].face.area, 0.5, places=6
            )
            self.assertAlmostEqual(
                result.info.target_faces[0].face.area, 0.5, places=6
            )
            self.assertAlmostEqual(
                result.info.source_faces[0].face.normal[2], -1.0, places=6
            )
            self.assertAlmostEqual(
                result.info.target_faces[0].face.normal[2], 1.0, places=6
            )
            self.assertEqual(result.info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_distance_within_bounds_no_clash(self):
        results = self._compute(
            face_a_selection=bottom_selection(),
            face_b_selection=top_selection(),
            distance=True,
            min_distance=0.5,
            max_distance=1.5,
        )
        self.assertEqual(results, [])

    def test_distance_bound_is_inclusive(self):
        results = self._compute(
            face_a_selection=bottom_selection(),
            face_b_selection=top_selection(),
            distance=True,
            min_distance=1.0,
        )
        self.assertEqual(results, [])

        results = self._compute(
            face_a_selection=bottom_selection(),
            face_b_selection=top_selection(),
            distance=True,
            min_distance=1.0 + 1e-6,
        )
        self.assertEqual(len(results), 4)

    def test_skip_adjacent_skips_touching_pairs(self):
        """With all the faces selected, adjacent pairs touch: skipped
        by default, flagged without the skip."""
        results = self._compute(distance=True, min_distance=0.1)
        self.assertEqual(results, [])

        results = self._compute(
            distance=True, min_distance=0.1, skip_adjacent=False
        )
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertAlmostEqual(
                result.info.measure(result.info.primary_measure), 0.0, places=6
            )

    def test_orientation_checks(self):
        """Top vs side normals are perpendicular: 90 passes, 0 fails."""
        parameters = {
            "face_a_selection": {"orientation": "Top"},
            "face_b_selection": {"orientation": "Side"},
            "orientation": True,
            "angle_tolerance": 5,
        }
        results = self._compute(angle=90, **parameters)
        self.assertEqual(results, [])

        results = self._compute(angle=0, **parameters)
        self.assertGreater(len(results), 0)
        self.assertEqual(
            {result.info.primary_measure for result in results}, {"angle"}
        )
        for result in results:
            self.assertAlmostEqual(
                result.info.measure(result.info.primary_measure), 90.0, places=6
            )

    def test_intersection_checks(self):
        """A watertight cube does not self-intersect; the crossed skin
        does, tolerated by a depth tolerance above the penetration."""
        results = self._compute(intersection=True)
        self.assertEqual(results, [])

        results = self._compute(
            "Crossed", intersection=True, intersection_tolerance=0.001
        )
        self.assertGreater(len(results), 0)
        for result in results:
            self.assertEqual(result.info.primary_measure, "penetration_depth")
            self.assertGreater(
                result.info.measure(result.info.primary_measure), 0.001
            )

        results = self._compute(
            "Crossed", intersection=True, intersection_tolerance=10.0
        )
        self.assertEqual(results, [])

    def test_compute_is_pure_of_management_and_display(self):
        rule = OneObjectFace(None, distance=True, min_distance=2.10)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = self._compute(
            face_a_selection=bottom_selection(),
            face_b_selection=top_selection(),
            distance=True,
            min_distance=2.10,
        )

        self.assertEqual(len(results), 4)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)

    def test_element_without_geometry_is_skipped(self):
        rule = OneObjectFace(None, distance=True, min_distance=0.1)
        project = self.file.by_type("IfcProject")[0]
        results = self._compute_entity(project)
        self.assertEqual(results, [])

    def _compute_entity(self, entity):
        """The compute of the default distance check on one given
        entity, whatever its geometry."""
        rule = OneObjectFace(None, distance=True, min_distance=0.1)
        return rule.compute(
            [entity],
            None,
            None,
            True,
            0.1,
            None,
            True,
            False,
            None,
            False,
            None,
            None,
        )


class TestComputeOneObjectFaceDispatch(unittest.TestCase):
    """The flat JSON declarations drive the compute through the
    registry dispatch."""

    def test_engine_params(self):
        self.assertEqual(
            engine_params("OneObjectFace"),
            [
                "face_a_selection",
                "face_b_selection",
                "distance",
                "min_distance",
                "max_distance",
                "skip_adjacent",
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
        model = os.path.join(temp_dir, "one_object_face.ifc")
        make_model(model)
        file = ifcopenshell.open(model)
        elements = {e.Name: e for e in file.by_type("IfcProduct")}

        rule = OneObjectFace(
            select_by_name("Cube"),
            face_a_selection=bottom_selection(),
            face_b_selection=top_selection(),
            distance=True,
            min_distance=2.10,
        )
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        results = compute_from_config(config, [elements["Cube"]])
        self.assertEqual(len(results), 4)
        self.assertEqual(results[0].info.primary_measure, "distance")


class TestComputeOneObjectFaceThroughAdapter(unittest.TestCase):
    """The migration adapter (run + RuleFile) produces the RuleOutput
    of the pipeline (SPEC): one integration node."""

    def test_rule_output_after_rule_file_run(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, True)
        model = os.path.join(temp_dir, "one_object_face.ifc")
        make_model(model)

        rule_file = RuleFile()
        rule_file.list_ifc_path = [model]
        rule = OneObjectFace(
            select_by_name("Cube"),
            face_a_selection=bottom_selection(),
            face_b_selection=top_selection(),
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
