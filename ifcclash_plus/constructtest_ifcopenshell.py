import ifcopenshell
import ifcopenshell.util.element as attt
import ifcopenshell.geom
import multiprocessing
from OCC.Core.Bnd import Bnd_OBB
from OCC.Core.BRepBndLib import brepbndlib
from OCC.Core.gp import gp_Dir,gp_XYZ,gp_Ax3,gp_Trsf,gp_Pnt,gp_Vec,gp_Ax1
from OCC.Core.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCC.Display.SimpleGui import init_display
from OCC.Core.AIS import AIS_Shape
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_Transform,BRepBuilderAPI_MakePolygon
import OCC.Core.BRepPrimAPI as br
import CustomOBB
import numpy as np
import ifcopenshell.util.placement



def get_front_direction_from_placement(placement, angle_offset=0, use_y_axis=False):
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
        front_direction = (axe_y[0].item(), axe_y[1].item(), axe_y[2].item())
    else:
        front_direction = (axe_x[0].item(), axe_x[1].item(), axe_x[2].item())
    
    # Appliquer une rotation si un angle est spécifié
    if angle_offset != 0:
        import math
        angle_rad = math.radians(angle_offset)
        # Rotation autour de l'axe Z
        new_x = front_direction[0] * math.cos(angle_rad) - front_direction[1] * math.sin(angle_rad)
        new_y = front_direction[0] * math.sin(angle_rad) + front_direction[1] * math.cos(angle_rad)
        front_direction = (new_x, new_y, front_direction[2])
    
    return front_direction


def display_front_direction(file_path,  angle_offset=0):
    """
    Visualise la direction du devant d'un ou plusieurs objets IFC dans un display.
    
    Args:
        file_path: Chemin vers le fichier IFC.
        object_indices: Liste d'indices des objets à visualiser (par défaut None pour tous les objets).
        angle_offset: Angle en degrés pour ajuster manuellement la direction (par défaut 0).
    """
    file = ifcopenshell.open(file_path)
    objects = file.by_type("IFCFURNISHINGELEMENT")
    
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
            
            if not iterator.next():
                break
    
    # Afficher les flèches de direction pour les objets spécifiés
    for objet in objects:
        placement = objet.ObjectPlacement
        front_direction = get_front_direction_from_placement(placement, angle_offset,True)

        
        

        # Obtenir la matrice de placement pour extraire le centre
        matrice = ifcopenshell.util.placement.get_local_placement(placement)
        position = matrice[:3, 3]  # Position (centre) de l'objet
        coordinate = (position[0].item(), position[1].item(), position[2].item())
        
        # Créer une flèche pour visualiser la direction du devant
        front_arrow = MakeBox_with_direction(front_direction, coordinate)
        front_arrow_AIS = AIS_Shape(front_arrow)
        front_arrow_AIS.SetColor(Quantity_Color(1.0, 0.0, 0.0, Quantity_TOC_RGB))  # Rouge pour la direction du devant
        display.Context.Display(front_arrow_AIS, True)
    
    display.FitAll()
    start_display()


def OBB_To_Shape(obb:Bnd_OBB):
    TheBox=BRepPrimAPI_MakeBox(obb.XHSize()*2,obb.YHSize()*2,obb.ZHSize()*2).Shape()

    center=gp_Pnt(obb.Center())
  

    
    trans=gp_Trsf()

    trans.SetTranslation(gp_Vec(center.X()-obb.XHSize(),center.Y()-obb.XHSize(),center.Z()-obb.ZHSize()))
    gp_ax1=gp_Ax1(gp_Pnt(obb.Center()),gp_Dir(obb.ZDirection()))
    #trans.SetRotation(gp_ax1,0.0)



    TheBox=BRepBuilderAPI_Transform(TheBox,trans).Shape()


    return TheBox

def MakeBox(obb:Bnd_OBB):
    center=obb.Center()
    x_dir=obb.XDirection()
    y_dir=obb.YDirection()
    z_dir=obb.ZDirection()

    x_half=obb.XHSize()
    y_half=obb.YHSize()
    z_half=obb.ZHSize()

    vertices=[]
    polygon=BRepBuilderAPI_MakePolygon()


    for dx in [-1,1]:
        for dy in [-1,1]:
            for dz in [-1,1]:
                vertice=center+x_dir*x_half*dx+y_dir*y_half*dy+z_dir*z_half*dz
                print(dx,dy,dz,vertice.DumpJson())
                polygon.Add(gp_Pnt(vertice))
                vertices.append(gp_Pnt(vertice))
    

    polygon.Close()
    polygon.Wire()

    return polygon.Shape()

def MakeBox_with_direction(dir,loc):

    vertices=[]
    polygon=BRepBuilderAPI_MakePolygon()

    listofvertice=[]
    listofvertice.append((0,0,0))
    listofvertice.append(dir)
    listofvertice.append(dir+(0.01,0.01,0.01))
    listofvertice.append((0.01,0.01,0.01))

    listofvertice.append((0,0,1))
    listofvertice.append(dir+(0,0,1))
    listofvertice.append(dir+(0.01,0.01,1.01))
    listofvertice.append((0.01,0.01,1.01))


    for element in listofvertice:
        x=float(element[0])+loc[0]
        y=float(element[1])+loc[1]
        z=float(element[2])+loc[2]

        pt_XYZ=gp_XYZ(x,y,z)
        polygon.Add(gp_Pnt(pt_XYZ))

    

    polygon.Close()
    polygon.Wire()

    return polygon.Shape()


def display_box():

    chemin="Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    file=ifcopenshell.open(chemin)

    spaces=file.by_type("IFCDISTRIBUTIONCONTROLELEMENT")
    #spaces=file.by_type("IFCSPACE")
    #spaces=file.by_type("IFCWALL")
    space=spaces[0]

    settings=ifcopenshell.geom.settings()
    settings.set("use-python-opencascade", True)
    #shape=ifcopenshell.geom.create_shape(settings,space.Representation)


    iterator = ifcopenshell.geom.iterator(
        settings,
        file,
        multiprocessing.cpu_count(),
        include=spaces,
    )

    display,start_display,add_menu,add_funtion=init_display()

    if iterator.initialize():
        while True:
            shape = iterator.get()
            geom = shape.geometry

            obb_temp = Bnd_OBB()
            brepbndlib.AddOBB(geom,obb_temp,True,True,True)

            Suzanne_AIS=AIS_Shape(geom)
            Suzanne_AIS.SetTransparency(0.5)

            display.Context.Display(Suzanne_AIS,True)

            
            # Récupérer le centre
            center = obb_temp.Center()

            # Créer une nouvelle OBB avec Z fixé
            obb = Bnd_OBB()
            z_dir = gp_Dir(0, 0, 1)
            x_dir = gp_Dir(1, 0, 0)

            half_size_x=obb_temp.XHSize()
            half_size_y=obb_temp.YHSize()
            half_size_z=obb_temp.ZHSize()

            

            # Projeter les dimensions sur le plan XY
            obb.SetCenter(gp_Pnt(center))
            obb.SetXComponent(x_dir, half_size_x)
            obb.SetYComponent(gp_Dir(0, 1, 0), half_size_y)
            obb.SetZComponent(z_dir, half_size_z)

            #
            obb_shape=CustomOBB.create_obb_with_fixed_z(geom)
            obb_shape=MakeBox(obb_shape)
            obb_AIS=AIS_Shape(obb_shape)
            obb_AIS.SetTransparency(0.5)
            display.Context.Display(obb_AIS,True)


            if not iterator.next():
                break

    display.FitAll()
    start_display()

def display_direction():
    chemin="Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    file=ifcopenshell.open(chemin)

    objects=file.by_type("IFCDISTRIBUTIONCONTROLELEMENT")
    #objects=file.by_type("IFCSPACE")
    #objects=file.by_type("IFCWALL")
    objects=file.by_type("IFCFURNISHINGELEMENT")
    #objects=file.by_type("IFCDOOR")
    objet=objects[35]
    #objet=objects


    placement=objet.ObjectPlacement


    matrice = ifcopenshell.util.placement.get_local_placement(placement)
    axe_x = matrice[:, 0][:3]  # Vecteur X (orientation locale)
    axe_y = matrice[:, 1][:3]  # Vecteur Y (orientation locale)
    axe_z = matrice[:, 2][:3]  # Vecteur Z (orientation locale)
    position = tuple(matrice[:3, 3])
    position=(position[0].item(),position[1].item(),position[2].item())  # [X, Y, Z]

    direction=(axe_x[0].item(),axe_x[1].item(),axe_x[2].item())  # 

    print(matrice)

    
    coordinate=objet.ObjectPlacement.RelativePlacement.Location.Coordinates

    direction_z=(0.0,0.0,1.0)
    u = np.array(direction)
    v = np.array(direction_z)
    w = np.cross(u, v)



    #@todo la direction semble orhtogonal au devant des objets. Il faut clairement creer une fonction pour visualiser le devant des objets, afin de vérifier si cette assumption est la bonne. 


    settings=ifcopenshell.geom.settings()
    settings.set("use-python-opencascade", True)
    #shape=ifcopenshell.geom.create_shape(settings,space.Representation)


    iterator = ifcopenshell.geom.iterator(
        settings,
        file,
        multiprocessing.cpu_count(),
        include=[objet],
    )


    display,start_display,add_menu,add_funtion=init_display()

    if iterator.initialize():
        while True:
            shape = iterator.get()
            geom = shape.geometry

            Suzanne_AIS=AIS_Shape(geom)
            Suzanne_AIS.SetTransparency(0.5)

            display.Context.Display(Suzanne_AIS,True)

        

            #
            obb_shape=MakeBox_with_direction(w,coordinate)
            obb_AIS=AIS_Shape(obb_shape)
            obb_AIS.SetTransparency(0.5)
            display.Context.Display(obb_AIS,True)


            if not iterator.next():
                break

    display.FitAll()
    start_display()


def select_with_ids(chemin):
    file=ifcopenshell.open(chemin)

    from ifctester import ids


    facet=ids.Attribute(name="GlobalId",value="2O2Fr$t4X7Zf8NOew3FLQD")
    facet=ids.Attribute(name="GlobalId",value="2O2Fr$t4X7Zf8NOew3FNhv")
    #facet=ids.Entity(name="IfcDoor")

    result=facet.filter(file,file.by_type("IfcWall"))


    for x in result:
        print(x)




if __name__ == "__main__":
    chemin="Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    select_with_ids(chemin)
    #display_front_direction(chemin,angle_offset=180)
