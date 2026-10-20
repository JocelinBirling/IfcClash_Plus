"""The compute contract of SurfaceRecover (SPEC Separation moteur/
gestion), tested directly — lists of entities and named parameters in,
raw results out.

The models come from IFC_Test_Model/IFC_Model: the SlabA_RecoverTop_*
models hold a slab hovering 0.9 m above its support (hence the
tolerance of 1.0 m in the tests), CubeA_TouchFace / CubeA_NextTo cover
the lateral contact and the out-of-contact cases.

The covering bounds reach the compute in their parsed form — the very
form carried by the instance and by the serialized declaration:
(("absolute"|"relative"), value) pairs or None.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_compute_SurfaceRecover.py -v
"""
import json
import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell

from Rules import SurfaceRecover
from RuleClass import SelectFacet, RuleFile, ClashResultTwoObjects
from registry import compute_from_config, engine_params
from serialization import serialize_rule_check
from tests.test_structure_ResultShape import assert_result_shape

MODEL_DIR = "IFC_Test_Model/IFC_Model"


def select_by_name(name):
    from ifctester import ids

    select = SelectFacet()
    select.applicability = [ids.Attribute(name="Name", value=name)]
    return select


class TestComputeSurfaceRecover(unittest.TestCase):
    """The compute contract of SurfaceRecover: two lists + the named
    parameters (the parsed covering bounds included)."""

    @classmethod
    def setUpClass(cls):
        # ifcopenshell 0.9: an entity does not keep its file alive —
        # the opened files are cached next to their entities.
        cls.files = {
            model: ifcopenshell.open(os.path.join(MODEL_DIR, model))
            for model in (
                "SlabA_RecoverTop_CuboidB_100%.ifc",
                "SlabA_RecoverTop_CuboidB_50%.ifc",
                "CubeA_TouchFace_CubeB.ifc",
                "CubeA_NextTo_CubeB_1m.ifc",
            )
        }

    @classmethod
    def tearDownClass(cls):
        cls.files.clear()

    def _element(self, model, name):
        matches = [e for e in self.files[model].by_type("IfcProduct") if e.Name == name]
        self.assertTrue(matches, f"no element named {name!r} in {model}")
        return matches[0]

    def _compute(self, model, source, target, **parameters):
        rule = SurfaceRecover(None, None)
        return rule.compute(
            [self._element(model, source)],
            [self._element(model, target)],
            parameters.get("direction", "Bottom"),
            parameters.get("reference", "Target"),
            parameters.get("tolerance", 1.0),
            min_covering=parameters.get("min_covering"),
            max_covering=parameters.get("max_covering"),
        )

    def test_min_covering_relative_clashes(self):
        """The slab covers 100% of the cuboid top: a minimum above 100%
        raises a clash carrying the pair data."""
        results = self._compute(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "CuboidB",
            min_covering=("relative", 101.0),
        )
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertTrue(result.status)
        self.assertEqual(result.source.Name, "SlabA")
        self.assertEqual(result.target.Name, "CuboidB")

        info = result.info
        # Contact = the whole 2 x 1 m cuboid top, 100% of the reference.
        self.assertAlmostEqual(info.contact_area, 2.0, places=3)
        self.assertAlmostEqual(info.ratio, 1.0, places=3)
        # The faces used: source bottom face vs target top face.
        self.assertAlmostEqual(info.source_faces[0].face.area, 9.0, places=3)
        self.assertAlmostEqual(info.target_faces[0].face.area, 2.0, places=3)
        self.assertAlmostEqual(info.distance, 0.9, places=3)
        # The contact triangles: the display data of the old registry.
        self.assertTrue(info.source_faces[0].face.triangles)

        self.assertEqual(info.validate(), [])
        assert_result_shape(SimpleNamespace(result=results))

    def test_full_coverage_compliant_no_clash(self):
        results = self._compute(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "CuboidB",
            min_covering=("relative", 95.0),
        )
        self.assertEqual(results, [])

    def test_half_coverage_clashes_and_passes(self):
        """The slab covers 50% of the cuboid top: 50% < 70% clashes,
        50% >= 40% passes."""
        model = "SlabA_RecoverTop_CuboidB_50%.ifc"
        results = self._compute(
            model, "SlabA", "CuboidB", min_covering=("relative", 70.0)
        )
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].info.contact_area, 1.0, places=3)
        self.assertAlmostEqual(results[0].info.ratio, 0.5, places=3)

        results = self._compute(
            model, "SlabA", "CuboidB", min_covering=("relative", 40.0)
        )
        self.assertEqual(results, [])

    def test_absolute_bound_in_m2(self):
        """An absolute minimum is an area in m2, the reference is
        ignored."""
        model = "SlabA_RecoverTop_CuboidB_100%.ifc"
        results = self._compute(
            model, "SlabA", "CuboidB", min_covering=("absolute", 1.5)
        )
        self.assertEqual(results, [])
        results = self._compute(
            model, "SlabA", "CuboidB", min_covering=("absolute", 2.5)
        )
        self.assertEqual(len(results), 1)

    def test_max_covering_above_clashes(self):
        """A maximum below the covering raises a clash."""
        model = "SlabA_RecoverTop_CuboidB_100%.ifc"
        results = self._compute(
            model, "SlabA", "CuboidB", max_covering=("relative", 95.0)
        )
        self.assertEqual(len(results), 1)
        results = self._compute(
            model, "SlabA", "CuboidB", max_covering=("relative", 101.0)
        )
        self.assertEqual(results, [])

    def test_reference_source_changes_denominator(self):
        """Reference = Source: the ratio is relative to the 9 m2 slab
        bottom, so the same full coverage is only ~22%."""
        model = "SlabA_RecoverTop_CuboidB_100%.ifc"
        results = self._compute(
            model,
            "SlabA",
            "CuboidB",
            reference="Source",
            min_covering=("relative", 30.0),
        )
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].info.ratio, 2.0 / 9.0, places=2)

    def test_no_bounds_never_clashes(self):
        """Without any bound, nothing is checked, no clash."""
        results = self._compute(
            "SlabA_RecoverTop_CuboidB_100%.ifc", "SlabA", "CuboidB"
        )
        self.assertEqual(results, [])

    def test_pair_not_in_contact_no_result(self):
        """Two cubes 1 m apart: no contact, no result even with an
        impossible minimum."""
        results = self._compute(
            "CubeA_NextTo_CubeB_1m.ifc",
            "CubeA",
            "CubeB",
            direction="Bottom",
            tolerance=0.001,
            min_covering=("relative", 150.0),
        )
        self.assertEqual(results, [])

    def test_lateral_auto_contact(self):
        """Two cubes touching on their side faces, direction Auto: the
        contact is 1 m2 (the whole touching face)."""
        results = self._compute(
            "CubeA_TouchFace_CubeB.ifc",
            "CubeA",
            "CubeB",
            direction="Auto",
            tolerance=0.01,
            min_covering=("absolute", 1.5),
        )
        self.assertEqual(len(results), 1)
        result = results[0]
        self.assertAlmostEqual(result.info.contact_area, 1.0, places=3)
        self.assertAlmostEqual(result.info.ratio, 1.0, places=3)

        results = self._compute(
            "CubeA_TouchFace_CubeB.ifc",
            "CubeA",
            "CubeB",
            direction="Auto",
            tolerance=0.01,
            min_covering=("absolute", 0.9),
        )
        self.assertEqual(results, [])

    def test_compute_is_pure_of_management_and_display(self):
        rule = SurfaceRecover(None, None)
        rule.result.append("sentinel")
        rule.display_items.append("sentinel")

        results = self._compute(
            "SlabA_RecoverTop_CuboidB_100%.ifc",
            "SlabA",
            "CuboidB",
            min_covering=("relative", 101.0),
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(rule.result, ["sentinel"])
        self.assertEqual(rule.display_items, ["sentinel"])
        self.assertIsNone(rule.output)

    def test_element_without_geometry_is_skipped(self):
        rule = SurfaceRecover(None, None)
        storey = self.files["SlabA_RecoverTop_CuboidB_100%.ifc"].by_type(
            "IfcBuildingStorey"
        )[0]
        results = rule.compute(
            [storey],
            [self._element("SlabA_RecoverTop_CuboidB_100%.ifc", "CuboidB")],
            "Bottom",
            "Target",
            1.0,
            min_covering=("relative", 101.0),
        )
        self.assertEqual(results, [])


class TestComputeSurfaceRecoverDispatch(unittest.TestCase):
    """The flat JSON declarations drive the compute through the
    registry dispatch."""

    def test_engine_params(self):
        self.assertEqual(
            engine_params("SurfaceRecover"),
            ["direction", "reference", "tolerance", "min_covering", "max_covering"],
        )

    def test_declaration_drives_the_compute(self):
        file = ifcopenshell.open(
            os.path.join(MODEL_DIR, "SlabA_RecoverTop_CuboidB_100%.ifc")
        )
        elements = {e.Name: e for e in file.by_type("IfcProduct")}

        rule = SurfaceRecover(
            select_by_name("SlabA"),
            select_by_name("CuboidB"),
            direction="Bottom",
            reference="Target",
            tolerance=1.0,
            min_covering="101%",
        )
        config = json.loads(json.dumps(serialize_rule_check(rule)))

        # The serialized declaration carries the parsed bound pair.
        self.assertEqual(config["min_covering"], ["relative", 101.0])

        results = compute_from_config(
            config, [elements["SlabA"]], [elements["CuboidB"]]
        )
        self.assertEqual(len(results), 1)
        self.assertAlmostEqual(results[0].info.ratio, 1.0, places=3)


class TestComputeSurfaceRecoverThroughAdapter(unittest.TestCase):
    """The migration adapter (run + RuleFile) produces the RuleOutput
    of the pipeline (SPEC): one integration node."""

    def test_rule_output_after_rule_file_run(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [
            os.path.join(MODEL_DIR, "SlabA_RecoverTop_CuboidB_100%.ifc")
        ]
        rule = SurfaceRecover(
            select_by_name("SlabA"),
            select_by_name("CuboidB"),
            direction="Bottom",
            reference="Target",
            tolerance=1.0,
            min_covering="101%",
        )
        rule_file.contains = [rule]
        rule_file.run()

        assert_result_shape(rule_file)
        self.assertEqual(len(rule.result), 1)
        self.assertIsNotNone(rule.output)
        self.assertIs(rule.output.results, rule.result)


if __name__ == "__main__":
    unittest.main()
