#!/usr/bin/env python3
"""
generate_models.py — Génère les fichiers IFC de test manquants pour IfcClash_Plus.

Part du template IFC_Test_Model/IFC_Model/CylinderA_Above_SlabA.ifc (qui contient
18 objets nommés), repositionne les objets par leur CENTRE en coordonnées monde,
et ajoute au besoin de nouvelles géométries : sphère, tore, cône, poutre élancée,
cylindres à profil circulaire vrai (IfcCircleProfileDef), plaque fine.

Convention de nommage des fichiers générés (identique aux fichiers existants) :
    Source_Position_Target[_parametre].ifc

Usage (depuis la racine du dépôt) :
    .venv/bin/python IFC_Test_Model/generate_models.py              # tout générer
    .venv/bin/python IFC_Test_Model/generate_models.py --list       # lister les specs
    .venv/bin/python IFC_Test_Model/generate_models.py --check      # vérifier les bbox
    .venv/bin/python IFC_Test_Model/generate_models.py SlabA_ZOverlap_SlabB   # un seul
"""
import os
import sys
import math

import numpy as np
import ifcopenshell
import ifcopenshell.guid
import ifcopenshell.geom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE = os.path.join(ROOT, "IFC_Test_Model", "IFC_Model", "CylinderA_Above_SlabA.ifc")
OUT_DIR = os.path.join(ROOT, "IFC_Test_Model", "IFC_Model")

# Objets présents dans le template, avec leur position par défaut (loin, axe X).
TEMPLATE_OBJECTS = [
    "CubeA", "CubeB", "SlabA", "SlabB", "CylinderA", "HollowCylinderA",
    "CuboidA", "CuboidB", "BigCubeA", "UshapeA", "SuzanneA", "SuzanneB",
    "WallA", "WallB", "45CuboidA", "45CuboidB", "FallenCuboidA", "FallenCuboidB",
]


def default_pos(i):
    return (200.0 + 20.0 * i, 0.0, 0.0)


DEFAULT_PLACE = {n: default_pos(i) for i, n in enumerate(TEMPLATE_OBJECTS)}


# ---------------------------------------------------------------------------
# Géométrie locale du template
# ---------------------------------------------------------------------------

_TEMPLATE_CENTERS = None


def load_template():
    return ifcopenshell.open(TEMPLATE)


def template_centers():
    """Centre local (bbox) des objets du template, mesuré UNE SEULE FOIS."""
    global _TEMPLATE_CENTERS
    if _TEMPLATE_CENTERS is None:
        f = load_template()
        s = ifcopenshell.geom.settings()
        out = {}
        for el in f.by_type("IfcProduct"):
            if el.is_a("IfcOpeningElement") or not el.Name:
                continue
            if el.is_a() in ("IfcBuilding", "IfcSite", "IfcBuildingStorey"):
                continue
            shape = ifcopenshell.geom.create_shape(s, el)
            v = np.array(shape.geometry.verts).reshape(-1, 3)
            mn, mx = v.min(axis=0), v.max(axis=0)
            out[el.Name] = ((mn + mx) / 2.0, mn, mx)
        _TEMPLATE_CENTERS = out
    return dict(_TEMPLATE_CENTERS)


def local_centers(f):
    return template_centers()


def get_obj(f, name):
    for el in f.by_type("IfcProduct"):
        if el.Name == name:
            return el
    raise KeyError(name)


def placement_matrix(pl):
    ax = pl.RelativePlacement
    x = np.array(ax.RefDirection.DirectionRatios[:3]) if ax.RefDirection else np.array([1.0, 0, 0])
    z = np.array(ax.Axis.DirectionRatios[:3]) if ax.Axis else np.array([0.0, 0, 1])
    x = x / np.linalg.norm(x)
    z = z / np.linalg.norm(z)
    y = np.cross(z, x)
    return np.column_stack([x, y, z])


def set_center(f, centers, name, x, y, z):
    """Place le centre de l'objet en (x, y, z) monde, en conservant sa rotation."""
    el = get_obj(f, name)
    R = placement_matrix(el.ObjectPlacement)
    loc = np.array([x, y, z], dtype=float) - R @ centers[name][0]
    el.ObjectPlacement.RelativePlacement.Location.Coordinates = tuple(float(v) for v in loc)


def save_as(f, name):
    path = os.path.join(OUT_DIR, name + ".ifc")
    f.header.file_name.name = name + ".ifc"
    f.write(path)
    return path


# ---------------------------------------------------------------------------
# Création de nouvelles géométries
# ---------------------------------------------------------------------------

def _storey(f):
    return f.by_type("IfcBuildingStorey")[0]


def _ctx(f):
    # Le subcontext 'Body'/'Model' partagé par tous les objets du template.
    for c in f.by_type("IfcGeometricRepresentationSubContext"):
        if c.ContextIdentifier == "Body":
            return c
    return f.by_type("IfcGeometricRepresentationContext")[0]


def _add_to_storey(f, storey, el):
    for rel in f.by_type("IfcRelContainedInSpatialStructure"):
        if rel.RelatingStructure == storey:
            rel.RelatedElements = list(rel.RelatedElements) + [el]
            return
    raise RuntimeError("IfcRelContainedInSpatialStructure introuvable")


def _new_placement(f, storey, loc):
    pt = f.create_entity("IfcCartesianPoint", [float(v) for v in loc])
    zdir = f.create_entity("IfcDirection", [0.0, 0.0, 1.0])
    xdir = f.create_entity("IfcDirection", [1.0, 0.0, 0.0])
    ax = f.create_entity("IfcAxis2Placement3D", pt, zdir, xdir)
    return f.create_entity("IfcLocalPlacement", storey.ObjectPlacement, ax)


def create_mesh_object(f, name, verts, faces, rep_type="Tessellation"):
    """Crée un IfcFan avec un IfcPolygonalFaceSet. Retourne (entity, centre_local)."""
    storey = _storey(f)
    pts = f.create_entity("IfcCartesianPointList3D", [[float(c) for c in v] for v in verts])
    face_ents = [f.create_entity("IfcIndexedPolygonalFace", [int(i) + 1 for i in fc]) for fc in faces]
    fset = f.create_entity("IfcPolygonalFaceSet", pts, None, face_ents, None)
    rep = f.create_entity("IfcShapeRepresentation", _ctx(f), "Body", rep_type, [fset])
    pds = f.create_entity("IfcProductDefinitionShape", None, None, [rep])
    lp = _new_placement(f, storey, (0.0, 0.0, 0.0))
    el = f.create_entity("IfcFan", ifcopenshell.guid.new(), None, name, None, None, lp, pds, None)
    _add_to_storey(f, storey, el)
    v = np.array(verts)
    return el, (v.min(axis=0) + v.max(axis=0)) / 2.0


def create_cylinder_true(f, name, radius, depth):
    """Crée un IfcFan avec IfcCircleProfileDef + IfcExtrudedAreaSolid (vrai cylindre).

    La géométrie locale va de z=0 à z=depth. Retourne (entity, centre_local).
    """
    storey = _storey(f)
    pt2 = f.create_entity("IfcCartesianPoint", [0.0, 0.0])
    pos2 = f.create_entity("IfcAxis2Placement2D", pt2, None)
    circle = f.create_entity("IfcCircleProfileDef", "AREA", None, pos2, float(radius))
    pt3 = f.create_entity("IfcCartesianPoint", [0.0, 0.0, 0.0])
    zdir = f.create_entity("IfcDirection", [0.0, 0.0, 1.0])
    xdir = f.create_entity("IfcDirection", [1.0, 0.0, 0.0])
    pos3 = f.create_entity("IfcAxis2Placement3D", pt3, zdir, xdir)
    solid = f.create_entity("IfcExtrudedAreaSolid", circle, pos3, zdir, float(depth))
    rep = f.create_entity("IfcShapeRepresentation", _ctx(f), "Body", "SweptSolid", [solid])
    pds = f.create_entity("IfcProductDefinitionShape", None, None, [rep])
    lp = _new_placement(f, storey, (0.0, 0.0, 0.0))
    el = f.create_entity("IfcFan", ifcopenshell.guid.new(), None, name, None, None, lp, pds, None)
    _add_to_storey(f, storey, el)
    return el, np.array([0.0, 0.0, depth / 2.0])


# --- Maillages procéduraux ---

def box_mesh(sx, sy, sz):
    x, y, z = sx / 2, sy / 2, sz / 2
    verts = [(-x, -y, -z), (-x, -y, z), (-x, y, z), (-x, y, -z),
             (x, -y, -z), (x, -y, z), (x, y, z), (x, y, -z)]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
             (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)]
    return verts, faces


def sphere_mesh(r=1.0, nlat=12, nlon=24):
    verts = [(0.0, 0.0, r)]
    for i in range(1, nlat):
        phi = math.pi * i / nlat
        for j in range(nlon):
            th = 2 * math.pi * j / nlon
            verts.append((r * math.sin(phi) * math.cos(th),
                          r * math.sin(phi) * math.sin(th),
                          r * math.cos(phi)))
    south = len(verts)
    verts.append((0.0, 0.0, -r))
    faces = []
    for j in range(nlon):
        faces.append((0, 1 + j, 1 + (j + 1) % nlon))
    for i in range(1, nlat - 1):
        for j in range(nlon):
            a = 1 + (i - 1) * nlon + j
            b = 1 + (i - 1) * nlon + (j + 1) % nlon
            c = 1 + i * nlon + (j + 1) % nlon
            d = 1 + i * nlon + j
            faces.append((a, b, c, d))
    base = 1 + (nlat - 2) * nlon
    for j in range(nlon):
        faces.append((base + j, base + (j + 1) % nlon, south))
    return verts, faces


def torus_mesh(R=2.0, r=0.5, nu=24, nv=12):
    verts, faces = [], []
    for i in range(nu):
        u = 2 * math.pi * i / nu
        for j in range(nv):
            v = 2 * math.pi * j / nv
            verts.append(((R + r * math.cos(v)) * math.cos(u),
                          (R + r * math.cos(v)) * math.sin(u),
                          r * math.sin(v)))
    for i in range(nu):
        for j in range(nv):
            a = i * nv + j
            b = i * nv + (j + 1) % nv
            c = ((i + 1) % nu) * nv + (j + 1) % nv
            d = ((i + 1) % nu) * nv + j
            faces.append((a, b, c, d))
    return verts, faces


def cone_mesh(r=1.0, h=2.0, n=24):
    """Cône : base (z=0, rayon r), sommet (z=h). Centre bbox local = (0,0,h/2)."""
    verts = [(r * math.cos(2 * math.pi * j / n), r * math.sin(2 * math.pi * j / n), 0.0)
             for j in range(n)]
    apex = n
    verts.append((0.0, 0.0, h))
    cbase = n + 1
    verts.append((0.0, 0.0, 0.0))
    faces = []
    for j in range(n):
        faces.append((cbase, j, (j + 1) % n))
        faces.append((j, (j + 1) % n, apex))
    return verts, faces


def create_door(f, name, width, height):
    """Crée un IfcDoor (boîte width x 0.05 x height, centrée en XY, base z=0).

    Retourne (entity, centre_local).
    """
    storey = _storey(f)
    verts, faces = box_mesh(width, 0.05, height)
    # recentrer : la box_mesh centre en (0,0,0) -> ramener la base en z=0
    verts = [(x, y, z + height / 2.0) for (x, y, z) in verts]
    pts = f.create_entity("IfcCartesianPointList3D", [[float(c) for c in v] for v in verts])
    face_ents = [f.create_entity("IfcIndexedPolygonalFace", [int(i) + 1 for i in fc]) for fc in faces]
    fset = f.create_entity("IfcPolygonalFaceSet", pts, None, face_ents, None)
    rep = f.create_entity("IfcShapeRepresentation", _ctx(f), "Body", "Tessellation", [fset])
    pds = f.create_entity("IfcProductDefinitionShape", None, None, [rep])
    lp = _new_placement(f, storey, (0.0, 0.0, 0.0))
    el = f.create_entity("IfcDoor", ifcopenshell.guid.new(), None, name, None, None,
                         lp, pds, None, float(height), float(width), None, None)
    _add_to_storey(f, storey, el)
    return el, np.array([0.0, 0.0, height / 2.0])


def make_new_object(f, spec):
    """spec = (kind, name, params...). Retourne le centre local de l'objet créé."""
    kind, name = spec[0], spec[1]
    if kind == "sphere":
        verts, faces = sphere_mesh(r=spec[2])
        _, c = create_mesh_object(f, name, verts, faces)
    elif kind == "torus":
        verts, faces = torus_mesh(R=spec[2], r=spec[3])
        _, c = create_mesh_object(f, name, verts, faces)
    elif kind == "cone":
        verts, faces = cone_mesh(r=spec[2], h=spec[3])
        _, c = create_mesh_object(f, name, verts, faces)
    elif kind == "box":
        verts, faces = box_mesh(*spec[2:5])
        _, c = create_mesh_object(f, name, verts, faces)
    elif kind == "cylinder":
        _, c = create_cylinder_true(f, name, spec[2], spec[3])
    elif kind == "door":
        _, c = create_door(f, name, spec[2], spec[3])
    else:
        raise ValueError(kind)
    return c


# ---------------------------------------------------------------------------
# Spécifications des fichiers à générer
# ---------------------------------------------------------------------------
# Chaque spec : (file, place, new)
#   file  : nom du fichier sans extension
#   place : {objet: (x, y, z)} centre monde des objets concernés
#           (les autres objets du template vont à leur position par défaut, loin)
#   new   : liste de géométries à créer, ex. [("sphere", "SphereA", 1.0)]

SPECS = [
    # ------------------------------------------------------------------
    # P1 — Positionnement manquant (géométries existantes)
    # ------------------------------------------------------------------
    ("SlabA_ZOverlap_SlabB",
     {"SlabA": (1.5, -0.8, -0.05), "SlabB": (2.5, 0.5, 0.0)}, []),
    #   SlabA: X[0,3] Y[-2.3,0.7] Z[-0.1,0]  |  SlabB: X[1,4] Y[-1,2] Z[-0.05,0.05]
    #   overlap X[1,3] Y[-1,0.7] Z[-0.05,0] = 0.17 m3 ; ni Above ni Below.

    ("SlabA_ZOverlapNoXY_SlabB",
     {"SlabA": (1.5, -0.8, -0.05), "SlabB": (6.5, 4.9, 0.0)}, []),
    #   Z commun mais X/Y disjoints -> Intersection 0, Above/Below 0.

    ("CubeA_NotBelow_CubeB_1m",
     {"CubeA": (2.0, 0.0, 0.0), "CubeB": (0.0, 0.0, 0.0)}, []),
    #   même plage Z, gap 1m en X -> pas Below.

    ("CubeA_AboveNotInFront_CuboidA_3m",
     {"CuboidA": (0.0, 0.0, 0.0), "CubeA": (0.0, 0.0, 3.0)}, []),
    #   CubeA au-dessus de CuboidA : Above = 1 mais PAS InFront/Behind
    #   (le front Wide de CuboidA est horizontal ; verticalement, hors zone).
    #   [calibre] OBB_FAB(CuboidA->CubeA, Wide, tol 2.0) = 0, Above = 1.

    ("SuzanneA_Side_CuboidA_NotFrontNotBehind",
     {"CuboidA": (0.0, 0.0, 0.0), "SuzanneA": (2.5, 0.0, 0.0)}, []),
    #   SuzanneA sur le côté +X de CuboidA : le front/back Wide de CuboidA est
    #   en Y -> SuzanneA n'est ni InFront ni Behind.
    #   [calibre] OBB_FAB(CuboidA->SuzanneA, Wide, tol 1.0) = 0.

    ("CubeA_Diagonal3D_CubeB_1,73m",
     {"CubeA": (0.0, 0.0, 0.0), "CubeB": (2.0, 2.0, 2.0)}, []),
    #   gap 1m sur chaque axe -> distance reelle sqrt(3) = 1.732m (vraie 3D).

    ("CubeB_InU_Crevasse_UshapeA",
     {"UshapeA": (-0.5, 0.0, 1.0), "CubeB": (0.0, 0.0, 1.0)}, []),
    #   UshapeA placement (0,0,0) : creux X[-2,2] Y[-2,2] Z[-1,3].
    #   CubeB au centre du creux : ni Above, ni Below, ni InFront, pas de contact.

    ("CubeA_Above_45CuboidA",
     {"45CuboidA": (0.0, 0.0, 0.0), "CubeA": (0.0, 0.0, 3.0)}, []),
    #   source inclinee 45deg, CubeA au-dessus.

    ("CubeA_Below_45CuboidA",
     {"45CuboidA": (0.0, 0.0, 0.0), "CubeA": (0.0, 0.0, -3.0)}, []),

    ("CubeA_PartialIntersect_UshapeA",
     {"UshapeA": (-0.5, 0.0, 1.0), "CubeA": (-2.25, 0.0, 1.0)}, []),
    #   CubeA X[-2.75,-1.75] penetre le bras ouest X[-3,-2] sur 0.75m.

    ("CubeA_NextTo_CubeB_0,1mm",
     {"CubeA": (0.0, 0.0, 0.0), "CubeB": (1.0001, 0.0, 0.0)}, []),

    ("CubeA_Far_CubeB_10m",
     {"CubeA": (0.0, 0.0, 0.0), "CubeB": (11.0, 0.0, 0.0)}, []),

    ("CubeA_Above_CubeB_Above_SlabA",
     {"SlabA": (1.5, -0.8, -0.05), "CubeB": (1.5, -0.8, 1.5), "CubeA": (1.5, -0.8, 3.5)}, []),
    #   scene 3 objets empiles : SlabA z[-0.1,0], CubeB z[1,2], CubeA z[3,4].

    ("45CuboidA_DiagClose_CubeB_37cm",
     {"45CuboidA": (0.0, 0.0, 0.0), "CubeB": (1.6, 1.6, 0.0)}, []),
    #   diagonale proche d'un cuboid incline : les OBB se chevauchent, les formes
    #   reelles sont disjointes (faux positif OBB potentiel).
    #   [calibre] a confirmer apres generation.

    ("SlabA_SameZ_OverlapXY_SlabB",
     {"SlabA": (1.5, -0.8, -0.05), "SlabB": (2.5, -0.8, -0.05)}, []),
    #   deux dalles au meme Z, overlap X[1,3] -> intersection volumique en plan.

    ("CylinderA_TouchOutside_HollowCylinderA",
     {"HollowCylinderA": (0.0, 0.0, 0.0), "CylinderA": (2.0, 0.0, 0.0)}, []),
    #   contact courbe-sur-courbe en x=1 (rayon ext 1.0 + rayon cyl 1.0).

    ("CylinderA_Inside_BigCubeA",
     {"BigCubeA": (0.0, 0.0, 0.0), "CylinderA": (0.0, 0.0, 0.0)}, []),
    #   cylindre r=1 h=4 (z[-2,2]) au centre du cube 10m.

    # ------------------------------------------------------------------
    # P2 — Nouvelles géométries (testent les hypothèses du moteur, pas OCC)
    # ------------------------------------------------------------------
    ("SphereA_Above_SlabA",
     {"SlabA": (1.5, -0.8, -0.05), "SphereA": (1.5, -0.8, 1.5)},
     [("sphere", "SphereA", 1.0)]),
    #   sphere z[0.5,2.5], dalle z max 0 -> gap 0.5m. Teste get_extreme_faces
    #   sur une forme sans face horizontale.

    ("SphereA_NotAbove_SlabA",
     {"SlabA": (1.5, -0.8, -0.05), "SphereA": (1.5, -0.8, 0.5)},
     [("sphere", "SphereA", 1.0)]),
    #   sphere z[-0.5,1.5] chevauche la plage Z de la dalle -> pas Above.

    ("SphereA_Intersect_SlabA",
     {"SlabA": (1.5, -0.8, -0.05), "SphereA": (1.5, -0.8, 0.0)},
     [("sphere", "SphereA", 1.0)]),
    #   sphere z[-1,1] penetre la dalle z[-0.1,0] (~10cm).
    #   [calibre] Intersection = 0 a toute tolerance (le BVH trianglebvh ne voit
    #   pas l'intersection courbe/plan), Collision = 1, Clearance(0.001) = 1.

    ("CubeA_InHole_TorusA",
     {"TorusA": (0.0, 0.0, 0.0), "CubeA": (0.0, 0.0, 0.0)},
     [("torus", "TorusA", 2.0, 0.5)]),
    #   tore R=2 r=0.5 : trou central de rayon 1.5. Cube 1m au centre ->
    #   PAS d'intersection, mais l'OBB du tore englobe le centre -> faux positif OBB.
    #   [calibre] Intersection(CubeA,TorusA) = 0, OBB_Above(TorusA,CubeA,tol 0.1) = 1.

    ("CubeA_Above_TorusA",
     {"TorusA": (0.0, 0.0, 0.0), "CubeA": (0.0, 0.0, 2.0)},
     [("torus", "TorusA", 2.0, 0.5)]),

    ("ConeA_Above_SlabA",
     {"SlabA": (1.5, -0.8, -0.05), "ConeA": (1.5, -0.8, 2.0)},
     [("cone", "ConeA", 1.0, 2.0)]),
    #   cone base z=1, sommet z=3 (centre bbox local z=1). Pas de face superieure plane.

    ("ConeA_PointIn_CubeB",
     {"CubeB": (0.0, 0.0, 2.0), "ConeA": (0.0, 0.0, 0.55)},
     [("cone", "ConeA", 1.0, 2.0)]),
    #   sommet du cone a z=1.55, dans CubeB z[1.5,2.5] -> penetration ponctuelle 5cm.
    #   [calibre] Collision = 1, Intersection = 0 (meme limite connue : Intersection
    #   manque les penetrations ponctuelles faibles).

    ("BeamLongA_Above_CubeA",
     {"CubeA": (0.0, 0.0, 0.0), "BeamLongA": (0.0, 0.0, 2.0)},
     [("box", "BeamLongA", 10.0, 0.02, 0.02)]),
    #   poutre 10m x 2cm x 2cm au-dessus du cube. Teste la stabilite du PCA.

    ("BeamLongA_Clearance_CubeA_1cm",
     {"CubeA": (0.0, 0.0, 0.0), "BeamLongA": (0.0, 0.52, 0.0)},
     [("box", "BeamLongA", 10.0, 0.02, 0.02)]),
    #   poutre le long de X a cote du cube, gap Y = 1cm.

    ("CylinderTrueA_Intersect_CubeA_1mm",
     {"CubeA": (0.0, 0.0, 0.0), "CylinderTrueA": (1.499, 0.0, 0.0)},
     [("cylinder", "CylinderTrueA", 1.0, 4.0)]),
    #   vrai cylindre (IfcCircleProfileDef) r=1 : X[0.499,2.499] -> penetration 1mm
    #   dans CubeA (X max 0.5). Compare Intersection (BVH) vs Intersection2 (BREP).

    ("CylinderSmallA_Clearance_HollowCylinderA_1cm",
     {"HollowCylinderA": (0.0, 0.0, 0.0), "CylinderSmallA": (0.0, 0.0, 0.0)},
     [("cylinder", "CylinderSmallA", 0.79, 4.0)]),
    #   cylindre r=0.79 dans le creux r=0.8 -> jeu nominal 1cm avec la paroi
    #   interieure (un jeu de 1mm serait parasite par la discretisation angulaire
    #   des deux cylindres polygonaux).

    # ------------------------------------------------------------------
    # P3 — Cas speciaux Intersection / Clearance
    # ------------------------------------------------------------------
    ("SphereA_TangentTop_SlabA",
     {"SlabA": (1.5, -0.8, -0.05), "SphereA": (1.5, -0.8, 1.0)},
     [("sphere", "SphereA", 1.0)]),
    #   sphere centre z=1, rayon 1 -> point bas a z=0 = top de la dalle.
    #   Contact ponctuel courbe-sur-plan.

    ("SphereA_Tangent_SphereB",
     {"SphereA": (0.0, 0.0, 0.0), "SphereB": (2.0, 0.0, 0.0)},
     [("sphere", "SphereA", 1.0), ("sphere", "SphereB", 1.0)]),
    #   deux spheres tangentes en (1,0,0) : contact ponctuel courbe-sur-courbe.
    #   [calibre] Collision = 0 meme avec allow_touching=True (contact ponctuel
    #   courbe non detecte), Clearance(0.001) = 1 (distance 0).

    ("PlateThinA_Through_CubeB_1mm",
     {"CubeB": (0.0, 0.0, 0.0), "PlateThinA": (0.0, 0.0, 0.0)},
     [("box", "PlateThinA", 3.0, 3.0, 0.001)]),
    #   plaque de 1mm d'epaisseur entierement dans le cube.
    #   Attendu (calibre) : Collision = 1, Intersection = 0 (meme bug connu que
    #   CubeA_Intersect_CubeB_1mm : Intersection manque les faibles penetrations/
    #   containments fins, Collision les voit).

    # ------------------------------------------------------------------
    # P4 — Modèles pour les règles sans couverture IFC dédiée
    # ------------------------------------------------------------------
    ("CubeA_DirectView_CubeB",
     {"CubeA": (0.0, 0.0, 0.0), "CubeB": (3.0, 0.0, 0.0)}, []),
    #   deux cubes face a face, rien entre -> DirectView/Ray_Check voient.

    ("CubeA_BlockedView_WallA_CubeB",
     {"CubeA": (0.0, 0.0, 1.5), "WallA": (2.0, 0.0, 1.5), "CubeB": (4.0, 0.0, 1.5)}, []),
    #   WallA (mur 3x0.1x3 vertical) entre les deux cubes -> vue bloquee.

    ("CubeA_FreeSpace_Clear",
     {"CubeA": (0.0, 0.0, 0.0)}, []),
    #   CubeA seul au centre, tout le reste loin -> FreeSpace libre.

    ("CubeA_FreeSpace_Blocked_CubeB_50cm",
     {"CubeA": (0.0, 0.0, 0.0), "CubeB": (1.5, 0.0, 0.0)}, []),
    #   CubeB a 50cm de CubeA -> FreeSpace bloque.

    ("BeamLongA_AxisParallel_BeamLongB_50cm",
     {"BeamLongA": (0.0, 0.0, 0.0), "BeamLongB": (0.0, 0.52, 0.0)},
     [("box", "BeamLongA", 10.0, 0.02, 0.02), ("box", "BeamLongB", 10.0, 0.02, 0.02)]),
    #   deux poutres parallèles selon X, distance axe-a-axe 50cm (Y).

    ("BeamLongA_AxisPerp_CuboidB",
     {"BeamLongA": (0.0, 0.0, 0.0), "CuboidB": (0.0, 0.0, 0.0)},
     [("box", "BeamLongA", 10.0, 0.02, 0.02)]),
    #   poutre selon X croisant CuboidB vertical (axe Z) -> axes perpendiculaires.

    ("DoorA_ClearanceFree_CubeB_2m",
     {"DoorA": (0.0, 0.0, 0.0), "CubeB": (0.0, 2.5, 0.0)},
     [("door", "DoorA", 0.9, 2.1)]),
    #   porte 0.9x2.1, cube a 2m devant (+Y) -> zone de degagement libre.

    ("DoorA_ClearanceBlocked_CubeB_50cm",
     {"DoorA": (0.0, 0.0, 0.0), "CubeB": (0.0, 1.0, 0.0)},
     [("door", "DoorA", 0.9, 2.1)]),
    #   cube a ~50cm devant la porte -> zone bloquee.

    ("CubeA_FaceParallel_CubeB_1m",
     {"CubeA": (0.0, 0.0, 0.0), "CubeB": (2.0, 0.0, 0.0)}, []),
    #   faces +X de CubeA et -X de CubeB paralleles, distance 1m.

    ("CubeA_FacePerp_FallenCuboidA",
     {"CubeA": (0.0, 0.0, 0.0), "FallenCuboidA": (2.0, 0.0, 0.0)}, []),
    #   FallenCuboidA couche (90deg) a cote de CubeA -> faces perpendiculaires.

    ("CubeA_CustomZoneAbove_CubeB_2m",
     {"CubeA": (0.0, 0.0, 0.0), "CubeB": (0.0, 0.0, 2.0)}, []),
    #   CubeB au-dessus : teste OBB_Custom avec detach_top_by_extrude.

    ("CubeA_CustomZoneBelow_CubeB_2m",
     {"CubeA": (0.0, 0.0, 0.0), "CubeB": (0.0, 0.0, -2.0)}, []),
    #   CubeB en dessous : teste OBB_Custom avec detach_bottom_by_extrude.

    ("CubeA_CubeB_CuboidB_AlignedX",
     {"CubeA": (0.0, 0.0, 0.0), "CubeB": (3.0, 0.0, 0.0), "CuboidB": (6.0, 0.0, 0.0)}, []),
    #   3 objets alignes selon X (meme Y, Z) -> Alignement detecte.

    ("CubeA_CubeB_CuboidB_NotAligned",
     {"CubeA": (0.0, 0.0, 0.0), "CubeB": (3.0, 1.0, 0.0), "CuboidB": (6.0, 0.0, 2.0)}, []),
    #   3 objets non alignes -> Alignement ne detecte pas.

    # ------------------------------------------------------------------
    # P5 — Positions manquantes
    # ------------------------------------------------------------------
    ("SlabA_RecoverBottom_SlabB_50%",
     {"SlabA": (1.5, -0.8, 0.05), "SlabB": (3.0, -0.8, -0.05)}, []),
    #   SlabA z[0,0.1], SlabB z[-0.1,0] en dessous, decalee en X de moitie :
    #   recouvrement 50% (4.5 m2 / 9 m2) de la face bottom de SlabA.

    ("SlabA_RecoverSide_CuboidB",
     {"SlabA": (1.5, -0.8, 0.05), "CuboidB": (4.0, -0.8, 0.05)}, []),
    #   CuboidB contre le cote +X de SlabA (contact en x=3).

    ("CylinderSmallA_TouchInside_HollowCylinderA",
     {"HollowCylinderA": (0.0, 0.0, 0.0), "CylinderSmallA": (0.011, 0.0, 0.0)},
     [("cylinder", "CylinderSmallA", 0.79, 4.0)]),
    #   cylindre r=0.79 decale de 11mm -> touche la paroi interieure (r=0.8).

    ("CubeB_Below_UshapeA_50cm",
     {"UshapeA": (-0.5, 0.0, 1.0), "CubeB": (0.0, 0.0, -2.6)}, []),
    #   CubeB z[-3.1,-2.1] sous le fond du U (z min -2) -> Below, gap 0.1m.
]


# ---------------------------------------------------------------------------
# Génération
# ---------------------------------------------------------------------------

def build_file(spec):
    file_name, place, new = spec
    f = load_template()
    centers = local_centers(f)

    # Tous les objets du template : position par défaut loin, sauf cas contraire.
    for n, pos in DEFAULT_PLACE.items():
        set_center(f, centers, n, *pos)
    # Positions du cas de test.
    for n, pos in place.items():
        if n in centers:
            set_center(f, centers, n, *pos)

    # Nouvelles géométries.
    for spec_new in new:
        c = make_new_object(f, spec_new)
        name = spec_new[1]
        centers[name] = (c, None, None)
        pos = place.get(name, (300.0, 0.0, 0.0))
        set_center(f, centers, name, *pos)

    return save_as(f, file_name)


def check_file(file_name):
    """Recharge un fichier généré et affiche les bbox monde de ses objets nommés."""
    path = os.path.join(OUT_DIR, file_name + ".ifc")
    f = ifcopenshell.open(path)
    s = ifcopenshell.geom.settings()
    s.set("use-world-coords", True)
    print(f"=== {file_name}.ifc ===")
    for el in f.by_type("IfcProduct"):
        if el.is_a("IfcOpeningElement") or not el.Name:
            continue
        if el.is_a() in ("IfcBuilding", "IfcSite", "IfcBuildingStorey"):
            continue
        shape = ifcopenshell.geom.create_shape(s, el)
        v = np.array(shape.geometry.verts).reshape(-1, 3)
        mn, mx = v.min(axis=0), v.max(axis=0)
        print(f"  {el.Name:18s} X [{mn[0]:7.3f},{mx[0]:7.3f}]  "
              f"Y [{mn[1]:7.3f},{mx[1]:7.3f}]  Z [{mn[2]:7.3f},{mx[2]:7.3f}]")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = {a for a in sys.argv[1:] if a.startswith("--")}

    if "--list" in flags:
        for spec in SPECS:
            print(f"  {spec[0]}")
        return

    selected = args if args else [s[0] for s in SPECS]
    for spec in SPECS:
        if spec[0] in selected:
            path = build_file(spec)
            print(f"genere: {os.path.basename(path)}")

    if "--check" in flags:
        for name in selected:
            check_file(name)


if __name__ == "__main__":
    main()
