"""The compute contract of Alignement (SPEC Separation moteur/gestion),
tested directly — one entity list and the named parameters in, raw
results out.

The test models are the ones of the unit suite, generated with the
ifcopenshell API: a row of columns with one plan offset (the vertical
case), walls in a common plane with one wall out of it (the horizontal
Plane case), and wall segments on one axis with one perpendicular
wall (the horizontal Line case).

The engine helpers read their configuration off the instance: the
compute poses the named parameters on the instance before running
(documented exception — the node remains the config carrier) and
leaves its engine state on it (self.alignment, the objects/groups of
the fitted zones).

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_Alignement.py -v
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

from Rules import Alignement
from RuleClass import SelectFacet, RuleFile, ClashResultOneObject
from registry import compute_from_config, engine_params
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape
from tests.test_UnitRule_Alignement import make_model, column, wall


def select_by_class(ifc_class):
    from ifctester import ids

    select = SelectFacet()
    select.applicability = [ids.Entity(name=ifc_class)]
    return select


class TestComputeAlignement(unittest.TestCase):
    """The compute contract of Alignement: one list + the named
    parameters."""

    @classmethod
    def setUpClass(cls):
        cls._temp_dir = tempfile.mkdtemp()
        cls.models = {}
        cls.models["row.ifc"] = os.path.join(cls._temp_dir, "row.ifc")
        make_model(
            cls.models["row.ifc"],
            [column(f"C{x}", x, 0.0) for x in (0, 2, 4, 8, 10, 12)]
            + [column("C_offset", 6, 0.5)],
        )
        cls.models["row_ok.ifc"] = os.path.join(cls._temp_dir, "row_ok.ifc")
        make_model(
            cls.models["row_ok.ifc"],
            [column(f"C{x}", x, 0.0) for x in (0, 2, 4, 6, 8)],
        )
        cls.models["facade.ifc"] = os.path.join(cls._temp_dir, "facade.ifc")
        make_model(
            cls.models["facade.ifc"],
            [
                wall("W_left", 0.0, 0.0),
                wall("W_middle", 6.0, 0.5),
                wall("W_right", 12.0, 0.2),
                ("IfcWall", "W_behind", (6.0, 2.0, 1.0), 0.0, 4.0, 0.2, 3.0),
            ],
        )
        cls.models["line.ifc"] = os.path.join(cls._temp_dir, "line.ifc")
        make_model(
            cls.models["line.ifc"],
            [
                wall("W_axis_0", 0.0, -2.0),
                wall("W_axis_1", 6.0, -2.0),
                wall("W_axis_2", 12.0, -2.0),
                wall("W_crossing", 6.0, -2.0, angle=__import__("math").pi / 2),
            ],
        )
        # ifcopenshell 0.9: an entity does not keep its file alive.
        cls.files = {
            name: ifcopenshell.open(path) for name, path in cls.models.items()
        }

    @classmethod
    def tearDownClass(cls):
        cls.files.clear()
        shutil.rmtree(cls._temp_dir, True)

    def _elements(self, model, ifc_class):
        return [e for e in self.files[model].by_type("IfcProduct") if e.is_a(ifc_class)]

    def _compute(self, model="row.ifc", ifc_class="IfcColumn", **parameters):
        rule = Alignement(None, tolerance=1.0)
        return rule.compute(
            self._elements(model, ifc_class),
            parameters.get("axis"),
            parameters.get("alignment_type", "Plane"),
            parameters.get("tolerance", 0.15),
            parameters.get("min_group", 3),
        )

    def test_vertical_row_outlier_clashes(self):
        """A row of columns, one column offset in plan: the outlier
        clashes, its offset guides the correction."""
        results = self._compute(axis="Vertical", tolerance=0.15)
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIsInstance(result, ClashResultOneObject)
        self.assertTrue(result.status)
        self.assertEqual(result.source.Name, "C_offset")
        self.assertGreater(result.info.offset, 0.35)
        self.assertLess(result.info.offset, 0.5)
        self.assertEqual(result.info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_vertical_alignment_engine_state(self):
        """The engine state left on the node: the fitted line and its
        member objects (the adapter-level information)."""
        rule = Alignement(None, tolerance=1.0)
        rule.compute(
            self._elements("row.ifc", "IfcColumn"),
            "Vertical",
            "Plane",
            0.15,
            3,
        )
        self.assertIsNotNone(rule.alignment)
        self.assertEqual(rule.alignment["orientation"], "Vertical")
        self.assertEqual(rule.alignment["element"], "Line")
        self.assertEqual(len(rule.alignment["members"]), 6)
        member_names = [member.Name for member in rule.alignment["members"]]
        self.assertNotIn("C_offset", member_names)

    def test_auto_detection_matches_vertical(self):
        """Without axis, the vertical set is detected and gives the
        same clash."""
        results = self._compute(tolerance=0.15)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source.Name, "C_offset")

    def test_horizontal_plane_outlier_clashes(self):
        """Walls in one common plane, one wall one meter higher: it
        belongs to no valid group and clashes."""
        results = self._compute(
            model="facade.ifc",
            ifc_class="IfcWall",
            axis="Horizontal",
            alignment_type="Plane",
            tolerance=0.05,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source.Name, "W_behind")

    def test_horizontal_line_crossing_wall_clashes(self):
        results = self._compute(
            model="line.ifc",
            ifc_class="IfcWall",
            axis="Horizontal",
            alignment_type="Line",
            tolerance=0.1,
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source.Name, "W_crossing")
        self.assertGreater(results[0].info.offset, 1.0)

    def test_clean_row_no_clash(self):
        results = self._compute(model="row_ok.ifc", axis="Vertical")
        self.assertEqual(results, [])

    def test_empty_set_no_clash(self):
        rule = Alignement(None, tolerance=1.0)
        results = rule.compute([], None, "Plane", 0.15, 3)
        self.assertEqual(results, [])
        self.assertIsNone(rule.alignment)

    def test_compute_is_pure_of_management_and_display(self):
        rule = Alignement(None, axis="Vertical", tolerance=0.15)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = self._compute(axis="Vertical", tolerance=0.15)

        self.assertEqual(len(results), 1)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)


class TestComputeAlignementDispatch(unittest.TestCase):
    """The flat JSON declarations drive the compute through the
    registry dispatch."""

    def test_engine_params(self):
        self.assertEqual(
            engine_params("Alignement"),
            ["axis", "alignment_type", "tolerance", "min_group"],
        )

    def test_declaration_drives_the_compute(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, True)
        model = os.path.join(temp_dir, "row.ifc")
        make_model(
            model,
            [column(f"C{x}", x, 0.0) for x in (0, 2, 4, 8, 10, 12)]
            + [column("C_offset", 6, 0.5)],
        )
        file = ifcopenshell.open(model)
        elements = [
            e for e in file.by_type("IfcProduct") if e.is_a("IfcColumn")
        ]

        rule = Alignement(
            select_by_class("IFCCOLUMN"), axis="Vertical", tolerance=0.15
        )
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        results = compute_from_config(config, elements)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source.Name, "C_offset")


class TestComputeAlignementThroughAdapter(unittest.TestCase):
    """The migration adapter (run + RuleFile) produces the RuleOutput
    of the pipeline (SPEC): one integration node."""

    def test_rule_output_after_rule_file_run(self):
        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, True)
        model = os.path.join(temp_dir, "row.ifc")
        make_model(
            model,
            [column(f"C{x}", x, 0.0) for x in (0, 2, 4, 8, 10, 12)]
            + [column("C_offset", 6, 0.5)],
        )

        rule_file = RuleFile()
        rule_file.list_ifc_path = [model]
        rule = Alignement(
            select_by_class("IFCCOLUMN"), axis="Vertical", tolerance=0.15
        )
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        self.assertEqual(len(rule.result), 1)
        self.assertEqual(rule.result[0].source.Name, "C_offset")
        self.assertIsNotNone(rule.output)
        self.assertIs(rule.output.results, rule.result)


if __name__ == "__main__":
    unittest.main()
