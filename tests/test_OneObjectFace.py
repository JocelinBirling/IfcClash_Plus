"""
Test suite for the OneObjectFace rule (doc/1ObjectsRules/OneObjectFace.md).

The models are generated with the ifcopenshell API: a unit cube (12
triangles), and a "crossed" element made of two plates that go through
each other (a self-intersecting skin) for the intersection check.

Execution (from the repository root):
    python -m pytest tests/test_OneObjectFace.py -v
"""
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell
import ifcopenshell.api

from Rules import OneObjectFace
from RuleClass import SelectFacet, RuleFile, ClashResultOneObject
from clash_utils import (
    distance_between_triangles,
    triangle_penetration_depth,
    triangles_cross_properly,
    triangles_share_geometry,
)
from ifctester import ids


def make_model(path):
    """A unit cube and a crossed element (two plates through each other)."""
    file = ifcopenshell.api.run("project.create_file")
    ifcopenshell.api.run("root.create_entity", file, ifc_class="IfcProject", name="P")
    ifcopenshell.api.run(
        "unit.assign_unit", file, length={"is_metric": True, "raw": "METERS"}
    )
    context = ifcopenshell.api.run("context.add_context", file, context_type="Model")
    body = ifcopenshell.api.run(
        "context.add_context",
        file,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=context,
    )

    def solid(dx, dy):
        profile = file.createIfcRectangleProfileDef(
            "AREA",
            None,
            file.createIfcAxis2Placement2D(
                file.createIfcCartesianPoint((0.0, 0.0)), None
            ),
            float(dx),
            float(dy),
        )
        placement = file.createIfcAxis2Placement3D(
            file.createIfcCartesianPoint((0.0, 0.0, 0.0)),
            file.createIfcDirection((0.0, 0.0, 1.0)),
            file.createIfcDirection((1.0, 0.0, 0.0)),
        )
        return file.createIfcExtrudedAreaSolid(
            profile,
            placement,
            file.createIfcDirection((0.0, 0.0, 1.0)),
            1.0,
        )

    cube = ifcopenshell.api.run(
        "root.create_entity", file, ifc_class="IfcBuildingElementProxy", name="Cube"
    )
    ifcopenshell.api.run(
        "geometry.edit_object_placement",
        file,
        product=cube,
        matrix=((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)),
    )
    cube_representation = file.createIfcShapeRepresentation(
        body, "Body", "SweptSolid", [solid(1.0, 1.0)]
    )
    ifcopenshell.api.run(
        "geometry.assign_representation",
        file,
        product=cube,
        representation=cube_representation,
    )

    crossed = ifcopenshell.api.run(
        "root.create_entity", file, ifc_class="IfcBuildingElementProxy", name="Crossed"
    )
    ifcopenshell.api.run(
        "geometry.edit_object_placement",
        file,
        product=crossed,
        matrix=((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)),
    )
    crossed_representation = file.createIfcShapeRepresentation(
        body, "Body", "SweptSolid", [solid(3.0, 0.1), solid(0.1, 3.0)]
    )
    ifcopenshell.api.run(
        "geometry.assign_representation",
        file,
        product=crossed,
        representation=crossed_representation,
    )

    file.write(path)


class TestOneObjectFace(unittest.TestCase):
    """The OneObjectFace rule on generated models."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, True)
        self.model = os.path.join(self.temp_dir, "one_object_face.ifc")
        make_model(self.model)

    @staticmethod
    def select(name):
        select = SelectFacet()
        select.applicability = [ids.Attribute(name="Name", value=name)]
        return select

    def run_rule(self, entity_name="Cube", **parameters):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.model]
        rule = OneObjectFace(self.select(entity_name), **parameters)
        rule_file.contains = [rule]
        rule_file.run()
        return rule

    def bottom_selection(self):
        return {"orientation": "Bottom", "extreme_faces": True}

    def top_selection(self):
        return {"orientation": "Top", "extreme_faces": True}

    # ---- Nominal: distance check

    def test_distance_below_min_clashes(self):
        """The free height of the cube is 1 m: a required 2.10 m fails."""
        rule = self.run_rule(
            face_a_selection=self.bottom_selection(),
            face_b_selection=self.top_selection(),
            distance=True,
            min=2.10,
        )

        # 2 triangles per face, all against all: 4 pairs, all failing.
        self.assertEqual(len(rule.result), 4)
        for result in rule.result:
            self.assertIsInstance(result, ClashResultOneObject)
            self.assertEqual(result.source.Name, "Cube")
            self.assertEqual(result.check, "distance")
            self.assertAlmostEqual(result.value, 1.0, places=6)
            self.assertAlmostEqual(result.face_a["area"], 0.5, places=6)
            self.assertAlmostEqual(result.face_b["area"], 0.5, places=6)
            self.assertAlmostEqual(result.face_a["normal"][2], -1.0, places=6)
            self.assertAlmostEqual(result.face_b["normal"][2], 1.0, places=6)

    def test_distance_within_bounds_no_clash(self):
        """The same 1 m height satisfies [0.5, 1.5]."""
        rule = self.run_rule(
            face_a_selection=self.bottom_selection(),
            face_b_selection=self.top_selection(),
            distance=True,
            min=0.5,
            max=1.5,
        )
        self.assertEqual(len(rule.result), 0)

    def test_distance_above_max_clashes(self):
        rule = self.run_rule(
            face_a_selection=self.bottom_selection(),
            face_b_selection=self.top_selection(),
            distance=True,
            max=0.5,
        )
        self.assertEqual(len(rule.result), 4)
        self.assertEqual({result.check for result in rule.result}, {"distance"})

    # ---- skip_adjacent

    def test_skip_adjacent_skips_touching_pairs(self):
        """With all the faces selected, adjacent pairs touch (distance 0):
        they are skipped by default, and flagged without the skip."""
        rule = self.run_rule(distance=True, min=0.1, skip_adjacent=True)
        self.assertEqual(len(rule.result), 0)

        rule = self.run_rule(distance=True, min=0.1, skip_adjacent=False)
        self.assertGreater(len(rule.result), 0)
        for result in rule.result:
            self.assertAlmostEqual(result.value, 0.0, places=6)

    # ---- Nominal: orientation check

    def test_orientation_perpendicular_passes(self):
        rule = self.run_rule(
            face_a_selection={"orientation": "Top"},
            face_b_selection={"orientation": "Side"},
            orientation=True,
            angle=90,
            angle_tolerance=5,
        )
        self.assertEqual(len(rule.result), 0)

    def test_orientation_wrong_angle_clashes(self):
        rule = self.run_rule(
            face_a_selection={"orientation": "Top"},
            face_b_selection={"orientation": "Side"},
            orientation=True,
            angle=0,
            angle_tolerance=5,
        )
        self.assertGreater(len(rule.result), 0)
        self.assertEqual({result.check for result in rule.result}, {"orientation"})
        for result in rule.result:
            self.assertAlmostEqual(result.value, 90.0, places=6)

    def test_orientation_opposing_faces(self):
        """Bottom vs top normals are opposite: 180 degrees."""
        rule = self.run_rule(
            face_a_selection=self.bottom_selection(),
            face_b_selection=self.top_selection(),
            orientation=True,
            angle=180,
            angle_tolerance=10,
        )
        self.assertEqual(len(rule.result), 0)

    # ---- Nominal: intersection check

    def test_watertight_cube_does_not_self_intersect(self):
        rule = self.run_rule("Cube", intersection=True)
        self.assertEqual(len(rule.result), 0)

    def test_crossed_skin_self_intersects(self):
        """The two crossed plates go through each other."""
        rule = self.run_rule(
            "Crossed", intersection=True, intersection_tolerance=0.001
        )

        self.assertGreater(len(rule.result), 0)
        for result in rule.result:
            self.assertEqual(result.check, "intersection")
            self.assertGreater(result.value, 0.001)

    def test_crossed_skin_tolerated_by_depth(self):
        """A tolerance above the penetration depth tolerates the
        crossing."""
        rule = self.run_rule(
            "Crossed", intersection=True, intersection_tolerance=10.0
        )
        self.assertEqual(len(rule.result), 0)

    # ---- Combined checks

    def test_pair_must_pass_all_enabled_checks(self):
        """The bottom/top pairs fail both the distance and the
        orientation check: one clash per pair per failed check."""
        rule = self.run_rule(
            face_a_selection=self.bottom_selection(),
            face_b_selection=self.top_selection(),
            distance=True,
            min=2.0,
            orientation=True,
            angle=0,
            angle_tolerance=5,
        )

        # 4 pairs x 2 failed checks.
        self.assertEqual(len(rule.result), 8)
        self.assertEqual(
            {result.check for result in rule.result}, {"distance", "orientation"}
        )

    def test_pair_passing_both_checks_no_clash(self):
        rule = self.run_rule(
            face_a_selection=self.bottom_selection(),
            face_b_selection=self.top_selection(),
            distance=True,
            min=0.5,
            orientation=True,
            angle=180,
            angle_tolerance=10,
        )
        self.assertEqual(len(rule.result), 0)

    # ---- Bornes

    def test_distance_bound_is_inclusive(self):
        """A distance exactly at min is compliant (only closer fails)."""
        rule = self.run_rule(
            face_a_selection=self.bottom_selection(),
            face_b_selection=self.top_selection(),
            distance=True,
            min=1.0,
        )
        self.assertEqual(len(rule.result), 0)

        rule = self.run_rule(
            face_a_selection=self.bottom_selection(),
            face_b_selection=self.top_selection(),
            distance=True,
            min=1.0 + 1e-6,
        )
        self.assertEqual(len(rule.result), 4)

    def test_orientation_bound_is_inclusive(self):
        """A deviation exactly at angle_tolerance is compliant."""
        rule = self.run_rule(
            face_a_selection={"orientation": "Top"},
            face_b_selection={"orientation": "Side"},
            orientation=True,
            angle=95,
            angle_tolerance=5,
        )
        self.assertEqual(len(rule.result), 0)

        rule = self.run_rule(
            face_a_selection={"orientation": "Top"},
            face_b_selection={"orientation": "Side"},
            orientation=True,
            angle=96,
            angle_tolerance=5,
        )
        self.assertGreater(len(rule.result), 0)

    # ---- Cas limites

    def test_empty_selection_no_crash(self):
        rule = self.run_rule("Nothing", distance=True, min=0.1)
        self.assertEqual(len(rule.result), 0)

    def test_invalid_parameters_raise_value_error(self):
        source = self.select("Cube")

        with self.assertRaises(ValueError):
            OneObjectFace(source)  # no check enabled
        with self.assertRaises(ValueError):
            OneObjectFace(source, orientation=True)  # angle missing
        with self.assertRaises(ValueError):
            OneObjectFace(source, orientation=True, angle=190)
        with self.assertRaises(ValueError):
            OneObjectFace(source, orientation=True, angle=90, angle_tolerance=-1)
        with self.assertRaises(ValueError):
            OneObjectFace(source, distance=True, min=2.0, max=1.0)
        with self.assertRaises(ValueError):
            OneObjectFace(source, distance=True, min=-1.0)
        with self.assertRaises(ValueError):
            OneObjectFace(source, intersection=True, intersection_tolerance=-0.1)
        with self.assertRaises(ValueError):
            OneObjectFace(source, face_a_selection={"color": "red"}, distance=True, min=1.0)


class TestOneObjectFaceUtilities(unittest.TestCase):
    """The triangle pair helpers of clash_utils used by OneObjectFace."""

    def horizontal_triangle(self):
        return np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [0.0, 4.0, 0.0]])

    def crossing_triangle(self):
        """A vertical triangle whose edge goes through the horizontal
        one: its plane is x=2, its vertices reach z=-1 and z=3."""
        return np.array([[2.0, 1.0, -1.0], [2.0, 1.0, 3.0], [2.0, 3.0, 1.0]])

    def test_share_geometry(self):
        a = self.horizontal_triangle()
        # Shares the vertex (4, 0, 0).
        b = np.array([[4.0, 0.0, 0.0], [4.0, 4.0, 0.0], [4.0, 0.0, 4.0]])
        self.assertTrue(triangles_share_geometry(a, b))
        self.assertFalse(triangles_share_geometry(a, self.crossing_triangle()))

    def test_proper_crossing(self):
        self.assertTrue(
            triangles_cross_properly(
                self.horizontal_triangle(), self.crossing_triangle()
            )
        )

    def test_touching_is_not_crossing(self):
        """Two triangles sharing an edge do not cross properly."""
        a = self.horizontal_triangle()
        b = np.array([[0.0, 0.0, 0.0], [4.0, 0.0, 0.0], [2.0, 0.0, 3.0]])
        self.assertTrue(triangles_share_geometry(a, b))
        self.assertFalse(triangles_cross_properly(a, b))

    def test_disjoint_triangles_do_not_cross(self):
        a = self.horizontal_triangle()
        far = np.array([[0.0, 0.0, 10.0], [1.0, 0.0, 10.0], [0.0, 1.0, 10.0]])
        self.assertFalse(triangles_cross_properly(a, far))

    def test_penetration_depth(self):
        """The crossing triangle dives 3 m past the horizontal plane
        (vertex at z=3); the horizontal one 2 m past the vertical plane
        (vertex at x=0, plane at x=2): the depth is 3 m."""
        depth = triangle_penetration_depth(
            self.horizontal_triangle(), self.crossing_triangle()
        )
        self.assertAlmostEqual(depth, 3.0, places=9)

    def test_distance_between_triangles(self):
        a = np.array([[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])
        b = np.array([[0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [0.0, 1.0, 1.0]])
        self.assertAlmostEqual(distance_between_triangles(a, b), 1.0, places=9)
        self.assertAlmostEqual(distance_between_triangles(a, a), 0.0, places=9)


if __name__ == "__main__":
    unittest.main()
