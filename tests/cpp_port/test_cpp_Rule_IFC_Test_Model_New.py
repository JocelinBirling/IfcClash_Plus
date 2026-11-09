# COPY of tests/test_Rule_IFC_Test_Model_New.py — the classes of the rules ported to C++
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
#     PYTHONNOUSERSITE=1 python -m pytest tests/cpp_port/test_cpp_Rule_IFC_Test_Model_New.py -v
import os

os.environ["IFCCLASH_ENGINE"] = "cpp"

import pytest  # noqa: E402

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ifcclash_plus"))

from Rules import (  # noqa: E402
    Above,
    AngleBetween,
    Below,
    Clearance,
    Collision,
    Intersection,
    Intersection2,
    OBB_Above,
    OBB_Below,
    OBB_Front_And_Back,
)
from tests.cpp_port.test_cpp_Rule_IFC_Test_Model import IFCModelRuleTestCase  # noqa: E402

ABOVE = dict(above_type="Above_MaxToMin")
BELOW = dict(below_type="Below_MinToMax")


# ---------------------------------------------------------------------------
# Intersection (BVH tree) vs Intersection2 (BREP pur) : les divergences
# entre les deux moteurs sont documentees par ces tests.
# ---------------------------------------------------------------------------

from engine.backends import cpp_backend  # noqa: E402

pytestmark = pytest.mark.skipif(
    not cpp_backend.AVAILABLE, reason="the C++ module _ifcclash_engine is not built for this Python"
)


class TestIntersection(IFCModelRuleTestCase):
    def test_overlap_volumique(self):
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", Intersection,
                           "SlabA", "SlabB", 1, tolerance=0.001)
        self._assert_count("CubeA_PartialIntersect_UshapeA.ifc", Intersection,
                           "CubeA", "UshapeA", 1, tolerance=0.001)
        self._assert_count("CylinderA_Inside_BigCubeA.ifc", Intersection,
                           "CylinderA", "BigCubeA", 1, tolerance=0.001)

    def test_pas_d_intersection(self):
        self._assert_count("SlabA_ZOverlapNoXY_SlabB.ifc", Intersection,
                           "SlabA", "SlabB", 0, tolerance=0.001)
        # chevauchement coplanaire : le BVH ne voit pas de volume commun
        self._assert_count("SlabA_SameZ_OverlapXY_SlabB.ifc", Intersection,
                           "SlabA", "SlabB", 0, tolerance=0.001)
        self._assert_count("CubeB_InU_Crevasse_UshapeA.ifc", Intersection,
                           "CubeB", "UshapeA", 0, tolerance=0.001)
        self._assert_count("CubeA_Diagonal3D_CubeB_1,73m.ifc", Intersection,
                           "CubeA", "CubeB", 0, tolerance=0.001)
        self._assert_count("CubeA_Far_CubeB_10m.ifc", Intersection,
                           "CubeA", "CubeB", 0, tolerance=0.001)
        self._assert_count("CubeA_NextTo_CubeB_0,1mm.ifc", Intersection,
                           "CubeA", "CubeB", 0, tolerance=0.001)
        self._assert_count("45CuboidA_DiagClose_CubeB_37cm.ifc", Intersection,
                           "45CuboidA", "CubeB", 0, tolerance=0.001)
        self._assert_count("CylinderA_TouchOutside_HollowCylinderA.ifc",
                           Intersection, "CylinderA", "HollowCylinderA",
                           0, tolerance=0.001)
        self._assert_count("CylinderSmallA_Clearance_HollowCylinderA_1cm.ifc",
                           Intersection, "CylinderSmallA", "HollowCylinderA",
                           0, tolerance=0.001)

    def test_formes_courbes_manquees_par_le_bvh(self):
        # sphère dans dalle (~10cm) : Intersection=0 a toute tolerance
        self._assert_count("SphereA_Intersect_SlabA.ifc", Intersection,
                           "SphereA", "SlabA", 0, tolerance=0.001)
        self._assert_count("SphereA_Intersect_SlabA.ifc", Intersection,
                           "SphereA", "SlabA", 0, tolerance=1.0)
        # contacts tangentiels courbes
        self._assert_count("SphereA_TangentTop_SlabA.ifc", Intersection,
                           "SphereA", "SlabA", 0, tolerance=0.001)
        self._assert_count("SphereA_Tangent_SphereB.ifc", Intersection,
                           "SphereA", "SphereB", 0, tolerance=0.001)
        # cube dans le trou du tore
        self._assert_count("CubeA_InHole_TorusA.ifc", Intersection,
                           "CubeA", "TorusA", 0, tolerance=0.001)
        # pointe de cone dans le cube (5cm)
        self._assert_count("ConeA_PointIn_CubeB.ifc", Intersection,
                           "ConeA", "CubeB", 0, tolerance=0.001)
        # plaque de 1mm dans le cube
        self._assert_count("PlateThinA_Through_CubeB_1mm.ifc", Intersection,
                           "PlateThinA", "CubeB", 0, tolerance=0.001)
        self._assert_count("PlateThinA_Through_CubeB_1mm.ifc", Intersection,
                           "PlateThinA", "CubeB", 0, tolerance=0.1)
        # pas d'intersection verticale non plus
        self._assert_count("SphereA_Above_SlabA.ifc", Intersection,
                           "SphereA", "SlabA", 0, tolerance=0.001)
        self._assert_count("BeamLongA_Above_CubeA.ifc", Intersection,
                           "CubeA", "BeamLongA", 0, tolerance=0.001)
        self._assert_count("ConeA_Above_SlabA.ifc", Intersection,
                           "ConeA", "SlabA", 0, tolerance=0.001)

    def test_cylindre_vrai_1mm_detecte(self):
        # vrai cylindre IfcCircleProfileDef : le BVH voit la penetration 1mm
        # (contrairement au cube-cube 1mm de la suite originale)
        self._assert_count("CylinderTrueA_Intersect_CubeA_1mm.ifc",
                           Intersection, "CylinderTrueA", "CubeA",
                           1, tolerance=0.001)


class TestCollision(IFCModelRuleTestCase):
    def test_collisions(self):
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", Collision,
                           "SlabA", "SlabB", 1)
        self._assert_count("CubeA_PartialIntersect_UshapeA.ifc", Collision,
                           "CubeA", "UshapeA", 1)
        self._assert_count("SphereA_Intersect_SlabA.ifc", Collision,
                           "SphereA", "SlabA", 1)
        self._assert_count("ConeA_PointIn_CubeB.ifc", Collision,
                           "ConeA", "CubeB", 1)
        self._assert_count("PlateThinA_Through_CubeB_1mm.ifc", Collision,
                           "PlateThinA", "CubeB", 1)
        self._assert_count("CylinderTrueA_Intersect_CubeA_1mm.ifc", Collision,
                           "CylinderTrueA", "CubeA", 1)

    def test_pas_de_collision(self):
        # coplanaire = pas de volume commun pour Collision non plus
        self._assert_count("SlabA_SameZ_OverlapXY_SlabB.ifc", Collision,
                           "SlabA", "SlabB", 0)
        self._assert_count("CubeB_InU_Crevasse_UshapeA.ifc", Collision,
                           "CubeB", "UshapeA", 0)
        self._assert_count("CubeA_InHole_TorusA.ifc", Collision,
                           "CubeA", "TorusA", 0)
        self._assert_count("CylinderA_Inside_BigCubeA.ifc", Collision,
                           "CylinderA", "BigCubeA", 0)
        self._assert_count("CubeA_NextTo_CubeB_0,1mm.ifc", Collision,
                           "CubeA", "CubeB", 0)
        self._assert_count("BeamLongA_Clearance_CubeA_1cm.ifc", Collision,
                           "CubeA", "BeamLongA", 0)
        self._assert_count("CylinderSmallA_Clearance_HollowCylinderA_1cm.ifc",
                           Collision, "CylinderSmallA", "HollowCylinderA", 0)
        self._assert_count("SphereA_TangentTop_SlabA.ifc", Collision,
                           "SphereA", "SlabA", 0)
        self._assert_count("SphereA_Tangent_SphereB.ifc", Collision,
                           "SphereA", "SphereB", 0)
        self._assert_count("CylinderA_TouchOutside_HollowCylinderA.ifc",
                           Collision, "CylinderA", "HollowCylinderA", 0)

    def test_allow_touching(self):
        # contact courbe exterieur cylindre/cylindre creux : detecte
        self._assert_count("CylinderA_TouchOutside_HollowCylinderA.ifc",
                           Collision, "CylinderA", "HollowCylinderA",
                           1, allow_touching=True)
        # contact ponctuel sphere/dalle : detecte
        self._assert_count("SphereA_TangentTop_SlabA.ifc", Collision,
                           "SphereA", "SlabA", 1, allow_touching=True)
        # contact ponctuel sphere/sphere courbe-sur-courbe : PAS detecte
        self._assert_count("SphereA_Tangent_SphereB.ifc", Collision,
                           "SphereA", "SphereB", 0, allow_touching=True)


# ---------------------------------------------------------------------------
# Clearance (distance strictement entre 0 et clearance ; les paires qui
# s'intersectent en volume ne sont PAS flaggees)
# ---------------------------------------------------------------------------


class TestClearance(IFCModelRuleTestCase):
    def test_distances(self):
        self._assert_count("CubeA_Diagonal3D_CubeB_1,73m.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=1.74)
        self._assert_count("CubeA_Diagonal3D_CubeB_1,73m.ifc", Clearance,
                           "CubeA", "CubeB", 0, clearance=1.70)
        self._assert_count("CubeA_NextTo_CubeB_0,1mm.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=0.001)
        self._assert_count("CubeA_NextTo_CubeB_0,1mm.ifc", Clearance,
                           "CubeA", "CubeB", 0, clearance=0.00005)
        self._assert_count("CubeA_Far_CubeB_10m.ifc", Clearance,
                           "CubeA", "CubeB", 0, clearance=10.0)
        self._assert_count("CubeA_Far_CubeB_10m.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=10.01)
        self._assert_count("CubeA_NotBelow_CubeB_1m.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=1.01)
        self._assert_count("CubeA_NotBelow_CubeB_1m.ifc", Clearance,
                           "CubeA", "CubeB", 0, clearance=1.0)
        self._assert_count("SuzanneA_Side_CuboidA_NotFrontNotBehind.ifc",
                           Clearance, "CuboidA", "SuzanneA", 1, clearance=2.0)
        self._assert_count("45CuboidA_DiagClose_CubeB_37cm.ifc", Clearance,
                           "45CuboidA", "CubeB", 0, clearance=0.05)
        self._assert_count("45CuboidA_DiagClose_CubeB_37cm.ifc", Clearance,
                           "45CuboidA", "CubeB", 1, clearance=0.2)

    def test_contacts_tangentiels_distance_zero(self):
        self._assert_count("SlabA_SameZ_OverlapXY_SlabB.ifc", Clearance,
                           "SlabA", "SlabB", 1, clearance=0.001)
        self._assert_count("CylinderA_TouchOutside_HollowCylinderA.ifc",
                           Clearance, "CylinderA", "HollowCylinderA",
                           1, clearance=0.001)
        self._assert_count("SphereA_TangentTop_SlabA.ifc", Clearance,
                           "SphereA", "SlabA", 1, clearance=0.001)
        self._assert_count("SphereA_Tangent_SphereB.ifc", Clearance,
                           "SphereA", "SphereB", 1, clearance=0.001)
        self._assert_count("CubeA_PartialIntersect_UshapeA.ifc", Clearance,
                           "CubeA", "UshapeA", 1, clearance=0.001)
        self._assert_count("SphereA_NotAbove_SlabA.ifc", Clearance,
                           "SphereA", "SlabA", 1, clearance=0.001)
        self._assert_count("SphereA_Intersect_SlabA.ifc", Clearance,
                           "SphereA", "SlabA", 1, clearance=0.001)
        self._assert_count("ConeA_PointIn_CubeB.ifc", Clearance,
                           "ConeA", "CubeB", 1, clearance=0.001)

    def test_intersections_volumiques_non_flaggees(self):
        # paires avec volume commun : Clearance ne les flagge pas
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", Clearance,
                           "SlabA", "SlabB", 0, clearance=0.001)
        self._assert_count("CylinderA_Inside_BigCubeA.ifc", Clearance,
                           "CylinderA", "BigCubeA", 0, clearance=0.001)
        self._assert_count("PlateThinA_Through_CubeB_1mm.ifc", Clearance,
                           "PlateThinA", "CubeB", 0, clearance=0.001)
        self._assert_count("CubeB_InU_Crevasse_UshapeA.ifc", Clearance,
                           "CubeB", "UshapeA", 0, clearance=0.001)
        self._assert_count("CubeA_InHole_TorusA.ifc", Clearance,
                           "CubeA", "TorusA", 0, clearance=0.001)
        self._assert_count("SlabA_ZOverlapNoXY_SlabB.ifc", Clearance,
                           "SlabA", "SlabB", 0, clearance=3.0)

    def test_jeux(self):
        self._assert_count("CylinderSmallA_Clearance_HollowCylinderA_1cm.ifc",
                           Clearance, "CylinderSmallA", "HollowCylinderA",
                           1, clearance=0.02)
        self._assert_count("CylinderSmallA_Clearance_HollowCylinderA_1cm.ifc",
                           Clearance, "CylinderSmallA", "HollowCylinderA",
                           0, clearance=0.005)
        self._assert_count("CylinderTrueA_Intersect_CubeA_1mm.ifc",
                           Clearance, "CylinderTrueA", "CubeA",
                           1, clearance=0.001)
        self._assert_count("BeamLongA_Clearance_CubeA_1cm.ifc", Clearance,
                           "CubeA", "BeamLongA", 1, clearance=0.02)
        self._assert_count("BeamLongA_Clearance_CubeA_1cm.ifc", Clearance,
                           "CubeA", "BeamLongA", 0, clearance=0.005)
        self._assert_count("BeamLongA_Above_CubeA.ifc", Clearance,
                           "CubeA", "BeamLongA", 1, clearance=2.0)
        self._assert_count("BeamLongA_Above_CubeA.ifc", Clearance,
                           "CubeA", "BeamLongA", 0, clearance=1.4)
        self._assert_count("SphereA_Above_SlabA.ifc", Clearance,
                           "SlabA", "SphereA", 1, clearance=0.6)
        self._assert_count("SphereA_Above_SlabA.ifc", Clearance,
                           "SlabA", "SphereA", 0, clearance=0.4)
        self._assert_count("ConeA_Above_SlabA.ifc", Clearance,
                           "SlabA", "ConeA", 1, clearance=1.1)
        self._assert_count("ConeA_Above_SlabA.ifc", Clearance,
                           "SlabA", "ConeA", 0, clearance=0.9)
        self._assert_count("CubeA_Above_TorusA.ifc", Clearance,
                           "TorusA", "CubeA", 1, clearance=1.5)
        self._assert_count("CubeA_Above_TorusA.ifc", Clearance,
                           "TorusA", "CubeA", 0, clearance=1.0)


# ---------------------------------------------------------------------------
# Above / Below (face-based)
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    import unittest

    unittest.main()
