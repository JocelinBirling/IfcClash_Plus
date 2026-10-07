"""
Test suite for the ClearanceForDoors rule
(doc/2ObjectsRules/ClearanceForDoors.md).

The models are generated with the ifcopenshell API: a door (0.90 m
wide, 2.10 m high) whose local placement has its X axis along the wall
and Y through it, with an IfcDoorType providing the OperationType, and
three boxes: one in the leaf sweep, one behind the door, one far away.

Execution (from the repository root):
    python -m pytest tests/test_ClearanceForDoors.py -v
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

from Rules import ClearanceForDoors
from RuleClass import SelectFacet, RuleFile, ClashResultTwoObjects
from clash_utils import (
    make_arc_zone,
    make_box_zone,
    max_penetration_depth,
    parse_door_operation,
)
from ifctester import ids


def make_model(path, operation="SINGLE_SWING_LEFT"):
    """A door with an OperationType and three obstruction boxes."""
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

    def box(name, x, y, z, dx, dy, height):
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

    door = ifcopenshell.api.run("root.create_entity", file, ifc_class="IfcDoor", name="Door")
    ifcopenshell.api.run(
        "geometry.edit_object_placement",
        file,
        product=door,
        matrix=((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)),
    )
    profile = file.createIfcRectangleProfileDef(
        "AREA",
        None,
        file.createIfcAxis2Placement2D(
            file.createIfcCartesianPoint((0.45, 0.0)), None
        ),
        0.9,
        0.05,
    )
    representation = ifcopenshell.api.run(
        "geometry.add_profile_representation",
        file,
        context=body,
        profile=profile,
        depth=2.1,
    )
    ifcopenshell.api.run(
        "geometry.assign_representation",
        file,
        product=door,
        representation=representation,
    )

    if operation is not None:
        door_type = ifcopenshell.api.run(
            "root.create_entity", file, ifc_class="IfcDoorType", name="T"
        )
        door_type.OperationType = operation
        door_type.ParameterTakesPrecedence = True
        ifcopenshell.api.run(
            "type.assign_type",
            file,
            related_objects=[door],
            relating_type=door_type,
        )

    # In the quarter disk swept by the leaf (hinge at the origin).
    box("InSweep", 0.55, 0.55, 0.0, 0.3, 0.3, 1.0)
    # Behind the door, in the back rectangle.
    box("Behind", 0.45, -0.6, 0.0, 0.3, 0.3, 1.0)
    # Far from everything.
    box("FarAway", 5.0, 5.0, 0.0, 0.3, 0.3, 1.0)
    file.write(path)


class TestClearanceForDoors(unittest.TestCase):
    """The ClearanceForDoors rule on generated models."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, True)
        self.model = os.path.join(self.temp_dir, "door.ifc")
        make_model(self.model)

    @staticmethod
    def select(ifc_class):
        select = SelectFacet()
        select.applicability = [ids.Entity(name=ifc_class)]
        return select

    def run_rule(self, model=None, **parameters):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [model or self.model]
        
        rule = ClearanceForDoors(
            self.select("IFCDOOR"),
            self.select("IFCBUILDINGELEMENTPROXY"),
            **parameters,
        )
        rule_file.contains = [rule]
        rule_file.run()
        return rule

    def target_names(self, rule):
        return sorted(result.target.Name for result in rule.result)

    # ---- Nominal

    def test_swing_arc_obstruction_clashes(self):
        """A box in the swept quarter disk of a SingleSwingLeft door
        clashes; the far box and the back box stay silent."""
        rule = self.run_rule(zone_shape="Arc", sides="Swing")

        self.assertEqual(len(rule.result), 1)
        result = rule.result[0]
        self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertEqual(result.source.Name, "Door")
        self.assertEqual(result.target.Name, "InSweep")
        self.assertEqual(result.zone["shape"], "Arc")
        self.assertEqual(result.zone["side"], "Front")
        self.assertEqual(result.zone["leaf"], 1)
        # The zone dimensions come from the door: leaf width and height.
        self.assertAlmostEqual(result.zone["width"], 0.9, places=3)
        self.assertAlmostEqual(result.zone["height"], 2.1, places=3)
        self.assertGreater(result.penetration_depth, 0.1)

    def test_sides_both_checks_front_and_back(self):
        rule = self.run_rule(zone_shape="Arc", sides="Both")
        self.assertEqual(self.target_names(rule), ["Behind", "InSweep"])
        by_target = {result.target.Name: result for result in rule.result}
        self.assertEqual(by_target["Behind"].zone["side"], "Back")
        self.assertEqual(by_target["Behind"].zone["shape"], "Rectangle")

    def test_rectangle_front(self):
        rule = self.run_rule(zone_shape="Rectangle", sides="Front")
        self.assertEqual(self.target_names(rule), ["InSweep"])
        self.assertEqual(rule.result[0].zone["shape"], "Rectangle")

    def test_sides_back_only(self):
        rule = self.run_rule(zone_shape="Arc", sides="Back")
        self.assertEqual(self.target_names(rule), ["Behind"])
        self.assertEqual(rule.result[0].zone["side"], "Back")

    def test_override_dimensions(self):
        """Regulatory dimensions override the door size."""
        rule = self.run_rule(
            zone_shape="Rectangle",
            sides="Front",
            width=1.5,
            depth=2.0,
            height=2.5,
        )
        self.assertEqual(self.target_names(rule), ["InSweep"])
        self.assertAlmostEqual(rule.result[0].zone["width"], 1.5, places=6)
        self.assertAlmostEqual(rule.result[0].zone["depth"], 2.0, places=6)
        self.assertAlmostEqual(rule.result[0].zone["height"], 2.5, places=6)

    # ---- Sliding doors and unknown operation

    def test_sliding_door_uses_rectangles(self):
        """A sliding door cannot sweep: rectangles on both sides,
        whatever Zone_Shape says."""
        model = os.path.join(self.temp_dir, "sliding.ifc")
        make_model(model, operation="SLIDING_TO_LEFT")

        rule = self.run_rule(model=model, zone_shape="Arc", sides="Swing")
        self.assertEqual(self.target_names(rule), ["Behind", "InSweep"])
        self.assertEqual(
            {result.zone["shape"] for result in rule.result}, {"Rectangle"}
        )

    def test_unknown_operation_falls_back_conservative(self):
        """Without an operation type, rectangles on both sides."""
        model = os.path.join(self.temp_dir, "notype.ifc")
        make_model(model, operation=None)

        rule = self.run_rule(model=model, zone_shape="Arc", sides="Swing")
        self.assertEqual(self.target_names(rule), ["Behind", "InSweep"])
        self.assertEqual(
            {result.zone["shape"] for result in rule.result}, {"Rectangle"}
        )

    # ---- Tolerance

    def test_tolerance_ignores_deep_only(self):
        """A tolerance above the penetration depth ignores the box."""
        rule = self.run_rule(zone_shape="Arc", sides="Swing", tolerance=10.0)
        self.assertEqual(len(rule.result), 0)

    # ---- Cas limites

    def test_no_door_selected_no_crash(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.model]
        rule = ClearanceForDoors(
            self.select("IFCWINDOW"), self.select("IFCBUILDINGELEMENTPROXY")
        )
        rule_file.contains = [rule]
        rule_file.run()
        self.assertEqual(len(rule.result), 0)

    def test_invalid_parameters_raise_value_error(self):
        source = self.select("IFCDOOR")
        target = self.select("IFCBUILDINGELEMENTPROXY")

        with self.assertRaises(ValueError):
            ClearanceForDoors(source, target, zone_shape="Circle")
        with self.assertRaises(ValueError):
            ClearanceForDoors(source, target, sides="Left")
        with self.assertRaises(ValueError):
            ClearanceForDoors(source, target, leaves=0)
        with self.assertRaises(ValueError):
            ClearanceForDoors(source, target, width=-1.0)
        with self.assertRaises(ValueError):
            ClearanceForDoors(source, target, tolerance=-0.1)


class TestClearanceForDoorsUtilities(unittest.TestCase):
    """The door helpers of clash_utils used by ClearanceForDoors."""

    ORIGIN = np.array([0.0, 0.0, 0.0])
    X = np.array([1.0, 0.0, 0.0])
    Y = np.array([0.0, 1.0, 0.0])
    Z = np.array([0.0, 0.0, 1.0])

    def test_parse_door_operation(self):
        parsed = parse_door_operation("SINGLE_SWING_LEFT")
        self.assertEqual(parsed, {"mechanism": "swing", "leaves": 1, "hinges": ["left"]})

        parsed = parse_door_operation("SINGLE_SWING_RIGHT")
        self.assertEqual(parsed["hinges"], ["right"])

        parsed = parse_door_operation("DOUBLE_DOOR_SINGLE_SWING")
        self.assertEqual(parsed["leaves"], 2)
        self.assertEqual(parsed["hinges"], ["left", "right"])

        parsed = parse_door_operation("SLIDING_TO_LEFT")
        self.assertEqual(parsed["mechanism"], "sliding")

        self.assertEqual(parse_door_operation(None)["mechanism"], "unknown")
        self.assertEqual(parse_door_operation("FOLDING_TO_LEFT")["mechanism"], "unknown")

    def test_box_zone_penetration(self):
        front = make_box_zone(self.ORIGIN, self.X, self.Y, self.Z, 0.9, 0.9, 2.1, 1.0)
        # Inside: the depth is the distance to the nearest face.
        self.assertAlmostEqual(
            max_penetration_depth(front, [[0.2, 0.2, 0.2]]), 0.2, places=6
        )
        # On the boundary and outside: no penetration.
        self.assertAlmostEqual(
            max_penetration_depth(front, [[0.0, 0.2, 0.2], [1.5, 0.2, 0.2]]),
            0.0,
            places=6,
        )

    def test_box_zone_back_side(self):
        back = make_box_zone(self.ORIGIN, self.X, self.Y, self.Z, 0.9, 0.9, 2.1, -1.0)
        self.assertAlmostEqual(
            max_penetration_depth(back, [[0.2, -0.2, 0.2]]), 0.2, places=6
        )
        # The front point stays outside the back zone.
        self.assertAlmostEqual(
            max_penetration_depth(back, [[0.2, 0.2, 0.2]]), 0.0, places=6
        )

    def test_arc_zone_penetration(self):
        zone = make_arc_zone(self.ORIGIN, self.X, self.Y, self.Z, 0.9, 2.1)
        # A point in the quarter disk: the nearest boundary is the arc
        # (radius 0.9), closer than the flat radial faces. The arc is
        # approximated by 16 segments, hence the coarse precision.
        depth = max_penetration_depth(zone, [[0.4, 0.4, 1.0]])
        expected = 0.9 - np.sqrt(0.4**2 + 0.4**2)
        self.assertAlmostEqual(depth, expected, places=3)
        # Outside the radius: no penetration.
        self.assertAlmostEqual(
            max_penetration_depth(zone, [[0.7, 0.7, 1.0]]), 0.0, places=6
        )


if __name__ == "__main__":
    unittest.main()
