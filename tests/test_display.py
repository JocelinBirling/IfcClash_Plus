"""
Test suite for Rules classes in Rules.py
"""
import unittest
import ifcopenshell
import sys
sys.path.insert(0, './ifcclash_plus')
from Rules import  Intersection, Above,Below ,OBB_Above,Clearance,Collision,OBB_Below, AngleBetween,OBB_Custom,OBB_Front_And_Back,Orientation
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



        intersection_rule = Intersection(first_select, second_select, 0.01,state="Display_Input")
        OneRuleFile.contains=[intersection_rule]
        OneRuleFile.run()



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

        obb_above_rule = OBB_Custom(first_select, second_select, list_of_modifications,state="Display_Input")
        
        OneRuleFile.contains=[obb_above_rule]
        OneRuleFile.run()


    def test_orientation_rule(self):
        """Test TopSurface rule"""
        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCDOOR")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]


        orientation_to_check=(0.0,1.0,0.0) #We check wall that are higher than longer. 
        angular_tolerance=0.1

        rule = Orientation(first_select, orientation_to_check,"narrow",'Parrallel',angular_tolerance,state="Display_Input")

        OneRuleFile.contains=[rule]
        OneRuleFile.run()

    
    
    def test_front_back_obb_input(self):
        """Test custom obb check"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCSLAB")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]



        rule = OBB_Front_And_Back(first_select, second_select,1.0,"Wide",state="Display_Input")
        
        OneRuleFile.contains=[rule]
        OneRuleFile.run()


    def test_below_rule(self):
        #@todo check below rule, it copy pasted only
        """Test Above rule, it's the same test than before but the other way around."""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCSLAB")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]


        above_rule = Below(source=first_select, target=second_select, tolerance=0.81, below_type="Below_MinToMax",state="Display_Input")

        OneRuleFile.contains=[above_rule]
        OneRuleFile.run()


    def test_angle_between_rule(self):
        """Test AngleBetween rule with walls and doors"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        # Select walls as source
        first_facet = ids.Attribute(name="GlobalId",value="2O2Fr$t4X7Zf8NOew3FLQD")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        # Select doors as target
        second_facet = ids.Entity(name="IFCDOOR")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        # Create AngleBetween rule to find perpendicular relationships (walls and doors)
        # Use Wide method for direction, 90 degrees for perpendicular, 15 degrees tolerance
        angle_between_rule = AngleBetween(
            source=first_select,
            target=second_select,
            direction_method_for_source="Wide",
            direction_method_for_target="Wide",
            angle_difference=0.0,
            angle_tolerance=1.0,state="Display_Input"
        )
       
        OneRuleFile.contains = [angle_between_rule]
        OneRuleFile.run()
    


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



        intersection_rule = Intersection(first_select, second_select, 0.01,state="Display_Result")
        OneRuleFile.contains=[intersection_rule]
        OneRuleFile.run()


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

        obb_above_rule = OBB_Above(first_select, second_select, 0.81,state="Display_Result")
        
        OneRuleFile.contains=[obb_above_rule]
        OneRuleFile.run()


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



        rule = OBB_Front_And_Back(first_select, second_select,1.0,"Wide",state="Display_Result")
        
        OneRuleFile.contains=[rule]
        OneRuleFile.run()
