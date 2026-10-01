"""
Test suite for Rules classes in Rules.py
"""
import unittest
import ifcopenshell
import sys
sys.path.insert(0, './ifcclash_plus')
from Rules import Volume, Area,Orientation,TopOrBottomSurface,LateralSurface,ProjectedSurface,ObbHigh
from RuleClass import SelectFacet,RuleFile,ClashResultOneObject
from ifctester import ids

import ifcopenshell.geom.main
import ifcopenshell.util.shape

class TestRules(unittest.TestCase):
    """
    Made with AI
    Test cases for Rules classes methods
    """

    def setUp(self):
        """Set up test fixtures"""
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
        self.ifc_file = ifcopenshell.open(self.ifc_path)

    def test_volume_rule(self):
        """Test Volume rule"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        wall_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        select_facet = SelectFacet()
        select_facet.applicability = [wall_facet]

        volume_rule = Volume(select_facet, 16, 17)

        OneRuleFile.contains=[volume_rule]
        OneRuleFile.run()

        self.assertEqual(len(volume_rule.result), 2) 
        for result in volume_rule.result:
            self.assertIsInstance(result, ClashResultOneObject)

    def test_area_rule(self):
        """Test area rule"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]


        area_rule = Area(first_select, 0, 1)

        OneRuleFile.contains=[area_rule]
        OneRuleFile.run()

        self.assertEqual(len(area_rule.result), 8) 
        for result in area_rule.result:
            self.assertIsInstance(result, ClashResultOneObject)

    def test_top_surface_rule(self):
        """Test TopSurface rule"""
        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        top_surface_rule = TopOrBottomSurface(first_select, 5, 10,"Top")

        OneRuleFile.contains=[top_surface_rule]
        OneRuleFile.run()

        self.assertEqual(len(top_surface_rule.result), 8)
        for result in top_surface_rule.result:
            print(result.source)
            self.assertIsInstance(result, ClashResultOneObject)

    def test_bottom_surface_rule(self):
        """Test bottom rule"""
        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        top_surface_rule = TopOrBottomSurface(first_select, 5, 10,"Bottom")

        OneRuleFile.contains=[top_surface_rule]
        OneRuleFile.run()

        self.assertEqual(len(top_surface_rule.result), 8) 
        for result in top_surface_rule.result:
            print(result.source)
            self.assertIsInstance(result, ClashResultOneObject)

    def test_lateral_rule(self):
        """Test TopSurface rule"""
        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]


        direction=(1.0,0.0,0.0)
        top_surface_rule = LateralSurface(first_select, 1, 2,direction)

        OneRuleFile.contains=[top_surface_rule]
        OneRuleFile.run()

        
        for result in top_surface_rule.result:
            print(result.source)
            self.assertIsInstance(result, ClashResultOneObject)

        self.assertEqual(len(top_surface_rule.result), 5) 

    def test_projected_rule(self):
        """Test TopSurface rule"""
        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        direction=(1.0,0.0,0.0)
        top_surface_rule = ProjectedSurface(first_select, 1, 2,direction)

        OneRuleFile.contains=[top_surface_rule]
        OneRuleFile.run()

        
        for result in top_surface_rule.result:
            print(result.source)
            self.assertIsInstance(result, ClashResultOneObject)

        self.assertEqual(len(top_surface_rule.result), 11) 

    def test_orientation_rule(self):
        """Test TopSurface rule"""
        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]


        orientation_to_check=(0.0,1.0,0.0) #We check wall that are higher than longer. 
        angular_tolerance=0.1

        rule = Orientation(first_select, orientation_to_check,"narrow",'Parrallel',angular_tolerance)

        OneRuleFile.contains=[rule]
        OneRuleFile.run()

        
        for result in rule.result:
            print(result.source)
            self.assertIsInstance(result, ClashResultOneObject)
        self.assertEqual(len(rule.result), 30) 


    def test_obb_high_rule(self):
        """Test TopSurface rule"""
        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]


        rule = ObbHigh(first_select,2,3)

        OneRuleFile.contains=[rule]
        OneRuleFile.run()

        
        for result in rule.result:
            self.assertIsInstance(result, ClashResultOneObject)
        self.assertEqual(len(rule.result), 25) 


if __name__ == '__main__':
    unittest.main()
