# Benchmark des moteurs IfcClash_Plus

- Source : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifc` (286 éléments avec représentation)
- Cible : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifc` (524 éléments)
- .ifcview : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifcview`, `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifcview`
- Lecture des IFC par ifcopenshell (Python, une fois, hors temps des règles) : 0.15 s

| Règle | Résultats | Python | C++ froid | C++ chaud | C++ .ifcview froid | C++ .ifcview chaud | Gain C++ froid | Gain .ifcview froid | Mêmes paires |
|---|---|---|---|---|---|---|---|---|---|
| Volume | 810 | 14.84 s | 1.13 s | 0.00 s | 1.17 s | 0.00 s | ×13.1 | ×12.7 | oui |
| Intersection | 802 | 1.39 s | 1.60 s | 0.33 s | 1.52 s | 0.33 s | ×0.9 | ×0.9 | oui |
| Clearance | 1953 | 1.50 s | 1.31 s | 0.06 s | 1.33 s | 0.07 s | ×1.1 | ×1.1 | oui |
| Collision | 491 | 1.20 s | 1.30 s | 0.02 s | 1.24 s | 0.02 s | ×0.9 | ×1.0 | oui |

Phases du moteur C++ (exécution froide) :

- IFC : `Volume   narrow: 810 → 810   (0.998 s)`
- .ifcview : `Volume   narrow: 810 → 810   (1.014 s)` — 760 of 810 boxes from the .ifcview
- IFC : `Intersection   broad: 149864 → 1600   mid: 1600 → 1590   narrow: 1590 → 802   (1.396 s)`
- .ifcview : `Intersection   broad: 149864 → 1981   mid: 1981 → 1981   narrow: 1981 → 802   (1.359 s)` — 760 of 810 boxes from the .ifcview
- IFC : `Clearance   broad: 149864 → 2426   mid: 2426 → 2414   narrow: 2414 → 1953   (1.136 s)`
- .ifcview : `Clearance   broad: 149864 → 2657   mid: 2657 → 2657   narrow: 2657 → 1953   (1.164 s)` — 760 of 810 boxes from the .ifcview
- IFC : `Collision   broad: 149864 → 1600   mid: 1600 → 1590   narrow: 1590 → 491   (1.138 s)`
- .ifcview : `Collision   broad: 149864 → 1981   mid: 1981 → 1981   narrow: 1981 → 491   (1.076 s)` — 760 of 810 boxes from the .ifcview
