# This file was generated with the assistance of an AI coding tool.
"""Export of the engine's data to JSON-safe dictionaries for the IPC
protocol: element cross-references and clash results.

An element is never exported as an OCC or ifcopenshell object: it becomes
a cross-reference (model index + STEP id + display fields) the client
joins against its own element registry. The result payload carries the
common core (id, type, status, criticity, actor) and the info blocks
(ResultInfo.to_dict, doc/specification_ResultData.md section 4).
"""

from typing import Any


def element_ref(entity, model_of_file: dict[int, int]) -> dict[str, Any] | None:
    """The cross-reference of one IFC entity, or None when unresolvable."""
    if entity is None:
        return None
    try:
        step_id = entity.id()
    except Exception:
        return None

    model = None
    ifc_file = getattr(entity, "file", None)
    if ifc_file is not None:
        model = model_of_file.get(id(ifc_file))
        if model is None:
            # The wrapper identity may differ: match by pathname
            # (ifcopenshell < 0.9) or by the underlying file pointer
            # (ifcopenshell >= 0.9, where file.pathname no longer
            # exists and every entity.file access builds a fresh
            # wrapper).
            pathname = getattr(ifc_file, "pathname", None)
            if pathname:
                model = model_of_file.get(("path", pathname))
        if model is None:
            # ifcopenshell >= 0.9: join by the underlying parse file
            # pointer, shared by every wrapper of the same file.
            file_pointer = getattr(ifc_file, "file_pointer", None)
            if file_pointer is not None:
                model = model_of_file.get(("fp", file_pointer()))

    ref: dict[str, Any] = {"step_id": step_id, "ifc_type": entity.is_a()}
    if model is not None:
        ref["model"] = model
    global_id = getattr(entity, "GlobalId", None)
    if global_id:
        ref["global_id"] = global_id
    name = getattr(entity, "Name", None)
    if name:
        ref["name"] = name
    return ref


def _refs(entities, model_of_file) -> list[dict[str, Any]]:
    refs = [element_ref(entity, model_of_file) for entity in entities or []]
    return [ref for ref in refs if ref is not None]


def _rule_type(rule) -> str:
    """The rule's type: self.type, falling back to the class name (some
    rules, ex. OBB_Above, never set self.type)."""
    return getattr(rule, "type", None) or type(rule).__name__


def result_to_dict(result, rule, model_of_file: dict[int, int]) -> dict[str, Any]:
    """One ClashResult (OneObject, TwoObjects or Complex) as JSON."""
    data: dict[str, Any] = {
        "id": result.id,
        "type": result.type,
        "rule": getattr(result, "rule_name", None) or _rule_type(rule),
        "rule_type": _rule_type(rule),
        "node_id": rule.id,
        "status": bool(result.status),
        "criticity": list(getattr(result, "criticity", []) or []),
        "actor": list(getattr(result, "actor", []) or []),
    }

    if hasattr(result, "sources"):
        # ClashResultComplex: the group is the result, an atomic whole.
        data["sources"] = _refs(result.sources, model_of_file)
        data["targets"] = _refs(result.targets, model_of_file)
        if getattr(result, "context", None):
            data["context"] = _refs(result.context, model_of_file)
    else:
        source = element_ref(getattr(result, "source", None), model_of_file)
        if source is not None:
            data["source"] = source
        target = element_ref(getattr(result, "target", None), model_of_file)
        if target is not None:
            data["target"] = target

    info = getattr(result, "info", None)
    if info is not None and hasattr(info, "to_dict"):
        info_dict = info.to_dict()
        if info_dict:
            data["info"] = info_dict

    return data


def results_to_dicts(results, rule, model_of_file) -> list[dict[str, Any]]:
    return [result_to_dict(result, rule, model_of_file) for result in results or []]
