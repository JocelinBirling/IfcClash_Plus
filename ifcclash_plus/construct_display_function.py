import ifcopenshell
import ifcopenshell.util.element as attt
import ifcopenshell.geom
import multiprocessing
from OCC.Core.Bnd import Bnd_OBB, Bnd_Box
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.gp import gp_Dir, gp_XYZ, gp_Ax3, gp_Trsf, gp_Pnt, gp_Vec, gp_Ax1
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Display.SimpleGui import init_display
from OCC.Core.AIS import AIS_Shape
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform, BRepBuilderAPI_MakePolygon
import OCC.Core.BRepPrimAPI as br
import CustomOBB
import numpy as np
import ifcopenshell.util.placement
from CustomOBB import Custom_OBB,create_obb_from_geom_verts
import math
import numpy as np
from OCC.Core.Bnd import Bnd_OBB
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.gp import gp_Pnt, gp_Dir, gp_XYZ
from OCC.Core.BRepBndLib import brepbndlib

from typing import Literal
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh

import numpy as np
from OCC.Core.BRep import BRep_Builder
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakeEdge,
    BRepBuilderAPI_MakeWire,
)
from OCC.Core.gp import gp_Pnt
from OCC.Core.TopoDS import TopoDS_Compound
from CustomOBB import create_obb_from_TopoDs_Shape,create_obb_from_TopoDs_Shape_via_pca,create_obb_with_fixed_z,create_obb_with_free_z,create_obb_from_verts_withOCC



def get_obb_vertices(obb: Bnd_OBB) -> np.ndarray:
    """
    Retourne les 8 sommets de l'OBB dans le repère monde.
    Utile pour visualisation ou debug.
    """
    c = obb.Center()
    cx, cy, cz = c.X(), c.Y(), c.Z()

    ax = obb.XDirection()
    ay = obb.YDirection()
    az = obb.ZDirection()

    x = np.array([ax.X(), ax.Y(), ax.Z()]) * obb.XHSize()
    y = np.array([ay.X(), ay.Y(), ay.Z()]) * obb.YHSize()
    z = np.array([az.X(), az.Y(), az.Z()]) * obb.ZHSize()
    center = np.array([cx, cy, cz])

    vertices = []
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            for sz in [-1, 1]:
                vertices.append(center + sx * x + sy * y + sz * z)

    return np.array(vertices)



def create_makepolygon_with_dir(dir: tuple, loc: tuple):
    """
    Crée un demi U en 3D, afin de pouvoir afficher la direction au sein d'un display 3D.

    Args:
        dir: Tuple représentant la direction (vecteur).
        loc: Tuple représentant la position de départ.

    Returns:
        Shape: Une forme de U est crée qui est ouverte vers la direction de l'objet
    """
    vertices = []
    polygon = BRepBuilderAPI_MakePolygon()

    listofvertice = []
    listofvertice.append((0, 0, 0))
    listofvertice.append(dir)
    listofvertice.append((dir[0] + 0.01, dir[1] + 0.01, dir[2] + 0.01))
    listofvertice.append((0.01, 0.01, 0.01))

    listofvertice.append((0, 0, 0.5))
    listofvertice.append((dir[0], dir[1], dir[2] + 0.5))
    listofvertice.append((dir[0] + 0.01, dir[1] + 0.01, dir[2] + 0.51))
    listofvertice.append((0.01, 0.01, 0.51))

    for element in listofvertice:
        x = float(element[0]) + loc[0]
        y = float(element[1]) + loc[1]
        z = float(element[2]) + loc[2]

        pt_XYZ = gp_XYZ(x, y, z)
        polygon.Add(gp_Pnt(pt_XYZ))

    polygon.Close()
    polygon.Wire()

    return polygon.Shape()


def get_front_direction_from_placement(
    placement, angle_offset=0, use_y_axis=False
) -> gp_Dir:
    """
    Détermine la direction du devant d'un objet IFC en fonction de son IfcAxis2Placement3D.

    Args:
        placement: L'objet IfcPlacement de l'objet IFC.
        angle_offset: Angle en degrés pour ajuster manuellement la direction (par défaut 0).
        use_y_axis: Si True, utilise l'axe Y au lieu de l'axe X pour la direction (par défaut False).

    Returns:
        tuple: Un tuple représentant la direction du devant de l'objet.
    """
    matrice = ifcopenshell.util.placement.get_local_placement(placement)
    axe_x = matrice[:, 0][:3]  # Vecteur X (orientation locale)
    axe_y = matrice[:, 1][:3]  # Vecteur Y (orientation locale)
    axe_z = matrice[:, 2][:3]  # Vecteur Z (orientation locale)

    # La direction du devant est généralement l'axe X local, mais peut être ajustée
    if use_y_axis:
        front_direction = gp_Dir(axe_y[0].item(), axe_y[1].item(), axe_y[2].item())
    else:
        front_direction = gp_Dir(axe_x[0].item(), axe_x[1].item(), axe_x[2].item())

    # Appliquer une rotation si un angle est spécifié
    if angle_offset != 0:
        angle_rad = math.radians(angle_offset)
        front_direction.Rotate(angle_rad)

    return front_direction


def display_front_direction(file_path, angle_offset=0):
    """
    Visualise la direction du devant d'un ou plusieurs objets IFC dans un display.

    Args:
        file_path: Chemin vers le fichier IFC.
        object_indices: Liste d'indices des objets à visualiser (par défaut None pour tous les objets).
        angle_offset: Angle en degrés pour ajuster manuellement la direction (par défaut 0).
    """
    file = ifcopenshell.open(file_path)
    objects = file.by_type("IFCDOOR")

    if not objects:
        print("Aucun objet IFCFURNISHINGELEMENT trouvé.")
        return

    settings = ifcopenshell.geom.settings()
    settings.set("use-python-opencascade", True)

    iterator = ifcopenshell.geom.iterator(
        settings,
        file,
        multiprocessing.cpu_count(),
        include=objects,
    )

    display, start_display, add_menu, add_function = init_display()

    if iterator.initialize():
        while True:
            shape = iterator.get()
            geom = shape.geometry


            from CustomOBB import create_obb_with_free_z

            #ais_shape = AIS_Shape(geom)
            ais_shape=create_obb_with_free_z(geom)
            ais_shape.SetTransparency(0.5)
            display.Context.Display(ais_shape, True)

            if not iterator.next():
                break

    # Afficher les flèches de direction pour les objets spécifiés
    for objet in objects:
        placement = objet.ObjectPlacement
        front_direction = get_front_direction_from_placement(
            placement, angle_offset, True
        )

        # Obtenir la matrice de placement pour extraire le centre
        matrice = ifcopenshell.util.placement.get_local_placement(placement)
        position = matrice[:3, 3]  # Position (centre) de l'objet
        coordinate = (position[0].item(), position[1].item(), position[2].item())

        # Créer une flèche pour visualiser la direction du devant
        front_direction=(front_direction.X(),front_direction.Y(),front_direction.Z())
        u_shape = create_makepolygon_with_dir(front_direction, coordinate)
        u_shape_AIS = AIS_Shape(u_shape)
        u_shape_AIS.SetColor(
            Quantity_Color(1.0, 0.0, 0.0, Quantity_TOC_RGB)
        )  # Rouge pour la direction du devant
        display.Context.Display(u_shape_AIS, True)

    display.FitAll()
    start_display()


def display_front_and_back_direction(file_path, angle_offset=0):
    """
    Visualise la direction du devant d'un ou plusieurs objets IFC dans un display.

    Args:
        file_path: Chemin vers le fichier IFC.
        object_indices: Liste d'indices des objets à visualiser (par défaut None pour tous les objets).
        angle_offset: Angle en degrés pour ajuster manuellement la direction (par défaut 0).
    """
    file = ifcopenshell.open(file_path)
    objects = file.by_type("IFCDOOR")

    if not objects:
        print("Aucun objet IFCFURNISHINGELEMENT trouvé.")
        return

    settings = ifcopenshell.geom.settings()
    settings.set("use-python-opencascade", True)

    iterator = ifcopenshell.geom.iterator(
        settings,
        file,
        multiprocessing.cpu_count(),
        include=objects,
    )

    display, start_display, add_menu, add_function = init_display()

    if iterator.initialize():
        while True:
            shape = iterator.get()
            geom = shape.geometry

            ais_shape = AIS_Shape(geom)
            ais_shape.SetTransparency(0.5)
            display.Context.Display(ais_shape, True)

            swig_elem = shape.data.product
            swig_elem_ifc_id = swig_elem.id_
            elem = file.by_id(swig_elem_ifc_id)
            OBB = CustomOBB.create_obb_with_free_z(shape)

            mains_direction_tuple = get_two_main_direction_OBB_shape(OBB, "wide")
            new_OBB = get_new_OBB_from_dir(OBB, mains_direction_tuple[0], 1.0)

            for one_direction in mains_direction_tuple:
                placement = elem.ObjectPlacement
                matrice = ifcopenshell.util.placement.get_local_placement(placement)
                position = matrice[:3, 3]  # Position (centre) de l'objet
                coordinate = (
                    position[0].item(),
                    position[1].item(),
                    position[2].item(),
                )

                # Créer une flèche pour visualiser la direction du devant
                direction_tuple = (
                    one_direction.X(),
                    one_direction.Y(),
                    one_direction.Z(),
                )
                u_shape = create_makepolygon_with_dir(direction_tuple, coordinate)
                u_shape_AIS = AIS_Shape(u_shape)
                u_shape_AIS.SetColor(
                    Quantity_Color(1.0, 0.0, 0.0, Quantity_TOC_RGB)
                )  # Rouge pour la direction du devant
                display.Context.Display(u_shape_AIS, True)

            if not iterator.next():
                break

    display.FitAll()
    start_display()

def display_OBB(file_path, angle_offset=0):
    """
    Visualise la direction du devant d'un ou plusieurs objets IFC dans un display.

    Args:
        file_path: Chemin vers le fichier IFC.
        object_indices: Liste d'indices des objets à visualiser (par défaut None pour tous les objets).
        angle_offset: Angle en degrés pour ajuster manuellement la direction (par défaut 0).
    """
    file = ifcopenshell.open(file_path)
    objects = file.by_type("IfcSlab")

    settings = ifcopenshell.geom.settings()
    settings.set("use-python-opencascade", True)

    iterator = ifcopenshell.geom.iterator(
        settings,
        file,
        multiprocessing.cpu_count(),
        include=objects,
    )

    display, start_display, add_menu, add_function = init_display()

    if iterator.initialize():
        while True:
            shape = iterator.get()
            geom = shape.geometry

            obb = create_obb_from_TopoDs_Shape(geom)
            custom_OBB=Custom_OBB(gp_Pnt(obb.Center()),gp_Dir(obb.XDirection()),gp_Dir(obb.YDirection()),gp_Dir(obb.ZDirection()),obb.XHSize(),obb.YHSize(),obb.ZHSize())
            #custom_OBB=create_obb_from_geom_verts(geom)
            custom_OBB=custom_OBB.detach_bottom_by_extrude(0.81)
            
            
            topo_DS_obb=custom_OBB.to_TopoDS_Compound()
            OBB_Shape = AIS_Shape(topo_DS_obb)
            OBB_Shape.SetTransparency(0.2)
            display.Context.Display(OBB_Shape, True)

            object = AIS_Shape(geom)
            display.Context.Display(object, True)

            if not iterator.next():
                break


    #Add another object
    objects = file.by_type("IfcFurnishingElement")
    iterator = ifcopenshell.geom.iterator(
        settings,
        file,
        multiprocessing.cpu_count(),
        include=objects,
    )
    if iterator.initialize():
        while True:
            shape = iterator.get()
            geom = shape.geometry
            object = AIS_Shape(geom)
            display.Context.Display(object, True)
            if not iterator.next():
                break
    
    
    display.FitAll()
    start_display()

def display_OBB_front_back(file_path, angle_offset=0):
    """
    Visualise la direction du devant d'un ou plusieurs objets IFC dans un display.

    Args:
        file_path: Chemin vers le fichier IFC.
        object_indices: Liste d'indices des objets à visualiser (par défaut None pour tous les objets).
        angle_offset: Angle en degrés pour ajuster manuellement la direction (par défaut 0).
    """
    file = ifcopenshell.open(file_path)
    objects = file.by_type("IFCDOOR")

    settings = ifcopenshell.geom.settings()
    settings.set("USE_WORLD_COORDS", True)
    #settings.set("use-python-opencascade", True)

    iterator = ifcopenshell.geom.iterator(
        settings,
        file,
        multiprocessing.cpu_count(),
        include=objects,
    )

    display, start_display, add_menu, add_function = init_display()

    if iterator.initialize():
        while True:
            shape = iterator.get()
            geom = shape.geometry

            obb = create_obb_from_verts_withOCC(geom)
            obb.Enlarge(0.1)
            custom_OBB=Custom_OBB(gp_Pnt(obb.Center()),gp_Dir(obb.XDirection()),gp_Dir(obb.YDirection()),gp_Dir(obb.ZDirection()),obb.XHSize(),obb.YHSize(),obb.ZHSize())


  
            main_tuple_dir=custom_OBB.get_two_main_direction_OBB_shape("wide")
            main1=custom_OBB.detach_side_by_extrude(main_tuple_dir[0],1.0)
            main2=custom_OBB.detach_side_by_extrude(main_tuple_dir[1],1.0)
            
            main1_V2=main1.extend_up(0.5)    



            
            topo_DS_obb=custom_OBB.to_TopoDS_Compound()
            OBB_Shape = AIS_Shape(topo_DS_obb)
            OBB_Shape.SetTransparency(0.2)
            display.Context.Display(OBB_Shape, True)






            if not iterator.next():
                break


    settings = ifcopenshell.geom.settings()
    settings.set("use-python-opencascade", True)
    for objet in objects:
        shape = ifcopenshell.geom.create_shape(settings, objet)

        ais_object = AIS_Shape(shape.geometry)
        display.Context.Display(ais_object, True)


    display.FitAll()
    start_display()




if __name__ == "__main__":
    chemin = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    display_OBB(chemin)
