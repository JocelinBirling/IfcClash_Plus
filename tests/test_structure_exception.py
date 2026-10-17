"""
Test suite for exception rule
"""
import unittest
import sys
sys.path.insert(0, './ifcclash_plus')
from OCC.Core.gp import gp_Pnt, gp_Dir, gp_Vec
from CustomOBB import Custom_OBB


class test_exception_relation(unittest.TestCase):
    """

    Test cases for Custom_OBB class methods"""
    
    def setUp(self):
        """Set up test fixtures
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

                              """

    def test_same_building_storey(self):
        ...

    def test_same_system(self):
        ...
    
    def test_min_distance_to_obb(self):
        """Test minimal distance calculation between two OBBs
        distance = self.obb.min_distance_to_obb(self.obb2)
        self.assertIsInstance(distance, float)
        self.assertGreaterEqual(distance, 0)
        """

class test_exception_rule(unittest.TestCase):
    """

    Test cases for Custom_OBB class methods"""
    



if __name__ == '__main__':
    unittest.main()
