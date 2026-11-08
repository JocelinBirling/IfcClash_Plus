"""Tests unitaires des fonctions du moteur sur les nouvelles géométries
générées par IFC_Test_Model/generate_models.py (sphère, tore, cône, poutre
élancée, vrai cylindre, dalle de référence).

Ces tests vérifient directement les hypothèses du code :
- get_extreme_faces (clash_utils) travaille sur la triangulation et cherche
  les normales > 0.1 selon Z : sur une sphère ou un cône, il n'y a pas de
  "face du dessus" nette -> presque toute la surface est retenue ;
- create_obb_from_geom_verts (CustomOBB, PCA sur les sommets) : le tore a un
  OBB qui englobe son trou central (faux positif structurel des règles OBB_*) ;
  la poutre élancée a le bon axe principal (X) malgré sa finesse.

Valeurs [calibrated] : observées sur les modèles générés.

Exécution (racine du dépôt, environnement conda de agent.md) :
    python -m pytest tests/test_unit_new_geometries.py -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ifcclash_plus"))

import ifcopenshell  # noqa: E402
import ifcopenshell.geom  # noqa: E402
import numpy as np  # noqa: E402

from clash_utils import element_shapes, get_extreme_faces_with_area  # noqa: E402
from CustomOBB import create_obb_from_geom_verts  # noqa: E402

MODEL_DIR = "IFC_Test_Model/IFC_Model"
SETTINGS = ifcopenshell.geom.settings()


def geom_of(model, name):
    """(file, geometry) de l'objet `name` dans le modèle, via element_shapes."""
    f = ifcopenshell.open(f"{MODEL_DIR}/{model}.ifc")
    el = [e for e in f.by_type("IfcProduct") if e.Name == name][0]
    for _ent, geom in element_shapes([el], SETTINGS):
        return f, geom
    raise AssertionError(f"pas de géométrie pour {name} dans {model}")


def point_inside_obb(obb, p):
    """Le point p (monde) est-il à l'intérieur de l'OBB ?"""
    c, axes, hs, _ = obb.to_data()
    R = np.array(axes)  # lignes = directions X,Y,Z de l'OBB
    local = R @ (np.array(p) - np.array(c))
    return bool(np.all(np.abs(local) <= np.array(hs) + 1e-9))


class TestExtremeFaces(unittest.TestCase):
    """get_extreme_faces_with_area en direction +Z sur les nouvelles formes."""

    def test_slab_reference(self):
        # dalle 3x3 : la face du dessus fait 9 m2 (2 triangles)
        _f, geom = geom_of("SlabA_ZOverlap_SlabB", "SlabA")
        ext = get_extreme_faces_with_area(geom, direction=(0.0, 0.0, 1.0))
        self.assertEqual(len(ext["extrem_faces"]), 2)
        self.assertAlmostEqual(ext["total_area"], 9.0, delta=0.01)

    def test_sphere_pas_de_dessus_net(self):
        # sphère : aucune face plane horizontale -> le filtre normal_tol=0.1
        # retient une grande partie de la surface (264 faces, ~6.19 m2,
        # soit presque toute la sphère 4pi = 12.57 m2, hémisphère 2pi = 6.28)
        _f, geom = geom_of("SphereA_Above_SlabA", "SphereA")
        ext = get_extreme_faces_with_area(geom, direction=(0.0, 0.0, 1.0))
        self.assertGreater(len(ext["extrem_faces"]), 100)
        self.assertGreater(ext["total_area"], 6.0)

    def test_cone_toute_la_surface_laterale(self):
        # cône r=1 h=2 : aire latérale = pi*sqrt(5) ~ 7.02, le sommet est un
        # point (pas de face) -> get_extreme_faces retourne ~toute la surface
        _f, geom = geom_of("ConeA_Above_SlabA", "ConeA")
        ext = get_extreme_faces_with_area(geom, direction=(0.0, 0.0, 1.0))
        self.assertAlmostEqual(ext["total_area"], 7.0, delta=0.1)

    def test_torus_moitie_superieure(self):
        # tore R=2 r=0.5 : aire totale 4 pi^2 R r ~ 39.5, moitié ~ 19.7
        _f, geom = geom_of("CubeA_InHole_TorusA", "TorusA")
        ext = get_extreme_faces_with_area(geom, direction=(0.0, 0.0, 1.0))
        self.assertAlmostEqual(ext["total_area"], 19.7, delta=0.5)

    def test_beamlong_face_top_fine(self):
        # poutre 10x0.02x0.02 : la face du dessus fait 0.2 m2 (2 triangles)
        _f, geom = geom_of("BeamLongA_Above_CubeA", "BeamLongA")
        ext = get_extreme_faces_with_area(geom, direction=(0.0, 0.0, 1.0))
        self.assertEqual(len(ext["extrem_faces"]), 2)
        self.assertAlmostEqual(ext["total_area"], 0.2, delta=0.01)


class TestOBB(unittest.TestCase):
    """create_obb_from_geom_verts (PCA sur les sommets)."""

    def test_sphere_obb_cubique(self):
        _f, geom = geom_of("SphereA_Above_SlabA", "SphereA")
        obb = create_obb_from_geom_verts(geom)
        _c, _axes, hs, _ = obb.to_data()
        for h in hs:
            self.assertAlmostEqual(h, 1.0, delta=0.02)  # rayon 1

    def test_torus_obb_englobe_le_trou(self):
        # le trou central du tore a rayon R-r = 1.5, mais l'OBB (PCA) a des
        # demi-axes X/Y ~ 2.5 : le centre (0,0,0), pourtant dans le vide du
        # tore, est A L'INTERIEUR de l'OBB -> faux positif structurel OBB_*
        _f, geom = geom_of("CubeA_InHole_TorusA", "TorusA")
        obb = create_obb_from_geom_verts(geom)
        c, _axes, hs, _ = obb.to_data()
        self.assertAlmostEqual(c[0], 0.0, delta=0.05)
        self.assertAlmostEqual(c[1], 0.0, delta=0.05)
        self.assertAlmostEqual(c[2], 0.0, delta=0.05)
        self.assertGreater(hs[0], 2.4)
        self.assertGreater(hs[1], 2.4)
        self.assertAlmostEqual(hs[2], 0.5, delta=0.02)
        self.assertTrue(point_inside_obb(obb, (0.0, 0.0, 0.0)))
        # un point du tore lui-même (anneau, rayon 2) est aussi dedans
        self.assertTrue(point_inside_obb(obb, (2.0, 0.0, 0.0)))

    def test_beamlong_axe_principal_x(self):
        # poutre 10m selon X : le plus grand demi-axe est selon X, Xdir ~ (1,0,0)
        _f, geom = geom_of("BeamLongA_Above_CubeA", "BeamLongA")
        obb = create_obb_from_geom_verts(geom)
        _c, axes, hs, _ = obb.to_data()
        self.assertAlmostEqual(hs[0], 5.0, delta=0.05)
        self.assertLess(hs[1], 0.05)
        self.assertLess(hs[2], 0.05)
        self.assertAlmostEqual(abs(axes[0][0]), 1.0, delta=0.05)

    def test_cylinder_true_obb(self):
        # vrai cylindre r=1 h=4 : demi-axes triés = (1, 1, 2)
        _f, geom = geom_of("CylinderTrueA_Intersect_CubeA_1mm", "CylinderTrueA")
        obb = create_obb_from_geom_verts(geom)
        _c, _axes, hs, _ = obb.to_data()
        self.assertEqual(sorted(round(h, 2) for h in hs), [1.0, 1.0, 2.0])

    def test_slab_obb(self):
        _f, geom = geom_of("SlabA_ZOverlap_SlabB", "SlabA")
        obb = create_obb_from_geom_verts(geom)
        c, _axes, hs, _ = obb.to_data()
        self.assertAlmostEqual(c[2], -0.05, delta=0.01)
        self.assertAlmostEqual(hs[2], 0.05, delta=0.01)  # épaisseur 0.1


if __name__ == "__main__":
    unittest.main()
