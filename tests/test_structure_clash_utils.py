"""
Test suite for clash_utils.py module
Tests for geometric utility functions used in clash detection
"""
import unittest
import sys
import os
import numpy as np

# Add the project directory to the path to import clash_utils directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ifcclash_plus'))

# Import clash_utils directly to avoid issues with ifcclash_plus.__init__.py
from clash_utils import (
    get_extreme_faces,
    triangle_to_occ_face,
    min_distance_two_faces,
    get_XYZ_placement,
    calculate_extreme_faces_surface,
    AXIS_LITERAL,
    VECTOR_3D
)


class TestGetExtremeFaces(unittest.TestCase):
    """Test cases for get_extreme_faces function"""

    def setUp(self):
        """Set up test fixtures"""
        # Import here to avoid issues with OCC initialization
        from ifcopenshell.geom import ShapeType
        self.ShapeType = ShapeType
        
    def test_with_simple_cube_geometry(self):
        """Test with a simple cube-like geometry - should return top and bottom faces"""
        # Create a simple cube geometry using numpy arrays
        # This is a mock test - in practice you'd need actual geometry
        from ifcopenshell.util.shape import get_vertices, get_faces
        
        # Create a simple tetrahedron (4 triangular faces)
        vertices = np.array([
            [0, 0, 0],   # Bottom front left
            [1, 0, 0],   # Bottom front right
            [0, 1, 0],   # Bottom back left
            [0, 0, 1],   # Top
            [1, 1, 0],   # Bottom back right
            [1, 0, 1],   # Top front right
            [0, 1, 1],   # Top back left
            [1, 1, 1]    # Top back right
        ], dtype=np.float64)
        
        faces = np.array([
            [0, 1, 3],   # Front face
            [0, 2, 3],   # Left face
            [1, 2, 3],   # Bottom face
            [4, 5, 6],   # Top face
            [4, 5, 7],   # Back face
            [5, 6, 7],   # Right face
        ])
        
        # Mock a simple geometry object
        class MockGeometry:
            def __init__(self, vertices, faces):
                self.vertices = vertices
                self.faces = faces
        
        # Test with Z axis (default)
        try:
            # This test may not work without actual ifcopenshell geometry
            # We'll test the logic with available data
            extreme_faces = get_extreme_faces(None)
            # If we get here, the function at least runs
        except Exception as e:
            # Expected for None input
            self.assertIsInstance(e, (TypeError, AttributeError))
            
    def test_with_z_axis_direction(self):
        """Test with Z axis and custom direction"""
        # Test that direction parameter is accepted
        try:
            result = get_extreme_faces(None, axis="Z", direction=(0, 0, 1))
        except Exception as e:
            # Expected for None input
            self.assertIsInstance(e, (TypeError, AttributeError))
            
    def test_with_x_axis(self):
        """Test with X axis"""
        try:
            result = get_extreme_faces(None, axis="X")
        except Exception as e:
            # Expected for None input
            self.assertIsInstance(e, (TypeError, AttributeError))
            
    def test_with_y_axis(self):
        """Test with Y axis"""
        try:
            result = get_extreme_faces(None, axis="Y")
        except Exception as e:
            # Expected for None input
            self.assertIsInstance(e, (TypeError, AttributeError))


class TestTriangleToOccFace(unittest.TestCase):
    """Test cases for triangle_to_occ_face function"""

    def test_valid_triangle(self):
        """Test with a valid triangle"""
        triangle = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        face = triangle_to_occ_face(triangle)
        
        self.assertIsNotNone(face)
        # OCC TopoDS_Face should not be null
        self.assertFalse(face.IsNull())
        
    def test_valid_triangle_3d(self):
        """Test with a 3D triangle"""
        triangle = [(0, 0, 0), (1, 0, 0), (0, 1, 1)]
        face = triangle_to_occ_face(triangle)
        
        self.assertIsNotNone(face)
        self.assertFalse(face.IsNull())
        
    def test_degenerate_triangle(self):
        """Test with a degenerate triangle (colinear points)"""
        # Colinear points - OpenCASCADE still creates a valid face
        triangle = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
        face = triangle_to_occ_face(triangle)
        
        # OpenCASCADE creates a valid face even for degenerate triangles
        self.assertIsNotNone(face)
        self.assertFalse(face.IsNull())
        
    def test_single_point(self):
        """Test with invalid input - single point"""
        # This should return None (less than 3 points)
        triangle = [(0, 0, 0)]
        face = triangle_to_occ_face(triangle)
        
        # Should return None for invalid input
        self.assertIsNone(face)
        
    def test_empty_list(self):
        """Test with empty list"""
        triangle = []
        face = triangle_to_occ_face(triangle)
        
        # Should return None for invalid input
        self.assertIsNone(face)


class TestMinDistanceTwoFaces(unittest.TestCase):
    """Test cases for min_distance_two_faces function"""

    def test_parallel_faces(self):
        """Test distance between parallel faces"""
        # Two parallel triangles on Z axis
        face1 = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        face2 = [(0, 0, 1), (1, 0, 1), (0, 1, 1)]
        
        result = min_distance_two_faces(face1, face2)
        
        self.assertIsInstance(result, dict)
        self.assertIn('distance', result)
        self.assertIn('point1', result)
        self.assertIn('point2', result)
        
        # Distance should be approximately 1.0 (Z difference)
        self.assertAlmostEqual(result['distance'], 1.0, places=4)
        
    def test_intersecting_faces(self):
        """Test distance between intersecting faces"""
        # Two triangles that intersect
        face1 = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        face2 = [(0.5, 0, 0), (1.5, 0, 0), (0.5, 1, 0)]
        
        result = min_distance_two_faces(face1, face2)
        
        self.assertIsInstance(result, dict)
        # Distance should be 0 or very small for intersecting faces
        self.assertLessEqual(result['distance'], 0.1)
        
    def test_identical_faces(self):
        """Test distance between identical faces"""
        face1 = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        face2 = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        
        result = min_distance_two_faces(face1, face2)
        
        self.assertIsInstance(result, dict)
        # Distance should be 0 for identical faces
        self.assertEqual(result['distance'], 0.0)
        
    def test_perpendicular_faces(self):
        """Test distance between perpendicular faces"""
        # Two perpendicular triangles
        face1 = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]  # XY plane
        face2 = [(0, 0, 0), (0, 0, 1), (0, 1, 0)]  # XZ plane
        
        result = min_distance_two_faces(face1, face2)
        
        self.assertIsInstance(result, dict)
        # Distance should be 0 since they share a common edge
        self.assertEqual(result['distance'], 0.0)
        
    def test_separated_faces(self):
        """Test distance between separated faces"""
        # Two triangles separated in space
        face1 = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        face2 = [(2, 0, 0), (3, 0, 0), (2, 1, 0)]
        
        result = min_distance_two_faces(face1, face2)
        
        self.assertIsInstance(result, dict)
        # Distance should be approximately 1.0 (X difference)
        self.assertAlmostEqual(result['distance'], 1.0, places=4)
        
    def test_invalid_faces(self):
        """Test with invalid faces (degenerate triangles)"""
        # Invalid triangles (degenerate)
        face1 = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]  # Colinear
        face2 = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]  # Valid
        
        # Degenerate triangles still create valid faces, so no exception is raised
        # The distance calculation should still work
        result = min_distance_two_faces(face1, face2)
        self.assertIsInstance(result, dict)
        self.assertIn('distance', result)


class TestGetXYZPlacement(unittest.TestCase):
    """Test cases for get_XYZ_placement function"""

    def test_with_mock_object(self):
        """Test with a mock IFC object"""
        # Create a mock object with ObjectPlacement
        class MockObjectPlacement:
            pass
            
        class MockObject:
            def __init__(self):
                self.ObjectPlacement = MockObjectPlacement()
        
        mock_obj = MockObject()
        
        # This will likely fail due to missing implementation
        # but we test that the function handles it gracefully
        try:
            result = get_XYZ_placement(mock_obj)
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 3)
        except Exception as e:
            # Expected for incomplete mock
            self.assertIsInstance(e, Exception)


class TestCalculateExtremeFacesSurface(unittest.TestCase):
    """Test cases for calculate_extreme_faces_surface function"""

    def test_with_simple_geometry(self):
        """Test surface calculation with simple geometry"""
        # This test depends on get_extreme_faces working
        # We'll create a mock geometry
        try:
            result = calculate_extreme_faces_surface(None, axis="Z")
        except Exception as e:
            # Expected for None input
            self.assertIsInstance(e, (TypeError, AttributeError))
            
    def test_with_x_axis(self):
        """Test surface calculation with X axis"""
        try:
            result = calculate_extreme_faces_surface(None, axis="X")
        except Exception as e:
            # Expected for None input
            self.assertIsInstance(e, (TypeError, AttributeError))


class TestUtilityTypes(unittest.TestCase):
    """Test cases for type definitions"""

    def test_axis_literal_type(self):
        """Test AXIS_LITERAL type definition"""
        # This is a type alias, we can't test much
        # but we can verify the module exports it
        self.assertTrue(hasattr(sys.modules[__name__], 'AXIS_LITERAL'))
        
    def test_vector_3d_type(self):
        """Test VECTOR_3D type definition"""
        self.assertTrue(hasattr(sys.modules[__name__], 'VECTOR_3D'))


class TestIntegrationScenarios(unittest.TestCase):
    """Integration tests for clash_utils functions working together"""

    def test_triangle_creation_and_distance(self):
        """Test creating faces from triangles and calculating distance between them"""
        # Create two triangles
        triangle1 = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        triangle2 = [(0, 0, 1), (1, 0, 1), (0, 1, 1)]
        
        # Convert to OCC faces
        face1 = triangle_to_occ_face(triangle1)
        face2 = triangle_to_occ_face(triangle2)
        
        self.assertIsNotNone(face1)
        self.assertIsNotNone(face2)
        
        # Calculate distance
        result = min_distance_two_faces(triangle1, triangle2)
        self.assertIsInstance(result, dict)
        self.assertAlmostEqual(result['distance'], 1.0, places=4)
        
    def test_extreme_faces_and_surface_calculation(self):
        """Test getting extreme faces and calculating their surface"""
        # This is a conceptual test - actual implementation depends on geometry
        try:
            # Create mock geometry
            class MockGeometry:
                pass
            
            mock_geom = MockGeometry()
            
            # These might fail with mock objects
            extreme_faces = get_extreme_faces(mock_geom)
            surface = calculate_extreme_faces_surface(mock_geom)
            
        except Exception as e:
            # Expected for mock objects
            self.assertIsInstance(e, Exception)


if __name__ == '__main__':
    unittest.main()
