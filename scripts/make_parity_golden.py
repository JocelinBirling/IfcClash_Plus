"""Generate the parity references of the C++ engine: the Python engine is
run ONCE per case (tests/parity_cases.py), in parallel over all the cores,
and its results are written to tests/parity_golden/<case>.json.

tests/test_parity_cpp.py then runs the C++ engine only and compares with
these references: seconds instead of the tens of minutes the Python engine
takes. Regenerate after a change of the Python rules (or of the cases).

Usage (repository root, ifcclash_cpp environment):
    PYTHONNOUSERSITE=1 python scripts/make_parity_golden.py            # every case
    PYTHONNOUSERSITE=1 python scripts/make_parity_golden.py Above Below  # some rules
    IFCCLASH_PARITY_FULL=1 ...                                         # every calibrated model
"""
import json
import multiprocessing
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from tests.parity_cases import CASES, GOLDEN_DIR, MODELS, TREE_RULES, case_id, selections  # noqa: E402

_files = {}


def _file(path):
    import ifcopenshell

    if path not in _files:
        _files[path] = ifcopenshell.open(os.path.join(ROOT, path))
    return _files[path]


def _jsonable(value):
    return json.loads(json.dumps(value))


def _record(result):
    target = getattr(result, "target", None)
    return {
        "source": result.source.id(),
        "target": target.id() if target is not None else None,
        "info": _jsonable(result.info.to_dict()),
    }


def _compute(case, sources, targets, context):
    rule_type, kind, factory, params = case
    rule = factory()
    extra = {"liste_objet_contexte": context} if context is not None else {}
    if kind in ("one", "one_ctx"):
        return rule.compute(sources, **params, **extra)
    return rule.compute(sources, targets, **params, **extra)


def _task(arguments):
    index, model = arguments
    case = CASES[index]
    ifc_file = _file(model)
    out = {}
    started = time.perf_counter()
    for mode, sources, targets, context in selections(ifc_file, case[1]):
        results = _compute(case, sources, targets, context)
        entry = {"results": [_record(r) for r in results]}
        if case[0] in TREE_RULES and mode == "overlapping":
            # The Python tree tests a pair met twice in an orientation of its
            # own; the C++ engine keeps (lower id, higher id): the reference
            # of that orientation, computed on the pair alone.
            single = {}
            for r in results:
                a, b = sorted((r.source.id(), r.target.id()))
                key = f"{a}-{b}"
                if key not in single:
                    alone = _compute(case, [ifc_file.by_id(a)], [ifc_file.by_id(b)], None)
                    single[key] = [_record(x) for x in alone]
            entry["single"] = single
        out[mode] = entry
    return index, model, out, time.perf_counter() - started


def main():
    wanted = set(sys.argv[1:])
    indices = [i for i, c in enumerate(CASES) if not wanted or c[0] in wanted]
    tasks = [(i, m) for i in indices for m in MODELS]
    os.makedirs(GOLDEN_DIR, exist_ok=True)
    golden = {i: {"case": case_id(CASES[i]), "rule": CASES[i][0], "params": CASES[i][3], "models": {}} for i in indices}
    started = time.perf_counter()
    # fork: the workers inherit the imported modules; one task per (case, model).
    with multiprocessing.get_context("fork").Pool(multiprocessing.cpu_count()) as pool:
        for done, (index, model, out, seconds) in enumerate(pool.imap_unordered(_task, tasks), 1):
            golden[index]["models"][model] = out
            print(f"[{done}/{len(tasks)}] {CASES[index][0]} {os.path.basename(model)}  {seconds:.1f} s", flush=True)
    for index, data in golden.items():
        with open(os.path.join(GOLDEN_DIR, data["case"] + ".json"), "w", encoding="utf-8") as f:
            json.dump(data, f)
    print(f"{len(indices)} case(s), {len(tasks)} task(s) in {time.perf_counter() - started:.0f} s -> {GOLDEN_DIR}")


if __name__ == "__main__":
    main()
