#!/usr/bin/env python3
"""
complex_example.py - a complete complex case with IfcClash_Plus.

Scenario: checking the clearance in front of passage doors.

1. Selection of the doors by the height of their oriented bounding box
   (OBB), with an ObbHigh rule reused as a selection thanks to a
   SelectRule (the rule cascade).
2. OBB_Front_And_Back rule: the furniture elements that penetrate the
   2 m detection zone created in front of and behind each door.
3. Exception rule: the OBB zone is intentionally generous, the pairs
   whose real distance exceeds 1 m are invalidated (status=False) by a
   Clearance rule evaluated pair by pair.

Run it from the repository root:

    python complex_example.py
"""

import sys

sys.path.insert(0, "./ifcclash_plus")

from ifctester import ids

from RuleClass import SelectFacet, SelectRule, RuleFile
from Rules import ObbHigh, OBB_Front_And_Back, Clearance
from booleanrule import BooleanLeaf

ARCH = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"

DOOR_HEIGHT_MIN = 1.9  # minimal OBB height of a passage door (m)
DOOR_HEIGHT_MAX = 2.2  # maximal OBB height (m)
OBB_ZONE = 2.0  # detection zone in front of and behind the door (m)
REAL_CLEARANCE = 1.0  # real distance beyond which a pair is excused (m)


def facet_select(*facets):
    """A SelectFacet selecting the objects that pass every facet."""
    select = SelectFacet()
    select.applicability = list(facets)
    return select


def describe(element):
    """A short human readable description of an IFC element."""
    if element is None:
        return "None"
    return f"{element.is_a()} '{element.Name}' (id {element.id()})"


def main():
    # The raw selection of all the doors and all the furniture.
    door_select = facet_select(ids.Entity(name="IFCDOOR"))
    furniture_select = facet_select(ids.Entity(name="IFCFURNISHINGELEMENT"))

    # 1. A first rule keeps the doors whose OBB height is between 1.9
    #    and 2.2 m: the passage doors, not the cabinet doors.
    door_height_rule = ObbHigh(door_select, DOOR_HEIGHT_MIN, DOOR_HEIGHT_MAX)

    # 2. The SelectRule turns the result of the rule into a selection:
    #    we keep the elements that pass the rule
    #    (element_state_to_pass=True), on the source side.
    passage_doors = SelectRule()
    passage_doors.rule = door_height_rule
    passage_doors.element_to_pass = "source"
    passage_doors.element_state_to_pass = True

    # 3. The main rule: the furniture that penetrates the 2 m detection
    #    zone created in front of and behind each passage door.
    front_back_rule = OBB_Front_And_Back(
        passage_doors, furniture_select, OBB_ZONE, "Wide",state="Display_Result"
    )

    # 4. The exception rule: it is created empty (without selection) and
    #    is evaluated pair by pair on the results of the main rule. For
    #    each pair, the Clearance rule checks whether the real distance
    #    between the door and the furniture is less than 1 m. The
    #    "have_no_result" mode invalidates the pair when the rule finds
    #    nothing: the 2 m OBB zone was only a pre-filter, only a piece of
    #    furniture really closer than 1 m to the door remains a problem.
    exception_rule = Clearance(None, None, clearance=REAL_CLEARANCE)
    front_back_rule.select_exception = BooleanLeaf(exception_rule, "have_no_result")

    # 5. The RuleFile loads the model and runs the rule.
    rule_file = RuleFile()
    rule_file.list_ifc_path = [ARCH]
    rule_file.contains = [front_back_rule]
    rule_file.run()

    # 6. Processing of the results: the valid pairs on one side, the
    #    pairs invalidated by the exception on the other side.
    kept = [r for r in front_back_rule.result if r.status]
    excused = [r for r in front_back_rule.result if not r.status]

    doors_selected = sum(len(e) for e in passage_doors.dict_elements.values())
    print(f"Passage doors (OBB height between {DOOR_HEIGHT_MIN} and "
          f"{DOOR_HEIGHT_MAX} m): {doors_selected}")
    print(f"OBB_Front_And_Back (zone of {OBB_ZONE} m): "
          f"{len(front_back_rule.result)} pair(s)")
    print()
    print(f"Kept pairs (real distance <= {REAL_CLEARANCE} m): {len(kept)}")
    for one_result in kept:
        print(f"  {describe(one_result.source)}  vs  {describe(one_result.target)}")
    print(f"Pairs invalidated by the exception rule: {len(excused)}")
    for one_result in excused:
        print(f"  {describe(one_result.source)}  vs  {describe(one_result.target)}"
              f"  [invalidated by the exception]")


if __name__ == "__main__":
    main()
