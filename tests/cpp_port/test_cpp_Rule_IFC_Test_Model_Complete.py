# COPY of tests/test_Rule_IFC_Test_Model_Complete.py (all the classes), generated on 2026-11-09 (SPEC_OptimisationInCPP).
#
# Same tests, same models, same expected values as the original, but every
# rule runs on the C++ engine: IFCCLASH_ENGINE=cpp forces the backend and
# forbids the silent fallback on Python (orchestrator.compute_rule). The
# original stays the reference of the Python engine; this copy is frozen on
# purpose, so that a change of the original cannot hide a regression of the
# port. Skipped when the C++ module is not built for the running Python.
#
# Execution (repository root, ifcclash_cpp environment, one file at a time):
#     PYTHONNOUSERSITE=1 python -m pytest tests/cpp_port/test_cpp_Rule_IFC_Test_Model_Complete.py -v
import os

os.environ["IFCCLASH_ENGINE"] = "cpp"

import pytest  # noqa: E402

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ifcclash_plus"))

from Rules import (  # noqa: E402
    Alignement,
    Above,
    Below,
    Clearance,
    ClearanceAxisToAxis,
    ClearanceForDoors,
    Collision,
    DirectView,
    FreeSpace,
    OBB_Below,
    OBB_Custom,
    Ray_Check,
    SurfaceRecover,
    TwoObjectsFace,
)
from RuleClass import RuleFile, SelectFacet  # noqa: E402
from ifctester import ids  # noqa: E402
from tests.test_structure_ResultShape import assert_result_shape  # noqa: E402

MODEL_DIR = "IFC_Test_Model/IFC_Model"


def _sel(name):
    s = SelectFacet()
    s.applicability = [ids.Attribute(name="Name", value=name)]
    return s


def _sel_entity(entity):
    s = SelectFacet()
    s.applicability = [ids.Entity(name=entity)]
    return s


_SEL_EMPTY = SelectFacet()

from engine.backends import cpp_backend  # noqa: E402

pytestmark = pytest.mark.skipif(
    not cpp_backend.AVAILABLE, reason="the C++ module _ifcclash_engine is not built for this Python"
)


class CompleteTestCase(unittest.TestCase):
    """Lance une règle (avec ou sans contexte) sur une paire d'un modèle."""

    def _run(self, model, rule):
        rf = RuleFile()
        rf.list_ifc_path = [os.path.join(MODEL_DIR, model + ".ifc")]
        rf.contains = [rule]
        rf.run()
        assert_result_shape(rf)
        return rule

    def _assert(self, model, rule, expected):
        rule = self._run(model, rule)
        self.assertEqual(
            len(rule.result), expected,
            msg=f"{model}: {rule.type} -> {len(rule.result)}, {expected} attendu",
        )


# ---------------------------------------------------------------------------
# 1. Les 4 variantes above_type / below_type sur modèles existants
# ---------------------------------------------------------------------------

class TestAboveBelowTypes(CompleteTestCase):
    """Sémantique [calibrated] : MaxToMin = 'cible au-dessus de la source'
    (gap > 0) ; MinToMin / MaxToMax = contact ou chevauchement des mêmes
    extrémités (gap <= 0) ; MinToMax ne détecte rien ici."""

    def test_above_gap_1m(self):
        m = "CubeA_Above_CubeB_1m"
        self._assert(m, Above(_sel("CubeB"), _sel("CubeA"),
                              above_type="Above_MaxToMin", tolerance=1.0), 1)
        for t in ("Above_MinToMax", "Above_MinToMin", "Above_MaxToMax"):
            self._assert(m, Above(_sel("CubeB"), _sel("CubeA"),
                                  above_type=t, tolerance=1.0), 0)
        # sens inverse : jamais above
        for t in ("Above_MaxToMin", "Above_MinToMax", "Above_MinToMin", "Above_MaxToMax"):
            self._assert(m, Above(_sel("CubeA"), _sel("CubeB"),
                                  above_type=t, tolerance=1.0), 0)

    def test_below_gap_1m(self):
        m = "CubeA_Below_CubeB_1m"
        self._assert(m, Below(_sel("CubeB"), _sel("CubeA"),
                              below_type="Below_MinToMax", tolerance=1.0), 1)
        for t in ("Below_MaxToMin", "Below_MinToMin", "Below_MaxToMax"):
            self._assert(m, Below(_sel("CubeB"), _sel("CubeA"),
                                  below_type=t, tolerance=1.0), 0)

    def test_above_contact_face(self):
        # gap 0 : MinToMin et MaxToMax détectent le contact, MaxToMin non
        m = "CubeA_TouchFace_CubeB"
        self._assert(m, Above(_sel("CubeB"), _sel("CubeA"),
                              above_type="Above_MinToMin", tolerance=0.1), 1)
        self._assert(m, Above(_sel("CubeB"), _sel("CubeA"),
                              above_type="Above_MaxToMax", tolerance=0.1), 1)
        self._assert(m, Above(_sel("CubeB"), _sel("CubeA"),
                              above_type="Above_MaxToMin", tolerance=0.1), 0)
        self._assert(m, Above(_sel("CubeB"), _sel("CubeA"),
                              above_type="Above_MinToMax", tolerance=0.1), 0)

    def test_above_intersection_10cm(self):
        # faces qui se chevauchent : aucun type ne détecte à tol 0.5
        m = "CubeA_Intersect_CubeB_10cm"
        for t in ("Above_MaxToMin", "Above_MinToMax", "Above_MinToMin", "Above_MaxToMax"):
            self._assert(m, Above(_sel("CubeB"), _sel("CubeA"),
                                  above_type=t, tolerance=0.5), 0)

    def test_above_z_overlap(self):
        # dalles en ZOverlap : MinToMin/MaxToMax voient le chevauchement (SlabA->SlabB)
        m = "SlabA_ZOverlap_SlabB"
        self._assert(m, Above(_sel("SlabA"), _sel("SlabB"),
                              above_type="Above_MinToMin", tolerance=0.1), 1)
        self._assert(m, Above(_sel("SlabA"), _sel("SlabB"),
                              above_type="Above_MaxToMax", tolerance=0.1), 1)
        self._assert(m, Above(_sel("SlabA"), _sel("SlabB"),
                              above_type="Above_MaxToMin", tolerance=0.1), 0)
        self._assert(m, Above(_sel("SlabB"), _sel("SlabA"),
                              above_type="Above_MinToMin", tolerance=0.1), 0)


# ---------------------------------------------------------------------------
# 2. Règles avec contexte : DirectView, Ray_Check, FreeSpace
# ---------------------------------------------------------------------------

class TestContextRules(CompleteTestCase):
    def test_direct_view_libre(self):
        m = "CubeA_DirectView_CubeB"
        self._assert(m, DirectView(_sel("CubeA"), _sel("CubeB"), _sel("BigCubeA"),
                                   ray_source="Both", ray_count=10, threshold="100%"), 1)
        self._assert(m, DirectView(_sel("CubeA"), _sel("CubeB"), _SEL_EMPTY,
                                   ray_source="Both", ray_count=10, threshold="100%"), 1)

    def test_direct_view_bloquee(self):
        m = "CubeA_BlockedView_WallA_CubeB"
        self._assert(m, DirectView(_sel("CubeA"), _sel("CubeB"), _sel("WallA"),
                                   ray_source="Both", ray_count=10, threshold="100%"), 0)

    def test_ray_check(self):
        m = "CubeA_DirectView_CubeB"
        # rayon atteint la cible (3m < max 5m), rien entre -> 1
        self._assert(m, Ray_Check(_sel("CubeA"), _sel("CubeB"), _SEL_EMPTY, 5.0), 1)
        m = "CubeA_BlockedView_WallA_CubeB"
        self._assert(m, Ray_Check(_sel("CubeA"), _sel("CubeB"), _sel("WallA"), 5.0), 0)
        # max_ray_length trop court (2m < 3m) -> le rayon n'atteint pas -> 0
        self._assert(m, Ray_Check(_sel("CubeA"), _sel("CubeB"), _sel("WallA"), 2.0), 0)

    def test_free_space(self):
        m = "CubeA_FreeSpace_Clear"
        self._assert(m, FreeSpace(_sel("CubeA"), _SEL_EMPTY, diameter=1.5, height=2.0), 1)
        m = "CubeA_FreeSpace_Blocked_CubeB_50cm"
        # sonde d=1.5 ou d=2.0 : CubeB a 50cm entre dans la zone -> 1
        self._assert(m, FreeSpace(_sel("CubeA"), _sel("CubeB"), diameter=1.5, height=2.0), 1)
        self._assert(m, FreeSpace(_sel("CubeA"), _sel("CubeB"), diameter=2.0, height=3.0), 1)
        # sonde d=0.4 : trop petite -> 0
        self._assert(m, FreeSpace(_sel("CubeA"), _sel("CubeB"), diameter=0.4, height=2.0), 0)


# ---------------------------------------------------------------------------
# 3. Règles 2-objets sans modèle dédié
# ---------------------------------------------------------------------------

class TestSpecializedRules(CompleteTestCase):
    def test_clearance_axis_to_axis_parallel(self):
        m = "BeamLongA_AxisParallel_BeamLongB_50cm"
        # distance axe-a-axe ~0.5m : dans [0, 0.4] -> 1, dans [0, 1] -> 0
        # (bornes [calibrated], sémantique à confirmer côté règle)
        self._assert(m, ClearanceAxisToAxis(_sel("BeamLongA"), _sel("BeamLongB"),
                                            mode="Perpendicular",
                                            min_distance=0.0, max_distance=0.4), 1)
        self._assert(m, ClearanceAxisToAxis(_sel("BeamLongA"), _sel("BeamLongB"),
                                            mode="Perpendicular",
                                            min_distance=0.0, max_distance=1.0), 0)
        self._assert(m, ClearanceAxisToAxis(_sel("BeamLongA"), _sel("BeamLongB"),
                                            mode="MinDistance",
                                            min_distance=0.0, max_distance=0.4), 1)

    def test_clearance_axis_to_axis_perp(self):
        # axes perpendiculaires qui se croisent : aucun mode ne flagge
        m = "BeamLongA_AxisPerp_CuboidB"
        self._assert(m, ClearanceAxisToAxis(_sel("BeamLongA"), _sel("CuboidB"),
                                            mode="Perpendicular",
                                            min_distance=0.0, max_distance=1.0), 0)
        self._assert(m, ClearanceAxisToAxis(_sel("BeamLongA"), _sel("CuboidB"),
                                            mode="MinDistance",
                                            min_distance=0.0, max_distance=1.0), 0)

    def test_clearance_for_doors(self):
        # cube a ~50cm devant la porte, zone depth 1m -> bloque (1)
        m = "DoorA_ClearanceBlocked_CubeB_50cm"
        self._assert(m, ClearanceForDoors(_sel("DoorA"), _sel("CubeB"),
                                          zone_shape="Rectangle", sides="Both",
                                          width=0.9, depth=1.0, height=2.1), 1)
        # zone depth 0.3m : le cube est hors zone -> 0
        self._assert(m, ClearanceForDoors(_sel("DoorA"), _sel("CubeB"),
                                          zone_shape="Rectangle", sides="Both",
                                          width=0.9, depth=0.3, height=2.1), 0)
        # cube a 2.5m, zone depth 1m -> libre (0) ; depth 2.5m -> dans la zone (1)
        m = "DoorA_ClearanceFree_CubeB_2m"
        self._assert(m, ClearanceForDoors(_sel("DoorA"), _sel("CubeB"),
                                          zone_shape="Rectangle", sides="Both",
                                          width=0.9, depth=1.0, height=2.1), 0)
        self._assert(m, ClearanceForDoors(_sel("DoorA"), _sel("CubeB"),
                                          zone_shape="Rectangle", sides="Both",
                                          width=0.9, depth=2.5, height=2.1), 1)

    def test_two_objects_face_parallel(self):
        m = "CubeA_FaceParallel_CubeB_1m"
        # 120 paires de faces avec angle 0 (parallèles), 48 avec 90deg
        self._assert(m, TwoObjectsFace(_sel("CubeA"), _sel("CubeB"),
                                       orientation=True, angle=0.0,
                                       angle_tolerance=5.0), 120)
        self._assert(m, TwoObjectsFace(_sel("CubeA"), _sel("CubeB"),
                                       orientation=True, angle=90.0,
                                       angle_tolerance=5.0), 48)

    def test_two_objects_face_perp(self):
        m = "CubeA_FacePerp_FallenCuboidA"
        self._assert(m, TwoObjectsFace(_sel("CubeA"), _sel("FallenCuboidA"),
                                       orientation=True, angle=90.0,
                                       angle_tolerance=15.0), 48)
        self._assert(m, TwoObjectsFace(_sel("CubeA"), _sel("FallenCuboidA"),
                                       orientation=True, angle=0.0,
                                       angle_tolerance=15.0), 120)

    def test_obb_custom(self):
        m = "CubeA_CustomZoneAbove_CubeB_2m"
        self._assert(m, OBB_Custom(_sel("CubeA"), _sel("CubeB"),
                                   ["detach_top_by_extrude:100%"]), 1)
        self._assert(m, OBB_Custom(_sel("CubeA"), _sel("CubeB"),
                                   ["detach_top_by_extrude:10%"]), 0)
        self._assert(m, OBB_Custom(_sel("CubeA"), _sel("CubeB"),
                                   ["detach_bottom_by_extrude:100%"]), 0)
        m = "CubeA_CustomZoneBelow_CubeB_2m"
        self._assert(m, OBB_Custom(_sel("CubeA"), _sel("CubeB"),
                                   ["detach_bottom_by_extrude:100%"]), 1)
        self._assert(m, OBB_Custom(_sel("CubeA"), _sel("CubeB"),
                                   ["detach_top_by_extrude:100%"]), 0)

    def test_alignement(self):
        # [calibrated] 4 groupes dans les deux modèles (les IfcFan par défaut
        # sont aussi alignés en Y=0 : le cas ne les isole pas complètement)
        for m in ("CubeA_CubeB_CuboidB_AlignedX", "CubeA_CubeB_CuboidB_NotAligned"):
            self._assert(m, Alignement(_sel_entity("IFCFAN"), axis="Horizontal",
                                       alignment_type="Plane", tolerance=0.1,
                                       min_group=3), 4)


# ---------------------------------------------------------------------------
# 4. Positions manquantes
# ---------------------------------------------------------------------------

class TestMissingPositions(CompleteTestCase):
    def test_recover_bottom(self):
        # SlabB sous SlabA, recouvrement 50% de la face bottom : dir='Bottom' -> 1
        m = "SlabA_RecoverBottom_SlabB_50%"
        self._assert(m, SurfaceRecover(_sel("SlabA"), _sel("SlabB"), direction="Bottom",
                                       min_covering=0.4, max_covering=0.6), 1)
        self._assert(m, SurfaceRecover(_sel("SlabA"), _sel("SlabB"), direction=(0, 0, -1),
                                       min_covering=0.0, max_covering=1.0), 1)
        # Auto/Top ne voient pas le dessous -> 0
        self._assert(m, SurfaceRecover(_sel("SlabA"), _sel("SlabB"), direction="Auto",
                                       min_covering=0.0, max_covering=1.0), 0)
        self._assert(m, SurfaceRecover(_sel("SlabA"), _sel("SlabB"), direction="Top",
                                       min_covering=0.0, max_covering=1.0), 0)

    def test_recover_side_contact_pur(self):
        # contact latéral pur (CuboidB contre le côté +X) : pas de recouvrement
        # détecté -> 0 même en 0-100%
        m = "SlabA_RecoverSide_CuboidB"
        self._assert(m, SurfaceRecover(_sel("SlabA"), _sel("CuboidB"), direction=(1, 0, 0),
                                       min_covering=0.0, max_covering=1.0), 0)

    def test_touch_inside_hollow_cylinder(self):
        # cylindre r=0.79 décalé de 11mm -> pénètre la paroi intérieure (r=0.8) de 1mm
        m = "CylinderSmallA_TouchInside_HollowCylinderA"
        self._assert(m, Collision(_sel("CylinderSmallA"), _sel("HollowCylinderA"),
                                  allow_touching=True), 1)
        self._assert(m, Collision(_sel("CylinderSmallA"), _sel("HollowCylinderA")), 1)
        self._assert(m, Clearance(_sel("CylinderSmallA"), _sel("HollowCylinderA"),
                                  clearance=0.001), 1)

    def test_below_ushape(self):
        # CubeB à 10cm sous le fond du U : Below tol 0.2 -> 1, tol 0.05 -> 0 (borne excl.)
        m = "CubeB_Below_UshapeA_50cm"
        self._assert(m, Below(_sel("UshapeA"), _sel("CubeB"),
                              below_type="Below_MinToMax", tolerance=0.2), 1)
        self._assert(m, Below(_sel("UshapeA"), _sel("CubeB"),
                              below_type="Below_MinToMax", tolerance=0.05), 0)
        self._assert(m, OBB_Below(_sel("UshapeA"), _sel("CubeB"), tolerance=0.2), 1)
        self._assert(m, Collision(_sel("CubeB"), _sel("UshapeA")), 0)


if __name__ == "__main__":
    unittest.main()
