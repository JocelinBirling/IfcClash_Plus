"""
Test suite for the SurfaceRecover rule (doc/2ObjectsRules/SurfaceRecover.md).

The models come from IFC_Test_Model/IFC_Model: the SlabA_RecoverTop_*
models were built for this rule (a slab hovering 0.9 m above its support,
covering 100% or 50% of it — hence the tolerance of 1.0 m in the tests),
and the CubeA_TouchFace / CubeA_NextTo models cover the lateral contact
and the out-of-contact cases.

Execution (from the repository root):
    python -m pytest tests/test_SurfaceRecover.py -v
"""
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, "./ifcclash_plus")

from Rules import SurfaceRecover
from RuleClass import SelectFacet, RuleFile, ClashResultTwoObjects
from clash_utils import (
    contact_area_between_triangle_sets,
    covering_out_of_bounds,
    extreme_triangles,
    triangles_projected_area,
)
from ifctester import ids

MODEL_DIR = "IFC_Test_Model/IFC_Model"


def select_by_name(name):
    select = SelectFacet()
    select.applicability = [ids.Attribute(name="Name", value=name)]
    return select


class TestSurfaceRecover(unittest.TestCase):
    """The SurfaceRecover rule on the IFC test models."""

    def run_rule(self, model, source, target, **parameters):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [os.path.join(MODEL_DIR, model)]
        parameters["state"]="Display_Result"
        rule = SurfaceRecover(
            select_by_name(source), select_by_name(target), **parameters
        )
        rule_file.contains = [rule]
        rule_file.run()
        return rule

    def bottom_parameters(self, **overrides):
        """The parameters of the RecoverTop models: the slab hovers 0.9 m
        above its support, so the contact tolerance must exceed 0.9 m."""
        parameters = {
            "direction": "Bottom",
            "reference": "Target",
            "tolerance": 1.0,
        }
        parameters.update(overrides)
        return parameters

    # ---- Nominal (the RecoverTop models, covering of the target)

    def test_full_coverage_compliant_no_clash(self):
        """The slab covers 100% of the cuboid top: 100% >= 95%, no clash."""
        rule = self.run_rule(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "CuboidB",
            **self.bottom_parameters(min_covering="95%"),
        )
        self.assertEqual(len(rule.result), 0)

    def test_full_coverage_below_min_clashes(self):
        """A minimum above the covering raises a clash with the pair data."""
        rule = self.run_rule(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "CuboidB",
            **self.bottom_parameters(min_covering="101%"),
        )

        self.assertEqual(len(rule.result), 1)
        result = rule.result[0]
        self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertEqual(result.source.Name, "SlabA")
        self.assertEqual(result.target.Name, "CuboidB")
        # Contact = the whole 2 x 1 m cuboid top, 100% of the reference.
        self.assertAlmostEqual(result.surface_contact_area, 2.0, places=3)
        self.assertAlmostEqual(result.ratio, 100.0, places=3)
        # The faces used: source bottom face vs target top face.
        self.assertAlmostEqual(result.source_face["area"], 9.0, places=3)
        self.assertAlmostEqual(result.target_face["area"], 2.0, places=3)
        self.assertAlmostEqual(result.distance_between, 0.9, places=3)

    def test_half_coverage_below_min_clashes(self):
        """The slab covers 50% of the cuboid top: 50% < 70%, clash."""
        rule = self.run_rule(
            "SlabA_RecoverTop_CuboidB_50%.ifc",
            "SlabA",
            "CuboidB",
            **self.bottom_parameters(min_covering="70%"),
        )

        self.assertEqual(len(rule.result), 1)
        self.assertAlmostEqual(rule.result[0].surface_contact_area, 1.0, places=3)
        self.assertAlmostEqual(rule.result[0].ratio, 50.0, places=3)

    def test_half_coverage_compliant_no_clash(self):
        """50% >= 40%: the partial support is accepted."""
        rule = self.run_rule(
            "SlabA_RecoverTop_CuboidB_50%.ifc",
            "SlabA",
            "CuboidB",
            **self.bottom_parameters(min_covering="40%"),
        )
        self.assertEqual(len(rule.result), 0)

    def test_curved_support_full_coverage(self):
        """A slab on a cylinder top covers 100% of the (tessellated) disk."""
        rule = self.run_rule(
            "SlabA_RecoverTop_CylinderA_100%.ifc",
            "SlabA",
            "CylinderA",
            **self.bottom_parameters(min_covering="95%"),
        )
        self.assertEqual(len(rule.result), 0)

        rule = self.run_rule(
            "SlabA_RecoverTop_CylinderA_100%.ifc",
            "SlabA",
            "CylinderA",
            **self.bottom_parameters(min_covering="101%"),
        )
        self.assertEqual(len(rule.result), 1)
        self.assertAlmostEqual(rule.result[0].ratio, 100.0, places=2)

    def test_curved_support_half_coverage(self):
        """A slab on half a cylinder top covers ~50% of the disk."""
        rule = self.run_rule(
            "SlabA_RecoverTop_CylinderA_50%.ifc",
            "SlabA",
            "CylinderA",
            **self.bottom_parameters(min_covering="60%"),
        )
        self.assertEqual(len(rule.result), 1)
        self.assertAlmostEqual(rule.result[0].ratio, 50.0, places=2)

    # ---- Reference face

    def test_reference_source_changes_denominator(self):
        """Reference = Source: the ratio is relative to the 9 m2 slab
        bottom, so the same full coverage is only ~22%."""
        rule = self.run_rule(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "CuboidB",
            **self.bottom_parameters(reference="Source", min_covering="30%"),
        )
        self.assertEqual(len(rule.result), 1)
        self.assertAlmostEqual(rule.result[0].ratio, 100.0 * 2.0 / 9.0, places=2)

        rule = self.run_rule(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "CuboidB",
            **self.bottom_parameters(reference="Source", min_covering="20%"),
        )
        self.assertEqual(len(rule.result), 0)

    # ---- Absolute bounds

    def test_absolute_bound_in_m2(self):
        """An absolute minimum is an area in m2, the reference is ignored."""
        rule = self.run_rule(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "CuboidB",
            **self.bottom_parameters(min_covering=1.5),
        )
        self.assertEqual(len(rule.result), 0)

        rule = self.run_rule(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "CuboidB",
            **self.bottom_parameters(min_covering=2.5),
        )
        self.assertEqual(len(rule.result), 1)

    # ---- Max covering

    def test_max_covering_above_clashes(self):
        """A maximum below the covering raises a clash (over-covering)."""
        rule = self.run_rule(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "CuboidB",
            **self.bottom_parameters(max_covering="95%"),
        )
        self.assertEqual(len(rule.result), 1)

        rule = self.run_rule(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "CuboidB",
            **self.bottom_parameters(max_covering="101%"),
        )
        self.assertEqual(len(rule.result), 0)

    # ---- Lateral contact with the Auto direction

    def test_lateral_auto_contact(self):
        """Two cubes touching on their side faces, direction Auto: the
        contact is 1 m2 (the whole touching face)."""
        rule = self.run_rule(
            "CubeA_TouchFace_CubeB.ifc",
            "CubeA",
            "CubeB",
            direction="Auto",
            tolerance=0.01,
            min_covering=1.5,
        )
        self.assertEqual(len(rule.result), 1)
        result = rule.result[0]
        self.assertAlmostEqual(result.surface_contact_area, 1.0, places=3)
        self.assertAlmostEqual(result.ratio, 100.0, places=3)

        rule = self.run_rule(
            "CubeA_TouchFace_CubeB.ifc",
            "CubeA",
            "CubeB",
            direction="Auto",
            tolerance=0.01,
            min_covering=0.9,
        )
        self.assertEqual(len(rule.result), 0)

    def test_auto_direction_vector_case(self):
        """Direction given as a 3D vector (the lateral +Y axis)."""
        rule = self.run_rule(
            "CubeA_TouchFace_CubeB.ifc",
            "CubeA",
            "CubeB",
            direction=(0.0, 2.0, 0.0),
            tolerance=0.01,
            min_covering=1.5,
        )
        self.assertEqual(len(rule.result), 1)

    # ---- Negative: pairs not in contact

    def test_pair_not_in_contact_no_result(self):
        """Two cubes 1 m apart with the default tolerance: no contact, no
        result even with an impossible minimum."""
        rule = self.run_rule(
            "CubeA_NextTo_CubeB_1m.ifc",
            "CubeA",
            "CubeB",
            direction="Bottom",
            tolerance=0.001,
            min_covering="150%",
        )
        self.assertEqual(len(rule.result), 0)

    # ---- Cas limites

    def test_empty_selection_no_crash(self):
        """A selection without matching element produces no result."""
        rule = self.run_rule(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "MissingObject",
            **self.bottom_parameters(min_covering="50%"),
        )
        self.assertEqual(len(rule.result), 0)

    def test_no_bounds_never_clashes(self):
        """Without any bound, only the provided bounds are checked:
        nothing is checked, no clash."""
        rule = self.run_rule(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "CuboidB",
            **self.bottom_parameters(),
        )
        self.assertEqual(len(rule.result), 0)

    def test_invalid_parameters_raise_value_error(self):
        source = select_by_name("SlabA")
        target = select_by_name("CuboidB")

        with self.assertRaises(ValueError):
            SurfaceRecover(source, target, direction="Diagonal")
        with self.assertRaises(ValueError):
            SurfaceRecover(source, target, direction=(0.0, 0.0, 0.0))
        with self.assertRaises(ValueError):
            SurfaceRecover(source, target, direction=(1.0, 2.0))
        with self.assertRaises(ValueError):
            SurfaceRecover(source, target, reference="Middle")
        with self.assertRaises(ValueError):
            SurfaceRecover(source, target, tolerance=-1.0)
        with self.assertRaises(ValueError):
            SurfaceRecover(source, target, min_covering="10")
        with self.assertRaises(ValueError):
            SurfaceRecover(source, target, max_covering="abc%")

    def test_direction_shortcuts_are_normalized_vectors(self):
        source = select_by_name("SlabA")
        target = select_by_name("CuboidB")
        rule = SurfaceRecover(source, target, direction="Top")
        self.assertEqual(rule.direction, (0.0, 0.0, 1.0))
        rule = SurfaceRecover(source, target, direction="Bottom")
        self.assertEqual(rule.direction, (0.0, 0.0, -1.0))
        rule = SurfaceRecover(source, target, direction=(0.0, 0.0, 3.0))
        self.assertAlmostEqual(rule.direction[2], 1.0)


class TestSurfaceRecoverUtilities(unittest.TestCase):
    """The contact helpers of clash_utils used by SurfaceRecover."""

    def open_box_mesh(self):
        """An open box: a bottom face at z=0 and an inner ceiling at z=1
        facing down, both candidates along -Z but only the bottom one is
        extreme (the ceiling is a face of a hole).
        """
        vertices = np.array(
            [
                [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0],
                [0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 1.0], [0.0, 1.0, 1.0],
            ]
        )
        faces = np.array(
            [
                # Bottom face, normals pointing down (-Z).
                [0, 2, 1], [0, 3, 2],
                # Inner ceiling, normals pointing down (-Z).
                [4, 6, 5], [4, 7, 6],
                # Side walls, to make the mesh a closed box.
                [0, 1, 5], [0, 5, 4],
                [1, 2, 6], [1, 6, 5],
                [2, 3, 7], [2, 7, 6],
                [3, 0, 4], [3, 4, 7],
            ]
        )
        return vertices, faces

    def test_extreme_triangles_ignores_holes(self):
        """Faces of holes pointing to the same direction are ignored."""
        vertices, faces = self.open_box_mesh()

        triangles = extreme_triangles(
            vertices, faces, (0.0, 0.0, -1.0), tolerance=0.001
        )

        # Only the 2 bottom triangles, the ceiling at z=1 is not extreme.
        self.assertEqual(len(triangles), 2)
        self.assertAlmostEqual(
            triangles_projected_area(triangles, (0.0, 0.0, -1.0)), 1.0, places=9
        )

    def test_extreme_triangles_empty_mesh(self):
        triangles = extreme_triangles(
            np.zeros((0, 3)), np.zeros((0, 3), dtype=int), (0.0, 0.0, 1.0),
            tolerance=0.1,
        )
        self.assertEqual(len(triangles), 0)

    def facing_squares(self, overlap, distance, same_orientation=False):
        """Two unit squares facing each other along -Z/+Y.

        Returns two triangle sets: a (2, 3, 3) source set at y=distance
        with normals pointing -Y, and a target set at y=0 with normals
        pointing +Y. The source is shifted so that the projected overlap
        is `overlap`.
        """
        shift = 1.0 - overlap
        source = np.array(
            [
                [[0.0 + shift, distance, 0.0], [1.0 + shift, distance, 0.0],
                 [1.0 + shift, distance, 1.0]],
                [[0.0 + shift, distance, 0.0], [1.0 + shift, distance, 1.0],
                 [0.0 + shift, distance, 1.0]],
            ]
        )
        # Source normals must point towards the target: -Y.
        v1 = source[:, 1] - source[:, 0]
        v2 = source[:, 2] - source[:, 0]
        if not (np.cross(v1, v2).mean(axis=0)[1] < 0):
            source = source[:, ::-1, :]

        target = np.array(
            [
                [[0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 0.0, 1.0]],
                [[0.0, 0.0, 0.0], [1.0, 0.0, 1.0], [0.0, 0.0, 1.0]],
            ]
        )
        # As built, both sets have -Y normals: flip the target so that it
        # faces the source (+Y), unless the test asks for the same side.
        if not same_orientation:
            target = target[:, ::-1, :]

        return source, target

    def test_contact_area_partial_overlap(self):
        source, target = self.facing_squares(overlap=0.5, distance=0.5)
        contact = contact_area_between_triangle_sets(
            source, target, (0.0, -1.0, 0.0), tolerance=1.0
        )
        self.assertAlmostEqual(contact, 0.5, places=9)

    def test_contact_area_full_overlap(self):
        source, target = self.facing_squares(overlap=1.0, distance=0.0)
        contact = contact_area_between_triangle_sets(
            source, target, (0.0, -1.0, 0.0), tolerance=0.001
        )
        self.assertAlmostEqual(contact, 1.0, places=9)

    def test_contact_area_distance_beyond_tolerance(self):
        source, target = self.facing_squares(overlap=1.0, distance=2.0)
        contact = contact_area_between_triangle_sets(
            source, target, (0.0, -1.0, 0.0), tolerance=1.0
        )
        self.assertAlmostEqual(contact, 0.0, places=9)

    def test_contact_area_requires_opposite_normals(self):
        source, target = self.facing_squares(
            overlap=1.0, distance=0.5, same_orientation=True
        )
        contact = contact_area_between_triangle_sets(
            source, target, (0.0, -1.0, 0.0), tolerance=1.0
        )
        self.assertAlmostEqual(contact, 0.0, places=9)

    # ---- Bornes of the covering bounds (inclusive)

    def test_covering_bound_at_exact_value_is_compliant(self):
        self.assertFalse(
            covering_out_of_bounds(2.0, 100.0, ("relative", 100.0), ("relative", 100.0))
        )
        self.assertFalse(
            covering_out_of_bounds(2.0, 100.0, ("absolute", 2.0), ("absolute", 2.0))
        )

    def test_covering_below_min_clashes(self):
        self.assertTrue(covering_out_of_bounds(1.9, 99.0, ("relative", 100.0), None))

    def test_covering_above_max_clashes(self):
        self.assertTrue(covering_out_of_bounds(2.1, 101.0, None, ("relative", 100.0)))

    def test_relative_bound_without_ratio_clashes(self):
        """A relative bound cannot be verified without a reference face:
        the pair clashes."""
        self.assertTrue(covering_out_of_bounds(1.0, None, ("relative", 50.0), None))
        self.assertFalse(covering_out_of_bounds(1.0, None, ("absolute", 0.5), None))


if __name__ == "__main__":
    unittest.main()
