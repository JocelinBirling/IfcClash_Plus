"""Strict parity of the C++ engine with the Python engine
(SPEC_OptimisationInCPP, "Validation" and "Tests").

For every rule ported to C++ (Volume, Intersection, Clearance, Collision),
on every model of IFC_Test_Model and on the Duplex architecture model,
both backends run on the same element lists and must return exactly the
same pairs, rule by rule; the measures and points must agree within the
documented tolerance. Any gap is a bug.

Two selections per model:
- disjoint: the products sorted by id, even ones as source, odd ones as
  target (the usual IDS case: two different families);
- overlapping: source = target = every product. The Python tree tests a
  pair met twice once, in an orientation that depends on its traversal
  order: the pairs are compared unordered in that case.

Prudence of the prefilters: the C++ results with prefilter="off" (no broad,
no mid phase) must be identical to the default ones.

Skipped when the C++ module is not built for the running interpreter.
IFCCLASH_PARITY_FULL=1 runs every calibrated model (one in five by
default); IFCCLASH_PARITY_HEAVY=1 adds the large Duplex models (MEP,
Plumbing...).

Execution (from the repository root, in the ifcclash_cpp environment):
    PYTHONNOUSERSITE=1 python -m pytest tests/test_parity_cpp.py -v
"""
import glob
import math
import os
import sys

import pytest

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell
import ifcopenshell.geom

from engine.backends import cpp_backend
from Rules import Clearance, Collision, Intersection, Volume

pytestmark = pytest.mark.skipif(
    not cpp_backend.AVAILABLE, reason="the C++ module _ifcclash_engine is not built for this Python"
)

# Documented parity tolerance per measure (absolute, metres / m3). The
# narrow phase of the tree rules is the same IfcOpenShell code on both
# sides, and the volume uses the same formula on the same vertices: the
# values are expected equal, the tolerance only absorbs float noise.
TOLERANCE = {"distance": 1e-9, "volume": 1e-9}
POINT_TOLERANCE = 1e-9

# Every calibrated model holds the same set of reference objects in a
# different layout, and its geometry costs a few seconds per Python call:
# by default one model in five, IFCCLASH_PARITY_FULL=1 runs them all.
_CALIBRATED = sorted(glob.glob("IFC_Test_Model/IFC_Model/*.ifc"))
MODELS = (_CALIBRATED if os.environ.get("IFCCLASH_PARITY_FULL") else _CALIBRATED[::5]) + [
    "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc",
]
if os.environ.get("IFCCLASH_PARITY_HEAVY"):
    MODELS += [
        "Ifc_Model/Ifc2s3_Duplex_Electrical.ifc",
        "Ifc_Model/Ifc2x3_Duplex_Mechanical.ifc",
        "Ifc_Model/Ifc2x3_Duplex_MEP.ifc",
        "Ifc_Model/Ifc2x3_Duplex_Plumbing.ifc",
    ]

# (rule type, Python rule factory, engine parameters)
CASES = [
    ("Volume", lambda: Volume(None, 0.5, 1.5), {"volume_min": 0.5, "volume_max": 1.5}),
    ("Volume", lambda: Volume(None, 0.0, 1e9), {"volume_min": 0.0, "volume_max": 1e9}),
    ("Intersection", lambda: Intersection(None, None), {"tolerance": 0.1}),
    ("Intersection", lambda: Intersection(None, None), {"tolerance": 0.002}),
    ("Clearance", lambda: Clearance(None, None), {"clearance": 0.05, "check_all": False}),
    ("Clearance", lambda: Clearance(None, None), {"clearance": 0.5, "check_all": True}),
    ("Collision", lambda: Collision(None, None), {"allow_touching": False}),
    ("Collision", lambda: Collision(None, None), {"allow_touching": True}),
]

_files = {}


def _file(path):
    if path not in _files:
        _files[path] = ifcopenshell.open(path)
    return _files[path]


def _products(ifc_file):
    products = [p for p in ifc_file.by_type("IfcProduct") if p.Representation is not None]
    return sorted(products, key=lambda p: p.id())


def _selections(ifc_file):
    products = _products(ifc_file)
    yield "disjoint", products[0::2], products[1::2]
    yield "overlapping", products, products


def _key(result, unordered):
    source = result.source.id()
    target = result.target.id() if hasattr(result, "target") else None
    if unordered and target is not None:
        return tuple(sorted((source, target)))
    return (source, target)


def _signature(result):
    info = result.info
    measures = {name: getattr(info, name) for name in info._measure_order}
    points = sorted(
        (tuple(float(c) for c in s.point), tuple(float(c) for c in t.point))
        for s, t in zip(info.source_points, info.target_points)
    )
    return measures, points


def _points_close(a, b, unordered):
    if len(a) != len(b):
        return False
    for (s1, t1), (s2, t2) in zip(a, b):
        direct = all(math.isclose(x, y, abs_tol=POINT_TOLERANCE) for x, y in zip(s1 + t1, s2 + t2))
        swapped = all(math.isclose(x, y, abs_tol=POINT_TOLERANCE) for x, y in zip(s1 + t1, t2 + s2))
        if not (direct or (unordered and swapped)):
            return False
    return True


def _compare(label, python_results, cpp_results, unordered, recheck=None):
    """Same pairs, same measures, same points. With overlapping lists
    (unordered), a pair is tested in one orientation chosen by the
    traversal order of the Python tree, and the measures of the tree are
    not symmetric: a measure gap is then re-checked against the Python
    engine run on that single pair, in the orientation of the C++ record
    (recheck)."""
    faults = []
    py = {}
    for r in python_results:
        py.setdefault(_key(r, unordered), r)
    cpp = {_key(r, unordered): r for r in cpp_results}
    if len(cpp) != len(cpp_results):
        faults.append(f"{label}: the C++ engine returned a pair twice")
    missing = sorted(set(py) - set(cpp))
    extra = sorted(set(cpp) - set(py))
    if missing:
        faults.append(f"{label}: pairs missing in C++ {missing}")
    if extra:
        faults.append(f"{label}: extra pairs in C++ {extra}")
    for key in sorted(set(py) & set(cpp)):
        m_py, p_py = _signature(py[key])
        m_cpp, p_cpp = _signature(cpp[key])
        if recheck is not None and not _same(m_py, p_py, m_cpp, p_cpp):
            single = recheck(cpp[key])
            if len(single) == 1:
                m_py, p_py = _signature(single[0])
        if list(m_py) != list(m_cpp):
            faults.append(f"{label} {key}: measures {list(m_py)} != {list(m_cpp)}")
            continue
        for name, value in m_py.items():
            if not math.isclose(value, m_cpp[name], abs_tol=TOLERANCE.get(name, 1e-9)):
                faults.append(f"{label} {key}: {name} {value} != {m_cpp[name]}")
        if not _points_close(p_py, p_cpp, unordered):
            faults.append(f"{label} {key}: points {p_py} != {p_cpp}")
    return faults


def _same(m1, p1, m2, p2):
    return (
        list(m1) == list(m2)
        and all(math.isclose(v, m2[n], abs_tol=TOLERANCE.get(n, 1e-9)) for n, v in m1.items())
        and _points_close(p1, p2, unordered=False)
    )


def _python_compute(factory, rule_type, params, sources, targets):
    rule = factory()
    if rule_type == "Volume":
        return rule.compute(sources, **params)
    return rule.compute(sources, targets, **params)


def _cpp_compute(path, ifc_file, rule_type, params, sources, targets, prefilter=True):
    raw = cpp_backend.run(
        rule_type,
        params,
        [path],
        [ifc_file],
        sources,
        None if rule_type == "Volume" else targets,
        prefilter=prefilter,
    )
    return cpp_backend.to_clash_results(raw, [ifc_file])


@pytest.fixture(scope="module", autouse=True)
def _close_sessions():
    yield
    cpp_backend.close_sessions()


@pytest.mark.parametrize(
    "rule_type,factory,params", CASES, ids=[f"{c[0]}-{list(c[2].values())}" for c in CASES]
)
def test_parity(rule_type, factory, params):
    faults = []
    for path in MODELS:
        ifc_file = _file(path)
        for mode, sources, targets in _selections(ifc_file):
            if rule_type == "Volume" and mode == "overlapping":
                continue  # one-object rule: the source list is enough
            label = f"{os.path.basename(path)} [{mode}]"
            python_results = _python_compute(factory, rule_type, params, sources, targets)
            cpp_results = _cpp_compute(path, ifc_file, rule_type, params, sources, targets)
            unordered = mode == "overlapping"

            def recheck(record):
                return _python_compute(factory, rule_type, params, [record.source], [record.target])

            faults += _compare(
                label, python_results, cpp_results, unordered, recheck if unordered else None
            )
    assert not faults, "\n".join(faults[:40]) + (f"\n... {len(faults)} faults" if len(faults) > 40 else "")


@pytest.mark.parametrize("rule_type,factory,params", CASES[2:], ids=[c[0] + "-" + str(list(c[2].values())) for c in CASES[2:]])
def test_prefilters_only_remove(rule_type, factory, params):
    faults = []
    for path in [m for m in MODELS if m.startswith("IFC_Test_Model")]:  # small: N×M narrow tests
        ifc_file = _file(path)
        for mode, sources, targets in _selections(ifc_file):
            label = f"{os.path.basename(path)} [{mode}] prefilter off"
            on = _cpp_compute(path, ifc_file, rule_type, params, sources, targets)
            off = _cpp_compute(path, ifc_file, rule_type, params, sources, targets, prefilter=False)
            faults += _compare(label, on, off, unordered=False)
    assert not faults, "\n".join(faults[:40])
