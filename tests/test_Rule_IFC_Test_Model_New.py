"""Tests des modèles IFC générés par IFC_Test_Model/generate_models.py.

31 modèles complémentaires dans IFC_Test_Model/IFC_Model/ : positionnements
manquants (ZOverlap, NotBelow, diagonale 3D, creux du U, source inclinée,
distances extrêmes, scène 3 objets, contact courbe) et nouvelles géométries
(sphère, tore, cône, poutre élancée, cylindres IfcCircleProfileDef, plaque
fine). Chaque modèle est testé par TOUTES les règles deux-objets pertinentes.

Toutes les valeurs sont [calibrated] : observées en lançant les règles sur les
modèles générés (session de génération, environnement conda de agent.md).

Exécution (racine du dépôt) :
    python -m pytest tests/test_Rule_IFC_Test_Model_New.py -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ifcclash_plus"))

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
from tests.test_Rule_IFC_Test_Model import IFCModelRuleTestCase  # noqa: E402

ABOVE = dict(above_type="Above_MaxToMin")
BELOW = dict(below_type="Below_MinToMax")


# ---------------------------------------------------------------------------
# Intersection (BVH tree) vs Intersection2 (BREP pur) : les divergences
# entre les deux moteurs sont documentees par ces tests.
# ---------------------------------------------------------------------------

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


class TestIntersection2(IFCModelRuleTestCase):
    """Moteur BREP pur (PythonOCC) : voit les volumes que le BVH manque."""

    def test_volumes_vus_par_le_brep(self):
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", Intersection2,
                           "SlabA", "SlabB", 1, tolerance=0.0)
        # chevauchement coplanaire : le BREP calcule un volume commun
        self._assert_count("SlabA_SameZ_OverlapXY_SlabB.ifc", Intersection2,
                           "SlabA", "SlabB", 1, tolerance=0.0)
        self._assert_count("CubeA_PartialIntersect_UshapeA.ifc", Intersection2,
                           "CubeA", "UshapeA", 1, tolerance=0.0)
        # sphère dans dalle : le BREP voit l'intersection courbe/plan
        self._assert_count("SphereA_Intersect_SlabA.ifc", Intersection2,
                           "SphereA", "SlabA", 1, tolerance=0.0)
        # pointe de cone dans le cube
        self._assert_count("ConeA_PointIn_CubeB.ifc", Intersection2,
                           "ConeA", "CubeB", 1, tolerance=0.0)
        # plaque de 1mm dans le cube
        self._assert_count("PlateThinA_Through_CubeB_1mm.ifc", Intersection2,
                           "PlateThinA", "CubeB", 1, tolerance=0.0)
        self._assert_count("CylinderA_Inside_BigCubeA.ifc", Intersection2,
                           "CylinderA", "BigCubeA", 1, tolerance=0.0)
        self._assert_count("CylinderTrueA_Intersect_CubeA_1mm.ifc",
                           Intersection2, "CylinderTrueA", "CubeA",
                           1, tolerance=0.0)

    def test_contacts_sans_volume_non_vus(self):
        self._assert_count("SphereA_TangentTop_SlabA.ifc", Intersection2,
                           "SphereA", "SlabA", 0, tolerance=0.0)
        self._assert_count("SphereA_Tangent_SphereB.ifc", Intersection2,
                           "SphereA", "SphereB", 0, tolerance=0.0)
        self._assert_count("CylinderA_TouchOutside_HollowCylinderA.ifc",
                           Intersection2, "CylinderA", "HollowCylinderA",
                           0, tolerance=0.0)

    def test_pas_d_intersection(self):
        self._assert_count("CubeA_NextTo_CubeB_0,1mm.ifc", Intersection2,
                           "CubeA", "CubeB", 0, tolerance=0.0)
        self._assert_count("45CuboidA_DiagClose_CubeB_37cm.ifc", Intersection2,
                           "45CuboidA", "CubeB", 0, tolerance=0.0)
        self._assert_count("CylinderSmallA_Clearance_HollowCylinderA_1cm.ifc",
                           Intersection2, "CylinderSmallA", "HollowCylinderA",
                           0, tolerance=0.0)

    def test_faux_positif_tore_maille(self):
        # le cube est geometriquement dans le trou du tore, mais le BREP
        # (mesh_to_solid sur faces loose) le voit comme intersectant
        self._assert_count("CubeA_InHole_TorusA.ifc", Intersection2,
                           "CubeA", "TorusA", 1, tolerance=0.0)


# ---------------------------------------------------------------------------
# Collision
# ---------------------------------------------------------------------------

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

class TestAboveBelow(IFCModelRuleTestCase):
    def test_z_overlap_ni_above_ni_below(self):
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", Above,
                           "SlabB", "SlabA", 0, **ABOVE, tolerance=0.1)
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", Above,
                           "SlabA", "SlabB", 0, **ABOVE, tolerance=0.1)
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", Below,
                           "SlabB", "SlabA", 0, **BELOW, tolerance=0.1)

    def test_not_below(self):
        self._assert_count("CubeA_NotBelow_CubeB_1m.ifc", Below,
                           "CubeB", "CubeA", 0, **BELOW, tolerance=1.0)
        self._assert_count("CubeA_NotBelow_CubeB_1m.ifc", Above,
                           "CubeB", "CubeA", 0, **ABOVE, tolerance=1.0)

    def test_source_inclinee(self):
        self._assert_count("CubeA_Above_45CuboidA.ifc", Above,
                           "45CuboidA", "CubeA", 0, **ABOVE, tolerance=1.0)
        self._assert_count("CubeA_Above_45CuboidA.ifc", Above,
                           "45CuboidA", "CubeA", 1, **ABOVE, tolerance=2.0)
        self._assert_count("CubeA_Below_45CuboidA.ifc", Below,
                           "45CuboidA", "CubeA", 0, **BELOW, tolerance=1.0)
        self._assert_count("CubeA_Below_45CuboidA.ifc", Below,
                           "45CuboidA", "CubeA", 1, **BELOW, tolerance=2.0)

    def test_multi_objets(self):
        m = "CubeA_Above_CubeB_Above_SlabA.ifc"
        self._assert_count(m, Above, "CubeB", "CubeA", 1, **ABOVE, tolerance=1.0)
        self._assert_count(m, Above, "SlabA", "CubeB", 1, **ABOVE, tolerance=1.0)
        self._assert_count(m, Above, "SlabA", "CubeA", 1, **ABOVE, tolerance=3.5)

    def test_formes_courbes(self):
        # sphere au-dessus de la dalle : gap 0.5m, borne exclusive
        self._assert_count("SphereA_Above_SlabA.ifc", Above,
                           "SlabA", "SphereA", 1, **ABOVE, tolerance=0.6)
        self._assert_count("SphereA_Above_SlabA.ifc", Above,
                           "SlabA", "SphereA", 0, **ABOVE, tolerance=0.4)
        # sphere qui chevauche la plage Z de la dalle : pas above
        self._assert_count("SphereA_NotAbove_SlabA.ifc", Above,
                           "SlabA", "SphereA", 0, **ABOVE, tolerance=0.1)
        # cone au-dessus : gap 1.0m
        self._assert_count("ConeA_Above_SlabA.ifc", Above,
                           "SlabA", "ConeA", 1, **ABOVE, tolerance=1.1)
        self._assert_count("ConeA_Above_SlabA.ifc", Above,
                           "SlabA", "ConeA", 0, **ABOVE, tolerance=0.9)
        # cube dans le creux du U : pas above
        self._assert_count("CubeB_InU_Crevasse_UshapeA.ifc", Above,
                           "UshapeA", "CubeB", 0, **ABOVE, tolerance=0.1)

    def test_above_facebased_echoue_sur_tore_et_poutre(self):
        # get_extreme_faces ne trouve pas de "face du dessus" nette :
        # Above=0 meme avec une grosse tolerance, OBB_Above=1 (voir plus bas)
        self._assert_count("CubeA_Above_TorusA.ifc", Above,
                           "TorusA", "CubeA", 0, **ABOVE, tolerance=2.0)
        self._assert_count("BeamLongA_Above_CubeA.ifc", Above,
                           "CubeA", "BeamLongA", 0, **ABOVE, tolerance=3.0)
        self._assert_count("CubeA_AboveNotInFront_CuboidA_3m.ifc", Above,
                           "CuboidA", "CubeA", 1, **ABOVE, tolerance=2.0)


# ---------------------------------------------------------------------------
# OBB_Above / OBB_Below / OBB_Front_And_Back (zones OBB)
# ---------------------------------------------------------------------------

class TestOBB(IFCModelRuleTestCase):
    def test_obb_above(self):
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", OBB_Above,
                           "SlabA", "SlabB", 1, tolerance=0.1)
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", OBB_Above,
                           "SlabB", "SlabA", 0, tolerance=0.1)
        self._assert_count("SlabA_ZOverlapNoXY_SlabB.ifc", OBB_Above,
                           "SlabA", "SlabB", 0, tolerance=0.1)
        self._assert_count("CubeA_NotBelow_CubeB_1m.ifc", OBB_Above,
                           "CubeB", "CubeA", 0, tolerance=1.0)
        self._assert_count("CubeA_AboveNotInFront_CuboidA_3m.ifc", OBB_Above,
                           "CuboidA", "CubeA", 1, tolerance=2.0)
        self._assert_count("CubeA_Above_45CuboidA.ifc", OBB_Above,
                           "45CuboidA", "CubeA", 1, tolerance=2.0)
        self._assert_count("CubeA_Above_CubeB_Above_SlabA.ifc", OBB_Above,
                           "SlabA", "CubeA", 1, tolerance=3.5)
        self._assert_count("SphereA_Above_SlabA.ifc", OBB_Above,
                           "SlabA", "SphereA", 1, tolerance=0.6)
        # sphère qui chevauche en Z : l'OBB la detecte quand meme (faux positif)
        self._assert_count("SphereA_NotAbove_SlabA.ifc", OBB_Above,
                           "SlabA", "SphereA", 1, tolerance=0.1)
        # faux positif OBB sur le tore : le cube est dans le trou
        self._assert_count("CubeA_InHole_TorusA.ifc", OBB_Above,
                           "TorusA", "CubeA", 1, tolerance=0.1)
        self._assert_count("CubeA_Above_TorusA.ifc", OBB_Above,
                           "TorusA", "CubeA", 1, tolerance=1.0)
        self._assert_count("ConeA_Above_SlabA.ifc", OBB_Above,
                           "SlabA", "ConeA", 1, tolerance=1.1)
        # poutre élancée : OBB_Above=1 alors que Above face-based=0
        self._assert_count("BeamLongA_Above_CubeA.ifc", OBB_Above,
                           "CubeA", "BeamLongA", 1, tolerance=2.0)

    def test_obb_below(self):
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", OBB_Below,
                           "SlabA", "SlabB", 0, tolerance=0.1)
        self._assert_count("CubeA_NotBelow_CubeB_1m.ifc", OBB_Below,
                           "CubeB", "CubeA", 0, tolerance=1.0)
        self._assert_count("CubeA_Below_45CuboidA.ifc", OBB_Below,
                           "45CuboidA", "CubeA", 1, tolerance=2.0)
        self._assert_count("CubeA_Above_CubeB_Above_SlabA.ifc", OBB_Below,
                           "CubeA", "SlabA", 1, tolerance=3.5)
        self._assert_count("CubeA_InHole_TorusA.ifc", OBB_Below,
                           "TorusA", "CubeA", 1, tolerance=0.1)
        self._assert_count("CubeA_Above_TorusA.ifc", OBB_Below,
                           "TorusA", "CubeA", 0, tolerance=1.0)
        self._assert_count("BeamLongA_Above_CubeA.ifc", OBB_Below,
                           "CubeA", "BeamLongA", 0, tolerance=2.0)
        self._assert_count("SphereA_Above_SlabA.ifc", OBB_Below,
                           "SlabA", "SphereA", 0, tolerance=0.6)

    def test_obb_front_and_back(self):
        # au-dessus => ni front ni back
        self._assert_count("CubeA_AboveNotInFront_CuboidA_3m.ifc",
                           OBB_Front_And_Back, "CuboidA", "CubeA",
                           0, tolerance=2.0, method="Wide")
        self._assert_count("CubeA_AboveNotInFront_CuboidA_3m.ifc",
                           OBB_Front_And_Back, "CuboidA", "CubeA",
                           0, tolerance=2.0, method="Narrow")
        # côté +X : hors zone Wide (front en Y), dans la zone Narrow (axe X)
        self._assert_count("SuzanneA_Side_CuboidA_NotFrontNotBehind.ifc",
                           OBB_Front_And_Back, "CuboidA", "SuzanneA",
                           0, tolerance=1.0, method="Wide")
        self._assert_count("SuzanneA_Side_CuboidA_NotFrontNotBehind.ifc",
                           OBB_Front_And_Back, "CuboidA", "SuzanneA",
                           1, tolerance=1.0, method="Narrow")
        # cube dans le creux du U : hors zones front/back
        self._assert_count("CubeB_InU_Crevasse_UshapeA.ifc",
                           OBB_Front_And_Back, "UshapeA", "CubeB",
                           0, tolerance=1.0, method="Wide")
        # cube dans le trou du tore : hors zone front
        self._assert_count("CubeA_InHole_TorusA.ifc", OBB_Front_And_Back,
                           "TorusA", "CubeA", 0, tolerance=0.1, method="Wide")
        # poutre à côté du cube (gap 1cm en Y) : dans la zone front du cube
        self._assert_count("BeamLongA_Clearance_CubeA_1cm.ifc",
                           OBB_Front_And_Back, "CubeA", "BeamLongA",
                           1, tolerance=0.5, method="Wide")


# ---------------------------------------------------------------------------
# AngleBetween (directions principales OBB)
# ---------------------------------------------------------------------------

class TestAngleBetween(IFCModelRuleTestCase):
    """Poutre selon X (10m) vs cube : Wide du cube parallele a X, Narrow a 90deg."""

    def test_beam_long_angles(self):
        m = "BeamLongA_Above_CubeA.ifc"
        self._assert_count(m, AngleBetween, "CubeA", "BeamLongA", 1,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Wide",
                           angle_difference=0, angle_tolerance=5)
        self._assert_count(m, AngleBetween, "CubeA", "BeamLongA", 0,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Wide",
                           angle_difference=90, angle_tolerance=5)
        self._assert_count(m, AngleBetween, "CubeA", "BeamLongA", 1,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Narrow",
                           angle_difference=90, angle_tolerance=5)
        self._assert_count(m, AngleBetween, "CubeA", "BeamLongA", 1,
                           direction_method_for_source="Narrow",
                           direction_method_for_target="Wide",
                           angle_difference=0, angle_tolerance=5)
        self._assert_count(m, AngleBetween, "CubeA", "BeamLongA", 1,
                           direction_method_for_source="Narrow",
                           direction_method_for_target="Narrow",
                           angle_difference=90, angle_tolerance=5)

    def test_beam_long_clearance_angles(self):
        m = "BeamLongA_Clearance_CubeA_1cm.ifc"
        self._assert_count(m, AngleBetween, "CubeA", "BeamLongA", 0,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Wide",
                           angle_difference=90, angle_tolerance=5)
        self._assert_count(m, AngleBetween, "CubeA", "BeamLongA", 1,
                           direction_method_for_source="Narrow",
                           direction_method_for_target="Narrow",
                           angle_difference=90, angle_tolerance=5)


if __name__ == "__main__":
    unittest.main()
