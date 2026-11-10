# Règles _triang contre règles d'origine

- Source : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifc` (60 éléments)
- Cible : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifc` (60 éléments)
- Triangles des règles _triang : `ifcview` (.ifcview : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifcview`, `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifcview`)
- Marge d'explication des écarts : 0.011 m (flèche .ifcview + flèche IFC)

« Froid » : ouverture d'une session (lecture de l'IFC, métadonnées du .ifcview) et première exécution (conversion IFC pour la règle d'origine, décodage du .ifcview pour la règle _triang). « Chaud » : la même règle relancée dans la session.

| Règle | Résultats origine | Résultats _triang | Communs | Manquants | En plus | Inexpliqués | Origine froid | Origine chaud | _triang froid | _triang chaud | Gain froid | Gain chaud |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DirectView_triang | 31 | 28 | 17 | 14 | 11 | 0 | 412.73 s | nan s | 0.22 s | 0.03 s | ×1910.6 | ×nan |

## DirectView_triang

Paramètres : `{'ray_source': 'Source', 'ray_count': 10, 'threshold': 50.0, 'max_distance': None}`.

- Phases _triang : `DirectView_triang   convert: 50 → 48   mid: 575 → 575   convert_narrow: 48 → 48   narrow: 575 → 28   (0.005 s)`
- Phases origine : `DirectView   convert: 50 → 50   mid: 625 → 625   narrow: 625 → 31   (411.996 s)`
- Écarts par cause : 20 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 4 absent du .ifcview, 1 échantillonnage
- 2 élément(s) absent(s) du .ifcview, ignorés (ex. #22226 1xS3BCk291UvhgP2dvNw00 is not in the .ifcview: skipped)

Manquants (14) :

- IfcSpace #67 A102 → IfcFlowFitting #135969 M_Elbow - Generic:Standard:Standard:632056 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcSpace #1782 B103 → IfcFlowFitting #148720 M_Elbow - Generic:Standard:Standard:649439 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcSpace #3586 B105 → IfcFlowFitting #100223 M_Elbow - Generic:Standard:Standard:600862 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcWallStandardCase #4643 Basic Wall:Foundation - Concrete (417mm):140479 → IfcSpace #2747 B101 — distance None — expliqué : échantillonnage : sur 200 rayons, visibilité 61 % (origine) et 58 % (_triang) pour un seuil de 50 % ; 10 rayons tirés sur d'autres triangles ne départagent pas
- IfcWallStandardCase #4643 Basic Wall:Foundation - Concrete (417mm):140479 → IfcFlowFitting #111906 M_Elbow - Generic:Standard:Standard:601283 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcSpace #70 A203 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowFitting #100223 M_Elbow - Generic:Standard:Standard:600862 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcFurnishingElement #17023 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162497 → IfcFlowSegment #21445 Pipe Types:Mechanical Pipe:550036 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcFurnishingElement #17902 M_Table-Coffee:0915 x 1830 x 0457mm:0915 x 1830 x 0457mm:168381 → IfcFlowSegment #16786 Pipe Types:Mechanical Pipe:547802 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcSlab #21449 Floor:Finish Floor - Ceramic Tile:170785 → IfcFlowFitting #58050 M_Transition - Generic:Standard:Standard:578610 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 → IfcSpace #70 A203 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 → IfcFlowSegment #43524 Pipe Types:Mechanical Pipe:557603 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 → IfcFlowFitting #148720 M_Elbow - Generic:Standard:Standard:649439 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22546 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:3 → IfcFlowFitting #49909 M_Elbow - Generic:Standard:Standard:577875 — distance None — expliqué : absent du .ifcview

En plus (11) :

- IfcSpace #67 A102 → IfcFlowFitting #150608 M_Tee - Generic:Standard:Standard:660964 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcSpace #1782 B103 → IfcFlowFitting #52912 M_Elbow - Generic:Standard:Standard:578386 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcSpace #1782 B103 → IfcFlowSegment #91282 Pipe Types:Mechanical Pipe:600381 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcSpace #1782 B103 → IfcFlowFitting #111906 M_Elbow - Generic:Standard:Standard:601283 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcWallStandardCase #4643 Basic Wall:Foundation - Concrete (417mm):140479 → IfcFlowSegment #91282 Pipe Types:Mechanical Pipe:600381 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcWallStandardCase #4643 Basic Wall:Foundation - Concrete (417mm):140479 → IfcFlowSegment #140964 Pipe Types:Mechanical Pipe:632820 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcDoor #6757 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678 → IfcFlowFitting #100223 M_Elbow - Generic:Standard:Standard:600862 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcWindow #7639 M_Casement:819mm x 759mm:819mm x 759mm:148607 → IfcFlowSegment #140964 Pipe Types:Mechanical Pipe:632820 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcDoor #16064 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065 → IfcFlowSegment #74840 Pipe Types:Mechanical Pipe:584238 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcFurnishingElement #17023 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162497 → IfcFlowFitting #135969 M_Elbow - Generic:Standard:Standard:632056 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
- IfcFurnishingElement #29127 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191680 → IfcFlowFitting #135969 M_Elbow - Generic:Standard:Standard:632056 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : les faces « tournées vers l'autre objet » se lisent sur les normales
