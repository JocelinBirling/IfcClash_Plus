"""
Test suite for Custom_OBB class in fixed_OBB.py
"""
import unittest
import sys
sys.path.insert(0, './ifcclash_plus')
from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec
from CustomOBB import Custom_OBB


class TestCustomOBB(unittest.TestCase):
    """
    Made with IA
    Test cases for Custom_OBB class methods"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a default OBB for testing
        self.center = gp_Pnt(0, 0, 0)
        self.x_dir = gp_Dir(1, 0, 0)
        self.y_dir = gp_Dir(0, 1, 0)
        self.z_dir = gp_Dir(0, 0, 1)
        self.x_h = 5
        self.y_h = 5
        self.z_h = 5
        self.obb = Custom_OBB(self.center, self.x_dir, self.y_dir, self.z_dir, 
                             self.x_h, self.y_h, self.z_h)
        
        # Create a second OBB for distance testing
        self.center2 = gp_Pnt(13, 0, 0)
        from OCC.Core.gp import gp_Vec
        self.x_dir2 = gp_Dir(gp_Vec(1, 1, 0))
        self.y_dir2 = gp_Dir(gp_Vec(1, -1, 0))
        self.z_dir2 = gp_Dir(0, 0, 1)
        self.obb2 = Custom_OBB(self.center2, self.x_dir2, self.y_dir2, self.z_dir2, 
                              self.x_h, self.y_h, self.z_h)
    
    def test_min_distance_to_obb(self):
        """Test minimal distance calculation between two OBBs"""
        distance = self.obb.min_distance_to_obb(self.obb2)
        self.assertIsInstance(distance, float)
        self.assertGreaterEqual(distance, 0)
        
        # Test with overlapping OBBs
        overlapping_obb = Custom_OBB(self.center, self.x_dir, self.y_dir, self.z_dir,
                                    self.x_h, self.y_h, self.z_h)
        distance = self.obb.min_distance_to_obb(overlapping_obb)
        self.assertEqual(distance, 0.0)
    
    def test_get_min_corner(self):
        """Test getting minimum corner of OBB"""
        min_corner = self.obb.get_min_corner()
        # Expected min corner should be (-5, -5, -5)
        self.assertAlmostEqual(min_corner.X(), -5, places=4)
        self.assertAlmostEqual(min_corner.Y(), -5, places=4)
        self.assertAlmostEqual(min_corner.Z(), -5, places=4)
    
    def test_get_max_corner(self):
        """Test getting maximum corner of OBB"""
        max_corner = self.obb.get_max_corner()
        # Expected max corner should be (5, 5, 5)
        self.assertAlmostEqual(max_corner.X(), 5, places=4)
        self.assertAlmostEqual(max_corner.Y(), 5, places=4)
        self.assertAlmostEqual(max_corner.Z(), 5, places=4)
    
    def test_extend_up(self):
        """Test extruding top of OBB"""
        original_z = self.obb.ZHSize()
        original_center_z = self.obb.Center().Z()
        
        # Test with percentage
        new_obb = self.obb.extend_up("10%")
        self.assertGreaterEqual(new_obb.ZHSize(), original_z)
        self.assertGreaterEqual(new_obb.Center().Z(), original_center_z)
        
        # Verify the height increase
        world_up = gp_Dir(0, 0, 1)
        x_dir = gp_Dir(self.obb.XDirection())
        y_dir = gp_Dir(self.obb.YDirection())
        z_dir = gp_Dir(self.obb.ZDirection())
        
        x_proj = abs(world_up.Dot(x_dir))
        y_proj = abs(world_up.Dot(y_dir))
        z_proj = abs(world_up.Dot(z_dir))
        hauteur = x_proj * self.obb.XHSize() * 2 + y_proj * self.obb.YHSize() * 2 + z_proj * self.obb.ZHSize() * 2
        expected_increase = hauteur * 0.10
        
        # Check if the new OBB's height matches the expected increase
        new_hauteur = x_proj * new_obb.XHSize() * 2 + y_proj * new_obb.YHSize() * 2 + z_proj * new_obb.ZHSize() * 2
        self.assertAlmostEqual(new_hauteur, hauteur + expected_increase, places=4)
        
    
    def test_extend_down(self):
        """Test extruding bottom of OBB"""
        original_z = self.obb.ZHSize()
        original_center_z = self.obb.Center().Z()
        
        # Test with percentage
        new_obb = self.obb.extend_down("10%")
        self.assertGreaterEqual(new_obb.ZHSize(), original_z)
        self.assertLessEqual(new_obb.Center().Z(), original_center_z)
        
        # Verify the height increase
        world_up = gp_Dir(0, 0, 1)
        x_dir = gp_Dir(self.obb.XDirection())
        y_dir = gp_Dir(self.obb.YDirection())
        z_dir = gp_Dir(self.obb.ZDirection())
        
        x_proj = abs(world_up.Dot(x_dir))
        y_proj = abs(world_up.Dot(y_dir))
        z_proj = abs(world_up.Dot(z_dir))
        hauteur = x_proj * self.obb.XHSize() * 2 + y_proj * self.obb.YHSize() * 2 + z_proj * self.obb.ZHSize() * 2
        expected_increase = hauteur * 0.10
        
        # Check if the new OBB's height matches the expected increase
        new_hauteur = x_proj * new_obb.XHSize() * 2 + y_proj * new_obb.YHSize() * 2 + z_proj * new_obb.ZHSize() * 2
        self.assertAlmostEqual(new_hauteur, hauteur + expected_increase, places=4)
        

    
    def test_detach_top_by_extrude(self):
        """Test detaching top part of OBB"""
        original_z = self.obb.ZHSize()
        original_center_z = self.obb.Center().Z()
        
        # Test with percentage
        top_obb = self.obb.detach_top_by_extrude("10%")
        self.assertEqual(top_obb.ZHSize(), 0.5)  # 10% of 10 / 2
        expected_center_z = original_center_z + original_z + 0.5 # 10% of 10 / 2
        self.assertAlmostEqual(top_obb.Center().Z(), expected_center_z, places=4)
        
        # Test with absolute value
        top_obb = self.obb.detach_top_by_extrude(2.0)
        self.assertEqual(top_obb.ZHSize(), 1.0)  # 2.0 / 2
        expected_center_z = original_center_z + original_z + 1.0
        self.assertAlmostEqual(top_obb.Center().Z(), expected_center_z, places=4)
    
    def test_detach_bottom_by_extrude(self):
        """Test detaching bottom part of OBB"""
        original_z = self.obb.ZHSize()
        original_center_z = self.obb.Center().Z()
        
        # Test with percentage
        bottom_obb = self.obb.detach_bottom_by_extrude("10%")
        self.assertEqual(bottom_obb.ZHSize(), 0.5)  # 10% of 10 / 2
        expected_center_z = original_center_z - original_z - 0.5  # 10% of 10 / 2
        self.assertAlmostEqual(bottom_obb.Center().Z(), expected_center_z, places=4)
        
        # Test with absolute value
        bottom_obb = self.obb.detach_bottom_by_extrude(2.0)
        self.assertEqual(bottom_obb.ZHSize(), 1.0)  # 2.0 / 2
        expected_center_z = original_center_z - original_z - 1.0
        self.assertAlmostEqual(bottom_obb.Center().Z(), expected_center_z, places=4)
    
    def test_project_onto_axis(self):
        """Test projection of OBB onto an axis"""
        from OCC.Core.gp import gp_Vec
        
        axis = gp_Vec(1, 0, 0)  # X axis
        min_proj, max_proj = self.obb._project_onto_axis(axis)
        
        # For a cube aligned with axes, projection on X should be [-5, 5]
        self.assertAlmostEqual(min_proj, -5, places=4)
        self.assertAlmostEqual(max_proj, 5, places=4)
        
        # Test with diagonal axis
        axis = gp_Vec(1, 1, 0).Normalized()
        min_proj, max_proj = self.obb._project_onto_axis(axis)
        # The projection should be larger than the simple axis projection
        self.assertGreater(max_proj - min_proj, 5)
    
    def test_test_separating_axis(self):
        """Test separating axis detection"""
        from OCC.Core.gp import gp_Vec
        
        axis = gp_Vec(1, 0, 0)  # X axis
        center_vector = gp_Vec(13, 0, 0)  # Vector between centers
        
        # Test with non-overlapping OBBs
        distance = self.obb._test_separating_axis(axis, self.obb2, center_vector)
        self.assertGreater(distance, 0)  # Should be a separating axis
        
        # Test with overlapping OBBs (same OBB)
        distance = self.obb._test_separating_axis(axis, self.obb, gp_Vec(0, 0, 0))
        self.assertLess(distance, 0)  # Should indicate overlap

    def test_get_two_main_direction_OBB_shape(self):
        """Check if the dectection"""
        
        from OCC.Core.gp import gp_Vec

        #@todo get a test for get_two_main_direction
        #We should check that Z is not taken in account if the object if big.
        
        self.assertLess(0, 0)  # Should indicate overlap


if __name__ == '__main__':
    unittest.main()
