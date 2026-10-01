import shapely
import shapely.ops
import numpy as np
import numpy.typing as npt
import ifcopenshell.ifcopenshell_wrapper as W
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.representation
from ifcopenshell.util.shape_builder import VectorType
from math import radians, cos
from ifcopenshell.geom import ShapeElementType, ShapeType
from typing import Optional, Literal, Union, Dict, List, Tuple
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon, BRepBuilderAPI_MakeFace
from OCC.Core.gp import gp_Pnt, gp_XYZ
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Face
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.BRep import BRep_Builder
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Shell, topods
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeSolid, BRepBuilderAPI_Sewing
from OCC.Core.TopAbs import TopAbs_SHELL
import math
from OCC.Core.gp import gp_Ax3, gp_Pnt, gp_Dir, gp_Trsf, gp_XYZ, gp_Vec
from OCC.Core.BRepGProp import BRepGProp_Face
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakeWire, BRepBuilderAPI_MakeEdge
from OCC.Core.TopoDS import TopoDS_Shell, TopoDS_Face
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface


AXIS_LITERAL = Literal["X", "Y", "Z"]

VECTOR_3D = tuple[float, float, float]

MatrixType = npt.NDArray[np.float64]
"""`npt.NDArray[np.float64]`"""


def get_extreme_faces(
    geometry: ShapeType,
    axis: AXIS_LITERAL = "Z",
    direction: Optional[VECTOR_3D] = None,
) -> list[VECTOR_3D]:
    
    #For skydome, there is no top because the object. It's not really possible to have a top.
    
    

    from ifcopenshell.util.shape import get_vertices,get_faces


 
    MIN_SURFACE_COVERAGE = 0.99


    if direction is None:
        # By default we will retrieve the top surface
        direction = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}[axis]

    vertices = get_vertices(geometry)
    faces = get_faces(geometry)

    # Calculate the triangle normal vectors
    v1 = vertices[faces[:, 1]] - vertices[faces[:, 0]]
    v2 = vertices[faces[:, 2]] - vertices[faces[:, 0]]
    triangle_normals = np.cross(v1, v2)

    # Normalize the normal vectors
    triangle_normals = triangle_normals / np.linalg.norm(triangle_normals, axis=1)[:, np.newaxis]
    direction = np.array(direction) / np.linalg.norm(direction)

    # Find the faces with a normal vector pointing in the desired direction using dot product
    # normal_tol < 0 is pointing away, = 0 is perpendicular, and > 0 is pointing towards.
    normal_tol = 0.1  # Close to perpendicular, but with a fuzz for numerical tolerance, 0.01 for almost no tolerance.
    dot_products = np.dot(triangle_normals, direction)
    filtered_face_indices = np.where(dot_products > normal_tol)[0]
    filtered_faces = faces[filtered_face_indices]

    polygons = [shapely.Polygon(vertices[face]) for face in filtered_faces]
    
    #Find the average height of each face in order to check if it's highest or lowest.
    list_of_z_avg=[]
    for face in filtered_faces:
        Points=vertices[face]
        z_avg=(Points[0][2]+Points[1][2]+Points[2][2])/3
        list_of_z_avg.append(z_avg)

    bottom_faces=[]
    for polygon,z_avg,face in zip(polygons,list_of_z_avg,filtered_faces):
        covered_area=0
        for loop_polygon,loop_z_avg in zip(polygons,list_of_z_avg):
            if polygon==loop_polygon:
                continue


            #This function can be used to find Top or Bottom element.
            if direction[2]==-1:
                if z_avg<loop_z_avg:
                    continue
            if direction[2]==1:
                if z_avg>loop_z_avg:
                    continue

            intersection=polygon.intersection(loop_polygon)
            covering_percent=intersection.area/polygon.area
            covered_area+=covering_percent

        #if the face is totaly recover, it's not a top (or bottom element). 
        if MIN_SURFACE_COVERAGE<covered_area:
            continue


        bottom_faces.append(face)
    
    return bottom_faces


def get_extreme_faces_OpenCascade(
    geometry: ShapeType,
    axis: AXIS_LITERAL = "Z",
    direction: Optional[VECTOR_3D] = None,
) -> list[VECTOR_3D]:
    
    #For skydome, there is no top because the object. It's not really possible to have a top.
    
    

    from ifcopenshell.util.shape import get_vertices,get_faces


 
    MIN_SURFACE_COVERAGE = 0.99


    if direction is None:
        # By default we will retrieve the top surface
        direction = {"X": (1.0, 0.0, 0.0), "Y": (0.0, 1.0, 0.0), "Z": (0.0, 0.0, 1.0)}[axis]

    vertices = get_vertices(geometry)
    faces = get_faces(geometry)

    # Calculate the triangle normal vectors
    v1 = vertices[faces[:, 1]] - vertices[faces[:, 0]]
    v2 = vertices[faces[:, 2]] - vertices[faces[:, 0]]
    triangle_normals = np.cross(v1, v2)

    # Normalize the normal vectors
    triangle_normals = triangle_normals / np.linalg.norm(triangle_normals, axis=1)[:, np.newaxis]
    direction = np.array(direction) / np.linalg.norm(direction)

    # Find the faces with a normal vector pointing in the desired direction using dot product
    # normal_tol < 0 is pointing away, = 0 is perpendicular, and > 0 is pointing towards.
    normal_tol = 0.1  # Close to perpendicular, but with a fuzz for numerical tolerance, 0.01 for almost no tolerance.
    dot_products = np.dot(triangle_normals, direction)
    filtered_face_indices = np.where(dot_products > normal_tol)[0]
    filtered_faces = faces[filtered_face_indices]

    polygons = [shapely.Polygon(vertices[face]) for face in filtered_faces]
    
    #Find the average height of each face in order to check if it's highest or lowest.
    list_of_z_avg=[]
    for face in filtered_faces:
        Points=vertices[face]
        z_avg=(Points[0][2]+Points[1][2]+Points[2][2])/3
        list_of_z_avg.append(z_avg)

    bottom_faces=[]
    for polygon,z_avg,face in zip(polygons,list_of_z_avg,filtered_faces):
        covered_area=0
        for loop_polygon,loop_z_avg in zip(polygons,list_of_z_avg):
            if polygon==loop_polygon:
                continue


            #This function can be used to find Top or Bottom element.
            if direction[2]==-1:
                if z_avg<loop_z_avg:
                    continue
            if direction[2]==1:
                if z_avg>loop_z_avg:
                    continue

            intersection=polygon.intersection(loop_polygon)
            covering_percent=intersection.area/polygon.area
            covered_area+=covering_percent

        #if the face is totaly recover, it's not a top (or bottom element). 
        if MIN_SURFACE_COVERAGE<covered_area:
            continue


        bottom_faces.append(face)
    
    return bottom_faces


def faces_to_compound(faces):
    """Toujours valide, même avec une seule face."""
    if not faces:
        return None
    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)
    for face in faces:
        builder.Add(compound, face)
    return compound


def list_of_faces_to_list_of_TopoDS_Face(list_of_faces,vertices):

    list_of_faces=[]
    
    for source_face in list_of_faces:

        s0 = vertices[source_face[0]]
        g0 = gp_Pnt(s0[0],s0[1],s0[2])

        s1 = vertices[source_face[1]]
        g1 = gp_Pnt(s1[0],s1[1],s1[2])

        s2 = vertices[source_face[2]]
        g2 = gp_Pnt(s2[0],s2[1],s2[2])


        edge1 = BRepBuilderAPI_MakeEdge(g0,g1).Edge()
        edge2 = BRepBuilderAPI_MakeEdge(g1, g2).Edge()
        edge3 = BRepBuilderAPI_MakeEdge(g2, g0).Edge()
        wire = BRepBuilderAPI_MakeWire(edge1, edge2, edge3).Wire()
        face = BRepBuilderAPI_MakeFace(wire).Face()
        list_of_faces.append(face)

    return list_of_faces 

def faces_to_shell(faces: list[TopoDS_Face]) -> TopoDS_Shell:
    """
    Construit un TopoDS_Shell à partir d'une liste de TopoDS_Face.

    Args:
        faces: Liste de faces à assembler

    Returns:
        TopoDS_Shell contenant toutes les faces
    """
    builder = BRep_Builder()
    shell = TopoDS_Shell()
    builder.MakeShell(shell)

    for face in faces:
        builder.Add(shell, face)

    return shell

def faces_to_shell_sewed(
    faces: list[TopoDS_Face],
    tolerance: float = 1e-3
) -> TopoDS_Shell:
    """
    Construit un TopoDS_Shell cousu (sewed) à partir d'une liste de TopoDS_Face.
    Le sewing recoud les edges partagées entre faces adjacentes,
    produisant un shell topologiquement propre.

    Args:
        faces:     Liste de faces à assembler
        tolerance: Tolérance de couture (défaut 1e-3)

    Returns:
        TopoDS_Shell cousu
    """
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Sewing
    from OCC.Core.TopoDS import topods

    sewing = BRepBuilderAPI_Sewing(tolerance)

    for face in faces:
        sewing.Add(face)

    sewing.Perform()
    sewed_shape = sewing.SewedShape()

    # Le résultat peut être un Shell, un Compound, ou une Face selon les cas
    from OCC.Core.TopAbs import TopAbs_SHELL, TopAbs_FACE, TopAbs_COMPOUND
    from OCC.Core.TopExp import TopExp_Explorer

    if sewed_shape.ShapeType() == TopAbs_SHELL:
        return topods.Shell(sewed_shape)

    # Si c'est un Compound (faces non connexes), on extrait le premier shell
    # ou on en construit un manuellement
    shell_faces = []
    explorer = TopExp_Explorer(sewed_shape, TopAbs_FACE)  # TopAbs_FACE pas TopAbs_SHELL car faces disjointes
    while explorer.More():
        shell_faces.append(explorer.Current())
        explorer.Next()

    builder = BRep_Builder()
    shell = TopoDS_Shell()
    builder.MakeShell(shell)
    for f in shell_faces:
        builder.Add(shell, f)

    return shell


def check_shell(shell: TopoDS_Shell) -> dict:
    """
    Vérifie la validité du shell et retourne un rapport.
    """
    analyzer = BRepCheck_Analyzer(shell)
    is_valid = analyzer.IsValid()

    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopAbs import TopAbs_FACE

    face_count = 0
    explorer = TopExp_Explorer(shell, TopAbs_FACE)
    while explorer.More():
        face_count += 1
        explorer.Next()

    return {
        "is_valid": is_valid,
        "face_count": face_count,
    }

from OCC.Core.TopoDS import TopoDS_Shell
from OCC.Core.ShapeFix import ShapeFix_Shell, ShapeFix_Shape
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE

from OCC.Core.BRepCheck import BRepCheck_ListIteratorOfListOfStatus
def diagnose_shell(shell: TopoDS_Shell) -> dict:
    from OCC.Core.BRepCheck import (
        BRepCheck_NoError,
        BRepCheck_InvalidPointOnCurve,
        BRepCheck_InvalidPointOnCurveOnSurface,
        BRepCheck_InvalidPointOnSurface,
        BRepCheck_No3DCurve,
        BRepCheck_Multiple3DCurve,
        BRepCheck_Invalid3DCurve,
        BRepCheck_NoCurveOnSurface,
        BRepCheck_InvalidCurveOnSurface,
        BRepCheck_InvalidCurveOnClosedSurface,
        BRepCheck_InvalidSameRangeFlag,
        BRepCheck_InvalidSameParameterFlag,
        BRepCheck_NotClosed,
        BRepCheck_NotConnected,
        BRepCheck_RedundantFace,
    )

    ERROR_LABELS = {
        BRepCheck_NoError: "NoError",
        BRepCheck_InvalidPointOnCurve: "InvalidPointOnCurve",
        BRepCheck_InvalidPointOnCurveOnSurface: "InvalidPointOnCurveOnSurface",
        BRepCheck_InvalidPointOnSurface: "InvalidPointOnSurface",
        BRepCheck_No3DCurve: "No3DCurve",
        BRepCheck_Multiple3DCurve: "Multiple3DCurve",
        BRepCheck_Invalid3DCurve: "Invalid3DCurve",
        BRepCheck_NoCurveOnSurface: "NoCurveOnSurface",
        BRepCheck_InvalidCurveOnSurface: "InvalidCurveOnSurface",
        BRepCheck_InvalidCurveOnClosedSurface: "InvalidCurveOnClosedSurface",
        BRepCheck_InvalidSameRangeFlag: "InvalidSameRangeFlag",
        BRepCheck_InvalidSameParameterFlag: "InvalidSameParameterFlag",
        BRepCheck_NotClosed: "NotClosed",
        BRepCheck_NotConnected: "NotConnected",
        BRepCheck_RedundantFace: "RedundantFace",
    }

    def iter_status(result, shape_label: str) -> list:
        """Itère sur un BRepCheck_Result et retourne les erreurs."""
        if result is None:
            return []
        errors = []
        status_list = result.Status()
        it = BRepCheck_ListIteratorOfListOfStatus(status_list)
        while it.More():
            code = it.Value()
            if code != BRepCheck_NoError:
                label = ERROR_LABELS.get(code, f"Unknown({code})")
                errors.append({"shape": shape_label, "error": label, "code": code})
            it.Next()
        return errors

    analyzer = BRepCheck_Analyzer(shell)
    errors = []

    # Vérification de chaque face
    explorer = TopExp_Explorer(shell, TopAbs_FACE)
    while explorer.More():
        face = explorer.Current()
        errors += iter_status(analyzer.Result(face), "Face")
        explorer.Next()

    # Vérification du shell lui-même
    errors += iter_status(analyzer.Result(shell), "Shell")

    return {
        "is_valid": analyzer.IsValid(),
        "errors": errors,
    }

def repair_shell(
    shell: TopoDS_Shell,
    tolerance: float = 1e-3,
    fix_orientation: bool = True,
) -> TopoDS_Shell:
    """
    Répare un TopoDS_Shell invalide via ShapeFix.

    Corrections appliquées :
      - Réorientation des faces incohérentes
      - Couture des edges libres (free edges)
      - Correction des courbes 3D / pcurves manquantes
      - Correction same-range / same-parameter
      - Suppression des faces redondantes

    Args:
        shell:           Shell à réparer
        tolerance:       Tolérance de réparation
        fix_orientation: Tente de rendre le shell fermé en réorientant les faces

    Returns:
        Shell réparé (nouveau TopoDS_Shell)
    """
    from OCC.Core.TopoDS import topods

    fixer = ShapeFix_Shell(shell)

    fixer.SetPrecision(tolerance)
    fixer.SetMinTolerance(tolerance * 0.01)
    fixer.SetMaxTolerance(tolerance * 10.0)

    # Réorientation des faces dont la normale est incohérente avec le shell
    fixer.SetFixOrientationMode(1 if fix_orientation else 0)

    # Recoud les edges libres restantes
    fixer.SetFixFaceMode(1)

    fixer.Perform()

    result = fixer.Shell()

    explorer = TopExp_Explorer(result, TopAbs_SHELL)
    if explorer.More():
        return topods.Shell(explorer.Current())

    if result.ShapeType() == TopAbs_SHELL:  # ✅ comparaison directe avec la constante
        return topods.Shell(result)

    return shell  # fallback

def get_faces_toward_direction(shape, direction: gp_Dir, angle_threshold_deg=45.0):
    cos_threshold = math.cos(math.radians(angle_threshold_deg))
    ref = gp_Vec(direction.X(), direction.Y(), direction.Z())

    result = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)

    while explorer.More():
        face = topods.Face(explorer.Current())
        props = BRepGProp_Face(face)

        umin, umax, vmin, vmax = props.Bounds()
        u_mid = (umin + umax) / 2.0
        v_mid = (vmin + vmax) / 2.0

        pnt = gp_Pnt()
        nor = gp_Vec()
        props.Normal(u_mid, v_mid, pnt, nor)

        mag = nor.Magnitude()
        if mag > 1e-10:
            nor.Divide(mag)
            if nor.Dot(ref) > cos_threshold:
                result.append(face)

        explorer.Next()

    # Retourner directement un compound — pas besoin de sewing ni de solid
    return faces_to_compound(result)

def triangle_to_occ_face(triangle):
    """Convertit un triangle en face OpenCASCADE"""
    # Check for invalid input (less than 3 points)
    if not triangle or len(triangle) < 3:
        return None
    
    polygon = BRepBuilderAPI_MakePolygon()
    for point in triangle:
        polygon.Add(gp_Pnt(float(point[0]), float(point[1]), float(point[2])))
    polygon.Close()
    
    if polygon.IsDone():
        face = BRepBuilderAPI_MakeFace(polygon.Wire())
        if face.IsDone():
            return face.Face()
    return None


def get_XYZ_placement(Object):
    Origin = ifcopenshell.util.placement.get_local_placement(
        Object.ObjectPlacement
    )
    Origin = Origin[:, 3][:3]
    Origin = (float(Origin[0]), float(Origin[1]), float(Origin[2]))
    return Origin


def calculate_extreme_faces_surface(
    geometry: ShapeType,
    axis: AXIS_LITERAL = "Z",
    direction: Optional[VECTOR_3D] = None
) -> float:
    """
    Calcule la surface totale des faces extrêmes retournées par get_extreme_faces.

    Args:
        geometry: La géométrie à analyser
        axis: Axe selon lequel trouver les faces extrêmes (X, Y, Z)
        direction: Direction personnalisée (optionnel)

    Returns:
        La surface totale en unités carrées
    """
    from ifcopenshell.util.shape import get_vertices

    extreme_faces = get_extreme_faces(geometry, axis, direction)
    vertices = get_vertices(geometry)

    total_surface = 0.0
    for face in extreme_faces:

        points = vertices[face]
        v1 = points[1] - points[0]
        v2 = points[2] - points[0]
        cross_product = np.cross(v1, v2)
        triangle_area = 0.5 * np.linalg.norm(cross_product)
        total_surface += triangle_area

    print("Total Surface", total_surface)
    return total_surface

def get_extreme_faces_with_area(
    geometry: ShapeType,
    axis: AXIS_LITERAL = "Z",
    direction: Optional[VECTOR_3D] = None,
) -> dict:
    """
    Calcule les faces extrêmes selon une direction donnée et retourne leur surface totale.
    
    Args:
        geometry: La géométrie à analyser (ShapeType de ifcopenshell).
        axis: L'axe selon lequel trouver les faces extrêmes (X, Y, Z).
        direction: Direction personnalisée (optionnel). Si None, utilise la direction positive de l'axe.
    
    Returns:
        Un dictionnaire contenant:
        - extrem_faces: Liste des indices des faces extrêmes.
        - total_area: Surface totale des faces extrêmes (sans recouvrement).
    """
    #@todo Verify this function with complex shape
    from ifcopenshell.util.shape import get_vertices
    
    # Utiliser get_extreme_faces pour obtenir les faces extrêmes
    extrem_faces = get_extreme_faces(geometry, axis, direction)
    
    if len(extrem_faces) == 0:
        return {"extrem_faces": [], "total_area": 0.0}
    
    vertices = get_vertices(geometry)
    
    # Calculer la surface totale des faces extrêmes (surface réelle, sans projection)
    total_area = 0.0
    for face in extrem_faces:
        points = vertices[face]
        v1 = points[1] - points[0]
        v2 = points[2] - points[0]
        cross_product = np.cross(v1, v2)
        triangle_area = 0.5 * np.linalg.norm(cross_product)
        total_area += triangle_area
    
    return {"extrem_faces": extrem_faces, "total_area": total_area}


def calculate_geometry_size_from_3_points(p1, p2, p3):
    """
    Calculate the size (area) of a triangle defined by three points in 3D space.

    Args:
        p1 (tuple[float, float, float]): First point coordinates (x, y, z).
        p2 (tuple[float, float, float]): Second point coordinates (x, y, z).
        p3 (tuple[float, float, float]): Third point coordinates (x, y, z).

    Returns:
        float: The area of the triangle formed by the three points.
    """
    # Convert points to numpy arrays for vector operations
    p1_arr = np.array(p1)
    p2_arr = np.array(p2)
    p3_arr = np.array(p3)

    # Calculate vectors from p1 to p2 and p1 to p3
    v1 = p2_arr - p1_arr
    v2 = p3_arr - p1_arr

    # Calculate the cross product of v1 and v2
    cross_product = np.cross(v1, v2)

    # The area of the triangle is half the magnitude of the cross product
    area = 0.5 * np.linalg.norm(cross_product)

    return area


def clash_bvh_copy_from_CPP(
    bvh_a,
    bvh_b,
    extend: float = 0.0
) -> Dict[int, List[int]]:
    """
    Detects collisions between two BVH trees and returns a dictionary of clashing pairs.
    This function is a Python port of the C++ `clash_bvh` function, designed to work with
    OpenCASCADE BVH trees for efficient collision detection.

    Args:
        bvh_a: The first BVH tree (source).
        bvh_b: The second BVH tree (target).
        extend: Additional tolerance for bounding box expansion (default: 0.0).

    Returns:
        A dictionary where keys are indices from `bvh_a` and values are lists of indices from `bvh_b` that collide.
    """
    bvh_clashes: Dict[int, List[int]] = {}

    # Iterate over all nodes in `bvh_a`
    for i in range(bvh_a.Length()):
        if not bvh_a.IsOuter(i):
            continue  # Skip non-outer nodes

        # Get the bounding box for node `i` in `bvh_a`
        bvh_a_min = bvh_a.MinPoint(i)
        bvh_a_max = bvh_a.MaxPoint(i)

        # Expand the bounding box slightly to avoid numerical issues
        bvh_a_min_expanded = gp_XYZ(
            bvh_a_min.X() - 1e-3,
            bvh_a_min.Y() - 1e-3,
            bvh_a_min.Z() - 1e-3,
        )
        bvh_a_max_expanded = gp_XYZ(
            bvh_a_max.X() + 1e-3,
            bvh_a_max.Y() + 1e-3,
            bvh_a_max.Z() + 1e-3,
        )

        # Create a bounding box for `bvh_a` node `i`
        box_a = Bnd_Box()
        box_a.Add(gp_Pnt(bvh_a_min_expanded))
        box_a.Add(gp_Pnt(bvh_a_max_expanded))

        # Use a stack to traverse `bvh_b` (DFS)
        stack = [0]  # Start from the root of `bvh_b`

        while stack:
            j = stack.pop()

            # Get the bounding box for node `j` in `bvh_b`
            bvh_b_min = bvh_b.MinPoint(j)
            bvh_b_max = bvh_b.MaxPoint(j)

            # Expand the bounding box with `extend` and a small tolerance
            bvh_b_min_expanded = gp_XYZ(
                bvh_b_min.X() - (extend + 1e-3),
                bvh_b_min.Y() - (extend + 1e-3),
                bvh_b_min.Z() - (extend + 1e-3),
            )
            bvh_b_max_expanded = gp_XYZ(
                bvh_b_max.X() + (extend + 1e-3),
                bvh_b_max.Y() + (extend + 1e-3),
                bvh_b_max.Z() + (extend + 1e-3),
            )

            # Create a bounding box for `bvh_b` node `j`
            box_b = Bnd_Box()
            box_b.Add(gp_Pnt(bvh_b_min_expanded))
            box_b.Add(gp_Pnt(bvh_b_max_expanded))

            # Check if `box_a` and `box_b` overlap
            if box_a.IsOut(box_b):
                continue  # No collision, skip

            # If `j` is an outer node, record the collision
            if bvh_b.IsOuter(j):
                if i in bvh_clashes:
                    bvh_clashes[i].append(j)
                else:
                    bvh_clashes[i] = [j]
            else:
                # Push children of `j` onto the stack for further traversal
                stack.append(bvh_b.Child(0, j))
                stack.append(bvh_b.Child(1, j))

    return bvh_clashes

from OCC.Core.TopoDS import TopoDS_Shape, TopoDS_Face
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.BRep import BRep_Tool
from OCC.Core.BRepAdaptor import BRepAdaptor_Surface
from OCC.Core.GeomAbs import GeomAbs_Plane
from OCC.Core.gp import gp_Dir, gp_Pnt, gp_Lin
from OCC.Core.BRepIntCurveSurface import BRepIntCurveSurface_Inter
from OCC.Core.IntCurveSurface import IntCurveSurface_TransitionOnCurve
from OCC.Core.BRepGProp import brepgprop
from OCC.Core.GProp import GProp_GProps
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.Bnd import Bnd_Box


def get_face_normal(face: TopoDS_Face) -> gp_Dir:
    """
    Retourne la normale moyenne d'une face plane.
    Pour les faces non-planes, utilise le centre de la surface.
    """
    surface = BRepAdaptor_Surface(face)

    u_mid = (surface.FirstUParameter() + surface.LastUParameter()) / 2.0
    v_mid = (surface.FirstVParameter() + surface.LastVParameter()) / 2.0

    props = surface.Surface()

    # Calcul de la normale via les dérivées partielles
    from OCC.Core.gp import gp_Vec
    p, du, dv = gp_Pnt(), gp_Vec(), gp_Vec()
    surface.D1(u_mid, v_mid, p, du, dv)

    normal_vec = du.Crossed(dv)
    if normal_vec.Magnitude() < 1e-10:
        return None

    normal_dir = gp_Dir(normal_vec)

    # Inverser si la face est orientée "reversed" dans la shape
    from OCC.Core.TopAbs import TopAbs_REVERSED
    if face.Orientation() == TopAbs_REVERSED:
        normal_dir.Reverse()

    return normal_dir


def get_face_center(face: TopoDS_Face) -> gp_Pnt:
    """Retourne le centre de gravité d'une face."""
    props = GProp_GProps()
    brepgprop.SurfaceProperties(face, props)
    return props.CentreOfMass()


def is_face_oriented_toward_direction(
    face: TopoDS_Face,
    direction: gp_Dir,
    angle_tolerance_deg: float = 45.0
) -> bool:
    """
    Vérifie si une face est orientée dans la direction donnée.
    La normale de la face doit former un angle <= angle_tolerance_deg avec la direction.
    """
    import math
    normal = get_face_normal(face)
    if normal is None:
        return False

    dot = normal.Dot(direction)
    angle_rad = math.acos(max(-1.0, min(1.0, dot)))
    angle_deg = math.degrees(angle_rad)

    return angle_deg <= angle_tolerance_deg


def is_face_visible(
    face: TopoDS_Face,
    shape: TopoDS_Shape,
    direction: gp_Dir,
    n_samples: int = 5
) -> bool:
    from OCC.Core.gp import gp_Vec

    OFFSET = 1e-3

    surface = BRepAdaptor_Surface(face)
    u_min = surface.FirstUParameter()
    u_max = surface.LastUParameter()
    v_min = surface.FirstVParameter()
    v_max = surface.LastVParameter()

    sample_params = []
    for i in range(n_samples):
        for j in range(n_samples):
            u = u_min + (u_max - u_min) * (i + 0.5) / n_samples
            v = v_min + (v_max - v_min) * (j + 0.5) / n_samples
            sample_params.append((u, v))

    visible_count = 0

    for u, v in sample_params:
        p = gp_Pnt()
        du, dv = gp_Vec(), gp_Vec()
        surface.D1(u, v, p, du, dv)

        origin = gp_Pnt(
            p.X() + direction.X() * OFFSET,
            p.Y() + direction.Y() * OFFSET,
            p.Z() + direction.Z() * OFFSET,
        )

        ray = gp_Lin(origin, direction)

        inter = BRepIntCurveSurface_Inter()
        inter.Init(shape, ray, 1e-7)

        hit_other_face = False
        while inter.More():
            t = inter.W()
            if t > OFFSET:
                hit_face = inter.Face()
                if not hit_face.IsSame(face):
                    hit_other_face = True
                    break
            inter.Next()

        if not hit_other_face:
            visible_count += 1

    return visible_count > (n_samples * n_samples) / 2

def get_visible_faces_in_direction(
    shape: TopoDS_Shape,
    direction: gp_Dir,
    angle_tolerance_deg: float = 45.0,
    n_ray_samples: int = 3,
) -> list[TopoDS_Face]:
    """
    Retourne la liste des faces du TopoDS_Shape qui sont :
      1. Orientées dans la direction donnée (normale alignée avec direction)
      2. Non occultées par d'autres faces de la géométrie

    Args:
        shape:               La géométrie d'entrée
        direction:           Direction de vue (gp_Dir)
        angle_tolerance_deg: Tolérance angulaire entre la normale et la direction (défaut 45°)
        n_ray_samples:       Nombre de subdivisions par axe pour le lancer de rayons (défaut 3 → 9 rayons)

    Returns:
        Liste de TopoDS_Face visibles dans la direction.
    """
    candidate_faces = []

    # Étape 1 : Explorer toutes les faces et filtrer par orientation
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = explorer.Current()
        if is_face_oriented_toward_direction(face, direction, angle_tolerance_deg):
            candidate_faces.append(face)
        explorer.Next()

    # Étape 2 : Parmi les candidats, ne garder que les faces non occultées
    visible_faces = []
    for face in candidate_faces:
        if is_face_visible(face, shape, direction, n_samples=n_ray_samples):
            visible_faces.append(face)

    return visible_faces

def min_distance_two_faces(ListPoint1, ListPoint2):
    face1 = triangle_to_occ_face(ListPoint1)
    face2 = triangle_to_occ_face(ListPoint2)
    
    if face1 is None or face2 is None:
        raise ValueError("Not possible to create face")
    
    dist_calc = BRepExtrema_DistShapeShape(face1, face2)
    
    if dist_calc.IsDone():
        point1 = dist_calc.PointOnShape1(1)
        point2 = dist_calc.PointOnShape2(1)
        
        return {
            'distance': dist_calc.Value(),
            'point1': [point1.X(), point1.Y(), point1.Z()],
            'point2': [point2.X(), point2.Y(), point2.Z()]
        }
    
    raise RuntimeError("Fail to calculate distance")



#### Function for Above Rule
def create_view_plane(
    shape: TopoDS_Shape,
    direction: gp_Dir,
    distance: float = 100.0,
    size_factor: float = 2.0
) -> TopoDS_Face:
    """
    Crée un plan perpendiculaire à la direction, placé à une distance donnée derrière la géométrie.
    
    Ce plan sert de surface de projection pour le lancer de rayons.
    
    Args:
        shape: La géométrie à analyser
        direction: Direction de vue (gp_Dir) - depuis le point de vue vers la scène
        distance: Distance à laquelle placer le plan derrière la géométrie (défaut: 100.0)
        size_factor: Facteur de taille du plan par rapport à la boîte englobante (défaut: 2.0)
    
    Returns:
        TopoDS_Face: Une face plane rectangulaire perpendiculaire à la direction
    """
    from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon
    
    # Calculer la boîte englobante de la shape
    bbox = Bnd_Box()
    brepbndlib.Add(shape, bbox)
    
    # Obtenir les coins min et max
    corner_min = bbox.CornerMin()
    corner_max = bbox.CornerMax()
    
    # Calculer le centre de la géométrie
    center = gp_Pnt(
        (corner_min.X() + corner_max.X()) / 2.0,
        (corner_min.Y() + corner_max.Y()) / 2.0,
        (corner_min.Z() + corner_max.Z()) / 2.0
    )
    
    # Calculer les dimensions de la boîte englobante
    width = corner_max.X() - corner_min.X()
    height = corner_max.Y() - corner_min.Y()
    depth = corner_max.Z() - corner_min.Z()
    
    # Calculer la taille du plan (suffisamment grand pour couvrir la géométrie)
    max_dim = max(width, height, depth)
    plane_size = max_dim * size_factor
    
    # Déplacer le centre dans la direction inverse pour placer le plan derrière
    # La direction pointe VERS la scène, donc on va dans la direction opposée
    offset_vec = gp_Vec(direction.X(), direction.Y(), direction.Z())
    offset_vec.Multiply(-distance)  # Direction inverse
    plane_center = gp_Pnt(
        center.X() + offset_vec.X(),
        center.Y() + offset_vec.Y(),
        center.Z() + offset_vec.Z()
    )
    
    # Trouver deux vecteurs perpendiculaires à la direction pour définir le plan
    dir_vec = gp_Vec(direction.X(), direction.Y(), direction.Z())
    
    # Trouver un premier vecteur perpendiculaire
    if abs(dir_vec.X()) < 0.5:
        base_x = gp_Vec(1, 0, 0)
    else:
        base_x = gp_Vec(0, 1, 0)
    
    # Orthogonaliser base_x par rapport à dir_vec
    dot_x_dir = base_x.Dot(dir_vec)
    dir_squared = dir_vec.Dot(dir_vec)
    if dir_squared > 1e-10:
        factor = dot_x_dir / dir_squared
        dir_scaled = gp_Vec(dir_vec.X() * factor, dir_vec.Y() * factor, dir_vec.Z() * factor)
        base_x.Subtract(dir_scaled)
    
    # Normaliser base_x
    base_x_mag = base_x.Magnitude()
    if base_x_mag > 1e-10:
        base_x.Divide(base_x_mag)
    
    # Calculer base_y = dir_vec × base_x
    base_y = dir_vec.Crossed(base_x)
    base_y_mag = base_y.Magnitude()
    if base_y_mag > 1e-10:
        base_y.Divide(base_y_mag)
    
    # Calculer les 4 coins du plan rectangulaire
    half_size = plane_size / 2.0
    
    corner1 = gp_Pnt(
        plane_center.X() - base_x.X() * half_size - base_y.X() * half_size,
        plane_center.Y() - base_x.Y() * half_size - base_y.Y() * half_size,
        plane_center.Z() - base_x.Z() * half_size - base_y.Z() * half_size
    )
    corner2 = gp_Pnt(
        plane_center.X() + base_x.X() * half_size - base_y.X() * half_size,
        plane_center.Y() + base_x.Y() * half_size - base_y.Y() * half_size,
        plane_center.Z() + base_x.Z() * half_size - base_y.Z() * half_size
    )
    corner3 = gp_Pnt(
        plane_center.X() + base_x.X() * half_size + base_y.X() * half_size,
        plane_center.Y() + base_x.Y() * half_size + base_y.Y() * half_size,
        plane_center.Z() + base_x.Z() * half_size + base_y.Z() * half_size
    )
    corner4 = gp_Pnt(
        plane_center.X() - base_x.X() * half_size + base_y.X() * half_size,
        plane_center.Y() - base_x.Y() * half_size + base_y.Y() * half_size,
        plane_center.Z() - base_x.Z() * half_size + base_y.Z() * half_size
    )
    
    # Créer la face rectangulaire
    polygon = BRepBuilderAPI_MakePolygon()
    polygon.Add(corner1)
    polygon.Add(corner2)
    polygon.Add(corner3)
    polygon.Add(corner4)
    polygon.Close()
    
    face = BRepBuilderAPI_MakeFace(polygon.Wire())
    if face.IsDone():
        return face.Face()
    
    raise RuntimeError("Failed to create view plane")

def sample_points_on_face(face: TopoDS_Face, n_samples: int = 3) -> List[gp_Pnt]:
    """
    Échantillonne des points uniformément sur une face.
    
    Args:
        face: La face à échantillonner
        n_samples: Nombre de subdivisions par dimension (défaut: 3 → 9 points)
    
    Returns:
        Liste de points gp_Pnt échantillonnés sur la face
    """
    surface = BRepAdaptor_Surface(face)
    
    u_min = surface.FirstUParameter()
    u_max = surface.LastUParameter()
    v_min = surface.FirstVParameter()
    v_max = surface.LastVParameter()
    
    points = []
    for i in range(n_samples):
        for j in range(n_samples):
            u = u_min + (u_max - u_min) * (i + 0.5) / n_samples
            v = v_min + (v_max - v_min) * (j + 0.5) / n_samples
            
            pnt = gp_Pnt()
            surface.D0(u, v, pnt)
            points.append(pnt)
    
    return points

def get_faces_visible_from_direction_with_plane(
    shape: TopoDS_Shape,
    direction: gp_Dir,
    angle_tolerance_deg: float = 45.0,
    plane_distance: float = 100.0,
    plane_size_factor: float = 1.0,
    n_ray_samples: int = 9
) -> dict:
    """
    Détermine les faces visibles depuis une direction en créant un plan perpendiculaire
    et en tirant des rayons depuis ce plan vers la géométrie.
    
    Cette fonction simule un point de vue lointain : les rayons sont tirés depuis un plan
    situé derrière l'objet (dans la direction opposée à la direction de vue) vers l'objet.


    #@todo If the object has a lot of triangle, the number of ray samples must be increased a lot in order to get the full surface.

    #This function has the advantages of giving the extrem surface even in case of bad modeling (flipped surface) but for complex objects it can not give best solution.
    
    Args:
        shape: La géométrie à analyser
        direction: Direction de vue (gp_Dir) - depuis le point de vue vers la scène
        angle_tolerance_deg: Tolérance angulaire pour considérer une face comme orientée
                            vers la direction (défaut: 45.0 degrés)
        plane_distance: Distance à laquelle placer le plan derrière la géométrie (défaut: 100.0)
        plane_size_factor: Facteur de taille du plan par rapport à la boîte englobante (défaut: 2.0)
        n_ray_samples: Nombre de subdivisions par axe pour le lancer de rayons (défaut: 3 → 9 rayons)
    
    Returns:
        dict contenant:
        - visible_faces: Liste des TopoDS_Face visibles (intersectées par les rayons)
        - plane: Le plan perpendiculaire créé (TopoDS_Face)
        - all_faces_toward_direction: Toutes les faces orientées vers la direction
        - occluded_faces: Faces orientées vers la direction mais non visibles (masquées)
        - hit_count: Dictionnaire {face: nombre_de_rayons_qui_ont_intersecté}
    """
    import math
    from OCC.Core.BRepIntCurveSurface import BRepIntCurveSurface_Inter
    from OCC.Core.gp import gp_Lin
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopAbs import TopAbs_FACE
    from OCC.Core.TopoDS import topods
    
    direction=-direction # We need to invert it, otherwise it doesn't make sense for the user.

    # Étape 1: Créer le plan perpendiculaire
    plane = create_view_plane(shape, direction, plane_distance, plane_size_factor)
    
    # Étape 2: Échantillonner des points sur le plan
    sample_points = sample_points_on_face(plane, n_ray_samples)
    
    # Étape 3: Trouver toutes les faces orientées vers la direction
    all_faces_toward_direction = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    
    while explorer.More():
        face = topods.Face(explorer.Current())
        if is_face_oriented_toward_direction(face, direction, angle_tolerance_deg):
            all_faces_toward_direction.append(face)
        explorer.Next()
    
    # Étape 4: Tirer des rayons depuis chaque point du plan et collecter les intersections
    hit_count = {}  # Compteur de rayons par face
    
    for point in sample_points:
        # Créer un rayon depuis le point dans la direction (vers la scène)
        ray = gp_Lin(point, direction)
        
        # Trouver les intersections avec la shape
        inter = BRepIntCurveSurface_Inter()
        inter.Init(shape, ray, 1e-7)
        
        first_hit_face = None
        first_hit_distance = float('inf')
        
        while inter.More():
            t = inter.W()
            if t < 0:
                inter.Next()
                continue
            
            hit_face = inter.Face()
            
            # Calculer le point d'intersection sur le rayon
            # point_on_ray = ray.Location() + t * ray.Direction()
            ray_location = ray.Location()
            ray_dir = ray.Direction()
            hit_point = gp_Pnt(
                ray_location.X() + t * ray_dir.X(),
                ray_location.Y() + t * ray_dir.Y(),
                ray_location.Z() + t * ray_dir.Z()
            )
            
            # Calculer la distance du point de départ du rayon au point d'intersection
            distance = point.Distance(hit_point)
            
            if distance < first_hit_distance:
                first_hit_distance = distance
                first_hit_face = hit_face
            
            inter.Next()
        
        # Si on a trouvé une face intersectée, incrémenter son compteur
        if first_hit_face is not None:
            face_key = first_hit_face
            if face_key in hit_count:
                hit_count[face_key] += 1
            else:
                hit_count[face_key] = 1
    
    # Étape 5: Classer les faces
    visible_faces = list(hit_count.keys())
    
    # Trouver les faces masquées : orientées vers la direction mais non intersectées
    occluded_faces = []
    for face in all_faces_toward_direction:
        if face not in hit_count:
            occluded_faces.append(face)
    
    return {
        'visible_faces': visible_faces,
        'plane': plane,
        'all_faces_toward_direction': all_faces_toward_direction,
        'occluded_faces': occluded_faces,
        'hit_count': hit_count
    }




#### Function for Above Rule, it's a second method. It works well with simple geometry but it struggle with more complex one.
def get_faces_toward_direction(shape, direction: gp_Dir, angle_threshold_deg=45.0):
    cos_threshold = math.cos(math.radians(angle_threshold_deg))
    ref = gp_Vec(direction.X(), direction.Y(), direction.Z())

    result = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)

    while explorer.More():
        face = topods.Face(explorer.Current())
        props = BRepGProp_Face(face)

        umin, umax, vmin, vmax = props.Bounds()
        u_mid = (umin + umax) / 2.0
        v_mid = (vmin + vmax) / 2.0

        pnt = gp_Pnt()
        nor = gp_Vec()
        props.Normal(u_mid, v_mid, pnt, nor)

        mag = nor.Magnitude()
        if mag > 1e-10:
            nor.Divide(mag)
            if nor.Dot(ref) > cos_threshold:
                result.append(face)

        explorer.Next()

    # Retourner directement un compound — pas besoin de sewing ni de solid
    return result


def get_box_corners(box: Bnd_Box) -> List[gp_Pnt]:
    """
    Retourne les 8 coins d'une boîte englobante.
    
    Args:
        box: Bnd_Box - la boîte englobante
        
    Returns:
        List[gp_Pnt]: Liste des 8 points des coins
    """
    corners = []
    min_p = box.CornerMin()
    max_p = box.CornerMax()
    for dx in [min_p.X(), max_p.X()]:
        for dy in [min_p.Y(), max_p.Y()]:
            for dz in [min_p.Z(), max_p.Z()]:
                corners.append(gp_Pnt(dx, dy, dz))
    return corners


def rectangles_overlap(rect1, rect2) -> bool:
    """
    Vérifie si deux rectangles axis-aligned se chevauchent.
    
    Args:
        rect1: Tuple (min_x, max_x, min_y, max_y)
        rect2: Tuple (min_x, max_x, min_y, max_y)
        
    Returns:
        bool: True si les rectangles se chevauchent
    """
    return not (rect1[1] < rect2[0] or rect2[1] < rect1[0] or
                rect1[3] < rect2[2] or rect2[3] < rect1[2])


def rectangles_overlap_50percent(rect1, rect2, threshold=0.5) -> bool:
    """
    Vérifie si deux rectangles axis-aligned se chevauchent avec au moins threshold% de recouvrement.
    Le recouvrement est calculé par rapport à la plus petite des deux surfaces.
    
    Args:
        rect1: Tuple (min_x, max_x, min_y, max_y)
        rect2: Tuple (min_x, max_x, min_y, max_y)
        threshold: Seuil de recouvrement (0.0 à 1.0), default 0.5 pour 50%
        
    Returns:
        bool: True si le recouvrement est >= threshold
    """
    # Vérifier d'abord s'il y a chevauchement
    if not rectangles_overlap(rect1, rect2):
        return False
    
    # Calculer l'intersection
    inter_min_x = max(rect1[0], rect2[0])
    inter_max_x = min(rect1[1], rect2[1])
    inter_min_y = max(rect1[2], rect2[2])
    inter_max_y = min(rect1[3], rect2[3])
    
    # Surface d'intersection
    inter_width = inter_max_x - inter_min_x
    inter_height = inter_max_y - inter_min_y
    inter_area = inter_width * inter_height
    
    if inter_area <= 0:
        return False
    
    # Surfaces des rectangles
    rect1_area = (rect1[1] - rect1[0]) * (rect1[3] - rect1[2])
    rect2_area = (rect2[1] - rect2[0]) * (rect2[3] - rect2[2])
    
    # Vérifier que le recouvrement représente au moins threshold de chaque rectangle
    # Utiliser la plus petite surface comme référence
    min_area = min(rect1_area, rect2_area)
    
    if min_area <= 0:
        return False
    
    return (inter_area / min_area) >= threshold


def project_on_plane(points: List[gp_Pnt], axis: gp_Dir, origin: gp_Pnt = None) -> Tuple[List[Tuple[float, float]], gp_Vec, gp_Vec]:
    """
    Projette des points sur le plan perpendiculaire à axis.
    
    Args:
        points: Liste de points à projeter
        axis: Direction de l'axe normal au plan
        origin: Point d'origine pour la projection (default: (0,0,0))
        
    Returns:
        Tuple: (liste de coordonnées 2D (x,y), vecteur base X, vecteur base Y)
    """
    axis_vec = gp_Vec(axis.X(), axis.Y(), axis.Z())
    
    # Trouver un vecteur perpendiculaire à axis
    if abs(axis_vec.X()) < 0.5:
        base_x = gp_Vec(1, 0, 0)
    else:
        base_x = gp_Vec(0, 1, 0)
    
    # Orthogonaliser base_x par rapport à axis
    dot_x_view = base_x.Dot(axis_vec)
    view_squared = axis_vec.Dot(axis_vec)
    if view_squared > 1e-10:
        factor = dot_x_view / view_squared
        axis_scaled = gp_Vec(axis_vec.X() * factor, axis_vec.Y() * factor, axis_vec.Z() * factor)
        base_x.Subtract(axis_scaled)
    
    # Normaliser base_x
    base_x_mag = base_x.Magnitude()
    if base_x_mag > 1e-10:
        base_x.Divide(base_x_mag)
    
    # base_y = axis × base_x
    base_y = axis_vec.Crossed(base_x)
    base_y_mag = base_y.Magnitude()
    if base_y_mag > 1e-10:
        base_y.Divide(base_y_mag)
    
    # Projeter les points
    if origin is None:
        origin = gp_Pnt(0, 0, 0)
    
    coords_2d = []
    for p in points:
        vec = gp_Vec(p.X() - origin.X(), p.Y() - origin.Y(), p.Z() - origin.Z())
        x = vec.Dot(base_x)
        y = vec.Dot(base_y)
        coords_2d.append((x, y))
    
    return coords_2d, base_x, base_y


def is_face_below(face: TopoDS_Face, other_face: TopoDS_Face, axis: gp_Dir, tolerance: float = 1e-6) -> bool:
    """
    Détermine si face est en dessous de other_face selon l'axe donné,
    avec chevauchement des projections sur le plan perpendiculaire.
    
    Une face est considérée comme "en dessous" si (Option C) :
    1. Leurs projections sur le plan perpendiculaire à l'axe se chevauchent 
       avec au moins 50% de recouvrement par rapport à la plus petite surface
    2. Le centre de face est en dessous du centre de other_face selon l'axe
    
    Args:
        face: TopoDS_Face - la face candidate à être en dessous
        other_face: TopoDS_Face - la face de référence
        axis: gp_Dir - l'axe selon lequel vérifier (ex: gp_Dir(0,0,1) pour Z)
        tolerance: Tolérance numérique pour les comparaisons
        
    Returns:
        bool: True si face est en dessous de other_face selon axis avec chevauchement >= 50%
    """
    # Éviter la comparaison avec soi-même
    if face.IsSame(other_face):
        return False
    
    # Calculer les boîtes englobantes
    face_box = Bnd_Box()
    brepbndlib.Add(face, face_box)
    other_box = Bnd_Box()
    brepbndlib.Add(other_face, other_box)
    
    # Obtenir tous les 8 coins
    face_corners = get_box_corners(face_box)
    other_corners = get_box_corners(other_box)
    
    # Calculer les centres pour la comparaison sur l'axe
    face_center = gp_Pnt(
        (face_box.CornerMin().X() + face_box.CornerMax().X()) / 2.0,
        (face_box.CornerMin().Y() + face_box.CornerMax().Y()) / 2.0,
        (face_box.CornerMin().Z() + face_box.CornerMax().Z()) / 2.0
    )
    other_center = gp_Pnt(
        (other_box.CornerMin().X() + other_box.CornerMax().X()) / 2.0,
        (other_box.CornerMin().Y() + other_box.CornerMax().Y()) / 2.0,
        (other_box.CornerMin().Z() + other_box.CornerMax().Z()) / 2.0
    )
    
    # Projeter les centres sur l'axe
    axis_vec = gp_Vec(axis.X(), axis.Y(), axis.Z())
    face_center_proj = gp_Vec(face_center.X(), face_center.Y(), face_center.Z()).Dot(axis_vec)
    other_center_proj = gp_Vec(other_center.X(), other_center.Y(), other_center.Z()).Dot(axis_vec)
    
    # Vérifier la relation "en dessous" : centre de face < centre de other_face sur l'axe
    if face_center_proj >= other_center_proj - tolerance:
        return False
    
    # Projeter sur le plan perpendiculaire à l'axe
    # Utiliser face_center comme origine
    face_2d, base_x, base_y = project_on_plane(face_corners, axis, face_center)
    other_2d, _, _ = project_on_plane(other_corners, axis, face_center)
    
    # Calculer les boîtes englobantes 2D
    face_rect = (
        min(p[0] for p in face_2d),
        max(p[0] for p in face_2d),
        min(p[1] for p in face_2d),
        max(p[1] for p in face_2d)
    )
    other_rect = (
        min(p[0] for p in other_2d),
        max(p[0] for p in other_2d),
        min(p[1] for p in other_2d),
        max(p[1] for p in other_2d)
    )
    
    # Vérifier le chevauchement 2D avec au moins 50% de recouvrement
    return rectangles_overlap_50percent(face_rect, other_rect, threshold=0.9)


def is_face_below_any(face: TopoDS_Face, other_faces: List[TopoDS_Face], axis: gp_Dir, tolerance: float = 1e-6) -> bool:
    """
    Vérifie si face est en dessous de n'importe quelle autre face dans other_faces
    selon l'axe donné, avec chevauchement des projections.
    
    Les faces doivent appartenir au même objet (c'est la responsabilité de l'appelant
    de passer uniquement des faces du même objet).
    
    Args:
        face: TopoDS_Face - la face à tester
        other_faces: List[TopoDS_Face] - liste des autres faces (du même objet)
        axis: gp_Dir - l'axe selon lequel vérifier (peut être n'importe quelle direction)
        tolerance: Tolérance numérique pour les comparaisons
        
    Returns:
        bool: True si face est en dessous d'au moins une face dans other_faces
    """
    for other_face in other_faces:
        if is_face_below(face, other_face, axis, tolerance):
            return True
    return False

