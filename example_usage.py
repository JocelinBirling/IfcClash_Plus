#!/usr/bin/env python3
"""
Example usage of IfcClash_Plus with the new import system
"""

import sys
sys.path.insert(0, './ifcclash_plus')

# Simple import of the main package

from ifcclash_plus.Rules import OBB_Above
from ifcclash_plus import RuleClass,SelectFacet
from ifctester import ids

def main():
    Chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    OneRuleFile = RuleClass.RuleFile()
    OneRuleFile.list_ifc_path= [Chemin]

    Source_Select = SelectFacet()
    Source_Facet = ids.Entity(name="IFCFURNISHINGELEMENT")
    Source_Select.applicability = [Source_Facet]


    Source_Select2 = SelectFacet()
    Source_Facet2 = ids.Entity(name="IFCSLAB")
    Source_Select2.applicability = [Source_Facet2]

    rule=OBB_Above(Source_Select,Source_Select2,0.85,state="Display_Result")


    OneRuleFile.contains=[rule]

    OneRuleFile.run()

    for result in rule.result:
        print()
        print(result.source,result.target)
if __name__ == "__main__":
    main()