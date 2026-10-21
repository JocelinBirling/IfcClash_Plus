# This file was generated with the assistance of an AI coding tool.
"""The IPC server of IfcClash_Plus: a JSON Lines worker process.

Launch: ``python /path/to/ifcclash_plus/ipc.py`` (the package uses flat
imports, the script directory is on sys.path automatically).

Protocol (SPEC_IfcClash_Plus_Integration.md section 4): one JSON message
per line on stdin (requests) and stdout (replies and events), UTF-8. A
reply repeats the request id; the unsolicited events of a run (progress,
rule_start, rule_result, display, log) carry the run's job id.

Requests:
    hello     -> the engine's identity and versions
    catalogue -> the rule/facet registry (registry.py)
    run       -> run a serialized RuleFile over the session's IFC paths,
                 streaming one rule_result (or display, in preview mode)
                 event per rule, then run_done
    preview   -> run, but export the display registry instead of results
    select    -> the elements matching a serialized SelectFacet
    cancel    -> stop the run after the current rule
    shutdown  -> exit

The OCC display of the engine (state Display_Input / Display_Result) is
never triggered here: those states run as Final and their geometry is
exported through the display contract instead.
"""

import json
import os
import re
import select
import signal
import sys
import traceback
import uuid

# The package uses flat imports (from RuleClass import ...): make the
# package directory importable whatever the working directory is.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ifcopenshell  # noqa: E402

from display_export import display_items_to_json  # noqa: E402
from orchestrator import run_rule  # noqa: E402
from registry import catalogue  # noqa: E402
from result_export import (  # noqa: E402
    _rule_type,  # noqa: E402
    element_ref,
    results_to_dicts,
)
from RuleClass import RuleFolder, distribute_files  # noqa: E402
from serialization import (  # noqa: E402
    deserialize_rule_file,
    deserialize_select,
)

ENGINE_NAME = "ifcclash_plus"
ENGINE_VERSION = "dev"
CATALOGUE_VERSION = 1

# The IFC files of a session stay open between the runs of the process
# (invalidated by mtime): {abspath: (mtime, ifcopenshell.file)}.
_FILES_CACHE = {}

_CANCELLED = False
_SHUTDOWN = False


def _load_engine_version():
    global ENGINE_VERSION
    init_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "__init__.py")
    try:
        with open(init_path, encoding="utf-8") as handle:
            match = re.search(r'^__version__\s*=\s*"([^"]+)"', handle.read(), re.M)
        if match:
            ENGINE_VERSION = match.group(1)
    except OSError:
        pass


def _emit(message):
    sys.stdout.write(json.dumps(message, default=str) + "\n")
    sys.stdout.flush()


def _reply(request_id, request_type, **payload):
    _emit({"id": request_id, "type": "reply", "reply_to": request_type, **payload})


def _error(request_id, request_type, message):
    _reply(request_id, request_type, error=message)


def _event(job_id, event_type, **payload):
    _emit({"id": job_id, "type": event_type, **payload})


def _versions():
    versions = {"python": sys.version.split()[0], "ifcopenshell": getattr(ifcopenshell, "version", None)}
    try:
        import ifctester  # noqa: F401

        versions["ifctester"] = getattr(ifctester, "__version__", "unknown")
    except Exception:
        versions["ifctester"] = None
    occ_version = None
    try:
        import OCC

        occ_version = getattr(OCC, "PACKAGE_VERSION", None) or getattr(OCC, "VERSION", None)
    except Exception:
        pass
    versions["occ"] = occ_version
    return versions


def load_files(paths):
    """The opened IFC files of the paths, cached by (path, mtime)."""
    files = []
    for path in paths:
        abspath = os.path.abspath(path)
        mtime = os.path.getmtime(abspath)
        cached = _FILES_CACHE.get(abspath)
        if cached is not None and cached[0] == mtime:
            files.append(cached[1])
            continue
        _event(None, "log", level="info", message=f"Opening {abspath}")
        ifc_file = ifcopenshell.open(abspath)
        _FILES_CACHE[abspath] = (mtime, ifc_file)
        files.append(ifc_file)
    return files


def _model_index(files, paths):
    """{file identity: model index} joined by the element cross-references."""
    by_identity = {id(ifc_file): index for index, ifc_file in enumerate(files)}
    # ifcopenshell >= 0.9: every entity.file access builds a fresh
    # wrapper, the opened files are also joined by their parse file
    # pointer.
    for index, ifc_file in enumerate(files):
        file_pointer = getattr(ifc_file, "file_pointer", None)
        if file_pointer is not None:
            by_identity[("fp", file_pointer())] = index
    by_path = {("path", os.path.abspath(path)): index for index, path in enumerate(paths)}
    by_path.update(by_identity)
    return by_path


def _count_rules(items):
    total = 0
    for item in items:
        if isinstance(item, RuleFolder):
            total += _count_rules(item.contains)
        else:
            total += 1
    return total


def _export_grouping(rule, model_of_file):
    """The grouped results (GroupResult) as JSON, when a Must check ran."""
    groups = []
    for group in getattr(rule, "grouped_result", []) or []:
        groups.append(
            {
                "id": getattr(group, "id", None),
                "sources": [element_ref(element, model_of_file) for element in getattr(group, "source_set", []) or []],
                "targets": [element_ref(element, model_of_file) for element in getattr(group, "target_set", []) or []],
                "result_count": len(getattr(group, "result_group", []) or []),
            }
        )
    return groups


def _run_rule(job_id, rule, model_of_file, preview):
    if rule.id is None:
        rule.id = str(uuid.uuid4())
    _event(job_id, "rule_start", node_id=rule.id, rule_type=_rule_type(rule))

    # The OCC display states never open a window here: they run as Final
    # and their geometry goes through the display contract.
    display_requested = rule.state in ("Display_Input", "Display_Result")
    rule.state = "Final"

    try:
        # The explicit orchestration (SPEC step 4): selections ->
        # compute -> display -> pipeline -> RuleOutput.
        run_rule(rule)
        run_error = None
    except Exception as exception:  # noqa: BLE001 - the run continues rule by rule
        run_error = f"{type(exception).__name__}: {exception}"
        _event(
            job_id,
            "log",
            level="error",
            message=f"Rule {rule.type} failed: {run_error}",
            trace=traceback.format_exc(),
        )

    if preview or display_requested:
        items = display_items_to_json(rule.display_items, model_of_file)
        _event(job_id, "display", node_id=rule.id, rule_type=_rule_type(rule), items=items)
    else:
        results = results_to_dicts(rule.result, rule, model_of_file)
        event = {
            "node_id": rule.id,
            "rule_type": _rule_type(rule),
            "results": results,
        }
        grouped = _export_grouping(rule, model_of_file)
        if grouped:
            event["grouped"] = grouped
        _event(job_id, "rule_result", **event)

    return run_error


def _run_items(job_id, items, model_of_file, preview, progress):
    """Runs the rules and folders; returns (rules_done, last_error)."""
    for item in items:
        global _CANCELLED
        if _CANCELLED or _poll_cancel():
            _CANCELLED = True
            return progress

        if isinstance(item, RuleFolder):
            active = False
            try:
                active = item.check_Activation_Rule()
            except Exception as exception:  # noqa: BLE001
                _event(
                    job_id,
                    "log",
                    level="error",
                    message=f"Activation of folder {item.id} failed: {exception}",
                )
            if active:
                progress = _run_items(job_id, item.contains, model_of_file, preview, progress)
            else:
                skipped = _count_rules(item.contains)
                done, total = progress
                percent = int(100 * done / total) if total else 100
                _event(job_id, "progress", percent=percent, message=f"Folder {item.id} skipped")
                progress = (done + skipped, total)
            continue

        error = _run_rule(job_id, item, model_of_file, preview)
        done, total = progress
        done += 1
        percent = int(100 * done / total) if total else 100
        progress = (done, total)
        _event(
            job_id,
            "progress",
            percent=percent,
            message=f"{_rule_type(item)} done" if not error else f"{_rule_type(item)} failed",
        )
    return progress


def _count_results(items):
    total = 0
    for item in items:
        if isinstance(item, RuleFolder):
            total += _count_results(item.contains)
        else:
            total += len(getattr(item, "result", []) or [])
    return total


def _poll_cancel():
    """True when a cancel request sits in stdin (checked between rules).

    Reads the raw fd: sys.stdin.readline() would buffer ahead and steal
    bytes from the main loop's os.read.
    """
    try:
        readable, _, _ = select.select([sys.stdin], [], [], 0)
    except (OSError, ValueError):
        return False
    if not readable:
        return False
    try:
        chunk = os.read(sys.stdin.fileno(), 65536)
    except OSError:
        return True  # the client is gone
    if not chunk:
        return True
    for line in chunk.decode("utf-8", errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except json.JSONDecodeError:
            continue
        if message.get("type") == "cancel":
            return True
    return False


def handle_run(job_id, payload):
    paths = payload.get("list_ifc_path", [])
    preview = payload.get("mode", "run") == "preview"
    if not paths:
        _event(job_id, "run_done", cancelled=False, error="No IFC model in the session")
        return

    try:
        rule_file = deserialize_rule_file(payload.get("rule_file", {}))
    except Exception as exception:  # noqa: BLE001
        _event(job_id, "run_done", cancelled=False, error=f"Bad rule file: {exception}")
        return

    try:
        files = load_files(paths)
    except Exception as exception:  # noqa: BLE001
        _event(job_id, "run_done", cancelled=False, error=f"IFC load failed: {exception}")
        return

    rule_file.list_ifc_path = list(paths)
    rule_file.list_ifc_file = files
    # The file distribution plumbing (SPEC step 5 — the former
    # update_file_info): every select of the tree gets the files.
    for item in rule_file.contains:
        distribute_files(item, list(paths), files)
    model_of_file = _model_index(files, paths)

    global _CANCELLED
    _CANCELLED = False
    total = _count_rules(rule_file.contains)
    _event(job_id, "progress", percent=0, message=f"Running {total} rule(s)")

    progress = (0, total)
    progress = _run_items(job_id, rule_file.contains, model_of_file, preview, progress)

    result_count = _count_results(rule_file.contains)
    _event(
        job_id,
        "run_done",
        cancelled=_CANCELLED,
        percent=int(100 * progress[0] / total) if total else 100,
        rule_count=total,
        result_count=result_count,
    )


def handle_select(request_id, payload):
    paths = payload.get("list_ifc_path", [])
    if not paths:
        _error(request_id, "select", "No IFC model in the session")
        return
    try:
        files = load_files(paths)
        select = deserialize_select(payload.get("select", {}))
        model_of_file = _model_index(files, paths)
    except Exception as exception:  # noqa: BLE001
        _error(request_id, "select", str(exception))
        return

    try:
        # The select may be a SelectRule: the walker distributes to
        # its rule too (SPEC step 5 — the former update_file_info).
        distribute_files(select, list(paths), files)
        select.run()
        select.create_list_of_element()
    except Exception as exception:  # noqa: BLE001
        _error(request_id, "select", f"Selection failed: {exception}")
        return

    elements = [element_ref(element, model_of_file) for element in select.list_of_elements]
    elements = [element for element in elements if element is not None]
    _reply(request_id, "select", elements=elements)


def handle_message(message):
    global _CANCELLED, _SHUTDOWN
    message_type = message.get("type")
    request_id = message.get("id")

    if message_type == "hello":
        _reply(
            request_id,
            "hello",
            engine=ENGINE_NAME,
            version=ENGINE_VERSION,
            versions=_versions(),
            catalogue_version=CATALOGUE_VERSION,
        )
    elif message_type == "catalogue":
        _reply(request_id, "catalogue", catalogue=catalogue())
    elif message_type == "run" or message_type == "preview":
        payload = dict(message)
        payload["mode"] = "preview" if message_type == "preview" else "run"
        handle_run(request_id, payload)
    elif message_type == "select":
        handle_select(request_id, message)
    elif message_type == "cancel":
        _CANCELLED = True
    elif message_type == "shutdown":
        _SHUTDOWN = True
        _reply(request_id, "shutdown", ok=True)
    else:
        _error(request_id, message_type or "unknown", f"Unknown request type: {message_type}")


def _on_signal(signum, frame):  # noqa: ARG001
    global _CANCELLED, _SHUTDOWN
    _CANCELLED = True
    _SHUTDOWN = True


def main():
    _load_engine_version()
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    # The engine is up: the client waits for this before its first request.
    _emit({"id": None, "type": "ready", "engine": ENGINE_NAME, "version": ENGINE_VERSION, "versions": _versions()})

    stdin_fd = sys.stdin.fileno()
    buffer = ""
    while not _SHUTDOWN:
        try:
            readable, _, _ = select.select([stdin_fd], [], [], None)
        except InterruptedError:
            continue
        if not readable:
            continue
        try:
            chunk = os.read(stdin_fd, 65536)
        except OSError:
            break
        if not chunk:
            break
        buffer += chunk.decode("utf-8", errors="replace")
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            line = line.strip()
            if not line:
                continue
            try:
                message = json.loads(line)
            except json.JSONDecodeError as exception:
                _emit({"id": None, "type": "log", "level": "error", "message": f"Malformed request: {exception}"})
                continue
            handle_message(message)


if __name__ == "__main__":
    main()
