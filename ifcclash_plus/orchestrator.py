"""The explicit orchestrator of one rule node (SPEC Separation moteur/
gestion, step 4).

RuleFile.run() — and every other driver of a rule node: SelectRule,
the BooleanRule activations of the folders, the exception leaves, the
IPC — goes through this orchestration:

    prepare the selections -> compute -> collect the results ->
    fill the display registry -> pipeline (end_rule_action) ->
    RuleOutput

The per-rule run() adapters are cut with this step: a rule node keeps
its engine (compute), its display hook (register_display_items) and
its result collection semantics (collect_results — extend, or replace
for the rules whose former run() replaced the list). The named compute
call is driven by the catalogue (registry.engine_params) and the
signature of the compute, the in-memory counterpart of
registry.compute_from_config.
"""

import os
import warnings

from pipeline import ResultPipeline  # noqa: F401 — re-exported for convenience
from registry import implementation
from engine.backends import cpp_backend, python_backend


def run_rule(rule, state=None):
    """Run one rule node through the explicit orchestration.

    The optional state is posed on the rule before the orchestration
    (SelectRule passes "Select", the folder activations pass "Final"):
    the state stays an attribute of the rule until step 5 of the SPEC.
    Returns the RuleOutput of the pipeline (rule.output).
    """
    if state is not None:
        rule.state = state

    sources, targets, context = _prepare_selections(rule)
    results = compute_rule(rule, sources, targets, context)
    rule.collect_results(results)

    # The display is a consumer of the registry: the rule fills it
    # through its display hook, in every state (as the former run()
    # adapters did — test_structure_DisplayUpdate pins this).
    rule.register_display_items(results)

    # The management pipeline + the display state routing.
    rule.end_rule_action()
    return rule.output


def _prepare_selections(rule):
    """Run the selects of the rule and return its input lists.

    The selects are the input preparation layer of the orchestrator:
    the source (always), the target (two-objects rules) and the
    context (complex rules) — the context select needs the same files
    as the source to be able to run. Each select is then flattened
    into its element list (create_list_of_element).
    """
    rule.display_items.clear()

    rule.select_source.run()
    select_target = getattr(rule, "select_target", None)
    if select_target is not None:
        select_target.run()

    select_context = getattr(rule, "select_context", None)
    if select_context is not None:
        select_context.list_ifc_path = rule.select_source.list_ifc_path
        select_context.list_ifc_file = rule.select_source.list_ifc_file
        select_context.run()

    rule.select_source.create_list_of_element()
    if select_target is not None:
        select_target.create_list_of_element()
    if select_context is not None:
        select_context.create_list_of_element()

    sources = rule.select_source.list_of_elements
    targets = select_target.list_of_elements if select_target is not None else None
    context = (
        select_context.list_of_elements if select_context is not None else None
    )
    return sources, targets, context


def backend_of(rule_type):
    """The backend that computes a rule (SPEC_OptimisationInCPP): the
    "implementation" field of its catalogue entry, unless the
    IFCCLASH_ENGINE environment variable forces "python" or "cpp"."""
    forced = os.environ.get("IFCCLASH_ENGINE", "").strip().lower()
    if forced in ("python", "cpp"):
        return forced
    return implementation(rule_type)


def compute_rule(rule, sources, targets=None, context=None):
    """The compute of one rule, on the backend chosen by the catalogue.

    The C++ backend falls back on the Python one when it cannot take the
    call (module not built for this interpreter, rule not ported, files
    without path): the results are the same by the parity contract, only
    the time changes."""
    if backend_of(type(rule).__name__) == "cpp":
        try:
            return cpp_backend.compute(rule, sources, targets, context)
        except cpp_backend.Unsupported as reason:
            if os.environ.get("IFCCLASH_ENGINE", "").strip().lower() == "cpp":
                # Forced C++ (the tests of tests/cpp_port): no silent
                # fallback, the Python engine must not answer instead.
                raise
            _warn_fallback(type(rule).__name__, reason)
    return python_backend.compute(rule, sources, targets, context)


def close_sessions():
    """Releases the C++ engine sessions (end of a RuleFile run)."""
    cpp_backend.close_sessions()


_warned = set()


def _warn_fallback(rule_type, reason):
    if rule_type not in _warned:
        _warned.add(rule_type)
        warnings.warn(f"{rule_type}: C++ engine unavailable ({reason}), Python engine used")
