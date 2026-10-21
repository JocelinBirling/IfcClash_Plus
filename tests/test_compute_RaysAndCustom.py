"""The compute contract of Ray_Check and OBB_Custom (SPEC Separation
moteur/gestion), tested directly — lists of entities and named
parameters in, raw results out.

Ray_Check is the first three-list engine of the migration: the
context is liste_objet_contexte, a third INPUT list, never a hidden
select (SPEC). The generated model holds a source box, a target box
4 m away and a context box standing between them.

OBB_Custom builds its detection zones from a list of modification
strings; the reference case mirrors OBB_Above: the band detached
above the source OBB catches the cube 1 m above.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_RaysAndCustom.py -v
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell

from registry import compute_from_config, engine_params
from Rules import OBB_Custom, Ray_Check
from RuleClass import ClashResultTwoObjects
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape
from tests.test_UnitRule_ClearanceAxisToAxis import box, make_model

MODEL_DIR = "IFC_Test_Model/IFC_Model"


class TestComputeRayCheck(unittest.TestCase):
    """The compute contract of Ray_Check: two lists + the context
    list + the named parameters."""

    @classmethod
    def setUpClass(cls):
        import tempfile, shutil

        cls._temp_dir = tempfile.mkdtemp()
        cls.model = os.path.join(cls._temp_dir, "rays.ifc")
        make_model(
            cls.model,
            [
                box("SourceA", 0.0, dx=0.5, dy=0.5, height=0.5),
                box("TargetA", 4.0, dx=0.5, dy=0.5, height=0.5),
                box("ContextA", 2.0, dx=0.5, dy=0.5, height=0.5),
            ],
        )
        cls.file = ifcopenshell.open(cls.model)

    @classmethod
    def tearDownClass(cls):
        import shutil

        shutil.rmtree(cls._temp_dir, True)

    def _element(self, name):
        matches = [e for e in self.file.by_type("IfcProduct") if e.Name == name]
        self.assertTrue(matches, f"no element named {name!r}")
        return matches[0]

    def _compute(self, max_ray_length, context):
        rule = Ray_Check(None, None, None, max_ray_length)
        return rule.compute(
            [self._element("SourceA")],
            [self._element("TargetA")],
            max_ray_length,
            liste_objet_contexte=[self._element(e) for e in context],
        )

    def test_direct_view_without_context(self):
        results = self._compute(10.0, [])
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertTrue(result.status)
        self.assertEqual(result.source.Name, "SourceA")
        self.assertEqual(result.target.Name, "TargetA")

        # The verdict carries the ray: the measured distance and the
        # two centers.
        self.assertAlmostEqual(result.info.distance, 4.0, delta=0.05)
        self.assertEqual(len(result.info.source_points), 1)
        self.assertEqual(len(result.info.target_points), 1)
        self.assertEqual(result.info.source_points[0].label, "ray")

        self.assertEqual(result.info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_blocked_by_context(self):
        # A context box stands between the two objects: no direct
        # view, no verdict.
        results = self._compute(10.0, ["ContextA"])
        self.assertEqual(results, [])

    def test_max_ray_length_too_short(self):
        # The centers are 4 m apart: a 3 m ray reaches nothing.
        results = self._compute(3.0, [])
        self.assertEqual(results, [])

    def test_compute_is_pure_of_management_and_display(self):
        rule = Ray_Check(None, None, None, 10.0)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = self._compute(10.0, [])

        self.assertEqual(len(results), 1)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)


class TestComputeOBB_Custom(unittest.TestCase):
    """The compute contract of OBB_Custom on the cube model."""

    @classmethod
    def setUpClass(cls):
        # ifcopenshell 0.9: an entity does not keep its file alive.
        cls.file = ifcopenshell.open(os.path.join(MODEL_DIR, "CubeA_Above_CubeB_1m.ifc"))

    def _element(self, name):
        matches = [e for e in self.file.by_type("IfcProduct") if e.Name == name]
        self.assertTrue(matches, f"no element named {name!r}")
        return matches[0]

    def _compute(self, modifications):
        rule = OBB_Custom(None, None, modifications)
        return rule.compute(
            [self._element("CubeB")], [self._element("CubeA")], modifications
        )

    def test_band_above_source_detected(self):
        # The zone detached 1.0 above CubeB catches CubeA (the
        # OBB_Above case, built by a modification string).
        results = self._compute(["detach_top_by_extrude:1.0"])
        self.assertEqual(len(results), 1)
        info = results[0].info

        self.assertIsNotNone(info.distance)
        self.assertLessEqual(info.distance, 1e-6)

        # The touched zone, the source object and the target object.
        source_labels = {obb.label for obb in info.source_obbs}
        target_labels = {obb.label for obb in info.target_obbs}
        self.assertEqual(source_labels, {"object", "zone"})
        self.assertEqual(target_labels, {"object"})

        self.assertEqual(info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_empty_modifications_leave_the_base_obb(self):
        # Without a modification, the only zone is the source OBB
        # itself: CubeA, 1 m above, does not touch it.
        results = self._compute([])
        self.assertEqual(results, [])

    def test_two_zones_new_obb(self):
        # Two zones: the band above the source, then NEW_OBB closes
        # it and the base OBB becomes the second zone.
        results = self._compute(["detach_top_by_extrude:1.0", "NEW_OBB"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].source.Name, "CubeB")
        self.assertEqual(results[0].target.Name, "CubeA")

    def test_compute_is_pure_of_management_and_display(self):
        rule = OBB_Custom(None, None, ["detach_top_by_extrude:1.0"])
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = self._compute(["detach_top_by_extrude:1.0"])

        self.assertEqual(len(results), 1)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)

    def test_display_states_emit_all_zone_geometries(self):
        """Display_Input: EVERY detection zone of the source comes out
        and the result list does not (the engine is not run).
        Display_Result: every zone AND the results — NEW_OBB closes a
        zone, the base OBB becomes the second one: both are drawn."""
        sources = [self._element("CubeB")]
        targets = [self._element("CubeA")]

        for modifications, expected_zones in (
            (["detach_top_by_extrude:1.0"], 1),
            (["detach_top_by_extrude:1.0", "NEW_OBB"], 2),
        ):
            rule = OBB_Custom(None, None, modifications, state="Display_Input")
            results = rule.compute(sources, targets, modifications)
            self.assertEqual(results, [])
            self.assertEqual(len(rule.display_items), expected_zones)
            for item in rule.display_items:
                self.assertEqual(item.category, "obb")
                self.assertEqual(item.color, (0.5, 0, 1))
                self.assertAlmostEqual(item.transparency, 0.2)

            rule = OBB_Custom(None, None, modifications, state="Display_Result")
            results = rule.compute(sources, targets, modifications)
            self.assertEqual(len(results), 1)
            self.assertEqual(len(rule.display_items), expected_zones)


class TestComputeRaysAndCustomDispatch(unittest.TestCase):
    """The flat JSON declarations drive the computes through the
    registry dispatch — including the context list of Ray_Check."""

    @staticmethod
    def _select(name):
        from ifctester import ids
        from RuleClass import SelectFacet

        s = SelectFacet()
        s.applicability = [ids.Attribute(name="Name", value=name)]
        return s

    def test_engine_params(self):
        self.assertEqual(engine_params("Ray_Check"), ["max_ray_length"])
        self.assertEqual(engine_params("OBB_Custom"), ["list_of_modifications"])

    def test_declaration_drives_ray_check_with_context(self):
        import tempfile, shutil

        temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, temp_dir, True)
        model = os.path.join(temp_dir, "rays.ifc")
        make_model(
            model,
            [
                box("SourceA", 0.0, dx=0.5, dy=0.5, height=0.5),
                box("TargetA", 4.0, dx=0.5, dy=0.5, height=0.5),
            ],
        )
        file = ifcopenshell.open(model)
        elements = {e.Name: e for e in file.by_type("IfcProduct")}

        rule = Ray_Check(
            self._select("SourceA"), self._select("TargetA"), None, 10.0
        )
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        results = compute_from_config(
            config, [elements["SourceA"]], [elements["TargetA"]]
        )
        self.assertEqual(len(results), 1)

    def test_declaration_drives_obb_custom(self):
        file = ifcopenshell.open(os.path.join(MODEL_DIR, "CubeA_Above_CubeB_1m.ifc"))
        elements = {e.Name: e for e in file.by_type("IfcProduct")}

        rule = OBB_Custom(
            self._select("CubeB"), self._select("CubeA"), ["detach_top_by_extrude:1.0"]
        )
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        results = compute_from_config(config, [elements["CubeB"]], [elements["CubeA"]])
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
