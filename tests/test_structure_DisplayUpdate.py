"""
Test suite for the display update of the base functions of RuleClass.py.

The GUI itself (init_display) cannot run headless: this file tests the
data the display functions are built on — the green/red color map of
the selections, the unique result pairs and the one-color-per-pair
assignment, the display hooks removal (everything goes through the
display registry, filled during run()) and the centralized
Display_Input handling of end_rule_action. The registry itself is
covered by test_structure_DisplayRegistry.py.

Execution (from the repository root):
    python -m pytest tests/test_structure_DisplayUpdate.py -v
"""
import os
import random
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell
import ifcopenshell.api

from Rules import Alignement, ClearanceForDoors, FreeSpace, SurfaceRecover
from RuleClass import SelectFacet, RuleFile
from ifctester import ids


def make_model(path, elements):
    """elements: list of (ifc_class, name, x, y, z, dx, dy, height)."""
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
    for ifc_class, name, x, y, z, dx, dy, height in elements:
        element = ifcopenshell.api.run(
            "root.create_entity", file, ifc_class=ifc_class, name=name
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


def select_by_name(name):
    select = SelectFacet()
    select.applicability = [ids.Attribute(name="Name", value=name)]
    return select


def select_by_class(ifc_class):
    select = SelectFacet()
    select.applicability = [ids.Entity(name=ifc_class)]
    return select


class TestDisplayColorMap(unittest.TestCase):
    """The green/red map and the pair lines, on real rule runs."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, True)

    def run_rule(self, model, rule):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [model]
        rule_file.contains = [rule]
        rule_file.run()
        return rule

    def test_one_object_color_map_green_and_red(self):
        """Alignement: every selected object is green except the
        clashing one, red."""
        model = os.path.join(self.temp_dir, "row.ifc")
        make_model(
            model,
            [("IfcColumn", "C0", 0, 0, 0, 0.3, 0.3, 3),
                ("IfcColumn", "C1", 2, 0, 0, 0.3, 0.3, 3),
                ("IfcColumn", "C2", 4, 0, 0, 0.3, 0.3, 3),
                ("IfcColumn", "C3", 8, 0, 0, 0.3, 0.3, 3),
                ("IfcColumn", "C4", 10, 0, 0, 0.3, 0.3, 3),
                ("IfcColumn", "C5", 12, 0, 0, 0.3, 0.3, 3),
                ("IfcColumn", "C_offset", 6, 0.5, 0, 0.3, 0.3, 3),
            ],
        )
        rule = self.run_rule(
            model, Alignement(select_by_class("IFCCOLUMN"), tolerance=0.15)
        )
        self.assertEqual(len(rule.result), 1)

        color_map = rule._result_color_map()
        # Every selected object appears exactly once.
        self.assertEqual(len(color_map), 7)
        # The clashing object is red, the others are green.
        clashing = rule.result[0].source
        for entity, is_red in color_map.items():
            self.assertEqual(is_red, entity == clashing)

    def test_two_objects_color_map_pairs_and_colors(self):
        """SurfaceRecover with two source/target pairs: the map covers
        both selections, one unique pair per result, one distinct color
        per pair."""
        model = os.path.join(self.temp_dir, "contact.ifc")
        make_model(
            model,
            [
                # Two slabs hovering 0.9 m above the same cuboid
                # (cuboid top at 2.0, slab bottoms at 2.9).
                ("IfcSlab", "SlabA", 2, 0, 2.9, 3, 3, 0.1),
                ("IfcSlab", "SlabB", 2, 0.3, 2.9, 3, 3, 0.1),
                ("IfcBuildingElementProxy", "Cuboid", 2, 0, 0, 2, 1, 2.0),
            ],
        )
        rule = self.run_rule(
            model,
            SurfaceRecover(
                select_by_class("IFCSLAB"),
                select_by_class("IFCBUILDINGELEMENTPROXY"),
                direction="Bottom",
                reference="Source",
                tolerance=1.0,
                min_covering="101%",
            ),
        )
        self.assertEqual(len(rule.result), 2)

        # The color map covers both selections: every object clashes
        # here (both slabs miss the 101% covering), everything is red.
        color_map = rule._result_color_map()
        self.assertEqual(len(color_map), 3)
        self.assertTrue(all(color_map.values()))

        # One unique pair per result.
        pairs = rule._result_pairs()
        self.assertEqual(len(pairs), 2)
        self.assertEqual(
            {(pair[0].Name, pair[1].Name) for pair in pairs},
            {("SlabA", "Cuboid"), ("SlabB", "Cuboid")},
        )

        # One distinct color per pair (deterministic under a fixed seed).
        random.seed(20261007)
        colors = rule._pair_colors(pairs)
        self.assertEqual(len(colors), 2)
        first, second = list(colors.values())
        self.assertNotEqual(
            (first.Red(), first.Green(), first.Blue()),
            (second.Red(), second.Green(), second.Blue()),
        )

    def test_two_objects_map_keeps_green_objects(self):
        """A rule run where only part of the selections clashes: the
        untouched objects stay green."""
        model = os.path.join(self.temp_dir, "mixed.ifc")
        make_model(
            model,
            [
                # In contact (0.9 m gap, tolerance 1.0) with the cuboid.
                ("IfcSlab", "SlabNear", 2, 0, 2.9, 3, 3, 0.1),
                # Far away: no contact, no result.
                ("IfcSlab", "SlabFar", 2, 20, 2.9, 3, 3, 0.1),
                ("IfcBuildingElementProxy", "Cuboid", 2, 0, 0, 2, 1, 2.0),
            ],
        )
        rule = self.run_rule(
            model,
            SurfaceRecover(
                select_by_class("IFCSLAB"),
                select_by_class("IFCBUILDINGELEMENTPROXY"),
                direction="Bottom",
                reference="Source",
                tolerance=1.0,
                min_covering="101%",
            ),
        )
        self.assertEqual(len(rule.result), 1)

        color_map = rule._result_color_map()
        by_name = {entity.Name: is_red for entity, is_red in color_map.items()}
        self.assertEqual(by_name, {"SlabNear": True, "Cuboid": True, "SlabFar": False})

        # One pair, one line color.
        pairs = rule._result_pairs()
        self.assertEqual(len(pairs), 1)

    def test_no_display_hooks_left(self):
        """The display hooks are gone: no rule overrides one, the base
        classes do not define them anymore. Every auxiliary geometry
        goes through the display registry, filled during run()."""
        from Rules import DirectView

        for rule_class in (
            Alignement,
            ClearanceForDoors,
            SurfaceRecover,
            FreeSpace,
            DirectView,
        ):
            self.assertNotIn("_display_input_zone", rule_class.__dict__)
            self.assertNotIn("_display_input_context", rule_class.__dict__)
            self.assertNotIn("_display_result_specific", rule_class.__dict__)

        from RuleClass import RuleCheck, RuleCheckOneObject, RuleCheckTwoObjects

        for base in (RuleCheck, RuleCheckOneObject, RuleCheckTwoObjects):
            self.assertNotIn("_display_input_zone", base.__dict__)
            self.assertNotIn("_display_input_context", base.__dict__)
            self.assertNotIn("_display_result_specific", base.__dict__)
            self.assertNotIn("_display_input_specific", base.__dict__)

    def test_display_input_centralized_in_end_rule_action(self):
        """end_rule_action owns the Display_Input state: it displays
        the generic input plus the registry, then stops the rule. The
        run() of the rules holds no display logic anymore."""
        import RuleClass as rule_class_module

        calls = []

        class FakeContext:
            def __init__(self):
                self.displayed = []

            def Display(self, ais_shape, update):
                self.displayed.append(ais_shape)

        class FakeDisplay:
            Context = FakeContext()

            def FitAll(self):
                calls.append("FitAll")

            def start_display(self):
                calls.append("start_display")

        fake_display = FakeDisplay()

        def fake_init_display():
            return fake_display, fake_display.start_display, None, None

        original = rule_class_module.init_display
        rule_class_module.init_display = fake_init_display
        try:
            rule = Alignement(SelectFacet(), tolerance=0.1, state="Display_Input")
            rule.register_display_item("zone", ("edge", (0, 0, 0), (1, 0, 0)))
            rule.end_rule_action()
        finally:
            rule_class_module.init_display = original

        self.assertEqual(calls, ["FitAll", "start_display"])
        # The registered zone item has been displayed by the registry.
        self.assertEqual(len(fake_display.Context.displayed), 1)

    def test_pilot_rules_fill_the_registry(self):
        """The migrated rules register their auxiliary geometries
        during run(), in the Final state: the display is a read-only
        consumer of the registry."""

        # Alignement: the fitted element of every valid group.
        model = os.path.join(self.temp_dir, "row.ifc")
        make_model(
            model,
            [("IfcColumn", "C0", 0, 0, 0, 0.3, 0.3, 3),
                ("IfcColumn", "C1", 2, 0, 0, 0.3, 0.3, 3),
                ("IfcColumn", "C2", 4, 0, 0, 0.3, 0.3, 3),
                ("IfcColumn", "C3", 8, 0, 0, 0.3, 0.3, 3),
                ("IfcColumn", "C4", 10, 0, 0, 0.3, 0.3, 3),
                ("IfcColumn", "C5", 12, 0, 0, 0.3, 0.3, 3),
                ("IfcColumn", "C_offset", 6, 0.5, 0, 0.3, 0.3, 3)],
        )
        rule = self.run_rule(
            model, Alignement(select_by_class("IFCCOLUMN"), tolerance=0.15)
        )
        self.assertEqual(rule.available_display_categories(), {"zone"})
        self.assertGreaterEqual(len(rule.display_items), 1)
        for item in rule.display_items:
            self.assertEqual(item.category, "zone")
            self.assertEqual(item.color, (0.5, 0, 1))

        # SurfaceRecover: the contact triangles of every clash.
        model = os.path.join(self.temp_dir, "contact.ifc")
        make_model(
            model,
            [
                ("IfcSlab", "SlabA", 2, 0, 2.9, 3, 3, 0.1),
                ("IfcSlab", "SlabB", 2, 0.3, 2.9, 3, 3, 0.1),
                ("IfcBuildingElementProxy", "Cuboid", 2, 0, 0, 2, 1, 2.0),
            ],
        )
        rule = self.run_rule(
            model,
            SurfaceRecover(
                select_by_class("IFCSLAB"),
                select_by_class("IFCBUILDINGELEMENTPROXY"),
                direction="Bottom",
                reference="Source",
                tolerance=1.0,
                min_covering="101%",
            ),
        )
        self.assertGreater(len(rule.result), 0)
        self.assertEqual(rule.available_display_categories(), {"face"})
        for item in rule.display_items:
            self.assertEqual(item.category, "face")
            self.assertEqual(item.color, (1, 0.5, 0))


if __name__ == "__main__":
    unittest.main()
