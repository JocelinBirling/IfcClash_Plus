# Benchmark des moteurs IfcClash_Plus

- Source : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifc` (100 éléments retenus)
- Cible : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifc` (100 éléments retenus)
- .ifcview : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifcview`, `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifcview`
- Lecture des IFC par ifcopenshell (Python, une fois, hors temps des règles) : 0.15 s
- Limites : Python 600 s, C++ 600 s par exécution
- Paramètres : premier cas de parité de chaque règle (`tests/parity_cases.py`)

« Froid » : nouvelle Session (parse et conversion de la géométrie compris), le coût d'une règle seule. « Chaud » : la même règle relancée dans la même Session, le coût d'une règle de plus dans un RuleFile.

| Règle | Type | Résultats | Python | C++ froid | C++ chaud | .ifcview froid | .ifcview chaud | Gain C++ froid | Gain C++ chaud | Mêmes résultats |
|---|---|---|---|---|---|---|---|---|---|---|
| Volume | one | 200 | 3.20 s | 0.73 s | 1.4 ms | 0.74 s | 1.5 ms | ×4.4 | ×2242.1 | oui |
| Area | one | 200 | 3.24 s | 0.73 s | 1.4 ms | 0.76 s | 1.5 ms | ×4.4 | ×2244.8 | oui |
| TopOrBottomSurface | one | 173 | 7.54 s | 2.67 s | 1.71 s | 2.63 s | 1.73 s | ×2.8 | ×4.4 | oui |
| LateralSurface | one | 193 | 3.51 s | 1.01 s | 1.8 ms | 0.97 s | 1.8 ms | ×3.5 | ×1912.6 | oui |
| ProjectedSurface | one | 174 | 3.87 s | 1.15 s | 0.19 s | 1.19 s | 0.19 s | ×3.4 | ×20.7 | oui |
| ObbHigh | one | 200 | 5.06 s | 3.40 s | 2.73 s | 3.38 s | 2.66 s | ×1.5 | ×1.9 | oui |
| ObbLength | one | 200 | 5.11 s | 3.40 s | 2.66 s | 3.41 s | 2.66 s | ×1.5 | ×1.9 | oui |
| Orientation | one | 0 | 5.03 s | 3.42 s | 2.70 s | 3.40 s | 2.72 s | ×1.5 | ×1.9 | oui |
| OneObjectFace | one | 22146 | 6.16 s | 1.48 s | 0.50 s | 1.49 s | 0.49 s | ×4.2 | ×12.3 | oui |
| Intersection | pair | 56 | 0.68 s | 0.90 s | 0.03 s | 0.48 s | 0.02 s | ×0.8 | ×27.2 | oui |
| Clearance | pair | 448 | 0.81 s | 0.90 s | 0.05 s | 0.96 s | 0.06 s | ×0.9 | ×14.9 | oui |
| Collision | pair | 32 | 0.69 s | 0.86 s | 3.2 ms | 0.45 s | 2.8 ms | ×0.8 | ×215.9 | oui |
| Intersection2 | pair | 66 | 4.99 s | 5.17 s | 4.21 s | 4.99 s | 4.13 s | ×1.0 | ×1.2 | oui |
| Above | pair | 99 | 65.76 s | 54.45 s | 54.38 s | 54.89 s | 55.42 s | ×1.2 | ×1.2 | oui |
| Below | pair | 77 | 67.37 s | 55.00 s | 53.41 s | 54.03 s | 53.38 s | ×1.2 | ×1.3 | oui |
| OBB_Above | pair | 163 | 5.38 s | 3.64 s | 2.88 s | 3.60 s | 2.91 s | ×1.5 | ×1.9 | oui |
| OBB_Below | pair | 114 | 5.27 s | 3.60 s | 2.84 s | 3.53 s | 2.80 s | ×1.5 | ×1.9 | oui |
| OBB_Front_And_Back | pair | 127 | 5.32 s | 3.69 s | 2.93 s | 3.63 s | 2.90 s | ×1.4 | ×1.8 | oui |
| OBB_Custom | pair | 293 | 5.90 s | 4.12 s | 3.43 s | 4.13 s | 3.39 s | ×1.4 | ×1.7 | oui |
| AngleBetween | pair | 4465 | 5.16 s | 3.38 s | 2.64 s | 3.33 s | 2.63 s | ×1.5 | ×2.0 | oui |
| ClearanceAxisToAxis | pair | n/a | > 600 s | > 600 s | > 600 s | > 600 s | > 600 s | n/a | n/a | non vérifié |
| TwoObjectsFace | pair | 8575 | 225.93 s | 6.92 s | 5.94 s | 6.95 s | 5.92 s | ×32.6 | ×38.0 | oui |
| SurfaceRecover | pair | 0 | 8.69 s | 5.49 s | 3.90 s | 5.48 s | 3.87 s | ×1.6 | ×2.2 | oui |
| ClearanceForDoors | pair | 332 | 212.51 s | 12.01 s | 9.98 s | 12.94 s | 10.22 s | ×17.7 | ×21.3 | oui |
| Ray_Check | pair_ctx | 268 | 366.91 s | 4.21 s | 2.60 s | 4.18 s | 2.59 s | ×87.2 | ×141.1 | oui |
| DirectView | pair_ctx | n/a | > 600 s | > 600 s | > 600 s | > 600 s | > 600 s | n/a | n/a | non vérifié |
| FreeSpace | one_ctx | 200 | 8.21 s | 4.20 s | 2.58 s | 4.17 s | 2.62 s | ×2.0 | ×3.2 | oui |
| Alignement | one | 62 | 3.76 s | 3.49 s | 2.75 s | 3.51 s | 2.76 s | ×1.1 | ×1.4 | oui |

Total sur les 26 règles où tous les moteurs ont fini : Python 1036.1 s, C++ froid 190.0 s, C++ chaud 165.0 s.

Phases du moteur C++ (exécution froide) :

- Volume, IFC : `Volume   convert: 200 → 200   narrow: 200 → 200   (0.568 s)`
- Volume, .ifcview : `Volume   convert: 200 → 200   narrow: 200 → 200   (0.565 s)` — 187 of 200 boxes from the .ifcview
- Area, IFC : `Area   convert: 200 → 200   narrow: 200 → 200   (0.562 s)`
- Area, .ifcview : `Area   convert: 200 → 200   narrow: 200 → 200   (0.577 s)` — 187 of 200 boxes from the .ifcview
- TopOrBottomSurface, IFC : `TopOrBottomSurface   convert: 200 → 200   narrow: 200 → 173   (2.374 s)`
- TopOrBottomSurface, .ifcview : `TopOrBottomSurface   convert: 200 → 200   narrow: 200 → 173   (2.347 s)` — 0 of 0 boxes from the .ifcview
- LateralSurface, IFC : `LateralSurface   convert: 200 → 200   narrow: 200 → 193   (0.834 s)`
- LateralSurface, .ifcview : `LateralSurface   convert: 200 → 200   narrow: 200 → 193   (0.780 s)` — 0 of 0 boxes from the .ifcview
- ProjectedSurface, IFC : `ProjectedSurface   convert: 200 → 200   narrow: 200 → 174   (0.966 s)`
- ProjectedSurface, .ifcview : `ProjectedSurface   convert: 200 → 200   narrow: 200 → 174   (0.988 s)` — 0 of 0 boxes from the .ifcview
- ObbHigh, IFC : `ObbHigh   convert: 200 → 200   narrow: 200 → 200   (3.214 s)`
- ObbHigh, .ifcview : `ObbHigh   convert: 200 → 200   narrow: 200 → 200   (3.195 s)` — 0 of 0 boxes from the .ifcview
- ObbLength, IFC : `ObbLength   convert: 200 → 200   narrow: 200 → 200   (3.218 s)`
- ObbLength, .ifcview : `ObbLength   convert: 200 → 200   narrow: 200 → 200   (3.226 s)` — 0 of 0 boxes from the .ifcview
- Orientation, IFC : `Orientation   convert: 200 → 200   narrow: 200 → 0   (3.233 s)`
- Orientation, .ifcview : `Orientation   convert: 200 → 200   narrow: 200 → 0   (3.227 s)` — 0 of 0 boxes from the .ifcview
- OneObjectFace, IFC : `OneObjectFace   convert: 200 → 200   narrow: 200 → 22146   (0.846 s)`
- OneObjectFace, .ifcview : `OneObjectFace   convert: 200 → 200   narrow: 200 → 22146   (0.852 s)` — 0 of 0 boxes from the .ifcview
- Intersection, IFC : `Intersection   convert: 200 → 200   broad: 10000 → 116   mid: 116 → 116   narrow: 116 → 56   (0.703 s)`
- Intersection, .ifcview : `Intersection   convert: 200 → 200   broad: 10000 → 136   mid: 136 → 136   convert_narrow: 117 → 117   narrow: 136 → 56   (0.286 s)` — 187 of 200 boxes from the .ifcview
- Clearance, IFC : `Clearance   convert: 200 → 200   broad: 10000 → 497   mid: 497 → 496   narrow: 496 → 448   (0.713 s)`
- Clearance, .ifcview : `Clearance   convert: 200 → 200   broad: 10000 → 532   mid: 532 → 532   convert_narrow: 181 → 181   narrow: 532 → 448   (0.772 s)` — 187 of 200 boxes from the .ifcview
- Collision, IFC : `Collision   convert: 200 → 200   broad: 10000 → 116   mid: 116 → 116   narrow: 116 → 32   (0.676 s)`
- Collision, .ifcview : `Collision   convert: 200 → 200   broad: 10000 → 136   mid: 136 → 136   convert_narrow: 117 → 117   narrow: 136 → 32   (0.264 s)` — 187 of 200 boxes from the .ifcview
- Intersection2, IFC : `Intersection2   convert: 200 → 200   broad: 10000 → 115   mid: 115 → 96   narrow: 96 → 66   (4.915 s)`
- Intersection2, .ifcview : `Intersection2   convert: 200 → 200   broad: 10000 → 115   mid: 115 → 96   convert_narrow: 99 → 99   narrow: 96 → 66   (4.752 s)` — 0 of 0 boxes from the .ifcview
- Above, IFC : `Above   convert: 200 → 200   broad: 10000 → 169   mid: 169 → 167   narrow: 167 → 99   (54.174 s)`
- Above, .ifcview : `Above   convert: 200 → 200   broad: 10000 → 169   mid: 169 → 167   convert_narrow: 128 → 128   narrow: 167 → 99   (54.618 s)` — 0 of 0 boxes from the .ifcview
- Below, IFC : `Below   convert: 200 → 200   broad: 10000 → 122   mid: 122 → 120   narrow: 120 → 77   (54.762 s)`
- Below, .ifcview : `Below   convert: 200 → 200   broad: 10000 → 122   mid: 122 → 120   convert_narrow: 88 → 88   narrow: 120 → 77   (53.745 s)` — 0 of 0 boxes from the .ifcview
- OBB_Above, IFC : `OBB_Above   convert: 200 → 200   broad: 10000 → 169   mid: 169 → 169   narrow: 169 → 163   (3.395 s)`
- OBB_Above, .ifcview : `OBB_Above   convert: 200 → 200   broad: 10000 → 169   mid: 169 → 169   convert_narrow: 128 → 128   narrow: 169 → 163   (3.350 s)` — 0 of 0 boxes from the .ifcview
- OBB_Below, IFC : `OBB_Below   convert: 200 → 200   broad: 10000 → 122   mid: 122 → 122   narrow: 122 → 114   (3.296 s)`
- OBB_Below, .ifcview : `OBB_Below   convert: 200 → 200   broad: 10000 → 122   mid: 122 → 122   convert_narrow: 90 → 90   narrow: 122 → 114   (3.285 s)` — 0 of 0 boxes from the .ifcview
- OBB_Front_And_Back, IFC : `OBB_Front_And_Back   convert: 200 → 200   broad: 10000 → 174   mid: 174 → 174   narrow: 174 → 127   (3.391 s)`
- OBB_Front_And_Back, .ifcview : `OBB_Front_And_Back   convert: 200 → 200   broad: 10000 → 174   mid: 174 → 174   convert_narrow: 134 → 134   narrow: 174 → 127   (3.370 s)` — 0 of 0 boxes from the .ifcview
- OBB_Custom, IFC : `OBB_Custom   convert: 200 → 200   broad: 10000 → 250   mid: 250 → 250   narrow: 250 → 293   (3.851 s)`
- OBB_Custom, .ifcview : `OBB_Custom   convert: 200 → 200   broad: 10000 → 250   mid: 250 → 250   convert_narrow: 145 → 145   narrow: 250 → 293   (3.835 s)` — 0 of 0 boxes from the .ifcview
- AngleBetween, IFC : `AngleBetween   convert: 200 → 200   mid: 10000 → 10000   narrow: 10000 → 4465   (3.151 s)`
- AngleBetween, .ifcview : `AngleBetween   convert: 200 → 200   mid: 10000 → 10000   convert_narrow: 200 → 200   narrow: 10000 → 4465   (3.109 s)` — 0 of 0 boxes from the .ifcview
- TwoObjectsFace, IFC : `TwoObjectsFace   convert: 200 → 186   broad: 8613 → 169   mid: 169 → 169   narrow: 169 → 8575   (6.558 s)`
- TwoObjectsFace, .ifcview : `TwoObjectsFace   convert: 200 → 186   broad: 8613 → 169   mid: 169 → 169   convert_narrow: 120 → 120   narrow: 169 → 8575   (6.580 s)` — 0 of 0 boxes from the .ifcview
- SurfaceRecover, IFC : `SurfaceRecover   convert: 200 → 200   broad: 10000 → 159   mid: 159 → 159   narrow: 159 → 0   (5.223 s)`
- SurfaceRecover, .ifcview : `SurfaceRecover   convert: 200 → 200   broad: 10000 → 159   mid: 159 → 159   convert_narrow: 130 → 130   narrow: 159 → 0   (5.218 s)` — 0 of 0 boxes from the .ifcview
- ClearanceForDoors, IFC : `ClearanceForDoors   convert: 200 → 200   broad: 10000 → 391   mid: 391 → 391   narrow: 391 → 332   (11.799 s)`
- ClearanceForDoors, .ifcview : `ClearanceForDoors   convert: 200 → 200   broad: 10000 → 391   mid: 391 → 391   convert_narrow: 164 → 164   narrow: 391 → 332   (12.715 s)` — 187 of 200 boxes from the .ifcview
- Ray_Check, IFC : `Ray_Check   convert: 200 → 200   broad: 10000 → 4441   mid: 4441 → 4441   narrow: 4441 → 268   (3.271 s)`
- Ray_Check, .ifcview : `Ray_Check   convert: 200 → 200   broad: 10000 → 4441   mid: 4441 → 4441   convert_narrow: 200 → 200   narrow: 4441 → 268   (3.248 s)` — 0 of 0 boxes from the .ifcview
- FreeSpace, IFC : `FreeSpace   convert: 200 → 200   narrow: 200 → 200   (3.268 s)`
- FreeSpace, .ifcview : `FreeSpace   convert: 200 → 200   narrow: 200 → 200   (3.235 s)` — 0 of 0 boxes from the .ifcview
- Alignement, IFC : `Alignement   convert: 200 → 200   narrow: 200 → 62   (3.305 s)`
- Alignement, .ifcview : `Alignement   convert: 200 → 200   narrow: 200 → 62   (3.313 s)` — 0 of 0 boxes from the .ifcview
