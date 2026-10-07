"""Geometric test suite for the models in IFC_Test_Model/IFC_Model/.

Each model is named Source_Position_Target[_parameter].ifc: the relationship
described by the name must be confirmed (exactly 1 Source/Target result) or
denied (0 results) by the corresponding ifcclash_plus rule.

Organization: one test class per rule (see IFC_Test_Model/README.md).
The same model can be used by several classes: the "obvious" use is the one
encoded in its name, the other uses serve as counter-examples or document
borderline behavior (touching, coincidence, exact distance).

Object selection: by name (IFC `Name`) through an ifctester Attribute facet,
because the objects are mapped onto heterogeneous IFC entities (IFCFAN,
IFCENGINE, IFCSLAB, IFCCOIL, IFCCOLUMN...).

Call order for directional rules
--------------------------------
Above / Below / OBB_Above / OBB_Below / OBB_Front_And_Back build a detection
zone ANCHORED ON THE SOURCE and detect the TARGET inside that zone (see
doc/2ObjectsRules/OBB_Above.md: "detect objects that are above source objects").
The tests therefore call these rules in SEMANTIC order:

    CubeA_Above_CubeB_1m.ifc  (CubeA is above CubeB)
        -> Above(source=CubeB, target=CubeA, above_type="Above_MaxToMin", ...)

    above_type "Above_MaxToMin" = top face of the source vs bottom face of
    the target (target above the source); "Above_MinToMax" is the reverse.
    below_type "Below_MinToMax" = bottom face of the source vs top face of
    the target (target below the source).

Origin of the expected values
-----------------------------
[calibrated]  observed behavior: IFC_Test_Model/calibration.jsonl (previous
              session) or verification runs of the current session (symmetric
              rules: Intersection, Clearance, Collision, AngleBetween).
[expected]    expectation encoded from the documented semantics of the
              directional rules (semantic order). These tests were NOT run
              when this file was written; adjust them on the first run.

Rule bugs documented through @unittest.expectedFailure
------------------------------------------------------
1. Collision: the constructor parameter allow_touching is overwritten
   (Rules.py, `self.allow_touching = False`), touching is never detected.
2. Intersection: a 1mm penetration (CubeA_Intersect_CubeB_1mm) is not
   detected, while Collision detects it.
3. Collision/Intersection: two perfectly coincident solids
   (CubeA_SamePlace_CubeB) are detected by neither rule.

Rules documented but not implemented
------------------------------------
Inside (doc/2ObjectsRules/Inside) and SurfaceRecover (doc/2ObjectsRules/
SurfaceRecover.md) do not exist in ifcclash_plus/Rules.py: the corresponding
models are covered by the closest rules (Intersection, Collision, Clearance)
and the "obvious" tests are skipTest with a justification.

Execution (from the repository root, with the project conda environment,
see agent.md):
    python -m pytest tests/test_IFC_Test_Model.py -v
    python -m unittest tests.test_IFC_Test_Model -v
"""
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
        rule = rule_cls(self._select(src), self._select(tgt), **kwargs)
        rule_file.contains = [rule]
        rule_file.run()
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
        # BUG [calibrated]: the Collision constructor overwrites the
        # allow_touching argument (`self.allow_touching = False` in Rules.py);
        # strict contact is never detected. Observed behavior: 0.
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 1, allow_touching=True)

    def test_CubeA_TouchEdge_CubeB_allow_touching_false(self):
        # [calibrated]
        self._assert_count("CubeA_TouchEdge_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 0, allow_touching=False)

    @unittest.expectedFailure
    def test_CubeA_TouchEdge_CubeB_allow_touching_true(self):
        # BUG: see test_CubeA_TouchFace_CubeB_allow_touching_true.
        self._assert_count("CubeA_TouchEdge_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 1, allow_touching=True)

    def test_CubeA_TouchPoint_CubeB_allow_touching_false(self):
        # [calibrated]
        self._assert_count("CubeA_TouchPoint_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 0, allow_touching=False)

    @unittest.expectedFailure
    def test_CubeA_TouchPoint_CubeB_allow_touching_true(self):
        # BUG: see test_CubeA_TouchFace_CubeB_allow_touching_true.
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


class TestAbove(IFCModelRuleTestCase):
    """Above rule (face-based) in semantic order: the TARGET is above the SOURCE.

    [expected] tests not run when written: order and parameters derived from
    the documented semantics and the distances in calibration.jsonl.
    """

    def test_CubeA_Above_CubeB_1m(self):
        # CubeA (z 1.5-2.5) is above CubeB (z -0.5-0.5), gap 1.0m.
        # The tolerance must cover the face-to-face gap (1.0): 0.1 is too short.
        self._assert_count("CubeA_Above_CubeB_1m.ifc", Above,
                           "CubeB", "CubeA", 1,
                           above_type="Above_MaxToMin", tolerance=1.0)
        self._assert_count("CubeA_Above_CubeB_1m.ifc", Above,
                           "CubeB", "CubeA", 0,
                           above_type="Above_MaxToMin", tolerance=0.1)

    def test_CubeB_Above_45CuboidA(self):
        # min distance 0.2767; tolerance 1.0 to cover the diagonal gap of the 45deg cuboid.
        self._assert_count("CubeB_Above_45CuboidA.ifc", Above,
                           "45CuboidA", "CubeB", 1,
                           above_type="Above_MaxToMin", tolerance=1.0)

    def test_CubeB_Above_UshapeA(self):
        # UshapeA (z max 4.0), CubeB (z 4.5-5.5): gap 0.5m.
        self._assert_count("CubeB_Above_UshapeA.ifc", Above,
                           "UshapeA", "CubeB", 1,
                           above_type="Above_MaxToMin", tolerance=1.0)

    def test_CylinderA_Above_SlabA(self):
        # gap 0.5m.
        self._assert_count("CylinderA_Above_SlabA.ifc", Above,
                           "SlabA", "CylinderA", 1,
                           above_type="Above_MaxToMin", tolerance=1.0)
        self._assert_count("CylinderA_Above_SlabA.ifc", Above,
                           "SlabA", "CylinderA", 0,
                           above_type="Above_MaxToMin", tolerance=0.1)

    def test_SuzanneA_Above_SlabA(self):
        # min distance 1.0156: tolerance 1.1 needed, 1.0 insufficient.
        self._assert_count("SuzanneA_Above_SlabA.ifc", Above,
                           "SlabA", "SuzanneA", 1,
                           above_type="Above_MaxToMin", tolerance=1.1)
        self._assert_count("SuzanneA_Above_SlabA.ifc", Above,
                           "SlabA", "SuzanneA", 0,
                           above_type="Above_MaxToMin", tolerance=1.0)

    def test_SuzanneA_Above_UshapeA(self):
        # min distance 0.2156.
        self._assert_count("SuzanneA_Above_UshapeA.ifc", Above,
                           "UshapeA", "SuzanneA", 1,
                           above_type="Above_MaxToMin", tolerance=0.3)

    def test_SuzanneB_Above_SuzanneA(self):
        # min distance 0.2118.
        self._assert_count("SuzanneB_Above_SuzanneA.ifc", Above,
                           "SuzanneA", "SuzanneB", 1,
                           above_type="Above_MaxToMin", tolerance=0.3)

    def test_CubeB_NotAbove_UshapeA(self):
        # [expected] CubeB sits in the U opening, NOT above UshapeA: 0.
        # NB [calibrated, reverse order]: OBB_Above(CubeB, UshapeA, 0.1) = 1
        # (UshapeA does surround CubeB upward) - the "above" relation is true
        # in the other direction here, which the model name denies.
        self._assert_count("CubeB_NotAbove_UshapeA.ifc", Above,
                           "UshapeA", "CubeB", 0,
                           above_type="Above_MaxToMin", tolerance=0.1)

    def test_SuzanneA_NotAbove_UshapeA(self):
        # [expected] SuzanneA overlaps the U plate (distance 0.0156),
        # it is not above: 0.
        self._assert_count("SuzanneA_NotAbove_UshapeA.ifc", Above,
                           "UshapeA", "SuzanneA", 0,
                           above_type="Above_MaxToMin", tolerance=0.1)

    def test_SuzanneA_NotFullyAbove_SlabA(self):
        # [expected] "not fully above": the strict check top face of the
        # source / bottom face of the target must fail.
        self._assert_count("SuzanneA_NotFullyAbove_SlabA.ifc", Above,
                           "SlabA", "SuzanneA", 0,
                           above_type="Above_MaxToMin", tolerance=1.1)

    def test_CubeB_NorFrontNorAbove_45CuboidA(self):
        # [expected] neither in front nor above: 0 even with a wide tolerance.
        self._assert_count("CubeB_NorFrontNorAbove_45CuboidA.ifc", Above,
                           "45CuboidA", "CubeB", 0,
                           above_type="Above_MaxToMin", tolerance=2.0)


class TestBelow(IFCModelRuleTestCase):
    """Below rule (face-based) in semantic order: the TARGET is below the SOURCE.

    [expected] tests not run when written.
    """

    def test_CubeA_Below_CubeB_1m(self):
        # CubeA (z -0.5-0.5) is below CubeB (z 1.5-2.5), gap 1.0m.
        self._assert_count("CubeA_Below_CubeB_1m.ifc", Below,
                           "CubeB", "CubeA", 1,
                           below_type="Below_MinToMax", tolerance=1.0)
        self._assert_count("CubeA_Below_CubeB_1m.ifc", Below,
                           "CubeB", "CubeA", 0,
                           below_type="Below_MinToMax", tolerance=0.1)

    def test_CubeB_Below_45CuboidA(self):
        # min distance 0.5914; tolerance 1.0 to cover the gap.
        self._assert_count("CubeB_Below_45CuboidA.ifc", Below,
                           "45CuboidA", "CubeB", 1,
                           below_type="Below_MinToMax", tolerance=1.0)

    def test_SuzanneA_Below_SlabA(self):
        # min distance 0.9156: tolerance 1.0.
        self._assert_count("SuzanneA_Below_SlabA.ifc", Below,
                           "SlabA", "SuzanneA", 1,
                           below_type="Below_MinToMax", tolerance=1.0)

    def test_SuzanneA_NotFullyBelow_SlabA(self):
        # [expected] "not fully below": strict check -> 0.
        self._assert_count("SuzanneA_NotFullyBelow_SlabA.ifc", Below,
                           "SlabA", "SuzanneA", 0,
                           below_type="Below_MinToMax", tolerance=1.0)


class TestOBB_Above(IFCModelRuleTestCase):
    """OBB_Above rule in semantic order: extrusion zone ABOVE the source.

    [expected] unless stated otherwise, tests not run when written.
    """

    def test_CubeA_Above_CubeB_1m(self):
        # zone extruded by 1.0 above CubeB: CubeB top z=0.5 -> zone up to 1.5,
        # CubeA starts at z=1.5. Tolerance 1.0 to cover it, 0.1 too short.
        self._assert_count("CubeA_Above_CubeB_1m.ifc", OBB_Above,
                           "CubeB", "CubeA", 1, tolerance=1.0)
        self._assert_count("CubeA_Above_CubeB_1m.ifc", OBB_Above,
                           "CubeB", "CubeA", 0, tolerance=0.1)

    def test_CubeB_Above_45CuboidA(self):
        self._assert_count("CubeB_Above_45CuboidA.ifc", OBB_Above,
                           "45CuboidA", "CubeB", 1, tolerance=1.0)

    def test_CubeB_Above_UshapeA(self):
        self._assert_count("CubeB_Above_UshapeA.ifc", OBB_Above,
                           "UshapeA", "CubeB", 1, tolerance=1.0)

    def test_CylinderA_Above_SlabA(self):
        self._assert_count("CylinderA_Above_SlabA.ifc", OBB_Above,
                           "SlabA", "CylinderA", 1, tolerance=1.0)
        self._assert_count("CylinderA_Above_SlabA.ifc", OBB_Above,
                           "SlabA", "CylinderA", 0, tolerance=0.1)

    def test_SuzanneA_Above_SlabA(self):
        # min distance 1.0156.
        self._assert_count("SuzanneA_Above_SlabA.ifc", OBB_Above,
                           "SlabA", "SuzanneA", 1, tolerance=1.1)
        self._assert_count("SuzanneA_Above_SlabA.ifc", OBB_Above,
                           "SlabA", "SuzanneA", 0, tolerance=1.0)

    def test_SuzanneA_Above_UshapeA(self):
        # min distance 0.2156.
        self._assert_count("SuzanneA_Above_UshapeA.ifc", OBB_Above,
                           "UshapeA", "SuzanneA", 1, tolerance=0.3)

    def test_SuzanneB_Above_SuzanneA(self):
        # min distance 0.2118.
        self._assert_count("SuzanneB_Above_SuzanneA.ifc", OBB_Above,
                           "SuzanneA", "SuzanneB", 1, tolerance=0.3)

    def test_CubeB_NotAbove_UshapeA(self):
        # [expected] CubeB is not above UshapeA: 0 in semantic order.
        # NB [calibrated, reverse order]: OBB_Above(CubeB, UshapeA, 0.1) = 1,
        # because UshapeA is indeed "above" CubeB (the U surrounds it).
        self._assert_count("CubeB_NotAbove_UshapeA.ifc", OBB_Above,
                           "UshapeA", "CubeB", 0, tolerance=0.1)

    def test_SuzanneA_NotAbove_UshapeA(self):
        # [expected] same: 0 in semantic order.
        self._assert_count("SuzanneA_NotAbove_UshapeA.ifc", OBB_Above,
                           "UshapeA", "SuzanneA", 0, tolerance=0.1)

    def test_SuzanneA_NotFullyAbove_SlabA(self):
        # [expected] illustration of the OBB / face-based difference: the
        # OBB zone extruded above SlabA covers part of SuzanneA
        # (partial overlap), hence 1, while the strict Above check returns
        # 0 (see TestAbove.test_SuzanneA_NotFullyAbove_SlabA).
        self._assert_count("SuzanneA_NotFullyAbove_SlabA.ifc", OBB_Above,
                           "SlabA", "SuzanneA", 1, tolerance=1.1)

    def test_CubeB_NorFrontNorAbove_45CuboidA(self):
        # [expected] neither in front nor above: 0 even with a wide tolerance.
        self._assert_count("CubeB_NorFrontNorAbove_45CuboidA.ifc", OBB_Above,
                           "45CuboidA", "CubeB", 0, tolerance=2.0)


class TestOBB_Below(IFCModelRuleTestCase):
    """OBB_Below rule in semantic order: extrusion zone BELOW the source.

    [expected] tests not run when written.
    """

    def test_CubeA_Below_CubeB_1m(self):
        self._assert_count("CubeA_Below_CubeB_1m.ifc", OBB_Below,
                           "CubeB", "CubeA", 1, tolerance=1.0)
        self._assert_count("CubeA_Below_CubeB_1m.ifc", OBB_Below,
                           "CubeB", "CubeA", 0, tolerance=0.1)

    def test_CubeB_Below_45CuboidA(self):
        self._assert_count("CubeB_Below_45CuboidA.ifc", OBB_Below,
                           "45CuboidA", "CubeB", 1, tolerance=1.0)

    def test_SuzanneA_Below_SlabA(self):
        # min distance 0.9156.
        self._assert_count("SuzanneA_Below_SlabA.ifc", OBB_Below,
                           "SlabA", "SuzanneA", 1, tolerance=1.0)

    def test_SuzanneA_NotFullyBelow_SlabA(self):
        # [expected] mirror illustration of the partial OBB detection
        # (see TestOBB_Above.test_SuzanneA_NotFullyAbove_SlabA).
        self._assert_count("SuzanneA_NotFullyBelow_SlabA.ifc", OBB_Below,
                           "SlabA", "SuzanneA", 1, tolerance=1.0)


class TestOBB_Front_And_Back(IFCModelRuleTestCase):
    """OBB_Front_And_Back rule: zones extruded along the two main directions
    of the source OBB; the target must touch a zone.

    Markers: [calibrated] = observed count (file-name order, where it matches
    the semantic order or the rule is nearly symmetric); [expected] = not
    run when written.
    """

    def test_CubeB_InFront_45CuboidA(self):
        # [calibrated file-name order, tol 1.0: 1 for both Wide and Narrow]
        # CubeB is in front of 45CuboidA along its main axis -> semantic
        # order: source=45CuboidA, target=CubeB, same result expected.
        self._assert_count("CubeB_InFront_45CuboidA.ifc", OBB_Front_And_Back,
                           "45CuboidA", "CubeB", 1, tolerance=1.0, method="Wide")
        self._assert_count("CubeB_InFront_45CuboidA.ifc", OBB_Front_And_Back,
                           "45CuboidA", "CubeB", 0, tolerance=0.1, method="Wide")

    def test_CubeB_InFrontOf_CuboidA_50cm(self):
        # [calibrated file-name order: tol 1.0 -> 1, tol 0.5 -> 0]
        # semantic order: source=CuboidA (CubeB is in front of it).
        self._assert_count("CubeB_InFrontOf_CuboidA_50cm.ifc", OBB_Front_And_Back,
                           "CuboidA", "CubeB", 1, tolerance=1.0, method="Wide")
        self._assert_count("CubeB_InFrontOf_CuboidA_50cm.ifc", OBB_Front_And_Back,
                           "CuboidA", "CubeB", 0, tolerance=0.5, method="Wide")

    def test_SuzanneA_InFrontOf_CuboidA_150cm(self):
        # [expected] min distance 1.4601: tolerance 2.0 so that the zone
        # reaches SuzanneA. (File-name order calibrated: 0 up to tol 1.5.)
        self._assert_count("SuzanneA_InFrontOf_CuboidA_150cm.ifc", OBB_Front_And_Back,
                           "CuboidA", "SuzanneA", 1, tolerance=2.0, method="Wide")

    def test_SuzanneB_Behind_SuzanneA(self):
        # [calibrated] the file-name order IS the semantic order here:
        # SuzanneA is in front of SuzanneB. Wide -> 1 from tolerance 0.1;
        # Narrow -> 0.
        self._assert_count("SuzanneB_Behind_SuzanneA.ifc", OBB_Front_And_Back,
                           "SuzanneB", "SuzanneA", 1, tolerance=0.1, method="Wide")
        self._assert_count("SuzanneB_Behind_SuzanneA.ifc", OBB_Front_And_Back,
                           "SuzanneB", "SuzanneA", 0, tolerance=0.1, method="Narrow")

    def test_CubeB_Side_45CuboidA(self):
        # [calibrated file-name order: Wide tol 1.0 -> 1] a "sideways"
        # placement is still covered by the zone of the second main
        # direction of the OBB -> 1 in semantic order too.
        self._assert_count("CubeB_Side_45CuboidA.ifc", OBB_Front_And_Back,
                           "45CuboidA", "CubeB", 1, tolerance=1.0, method="Wide")

    def test_CubeB_Side_CuboidA_50cm(self):
        # [calibrated file-name order: 0 at every tested tolerance <= 1.0]
        # sideways placement outside the front/back zones of CuboidA -> 0.
        self._assert_count("CubeB_Side_CuboidA_50cm.ifc", OBB_Front_And_Back,
                           "CuboidA", "CubeB", 0, tolerance=1.0, method="Wide")

    def test_CubeB_NorFrontNorAbove_45CuboidA(self):
        # [calibrated file-name order: 0 for both Wide and Narrow] neither
        # in front nor behind.
        self._assert_count("CubeB_NorFrontNorAbove_45CuboidA.ifc", OBB_Front_And_Back,
                           "45CuboidA", "CubeB", 0, tolerance=1.0, method="Wide")
        self._assert_count("CubeB_NorFrontNorAbove_45CuboidA.ifc", OBB_Front_And_Back,
                           "45CuboidA", "CubeB", 0, tolerance=1.0, method="Narrow")


class TestAngleBetween(IFCModelRuleTestCase):
    """AngleBetween rule on the Orient / NoOrient models.

    Measured real angles (OBB main directions, Wide/Narrow method):
      - CuboidA_Orient_45Cuboid_45    : Wide-Narrow 45deg, Wide-Wide 135deg,
                                        Narrow-Wide 90deg, Narrow-Narrow 90deg;
      - CuboidA_NoOrient_45Cuboid     : Wide-Wide/Wide-Narrow 75.2deg,
                                        Narrow-Wide/Narrow-Narrow 131.2deg;
      - CuboidA_Orient_FallenCuboidA_90: Wide-Wide 90deg, Wide-Narrow 0deg,
                                        Narrow-Wide 0deg, Narrow-Narrow 90deg.
    """

    def test_CuboidA_Orient_FallenCuboidA_90(self):
        # [calibrated] nominal 90deg angle between Wide directions.
        self._assert_count("CuboidA_Orient_FallenCuboidA_90.ifc", AngleBetween,
                           "CuboidA", "FallenCuboidA", 1,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Wide",
                           angle_difference=90, angle_tolerance=5)
        # [calibrated] crossed directions: 0deg between Wide of CuboidA and Narrow of FallenCuboidA.
        self._assert_count("CuboidA_Orient_FallenCuboidA_90.ifc", AngleBetween,
                           "CuboidA", "FallenCuboidA", 1,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Narrow",
                           angle_difference=0, angle_tolerance=5)
        # [calibrated] counter-examples: neither 0deg nor 45deg between Wide-Wide directions.
        self._assert_count("CuboidA_Orient_FallenCuboidA_90.ifc", AngleBetween,
                           "CuboidA", "FallenCuboidA", 0,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Wide",
                           angle_difference=0, angle_tolerance=5)
        self._assert_count("CuboidA_Orient_FallenCuboidA_90.ifc", AngleBetween,
                           "CuboidA", "FallenCuboidA", 0,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Wide",
                           angle_difference=45, angle_tolerance=15)

    def test_CuboidA_Orient_45Cuboid_45(self):
        # [expected, measured angles] actual target: 45CuboidA (see NAME_OVERRIDES).
        # The nominal 45deg angle is between Wide of CuboidA and Narrow of 45CuboidA.
        self._assert_count("CuboidA_Orient_45Cuboid_45.ifc", AngleBetween,
                           "CuboidA", "45Cuboid", 1,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Narrow",
                           angle_difference=45, angle_tolerance=15)
        self._assert_count("CuboidA_Orient_45Cuboid_45.ifc", AngleBetween,
                           "CuboidA", "45Cuboid", 0,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Wide",
                           angle_difference=45, angle_tolerance=15)
        self._assert_count("CuboidA_Orient_45Cuboid_45.ifc", AngleBetween,
                           "CuboidA", "45Cuboid", 1,
                           direction_method_for_source="Narrow",
                           direction_method_for_target="Wide",
                           angle_difference=90, angle_tolerance=5)
        self._assert_count("CuboidA_Orient_45Cuboid_45.ifc", AngleBetween,
                           "CuboidA", "45Cuboid", 1,
                           direction_method_for_source="Narrow",
                           direction_method_for_target="Narrow",
                           angle_difference=90, angle_tolerance=5)

    def test_CuboidA_NoOrient_45Cuboid(self):
        # [expected, measured angles] no direction pair forms 0, 45 or
        # 90 degrees (75.2 / 131.2): all these searches fail.
        self._assert_count("CuboidA_NoOrient_45Cuboid.ifc", AngleBetween,
                           "CuboidA", "45Cuboid", 0,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Narrow",
                           angle_difference=45, angle_tolerance=5)
        self._assert_count("CuboidA_NoOrient_45Cuboid.ifc", AngleBetween,
                           "CuboidA", "45Cuboid", 0,
                           direction_method_for_source="Narrow",
                           direction_method_for_target="Wide",
                           angle_difference=45, angle_tolerance=5)
        self._assert_count("CuboidA_NoOrient_45Cuboid.ifc", AngleBetween,
                           "CuboidA", "45Cuboid", 0,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Narrow",
                           angle_difference=90, angle_tolerance=5)
        self._assert_count("CuboidA_NoOrient_45Cuboid.ifc", AngleBetween,
                           "CuboidA", "45Cuboid", 0,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Narrow",
                           angle_difference=0, angle_tolerance=5)


class TestUnimplementedRules(IFCModelRuleTestCase):
    """Rules documented but absent from ifcclash_plus/Rules.py."""

    def test_Inside_rule_not_implemented(self):
        # The CubeA_Inside_BigCubeA, CubeB_Inside_BigCubeA,
        # CubeA_InsideFaceTouch_BigCubeA and CubeA_TouchOutside_BigCubeA_1mm
        # models are covered through Intersection/Collision/Clearance (see
        # the classes above); the Inside rule only exists in doc/2ObjectsRules/Inside.
        self.skipTest(
            "Inside rule documented (doc/2ObjectsRules/Inside) but not "
            "implemented in ifcclash_plus/Rules.py."
        )

    def test_SurfaceRecover_not_implemented(self):
        # Models SlabA_RecoverTop_CuboidB_100%/50% and
        # SlabA_RecoverTop_CylinderA_100%/50%.
        self.skipTest(
            "SurfaceRecover rule documented (doc/2ObjectsRules/SurfaceRecover.md) "
            "but not implemented in ifcclash_plus/Rules.py."
        )


if __name__ == "__main__":
    unittest.main()
