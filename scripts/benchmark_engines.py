"""Speed comparison of the three engines of IfcClash_Plus
(SPEC_OptimisationInCPP, "Ordre de migration", steps 2 and 6):

    python       the compute() of the rules (Rules.py), the reference
    cpp          libifcclash_engine, geometry read from the IFC
    cpp+ifcview  libifcclash_engine, broad and mid phases on the boxes of an
                 already produced .ifcview (BonsaiViewer cache), narrow
                 phase on the IFC

For each ported rule (Volume, Intersection, Clearance, Collision) the script
times one run per engine on the same element lists and checks that the
three engines return the same pairs (a gap is reported, never hidden: the
exit code is non-zero).

C++ times: "cold" = a new Session (IFC parse + geometry conversion
included: what one rule costs in a RuleFile), "warm" = the same rule run
again in the same Session (the RuleFile cache is filled). The Python time
includes the geometry conversion of each call (the Python engine has no
cache between rules); its IFC parse (ifcopenshell.open) is timed apart.

Default models: Duplex Architecture (source) against Duplex Mechanical
(target) from IfcSampleFiles-main, whose .ifcview (v19) were produced by
BonsaiViewer.

Usage (repository root, ifcclash_cpp environment, after the C++ build):
    PYTHONNOUSERSITE=1 python scripts/benchmark_engines.py
    PYTHONNOUSERSITE=1 python scripts/benchmark_engines.py \\
        --source a.ifc --target b.ifc --rules Clearance Collision \\
        --output benchmark.md
"""
import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "ifcclash_plus"))

import ifcopenshell  # noqa: E402
import ifcopenshell.geom  # noqa: E402

from engine.backends import cpp_backend  # noqa: E402
from Rules import Clearance, Collision, Intersection, Volume  # noqa: E402

SAMPLES = "/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main"
DEFAULT_SOURCE = os.path.join(SAMPLES, "Ifc2x3_Duplex_Architecture.ifc")
DEFAULT_TARGET = os.path.join(SAMPLES, "Ifc2x3_Duplex_Mechanical.ifc")

RULES = {
    "Volume": (lambda: Volume(None, 0.0, 1e9), {"volume_min": 0.0, "volume_max": 1e9}),
    "Intersection": (lambda: Intersection(None, None), {"tolerance": 0.002}),
    "Clearance": (lambda: Clearance(None, None), {"clearance": 0.05, "check_all": False}),
    "Collision": (lambda: Collision(None, None), {"allow_touching": False}),
}


def find_ifcview(ifc_path):
    stem, _ = os.path.splitext(ifc_path)
    for candidate in (stem + ".ifcview", ifc_path + ".ifcview"):
        if os.path.exists(candidate):
            return candidate
    return None


def products(ifc_file):
    return [p for p in ifc_file.by_type("IfcProduct") if p.Representation is not None]


def key_set(results, one_object, files):
    """(file index, STEP id) of each side: comparable across engines."""

    def side(entity):
        for index, f in enumerate(files):
            if entity.file == f:
                return (index, entity.id())
        return (-1, entity.id())

    if one_object:
        return {side(r.source) for r in results}
    return {(side(r.source), side(r.target)) for r in results}


def time_python(factory, params, sources, targets, one_object):
    rule = factory()
    t0 = time.perf_counter()
    if one_object:
        results = rule.compute(sources, **params)
    else:
        results = rule.compute(sources, targets, **params)
    return time.perf_counter() - t0, results


def time_cpp(paths, files, rule_type, params, sources, targets, one_object, ifcview_paths=None):
    """(cold, warm, results, phase summary, .ifcview diagnostics) of one rule."""
    from engine import _ifcclash_engine as native

    selections = {"source": cpp_backend._slot(sources, files)}
    if not one_object:
        selections["target"] = cpp_backend._slot(targets, files)

    t0 = time.perf_counter()
    if ifcview_paths:
        session = native.Session(ifc_paths=paths, geometry_cache="require", ifcview_paths=ifcview_paths)
    else:
        session = native.Session(ifc_paths=paths, geometry_cache="off")
    raw = session.run(rule_type=rule_type, params=params, selections=selections)
    cold = time.perf_counter() - t0

    t1 = time.perf_counter()
    session.run(rule_type=rule_type, params=params, selections=selections)
    warm = time.perf_counter() - t1

    diagnostics = [d["message"] for d in raw["diagnostics"] if d["code"] == "ifcview_boxes"]
    session.close()
    return cold, warm, cpp_backend.to_clash_results(raw, files), raw["stats"]["summary"], diagnostics


def render(paths, ifcviews, sources, targets, python_open, rows):
    def s(value):
        return "n/a" if value is None else f"{value:.2f} s"

    def gain(reference, value):
        return "n/a" if not value else f"×{reference / value:.1f}"

    lines = [
        "# Benchmark des moteurs IfcClash_Plus",
        "",
        f"- Source : `{paths[0]}` ({len(sources)} éléments avec représentation)",
        f"- Cible : `{paths[-1]}` ({len(targets)} éléments)",
        "- .ifcview : " + (", ".join(f"`{v}`" for v in ifcviews) if all(ifcviews) else "absent (colonnes n/a)"),
        f"- Lecture des IFC par ifcopenshell (Python, une fois, hors temps des règles) : {python_open:.2f} s",
        "",
        "| Règle | Résultats | Python | C++ froid | C++ chaud | C++ .ifcview froid | C++ .ifcview chaud "
        "| Gain C++ froid | Gain .ifcview froid | Mêmes paires |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        same = r["cpp_same_pairs"] and r.get("ifcview_same_pairs", True)
        lines.append(
            f"| {r['rule']} | {r['results']} | {s(r['python_s'])} | {s(r['cpp_cold_s'])} | {s(r['cpp_warm_s'])} "
            f"| {s(r.get('ifcview_cold_s'))} | {s(r.get('ifcview_warm_s'))} "
            f"| {gain(r['python_s'], r['cpp_cold_s'])} | {gain(r['python_s'], r.get('ifcview_cold_s'))} "
            f"| {'oui' if same else '**NON**'} |"
        )
    lines += ["", "Phases du moteur C++ (exécution froide) :", ""]
    for r in rows:
        lines.append(f"- IFC : `{r['cpp_stats']}`")
        if "ifcview_stats" in r:
            lines.append(f"- .ifcview : `{r['ifcview_stats']}` — {'; '.join(r['ifcview_diagnostics'])}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="IFC of the source elements")
    parser.add_argument("--target", default=DEFAULT_TARGET, help="IFC of the target elements (may be the source)")
    parser.add_argument("--rules", nargs="+", default=list(RULES), choices=list(RULES))
    parser.add_argument("--output", help="write the report (Markdown) and a .json next to it")
    args = parser.parse_args()

    if not cpp_backend.AVAILABLE:
        sys.exit("the C++ module _ifcclash_engine is not built for this Python")

    same_file = os.path.abspath(args.source) == os.path.abspath(args.target)
    paths = [args.source] if same_file else [args.source, args.target]
    ifcviews = [find_ifcview(p) for p in paths]
    has_ifcview = all(ifcviews)

    t0 = time.perf_counter()
    files = [ifcopenshell.open(p) for p in paths]
    python_open = time.perf_counter() - t0

    if len(files) == 2:
        sources, targets = products(files[0]), products(files[1])
    else:
        everything = sorted(products(files[0]), key=lambda p: p.id())
        sources, targets = everything[0::2], everything[1::2]

    rows = []
    for rule_type in args.rules:
        factory, params = RULES[rule_type]
        one_object = rule_type == "Volume"
        elements = sources + targets if one_object else sources
        rule_targets = None if one_object else targets
        print(f"{rule_type}...", file=sys.stderr, flush=True)

        py_time, py_results = time_python(factory, params, elements, rule_targets, one_object)
        c_cold, c_warm, c_results, c_stats, _ = time_cpp(
            paths, files, rule_type, params, elements, rule_targets, one_object
        )
        reference = key_set(py_results, one_object, files)
        row = {
            "rule": rule_type,
            "params": params,
            "results": len(py_results),
            "python_s": py_time,
            "cpp_cold_s": c_cold,
            "cpp_warm_s": c_warm,
            "cpp_stats": c_stats,
            "cpp_same_pairs": reference == key_set(c_results, one_object, files),
        }
        if has_ifcview:
            v_cold, v_warm, v_results, v_stats, v_diag = time_cpp(
                paths, files, rule_type, params, elements, rule_targets, one_object, ifcviews
            )
            row.update(
                {
                    "ifcview_cold_s": v_cold,
                    "ifcview_warm_s": v_warm,
                    "ifcview_stats": v_stats,
                    "ifcview_diagnostics": v_diag,
                    "ifcview_same_pairs": reference == key_set(v_results, one_object, files),
                }
            )
        rows.append(row)

    report = render(paths, ifcviews, sources, targets, python_open, rows)
    print(report)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as out:
            out.write(report)
        with open(os.path.splitext(args.output)[0] + ".json", "w", encoding="utf-8") as out:
            json.dump({"models": paths, "ifcview": ifcviews, "python_open_s": python_open, "rows": rows}, out, indent=2)

    if not all(r["cpp_same_pairs"] and r.get("ifcview_same_pairs", True) for r in rows):
        sys.exit("PARITY GAP: an engine returned other pairs than the Python engine (see the report)")


if __name__ == "__main__":
    main()
