"""
Module pour tester la détection d'occlusion et la position relative de faces 3D avec PythonOCC.

Fonctions principales :
- get_faces_toward_direction : obtient les faces orientées vers une direction
- is_face_occluded : vérifie si une face est masquée (version rapide avec boîtes englobantes)
- is_face_occluded_precise : vérifie si une face est masquée (version précise avec projection 2D)
- is_face_below : vérifie si une face est en dessous d'une autre selon un axe donné (avec 50% de recouvrement minimum)
- is_face_below_any : vérifie si une face est en dessous de n'importe quelle autre face d'une liste

Fonctions helpers :
- get_box_corners : retourne les 8 coins d'une boîte englobante
- project_on_axis : projette des points sur un axe
- project_on_plane : projette des points sur un plan perpendiculaire à un axe
- rectangles_overlap : vérifie si deux rectangles 2D se chevauchent
- rectangles_overlap_50percent : vérifie si deux rectangles 2D se chevauchent avec au moins 50% de recouvrement
"""

import numpy as np
import numpy.typing as npt
import math
from math import radians, cos
from typing import Optional, Literal, Union, Dict, List, Tuple

import ifcopenshell
import ifcopenshell.geom
import ifcopenshell.ifcopenshell_wrapper as W
import ifcopenshell.util.element
import ifcopenshell.util.placement
import ifcopenshell.util.representation
from ifcopenshell.util.shape_builder import VectorType
from ifcopenshell.geom import ShapeElementType, ShapeType

import multiprocessing
import trimesh
import shapely
import shapely.ops

# Imports OCC
from OCC.Core.BRep import BRep_Builder, BRep_Tool
from OCC.Core.BRepBuilderAPI import (
    BRepBuilderAPI_MakePolygon, 
    BRepBuilderAPI_MakeFace, 
    BRepBuilderAPI_Sewing,
    BRepBuilderAPI_MakeSolid,
    BRepBuilderAPI_MakeWire,
    BRepBuilderAPI_MakeEdge
)
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape
from OCC.Core.BRepGProp import BRepGProp_Face
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.BRepCheck import BRepCheck_Analyzer
from OCC.Core.gp import gp_Pnt, gp_XYZ, gp_Ax3, gp_Dir, gp_Trsf, gp_Vec
from OCC.Core.Bnd import Bnd_Box
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Face, TopoDS_Shell, topods
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_FACE, TopAbs_SHELL
from OCC.Core.AIS import AIS_Shape
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Display.SimpleGui import init_display
import clash_utils








def add_to_display(display,geom):
    ais_shape=AIS_Shape(geom)
    ais_shape.SetTransparency(0.2)
    display.Context.Display(ais_shape, True)
    return display

def add_to_display_green(display,geom):
    ais_shape=AIS_Shape(geom)
    green_color = Quantity_Color(0.0, 1.0, 0.0, Quantity_TOC_RGB)
    ais_shape.SetColor(green_color)
    ais_shape.SetTransparency(0.2)
    display.Context.Display(ais_shape, True)
    return display

def add_to_display_red(display,geom):
    """Affiche une géométrie en rouge pour les faces masquées"""
    ais_shape=AIS_Shape(geom)
    red_color = Quantity_Color(1.0, 0.0, 0.0, Quantity_TOC_RGB)
    ais_shape.SetColor(red_color)
    ais_shape.SetTransparency(0.5)
    display.Context.Display(ais_shape, True)
    return display

def add_to_display_yellow(display,geom):
    """Affiche une géométrie en rouge pour les faces masquées"""
    ais_shape=AIS_Shape(geom)
    red_color = Quantity_Color(1.0, 1.0, 0.0, Quantity_TOC_RGB)
    ais_shape.SetColor(red_color)
    ais_shape.SetTransparency(0.9)
    display.Context.Display(ais_shape, True)
    return display


if __name__ == "__main__":
    Chemin="/home/jocelin/Documents/05 - Programmation/IfcClash_Plus/Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    file=ifcopenshell.open(Chemin)

    objects=file.by_type("IfcDistributionControlElement")
    #objects=file.by_type("IfcFurnishingElement")
    the_settings=ifcopenshell.geom.settings()
    the_settings.set("use-python-opencascade", True)
    iterator = ifcopenshell.geom.iterator(
                the_settings,
                file,
                multiprocessing.cpu_count(),
                include=objects,
            )


    display, start_display, add_menu, add_function = init_display()
    
    # Liste pour stocker toutes les faces visibles (orientées vers la direction)
    
    direction_to_check=gp_Dir(0.0, 0.0, 1.0)
    
    if iterator.initialize():
        # Première passe : collecter toutes les faces visibles
        while True:
            shape = iterator.get()
            geom = shape.geometry
            entity = file.by_id(shape.data.id)

            display = add_to_display_yellow(display, geom)

            List_of_faces = clash_utils.get_faces_toward_direction(geom,direction_to_check)


            for oneface in List_of_faces:
                # Utiliser la nouvelle fonction pour détecter les faces en dessous
                # selon l'axe Z (direction_to_check = (0,0,1))
                if clash_utils.is_face_below_any(oneface, List_of_faces, direction_to_check):
                    display = add_to_display_red(display, oneface)
                else:
                    display = add_to_display_green(display, oneface)



            if not iterator.next():
                break

    display.FitAll()
    start_display()