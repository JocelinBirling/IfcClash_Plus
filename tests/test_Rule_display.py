"""
Test suite for Rules classes in Rules.py
"""
import unittest
import ifcopenshell
import sys
sys.path.insert(0, './ifcclash_plus')
from Rules import  Intersection, Above,Below ,OBB_Above,Clearance,Collision,OBB_Below, AngleBetween,OBB_Custom,OBB_Front_And_Back,Orientation,Volume,Area,TopOrBottomSurface,LateralSurface,ProjectedSurface,ObbHigh,ObbLength,Alignement,OneObjectFace,ClearanceAxisToAxis,Ray_Check,SurfaceRecover,DirectView,TwoObjectsFace,ClearanceForDoors,FreeSpace
from RuleClass import SelectFacet,RuleFile,ClashResultOneObject,ClashResultTwoObjects
from ifctester import ids


#Those test should never be launched automaticly. They all open a GUI window that need to be closed manually.
#They are here only to facilitate de result reading

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

        rule = Orientation(first_select, orientation_to_check,'Parrallel',"narrow",angular_tolerance,state="Display_Input")

        OneRuleFile.contains=[rule]
        OneRuleFile.run()

    
    
    def test_front_back_obb_input(self):
        """Test custom obb check"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path= [self.ifc_path]

        first_facet = ids.Entity(name="IFCDOOR")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]



        rule = OBB_Front_And_Back(first_select, second_select,1.0,"Wide",state="Display_Input")
        
        OneRuleFile.contains=[rule]
        OneRuleFile.run()


    def test_below_rule(self):
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

    def test_volume_input_display(self):
        """Test Volume rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = Volume(first_select, 16, 17, state="Display_Input")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_area_input_display(self):
        """Test Area rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = Area(first_select, 0, 1, state="Display_Input")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_top_or_bottom_surface_input_display(self):
        """Test TopOrBottomSurface rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCSLAB")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = TopOrBottomSurface(first_select, 5, 10, "Top", state="Display_Input")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_lateral_surface_input_display(self):
        """Test LateralSurface rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = LateralSurface(first_select, 1, 2, (1.0, 0.0, 0.0), state="Display_Input")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_projected_surface_input_display(self):
        """Test ProjectedSurface rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = ProjectedSurface(first_select, 1, 2, (1.0, 0.0, 0.0), state="Display_Input")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_obb_high_input_display(self):
        """Test ObbHigh rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = ObbHigh(first_select, 2, 3, state="Display_Input")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_obb_length_input_display(self):
        """Test ObbLength rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = ObbLength(first_select, 2, 3, "wide", state="Display_Input")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_alignement_input_display(self):
        """Test Alignement rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = Alignement(
            first_select,
            axis="Vertical",
            alignment_type="Plane",
            tolerance=0.01,
            min_group=2,
            state="Display_Input",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_one_object_face_input_display(self):
        """Test OneObjectFace rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Attribute(name="GlobalId", value="2O2Fr$t4X7Zf8NOew3FLQD")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = OneObjectFace(first_select, intersection=True, state="Display_Input")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_clearance_input_display(self):
        """Test Clearance rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = Clearance(first_select, second_select, 0.5, state="Display_Input")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_clearance_axis_to_axis_input_display(self):
        """Test ClearanceAxisToAxis rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        beam_facet = ids.Attribute(name="GlobalId", value="2OrWItJ6zAwBNp0OUxK$Dv")
        beam_select = SelectFacet()
        beam_select.applicability = [beam_facet]

        all_beams_facet = ids.Entity(name="IFCBEAM")
        all_beams_select = SelectFacet()
        all_beams_select.applicability = [all_beams_facet]

        rule = ClearanceAxisToAxis(
            beam_select,
            all_beams_select,
            mode="Perpendicular",
            min_distance=4.5,
            max_distance=5.5,
            state="Display_Input",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_collision_input_display(self):
        """Test Collision rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCDOOR")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCSLAB")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = Collision(first_select, second_select, False, state="Display_Input")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_ray_check_input_display(self):
        """Test Ray_Check rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCDOOR")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]


        context_facet = ids.Entity(
            name=ids.Restriction(
                options={"enumeration": ["IFCWALLSTANDARDCASE", "IFCSLAB"]}
            )
        )
        context_select = SelectFacet()
        context_select.applicability = [context_facet]

        rule = Ray_Check(
            first_select, second_select, context_select, 5, state="Display_Input"
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_above_input_display(self):
        """Test Above rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCSLAB")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = Above(
            source=first_select,
            target=second_select,
            tolerance=0.85,
            above_type="Above_MaxToMin",
            state="Display_Input",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_obb_above_input_display(self):
        """Test OBB_Above rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCSLAB")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = OBB_Above(first_select, second_select, 0.81, state="Display_Input")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_obb_below_input_display(self):
        """Test OBB_Below rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCSLAB")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = OBB_Below(first_select, second_select, 0.81, state="Display_Input")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_surface_recover_input_display(self):
        """Test SurfaceRecover rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCSLAB")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = SurfaceRecover(
            first_select,
            second_select,
            direction="Bottom",
            reference="Source",
            tolerance=0.05,
            min_covering="101%",
            state="Display_Input",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_direct_view_input_display(self):
        """Test DirectView rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        window_facet = ids.Entity(name="IFCWINDOW")
        window_select = SelectFacet()
        window_select.applicability = [window_facet]

        wall_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        wall_select = SelectFacet()
        wall_select.applicability = [wall_facet]

        rule = DirectView(
            window_select,
            window_select,
            wall_select,
            ray_source="Both",
            ray_count=10,
            threshold="100%",
            state="Display_Input",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_two_objects_face_input_display(self):
        """Test TwoObjectsFace rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCDOOR")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCWINDOW")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = TwoObjectsFace(
            first_select, second_select, intersection=True, state="Display_Input"
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_clearance_for_doors_input_display(self):
        """Test ClearanceForDoors rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        door_facet = ids.Entity(name="IFCDOOR")
        door_select = SelectFacet()
        door_select.applicability = [door_facet]

        furniture_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        furniture_select = SelectFacet()
        furniture_select.applicability = [furniture_facet]

        rule = ClearanceForDoors(
            door_select, furniture_select, tolerance=0.001, state="Display_Input"
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_free_space_input_display(self):
        """Test FreeSpace rule in input display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        space_facet = ids.Entity(name="IFCSPACE")
        space_select = SelectFacet()
        space_select.applicability = [space_facet]

        furniture_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        furniture_select = SelectFacet()
        furniture_select.applicability = [furniture_facet]

        rule = FreeSpace(
            space_select,
            furniture_select,
            diameter=1.5,
            height=2.0,
            state="Display_Input",
        )

        OneRuleFile.contains = [rule]
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

    def test_volume_result_display(self):
        """Test Volume rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = Volume(first_select, 16, 17, state="Display_Result")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_area_result_display(self):
        """Test Area rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = Area(first_select, 0, 1, state="Display_Result")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_top_or_bottom_surface_result_display(self):
        """Test TopOrBottomSurface rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = TopOrBottomSurface(first_select, 1, 5, "Top", state="Display_Result")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_lateral_surface_result_display(self):
        """Test LateralSurface rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = LateralSurface(first_select, 1, 2, (1.0, 0.0, 0.0), state="Display_Result")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_projected_surface_result_display(self):
        """Test ProjectedSurface rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = ProjectedSurface(first_select, 1, 2, (1.0, 0.0, 0.0), state="Display_Result")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_obb_high_result_display(self):
        """Test ObbHigh rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = ObbHigh(first_select, 2, 4, state="Display_Result")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_obb_length_result_display(self):
        """Test ObbLength rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = ObbLength(first_select, 1.5, 3, "wide", state="Display_Result")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_orientation_result_display(self):
        """Test Orientation rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCDOOR")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        orientation_to_check = (0.0, 1.0, 0.0)
        angular_tolerance = 0.1

        rule = Orientation(first_select, orientation_to_check, 'Parrallel', "narrow", angular_tolerance, state="Display_Result")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_alignement_result_display(self):
        """Test Alignement rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = Alignement(
            first_select,
            axis="Vertical",
            alignment_type="Plane",
            tolerance=0.01,
            min_group=2,
            state="Display_Result",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_one_object_face_result_display(self):
        """Test OneObjectFace rule in result display.

        Business rule: two faces of the object oriented the same way
        (parallel normals, same sense) must not exceed 0.1 m2 each. The
        face selections keep only the faces bigger than 0.1 m2, the
        orientation check flags the same-oriented pairs.

        The orientation check flags the pairs DEVIATING from the target
        angle: flagging the same-oriented pairs (measured angle close
        to 0 deg) is expressed as a deviation of more than 179 deg
        from the 180 deg target.
        """

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Attribute(name="GlobalId", value="2O2Fr$t4X7Zf8NOew3FLQD")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        rule = OneObjectFace(
            first_select,
            face_a_selection={"min_surface": 0.1,"orientation":"Top"},
            face_b_selection={"min_surface": 0.1,"orientation":"Bottom"},
            #orientation=True,angle=180.0,angle_tolerance=10,
            distance=True,min_distance=0.2,max_distance=2.0,
            state="Display_Result",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_above_result_display(self):
        """Test Above rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCSLAB")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = Above(
            source=first_select,
            target=second_select,
            tolerance=0.85,
            above_type="Above_MaxToMin",
            state="Display_Result",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_below_result_display(self):
        """Test Below rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCSLAB")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = Below(
            source=first_select,
            target=second_select,
            tolerance=0.81,
            below_type="Below_MinToMax",
            state="Display_Result",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_angle_between_result_display(self):
        """Test AngleBetween rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Attribute(name="GlobalId", value="2O2Fr$t4X7Zf8NOew3FLQD")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCDOOR")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = AngleBetween(
            source=first_select,
            target=second_select,
            direction_method_for_source="Wide",
            direction_method_for_target="Wide",
            angle_difference=0.0,
            angle_tolerance=1.0,
            state="Display_Result",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_clearance_result_display(self):
        """Test Clearance rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCSTAIRFLIGHT")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = Clearance(first_select, second_select, 2.0, state="Display_Result")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_clearance_axis_to_axis_result_display(self):
        """Test ClearanceAxisToAxis rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        beam_facet = ids.Attribute(name="GlobalId", value="2OrWItJ6zAwBNp0OUxK$Dv")
        beam_select = SelectFacet()
        beam_select.applicability = [beam_facet]

        all_beams_facet = ids.Entity(name="IFCBEAM")
        all_beams_select = SelectFacet()
        all_beams_select.applicability = [all_beams_facet]

        rule = ClearanceAxisToAxis(
            beam_select,
            all_beams_select,
            mode="Perpendicular",
            min_distance=4.5,
            max_distance=5.5,
            state="Display_Result",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_collision_result_display(self):
        """Test Collision rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCDOOR")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCSLAB")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = Collision(first_select, second_select, False, state="Display_Result")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_ray_check_result_display(self):
        """Test Ray_Check rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCDOOR")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        context_facet = ids.Entity(
            name=ids.Restriction(
                options={"enumeration": ["IFCWALLSTANDARDCASE", "IFCSLAB"]}
            )
        )
        context_select = SelectFacet()
        context_select.applicability = [context_facet]

        rule = Ray_Check(
            first_select, second_select, context_select, 5, state="Display_Result"
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_obb_below_result_display(self):
        """Test OBB_Below rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCSLAB")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = OBB_Below(first_select, second_select, 0.81, state="Display_Result")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_custom_obb_result_display(self):
        """Test custom obb check in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCDOOR")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IfcWindow")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        list_of_modifications = ["detach_top_by_extrude:20%","NEW_OBB", "detach_bottom_by_extrude:50%"]

        rule = OBB_Custom(first_select, second_select, list_of_modifications, state="Display_Result")

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_surface_recover_result_display(self):
        """Test SurfaceRecover rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        first_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        first_select = SelectFacet()
        first_select.applicability = [first_facet]

        second_facet = ids.Entity(name="IFCSLAB")
        second_select = SelectFacet()
        second_select.applicability = [second_facet]

        rule = SurfaceRecover(
            first_select,
            second_select,
            direction="Bottom",
            reference="Source",
            tolerance=0.05,
            min_covering="101%",
            state="Display_Result",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_direct_view_result_display(self):
        """Test DirectView rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        window_facet = ids.Entity(name="IFCWINDOW")
        window_select = SelectFacet()
        window_select.applicability = [window_facet]

        wall_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
        wall_select = SelectFacet()
        wall_select.applicability = [wall_facet]

        rule = DirectView(
            window_select,
            window_select,
            wall_select,
            ray_source="Both",
            ray_count=10,
            threshold="100%",
            state="Display_Result",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_two_objects_face_result_display(self):
        """Test TwoObjectsFace rule in result display: the extreme top
        faces of the tall cabinets must stand at least 0.9 m below the
        slabs over them (the scenario of the unit test, documented in
        doc/2ObjectsRules/TwoObjectsFace.md)."""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        cabinet_facet = ids.Attribute(
            name="Name",
            value=ids.Restriction(options={"pattern": ["M_Tall Cabinet-Single Door.*"]}),
        )
        cabinet_select = SelectFacet()
        cabinet_select.applicability = [cabinet_facet]

        slab_facet = ids.Entity(name="IFCSLAB")
        slab_select = SelectFacet()
        slab_select.applicability = [slab_facet]

        rule = TwoObjectsFace(
            cabinet_select, slab_select,
            source_face_selection={"orientation": "Top", "extreme_faces": True},
            target_face_selection={"orientation": "Bottom"},
            distance=True, min_distance=0.9,
            state="Display_Result",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_clearance_for_doors_result_display(self):
        """Test ClearanceForDoors rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        door_facet = ids.Entity(name="IFCDOOR")
        door_select = SelectFacet()
        door_select.applicability = [door_facet]

        furniture_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        furniture_select = SelectFacet()
        furniture_select.applicability = [furniture_facet]

        rule = ClearanceForDoors(
            door_select, furniture_select, tolerance=0.001, state="Display_Result"
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

    def test_free_space_result_display(self):
        """Test FreeSpace rule in result display"""

        OneRuleFile = RuleFile()
        OneRuleFile.list_ifc_path = [self.ifc_path]

        space_facet = ids.Entity(name="IFCSPACE")
        space_select = SelectFacet()
        space_select.applicability = [space_facet]

        furniture_facet = ids.Entity(name="IFCFURNISHINGELEMENT")
        furniture_select = SelectFacet()
        furniture_select.applicability = [furniture_facet]

        rule = FreeSpace(
            space_select,
            furniture_select,
            diameter=1.5,
            height=2.0,
            state="Display_Result",
        )

        OneRuleFile.contains = [rule]
        OneRuleFile.run()

