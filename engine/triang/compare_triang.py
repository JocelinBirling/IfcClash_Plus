"""Compare the _triang rules (the .ifcview triangles only) with their
original rules (the IFC conversion), on the same selection: same pairs up
to the .ifcview approximation, and the time of each.

A difference is "explained" when it sits within the margin of the .ifcview
tessellation (--margin: its deflection plus the IFC one), per rule:
  - an element the .ifcview does not hold (IfcOpeningElement...): skipped;
  - Intersection: the penetration of the pair (measured by the rule that
    found it) is at most tolerance + margin (a contact, a light touch), or
    an element is an open (non-manifold) mesh in the IFC triangulation:
    the IfcOpenShell tree then runs its contact test instead of measuring a
    penetration, while the .ifcview mesh of the element is closed; or the
    two IFC geometries are in contact (Clearance at the margin): on
    coincident faces the penetration test of IfcOpenShell is unstable (a
    vertex on a face is "outside", 0.05 mm inside gives the full depth);
  - Above: the vertical gap is within the margin of 0 or of the tolerance,
    or the pair comes back / goes away with the tolerance and the plan
    tolerance moved by the margin (+margin to come back, -margin: the faces
    must overlap by the margin, to go away); or a defect of the original:
    its ray grid (50 x 50 over the largest dimension of the object, height
    included) passes beside an object thinner in plan than its spacing (a
    vertical riser), or its "ray" check intersects an infinite line and
    keeps a target lying below the source; or, for a pair only _triang
    finds, the IFC geometry confirms it: at the point _triang reports, a
    vertical line through the IFC B-Reps of the source and the target
    (OpenCascade) measures a gap within [0, tolerance] (up to the margin)
    — the original only looks at the closest points of the two faces;
  - OBB_Above: the pair comes back / goes away with the band height and the
    contact tolerance moved by the margin (-margin: the target must enter
    the band by the margin); or the optimal OBB of the source is not unique
    (same dimensions, axes turned: a square or round section), so "above"
    follows another axis.
Any other difference is listed as unexplained.

The original rules run in a session without .ifcview (geometry_cache
"off"), the _triang ones in a session that requires it. Times: "cold" =
opening a new session (IFC parse, .ifcview metadata) + the first run,
"warm" = the same rule again in that session.

Usage (repository root, ifcclash_cpp environment, after the C++ build):
    PYTHONNOUSERSITE=1 python engine/triang/compare_triang.py --output doc/triang_comparison.md
    PYTHONNOUSERSITE=1 python engine/triang/compare_triang.py --source a.ifc --target b.ifc --max-elements 100
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
# contact parameter of the _triang rule moved with the margin)
CASES = [
    ("Intersection", "Intersection_triang", {"tolerance": 0.002}, "penetration", None),
    ("Above", "Above_triang", {"above_type": "Above_MaxToMin", "tolerance": 1.0}, "gap", "plan_tolerance"),
    ("OBB_Above", "OBB_Above_triang", {"tolerance": 1.0}, "band", "contact_tolerance"),
]


def ifc_mesh_facts(files):
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
    settings = ifcopenshell.geom.settings()
    settings.set("use-world-coords", True)
    for index, f in enumerate(files):
        it = ifcopenshell.geom.iterator(settings, f, os.cpu_count() or 1)
        if not it.initialize():
            continue
        while True:
            shape = it.get()
            if not manifold(list(shape.geometry.faces)):
                open_meshes.add((index, shape.id))
            v = shape.geometry.verts
            if v:
                xs, ys, zs = v[0::3], v[1::3], v[2::3]
                boxes[(index, shape.id)] = (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))
            if not it.next():
                break
    return open_meshes, boxes


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

    def gap(self, key, above_type, x, y):
        """The gap at (x, y), or a point within 1 mm (a line on an edge may
        miss the face)."""
        for dx, dy in ((0, 0), (1e-3, 0), (-1e-3, 0), (0, 1e-3), (0, -1e-3)):
            zs = self.heights(key[:2], x + dx, y + dy)
            zt = self.heights(key[2:], x + dx, y + dy)
            if zs and zt:
                source = min(zs) if "MinTo" in above_type else max(zs)
                target = min(zt) if "ToMin" in above_type else max(zt)
                return target - source
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


def thin_for_original_grid(box):
    """Whether the ray grid of the original Above (50 x 50 over the largest
    dimension, height included) can pass beside the object in plan."""
    if not box:
        return False
    return min(box[0], box[1]) < max(box) / 50.0


def run(session, rule, params, selections):
    t0 = time.perf_counter()
    raw = session.run(rule_type=rule, params=params, selections=selections)
    return time.perf_counter() - t0, raw


def pairs(raw):
    out = {}
    for r in raw["results"]:
        key = (r["source"]["file_index"], r["source"]["entity_id"], r["target"]["file_index"], r["target"]["entity_id"])
        out.setdefault(key, r)
    return out


def describe(files, key):
    def one(f, i):
        e = files[f].by_id(i)
        return f"{e.is_a()} #{i} {getattr(e, 'Name', '') or ''}".strip()

    return f"{one(key[0], key[1])} → {one(key[2], key[3])}"


def distance_of(result):
    return result.get("info", {}).get("measure", {}).get("distance", {}).get("value")


def explained(kind, params, margin, result, key, other_threshold_run, skipped, open_meshes, contacts, boxes,
              from_original, obbs=None, vertical=None):
    """Why a difference sits within the .ifcview approximation, or None."""
    if key[1] in skipped.get(key[0], ()) or key[3] in skipped.get(key[2], ()):
        return "absent du .ifcview"
    d = distance_of(result)
    tol = params["tolerance"]
    if kind == "penetration":
        if d is not None and d <= tol + margin:
            return f"pénétration {d:.4f} ≤ tolérance + marge"
        if (key[0], key[1]) in open_meshes or (key[2], key[3]) in open_meshes:
            return "maillage IFC ouvert : test de contact au lieu de la pénétration"
        if key in contacts:
            return "géométries IFC au contact : test de pénétration instable sur faces coïncidentes"
        return None
    if kind == "gap" and d is not None and (d <= margin or abs(d - tol) <= margin):
        return f"écart vertical {d:.4f} au bord de [0, tolérance]"
    if kind == "gap" and from_original:
        points = result.get("info", {}).get("points", [])
        if points and points[0].get("label") == "ray" and points[0]["target"][2] < points[0]["source"][2] - 1e-6:
            return "faux positif de l'original : son test « ray » coupe une droite infinie (cible sous la source)"
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
            g = vertical.gap(key, params["above_type"], x, y)
            if g is not None and -margin <= g <= tol + margin:
                return (f"faux négatif de l'original, vérifié sur l'IFC : la cible est {g:.3f} m au-dessus "
                        f"de la source en ({x:.2f}, {y:.2f})")
    if other_threshold_run:
        return "seuils à ± marge"
    if kind == "band" and obbs and turned_obb(obbs[0].get(key[:2]), obbs[1].get(key[:2]), margin):
        return "OBB optimale non unique (mêmes dimensions, axes tournés) : la bande « au-dessus » suit un autre axe"
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--target", default=DEFAULT_TARGET)
    parser.add_argument("--max-elements", type=int, default=0, help="at most N elements per side (0 = all)")
    parser.add_argument("--margin", type=float, default=0.011,
                        help="m: .ifcview linear deflection (0.01) + IFC one (0.001)")
    parser.add_argument("--output", help="write the report (Markdown)")
    args = parser.parse_args()

    from engine import _ifcclash_engine as native

    same_file = os.path.abspath(args.source) == os.path.abspath(args.target)
    paths = [args.source] if same_file else [args.source, args.target]
    views = [find_ifcview(p) for p in paths]
    if not all(views):
        sys.exit("a .ifcview is missing next to the IFC files")
    files = [ifcopenshell.open(p) for p in paths]
    if same_file:  # one model: even / odd elements, as the benchmark
        everything = products(files[0])
        sources, targets = everything[0::2], everything[1::2]
    else:
        sources, targets = products(files[0]), products(files[1])
    sources, targets = thin(sources, args.max_elements), thin(targets, args.max_elements)
    selections = {"source": cpp_backend._slot(sources, files), "target": cpp_backend._slot(targets, files)}

    lines = [
        "# Règles _triang contre règles d'origine",
        "",
        f"- Source : `{paths[0]}` ({len(sources)} éléments)",
        f"- Cible : `{paths[-1]}` ({len(targets)} éléments)",
        f"- .ifcview : {', '.join(f'`{v}`' for v in views)}",
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
    open_meshes, boxes = ifc_mesh_facts(files)
    for original, triang, params, kind, contact in CASES:
        print(f"{original}...", file=sys.stderr, flush=True)
        t0 = time.perf_counter()
        ifc = native.Session(ifc_paths=paths, geometry_cache="off")
        try:
            _, ref = run(ifc, original, params, selections)
        except Exception as error:  # an engine failure is a result too
            ifc.close()
            try:
                view = native.Session(ifc_paths=paths, geometry_cache="require", ifcview_paths=views)
                t1 = time.perf_counter()
                _, tri = run(view, triang, params, selections)
                status = f"{len(tri['results'])} résultats en {time.perf_counter() - t1:.2f} s"
                view.close()
            except Exception as error2:
                status = f"erreur aussi : {error2}"
            lines.append(f"| {triang} | **erreur** | {status} | | | | | | | | | | |")
            details += ["", f"## {triang}", "", f"La règle d'origine {original} échoue : `{error}`. "
                        f"{triang} : {status}."]
            continue
        o_cold = time.perf_counter() - t0
        o_warm, _ = run(ifc, original, params, selections)
        contacts = set()
        if kind == "penetration":  # the pairs whose IFC geometries are within the margin
            _, near = run(ifc, "Clearance", {"clearance": args.margin, "check_all": False}, selections)
            contacts = set(pairs(near))
        ifc.close()

        t0 = time.perf_counter()
        view = native.Session(ifc_paths=paths, geometry_cache="require", ifcview_paths=views)
        _, tri = run(view, triang, params, selections)
        t_cold = time.perf_counter() - t0
        t_warm, _ = run(view, triang, params, selections)
        wide = dict(params, tolerance=params["tolerance"] + args.margin)
        narrow = dict(params, tolerance=max(0.0, params["tolerance"] - args.margin))
        if contact:
            wide[contact], narrow[contact] = args.margin, -args.margin
        _, tri_wide = run(view, triang, wide, selections)
        _, tri_narrow = run(view, triang, narrow, selections)
        skipped_diags = [d for d in tri["diagnostics"] if d["code"] == "not_in_ifcview"]
        skipped = {}
        for d in skipped_diags:
            el = d.get("element") or {}
            skipped.setdefault(el.get("file_index"), set()).add(el.get("entity_id"))
        view.close()

        a, b = pairs(ref), pairs(tri)
        b_wide, b_narrow = pairs(tri_wide), pairs(tri_narrow)
        missing = sorted(set(a) - set(b))
        extra = sorted(set(b) - set(a))
        why = {}
        obbs = (source_obbs(ref), source_obbs(tri))
        for k in missing:
            why[k] = explained(kind, params, args.margin, a[k], k, k in b_wide, skipped, open_meshes, contacts,
                               boxes, True, obbs)
        vertical = IfcVerticalCheck(files) if kind == "gap" else None
        for k in extra:
            why[k] = explained(kind, params, args.margin, b[k], k, k not in b_narrow, skipped, open_meshes,
                               contacts, boxes, False, obbs, vertical)
        unexplained = [k for k in missing + extra if why[k] is None]
        unexplained_total += len(unexplained)
        lines.append(
            f"| {triang} | {len(a)} | {len(b)} | {len(set(a) & set(b))} | {len(missing)} | {len(extra)} "
            f"| {len(unexplained)} | {o_cold:.2f} s | {o_warm:.2f} s | {t_cold:.2f} s | {t_warm:.2f} s "
            f"| ×{o_cold / t_cold:.1f} | ×{o_warm / max(t_warm, 1e-9):.1f} |"
        )
        details += ["", f"## {triang}", "", f"Paramètres : `{params}`.", ""]
        details.append(f"- Phases _triang : `{tri['stats']['summary']}`")
        details.append(f"- Phases origine : `{ref['stats']['summary']}`")
        categories = {}
        for k in missing + extra:
            w = why[k]
            if w is None:
                label = "**inexpliqué**"
            elif w.startswith("pénétration"):
                label = "pénétration ≤ tolérance + marge"
            elif w.startswith("écart vertical"):
                label = "écart vertical au bord de [0, tolérance]"
            elif w.startswith("faux négatif de l'original, vérifié"):
                label = "faux négatif de l'original, vérifié sur l'IFC"
            else:
                label = w.split(" (")[0].split(" :")[0]
            categories[label] = categories.get(label, 0) + 1
        if categories:
            details.append("- Écarts par cause : " + ", ".join(f"{n} {c}" for c, n in
                                                              sorted(categories.items(), key=lambda x: -x[1])))
        if skipped_diags:
            details.append(f"- {len(skipped_diags)} élément(s) absent(s) du .ifcview, ignorés "
                           f"(ex. {skipped_diags[0]['message']})")
        for label, keys, source in (("Manquants", missing, a), ("En plus", extra, b)):
            if not keys:
                continue
            details += ["", f"{label} ({len(keys)}) :", ""]
            shown = sorted(keys, key=lambda k: why[k] is not None)[:40]  # unexplained first
            for k in shown:
                d = distance_of(source[k])
                details.append(f"- {describe(files, k)} — distance {d if d is None else round(d, 4)} — "
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
