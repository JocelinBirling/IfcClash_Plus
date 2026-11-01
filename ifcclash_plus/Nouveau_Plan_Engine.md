


BonsaiViewer, pour lancer la géométrie vient créer des fichiers .ifcview.

CGAL sait bien utiliser .ifcview.
Opencascade sait bien utiliser .ifc (pour reconstruire la géométrie).




Rapport : détection de clash à partir des .ifcview

Format .ifcview (v19)

Géométrie compressée par chunk (zstd), lisible indépendamment.
Métadonnées : meshes, instances (mesh_id, object_id, translation en double, partie linéaire en float), georef, table des éléments (GUID, nom, type).
Absents : relations IFC et propriétés.

Précision et LOD

Positions sur u16 relatives à la boîte locale du mesh. Un pas vaut extent / 65535, soit environ 0,15 mm pour un mesh de 10 m. Ce chiffre reste à confirmer dans VertexQuantization.h.
Deux niveaux : LOD0 (complet) et LOD1 (optionnel, décimé). L’erreur de LOD1 est forcée à au moins 0,2 de l’étendue du mesh, donc trop grossière pour un clash. On utilise LOD0 uniquement.

Économie

Lire le .ifcview coûte peu, la génération a déjà été payée. Régénérer depuis l’IFC est plus lent mais plus précis.
Pas de contrôle de fraîcheur : un cache obsolète reste utilisé.
Approche retenue à valider : pré-filtrage avec le .ifcview (marge = quantification + tolérance), puis vérification exacte sur l’IFC.

Pipeline après lecture

Métadonnées puis chunks à la demande.
Dequantification, placement, CoordinateOperation si fédération.
Primitives par élément (triangles monde, boîte, métadonnées).
Phase large : BVH ou grille, boîtes élargies.
Filtrage par règles.
Phase fine : triangle contre triangle (clash dur), distance minimale (clearance), inclusion de point (zones).
Résultats regroupés.
Sortie CSV/JSON, marqueurs, focus caméra.

Limite : sans relations, les règles ne peuvent utiliser que classe, nom, type et GUID.

Bibliothèques

Déjà disponibles : Eigen, zstd, meshoptimizer (optionnelle).
Recommandé au départ : BVH maison et test de Möller, sans nouvelle dépendance.
En option : FCL (BSD) pour la distance mesh/mesh, CGAL pour la robustesse (licence à vérifier).
Chemin IFC : OpenCASCADE, déjà utilisée par IfcOpenShell.
CGAL pour les triangles (.ifcview), OCC pour les B-Rep (IFC).

Décisions en attente

Clash dur seul, ou aussi clearance ?
Un modèle ou plusieurs modèles fédérés ?
Tolérance par défaut (par exemple 10 mm) ?
Format de sortie : CSV, panneau, ou BCF plus tard ?
Démarrer par le module CPU avec tests, ou par la comparaison IFC ?
Possèdes-tu les fichiers IFC sources ?

