"""
Test suite for Rules classes in Rules.py
"""
import unittest
import ifcopenshell
import sys
sys.path.insert(0, './ifcclash_plus')
from Rules import  Intersection, Above,Below ,OBB_Above,Clearance,Collision,OBB_Below, AngleBetween,OBB_Custom,OBB_Front_And_Back
from RuleClass import SelectFacet,RuleFile,ClashResultOneObject,ClashResultTwoObjects
from ifctester import ids


class Test_Input_Display(unittest.TestCase):
    """
    Made with AI
    Test cases for Rules classes methods
    """

    def setUp(self):
        """Set up test fixtures"""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
        self.ifc_file = ifcopenshell.open(self.ifc_path)

    def test_intersection_input_display(self):
        """Test Intersection rule"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]



        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]



        intersection_rule = Intersection(first_select, second_select, 0.01)
        OneRuleFile.contains=[intersection_rule]
        OneRuleFile.run()


        intersection_rule.display_input()

    def test_custom_obb_input(self):
        """Test custom obb check"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IfcWallStandardCase")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IfcWindow")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]


        list_of_modifications=["detach_top_by_extrude:10%","NEW_OBB","detach_bottom_by_extrude:10%"]

        obb_above_rule = OBB_Custom(first_select, second_select, list_of_modifications)
        
        OneRuleFile.contains=[obb_above_rule]
        OneRuleFile.run()

        obb_above_rule.display_input()
    
    def test_front_back_obb_input(self):
        """Test custom obb check"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IfcDoor")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]



        rule = OBB_Front_And_Back(first_select, second_select,0.1,"Wide")
        
        OneRuleFile.contains=[rule]
        OneRuleFile.run()

        rule.display_input()


class Test_Result_Display(unittest.TestCase):
    """
    Made with AI
    Test cases for Rules classes methods
    """

    def setUp(self):
        """Set up test fixtures"""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
        self.ifc_file = ifcopenshell.open(self.ifc_path)

    def test_intersection_result_display(self):
        """Test Intersection rule"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]



        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]



        intersection_rule = Intersection(first_select, second_select, 0.01)
        OneRuleFile.contains=[intersection_rule]
        OneRuleFile.run()


        intersection_rule.display_result()

    def test_OBB_Above_result_display(self):
        """Test Intersection rule"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCSLAB")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        obb_above_rule = OBB_Above(first_select, second_select, 0.81)
        
        OneRuleFile.contains=[obb_above_rule]
        OneRuleFile.run()

        obb_above_rule.display_result()

    def test_front_back_obb_result(self):
        """Test custom obb check"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IfcDoor")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]



        rule = OBB_Front_And_Back(first_select, second_select,1.0,"Wide")
        
        OneRuleFile.contains=[rule]
        OneRuleFile.run()

        rule.display_result()