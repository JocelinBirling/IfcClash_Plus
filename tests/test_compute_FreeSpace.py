"""The compute contract of FreeSpace (SPEC Separation moteur/gestion),
tested directly — the LE case of the three-list contract: one entity
list, the named parameters, and the context as a THIRD INPUT LIST
(liste_objet_contexte), raw results out.

The models are the ones of the unit suite: a 4 x 4 room with a table,
a room smaller than the turning circle, a room split by a partition, a
room with a suspended lamp, and a corridor exactly as wide as the
circle.

The search helpers read their configuration off the instance: the
compute poses the named parameters on the instance before running
(documented exception — the node remains the config carrier) and
leaves its engine state on it (the found placements and the probe
positions).

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_FreeSpace.py -v
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

from Rules import FreeSpace
from RuleClass import SelectFacet, RuleFile, ClashResultOneObject
from registry import compute_from_config, engine_params
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape
from tests.test_UnitRule_FreeSpace import make_model


def select_by_name(name):
    from ifctester import ids

    select = SelectFacet()
    select.applicability = [ids.Attribute(name="Name", value=name)]
    return select


class TestComputeFreeSpace(unittest.TestCase):
    """The compute contract of FreeSpace: the three-list contract of
    the SPEC (source + context), the target list is absent."""

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.mkdtemp()
        cls.models = {
            "room": [("Room", 2, 2, 0, 4, 4, 3), ("Table", 2, 2, 0, 1, 1, 0.75)],
            "small": [("Room", 0.6, 0.6, 0, 1.2, 1.2, 3)],
            "split": [
                ("Room", 1.5, 1.5, 0, 3, 3, 3),
                ("Partition", 1.5, 1.5, 0, 0.2, 3, 3),
            ],
            "high": [("Room", 2, 2, 0, 4, 4, 3), ("Lamp", 2, 2, 2.0, 2, 2, 0.5)],
            "corridor": [("Room", 1.5, 0.75, 0, 3, 1.5, 3)],
        }
        cls.paths = {}
        for name, elements in cls.models.items():
            path = os.path.join(cls._temp_dir, f"{name}.ifc")
            make_model(path, elements)
            cls.paths[name] = path
        # ifcopenshell 0.9: an entity does not keep its file alive.
        cls.files = {name: ifcopenshell.open(path) for name, path in cls.paths.items()}

    @classmethod
    def tearDownClass(cls):
        cls.files.clear()
        shutil.rmtree(cls._temp_dir, True)

    def _element(self, model, name):
        matches = [e for e in self.files[model].by_type("IfcProduct") if e.Name == name]
        self.assertTrue(matches, f"no element named {name!r} in {model}")
        return matches[0]

    def _compute(self, model="room", context=(), diameter=1.5, height=1.4):
        rule = FreeSpace(None, None, diameter=1.5, height=1.4)
        return rule.compute(
            [self._element(model, "Room")],
            diameter,
            height,
            liste_objet_contexte=[self._element(model, name) for name in context],
        ), rule

    def test_free_placement_found(self):
        """A 1.50 m turning circle fits in a 4 x 4 room with a table:
        no clash, the placement is left on the node."""
        results, rule = self._compute(context=("Table",), diameter=1.5, height=1.4)
        self.assertEqual(results, [])
        self.assertEqual(len(rule.placements), 1)
        placement = rule.placements[list(rule.placements)[0]]
        x, y, z_base = placement["position"]
        self.assertGreaterEqual(x, 0.0)
        self.assertLessEqual(x, 4.0)
        self.assertGreaterEqual(y, 0.0)
        self.assertLessEqual(y, 4.0)
        self.assertAlmostEqual(z_base, 0.0, places=6)
        self.assertGreaterEqual(placement["margin"], 0.0)

    def test_small_room_clashes(self):
        """A 1.2 x 1.2 room cannot host a 1.50 m circle."""
        results, rule = self._compute(
            model="small", context=(), diameter=1.5, height=1.4
        )
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIsInstance(result, ClashResultOneObject)
        self.assertTrue(result.status)
        self.assertEqual(result.source.Name, "Room")
        self.assertEqual(rule.placements, {})
        self.assertEqual(result.info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_split_room_clashes(self):
        """The partition leaves two halves of 1.4 m: too narrow."""
        results, rule = self._compute(
            model="split", context=("Partition",), diameter=1.5, height=1.4
        )
        self.assertEqual(len(results), 1)

    def test_height_respects_suspended_obstacles(self):
        """The lamp at 2 m does not block a 1.4 m high cylinder, but
        blocks a 2.5 m one."""
        results, rule = self._compute(
            model="high", context=("Lamp",), diameter=1.5, height=1.4
        )
        self.assertEqual(results, [])
        self.assertEqual(len(rule.placements), 1)

        results, rule = self._compute(
            model="high", context=("Lamp",), diameter=1.5, height=2.5
        )
        self.assertEqual(len(results), 1)

    def test_tangent_placement_is_free(self):
        """A corridor exactly as wide as the circle: the tangent
        placement is free, with a zero margin."""
        results, rule = self._compute(
            model="corridor", context=(), diameter=1.499, height=1.4
        )
        self.assertEqual(results, [])
        placement = rule.placements[list(rule.placements)[0]]
        self.assertAlmostEqual(placement["margin"], 0.0, places=3)

    def test_tangent_larger_diameter_clashes(self):
        results, rule = self._compute(
            model="corridor", context=(), diameter=1.6, height=1.4
        )
        self.assertEqual(len(results), 1)

    def test_empty_context_free(self):
        """Without obstacles, the footprint alone decides."""
        results, rule = self._compute(context=(), diameter=1.5, height=1.4)
        self.assertEqual(results, [])
        self.assertEqual(len(rule.placements), 1)

    def test_compute_poses_the_params_and_leaves_the_probe_state(self):
        """Documented exception and engine state: the params are posed
        on the instance, the probe position is left for the adapter."""
        results, rule = self._compute(
            model="small", context=(), diameter=1.5, height=1.4
        )
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(rule.diameter, 1.5)
        self.assertAlmostEqual(rule.height, 1.4)
        # The probe of the clash stays at the center of the footprint.
        room = self._element("small", "Room")
        self.assertIn(room, rule._probe_positions)

    def test_compute_is_pure_of_management_and_display(self):
        rule = FreeSpace(None, None, diameter=1.5, height=1.4)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results, _ = self._compute(context=("Table",), diameter=1.5, height=1.4)

        self.assertEqual(results, [])
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)


class TestComputeFreeSpaceDispatch(unittest.TestCase):
    """The flat JSON declarations drive the compute through the
    registry dispatch — including the context list."""

    def test_engine_params(self):
        self.assertEqual(engine_params("FreeSpace"), ["diameter", "height"])

    def test_declaration_drives_the_compute_with_context(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, True)
        model = os.path.join(temp_dir, "room.ifc")
        make_model(
            model,
            [("Room", 2, 2, 0, 4, 4, 3), ("Table", 2, 2, 0, 1, 1, 0.75)],
        )
        file = ifcopenshell.open(model)
        elements = {e.Name: e for e in file.by_type("IfcProduct")}

        context = SelectFacet()
        context.applicability = [select_by_name("Table").applicability[0]]
        rule = FreeSpace(select_by_name("Room"), context, diameter=1.5, height=1.4)
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        # Without the table: the room alone is free.
        results = compute_from_config(config, [elements["Room"]])
        self.assertEqual(results, [])

        # With the table as the context list: same outcome here (the
        # room is large enough), the placement is found either way.
        results = compute_from_config(
            config, [elements["Room"]], None, [elements["Table"]]
        )
        self.assertEqual(results, [])


class TestComputeFreeSpaceThroughAdapter(unittest.TestCase):
    """The migration adapter (run + RuleFile) produces the RuleOutput
    of the pipeline (SPEC): one integration node."""

    def test_rule_output_after_rule_file_run(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, True)
        model = os.path.join(temp_dir, "small.ifc")
        make_model(model, [("Room", 0.6, 0.6, 0, 1.2, 1.2, 3)])

        rule_file = RuleFile()
        rule_file.list_ifc_path = [model]
        context = SelectFacet()
        rule = FreeSpace(select_by_name("Room"), context, diameter=1.5, height=1.4)
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        self.assertEqual(len(rule.result), 1)
        self.assertIsNotNone(rule.output)
        self.assertIs(rule.output.results, rule.result)


if __name__ == "__main__":
    unittest.main()
