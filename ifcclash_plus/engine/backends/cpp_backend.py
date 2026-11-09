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


def implemented_rules():
    """The rule types the C++ module implements."""
    if _native is None:
        return set()
    import json

    return {rule["type"] for rule in json.loads(_native.catalogue_json())["rules"]}


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


def run(rule_type, params, files_paths, files, sources, targets=None, prefilter=True):
    """Run one rule on the C++ engine and return its raw result dict."""
    selections = {"source": _slot(sources, files)}
    if targets is not None:
        selections["target"] = _slot(targets, files)
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
        results.append(result)
    return results


def compute(rule, sources, targets=None, context=None):
    """The C++ counterpart of python_backend.compute."""
    if _native is None:
        raise Unsupported("the C++ module _ifcclash_engine is not available")
    rule_type = type(rule).__name__
    if context:
        raise Unsupported(f"{rule_type}: the context pipeline is not ported yet")
    paths, files = _files_of(rule)
    params = {name: getattr(rule, name) for name in engine_params(rule_type)}
    raw = run(rule_type, params, paths, files, sources, targets if hasattr(rule, "select_target") else None)
    return to_clash_results(raw, files)
