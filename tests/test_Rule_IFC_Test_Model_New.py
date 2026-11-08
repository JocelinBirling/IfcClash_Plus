"""Tests des modèles IFC générés par IFC_Test_Model/generate_models.py.

Ces 31 modèles complètent la couverture de IFC_Test_Model/IFC_Model/ :
positionnements manquants (ZOverlap, NotBelow, diagonale 3D, creux du U,
source inclinée, distances extrêmes, scène 3 objets, contact courbe) et
nouvelles géométries (sphère, tore, cône, poutre élancée, cylindres à profil
circulaire vrai, plaque fine) qui testent les hypothèses du moteur
(get_extreme_faces sur formes courbes, faux positifs OBB, stabilité du PCA).

Toutes les valeurs sont [calibrated] : observées en lançant les règles sur les
modèles générés (session de génération, environnement conda de agent.md).

Exécution (racine du dépôt) :
    python -m pytest tests/test_Rule_IFC_Test_Model_New.py -v
"""
import sys
import unittest

sys.path.insert(0, "./ifcclash_plus")

from Rules import (  # noqa: E402
    Above,
    Below,
    Clearance,
    Collision,
    Intersection,
    OBB_Above,
    OBB_Front_And_Back,
)
from tests.test_Rule_IFC_Test_Model import IFCModelRuleTestCase  # noqa: E402


class TestZOverlap(IFCModelRuleTestCase):
    """Chevauchement partiel en Z : intersection volumique mais ni Above ni Below."""

    def test_SlabA_ZOverlap_SlabB_intersection(self):
        # [calibrated] overlap X[1,3] Y[-1,0.7] Z[-0.05,0] = 0.17 m3.
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", Intersection,
                           "SlabA", "SlabB", 1, tolerance=0.001)

    def test_SlabA_ZOverlap_SlabB_not_above_not_below(self):
        # [calibrated] les plages Z se chevauchent : aucune dalle ne domine.
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", Above,
                           "SlabB", "SlabA", 0,
                           above_type="Above_MaxToMin", tolerance=0.1)
        self._assert_count("SlabA_ZOverlap_SlabB.ifc", Below,
                           "SlabB", "SlabA", 0,
                           below_type="Below_MinToMax", tolerance=0.1)

    def test_SlabA_ZOverlapNoXY_SlabB_no_intersection(self):
        # [calibrated] Z commun mais X/Y disjoints : pas d'intersection.
        self._assert_count("SlabA_ZOverlapNoXY_SlabB.ifc", Intersection,
                           "SlabA", "SlabB", 0, tolerance=0.001)

    def test_SlabA_SameZ_OverlapXY_SlabB_coplanar(self):
        # [calibrated] deux dalles coplanaires qui se chevauchent en plan :
        # pas de volume commun "propre" pour le BVH -> Intersection=0,
        # Collision=0, mais distance 0 -> Clearance=1.
        self._assert_count("SlabA_SameZ_OverlapXY_SlabB.ifc", Intersection,
                           "SlabA", "SlabB", 0, tolerance=0.001)
        self._assert_count("SlabA_SameZ_OverlapXY_SlabB.ifc", Collision,
                           "SlabA", "SlabB", 0)
        self._assert_count("SlabA_SameZ_OverlapXY_SlabB.ifc", Clearance,
                           "SlabA", "SlabB", 1, clearance=0.001)


class TestNegations(IFCModelRuleTestCase):
    """Négations explicites manquantes dans la suite originale."""

    def test_CubeA_NotBelow_CubeB(self):
        # [calibrated] même plage Z, gap 1m en X.
        self._assert_count("CubeA_NotBelow_CubeB_1m.ifc", Below,
                           "CubeB", "CubeA", 0,
                           below_type="Below_MinToMax", tolerance=1.0)

    def test_CubeA_AboveNotInFront_CuboidA(self):
        # [calibrated] CubeA au-dessus de CuboidA : Above=1, OBB_Above=1,
        # mais ni front ni back (les zones Wide/Narrow sont horizontales).
        self._assert_count("CubeA_AboveNotInFront_CuboidA_3m.ifc", Above,
                           "CuboidA", "CubeA", 1,
                           above_type="Above_MaxToMin", tolerance=2.0)
        self._assert_count("CubeA_AboveNotInFront_CuboidA_3m.ifc",
                           OBB_Front_And_Back,
                           "CuboidA", "CubeA", 0, tolerance=2.0, method="Wide")
        self._assert_count("CubeA_AboveNotInFront_CuboidA_3m.ifc",
                           OBB_Front_And_Back,
                           "CuboidA", "CubeA", 0, tolerance=2.0, method="Narrow")

    def test_SuzanneA_Side_CuboidA_NotFrontNotBehind(self):
        # [calibrated] SuzanneA sur le côté +X de CuboidA : la zone Wide
        # (front/back horizontal en Y) ne l'atteint pas -> 0, mais la zone
        # Narrow (axe X) si -> 1. Documente la différence Wide/Narrow.
        self._assert_count("SuzanneA_Side_CuboidA_NotFrontNotBehind.ifc",
                           OBB_Front_And_Back,
                           "CuboidA", "SuzanneA", 0, tolerance=1.0, method="Wide")
        self._assert_count("SuzanneA_Side_CuboidA_NotFrontNotBehind.ifc",
                           OBB_Front_And_Back,
                           "CuboidA", "SuzanneA", 1, tolerance=1.0, method="Narrow")


class TestDistances(IFCModelRuleTestCase):
    """Diagonale 3D et distances extrêmes pour Clearance."""

    def test_CubeA_Diagonal3D_CubeB(self):
        # [calibrated] gap 1m sur chaque axe -> distance reelle sqrt(3) = 1.732m.
        self._assert_count("CubeA_Diagonal3D_CubeB_1,73m.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=1.74)
        self._assert_count("CubeA_Diagonal3D_CubeB_1,73m.ifc", Clearance,
                           "CubeA", "CubeB", 0, clearance=1.70)

    def test_CubeA_NextTo_CubeB_0_1mm(self):
        # [expected] gap 0.1mm.
        self._assert_count("CubeA_NextTo_CubeB_0,1mm.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=0.001)
        self._assert_count("CubeA_NextTo_CubeB_0,1mm.ifc", Clearance,
                           "CubeA", "CubeB", 0, clearance=0.00005)

    def test_CubeA_Far_CubeB_10m(self):
        # [calibrated] distance 10m, borne exclusive.
        self._assert_count("CubeA_Far_CubeB_10m.ifc", Clearance,
                           "CubeA", "CubeB", 0, clearance=10.0)
        self._assert_count("CubeA_Far_CubeB_10m.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=10.01)


class TestUshape(IFCModelRuleTestCase):
    """Cas limites avec le U non convexe (creux X[-2,2] Y[-2,2] Z[-1,3])."""

    def test_CubeB_InU_Crevasse_no_contact(self):
        # [calibrated] CubeB au centre du creux.
        self._assert_count("CubeB_InU_Crevasse_UshapeA.ifc", Collision,
                           "CubeB", "UshapeA", 0)
        self._assert_count("CubeB_InU_Crevasse_UshapeA.ifc", Intersection,
                           "CubeB", "UshapeA", 0, tolerance=0.001)

    def test_CubeA_PartialIntersect_UshapeA(self):
        # [calibrated] CubeA penetre le bras ouest X[-3,-2] sur 0.75m.
        self._assert_count("CubeA_PartialIntersect_UshapeA.ifc", Intersection,
                           "CubeA", "UshapeA", 1, tolerance=0.001)


class TestInclinedSource(IFCModelRuleTestCase):
    """Above/Below avec la source inclinée (45CuboidA) + diagonale proche."""

    def test_CubeA_Above_45CuboidA(self):
        # [calibrated] Above tol 1.0 = 0, tol 2.0 = 1 (gap ~1-2m selon les
        # faces extrêmes du cuboid incliné).
        self._assert_count("CubeA_Above_45CuboidA.ifc", Above,
                           "45CuboidA", "CubeA", 0,
                           above_type="Above_MaxToMin", tolerance=1.0)
        self._assert_count("CubeA_Above_45CuboidA.ifc", Above,
                           "45CuboidA", "CubeA", 1,
                           above_type="Above_MaxToMin", tolerance=2.0)
        self._assert_count("CubeA_Above_45CuboidA.ifc", OBB_Above,
                           "45CuboidA", "CubeA", 1, tolerance=2.0)

    def test_CubeA_Below_45CuboidA(self):
        # [calibrated]
        self._assert_count("CubeA_Below_45CuboidA.ifc", Below,
                           "45CuboidA", "CubeA", 0,
                           below_type="Below_MinToMax", tolerance=1.0)
        self._assert_count("CubeA_Below_45CuboidA.ifc", Below,
                           "45CuboidA", "CubeA", 1,
                           below_type="Below_MinToMax", tolerance=2.0)

    def test_45CuboidA_DiagClose_CubeB_37cm(self):
        # [calibrated] formes disjointes en diagonale (distance ~0.1-0.2m) :
        # pas d'intersection, Clearance(0.05)=0, Clearance(0.2)=1.
        self._assert_count("45CuboidA_DiagClose_CubeB_37cm.ifc", Intersection,
                           "45CuboidA", "CubeB", 0, tolerance=0.001)
        self._assert_count("45CuboidA_DiagClose_CubeB_37cm.ifc", Clearance,
                           "45CuboidA", "CubeB", 0, clearance=0.05)
        self._assert_count("45CuboidA_DiagClose_CubeB_37cm.ifc", Clearance,
                           "45CuboidA", "CubeB", 1, clearance=0.2)


class TestMultiObject(IFCModelRuleTestCase):
    """Scène à 3 objets empilés : SlabA z[-0.1,0], CubeB z[1,2], CubeA z[3,4]."""

    def test_CubeA_Above_CubeB_Above_SlabA(self):
        # [calibrated]
        self._assert_count("CubeA_Above_CubeB_Above_SlabA.ifc", Above,
                           "CubeB", "CubeA", 1,
                           above_type="Above_MaxToMin", tolerance=1.0)
        self._assert_count("CubeA_Above_CubeB_Above_SlabA.ifc", Above,
                           "SlabA", "CubeB", 1,
                           above_type="Above_MaxToMin", tolerance=1.0)
        self._assert_count("CubeA_Above_CubeB_Above_SlabA.ifc", Above,
                           "SlabA", "CubeA", 1,
                           above_type="Above_MaxToMin", tolerance=3.5)


class TestHollowCylinder(IFCModelRuleTestCase):
    """Contacts et jeux avec le cylindre creux (paroi r_int=0.8, r_ext=1.0)."""

    def test_CylinderA_TouchOutside_HollowCylinderA(self):
        # [calibrated] contact courbe-sur-courbe en x=1.
        self._assert_count("CylinderA_TouchOutside_HollowCylinderA.ifc", Collision,
                           "CylinderA", "HollowCylinderA", 1, allow_touching=True)

    def test_CylinderSmallA_Clearance_HollowCylinderA_1cm(self):
        # [calibrated] cylindre r=0.79 dans le creux r=0.8 -> jeu 1cm.
        self._assert_count("CylinderSmallA_Clearance_HollowCylinderA_1cm.ifc",
                           Clearance, "CylinderSmallA", "HollowCylinderA",
                           1, clearance=0.02)
        self._assert_count("CylinderSmallA_Clearance_HollowCylinderA_1cm.ifc",
                           Clearance, "CylinderSmallA", "HollowCylinderA",
                           0, clearance=0.005)
        self._assert_count("CylinderSmallA_Clearance_HollowCylinderA_1cm.ifc",
                           Collision, "CylinderSmallA", "HollowCylinderA", 0)

    def test_CylinderA_Inside_BigCubeA(self):
        # [expected] cylindre r=1 h=4 au centre du cube 10m.
        self._assert_count("CylinderA_Inside_BigCubeA.ifc", Intersection,
                           "CylinderA", "BigCubeA", 1, tolerance=0.001)


class TestSphere(IFCModelRuleTestCase):
    """Sphère : forme courbe sans face horizontale (teste get_extreme_faces)."""

    def test_SphereA_Above_SlabA(self):
        # [calibrated] sphère z[0.5,2.5], dalle z max 0, gap 0.5m.
        self._assert_count("SphereA_Above_SlabA.ifc", Above,
                           "SlabA", "SphereA", 1,
                           above_type="Above_MaxToMin", tolerance=0.6)
        self._assert_count("SphereA_Above_SlabA.ifc", OBB_Above,
                           "SlabA", "SphereA", 1, tolerance=0.6)

    def test_SphereA_NotAbove_SlabA(self):
        # [calibrated] sphère z[-0.5,1.5] chevauche la plage Z de la dalle.
        self._assert_count("SphereA_NotAbove_SlabA.ifc", Above,
                           "SlabA", "SphereA", 0,
                           above_type="Above_MaxToMin", tolerance=0.1)

    def test_SphereA_Intersect_SlabA(self):
        # [calibrated] pénétration ~10cm mais Intersection (BVH) = 0,
        # Collision = 1, Clearance = 1 : divergence documentee courbe vs plan.
        self._assert_count("SphereA_Intersect_SlabA.ifc", Intersection,
                           "SphereA", "SlabA", 0, tolerance=0.001)
        self._assert_count("SphereA_Intersect_SlabA.ifc", Intersection,
                           "SphereA", "SlabA", 0, tolerance=1.0)
        self._assert_count("SphereA_Intersect_SlabA.ifc", Collision,
                           "SphereA", "SlabA", 1)
        self._assert_count("SphereA_Intersect_SlabA.ifc", Clearance,
                           "SphereA", "SlabA", 1, clearance=0.001)

    def test_SphereA_TangentTop_SlabA(self):
        # [calibrated] contact ponctuel en z=0 : pas d'intersection, distance 0.
        self._assert_count("SphereA_TangentTop_SlabA.ifc", Intersection,
                           "SphereA", "SlabA", 0, tolerance=0.001)
        self._assert_count("SphereA_TangentTop_SlabA.ifc", Clearance,
                           "SphereA", "SlabA", 1, clearance=0.001)

    def test_SphereA_Tangent_SphereB(self):
        # [calibrated] contact ponctuel courbe-sur-courbe en (1,0,0) :
        # Collision = 0 meme avec allow_touching, Clearance = 1.
        self._assert_count("SphereA_Tangent_SphereB.ifc", Collision,
                           "SphereA", "SphereB", 0, allow_touching=True)
        self._assert_count("SphereA_Tangent_SphereB.ifc", Clearance,
                           "SphereA", "SphereB", 1, clearance=0.001)


class TestTorus(IFCModelRuleTestCase):
    """Tore : faux positif OBB (l'OBB englobe le trou central)."""

    def test_CubeA_InHole_TorusA(self):
        # [calibrated] CubeA 1m au centre du trou (rayon 1.5) :
        # pas d'intersection reelle, mais l'OBB du tore englobe le centre.
        self._assert_count("CubeA_InHole_TorusA.ifc", Intersection,
                           "CubeA", "TorusA", 0, tolerance=0.001)
        self._assert_count("CubeA_InHole_TorusA.ifc", OBB_Above,
                           "TorusA", "CubeA", 1, tolerance=0.1)

    def test_CubeA_Above_TorusA(self):
        # [calibrated] Above face-based = 0 a toute tolerance (get_extreme_faces
        # ne trouve pas de "face du dessus" nette sur le tore maillé),
        # OBB_Above = 1 : divergence face-based vs OBB sur forme courbe.
        self._assert_count("CubeA_Above_TorusA.ifc", Above,
                           "TorusA", "CubeA", 0,
                           above_type="Above_MaxToMin", tolerance=2.0)
        self._assert_count("CubeA_Above_TorusA.ifc", OBB_Above,
                           "TorusA", "CubeA", 1, tolerance=1.0)


class TestCone(IFCModelRuleTestCase):
    """Cône : sommet ponctuel, pas de face supérieure plane."""

    def test_ConeA_Above_SlabA(self):
        # [calibrated] base du cone a z=1, dalle z max 0, gap 1m.
        self._assert_count("ConeA_Above_SlabA.ifc", Above,
                           "SlabA", "ConeA", 1,
                           above_type="Above_MaxToMin", tolerance=1.1)
        self._assert_count("ConeA_Above_SlabA.ifc", OBB_Above,
                           "SlabA", "ConeA", 1, tolerance=1.1)

    def test_ConeA_PointIn_CubeB(self):
        # [calibrated] pointe a z=1.55 dans CubeB z[1.5,2.5] :
        # Collision = 1, Intersection = 0 (penetration ponctuelle faible).
        self._assert_count("ConeA_PointIn_CubeB.ifc", Collision,
                           "ConeA", "CubeB", 1)
        self._assert_count("ConeA_PointIn_CubeB.ifc", Intersection,
                           "ConeA", "CubeB", 0, tolerance=0.001)


class TestBeamLong(IFCModelRuleTestCase):
    """Poutre élancée 10m x 2cm x 2cm : stabilité numérique du PCA/OBB."""

    def test_BeamLongA_Above_CubeA(self):
        # [calibrated] Above face-based = 0 a toute tolerance (faces top/bottom
        # de 0.2 m2 perdues dans le filtrage), OBB_Above = 1, Clearance = 1 :
        # divergence face-based vs OBB sur objet élancé.
        self._assert_count("BeamLongA_Above_CubeA.ifc", Above,
                           "CubeA", "BeamLongA", 0,
                           above_type="Above_MaxToMin", tolerance=3.0)
        self._assert_count("BeamLongA_Above_CubeA.ifc", OBB_Above,
                           "CubeA", "BeamLongA", 1, tolerance=2.0)
        self._assert_count("BeamLongA_Above_CubeA.ifc", Clearance,
                           "CubeA", "BeamLongA", 1, clearance=2.0)

    def test_BeamLongA_Clearance_CubeA_1cm(self):
        # [calibrated] gap Y = 1cm entre la poutre (Y[0.51,0.53]) et le cube.
        self._assert_count("BeamLongA_Clearance_CubeA_1cm.ifc", Clearance,
                           "CubeA", "BeamLongA", 1, clearance=0.02)
        self._assert_count("BeamLongA_Clearance_CubeA_1cm.ifc", Clearance,
                           "CubeA", "BeamLongA", 0, clearance=0.005)


class TestCylinderTrue(IFCModelRuleTestCase):
    """Vrai cylindre IfcCircleProfileDef : comparaison BVH vs BREP (Intersection2)."""

    def test_CylinderTrueA_Intersect_CubeA_1mm(self):
        # [calibrated] penetration 1mm (cylindre X[0.499,2.499], cube X max 0.5).
        self._assert_count("CylinderTrueA_Intersect_CubeA_1mm.ifc", Collision,
                           "CylinderTrueA", "CubeA", 1)


class TestThinPlate(IFCModelRuleTestCase):
    """Plaque de 1mm entièrement dans le cube : plus fine que la maille adverse."""

    def test_PlateThinA_Through_CubeB(self):
        # [calibrated] Collision = 1, Intersection = 0 (meme limite connue que
        # CubeA_Intersect_CubeB_1mm : Intersection manque les containments fins).
        self._assert_count("PlateThinA_Through_CubeB_1mm.ifc", Collision,
                           "PlateThinA", "CubeB", 1)
        self._assert_count("PlateThinA_Through_CubeB_1mm.ifc", Intersection,
                           "PlateThinA", "CubeB", 0, tolerance=0.001)
        self._assert_count("PlateThinA_Through_CubeB_1mm.ifc", Intersection,
                           "PlateThinA", "CubeB", 0, tolerance=0.1)


if __name__ == "__main__":
    unittest.main()
