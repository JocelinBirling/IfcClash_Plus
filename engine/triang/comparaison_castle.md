# Règles _triang contre règles d'origine

- Source : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_SampleCastle.ifc` (300 éléments)
- Cible : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_SampleCastle.ifc` (300 éléments)
- .ifcview : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_SampleCastle.ifcview`
- Marge d'explication des écarts : 0.011 m (flèche .ifcview + flèche IFC)

« Froid » : ouverture d'une session (lecture de l'IFC, métadonnées du .ifcview) et première exécution (conversion IFC pour la règle d'origine, décodage du .ifcview pour la règle _triang). « Chaud » : la même règle relancée dans la session.

| Règle | Résultats origine | Résultats _triang | Communs | Manquants | En plus | Inexpliqués | Origine froid | Origine chaud | _triang froid | _triang chaud | Gain froid | Gain chaud |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Intersection_triang | 14 | 9 | 7 | 7 | 2 | 0 | 1.85 s | 0.01 s | 1.19 s | 0.01 s | ×1.6 | ×1.3 |
| Above_triang | **erreur** | 120 résultats en 0.09 s | | | | | | | | | | |
| OBB_Above_triang | **erreur** | 204 résultats en 0.07 s | | | | | | | | | | |

## Intersection_triang

Paramètres : `{'tolerance': 0.002}`.

- Phases _triang : `Intersection_triang   convert: 600 → 563   broad: 79236 → 215   mid: 215 → 214   convert_narrow: 306 → 306   narrow: 214 → 9   (0.019 s)`
- Phases origine : `Intersection   convert: 600 → 574   broad: 82369 → 223   mid: 223 → 206   narrow: 206 → 14   (0.871 s)`
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

## OBB_Above_triang

La règle d'origine OBB_Above échoue : `gp_Dir() - input vector has zero norm`. OBB_Above_triang : 204 résultats en 0.07 s.
