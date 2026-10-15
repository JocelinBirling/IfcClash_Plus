"""The contract test sheet of the result data structure.

Every rule writes its result data through ResultInfo (the attributes,
the measure vocabulary and the NamedTuple blocks); this sheet checks
the contract itself:

- RESULT_SHAPE declares real types;
- a filled ResultInfo exports exactly the contract shape via to_dict();
- assert_result_shape(rule) checks every result of a rule against
  RESULT_SHAPE in subset comparison, and validate() reports no fault;
- the negative cases: an out-of-vocabulary attribute is invisible to
  the export, a non-numeric measure, a malformed point/face/OBB, an
  orphan pair number and a malformed rule-specific block are all
  reported by validate().

assert_result_shape is the helper called by every rule test after
rule_file.run() (one line per test).
"""
import sys
import os
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ifcclash_plus"))

from RuleClass import (
    RESULT_SHAPE,
    ResultInfo,
    PointEntry,
    FaceData,
    FaceEntry,
    ObbData,
    RaycastData,
    ZoneData,
)


# ==== The subset comparison of an exported dict against RESULT_SHAPE
def _leaf_fault(data, declared, path):
    """The fault of one leaf value against its declared type."""
    if declared is float:
        if isinstance(data, bool) or not isinstance(data, (int, float)):
            return [f"{path}: {type(data).__name__} != float"]
    elif declared is int:
        if isinstance(data, bool) or not isinstance(data, int):
            return [f"{path}: {type(data).__name__} != int"]
    elif declared is bool:
        if not isinstance(data, bool):
            return [f"{path}: {type(data).__name__} != bool"]
    elif declared is str:
        if not isinstance(data, str):
            return [f"{path}: {type(data).__name__} != str"]
    elif declared is tuple:
        if not isinstance(data, tuple):
            return [f"{path}: {type(data).__name__} != tuple"]
    elif declared is list:
        if not isinstance(data, list):
            return [f"{path}: {type(data).__name__} != list"]
    elif declared is dict:
        if not isinstance(data, dict):
            return [f"{path}: {type(data).__name__} != dict"]
    return []


def _subset_faults(data, shape, path="info"):
    """Every key written by data must exist in shape with the declared
    type; the blocks absent from data are normal (a rule fills what it
    measures). The measure block accepts any measure name of the
    vocabulary."""
    faults = []

    if path.split(".")[-1] == "measure":
        # The keys are measure names: any measure of the vocabulary,
        # each with its value.
        if not isinstance(data, dict):
            return [f"{path}: {type(data).__name__} != dict"]
        for name, entry in data.items():
            if name not in ResultInfo.MEASURE_ATTRIBUTES:
                faults.append(f"{path}.{name}: unknown measure")
                continue
            if not isinstance(entry, dict) or set(entry) != {"value"}:
                faults.append(f"{path}.{name}: {{'value': ...}} expected")
                continue
            faults.extend(_leaf_fault(entry["value"], float, f"{path}.{name}.value"))
        return faults

    if isinstance(shape, dict):
        if not isinstance(data, dict):
            return [f"{path}: {type(data).__name__} != dict"]
        for key, value in data.items():
            if key not in shape:
                faults.append(f"{path}.{key}: unknown key in RESULT_SHAPE")
                continue
            faults.extend(_subset_faults(value, shape[key], f"{path}.{key}"))
        return faults

    if isinstance(shape, list):
        if not isinstance(data, list):
            return [f"{path}: {type(data).__name__} != list"]
        for index, item in enumerate(data):
            faults.extend(_subset_faults(item, shape[0], f"{path}[{index}]"))
        return faults

    return _leaf_fault(data, shape, path)


def assert_result_shape(rule):
    """The contract check of every result of a rule: to_dict() compared
    to RESULT_SHAPE in subset (with the exact fault path), and
    validate() reporting no fault."""
    for index, result in enumerate(getattr(rule, "result", []) or []):
        info = getattr(result, "info", None)
        if info is None:
            raise AssertionError(f"result[{index}]: no info attached")
        faults = _subset_faults(info.to_dict(), RESULT_SHAPE, "info")
        if faults:
            raise AssertionError(f"result[{index}]: " + "; ".join(faults))
        validate_faults = info.validate()
        if validate_faults:
            raise AssertionError(
                f"result[{index}]: " + "; ".join(validate_faults)
            )


# ==== The tests
class TestResultShapeDeclaration(unittest.TestCase):
    def test_result_shape_declares_types(self):
        """Every leaf of RESULT_SHAPE must be a declared type."""
        def walk(value, path):
            if isinstance(value, dict):
                for key, item in value.items():
                    walk(item, f"{path}.{key}")
            elif isinstance(value, list):
                for index, item in enumerate(value):
                    walk(item, f"{path}[{index}]")
            else:
                self.assertIsInstance(value, type, f"{path}: {value!r}")

        walk(RESULT_SHAPE, "RESULT_SHAPE")


class TestResultInfoExport(unittest.TestCase):
    def test_filled_info_round_trip(self):
        """A ResultInfo filled with every block exports exactly the
        contract shape (subset comparison), with no validate fault."""
        info = ResultInfo()
        info.penetration_depth = 0.32  # m — nominale
        info.add_point_pair(
            (12.41, 3.02, 0.85), (12.41, 2.80, 0.85), label="entry"
        )
        info.add_point_pair(
            (12.41, 2.60, 0.85), (12.41, 2.44, 0.85), label="exit"
        )
        info.add_face_pair(
            (
                (0.0, -1.0, 0.0),
                0.0312,
                [((0.1, 2.71, 3.02), (0.34, 2.71, 3.02), (0.1, 2.71, 2.8))],
            ),
            (
                (0.0, 1.0, 0.0),
                0.0312,
                [((0.1, 2.70, 3.02), (0.34, 2.70, 3.02), (0.1, 2.70, 2.8))],
            ),
        )
        info.volume_intersection = 0.0012  # m3
        info.volume_ratio = 0.012
        info.containment_ratio = 0.85
        info.clearance_violated_volume = 0.0
        info.add_source_obb(
            (
                (4.0, 2.0, 0.95),
                ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                (0.5, 0.4, 0.425),
                "zone",
            )
        )
        info.add_target_obb(
            (
                (4.1, 2.05, 0.9),
                ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                (0.2, 0.15, 0.05),
                "object",
            )
        )
        info.axis_mode = "Perpendicular"
        info.axis_degraded = False
        info.raycast = RaycastData(
            planned=120,
            cast=118,
            hit=45,
            hit_segments=[((10.0, 2.0, 1.5), (14.0, 2.0, 1.5))],
            blocked_segments=[((10.0, 2.0, 1.5), (14.0, 2.0, 1.5))],
        )
        info.zone = ZoneData(
            side="Front",
            leaf="SingleSwingLeft",
            width=1.0,
            depth=0.9,
            height=2.1,
        )

        data = info.to_dict()
        self.assertEqual(info.primary_measure, "penetration_depth")
        self.assertEqual(
            list(data["measure"]),
            ["penetration_depth"],
        )
        self.assertTrue(info.has_volumes)
        faults = _subset_faults(data, RESULT_SHAPE, "info")
        self.assertEqual(faults, [])
        self.assertEqual(info.validate(), [])
        # The pairing of the points by number.
        self.assertEqual(
            [point["number"] for point in data["points"]],
            [1, 2],
        )
        self.assertEqual(data["points"][0]["label"], "entry")

    def test_empty_info_exports_nothing(self):
        self.assertEqual(ResultInfo().to_dict(), {})
        self.assertEqual(ResultInfo().validate(), [])
        self.assertIsNone(ResultInfo().primary_measure)
        self.assertFalse(ResultInfo().has_volumes)


class TestResultInfoMeasureOrder(unittest.TestCase):
    def test_first_posed_measure_is_nominal(self):
        info = ResultInfo()
        self.assertIsNone(info.primary_measure)
        info.angle = 88.6
        info.distance = 0.031
        self.assertEqual(info.primary_measure, "angle")
        self.assertEqual(info.measure("distance"), 0.031)
        self.assertIsNone(info.measure("ratio"))
        # A measure set back to None is no longer posed.
        info.angle = None
        self.assertEqual(info.primary_measure, "distance")

    def test_helpers_number_the_pairs(self):
        info = ResultInfo()
        number = info.add_point_pair((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
        self.assertEqual(number, 1)
        self.assertEqual(info.source_points, [PointEntry(1, (0.0, 0.0, 0.0), None)])
        self.assertEqual(number, info.source_points[0].number)
        number = info.add_face_pair(
            ((0.0, 0.0, 1.0), 1.0, []), ((0.0, 0.0, -1.0), 1.0, [])
        )
        self.assertEqual(number, 1)
        self.assertIsInstance(info.source_faces[0].face, FaceData)
        self.assertIsInstance(info.source_faces[0], FaceEntry)
        # A naked tuple appended directly remains structurally valid
        # (it is not an ObbData instance, but validate() accepts it
        # and to_dict() coerces it).
        naked_obb = (
            (0.0, 0.0, 0.0),
            ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
            (1.0, 1.0, 1.0),
            "object",
        )
        info.source_obbs.append(naked_obb)
        self.assertNotIsInstance(info.source_obbs[0], ObbData)
        self.assertEqual(info.validate(), [])
        self.assertEqual(
            info.to_dict()["obbs"]["source"][0]["center"],
            naked_obb[0],
        )


class TestResultInfoNegative(unittest.TestCase):
    def test_out_of_vocabulary_attribute_is_invisible(self):
        """info.chek is stored but neither tracked nor exported; the
        fault only shows if the rule test asserts its measures."""
        info = ResultInfo()
        info.chek = 1.0
        self.assertEqual(info.to_dict(), {})
        self.assertEqual(info.validate(), [])

    def test_non_numeric_measure_is_a_validate_fault(self):
        info = ResultInfo()
        info.ratio = "0.62"
        faults = info.validate()
        self.assertEqual(len(faults), 1)
        self.assertIn("ratio", faults[0])
        self.assertIn("str", faults[0])

    def test_malformed_point_is_a_validate_fault(self):
        info = ResultInfo()
        # A direct append of a non-3D point.
        info.source_points.append((1, (1.0, 2.0), None))
        info.target_points.append((1, (1.0, 2.0, 3.0), None))
        faults = info.validate()
        self.assertTrue(any("source_points[0].point" in fault for fault in faults))

    def test_orphan_pair_number_is_a_validate_fault(self):
        info = ResultInfo()
        info.add_point_pair((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))
        # A number posed on the source side only.
        info.source_points.append((2, (0.0, 1.0, 0.0), None))
        faults = info.validate()
        self.assertTrue(any("orphan" in fault for fault in faults))
        self.assertTrue(any("faces: orphan" not in fault for fault in faults))

    def test_orphan_face_number_is_a_validate_fault(self):
        info = ResultInfo()
        info.add_face_pair(((0.0, 0.0, 1.0), 1.0, []), ((0.0, 0.0, -1.0), 1.0, []))
        info.target_faces.append((2, FaceData((0.0, 1.0, 0.0), 1.0, [])))
        faults = info.validate()
        self.assertTrue(any("orphan" in fault for fault in faults))

    def test_malformed_obb_is_a_validate_fault(self):
        info = ResultInfo()
        info.add_source_obb(
            (
                (0.0, 1.0),  # center not 3D
                ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
                (0.5, -0.5, 0.5),  # negative half size
                "zone",
            )
        )
        faults = info.validate()
        self.assertTrue(any("center" in fault for fault in faults))
        self.assertTrue(any("negative" in fault for fault in faults))

    def test_malformed_raycast_is_a_validate_fault(self):
        info = ResultInfo()
        info.raycast = RaycastData(
            planned=120,
            cast="118",
            hit=45,
            hit_segments=[((10.0, 2.0, 1.5), (14.0, 2.0, 1.5))],
            blocked_segments=[],
        )
        faults = info.validate()
        self.assertTrue(any("raycast.cast" in fault for fault in faults))
        info.raycast = RaycastData(
            planned=120,
            cast=118,
            hit=45,
            hit_segments=[((10.0, 2.0, 1.5),)],
            blocked_segments=[],
        )
        faults = info.validate()
        self.assertTrue(
            any("raycast.hit_segments[0]" in fault for fault in faults)
        )

    def test_malformed_zone_is_a_validate_fault(self):
        info = ResultInfo()
        info.zone = ZoneData(
            side="Front",
            leaf="SingleSwingLeft",
            width="1.0",
            depth=0.9,
            height=2.1,
        )
        faults = info.validate()
        self.assertTrue(any("zone.width" in fault for fault in faults))
        info.zone = ZoneData(
            side="Front",
            leaf="SingleSwingLeft",
            width=1.0,
            depth=0.9,
            height=2.1,
        )
        self.assertEqual(info.validate(), [])

    def test_malformed_measure_block_fails_the_subset_check(self):
        """A measure entry with a wrong shape is caught by the subset
        comparison, not by validate()."""
        info = ResultInfo()
        info.distance = 0.42
        data = info.to_dict()
        data["measure"]["distance"] = {"value": "0.42"}
        faults = _subset_faults(data, RESULT_SHAPE, "info")
        self.assertTrue(
            any("measure.distance.value" in fault for fault in faults)
        )

    def test_unknown_export_key_fails_the_subset_check(self):
        data = {"unknown_block": 1.0}
        faults = _subset_faults(data, RESULT_SHAPE, "info")
        self.assertTrue(any("unknown_block" in fault for fault in faults))


if __name__ == "__main__":
    unittest.main()
