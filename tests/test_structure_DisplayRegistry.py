"""
Test suite for the display geometry registry of RuleClass.py.

The GUI itself (init_display) cannot run headless: this file tests the
registry itself — the registration, the category validation, the
category filtering of _display_registered_items (on a stubbed display),
the lightweight shape conversions of _item_shape and the
keep_display_items lifecycle.

Execution (from the repository root):
    python -m pytest tests/test_structure_DisplayRegistry.py -v
"""
import sys
import unittest

sys.path.insert(0, "./ifcclash_plus")

from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.gp import gp_Pnt

from Rules import Alignement
from RuleClass import DisplayItem, SelectFacet


class StubContext:
    """Records the shapes sent to the viewer."""

    def __init__(self):
        self.displayed = []

    def Display(self, ais_shape, update):
        self.displayed.append(ais_shape)


class StubDisplay:
    def __init__(self):
        self.Context = StubContext()


class StubOBB:
    """Anything with to_TopoDS_Compound is converted at display time."""

    def __init__(self, compound):
        self._compound = compound

    def to_TopoDS_Compound(self):
        return self._compound


class TestDisplayRegistry(unittest.TestCase):
    """register_display_item and available_display_categories."""

    def setUp(self):
        self.rule = Alignement(SelectFacet(), tolerance=0.1)

    def test_register_and_available_categories(self):
        self.assertEqual(self.rule.display_items, [])
        self.assertEqual(self.rule.available_display_categories(), set())

        self.rule.register_display_item("axis", ("axis", (0, 0, 0), (0, 0, 1)))
        self.rule.register_display_item("zone", ("face", [(0, 0, 0)] * 3))
        self.rule.register_display_item(
            "zone", ("face", [(0, 0, 0)] * 3), color=(0, 1, 0), element="an_entity"
        )

        self.assertEqual(len(self.rule.display_items), 3)
        self.assertEqual(self.rule.available_display_categories(), {"axis", "zone"})

        item = self.rule.display_items[0]
        self.assertIsInstance(item, DisplayItem)
        self.assertEqual(item.category, "axis")
        self.assertEqual(item.color, (1, 0, 0))
        self.assertEqual(item.transparency, 0.6)
        self.assertIsNone(item.element)
        self.assertEqual(self.rule.display_items[2].element, "an_entity")

    def test_invalid_category_raises(self):
        with self.assertRaises(ValueError):
            self.rule.register_display_item("polygon", ("face", [(0, 0, 0)] * 3))

    def test_display_options_default(self):
        for category, enabled in self.rule.display_options.items():
            self.assertTrue(enabled)


class TestDisplayRegisteredItems(unittest.TestCase):
    """The generic display of the registry, filtered by category."""

    def setUp(self):
        self.rule = Alignement(SelectFacet(), tolerance=0.1)
        self.rule.display = StubDisplay()

    def displayed_shapes(self):
        context = self.rule.display.Context
        return [ais.Shape() for ais in context.displayed]

    def test_all_categories_displayed_by_default(self):
        self.rule.register_display_item("axis", ("axis", (0, 0, 0), (1, 0, 0), 1.0))
        self.rule.register_display_item(
            "face", ("face", [(0, 0, 0), (1, 0, 0), (0, 1, 0)])
        )
        self.rule.register_display_item("segment", ("edge", (0, 0, 0), (1, 1, 1)))

        self.rule._display_registered_items()

        shapes = self.displayed_shapes()
        self.assertEqual(len(shapes), 3)
        for shape in shapes:
            self.assertIsInstance(shape, TopoDS_Shape)

    def test_filtered_category_is_hidden(self):
        self.rule.register_display_item("axis", ("axis", (0, 0, 0), (1, 0, 0)))
        self.rule.register_display_item("zone", ("edge", (0, 0, 0), (1, 0, 0)))

        self.rule.display_options["zone"] = False
        self.rule._display_registered_items()

        shapes = self.displayed_shapes()
        self.assertEqual(len(shapes), 1)

    def test_color_and_transparency_applied(self):
        self.rule.register_display_item(
            "zone", ("edge", (0, 0, 0), (1, 0, 0)), color=(0, 1, 0), transparency=0.2
        )

        self.rule._display_registered_items()

        ais_shape = self.rule.display.Context.displayed[0]
        self.assertAlmostEqual(ais_shape.Transparency(), 0.2)

    def test_unknown_category_in_options_displays_by_default(self):
        """An item whose category is missing from display_options is
        displayed (the options only hide)."""
        self.rule.display_options = {}
        self.rule.register_display_item("axis", ("edge", (0, 0, 0), (1, 0, 0)))

        self.rule._display_registered_items()

        self.assertEqual(len(self.rule.display.Context.displayed), 1)


class TestItemShape(unittest.TestCase):
    """The lightweight representations of _item_shape."""

    def setUp(self):
        self.rule = Alignement(SelectFacet(), tolerance=0.1)

    def test_topods_shape_passthrough(self):
        edge = BRepBuilderAPI_MakeEdge(gp_Pnt(0, 0, 0), gp_Pnt(1, 0, 0)).Edge()
        item = DisplayItem(category="segment", shape=edge)
        self.assertIs(self.rule._item_shape(item), edge)

    def test_obb_converted_to_compound(self):
        edge = BRepBuilderAPI_MakeEdge(gp_Pnt(0, 0, 0), gp_Pnt(1, 0, 0)).Edge()
        compound = StubOBB(edge)
        item = DisplayItem(category="obb", shape=compound)
        self.assertIs(self.rule._item_shape(item), edge)

    def test_axis_edge_from_center_and_direction(self):
        item = DisplayItem(category="axis", shape=("axis", (0, 0, 0), (0, 0, 1), 2.0))
        edge = self.rule._item_shape(item)
        # An edge along +Z, 2 m long.
        self.assertAlmostEqual(BRepAdaptor_Curve(edge).LastParameter(), 2.0)

    def test_axis_default_length(self):
        item = DisplayItem(category="axis", shape=("axis", (0, 0, 0), (0, 0, 1)))
        edge = self.rule._item_shape(item)
        self.assertAlmostEqual(BRepAdaptor_Curve(edge).LastParameter(), 0.5)

    def test_face_from_three_corners(self):
        item = DisplayItem(
            category="face",
            shape=("face", [(0, 0, 0), (1, 0, 0), (0, 1, 0)]),
        )
        face = self.rule._item_shape(item)
        self.assertEqual(face.ShapeType(), TopAbs_FACE)

    def test_unsupported_shape_raises(self):
        item = DisplayItem(category="zone", shape=42)
        with self.assertRaises(TypeError):
            self.rule._item_shape(item)


class TestKeepDisplayItems(unittest.TestCase):
    """The lifecycle of the registry through end_rule_action."""

    def setUp(self):
        self.rule = Alignement(SelectFacet(), tolerance=0.1, state="Final")

    def test_registry_kept_by_default_after_final_run(self):
        self.rule.register_display_item("axis", ("edge", (0, 0, 0), (1, 0, 0)))
        self.rule.end_rule_action()
        self.assertEqual(len(self.rule.display_items), 1)

    def test_registry_cleared_when_not_kept(self):
        self.rule.register_display_item("axis", ("edge", (0, 0, 0), (1, 0, 0)))
        self.rule.keep_display_items = False
        self.rule.end_rule_action()
        self.assertEqual(self.rule.display_items, [])


if __name__ == "__main__":
    unittest.main()
