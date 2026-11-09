# COPY of tests/test_Rule_IFC_Test_Model_OneObject.py — the classes of the rules ported to C++
# (TestVolume), generated on 2026-11-09 (SPEC_OptimisationInCPP).
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


if __name__ == "__main__":
    import unittest

    unittest.main()
