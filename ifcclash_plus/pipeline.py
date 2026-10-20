# This file was written with the assistance of an AI coding tool.
"""The result management pipeline (SPEC_Separation_Moteur_Gestion).

The pipeline applies, outside of the rule computation, the management
steps configured on a rule to its raw results:

    Exception -> Criticity -> Actor -> (Grouping | Must) -> Select

Migration step 1 of the SPEC: the steps delegate to the management
methods the rules already expose (same behavior, same serialized
configuration keys). The pipeline is the seam; the steps move into it
rule by rule as they migrate on compute(). The step 5 (Select) stays
a delegation to the rule produce_select for as long as the SelectRule
consumes it.
"""


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
            output.selection = rule.produce_select()

        return output
