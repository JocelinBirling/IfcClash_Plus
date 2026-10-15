"""
Test suite for the DirectView rule (doc/2ObjectsRules/DirectView.md).

The models are generated with the ifcopenshell API: an observer box, a
target box 8 m away, and a wall in between (fully blocking, or blocking
one side of the corridor for the partial occlusion cases). The sampling
of the rays is deterministic, so the expected ratios are reproducible.

Execution (from the repository root):
    python -m pytest tests/test_DirectView.py -v
"""
import math
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell
import ifcopenshell.api

from Rules import DirectView
from RuleClass import SelectFacet, RuleFile, ClashResultTwoObjects

from tests.test_structure_ResultShape import assert_result_shape
from clash_utils import (
    direct_view_early_stop,
    plan_ray_counts,
    r2_sequence,
    sample_point_in_triangle,
)
from ifctester import ids


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


class TestDirectView(unittest.TestCase):
    """The DirectView rule on generated models."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, True)

        self.clear_model = os.path.join(self.temp_dir, "clear.ifc")
        make_model(self.clear_model, [box("Observer", 0.0), box("Target", 8.0)])

        self.blocked_model = os.path.join(self.temp_dir, "blocked.ifc")
        make_model(
            self.blocked_model,
            [
                box("Observer", 0.0),
                box("Target", 8.0),
                box("Wall", 4.0, dx=0.2, dy=4.0, height=3.0),
            ],
        )

        # The wall covers one side of the corridor: most rays are
        # blocked, a small fraction still reaches the target.
        self.partial_model = os.path.join(self.temp_dir, "partial.ifc")
        make_model(
            self.partial_model,
            [
                box("Observer", 0.0),
                box("Target", 8.0),
                box("Wall", 4.0, y=0.6, dx=0.2, dy=1.5, height=3.0),
            ],
        )

    @staticmethod
    def select(name):
        select = SelectFacet()
        select.applicability = [ids.Attribute(name="Name", value=name)]
        return select

    def run_rule(self, model, context_names=(), **parameters):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [model]
        context = SelectFacet()
        parameters["state"]="Final"
        context.applicability = [
            ids.Attribute(name="Name", value=name) for name in context_names
        ]
        rule = DirectView(
            self.select("Observer"), self.select("Target"), context, **parameters
        )
        rule_file.contains = [rule]
        rule_file.run()
        assert_result_shape(rule)
        return rule

    # ---- Nominal

    def test_clear_view_clashes(self):
        """Without obstacle, every ray passes between the two objects:
        the pair is in direct view and clashes at 100%."""
        for ray_source in ("Source", "Both", "Target"):
            rule = self.run_rule(
                self.clear_model, ray_source=ray_source, threshold="100%"
            )
            self.assertEqual(len(rule.result), 1, ray_source)
            result = rule.result[0]
            self.assertIsInstance(result, ClashResultTwoObjects)
            self.assertEqual(result.source.Name, "Observer")
            self.assertEqual(result.target.Name, "Target")
            self.assertAlmostEqual(result.info.hit_ratio, 1.0, places=6)

    def test_blocked_view_no_clash(self):
        """A wall between the observer and the target blocks every
        ray: no direct view, no result."""
        rule = self.run_rule(self.blocked_model, context_names=("Wall",))

        self.assertEqual(len(rule.result), 0)

    def test_clear_early_stop_ratio_over_cast_rays(self):
        """Threshold 50% of 20 planned rays: the outcome is decided
        once 10 rays touch (10/20 reaches 50%): the rule stops, the
        ratio is reported over the rays actually cast."""
        rule = self.run_rule(
            self.clear_model,
            ray_count=20,
            threshold="50%",
        )

        self.assertEqual(len(rule.result), 1)
        result = rule.result[0]
        self.assertEqual(result.info.raycast.cast, 10)
        self.assertAlmostEqual(result.info.hit_ratio, 1.0, places=6)

    def test_blocked_target_emits(self):
        """Ray_Source = Target: the wall blocks the rays, no result."""
        rule = self.run_rule(
            self.blocked_model,
            context_names=("Wall",),
            ray_source="Target",
            threshold="100%",
        )
        self.assertEqual(len(rule.result), 0)

    def test_both_emitters_single_ratio(self):
        """Ray_Source = Both: one combined ratio over the two emitters."""
        rule = self.run_rule(
            self.clear_model,
            ray_source="Both",
            ray_count=10,
            threshold="100%",
        )
        self.assertEqual(len(rule.result), 1)
        result = rule.result[0]
        self.assertEqual(result.info.raycast.planned, 20)
        self.assertEqual(result.info.raycast.cast, 20)
        self.assertAlmostEqual(result.info.hit_ratio, 1.0, places=6)

    def test_partial_occlusion_below_threshold_no_clash(self):
        """A wall on one side of the corridor: the hit ratio (~10-16%)
        stays below a 50% requirement: the pair is not in direct view."""
        rule = self.run_rule(
            self.partial_model,
            context_names=("Wall",),
            ray_count=40,
            threshold="50%",
        )

        self.assertEqual(len(rule.result), 0)

    def test_partial_occlusion_reaches_threshold_clashes(self):
        """The same partial occlusion reaches a 5% visibility
        requirement: the pair is in direct view and clashes."""
        rule = self.run_rule(
            self.partial_model,
            context_names=("Wall",),
            ray_count=40,
            threshold="5%",
        )
        self.assertEqual(len(rule.result), 1)
        result = rule.result[0]
        # The ratio over the rays actually cast reaches the threshold.
        self.assertGreaterEqual(result.info.hit_ratio, 0.05)
        # The reported zones cover exactly the rays actually cast.
        self.assertEqual(
            len(result.info.raycast.hit_segments)
            + len(result.info.raycast.blocked_segments),
            result.info.raycast.cast,
        )

    # ---- Max_Distance

    def test_max_distance_too_short_no_clash(self):
        """The target is 8 m away, the rays stop at 5 m: all misses,
        no direct view, no result."""
        rule = self.run_rule(self.clear_model, max_distance=5.0)
        self.assertEqual(len(rule.result), 0)

    def test_max_distance_long_enough_clashes(self):
        rule = self.run_rule(self.clear_model, max_distance=50.0)
        self.assertEqual(len(rule.result), 1)

    # ---- Cas limites

    def test_empty_context_nothing_blocks(self):
        """An empty Context set: nothing can block the rays, the pair
        is in direct view."""
        rule = self.run_rule(self.clear_model, context_names=("Nothing",))
        self.assertEqual(len(rule.result), 1)

    def test_threshold_zero_clashes_every_pair(self):
        """A 0% threshold: even a fully blocked pair reaches 0% and
        clashes (without casting any ray)."""
        rule = self.run_rule(
            self.blocked_model, context_names=("Wall",), threshold="0%"
        )
        self.assertEqual(len(rule.result), 1)
        self.assertAlmostEqual(rule.result[0].info.hit_ratio, 0.0, places=6)

    def test_invalid_parameters_raise_value_error(self):
        source = self.select("Observer")
        target = self.select("Target")
        context = SelectFacet()

        with self.assertRaises(ValueError):
            DirectView(source, target, context, ray_source="Everywhere")
        with self.assertRaises(ValueError):
            DirectView(source, target, context, ray_count=0)
        with self.assertRaises(ValueError):
            DirectView(source, target, context, ray_count=2.5)
        with self.assertRaises(ValueError):
            DirectView(source, target, context, threshold="100")
        with self.assertRaises(ValueError):
            DirectView(source, target, context, threshold="abc%")
        with self.assertRaises(ValueError):
            DirectView(source, target, context, threshold="150%")
        with self.assertRaises(ValueError):
            DirectView(source, target, context, max_distance=0)
        with self.assertRaises(ValueError):
            DirectView(source, target, context, max_distance=-1.0)


class TestDirectViewUtilities(unittest.TestCase):
    """The deterministic ray helpers of clash_utils used by DirectView."""

    def test_r2_sequence_in_unit_square(self):
        for index in (0, 1, 5, 100, 12345):
            u, v = r2_sequence(index)
            self.assertTrue(0.0 <= u < 1.0)
            self.assertTrue(0.0 <= v < 1.0)

    def test_sample_point_inside_triangle(self):
        triangle = np.array(
            [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 2.0, 0.0]]
        )
        for index in range(20):
            point = sample_point_in_triangle(triangle, index)
            # Barycentric coordinates: x >= 0, y >= 0, x + y <= 2.
            self.assertGreaterEqual(point[0], 0.0)
            self.assertGreaterEqual(point[1], 0.0)
            self.assertLessEqual(point[0] + point[1], 2.0 + 1e-9)
            self.assertEqual(point[2], 0.0)

    def test_sample_point_is_deterministic(self):
        triangle = np.array(
            [[0.0, 0.0, 0.0], [2.0, 0.0, 0.0], [0.0, 2.0, 0.0]]
        )
        first = sample_point_in_triangle(triangle, 3)
        second = sample_point_in_triangle(triangle, 3)
        self.assertTrue(np.allclose(first, second))
        other = sample_point_in_triangle(triangle, 4)
        self.assertFalse(np.allclose(first, other))

    def test_plan_ray_counts_proportional(self):
        """The rays are spread proportionally to the areas; a tie of
        remainders goes to the first face."""
        self.assertEqual(plan_ray_counts([3.0, 1.0], 10), [8, 2])
        self.assertEqual(plan_ray_counts([1.0, 1.0, 1.0], 10), [4, 3, 3])
        self.assertEqual(plan_ray_counts([1.0, 3.0], 10), [3, 7])

    def test_plan_ray_counts_sum_is_exact(self):
        counts = plan_ray_counts([1.2, 0.7, 3.3, 2.8], 13)
        self.assertEqual(sum(counts), 13)
        self.assertEqual(len(counts), 4)

    def test_plan_ray_counts_edge_cases(self):
        self.assertEqual(plan_ray_counts([], 10), [])
        self.assertEqual(plan_ray_counts([1.0, 2.0], 0), [0, 0])
        # Degenerate faces (zero area): the rays are spread evenly.
        self.assertEqual(plan_ray_counts([0.0, 0.0], 5), [3, 2])

    def test_early_stop_guarantees_the_decision(self):
        planned = 10
        # Threshold 50%: 5 touches of the planned rays decide the outcome.
        self.assertEqual(
            direct_view_early_stop(5, 6, planned, 0.5), "reaches_threshold"
        )
        # Even all the remaining rays touching would stay below 50%.
        self.assertEqual(
            direct_view_early_stop(0, 6, planned, 0.5), "below_threshold"
        )
        # Undecided: continue casting.
        self.assertIsNone(direct_view_early_stop(3, 6, planned, 0.5))

    def test_early_stop_threshold_100(self):
        # Any miss with a 100% requirement decides the outcome.
        self.assertEqual(
            direct_view_early_stop(2, 3, 10, 1.0), "below_threshold"
        )
        # All the planned rays must touch to reach the threshold.
        self.assertEqual(
            direct_view_early_stop(10, 10, 10, 1.0), "reaches_threshold"
        )
        self.assertIsNone(direct_view_early_stop(9, 9, 10, 1.0))

    def test_early_stop_bound_is_inclusive(self):
        # hits / planned exactly at the threshold: decided.
        self.assertEqual(
            direct_view_early_stop(4, 8, 8, 0.5), "reaches_threshold"
        )
        # Max possible ratio exactly at the threshold: continue.
        self.assertIsNone(direct_view_early_stop(4, 8, 10, 0.5))


if __name__ == "__main__":
    unittest.main()
