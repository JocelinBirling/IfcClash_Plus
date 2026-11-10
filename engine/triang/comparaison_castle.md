# Règles _triang contre règles d'origine
- Source : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_SampleCastle.ifc` (300 éléments)
- Cible : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_SampleCastle.ifc` (300 éléments)
- Triangles des règles _triang : `ifcview` (.ifcview : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_SampleCastle.ifcview`)
- Marge d'explication des écarts : 0.011 m (flèche .ifcview + flèche IFC)

25 règles `_triang`, une par processus (`compare_triang.py --rules`, 4 à 8 threads, une à la fois). **0 écart(s) inexpliqué(s).** ClearanceForDoors et Intersection2 ne sont plus portées ; DirectView est comparée à part (`comparaison_directview.md`).

Temps de l'origine : sa première exécution, froide (ouverture de session et conversion IFC comprises), lue ensuite dans le cache du comparateur (`build/engine/triang_original_cache`) : les règles d'origine ne changent pas, elles ne sont plus relancées. Ces premières exécutions ont tourné avec 2, 4 ou 8 threads selon les passes : les gains sont des ordres de grandeur. `_triang` : froid = ouverture de session et première exécution, chaud = la règle relancée dans la session.

| Règle | Origine | _triang | Communs | Manquants | En plus | Inexpliqués | Origine froid | _triang froid | _triang chaud | Gain froid |
|---|---|---|---|---|---|---|---|---|---|---|
| Intersection_triang | 14 | 9 | 7 | 7 | 2 | 0 | 1.86 s | 1.07 s | 0.01 s | ×1.7 |
| Above_triang | **erreur** | 120 résultats en 0.09 s |  |  |  |  |  |  |  |  |
| Below_triang | **erreur** | 93 résultats en 0.09 s |  |  |  |  |  |  |  |  |
| OBB_Above_triang | **erreur** | 204 résultats en 0.08 s |  |  |  |  |  |  |  |  |
| OBB_Below_triang | **erreur** | 192 résultats en 0.08 s |  |  |  |  |  |  |  |  |
| OBB_Front_And_Back_triang | **erreur** | 434 résultats en 0.09 s |  |  |  |  |  |  |  |  |
| OBB_Custom_triang | **erreur** | 430 résultats en 0.09 s |  |  |  |  |  |  |  |  |
| AngleBetween_triang | **erreur** | 34707 résultats en 0.66 s |  |  |  |  |  |  |  |  |
| ObbHigh_triang | **erreur** | 563 résultats en 0.07 s |  |  |  |  |  |  |  |  |
| ObbLength_triang | **erreur** | 563 résultats en 0.07 s |  |  |  |  |  |  |  |  |
| Orientation_triang | **erreur** | 563 résultats en 0.07 s |  |  |  |  |  |  |  |  |
| Alignement_triang | **erreur** | 40 résultats en 0.15 s |  |  |  |  |  |  |  |  |
| Clearance_triang | 882 | 859 | 858 | 24 | 1 | 0 | 1.91 s | 1.11 s | 0.08 s | ×1.7 |
| Collision_triang | 17 | 18 | 12 | 5 | 6 | 0 | 1.85 s | 1.06 s | 0.00 s | ×1.8 |
| Volume_triang | 574 | 563 | 563 | 11 | 0 | 0 | 1.87 s | 1.06 s | 0.00 s | ×1.8 |
| Area_triang | 574 | 563 | 563 | 11 | 0 | 0 | 1.86 s | 1.06 s | 0.00 s | ×1.8 |
| TopOrBottomSurface_triang | 574 | 563 | 563 | 11 | 0 | 0 | 3.38 s | 2.63 s | 1.70 s | ×1.3 |
| LateralSurface_triang | 555 | 547 | 544 | 11 | 3 | 0 | 2.05 s | 1.17 s | 0.00 s | ×1.7 |
| ProjectedSurface_triang | 574 | 563 | 563 | 11 | 0 | 0 | 2.19 s | 1.39 s | 0.21 s | ×1.6 |
| ClearanceAxisToAxis_triang | **erreur** | 43 résultats en 0.08 s |  |  |  |  |  |  |  |  |
| SurfaceRecover_triang | **erreur** | 88 résultats en 0.11 s |  |  |  |  |  |  |  |  |
| Ray_Check_triang | 3054 | 3007 | 2930 | 124 | 77 | 0 | 8.22 s | 1.18 s | 0.15 s | ×7.0 |
| OneObjectFace_triang | 271 | 272 | 271 | 0 | 1 | 0 | 6.14 s | 5.23 s | 4.17 s | ×1.2 |
| TwoObjectsFace_triang | 323 | 315 | 314 | 9 | 1 | 0 | 3.38 s | 2.30 s | 1.23 s | ×1.5 |
| FreeSpace_triang | **erreur** | 563 résultats en 0.11 s |  |  |  |  |  |  |  |  |

## Intersection_triang

Paramètres : `{'tolerance': 0.002}`.

- Phases _triang : `Intersection_triang   convert: 600 → 563   broad: 79236 → 215   mid: 215 → 214   convert_narrow: 306 → 306   narrow: 214 → 9   (0.021 s)`
- Phases origine : `Intersection   convert: 600 → 574   broad: 82369 → 223   mid: 223 → 206   narrow: 206 → 14   (0.974 s)`
- Écarts par cause : 6 absent du .ifcview, 3 géométries IFC au contact
- 37 élément(s) absent(s) du .ifcview, ignorés (ex. #49281 2qmQa8nAP39u6po5334l9v is not in the .ifcview: skipped)

Manquants (7) :

- IfcOpeningElement #112436 merk B1 → IfcWindow #113293 merk B1 — distance 0.151 — expliqué : absent du .ifcview
- IfcCovering #204160 vensterbank → IfcOpeningElement #49325 merk B1sp — distance 0.026 — expliqué : absent du .ifcview
- IfcOpeningElement #340204 merk B1sp-R → IfcWindow #341061 merk B1sp-R — distance 0.151 — expliqué : absent du .ifcview
- IfcOpeningElement #340204 merk B1sp-R → IfcCovering #490140 vensterbank — distance 0.026 — expliqué : absent du .ifcview
- IfcCovering #722078 zinkwerk → IfcCovering #722316 zinkwerk — distance 0.018 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcOpeningElement #778649 merk Dsp → IfcWindow #779510 merk Dsp — distance 0.151 — expliqué : absent du .ifcview
- IfcSlab #905787 dekvloer → IfcOpeningElement #820778 merk A3sp — distance 0.342 — expliqué : absent du .ifcview

En plus (2) :

- IfcBeam #707716 betonlatei → IfcWall #609468 liftwand — distance 0.164 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcSlab #905787 dekvloer → IfcWallStandardCase #825203 liftwand — distance 0.0446 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes

## Above_triang

La règle d'origine Above échoue : `gp_Dir() - input vector has zero norm`. Above_triang : 120 résultats en 0.09 s.

## Below_triang

La règle d'origine Below échoue : `gp_Dir() - input vector has zero norm`. Below_triang : 93 résultats en 0.09 s.

## OBB_Above_triang

La règle d'origine OBB_Above échoue : `gp_Dir() - input vector has zero norm`. OBB_Above_triang : 204 résultats en 0.08 s.

## OBB_Below_triang

La règle d'origine OBB_Below échoue : `gp_Dir() - input vector has zero norm`. OBB_Below_triang : 192 résultats en 0.08 s.

## OBB_Front_And_Back_triang

La règle d'origine OBB_Front_And_Back échoue : `gp_Dir() - input vector has zero norm`. OBB_Front_And_Back_triang : 434 résultats en 0.09 s.

## OBB_Custom_triang

La règle d'origine OBB_Custom échoue : `gp_Dir() - input vector has zero norm`. OBB_Custom_triang : 430 résultats en 0.09 s.

## AngleBetween_triang

La règle d'origine AngleBetween échoue : `gp_Dir() - input vector has zero norm`. AngleBetween_triang : 34707 résultats en 0.66 s.

## ObbHigh_triang

La règle d'origine ObbHigh échoue : `gp_Dir() - input vector has zero norm`. ObbHigh_triang : 563 résultats en 0.07 s.

## ObbLength_triang

La règle d'origine ObbLength échoue : `gp_Dir() - input vector has zero norm`. ObbLength_triang : 563 résultats en 0.07 s.

## Orientation_triang

La règle d'origine Orientation échoue : `gp_Dir() - input vector has zero norm`. Orientation_triang : 563 résultats en 0.07 s.

## Alignement_triang

La règle d'origine Alignement échoue : `gp_Dir() - input vector has zero norm`. Alignement_triang : 40 résultats en 0.15 s.

## Clearance_triang

Paramètres : `{'clearance': 0.5, 'check_all': True}`.

- Phases _triang : `Clearance_triang   convert: 600 → 563   broad: 79236 → 927   mid: 927 → 924   convert_narrow: 531 → 531   narrow: 924 → 859   (0.061 s)`
- Phases origine : `Clearance   convert: 600 → 574   broad: 82369 → 954   mid: 954 → 943   narrow: 943 → 882   (1.020 s)`
- Écarts par cause : 24 absent du .ifcview, 1 distance au bord du seuil
- 37 élément(s) absent(s) du .ifcview, ignorés (ex. #49281 2qmQa8nAP39u6po5334l9v is not in the .ifcview: skipped)

Manquants (24) :

- IfcCovering #65691 gevelisolatie → IfcOpeningElement #49325 merk B1sp — distance 0.03 — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 → IfcWindow #113293 merk B1 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 → IfcWallStandardCase #397232 buitenblad — distance 0.37 — expliqué : absent du .ifcview
- IfcCovering #204160 vensterbank → IfcOpeningElement #49325 merk B1sp — distance 0.005 — expliqué : absent du .ifcview
- IfcWall #337098 binnenblad → IfcOpeningElement #401514 merk B1-R — distance 0.009 — expliqué : absent du .ifcview
- IfcOpeningElement #340204 merk B1sp-R → IfcWindow #341061 merk B1sp-R — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #340204 merk B1sp-R → IfcCovering #490140 vensterbank — distance 0.005 — expliqué : absent du .ifcview
- IfcCovering #361453 gevelisolatie → IfcOpeningElement #52392 merk B1 — distance 0.3719 — expliqué : absent du .ifcview
- IfcWall #363809 buitenblad → IfcOpeningElement #52392 merk B1 — distance 0.37 — expliqué : absent du .ifcview
- IfcWallStandardCase #366933 buitenblad → IfcOpeningElement #49325 merk B1sp — distance 0.37 — expliqué : absent du .ifcview
- IfcWall #438801 buitenblad → IfcOpeningElement #435351 merk B2-R — distance 0.0 — expliqué : absent du .ifcview
- IfcCovering #508846 vensterbank → IfcOpeningElement #424497 merk M — distance 0.376 — expliqué : absent du .ifcview
- IfcOpeningElement #778649 merk Dsp → IfcWindow #779510 merk Dsp — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #778649 merk Dsp → IfcCovering #856191 zinkwerk — distance 0.2638 — expliqué : absent du .ifcview
- IfcOpeningElement #778649 merk Dsp → IfcWall #876108 knieschot — distance 0.1746 — expliqué : absent du .ifcview
- IfcSlab #782593 vloerveld → IfcOpeningElement #820778 merk A3sp — distance 0.288 — expliqué : absent du .ifcview
- IfcWallStandardCase #787207 kozijn → IfcOpeningElement #787251 merk K — distance 0.0 — expliqué : absent du .ifcview
- IfcCovering #828640 dakpan (vlak) → IfcOpeningElement #787251 merk K — distance 0.0025 — expliqué : absent du .ifcview
- IfcCovering #855988 dak dakkapel → IfcOpeningElement #787251 merk K — distance 0.146 — expliqué : absent du .ifcview
- IfcWall #868096 knieschot → IfcOpeningElement #787251 merk K — distance 0.0957 — expliqué : absent du .ifcview
- IfcSlab #905787 dekvloer → IfcOpeningElement #820778 merk A3sp — distance 0.0116 — expliqué : absent du .ifcview
- IfcCovering #973159 zinkwerk → IfcOpeningElement #787251 merk K — distance 0.169 — expliqué : absent du .ifcview
- IfcSlab #991286 dakvloer → IfcOpeningElement #820778 merk A3sp — distance 0.012 — expliqué : absent du .ifcview
- IfcCovering #1020012 betontegels → IfcOpeningElement #820778 merk A3sp — distance 0.455 — expliqué : absent du .ifcview

En plus (1) :

- IfcWall #705309 buitenblad → IfcWall #547627 separatiewand — distance 0.5 — expliqué : distance 0.5000 au bord du seuil (± marge)

## Collision_triang

Paramètres : `{'allow_touching': False}`.

- Phases _triang : `Collision_triang   convert: 600 → 563   broad: 79236 → 215   mid: 215 → 214   convert_narrow: 306 → 306   narrow: 214 → 18   (0.016 s)`
- Phases origine : `Collision   convert: 600 → 574   broad: 82369 → 223   mid: 223 → 206   narrow: 206 → 17   (0.969 s)`
- Écarts par cause : 8 géométries IFC au contact, 3 absent du .ifcview
- 37 élément(s) absent(s) du .ifcview, ignorés (ex. #49281 2qmQa8nAP39u6po5334l9v is not in the .ifcview: skipped)

Manquants (5) :

- IfcCovering #204160 vensterbank → IfcOpeningElement #49325 merk B1sp — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #340204 merk B1sp-R → IfcCovering #490140 vensterbank — distance 0.0 — expliqué : absent du .ifcview
- IfcDoor #561231 liftdeur → IfcDoor #561395 liftdeur — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWall #660018 buitenblad → IfcCovering #665749 afdekker — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcSlab #905787 dekvloer → IfcOpeningElement #820778 merk A3sp — distance 0.0 — expliqué : absent du .ifcview

En plus (6) :

- IfcSlab #327806 vloerveld → IfcCovering #349401 gevelisolatie — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWall #552499 separatiewand → IfcDoor #552649 D1R — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWall #577370 separatiewand → IfcDoor #577520 D2R — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcBuildingElementPart #807927 → IfcBuildingElementPart #860088 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcBuildingElementPart #818239 → IfcBuildingElementPart #799717 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcSlab #905787 dekvloer → IfcWallStandardCase #825203 liftwand — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation

## Volume_triang

Paramètres : `{'volume_min': 0.0, 'volume_max': 1000000000.0}`.

- Phases _triang : `Volume_triang   convert: 600 → 563   narrow: 563 → 563   (0.015 s)`
- Phases origine : `Volume   convert: 600 → 574   narrow: 574 → 574   (0.970 s)`
- Mesures comparées sur 563 éléments communs : 7 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 11 absent du .ifcview, 5 maillage _triang non fermé une fois réparé, 2 maillage IFC ouvert
- 37 élément(s) absent(s) du .ifcview, ignorés (ex. #49281 2qmQa8nAP39u6po5334l9v is not in the .ifcview: skipped)

Manquants (11) :

- IfcOpeningElement #49325 merk B1sp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #52392 merk B1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #119898 merk B1sp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #340204 merk B1sp-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #401514 merk B1-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #424497 merk M — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #435351 merk B2-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #778649 merk Dsp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #787251 merk K — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #820778 merk A3sp — distance None — expliqué : absent du .ifcview

Mesures (7) :

- IfcWindow #131772 merk N — écart -0.0137 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #144091 merk M — écart -0.0518 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcDoor #316267 merk A3 — écart -0.0933 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #683412 merk Csp — écart -0.0156 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #879766 merk J — écart -0.0749 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #944800 velux K08 — écart 0.0565 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcWindow #948940 velux K08 — écart 0.0565 — expliqué : maillage IFC ouvert : volume non défini pour l'original

## Area_triang

Paramètres : `{'volume_min': 0.0, 'volume_max': 1000000000.0}`.

- Phases _triang : `Area_triang   convert: 600 → 563   narrow: 563 → 563   (0.014 s)`
- Phases origine : `Area   convert: 600 → 574   narrow: 574 → 574   (0.970 s)`
- Mesures comparées sur 563 éléments communs : 0 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 11 absent du .ifcview
- 37 élément(s) absent(s) du .ifcview, ignorés (ex. #49281 2qmQa8nAP39u6po5334l9v is not in the .ifcview: skipped)

Manquants (11) :

- IfcOpeningElement #49325 merk B1sp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #52392 merk B1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #119898 merk B1sp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #340204 merk B1sp-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #401514 merk B1-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #424497 merk M — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #435351 merk B2-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #778649 merk Dsp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #787251 merk K — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #820778 merk A3sp — distance None — expliqué : absent du .ifcview

## TopOrBottomSurface_triang

Paramètres : `{'surface_min': 0.0, 'surface_max': 1000000000.0, 'top_or_bot_method': 'Top'}`.

- Phases _triang : `TopOrBottomSurface_triang   convert: 600 → 563   narrow: 563 → 563   (1.529 s)`
- Phases origine : `TopOrBottomSurface   convert: 600 → 600   narrow: 600 → 574   (2.353 s)`
- Mesures comparées sur 563 éléments communs : 7 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 11 absent du .ifcview, 7 maillage _triang non fermé une fois réparé
- 37 élément(s) absent(s) du .ifcview, ignorés (ex. #49281 2qmQa8nAP39u6po5334l9v is not in the .ifcview: skipped)

Manquants (11) :

- IfcOpeningElement #49325 merk B1sp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #52392 merk B1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #119898 merk B1sp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #340204 merk B1sp-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #401514 merk B1-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #424497 merk M — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #435351 merk B2-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #778649 merk Dsp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #787251 merk K — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #820778 merk A3sp — distance None — expliqué : absent du .ifcview

Mesures (7) :

- IfcWindow #131772 merk N — écart -0.0205 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #144091 merk M — écart 0.0247 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #879766 merk J — écart -0.0772 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #944800 velux K08 — écart 0.0469 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #948940 velux K08 — écart 0.0469 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #1019007 dakkoepel 1000x — écart 0.0645 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #1019087 dakkoepel 1000x — écart 0.0645 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains

## LateralSurface_triang

Paramètres : `{'surface_min': 0.0, 'surface_max': 1000000000.0, 'direction': [0.0, 1.0, 0.0]}`.

- Phases _triang : `LateralSurface_triang   convert: 600 → 563   narrow: 563 → 547   (0.016 s)`
- Phases origine : `LateralSurface   convert: 600 → 600   narrow: 600 → 555   (1.070 s)`
- Mesures comparées sur 544 éléments communs : 3 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 11 absent du .ifcview, 3 propre au maillage .ifcview, 3 maillage _triang non fermé une fois réparé
- 37 élément(s) absent(s) du .ifcview, ignorés (ex. #49281 2qmQa8nAP39u6po5334l9v is not in the .ifcview: skipped)

Manquants (11) :

- IfcOpeningElement #49325 merk B1sp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #52392 merk B1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #119898 merk B1sp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #340204 merk B1sp-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #401514 merk B1-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #424497 merk M — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #435351 merk B2-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #778649 merk Dsp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #787251 merk K — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #820778 merk A3sp — distance None — expliqué : absent du .ifcview

En plus (3) :

- IfcBuildingElementPart #799233 — distance None — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcBuildingElementPart #799717 — distance None — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcCovering #1014756 zinkwerk — distance None — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original

Mesures (3) :

- IfcWindow #131772 merk N — écart 0.0918 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #144091 merk M — écart -0.2633 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #879766 merk J — écart 0.3838 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains

## ProjectedSurface_triang

Paramètres : `{'surface_min': 0.0, 'surface_max': 1000000000.0, 'direction': [0.0, 0.0, 1.0]}`.

- Phases _triang : `ProjectedSurface_triang   convert: 600 → 563   narrow: 563 → 563   (0.218 s)`
- Phases origine : `ProjectedSurface   convert: 600 → 600   narrow: 600 → 574   (1.206 s)`
- Mesures comparées sur 563 éléments communs : 0 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 11 absent du .ifcview
- 37 élément(s) absent(s) du .ifcview, ignorés (ex. #49281 2qmQa8nAP39u6po5334l9v is not in the .ifcview: skipped)

Manquants (11) :

- IfcOpeningElement #49325 merk B1sp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #52392 merk B1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #119898 merk B1sp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #340204 merk B1sp-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #401514 merk B1-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #424497 merk M — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #435351 merk B2-R — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #778649 merk Dsp — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #787251 merk K — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #820778 merk A3sp — distance None — expliqué : absent du .ifcview

## ClearanceAxisToAxis_triang

La règle d'origine ClearanceAxisToAxis échoue : `gp_Dir() - input vector has zero norm`. ClearanceAxisToAxis_triang : 43 résultats en 0.08 s.

## SurfaceRecover_triang

La règle d'origine SurfaceRecover échoue : `gp_Dir() - input vector has zero norm`. SurfaceRecover_triang : 88 résultats en 0.11 s.

## Ray_Check_triang

Paramètres : `{'max_ray_length': 5.0}`.

- Phases _triang : `Ray_Check_triang   convert: 600 → 563   broad: 79236 → 8394   mid: 8394 → 8394   convert_narrow: 563 → 563   narrow: 8394 → 3007   (0.011 s)`
- Phases origine : `Ray_Check   convert: 600 → 574   broad: 82369 → 8755   mid: 8755 → 8755   narrow: 8755 → 3054   (6.452 s)`
- Écarts par cause : 124 absent du .ifcview, 70 ensemble d'entrée différent, 7 propre au maillage .ifcview
- 37 élément(s) absent(s) du .ifcview, ignorés (ex. #49281 2qmQa8nAP39u6po5334l9v is not in the .ifcview: skipped)

Manquants (124) :

- IfcBeam #2299 fund_opstort → IfcOpeningElement #49325 merk B1sp — distance 3.0201 — expliqué : absent du .ifcview
- IfcBeam #2299 fund_opstort → IfcOpeningElement #52392 merk B1 — distance 4.3404 — expliqué : absent du .ifcview
- IfcBeam #10431 fund_opstort → IfcOpeningElement #119898 merk B1sp — distance 4.4979 — expliqué : absent du .ifcview
- IfcWall #13956 opgaand werk → IfcOpeningElement #52392 merk B1 — distance 3.5466 — expliqué : absent du .ifcview
- IfcWall #21839 opgaand werk → IfcOpeningElement #119898 merk B1sp — distance 4.5291 — expliqué : absent du .ifcview
- IfcSlab #34761 vloer_V0 → IfcOpeningElement #119898 merk B1sp — distance 2.6092 — expliqué : absent du .ifcview
- IfcSlab #36417 vloer_V0 → IfcOpeningElement #119898 merk B1sp — distance 4.9692 — expliqué : absent du .ifcview
- IfcFlowSegment #40694 hwa afvoer → IfcOpeningElement #119898 merk B1sp — distance 2.5805 — expliqué : absent du .ifcview
- IfcCovering #44653 gevelisolatie → IfcOpeningElement #424497 merk M — distance 2.9147 — expliqué : absent du .ifcview
- IfcWall #56879 buitenblad → IfcOpeningElement #49325 merk B1sp — distance 3.5024 — expliqué : absent du .ifcview
- IfcWall #56879 buitenblad → IfcOpeningElement #52392 merk B1 — distance 1.6097 — expliqué : absent du .ifcview
- IfcCovering #65691 gevelisolatie → IfcOpeningElement #49325 merk B1sp — distance 1.5523 — expliqué : absent du .ifcview
- IfcCovering #65691 gevelisolatie → IfcOpeningElement #52392 merk B1 — distance 2.4742 — expliqué : absent du .ifcview
- IfcWall #68378 buitenblad → IfcOpeningElement #424497 merk M — distance 4.7233 — expliqué : absent du .ifcview
- IfcWall #71078 buitenblad → IfcOpeningElement #424497 merk M — distance 4.208 — expliqué : absent du .ifcview
- IfcWall #74894 buitenblad → IfcOpeningElement #49325 merk B1sp — distance 1.6434 — expliqué : absent du .ifcview
- IfcWall #74894 buitenblad → IfcOpeningElement #52392 merk B1 — distance 3.5261 — expliqué : absent du .ifcview
- IfcWall #91538 buitenblad → IfcOpeningElement #401514 merk B1-R — distance 4.0447 — expliqué : absent du .ifcview
- IfcCovering #94503 gevelisolatie → IfcOpeningElement #119898 merk B1sp — distance 3.9619 — expliqué : absent du .ifcview
- IfcWall #109935 buitenblad → IfcOpeningElement #401514 merk B1-R — distance 3.5162 — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 → IfcFlowSegment #46029 hwa afvoer — distance 1.9464 — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 → IfcWindow #113293 merk B1 — distance 0.057 — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 → IfcFlowSegment #333562 hwa afvoer — distance 2.9188 — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 → IfcCovering #381357 betontegels — distance 3.0374 — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 → IfcCovering #395708 betontegels — distance 2.4749 — expliqué : absent du .ifcview
- IfcCovering #117764 gevelisolatie → IfcOpeningElement #119898 merk B1sp — distance 4.1129 — expliqué : absent du .ifcview
- IfcWindow #144091 merk M → IfcOpeningElement #424497 merk M — distance 3.3818 — expliqué : absent du .ifcview
- IfcCovering #162403 gevelisolatie → IfcOpeningElement #435351 merk B2-R — distance 4.6523 — expliqué : absent du .ifcview
- IfcWindow #171385 stelkozijn → IfcOpeningElement #119898 merk B1sp — distance 4.9817 — expliqué : absent du .ifcview
- IfcCovering #174789 gevelisolatie → IfcOpeningElement #119898 merk B1sp — distance 4.1658 — expliqué : absent du .ifcview
- IfcCovering #174789 gevelisolatie → IfcOpeningElement #435351 merk B2-R — distance 4.5172 — expliqué : absent du .ifcview
- IfcCovering #177377 afdekker → IfcOpeningElement #119898 merk B1sp — distance 4.9407 — expliqué : absent du .ifcview
- IfcCovering #204160 vensterbank → IfcOpeningElement #49325 merk B1sp — distance 0.9486 — expliqué : absent du .ifcview
- IfcCovering #204160 vensterbank → IfcOpeningElement #52392 merk B1 — distance 2.0487 — expliqué : absent du .ifcview
- IfcCovering #205984 vensterbank → IfcOpeningElement #119898 merk B1sp — distance 3.519 — expliqué : absent du .ifcview
- IfcDoor #231560 D5R → IfcOpeningElement #119898 merk B1sp — distance 4.8693 — expliqué : absent du .ifcview
- IfcWallStandardCase #250096 separatiewand → IfcOpeningElement #424497 merk M — distance 3.7477 — expliqué : absent du .ifcview
- IfcBeam #297791 staallatei ?? → IfcOpeningElement #401514 merk B1-R — distance 3.8762 — expliqué : absent du .ifcview
- IfcCovering #305226 wandtegelwerk → IfcOpeningElement #401514 merk B1-R — distance 4.8816 — expliqué : absent du .ifcview
- IfcWall #337098 binnenblad → IfcOpeningElement #401514 merk B1-R — distance 0.6457 — expliqué : absent du .ifcview
- ... 84 de plus

En plus (77) :

- IfcBeam #2299 fund_opstort → IfcCovering #65891 gevelisolatie — distance 3.9508 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #59828 buitenblad → IfcCovering #349401 gevelisolatie — distance 0.2396 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcWall #59828 buitenblad → IfcWall #367146 buitenblad — distance 3.9302 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #65691 gevelisolatie → IfcWall #57162 buitenblad — distance 4.8066 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #65691 gevelisolatie → IfcCovering #378604 gevelisolatie — distance 4.9523 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #65691 gevelisolatie → IfcCovering #474543 zinkwerk — distance 4.9202 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #68378 buitenblad → IfcCovering #349401 gevelisolatie — distance 3.3704 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcWall #71078 buitenblad → IfcWindow #341061 merk B1sp-R — distance 3.6019 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #74894 buitenblad → IfcCovering #65891 gevelisolatie — distance 2.0396 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #91538 buitenblad → IfcWindow #113293 merk B1 — distance 2.7134 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #97183 buitenblad → IfcWindow #113293 merk B1 — distance 4.9057 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #101093 buitenblad → IfcWindow #113293 merk B1 — distance 3.8543 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #109935 buitenblad → IfcWindow #113293 merk B1 — distance 1.8157 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #109935 buitenblad → IfcCovering #657433 gevelisolatie — distance 4.9937 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #125316 HSB-element → IfcCovering #349401 gevelisolatie — distance 0.1398 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcWindow #131772 merk N → IfcWindow #113293 merk B1 — distance 4.1335 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #204160 vensterbank → IfcCovering #65891 gevelisolatie — distance 2.0431 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #204160 vensterbank → IfcCovering #378604 gevelisolatie — distance 4.3985 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #204160 vensterbank → IfcCovering #474543 zinkwerk — distance 4.3705 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #204160 vensterbank → IfcBuildingElementPart #500567 — distance 4.9013 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcSlab #239582 dekvloer → IfcWindow #113293 merk B1 — distance 3.4594 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcBeam #295147 staallatei ?? → IfcWindow #341061 merk B1sp-R — distance 1.9835 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcBeam #295147 staallatei ?? → IfcCovering #349401 gevelisolatie — distance 2.2312 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcBeam #295147 staallatei ?? → IfcWall #621951 buitenblad — distance 3.9883 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #305226 wandtegelwerk → IfcWindow #113293 merk B1 — distance 2.8331 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWallStandardCase #333227 binnenblad → IfcWindow #341061 merk B1sp-R — distance 1.2666 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #337098 binnenblad → IfcWindow #113293 merk B1 — distance 2.5976 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #337098 binnenblad → IfcFlowSegment #333562 hwa afvoer — distance 1.0559 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #337098 binnenblad → IfcWallStandardCase #397232 buitenblad — distance 1.0155 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #337098 binnenblad → IfcBuildingElementPart #817123 — distance 4.7109 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #350974 betontegels → IfcWindow #341061 merk B1sp-R — distance 3.7207 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #353612 buitenblad → IfcWindow #341061 merk B1sp-R — distance 1.8271 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWall #353612 buitenblad → IfcCovering #349401 gevelisolatie — distance 1.8245 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcWall #353612 buitenblad → IfcWall #367146 buitenblad — distance 3.2067 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #356252 betontegels → IfcWindow #341061 merk B1sp-R — distance 3.2296 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #357723 betontegels → IfcWindow #341061 merk B1sp-R — distance 4.0699 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWallStandardCase #366933 buitenblad → IfcWall #57162 buitenblad — distance 4.9361 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWallStandardCase #366933 buitenblad → IfcWall #75110 buitenblad — distance 3.6887 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #381121 gevelisolatie → IfcWindow #132846 merk N — distance 4.5029 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcCovering #381121 gevelisolatie → IfcWall #393170 buitenblad — distance 3.6906 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- ... 37 de plus

## OneObjectFace_triang

Paramètres : `{'distance': True, 'min_distance': 0.5, 'max_distance': None, 'intersection': True, 'intersection_tolerance': 0.0, 'orientation': False, 'angle': None, 'angle_tolerance': 0.0, 'face_a_selection': {'orientation': 'Top', 'extreme_faces': True}, 'face_b_selection': {'orientation': 'Bottom', 'extreme_faces': True}, 'skip_adjacent': True}`.

- Phases _triang : `OneObjectFace_triang   convert: 600 → 563   narrow: 563 → 2940   (4.074 s)`
- Phases origine : `OneObjectFace   convert: 600 → 600   narrow: 600 → 2970   (5.151 s)`
- Écarts par cause : 1 propre au maillage .ifcview
- 37 élément(s) absent(s) du .ifcview, ignorés (ex. #49281 2qmQa8nAP39u6po5334l9v is not in the .ifcview: skipped)

En plus (1) :

- IfcWall #868365 knieschot — distance 0.0042 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original

## TwoObjectsFace_triang

Paramètres : `{'distance': True, 'min_distance': 0.3, 'max_distance': None, 'intersection': True, 'intersection_tolerance': 0.0, 'orientation': False, 'angle': None, 'angle_tolerance': 0.0, 'source_face_selection': {'orientation': 'Top', 'extreme_faces': True}, 'target_face_selection': {'orientation': 'Bottom'}}`.

- Phases _triang : `TwoObjectsFace_triang   convert: 600 → 553   broad: 76452 → 353   mid: 353 → 353   convert_narrow: 371 → 371   narrow: 353 → 4850   (1.119 s)`
- Phases origine : `TwoObjectsFace   convert: 600 → 564   broad: 79515 → 363   mid: 363 → 363   narrow: 363 → 5079   (2.279 s)`
- Écarts par cause : 9 absent du .ifcview, 1 propre au maillage .ifcview
- 37 élément(s) absent(s) du .ifcview, ignorés (ex. #49281 2qmQa8nAP39u6po5334l9v is not in the .ifcview: skipped)

Manquants (9) :

- IfcCovering #65691 gevelisolatie → IfcOpeningElement #49325 merk B1sp — distance 0.03 — expliqué : absent du .ifcview
- IfcOpeningElement #112436 merk B1 → IfcWindow #113293 merk B1 — distance 0.1301 — expliqué : absent du .ifcview
- IfcCovering #204160 vensterbank → IfcOpeningElement #49325 merk B1sp — distance 0.025 — expliqué : absent du .ifcview
- IfcOpeningElement #340204 merk B1sp-R → IfcWindow #341061 merk B1sp-R — distance 0.1301 — expliqué : absent du .ifcview
- IfcOpeningElement #778649 merk Dsp → IfcWindow #779510 merk Dsp — distance 0.073 — expliqué : absent du .ifcview
- IfcOpeningElement #778649 merk Dsp → IfcCovering #856191 zinkwerk — distance 0.2841 — expliqué : absent du .ifcview
- IfcSlab #782593 vloerveld → IfcOpeningElement #820778 merk A3sp — distance 0.288 — expliqué : absent du .ifcview
- IfcWall #868096 knieschot → IfcOpeningElement #787251 merk K — distance 0.0957 — expliqué : absent du .ifcview
- IfcSlab #905787 dekvloer → IfcOpeningElement #820778 merk A3sp — distance 0.034 — expliqué : absent du .ifcview

En plus (1) :

- IfcWall #421162 buitenblad → IfcWall #345024 buitenblad — distance 0.3 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original

## FreeSpace_triang

La règle d'origine FreeSpace échoue : `Bnd_Box is void`. FreeSpace_triang : 563 résultats en 0.11 s.
