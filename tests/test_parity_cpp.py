"""Strict parity of the C++ engine with the Python engine
(SPEC_OptimisationInCPP, "Validation").

The Python results are references computed once by
scripts/make_parity_golden.py (tests/parity_golden/); this test runs the
C++ engine only, on the same models and selections (tests/parity_cases.py),
and compares: same pairs (or elements), same info blocks (measures, points,
faces, OBBs, axes, zones, rays), floats within 1e-9. Any gap is a bug.

Overlapping lists (source = target): the Python tree (Intersection,
Clearance, Collision) tests a pair met twice once, in an orientation of its
own; the pairs are compared unordered and the measures against the
reference of the pair alone in the C++ orientation.

Prudence of the prefilters: the C++ results with prefilter=False (no broad,
no mid phase) must be identical (C++ only, no reference needed).

Execution (repository root, ifcclash_cpp environment):
    PYTHONNOUSERSITE=1 python scripts/make_parity_golden.py   # once, or after a Python change
    PYTHONNOUSERSITE=1 python -m pytest tests/test_parity_cpp.py -q
"""
import json
import math
import os
import sys

import pytest

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell  # noqa: E402

from engine.backends import cpp_backend  # noqa: E402
from tests.parity_cases import CASES, GOLDEN_DIR, TREE_RULES, case_id, selections  # noqa: E402

pytestmark = pytest.mark.skipif(
    not cpp_backend.AVAILABLE, reason="the C++ module _ifcclash_engine is not built for this Python"
)

_files = {}


def _file(path):
    if path not in _files:
        _files[path] = ifcopenshell.open(path)
    return _files[path]


@pytest.fixture(scope="module", autouse=True)
def _close_sessions():
    yield
    cpp_backend.close_sessions()


def _cpp(model, case, sources, targets, context, prefilter=True):
    ifc_file = _file(model)
    raw = cpp_backend.run(case[0], case[3], [model], [ifc_file], sources, targets, prefilter=prefilter,
                          context=context)
    out = []
    for r in cpp_backend.to_clash_results(raw, [ifc_file]):
        target = getattr(r, "target", None)
        out.append({"source": r.source.id(), "target": target.id() if target is not None else None,
                    "info": json.loads(json.dumps(r.info.to_dict()))})
    return out


def _close(a, b, path, faults, tolerance=1e-9):
    if isinstance(a, dict) and isinstance(b, dict):
        if list(a) != list(b):
            faults.append(f"{path}: keys {list(a)} != {list(b)}")
            return
        for k in a:
            _close(a[k], b[k], f"{path}.{k}", faults, tolerance)
    elif isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            faults.append(f"{path}: {len(a)} items != {len(b)}")
            return
        for i, (x, y) in enumerate(zip(a, b)):
            _close(x, y, f"{path}[{i}]", faults, tolerance)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) and not isinstance(b, bool):
        if not math.isclose(float(a), float(b), rel_tol=1e-9, abs_tol=tolerance):
            faults.append(f"{path}: {a!r} != {b!r}")
    elif a != b:
        faults.append(f"{path}: {a!r} != {b!r}")


def _group(records, unordered):
    out = {}
    for r in records:
        key = (r["source"], r["target"])
        if unordered and r["target"] is not None:
            key = tuple(sorted(key))
        out.setdefault(key, []).append(r)
    if unordered:
        out = {k: v[:1] for k, v in out.items()}
    return out


def _compare(label, reference, cpp, unordered, single=None):
    faults = []
    py, cc = _group(reference, unordered), _group(cpp, unordered)
    missing, extra = sorted(set(py) - set(cc), key=str), sorted(set(cc) - set(py), key=str)
    if missing:
        faults.append(f"{label}: missing in C++ {missing}")
    if extra:
        faults.append(f"{label}: extra in C++ {extra}")
    for key in sorted(set(py) & set(cc), key=str):
        if len(py[key]) != len(cc[key]):
            faults.append(f"{label} {key}: {len(py[key])} results != {len(cc[key])}")
            continue
        for n, (p, c) in enumerate(zip(py[key], cc[key])):
            gaps = []
            _close(p["info"], c["info"], f"{label} {key}#{n}", gaps)
            if gaps and single is not None:
                alone = single.get(f"{key[0]}-{key[1]}", [])
                if len(alone) == 1:
                    gaps = []
                    _close(alone[0]["info"], c["info"], f"{label} {key} (pair alone)", gaps)
            faults += gaps
    return faults


def _golden(case):
    path = os.path.join(GOLDEN_DIR, case_id(case) + ".json")
    if not os.path.exists(path):
        pytest.skip(f"no reference {os.path.basename(path)}: run scripts/make_parity_golden.py {case[0]}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@pytest.mark.parametrize("case", CASES, ids=[case_id(c) for c in CASES])
def test_parity(case):
    golden = _golden(case)
    faults = []
    for model, modes in golden["models"].items():
        ifc_file = _file(model)
        for mode, sources, targets, context in selections(ifc_file, case[1]):
            if mode not in modes:
                continue
            unordered = mode == "overlapping" and case[0] in TREE_RULES
            cpp = _cpp(model, case, sources, targets, context)
            faults += _compare(f"{os.path.basename(model)} [{mode}]", modes[mode]["results"], cpp, unordered,
                               modes[mode].get("single"))
    assert not faults, "\n".join(faults[:40]) + (f"\n... {len(faults)} faults" if len(faults) > 40 else "")


PREFILTERED = [c for c in CASES if c[1] == "pair"]


@pytest.mark.parametrize("case", PREFILTERED, ids=[case_id(c) for c in PREFILTERED])
def test_prefilters_only_remove(case):
    from tests.parity_cases import MODELS

    faults = []
    for model in MODELS:
        ifc_file = _file(model)
        for mode, sources, targets, context in selections(ifc_file, case[1]):
            on = _cpp(model, case, sources, targets, context)
            off = _cpp(model, case, sources, targets, context, prefilter=False)
            faults += _compare(f"{os.path.basename(model)} [{mode}] prefilter off", on, off, unordered=False)
    assert not faults, "\n".join(faults[:40])


# The rules whose per-element work runs on several threads
# (RuleBase::parallel_safe): the results must not depend on the number of
# threads, nor on the Session cache shared between runs (second run).
THREADED = [c for c in CASES if c[0] in (
    "Volume", "Area", "TopOrBottomSurface", "LateralSurface", "ProjectedSurface", "ObbHigh", "ObbLength",
    "Orientation", "Above", "Below", "OBB_Above", "OBB_Below", "OBB_Front_And_Back", "OBB_Custom",
    "AngleBetween", "ClearanceAxisToAxis", "Intersection2", "SurfaceRecover")]


def _raw(session, files, case, sources, targets, context):
    selections = {"source": cpp_backend._slot(sources, files)}
    if targets is not None:
        selections["target"] = cpp_backend._slot(targets, files)
    if context is not None:
        selections["context"] = cpp_backend._slot(context, files)
    return json.dumps(session.run(rule_type=case[0], params=case[3], selections=selections)["results"],
                      sort_keys=True)


@pytest.mark.parametrize("case", THREADED, ids=[case_id(c) for c in THREADED])
def test_threads_and_session_cache_change_nothing(case):
    from engine import _ifcclash_engine as native
    from tests.parity_cases import MODELS

    for model in MODELS:
        files = [_file(model)]
        for mode, sources, targets, context in selections(files[0], case[1]):
            with_threads = native.Session(ifc_paths=[model], geometry_cache="off")
            sequential = native.Session(ifc_paths=[model], geometry_cache="off", rule_threads=1)
            try:
                first = _raw(with_threads, files, case, sources, targets, context)
                again = _raw(with_threads, files, case, sources, targets, context)  # from the Session cache
                alone = _raw(sequential, files, case, sources, targets, context)
            finally:
                with_threads.close()
                sequential.close()
            assert first == alone, f"{os.path.basename(model)} [{mode}]: threads change the results"
            assert first == again, f"{os.path.basename(model)} [{mode}]: the Session cache changes the results"
