# COPY of tests/test_Rule_IFC_Test_Model.py — the classes of the rules ported to C++
# (TestIntersection, TestCollision, TestClearance), generated on 2026-11-09 (SPEC_OptimisationInCPP).
#
# Same tests, same models, same expected values as the original, but every
# rule runs on the C++ engine: IFCCLASH_ENGINE=cpp forces the backend and
# forbids the silent fallback on Python (orchestrator.compute_rule). The
# original stays the reference of the Python engine; this copy is frozen on
# purpose, so that a change of the original cannot hide a regression of the
# port. Skipped when the C++ module is not built for the running Python.
#
# Execution (repository root, ifcclash_cpp environment, one file at a time):
#     PYTHONNOUSERSITE=1 python -m pytest tests/cpp_port/test_cpp_Rule_IFC_Test_Model.py -v
import os

os.environ["IFCCLASH_ENGINE"] = "cpp"

import pytest  # noqa: E402

import os
import sys
import unittest

sys.path.insert(0, "./ifcclash_plus")

from Rules import (  # noqa: E402
    Above,
    AngleBetween,
    Below,
    Clearance,
    Collision,
    Intersection,
    OBB_Above,
    OBB_Below,
    OBB_Front_And_Back,
)
from RuleClass import RuleFile, SelectFacet  # noqa: E402
from ifctester import ids  # noqa: E402
from tests.test_structure_ResultShape import assert_result_shape


MODEL_DIR = "IFC_Test_Model/IFC_Model"

# Some models carry a target name that does not exactly match the IFC `Name`
# of the intended object (hand-written files):
#   - "HollowCylinderA" is called "Hollow_CylinderA" in a single model;
#   - "45Cuboid" does not exist: the intended object (close to the source)
#     is "45CuboidA", "45CuboidB" being placed far away from all sources.
NAME_OVERRIDES = {
    "CubeA_NotTouch_HollowCylinderA.ifc": {"HollowCylinderA": "Hollow_CylinderA"},
    "CubeB_Intersect_45Cuboid.ifc": {"45Cuboid": "45CuboidA"},
    "CuboidA_NoOrient_45Cuboid.ifc": {"45Cuboid": "45CuboidA"},
    "CuboidA_Orient_45Cuboid_45.ifc": {"45Cuboid": "45CuboidA"},
}

from engine.backends import cpp_backend  # noqa: E402

pytestmark = pytest.mark.skipif(
    not cpp_backend.AVAILABLE, reason="the C++ module _ifcclash_engine is not built for this Python"
)


class IFCModelRuleTestCase(unittest.TestCase):
    """Common base: run a rule on a Source/Target pair from one model."""

    @staticmethod
    def _select(name):
        select = SelectFacet()
        select.applicability = [ids.Attribute(name="Name", value=name)]
        return select

    def _resolved(self, model, name):
        return NAME_OVERRIDES.get(model, {}).get(name, name)

    def _run_rule(self, model, rule_cls, source, target, **kwargs):
        """Build the rule on the (source, target) pair of the model and run it."""
        rule_file = RuleFile()
        rule_file.list_ifc_path = [os.path.join(MODEL_DIR, model)]
        src = self._resolved(model, source)
        tgt = self._resolved(model, target)
        #kwargs["state"]="Display_Result"
        rule = rule_cls(self._select(src), self._select(tgt), **kwargs)
        rule_file.contains = [rule]
        rule_file.run()
        assert_result_shape(rule_file)
        return rule, src, tgt

    def _assert_count(self, model, rule_cls, source, target, expected, **kwargs):
        """Run the rule and check the number of results (and the returned pair)."""
        rule, src, tgt = self._run_rule(model, rule_cls, source, target, **kwargs)
        self.assertEqual(
            len(rule.result),
            expected,
            msg=f"{model}: {rule_cls.__name__}{kwargs} -> "
            f"{len(rule.result)} result(s), {expected} expected",
        )
        if expected == 1:
            result = rule.result[0]
            self.assertEqual(result.source.Name, src)
            self.assertEqual(result.target.Name, tgt)


class TestIntersection(IFCModelRuleTestCase):
    """Intersection rule on the models (keywords: Intersect, Inside*, TouchOutside)."""

    def test_CubeA_Intersect_CubeB_10cm(self):
        # [calibrated] true volumetric intersection: detected at every tested tolerance.
        self._assert_count("CubeA_Intersect_CubeB_10cm.ifc", Intersection,
                           "CubeA", "CubeB", 1, tolerance=0.001)
        self._assert_count("CubeA_Intersect_CubeB_10cm.ifc", Intersection,
                           "CubeA", "CubeB", 1, tolerance=0.1)

    @unittest.expectedFailure
    def test_CubeA_Intersect_CubeB_1mm(self):
        # BUG [calibrated]: 1mm penetration not detected by Intersection (0
        # observed at tolerance 0.001 as well as 0.1) while Collision detects it.
        self._assert_count("CubeA_Intersect_CubeB_1mm.ifc", Intersection,
                           "CubeA", "CubeB", 1, tolerance=0.001)

    def test_CylinderA_Intersect_SlabA(self):
        # [calibrated]
        self._assert_count("CylinderA_Intersect_SlabA.ifc", Intersection,
                           "CylinderA", "SlabA", 1, tolerance=0.001)
        self._assert_count("CylinderA_Intersect_SlabA.ifc", Intersection,
                           "CylinderA", "SlabA", 1, tolerance=0.1)

    def test_CylinderA_Intersect_SlabA_Case2(self):
        # [calibrated]
        self._assert_count("CylinderA_Intersect_SlabA_Case2.ifc", Intersection,
                           "CylinderA", "SlabA", 1, tolerance=0.001)

    def test_CylinderA_Intersect_SlabA_Case3(self):
        # [calibrated]
        self._assert_count("CylinderA_Intersect_SlabA_Case3.ifc", Intersection,
                           "CylinderA", "SlabA", 1, tolerance=0.001)

    def test_SuzanneA_Intersect_UshapeA(self):
        # [calibrated]
        self._assert_count("SuzanneA_Intersect_UshapeA.ifc", Intersection,
                           "SuzanneA", "UshapeA", 1, tolerance=0.001)

    def test_SuzanneA_Intersect_HollowCylinderA(self):
        # [calibrated]
        self._assert_count("SuzanneA_Intersect_HollowCylinderA.ifc", Intersection,
                           "SuzanneA", "HollowCylinderA", 1, tolerance=0.001)

    def test_CubeB_Intersect_45Cuboid(self):
        # [calibrated] actual target: 45CuboidA (see NAME_OVERRIDES).
        self._assert_count("CubeB_Intersect_45Cuboid.ifc", Intersection,
                           "CubeB", "45Cuboid", 1, tolerance=0.001)
        self._assert_count("CubeB_Intersect_45Cuboid.ifc", Intersection,
                           "CubeB", "45Cuboid", 1, tolerance=0.1)

    def test_CubeA_Inside_BigCubeA(self):
        # [calibrated] Inside rule not implemented: the model illustrates the
        # behavior of Intersection on a full containment.
        self._assert_count("CubeA_Inside_BigCubeA.ifc", Intersection,
                           "CubeA", "BigCubeA", 1, tolerance=0.001)

    def test_CubeB_Inside_BigCubeA(self):
        # [calibrated]
        self._assert_count("CubeB_Inside_BigCubeA.ifc", Intersection,
                           "CubeB", "BigCubeA", 1, tolerance=0.001)

    def test_CubeA_InsideFaceTouch_BigCubeA(self):
        # [calibrated] containment with face contact: the intersection is detected.
        self._assert_count("CubeA_InsideFaceTouch_BigCubeA.ifc", Intersection,
                           "CubeA", "BigCubeA", 1, tolerance=0.001)

    def test_CubeA_TouchOutside_BigCubeA_1mm(self):
        # [calibrated] cube resting on the outer face of the big cube:
        # the contact is seen as an intersection.
        self._assert_count("CubeA_TouchOutside_BigCubeA_1mm.ifc", Intersection,
                           "CubeA", "BigCubeA", 1, tolerance=0.001)

    def test_CubeA_TouchFace_CubeB(self):
        # [calibrated] strict-contact behavior: two solids touching by a face
        # do NOT produce an Intersection result.
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Intersection,
                           "CubeA", "CubeB", 0, tolerance=0.001)
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Intersection,
                           "CubeA", "CubeB", 0, tolerance=0.1)

    def test_CubeA_SamePlace_CubeB(self):
        # [calibrated] perfect-coincidence behavior: two exactly overlapping
        # solids are NOT detected by Intersection.
        self._assert_count("CubeA_SamePlace_CubeB.ifc", Intersection,
                           "CubeA", "CubeB", 0, tolerance=1.0)


class TestCollision(IFCModelRuleTestCase):
    """Collision rule on the models (keywords: Collide, Intersect, NotCollide, Touch*)."""

    def test_CubeA_Intersect_CubeB_10cm(self):
        # [calibrated]
        self._assert_count("CubeA_Intersect_CubeB_10cm.ifc", Collision,
                           "CubeA", "CubeB", 1)

    def test_CubeA_Intersect_CubeB_1mm(self):
        # [calibrated] it is Collision (not Intersection) that sees the 1mm penetration.
        self._assert_count("CubeA_Intersect_CubeB_1mm.ifc", Collision,
                           "CubeA", "CubeB", 1)

    def test_CylinderA_Intersect_SlabA(self):
        # [calibrated]
        self._assert_count("CylinderA_Intersect_SlabA.ifc", Collision,
                           "CylinderA", "SlabA", 1)

    def test_CylinderA_Intersect_SlabA_Case2(self):
        # [calibrated]
        self._assert_count("CylinderA_Intersect_SlabA_Case2.ifc", Collision,
                           "CylinderA", "SlabA", 1)

    def test_CylinderA_Intersect_SlabA_Case3(self):
        # [calibrated]
        self._assert_count("CylinderA_Intersect_SlabA_Case3.ifc", Collision,
                           "CylinderA", "SlabA", 1)

    def test_SuzanneA_Intersect_UshapeA(self):
        # [calibrated]
        self._assert_count("SuzanneA_Intersect_UshapeA.ifc", Collision,
                           "SuzanneA", "UshapeA", 1)

    def test_SuzanneA_Intersect_HollowCylinderA(self):
        # [calibrated]
        self._assert_count("SuzanneA_Intersect_HollowCylinderA.ifc", Collision,
                           "SuzanneA", "HollowCylinderA", 1)

    def test_CubeB_Intersect_45Cuboid(self):
        # [calibrated]
        self._assert_count("CubeB_Intersect_45Cuboid.ifc", Collision,
                           "CubeB", "45Cuboid", 1)

    def test_SuzanneA_Collide_CuboidA_150cm(self):
        # [calibrated]
        self._assert_count("SuzanneA_Collide_CuboidA_150cm.ifc", Collision,
                           "SuzanneA", "CuboidA", 1)

    def test_SuzanneA_Collide_SuzanneB_n1(self):
        # [calibrated]
        self._assert_count("SuzanneA_Collide_SuzanneB_n1.ifc", Collision,
                           "SuzanneA", "SuzanneB", 1)

    def test_SuzanneA_Collide_SuzanneB_n2(self):
        # [calibrated]
        self._assert_count("SuzanneA_Collide_SuzanneB_n2.ifc", Collision,
                           "SuzanneA", "SuzanneB", 1)

    def test_SuzanneA_Collide_SuzanneB_n3(self):
        # [calibrated]
        self._assert_count("SuzanneA_Collide_SuzanneB_n3.ifc", Collision,
                           "SuzanneA", "SuzanneB", 1)

    def test_SuzanneA_NotCollide_SuzanneB(self):
        # [calibrated]
        self._assert_count("SuzanneA_NotCollide_SuzanneB.ifc", Collision,
                           "SuzanneA", "SuzanneB", 0)

    def test_SuzanneA_NotTouch_HollowCylinderA(self):
        # [calibrated]
        self._assert_count("SuzanneA_NotTouch_HollowCylinderA.ifc", Collision,
                           "SuzanneA", "HollowCylinderA", 0)

    def test_SuzanneA_NotTouch_HollowCylinderA_n2(self):
        # [calibrated]
        self._assert_count("SuzanneA_NotTouch_HollowCylinderA_n2.ifc", Collision,
                           "SuzanneA", "HollowCylinderA", 0)

    def test_CubeA_NotTouch_HollowCylinderA(self):
        # [calibrated] (IFC object "Hollow_CylinderA" in this model, see NAME_OVERRIDES)
        self._assert_count("CubeA_NotTouch_HollowCylinderA.ifc", Collision,
                           "CubeA", "HollowCylinderA", 0)

    def test_UshapeA_NoTouch_CubeB(self):
        # [calibrated]
        self._assert_count("UshapeA_NoTouch_CubeB.ifc", Collision,
                           "UshapeA", "CubeB", 0)

    def test_CubeA_TouchFace_CubeB_allow_touching_false(self):
        # [calibrated] without penetration (strict contact), Collision returns nothing.
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 0, allow_touching=False)

    @unittest.expectedFailure
    def test_CubeA_TouchFace_CubeB_allow_touching_true(self):
        # BUG [calibrated]: a face-to-face strict contact is still not
        # detected by the ifcopenshell 0.9 collision backend
        # (allow_touching=True, observed 0; edge and point contacts
        # are detected). Observed behavior: 0.
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 1, allow_touching=True)

    def test_CubeA_TouchEdge_CubeB_allow_touching_false(self):
        # [calibrated]
        self._assert_count("CubeA_TouchEdge_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 0, allow_touching=False)

    def test_CubeA_TouchEdge_CubeB_allow_touching_true(self):
        # ifcopenshell 0.9: see test_CubeA_TouchFace_CubeB_allow_touching_true.
        self._assert_count("CubeA_TouchEdge_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 1, allow_touching=True)

    def test_CubeA_TouchPoint_CubeB_allow_touching_false(self):
        # [calibrated]
        self._assert_count("CubeA_TouchPoint_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 0, allow_touching=False)

    def test_CubeA_TouchPoint_CubeB_allow_touching_true(self):
        # ifcopenshell 0.9: see test_CubeA_TouchFace_CubeB_allow_touching_true.
        self._assert_count("CubeA_TouchPoint_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 1, allow_touching=True)

    @unittest.expectedFailure
    def test_CubeA_SamePlace_CubeB(self):
        # BUG [calibrated]: two perfectly coincident solids are detected by
        # neither Collision nor Intersection (0 observed).
        # README mapping: SamePlace -> Collision, so 1 result expected.
        self._assert_count("CubeA_SamePlace_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 1)


class TestClearance(IFCModelRuleTestCase):
    """Clearance rule on the models (keywords: NextTo, Next, Diagonal, Touch*, NotTouch).

    Observed semantics [calibrated]: Clearance returns the pairs whose
    distance is STRICTLY smaller than the clearance parameter (clearance
    violation). A pair exactly at the `clearance` distance is not returned.
    """

    def test_CubeA_NextTo_CubeB_1m(self):
        # [calibrated] actual distance = 1.0m: exclusive boundary.
        self._assert_count("CubeA_NextTo_CubeB_1m.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=1.01)
        self._assert_count("CubeA_NextTo_CubeB_1m.ifc", Clearance,
                           "CubeA", "CubeB", 0, clearance=1.0)

    def test_CubeA_Diagonal_CubeB_1_41m(self):
        # [calibrated] actual distance = 1.4142m (diagonal).
        self._assert_count("CubeA_Diagonal_CubeB_1,41m.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=1.424)
        self._assert_count("CubeA_Diagonal_CubeB_1,41m.ifc", Clearance,
                           "CubeA", "CubeB", 0, clearance=1.396)

    def test_CubeA_TouchFace_CubeB(self):
        # [calibrated] zero distance at contact: any positive clearance detects it.
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=0.1)
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=0.001)

    def test_CubeA_TouchEdge_CubeB(self):
        # [calibrated]
        self._assert_count("CubeA_TouchEdge_CubeB.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=0.1)

    def test_CubeA_TouchPoint_CubeB(self):
        # [calibrated]
        self._assert_count("CubeA_TouchPoint_CubeB.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=0.1)

    def test_CubeA_TouchOutside_BigCubeA_1mm(self):
        # [calibrated] contact on the outer face: zero distance.
        self._assert_count("CubeA_TouchOutside_BigCubeA_1mm.ifc", Clearance,
                           "CubeA", "BigCubeA", 1, clearance=0.011)

    def test_CubeA_SamePlace_CubeB(self):
        # [calibrated] the only rule that "sees" two coincident solids.
        self._assert_count("CubeA_SamePlace_CubeB.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=0.001)

    def test_SuzanneA_Collide_CuboidA_150cm(self):
        # [calibrated] the pair collides (distance 0 < 1.5).
        self._assert_count("SuzanneA_Collide_CuboidA_150cm.ifc", Clearance,
                           "SuzanneA", "CuboidA", 1, clearance=1.5)

    def test_CubeB_Next_CuboidA_50cm(self):
        # [calibrated] actual distance ~1.03m: no violation of a 50cm clearance.
        self._assert_count("CubeB_Next_CuboidA_50cm.ifc", Clearance,
                           "CubeB", "CuboidA", 0, clearance=0.505)

    def test_CubeA_NotTouch_HollowCylinderA(self):
        # [calibrated] no contact (0 at clearance=0.001) but the pair is
        # close: actual distance < 10cm, hence 1 at clearance=0.1.
        self._assert_count("CubeA_NotTouch_HollowCylinderA.ifc", Clearance,
                           "CubeA", "HollowCylinderA", 0, clearance=0.001)
        self._assert_count("CubeA_NotTouch_HollowCylinderA.ifc", Clearance,
                           "CubeA", "HollowCylinderA", 1, clearance=0.1)

    def test_SuzanneA_NotTouch_HollowCylinderA_n2(self):
        # [calibrated] same profile as the previous model.
        self._assert_count("SuzanneA_NotTouch_HollowCylinderA_n2.ifc", Clearance,
                           "SuzanneA", "HollowCylinderA", 0, clearance=0.001)
        self._assert_count("SuzanneA_NotTouch_HollowCylinderA_n2.ifc", Clearance,
                           "SuzanneA", "HollowCylinderA", 1, clearance=0.1)

    def test_UshapeA_NoTouch_CubeB(self):
        # [calibrated] actual distance 0.5m: no violation of a 1mm clearance.
        self._assert_count("UshapeA_NoTouch_CubeB.ifc", Clearance,
                           "UshapeA", "CubeB", 0, clearance=0.001)


if __name__ == "__main__":
    import unittest

    unittest.main()
