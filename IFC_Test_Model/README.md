In this folder you will find the IFC test models. They provide a small object library.

These objects are paired two by two in the model, with a position that is described in the title.

ObjectA_Position_ObjectB_Parameter.

The goal is to describe different relative object positions and to test the rules.
A single file can therefore be used for different rules.

## Génération des modèles manquants

`generate_models.py` (racine de ce dossier) régénère les 31 modèles
complémentaires à partir du template `IFC_Model/CylinderA_Above_SlabA.ifc`
(qui contient les 18 objets nommés de base). Il repositionne les objets par
leur centre en coordonnées monde et crée au besoin de nouvelles géométries
(sphère, tore, cône, poutre élancée, cylindres `IfcCircleProfileDef`, plaque
fine). Les specs (nom de fichier + placements + nouvelles géométries) sont
documentées dans la liste `SPECS` du script.

Depuis la racine du dépôt :

    .venv/bin/python IFC_Test_Model/generate_models.py            # tout générer
    .venv/bin/python IFC_Test_Model/generate_models.py --list       # lister les specs
    .venv/bin/python IFC_Test_Model/generate_models.py <nom>        # un seul modèle

Les tests associés (valeurs calibrées) sont dans :
- `tests/test_Rule_IFC_Test_Model_New.py` — règles 2-objets sur les nouveaux modèles ;
- `tests/test_Rule_IFC_Test_Model_Complete.py` — variantes above/below_type,
  règles avec contexte (DirectView, Ray_Check, FreeSpace), règles spécialisées
  (ClearanceAxisToAxis, ClearanceForDoors, TwoObjectsFace, OBB_Custom,
  Alignement), positions manquantes (RecoverBottom, TouchInside, Below U) ;
- `tests/test_unit_new_geometries.py` — tests unitaires de get_extreme_faces
  et de l'OBB (PCA) sur les nouvelles géométries ;
- `tests/test_Rule_IFC_Test_Model_OneObject.py` — règles 1-objet (Volume, Area,
  TopOrBottomSurface, LateralSurface, ProjectedSurface, ObbHigh, ObbLength,
  Orientation, OneObjectFace) testées sur CubeA et SuzanneA.
