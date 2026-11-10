"""Compare the _triang rules (computed on triangles only: the .ifcview, or
the IFC triangulation with --triangles ifc) with their original rules (the
IFC conversion), on the same selection: same results up to the
approximation of the tessellation, and the time of each.

A difference is "explained" only when its cause is measured, per kind of
rule (CASES):
  - every kind: an element the .ifcview does not hold
    (IfcOpeningElement...) is skipped; the result comes back / goes away
    with the threshold and the contact parameter moved by the margin
    (--margin: the .ifcview deflection plus the IFC one; --angle-margin for
    the angles);
  - penetration (Intersection): the penetration is at most tolerance +
    margin, or an element is an open mesh in the IFC triangulation (the
    IfcOpenShell tree then runs its contact test), or the two IFC
    geometries are in contact (unstable penetration test on coincident
    faces);
  - gap (Above, Below): the vertical gap within the margin of 0 or of the
    tolerance; a defect of the original: its ray grid (50 x 50 over the
    largest dimension) passes beside a thin object, its "ray" test cuts an
    infinite line or keeps the distance of the closest points while the
    vertical gap at the ray exceeds the tolerance; or, for a pair only
    _triang finds, a vertical line through the IFC B-Reps confirms it;
  - band, zones (OBB_*): the optimal OBB is not unique (same dimensions,
    axes turned) or its main axis is ambiguous (two dimensions equal within
    the margin);
  - angle_pairs (AngleBetween), measure_length / measure_angle (ObbHigh,
    ObbLength, Orientation: the measures of the common elements compared):
    turned or ambiguous OBB axis, or the same axis in the opposite sense
    (supplementary angles: the sense of an OBB axis is arbitrary);
  - alignment (Alignement): turned or ambiguous axis, or the original gives
    the same verdict on the very same elements (without those the .ifcview
    lacks), or both agree once the elements of explained differences are
    left out (the groups depend on all the axes).
Any other difference is listed as unexplained (exit code 1).

The original rules run in a session without .ifcview (geometry_cache
"off"). Times: "cold" = opening a new session (IFC parse, .ifcview
metadata) + the first run, "warm" = the same rule again in that session.

Usage (repository root, ifcclash_cpp environment, after the C++ build):
    PYTHONNOUSERSITE=1 python engine/triang/compare_triang.py --output doc/triang_comparison.md
    PYTHONNOUSERSITE=1 python engine/triang/compare_triang.py --source a.ifc --target b.ifc --max-elements 100
    PYTHONNOUSERSITE=1 python engine/triang/compare_triang.py --triangles ifc --margin 0.002 --rules ObbHigh_triang
"""
import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
sys.path.insert(0, os.path.join(ROOT, "ifcclash_plus"))

import ifcopenshell  # noqa: E402

from benchmark_engines import DEFAULT_SOURCE, DEFAULT_TARGET, find_ifcview, products, thin  # noqa: E402
from engine.backends import cpp_backend  # noqa: E402

# (original, _triang, parameters, how a difference is explained, the
# contact parameter of the _triang rule moved with the margin). The
# parameters are those of the parity cases (tests/parity_cases.py).
_ALL = {"length_min": 0.0, "length_max": 1e9}
CASES = [
    ("Intersection", "Intersection_triang", {"tolerance": 0.002}, "penetration", None),
    ("Above", "Above_triang", {"above_type": "Above_MaxToMin", "tolerance": 1.0}, "gap", "plan_tolerance"),
    ("Below", "Below_triang", {"below_type": "Below_MinToMax", "tolerance": 1.0}, "gap", "plan_tolerance"),
    ("OBB_Above", "OBB_Above_triang", {"tolerance": 1.0}, "band", "contact_tolerance"),
    ("OBB_Below", "OBB_Below_triang", {"tolerance": 1.0}, "band", "contact_tolerance"),
    ("OBB_Front_And_Back", "OBB_Front_And_Back_triang", {"tolerance": 0.5, "direction_method": "Wide"}, "band",
     "contact_tolerance"),
    ("OBB_Custom", "OBB_Custom_triang",
     {"list_of_modifications": ["detach_top_by_extrude:0.5", "NEW_OBB", "extend_down:50%"]}, "zones",
     "contact_tolerance"),
    ("AngleBetween", "AngleBetween_triang", {"direction_method_for_source": "Wide", "direction_method_for_target": "Wide",
                                             "angle_difference": 90.0, "angle_tolerance": 5.0}, "angle_pairs", None),
    ("ObbHigh", "ObbHigh_triang", dict(_ALL), "measure_length", None),
    ("ObbLength", "ObbLength_triang", dict(_ALL, direction_method="Narrow"), "measure_length", None),
    ("Orientation", "Orientation_triang", {"orientation": [0.0, 0.0, 1.0], "orientation_type": "Perpendicular",
                                           "direction_method": "Wide", "angular_tolerance": 0.1}, "measure_angle", None),
    ("Alignement", "Alignement_triang", {"axis": None, "alignment_type": "Plane", "tolerance": 0.05, "min_group": 3},
     "alignment", None),
    # Wave 2
    ("Clearance", "Clearance_triang", {"clearance": 0.5, "check_all": True}, "clearance", None),
    ("Collision", "Collision_triang", {"allow_touching": False}, "collision", None),
    ("Volume", "Volume_triang", {"volume_min": 0.0, "volume_max": 1e9}, "measure_volume", None),
    ("Area", "Area_triang", {"volume_min": 0.0, "volume_max": 1e9}, "measure_area", None),
    ("TopOrBottomSurface", "TopOrBottomSurface_triang",
     {"surface_min": 0.0, "surface_max": 1e9, "top_or_bot_method": "Top"}, "measure_surface", None),
    ("LateralSurface", "LateralSurface_triang", {"surface_min": 0.0, "surface_max": 1e9, "direction": [0.0, 1.0, 0.0]},
     "measure_surface", None),
    ("ProjectedSurface", "ProjectedSurface_triang",
     {"surface_min": 0.0, "surface_max": 1e9, "direction": [0.0, 0.0, 1.0]}, "measure_surface", None),
]
CASES += [
    # Wave 3
    ("ClearanceAxisToAxis", "ClearanceAxisToAxis_triang",
     {"mode": "MinDistance", "min_distance": 0.2, "max_distance": 5.0, "tolerance": 0.01, "linearity_ratio": 1.5,
      "on_non_linear": "Fallback", "parallel_tolerance": 5.0, "search_radius": 2.0}, "axis", None),
    # min_covering 101 %: every pair in contact is reported, with its covering.
    ("SurfaceRecover", "SurfaceRecover_triang",
     {"direction": "Auto", "reference": "Source", "tolerance": 0.01, "min_covering": ["relative", 101.0],
      "max_covering": None}, "recover", None),
    ("Ray_Check", "Ray_Check_triang", {"max_ray_length": 5.0}, "rays", None),
    ("DirectView", "DirectView_triang",
     {"ray_source": "Source", "ray_count": 10, "threshold": 50.0, "max_distance": None}, "view", None),
]
_FACE_OFF = dict(distance=False, min_distance=None, max_distance=None, intersection=False,
                 intersection_tolerance=0.0, orientation=False, angle=None, angle_tolerance=0.0)
CASES += [
    # Wave 4
    ("OneObjectFace", "OneObjectFace_triang",
     dict(_FACE_OFF, face_a_selection={"orientation": "Top", "extreme_faces": True},
          face_b_selection={"orientation": "Bottom", "extreme_faces": True}, skip_adjacent=True,
          distance=True, min_distance=0.5, intersection=True), "faces_one", None),
    ("TwoObjectsFace", "TwoObjectsFace_triang",
     dict(_FACE_OFF, source_face_selection={"orientation": "Top", "extreme_faces": True},
          target_face_selection={"orientation": "Bottom"}, distance=True, min_distance=0.3, intersection=True),
     "faces_two", None),
    ("FreeSpace", "FreeSpace_triang", {"diameter": 1.0, "height": 2.0}, "free", None),
]
# The kinds whose rule reads a context (every element of both sides).
WITH_CONTEXT = {"rays", "view", "free"}
# At most this many elements per side for a kind (the original is slow: the
# Fallback of ClearanceAxisToAxis measures BRepExtrema skin to skin).
KIND_MAX_ELEMENTS = {"axis": 100, "view": 25}
# The kinds whose original is too slow to run twice: no warm time.
NO_WARM = {"view"}

# The measures compared on the common elements: (measure, margin kind).
MEASURES = {"measure_length": ("offset", "abs"), "measure_angle": ("angle", "angle"),
            "measure_volume": ("volume", "rel"), "measure_area": ("area", "rel"), "measure_surface": ("area", "rel")}
# The kinds run on one selection (sources and targets together).
ONE_OBJECT = {"measure_length", "measure_angle", "measure_volume", "measure_area", "measure_surface", "alignment",
              "faces_one", "free"}


def ifc_mesh_facts(files, threads=2):
    """From the IFC triangulation of every element: the set of the open
    meshes (ifcopenshell.geom.tree.is_manifold: every directed edge matched
    by its reverse) and the world bounding box of each, by (file index, STEP
    id)."""
    import ifcopenshell.geom

    def manifold(faces):
        edges = set()
        for i in range(0, len(faces), 3):
            for j in range(3):
                d = (faces[i + j], faces[i + (j + 1) % 3])
                if d in edges:
                    edges.remove(d)
                else:
                    edges.add((d[1], d[0]))
        return not edges

    open_meshes, boxes = set(), {}
    inward = set()  # closed meshes wound inwards (negative signed volume), or wound inconsistently
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    for index, f in enumerate(files):
        it = ifcopenshell.geom.iterator(settings, f, max(1, threads))
        if not it.initialize():
            continue
        while True:
            shape = it.get()
            faces = list(shape.geometry.faces)
            v = shape.geometry.verts
            directed = set()
            inconsistent = False
            for i in range(0, len(faces), 3):
                for j in range(3):
                    d = (faces[i + j], faces[i + (j + 1) % 3])
                    if d in directed:
                        inconsistent = True  # an edge run twice in the same direction
                    directed.add(d)
            if inconsistent:
                inward.add((index, shape.id))
            if not manifold(faces):
                open_meshes.add((index, shape.id))
            elif v:
                signed = 0.0
                for i in range(0, len(faces), 3):
                    a, b, c = (v[3 * faces[i + k]:3 * faces[i + k] + 3] for k in range(3))
                    signed += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                               + a[2] * (b[0] * c[1] - b[1] * c[0]))
                if signed < 0:
                    inward.add((index, shape.id))
            if v:
                xs, ys, zs = v[0::3], v[1::3], v[2::3]
                boxes[(index, shape.id)] = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
            if not it.next():
                break
    return open_meshes, boxes, inward


class IfcVerticalCheck:
    """The gap target - source of an Above pair on the IFC geometry, along
    the vertical line through (x, y): source side (Max: highest hit, Min:
    lowest) against target side, as above_below_directions."""

    def __init__(self, files):
        import ifcopenshell.geom

        self.files = files
        self.settings = ifcopenshell.geom.settings()
        self.settings.set("use-python-opencascade", True)
        self.settings.set("use-world-coords", True)
        self.shapes = {}

    def shape(self, key):
        import ifcopenshell.geom

        if key not in self.shapes:
            try:
                self.shapes[key] = ifcopenshell.geom.create_shape(self.settings, self.files[key[0]].by_id(key[1])).geometry
            except Exception:
                self.shapes[key] = None
        return self.shapes[key]

    def heights(self, key, x, y):
        from OCC.Core.BRepIntCurveSurface import BRepIntCurveSurface_Inter
        from OCC.Core.gp import gp_Dir, gp_Lin, gp_Pnt

        shape = self.shape(key)
        if shape is None:
            return []
        inter = BRepIntCurveSurface_Inter()
        inter.Init(shape, gp_Lin(gp_Pnt(x, y, 0.0), gp_Dir(0.0, 0.0, 1.0)), 1e-7)
        out = []
        while inter.More():
            out.append(inter.Pnt().Z())
            inter.Next()
        return out

    def absent(self, key, x, y):
        """No surface of the element on the vertical line through (x, y),
        nor within 1 mm."""
        return not any(self.heights(key, x + dx, y + dy)
                       for dx, dy in ((0, 0), (1e-3, 0), (-1e-3, 0), (0, 1e-3), (0, -1e-3)))

    def gap(self, key, above_type, x, y, sign=1.0):
        """The gap at (x, y), or a point within 1 mm (a line on an edge may
        miss the face): target - source (sign +1, Above), source - target
        (sign -1, Below)."""
        for dx, dy in ((0, 0), (1e-3, 0), (-1e-3, 0), (0, 1e-3), (0, -1e-3)):
            zs = self.heights(key[:2], x + dx, y + dy)
            zt = self.heights(key[2:], x + dx, y + dy)
            if zs and zt:
                source = min(zs) if "MinTo" in above_type else max(zs)
                target = min(zt) if "ToMin" in above_type else max(zt)
                return sign * (target - source)
        return None


def source_obbs(raw):
    """The object OBB of each source, from the result blocks: (file, id) ->
    (half sizes, axes)."""
    out = {}
    for r in raw["results"]:
        for o in r.get("info", {}).get("obbs", {}).get("source", []):
            if o.get("label") == "object":
                out[(r["source"]["file_index"], r["source"]["entity_id"])] = (o["half_sizes"], o["axes"])
    return out


def turned_obb(a, b, margin):
    """Same dimensions (within the margin), axes turned by more than 1°."""
    import math

    if not a or not b:
        return False
    if any(abs(x - y) > margin for x, y in zip(sorted(a[0]), sorted(b[0]))):
        return False
    worst = 1.0
    for u in a[1]:
        worst = min(worst, max(abs(sum(p * q for p, q in zip(u, v))) for v in b[1]))
    return math.degrees(math.acos(min(1.0, worst))) > 1.0


def ambiguous_axis(obb, method, margin):
    """Whether the main axis of an OBB is ambiguous: the two largest (Wide)
    or two smallest (Narrow) dimensions within the margin, so the axis picked
    depends on rounding (a cube, a square section)."""
    if not obb:
        return False
    sizes = sorted(2 * h for h in obb[0])
    pair = sizes[1:] if method == "Wide" else sizes[:2]
    return abs(pair[1] - pair[0]) <= margin


def thin_for_original_grid(box):
    """Whether the ray grid of the original Above (50 x 50 over the largest
    dimension, height included) can pass beside the object in plan."""
    if not box:
        return False
    return min(box[0], box[1]) < max(box) / 50.0


ORIGINAL_CACHE = os.path.join(ROOT, "build", "engine", "triang_original_cache")


class OriginalSession:
    """The original rules, their results kept on disk: the original rules
    do not change, a rerun of the comparator reads their results instead
    of running them again (the cold time stored is that of the first run,
    session opening included). The IFC session opens only on a miss. The
    key: the rule, its parameters, the selection, the IFC files (path,
    size, modification time). --no-original-cache runs them anyway."""

    enabled = True

    def __init__(self, paths, threads):
        self.paths, self.threads, self.session = paths, threads, None
        self.files = [(os.path.abspath(p), os.path.getsize(p), os.path.getmtime(p)) for p in paths]

    def _key(self, rule, params, selections):
        import hashlib
        import json
        text = json.dumps([rule, params, selections, self.files], sort_keys=True, default=str)
        return hashlib.sha256(text.encode()).hexdigest()[:32]

    def run(self, rule_type, params, selections):
        import pickle
        path = os.path.join(ORIGINAL_CACHE, self._key(rule_type, params, selections) + ".pickle")
        if self.enabled and os.path.exists(path):
            with open(path, "rb") as f:
                stored = pickle.load(f)
            self.last_elapsed = stored["elapsed"]
            if "error" in stored:
                raise RuntimeError(stored["error"])
            return stored["raw"]
        from engine import _ifcclash_engine as native
        t0 = time.perf_counter()
        if self.session is None:
            self.session = native.Session(ifc_paths=self.paths, rule_threads=self.threads,
                                          iterator_threads=self.threads, geometry_cache="off")
        try:
            raw = self.session.run(rule_type=rule_type, params=params, selections=selections)
        except Exception as error:  # an engine failure is a result too: kept as well
            stored = {"error": str(error), "elapsed": time.perf_counter() - t0}
            os.makedirs(ORIGINAL_CACHE, exist_ok=True)
            with open(path, "wb") as f:
                pickle.dump(stored, f)
            raise
        self.last_elapsed = time.perf_counter() - t0
        os.makedirs(ORIGINAL_CACHE, exist_ok=True)
        with open(path, "wb") as f:
            pickle.dump({"raw": raw, "elapsed": self.last_elapsed}, f)
        return raw

    def close(self):
        if self.session is not None:
            self.session.close()
            self.session = None


def run(session, rule, params, selections):
    t0 = time.perf_counter()
    raw = session.run(rule_type=rule, params=params, selections=selections)
    return time.perf_counter() - t0, raw


DENSE_RAYS = 200   # DirectView: rays of the dense visibility measure
DENSE_AGREE = 10.0  # points of % within which two dense visibilities agree


def dense_ratio(session, rule, params, selection, steps=5):
    """The visibility (% of rays not blocked) of one DirectView pair over
    DENSE_RAYS rays: the rule stops early once the threshold is decided, so
    the ratio is bracketed by bisection on the threshold (100 / 2**steps)."""
    lo, hi = 0.0, 100.0
    for _ in range(steps):
        mid = (lo + hi) / 2
        _, raw = run(session, rule, dict(params, ray_count=DENSE_RAYS, threshold=mid), selection)
        lo, hi = (mid, hi) if raw["results"] else (lo, mid)
    return (lo + hi) / 2


def pairs(raw):
    """The results by (source file, source id, target file, target id); the
    target is (None, None) for a one-object rule."""
    out = {}
    for r in raw["results"]:
        t = r.get("target") or {}
        key = (r["source"]["file_index"], r["source"]["entity_id"], t.get("file_index"), t.get("entity_id"))
        out.setdefault(key, r)
    return out


def describe(files, key):
    def one(f, i):
        e = files[f].by_id(i)
        return f"{e.is_a()} #{i} {getattr(e, 'Name', '') or ''}".strip()

    if key[2] is None:
        return one(key[0], key[1])
    return f"{one(key[0], key[1])} → {one(key[2], key[3])}"


def distance_of(result):
    return result.get("info", {}).get("measure", {}).get("distance", {}).get("value")


inward_set = set()


def explained(kind, params, margin, result, key, other_threshold_run, skipped, open_meshes, contacts, boxes,
              from_original, obbs=None, vertical=None, view_geometry=False):
    """Why a difference sits within the .ifcview approximation, or None."""
    if key[1] in skipped.get(key[0], ()) or key[3] in skipped.get(key[2], ()):
        return "absent du .ifcview"
    d = distance_of(result)
    tol = params.get("tolerance", 0.0)
    if kind == "penetration":
        if d is not None and d <= tol + margin:
            return f"pénétration {d:.4f} ≤ tolérance + marge"
        if (key[0], key[1]) in open_meshes or (key[2], key[3]) in open_meshes:
            return "maillage IFC ouvert : test de contact au lieu de la pénétration"
        if key in contacts:
            return "géométries IFC au contact : test de pénétration instable sur faces coïncidentes"
        return None
    if kind == "recover" and from_original:
        m = result.get("info", {}).get("measure", {})
        area = m.get("contact_area", {}).get("value")
        ratio = m.get("ratio", {}).get("value")
        if area is not None and ratio and ratio > 0:
            width = area / (area / ratio) ** 0.5  # contact area / side of the reference face
            if width <= margin:
                return (f"contact marginal : {area:.1e} m² ({100 * ratio:.2f} % de la face), bande de largeur "
                        f"équivalente {width * 1000:.1f} mm < marge")
    if kind == "clearance" and d is not None and abs(d - params["clearance"]) <= margin:
        return f"distance {d:.4f} au bord du seuil (± marge)"
    if kind == "measure_surface" and not from_original and \
            ((key[0], key[1]) in inward_set or (key[0], key[1]) in open_meshes):
        return ("enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle "
                "orienté dans la direction")
    if kind in ("faces_one", "faces_two", "view"):
        sides = [(key[0], key[1])] + ([(key[2], key[3])] if key[2] is not None else [])
        bad = [k for k in sides if k in inward_set or k in open_meshes]
        if bad:
            what = {"faces_one": "la sélection de faces par orientation (Top, Bottom) lit les normales",
                    "faces_two": "la sélection de faces par orientation (Top, Bottom) lit les normales",
                    "view": "les faces « tournées vers l'autre objet » se lisent sur les normales"}[kind]
            return f"enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : {what}"
        return "seuils à ± marge" if other_threshold_run else None
    if kind == "collision":
        if (key[0], key[1]) in open_meshes or (key[2], key[3]) in open_meshes:
            return "maillage IFC ouvert : test de contact au lieu de la pénétration"
        if key in contacts:
            return "géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation"
        return None
    if kind == "gap" and d is not None and (d <= margin or abs(d - tol) <= margin):
        return f"écart vertical {d:.4f} au bord de [0, tolérance]"
    sign = -1.0 if "below_type" in params else 1.0
    if kind == "gap" and from_original:
        points = result.get("info", {}).get("points", [])
        if points and points[0].get("label") == "ray" and \
                sign * (points[0]["target"][2] - points[0]["source"][2]) < -1e-6:
            return ("faux positif de l'original : son test « ray » coupe une droite infinie "
                    f"(cible {'sous' if sign > 0 else 'sur'} la source)")
        if points and points[0].get("label") == "ray" and \
                sign * (points[0]["target"][2] - points[0]["source"][2]) > tol + margin:
            g = sign * (points[0]["target"][2] - points[0]["source"][2])
            return ("faux positif de l'original : son test « ray » garde la distance des points les plus proches, "
                    f"l'écart vertical au point du rayon ({g:.3f} m) dépasse la tolérance")
    if kind == "gap" and not from_original:
        side = [(key[0], key[1]), (key[2], key[3])]
        thin = [k for k in side if thin_for_original_grid(boxes.get(k))]
        if thin:
            b = boxes[thin[0]]
            return (f"faux négatif de l'original : sa grille de rayons (pas {max(b) / 50 * 100:.1f} cm) "
                    f"passe à côté d'un objet de {min(b[0], b[1]) * 100:.1f} cm en plan")
        points = result.get("info", {}).get("points", [])
        if vertical and points:
            x, y = points[0]["source"][0], points[0]["source"][1]
            if view_geometry and vertical.absent(key[:2], x, y):
                return ("géométrie du .ifcview différente de l'IFC : la source n'a pas de surface à ce point dans "
                        "l'IFC (ouverture non soustraite dans le .ifcview)")
            if view_geometry and vertical.absent(key[2:], points[0]["target"][0], points[0]["target"][1]):
                return ("géométrie du .ifcview différente de l'IFC : la cible n'a pas de surface à ce point dans "
                        "l'IFC (ouverture non soustraite dans le .ifcview)")
            g = vertical.gap(key, params.get("above_type") or params.get("below_type"), x, y, sign)
            if g is not None and -margin <= g <= tol + margin:
                return (f"faux négatif de l'original, vérifié sur l'IFC : la cible est {g:.3f} m "
                        f"{'au-dessus' if sign > 0 else 'au-dessous'} de la source en ({x:.2f}, {y:.2f})")
    if other_threshold_run:
        return "seuils à ± marge"
    if kind == "axis" and obbs:
        # The long axis of an element is that of its OBB: an optimal OBB that
        # is not unique (same dimensions, axes turned: a compact fitting)
        # gives another axis, another axis-to-axis distance.
        turned = [k for k in (key[:2], key[2:]) if turned_obb(obbs[0].get(k), obbs[1].get(k), margin)]
        if turned:
            return ("OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe de "
                    f"{'la source' if turned[0] == key[:2] else 'la cible'} suit un autre axe de la boîte")
    if kind in ("band", "zones") and obbs and turned_obb(obbs[0].get(key[:2]), obbs[1].get(key[:2]), margin):
        return "OBB optimale non unique (mêmes dimensions, axes tournés) : la zone suit un autre axe"
    if kind in ("band", "zones") and obbs and "direction_method" in params and any(
            ambiguous_axis(o.get(key[:2]), params["direction_method"], margin) for o in obbs):
        return "axe principal ambigu : deux dimensions de l'OBB égales à la marge près, la zone suit un autre axe"
    if kind == "alignment" and obbs:
        if turned_obb(obbs[0].get(key[:2]), obbs[1].get(key[:2]), margin):
            return "OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change"
        if any(ambiguous_axis(o.get(key[:2]), "Wide", margin) for o in obbs):
            return "axe principal ambigu : deux dimensions de l'OBB égales à la marge près"
    if kind == "angle_pairs" and obbs:
        methods = (params["direction_method_for_source"], params["direction_method_for_target"])
        for side, method in zip((key[:2], key[2:]), methods):
            if turned_obb(obbs[0].get(side), obbs[1].get(side), margin):
                return "OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change"
            if ambiguous_axis(obbs[0].get(side), method, margin) or ambiguous_axis(obbs[1].get(side), method, margin):
                return "axe principal ambigu : deux dimensions de l'OBB égales à la marge près"
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--target", default=DEFAULT_TARGET)
    parser.add_argument("--max-elements", type=int, default=0, help="at most N elements per side (0 = all)")
    parser.add_argument("--margin", type=float, default=0.011,
                        help="m: .ifcview linear deflection (0.01) + IFC one (0.001)")
    parser.add_argument("--output", help="write the report (Markdown)")
    parser.add_argument("--triangles", choices=["ifcview", "auto", "ifc"], default="ifcview",
                        help="triangle_source of the _triang session (ifc: no .ifcview needed)")
    parser.add_argument("--rules", nargs="*", help="only these _triang rules (default: every case)")
    parser.add_argument("--threads", type=int, default=2,
                        help="engine threads of every session (rule and iterator): keeps the machine usable")
    parser.add_argument("--relative-margin", type=float, default=0.02,
                        help="relative margin of the volumes and areas")
    parser.add_argument("--angle-margin", type=float, default=1.0,
                        help="degrees: margin of the angle thresholds and measures")
    parser.add_argument("--no-original-cache", action="store_true",
                        help="run the original rules again instead of reading their stored results")
    args = parser.parse_args()
    OriginalSession.enabled = not args.no_original_cache

    from engine import _ifcclash_engine as native

    same_file = os.path.abspath(args.source) == os.path.abspath(args.target)
    paths = [args.source] if same_file else [args.source, args.target]
    views = [find_ifcview(p) for p in paths]
    if args.triangles != "ifc" and not all(views):
        sys.exit("a .ifcview is missing next to the IFC files")

    def triang_session():
        if args.triangles == "ifc":
            return native.Session(ifc_paths=paths, rule_threads=args.threads, iterator_threads=args.threads, geometry_cache="off", triangle_source="ifc")
        return native.Session(ifc_paths=paths, rule_threads=args.threads, iterator_threads=args.threads, geometry_cache="require", ifcview_paths=views,
                              triangle_source=args.triangles)
    files = [ifcopenshell.open(p) for p in paths]
    if same_file:  # one model: even / odd elements, as the benchmark
        everything = products(files[0])
        sources, targets = everything[0::2], everything[1::2]
    else:
        sources, targets = products(files[0]), products(files[1])
    sources, targets = thin(sources, args.max_elements), thin(targets, args.max_elements)
    selections = {"source": cpp_backend._slot(sources, files), "target": cpp_backend._slot(targets, files)}
    one_selection = {"source": cpp_backend._slot(sources + targets, files)}

    lines = [
        "# Règles _triang contre règles d'origine",
        "",
        f"- Source : `{paths[0]}` ({len(sources)} éléments)",
        f"- Cible : `{paths[-1]}` ({len(targets)} éléments)",
        f"- Triangles des règles _triang : `{args.triangles}`"
        + (f" (.ifcview : {', '.join(f'`{v}`' for v in views)})" if args.triangles != "ifc" else ""),
        f"- Marge d'explication des écarts : {args.margin} m (flèche .ifcview + flèche IFC)",
        "",
        "« Froid » : ouverture d'une session (lecture de l'IFC, métadonnées du .ifcview) et première "
        "exécution (conversion IFC pour la règle d'origine, décodage du .ifcview pour la règle _triang). "
        "« Chaud » : la même règle relancée dans la session.",
        "",
        "| Règle | Résultats origine | Résultats _triang | Communs | Manquants | En plus | Inexpliqués "
        "| Origine froid | Origine chaud | _triang froid | _triang chaud | Gain froid | Gain chaud |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    details = []
    unexplained_total = 0
    print("IFC meshes...", file=sys.stderr, flush=True)
    open_meshes, boxes, inward = ifc_mesh_facts(files, args.threads)
    inward_set.update(inward)
    obb_maps = None
    facts_session = None

    ifc_session = None

    def ifc_facts():
        """A session on the IFC triangles (triangle_source "ifc")."""
        nonlocal ifc_session
        if ifc_session is None:
            ifc_session = native.Session(ifc_paths=paths, rule_threads=args.threads, iterator_threads=args.threads,
                                         geometry_cache="off", triangle_source="ifc")
        return ifc_session

    def view_facts():
        """A session on the triangles of the _triang rules, for the facts of
        one element (TriMesh closed...)."""
        nonlocal facts_session
        if facts_session is None:
            facts_session = triang_session()
        return facts_session

    def obbs_of_elements():
        """The object OBB of every element, original and _triang (ObbHigh
        reports it for every element with bounds 0..1e9)."""
        nonlocal obb_maps
        if obb_maps is None:
            ifc = OriginalSession(paths, args.threads)
            _, ref = run(ifc, "ObbHigh", dict(_ALL), one_selection)
            ifc.close()
            view = triang_session()
            _, tri = run(view, "ObbHigh_triang", dict(_ALL), one_selection)
            view.close()
            obb_maps = (source_obbs(ref), source_obbs(tri))
        return obb_maps

    thresholds = {"penetration": ("tolerance", args.margin), "gap": ("tolerance", args.margin),
                  "band": ("tolerance", args.margin), "angle_pairs": ("angle_tolerance", args.angle_margin),
                  "alignment": ("tolerance", args.margin), "clearance": ("clearance", args.margin),
                  "axis": ("min_distance", args.margin), "view": ("threshold", None),
                  "recover": ("tolerance", args.margin)}
    for original, triang, params, kind, contact in CASES:
        if args.rules and triang not in args.rules:
            continue
        print(f"{original}...", file=sys.stderr, flush=True)
        sel = one_selection if kind in ONE_OBJECT else selections
        if kind in KIND_MAX_ELEMENTS and (not args.max_elements or args.max_elements > KIND_MAX_ELEMENTS[kind]):
            n = KIND_MAX_ELEMENTS[kind]
            sel = {"source": cpp_backend._slot(thin(sources, n), files),
                   "target": cpp_backend._slot(thin(targets, n), files)}
        if kind in WITH_CONTEXT:
            sel = dict(sel, context=cpp_backend._slot(sources + targets, files))
        ifc = OriginalSession(paths, args.threads)
        try:
            _, ref = run(ifc, original, params, sel)
        except Exception as error:  # an engine failure is a result too
            ifc.close()
            try:
                view = triang_session()
                t1 = time.perf_counter()
                _, tri = run(view, triang, params, sel)
                status = f"{len(tri['results'])} résultats en {time.perf_counter() - t1:.2f} s"
                view.close()
            except Exception as error2:
                status = f"erreur aussi : {error2}"
            lines.append(f"| {triang} | **erreur** | {status} | | | | | | | | | | |")
            details += ["", f"## {triang}", "", f"La règle d'origine {original} échoue : `{error}`. "
                        f"{triang} : {status}."]
            continue
        o_cold = ifc.last_elapsed  # the first run of the rule (cached since)
        o_warm = float("nan")  # the original is not run again (it does not change)
        contacts = set()
        if kind in ("penetration", "collision"):  # the pairs whose IFC geometries are within the margin
            _, near = run(ifc, "Clearance", {"clearance": args.margin, "check_all": False}, sel)
            contacts = set(pairs(near))
        ifc.close()

        t0 = time.perf_counter()
        view = triang_session()
        _, tri = run(view, triang, params, sel)
        t_cold = time.perf_counter() - t0
        t_warm, _ = run(view, triang, params, sel)
        b_wide, b_narrow = None, None
        if kind in thresholds or contact:
            wide, narrow = dict(params), dict(params)
            if kind in thresholds:
                key_t, m = thresholds[kind]
                if m is None:  # DirectView: one ray of the ray count, in %
                    m = 100.0 / params["ray_count"]
                wide[key_t] = params[key_t] + m
                narrow[key_t] = max(0.0, params[key_t] - m)
            if contact:
                wide[contact], narrow[contact] = args.margin, -args.margin
            _, tri_wide = run(view, triang, wide, sel)
            _, tri_narrow = run(view, triang, narrow, sel)
            b_wide, b_narrow = pairs(tri_wide), pairs(tri_narrow)
        skipped_diags = [d for d in tri["diagnostics"] if d["code"] == "not_in_ifcview"]
        skipped = {}
        for d in skipped_diags:
            el = d.get("element") or {}
            skipped.setdefault(el.get("file_index"), set()).add(el.get("entity_id"))
        view.close()

        a, b = pairs(ref), pairs(tri)
        missing = sorted(set(a) - set(b))
        extra = sorted(set(b) - set(a))
        why = {}
        # A set rule groups all its elements together: without the elements
        # the _triang rule skipped, the original may group the others
        # differently. Its result on the very same elements decides.
        same_inputs = None
        if kind in WITH_CONTEXT and args.triangles == "ifcview":
            # The context elements the .ifcview lacks are no obstacle for the
            # _triang rule: the original on the very same context decides.
            facts = view_facts()
            context_kept = [e for e in sources if len(facts.triangles(0, e.id())[1])] + \
                [e for e in targets if len(facts.triangles(0 if same_file else 1, e.id())[1])]
            if len(context_kept) < len(sources) + len(targets):
                ifc = OriginalSession(paths, args.threads)
                _, ref_same = run(ifc, original, params, dict(sel, context=cpp_backend._slot(context_kept, files)))
                ifc.close()
                same_inputs = pairs(ref_same)
        if kind == "alignment" and skipped:
            target_file = 0 if same_file else 1
            kept = [e for e in sources if e.id() not in skipped.get(0, ())] + \
                   [e for e in targets if e.id() not in skipped.get(target_file, ())]
            ifc = OriginalSession(paths, args.threads)
            _, ref_same = run(ifc, original, params, {"source": cpp_backend._slot(kept, files)})
            ifc.close()
            same_inputs = pairs(ref_same)
        if kind in ("band", "zones", "angle_pairs", "measure_length", "measure_angle", "alignment", "axis"):  # OBB based
            obbs = obbs_of_elements()
        else:
            obbs = (source_obbs(ref), source_obbs(tri))
        for k in missing:
            why[k] = explained(kind, params, args.margin, a[k], k, b_wide is not None and k in b_wide, skipped,
                               open_meshes, contacts, boxes, True, obbs)
        if same_inputs is not None:
            for k in missing + extra:
                if why.get(k) is None and (k in same_inputs) == (k in b):
                    why[k] = ("ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, "
                              "membres d'un groupe), l'original donne le même verdict")
        vertical = IfcVerticalCheck(files) if kind == "gap" else None
        for k in extra:
            why[k] = explained(kind, params, args.margin, b[k], k, b_narrow is not None and k not in b_narrow,
                               skipped, open_meshes, contacts, boxes, False, obbs, vertical,
                               args.triangles != "ifc")
        if same_inputs is not None:
            for k in extra:
                if why.get(k) is None and (k in same_inputs) == (k in b):
                    why[k] = ("ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, "
                              "membres d'un groupe), l'original donne le même verdict")
        if kind == "alignment" and any(why.get(k) is None for k in missing + extra):
            # The groups depend on the axes of all the elements: without the
            # elements whose own difference is explained (ambiguous or turned
            # axis, absent), both rules must agree on the rest.
            explained_keys = {k[:2] for k in missing + extra if why.get(k) is not None}
            target_file = 0 if same_file else 1
            kept = [e for e in sources if (0, e.id()) not in explained_keys
                    and e.id() not in skipped.get(0, ())] + \
                   [e for e in targets if (target_file, e.id()) not in explained_keys
                    and e.id() not in skipped.get(target_file, ())]
            reduced = {"source": cpp_backend._slot(kept, files)}
            ifc = OriginalSession(paths, args.threads)
            _, r1 = run(ifc, original, params, reduced)
            ifc.close()
            view = triang_session()
            _, r2 = run(view, triang, params, reduced)
            view.close()
            p1, p2 = pairs(r1), pairs(r2)
            for k in missing + extra:
                if why.get(k) is None and (k in p1) == (k in p2):
                    why[k] = ("groupe recomposé : sans les éléments aux axes ambigus ou tournés, les deux règles "
                              "donnent le même verdict")
        if args.triangles != "ifc" and kind not in ("alignment",) and \
                any(why.get(k) is None for k in missing + extra):
            # The same _triang rule on the IFC triangles of this very pair
            # (same context): the original's verdict = the difference comes
            # from the .ifcview tessellation, not from the rule.
            for k in missing + extra:
                if why.get(k) is not None:
                    continue
                one = {"source": [{"file_index": k[0], "entity_ids": [k[1]]}]}
                if k[2] is not None:
                    one["target"] = [{"file_index": k[2], "entity_ids": [k[3]]}]
                if "context" in sel:
                    one["context"] = sel["context"]
                _, on_ifc = run(ifc_facts(), triang, params, one)
                if (k in pairs(on_ifc)) == (k in a):
                    why[k] = ("propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le "
                              "verdict de l'original")
        if kind == "measure_volume":
            # A zero-thickness element: every triangle of the IFC
            # triangulation has a coincident twin (a surface given twice).
            # The repaired mesh encloses nothing (volume 0, out of
            # ]volume_min, ...[); the signed volume of the raw triangles is
            # that of the doubled surface (twins of the same winding add up),
            # which depends on the origin: no volume of the element.
            import numpy as np
            from collections import Counter
            for k in missing:
                if why.get(k) is not None:
                    continue
                v_, f_ = view_facts().triangles(k[0], k[1])
                if not len(f_) or abs(native.bench.tri_mesh(v_, f_)["volume"]) > 1e-9:
                    continue
                vi_, fi_ = ifc_facts().triangles(k[0], k[1])
                if not len(fi_):
                    continue
                verts = np.round(np.asarray(vi_, dtype=float).reshape(-1, 3), 7)
                tris = np.asarray(fi_).reshape(-1, 3)
                twins = Counter(tuple(sorted(map(tuple, verts[t]))) for t in tris)
                vo = a[k].get("info", {}).get("measure", {}).get("volume", {}).get("value")
                if twins and all(n % 2 == 0 for n in twins.values()):
                    why[k] = (f"géométrie sans épaisseur : les {len(tris)} triangles IFC vont par paires confondues, "
                              f"volume réparé nul ; l'original garde le volume signé de la surface doublée "
                              f"({vo:.1e} m³, dépend de l'origine)")
        if kind == "view" and any(why.get(k) is None for k in missing + extra):
            # DirectView draws ray_count rays: a pair whose visibility is near
            # the threshold flips with the rays drawn (other triangles, other
            # samples). The visibility measured on DENSE_RAYS rays, by the
            # original and by the _triang rule, decides: the same within
            # DENSE_AGREE points = same visibility, only the sampling differs.
            ifc = OriginalSession(paths, args.threads)
            view = triang_session()
            on_ifc = ifc_facts() if args.triangles != "ifc" else None
            for k in missing + extra:
                if why.get(k) is not None:
                    continue
                one = {"source": [{"file_index": k[0], "entity_ids": [k[1]]}],
                       "target": [{"file_index": k[2], "entity_ids": [k[3]]}], "context": sel["context"]}
                p_o = dense_ratio(ifc, original, params, one)
                p_t = dense_ratio(view, triang, params, one)
                if abs(p_o - p_t) <= DENSE_AGREE:
                    why[k] = (f"échantillonnage : sur {DENSE_RAYS} rayons, visibilité {p_o:.0f} % (origine) et "
                              f"{p_t:.0f} % (_triang) pour un seuil de {params['threshold']:.0f} % ; "
                              f"{params['ray_count']} rayons tirés sur d'autres triangles ne départagent pas")
                elif on_ifc is not None:
                    p_i = dense_ratio(on_ifc, triang, params, one)
                    if abs(p_o - p_i) <= DENSE_AGREE:
                        why[k] = (f"propre au maillage .ifcview : sur {DENSE_RAYS} rayons, la même règle sur les "
                                  f"triangles IFC voit {p_i:.0f} % comme l'original ({p_o:.0f} %), "
                                  f"{p_t:.0f} % sur le .ifcview")
            ifc.close()
            view.close()
        # One-object measures: the value of every common element.
        measure_gaps = []
        if kind in MEASURES:
            name, how = MEASURES[kind]
            for k in sorted(set(a) & set(b)):
                va = a[k].get("info", {}).get("measure", {}).get(name, {}).get("value")
                vb = b[k].get("info", {}).get("measure", {}).get(name, {}).get("value")
                if how == "abs":
                    limit = args.margin
                elif how == "angle":
                    limit = args.angle_margin
                else:  # relative, at least the area / volume of the margin on a 1 m element
                    limit = max(args.relative_margin * max(abs(va or 0.0), abs(vb or 0.0)), args.margin)
                if va is None or vb is None or abs(va - vb) <= limit:
                    continue
                reason = None
                tri_closed = None
                if kind in ("measure_volume", "measure_surface"):
                    view_for_facts = view_facts()
                    v_, f_ = view_for_facts.triangles(k[0], k[1])
                    tri_closed = bool(len(f_)) and native.bench.tri_mesh(v_, f_)["closed"]
                if kind == "measure_volume" and k[:2] in open_meshes:
                    reason = "maillage IFC ouvert : volume non défini pour l'original"
                elif kind in ("measure_volume", "measure_surface") and tri_closed is False:
                    reason = ("maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : "
                              "orientation ou volume incertains")
                elif kind == "measure_surface" and (k[:2] in inward or k[:2] in open_meshes):
                    reason = ("enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre "
                              "les triangles sur leur normale")
                if reason is None and kind == "measure_volume":
                    # Open once welded (TriMesh of the engine's IFC triangles):
                    # the signed volume of the original depends on the origin.
                    vi_, fi_ = ifc_facts().triangles(k[0], k[1])
                    if len(fi_) and not native.bench.tri_mesh(vi_, fi_)["closed"]:
                        reason = "maillage IFC ouvert une fois soudé : volume non défini pour l'original"
                if reason is None and args.triangles != "ifc" and how == "rel":
                    # The same _triang rule on the IFC triangles of this element.
                    one = {"source": [{"file_index": k[0], "entity_ids": [k[1]]}]}
                    _, on_ifc = run(ifc_facts(), triang, params, one)
                    vi = next((r.get("info", {}).get("measure", {}).get(name, {}).get("value")
                               for r in on_ifc["results"]), None)
                    if vi is not None and abs(vi - va) <= limit:
                        reason = ("propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur "
                                  f"de l'original ({vi:.4f})")
                if reason:
                    pass
                elif kind == "measure_angle" and abs(va + vb - 180.0) <= limit:
                    reason = "même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)"
                elif turned_obb(obbs[0].get(k[:2]), obbs[1].get(k[:2]), args.margin):
                    reason = "OBB optimale non unique (mêmes dimensions, axes tournés)"
                elif kind == "measure_angle" and any(ambiguous_axis(o.get(k[:2]), params["direction_method"],
                                                                    args.margin) for o in obbs):
                    reason = "axe principal ambigu : deux dimensions de l'OBB égales à la marge près"
                measure_gaps.append(k)
                why[k] = reason
                a[k]["_delta"] = vb - va
        unexplained = [k for k in missing + extra + measure_gaps if why[k] is None]
        unexplained_total += len(unexplained)
        lines.append(
            f"| {triang} | {len(a)} | {len(b)} | {len(set(a) & set(b))} | {len(missing)} | {len(extra)} "
            f"| {len(unexplained)} | {o_cold:.2f} s | {o_warm:.2f} s | {t_cold:.2f} s | {t_warm:.2f} s "
            f"| ×{o_cold / t_cold:.1f} | ×{o_warm / max(t_warm, 1e-9):.1f} |"
        )
        details += ["", f"## {triang}", "", f"Paramètres : `{params}`.", ""]
        details.append(f"- Phases _triang : `{tri['stats']['summary']}`")
        details.append(f"- Phases origine : `{ref['stats']['summary']}`")
        if kind in MEASURES:
            how = MEASURES[kind][1]
            limit = {"abs": f"{args.margin} m", "angle": f"{args.angle_margin}°",
                     "rel": f"{args.relative_margin * 100:g} % (au moins {args.margin})"}[how]
            details.append(f"- Mesures comparées sur {len(set(a) & set(b))} éléments communs : "
                           f"{len(measure_gaps)} écart(s) au-delà de {limit}")
        categories = {}
        for k in missing + extra + measure_gaps:
            w = why[k]
            if w is None:
                label = "**inexpliqué**"
            elif w.startswith("pénétration"):
                label = "pénétration ≤ tolérance + marge"
            elif w.startswith("écart vertical"):
                label = "écart vertical au bord de [0, tolérance]"
            elif w.startswith("faux négatif de l'original, vérifié"):
                label = "faux négatif de l'original, vérifié sur l'IFC"
            elif w.startswith("distance") and "au bord du seuil" in w:
                label = "distance au bord du seuil"
            elif w.startswith("propre au maillage .ifcview"):
                label = "propre au maillage .ifcview"
            elif w.startswith("faux négatif de l'original : sa grille"):
                label = "faux négatif de l'original : grille de rayons"
            else:
                label = w.split(" (")[0].split(" :")[0]
            categories[label] = categories.get(label, 0) + 1
        if categories:
            details.append("- Écarts par cause : " + ", ".join(f"{n} {c}" for c, n in
                                                              sorted(categories.items(), key=lambda x: -x[1])))
        if skipped_diags:
            details.append(f"- {len(skipped_diags)} élément(s) absent(s) du .ifcview, ignorés "
                           f"(ex. {skipped_diags[0]['message']})")
        for label, keys, source in (("Manquants", missing, a), ("En plus", extra, b), ("Mesures", measure_gaps, a)):
            if not keys:
                continue
            details += ["", f"{label} ({len(keys)}) :", ""]
            shown = sorted(keys, key=lambda k: why[k] is not None)[:40]  # unexplained first
            for k in shown:
                d = source[k].get("_delta") if label == "Mesures" else distance_of(source[k])
                what = "écart" if label == "Mesures" else "distance"
                details.append(f"- {describe(files, k)} — {what} {d if d is None else round(d, 4)} — "
                               f"{('expliqué : ' + why[k]) if why[k] else '**inexpliqué**'}")
            if len(keys) > len(shown):
                details.append(f"- ... {len(keys) - len(shown)} de plus")

    report = "\n".join(lines + details) + "\n"
    print(report)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as out:
            out.write(report)
    if unexplained_total:
        sys.exit(f"{unexplained_total} unexplained difference(s)")


if __name__ == "__main__":
    main()
