"""The Python backend: the compute() of the rules, the reference
implementation (and the oracle of the parity tests)."""

import inspect

from registry import engine_params


def compute(rule, sources, targets=None, context=None):
    """The named compute call of one rule, driven by the catalogue and
    the signature of its compute: the engine parameters are read off
    the rule instance (engine_params names == instance attributes), the
    entity lists follow the signature (a one-object rule takes no
    target list, a complex rule takes the context list of its
    contract)."""
    parameters = inspect.signature(rule.compute).parameters
    call = {
        name: getattr(rule, name)
        for name in engine_params(type(rule).__name__)
    }
    call["liste_objet_source"] = sources
    if "liste_objet_target" in parameters:
        call["liste_objet_target"] = targets
    if "liste_objet_contexte" in parameters:
        call["liste_objet_contexte"] = context
    return rule.compute(**call)
