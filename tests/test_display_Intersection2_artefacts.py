"""The 32 artefact pairs of Intersection2 on the Duplex Architecture
model: the pairs the former engine flagged (one boolean per ordered
pair, AABB prefilter only) and that the optimized engine no longer
flags.

Each pair is an artefact of the OCCT boolean common on the sewn
solids (clash_utils.mesh_to_solid), never a real overlap:
- obb_disjoint (29 pairs): the oriented bounding boxes are disjoint,
  no overlap is possible — yet the boolean returned a volume, most of
  the time the WHOLE volume of one of the two solids;
- inverted_solid (3 pairs): one sewn solid is inverted (negative
  volume): the sign of the common depends on the argument order, the
  former engine flagged the positive order only. The optimized engine
  runs ONE boolean per unordered pair, in the order of the elements:
  on the Duplex all-vs-all run that order gives the negative sign, but
  the verdict still depends on the order (NOT fixed, the sewn solid
  must be reoriented — mesh_to_solid).

The automatic tests check that the optimized engine flags none of the
obb_disjoint pairs, document the order dependency of the
inverted_solid pairs, and prove why each pair is an artefact. The
display tests open a GUI window that must be closed manually (like
test_Rule_display.py), to read the artefacts on screen —
    blue  = first element (sewn solid), orange = second element,
    red   = the artefact common returned by the former boolean,
    label = the index of the pair in ARTEFACTS.

Execution (from the repository root, one file at a time):
    python -m pytest tests/test_display_Intersection2_artefacts.py -v -k "TestIntersection2Artefacts"
    python -m pytest tests/test_display_Intersection2_artefacts.py -v -k display_all
"""
import sys
import unittest

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell
import ifcopenshell.geom

import clash_utils
from Rules import Intersection2

IFC_PATH = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

# (kind, GlobalId of the first element, GlobalId of the second
# element, volume flagged by the former engine in m3). The order of
# the pair is the order in which the former engine flagged it.
ARTEFACTS = [
    ("inverted_solid", "21ldoMpbP4VfsJ0XGY_34P", "3bXiCStxP6Fgxdej$yc5T8", 3.2451),  # Railing 900mm / Ceiling 187149
    ("inverted_solid", "3bXiCStxP6Fgxdej$yc50U", "3bXiCStxP6Fgxdej$yc5T8", 3.059),  # Ceiling 187483 / Ceiling 187149
    ("inverted_solid", "3bXiCStxP6Fgxdej$yc50n", "3bXiCStxP6Fgxdej$yc5T8", 0.0329),  # Ceiling 187508 / Ceiling 187149
    ("obb_disjoint", "0dxE1Sy6nDqfpDb5vIMN_Z", "2gRXFgjRn2HPE$YoDLX0mp", 1.6409),  # Furring wall 194166 / Vanity 204934
    ("obb_disjoint", "0dxE1Sy6nDqfpDb5vIMNiA", "2gRXFgjRn2HPE$YoDLX0ra", 1.6409),  # Furring wall 193247 / Vanity 205265
    ("obb_disjoint", "0dxE1Sy6nDqfpDb5vIMNiA", "2gRXFgjRn2HPE$YoDLX0rb", 1.6409),  # Furring wall 193247 / Vanity 205264
    ("obb_disjoint", "0iEHWY1$XA8eQeeULq4jDb", "2gRXFgjRn2HPE$YoDLX0vP", 0.975),  # Furring wall 190774 / Vanity 205548
    ("obb_disjoint", "0iEHWY1$XA8eQeeULq4jOM", "0iEHWY1$XA8eQeeULq4jQJ", 0.0377),  # Upper cabinet 191557 / Upper cabinet 191680
    ("obb_disjoint", "0iEHWY1$XA8eQeeULq4jZ1", "0wkEuT1wr1kOyafLY4vyMO", 1.8493),  # Furring wall 189074 / Base cabinet 159159
    ("obb_disjoint", "0iEHWY1$XA8eQeeULq4jZ1", "2OBrcmyk58NupXoVOHUvGQ", 1.8493),  # Furring wall 189074 / Base cabinet 160671
    ("obb_disjoint", "0wkEuT1wr1kOyafLY4vyMO", "2OBrcmyk58NupXoVOHUv88", 0.0808),  # Base cabinet 159159 / Counter top 161165
    ("obb_disjoint", "0wkEuT1wr1kOyafLY4vyOn", "2OBrcmyk58NupXoVOHUv88", 0.0808),  # Base cabinet 159262 / Counter top 161165
    ("obb_disjoint", "1aj$VJZFn2TxepZUBcKpZw", "2gRXFgjRn2HPE$YoDLX0ra", 0.356),  # Partition 203998 / Vanity 205265
    ("obb_disjoint", "1aj$VJZFn2TxepZUBcKpvt", "2gRXFgjRn2HPE$YoDLX0mp", 0.356),  # Partition 203347 / Vanity 204934
    ("obb_disjoint", "21ldoMpbP4VfsJ0XGY_34P", "2O2Fr$t4X7Zf8NOew3FKRi", 5.7887),  # Railing 900mm / Party wall 139347
    ("obb_disjoint", "21ldoMpbP4VfsJ0XGY_34P", "2O2Fr$t4X7Zf8NOew3FLTF", 0.6599),  # Railing 900mm / Partition 143856
    ("obb_disjoint", "21ldoMpbP4VfsJ0XGY_34P", "2OBrcmyk58NupXoVOHUt8s", 0.137),  # Railing 900mm / Floor wood 169395
    ("obb_disjoint", "21ldoMpbP4VfsJ0XGY_34P", "2OBrcmyk58NupXoVOHUtC0", 0.4188),  # Railing 900mm / Floor wood 169093
    ("obb_disjoint", "21ldoMpbP4VfsJ0XGY_34P", "3bXiCStxP6Fgxdej$yc50n", 3.2122),  # Railing 900mm / Ceiling 187508
    ("obb_disjoint", "2O2Fr$t4X7Zf8NOew3FKST", "0iEHWY1$XA8eQeeULq4j7w", 0.82),  # Partition 139682 / Upper cabinet 191401
    ("obb_disjoint", "2O2Fr$t4X7Zf8NOew3FKST", "2OBrcmyk58NupXoVOHUvqy", 0.82),  # Partition 139682 / Base cabinet 162489
    ("obb_disjoint", "2OBrcmyk58NupXoVOHUtOy", "2OBrcmyk58NupXoVOHUtO$", 0.8018),  # Sofa 168377 / Sofa 168378
    ("obb_disjoint", "2OBrcmyk58NupXoVOHUvGQ", "2OBrcmyk58NupXoVOHUv88", 0.0808),  # Base cabinet 160671 / Counter top 161165
    ("obb_disjoint", "2OBrcmyk58NupXoVOHUvqp", "2OBrcmyk58NupXoVOHUvqo", 0.017),  # Base cabinet 162486 / Base cabinet 162487
    ("obb_disjoint", "2OBrcmyk58NupXoVOHUvup", "2OBrcmyk58NupXoVOHUvs2", 0.017),  # Base cabinet 162230 / Base cabinet 162311
    ("obb_disjoint", "2gRXFgjRn2HPE$YoDLX0mp", "2gRXFgjRn2HPE$YoDLX0q2", 0.0101),  # Vanity 204934 / Vanity 205239
    ("obb_disjoint", "37Fy90kSD2PvviizyM7EKl", "21ldoMpbP4VfsJ0XGY_34P", 0.0926),  # Stair 198878:2 / Railing 900mm
    ("obb_disjoint", "3bXiCStxP6Fgxdej$yc50U", "2O2Fr$t4X7Zf8NOew3FKST", 0.82),  # Ceiling 187483 / Partition 139682
    ("obb_disjoint", "3bXiCStxP6Fgxdej$yc50n", "2O2Fr$t4X7Zf8NOew3FNqI", 20.7352),  # Ceiling 187508 / Exterior wall 138157
    ("obb_disjoint", "3bXiCStxP6Fgxdej$yc55M", "2O2Fr$t4X7Zf8NOew3FL9r", 1.7328),  # Ceiling 187667 / Partition 144586
    ("obb_disjoint", "3bXiCStxP6Fgxdej$yc55U", "2O2Fr$t4X7Zf8NOew3FKau", 25.8301),  # Ceiling 187675 / Party wall 143239
    ("obb_disjoint", "3bXiCStxP6Fgxdej$yc5T8", "0wkEuT1wr1kOyafLY4v_PL", 0.0058),  # Ceiling 187149 / Railing 151162
]


def solid_volume(shape):
    """The signed volume (m3) of a shape: negative for an inverted
    solid."""
    from OCC.Core import BRepGProp
    from OCC.Core.GProp import GProp_GProps

    properties = GProp_GProps()
    BRepGProp.brepgprop.VolumeProperties(shape, properties)
    return properties.Mass()


def oriented_box(shape):
    from OCC.Core.Bnd import Bnd_OBB
    from OCC.Core.BRepBndLib import brepbndlib

    box = Bnd_OBB()
    brepbndlib.AddOBB(shape, box, False, False, False)
    return box


class _ArtefactModel:
    """The Duplex model, its elements by GlobalId and their sewn
    solids (the geometry the boolean of Intersection2 works on)."""

    @classmethod
    def setUpClass(cls):
        # ifcopenshell 0.9: an entity does not keep its file alive.
        cls.ifc_file = ifcopenshell.open(IFC_PATH)
        global_ids = {gid for _, a, b, _ in ARTEFACTS for gid in (a, b)}
        cls.elements = {gid: cls.ifc_file.by_guid(gid) for gid in global_ids}

        settings = ifcopenshell.geom.settings()
        settings.set(settings.USE_PYTHON_OPENCASCADE, True)
        cls.solids = {
            entity.GlobalId: clash_utils.mesh_to_solid(shape)
            for entity, shape in clash_utils.element_shapes(
                list(cls.elements.values()), settings
            )
        }

    @classmethod
    def tearDownClass(cls):
        cls.solids.clear()
        cls.elements.clear()


class TestIntersection2Artefacts(_ArtefactModel, unittest.TestCase):
    """Automatic: the optimized engine flags none of the artefacts,
    and each one is proven to be an artefact."""

    def test_32_artefacts(self):
        self.assertEqual(len(ARTEFACTS), 32)
        kinds = [kind for kind, *_ in ARTEFACTS]
        self.assertEqual(kinds.count("obb_disjoint"), 29)
        self.assertEqual(kinds.count("inverted_solid"), 3)

    def test_obb_disjoint_not_flagged_by_intersection2(self):
        rule = Intersection2(None, None)
        for index, (kind, gid_a, gid_b, _) in enumerate(ARTEFACTS):
            if kind != "obb_disjoint":
                continue
            with self.subTest(index=index):
                results = rule.compute(
                    [self.elements[gid_a]], [self.elements[gid_b]], 0.0
                )
                self.assertEqual(results, [])
                # The pair is symmetric: one boolean per unordered pair.
                results = rule.compute(
                    [self.elements[gid_b]], [self.elements[gid_a]], 0.0
                )
                self.assertEqual(results, [])

    def test_inverted_solid_verdict_depends_on_order(self):
        """KNOWN DEFECT: with an inverted solid, the verdict follows
        the order of the elements — flagged in the order of the former
        verdict, not flagged in the reverse order."""
        rule = Intersection2(None, None)
        for index, (kind, gid_a, gid_b, _) in enumerate(ARTEFACTS):
            if kind != "inverted_solid":
                continue
            with self.subTest(index=index):
                element_a, element_b = self.elements[gid_a], self.elements[gid_b]
                self.assertEqual(len(rule.compute([element_a], [element_b], 0.0)), 1)
                self.assertEqual(rule.compute([element_b], [element_a], 0.0), [])

    def test_obb_disjoint_no_possible_overlap(self):
        """Disjoint oriented boxes: the solids cannot overlap, the
        volume of the former boolean is an artefact."""
        for index, (kind, gid_a, gid_b, _) in enumerate(ARTEFACTS):
            if kind != "obb_disjoint":
                continue
            with self.subTest(index=index):
                box_a = oriented_box(self.solids[gid_a])
                box_b = oriented_box(self.solids[gid_b])
                self.assertTrue(box_a.IsOut(box_b))

    def test_inverted_solid(self):
        """One sewn solid of the pair is inverted (negative volume):
        the common of the pair changes sign with the argument order."""
        for index, (kind, gid_a, gid_b, _) in enumerate(ARTEFACTS):
            if kind != "inverted_solid":
                continue
            with self.subTest(index=index):
                volumes = (
                    solid_volume(self.solids[gid_a]),
                    solid_volume(self.solids[gid_b]),
                )
                self.assertLess(min(volumes), 0.0)

                forward = clash_utils.common_volume(
                    self.solids[gid_a], self.solids[gid_b]
                )
                backward = clash_utils.common_volume(
                    self.solids[gid_b], self.solids[gid_a]
                )
                self.assertGreater(forward[0], 0.0)
                self.assertAlmostEqual(forward[0], -backward[0], places=6)


#Those test should never be launched automaticly. They all open a GUI window that need to be closed manually.
#They are here only to facilitate de result reading
class TestDisplayIntersection2Artefacts(_ArtefactModel, unittest.TestCase):
    """Manual: the artefacts on screen, one window per test."""

    def _display(self, kinds):
        from OCC.Core.AIS import AIS_Shape
        from OCC.Core.BRepAlgoAPI import BRepAlgoAPI_Common
        from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
        from OCC.Display.SimpleGui import init_display

        blue = Quantity_Color(0, 0, 1, Quantity_TOC_RGB)
        orange = Quantity_Color(1, 0.45, 0, Quantity_TOC_RGB)
        red = Quantity_Color(0.9, 0, 0, Quantity_TOC_RGB)

        display, start_display, _, _ = init_display()

        def show(shape, color, transparency):
            ais_shape = AIS_Shape(shape)
            ais_shape.SetColor(color)
            ais_shape.SetTransparency(transparency)
            display.Context.Display(ais_shape, False)

        shown = set()
        for index, (kind, gid_a, gid_b, volume) in enumerate(ARTEFACTS):
            if kind not in kinds:
                continue
            solid_a, solid_b = self.solids[gid_a], self.solids[gid_b]
            for gid, color in ((gid_a, blue), (gid_b, orange)):
                if gid not in shown:
                    show(self.solids[gid], color, 0.7)
                    shown.add(gid)

            # The artefact: the common of the former engine, in the
            # order it was flagged.
            common = BRepAlgoAPI_Common(solid_a, solid_b)
            common.Build()
            if common.IsDone() and not common.Shape().IsNull():
                show(common.Shape(), red, 0.3)
                center = clash_utils.common_volume(solid_a, solid_b)[1]
                display.DisplayMessage(
                    clash_utils.gp_Pnt(*center), f"{index} ({volume} m3)"
                )

            print(
                f"{index:2d} {kind:15s} {volume:8.4f} m3  "
                f"{self.elements[gid_a].Name} / {self.elements[gid_b].Name}"
            )

        display.Context.UpdateCurrentViewer()
        display.FitAll()
        start_display()

    def test_display_all_artefacts(self):
        self._display({"obb_disjoint", "inverted_solid"})

    def test_display_obb_disjoint(self):
        self._display({"obb_disjoint"})

    def test_display_inverted_solid(self):
        self._display({"inverted_solid"})


if __name__ == "__main__":
    unittest.main()
