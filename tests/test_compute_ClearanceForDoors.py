"""The compute contract of ClearanceForDoors (SPEC Separation moteur/
gestion), tested directly — entity lists and the named parameters in,
raw results out.

The model is the one of the unit suite: a door (0.90 m wide, 2.10 m
high) whose local placement has its X axis along the wall and Y
through it, with an IfcDoorType providing the OperationType, and
three boxes: one in the leaf sweep, one behind the door, one far away.

The zone builder reads its configuration off the instance: the compute
poses the named parameters on the instance before building the zones
(documented exception — the node remains the config carrier), while
the outputs stay pure.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_ClearanceForDoors.py -v
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

from Rules import ClearanceForDoors
from RuleClass import SelectFacet, RuleFile, ClashResultTwoObjects
from registry import compute_from_config, engine_params
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape
from tests.test_UnitRule_ClearanceForDoors import make_model


def select_by_class(ifc_class):
    from ifctester import ids

    select = SelectFacet()
    select.applicability = [ids.Entity(name=ifc_class)]
    return select


class TestComputeClearanceForDoors(unittest.TestCase):
    """The compute contract of ClearanceForDoors: two lists + the
    named parameters."""

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.mkdtemp()
        cls.model = os.path.join(cls._temp_dir, "door.ifc")
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

    def _door(self):
        return self.file.by_type("IfcDoor")[0]

    def _compute(self, **parameters):
        rule = ClearanceForDoors(None, None)
        return rule.compute(
            [self._door()],
            [self._element(name) for name in ("InSweep", "Behind", "FarAway")],
            parameters.get("zone_shape", "Arc"),
            parameters.get("sides", "Swing"),
            parameters.get("leaves"),
            parameters.get("width"),
            parameters.get("depth"),
            parameters.get("height"),
            parameters.get("tolerance", 0.001),
        )

    def target_names(self, results):
        return sorted(result.target.Name for result in results)

    def test_swing_arc_obstruction_clashes(self):
        """A box in the swept quarter disk of a SingleSwingLeft door
        clashes; the far box and the back box stay silent."""
        results = self._compute(zone_shape="Arc", sides="Swing")
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertTrue(result.status)
        self.assertEqual(result.source.Name, "Door")
        self.assertEqual(result.target.Name, "InSweep")
        # ZoneData carries the serializable dimensions of the zone;
        # the swept shape (Arc) stays in the rule, not in the result.
        self.assertEqual(result.info.zone.side, "Front")
        self.assertEqual(result.info.zone.leaf, "SINGLE_SWING_LEFT")
        # The zone dimensions come from the door: leaf width and height.
        self.assertAlmostEqual(result.info.zone.width, 0.9, places=3)
        self.assertAlmostEqual(result.info.zone.height, 2.1, places=3)
        self.assertGreater(result.info.penetration_depth, 0.1)

        self.assertEqual(result.info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_sides_both_checks_front_and_back(self):
        results = self._compute(zone_shape="Arc", sides="Both")
        self.assertEqual(self.target_names(results), ["Behind", "InSweep"])
        by_target = {result.target.Name: result for result in results}
        self.assertEqual(by_target["Behind"].info.zone.side, "Back")

    def test_rectangle_front(self):
        results = self._compute(zone_shape="Rectangle", sides="Front")
        self.assertEqual(self.target_names(results), ["InSweep"])
        self.assertEqual(results[0].info.zone.side, "Front")

    def test_override_dimensions(self):
        """Regulatory dimensions override the door size."""
        results = self._compute(
            zone_shape="Rectangle",
            sides="Front",
            width=1.5,
            depth=2.0,
            height=2.5,
        )
        self.assertEqual(self.target_names(results), ["InSweep"])
        self.assertAlmostEqual(results[0].info.zone.width, 1.5, places=6)
        self.assertAlmostEqual(results[0].info.zone.depth, 2.0, places=6)
        self.assertAlmostEqual(results[0].info.zone.height, 2.5, places=6)

    def test_sliding_door_uses_rectangles(self):
        """A sliding door cannot sweep: rectangles on both sides,
        whatever zone_shape says."""
        model = os.path.join(self._temp_dir, "sliding.ifc")
        make_model(model, operation="SLIDING_TO_LEFT")
        file = ifcopenshell.open(model)
        door = file.by_type("IfcDoor")[0]
        boxes = [e for e in file.by_type("IfcProduct") if e.is_a("IfcBuildingElementProxy")]

        rule = ClearanceForDoors(None, None)
        results = rule.compute(
            [door], boxes, "Arc", "Swing", None, None, None, None, 0.001
        )
        self.assertEqual(
            sorted(result.target.Name for result in results), ["Behind", "InSweep"]
        )
        self.assertEqual(
            {result.info.zone.side for result in results}, {"Front", "Back"}
        )

    def test_tolerance_ignores_deep_only(self):
        """A tolerance above the penetration depth ignores the box."""
        results = self._compute(tolerance=10.0)
        self.assertEqual(results, [])

    def test_compute_poses_the_params_on_the_instance(self):
        """Documented exception: the zone builder reads its config off
        the instance, the compute poses the named parameters on it."""
        rule = ClearanceForDoors(None, None)
        rule.compute(
            [self._door()],
            [self._element(name) for name in ("InSweep", "Behind", "FarAway")],
            "Rectangle",
            "Front",
            None,
            1.5,
            None,
            None,
            0.001,
        )
        self.assertEqual(rule.zone_shape, "Rectangle")
        self.assertEqual(rule.sides, "Front")
        self.assertAlmostEqual(rule.width, 1.5)

    def test_compute_is_pure_of_management_and_display(self):
        rule = ClearanceForDoors(None, None)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = self._compute()

        self.assertEqual(len(results), 1)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)


class TestComputeClearanceForDoorsDispatch(unittest.TestCase):
    """The flat JSON declarations drive the compute through the
    registry dispatch."""

    def test_engine_params(self):
        self.assertEqual(
            engine_params("ClearanceForDoors"),
            [
                "zone_shape",
                "sides",
                "leaves",
                "width",
                "depth",
                "height",
                "tolerance",
            ],
        )

    def test_declaration_drives_the_compute(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, True)
        model = os.path.join(temp_dir, "door.ifc")
        make_model(model)
        file = ifcopenshell.open(model)
        door = file.by_type("IfcDoor")[0]
        boxes = [e for e in file.by_type("IfcProduct") if e.is_a("IfcBuildingElementProxy")]

        rule = ClearanceForDoors(
            select_by_class("IFCDOOR"),
            select_by_class("IFCBUILDINGELEMENTPROXY"),
        )
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        results = compute_from_config(config, [door], boxes)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].target.Name, "InSweep")


class TestComputeClearanceForDoorsThroughAdapter(unittest.TestCase):
    """The migration adapter (run + RuleFile) produces the RuleOutput
    of the pipeline (SPEC): one integration node."""

    def test_rule_output_after_rule_file_run(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, True)
        model = os.path.join(temp_dir, "door.ifc")
        make_model(model)

        rule_file = RuleFile()
        rule_file.list_ifc_path = [model]
        rule = ClearanceForDoors(
            select_by_class("IFCDOOR"),
            select_by_class("IFCBUILDINGELEMENTPROXY"),
        )
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        self.assertEqual(len(rule.result), 1)
        self.assertIsNotNone(rule.output)
        self.assertIs(rule.output.results, rule.result)


if __name__ == "__main__":
    unittest.main()
