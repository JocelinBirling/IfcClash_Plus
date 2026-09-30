from OCC.Core.Bnd import Bnd_Box, Bnd_OBB
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeEdge
from OCC.Core.gp import gp_Ax3, gp_Pnt, gp_Dir, gp_Trsf, gp_XYZ, gp_Vec
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Shell, TopoDS_Solid, TopoDS_Face
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE

import ifcopenshell.util.shape
import ifcopenshell.geom
import ifcopenshell.ifcopenshell_wrapper as W

from typing import Literal, List
import numpy as np
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakePolygon,BRepBuilderAPI_MakeFace



"""
Those function all create an Bnd_OBB. They have different method. 
The two promissing one, are
create_obb_with_fixed_z => It's very usefull, for sqarred like object.
create_obb_via_pac => It's very fast, but not very precise.

I should test all these function to get the fastest one.
"""

def create_obb_with_fixed_z(shape:TopoDS_Compound) -> "Custom_OBB":
    """
    Made with IA
    Crée une OBB avec l'axe Z fixé a (0,0,1)
    """
    # 1. Créer une bounding box AABB pour obtenir les limites Z
    aabb = Bnd_Box()
    brepbndlib.Add(shape, aabb)
    xmin, ymin, zmin, xmax, ymax, zmax = aabb.Get()

    # 2. Calculer les projections des points sur le plan XY
    # Pour cela, on peut transformer la shape ou analyser ses vertices
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopAbs import TopAbs_VERTEX
    from OCC.Core.BRep import BRep_Tool

    points_xy = []
    explorer = TopExp_Explorer(shape, TopAbs_VERTEX)
    while explorer.More():
        vertex = explorer.Current()
        pnt = BRep_Tool.Pnt(vertex)
        points_xy.append([pnt.X(), pnt.Y()])
        explorer.Next()

    points_xy = np.array(points_xy)

    # 3. Calculer l'OBB 2D optimale dans le plan XY
    # Méthode simple: tester différentes rotations autour de Z
    min_area = float("inf")
    best_angle = 0

    for angle in np.linspace(0, np.pi, 180):
        # Matrice de rotation
        cos_a, sin_a = np.cos(angle), np.sin(angle)
        rot_matrix = np.array([[cos_a, sin_a], [-sin_a, cos_a]])

        # Rotation des points
        rotated = points_xy @ rot_matrix.T

        # Calculer les dimensions de la bounding box alignée sur les axes
        x_range = rotated[:, 0].max() - rotated[:, 0].min()
        y_range = rotated[:, 1].max() - rotated[:, 1].min()
        area = x_range * y_range

        if area < min_area:
            min_area = area
            best_angle = angle
            best_x_range = x_range
            best_y_range = y_range
            best_x_center = (rotated[:, 0].max() + rotated[:, 0].min()) / 2
            best_y_center = (rotated[:, 1].max() + rotated[:, 1].min()) / 2

    # 4. Transformer le centre dans le repère global
    cos_a, sin_a = np.cos(best_angle), np.sin(best_angle)
    center_x = best_x_center * cos_a - best_y_center * sin_a
    center_y = best_x_center * sin_a + best_y_center * cos_a
    center_z = (zmax + zmin) / 2

    # 5. Créer l'OBB avec les bonnes dimensions

    center = gp_Pnt(center_x, center_y, center_z)

    z_dir = gp_Dir(0, 0, 1)
    x_dir = gp_Dir(cos_a, sin_a, 0)
    y_dir = gp_Dir(-sin_a, cos_a, 0)

    obb = Custom_OBB(
        center,
        x_dir,
        y_dir,
        z_dir,
        best_x_range / 2,
        best_y_range / 2,
        (zmax - zmin) / 2,
    )

    # obb.SetCenter(center)
    # obb.SetXComponent(x_dir, best_x_range / 2)
    # obb.SetYComponent(y_dir, best_y_range / 2)
    # obb.SetZComponent(z_dir, (zmax - zmin) / 2)  # Hauteur complète

    return obb


def create_obb_with_free_z(shape:TopoDS_Compound) -> "Custom_OBB":
    """
    Made with IA
    Crée une OBB à partir d'une shape d'IfcOpenShell.

    Args:
        ifc_shape: Une shape d'IfcOpenShell (généralement obtenue via ifcopenshell.geometry)

    Returns:
        Bnd_OBB: Une OBB de OCC représentant la shape
    """
    # Convertir la shape IfcOpenShell en une shape OCC si nécessaire

    # Utiliser la méthode de covariance pour calculer l'OBB
    from OCC.Core.TopExp import TopExp_Explorer
    from OCC.Core.TopAbs import TopAbs_VERTEX
    from OCC.Core.BRep import BRep_Tool

    # Collecter tous les points de la shape
    points = []
    explorer = TopExp_Explorer(shape, TopAbs_VERTEX)
    while explorer.More():
        vertex = explorer.Current()
        pnt = BRep_Tool.Pnt(vertex)
        points.append([pnt.X(), pnt.Y(), pnt.Z()])
        explorer.Next()

    points = np.array(points)

    # Calculer le centroïde
    centroid = np.mean(points, axis=0)

    # Centrer les points
    centered_points = points - centroid

    # Calculer la matrice de covariance
    covariance_matrix = np.cov(centered_points, rowvar=False)

    # Calculer les vecteurs propres et les valeurs propres
    eigenvalues, eigenvectors = np.linalg.eig(covariance_matrix)

    # Trier les vecteurs propres par ordre décroissant des valeurs propres
    sorted_indices = np.argsort(eigenvalues)[::-1]
    eigenvectors = eigenvectors[:, sorted_indices]

    # Créer les directions de l'OBB à partir des vecteurs propres
    x_dir = gp_Dir(eigenvectors[0, 0], eigenvectors[1, 0], eigenvectors[2, 0])
    y_dir = gp_Dir(eigenvectors[0, 1], eigenvectors[1, 1], eigenvectors[2, 1])
    z_dir = gp_Dir(eigenvectors[0, 2], eigenvectors[1, 2], eigenvectors[2, 2])

    # Projeter les points sur les axes principaux pour obtenir les dimensions
    x_projections = np.dot(centered_points, eigenvectors[:, 0])
    y_projections = np.dot(centered_points, eigenvectors[:, 1])
    z_projections = np.dot(centered_points, eigenvectors[:, 2])

    x_h = (np.max(x_projections) - np.min(x_projections)) / 2
    y_h = (np.max(y_projections) - np.min(y_projections)) / 2
    z_h = (np.max(z_projections) - np.min(z_projections)) / 2

    # Créer l'OBB
    center = gp_Pnt(centroid[0], centroid[1], centroid[2])
    obb = Custom_OBB(center, x_dir, y_dir, z_dir, x_h, y_h, z_h)

    return obb


def create_obb_from_geom_verts(geom:W.Triangulation) -> "Custom_OBB":
    """
    Crée une OBB à partir des sommets d'une géométrie IfcOpenShell.

    Args:
        geom: Une géométrie IfcOpenShell (généralement obtenue via ifcopenshell.geom.create_shape)

    Returns:
        Custom_OBB: Une OBB représentant la géométrie
    """
    # Extraire les points de la géométrie IfcOpenShell

    points = ifcopenshell.util.shape.get_vertices(geom)

    # Calculer le centroïde
    centroid = np.mean(points, axis=0)

    # Centrer les points
    centered_points = points - centroid

    # Calculer la matrice de covariance
    covariance_matrix = np.cov(centered_points, rowvar=False)

    # Calculer les vecteurs propres et les valeurs propres
    eigenvalues, eigenvectors = np.linalg.eig(covariance_matrix)

    # Trier les vecteurs propres par ordre décroissant des valeurs propres
    sorted_indices = np.argsort(eigenvalues)[::-1]
    eigenvectors = eigenvectors[:, sorted_indices]

    # Créer les directions de l'OBB à partir des vecteurs propres
    x_dir = gp_Dir(eigenvectors[0, 0], eigenvectors[1, 0], eigenvectors[2, 0])
    y_dir = gp_Dir(eigenvectors[0, 1], eigenvectors[1, 1], eigenvectors[2, 1])
    z_dir = gp_Dir(eigenvectors[0, 2], eigenvectors[1, 2], eigenvectors[2, 2])

    # Projeter les points sur les axes principaux pour obtenir les dimensions
    x_projections = np.dot(centered_points, eigenvectors[:, 0])
    y_projections = np.dot(centered_points, eigenvectors[:, 1])
    z_projections = np.dot(centered_points, eigenvectors[:, 2])

    x_h = (np.max(x_projections) - np.min(x_projections)) / 2
    y_h = (np.max(y_projections) - np.min(y_projections)) / 2
    z_h = (np.max(z_projections) - np.min(z_projections)) / 2

    # Créer l'OBB
    center = gp_Pnt(centroid[0], centroid[1], centroid[2])
    obb = Custom_OBB(center, x_dir, y_dir, z_dir, x_h, y_h, z_h)

    return obb

def create_aabb_from_list_of_faces(list_of_faces,vertices) -> "Custom_OBB":
    """

    """
    from OCC.Core.TColgp import TColgp_Array1OfPnt

    theobb = Bnd_OBB()
    list_of_points=[]
    #@todo clean this
    
    for source_face in list_of_faces:
        s0 = vertices[source_face[0]]
        s1 = vertices[source_face[1]]
        s2 = vertices[source_face[2]]

        g0=gp_Pnt(s0[0],s0[1],s0[2])
        g1=gp_Pnt(s1[0],s1[1],s1[2])
        g2=gp_Pnt(s2[0],s2[1],s2[2])

        list_of_points.append(g0)
        list_of_points.append(g1)
        list_of_points.append(g2)
        theobb.Add(g0)
        theobb.Add(g1)
        theobb.Add(g2)
        print(s0)
        break
        
    return theobb
    """
    tcolgp=TColgp_Array1OfPnt(1,len(list_of_points))
    for i, point in enumerate(list_of_points, start=1):
        tcolgp.SetValue(i, point)

    theobb=Custom_OBB.ReBuild(tcolgp)
    """




def create_obb_from_TopoDs_Shape(shape:TopoDS_Compound) -> "Custom_OBB":
    """
    Calcule l'OBB (Oriented Bounding Box) d'une forme TopoDS_Shape.

    Args:
        shape: Un objet TopoDS_Shape.

    Returns:
        Bnd_OBB: L'OBB calculé pour la forme.
    """

    mesh = BRepMesh_IncrementalMesh(shape, 0.1, False, 0.5)
    mesh.Perform()

    # Calculer directement l'OBB à partir de la forme avec une tolérance précise
    obb = Bnd_OBB()
    brepbndlib.AddOBB(
        shape, obb, True, True, True
    )  # Utiliser les flags pour inclure les sous-formes

    center = gp_Pnt(obb.Center())
    x_dir = gp_Dir(obb.XDirection())
    y_dir = gp_Dir(obb.YDirection())
    z_dir = gp_Dir(obb.ZDirection())
    x_h=obb.XHSize()
    y_h=obb.YHSize()
    z_h=obb.ZHSize()
    
    thecustomobb = Custom_OBB(center, x_dir, y_dir, z_dir, x_h, y_h, z_h)
    return thecustomobb


def create_obb_from_TopoDs_Shape_via_pca(shape:TopoDS_Compound) -> "Custom_OBB":
    """
    This is not an optimal solution for the obb. It's not the smallest OBB.
    It can give weird optimised solution. IF the objects is flat, and cubic like, it may be better to use create_obb_with_fixed_z.
    """
    # 1. Tessellation
    mesh = BRepMesh_IncrementalMesh(shape, 0.01, False, 0.1)
    mesh.Perform()

    # 2. Collecter tous les sommets
    points = []
    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    while explorer.More():
        face = explorer.Current()
        location = face.Location()
        triangulation = BRep_Tool.Triangulation(face, location)

        if triangulation is not None:
            trsf = location.IsIdentity()
            for i in range(1, triangulation.NbNodes() + 1):
                node = triangulation.Node(i)
                if not trsf:
                    node = node.Transformed(location.Transformation())
                points.append([node.X(), node.Y(), node.Z()])

        explorer.Next()

    if len(points) < 3:
        raise ValueError("Pas assez de points pour calculer une OBB.")

    pts = np.array(points)

    # 3. PCA
    centroid = pts.mean(axis=0)
    centered = pts - centroid
    cov = np.cov(centered.T)
    eigenvalues, eigenvectors = np.linalg.eigh(cov)

    order = np.argsort(eigenvalues)[::-1]
    axes = eigenvectors[:, order]

    # 4. Projection et calcul des demi-tailles
    projected = centered @ axes
    min_proj = projected.min(axis=0)
    max_proj = projected.max(axis=0)

    half_sizes = (max_proj - min_proj) / 2.0
    local_center = centroid + axes @ ((min_proj + max_proj) / 2.0)

    # 5. Construction de l'OBB
    obb = Custom_OBB()
    obb.SetCenter(gp_Pnt(*local_center))
    obb.SetXComponent(gp_Dir(*axes[:, 0]), half_sizes[0])
    obb.SetYComponent(gp_Dir(*axes[:, 1]), half_sizes[1])
    obb.SetZComponent(gp_Dir(*axes[:, 2]), half_sizes[2])

    return obb


def create_obb_from_verts_withOCC(geom:W.Triangulation) -> "Custom_OBB":
    """
    Crée une Bnd_OBB à partir d'une liste de sommets (X, Y, Z) en utilisant la fonction ReBuild.

    Args:
        geom

    Returns:
        Custom_OBB: Une OBB représentant les sommets
    """
    from OCC.Core.TColgp import TColgp_Array1OfPnt
    from OCC.Core.TColStd import TColStd_Array1OfReal

    verts = ifcopenshell.util.shape.get_vertices(geom)

    # Créer un tableau de points
    points_array = TColgp_Array1OfPnt(1, len(verts))

    # Remplir le tableau avec les sommets
    for i, vert in enumerate(verts, 1):
        points_array.SetValue(i, gp_Pnt(vert[0], vert[1], vert[2]))

    # Créer une OBB vide
    obb = Custom_OBB()

    # Utiliser ReBuild pour créer l'OBB à partir des points
    obb.ReBuild(points_array)

    return obb


def create_obb_from_faces(faces: List[TopoDS_Face]) -> "Custom_OBB":
    """
    Crée une OBB (Oriented Bounding Box) à partir d'une liste de faces TopoDS_Face.
    
    Cette fonction utilise l'analyse en composantes principales (PCA) pour calculer
    l'OBB optimale qui englobe toutes les faces fournies.
    
    Args:
        faces: Liste de TopoDS_Face à englober
    
    Returns:
        Custom_OBB: Une OBB représentant la boîte englobante orientée
    """
    # Collecter tous les sommets de toutes les faces
    points = []
    
    for face in faces:
        # Utiliser l'explorateur de sommets pour cette face
        from OCC.Core.TopExp import TopExp_Explorer
        from OCC.Core.TopAbs import TopAbs_VERTEX
        
        vertex_explorer = TopExp_Explorer(face, TopAbs_VERTEX)
        while vertex_explorer.More():
            vertex = vertex_explorer.Current()
            pnt = BRep_Tool.Pnt(vertex)
            points.append([pnt.X(), pnt.Y(), pnt.Z()])
            vertex_explorer.Next()
    
    if len(points) < 3:
        # Si pas assez de points, essayer d'utiliser la triangulation
        for face in faces:
            location = face.Location()
            triangulation = BRep_Tool.Triangulation(face, location)
            
            if triangulation is not None:
                trsf = location.Transformation()
                has_transformation = not location.IsIdentity()
                
                for i in range(1, triangulation.NbNodes() + 1):
                    node = triangulation.Node(i)
                    if has_transformation:
                        node = node.Transformed(trsf)
                    points.append([node.X(), node.Y(), node.Z()])
    
    if len(points) < 3:
        raise ValueError(f"Pas assez de points pour calculer une OBB. Seulement {len(points)} points trouvés.")
    
    pts = np.array(points)
    
    # Calculer le centroïde
    centroid = pts.mean(axis=0)
    
    # Centrer les points
    centered = pts - centroid
    
    # Calculer la matrice de covariance
    cov = np.cov(centered.T)
    
    # Calculer les vecteurs propres et les valeurs propres
    eigenvalues, eigenvectors = np.linalg.eigh(cov)
    
    # Trier par ordre décroissant des valeurs propres
    order = np.argsort(eigenvalues)[::-1]
    axes = eigenvectors[:, order]
    
    # Projection et calcul des demi-tailles
    projected = centered @ axes
    min_proj = projected.min(axis=0)
    max_proj = projected.max(axis=0)
    
    half_sizes = (max_proj - min_proj) / 2.0
    local_center = centroid + axes @ ((min_proj + max_proj) / 2.0)
    
    # Construction de l'OBB
    obb = Custom_OBB()
    obb.SetCenter(gp_Pnt(*local_center))
    obb.SetXComponent(gp_Dir(*axes[:, 0]), half_sizes[0])
    obb.SetYComponent(gp_Dir(*axes[:, 1]), half_sizes[1])
    obb.SetZComponent(gp_Dir(*axes[:, 2]), half_sizes[2])
    
    return obb


class Custom_OBB(Bnd_OBB):
    # Made with IA
    def __init__(
        self,
        center=None,
        x_dir=None,
        y_dir=None,
        z_dir=None,
        x_h=None,
        y_h=None,
        z_h=None,
    ):
        if center is not None:
            super().__init__(center, x_dir, y_dir, z_dir, x_h, y_h, z_h)
        else:
            super().__init__()

    def min_distance_to_obb(self, other_obb: Bnd_OBB) -> float:
        """
        Calculate the minimal distance between two Bnd_OBB objects using Separating Axis Theorem.
        Works for OBBs with arbitrary orientations.

        Args:
            other_obb: Another Bnd_OBB to calculate distance to

        Returns:
            float: The minimal distance between the two OBBs (0 if overlapping)
        """
        # Get the axes of both OBBs
        self_axes = [
            gp_Vec(self.XDirection()),
            gp_Vec(self.YDirection()),
            gp_Vec(self.ZDirection()),
        ]

        other_axes = [
            gp_Vec(other_obb.XDirection()),
            gp_Vec(other_obb.YDirection()),
            gp_Vec(other_obb.ZDirection()),
        ]

        # Vector between centers
        center1 = self.Center()
        center2 = other_obb.Center()
        center_vector = gp_Vec(
            center2.X() - center1.X(),
            center2.Y() - center1.Y(),
            center2.Z() - center1.Z(),
        )

        # Test all 15 potential separating axes (3 from each OBB + 9 cross products)
        min_distance = float("inf")
        has_overlap = False

        # Test axes from first OBB
        for axis in self_axes:
            distance = self._test_separating_axis(axis, other_obb, center_vector)
            if distance > 0:  # This is a separating axis
                if distance < min_distance:
                    min_distance = distance
            else:
                has_overlap = True  # Overlap on this axis

        # Test axes from second OBB
        for axis in other_axes:
            distance = self._test_separating_axis(axis, other_obb, center_vector)
            if distance > 0:  # This is a separating axis
                if distance < min_distance:
                    min_distance = distance
            else:
                has_overlap = True  # Overlap on this axis

        # Test cross products of axes
        for axis1 in self_axes:
            for axis2 in other_axes:
                cross_axis = axis1.Crossed(axis2)
                if cross_axis.Magnitude() > 1e-6:  # Avoid near-zero vectors
                    cross_axis.Normalize()
                    distance = self._test_separating_axis(
                        cross_axis, other_obb, center_vector
                    )
                    if distance > 0:  # This is a separating axis
                        if distance < min_distance:
                            min_distance = distance
                    else:
                        has_overlap = True  # Overlap on this axis

        # If we found overlap on all axes, the OBBs overlap
        if has_overlap and min_distance == float("inf"):
            return 0.0

        return max(0.0, min_distance)

    def _test_separating_axis(
        self, axis: gp_Vec, other_obb: Bnd_OBB, center_vector: gp_Vec
    ) -> float:
        """
        Test a single separating axis and return the minimal distance.
        """
        # Project both OBBs onto the axis
        self_proj = self._project_onto_axis(axis)
        other_proj = other_obb._project_onto_axis(axis)

        # Calculate overlap
        if self_proj[1] < other_proj[0]:
            # Self is to the "left" of other
            return other_proj[0] - self_proj[1]
        elif other_proj[1] < self_proj[0]:
            # Self is to the "right" of other
            return self_proj[0] - other_proj[1]
        else:
            # Overlapping on this axis
            return -float("inf")  # Indicates overlap

    def _project_onto_axis(self, axis: gp_Vec) -> tuple:
        """
        Project this OBB onto the given axis and return (min, max) projections.
        """
        center = self.Center()

        # Project center onto axis
        center_proj = (
            center.X() * axis.X() + center.Y() * axis.Y() + center.Z() * axis.Z()
        )

        # Project each half-extent onto the axis
        x_proj = self.XHSize() * abs(axis.Dot(gp_Vec(self.XDirection())))
        y_proj = self.YHSize() * abs(axis.Dot(gp_Vec(self.YDirection())))
        z_proj = self.ZHSize() * abs(axis.Dot(gp_Vec(self.ZDirection())))

        # Total projection extent
        total_proj = x_proj + y_proj + z_proj

        return (center_proj - total_proj, center_proj + total_proj)

    def get_min_corner(self) -> float:
        center = self.Center()
        x_comp = self.XDirection().Multiplied(self.XHSize())
        y_comp = self.YDirection().Multiplied(self.YHSize())
        Z_comp = self.ZDirection().Multiplied(self.ZHSize())

        mincorner = center - (x_comp + y_comp + Z_comp)
        return mincorner

    def get_max_corner(self) -> float:
        center = self.Center()
        x_comp = self.XDirection().Multiplied(self.XHSize())
        y_comp = self.YDirection().Multiplied(self.YHSize())
        Z_comp = self.ZDirection().Multiplied(self.ZHSize())
        mincorner = center + (x_comp + y_comp + Z_comp)
        return mincorner

    def expand_sides(self, change):
        center = self.Center()
        theHXSize = self.XHSize()
        theHYSize = self.YHSize()
        theHZSize = self.ZHSize()
        new_theHXSize = theHXSize
        new_theHYSize = theHYSize

        if type(change) is str:
            change = change.replace("%", "")
            change = float(change)
            change = change / 100
            new_theHXSize = theHXSize + (theHXSize * change) / 2
            new_theHYSize = theHYSize + (theHYSize * change) / 2

        else:
            new_theHXSize = theHZSize + change / 2
            new_theHYSize = theHZSize + change / 2

        self.SetXComponent(gp_Dir(self.XDirection()), new_theHXSize)
        self.SetYComponent(gp_Dir(self.YDirection()), new_theHYSize)

    def detach_top_by_extrude(self, change) -> "Custom_OBB":
        # Direction mondiale vers le haut
        world_dir = gp_Dir(0, 0, 1)

        current_center = self.Center()
        x_dir = gp_Dir(self.XDirection())
        y_dir = gp_Dir(self.YDirection())
        z_dir = gp_Dir(self.ZDirection())

        axes = [
            (x_dir, self.XHSize()),
            (y_dir, self.YHSize()),
            (z_dir, self.ZHSize()),
        ]

        # Identifier l'axe local le plus aligné avec Z mondial (up)
        # On garde le signe pour orienter vers le haut
        best_dot = None
        up_axis_idx = None
        for i, (ax, _) in enumerate(axes):
            dot = world_dir.Dot(ax)
            if best_dot is None or abs(dot) > abs(best_dot):
                best_dot = dot
                up_axis_idx = i

        up_dir, up_hsize = axes[up_axis_idx]

        up_dir, up_hsize = axes[up_axis_idx]

        if type(change) is str and "%" in change:
            ratio = float(change.replace("%", "")) / 100
            change = ratio * up_hsize*2

        # Si l'axe local pointe vers le bas, on l'inverse pour pointer vers le haut
        if best_dot < 0:
            up_dir = up_dir.Reversed()

        # Les deux axes horizontaux restants
        horiz_axes = [axes[i] for i in range(3) if i != up_axis_idx]

        # Sommet de l'OBB actuel dans la direction up locale
        # highest_point = center + up_dir * up_hsize
        top_center = gp_Pnt(
            current_center.X() + up_dir.X() * up_hsize + up_dir.X() * (change / 2),
            current_center.Y() + up_dir.Y() * up_hsize + up_dir.Y() * (change / 2),
            current_center.Z() + up_dir.Z() * up_hsize + up_dir.Z() * (change / 2),
        )

        # Les half-sizes horizontaux restent identiques
        h_dir_0, h_hsize_0 = horiz_axes[0]
        h_dir_1, h_hsize_1 = horiz_axes[1]

        # Reconstruire les 3 axes dans le bon ordre (X, Y, Z de Custom_OBB)
        # On réaffecte en respectant l'ordre original des axes
        new_axes = [None, None, None]
        new_hsizes = [None, None, None]

        new_axes[up_axis_idx] = up_dir
        new_hsizes[up_axis_idx] = change / 2

        horiz_indices = [i for i in range(3) if i != up_axis_idx]
        new_axes[horiz_indices[0]] = h_dir_0
        new_hsizes[horiz_indices[0]] = h_hsize_0
        new_axes[horiz_indices[1]] = h_dir_1
        new_hsizes[horiz_indices[1]] = h_hsize_1

        top_OBB = Custom_OBB(
            top_center,
            new_axes[0], new_axes[1], new_axes[2],
            new_hsizes[0], new_hsizes[1], new_hsizes[2],
        )

        return top_OBB

    def detach_bottom_by_extrude(self, change) -> "Custom_OBB":
        # Direction mondiale vers le haut
        world_dir = gp_Dir(0, 0, -1)

        current_center = self.Center()
        x_dir = gp_Dir(self.XDirection())
        y_dir = gp_Dir(self.YDirection())
        z_dir = gp_Dir(self.ZDirection())

        axes = [
            (x_dir, self.XHSize()),
            (y_dir, self.YHSize()),
            (z_dir, self.ZHSize()),
        ]

        # Identifier l'axe local le plus aligné avec Z mondial (up)
        # On garde le signe pour orienter vers le haut
        best_dot = None
        up_axis_idx = None
        for i, (ax, _) in enumerate(axes):
            dot = world_dir.Dot(ax)
            if best_dot is None or abs(dot) > abs(best_dot):
                best_dot = dot
                up_axis_idx = i

        up_dir, up_hsize = axes[up_axis_idx]

        up_dir, up_hsize = axes[up_axis_idx]

        if type(change) is str and "%" in change:
            ratio = float(change.replace("%", "")) / 100
            change = ratio * up_hsize*2

        # Si l'axe local pointe vers le bas, on l'inverse pour pointer vers le haut
        if best_dot < 0:
            up_dir = up_dir.Reversed()

        # Les deux axes horizontaux restants
        horiz_axes = [axes[i] for i in range(3) if i != up_axis_idx]

        # Sommet de l'OBB actuel dans la direction up locale
        # highest_point = center + up_dir * up_hsize
        top_center = gp_Pnt(
            current_center.X() + up_dir.X() * up_hsize + up_dir.X() * (change / 2),
            current_center.Y() + up_dir.Y() * up_hsize + up_dir.Y() * (change / 2),
            current_center.Z() + up_dir.Z() * up_hsize + up_dir.Z() * (change / 2),
        )

        # Les half-sizes horizontaux restent identiques
        h_dir_0, h_hsize_0 = horiz_axes[0]
        h_dir_1, h_hsize_1 = horiz_axes[1]

        # Reconstruire les 3 axes dans le bon ordre (X, Y, Z de Custom_OBB)
        # On réaffecte en respectant l'ordre original des axes
        new_axes = [None, None, None]
        new_hsizes = [None, None, None]

        new_axes[up_axis_idx] = up_dir
        new_hsizes[up_axis_idx] = change / 2

        horiz_indices = [i for i in range(3) if i != up_axis_idx]
        new_axes[horiz_indices[0]] = h_dir_0
        new_hsizes[horiz_indices[0]] = h_hsize_0
        new_axes[horiz_indices[1]] = h_dir_1
        new_hsizes[horiz_indices[1]] = h_hsize_1

        top_OBB = Custom_OBB(
            top_center,
            new_axes[0], new_axes[1], new_axes[2],
            new_hsizes[0], new_hsizes[1], new_hsizes[2],
        )

        return top_OBB

    def extend_up(self, change: float) -> "Custom_OBB":
        """
        Étend l'OBB vers le haut dans la direction mondiale (0, 0, 1).
        Fonctionne même si l'objet est incliné.

        Args:
            distance: La distance d'extension vers le haut

        Returns:
            Custom_OBB: Une nouvelle OBB étendue vers le haut
        """

        center = self.Center()
        x_dir = gp_Dir(self.XDirection())
        y_dir = gp_Dir(self.YDirection())
        z_dir = gp_Dir(self.ZDirection())
        x_h = self.XHSize()
        y_h = self.YHSize()
        z_h = self.ZHSize()

        # Direction mondiale vers le haut (0, 0, 1)
        world_up = gp_Dir(0, 0, 1)
        x_proj = abs(world_up.Dot(x_dir))
        y_proj = abs(world_up.Dot(y_dir))
        z_proj = abs(world_up.Dot(z_dir))
        hauteur = x_proj * x_h * 2 + y_proj * y_h * 2 + z_proj * z_h * 2
        if type(change) is str:
            change = change.replace("%", "")
            change = float(change)
            change = change / 100
            change = hauteur * change

        # Déplacer le centre de distance/2 dans la direction mondiale vers le haut
        new_center = gp_Pnt(
            center.X() + world_up.X() * change / 2,
            center.Y() + world_up.Y() * change / 2,
            center.Z() + world_up.Z() * change / 2,
        )

        # Projeter la direction mondiale sur chaque axe LOCAL de l'OBB
        # pour savoir combien chaque demi-taille doit croître
        x_proj = abs(world_up.Dot(x_dir))
        y_proj = abs(world_up.Dot(y_dir))
        z_proj = abs(world_up.Dot(z_dir))

        new_x_h = x_h + x_proj * change / 2
        new_y_h = y_h + y_proj * change / 2
        new_z_h = z_h + z_proj * change / 2

        return Custom_OBB(new_center, x_dir, y_dir, z_dir, new_x_h, new_y_h, new_z_h)

    def extend_down(self, change: float) -> "Custom_OBB":
        """
        Étend l'OBB vers le bas dans la direction mondiale (0, 0, -1).
        Fonctionne même si l'objet est incliné.

        Args:
            distance: La distance d'extension vers le bas

        Returns:
            Custom_OBB: Une nouvelle OBB étendue vers le bas
        """
        # Récupérer les propriétés de l'OBB actuelle
        center = self.Center()
        x_dir = gp_Dir(self.XDirection())
        y_dir = gp_Dir(self.YDirection())
        z_dir = gp_Dir(self.ZDirection())
        x_h = self.XHSize()
        y_h = self.YHSize()
        z_h = self.ZHSize()

        # Direction mondiale vers le bas (0, 0, -1)
        world_down = gp_Dir(0, 0, -1)

        x_proj = abs(world_down.Dot(x_dir))
        y_proj = abs(world_down.Dot(y_dir))
        z_proj = abs(world_down.Dot(z_dir))
        hauteur = x_proj * x_h * 2 + y_proj * y_h * 2 + z_proj * z_h * 2
        if type(change) is str:
            change = change.replace("%", "")
            change = float(change)
            change = change / 100
            change = hauteur * change

        # Déplacer le centre de distance/2 dans la direction mondiale vers le bas
        new_center = gp_Pnt(
            center.X() + world_down.X() * change / 2,
            center.Y() + world_down.Y() * change / 2,
            center.Z() + world_down.Z() * change / 2,
        )

        # Projeter la direction mondiale sur chaque axe LOCAL de l'OBB
        # pour savoir combien chaque demi-taille doit croître
        x_proj = abs(world_down.Dot(x_dir))
        y_proj = abs(world_down.Dot(y_dir))
        z_proj = abs(world_down.Dot(z_dir))

        new_x_h = x_h + x_proj * change / 2
        new_y_h = y_h + y_proj * change / 2
        new_z_h = z_h + z_proj * change / 2

        return Custom_OBB(new_center, x_dir, y_dir, z_dir, new_x_h, new_y_h, new_z_h)

    def extend_obb_in_direction(
        self, direction: gp_Dir, distance: float
    ) -> "Custom_OBB":
        """
        Crée une nouvelle OBB qui s'étend à partir de l'OBB actuelle dans une direction donnée.
        Args:
            direction: La direction dans laquelle étendre l'OBB (gp_Dir)
            distance: La distance d'extension
        Returns:
            Custom_OBB: Une nouvelle OBB étendue dans la direction spécifiée
        """
        # Récupérer les propriétés de l'OBB actuelle
        center = self.Center()
        x_dir = gp_Dir(self.XDirection())
        y_dir = gp_Dir(self.YDirection())
        z_dir = gp_Dir(self.ZDirection())
        x_h = self.XHSize()
        y_h = self.YHSize()
        z_h = self.ZHSize()

        # Déplacer le centre de distance/2 dans la direction donnée (repère monde)
        new_center = gp_Pnt(
            center.X() + direction.X() * distance / 2,
            center.Y() + direction.Y() * distance / 2,
            center.Z() + direction.Z() * distance / 2,
        )

        # Projeter la direction sur chaque axe LOCAL de l'OBB
        # pour savoir combien chaque demi-taille doit croître
        x_proj = abs(direction.Dot(x_dir))
        y_proj = abs(direction.Dot(y_dir))
        z_proj = abs(direction.Dot(z_dir))

        new_x_h = x_h + x_proj * distance / 2
        new_y_h = y_h + y_proj * distance / 2
        new_z_h = z_h + z_proj * distance / 2

        return Custom_OBB(new_center, x_dir, y_dir, z_dir, new_x_h, new_y_h, new_z_h)

    def detach_side_by_extrude(
        self, direction: gp_Dir, distance: float
    ) -> "Custom_OBB":
        """
        Crée une nouvelle OBB détachée dans une direction donnée, adjacente à l'OBB actuelle.
        La nouvelle OBB est positionnée de manière à juste toucher l'OBB actuelle sans chevauchement.

        Args:
            direction: La direction dans laquelle créer la nouvelle OBB (gp_Dir)
            distance: La taille de la nouvelle OBB dans la direction donnée

        Returns:
            Custom_OBB: Une nouvelle OBB détachée dans la direction spécifiée, adjacente à l'OBB actuelle
        """
        # Récupérer les propriétés de l'OBB actuelle
        center = self.Center()
        x_dir = gp_Dir(self.XDirection())
        y_dir = gp_Dir(self.YDirection())
        z_dir = gp_Dir(self.ZDirection())
        x_h = self.XHSize()
        y_h = self.YHSize()
        z_h = self.ZHSize()

        # Calculer la projection de la direction sur chaque axe LOCAL de l'OBB
        # Cela nous permet de déterminer combien chaque demi-taille contribue
        # à la distance dans la direction donnée
        x_proj = abs(direction.Dot(x_dir))
        y_proj = abs(direction.Dot(y_dir))
        z_proj = abs(direction.Dot(z_dir))

        # Calculer la distance totale de l'OBB actuelle dans la direction donnée
        # C'est la somme des projections pondérées par les demi-tailles
        obb_size_in_direction = x_h * x_proj + y_h * y_proj + z_h * z_proj

        # Calculer la position du centre de la nouvelle OBB
        # On place le centre à une distance égale à la moitié de la taille de l'OBB actuelle
        # plus la moitié de la taille de la nouvelle OBB dans la direction donnée
        # Cela fait en sorte que les deux OBB se touchent sans se chevaucher
        new_center = gp_Pnt(
            center.X() + direction.X() * (obb_size_in_direction + distance / 2),
            center.Y() + direction.Y() * (obb_size_in_direction + distance / 2),
            center.Z() + direction.Z() * (obb_size_in_direction + distance / 2),
        )

        # Calculer les dimensions de la nouvelle OBB
        # La nouvelle OBB a la même taille que l'OBB actuelle dans les directions perpendiculaires
        # et une taille spécifiée par 'distance' dans la direction donnée
        new_x_h = x_h
        new_y_h = y_h
        new_z_h = z_h

        # Si la direction est principalement alignée avec un axe, on peut ajuster la taille
        # dans cette direction pour correspondre à la distance spécifiée
        if x_proj > y_proj and x_proj > z_proj:
            new_x_h = distance / 2
        elif y_proj > x_proj and y_proj > z_proj:
            new_y_h = distance / 2
        else:
            new_z_h = distance / 2

        return Custom_OBB(new_center, x_dir, y_dir, z_dir, new_x_h, new_y_h, new_z_h)

    def get_corners(self) -> list[gp_XYZ]:
        pt1 = self.Center() + gp_XYZ(self.XHSize(), self.YHSize(), self.ZHSize())
        pt2 = self.Center() + gp_XYZ(self.XHSize(), -self.YHSize(), self.ZHSize())
        pt3 = self.Center() + gp_XYZ(self.XHSize(), self.YHSize(), -self.ZHSize())
        pt4 = self.Center() + gp_XYZ(self.XHSize(), -self.YHSize(), -self.ZHSize())
        pt5 = self.Center() + gp_XYZ(-self.XHSize(), self.YHSize(), self.ZHSize())
        pt6 = self.Center() + gp_XYZ(-self.XHSize(), -self.YHSize(), self.ZHSize())
        pt7 = self.Center() + gp_XYZ(-self.XHSize(), self.YHSize(), -self.ZHSize())
        pt8 = self.Center() + gp_XYZ(-self.XHSize(), -self.YHSize(), -self.ZHSize())
        return [pt1, pt2, pt3, pt4, pt5, pt6, pt7, pt8]

    def get_corners_of_dir(self, dir: gp_Dir) -> list[gp_XYZ]:
        """
        Returns the 4 corners of the OBB that are in the direction of the given direction.

        Args:
            dir: The direction to check against.

        Returns:
            list[gp_XYZ]: A list of 4 points that are in the direction of the given direction.
        """
        # Get all 8 corners of the OBB
        all_corners = self.get_corners()

        # Filter corners that are in the direction of the given direction
        corners_in_dir = []
        center = self.Center()

        for corner in all_corners:
            # Vector from center to corner
            corner_vec = gp_Vec(
                corner.X() - center.X(),
                corner.Y() - center.Y(),
                corner.Z() - center.Z(),
            )

            # Check if the corner is in the direction of the given direction
            # We use the dot product to determine if the angle between the vectors is acute
            if corner_vec.Dot(gp_Vec(dir)) > 0:
                corners_in_dir.append(corner)

        # Return the 4 corners that are in the direction
        return corners_in_dir

    def get_two_main_direction_OBB_shape(
        self, wide_or_narrow: Literal["wide", "narrow"]
    ) -> tuple[gp_Dir, gp_Dir]:
        """
        Détermine les deux directions des faces larges (ou étroites) de l'OBB.

        Args:
            OBB: Une instance de Custom_OBB.
            wide_or_narrow: Chaîne de caractères indiquant si l'on veut les faces larges ('wide') ou étroites ('narrow').

        Returns:
            tuple: Un tuple contenant les directions des faces avant et arrière.
        """
        # Récupérer les dimensions de l'OBB
        x_size = self.XHSize() * 2
        y_size = self.YHSize() * 2
        z_size = self.ZHSize() * 2

        # Identifier les deux faces les plus larges ou étroites
        # On compare les dimensions pour déterminer les faces larges ou étroites
        dimensions = {"X": x_size, "Y": y_size, "Z": z_size}

        # Trouver les deux dimensions les plus grandes ou les plus petites
        sorted_dimensions = sorted(
            dimensions.items(),
            key=lambda item: item[1],
            reverse=(wide_or_narrow == "narrow"),
        )

        # Les deux faces les plus larges ou étroites sont les deux premières dimensions
        first_dimension = sorted_dimensions[0][0]

        # Déterminer les directions des faces avant et arrière
        if first_dimension == "X":
            main_direction_1 = gp_Dir(self.XDirection())
            main_direction_2 = gp_Dir(self.XDirection().Reversed())
        elif first_dimension == "Y":
            main_direction_1 = gp_Dir(self.YDirection())
            main_direction_2 = gp_Dir(self.YDirection().Reversed())
        else:  # 'Z'
            main_direction_1 = gp_Dir(self.ZDirection())
            main_direction_2 = gp_Dir(self.ZDirection().Reversed())

        return main_direction_1, main_direction_2

    def to_TopoDS_Compound(self) -> TopoDS_Compound:
        """
        Convertit une Bnd_OBB en TopoDS_Compound contenant les 12 arêtes
        du wireframe de la boîte orientée.

        Args:
            obb: La boîte orientée à convertir.

        Returns:
            Un TopoDS_Compound contenant les arêtes du wireframe.
        """
        # Récupérer centre et axes
        center = self.Center()
        c = np.array([center.X(), center.Y(), center.Z()])

        ax = self.XDirection()
        ay = self.YDirection()
        az = self.ZDirection()

        x = np.array([ax.X(), ax.Y(), ax.Z()]) * self.XHSize()
        y = np.array([ay.X(), ay.Y(), ay.Z()]) * self.YHSize()
        z = np.array([az.X(), az.Y(), az.Z()]) * self.ZHSize()

        # 8 sommets du cube orienté
        #
        #     6 ---- 7
        #    /|     /|
        #   4 ---- 5 |
        #   | 2 ---| 3
        #   |/     |/
        #   0 ---- 1
        #
        signs = [
            (-1, -1, -1),  # 0
            (+1, -1, -1),  # 1
            (-1, +1, -1),  # 2
            (+1, +1, -1),  # 3
            (-1, -1, +1),  # 4
            (+1, -1, +1),  # 5
            (-1, +1, +1),  # 6
            (+1, +1, +1),  # 7
        ]

        corners = []
        for sx, sy, sz in signs:
            pt = c + sx * x + sy * y + sz * z
            corners.append(gp_Pnt(float(pt[0]), float(pt[1]), float(pt[2])))

        # 12 arêtes du cube (paires d'indices)
        edges_indices = [
            # Face basse (z-)
            (0, 1),
            (1, 3),
            (3, 2),
            (2, 0),
            # Face haute (z+)
            (4, 5),
            (5, 7),
            (7, 6),
            (6, 4),
            # Montants verticaux
            (0, 4),
            (1, 5),
            (2, 6),
            (3, 7),
        ]

        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)

        for i, j in edges_indices:
            edge = BRepBuilderAPI_MakeEdge(corners[i], corners[j]).Edge()
            builder.Add(compound, edge)

        return compound

    def to_TopoDS_Compound_V2(self):
        """
        Convertit un Bnd_OBB en TopoDS_Compound en calculant ses 8 coins.

        Args:
            obb (Bnd_OBB): Une boîte englobante orientée.

        Returns:
            TopoDS_Compound: Un compound contenant la géométrie de la boîte.
        """
        # Récupérer le centre et les axes de l'OBB
        center = self.Center()
        x_axis = self.XHSize()  # Demi-longueur en X
        y_axis = self.YHSize()  # Demi-longueur en Y
        z_axis = self.ZHSize()  # Demi-longueur en Z

        # Récupérer les directions des axes
        x_dir = self.XDirection()
        y_dir = self.YDirection()
        z_dir = self.ZDirection()

        # Calculer les 8 coins en combinant ±x, ±y, ±z
        corners = []
        for dx in [-1, 1]:
            for dy in [-1, 1]:
                for dz in [-1, 1]:
                    corner = gp_Pnt(
                        center.X() + dx * x_axis * x_dir.X() + dy * y_axis * y_dir.X() + dz * z_axis * z_dir.X(),
                        center.Y() + dx * x_axis * x_dir.Y() + dy * y_axis * y_dir.Y() + dz * z_axis * z_dir.Y(),
                        center.Z() + dx * x_axis * x_dir.Z() + dy * y_axis * y_dir.Z() + dz * z_axis * z_dir.Z()
                    )
                    corners.append(corner)

        # Créer les 6 faces de la boîte
        faces = [
            # Face avant (z min)
            BRepBuilderAPI_MakeFace(
                BRepBuilderAPI_MakePolygon(corners[0], corners[1], corners[2], corners[3], True).Wire()
            ).Face(),
            # Face arrière (z max)
            BRepBuilderAPI_MakeFace(
                BRepBuilderAPI_MakePolygon(corners[4], corners[5], corners[6], corners[7], True).Wire()
            ).Face(),
            # Face gauche (x min)
            BRepBuilderAPI_MakeFace(
                BRepBuilderAPI_MakePolygon(corners[0], corners[3], corners[7], corners[4], True).Wire()
            ).Face(),
            # Face droite (x max)
            BRepBuilderAPI_MakeFace(
                BRepBuilderAPI_MakePolygon(corners[1], corners[2], corners[6], corners[5], True).Wire()
            ).Face(),
            # Face inférieure (y min)
            BRepBuilderAPI_MakeFace(
                BRepBuilderAPI_MakePolygon(corners[0], corners[1], corners[5], corners[4], True).Wire()
            ).Face(),
            # Face supérieure (y max)
            BRepBuilderAPI_MakeFace(
                BRepBuilderAPI_MakePolygon(corners[3], corners[2], corners[6], corners[7], True).Wire()
            ).Face(),
        ]

        # Créer un TopoDS_Compound
        builder = BRep_Builder()
        compound = TopoDS_Compound()
        builder.MakeCompound(compound)

        # Ajouter toutes les faces au compound
        for face in faces:
            builder.Add(compound, face)

        return compound

    def to_TopoDS_Solid(self) -> TopoDS_Solid:
        """
        Convertit un Bnd_OBB en TopoDS_Solid (boîte pleine).
        
        Créer un solide valide avec une orientation cohérente des faces (vers l'extérieur).
        
        Returns:
            TopoDS_Solid: Un solide représentant la boîte orientée.
        """
        # Récupérer le centre et les axes de l'OBB
        center = self.Center()
        x_axis = self.XHSize()  # Demi-longueur en X
        y_axis = self.YHSize()  # Demi-longueur en Y
        z_axis = self.ZHSize()  # Demi-longueur en Z

        # Récupérer les directions des axes
        x_dir = self.XDirection()
        y_dir = self.YDirection()
        z_dir = self.ZDirection()

        # Calculer les 8 coins en combinant ±x, ±y, ±z
        corners = []
        for dx in [-1, 1]:
            for dy in [-1, 1]:
                for dz in [-1, 1]:
                    corner = gp_Pnt(
                        center.X() + dx * x_axis * x_dir.X() + dy * y_axis * y_dir.X() + dz * z_axis * z_dir.X(),
                        center.Y() + dx * x_axis * x_dir.Y() + dy * y_axis * y_dir.Y() + dz * z_axis * z_dir.Y(),
                        center.Z() + dx * x_axis * x_dir.Z() + dy * y_axis * y_dir.Z() + dz * z_axis * z_dir.Z()
                    )
                    corners.append(corner)

        # Créer les 6 faces avec orientation cohérente (anti-horaire vu de l'extérieur)
        # Ordre des coins :
        # 0: (-1,-1,-1), 1: (+1,-1,-1), 2: (-1,+1,-1), 3: (+1,+1,-1)  => Face basse (z-)
        # 4: (-1,-1,+1), 5: (+1,-1,+1), 6: (-1,+1,+1), 7: (+1,+1,+1)  => Face haute (z+)
        faces = [
            # Face basse (z min) - vue de dessous, sens anti-horaire
            BRepBuilderAPI_MakeFace(
                BRepBuilderAPI_MakePolygon(corners[0], corners[1], corners[3], corners[2], True).Wire()
            ).Face(),
            # Face haute (z max) - vue de dessus, sens anti-horaire
            BRepBuilderAPI_MakeFace(
                BRepBuilderAPI_MakePolygon(corners[5], corners[7], corners[6], corners[4], True).Wire()
            ).Face(),
            # Face gauche (x min) - vue de gauche, sens anti-horaire
            BRepBuilderAPI_MakeFace(
                BRepBuilderAPI_MakePolygon(corners[0], corners[4], corners[6], corners[2], True).Wire()
            ).Face(),
            # Face droite (x max) - vue de droite, sens anti-horaire
            BRepBuilderAPI_MakeFace(
                BRepBuilderAPI_MakePolygon(corners[1], corners[3], corners[7], corners[5], True).Wire()
            ).Face(),
            # Face avant (y min) - vue de devant, sens anti-horaire
            BRepBuilderAPI_MakeFace(
                BRepBuilderAPI_MakePolygon(corners[0], corners[1], corners[5], corners[4], True).Wire()
            ).Face(),
            # Face arrière (y max) - vue de derrière, sens anti-horaire
            BRepBuilderAPI_MakeFace(
                BRepBuilderAPI_MakePolygon(corners[2], corners[6], corners[7], corners[3], True).Wire()
            ).Face(),
        ]

        # Créer une coque (shell) à partir des faces
        shell_builder = BRep_Builder()
        shell = TopoDS_Shell()
        shell_builder.MakeShell(shell)
        for face in faces:
            shell_builder.Add(shell, face)

        # Créer un solide à partir de la coque
        solid_builder = BRep_Builder()
        solid = TopoDS_Solid()
        solid_builder.MakeSolid(solid)
        solid_builder.Add(solid, shell)

        return solid
    
if __name__ == "__main__":
    import ifcopenshell

    center = gp_Pnt(0, 0, 0)
    x_dir = gp_Dir(1, 0, 0)
    y_dir = gp_Dir(0, 1, 0)
    z_dir = gp_Dir(0, 0, 1)
    x_h = 5
    y_h = 5
    z_h = 5
    import math

    genuineobb = Bnd_OBB(center, x_dir, y_dir, z_dir, x_h, y_h, z_h)

    the_OBB = Custom_OBB(center, x_dir, y_dir, z_dir, x_h, y_h, z_h)
    print(the_OBB.DumpJson())

    new_OBB = the_OBB.detach_top_by_extrude(1.0)
    print(new_OBB.DumpJson())

    file = ifcopenshell.open("Ifc_Model/Ifc2x3_Duplex_Architecture_with_suzanne.ifc")
    doors = file.by_type("IFCDOOR")
    settings = ifcopenshell.geom.settings()
    settings.set(settings.USE_WORLD_COORDS, True)

    shape = ifcopenshell.geom.create_shape(settings, doors[0])

