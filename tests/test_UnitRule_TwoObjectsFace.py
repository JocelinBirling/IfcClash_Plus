"""
Test suite for the TwoObjectsFace rule (doc/2ObjectsRules/TwoObjectsFace.md).

The model is generated with the ifcopenshell API: two unit cubes 2 m
apart ("Near" at the origin, "Far" translated by (3, 0, 0), so the
facing side faces are 2 m apart), and two plates that go through each
other ("PlateX" and "PlateY", the crossed skins split over two
objects) for the intersection check.

Execution (from the repository root):
    python -m pytest tests/test_UnitRule_TwoObjectsFace.py -v
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

from Rules import TwoObjectsFace
from RuleClass import SelectFacet, RuleFile, ClashResultTwoObjects
from ifctester import ids


def make_model(path):
    """Two unit cubes 2 m apart and two crossed plates."""
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

    def element(name, shapes, matrix):
        product = ifcopenshell.api.run(
            "root.create_entity", file, ifc_class="IfcBuildingElementProxy", name=name
        )
        ifcopenshell.api.run(
            "geometry.edit_object_placement",
            file,
            product=product,
            matrix=matrix,
        )
        representation = file.createIfcShapeRepresentation(
            body, "Body", "SweptSolid", shapes
        )
        ifcopenshell.api.run(
            "geometry.assign_representation",
            file,
            product=product,
            representation=representation,
        )
        return product

    identity = ((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))
    shifted = ((1, 0, 0, 3), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1))

    element("Near", [solid(1.0, 1.0)], identity)
    element("Far", [solid(1.0, 1.0)], shifted)
    element("PlateX", [solid(3.0, 0.1)], identity)
    element("PlateY", [solid(0.1, 3.0)], identity)

    file.write(path)


class TestTwoObjectsFace(unittest.TestCase):
    """The TwoObjectsFace rule on a generated model."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, True)
        self.model = os.path.join(self.temp_dir, "two_objects_face.ifc")
        make_model(self.model)

    @staticmethod
    def select(name):
        select = SelectFacet()
        select.applicability = [ids.Attribute(name="Name", value=name)]
        return select

    def run_rule(self, source_name="Near", target_name="Far", **parameters):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.model]
        parameters["state"] = "Final"
        rule = TwoObjectsFace(
            self.select(source_name), self.select(target_name), **parameters
        )
        rule_file.contains = [rule]
        rule_file.run()
        return rule

    @staticmethod
    def toward_target():
        """The faces of Near oriented toward Far (+X)."""
        return {"orientation": (1.0, 0.0, 0.0)}

    @staticmethod
    def toward_source():
        """The faces of Far oriented toward Near (-X)."""
        return {"orientation": (-1.0, 0.0, 0.0)}

    # ---- Nominal: distance check, face-to-face

    def test_distance_below_min_clashes(self):
        """The facing side faces are 2 m apart: a required 2.10 m fails."""
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            target_face_selection=self.toward_source(),
            distance=True,
            min_distance=2.10,
            max_distance=10
        )

        # 2 triangles per face, all against all: 4 pairs, all failing.
        self.assertEqual(len(rule.result), 4)
        for result in rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)
            self.assertEqual(result.source.Name, "Near")
            self.assertEqual(result.target.Name, "Far")
            self.assertEqual(result.check, "distance")
            self.assertAlmostEqual(result.value, 2.0, places=6)
            self.assertAlmostEqual(result.face_a["area"], 0.5, places=6)
            self.assertAlmostEqual(result.face_b["area"], 0.5, places=6)
            self.assertAlmostEqual(result.face_a["normal"][0], 1.0, places=6)
            self.assertAlmostEqual(result.face_b["normal"][0], -1.0, places=6)

    def test_distance_within_bounds_no_clash(self):
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            target_face_selection=self.toward_source(),
            distance=True,
            min_distance=1.5,
            max_distance=2.5,
        )
        self.assertEqual(len(rule.result), 0)

    def test_distance_above_max_clashes(self):
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            target_face_selection=self.toward_source(),
            distance=True,
            max_distance=1.0,
        )
        self.assertEqual(len(rule.result), 4)
        self.assertEqual({result.check for result in rule.result}, {"distance"})

    def test_distance_bound_is_inclusive(self):
        """Exactly 2 m satisfies [2.0, 2.0]."""
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            target_face_selection=self.toward_source(),
            distance=True,
            min_distance=2.0,
            max_distance=2.0,
        )
        self.assertEqual(len(rule.result), 0)

    # ---- Distance check against the whole target objects

    def test_whole_target_distance_min(self):
        """Without Target_Face_Selection, the source faces are checked
        against all the faces of Far (24 pairs): 19 pairs hold a
        closest approach at exactly 2 m, the others are farther and
        pass."""
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            distance=True,
            min_distance=2.10,
            max_distance=10
        )

        self.assertEqual(len(rule.result), 19)
        for result in rule.result:
            self.assertEqual(result.check, "distance")
            self.assertAlmostEqual(result.value, 2.0, places=6)

    def test_whole_target_distance_bounds(self):
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            distance=True,
            min_distance=1.5,
            max_distance=3.5,
        )
        self.assertEqual(len(rule.result), 0)

    def test_whole_target_distance_max(self):
        """All 24 pairs (2 source triangles x 12 target triangles) are
        farther than 1 m."""
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            distance=True,
            max_distance=1.0,
        )
        self.assertEqual(len(rule.result), 24)

    # ---- Nominal: intersection check

    def test_disjoint_objects_do_not_intersect(self):
        rule = self.run_rule("Near", "Far", intersection=True)
        self.assertEqual(len(rule.result), 0)

    def test_crossed_skins_intersect(self):
        """The skins of the two plates go through each other."""
        rule = self.run_rule(
            "PlateX", "PlateY", intersection=True, intersection_tolerance=0.001
        )

        self.assertGreater(len(rule.result), 0)
        for result in rule.result:
            self.assertEqual(result.source.Name, "PlateX")
            self.assertEqual(result.target.Name, "PlateY")
            self.assertEqual(result.check, "intersection")
            self.assertGreater(result.value, 0.001)

    def test_crossed_skins_tolerated_by_depth(self):
        rule = self.run_rule("PlateX", "PlateY", intersection=True,
                             intersection_tolerance=10.0)
        self.assertEqual(len(rule.result), 0)

    # ---- Nominal: orientation check

    def test_orientation_opposing_faces_pass(self):
        """The facing side faces have opposite normals: 180 degrees."""
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            target_face_selection=self.toward_source(),
            orientation=True,
            angle=180,
            angle_tolerance=10,
        )
        self.assertEqual(len(rule.result), 0)

    def test_orientation_wrong_angle_clashes(self):
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            target_face_selection=self.toward_source(),
            orientation=True,
            angle=0,
            angle_tolerance=5,
        )
        self.assertEqual(len(rule.result), 4)
        self.assertEqual({result.check for result in rule.result}, {"orientation"})
        for result in rule.result:
            self.assertAlmostEqual(result.value, 180.0, places=6)

    def test_orientation_bound_is_inclusive(self):
        """A deviation exactly at angle_tolerance is compliant."""
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            target_face_selection=self.toward_source(),
            orientation=True,
            angle=170,
            angle_tolerance=10,
        )
        self.assertEqual(len(rule.result), 0)

    # ---- Combined checks

    def test_pair_must_pass_all_enabled_checks(self):
        """The distance passes, the orientation fails: only the
        orientation clashes."""
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            target_face_selection=self.toward_source(),
            distance=True,
            min_distance=1.5,
            max_distance=2.5,
            orientation=True,
            angle=0,
            angle_tolerance=5,
        )
        self.assertEqual(len(rule.result), 4)
        self.assertEqual({result.check for result in rule.result}, {"orientation"})

    # ---- Selection behavior

    def test_empty_selection_selects_all_faces(self):
        """The default selections keep every face: 12 x 12 = 144 pairs,
        none closer than 2 m or farther than 10 m."""
        rule = self.run_rule(distance=True, min_distance=2.0, max_distance=10.0)
        self.assertEqual(len(rule.result), 0)

    def test_selection_without_matching_face_no_clash(self):
        """Far carries no material: a materials selection keeps none of
        its faces, so no pair is built at all."""
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            target_face_selection={"materials": ["Glass"]},
            distance=True,
            min_distance=5.0,
        )
        self.assertEqual(len(rule.result), 0)

    def test_same_element_in_both_selections_is_skipped(self):
        """An element is not checked against itself."""
        rule = self.run_rule(
            "Near", "Near", distance=True, min_distance=0.1
        )
        self.assertEqual(len(rule.result), 0)

    # ---- Selection modes: ObjetVsFace and FaceVsFace
    #
    # A side of the rule is used as its whole object when no
    # FaceSelection is provided, and as its selected faces only
    # otherwise. The nominal section covers FaceVsFace and the
    # whole-target section covers FaceVsObjet; the tests below pin
    # ObjetVsFace (the whole source against selected target faces)
    # and the exact pairing of FaceVsFace.

    def test_object_vs_face_distance_min(self):
        """ObjetVsFace: without Source_Face_Selection the whole Near
        object (12 triangles) is checked against the faces of Far
        oriented toward Near (2 triangles): 24 pairs, the ones
        holding the 2 m gap clash under a 2.10 m requirement (the
        mirror image of the whole-target test)."""
        rule = self.run_rule(
            target_face_selection=self.toward_source(),
            distance=True,
            min_distance=2.10,
            max_distance=100
        )

        self.assertEqual(len(rule.result), 19)
        for result in rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)
            self.assertEqual(result.source.Name, "Near")
            self.assertEqual(result.target.Name, "Far")
            self.assertEqual(result.check, "distance")
            self.assertAlmostEqual(result.value, 2.0, places=6)

    def test_object_vs_face_distance_within_bounds(self):
        """ObjetVsFace: every pair of the whole Near object against
        the faces of Far oriented toward Near lies within [1.5, 3.5]:
        no clash."""
        rule = self.run_rule(
            target_face_selection=self.toward_source(),
            distance=True,
            min_distance=1.5,
            max_distance=3.5,
        )
        self.assertEqual(len(rule.result), 0)

    def test_object_vs_face_orientation(self):
        """ObjetVsFace: the normals of the whole Near object (12
        triangles) against the faces of Far oriented toward Near (2
        triangles). Against the -X normal of Far, the +X face of Near
        measures 180 degrees (4 pairs), the -X face 0 degrees (4
        pairs) and the 4 side faces 90 degrees (16 pairs). Under a
        180 degree requirement only the opposing pairs pass: 20
        clashes; under a 90 degree requirement the side pairs pass:
        8 clashes (4 at 180 degrees, 4 at 0 degrees)."""
        rule = self.run_rule(
            target_face_selection=self.toward_source(),
            orientation=True,
            angle=180,
            angle_tolerance=0,
        )
        self.assertEqual(len(rule.result), 20)
        self.assertEqual({result.check for result in rule.result}, {"orientation"})

        rule = self.run_rule(
            target_face_selection=self.toward_source(),
            orientation=True,
            angle=90,
            angle_tolerance=0,
        )
        self.assertEqual(len(rule.result), 8)
        measured = {}
        for result in rule.result:
            measured[round(result.value)] = (
                measured.get(round(result.value), 0) + 1
            )
        self.assertEqual(measured, {180: 4, 0: 4})

    def test_face_vs_face_pairs_only_the_selected_faces(self):
        """FaceVsFace: each side keeps its 2 facing triangles, so the
        rule pairs exactly 2 x 2 = 4 faces. With a 0 m requirement
        every pair clashes: any face leaking out of a selection would
        raise the count above 4."""
        rule = self.run_rule(
            source_face_selection=self.toward_target(),
            target_face_selection=self.toward_source(),
            distance=True,
            max_distance=0.0,
        )

        self.assertEqual(len(rule.result), 4)
        for result in rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)
            self.assertEqual(result.source.Name, "Near")
            self.assertEqual(result.target.Name, "Far")
            self.assertAlmostEqual(result.face_a["normal"][0], 1.0, places=6)
            self.assertAlmostEqual(result.face_b["normal"][0], -1.0, places=6)
            self.assertAlmostEqual(result.face_a["area"], 0.5, places=6)
            self.assertAlmostEqual(result.face_b["area"], 0.5, places=6)

    # ---- Invalid parameters

    def test_invalid_parameters_raise_value_error(self):
        source = self.select("Near")
        target = self.select("Far")

        with self.assertRaises(ValueError):
            TwoObjectsFace(source, target)  # no check enabled
        with self.assertRaises(ValueError):
            TwoObjectsFace(source, target, orientation=True)  # angle missing
        with self.assertRaises(ValueError):
            TwoObjectsFace(source, target, orientation=True, angle=190)
        with self.assertRaises(ValueError):
            TwoObjectsFace(
                source, target, orientation=True, angle=90, angle_tolerance=-1
            )
        with self.assertRaises(ValueError):
            TwoObjectsFace(
                source, target, distance=True, min_distance=2.0, max_distance=1.0
            )
        with self.assertRaises(ValueError):
            TwoObjectsFace(source, target, distance=True, min_distance=-1.0)
        with self.assertRaises(ValueError):
            TwoObjectsFace(
                source, target, intersection=True, intersection_tolerance=-0.1
            )
        with self.assertRaises(ValueError):
            TwoObjectsFace(
                source,
                target,
                source_face_selection={"color": "red"},
                distance=True,
                min_distance=1.0,
            )
        with self.assertRaises(ValueError):
            TwoObjectsFace(
                source,
                target,
                target_face_selection={"interior_exterior": "Interior"},
                distance=True,
                min_distance=1.0,
            )


if __name__ == "__main__":
    unittest.main()
