"""Speed comparison of the ways to find the faces of an element seen from
above (or from below): the existing functions against the rasterized
height map (engine/triang/HeightMap.h).

Methods, per element, side "top" (direction +Z) or "bottom" (-Z):

    py_brep_rays     clash_utils.get_faces_visible_from_direction_with_plane
                     (B-Rep, 50 x 50 rays: what Above uses, Python)
    cpp_brep_rays    its C++ port, geometry::visible_faces
    py_mesh_shapely  clash_utils.get_extreme_faces (triangles, shapely
                     coverage, pairs of triangles: Python)
    cpp_mesh_geos    its C++ port, geometry::extreme_faces (GEOS)
    cpp_sampled      triang::visible_triangles (4 sample points per
                     triangle, BVH: Above_triang today)
    cpp_raster       triang::visible_triangles_raster (height map, 1 cm
                     cells, 64 to 1024 per side): the new method
    cpp_raster_coarse  the same, 5 cm cells, 16 to 256 per side
    cpp_auto         triang::visible_triangles_auto: cpp_sampled under
                     --from-triangles triangles (default 200), cpp_raster
                     from it on

Geometry: the B-Rep methods take the Python-OCC shape of the rules
(ifcopenshell kernel, USE_PYTHON_OPENCASCADE); the triangle methods take
the world triangulation of the same element (plain settings, the clash
tree input). The C++ times are measured inside C++ (numpy and BRep text
conversions excluded); the Python times with perf_counter.

Quality, for the triangle methods only (the B-Rep methods return faces,
not triangles):
    coverage   plan area of the union of the triangles found / plan area
               of the union of all the non-vertical triangles. A method
               that misses partly seen triangles stays under 1.
    vs_fine    Jaccard index of the triangles found against a fine height
               map (2 mm cells, 256 to 4096 per side), the reference.
    missed / extra  plan area (m2) of the triangles the fine map finds and the
               method does not / the method finds and the fine map does not
               (summed over the elements): area weighted, unlike Jaccard,
               which counts a 1 mm sliver like a whole face.

Usage:
    PYTHONNOUSERSITE=1 python scripts/benchmark_extreme_faces.py \
        [--ifc A.ifc B.ifc] [--max-elements N] [--side top|bottom] \
        [--python-timeout 20] [--output doc/benchmark_extreme_faces]
"""

import argparse
import json
import os
import signal
import statistics
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "ifcclash_plus"))

import numpy as np  # noqa: E402
import ifcopenshell  # noqa: E402
import ifcopenshell.geom  # noqa: E402
import shapely  # noqa: E402
from OCC.Core.BRepTools import breptools  # noqa: E402
from OCC.Core.gp import gp_Dir  # noqa: E402

import clash_utils  # noqa: E402
from engine import _ifcclash_engine as native  # noqa: E402

SAMPLES = "/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main"
DEFAULT_IFC = [
    os.path.join(SAMPLES, "Ifc2x3_Duplex_Architecture.ifc"),
    os.path.join(SAMPLES, "Ifc2x3_Duplex_Mechanical.ifc"),
]
METHODS = [
    "py_brep_rays", "cpp_brep_rays", "py_mesh_shapely", "cpp_mesh_geos", "cpp_sampled", "cpp_raster",
    "cpp_raster_coarse", "cpp_auto",
]
SWEEP = [0, 50, 100, 150, 200, 300, 500, 1000, 10**9]
TRIANGLE_METHODS = ["py_mesh_shapely", "cpp_mesh_geos", "cpp_sampled", "cpp_raster", "cpp_raster_coarse", "cpp_auto"]


class Timeout(Exception):
    pass


def _alarm(signum, frame):
    raise Timeout()


def python_timed(func, limit):
    """(result, seconds), or (None, None) past the limit."""
    signal.signal(signal.SIGALRM, _alarm)
    signal.setitimer(signal.ITIMER_REAL, limit)
    t0 = time.perf_counter()
    try:
        out = func()
        return out, time.perf_counter() - t0
    except Timeout:
        return None, None
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)


class _Triangulation:
    """The buffers get_extreme_faces reads through
    ifcopenshell.util.shape.get_vertices / get_faces."""

    def __init__(self, verts, faces):
        self.verts_buffer = np.ascontiguousarray(verts, dtype="d").tobytes()
        self.faces_buffer = np.ascontiguousarray(faces, dtype="i").tobytes()


def plan_union(verts, faces, indices):
    if len(indices) == 0:
        return shapely.Polygon()
    tris = verts[faces[np.asarray(indices)]][:, :, :2]
    polys = [shapely.Polygon(t) for t in tris]
    polys = [p for p in polys if p.area > 1e-12]
    return shapely.union_all(polys) if polys else shapely.Polygon()


def tri_plan_area(verts, faces, indices):
    """Sum of the plan areas of the triangles (overlaps counted twice)."""
    if not indices:
        return 0.0
    t = verts[faces[np.asarray(sorted(indices))]][:, :, :2]
    a, b = t[:, 1] - t[:, 0], t[:, 2] - t[:, 0]
    return float(np.abs(a[:, 0] * b[:, 1] - a[:, 1] * b[:, 0]).sum() / 2)


def non_vertical(verts, faces):
    t = verts[faces]
    n = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    norm = np.linalg.norm(n, axis=1)
    ok = (norm > 1e-14) & (np.abs(n[:, 2]) > 1e-6 * np.maximum(norm, 1e-300))
    return np.nonzero(ok)[0]


def jaccard(a, b):
    a, b = set(a), set(b)
    return 1.0 if not a and not b else len(a & b) / len(a | b)


def elements_of(path, max_elements):
    f = ifcopenshell.open(path)
    mesh_settings = ifcopenshell.geom.settings()
    mesh_settings.set("use-world-coords", True)
    brep_settings = ifcopenshell.geom.settings()
    brep_settings.set("USE_PYTHON_OPENCASCADE", True)
    it = ifcopenshell.geom.iterator(mesh_settings, f, 1)
    meshes = []
    if it.initialize():
        while True:
            s = it.get()
            g = s.geometry
            verts = np.asarray(g.verts, dtype=float).reshape(-1, 3)
            faces = np.asarray(g.faces, dtype=np.int32).reshape(-1, 3)
            if len(faces):
                meshes.append((s.id, verts, faces))
            if not it.next():
                break
    meshes.sort(key=lambda m: m[0])
    if max_elements:
        meshes = meshes[:max_elements]
    kernel = ifcopenshell.geom.kernel(brep_settings, f)
    for eid, verts, faces in meshes:
        entity = f.by_id(eid)
        try:
            shape = kernel.create_shape(inst=entity).geometry
        except Exception:
            shape = None
        yield f, entity, verts, faces, shape


def run(args):
    side = 1.0 if args.side == "top" else -1.0
    direction = (0.0, 0.0, side)
    rows = []
    for path in args.ifc:
        name = os.path.basename(path)
        print(f"== {name}", flush=True)
        for k, (f, entity, verts, faces, shape) in enumerate(elements_of(path, args.max_elements)):
            row = {"file": name, "id": entity.id(), "type": entity.is_a(), "triangles": int(len(faces)),
                   "time": {}, "count": {}, "coverage": {}, "vs_fine": {}}
            found = {}
            # B-Rep rays
            if shape is not None:
                out, sec = python_timed(
                    lambda: clash_utils.get_faces_visible_from_direction_with_plane(
                        shape=shape, direction=gp_Dir(*direction)), args.python_timeout)
                row["time"]["py_brep_rays"] = sec
                row["count"]["py_brep_rays"] = None if out is None else len(out["visible_faces"])
                n, sec = native.bench.visible_faces_brep(breptools.WriteToString(shape), direction)
                row["time"]["cpp_brep_rays"] = sec
                row["count"]["cpp_brep_rays"] = n
            # Triangles
            tri = _Triangulation(verts, faces)
            out, sec = python_timed(lambda: clash_utils.get_extreme_faces(tri, direction=direction),
                                    args.python_timeout)
            row["time"]["py_mesh_shapely"] = sec
            if out is not None:
                # get_extreme_faces returns the faces (vertex triples): back to triangle numbers.
                keys = {tuple(x) for x in np.asarray(out).reshape(-1, 3).tolist()}
                found["py_mesh_shapely"] = [i for i, fc in enumerate(faces.tolist()) if tuple(fc) in keys]
            idx, sec = native.bench.extreme_faces(verts, faces, direction)
            row["time"]["cpp_mesh_geos"], found["cpp_mesh_geos"] = sec, idx
            idx, sec = native.bench.visible_triangles(verts, faces, side, repeat=args.repeat)
            row["time"]["cpp_sampled"], found["cpp_sampled"] = sec, idx
            idx, sec = native.bench.visible_triangles_raster(verts, faces, side, cell=args.cell,
                                                             max_side=args.max_side, min_side=args.min_side,
                                                             repeat=args.repeat)
            row["time"]["cpp_raster"], found["cpp_raster"] = sec, idx
            idx, sec = native.bench.visible_triangles_raster(verts, faces, side, cell=0.05, max_side=256, min_side=16,
                                                             repeat=args.repeat)
            row["time"]["cpp_raster_coarse"], found["cpp_raster_coarse"] = sec, idx
            idx, sec = native.bench.visible_triangles_auto(verts, faces, side, from_triangles=args.from_triangles,
                                                           repeat=args.repeat)
            row["time"]["cpp_auto"], found["cpp_auto"] = sec, idx

            # Quality
            fine, _ = native.bench.visible_triangles_raster(verts, faces, side, cell=0.002, max_side=4096, min_side=256)
            whole = plan_union(verts, faces, non_vertical(verts, faces)).area
            fine_set = set(fine)
            row["fine_area"] = tri_plan_area(verts, faces, fine_set)
            row["missed"], row["extra"] = {}, {}
            for m, idx in found.items():
                row["missed"][m] = tri_plan_area(verts, faces, fine_set - set(idx))
                row["extra"][m] = tri_plan_area(verts, faces, set(idx) - fine_set)
                row["count"][m] = len(idx)
                row["vs_fine"][m] = jaccard(idx, fine)
                row["coverage"][m] = plan_union(verts, faces, idx).area / whole if whole > 1e-12 else 1.0
            rows.append(row)
            if (k + 1) % 50 == 0:
                print(f"   {k + 1} elements", flush=True)
    return rows


def fmt_s(x):
    if x is None:
        return "–"
    if x < 1e-3:
        return f"{x * 1e6:.0f} µs"
    if x < 1:
        return f"{x * 1e3:.1f} ms"
    return f"{x:.2f} s"


def report(rows, args):
    common = [r for r in rows if all(r["time"].get(m) is not None for m in METHODS)]
    lines = [
        "# Faces extrêmes : carte de hauteur rasterisée contre les fonctions existantes",
        "",
        f"Côté : **{args.side}**. Maquettes : {', '.join(os.path.basename(p) for p in args.ifc)}. "
        f"Éléments : {len(rows)} ; sous-ensemble où toutes les méthodes ont abouti : {len(common)} "
        f"(limite Python {args.python_timeout:g} s par appel). Carte : maille {args.cell:g} m, "
        f"de {args.min_side} à {args.max_side} mailles par côté.",
        "",
        "Généré par `scripts/benchmark_extreme_faces.py`.",
        "",
        "## Vitesse (sous-ensemble commun)",
        "",
        "| Méthode | Total | Moyenne / élément | Médiane | Max | Gain de cpp_raster |",
        "|---|---|---|---|---|---|",
    ]
    raster_total = sum(r["time"]["cpp_raster"] for r in common) if common else 0.0
    for m in METHODS:
        ts = [r["time"][m] for r in common]
        if not ts:
            continue
        total = sum(ts)
        ratio = total / raster_total if raster_total > 0 else None
        gain = "–" if ratio is None else (f"×{ratio:,.0f}".replace(",", " ") if ratio >= 10 else f"×{ratio:.2f}")
        lines.append(f"| `{m}` | {fmt_s(total)} | {fmt_s(total / len(ts))} | {fmt_s(statistics.median(ts))} "
                     f"| {fmt_s(max(ts))} | {gain if m != 'cpp_raster' else '—'} |")
    lines += ["", "Par taille de maillage (temps cumulés) :", "",
              "| Triangles | Éléments | " + " | ".join(f"`{m}`" for m in METHODS) + " |",
              "|---|---|" + "---|" * len(METHODS)]
    for lo, hi, label in [(0, 100, "< 100"), (100, 1000, "100 – 999"), (1000, None, "≥ 1 000")]:
        part = [r for r in common if r["triangles"] >= lo and (hi is None or r["triangles"] < hi)]
        if part:
            lines.append(f"| {label} | {len(part)} | "
                         + " | ".join(fmt_s(sum(r["time"][m] for r in part)) for m in METHODS) + " |")
    if common:
        lines += ["", "Seuil de `cpp_auto` (échantillonnage sous le seuil, carte au-delà), temps cumulés "
                  "recalculés à partir des mesures `cpp_sampled` et `cpp_raster` :", "",
                  "| Seuil (triangles) | " + " | ".join(
                      "0 (carte seule)" if t == 0 else "∞ (échantillonnage seul)" if t >= 10**9 else str(t)
                      for t in SWEEP) + " |",
                  "|---|" + "---|" * len(SWEEP),
                  "| Total | " + " | ".join(
                      fmt_s(sum(r["time"]["cpp_sampled"] if r["triangles"] < t else r["time"]["cpp_raster"]
                                for r in common)) for t in SWEEP) + " |",
                  "", "Meilleur choix possible élément par élément : "
                  + fmt_s(sum(min(r["time"]["cpp_sampled"], r["time"]["cpp_raster"]) for r in common)) + "."]
    timeouts = {m: sum(1 for r in rows if m in r["time"] and r["time"][m] is None) for m in METHODS}
    no_brep = sum(1 for r in rows if "py_brep_rays" not in r["time"])
    lines += ["", f"Appels Python au-delà de la limite : "
              + ", ".join(f"`{m}` {n}" for m, n in timeouts.items() if n) if any(timeouts.values())
              else "Aucun appel Python au-delà de la limite.",
              f"Éléments sans B-Rep Python-OCC : {no_brep}." if no_brep else ""]

    lines += ["", "## Qualité (méthodes sur triangles, sous-ensemble commun)", "",
              "| Méthode | Couverture moyenne | Couverture min | Éléments à couverture < 99 % "
              "| Manqué vs carte fine | En trop vs carte fine | Jaccard moyen vs carte fine |",
              "|---|---|---|---|---|---|---|"]
    fine_total = sum(r["fine_area"] for r in common)
    for m in TRIANGLE_METHODS:
        cov = [r["coverage"][m] for r in common if m in r["coverage"]]
        jac = [r["vs_fine"][m] for r in common if m in r["vs_fine"]]
        if not cov:
            continue
        missed = sum(r["missed"][m] for r in common if m in r["missed"])
        extra = sum(r["extra"][m] for r in common if m in r["extra"])
        lines.append(f"| `{m}` | {statistics.mean(cov):.4f} | {min(cov):.4f} | {sum(c < 0.99 for c in cov)} "
                     f"| {missed:.3f} m² ({100 * missed / fine_total:.3f} %) "
                     f"| {extra:.3f} m² ({100 * extra / fine_total:.3f} %) | {statistics.mean(jac):.4f} |")
    lines += ["", f"Surface en plan vue selon la carte fine : {fine_total:.1f} m² (triangles cumulés)."]

    # The slowest elements for the existing methods
    lines += ["", "## Éléments les plus lents (méthode d'Above, `py_brep_rays`)", "",
              "| Élément | Triangles | py_brep_rays | cpp_brep_rays | cpp_sampled | cpp_raster |",
              "|---|---|---|---|---|---|"]
    slow = sorted((r for r in rows if r["time"].get("py_brep_rays")), key=lambda r: -r["time"]["py_brep_rays"])
    for r in slow[:10]:
        t = r["time"]
        lines.append(f"| {r['file']} #{r['id']} {r['type']} | {r['triangles']} | {fmt_s(t['py_brep_rays'])} "
                     f"| {fmt_s(t['cpp_brep_rays'])} | {fmt_s(t['cpp_sampled'])} | {fmt_s(t['cpp_raster'])} |")
    return "\n".join(lines) + "\n"


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--ifc", nargs="+", default=DEFAULT_IFC)
    p.add_argument("--max-elements", type=int, default=0, help="per file, 0 = all")
    p.add_argument("--side", choices=["top", "bottom"], default="top")
    p.add_argument("--python-timeout", type=float, default=20.0, help="seconds per Python call")
    p.add_argument("--repeat", type=int, default=3, help="repetitions of the fast C++ mesh methods")
    p.add_argument("--cell", type=float, default=0.01)
    p.add_argument("--max-side", type=int, default=1024)
    p.add_argument("--min-side", type=int, default=64)
    p.add_argument("--from-triangles", type=int, default=200, help="threshold of cpp_auto")
    p.add_argument("--output", default=os.path.join(ROOT, "doc", "benchmark_extreme_faces"))
    args = p.parse_args()
    rows = run(args)
    with open(args.output + ".json", "w") as fh:
        json.dump({"args": vars(args), "rows": rows}, fh, indent=1)
    text = report(rows, args)
    with open(args.output + ".md", "w") as fh:
        fh.write(text)
    print(text)


if __name__ == "__main__":
    main()
