"""
Test suite for the FreeSpace rule (doc/ComplexRules/FreeSpace.md).

The models are generated with the ifcopenshell API: a box room and
obstruction boxes (table, partition, suspended lamp).

Execution (from the repository root):
    python -m pytest tests/test_FreeSpace.py -v
"""
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell
import ifcopenshell.api
import numpy as np

from Rules import FreeSpace
from RuleClass import SelectFacet, RuleFile, ClashResultOneObject
from clash_utils import (
    cylinder_solid,
    lowest_footprint,
    shapes_intersect_volume,
)
from ifctester import ids


def make_model(path, elements):
    """elements: list of (name, x, y, z, dx, dy, height) boxes."""
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


class TestFreeSpace(unittest.TestCase):
    """The FreeSpace rule on generated models."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, True)

        # A 4 x 4 room with a table in the middle.
        self.room_model = os.path.join(self.temp_dir, "room.ifc")
        make_model(
            self.room_model,
            [("Room", 2, 2, 0, 4, 4, 3), ("Table", 2, 2, 0, 1, 1, 0.75)],
        )

        # A room smaller than the turning circle.
        self.small_model = os.path.join(self.temp_dir, "small.ifc")
        make_model(self.small_model, [("Room", 0.6, 0.6, 0, 1.2, 1.2, 3)])

        # A 3 x 3 room split in two by a partition (halves of 1.4 m).
        self.split_model = os.path.join(self.temp_dir, "split.ifc")
        make_model(
            self.split_model,
            [("Room", 1.5, 1.5, 0, 3, 3, 3), ("Partition", 1.5, 1.5, 0, 0.2, 3, 3)],
        )

        # A 4 x 4 room with a lamp suspended at 2 m.
        self.high_model = os.path.join(self.temp_dir, "high.ifc")
        make_model(
            self.high_model,
            [("Room", 2, 2, 0, 4, 4, 3), ("Lamp", 2, 2, 2.0, 2, 2, 0.5)],
        )

        # A corridor exactly as wide as the turning circle.
        self.corridor_model = os.path.join(self.temp_dir, "corridor.ifc")
        make_model(self.corridor_model, [("Room", 1.5, 0.75, 0, 3, 1.5, 3)])

    @staticmethod
    def select(name):
        select = SelectFacet()
        select.applicability = [ids.Attribute(name="Name", value=name)]
        return select

    def run_rule(self, model, context_names=("Table",), **parameters):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [model]
        context = SelectFacet()
        parameters["state"]="Display_Result"
        context.applicability = [
            ids.Attribute(name="Name", value=name) for name in context_names
        ]
        rule = FreeSpace(self.select("Room"), context, **parameters)
        rule_file.contains = [rule]
        rule_file.run()
        return rule

    def placement_of(self, rule):
        self.assertEqual(len(rule.placements), 1)
        return rule.placements[list(rule.placements)[0]]

    # ---- Nominal

    def test_free_placement_found(self):
        """A 1.50 m turning circle fits in a 4 x 4 room with a table."""
        rule = self.run_rule(self.room_model, diameter=1.5, height=1.4)

        self.assertEqual(len(rule.result), 0)
        placement = self.placement_of(rule)
        x, y, z_base = placement["position"]
        # Inside the room (0..4), on the floor.
        self.assertGreaterEqual(x, 0.0)
        self.assertLessEqual(x, 4.0)
        self.assertGreaterEqual(y, 0.0)
        self.assertLessEqual(y, 4.0)
        self.assertAlmostEqual(z_base, 0.0, places=6)
        self.assertGreaterEqual(placement["margin"], 0.0)

    def test_small_room_clashes(self):
        """A 1.2 x 1.2 room cannot host a 1.50 m circle."""
        rule = self.run_rule(self.small_model, context_names=(), diameter=1.5, height=1.4)
        self.assertEqual(len(rule.result), 1)
        self.assertIsInstance(rule.result[0], ClashResultOneObject)
        self.assertEqual(rule.result[0].source.Name, "Room")
        self.assertEqual(len(rule.placements), 0)

    def test_split_room_clashes(self):
        """The partition leaves two halves of 1.4 m: too narrow."""
        rule = self.run_rule(
            self.split_model, context_names=("Partition",), diameter=1.5, height=1.4
        )
        self.assertEqual(len(rule.result), 1)

    def test_height_respects_suspended_obstacles(self):
        """The lamp at 2 m does not block a 1.4 m high cylinder, but
        blocks a 2.5 m one."""
        rule = self.run_rule(
            self.high_model, context_names=("Lamp",), diameter=1.5, height=1.4
        )
        self.assertEqual(len(rule.result), 0)
        self.placement_of(rule)

        rule = self.run_rule(
            self.high_model, context_names=("Lamp",), diameter=1.5, height=2.5
        )
        self.assertEqual(len(rule.result), 1)

    # ---- Touching is allowed

    def test_tangent_placement_is_free(self):
        """A corridor exactly as wide as the circle: the tangent
        placement is free, with a zero margin."""
        rule = self.run_rule(
            self.corridor_model, context_names=(), diameter=1.5, height=1.4
        )
        self.assertEqual(len(rule.result), 0)
        placement = self.placement_of(rule)
        self.assertAlmostEqual(placement["margin"], 0.0, places=3)

    def test_tangent_larger_diameter_clashes(self):
        """The same corridor cannot host a 1.60 m circle."""
        rule = self.run_rule(
            self.corridor_model, context_names=(), diameter=1.6, height=1.4
        )
        self.assertEqual(len(rule.result), 1)

    # ---- Context

    def test_empty_context_free(self):
        """Without obstacles, the footprint alone decides."""
        rule = self.run_rule(self.room_model, context_names=(), diameter=1.5, height=1.4)
        self.assertEqual(len(rule.result), 0)
        self.placement_of(rule)

    # ---- Cas limites

    def test_no_source_selected_no_crash(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.room_model]
        context = SelectFacet()
        rule = FreeSpace(self.select("Nothing"), context, diameter=1.5, height=1.4)
        rule_file.contains = [rule]
        rule_file.run()
        self.assertEqual(len(rule.result), 0)

    def test_invalid_parameters_raise_value_error(self):
        source = self.select("Room")
        context = SelectFacet()

        with self.assertRaises(ValueError):
            FreeSpace(source, context, diameter=0)
        with self.assertRaises(ValueError):
            FreeSpace(source, context, diameter=-1.5)
        with self.assertRaises(ValueError):
            FreeSpace(source, context)  # height missing
        with self.assertRaises(ValueError):
            FreeSpace(source, context, height=-1.0)


class TestFreeSpaceUtilities(unittest.TestCase):
    """The free space helpers of clash_utils."""

    def box_mesh(self, dx=2.0, dy=3.0, height=1.0):
        vertices = np.array(
            [
                [0.0, 0.0, 0.0], [dx, 0.0, 0.0], [dx, dy, 0.0], [0.0, dy, 0.0],
                [0.0, 0.0, height], [dx, 0.0, height], [dx, dy, height],
                [0.0, dy, height],
            ]
        )
        faces = np.array(
            [
                [0, 2, 1], [0, 3, 2],
                [4, 5, 6], [4, 6, 7],
                [0, 1, 5], [0, 5, 4],
                [1, 2, 6], [1, 6, 5],
                [2, 3, 7], [2, 7, 6],
                [3, 0, 4], [3, 4, 7],
            ]
        )
        return vertices, faces

    def test_lowest_footprint(self):
        vertices, faces = self.box_mesh()
        footprint, z_min = lowest_footprint(vertices, faces)
        self.assertAlmostEqual(z_min, 0.0, places=9)
        self.assertAlmostEqual(footprint.area, 6.0, places=6)
        self.assertAlmostEqual(footprint.bounds[0], 0.0, places=6)
        self.assertAlmostEqual(footprint.bounds[2], 2.0, places=6)

    def test_intersect_volume(self):
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
        from OCC.Core.gp import gp_Pnt

        box_a = BRepPrimAPI_MakeBox(gp_Pnt(0, 0, 0), 1.0, 1.0, 1.0).Shape()
        box_b = BRepPrimAPI_MakeBox(gp_Pnt(0.5, 0.5, 0.5), 1.0, 1.0, 1.0).Shape()
        box_far = BRepPrimAPI_MakeBox(gp_Pnt(5, 5, 5), 1.0, 1.0, 1.0).Shape()
        box_touch = BRepPrimAPI_MakeBox(gp_Pnt(1.0, 0, 0), 1.0, 1.0, 1.0).Shape()

        self.assertGreater(shapes_intersect_volume(box_a, box_b), 0.1)
        self.assertAlmostEqual(shapes_intersect_volume(box_a, box_far), 0.0, places=9)
        # Touching does not intersect: no volume.
        self.assertAlmostEqual(shapes_intersect_volume(box_a, box_touch), 0.0, places=9)

    def test_cylinder_solid(self):
        from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
        from OCC.Core.gp import gp_Pnt

        cylinder = cylinder_solid(0.0, 0.0, 0.0, radius=0.75, height=1.4)
        inside_box = BRepPrimAPI_MakeBox(gp_Pnt(-1, -1, -1), 2.0, 2.0, 2.0).Shape()
        self.assertGreater(shapes_intersect_volume(cylinder, inside_box), 1.0)


if __name__ == "__main__":
    unittest.main()
