"""
Test suite for Rules classes in Rules.py
"""
import unittest
import ifcopenshell
import sys
sys.path.insert(0, './ifcclash_plus')
from Rules import  Intersection, Above,Below ,OBB_Above,Clearance,Collision,OBB_Below, AngleBetween,OBB_Custom
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

    def test_intersection_rule(self):
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

 
        self.assertEqual(len(intersection_rule.result), 1)
        for result in intersection_rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)

    def test_collision_rule(self):
        """Test collision rule"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]
        first_facet = ids.Entity(name="IFCDOOR")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]


        second_facet = ids.Entity(name="IFCSLAB")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]


        rule = Collision(first_select, second_select, False) 

        OneRuleFile.contains=[rule]
        OneRuleFile.run()

        self.assertEqual(len(rule.result), 24)
        for result in rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)

    def test_clearance_rule(self):
        """Test Intersection rule"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]
        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]


        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        intersection_rule = Clearance(first_select, second_select, 0.5) 

        OneRuleFile.contains=[intersection_rule]
        OneRuleFile.run()

        for result in intersection_rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)

        self.assertEqual(len(intersection_rule.result), 152)

    def test_above_rule_Max_To_Min(self):
        """Test Above rule"""

        #The high cabinet are 0.8m below the slab. We should find 8 of them.

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCSLAB")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]


        above_rule = Above(source=first_select, target=second_select, tolerance=0.85, above_type="Above_MaxToMin") #0.81 should work.
        above_rule.run()

        OneRuleFile.contains=[above_rule]
        OneRuleFile.run()

        self.assertEqual(len(above_rule.result), 8)
        for result in above_rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)


    def test_above_rule_MaxToMax(self):
        """Test Above rule"""

        #The high cabinet are 0.8m below the slab. We should find 8 of them.

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCWINDOW")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]


        above_rule = Above(source=first_select, target=second_select, tolerance=1.0, above_type="Above_MaxToMax")
        above_rule.run()

        OneRuleFile.contains=[above_rule]
        OneRuleFile.run()


        for result in above_rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertEqual(len(above_rule.result), 13) #It's 13 because one windows is badly modelized.




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
            angle_tolerance=1.0
        )
       
        OneRuleFile.contains = [angle_between_rule]
        OneRuleFile.run()

        # Verify results
        for result in angle_between_rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)

        # Should find some walls and doors that are parrallels to that one walls.
        self.assertEqual(len(angle_between_rule.result), 4)
        

    def test_angle_between_rule2(self):
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
            angle_difference=90.0,
            angle_tolerance=1.0
        )
       
        OneRuleFile.contains = [angle_between_rule]
        OneRuleFile.run()


        # Verify results
        for result in angle_between_rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)

        # Should find some walls and doors that are parrallels to that one walls.
        self.assertEqual(len(angle_between_rule.result), 6)
        
class TestRulesOBB(unittest.TestCase):
    """
    Made with AI
    Test cases for Rules classes methods
    """

    def setUp(self):
        """Set up test fixtures"""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
        self.ifc_file = ifcopenshell.open(self.ifc_path)


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


        above_rule = Below(source=first_select, target=second_select, tolerance=0.81, below_type="Below_MinToMax")
        above_rule.run()

        OneRuleFile.contains=[above_rule]
        OneRuleFile.run()

        
        for result in above_rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)
        self.assertEqual(len(above_rule.result), 8)

    def test_obb_above_rule(self):
        """Test OBB_Above rule"""

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

        self.assertEqual(len(obb_above_rule.result), 8)
        for result in obb_above_rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)


    def test_obb_below_rule(self):
        """Test OBB_Below rule"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IfcWindow")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IfcSLab")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        obb_above_rule = OBB_Below(first_select, second_select, 0.1)

        
        OneRuleFile.contains=[obb_above_rule]
        OneRuleFile.run()

        self.assertEqual(len(obb_above_rule.result), 34)
        #There is a lot of layer of slab in the house
        for result in obb_above_rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)

    def test_obb_below_rule_2(self):
        """Test OBB_Below rule. It's the inverse of OBB Above, to cross check"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IfcSlab")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        obb_above_rule = OBB_Below(first_select, second_select, 0.81) #0.81 should work
        
        
        OneRuleFile.contains=[obb_above_rule]
        OneRuleFile.run()

    
        for result in obb_above_rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)

        self.assertEqual(len(obb_above_rule.result), 14)
        #We should have get the same amount of result as OBB_Above(FurnishingElement,Slab), but the 3 tables are going threw the 2 finish layer.

    def test_obb_above_rule_2(self):
        """Test OBB_above rule, it's the inverse of OBB_Below, to cross check"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IfcSlab")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IfcWindow")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        obb_above_rule = OBB_Above(first_select, second_select, 0.1)
        obb_above_rule._display_specific()
        
        OneRuleFile.contains=[obb_above_rule]
        OneRuleFile.run()

        self.assertEqual(len(obb_above_rule.result), 34)
        #We should find the same number as the above test rule. 
        for result in obb_above_rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)



    def test_display_custom_obb(self):
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

        obb_custom = OBB_Custom(first_select, second_select, list_of_modifications)

        obb_custom._display_input()


        


    def test_custom_obb(self):
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

        obb_above_rule.display_result()

        self.assertEqual(len(obb_above_rule.result), 34)
        #We should find the same number as the above test rule. 
        for result in obb_above_rule.result:
            self.assertIsInstance(result, ClashResultTwoObjects)

        


if __name__ == '__main__':
    unittest.main()
