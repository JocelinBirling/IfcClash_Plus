"""
Test suite for the ClearanceAxisToAxis rule
(doc/2ObjectsRules/ClearanceAxisToAxis.md).

The models are generated with the ifcopenshell API: slender boxes as
linear objects (cable trays, pipe runs) with known axis positions, so
the expected axis-to-axis distances are exact.

Execution (from the repository root):
    python -m pytest tests/test_UnitRule_ClearanceAxisToAxis.py -v
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

from Rules import ClearanceAxisToAxis
from RuleClass import SelectFacet, RuleFile, ClashResultTwoObjects
from CustomOBB import create_obb_from_TopoDs_Shape
from clash_utils import (
    axial_overlap,
    axis_angle,
    obb_long_axis,
    parallel_line_offset,
    segment_segment_distance,
)
from ifctester import ids

from tests.test_structure_ResultShape import assert_result_shape


def make_model(path, elements):
    """Write a small IFC file with box elements.

    elements: list of (name, x, y, z, dx, dy, height). The rectangular
    profile is centered on the placement in x and y, the extrusion goes
    from z to z + height.
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
    for name, x, y, z, dx, dy, height in elements:
        element = ifcopenshell.api.run(
            "root.create_entity", file, ifc_class="IfcBuildingElementProxy", name=name
        )
        ifcopenshell.api.run(
            "geometry.edit_object_placement",
            file,
            product=element,
            matrix=((1, 0, 0, x), (0, 1, 0, y), (0, 0, 1, z), (0, 0, 0, 1)),
        )
        profile = file.createIfcRectangleProfileDef(
            "AREA",
            None,
            file.createIfcAxis2Placement2D(
                file.createIfcCartesianPoint((0.0, 0.0)), None
            ),
            float(dx),
            float(dy),
        )
        representation = ifcopenshell.api.run(
            "geometry.add_profile_representation",
            file,
            context=body,
            profile=profile,
            depth=float(height),
        )
        ifcopenshell.api.run(
            "geometry.assign_representation",
            file,
            product=element,
            representation=representation,
        )
    file.write(path)


def box(name, x, y=0.0, z=0.0, dx=1.0, dy=1.0, height=1.0):
    return (name, x, y, z, dx, dy, height)


class TestClearanceAxisToAxis(unittest.TestCase):
    """The ClearanceAxisToAxis rule on generated models."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, True)

        # Two trays running side by side along x, 0.5 m apart:
        # perpendicular offset between the axes = 0.5 m.
        self.parallel_model = os.path.join(self.temp_dir, "parallel.ifc")
        make_model(
            self.parallel_model,
            [
                box("TrayA", 0.0, dx=4.0, dy=0.1, height=0.1),
                box("TrayB", 0.0, y=0.5, dx=4.0, dy=0.1, height=0.1),
            ],
        )

        # Two collinear pipe runs butted end to end with a 0.1 m gap:
        # offset between the support lines = 0, minimum distance
        # between the segments = 0.1 m.
        self.end_to_end_model = os.path.join(self.temp_dir, "end_to_end.ifc")
        make_model(
            self.end_to_end_model,
            [
                box("PipeA", 0.0, dx=2.0, dy=0.1, height=0.1),
                box("PipeB", 2.1, dx=2.0, dy=0.1, height=0.1),
            ],
        )

        # Two perpendicular pipe runs: minimum distance between the
        # segments = 0.5 m (from the end of A to the axis of B).
        self.perpendicular_model = os.path.join(self.temp_dir, "perpendicular.ifc")
        make_model(
            self.perpendicular_model,
            [
                box("PipeA", 0.0, dx=4.0, dy=0.1, height=0.1),
                box("PipeB", 2.5, y=1.0, dx=0.1, dy=4.0, height=0.1),
            ],
        )

        # A compact block (not linear, ratio 1) next to a pipe run:
        # skin-to-skin distance = 0.95 m.
        self.non_linear_model = os.path.join(self.temp_dir, "non_linear.ifc")
        make_model(
            self.non_linear_model,
            [
                box("Block", 0.0, dx=1.0, dy=1.0, height=1.0),
                box("Pipe", 0.0, y=1.5, dx=4.0, dy=0.1, height=0.1),
            ],
        )

    @staticmethod
    def select(name):
        select = SelectFacet()
        select.applicability = [ids.Attribute(name="Name", value=name)]
        return select

    def run_rule(self, model, first, second, **parameters):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [model]
        rule = ClearanceAxisToAxis(
            self.select(first), self.select(second), **parameters
        )
        rule_file.contains = [rule]
        rule_file.run()
        assert_result_shape(rule)
        return rule

    # ---- Perpendicular mode

    def test_parallel_offset_in_interval(self):
        """Two trays 0.5 m apart, valid between 0.4 and 0.6: no clash."""
        rule = self.run_rule(
            self.parallel_model, "TrayA", "TrayB", mode="Perpendicular",
            min_distance=0.4, max_distance=0.6,
        )
        self.assertEqual(len(rule.result), 0)

    def test_parallel_offset_too_close(self):
        """Two trays 0.5 m apart, required above 0.6: one clash with
        the measured offset as attribute."""
        rule = self.run_rule(
            self.parallel_model, "TrayA", "TrayB", mode="Perpendicular",
            min_distance=0.6, max_distance=1.0,
        )
        self.assertEqual(len(rule.result), 1)
        result = rule.result[0]
        self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertEqual(result.source.Name, "TrayA")
        self.assertEqual(result.target.Name, "TrayB")
        self.assertAlmostEqual(result.info.distance, 0.5, places=4)
        self.assertEqual(result.info.axis_mode, "Perpendicular")
        self.assertFalse(result.info.axis_degraded)
        self.assertAlmostEqual(result.info.angle, 0.0, places=4)

    def test_parallel_offset_too_far(self):
        """Two trays 0.5 m apart, required below 0.4: the interval
        also detects "too far" (coverage holes)."""
        rule = self.run_rule(
            self.parallel_model, "TrayA", "TrayB", mode="Perpendicular",
            min_distance=0.1, max_distance=0.4,
        )
        self.assertEqual(len(rule.result), 1)
        self.assertAlmostEqual(rule.result[0].info.distance, 0.5, places=4)

    def test_tolerance_widens_the_interval(self):
        """The same too-close pair with a 0.1 m tolerance: 0.5 stays
        inside [0.6 - 0.1, 1.0 + 0.1], no clash."""
        rule = self.run_rule(
            self.parallel_model, "TrayA", "TrayB", mode="Perpendicular",
            min_distance=0.6, max_distance=1.0, tolerance=0.1,
        )
        self.assertEqual(len(rule.result), 0)

    def test_perpendicular_mode_falls_back_on_non_parallel(self):
        """The perpendicular offset is meaningless for converging
        axes: the pair automatically falls back to the minimum
        distance between segments."""
        rule = self.run_rule(
            self.perpendicular_model, "PipeA", "PipeB", mode="Perpendicular",
            min_distance=0.1, max_distance=0.4,
        )
        self.assertEqual(len(rule.result), 1)
        result = rule.result[0]
        self.assertAlmostEqual(result.info.distance, 0.5, places=4)
        self.assertEqual(result.info.axis_mode, "MinDistance")
        self.assertAlmostEqual(result.info.angle, 90.0, places=4)

    # ---- MinDistance mode

    def test_min_distance_mode_end_to_end(self):
        """Two collinear runs butted end to end, 0.1 m axis gap:
        valid below 0.15 in MinDistance mode."""
        rule = self.run_rule(
            self.end_to_end_model, "PipeA", "PipeB", mode="MinDistance",
            min_distance=0.05, max_distance=0.15
        )
        self.assertEqual(len(rule.result), 0)

    def test_min_distance_mode_gap_too_wide(self):
        """The same runs with a 0.05 m requirement: one clash carrying
        the end-to-end gap."""
        rule = self.run_rule(
            self.end_to_end_model, "PipeA", "PipeB", mode="MinDistance",
            max_distance=0.05,
        )
        self.assertEqual(len(rule.result), 1)
        result = rule.result[0]
        self.assertAlmostEqual(result.info.distance, 0.1, places=4)
        self.assertEqual(result.info.axis_mode, "MinDistance")

    def test_perpendicular_mode_ignores_collinear_runs(self):
        """The same end-to-end runs in Perpendicular mode: the segments
        do not face each other (a collinear continuation), so they are
        not a side-by-side pair — no result, whatever the interval
        (before the 2026-11-09 fix, their offset 0 came out as "too
        close")."""
        rule = self.run_rule(
            self.end_to_end_model, "PipeA", "PipeB", mode="Perpendicular",
            min_distance=0.05, max_distance=0.15,
        )
        self.assertEqual(len(rule.result), 0)

    # ---- Non-linear objects

    def test_non_linear_pair_skipped(self):
        """A compact block is not linear: with Skip, the pair produces
        no result, whatever its distance."""
        rule = self.run_rule(
            self.non_linear_model, "Block", "Pipe", min_distance=0.1, max_distance=0.5,
        )
        self.assertEqual(len(rule.result), 0)

    def test_non_linear_pair_fallback(self):
        """With Fallback, the pair is measured skin to skin against the
        same interval and the result is flagged degraded."""
        rule = self.run_rule(
            self.non_linear_model, "Block", "Pipe", min_distance=0.1, max_distance=0.5,
            on_non_linear="Fallback",
        )
        self.assertEqual(len(rule.result), 1)
        result = rule.result[0]
        self.assertAlmostEqual(result.info.distance, 0.95, places=4)
        self.assertEqual(result.info.axis_mode, "Fallback")
        self.assertTrue(result.info.axis_degraded)

    def test_non_linear_pair_fallback_in_interval(self):
        """The same fallback measurement inside the interval: no
        clash, the degraded path validates like any other."""
        rule = self.run_rule(
            self.non_linear_model, "Block", "Pipe", min_distance=0.9, max_distance=1.0,
            on_non_linear="Fallback",
        )
        self.assertEqual(len(rule.result), 0)

    # ---- Symmetry

    def test_rule_is_symmetric(self):
        """Source and Target play the same role: swapping the two
        selections gives the same clash and the same distance."""
        forward = ClearanceAxisToAxis(
            self.select("TrayA"), self.select("TrayB"),
            min_distance=0.6, max_distance=1.0,
        )
        backward = ClearanceAxisToAxis(
            self.select("TrayB"), self.select("TrayA"),
            min_distance=0.6, max_distance=1.0,
        )
        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.parallel_model]
        rule_file.contains = [forward, backward]
        rule_file.run()

        self.assertEqual(len(forward.result), 1)
        self.assertEqual(len(backward.result), 1)
        self.assertAlmostEqual(
            forward.result[0].info.distance,
            backward.result[0].info.distance,
            places=4,
        )

    # ---- Parameter validation

    def test_invalid_parameters_raise_value_error(self):
        source = self.select("TrayA")
        target = self.select("TrayB")

        with self.assertRaises(ValueError):
            ClearanceAxisToAxis(source, target, mode="Everywhere")
        with self.assertRaises(ValueError):
            ClearanceAxisToAxis(source, target, max_distance=1.0, on_non_linear="Ignore")
        with self.assertRaises(ValueError):
            ClearanceAxisToAxis(source, target)
        with self.assertRaises(ValueError):
            ClearanceAxisToAxis(source, target, min_distance=2.0, max_distance=1.0)
        with self.assertRaises(ValueError):
            ClearanceAxisToAxis(source, target, max_distance=1.0, min_distance=-1.0)
        with self.assertRaises(ValueError):
            ClearanceAxisToAxis(source, target, max_distance=1.0, tolerance=-0.1)
        with self.assertRaises(ValueError):
            ClearanceAxisToAxis(source, target, max_distance=1.0, linearity_ratio=0.5)
        with self.assertRaises(ValueError):
            ClearanceAxisToAxis(source, target, max_distance=1.0, parallel_tolerance=0.0)
        with self.assertRaises(ValueError):
            ClearanceAxisToAxis(source, target, max_distance=1.0, parallel_tolerance=95.0)
        with self.assertRaises(ValueError):
            ClearanceAxisToAxis(source, target, max_distance=1.0, search_radius=-0.5)


class TestClearanceAxisToAxisNetwork(unittest.TestCase):
    """The rule on networks: every pipe in the source AND the target,
    as the documentation examples (a bundle, a connection check). Only
    the real defects come out: no collinear continuation, no unrelated
    run, no outer pair of a bundle, each pair once."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, True)

    def run_network(self, elements, **parameters):
        path = os.path.join(self.temp_dir, f"network_{len(os.listdir(self.temp_dir))}.ifc")
        make_model(path, elements)
        select = SelectFacet()
        select.applicability = [ids.Entity(name="IFCBUILDINGELEMENTPROXY")]
        rule_file = RuleFile()
        rule_file.list_ifc_path = [path]
        rule = ClearanceAxisToAxis(select, select, **parameters)
        rule_file.contains = [rule]
        rule_file.run()
        assert_result_shape(rule)
        return sorted(
            (r.source.Name, r.target.Name, round(r.info.distance, 4)) for r in rule.result
        )

    BUNDLE = dict(mode="Perpendicular", min_distance=0.14, max_distance=0.16)

    def test_correct_bundle_of_three_pipes(self):
        """Three pipes 0.15 m apart: the outer pair (0.30 m) is not a
        hole, each pipe is checked against its nearest neighbour."""
        results = self.run_network(
            [box(f"P{i}", 0.0, y=0.15 * i, dx=4.0, dy=0.1, height=0.1) for i in range(3)],
            **self.BUNDLE,
        )
        self.assertEqual(results, [])

    def test_hole_in_a_bundle(self):
        """The third pipe 0.40 m away: a 0.25 m hole from its nearest
        neighbour, reported once."""
        results = self.run_network(
            [
                box("P0", 0.0, y=0.00, dx=4.0, dy=0.1, height=0.1),
                box("P1", 0.0, y=0.15, dx=4.0, dy=0.1, height=0.1),
                box("P2", 0.0, y=0.40, dx=4.0, dy=0.1, height=0.1),
            ],
            **self.BUNDLE,
        )
        self.assertEqual(results, [("P2", "P1", 0.25)])

    def test_too_close_pair_reported_once(self):
        """Two pipes 0.10 m apart in an overlapping selection: one
        result, not (A, B) and (B, A)."""
        results = self.run_network(
            [
                box("A", 0.0, y=0.00, dx=4.0, dy=0.1, height=0.1),
                box("B", 0.0, y=0.10, dx=4.0, dy=0.1, height=0.1),
            ],
            mode="Perpendicular", min_distance=0.14,
        )
        self.assertEqual(results, [("A", "B", 0.1)])

    def test_continuation_and_shifted_runs_are_not_side_by_side(self):
        """C continues A on the same line 10 m further, E runs parallel
        to B 0.15 m away but 20 m further along x: neither faces its
        partner, so no "too close" (offset 0) nor "too far"."""
        results = self.run_network(
            [
                box("A", 0.0, y=0.00, dx=4.0, dy=0.1, height=0.1),
                box("B", 0.0, y=0.15, dx=4.0, dy=0.1, height=0.1),
                box("C", 10.0, y=0.00, dx=4.0, dy=0.1, height=0.1),
                box("E", 20.0, y=0.30, dx=4.0, dy=0.1, height=0.1),
            ],
            mode="Perpendicular", min_distance=0.14,
        )
        self.assertEqual(results, [])

    def test_isolated_run_and_search_radius(self):
        """An isolated run 5 m from the bundle: without search radius,
        its nearest neighbour is "too far"; with a 0.5 m radius it has
        no neighbour and is not checked."""
        elements = [
            box("A", 0.0, y=0.00, dx=4.0, dy=0.1, height=0.1),
            box("B", 0.0, y=0.15, dx=4.0, dy=0.1, height=0.1),
            box("D", 0.0, y=5.00, dx=4.0, dy=0.1, height=0.1),
        ]
        self.assertEqual(self.run_network(elements, **self.BUNDLE), [("D", "B", 4.85)])
        self.assertEqual(self.run_network(elements, search_radius=0.5, **self.BUNDLE), [])

    def test_connections_coaxiality(self):
        """Two connections: A-B good (collinear, butted), C-D off by
        2 cm. Only C-D comes out: the unrelated runs 3 m apart are not
        each other's nearest neighbour."""
        results = self.run_network(
            [
                box("A", 0.0, y=0.00, dx=2.0, dy=0.1, height=0.1),
                box("B", 2.0, y=0.00, dx=2.0, dy=0.1, height=0.1),
                box("C", 0.0, y=3.00, dx=2.0, dy=0.1, height=0.1),
                box("D", 2.0, y=3.02, dx=2.0, dy=0.1, height=0.1),
            ],
            mode="MinDistance", max_distance=0.005,
        )
        self.assertEqual(results, [("C", "D", 0.02)])

    def test_fallback_beyond_search_radius_not_measured(self):
        """A compact block 5 m from a pipe (non-linear, Fallback): with
        a 1 m radius the pair is not a neighbour — no result, and the
        skin distance is not even computed (box test)."""
        elements = [
            box("Block", 0.0, y=5.0, dx=1.0, dy=1.0, height=1.0),
            box("Pipe", 0.0, dx=4.0, dy=0.1, height=0.1),
        ]
        far = self.run_network(elements, min_distance=0.1, max_distance=0.5, on_non_linear="Fallback")
        self.assertEqual(len(far), 1)
        self.assertEqual(
            self.run_network(elements, min_distance=0.1, max_distance=0.5, on_non_linear="Fallback",
                             search_radius=1.0),
            [],
        )


class TestAxisHelpers(unittest.TestCase):
    """The pure axis helpers of clash_utils used by the rule."""

    def test_segment_segment_distance_parallel(self):
        """Two parallel segments, offset 0.5."""
        distance = segment_segment_distance(
            np.array([0.0, 0.0, 0.0]), np.array([4.0, 0.0, 0.0]),
            np.array([0.0, 0.5, 0.0]), np.array([4.0, 0.5, 0.0]),
        )
        self.assertAlmostEqual(distance, 0.5, places=9)

    def test_segment_segment_distance_crossing(self):
        """Two crossing segments: distance 0."""
        distance = segment_segment_distance(
            np.array([-1.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]),
            np.array([0.0, -1.0, 0.0]), np.array([0.0, 1.0, 0.0]),
        )
        self.assertAlmostEqual(distance, 0.0, places=9)

    def test_segment_segment_distance_end_gap(self):
        """Two collinear segments with a 0.1 gap: the closest points
        are the two ends."""
        distance = segment_segment_distance(
            np.array([-2.0, 0.0, 0.0]), np.array([0.0, 0.0, 0.0]),
            np.array([0.1, 0.0, 0.0]), np.array([2.1, 0.0, 0.0]),
        )
        self.assertAlmostEqual(distance, 0.1, places=9)

    def test_segment_segment_distance_skew(self):
        """Two skew segments crossing over: the closest points sit
        inside both segments."""
        distance = segment_segment_distance(
            np.array([0.0, 0.0, 0.0]), np.array([2.0, 0.0, 0.0]),
            np.array([1.0, 1.0, -1.0]), np.array([1.0, 1.0, 1.0]),
        )
        self.assertAlmostEqual(distance, 1.0, places=9)

    def test_segment_segment_distance_degenerate_point(self):
        """A segment degenerating to a point: plain point distance."""
        point = np.array([3.0, 0.0, 0.0])
        distance = segment_segment_distance(
            np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]),
            point, point.copy(),
        )
        self.assertAlmostEqual(distance, 2.0, places=9)

    def test_parallel_line_offset(self):
        offset = parallel_line_offset(
            np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]),
            np.array([1.0, 0.5, 0.0]), np.array([1.0, 0.0, 0.0]),
        )
        self.assertAlmostEqual(offset, 0.5, places=9)

    def test_parallel_line_offset_nearly_anti_parallel(self):
        """Two quasi-parallel axes given with opposite senses (the sign
        of an OBB axis is arbitrary): the bisector is taken on one
        sense, the offset stays the lateral one (0.15), not the 10 m
        along the axes (the bug before 2026-11-09)."""
        angle = np.radians(0.1)
        offset = parallel_line_offset(
            np.array([0.0, 0.0, 0.0]),
            np.array([1.0, 0.0, 0.0]),
            np.array([10.0, 0.15, 0.0]),
            np.array([-np.cos(angle), np.sin(angle), 0.0]),
        )
        self.assertAlmostEqual(offset, 0.15, delta=0.01)

    def test_axial_overlap(self):
        """Side by side over 2 m, butted end to end (0) and shifted
        apart (-6 m gap)."""
        x = np.array([1.0, 0.0, 0.0])
        self.assertAlmostEqual(axial_overlap(np.zeros(3), x, 2.0, np.array([1.0, 0.15, 0.0]), x, 2.0), 3.0)
        self.assertAlmostEqual(axial_overlap(np.zeros(3), x, 1.0, np.array([2.0, 0.0, 0.0]), -x, 1.0), 0.0)
        self.assertAlmostEqual(axial_overlap(np.zeros(3), x, 2.0, np.array([10.0, 0.0, 0.0]), x, 2.0), -6.0)

    def test_parallel_line_offset_anti_parallel(self):
        """Anti-parallel axis directions: same support line, the
        offset stays the perpendicular one."""
        offset = parallel_line_offset(
            np.array([0.0, 0.0, 0.0]), np.array([1.0, 0.0, 0.0]),
            np.array([0.0, 0.5, 0.0]), np.array([-1.0, 0.0, 0.0]),
        )
        self.assertAlmostEqual(offset, 0.5, places=9)

    def test_axis_angle_unsigned(self):
        """Parallel and anti-parallel axes both give 0 degree."""
        x_axis = np.array([1.0, 0.0, 0.0])
        y_axis = np.array([0.0, 1.0, 0.0])
        self.assertAlmostEqual(axis_angle(x_axis, x_axis), 0.0, places=9)
        self.assertAlmostEqual(axis_angle(x_axis, -x_axis), 0.0, places=9)
        self.assertAlmostEqual(axis_angle(x_axis, y_axis), 90.0, places=9)

    def test_obb_long_axis_of_a_slender_box(self):
        """The long axis of a slender box: center, direction, half
        length and thickness of the OBB."""
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
        from OCC.Core.gp import gp_Pnt

        shape = BRepPrimAPI_MakeBox(gp_Pnt(0.0, 0.0, 0.0), 4.0, 0.1, 0.1).Shape()
        obb = create_obb_from_TopoDs_Shape(shape)
        center, direction, half_length, thickness = obb_long_axis(obb)

        self.assertAlmostEqual(half_length, 2.0, places=6)
        self.assertAlmostEqual(thickness, 0.1, places=6)
        self.assertAlmostEqual(abs(float(direction[0])), 1.0, places=6)
        self.assertAlmostEqual(float(direction[1]), 0.0, places=6)
        self.assertAlmostEqual(float(direction[2]), 0.0, places=6)
        self.assertAlmostEqual(float(center[0]), 2.0, places=6)
        self.assertAlmostEqual(float(center[1]), 0.05, places=6)
        self.assertAlmostEqual(float(center[2]), 0.05, places=6)


if __name__ == "__main__":
    unittest.main()
