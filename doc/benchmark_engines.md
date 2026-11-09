# Benchmark des moteurs IfcClash_Plus

- Source : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifc` (100 éléments retenus)
- Cible : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifc` (100 éléments retenus)
- .ifcview : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifcview`, `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifcview`
- Lecture des IFC par ifcopenshell (Python, une fois, hors temps des règles) : 0.17 s
- Limites : Python 600 s, C++ 600 s par exécution
- Paramètres : premier cas de parité de chaque règle (`tests/parity_cases.py`)

« Froid » : nouvelle Session (parse et conversion de la géométrie compris), le coût d'une règle seule. « Chaud » : la même règle relancée dans la même Session, le coût d'une règle de plus dans un RuleFile.

| Règle | Type | Résultats | Python | C++ froid | C++ chaud | .ifcview froid | .ifcview chaud | Gain C++ froid | Gain C++ chaud | Mêmes résultats |
|---|---|---|---|---|---|---|---|---|---|---|
| Volume | one | 200 | 3.50 s | 0.84 s | 2.5 ms | 0.85 s | 2.1 ms | ×4.2 | ×1406.6 | oui |
| Area | one | 200 | 3.46 s | 0.82 s | 1.9 ms | 0.82 s | 2.1 ms | ×4.2 | ×1859.1 | oui |
| TopOrBottomSurface | one | 173 | 7.67 s | 1.87 s | 0.89 s | 1.90 s | 0.90 s | ×4.1 | ×8.7 | oui |
| LateralSurface | one | 193 | 3.43 s | 1.03 s | 5.7 ms | 1.00 s | 6.0 ms | ×3.3 | ×601.9 | oui |
| ProjectedSurface | one | 174 | 3.86 s | 1.04 s | 0.05 s | 1.05 s | 0.05 s | ×3.7 | ×78.1 | oui |
| ObbHigh | one | 200 | 5.05 s | 1.31 s | 2.7 ms | 1.35 s | 3.4 ms | ×3.9 | ×1838.3 | oui |
| ObbLength | one | 200 | 5.06 s | 1.37 s | 2.5 ms | 1.39 s | 3.0 ms | ×3.7 | ×2009.5 | oui |
| Orientation | one | 0 | 5.09 s | 1.38 s | 5.5 ms | 1.35 s | 5.0 ms | ×3.7 | ×923.0 | oui |
| OneObjectFace | one | 22146 | 6.17 s | 1.50 s | 0.50 s | 1.53 s | 0.50 s | ×4.1 | ×12.2 | oui |
| Intersection | pair | 56 | 0.69 s | 0.88 s | 0.03 s | 0.47 s | 0.03 s | ×0.8 | ×27.5 | oui |
| Clearance | pair | 448 | 0.76 s | 0.90 s | 0.06 s | 0.89 s | 0.06 s | ×0.8 | ×12.7 | oui |
| Collision | pair | 32 | 0.69 s | 0.84 s | 3.9 ms | 0.45 s | 3.3 ms | ×0.8 | ×175.7 | oui |
| Intersection2 | pair | 66 | 4.79 s | 4.49 s | 3.79 s | 4.51 s | 3.69 s | ×1.1 | ×1.3 | oui |
| Above | pair | 99 | 67.39 s | 7.38 s | 0.83 s | 7.55 s | 0.82 s | ×9.1 | ×81.6 | oui |
| Below | pair | 77 | 66.93 s | 7.06 s | 0.48 s | 7.22 s | 0.48 s | ×9.5 | ×140.2 | oui |
| OBB_Above | pair | 163 | 5.42 s | 1.71 s | 0.30 s | 1.64 s | 0.28 s | ×3.2 | ×18.0 | oui |
| OBB_Below | pair | 114 | 5.26 s | 1.57 s | 0.19 s | 1.60 s | 0.20 s | ×3.4 | ×27.0 | oui |
| OBB_Front_And_Back | pair | 127 | 5.32 s | 1.68 s | 0.28 s | 1.70 s | 0.30 s | ×3.2 | ×18.7 | oui |
| OBB_Custom | pair | 293 | 5.92 s | 1.90 s | 0.51 s | 1.94 s | 0.51 s | ×3.1 | ×11.7 | oui |
| AngleBetween | pair | 4465 | 5.14 s | 1.49 s | 0.06 s | 1.40 s | 0.06 s | ×3.4 | ×79.4 | oui |
| ClearanceAxisToAxis | pair | n/a | > 600 s | > 600 s | > 600 s | > 600 s | > 600 s | n/a | n/a | non vérifié |
| TwoObjectsFace | pair | 8575 | 228.58 s | 6.91 s | 5.88 s | 6.94 s | 5.98 s | ×33.1 | ×38.9 | oui |
| SurfaceRecover | pair | 0 | 8.80 s | 3.29 s | 1.10 s | 3.37 s | 1.12 s | ×2.7 | ×8.0 | oui |
| ClearanceForDoors | pair | 332 | 214.79 s | 12.60 s | 10.41 s | 13.40 s | 10.41 s | ×17.0 | ×20.6 | oui |
| Ray_Check | pair_ctx | 268 | 363.89 s | 4.15 s | 2.58 s | 4.13 s | 2.60 s | ×87.8 | ×140.9 | oui |
| DirectView | pair_ctx | n/a | > 600 s | > 600 s | > 600 s | > 600 s | > 600 s | n/a | n/a | non vérifié |
| FreeSpace | one_ctx | 200 | 8.26 s | 4.21 s | 2.59 s | 4.17 s | 2.61 s | ×2.0 | ×3.2 | oui |
| Alignement | one | 62 | 3.77 s | 3.49 s | 4.3 ms | 3.51 s | 4.4 ms | ×1.1 | ×871.1 | oui |

Total sur les 26 règles où tous les moteurs ont fini : Python 1039.7 s, C++ froid 75.7 s, C++ chaud 30.6 s.

Écarts et erreurs :

- ClearanceAxisToAxis : non relancée après optimisation (limite atteinte avant, partie lente non modifiée)
- DirectView : non relancée après optimisation (limite atteinte avant, partie lente non modifiée)

Phases du moteur C++ (exécution froide) :

- Volume, IFC : `Volume   convert: 200 → 200   narrow: 200 → 200   (0.655 s)`
- Volume, .ifcview : `Volume   convert: 200 → 200   narrow: 200 → 200   (0.669 s)` — 187 of 200 boxes from the .ifcview
- Area, IFC : `Area   convert: 200 → 200   narrow: 200 → 200   (0.634 s)`
- Area, .ifcview : `Area   convert: 200 → 200   narrow: 200 → 200   (0.631 s)` — 187 of 200 boxes from the .ifcview
- TopOrBottomSurface, IFC : `TopOrBottomSurface   convert: 200 → 200   narrow: 200 → 173   (1.567 s)`
- TopOrBottomSurface, .ifcview : `TopOrBottomSurface   convert: 200 → 200   narrow: 200 → 173   (1.587 s)` — 0 of 0 boxes from the .ifcview
- LateralSurface, IFC : `LateralSurface   convert: 200 → 200   narrow: 200 → 193   (0.841 s)`
- LateralSurface, .ifcview : `LateralSurface   convert: 200 → 200   narrow: 200 → 193   (0.808 s)` — 0 of 0 boxes from the .ifcview
- ProjectedSurface, IFC : `ProjectedSurface   convert: 200 → 200   narrow: 200 → 174   (0.851 s)`
- ProjectedSurface, .ifcview : `ProjectedSurface   convert: 200 → 200   narrow: 200 → 174   (0.869 s)` — 0 of 0 boxes from the .ifcview
- ObbHigh, IFC : `ObbHigh   convert: 200 → 200   narrow: 200 → 200   (1.122 s)`
- ObbHigh, .ifcview : `ObbHigh   convert: 200 → 200   narrow: 200 → 200   (1.152 s)` — 0 of 0 boxes from the .ifcview
- ObbLength, IFC : `ObbLength   convert: 200 → 200   narrow: 200 → 200   (1.178 s)`
- ObbLength, .ifcview : `ObbLength   convert: 200 → 200   narrow: 200 → 200   (1.191 s)` — 0 of 0 boxes from the .ifcview
- Orientation, IFC : `Orientation   convert: 200 → 200   narrow: 200 → 0   (1.191 s)`
- Orientation, .ifcview : `Orientation   convert: 200 → 200   narrow: 200 → 0   (1.165 s)` — 0 of 0 boxes from the .ifcview
- OneObjectFace, IFC : `OneObjectFace   convert: 200 → 200   narrow: 200 → 22146   (0.862 s)`
- OneObjectFace, .ifcview : `OneObjectFace   convert: 200 → 200   narrow: 200 → 22146   (0.882 s)` — 0 of 0 boxes from the .ifcview
- Intersection, IFC : `Intersection   convert: 200 → 200   broad: 10000 → 116   mid: 116 → 116   narrow: 116 → 56   (0.679 s)`
- Intersection, .ifcview : `Intersection   convert: 200 → 200   broad: 10000 → 136   mid: 136 → 136   convert_narrow: 117 → 117   narrow: 136 → 56   (0.281 s)` — 187 of 200 boxes from the .ifcview
- Clearance, IFC : `Clearance   convert: 200 → 200   broad: 10000 → 497   mid: 497 → 496   narrow: 496 → 448   (0.713 s)`
- Clearance, .ifcview : `Clearance   convert: 200 → 200   broad: 10000 → 532   mid: 532 → 532   convert_narrow: 181 → 181   narrow: 532 → 448   (0.702 s)` — 187 of 200 boxes from the .ifcview
- Collision, IFC : `Collision   convert: 200 → 200   broad: 10000 → 116   mid: 116 → 116   narrow: 116 → 32   (0.651 s)`
- Collision, .ifcview : `Collision   convert: 200 → 200   broad: 10000 → 136   mid: 136 → 136   convert_narrow: 117 → 117   narrow: 136 → 32   (0.267 s)` — 187 of 200 boxes from the .ifcview
- Intersection2, IFC : `Intersection2   convert: 200 → 200   broad: 10000 → 115   mid: 115 → 96   narrow: 96 → 66   (4.260 s)`
- Intersection2, .ifcview : `Intersection2   convert: 200 → 200   broad: 10000 → 115   mid: 115 → 96   convert_narrow: 99 → 99   narrow: 96 → 66   (4.282 s)` — 0 of 0 boxes from the .ifcview
- Above, IFC : `Above   convert: 200 → 200   broad: 10000 → 169   mid: 169 → 167   narrow: 167 → 99   (7.191 s)`
- Above, .ifcview : `Above   convert: 200 → 200   broad: 10000 → 169   mid: 169 → 167   convert_narrow: 128 → 128   narrow: 167 → 99   (7.353 s)` — 0 of 0 boxes from the .ifcview
- Below, IFC : `Below   convert: 200 → 200   broad: 10000 → 122   mid: 122 → 120   narrow: 120 → 77   (6.880 s)`
- Below, .ifcview : `Below   convert: 200 → 200   broad: 10000 → 122   mid: 122 → 120   convert_narrow: 88 → 88   narrow: 120 → 77   (7.024 s)` — 0 of 0 boxes from the .ifcview
- OBB_Above, IFC : `OBB_Above   convert: 200 → 200   broad: 10000 → 169   mid: 169 → 169   narrow: 169 → 163   (1.512 s)`
- OBB_Above, .ifcview : `OBB_Above   convert: 200 → 200   broad: 10000 → 169   mid: 169 → 169   convert_narrow: 128 → 128   narrow: 169 → 163   (1.445 s)` — 0 of 0 boxes from the .ifcview
- OBB_Below, IFC : `OBB_Below   convert: 200 → 200   broad: 10000 → 122   mid: 122 → 122   narrow: 122 → 114   (1.383 s)`
- OBB_Below, .ifcview : `OBB_Below   convert: 200 → 200   broad: 10000 → 122   mid: 122 → 122   convert_narrow: 90 → 90   narrow: 122 → 114   (1.412 s)` — 0 of 0 boxes from the .ifcview
- OBB_Front_And_Back, IFC : `OBB_Front_And_Back   convert: 200 → 200   broad: 10000 → 174   mid: 174 → 174   narrow: 174 → 127   (1.492 s)`
- OBB_Front_And_Back, .ifcview : `OBB_Front_And_Back   convert: 200 → 200   broad: 10000 → 174   mid: 174 → 174   convert_narrow: 134 → 134   narrow: 174 → 127   (1.512 s)` — 0 of 0 boxes from the .ifcview
- OBB_Custom, IFC : `OBB_Custom   convert: 200 → 200   broad: 10000 → 250   mid: 250 → 250   narrow: 250 → 293   (1.706 s)`
- OBB_Custom, .ifcview : `OBB_Custom   convert: 200 → 200   broad: 10000 → 250   mid: 250 → 250   convert_narrow: 145 → 145   narrow: 250 → 293   (1.747 s)` — 0 of 0 boxes from the .ifcview
- AngleBetween, IFC : `AngleBetween   convert: 200 → 200   mid: 10000 → 10000   narrow: 10000 → 4465   (1.230 s)`
- AngleBetween, .ifcview : `AngleBetween   convert: 200 → 200   mid: 10000 → 10000   convert_narrow: 200 → 200   narrow: 10000 → 4465   (1.157 s)` — 0 of 0 boxes from the .ifcview
- TwoObjectsFace, IFC : `TwoObjectsFace   convert: 200 → 186   broad: 8613 → 169   mid: 169 → 169   narrow: 169 → 8575   (6.530 s)`
- TwoObjectsFace, .ifcview : `TwoObjectsFace   convert: 200 → 186   broad: 8613 → 169   mid: 169 → 169   convert_narrow: 120 → 120   narrow: 169 → 8575   (6.566 s)` — 0 of 0 boxes from the .ifcview
- SurfaceRecover, IFC : `SurfaceRecover   convert: 200 → 200   broad: 10000 → 159   mid: 159 → 159   narrow: 159 → 0   (3.093 s)`
- SurfaceRecover, .ifcview : `SurfaceRecover   convert: 200 → 200   broad: 10000 → 159   mid: 159 → 159   convert_narrow: 130 → 130   narrow: 159 → 0   (3.177 s)` — 0 of 0 boxes from the .ifcview
- ClearanceForDoors, IFC : `ClearanceForDoors   convert: 200 → 200   broad: 10000 → 391   mid: 391 → 391   narrow: 391 → 332   (12.357 s)`
- ClearanceForDoors, .ifcview : `ClearanceForDoors   convert: 200 → 200   broad: 10000 → 391   mid: 391 → 391   convert_narrow: 164 → 164   narrow: 391 → 332   (13.158 s)` — 187 of 200 boxes from the .ifcview
- Ray_Check, IFC : `Ray_Check   convert: 200 → 200   broad: 10000 → 4441   mid: 4441 → 4441   narrow: 4441 → 268   (3.205 s)`
- Ray_Check, .ifcview : `Ray_Check   convert: 200 → 200   broad: 10000 → 4441   mid: 4441 → 4441   convert_narrow: 200 → 200   narrow: 4441 → 268   (3.200 s)` — 0 of 0 boxes from the .ifcview
- FreeSpace, IFC : `FreeSpace   convert: 200 → 200   narrow: 200 → 200   (3.260 s)`
- FreeSpace, .ifcview : `FreeSpace   convert: 200 → 200   narrow: 200 → 200   (3.246 s)` — 0 of 0 boxes from the .ifcview
- Alignement, IFC : `Alignement   convert: 200 → 200   narrow: 200 → 62   (3.300 s)`
- Alignement, .ifcview : `Alignement   convert: 200 → 200   narrow: 200 → 62   (3.311 s)` — 0 of 0 boxes from the .ifcview
