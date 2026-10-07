"""Suite de tests geometriques pour les maquettes de IFC_Test_Model/IFC_Model/.

Chaque maquette porte un nom de la forme Source_Position_Target[_parametre].ifc :
la relation decrite par le nom doit etre confirmee (exactement 1 resultat Source/Target)
ou infirmee (0 resultat) par la regle correspondante de ifcclash_plus.

Organisation : une classe de test par regle (voir IFC_Test_Model/README.md).
Un meme modele peut etre utilise par plusieurs classes : l'utilisation "evidente"
est celle encodee dans son nom, les autres utilisations servent de contre-exemple
ou documentent un comportement au bord (contact, coïncidence, distance limite).

Selection des objets : par nom (IFC `Name`) via un facet ifctester Attribute,
car les objets sont mappes sur des entites IFC heterogenes (IFCFAN, IFCENGINE,
IFCSLAB, IFCCOIL, IFCCOLUMN...).

Ordre d'appel des regles directionnelles
----------------------------------------
Above / Below / OBB_Above / OBB_Below / OBB_Front_And_Back construisent une zone
de detection ANCREE SUR LA SOURCE et detectent la CIBLE dans cette zone (voir
doc/2ObjectsRules/OBB_Above.md : "detect objects that are above source objects").
Les tests appellent donc ces regles dans l'ordre SEMANTIQUE :

    CubeA_Above_CubeB_1m.ifc  (CubeA est au-dessus de CubeB)
        -> Above(source=CubeB, target=CubeA, above_type="Above_MaxToMin", ...)

    above_type "Above_MaxToMin" = face haute de la source vs face basse de la
    cible (cible au-dessus de la source) ; "Above_MinToMax" = l'inverse.
    below_type "Below_MinToMax" = face basse de la source vs face haute de la
    cible (cible au-dessous de la source).

Provenance des valeurs attendues
--------------------------------
[calibre]  comportement observe : IFC_Test_Model/calibration.jsonl (session
           precedente) ou runs de verification de la session courante (regles
           symetriques : Intersection, Clearance, Collision, AngleBetween).
[attendu]  attente encodee d'apres la semantique documentee des regles
           directionnelles (ordre semantique). Ces tests n'ont PAS ete
           executes a l'ecriture de ce fichier ; a ajuster au premier run.

Bugs de regles documentes par des @unittest.expectedFailure
-----------------------------------------------------------
1. Collision : le parametre allow_touching du constructeur est ecrase
   (Rules.py, `self.allow_touching = False`), le contact n'est jamais detecte.
2. Intersection : une penetration de 1mm (CubeA_Intersect_CubeB_1mm) n'est pas
   detectee, alors que Collision la detecte.
3. Collision/Intersection : deux solides parfaitement coincidents
   (CubeA_SamePlace_CubeB) ne sont detectes par aucune des deux regles.

Regles documentees mais non implémentees
-----------------------------------------
Inside (doc/2ObjectsRules/Inside) et SurfaceRecover (doc/2ObjectsRules/
SurfaceRecover.md) n'existent pas dans ifcclash_plus/Rules.py : les maquettes
correspondantes sont couvertes par les regles les plus proches (Intersection,
Collision, Clearance) et les tests "evidents" sont skipTest avec justification.

Execution (depuis la racine du depot, avec l'environnement conda du projet,
voir agent.md) :
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

# Certains modeles portent un nom de cible qui ne correspond pas exactement au
# `Name` IFC de l'objet vise (fichiers generes a la main) :
#   - "HollowCylinderA" s'appelle "Hollow_CylinderA" dans un seul modele ;
#   - "45Cuboid" n'existe pas : l'objet vise (proche de la source) est
#     "45CuboidA", "45CuboidB" etant place loin de toutes les sources.
NAME_OVERRIDES = {
    "CubeA_NotTouch_HollowCylinderA.ifc": {"HollowCylinderA": "Hollow_CylinderA"},
    "CubeB_Intersect_45Cuboid.ifc": {"45Cuboid": "45CuboidA"},
    "CuboidA_NoOrient_45Cuboid.ifc": {"45Cuboid": "45CuboidA"},
    "CuboidA_Orient_45Cuboid_45.ifc": {"45Cuboid": "45CuboidA"},
}


class IFCModelRuleTestCase(unittest.TestCase):
    """Base commune : execution d'une regle sur un couple Source/Target d'une maquette."""

    @staticmethod
    def _select(name):
        select = SelectFacet()
        select.applicability = [ids.Attribute(name="Name", value=name)]
        return select

    def _resolved(self, model, name):
        return NAME_OVERRIDES.get(model, {}).get(name, name)

    def _run_rule(self, model, rule_cls, source, target, **kwargs):
        """Construit la regle sur le couple (source, target) de la maquette et la joue."""
        rule_file = RuleFile()
        rule_file.list_ifc_path = [os.path.join(MODEL_DIR, model)]
        src = self._resolved(model, source)
        tgt = self._resolved(model, target)
        rule = rule_cls(self._select(src), self._select(tgt), **kwargs)
        rule_file.contains = [rule]
        rule_file.run()
        return rule, src, tgt

    def _assert_count(self, model, rule_cls, source, target, expected, **kwargs):
        """Joue la regle et verifie le nombre de resultats (et le couple retourne)."""
        rule, src, tgt = self._run_rule(model, rule_cls, source, target, **kwargs)
        self.assertEqual(
            len(rule.result),
            expected,
            msg=f"{model} : {rule_cls.__name__}{kwargs} -> "
            f"{len(rule.result)} resultat(s), {expected} attendu(s)",
        )
        if expected == 1:
            result = rule.result[0]
            self.assertEqual(result.source.Name, src)
            self.assertEqual(result.target.Name, tgt)


class TestIntersection(IFCModelRuleTestCase):
    """Regle Intersection sur les maquettes (mots-cles : Intersect, Inside*, TouchOutside)."""

    def test_CubeA_Intersect_CubeB_10cm(self):
        # [calibre] vraie intersection volumique : detectee a toutes les tolerances testees.
        self._assert_count("CubeA_Intersect_CubeB_10cm.ifc", Intersection,
                           "CubeA", "CubeB", 1, tolerance=0.001)
        self._assert_count("CubeA_Intersect_CubeB_10cm.ifc", Intersection,
                           "CubeA", "CubeB", 1, tolerance=0.1)
        
        self._assert_count("CubeA_Intersect_CubeB_10cm.ifc", Intersection,
                           "CubeA", "CubeB", 0, tolerance=0.11)
        self._assert_count("CubeA_Intersect_CubeB_10cm.ifc", Intersection,
                           "CubeA", "CubeB", 0, tolerance=0.5)


    def test_CubeA_Intersect_CubeB_1mm(self):
        # BUG [calibre] : penetration de 1mm non detectee par Intersection (0 observe
        # a tolerance 0.001 comme a 0.1) alors que Collision la detecte.
        self._assert_count("CubeA_Intersect_CubeB_1mm.ifc", Intersection,
                           "CubeA", "CubeB", 1, tolerance=0.0009)
        self._assert_count("CubeA_Intersect_CubeB_1mm.ifc", Intersection,
                           "CubeA", "CubeB", 0, tolerance=0.0011)

    def test_CylinderA_Intersect_SlabA(self):
        # [calibre]
        self._assert_count("CylinderA_Intersect_SlabA.ifc", Intersection,
                           "CylinderA", "SlabA", 1, tolerance=0.001)
        self._assert_count("CylinderA_Intersect_SlabA.ifc", Intersection,
                           "CylinderA", "SlabA", 1, tolerance=0.1)

    def test_CylinderA_Intersect_SlabA_Case2(self):
        # [calibre]
        self._assert_count("CylinderA_Intersect_SlabA_Case2.ifc", Intersection,
                           "CylinderA", "SlabA", 1, tolerance=0.001)

    def test_CylinderA_Intersect_SlabA_Case3(self):
        # [calibre]
        self._assert_count("CylinderA_Intersect_SlabA_Case3.ifc", Intersection,
                           "CylinderA", "SlabA", 1, tolerance=0.001)

    def test_SuzanneA_Intersect_UshapeA(self):
        # [calibre]
        self._assert_count("SuzanneA_Intersect_UshapeA.ifc", Intersection,
                           "SuzanneA", "UshapeA", 1, tolerance=0.001)

    def test_SuzanneA_Intersect_HollowCylinderA(self):
        # [calibre]
        self._assert_count("SuzanneA_Intersect_HollowCylinderA.ifc", Intersection,
                           "SuzanneA", "HollowCylinderA", 1, tolerance=0.001)

    def test_CubeB_Intersect_45Cuboid(self):
        # [calibre] cible reelle : 45CuboidA (voir NAME_OVERRIDES).
        self._assert_count("CubeB_Intersect_45Cuboid.ifc", Intersection,
                           "CubeB", "45Cuboid", 1, tolerance=0.001)
        self._assert_count("CubeB_Intersect_45Cuboid.ifc", Intersection,
                           "CubeB", "45Cuboid", 1, tolerance=0.1)

    def test_CubeA_Inside_BigCubeA(self):
        # [calibre] regle Inside non implémentee : la maquette illustre le
        # comportement d'Intersection sur une inclusion complete.
        self._assert_count("CubeA_Inside_BigCubeA.ifc", Intersection,
                           "CubeA", "BigCubeA", 1, tolerance=0.001)

    def test_CubeB_Inside_BigCubeA(self):
        # [calibre]
        self._assert_count("CubeB_Inside_BigCubeA.ifc", Intersection,
                           "CubeB", "BigCubeA", 1, tolerance=0.001)

    def test_CubeA_InsideFaceTouch_BigCubeA(self):
        # [calibre] inclusion avec contact de face : l'intersection est detectee.
        self._assert_count("CubeA_InsideFaceTouch_BigCubeA.ifc", Intersection,
                           "CubeA", "BigCubeA", 1, tolerance=0.001)

    def test_CubeA_TouchOutside_BigCubeA_1mm(self):
        # [calibre] cube pose sur la face exterieure du gros cube :
        # le contact est vu comme intersection.
        self._assert_count("CubeA_TouchOutside_BigCubeA_1mm.ifc", Intersection,
                           "CubeA", "BigCubeA", 1, tolerance=0.001)

    def test_CubeA_TouchFace_CubeB(self):
        # [calibre] comportement au contact strict : deux solides qui se touchent
        # par une face ne produisent PAS de resultat d'Intersection.
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Intersection,
                           "CubeA", "CubeB", 0, tolerance=0.001)
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Intersection,
                           "CubeA", "CubeB", 0, tolerance=0.1)

    def test_CubeA_SamePlace_CubeB(self):
        # [calibre] comportement en coincidence parfaite : deux solides
        # superposes exactement ne sont PAS detectes par Intersection.
        self._assert_count("CubeA_SamePlace_CubeB.ifc", Intersection,
                           "CubeA", "CubeB", 0, tolerance=1.0)


class TestCollision(IFCModelRuleTestCase):
    """Regle Collision sur les maquettes (mots-cles : Collide, Intersect, NotCollide, Touch*)."""

    def test_CubeA_Intersect_CubeB_10cm(self):
        # [calibre]
        self._assert_count("CubeA_Intersect_CubeB_10cm.ifc", Collision,
                           "CubeA", "CubeB", 1)

    def test_CubeA_Intersect_CubeB_1mm(self):
        # [calibre] c'est Collision (et non Intersection) qui voit la penetration 1mm.
        self._assert_count("CubeA_Intersect_CubeB_1mm.ifc", Collision,
                           "CubeA", "CubeB", 1)

    def test_CylinderA_Intersect_SlabA(self):
        # [calibre]
        self._assert_count("CylinderA_Intersect_SlabA.ifc", Collision,
                           "CylinderA", "SlabA", 1)

    def test_CylinderA_Intersect_SlabA_Case2(self):
        # [calibre]
        self._assert_count("CylinderA_Intersect_SlabA_Case2.ifc", Collision,
                           "CylinderA", "SlabA", 1)

    def test_CylinderA_Intersect_SlabA_Case3(self):
        # [calibre]
        self._assert_count("CylinderA_Intersect_SlabA_Case3.ifc", Collision,
                           "CylinderA", "SlabA", 1)

    def test_SuzanneA_Intersect_UshapeA(self):
        # [calibre]
        self._assert_count("SuzanneA_Intersect_UshapeA.ifc", Collision,
                           "SuzanneA", "UshapeA", 1)

    def test_SuzanneA_Intersect_HollowCylinderA(self):
        # [calibre]
        self._assert_count("SuzanneA_Intersect_HollowCylinderA.ifc", Collision,
                           "SuzanneA", "HollowCylinderA", 1)

    def test_CubeB_Intersect_45Cuboid(self):
        # [calibre]
        self._assert_count("CubeB_Intersect_45Cuboid.ifc", Collision,
                           "CubeB", "45Cuboid", 1)

    def test_SuzanneA_Collide_CuboidA_150cm(self):
        # [calibre]
        self._assert_count("SuzanneA_Collide_CuboidA_150cm.ifc", Collision,
                           "SuzanneA", "CuboidA", 1)

    def test_SuzanneA_Collide_SuzanneB_n1(self):
        # [calibre]
        self._assert_count("SuzanneA_Collide_SuzanneB_n1.ifc", Collision,
                           "SuzanneA", "SuzanneB", 1)

    def test_SuzanneA_Collide_SuzanneB_n2(self):
        # [calibre]
        self._assert_count("SuzanneA_Collide_SuzanneB_n2.ifc", Collision,
                           "SuzanneA", "SuzanneB", 1)

    def test_SuzanneA_Collide_SuzanneB_n3(self):
        # [calibre]
        self._assert_count("SuzanneA_Collide_SuzanneB_n3.ifc", Collision,
                           "SuzanneA", "SuzanneB", 1)

    def test_SuzanneA_NotCollide_SuzanneB(self):
        # [calibre]
        self._assert_count("SuzanneA_NotCollide_SuzanneB.ifc", Collision,
                           "SuzanneA", "SuzanneB", 0)

    def test_SuzanneA_NotTouch_HollowCylinderA(self):
        # [calibre]
        self._assert_count("SuzanneA_NotTouch_HollowCylinderA.ifc", Collision,
                           "SuzanneA", "HollowCylinderA", 0)

    def test_SuzanneA_NotTouch_HollowCylinderA_n2(self):
        # [calibre]
        self._assert_count("SuzanneA_NotTouch_HollowCylinderA_n2.ifc", Collision,
                           "SuzanneA", "HollowCylinderA", 0)

    def test_CubeA_NotTouch_HollowCylinderA(self):
        # [calibre] (objet IF C "Hollow_CylinderA" dans ce modele, voir NAME_OVERRIDES)
        self._assert_count("CubeA_NotTouch_HollowCylinderA.ifc", Collision,
                           "CubeA", "HollowCylinderA", 0)

    def test_UshapeA_NoTouch_CubeB(self):
        # [calibre]
        self._assert_count("UshapeA_NoTouch_CubeB.ifc", Collision,
                           "UshapeA", "CubeB", 0)

    def test_CubeA_TouchFace_CubeB_allow_touching_false(self):
        #@todo, rule or test not working
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 1, allow_touching=False)


    def test_CubeA_TouchFace_CubeB_allow_touching_true(self):
        #@todo, rule or test not working
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 0, allow_touching=True)

    def test_CubeA_TouchEdge_CubeB_allow_touching_false(self):
        #@todo, rule or test not working
        self._assert_count("CubeA_TouchEdge_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 1, allow_touching=False)

    def test_CubeA_TouchEdge_CubeB_allow_touching_true(self):
        #@todo, rule or test not working
        self._assert_count("CubeA_TouchEdge_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 0, allow_touching=True)

    def test_CubeA_TouchPoint_CubeB_allow_touching_false(self):
        #@todo, rule or test not working
        self._assert_count("CubeA_TouchPoint_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 1, allow_touching=False)


    def test_CubeA_TouchPoint_CubeB_allow_touching_true(self):
        #@todo, rule or test not working
        self._assert_count("CubeA_TouchPoint_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 0, allow_touching=True)

    def test_CubeA_SamePlace_CubeB(self):
        #@todo Create the same rule and update this test.
        # BUG [calibre] : deux solides parfaitement coincidents ne sont
        # detectes ni par Collision ni par Intersection (0 observe).
        # Mapping du README : SamePlace -> Collision, donc 1 resultat attendu.
        self._assert_count("CubeA_SamePlace_CubeB.ifc", Collision,
                           "CubeA", "CubeB", 1)


class TestClearance(IFCModelRuleTestCase):
    """Regle Clearance sur les maquettes (mots-cles : NextTo, Next, Diagonal, Touch*, NotTouch).

    Semantique observee [calibre] : Clearance retourne les couples dont la
    distance est STRICTEMENT inferieure au parametre clearance (violation de
    garde). Un couple exactement a la distance `clearance` n'est pas retourne.
    """

    def test_CubeA_NextTo_CubeB_1m(self):
        # [calibre] distance reelle = 1.0m : limite exclusive.
        self._assert_count("CubeA_NextTo_CubeB_1m.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=1.01)
        self._assert_count("CubeA_NextTo_CubeB_1m.ifc", Clearance,
                           "CubeA", "CubeB", 0, clearance=0.99)

    def test_CubeA_Diagonal_CubeB_1_41m(self):
        # [calibre] distance reelle = 1.4142m (diagonale).
        self._assert_count("CubeA_Diagonal_CubeB_1,41m.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=1.424)
        self._assert_count("CubeA_Diagonal_CubeB_1,41m.ifc", Clearance,
                           "CubeA", "CubeB", 0, clearance=1.396)

    def test_CubeA_TouchFace_CubeB(self):
        # [calibre] distance nulle au contact : toute clearance positive detecte.
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=0.1)
        self._assert_count("CubeA_TouchFace_CubeB.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=0.001)

    def test_CubeA_TouchEdge_CubeB(self):
        # [calibre]
        self._assert_count("CubeA_TouchEdge_CubeB.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=0.1)

    def test_CubeA_TouchPoint_CubeB(self):
        # [calibre]
        self._assert_count("CubeA_TouchPoint_CubeB.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=0.1)

    def test_CubeA_TouchOutside_BigCubeA_1mm(self):
        # [calibre] contact sur la face exterieure : distance nulle.
        self._assert_count("CubeA_TouchOutside_BigCubeA_1mm.ifc", Clearance,
                           "CubeA", "BigCubeA", 1, clearance=0.011)

    def test_CubeA_SamePlace_CubeB(self):
        # [calibre] seule regle qui "voit" deux solides coincidents.
        self._assert_count("CubeA_SamePlace_CubeB.ifc", Clearance,
                           "CubeA", "CubeB", 1, clearance=0.001)

    def test_SuzanneA_Collide_CuboidA_150cm(self):
        # [calibre] le couple est en collision (distance 0 < 1.5).
        self._assert_count("SuzanneA_Collide_CuboidA_150cm.ifc", Clearance,
                           "SuzanneA", "CuboidA", 1, clearance=1.5)

    def test_CubeB_Next_CuboidA_50cm(self):
        # [calibre] distance reelle ~1.03m : pas de violation d'une garde de 50cm.
        self._assert_count("CubeB_Next_CuboidA_50cm.ifc", Clearance,
                           "CubeB", "CuboidA", 0, clearance=0.505)

    def test_CubeA_NotTouch_HollowCylinderA(self):
        # [calibre] pas de contact (0 a clearance=0.001) mais le couple est
        # proche : distance reelle < 10cm, d'ou 1 a clearance=0.1.
        self._assert_count("CubeA_NotTouch_HollowCylinderA.ifc", Clearance,
                           "CubeA", "HollowCylinderA", 0, clearance=0.001)
        self._assert_count("CubeA_NotTouch_HollowCylinderA.ifc", Clearance,
                           "CubeA", "HollowCylinderA", 1, clearance=0.1)

    def test_SuzanneA_NotTouch_HollowCylinderA_n2(self):
        # [calibre] meme profil que le modele precedent.
        self._assert_count("SuzanneA_NotTouch_HollowCylinderA_n2.ifc", Clearance,
                           "SuzanneA", "HollowCylinderA", 0, clearance=0.001)
        self._assert_count("SuzanneA_NotTouch_HollowCylinderA_n2.ifc", Clearance,
                           "SuzanneA", "HollowCylinderA", 1, clearance=0.1)

    def test_UshapeA_NoTouch_CubeB(self):
        # [calibre] distance reelle 0.5m : pas de violation d'une garde de 1mm.
        self._assert_count("UshapeA_NoTouch_CubeB.ifc", Clearance,
                           "UshapeA", "CubeB", 0, clearance=0.001)


class TestAbove(IFCModelRuleTestCase):
    """Regle Above (face-based) en ordre semantique : la CIBLE est au-dessus de la SOURCE.

    [attendu] tests non executes a l'ecriture : ordre et parametres deduits
    de la semantique documentee et des distances de calibration.jsonl.
    """

    def test_CubeA_Above_CubeB_1m(self):
        # CubeA (z 1.5-2.5) est au-dessus de CubeB (z -0.5-0.5), ecart 1.0m.
        # La tolerance doit couvrir l'ecart entre faces (1.0) : 0.1 est trop court.
        self._assert_count("CubeA_Above_CubeB_1m.ifc", Above,
                           "CubeB", "CubeA", 1,
                           above_type="Above_MaxToMin", tolerance=1.0)
        self._assert_count("CubeA_Above_CubeB_1m.ifc", Above,
                           "CubeB", "CubeA", 0,
                           above_type="Above_MaxToMin", tolerance=0.1)

    def test_CubeB_Above_45CuboidA(self):
        # distance min 0.2767 ; tolerance 1.0 pour couvrir l'ecart diagonal du cuboid 45deg.
        self._assert_count("CubeB_Above_45CuboidA.ifc", Above,
                           "45CuboidA", "CubeB", 1,
                           above_type="Above_MaxToMin", tolerance=1.0)

    def test_CubeB_Above_UshapeA(self):
        # UshapeA (z max 4.0), CubeB (z 4.5-5.5) : ecart 0.5m.
        self._assert_count("CubeB_Above_UshapeA.ifc", Above,
                           "UshapeA", "CubeB", 1,
                           above_type="Above_MaxToMin", tolerance=1.0)

    def test_CylinderA_Above_SlabA(self):
        # ecart 0.5m.
        self._assert_count("CylinderA_Above_SlabA.ifc", Above,
                           "SlabA", "CylinderA", 1,
                           above_type="Above_MaxToMin", tolerance=1.0)
        self._assert_count("CylinderA_Above_SlabA.ifc", Above,
                           "SlabA", "CylinderA", 0,
                           above_type="Above_MaxToMin", tolerance=0.1)

    def test_SuzanneA_Above_SlabA(self):
        # distance min 1.0156 : tolerance 1.1 necessaire, 1.0 insuffisante.
        #@todo, rule or test not working
        self._assert_count("SuzanneA_Above_SlabA.ifc", Above,
                           "SlabA", "SuzanneA", 1,
                           above_type="Above_MaxToMin", tolerance=1.1)
        self._assert_count("SuzanneA_Above_SlabA.ifc", Above,
                           "SlabA", "SuzanneA", 0,
                           above_type="Above_MaxToMin", tolerance=1.0)

    def test_SuzanneA_Above_UshapeA(self):
        # distance min 0.2156.
        #@todo, rule or test not working
        self._assert_count("SuzanneA_Above_UshapeA.ifc", Above,
                           "UshapeA", "SuzanneA", 1,
                           above_type="Above_MaxToMin", tolerance=0.3)
        self._assert_count("SuzanneA_Above_UshapeA.ifc", Above,
                           "UshapeA", "SuzanneA", 0,
                           above_type="Above_MaxToMin", tolerance=0.2)

    def test_SuzanneB_Above_SuzanneA(self):
        # distance min 0.2118.
        #@todo, rule or test not working
        self._assert_count("SuzanneB_Above_SuzanneA.ifc", Above,
                           "SuzanneA", "SuzanneB", 1,
                           above_type="Above_MaxToMin", tolerance=0.3)
        self._assert_count("SuzanneB_Above_SuzanneA.ifc", Above,
                           "SuzanneA", "SuzanneB", 0,
                           above_type="Above_MaxToMin", tolerance=0.2)

    def test_CubeB_NotAbove_UshapeA(self):
        # [attendu] CubeB est dans l'ouverture du U, PAS au-dessus de UshapeA : 0.
        # NB [calibre, ordre inverse] : OBB_Above(CubeB, UshapeA, 0.1) = 1
        # (UshapeA entoure bien CubeB vers le haut) - la relation "au-dessus
        # de" est ici vraie dans l'autre sens, ce que le nom du modele nie.
        self._assert_count("CubeB_NotAbove_UshapeA.ifc", Above,
                           "UshapeA", "CubeB", 0,
                           above_type="Above_MaxToMin", tolerance=0.1)
        self._assert_count("CubeB_NotAbove_UshapeA.ifc", Above,
                           "UshapeA", "CubeB", 0,
                           above_type="Above_MaxToMin", tolerance=3)

    def test_SuzanneA_NotAbove_UshapeA(self):
        # [attendu] SuzanneA chevauche la plaque du U (distance 0.0156),
        # elle n'est pas au-dessus : 0.
        self._assert_count("SuzanneA_NotAbove_UshapeA.ifc", Above,
                           "UshapeA", "SuzanneA", 0,
                           above_type="Above_MaxToMin", tolerance=0.1)
        self._assert_count("SuzanneA_NotAbove_UshapeA.ifc", Above,
                           "UshapeA", "SuzanneA", 0,
                           above_type="Above_MaxToMin", tolerance=3)

    def test_SuzanneA_NotFullyAbove_SlabA(self):
        # [attendu] "pas completement au-dessus" : la verification stricte
        # face haute de la source / face basse de la cible doit echouer.
        #@todo, rule or test not working, expand the rule with Min_To_max,etc...
        #The first part that is above the slab is at 1.515 above the slab around the edge.
        
        self._assert_count("SuzanneA_NotFullyAbove_SlabA.ifc", Above,
                           "SlabA", "SuzanneA", 0,
                           above_type="Above_MaxToMin", tolerance=1.1)
        self._assert_count("SuzanneA_NotFullyAbove_SlabA.ifc", Above,
                           "SlabA", "SuzanneA", 1,
                           above_type="Above_MaxToMin", tolerance=1.52)


    def test_CubeB_NorFrontNorAbove_45CuboidA(self):
        # [attendu] ni devant ni au-dessus : 0 meme avec une large tolerance.
        self._assert_count("CubeB_NorFrontNorAbove_45CuboidA.ifc", Above,
                           "45CuboidA", "CubeB", 0,
                           above_type="Above_MaxToMin", tolerance=2.0)


class TestBelow(IFCModelRuleTestCase):
    """Regle Below (face-based) en ordre semantique : la CIBLE est au-dessous de la SOURCE.

    [attendu] tests non executes a l'ecriture.
    """

    def test_CubeA_Below_CubeB_1m(self):
        # CubeA (z -0.5-0.5) est en dessous de CubeB (z 1.5-2.5), ecart 1.0m.
        self._assert_count("CubeA_Below_CubeB_1m.ifc", Below,
                           "CubeB", "CubeA", 1,
                           below_type="Below_MinToMax", tolerance=1.0)
        self._assert_count("CubeA_Below_CubeB_1m.ifc", Below,
                           "CubeB", "CubeA", 0,
                           below_type="Below_MinToMax", tolerance=0.1)

    def test_CubeB_Below_45CuboidA(self):
        # distance min 0.5914 ; tolerance 1.0 pour couvrir l'ecart.
        self._assert_count("CubeB_Below_45CuboidA.ifc", Below,
                           "45CuboidA", "CubeB", 1,
                           below_type="Below_MinToMax", tolerance=1.0)
                           

    def test_SuzanneA_Below_SlabA(self):
        # distance min 0.9156 : tolerance 1.0.
        #@todo, rule or not working,
        self._assert_count("SuzanneA_Below_SlabA.ifc", Below,
                           "SlabA", "SuzanneA", 1,
                           below_type="Below_MinToMax", tolerance=1.0)

    def test_SuzanneA_NotFullyBelow_SlabA(self):
        #@todo, rule or test not working,
        self._assert_count("SuzanneA_NotFullyBelow_SlabA.ifc", Below,
                           "SlabA", "SuzanneA", 1,
                           below_type="Below_MinToMax", tolerance=0.95)
        self._assert_count("SuzanneA_NotFullyBelow_SlabA.ifc", Below,
                           "SlabA", "SuzanneA", 0,
                           below_type="Below_MinToMax", tolerance=0.8)

        self._assert_count("SuzanneA_NotFullyBelow_SlabA.ifc", Below,
                           "SlabA", "SuzanneA", 0,
                           below_type="Below_MinToMin", tolerance=2.3)
        self._assert_count("SuzanneA_NotFullyBelow_SlabA.ifc", Below,
                           "SlabA", "SuzanneA", 1,
                           below_type="Below_MinToMin", tolerance=2.4)


class TestOBB_Above(IFCModelRuleTestCase):
    """Regle OBB_Above en ordre semantique : zone d'extrusion AU-DESSUS de la source.

    [attendu] sauf mention contraire, tests non executes a l'ecriture.
    """

    def test_CubeA_Above_CubeB_1m(self):
        # zone extrudee de 1.0 au-dessus de CubeB : CubeB top z=0.5 -> zone jusqu'a 1.5,
        # CubeA commence a z=1.5. Tolerance 1.0 pour couvrir, 0.1 trop court.
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
        # distance min 1.0156.
        #@todo Rule is not working. This rule is OBB, should we give a precision value ?
        self._assert_count("SuzanneA_Above_SlabA.ifc", OBB_Above,
                           "SlabA", "SuzanneA", 1, tolerance=1.2)
        self._assert_count("SuzanneA_Above_SlabA.ifc", OBB_Above,
                           "SlabA", "SuzanneA", 0, tolerance=1.0)

    def test_SuzanneA_Above_UshapeA(self):
        # distance min 0.2156.
        self._assert_count("SuzanneA_Above_UshapeA.ifc", OBB_Above,
                           "UshapeA", "SuzanneA", 1, tolerance=0.3)

    def test_SuzanneB_Above_SuzanneA(self):
        # distance min 0.2118.
        self._assert_count("SuzanneB_Above_SuzanneA.ifc", OBB_Above,
                           "SuzanneA", "SuzanneB", 1, tolerance=0.3)

    def test_CubeB_NotAbove_UshapeA(self):
        # [attendu] CubeB n'est pas au-dessus de UshapeA : 0 en ordre semantique.
        # NB [calibre, ordre inverse] : OBB_Above(CubeB, UshapeA, 0.1) = 1,
        # car UshapeA est bien "au-dessus de" CubeB (le U l'entoure).
        self._assert_count("CubeB_NotAbove_UshapeA.ifc", OBB_Above,
                           "UshapeA", "CubeB", 0, tolerance=0.1)
        self._assert_count("CubeB_NotAbove_UshapeA.ifc", OBB_Above,
                           "UshapeA", "CubeB", 0, tolerance=3)

    def test_SuzanneA_NotAbove_UshapeA(self):
        # [attendu] idem : 0 en ordre semantique.
        self._assert_count("SuzanneA_NotAbove_UshapeA.ifc", OBB_Above,
                           "UshapeA", "SuzanneA", 0, tolerance=0.1)
        self._assert_count("SuzanneA_NotAbove_UshapeA.ifc", OBB_Above,
                           "UshapeA", "SuzanneA", 0, tolerance=3)

    def test_SuzanneA_NotFullyAbove_SlabA(self):
        # [attendu] illustration de la difference OBB / face-based : la zone
        # OBB extrudee au-dessus de SlabA couvre une partie de SuzanneA
        # (chevauchement partiel), donc 1, alors que la verification stricte
        # Above retourne 0 (voir TestAbove.test_SuzanneA_NotFullyAbove_SlabA).
        #@todo Rule is not working, what should be the precision of OBB ?
        self._assert_count("SuzanneA_NotFullyAbove_SlabA.ifc", OBB_Above,
                           "SlabA", "SuzanneA", 1, tolerance=1.1)
        
        self._assert_count("SuzanneA_NotFullyAbove_SlabA.ifc", OBB_Above,
                           "SlabA", "SuzanneA", 0,
                           above_type="Above_MaxToMin", tolerance=1.1)
        self._assert_count("SuzanneA_NotFullyAbove_SlabA.ifc", OBB_Above,
                           "SlabA", "SuzanneA", 1,
                           above_type="Above_MaxToMin", tolerance=1.52)

    def test_CubeB_NorFrontNorAbove_45CuboidA(self):
        # [attendu] ni devant ni au-dessus : 0 meme avec une large tolerance.
        self._assert_count("CubeB_NorFrontNorAbove_45CuboidA.ifc", OBB_Above,
                           "45CuboidA", "CubeB", 0, tolerance=2.0)


class TestOBB_Below(IFCModelRuleTestCase):
    """Regle OBB_Below en ordre semantique : zone d'extrusion EN-DESSOUS de la source.

    [attendu] tests non executes a l'ecriture.
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
        # distance min 0.9156.
        self._assert_count("SuzanneA_Below_SlabA.ifc", OBB_Below,
                           "SlabA", "SuzanneA", 1, tolerance=1.0)

    def test_SuzanneA_NotFullyBelow_SlabA(self):
        # [attendu] illustration miroir de la detection partielle OBB
        # (voir TestOBB_Above.test_SuzanneA_NotFullyAbove_SlabA).
        self._assert_count("SuzanneA_NotFullyBelow_SlabA.ifc", OBB_Below,
                           "SlabA", "SuzanneA", 1, tolerance=1.0)


class TestOBB_Front_And_Back(IFCModelRuleTestCase):
    """Regle OBB_Front_And_Back : zones extrudees le long des deux directions
    principales de l'OBB de la source ; la cible doit toucher une zone.

    Marqueurs : [calibre] = compte observe (ordre du nom de fichier, la ou il
    coincide avec l'ordre semantique ou que la regle est quasi symetrique) ;
    [attendu] = non execute a l'ecriture.
    """

    def test_CubeB_InFront_45CuboidA(self):
        # [calibre ordre du nom, tol 1.0 : 1 pour Wide et Narrow]
        # CubeB est devant 45CuboidA le long de son axe principal -> ordre
        # semantique : source=45CuboidA, target=CubeB, meme resultat attendu.
        #@todo Rule not working, what precision for OBB ?
        self._assert_count("CubeB_InFront_45CuboidA.ifc", OBB_Front_And_Back,
                           "45CuboidA", "CubeB", 1, tolerance=1.0, method="Wide")
        self._assert_count("CubeB_InFront_45CuboidA.ifc", OBB_Front_And_Back,
                           "45CuboidA", "CubeB", 0, tolerance=0.1, method="Wide")

    def test_CubeB_InFrontOf_CuboidA_50cm(self):
        # [calibre ordre du nom : tol 1.0 -> 1, tol 0.5 -> 0]
        # ordre semantique : source=CuboidA (CubeB est devant lui).
        self._assert_count("CubeB_InFrontOf_CuboidA_50cm.ifc", OBB_Front_And_Back,
                           "CuboidA", "CubeB", 1, tolerance=1.0, method="Wide")
        self._assert_count("CubeB_InFrontOf_CuboidA_50cm.ifc", OBB_Front_And_Back,
                           "CuboidA", "CubeB", 0, tolerance=0.5, method="Wide")

    def test_SuzanneA_InFrontOf_CuboidA_146cm(self):
        # [attendu] distance min 1.4601 : tolerance 2.0 pour que la zone
        # atteigne SuzanneA. (Ordre du nom calibre : 0 jusqu'a tol 1.5.)
        self._assert_count("SuzanneA_InFrontOf_CuboidA_146cm.ifc", OBB_Front_And_Back,
                           "CuboidA", "SuzanneA", 1, tolerance=1.47, method="Wide")
        self._assert_count("SuzanneA_InFrontOf_CuboidA_146cm.ifc", OBB_Front_And_Back,
                           "CuboidA", "SuzanneA", 0, tolerance=1.45, method="Wide")

    def test_SuzanneB_Behind_SuzanneA(self):
        # [calibre] l'ordre du nom EST l'ordre semantique ici : SuzanneA est
        # devant SuzanneB. Wide -> 1 des tolerance 0.1 ; Narrow -> 0.
        self._assert_count("SuzanneB_Behind_SuzanneA.ifc", OBB_Front_And_Back,
                           "SuzanneB", "SuzanneA", 1, tolerance=0.1, method="Wide")
        self._assert_count("SuzanneB_Behind_SuzanneA.ifc", OBB_Front_And_Back,
                           "SuzanneB", "SuzanneA", 0, tolerance=0.1, method="Narrow")

    def test_CubeB_Side_45CuboidA(self):
        # [calibre ordre du nom : Wide tol 1.0 -> 1] un placement "de cote"
        # reste couvert par la zone de la seconde direction principale de
        # l'OBB -> 1 en ordre semantique egalement.
        #@Test not working, make more rule like that. Something might be wrong with the OBB shape and side select.
        self._assert_count("CubeB_Side_45CuboidA.ifc", OBB_Front_And_Back,
                           "45CuboidA", "CubeB", 1, tolerance=1.0, method="wide")


    def test_CubeB_Side_CuboidA_50cm(self):
        # [calibre ordre du nom : 0 a toutes tolerances testees <= 1.0]
        # placement lateral hors des zones front/back de CuboidA -> 0.
        self._assert_count("CubeB_Side_CuboidA_50cm.ifc", OBB_Front_And_Back,
                           "CuboidA", "CubeB", 0, tolerance=1.0, method="Wide")

    def test_CubeB_NorFrontNorAbove_45CuboidA(self):
        # [calibre ordre du nom : 0 pour Wide et Narrow] ni devant ni derriere.
        self._assert_count("CubeB_NorFrontNorAbove_45CuboidA.ifc", OBB_Front_And_Back,
                           "45CuboidA", "CubeB", 0, tolerance=1.0, method="Wide")
        self._assert_count("CubeB_NorFrontNorAbove_45CuboidA.ifc", OBB_Front_And_Back,
                           "45CuboidA", "CubeB", 0, tolerance=1.0, method="Narrow")


class TestAngleBetween(IFCModelRuleTestCase):
    """Regle AngleBetween sur les maquettes Orient / NoOrient.

    Angles reels mesures (directions principales des OBB, methode Wide/Narrow) :
      - CuboidA_Orient_45Cuboid_45    : Wide-Narrow 45deg, Wide-Wide 135deg,
                                        Narrow-Wide 90deg, Narrow-Narrow 90deg ;
      - CuboidA_NoOrient_45Cuboid     : Wide-Wide/Wide-Narrow 75.2deg,
                                        Narrow-Wide/Narrow-Narrow 131.2deg ;
      - CuboidA_Orient_FallenCuboidA_90 : Wide-Wide 90deg, Wide-Narrow 0deg,
                                        Narrow-Wide 0deg, Narrow-Narrow 90deg.
    """

    def test_CuboidA_Orient_FallenCuboidA_90(self):
        # [calibre] angle nominal 90deg entre directions Wide.
        self._assert_count("CuboidA_Orient_FallenCuboidA_90.ifc", AngleBetween,
                           "CuboidA", "FallenCuboidA", 1,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Wide",
                           angle_difference=90, angle_tolerance=5)
        # [calibre] directions croisees : 0deg entre Wide de CuboidA et Narrow de FallenCuboidA.
        self._assert_count("CuboidA_Orient_FallenCuboidA_90.ifc", AngleBetween,
                           "CuboidA", "FallenCuboidA", 1,
                           direction_method_for_source="Wide",
                           direction_method_for_target="Narrow",
                           angle_difference=0, angle_tolerance=5)
        # [calibre] contre-exemples : ni 0deg ni 45deg entre directions Wide-Wide.
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
        # [attendu, angles mesures] cible reelle 45CuboidA (voir NAME_OVERRIDES).
        # L'angle nominal 45deg est entre Wide de CuboidA et Narrow de 45CuboidA.
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
        # [attendu, angles mesures] aucun couple de directions ne fait
        # 0, 45 ni 90 degre (75.2 / 131.2) : toutes ces recherches echouent.
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
    """Regles documentees mais absentes de ifcclash_plus/Rules.py."""

    def test_Inside_rule_not_implemented(self):
        # Les maquettes CubeA_Inside_BigCubeA, CubeB_Inside_BigCubeA,
        # CubeA_InsideFaceTouch_BigCubeA et CubeA_TouchOutside_BigCubeA_1mm
        # sont couvertes via Intersection/Collision/Clearance (voir classes
        # precedentes) ; la regle Inside n'existe que dans doc/2ObjectsRules/Inside.
        self.skipTest(
            "Regle Inside documentee (doc/2ObjectsRules/Inside) mais non "
            "implementee dans ifcclash_plus/Rules.py."
        )

    def test_SurfaceRecover_not_implemented(self):
        # Maquettes SlabA_RecoverTop_CuboidB_100%/50% et
        # SlabA_RecoverTop_CylinderA_100%/50%.
        self.skipTest(
            "Regle SurfaceRecover documentee (doc/2ObjectsRules/SurfaceRecover.md) "
            "mais non implementee dans ifcclash_plus/Rules.py."
        )


if __name__ == "__main__":
    unittest.main()
