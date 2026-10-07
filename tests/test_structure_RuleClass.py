"""
Test suite for Rules classes in Rules.py
"""
import unittest
import ifcopenshell
import sys
sys.path.insert(0, './ifcclash_plus')
from Rules import  Intersection, Above,Below ,OBB_Above,Clearance,Collision,OBB_Below, AngleBetween
from RuleClass import SelectFacet,RuleFile,ClashResultOneObject,ClashResultTwoObjects
from ifctester import ids


class TestRules(unittest.TestCase):
    """
    Made with AI
    Test cases for Rules classes methods
    """

    def setUp(self):
        """Set up test fixtures"""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
        self.ifc_file = ifcopenshell.open(self.ifc_path)


    def test_grouping_by_source(self):
        """Test Intersection rule"""


        #@todo Finish the test result

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]



        first_facet = ids.Entity(name="IFCDOOR")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]



        intersection_rule = Intersection(first_select, second_select, 0.1)
        intersection_rule.select_grouping = "TARGET"

        OneRuleFile.contains=[intersection_rule]
        OneRuleFile.run()



        set_of_source=set()
        set_of_target=set()
        

        for result in intersection_rule.result:
            set_of_source.add(result.source)
            set_of_target.add(result.target)

        number_of_source_result=len(set_of_source)
        number_of_target_result=len(set_of_target)

        print(number_of_source_result)
        print(number_of_target_result)


        for result in intersection_rule.grouped_result:
            print(result.source_set)
            print("---",result.target_set)

        print("TO FINISH")




if __name__ == '__main__':
    unittest.main()
