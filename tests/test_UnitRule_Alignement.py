"""
Test suite for the Alignement rule (doc/ComplexRules/Alignement.md).

The test models are generated with the ifcopenshell API: the IFC test
models do not contain known alignment cases (rows of columns, facades).
Each model is written to a temporary file, loaded through a RuleFile like
any other rule.
"""
import math
import os
import shutil
import tempfile
import unittest

import ifcopenshell
import ifcopenshell.api
import sys

sys.path.insert(0, "./ifcclash_plus")

from Rules import Alignement
from RuleClass import SelectFacet, RuleFile, ClashResultOneObject
from clash_utils import (
    alignment_clash_flags,
    least_squares_line_2d,
    least_squares_line_3d,
    least_squares_plane_3d,
    point_line_distance,
    point_plane_distance,
)
from ifctester import ids


def make_model(path, elements):
    """Write a small IFC file with box elements.

    elements: list of (ifc_class, name, (x, y, z), plan_angle_rad,
              profile_x, profile_y, depth). The profile is extruded along
              Z from the element placement, so depth is the height.
    """
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
    for ifc_class, name, (x, y, z), angle, profile_x, profile_y, depth in elements:
        element = ifcopenshell.api.run(
            "root.create_entity", file, ifc_class=ifc_class, name=name
        )
        cos_a, sin_a = math.cos(angle), math.sin(angle)
        ifcopenshell.api.run(
            "geometry.edit_object_placement",
            file,
            product=element,
            matrix=((cos_a, -sin_a, 0, x), (sin_a, cos_a, 0, y), (0, 0, 1, z), (0, 0, 0, 1)),
        )
        profile = file.createIfcRectangleProfileDef(
            "AREA",
            None,
            file.createIfcAxis2Placement2D(
                file.createIfcCartesianPoint((0.0, 0.0)), None
            ),
            float(profile_x),
            float(profile_y),
        )
        representation = ifcopenshell.api.run(
            "geometry.add_profile_representation",
            file,
            context=body,
            profile=profile,
            depth=float(depth),
        )
        ifcopenshell.api.run(
            "geometry.assign_representation",
            file,
            product=element,
            representation=representation,
        )
    file.write(path)


def column(name, x, y, z=0.0, section=0.3, height=3.0):
    return ("IfcColumn", name, (x, y, z), 0.0, section, section, height)


def wall(name, x, y, angle=0.0, length=4.0, thickness=0.2, height=3.0):
    return ("IfcWall", name, (x, y, 0.0), angle, length, thickness, height)


class TestAlignement(unittest.TestCase):
    """The Alignement rule on generated models."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, True)

    def write_model(self, file_name, elements):
        path = os.path.join(self.temp_dir, file_name)
        make_model(path, elements)
        return path

    def run_rule(self, path, entity="IFCCOLUMN", **parameters):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [path]
        select = SelectFacet()
        select.applicability = [ids.Entity(name=entity)]
        rule = Alignement(select, **parameters)
        rule_file.contains = [rule]
        rule_file.run()
        return rule

    # ---- Nominal

    def test_vertical_row_outlier_clashes(self):
        """A row of columns, one column offset in plan: the outlier clashes."""
        path = self.write_model(
            "row.ifc",
            [column(f"C{x}", x, 0.0) for x in (0, 2, 4, 8, 10, 12)]
            + [column("C_offset", 6, 0.5)],
        )

        rule = self.run_rule(path, axis="Vertical", tolerance=0.15)

        self.assertEqual(len(rule.result), 1)
        result = rule.result[0]
        self.assertIsInstance(result, ClashResultOneObject)
        self.assertEqual(result.source.Name, "C_offset")
        # Offset guides the correction: ~0.43 m from the fitted line.
        self.assertGreater(result.offset, 0.35)
        self.assertLess(result.offset, 0.5)

    def test_vertical_alignment_info(self):
        """The rule exposes the fitted line and its member objects."""
        path = self.write_model(
            "row.ifc",
            [column(f"C{x}", x, 0.0) for x in (0, 2, 4, 8, 10, 12)]
            + [column("C_offset", 6, 0.5)],
        )

        rule = self.run_rule(path, axis="Vertical", tolerance=0.15)

        self.assertIsNotNone(rule.alignment)
        self.assertEqual(rule.alignment["orientation"], "Vertical")
        self.assertEqual(rule.alignment["element"], "Line")
        self.assertEqual(len(rule.alignment["members"]), 6)
        member_names = [member.Name for member in rule.alignment["members"]]
        self.assertNotIn("C_offset", member_names)

    def test_auto_detection_matches_vertical(self):
        """Without axis, the vertical set is detected and gives the same clash."""
        path = self.write_model(
            "row.ifc",
            [column(f"C{x}", x, 0.0) for x in (0, 2, 4, 8, 10, 12)]
            + [column("C_offset", 6, 0.5)],
        )

        rule = self.run_rule(path, tolerance=0.15)

        self.assertEqual(len(rule.result), 1)
        self.assertEqual(rule.result[0].source.Name, "C_offset")
        self.assertEqual(rule.alignment["orientation"], "Vertical")

    def test_horizontal_plane_facade_outlier_clashes(self):
        """Facade walls in one plane, one wall behind the facade: clash."""
        path = self.write_model(
            "facade.ifc",
            [
                wall("W_left", 0.0, 0.0),
                wall("W_middle", 6.0, 0.0),
                wall("W_right", 12.0, 0.0),
                wall("W_behind", 6.0, 2.0),
            ],
        )

        rule = self.run_rule(
            path,
            entity="IFCWALL",
            axis="Horizontal",
            alignment_type="Plane",
            tolerance=1.0,
        )

        self.assertEqual(len(rule.result), 1)
        self.assertEqual(rule.result[0].source.Name, "W_behind")
        self.assertGreater(rule.result[0].offset, 1.0)
        self.assertEqual(rule.alignment["element"], "Plane")

    def test_horizontal_line_crossing_wall_clashes(self):
        """Wall segments on one axis, one perpendicular wall: clash."""
        path = self.write_model(
            "line.ifc",
            [
                wall("W_axis_0", 0.0, -2.0),
                wall("W_axis_1", 6.0, -2.0),
                wall("W_axis_2", 12.0, -2.0),
                wall("W_crossing", 6.0, -2.0, angle=math.pi / 2),
            ],
        )

        rule = self.run_rule(
            path,
            entity="IFCWALL",
            axis="Horizontal",
            alignment_type="Line",
            tolerance=0.1,
        )

        self.assertEqual(len(rule.result), 1)
        self.assertEqual(rule.result[0].source.Name, "W_crossing")
        self.assertGreater(rule.result[0].offset, 1.0)

    # ---- Negative

    def test_vertical_row_aligned_no_clash(self):
        """A clean row of columns raises no clash."""
        path = self.write_model(
            "row_ok.ifc", [column(f"C{x}", x, 0.0) for x in (0, 2, 4, 6, 8)]
        )

        rule = self.run_rule(path, axis="Vertical", tolerance=0.15)

        self.assertEqual(len(rule.result), 0)
        self.assertEqual(len(rule.alignment["members"]), 5)

    def test_stacked_columns_same_axis_no_clash(self):
        """Columns stacked across storeys on the same axis are aligned.

        Their plan projections coincide, the fitted line is degenerate and
        all the offsets are zero.
        """
        path = self.write_model(
            "stack.ifc",
            [
                column("C_ground", 0.0, 0.0, z=0.0),
                column("C_storey1", 0.0, 0.0, z=3.5),
                column("C_storey2", 0.0, 0.0, z=7.0),
            ],
        )

        rule = self.run_rule(path, axis="Vertical", tolerance=0.10)

        self.assertEqual(len(rule.result), 0)

    def test_horizontal_plane_negative(self):
        """Four walls in one facade plane raise no clash."""
        path = self.write_model(
            "facade_ok.ifc",
            [wall(f"W{i}", 6.0 * i, 0.0) for i in range(4)],
        )

        rule = self.run_rule(
            path,
            entity="IFCWALL",
            axis="Horizontal",
            alignment_type="Plane",
            tolerance=0.5,
        )

        self.assertEqual(len(rule.result), 0)

    def test_horizontal_line_collinear_no_clash(self):
        """Wall segments continuing on the same axis raise no clash."""
        path = self.write_model(
            "line_ok.ifc",
            [
                wall("W_axis_0", 0.0, -2.0),
                wall("W_axis_1", 6.0, -2.0),
                wall("W_axis_2", 12.0, -2.0),
            ],
        )

        rule = self.run_rule(
            path,
            entity="IFCWALL",
            axis="Horizontal",
            alignment_type="Line",
            tolerance=0.1,
        )

        self.assertEqual(len(rule.result), 0)

    # ---- Bornes (limit values, on the decision helper)

    def test_group_tolerance_is_inclusive(self):
        """An object at exactly Tolerance belongs to the group."""
        flags = alignment_clash_flags([0.0, 0.1, 0.100001], tolerance=0.1, min_group=1)
        self.assertEqual(flags, [False, False, True])

    def test_group_at_min_group_is_valid(self):
        """A group of exactly Min_Group members is a valid alignment."""
        offsets = [0.0, 0.0, 0.0, 5.0]
        flags = alignment_clash_flags(offsets, tolerance=0.1, min_group=3)
        self.assertEqual(flags, [False, False, False, True])

    def test_group_below_min_group_all_clash(self):
        """A group one member short invalidates the alignment: all clash."""
        offsets = [0.0, 0.0, 5.0, 5.0]
        flags = alignment_clash_flags(offsets, tolerance=0.1, min_group=3)
        self.assertEqual(flags, [True, True, True, True])

    def test_two_distinct_positions_fit_exactly(self):
        """Two distinct plan positions define the fitted line exactly.

        Even a column 0.5 m off the others gets a zero offset when the set
        has only two distinct positions: the fitted line goes through both.
        This is the spec limitation that motivates Min_Group = 3: at least
        three distinct positions are needed to detect an off-axis object.
        """
        origin, direction = least_squares_line_2d([(0, 0), (0, 0), (0.5, 0)])
        offsets = [
            point_line_distance(point, origin, direction)
            for point in [(0, 0), (0, 0), (0.5, 0)]
        ]
        self.assertTrue(all(offset < 1e-9 for offset in offsets))

    # ---- Cas limites

    def test_empty_selection_no_clash_no_crash(self):
        """An empty selection produces no result and does not crash."""
        path = self.write_model("row_ok.ifc", [column("C0", 0.0, 0.0)])

        rule = self.run_rule(path, entity="IFCROOF", tolerance=0.1)

        self.assertEqual(len(rule.result), 0)
        self.assertIsNone(rule.alignment)

    def test_single_object_clashes_below_min_group(self):
        """A lone object cannot validate an alignment of Min_Group objects."""
        path = self.write_model("one.ifc", [column("C0", 0.0, 0.0)])

        rule = self.run_rule(path, tolerance=0.1)
        self.assertEqual(len(rule.result), 1)

        rule = self.run_rule(path, tolerance=0.1, min_group=1)
        self.assertEqual(len(rule.result), 0)

    def test_two_objects_clash_below_min_group(self):
        """Two objects alone always align, so Min_Group = 3 invalidates them."""
        path = self.write_model(
            "two.ifc", [column("C0", 0.0, 0.0), column("C1", 4.0, 0.0)]
        )

        rule = self.run_rule(path, tolerance=0.1)
        self.assertEqual(len(rule.result), 2)

        rule = self.run_rule(path, tolerance=0.1, min_group=2)
        self.assertEqual(len(rule.result), 0)

    def test_flat_object_degenerate_geometry_no_crash(self):
        """A flat slab (zero volume) joins an alignment without crashing."""
        path = self.write_model(
            "flat.ifc",
            [
                wall("W_axis_0", 0.0, -2.0),
                wall("W_axis_1", 6.0, -2.0),
                wall("W_axis_2", 12.0, -2.0),
                ("IfcSlab", "S_flat", (18.0, -2.0, 0.0), 0.0, 4.0, 0.2, 0.002),
            ],
        )

        rule = self.run_rule(
            path,
            entity="IFCWALL,IFCSLAB",
            axis="Horizontal",
            alignment_type="Line",
            tolerance=0.1,
        )

        self.assertEqual(len(rule.result), 0)

    def test_invalid_parameters_raise_value_error(self):
        select = SelectFacet()
        select.applicability = [ids.Entity(name="IFCCOLUMN")]

        with self.assertRaises(ValueError):
            Alignement(select, axis="Diagonal", tolerance=0.1)
        with self.assertRaises(ValueError):
            Alignement(select, alignment_type="Curve", tolerance=0.1)
        with self.assertRaises(ValueError):
            Alignement(select, tolerance=None)
        with self.assertRaises(ValueError):
            Alignement(select, tolerance=-1.0)
        with self.assertRaises(ValueError):
            Alignement(select, tolerance=0.1, min_group=0)


class TestAlignmentUtilities(unittest.TestCase):
    """The least-squares fitting helpers of clash_utils used by Alignement."""

    def test_line_2d_exact_fit(self):
        origin, direction = least_squares_line_2d([(0, 0), (4, 0), (8, 0)])
        offsets = [
            point_line_distance(point, origin, direction)
            for point in [(0, 0), (4, 0), (8, 0)]
        ]
        self.assertTrue(all(offset < 1e-9 for offset in offsets))
        self.assertAlmostEqual(abs(float(direction[1])), 0.0, places=9)

    def test_line_2d_coincident_points_degenerate(self):
        origin, direction = least_squares_line_2d([(1.0, 1.0), (1.0, 1.0)])
        offsets = [
            point_line_distance(point, origin, direction)
            for point in [(1.0, 1.0), (1.0, 1.0)]
        ]
        self.assertTrue(all(offset < 1e-9 for offset in offsets))

    def test_line_2d_spreads_outlier_offset(self):
        """One outlier among collinear points: every point gets a share."""
        origin, direction = least_squares_line_2d(
            [(0, 0), (2, 0), (4, 0), (8, 0), (10, 0), (12, 0), (6, 0.5)]
        )
        offsets = [
            point_line_distance(point, origin, direction)
            for point in [(0, 0), (2, 0), (4, 0), (8, 0), (10, 0), (12, 0), (6, 0.5)]
        ]
        # The outlier keeps the largest offset, the inliers stay small.
        self.assertGreater(offsets[-1], 0.4)
        self.assertTrue(all(offset < 0.1 for offset in offsets[:-1]))

    def test_line_3d_and_plane_3d_on_collinear_points(self):
        points = [(0.0, 0.0, 1.0), (1.0, 0.0, 1.0), (2.0, 0.0, 1.0)]
        origin, direction = least_squares_line_3d(points)
        self.assertAlmostEqual(
            point_line_distance((5.0, 0.0, 1.0), origin, direction), 0.0, places=9
        )
        plane_origin, normal = least_squares_plane_3d(points)
        # Collinear points: any plane containing the line fits them.
        self.assertAlmostEqual(
            point_plane_distance((5.0, 0.0, 1.0), plane_origin, normal), 0.0, places=9
        )

    def test_point_plane_distance(self):
        self.assertAlmostEqual(
            point_plane_distance((0.0, 2.0, 5.0), (0.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
            2.0,
        )

    def test_alignment_clash_flags_empty(self):
        self.assertEqual(alignment_clash_flags([], tolerance=0.1, min_group=3), [])


if __name__ == "__main__":
    unittest.main()
