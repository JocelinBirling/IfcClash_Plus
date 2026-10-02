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


from constructtest_pythonOCC import add_to_display_yellow,add_to_display_green,add_to_display_red

import clash_utils



if __name__ == "__main__":
    Chemin="/home/jocelin/Documents/05 - Programmation/IfcClash_Plus/Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    file=ifcopenshell.open(Chemin)

    #objects=file.by_type("IfcWallStandardCase")
    objects=file.by_type("IfcFurnishingElement")
    objects=file.by_type("IfcDistributionControlElement")
    objects=file.by_type("IfcWindow")
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

            result = clash_utils.get_faces_visible_from_direction_with_plane(shape=geom,direction=direction_to_check,n_ray_samples=10)
            List_of_faces = result['visible_faces']

            print(entity)
            print(len(entity))


            for oneface in List_of_faces:
                display = add_to_display_green(display, oneface)




            if not iterator.next():
                break

    display.FitAll()
    start_display()