"""The C++ backend: libifcclash_engine through its pybind11 module.

One engine Session per set of IFC files, kept for the whole RuleFile run
(parse and geometry conversion happen once), released by close_sessions().

Exchange (SPEC "Interface Python / C++"):
- in: the rule type, its engine parameters (catalogue keys) and, per slot,
  the selected elements of each file. The STEP ids are sent: both sides
  parse the same file, so the id is exact even for a duplicated GlobalId;
- out: ResultRecords in the ResultInfo.to_dict() shape, rebuilt here into
  the usual ClashResult objects — the management pipeline, the JSON export
  and the IPC do not change.
"""

import os

from registry import engine_params

try:
    from engine import _ifcclash_engine as _native
except ImportError:  # module not built, or built for another Python
    _native = None

AVAILABLE = _native is not None

# The results of the C++ engine are sorted by (source, target); the
# measures that the result record may carry (ResultInfo vocabulary).
_MEASURES = (
    "distance",
    "penetration_depth",
    "contact_area",
    "ratio",
    "offset",
    "hit_ratio",
    "angle",
    "volume",
    "area",
)

_sessions = {}


class Unsupported(Exception):
    """The call cannot go through the C++ engine (module missing, rule
    not ported, files unknown): the orchestrator falls back on Python."""


_implemented = None


def implemented_rules():
    """The rule types the C++ module implements."""
    global _implemented
    if _native is None:
        return set()
    if _implemented is None:
        import json

        _implemented = {rule["type"] for rule in json.loads(_native.catalogue_json())["rules"]}
    return _implemented


def session_for(paths):
    """The Session of a set of files, opened once (per RuleFile)."""
    if _native is None:
        raise Unsupported("the C++ module _ifcclash_engine is not available")
    key = tuple(os.path.abspath(p) for p in paths)
    session = _sessions.get(key)
    if session is None or session.closed:
        session = _native.Session(
            ifc_paths=list(key),
            geometry_cache=os.environ.get("IFCCLASH_GEOMETRY_CACHE", "off"),
        )
        _sessions[key] = session
    return session


def close_sessions():
    """Releases every open Session (end of a RuleFile run)."""
    for session in _sessions.values():
        session.close()
    _sessions.clear()


def _files_of(rule):
    """(paths, files) of the rule: the selects carry them in parallel."""
    select = rule.select_source
    paths = list(getattr(select, "list_ifc_path", None) or [])
    files = list(getattr(select, "list_ifc_file", None) or [])
    if not paths or len(paths) != len(files):
        raise Unsupported("the rule files have no path")
    return paths, files


def _file_index(ifc_file, files):
    for index, candidate in enumerate(files):
        if candidate is ifc_file or candidate == ifc_file:
            return index
    raise Unsupported("an element belongs to a file the rule does not know")


def _slot(elements, files):
    """The per-file selection of one slot (STEP ids, in input order)."""
    by_file = {}
    for element in elements or []:
        by_file.setdefault(_file_index(element.file, files), []).append(element.id())
    return [{"file_index": i, "entity_ids": ids} for i, ids in sorted(by_file.items())]


def run(rule_type, params, files_paths, files, sources, targets=None, prefilter=True, context=None):
    """Run one rule on the C++ engine and return its raw result dict."""
    selections = {"source": _slot(sources, files)}
    if targets is not None:
        selections["target"] = _slot(targets, files)
    if context is not None:
        selections["context"] = _slot(context, files)
    session = session_for(files_paths)
    return session.run(
        rule_type=rule_type,
        params=params,
        selections=selections,
        mode="verdicts",
        prefilter=prefilter,
    )


def to_clash_results(raw, files):
    """The ClashResult objects of a raw C++ result (the adapter)."""
    # Imported here: RuleClass imports the orchestrator, which imports
    # this module.
    from RuleClass import ClashResultOneObject, ClashResultTwoObjects

    results = []
    for record in raw["results"]:
        source = files[record["source"]["file_index"]].by_id(record["source"]["entity_id"])
        if record["target"] is None:
            result = ClashResultOneObject(source=source, state=record["status"])
        else:
            target = files[record["target"]["file_index"]].by_id(record["target"]["entity_id"])
            result = ClashResultTwoObjects(source=source, target=target, state=record["status"])
        info = record["info"]
        # The measures in their order of pose (the first is the nominal one).
        for name, measure in info.get("measure", {}).items():
            if name in _MEASURES:
                setattr(result.info, name, measure["value"])
        for point in info.get("points", []):
            result.info.add_point_pair(
                tuple(point["source"]), tuple(point["target"]), label=point.get("label")
            )
        _fill_blocks(result.info, info)
        results.append(result)
    return results


def _point(value):
    return tuple(float(c) for c in value)


def _face(face):
    return (
        _point(face["normal"]),
        face["area"],
        [tuple(_point(p) for p in triangle) for triangle in face["triangles"]],
    )


def _obb(obb):
    return (
        _point(obb["center"]),
        tuple(_point(axis) for axis in obb["axes"]),
        _point(obb["half_sizes"]),
        obb.get("label"),
    )


def _fill_blocks(target, info):
    """The blocks of ResultInfo.to_dict() other than measure / points,
    back into the ResultInfo (same tuples as the Python rules pose)."""
    from RuleClass import RaycastData, ZoneData

    for face in info.get("faces", []):
        target.add_face_pair(_face(face["source"]), _face(face["target"]))
    volumes = info.get("volumes", {})
    for name, attribute in (
        ("intersection", "volume_intersection"),
        ("ratio", "volume_ratio"),
        ("containment", "containment_ratio"),
        ("clearance_violated", "clearance_violated_volume"),
    ):
        if name in volumes:
            setattr(target, attribute, volumes[name])
    obbs = info.get("obbs", {})
    for obb in obbs.get("source", []):
        target.add_source_obb(_obb(obb))
    for obb in obbs.get("target", []):
        target.add_target_obb(_obb(obb))
    if "axis" in info:
        target.axis_mode = info["axis"]["mode"]
        target.axis_degraded = info["axis"]["degraded"]
    if "raycast" in info:
        r = info["raycast"]
        target.raycast = RaycastData(
            r["planned"],
            r["cast"],
            r["hit"],
            [(_point(a), _point(b)) for a, b in r["hit_segments"]],
            [(_point(a), _point(b)) for a, b in r["blocked_segments"]],
        )
    if "zone" in info:
        z = info["zone"]
        target.zone = ZoneData(z["side"], z["leaf"], z["width"], z["depth"], z["height"])
    for axis in info.get("axes", []):
        target.add_axis((_point(axis["center"]), _point(axis["direction"]), axis["length"], axis.get("label")))


def compute(rule, sources, targets=None, context=None):
    """The C++ counterpart of python_backend.compute."""
    if _native is None:
        raise Unsupported("the C++ module _ifcclash_engine is not available")
    rule_type = type(rule).__name__
    if getattr(rule, "state", None) in ("Display_Input", "Display_Result"):
        # The display geometries some rules emit from compute() are not
        # ported: the display states stay on the Python engine.
        raise Unsupported(f"{rule_type}: display states run on the Python engine")
    if rule_type not in implemented_rules():
        raise Unsupported(f"{rule_type}: not ported to C++ yet")
    paths, files = _files_of(rule)
    params = {name: getattr(rule, name) for name in engine_params(rule_type)}
    raw = run(
        rule_type,
        params,
        paths,
        files,
        sources,
        targets if hasattr(rule, "select_target") else None,
        context=context,
    )
    return to_clash_results(raw, files)
