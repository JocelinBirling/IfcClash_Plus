"""
Test suite for the FaceSelection engine of the FaceCheck family
(doc/2ObjectsRules/FaceCheck.md).

FaceCheck.md is the family summary: it defines the face selection shared
by the member rules (FaceClearance, FaceIntersect, FaceOBB, FaceOrient,
to be deployed when their specifications are written). This file tests
the engine itself: the FaceSelection dictionary (validation, filters)
and the material name resolution.

Execution (from the repository root):
    python -m pytest tests/test_FaceCheck.py -v
"""
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

sys.path.insert(0, "./ifcclash_plus")

import ifcopenshell
import ifcopenshell.api
import ifcopenshell.geom
import multiprocessing

from clash_utils import (
    get_element_material_names,
    select_faces,
    validate_face_selection,
)
from ifcopenshell.util.shape import get_vertices, get_faces


def closed_box_mesh():
    """A closed unit cube (12 triangles of area 0.5, outward normals)."""
    vertices = np.array(
        [
            [0.0, 0.0, 0.0], [1.0, 0.0, 0.0], [1.0, 1.0, 0.0], [0.0, 1.0, 0.0],
            [0.0, 0.0, 1.0], [1.0, 0.0, 1.0], [1.0, 1.0, 1.0], [0.0, 1.0, 1.0],
        ]
    )
    faces = np.array(
        [
            # Bottom (normal -Z).
            [0, 2, 1], [0, 3, 2],
            # Top (normal +Z).
            [4, 5, 6], [4, 6, 7],
            # Front (normal -Y).
            [0, 1, 5], [0, 5, 4],
            # Right (normal +X).
            [1, 2, 6], [1, 6, 5],
            # Back (normal +Y).
            [2, 3, 7], [2, 7, 6],
            # Left (normal -X).
            [3, 0, 4], [3, 4, 7],
        ]
    )
    return vertices, faces


def open_box_mesh():
    """An open box: a bottom face at z=0 and an inner ceiling at z=1
    facing down (a face of a hole pointing like the bottom face)."""
    vertices, faces = closed_box_mesh()
    faces = np.array(
        [
            # Bottom (normal -Z).
            [0, 2, 1], [0, 3, 2],
            # Inner ceiling (normal -Z), 1 m above the bottom.
            [4, 6, 5], [4, 7, 6],
            # Walls.
            [0, 1, 5], [0, 5, 4],
            [1, 2, 6], [1, 6, 5],
            [2, 3, 7], [2, 7, 6],
            [3, 0, 4], [3, 4, 7],
        ]
    )
    return vertices, faces


class TestFaceSelectionValidation(unittest.TestCase):
    """The FaceSelection dictionary schema."""

    def test_none_and_empty_select_all(self):
        self.assertEqual(validate_face_selection(None), {})
        self.assertEqual(validate_face_selection({}), {})

    def test_orientation_presets_and_vector(self):
        normalized = validate_face_selection({"orientation": "Top"})
        self.assertEqual(normalized["orientation"], "Top")

        normalized = validate_face_selection({"orientation": (0.0, 0.0, 2.0)})
        self.assertAlmostEqual(normalized["orientation"][2], 1.0)

    def test_unknown_key_raises(self):
        with self.assertRaises(ValueError):
            validate_face_selection({"color": "red"})

    def test_invalid_values_raise(self):
        with self.assertRaises(ValueError):
            validate_face_selection({"min_surface": -1.0})
        with self.assertRaises(ValueError):
            validate_face_selection({"orientation": "North"})
        with self.assertRaises(ValueError):
            validate_face_selection({"orientation": (0.0, 0.0, 0.0)})
        with self.assertRaises(ValueError):
            validate_face_selection({"orientation": (1.0, 2.0)})
        with self.assertRaises(ValueError):
            validate_face_selection({"extreme_faces": "yes"})
        with self.assertRaises(ValueError):
            validate_face_selection({"materials": "glass"})
        with self.assertRaises(ValueError):
            validate_face_selection({"materials": [42]})

    def test_interior_exterior_not_implemented_in_v1(self):
        with self.assertRaises(ValueError):
            validate_face_selection({"interior_exterior": "Interior"})

    def test_selection_must_be_a_dictionary(self):
        with self.assertRaises(ValueError):
            validate_face_selection(["orientation"])


class TestFaceSelection(unittest.TestCase):
    """The face filters of the FaceSelection engine."""

    def setUp(self):
        self.vertices, self.faces = closed_box_mesh()
        self.total = 12  # triangles of the cube

    def count(self, selection, material_names=None, vertices=None, faces=None):
        vertices = self.vertices if vertices is None else vertices
        faces = self.faces if faces is None else faces
        return len(select_faces(vertices, faces, selection, material_names))

    def test_empty_selection_returns_all_faces(self):
        self.assertEqual(self.count({}), self.total)
        self.assertEqual(self.count(None), self.total)

    def test_min_and_max_surface_strict_bounds(self):
        # Every triangle of the cube has an area of 0.5 m2.
        self.assertEqual(self.count({"min_surface": 0.4}), self.total)
        self.assertEqual(self.count({"max_surface": 0.6}), self.total)

        # Exactly at the bound: excluded (strictly above / below).
        self.assertEqual(self.count({"min_surface": 0.5}), 0)
        self.assertEqual(self.count({"max_surface": 0.5}), 0)

    def test_orientation_presets(self):
        self.assertEqual(self.count({"orientation": "Top"}), 2)
        self.assertEqual(self.count({"orientation": "Bottom"}), 2)
        # The 4 side faces, 2 triangles each.
        self.assertEqual(self.count({"orientation": "Side"}), 8)

    def test_orientation_vector(self):
        self.assertEqual(self.count({"orientation": (1.0, 0.0, 0.0)}), 2)
        self.assertEqual(self.count({"orientation": (0.0, -1.0, 0.0)}), 2)
        # A diagonal keeps nothing on an axis-aligned cube (45 degrees
        # is the limit: dot = cos(45) is not strictly above cos(45)).
        self.assertEqual(self.count({"orientation": (1.0, 1.0, 0.0)}), 0)

    def test_extreme_faces_keeps_only_the_extreme_plane(self):
        """On the open box, the inner ceiling points down like the
        bottom face but is not extreme: only the bottom is kept."""
        vertices, faces = open_box_mesh()

        selection = {"orientation": "Bottom", "extreme_faces": True}
        self.assertEqual(self.count(selection, vertices=vertices, faces=faces), 2)

        # Without extreme_faces, both the bottom and the ceiling match.
        self.assertEqual(self.count({"orientation": "Bottom"}, vertices=vertices, faces=faces), 4)

    def test_extreme_faces_requires_orientation(self):
        """Without orientation, extreme_faces is ignored."""
        self.assertEqual(self.count({"extreme_faces": True}), self.total)

    def test_materials_inclusion(self):
        self.assertEqual(
            self.count({"materials": ["Glass"]}, material_names=["Glass"]),
            self.total,
        )
        self.assertEqual(
            self.count({"materials": ["Glass"]}, material_names=["Wood"]),
            0,
        )
        # No material on the object: nothing matches.
        self.assertEqual(self.count({"materials": ["Glass"]}), 0)

    def test_keys_combine_with_and(self):
        self.assertEqual(
            self.count({"orientation": "Top", "min_surface": 0.4}), 2
        )
        self.assertEqual(
            self.count({"orientation": "Top", "min_surface": 0.6}), 0
        )
        self.assertEqual(
            self.count(
                {"orientation": "Top", "materials": ["Glass"]},
                material_names=["Glass"],
            ),
            2,
        )

    def test_empty_mesh(self):
        self.assertEqual(
            len(select_faces(np.zeros((0, 3)), np.zeros((0, 3), dtype=int), {})),
            0,
        )


class TestElementMaterialNames(unittest.TestCase):
    """The material name resolution of the engine (V1: object level)."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.temp_dir, True)

    def write_model(self, path, with_layer_set=False):
        file = ifcopenshell.api.run("project.create_file")
        ifcopenshell.api.run(
            "root.create_entity", file, ifc_class="IfcProject", name="P"
        )
        ifcopenshell.api.run(
            "unit.assign_unit", file, length={"is_metric": True, "raw": "METERS"}
        )
        context = ifcopenshell.api.run(
            "context.add_context", file, context_type="Model"
        )
        body = ifcopenshell.api.run(
            "context.add_context",
            file,
            context_type="Model",
            context_identifier="Body",
            target_view="MODEL_VIEW",
            parent=context,
        )
        element = ifcopenshell.api.run(
            "root.create_entity", file, ifc_class="IfcWall", name="W"
        )
        ifcopenshell.api.run(
            "geometry.edit_object_placement",
            file,
            product=element,
            matrix=((1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)),
        )
        profile = file.createIfcRectangleProfileDef(
            "AREA",
            None,
            file.createIfcAxis2Placement2D(
                file.createIfcCartesianPoint((0.0, 0.0)), None
            ),
            1.0,
            0.2,
        )
        representation = ifcopenshell.api.run(
            "geometry.add_profile_representation",
            file,
            context=body,
            profile=profile,
            depth=1.0,
        )
        ifcopenshell.api.run(
            "geometry.assign_representation",
            file,
            product=element,
            representation=representation,
        )

        if with_layer_set:
            layer_set = ifcopenshell.api.run(
                "material.add_material_set",
                file,
                name="WallLayers",
                set_type="IfcMaterialLayerSet",
            )
            ifcopenshell.api.run(
                "material.add_layer",
                file,
                layer_set=layer_set,
                material=ifcopenshell.api.run(
                    "material.add_material", file, name="Brick"
                ),
            )
            ifcopenshell.api.run(
                "material.add_layer",
                file,
                layer_set=layer_set,
                material=ifcopenshell.api.run(
                    "material.add_material", file, name="Plaster"
                ),
            )
            ifcopenshell.api.run(
                "material.assign_material",
                file,
                products=[element],
                type="IfcMaterialLayerSet",
                material=layer_set,
            )
        else:
            material = ifcopenshell.api.run(
                "material.add_material", file, name="Concrete"
            )
            ifcopenshell.api.run(
                "material.assign_material",
                file,
                products=[element],
                material=material,
            )
        file.write(path)

    def test_simple_material_name(self):
        path = os.path.join(self.temp_dir, "material.ifc")
        self.write_model(path)
        opened = ifcopenshell.open(path)
        element = opened.by_type("IfcWall")[0]
        self.assertEqual(get_element_material_names(element), ["Concrete"])

    def test_layer_set_names(self):
        path = os.path.join(self.temp_dir, "layers.ifc")
        self.write_model(path, with_layer_set=True)
        opened = ifcopenshell.open(path)
        element = opened.by_type("IfcWall")[0]
        self.assertEqual(
            sorted(get_element_material_names(element)), ["Brick", "Plaster"]
        )

    def test_element_without_material(self):
        file = ifcopenshell.api.run("project.create_file")
        ifcopenshell.api.run(
            "root.create_entity", file, ifc_class="IfcProject", name="P"
        )
        element = ifcopenshell.api.run(
            "root.create_entity", file, ifc_class="IfcWall", name="W"
        )
        self.assertEqual(get_element_material_names(element), [])

    def test_select_faces_with_real_material(self):
        """End to end: the materials filter selects the faces of a
        glass element, and rejects a concrete one."""
        path = os.path.join(self.temp_dir, "material.ifc")
        self.write_model(path)
        opened = ifcopenshell.open(path)
        element = opened.by_type("IfcWall")[0]

        settings = ifcopenshell.geom.settings()
        settings.set("USE_WORLD_COORDS", True)
        iterator = ifcopenshell.geom.iterator(
            settings, opened, multiprocessing.cpu_count(), include=[element]
        )
        iterator.initialize()
        shape = iterator.get()
        vertices = get_vertices(shape.geometry)
        faces = get_faces(shape.geometry)

        material_names = get_element_material_names(element)
        selected = select_faces(
            vertices, faces, {"materials": ["Concrete"]}, material_names
        )
        self.assertEqual(len(selected), len(faces))

        selected = select_faces(
            vertices, faces, {"materials": ["Glass"]}, material_names
        )
        self.assertEqual(len(selected), 0)


if __name__ == "__main__":
    unittest.main()
