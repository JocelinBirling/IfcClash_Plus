# This file was written with the assistance of an AI coding tool.
"""The result management pipeline (SPEC_Separation_Moteur_Gestion).

The pipeline applies, outside of the rule computation, the management
steps configured on a rule to its raw results:

    Exception -> Criticity -> Actor -> (Grouping | Must) -> Select

Migration step 1 of the SPEC: the steps delegate to the management
methods the rules already expose (same behavior, same serialized
configuration keys). The pipeline is the seam; the steps move into it
rule by rule as they migrate on compute(). The step 5 (Select) moved
here entirely with step 5 of the SPEC: the chaining selection is
computed by selection_of below (the former produce_select of the
rules).
"""


def selection_of(rule):
    """The chaining selection (the Select step of the pipeline, SPEC
    step 5 — the former produce_select of the rules).

    Configuration (posed on the rule by the downstream SelectRule
    before the orchestration): element_state_to_pass True picks the
    elements of the results with status True, False picks the elements
    of the input selection that went through the rule but produced no
    result (an element invalidated by an exception still excludes its
    source from the complement). A two-objects rule reads
    element_to_pass ("source" or "target"); a one-object rule only
    has sources, the configuration is ignored.

    Returns a dict {ifc_file: [elements]}, an element appearing in
    several results is returned only once.
    """
    # A one-object rule has no target: it passes sources only, the
    # element_to_pass configuration is ignored (the former
    # one-object produce_select read .source directly).
    if getattr(rule, "select_target", None) is None:
        element_to_pass = "source"
    else:
        element_to_pass = rule.element_to_pass
        if element_to_pass not in ("source", "target"):
            raise ValueError(
                "element_to_pass must be 'source' or 'target', "
                f"got '{element_to_pass}'"
            )

    dict_return = {}

    if rule.element_state_to_pass:
        elements_already_added = set()
        for oneresult in rule.result:
            if oneresult.status:
                the_element = getattr(oneresult, element_to_pass)
                if the_element is None:
                    continue
                if the_element in elements_already_added:
                    continue
                elements_already_added.add(the_element)
                if the_element.file in dict_return:
                    dict_return[the_element.file].append(the_element)
                else:
                    dict_return[the_element.file] = [the_element]

        return dict_return

    # Elements of the input selection absent from the results.
    # The entity_instance equality is value based, so a set of elements
    # works even if the file wrappers of the results are different
    # from the ones of the selection.
    selection = (
        rule.select_source
        if element_to_pass == "source"
        else rule.select_target
    )
    elements_in_results = set()
    for oneresult in rule.result:
        the_element = getattr(oneresult, element_to_pass)
        if the_element is not None:
            elements_in_results.add(the_element)

    for ifc_file, elements in selection.dict_elements.items():
        if not elements:
            continue
        absent = [
            one_element
            for one_element in elements
            if one_element not in elements_in_results
        ]
        if absent:
            dict_return[ifc_file] = absent

    return dict_return


class RuleOutput:
    """The output of one rule node (SPEC): the results after the
    pipeline, plus the products of the Grouping/Must and Select steps.

    The export JSON (save_results_to_json) and the IPC consume this
    output without any format adaptation: results is the rule result
    list, groups the grouped_result of the Grouping/Must step.
    """

    def __init__(self):
        # After the pipeline.
        self.results: list = []
        # The chaining product (Select step), consumed by the
        # SelectRule of the downstream rules. None when the Select
        # step did not run.
        self.selection: object = None
        # The groups of the Grouping/Must step, None without grouping.
        self.groups: list = None


class ResultPipeline:
    """The management steps applied to the raw results of a rule."""

    def __init__(self, rule):
        # The rule carries the configuration of every step (same
        # attributes as before the extraction) and the state routing.
        self.rule = rule

    def apply(self) -> RuleOutput:
        """Exception -> Criticity -> Actor -> (Grouping | Must) -> Select.

        The exception step invalidates in place (status = False), it
        never removes a result. The Criticity, Actor and Grouping/Must
        steps run on the "Final" path only, the Select step on the
        "Select" path, exactly as the former end_rule_action did.
        """
        rule = self.rule
        output = RuleOutput()

        # 1. Exception: invalidates the matching results in place.
        rule.run_exception()

        # 2, 3, 4. Criticity, Actor, then Grouping or Must (exclusive).
        if rule.state == "Final":
            rule.manage_result()

        output.results = rule.result
        output.groups = rule.grouped_result or None

        # 5. Select: the chaining product for the downstream rules.
        if rule.state == "Select":
            output.selection = selection_of(rule)

        return output
