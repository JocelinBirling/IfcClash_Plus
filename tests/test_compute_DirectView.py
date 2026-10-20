"""The compute contract of DirectView (SPEC Separation moteur/gestion),
tested directly — entity lists and the named parameters in, raw
results out.

The context is a THIRD INPUT LIST (liste_objet_contexte), never a
hidden select. The models are the ones of the unit suite: an observer
box, a target box 8 m away, and a wall in between (fully blocking, or
blocking one side of the corridor for the partial occlusion cases).
The sampling of the rays is deterministic, so the expected ratios are
reproducible.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_DirectView.py -v
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

from Rules import DirectView
from RuleClass import SelectFacet, RuleFile, ClashResultTwoObjects
from registry import compute_from_config, engine_params
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape
from tests.test_UnitRule_DirectView import make_model, box


def select_by_name(name):
    from ifctester import ids

    select = SelectFacet()
    select.applicability = [ids.Attribute(name="Name", value=name)]
    return select


class TestComputeDirectView(unittest.TestCase):
    """The compute contract of DirectView: two lists + the context
    list + the named parameters (threshold as a percentage)."""

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.mkdtemp()
        cls.clear_model = os.path.join(cls._temp_dir, "clear.ifc")
        make_model(cls.clear_model, [box("Observer", 0.0), box("Target", 8.0)])
        cls.blocked_model = os.path.join(cls._temp_dir, "blocked.ifc")
        make_model(
            cls.blocked_model,
            [
                box("Observer", 0.0),
                box("Target", 8.0),
                box("Wall", 4.0, dx=0.2, dy=4.0, height=3.0),
            ],
        )
        cls.partial_model = os.path.join(cls._temp_dir, "partial.ifc")
        make_model(
            cls.partial_model,
            [
                box("Observer", 0.0),
                box("Target", 8.0),
                box("Wall", 4.0, y=0.6, dx=0.2, dy=1.5, height=3.0),
            ],
        )
        # ifcopenshell 0.9: an entity does not keep its file alive.
        cls.files = {
            name: ifcopenshell.open(path)
            for name, path in (
                ("clear", cls.clear_model),
                ("blocked", cls.blocked_model),
                ("partial", cls.partial_model),
            )
        }

    @classmethod
    def tearDownClass(cls):
        cls.files.clear()
        shutil.rmtree(cls._temp_dir, True)

    def _element(self, model, name):
        matches = [e for e in self.files[model].by_type("IfcProduct") if e.Name == name]
        self.assertTrue(matches, f"no element named {name!r}")
        return matches[0]

    def _compute(
        self,
        model="clear",
        context=(),
        ray_source="Source",
        ray_count=10,
        threshold=100.0,
        max_distance=None,
    ):
        rule = DirectView(None, None, None)
        return rule.compute(
            [self._element(model, "Observer")],
            [self._element(model, "Target")],
            ray_source,
            ray_count,
            threshold,
            max_distance,
            liste_objet_contexte=[
                self._element(model, name) for name in context
            ],
        )

    def test_clear_view_clashes(self):
        """Without obstacle, every ray passes between the two objects:
        the pair is in direct view and clashes at 100%."""
        results = self._compute()
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertTrue(result.status)
        self.assertEqual(result.source.Name, "Observer")
        self.assertEqual(result.target.Name, "Target")
        self.assertAlmostEqual(result.info.hit_ratio, 1.0, places=6)
        self.assertEqual(result.info.raycast.hit, result.info.raycast.cast)

        self.assertEqual(result.info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_blocked_view_no_clash(self):
        """A wall between the observer and the target blocks every
        ray: no direct view, no result."""
        results = self._compute(model="blocked", context=("Wall",))
        self.assertEqual(results, [])

    def test_clear_early_stop_ratio_over_cast_rays(self):
        """Threshold 50% of 20 planned rays: the outcome is decided
        once 10 rays touch: the rule stops, the ratio is reported over
        the rays actually cast."""
        results = self._compute(ray_count=20, threshold=50.0)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].info.raycast.cast, 10)
        self.assertAlmostEqual(results[0].info.hit_ratio, 1.0, places=6)

    def test_both_emitters_single_ratio(self):
        """Ray_Source = Both: one combined ratio over the two
        emitters."""
        results = self._compute(ray_source="Both", ray_count=10, threshold=100.0)
        self.assertEqual(len(results), 1)
        raycast = results[0].info.raycast
        self.assertEqual(raycast.planned, 20)
        self.assertEqual(raycast.cast, 20)
        self.assertAlmostEqual(results[0].info.hit_ratio, 1.0, places=6)

    def test_partial_occlusion_thresholds(self):
        """The partial occlusion (~10-16%) stays below a 50%
        requirement, and reaches a 5% one."""
        results = self._compute(
            model="partial", context=("Wall",), ray_count=40, threshold=50.0
        )
        self.assertEqual(results, [])

        results = self._compute(
            model="partial", context=("Wall",), ray_count=40, threshold=5.0
        )
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertGreaterEqual(result.info.hit_ratio, 0.05)
        # The reported segments cover exactly the rays actually cast.
        self.assertEqual(
            len(result.info.raycast.hit_segments)
            + len(result.info.raycast.blocked_segments),
            result.info.raycast.cast,
        )

    def test_max_distance(self):
        """The target is 8 m away: the rays stop at 5 m (misses), 50 m
        is enough."""
        results = self._compute(max_distance=5.0)
        self.assertEqual(results, [])

        results = self._compute(max_distance=50.0)
        self.assertEqual(len(results), 1)

    def test_threshold_zero_clashes_every_pair(self):
        """A 0% threshold: even a fully blocked pair reaches 0% and
        clashes (without casting any ray)."""
        results = self._compute(model="blocked", context=("Wall",), threshold=0.0)
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].info.hit_ratio, 0.0, places=6)

    def test_compute_is_pure_of_management_and_display(self):
        rule = DirectView(None, None, None)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = self._compute()

        self.assertEqual(len(results), 1)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)


class TestComputeDirectViewDispatch(unittest.TestCase):
    """The flat JSON declarations drive the compute through the
    registry dispatch — including the context list."""

    def test_engine_params(self):
        self.assertEqual(
            engine_params("DirectView"),
            ["ray_source", "ray_count", "threshold", "max_distance"],
        )

    def test_declaration_drives_the_compute_with_context(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, True)
        model = os.path.join(temp_dir, "blocked.ifc")
        make_model(
            model,
            [
                box("Observer", 0.0),
                box("Target", 8.0),
                box("Wall", 4.0, dx=0.2, dy=4.0, height=3.0),
            ],
        )
        file = ifcopenshell.open(model)
        elements = {e.Name: e for e in file.by_type("IfcProduct")}

        context = SelectFacet()
        context.applicability = [select_by_name("Wall").applicability[0]]
        rule = DirectView(
            select_by_name("Observer"), select_by_name("Target"), context
        )
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        # Without the context: the pair is in direct view.
        results = compute_from_config(
            config, [elements["Observer"]], [elements["Target"]]
        )
        self.assertEqual(len(results), 1)

        # With the wall as the context list: every ray is blocked.
        results = compute_from_config(
            config,
            [elements["Observer"]],
            [elements["Target"]],
            [elements["Wall"]],
        )
        self.assertEqual(results, [])


class TestComputeDirectViewThroughAdapter(unittest.TestCase):
    """The migration adapter (run + RuleFile) produces the RuleOutput
    of the pipeline (SPEC): one integration node."""

    def test_rule_output_after_rule_file_run(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, True)
        model = os.path.join(temp_dir, "clear.ifc")
        make_model(model, [box("Observer", 0.0), box("Target", 8.0)])

        rule_file = RuleFile()
        rule_file.list_ifc_path = [model]
        rule = DirectView(
            select_by_name("Observer"), select_by_name("Target"), SelectFacet()
        )
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        self.assertEqual(len(rule.result), 1)
        self.assertIsNotNone(rule.output)
        self.assertIs(rule.output.results, rule.result)


if __name__ == "__main__":
    unittest.main()
