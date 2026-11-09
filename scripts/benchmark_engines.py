"""Speed comparison of the three engines of IfcClash_Plus, on the 28 rules
(SPEC_OptimisationInCPP, "Ordre de migration"):

    python       the compute() of the rules (Rules.py), the reference
    cpp          libifcclash_engine, geometry read from the IFC
    cpp+ifcview  libifcclash_engine, broad and mid phases on the boxes of an
                 already produced .ifcview (BonsaiViewer cache), narrow
                 phase on the IFC

Each rule runs with the parameters of its first parity case
(tests/parity_cases.py) on the same element lists for the three engines,
and the script checks that they return the same results (same elements or
pairs, same number of results each; a gap is reported, never hidden: the
exit code is non-zero).

Selections, by kind of rule:
    one       every element of the source and of the target
    one_ctx   the same, context = the same
    pair      source elements against target elements
    pair_ctx  the same, context = every element

C++ times: "cold" = a new Session (IFC parse + geometry conversion
included: what one rule costs alone in a RuleFile), "warm" = the same rule
run again in the same Session (the RuleFile cache is filled). The Python
time includes the geometry conversion of each call (the Python engine has
no cache between rules); its IFC parse (ifcopenshell.open) is timed apart.

Every run is done in a forked child process with a time limit: a Python
rule that does not finish is reported "> limit" (no parity check for it),
and does not block the other rules. The report is rewritten after each
rule.

Default models: Duplex Architecture (source) against Duplex Mechanical
(target) from IfcSampleFiles-main, whose .ifcview (v19) were produced by
BonsaiViewer.

Usage (repository root, ifcclash_cpp environment, after the C++ build):
    PYTHONNOUSERSITE=1 python scripts/benchmark_engines.py --output doc/benchmark_engines.md
    PYTHONNOUSERSITE=1 python scripts/benchmark_engines.py \\
        --source a.ifc --target b.ifc --rules Clearance Above \\
        --max-elements 100 --python-timeout 300 --output benchmark.md
"""
import argparse
import collections
import json
import multiprocessing
import os
import sys
import time
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "ifcclash_plus"))

import ifcopenshell  # noqa: E402

from engine.backends import cpp_backend  # noqa: E402
from tests.parity_cases import CASES  # noqa: E402

SAMPLES = "/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main"
DEFAULT_SOURCE = os.path.join(SAMPLES, "Ifc2x3_Duplex_Architecture.ifc")
DEFAULT_TARGET = os.path.join(SAMPLES, "Ifc2x3_Duplex_Mechanical.ifc")

# One case per rule: the first one of the parity cases.
RULES = {}
for _case in CASES:
    RULES.setdefault(_case[0], _case)

# Shared with the forked children (set in main before any fork).
STATE = {}


def find_ifcview(ifc_path):
    stem, _ = os.path.splitext(ifc_path)
    for candidate in (stem + ".ifcview", ifc_path + ".ifcview"):
        if os.path.exists(candidate):
            return candidate
    return None


def products(ifc_file):
    found = [p for p in ifc_file.by_type("IfcProduct") if p.Representation is not None]
    return sorted(found, key=lambda p: p.id())


def thin(elements, limit):
    """At most `limit` elements, taken evenly along the list."""
    if not limit or len(elements) <= limit:
        return elements
    step = len(elements) / limit
    return [elements[int(i * step)] for i in range(limit)]


def selection(kind, sources, targets):
    """(sources, targets, context) of a kind of rule."""
    everything = sources + targets
    if kind == "one":
        return everything, None, None
    if kind == "one_ctx":
        return everything, None, everything
    if kind == "pair":
        return sources, targets, None
    return sources, targets, everything


def result_keys(results, files):
    """Multiset of the (file index, STEP id) of each side: comparable across
    engines, and small enough to cross a process boundary."""

    def side(entity):
        if entity is None:
            return None
        for index, f in enumerate(files):
            if entity.file == f:
                return (index, entity.id())
        return (-1, entity.id())

    return collections.Counter((side(r.source), side(getattr(r, "target", None))) for r in results)


# --------------------------------------------------------------------------
# The runs (in a forked child)


def run_python(rule_type):
    _, kind, factory, params = RULES[rule_type]
    sources, targets, context = STATE["selections"][rule_type]
    rule = factory()
    extra = {"liste_objet_contexte": context} if context is not None else {}
    t0 = time.perf_counter()
    if kind.startswith("one"):
        results = rule.compute(sources, **params, **extra)
    else:
        results = rule.compute(sources, targets, **params, **extra)
    seconds = time.perf_counter() - t0
    return {"seconds": seconds, "keys": result_keys(results, STATE["files"])}


def run_cpp(rule_type, use_ifcview):
    from engine import _ifcclash_engine as native

    _, _, _, params = RULES[rule_type]
    sources, targets, context = STATE["selections"][rule_type]
    files, paths = STATE["files"], STATE["paths"]
    selections = {"source": cpp_backend._slot(sources, files)}
    if targets is not None:
        selections["target"] = cpp_backend._slot(targets, files)
    if context is not None:
        selections["context"] = cpp_backend._slot(context, files)

    t0 = time.perf_counter()
    if use_ifcview:
        session = native.Session(ifc_paths=paths, geometry_cache="require", ifcview_paths=STATE["ifcviews"])
    else:
        session = native.Session(ifc_paths=paths, geometry_cache="off")
    raw = session.run(rule_type=rule_type, params=params, selections=selections)
    cold = time.perf_counter() - t0

    t1 = time.perf_counter()
    session.run(rule_type=rule_type, params=params, selections=selections)
    warm = time.perf_counter() - t1

    diagnostics = [d["message"] for d in raw["diagnostics"] if d["code"] == "ifcview_boxes"]
    session.close()
    return {
        "cold": cold,
        "warm": warm,
        "keys": result_keys(cpp_backend.to_clash_results(raw, files), files),
        "stats": raw["stats"]["summary"],
        "diagnostics": diagnostics,
    }


def _child(connection, function, arguments):
    try:
        connection.send(("ok", function(*arguments)))
    except BaseException:  # noqa: BLE001 - reported to the parent
        connection.send(("error", traceback.format_exc(limit=5)))
    finally:
        connection.close()


def limited(timeout, function, *arguments):
    """("ok", value) | ("error", traceback) | ("timeout", None)."""
    context = multiprocessing.get_context("fork")
    parent, child = context.Pipe(duplex=False)
    process = context.Process(target=_child, args=(child, function, arguments))
    process.start()
    child.close()
    if parent.poll(timeout):
        try:
            outcome = parent.recv()
        except EOFError:
            outcome = ("error", f"the child died (exit code {process.exitcode})")
    else:
        outcome = ("timeout", None)
    if process.is_alive():
        process.kill()
    process.join()
    if outcome[0] == "ok" or outcome[0] == "timeout":
        return outcome
    return outcome if process.exitcode in (0, None) else ("error", f"{outcome[1]} (exit code {process.exitcode})")


# --------------------------------------------------------------------------
# The report


def render(meta, rows):
    def s(row, key):
        status = row.get(key + "_status", "ok")
        if status == "timeout":
            return f"> {row[key + '_limit']:.0f} s"
        if status == "error":
            return "erreur"
        value = row.get(key)
        if value is None:
            return "n/a"
        return f"{value:.2f} s" if value >= 0.01 else f"{value * 1000:.1f} ms"

    def gain(row, key):
        python, value = row.get("python_s"), row.get(key)
        if row.get(key + "_status", "ok") != "ok" or not value:
            return "n/a"
        if row.get("python_s_status") == "timeout":
            return f"> ×{row['python_s_limit'] / value:.0f}"
        if row.get("python_s_status", "ok") != "ok" or python is None:
            return "n/a"
        return f"×{python / value:.1f}"

    def same(row):
        verdicts = [row.get("cpp_same"), row.get("ifcview_same")]
        verdicts = [v for v in verdicts if v is not None]
        if not verdicts:
            return "non vérifié"
        return "oui" if all(verdicts) else "**NON**"

    lines = [
        "# Benchmark des moteurs IfcClash_Plus",
        "",
        f"- Source : `{meta['paths'][0]}` ({meta['sources']} éléments retenus)",
        f"- Cible : `{meta['paths'][-1]}` ({meta['targets']} éléments retenus)",
        "- .ifcview : " + (", ".join(f"`{v}`" for v in meta["ifcviews"]) if meta["has_ifcview"] else "non utilisé"),
        f"- Lecture des IFC par ifcopenshell (Python, une fois, hors temps des règles) : {meta['python_open_s']:.2f} s",
        f"- Limites : Python {meta['python_timeout']:.0f} s, C++ {meta['cpp_timeout']:.0f} s par exécution",
        "- Paramètres : premier cas de parité de chaque règle (`tests/parity_cases.py`)",
        "",
        "« Froid » : nouvelle Session (parse et conversion de la géométrie compris), le coût d'une règle seule. "
        "« Chaud » : la même règle relancée dans la même Session, le coût d'une règle de plus dans un RuleFile.",
        "",
        "| Règle | Type | Résultats | Python | C++ froid | C++ chaud | .ifcview froid | .ifcview chaud "
        "| Gain C++ froid | Gain C++ chaud | Mêmes résultats |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['rule']} | {r['kind']} | {r.get('results', 'n/a')} | {s(r, 'python_s')} | {s(r, 'cpp_cold_s')} "
            f"| {s(r, 'cpp_warm_s')} | {s(r, 'ifcview_cold_s')} | {s(r, 'ifcview_warm_s')} "
            f"| {gain(r, 'cpp_cold_s')} | {gain(r, 'cpp_warm_s')} | {same(r)} |"
        )

    totals = {}
    for key in ("python_s", "cpp_cold_s", "cpp_warm_s"):
        complete = [r for r in rows if r.get("python_s_status", "ok") == "ok" and r.get(key + "_status", "ok") == "ok"
                    and r.get(key) is not None and r.get("python_s") is not None]
        totals[key] = sum(r[key] for r in complete), len(complete)
    if totals["python_s"][1]:
        lines += [
            "",
            f"Total sur les {totals['python_s'][1]} règles où tous les moteurs ont fini : Python "
            f"{totals['python_s'][0]:.1f} s, C++ froid {totals['cpp_cold_s'][0]:.1f} s, "
            f"C++ chaud {totals['cpp_warm_s'][0]:.1f} s.",
        ]

    faults = [r for r in rows if r.get("faults")]
    if faults:
        lines += ["", "Écarts et erreurs :", ""]
        for r in faults:
            for fault in r["faults"]:
                lines.append(f"- {r['rule']} : {fault}")

    lines += ["", "Phases du moteur C++ (exécution froide) :", ""]
    for r in rows:
        if "cpp_stats" in r:
            lines.append(f"- {r['rule']}, IFC : `{r['cpp_stats']}`")
        if "ifcview_stats" in r:
            lines.append(f"- {r['rule']}, .ifcview : `{r['ifcview_stats']}` — {'; '.join(r['ifcview_diagnostics'])}")
    lines.append("")
    return "\n".join(lines)


def describe_gap(reference, other):
    missing, extra = reference - other, other - reference
    parts = []
    if missing:
        parts.append(f"{sum(missing.values())} résultats manquants (ex. {sorted(missing)[:3]})")
    if extra:
        parts.append(f"{sum(extra.values())} résultats en plus (ex. {sorted(extra)[:3]})")
    return ", ".join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", default=DEFAULT_SOURCE, help="IFC of the source elements")
    parser.add_argument("--target", default=DEFAULT_TARGET, help="IFC of the target elements (may be the source)")
    parser.add_argument("--rules", nargs="+", default=list(RULES), choices=list(RULES))
    parser.add_argument("--max-elements", type=int, default=0,
                        help="at most N elements per side, taken evenly (0 = all)")
    parser.add_argument("--python-timeout", type=float, default=900.0, help="seconds per Python run")
    parser.add_argument("--cpp-timeout", type=float, default=1800.0, help="seconds per C++ run (cold + warm)")
    parser.add_argument("--no-ifcview", action="store_true", help="skip the cpp+ifcview engine")
    parser.add_argument("--output", help="write the report (Markdown) and a .json next to it")
    args = parser.parse_args()

    if not cpp_backend.AVAILABLE:
        sys.exit("the C++ module _ifcclash_engine is not built for this Python")

    same_file = os.path.abspath(args.source) == os.path.abspath(args.target)
    paths = [args.source] if same_file else [args.source, args.target]
    ifcviews = [find_ifcview(p) for p in paths]
    has_ifcview = all(ifcviews) and not args.no_ifcview

    t0 = time.perf_counter()
    files = [ifcopenshell.open(p) for p in paths]
    python_open = time.perf_counter() - t0

    if len(files) == 2:
        sources, targets = products(files[0]), products(files[1])
    else:
        everything = products(files[0])
        sources, targets = everything[0::2], everything[1::2]
    sources, targets = thin(sources, args.max_elements), thin(targets, args.max_elements)

    STATE.update(
        files=files,
        paths=paths,
        ifcviews=ifcviews,
        selections={rule: selection(RULES[rule][1], sources, targets) for rule in args.rules},
    )
    meta = {
        "paths": paths,
        "ifcviews": ifcviews,
        "has_ifcview": has_ifcview,
        "sources": len(sources),
        "targets": len(targets),
        "python_open_s": python_open,
        "python_timeout": args.python_timeout,
        "cpp_timeout": args.cpp_timeout,
    }

    rows = []
    for rule_type in args.rules:
        _, kind, _, params = RULES[rule_type]
        row = {"rule": rule_type, "kind": kind, "params": params, "faults": []}
        print(f"{rule_type}: python...", file=sys.stderr, flush=True)

        status, py = limited(args.python_timeout, run_python, rule_type)
        row["python_s_status"] = status
        row["python_s_limit"] = args.python_timeout
        reference = None
        if status == "ok":
            row["python_s"] = py["seconds"]
            reference = py["keys"]
            row["results"] = sum(reference.values())
        elif status == "error":
            row["faults"].append("Python : " + py.strip().splitlines()[-1])

        engines = [("cpp", False)] + ([("ifcview", True)] if has_ifcview else [])
        for name, use_ifcview in engines:
            print(f"{rule_type}: {name}...", file=sys.stderr, flush=True)
            status, out = limited(args.cpp_timeout, run_cpp, rule_type, use_ifcview)
            for key in ("cold_s", "warm_s"):
                row[f"{name}_{key}_status"] = status
                row[f"{name}_{key}_limit"] = args.cpp_timeout
            if status == "error":
                row["faults"].append(f"{name} : " + out.strip().splitlines()[-1])
                continue
            if status == "timeout":
                continue
            row[f"{name}_cold_s"], row[f"{name}_warm_s"] = out["cold"], out["warm"]
            row[f"{name}_stats"] = out["stats"]
            if use_ifcview:
                row["ifcview_diagnostics"] = out["diagnostics"]
            row.setdefault("results", sum(out["keys"].values()))
            if reference is not None:
                row[f"{name}_same"] = out["keys"] == reference
                if not row[f"{name}_same"]:
                    row["faults"].append(f"{name} : " + describe_gap(reference, out["keys"]))
        rows.append(row)

        report = render(meta, rows)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as out_file:
                out_file.write(report)
            with open(os.path.splitext(args.output)[0] + ".json", "w", encoding="utf-8") as out_file:
                json.dump(dict(meta, rows=rows), out_file, indent=2, default=str)
        summary = {k: row.get(k) for k in ("results", "python_s", "cpp_cold_s", "cpp_warm_s", "cpp_same")}
        print(f"{rule_type}: {summary} status={row['python_s_status']} faults={row['faults']}",
              file=sys.stderr, flush=True)

    print(render(meta, rows))
    gaps = [r for r in rows if r.get("cpp_same") is False or r.get("ifcview_same") is False]
    if gaps:
        sys.exit("PARITY GAP: an engine returned other results than the Python engine (see the report)")


if __name__ == "__main__":
    main()
