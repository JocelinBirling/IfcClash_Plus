# COPY of tests/test_Rule_IFC_Test_Model_OneObject.py (all the classes), generated on 2026-11-09 (SPEC_OptimisationInCPP).
#
# Same tests, same models, same expected values as the original, but every
# rule runs on the C++ engine: IFCCLASH_ENGINE=cpp forces the backend and
# forbids the silent fallback on Python (orchestrator.compute_rule). The
# original stays the reference of the Python engine; this copy is frozen on
# purpose, so that a change of the original cannot hide a regression of the
# port. Skipped when the C++ module is not built for the running Python.
#
# Execution (repository root, ifcclash_cpp environment, one file at a time):
#     PYTHONNOUSERSITE=1 python -m pytest tests/cpp_port/test_cpp_Rule_IFC_Test_Model_OneObject.py -v
import os

os.environ["IFCCLASH_ENGINE"] = "cpp"

import pytest  # noqa: E402

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ifcclash_plus"))

from Rules import (  # noqa: E402
    Area,
    ObbHigh,
    ObbLength,
    OneObjectFace,
    Orientation,
    LateralSurface,
    ProjectedSurface,
    TopOrBottomSurface,
    Volume,
)
from RuleClass import RuleFile, SelectFacet  # noqa: E402
from ifctester import ids  # noqa: E402
from tests.test_structure_ResultShape import assert_result_shape  # noqa: E402

MODEL_DIR = "IFC_Test_Model/IFC_Model"
CUBE_MODEL = "CubeA_Above_CubeB_1m"
SUZ_MODEL = "SuzanneA_Above_SlabA"


def _sel(name):
    s = SelectFacet()
    s.applicability = [ids.Attribute(name="Name", value=name)]
    return s

from engine.backends import cpp_backend  # noqa: E402

pytestmark = pytest.mark.skipif(
    not cpp_backend.AVAILABLE, reason="the C++ module _ifcclash_engine is not built for this Python"
)


class OneObjectTestCase(unittest.TestCase):
    def _run(self, model, obj, rule):
        rf = RuleFile()
        rf.list_ifc_path = [os.path.join(MODEL_DIR, model + ".ifc")]
        rf.contains = [rule]
        rf.run()
        assert_result_shape(rf)
        return rule

    def _count(self, model, obj, rule, expected):
        rule = self._run(model, obj, rule)
        self.assertEqual(
            len(rule.result), expected,
            msg=f"{model}/{obj}: {rule.type} -> {len(rule.result)}, {expected} attendu",
        )
        return rule

    def _value(self, model, obj, rule, attr):
        """Lance la règle et retourne la valeur mesurée dans info (1 résultat attendu)."""
        rule = self._run(model, obj, rule)
        self.assertEqual(len(rule.result), 1, msg=f"{model}/{obj}: {rule.type}")
        return float(getattr(rule.result[0].info, attr))


class TestVolume(OneObjectTestCase):
    def test_cube(self):
        self._count(CUBE_MODEL, "CubeA", Volume(_sel("CubeA"), 0.5, 1.5), 1)
        self._count(CUBE_MODEL, "CubeA", Volume(_sel("CubeA"), 0.0, 0.5), 0)
        v = self._value(CUBE_MODEL, "CubeA", Volume(_sel("CubeA"), 0.0, 100.0), "volume")
        self.assertAlmostEqual(v, 1.0, delta=0.05)

    def test_suzanne(self):
        # volume mesuré de Suzanne : 0.593 m3
        self._count(SUZ_MODEL, "SuzanneA", Volume(_sel("SuzanneA"), 0.5, 1.5), 1)
        self._count(SUZ_MODEL, "SuzanneA", Volume(_sel("SuzanneA"), 0.0, 0.5), 0)
        v = self._value(SUZ_MODEL, "SuzanneA", Volume(_sel("SuzanneA"), 0.0, 100.0), "volume")
        self.assertAlmostEqual(v, 0.593, delta=0.02)


class TestArea(OneObjectTestCase):
    def test_cube(self):
        self._count(CUBE_MODEL, "CubeA", Area(_sel("CubeA"), 5.5, 6.5), 1)
        self._count(CUBE_MODEL, "CubeA", Area(_sel("CubeA"), 0.0, 5.0), 0)
        a = self._value(CUBE_MODEL, "CubeA", Area(_sel("CubeA"), 0.0, 100.0), "area")
        self.assertAlmostEqual(a, 6.0, delta=0.05)

    def test_suzanne(self):
        # aire mesurée de Suzanne : 13.92 m2
        self._count(SUZ_MODEL, "SuzanneA", Area(_sel("SuzanneA"), 13.0, 15.0), 1)
        self._count(SUZ_MODEL, "SuzanneA", Area(_sel("SuzanneA"), 0.0, 5.0), 0)
        a = self._value(SUZ_MODEL, "SuzanneA", Area(_sel("SuzanneA"), 0.0, 100.0), "area")
        self.assertAlmostEqual(a, 13.92, delta=0.1)


class TestTopOrBottomSurface(OneObjectTestCase):
    def test_cube(self):
        # face top et bottom du cube = 1 m2 chacune
        for tob in ("Top", "Bottom"):
            self._count(CUBE_MODEL, "CubeA",
                        TopOrBottomSurface(_sel("CubeA"), 0.5, 1.5, tob), 1)
            self._count(CUBE_MODEL, "CubeA",
                        TopOrBottomSurface(_sel("CubeA"), 0.0, 0.5, tob), 0)
            a = self._value(CUBE_MODEL, "CubeA",
                            TopOrBottomSurface(_sel("CubeA"), 0.0, 100.0, tob), "area")
            self.assertAlmostEqual(a, 1.0, delta=0.05)

    def test_suzanne(self):
        # Suzanne n'a pas de dessus net : top = 4.42 m2, bottom = 4.92 m2 [calibrated]
        a_top = self._value(SUZ_MODEL, "SuzanneA",
                            TopOrBottomSurface(_sel("SuzanneA"), 0.0, 100.0, "Top"), "area")
        a_bot = self._value(SUZ_MODEL, "SuzanneA",
                            TopOrBottomSurface(_sel("SuzanneA"), 0.0, 100.0, "Bottom"), "area")
        self.assertAlmostEqual(a_top, 4.42, delta=0.1)
        self.assertAlmostEqual(a_bot, 4.92, delta=0.1)
        self._count(SUZ_MODEL, "SuzanneA",
                    TopOrBottomSurface(_sel("SuzanneA"), 4.0, 5.0, "Top"), 1)
        self._count(SUZ_MODEL, "SuzanneA",
                    TopOrBottomSurface(_sel("SuzanneA"), 0.0, 4.0, "Top"), 0)


class TestLateralSurface(OneObjectTestCase):
    def test_cube(self):
        # cube : 1 face de 1 m2 visible par direction (cone 45 deg)
        for d in ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)):
            a = self._value(CUBE_MODEL, "CubeA",
                            LateralSurface(_sel("CubeA"), 0.0, 100.0, d), "area")
            self.assertAlmostEqual(a, 1.0, delta=0.05)

    def test_suzanne(self):
        a_z = self._value(SUZ_MODEL, "SuzanneA",
                          LateralSurface(_sel("SuzanneA"), 0.0, 100.0, (0.0, 0.0, 1.0)), "area")
        a_x = self._value(SUZ_MODEL, "SuzanneA",
                          LateralSurface(_sel("SuzanneA"), 0.0, 100.0, (1.0, 0.0, 0.0)), "area")
        self.assertAlmostEqual(a_z, 2.14, delta=0.05)
        self.assertAlmostEqual(a_x, 1.49, delta=0.05)


class TestProjectedSurface(OneObjectTestCase):
    def test_cube(self):
        # projection du cube = 1 m2 selon X comme selon Z
        for d in ((0.0, 0.0, 1.0), (1.0, 0.0, 0.0)):
            a = self._value(CUBE_MODEL, "CubeA",
                            ProjectedSurface(_sel("CubeA"), 0.0, 100.0, d), "area")
            self.assertAlmostEqual(a, 1.0, delta=0.05)

    def test_suzanne(self):
        a_z = self._value(SUZ_MODEL, "SuzanneA",
                          ProjectedSurface(_sel("SuzanneA"), 0.0, 100.0, (0.0, 0.0, 1.0)), "area")
        a_x = self._value(SUZ_MODEL, "SuzanneA",
                          ProjectedSurface(_sel("SuzanneA"), 0.0, 100.0, (1.0, 0.0, 0.0)), "area")
        self.assertAlmostEqual(a_z, 2.21, delta=0.05)
        self.assertAlmostEqual(a_x, 1.79, delta=0.05)


class TestObbHigh(OneObjectTestCase):
    def test_cube(self):
        # OBB du cube = 1x1x1 -> hauteur 1.0
        self._count(CUBE_MODEL, "CubeA", ObbHigh(_sel("CubeA"), 0.5, 1.5), 1)
        self._count(CUBE_MODEL, "CubeA", ObbHigh(_sel("CubeA"), 0.0, 0.5), 0)
        self._count(CUBE_MODEL, "CubeA", ObbHigh(_sel("CubeA"), 1.5, 3.0), 0)

    def test_suzanne(self):
        # hauteur OBB de Suzanne ~2.5-3.0 [calibrated]
        self._count(SUZ_MODEL, "SuzanneA", ObbHigh(_sel("SuzanneA"), 2.0, 3.0), 1)
        self._count(SUZ_MODEL, "SuzanneA", ObbHigh(_sel("SuzanneA"), 1.5, 2.5), 0)
        self._count(SUZ_MODEL, "SuzanneA", ObbHigh(_sel("SuzanneA"), 0.0, 1.0), 0)


class TestObbLength(OneObjectTestCase):
    def test_cube(self):
        # OBB 1x1x1 : Wide et Narrow = 1.0
        for meth in ("Wide", "Narrow"):
            self._count(CUBE_MODEL, "CubeA", ObbLength(_sel("CubeA"), 0.5, 1.5, meth), 1)
            self._count(CUBE_MODEL, "CubeA", ObbLength(_sel("CubeA"), 0.0, 0.5, meth), 0)

    def test_suzanne(self):
        # OBB Suzanne : Wide ~2.7, Narrow ~1.7 [calibrated]
        self._count(SUZ_MODEL, "SuzanneA", ObbLength(_sel("SuzanneA"), 2.0, 3.0, "Wide"), 1)
        self._count(SUZ_MODEL, "SuzanneA", ObbLength(_sel("SuzanneA"), 0.0, 2.0, "Wide"), 0)
        self._count(SUZ_MODEL, "SuzanneA", ObbLength(_sel("SuzanneA"), 0.0, 2.0, "Narrow"), 1)
        self._count(SUZ_MODEL, "SuzanneA", ObbLength(_sel("SuzanneA"), 2.0, 3.0, "Narrow"), 0)


class TestOrientation(OneObjectTestCase):
    def test_cube(self):
        # le cube a un axe OBB parallele a Z et un parallele a X
        self._count(CUBE_MODEL, "CubeA",
                    Orientation(_sel("CubeA"), (0, 0, 1), "Parrallel", "Wide", 5.0), 1)
        self._count(CUBE_MODEL, "CubeA",
                    Orientation(_sel("CubeA"), (0, 0, 1), "Perpendicular", "Wide", 5.0), 0)
        self._count(CUBE_MODEL, "CubeA",
                    Orientation(_sel("CubeA"), (1, 0, 0), "Parrallel", "Wide", 5.0), 1)

    def test_suzanne(self):
        self._count(SUZ_MODEL, "SuzanneA",
                    Orientation(_sel("SuzanneA"), (0, 0, 1), "Parrallel", "Wide", 5.0), 1)
        self._count(SUZ_MODEL, "SuzanneA",
                    Orientation(_sel("SuzanneA"), (0, 0, 1), "Perpendicular", "Wide", 5.0), 0)


class TestOneObjectFace(OneObjectTestCase):
    def test_cube(self):
        # faces Top vs Bottom du cube : distance 1m, normales opposees (180 deg
        # = 0 deg sur le cote court). 4 paires de faces (triangulation).
        s = _sel("CubeA")
        self._count(CUBE_MODEL, "CubeA",
                    OneObjectFace(s, {"orientation": "Top"}, {"orientation": "Bottom"},
                                  distance=True, min_distance=2.0, max_distance=100.0), 4)
        self._count(CUBE_MODEL, "CubeA",
                    OneObjectFace(s, {"orientation": "Top"}, {"orientation": "Bottom"},
                                  distance=True, min_distance=0.5, max_distance=100.0), 0)
        self._count(CUBE_MODEL, "CubeA",
                    OneObjectFace(s, {"orientation": "Top"}, {"orientation": "Bottom"},
                                  orientation=True, angle=0.0, angle_tolerance=5.0), 4)
        self._count(CUBE_MODEL, "CubeA",
                    OneObjectFace(s, {"orientation": "Top"}, {"orientation": "Bottom"},
                                  orientation=True, angle=180.0, angle_tolerance=5.0), 0)

    def test_suzanne(self):
        # Suzanne a ~500 faces : les paires Top/Bottom sont nombreuses.
        # On vérifie les signes (positif/nul) plutôt que les counts exacts.
        s = _sel("SuzanneA")
        r = self._run(SUZ_MODEL, "SuzanneA",
                      OneObjectFace(s, {"orientation": "Top"}, {"orientation": "Bottom"},
                                    distance=True, min_distance=2.0, max_distance=100.0))
        self.assertGreater(len(r.result), 0)
        # min_distance=0 : aucune paire a distance < 0 -> 0 (clash si dist < min)
        self._count(SUZ_MODEL, "SuzanneA",
                    OneObjectFace(s, {"orientation": "Top"}, {"orientation": "Bottom"},
                                  distance=True, min_distance=0.0, max_distance=100.0), 0)
        r = self._run(SUZ_MODEL, "SuzanneA",
                      OneObjectFace(s, {"orientation": "Top"}, {"orientation": "Bottom"},
                                    orientation=True, angle=0.0, angle_tolerance=5.0))
        self.assertGreater(len(r.result), 0)


if __name__ == "__main__":
    unittest.main()
