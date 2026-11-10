# Règles _triang contre règles d'origine
- Source : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifc` (286 éléments)
- Cible : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifc` (524 éléments)
- Triangles des règles _triang : `ifc`
- Marge d'explication des écarts : 0.011 m (flèche .ifcview + flèche IFC)

25 règles `_triang`, une par processus (`compare_triang.py --rules`, 4 à 8 threads, une à la fois). **0 écart(s) inexpliqué(s).** ClearanceForDoors et Intersection2 ne sont plus portées ; DirectView est comparée à part (`comparaison_directview.md`).

Temps de l'origine : sa première exécution, froide (ouverture de session et conversion IFC comprises), lue ensuite dans le cache du comparateur (`build/engine/triang_original_cache`) : les règles d'origine ne changent pas, elles ne sont plus relancées. Ces premières exécutions ont tourné avec 2, 4 ou 8 threads selon les passes : les gains sont des ordres de grandeur. `_triang` : froid = ouverture de session et première exécution, chaud = la règle relancée dans la session.

| Règle | Origine | _triang | Communs | Manquants | En plus | Inexpliqués | Origine froid | _triang froid | _triang chaud | Gain froid |
|---|---|---|---|---|---|---|---|---|---|---|
| Intersection_triang | 802 | 803 | 801 | 1 | 2 | 0 | 1.77 s | 6.11 s | 0.38 s | ×0.3 |
| Above_triang | 1359 | 1476 | 1356 | 3 | 120 | 0 | 46.66 s | 5.61 s | 0.08 s | ×8.3 |
| Below_triang | 967 | 1125 | 959 | 8 | 166 | 0 | 36.18 s | 5.55 s | 0.06 s | ×6.5 |
| OBB_Above_triang | 2259 | 2288 | 2259 | 0 | 29 | 0 | 8.60 s | 5.42 s | 0.06 s | ×1.6 |
| OBB_Below_triang | 1560 | 1578 | 1560 | 0 | 18 | 0 | 8.02 s | 5.03 s | 0.04 s | ×1.6 |
| OBB_Front_And_Back_triang | 1683 | 1741 | 1683 | 0 | 58 | 0 | 8.92 s | 5.00 s | 0.05 s | ×1.8 |
| OBB_Custom_triang | 3369 | 3369 | 3369 | 0 | 0 | 0 | 11.71 s | 5.05 s | 0.11 s | ×2.3 |
| AngleBetween_triang | 64784 | 64785 | 64767 | 17 | 18 | 0 | 6.10 s | 6.90 s | 1.07 s | ×0.9 |
| ObbHigh_triang | 810 | 810 | 810 | 0 | 0 | 0 | 5.15 s | 4.92 s | 0.01 s | ×1.0 |
| ObbLength_triang | 810 | 810 | 810 | 0 | 0 | 0 | 4.95 s | 4.91 s | 0.01 s | ×1.0 |
| Orientation_triang | 810 | 810 | 810 | 0 | 0 | 0 | 4.96 s | 4.97 s | 0.01 s | ×1.0 |
| Alignement_triang | 158 | 160 | 158 | 0 | 2 | 0 | 14.81 s | 5.43 s | 0.32 s | ×2.7 |
| Clearance_triang | 6244 | 6244 | 6244 | 0 | 0 | 0 | 1.97 s | 5.59 s | 0.64 s | ×0.4 |
| Collision_triang | 491 | 491 | 491 | 0 | 0 | 0 | 1.36 s | 4.97 s | 0.03 s | ×0.3 |
| Volume_triang | 810 | 810 | 810 | 0 | 0 | 0 | 1.26 s | 4.87 s | 0.01 s | ×0.3 |
| Area_triang | 810 | 810 | 810 | 0 | 0 | 0 | 1.28 s | 4.88 s | 0.01 s | ×0.3 |
| TopOrBottomSurface_triang | 704 | 808 | 704 | 0 | 104 | 0 | 6.09 s | 7.27 s | 2.41 s | ×0.8 |
| LateralSurface_triang | 792 | 810 | 792 | 0 | 18 | 0 | 3.54 s | 4.86 s | 0.01 s | ×0.7 |
| ProjectedSurface_triang | 706 | 810 | 706 | 0 | 104 | 0 | 3.70 s | 5.40 s | 0.61 s | ×0.7 |
| ClearanceAxisToAxis_triang | 157 | 157 | 157 | 0 | 0 | 0 | 75.85 s | 1.30 s | 0.13 s | ×58.3 |
| SurfaceRecover_triang | 58 | 64 | 57 | 1 | 7 | 0 | 37.44 s | 5.00 s | 0.08 s | ×7.5 |
| Ray_Check_triang | 539 | 539 | 539 | 0 | 0 | 0 | 37.82 s | 5.15 s | 0.29 s | ×7.3 |
| OneObjectFace_triang | 473 | 532 | 460 | 13 | 72 | 0 | 44.40 s | 52.95 s | 47.86 s | ×0.8 |
| TwoObjectsFace_triang | 1868 | 1756 | 1669 | 199 | 87 | 0 | 83.16 s | 73.90 s | 68.36 s | ×1.1 |
| FreeSpace_triang | 810 | 810 | 810 | 0 | 0 | 0 | 9.77 s | 4.88 s | 0.04 s | ×2.0 |

## Intersection_triang

Paramètres : `{'tolerance': 0.002}`.

- Phases _triang : `Intersection_triang   convert: 810 → 810   broad: 149864 → 1600   mid: 1600 → 1590   narrow: 1590 → 803   (5.924 s)`
- Phases origine : `Intersection   convert: 810 → 810   broad: 149864 → 1600   mid: 1600 → 1590   narrow: 1590 → 802   (1.589 s)`
- Écarts par cause : 2 maillage IFC ouvert, 1 pénétration ≤ tolérance + marge

Manquants (1) :

- IfcWallStandardCase #5903 Basic Wall:Interior - Partition (92mm Stud):144518 → IfcSpace #1635 A101 — distance 0.0 — expliqué : pénétration 0.0000 ≤ tolérance + marge

En plus (2) :

- IfcWallStandardCase #5903 Basic Wall:Interior - Partition (92mm Stud):144518 → IfcSpace #424 A201 — distance 0.124 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWallStandardCase #5903 Basic Wall:Interior - Partition (92mm Stud):144518 → IfcSpace #4367 A201 — distance 0.124 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration

## Above_triang

Paramètres : `{'above_type': 'Above_MaxToMin', 'tolerance': 1.0}`.

- Phases _triang : `Above_triang   convert: 810 → 810   broad: 149864 → 2395   mid: 2395 → 2377   narrow: 2377 → 1476   (5.382 s)`
- Phases origine : `Above   convert: 810 → 810   broad: 149864 → 2394   mid: 2394 → 2346   narrow: 2346 → 1359   (46.423 s)`
- Écarts par cause : 52 écart vertical au bord de [0, tolérance], 52 faux négatif de l'original : grille de rayons, 12 faux négatif de l'original, vérifié sur l'IFC, 5 seuils à ± marge, 2 faux positif de l'original

Manquants (3) :

- IfcSpace #3456 A105 → IfcSpace #424 A201 — distance 0.5192 — expliqué : faux positif de l'original : son test « ray » coupe une droite infinie (cible sous la source)
- IfcSpace #3586 B105 → IfcSpace #931 B201 — distance 0.5192 — expliqué : faux positif de l'original : son test « ray » coupe une droite infinie (cible sous la source)
- IfcSlab #21545 Floor:Finish Floor - Ceramic Tile:171261 → IfcSpace #2604 B104 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]

En plus (120) :

- IfcSpace #67 A102 → IfcFlowSegment #38151 Pipe Types:Mechanical Pipe:557527 — distance 0.0559 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.7 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #67 A102 → IfcFlowSegment #132471 Pipe Types:Mechanical Pipe:631911 — distance 0.0002 — expliqué : écart vertical 0.0002 au bord de [0, tolérance]
- IfcSpace #212 A103 → IfcFlowSegment #11485 Pipe Types:Mechanical Pipe:546131 — distance 0.1488 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #38151 Pipe Types:Mechanical Pipe:557527 — distance 0.0557 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.7 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #135882 Pipe Types:Mechanical Pipe:631996 — distance 0.1444 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #355 A104 → IfcFlowSegment #21037 Pipe Types:Mechanical Pipe:550018 — distance 0.1405 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.143 m au-dessus de la source en (6.23, -10.25)
- IfcSpace #355 A104 → IfcFlowSegment #21217 Pipe Types:Mechanical Pipe:550028 — distance 0.5896 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.590 m au-dessus de la source en (6.23, -9.86)
- IfcSpace #355 A104 → IfcFlowSegment #22034 Pipe Types:Mechanical Pipe:550077 — distance 0.5896 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.590 m au-dessus de la source en (6.23, -9.24)
- IfcSpace #514 A101 → IfcFlowSegment #128136 Pipe Types:Mechanical Pipe:631126 — distance 0.0002 — expliqué : écart vertical 0.0002 au bord de [0, tolérance]
- IfcSpace #514 A101 → IfcFlowSegment #135882 Pipe Types:Mechanical Pipe:631996 — distance 0.1478 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1627 B102 → IfcFlowSegment #8141 Pipe Types:Mechanical Pipe:540175 — distance 0.1429 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1627 B102 → IfcFlowSegment #143609 Pipe Types:Mechanical Pipe:633327 — distance 0.0001 — expliqué : écart vertical 0.0001 au bord de [0, tolérance]
- IfcSpace #1627 B102 → IfcFlowSegment #144732 Pipe Types:Mechanical Pipe:633360 — distance 0.0544 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1782 B103 → IfcFlowSegment #8141 Pipe Types:Mechanical Pipe:540175 — distance 0.1431 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1782 B103 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.053 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #46770 Pipe Types:Mechanical Pipe:557647 — distance 0.0506 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.053 m au-dessus de la source en (2.57, -7.55)
- IfcSpace #1928 B104 → IfcFlowSegment #46950 Pipe Types:Mechanical Pipe:557648 — distance 0.5896 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.590 m au-dessus de la source en (2.57, -7.91)
- IfcSpace #1928 B104 → IfcFlowSegment #47767 Pipe Types:Mechanical Pipe:557656 — distance 0.587 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.590 m au-dessus de la source en (2.57, -8.53)
- IfcSpace #2108 B101 → IfcFlowSegment #139518 Pipe Types:Mechanical Pipe:632681 — distance 0.0487 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2108 B101 → IfcFlowSegment #143609 Pipe Types:Mechanical Pipe:633327 — distance 0.0535 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4643 Basic Wall:Foundation - Concrete (417mm):140479 → IfcFlowSegment #42359 Pipe Types:Mechanical Pipe:557590 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4643 Basic Wall:Foundation - Concrete (417mm):140479 → IfcFlowSegment #42799 Pipe Types:Mechanical Pipe:557597 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4818 Basic Wall:Foundation - Concrete (417mm):140520 → IfcFlowSegment #43285 Pipe Types:Mechanical Pipe:557601 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4818 Basic Wall:Foundation - Concrete (417mm):140520 → IfcFlowSegment #43882 Pipe Types:Mechanical Pipe:557605 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4818 Basic Wall:Foundation - Concrete (417mm):140520 → IfcFlowSegment #148417 Pipe Types:Mechanical Pipe:649433 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4818 Basic Wall:Foundation - Concrete (417mm):140520 → IfcFlowSegment #149234 Pipe Types:Mechanical Pipe:649463 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4868 Basic Wall:Foundation - Concrete (417mm):140554 → IfcFlowSegment #15805 Pipe Types:Mechanical Pipe:547286 — distance 0.0006 — expliqué : écart vertical 0.0006 au bord de [0, tolérance]
- IfcWallStandardCase #4868 Basic Wall:Foundation - Concrete (417mm):140554 → IfcFlowSegment #16201 Pipe Types:Mechanical Pipe:547595 — distance 0.1158 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.2 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4918 Basic Wall:Foundation - Concrete (417mm):140602 → IfcFlowSegment #16429 Pipe Types:Mechanical Pipe:547742 — distance 0.1158 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.2 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4918 Basic Wall:Foundation - Concrete (417mm):140602 → IfcFlowSegment #16964 Pipe Types:Mechanical Pipe:547856 — distance 0.1158 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.2 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4918 Basic Wall:Foundation - Concrete (417mm):140602 → IfcFlowSegment #136525 Pipe Types:Mechanical Pipe:632423 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4918 Basic Wall:Foundation - Concrete (417mm):140602 → IfcFlowSegment #138339 Pipe Types:Mechanical Pipe:632454 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #44238 Pipe Types:Mechanical Pipe:557611 — distance 0.1158 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #139858 Pipe Types:Mechanical Pipe:632744 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #140710 Pipe Types:Mechanical Pipe:632815 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSlab #5267 Floor:127mm Slab on Grade:143106 → IfcFlowSegment #18358 Pipe Types:Mechanical Pipe:548047 — distance 0.1158 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.2 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSlab #5267 Floor:127mm Slab on Grade:143106 → IfcFlowSegment #127853 Pipe Types:Mechanical Pipe:631121 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.1 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSlab #5267 Floor:127mm Slab on Grade:143106 → IfcFlowSegment #128958 Pipe Types:Mechanical Pipe:631284 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.1 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #40138 Pipe Types:Mechanical Pipe:557563 — distance 0.0762 — expliqué : seuils à ± marge
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowSegment #12343 Pipe Types:Mechanical Pipe:546826 — distance 0.0692 — expliqué : seuils à ± marge
- ... 80 de plus

## Below_triang

Paramètres : `{'below_type': 'Below_MinToMax', 'tolerance': 1.0}`.

- Phases _triang : `Below_triang   convert: 810 → 810   broad: 149864 → 1701   mid: 1701 → 1681   narrow: 1681 → 1125   (5.339 s)`
- Phases origine : `Below   convert: 810 → 810   broad: 149864 → 1701   mid: 1701 → 1663   narrow: 1663 → 967   (35.976 s)`
- Écarts par cause : 149 faux négatif de l'original : grille de rayons, 17 écart vertical au bord de [0, tolérance], 6 faux positif de l'original, 1 seuils à ± marge, 1 faux négatif de l'original, vérifié sur l'IFC

Manquants (8) :

- IfcWallStandardCase #5731 Basic Wall:Interior - Partition (92mm Stud):143960 → IfcFlowSegment #37971 Pipe Types:Mechanical Pipe:557526 — distance 0.8963 — expliqué : faux positif de l'original : son test « ray » garde la distance des points les plus proches, l'écart vertical au point du rayon (2.457 m) dépasse la tolérance
- IfcWallStandardCase #5731 Basic Wall:Interior - Partition (92mm Stud):143960 → IfcFlowFitting #38792 M_Elbow - Generic:Standard:Standard:557546 — distance 0.9106 — expliqué : faux positif de l'original : son test « ray » garde la distance des points les plus proches, l'écart vertical au point du rayon (2.470 m) dépasse la tolérance
- IfcWallStandardCase #5992 Basic Wall:Interior - Partition (92mm Stud):144633 → IfcFlowSegment #7915 Pipe Types:Mechanical Pipe:540160 — distance 0.3572 — expliqué : faux positif de l'original : son test « ray » garde la distance des points les plus proches, l'écart vertical au point du rayon (2.367 m) dépasse la tolérance
- IfcWallStandardCase #5992 Basic Wall:Interior - Partition (92mm Stud):144633 → IfcFlowFitting #10911 M_Elbow - Generic:Standard:Standard:545367 — distance 0.373 — expliqué : faux positif de l'original : son test « ray » garde la distance des points les plus proches, l'écart vertical au point du rayon (2.380 m) dépasse la tolérance
- IfcDoor #15962 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734 → IfcFlowSegment #37971 Pipe Types:Mechanical Pipe:557526 — distance 0.8963 — expliqué : faux positif de l'original : son test « ray » garde la distance des points les plus proches, l'écart vertical au point du rayon (2.457 m) dépasse la tolérance
- IfcDoor #16013 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834 → IfcFlowSegment #7915 Pipe Types:Mechanical Pipe:540160 — distance 0.3572 — expliqué : faux positif de l'original : son test « ray » garde la distance des points les plus proches, l'écart vertical au point du rayon (2.367 m) dépasse la tolérance
- IfcCovering #23671 Compound Ceiling:Gypsum Board:187149 → IfcSpace #2462 B103 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcCovering #23992 Compound Ceiling:Gypsum Board:187508 → IfcSpace #1942 A103 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]

En plus (166) :

- IfcSpace #819 A201 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.4435 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1059 A204 → IfcFlowSegment #11485 Pipe Types:Mechanical Pipe:546131 — distance 0.3476 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1059 A204 → IfcFlowSegment #18179 Pipe Types:Mechanical Pipe:547956 — distance 0.3849 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.2 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1059 A204 → IfcFlowSegment #18358 Pipe Types:Mechanical Pipe:548047 — distance 0.3849 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.2 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1218 A203 → IfcFlowSegment #15213 Pipe Types:Mechanical Pipe:547247 — distance 0.0012 — expliqué : écart vertical 0.0012 au bord de [0, tolérance]
- IfcSpace #1218 A203 → IfcFlowSegment #15592 Pipe Types:Mechanical Pipe:547273 — distance 0.0012 — expliqué : écart vertical 0.0012 au bord de [0, tolérance]
- IfcSpace #1218 A203 → IfcFlowSegment #127853 Pipe Types:Mechanical Pipe:631121 — distance 0.3909 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.1 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1218 A203 → IfcFlowSegment #128136 Pipe Types:Mechanical Pipe:631126 — distance 0.3536 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1218 A203 → IfcFlowSegment #128958 Pipe Types:Mechanical Pipe:631284 — distance 0.3909 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.1 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1218 A203 → IfcFlowSegment #132471 Pipe Types:Mechanical Pipe:631911 — distance 0.3536 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1218 A203 → IfcFlowSegment #135882 Pipe Types:Mechanical Pipe:631996 — distance 0.3536 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1442 A202 → IfcFlowSegment #8141 Pipe Types:Mechanical Pipe:540175 — distance 0.3541 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2412 B201 → IfcFlowSegment #11485 Pipe Types:Mechanical Pipe:546131 — distance 0.3536 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2637 B204 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.4375 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2637 B204 → IfcFlowSegment #44059 Pipe Types:Mechanical Pipe:557609 — distance 0.4749 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2637 B204 → IfcFlowSegment #44238 Pipe Types:Mechanical Pipe:557611 — distance 0.4749 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2789 B203 → IfcFlowSegment #139518 Pipe Types:Mechanical Pipe:632681 — distance 0.4436 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2789 B203 → IfcFlowSegment #139858 Pipe Types:Mechanical Pipe:632744 — distance 0.4809 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2789 B203 → IfcFlowSegment #140710 Pipe Types:Mechanical Pipe:632815 — distance 0.4809 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2789 B203 → IfcFlowSegment #143609 Pipe Types:Mechanical Pipe:633327 — distance 0.4441 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2789 B203 → IfcFlowSegment #144732 Pipe Types:Mechanical Pipe:633360 — distance 0.4436 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #3013 B202 → IfcFlowSegment #38151 Pipe Types:Mechanical Pipe:557527 — distance 0.4435 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.7 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #3197 A205 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.4375 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #3325 B205 → IfcFlowSegment #11485 Pipe Types:Mechanical Pipe:546131 — distance 0.3476 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowSegment #11485 Pipe Types:Mechanical Pipe:546131 — distance 0.3346 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.4245 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowSegment #39016 Pipe Types:Mechanical Pipe:557550 — distance 0.4251 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowSegment #42359 Pipe Types:Mechanical Pipe:557590 — distance 0.4682 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowSegment #42799 Pipe Types:Mechanical Pipe:557597 — distance 0.4682 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowSegment #43524 Pipe Types:Mechanical Pipe:557603 — distance 0.4329 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowSegment #139518 Pipe Types:Mechanical Pipe:632681 — distance 0.4251 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowSegment #144732 Pipe Types:Mechanical Pipe:633360 — distance 0.4296 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #39256 Pipe Types:Mechanical Pipe:557552 — distance 0.4251 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.1 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.4245 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #43285 Pipe Types:Mechanical Pipe:557601 — distance 0.4682 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #43524 Pipe Types:Mechanical Pipe:557603 — distance 0.4245 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #43882 Pipe Types:Mechanical Pipe:557605 — distance 0.4682 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #49169 Pipe Types:Mechanical Pipe:577808 — distance 0.3346 — expliqué : faux négatif de l'original : sa grille de rayons (pas 9.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #50423 Pipe Types:Mechanical Pipe:577920 — distance 0.3429 — expliqué : seuils à ± marge
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #135882 Pipe Types:Mechanical Pipe:631996 — distance 0.3351 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- ... 126 de plus

## OBB_Above_triang

Paramètres : `{'tolerance': 1.0}`.

- Phases _triang : `OBB_Above_triang   convert: 810 → 810   broad: 149864 → 2395   mid: 2395 → 2377   narrow: 2377 → 2288   (5.197 s)`
- Phases origine : `OBB_Above   convert: 810 → 810   broad: 149864 → 2394   mid: 2394 → 2394   narrow: 2394 → 2259   (8.389 s)`
- Écarts par cause : 29 seuils à ± marge

En plus (29) :

- IfcSpace #1059 A204 → IfcSpace #1308 A204 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1059 A204 → IfcSpace #4134 A204 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1218 A203 → IfcSpace #70 A203 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1218 A203 → IfcSpace #424 A201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1218 A203 → IfcSpace #4367 A201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1218 A203 → IfcSpace #4491 A203 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1442 A202 → IfcSpace #424 A201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1442 A202 → IfcSpace #581 A202 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1442 A202 → IfcSpace #3677 A202 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1442 A202 → IfcSpace #4367 A201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2637 B204 → IfcSpace #1080 B204 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2637 B204 → IfcSpace #3961 B204 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2789 B203 → IfcSpace #730 B203 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2789 B203 → IfcSpace #931 B201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2789 B203 → IfcSpace #3553 B203 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2789 B203 → IfcSpace #3845 B201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #3013 B202 → IfcSpace #223 B202 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #3013 B202 → IfcSpace #931 B201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #3013 B202 → IfcSpace #3845 B201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #3013 B202 → IfcSpace #4614 B202 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #3197 A205 → IfcSpace #1422 A205 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #3197 A205 → IfcSpace #4226 A205 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #3325 B205 → IfcSpace #1194 B205 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #3325 B205 → IfcSpace #4053 B205 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #3456 A105 → IfcSpace #4367 A201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #3586 B105 → IfcSpace #3845 B201 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4219 Basic Wall:Interior - Partition (92mm Stud):139143 → IfcSpace #2604 B104 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #24596 Basic Wall:Interior - Furring (152 mm Stud):189074 → IfcSpace #2604 B104 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #24723 Basic Wall:Interior - Partition (92mm Stud):190140 → IfcSpace #2604 B104 — distance 0.0 — expliqué : seuils à ± marge

## OBB_Below_triang

Paramètres : `{'tolerance': 1.0}`.

- Phases _triang : `OBB_Below_triang   convert: 810 → 810   broad: 149864 → 1701   mid: 1701 → 1681   narrow: 1681 → 1578   (4.836 s)`
- Phases origine : `OBB_Below   convert: 810 → 810   broad: 149864 → 1701   mid: 1701 → 1701   narrow: 1701 → 1560   (7.831 s)`
- Écarts par cause : 18 seuils à ± marge

En plus (18) :

- IfcSpace #514 A101 → IfcEnergyConversionDevice #7747 M_Radiator - Hosted:25:25:538847 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #514 A101 → IfcEnergyConversionDevice #19618 M_Radiator - Hosted:25:25:548240 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1218 A203 → IfcEnergyConversionDevice #6651 M_Radiator - Hosted:25:25:535063 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1928 B104 → IfcSpace #2604 B104 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2108 B101 → IfcEnergyConversionDevice #45498 M_Radiator - Hosted:25:25:557620 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #3013 B202 → IfcEnergyConversionDevice #37761 M_Radiator - Hosted:25:25:557522 — distance 0.0 — expliqué : seuils à ± marge
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 → IfcSpace #4722 A/B — distance 0.0 — expliqué : seuils à ± marge
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 → IfcSpace #4799 A/B — distance 0.0 — expliqué : seuils à ± marge
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 → IfcSpace #4722 A/B — distance 0.0 — expliqué : seuils à ± marge
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 → IfcSpace #4799 A/B — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #36497 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206283 → IfcSpace #730 B203 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #36497 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206283 → IfcSpace #3553 B203 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #36526 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206502 → IfcSpace #581 A202 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #36526 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206502 → IfcSpace #3677 A202 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #36555 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206675 → IfcSpace #223 B202 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #36555 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206675 → IfcSpace #4614 B202 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #36584 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206876 → IfcSpace #70 A203 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #36584 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206876 → IfcSpace #4491 A203 — distance 0.0 — expliqué : seuils à ± marge

## OBB_Front_And_Back_triang

Paramètres : `{'tolerance': 0.5, 'direction_method': 'Wide'}`.

- Phases _triang : `OBB_Front_And_Back_triang   convert: 810 → 810   broad: 149864 → 2376   mid: 2376 → 2376   narrow: 2376 → 2026   (4.798 s)`
- Phases origine : `OBB_Front_And_Back   convert: 810 → 810   broad: 149864 → 2369   mid: 2369 → 2369   narrow: 2369 → 1888   (8.718 s)`
- Écarts par cause : 58 seuils à ± marge

En plus (58) :

- IfcSpace #514 A101 → IfcEnergyConversionDevice #127046 M_Radiator - Hosted:25:25:629670 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1218 A203 → IfcEnergyConversionDevice #6651 M_Radiator - Hosted:25:25:535063 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1218 A203 → IfcEnergyConversionDevice #131877 M_Radiator - Hosted:25:25:631726 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1442 A202 → IfcSpace #424 A201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1442 A202 → IfcSpace #4367 A201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1442 A202 → IfcEnergyConversionDevice #7704 M_Radiator - Hosted:25:25:538562 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1782 B103 → IfcSpace #2462 B103 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1782 B103 → IfcSpace #2959 B103 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1928 B104 → IfcEnergyConversionDevice #45498 M_Radiator - Hosted:25:25:557620 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2412 B201 → IfcEnergyConversionDevice #37676 M_Radiator - Hosted:25:25:557519 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2637 B204 → IfcSpace #1080 B204 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2637 B204 → IfcSpace #3961 B204 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2789 B203 → IfcEnergyConversionDevice #37633 M_Radiator - Hosted:25:25:557517 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2789 B203 → IfcEnergyConversionDevice #143417 M_Radiator - Hosted:25:25:633263 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcSpace #931 B201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcSpace #3845 B201 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #14394 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984 → IfcFlowFitting #53744 M_Transition - Generic:Standard:Standard:578414 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #14394 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984 → IfcFlowFitting #57217 M_Transition - Generic:Standard:Standard:578599 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #16802 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490 → IfcSpace #1942 A103 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #16802 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490 → IfcSpace #3276 A103 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #20958 Floor:Finish Floor - Wood:169308 → IfcSpace #424 A201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #20958 Floor:Finish Floor - Wood:169308 → IfcSpace #1635 A101 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #20958 Floor:Finish Floor - Wood:169308 → IfcSpace #4367 A201 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #20958 Floor:Finish Floor - Wood:169308 → IfcEnergyConversionDevice #6651 M_Radiator - Hosted:25:25:535063 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21195 Floor:Finish Floor - Ceramic Tile:169772 → IfcSpace #1080 B204 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21195 Floor:Finish Floor - Ceramic Tile:169772 → IfcSpace #1194 B205 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21195 Floor:Finish Floor - Ceramic Tile:169772 → IfcSpace #3961 B204 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21195 Floor:Finish Floor - Ceramic Tile:169772 → IfcSpace #4053 B205 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21401 Floor:Finish Floor - Wood:170352 → IfcSpace #1635 A101 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21497 Floor:Finish Floor - Ceramic Tile:171230 → IfcSpace #3454 A104 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21545 Floor:Finish Floor - Ceramic Tile:171261 → IfcSpace #2604 B104 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21610 Floor:Finish Floor - Wood:171292 → IfcSpace #2747 B101 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21610 Floor:Finish Floor - Wood:171292 → IfcSpace #3154 A101 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #22492 Basic Roof:Live Roof over Wood Joist Flat Roof:184483 → IfcSpace #4722 A/B — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #22492 Basic Roof:Live Roof over Wood Joist Flat Roof:184483 → IfcSpace #4799 A/B — distance 0.0 — expliqué : seuils à ± marge
- IfcCovering #23671 Compound Ceiling:Gypsum Board:187149 → IfcSpace #2329 B102 — distance 0.0 — expliqué : seuils à ± marge
- IfcCovering #23671 Compound Ceiling:Gypsum Board:187149 → IfcSpace #2462 B103 — distance 0.0 — expliqué : seuils à ± marge
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcSpace #2604 B104 — distance 0.0 — expliqué : seuils à ± marge
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcSpace #2604 B104 — distance 0.0 — expliqué : seuils à ± marge
- IfcCovering #23992 Compound Ceiling:Gypsum Board:187508 → IfcSpace #1942 A103 — distance 0.0 — expliqué : seuils à ± marge
- ... 18 de plus

## OBB_Custom_triang

Paramètres : `{'list_of_modifications': ['detach_top_by_extrude:0.5', 'NEW_OBB', 'extend_down:50%']}`.

- Phases _triang : `OBB_Custom_triang   convert: 810 → 810   broad: 149864 → 3531   mid: 3531 → 3531   narrow: 3531 → 4085   (4.788 s)`
- Phases origine : `OBB_Custom   convert: 810 → 810   broad: 149864 → 3529   mid: 3529 → 3529   narrow: 3529 → 4056   (11.443 s)`

## AngleBetween_triang

Paramètres : `{'direction_method_for_source': 'Wide', 'direction_method_for_target': 'Wide', 'angle_difference': 90.0, 'angle_tolerance': 5.0}`.

- Phases _triang : `AngleBetween_triang   convert: 810 → 810   mid: 149864 → 149864   narrow: 149864 → 64785   (5.740 s)`
- Phases origine : `AngleBetween   convert: 810 → 810   mid: 149864 → 149864   narrow: 149864 → 64784   (4.930 s)`
- Écarts par cause : 35 OBB optimale non unique

Manquants (17) :

- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #21445 Pipe Types:Mechanical Pipe:550036 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #45846 Pipe Types:Mechanical Pipe:557623 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #52650 Pipe Types:Mechanical Pipe:578230 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #57060 Pipe Types:Mechanical Pipe:578532 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #99262 Pipe Types:Mechanical Pipe:600584 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #109267 Pipe Types:Mechanical Pipe:601142 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #111851 Pipe Types:Mechanical Pipe:601282 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #113558 Pipe Types:Mechanical Pipe:601377 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #127683 Pipe Types:Mechanical Pipe:631112 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #140325 Pipe Types:Mechanical Pipe:632764 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #11125 Pipe Types:Mechanical Pipe:545888 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #18946 Pipe Types:Mechanical Pipe:548116 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #20628 Pipe Types:Mechanical Pipe:549955 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #41773 Pipe Types:Mechanical Pipe:557576 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #103337 Pipe Types:Mechanical Pipe:600913 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #129424 Pipe Types:Mechanical Pipe:631334 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change

En plus (18) :

- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #11125 Pipe Types:Mechanical Pipe:545888 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #18946 Pipe Types:Mechanical Pipe:548116 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #20628 Pipe Types:Mechanical Pipe:549955 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #41773 Pipe Types:Mechanical Pipe:557576 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #42799 Pipe Types:Mechanical Pipe:557597 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #103337 Pipe Types:Mechanical Pipe:600913 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #129424 Pipe Types:Mechanical Pipe:631334 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #21445 Pipe Types:Mechanical Pipe:550036 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #45846 Pipe Types:Mechanical Pipe:557623 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #52650 Pipe Types:Mechanical Pipe:578230 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #57060 Pipe Types:Mechanical Pipe:578532 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #99262 Pipe Types:Mechanical Pipe:600584 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #109267 Pipe Types:Mechanical Pipe:601142 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #111851 Pipe Types:Mechanical Pipe:601282 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #113558 Pipe Types:Mechanical Pipe:601377 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #127683 Pipe Types:Mechanical Pipe:631112 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #140325 Pipe Types:Mechanical Pipe:632764 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change

## ObbHigh_triang

Paramètres : `{'length_min': 0.0, 'length_max': 1000000000.0}`.

- Phases _triang : `ObbHigh_triang   convert: 810 → 810   narrow: 810 → 810   (4.751 s)`
- Phases origine : `ObbHigh   convert: 810 → 810   narrow: 810 → 810   (4.989 s)`
- Mesures comparées sur 810 éléments communs : 0 écart(s) au-delà de 0.011 m

## ObbLength_triang

Paramètres : `{'length_min': 0.0, 'length_max': 1000000000.0, 'direction_method': 'Narrow'}`.

- Phases _triang : `ObbLength_triang   convert: 810 → 810   narrow: 810 → 810   (4.747 s)`
- Phases origine : `ObbLength   convert: 810 → 810   narrow: 810 → 810   (4.785 s)`
- Mesures comparées sur 810 éléments communs : 0 écart(s) au-delà de 0.011 m

## Orientation_triang

Paramètres : `{'orientation': [0.0, 0.0, 1.0], 'orientation_type': 'Perpendicular', 'direction_method': 'Wide', 'angular_tolerance': 0.1}`.

- Phases _triang : `Orientation_triang   convert: 810 → 810   narrow: 810 → 810   (4.802 s)`
- Phases origine : `Orientation   convert: 810 → 810   narrow: 810 → 810   (4.802 s)`
- Mesures comparées sur 810 éléments communs : 100 écart(s) au-delà de 1.0°
- Écarts par cause : 59 même axe, sens opposé, 41 OBB optimale non unique

Mesures (100) :

- IfcFlowSegment #8322 Pipe Types:Mechanical Pipe:540182 — écart -60.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #11125 Pipe Types:Mechanical Pipe:545888 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #11665 Pipe Types:Mechanical Pipe:546374 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #11893 Pipe Types:Mechanical Pipe:546381 — écart -45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #12522 Pipe Types:Mechanical Pipe:546828 — écart -15.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #13824 Pipe Types:Mechanical Pipe:546906 — écart 60.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #14185 Pipe Types:Mechanical Pipe:547114 — écart 30.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #14546 Pipe Types:Mechanical Pipe:547146 — écart 15.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #14823 Pipe Types:Mechanical Pipe:547150 — écart 15.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #15003 Pipe Types:Mechanical Pipe:547183 — écart 60.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #16606 Pipe Types:Mechanical Pipe:547784 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #16786 Pipe Types:Mechanical Pipe:547802 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #18537 Pipe Types:Mechanical Pipe:548082 — écart 15.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #18766 Pipe Types:Mechanical Pipe:548089 — écart 15.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #18946 Pipe Types:Mechanical Pipe:548116 — écart -45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #19786 Pipe Types:Mechanical Pipe:548835 — écart 30.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #19966 Pipe Types:Mechanical Pipe:549038 — écart -60.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #20857 Pipe Types:Mechanical Pipe:549960 — écart 15.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #21037 Pipe Types:Mechanical Pipe:550018 — écart -15.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #21217 Pipe Types:Mechanical Pipe:550028 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #21445 Pipe Types:Mechanical Pipe:550036 — écart -45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #21674 Pipe Types:Mechanical Pipe:550041 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #36993 Pipe Types:Mechanical Pipe:554580 — écart 60.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #37173 Pipe Types:Mechanical Pipe:554945 — écart -45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #37354 Pipe Types:Mechanical Pipe:555449 — écart -45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #37532 Pipe Types:Mechanical Pipe:555856 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #38151 Pipe Types:Mechanical Pipe:557527 — écart -45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #38332 Pipe Types:Mechanical Pipe:557528 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #39016 Pipe Types:Mechanical Pipe:557550 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #39256 Pipe Types:Mechanical Pipe:557552 — écart -45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — écart 15.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #39664 Pipe Types:Mechanical Pipe:557555 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #40317 Pipe Types:Mechanical Pipe:557564 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #40594 Pipe Types:Mechanical Pipe:557567 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #40774 Pipe Types:Mechanical Pipe:557568 — écart -45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #41953 Pipe Types:Mechanical Pipe:557586 — écart 30.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #43524 Pipe Types:Mechanical Pipe:557603 — écart -45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #43704 Pipe Types:Mechanical Pipe:557604 — écart 45.0 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #44417 Pipe Types:Mechanical Pipe:557612 — écart 60.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #44646 Pipe Types:Mechanical Pipe:557614 — écart 15.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- ... 60 de plus

## Alignement_triang

Paramètres : `{'axis': None, 'alignment_type': 'Plane', 'tolerance': 0.05, 'min_group': 3}`.

- Phases _triang : `Alignement_triang   convert: 810 → 810   narrow: 810 → 160   (5.272 s)`
- Phases origine : `Alignement   convert: 810 → 810   narrow: 810 → 158   (14.652 s)`
- Écarts par cause : 2 OBB optimale non unique

En plus (2) :

- IfcFlowSegment #36635 Pipe Types:Mechanical Pipe:554197 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowSegment #45055 Pipe Types:Mechanical Pipe:557617 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change

## Clearance_triang

Paramètres : `{'clearance': 0.5, 'check_all': True}`.

- Phases _triang : `Clearance_triang   convert: 810 → 810   broad: 149864 → 6835   mid: 6835 → 6803   narrow: 6803 → 6244   (5.372 s)`
- Phases origine : `Clearance   convert: 810 → 810   broad: 149864 → 6835   mid: 6835 → 6803   narrow: 6803 → 6244   (1.765 s)`

## Collision_triang

Paramètres : `{'allow_touching': False}`.

- Phases _triang : `Collision_triang   convert: 810 → 810   broad: 149864 → 1600   mid: 1600 → 1590   narrow: 1590 → 491   (4.808 s)`
- Phases origine : `Collision   convert: 810 → 810   broad: 149864 → 1600   mid: 1600 → 1590   narrow: 1590 → 491   (1.200 s)`

## Volume_triang

Paramètres : `{'volume_min': 0.0, 'volume_max': 1000000000.0}`.

- Phases _triang : `Volume_triang   convert: 810 → 810   narrow: 810 → 810   (4.710 s)`
- Phases origine : `Volume   convert: 810 → 810   narrow: 810 → 810   (1.099 s)`
- Mesures comparées sur 810 éléments communs : 81 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 81 maillage IFC ouvert

Mesures (81) :

- IfcSpace #819 A201 — écart 17.3941 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcSpace #2412 B201 — écart 5.9864 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 — écart 23.7469 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcRailing #12184 Railing:1100mm Guard Rail:151166 — écart -2.2324 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #15463 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159159 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #15856 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159262 — écart -0.2381 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16149 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160671 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16175 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160717 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16485 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162230 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16563 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162311 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16589 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162357 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16615 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162383 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16641 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162486 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16667 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162487 — écart -0.2381 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16693 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162488 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16719 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162489 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16914 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162493 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16971 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162495 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16997 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162496 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #17023 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162497 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #19275 M_Bed-Standard:1525 x 2007mm - Queen:1525 x 2007mm - Queen:168449 — écart 0.4712 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #20657 M_Bed-Standard:1981 x 2032mm - King:1981 x 2032mm - King:168717 — écart 0.611 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #20726 M_Bed-Standard:1981 x 2032mm - King:1981 x 2032mm - King:168914 — écart 0.611 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #20755 M_Bed-Standard:1525 x 2007mm - Queen:1525 x 2007mm - Queen:169008 — écart 0.4712 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 — écart -4.5447 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 — écart -4.5447 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #23671 Compound Ceiling:Gypsum Board:187149 — écart -0.8384 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 — écart -6.1586 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 — écart -6.1586 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #23884 Compound Ceiling:Gypsum Board:187483 — écart -6.6981 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #23992 Compound Ceiling:Gypsum Board:187508 — écart -4.7294 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #24060 Compound Ceiling:Gypsum Board:187639 — écart -38.4089 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #24128 Compound Ceiling:Gypsum Board:187649 — écart -0.3312 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #24186 Compound Ceiling:Gypsum Board:187659 — écart -12.8308 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #24268 Compound Ceiling:Gypsum Board:187667 — écart -18.5083 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #24326 Compound Ceiling:Gypsum Board:187675 — écart -12.4916 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #24408 Compound Ceiling:Gypsum Board:187683 — écart -17.1899 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #24476 Compound Ceiling:Gypsum Board:187691 — écart -0.9159 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #24544 Compound Ceiling:Gypsum Board:187701 — écart -40.9301 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #26941 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191401 — écart -0.0682 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- ... 41 de plus

## Area_triang

Paramètres : `{'volume_min': 0.0, 'volume_max': 1000000000.0}`.

- Phases _triang : `Area_triang   convert: 810 → 810   narrow: 810 → 810   (4.719 s)`
- Phases origine : `Area   convert: 810 → 810   narrow: 810 → 810   (1.116 s)`
- Mesures comparées sur 810 éléments communs : 0 écart(s) au-delà de 2 % (au moins 0.011)

## TopOrBottomSurface_triang

Paramètres : `{'surface_min': 0.0, 'surface_max': 1000000000.0, 'top_or_bot_method': 'Top'}`.

- Phases _triang : `TopOrBottomSurface_triang   convert: 810 → 810   narrow: 810 → 808   (6.595 s)`
- Phases origine : `TopOrBottomSurface   convert: 810 → 810   narrow: 810 → 704   (5.134 s)`
- Mesures comparées sur 704 éléments communs : 42 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 126 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 20 maillage _triang non fermé une fois réparé

En plus (104) :

- IfcSpace #819 A201 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcSpace #2412 B201 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #15463 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159159 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #15856 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159262 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16149 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160671 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16175 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160717 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16485 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162230 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16563 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162311 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16589 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162357 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16615 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162383 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16641 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162486 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16667 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162487 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16693 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162488 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16719 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162489 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16914 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162493 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16971 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162495 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16997 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162496 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #17023 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162497 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #23884 Compound Ceiling:Gypsum Board:187483 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #24060 Compound Ceiling:Gypsum Board:187639 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #24186 Compound Ceiling:Gypsum Board:187659 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #24268 Compound Ceiling:Gypsum Board:187667 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #24326 Compound Ceiling:Gypsum Board:187675 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #24408 Compound Ceiling:Gypsum Board:187683 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #24544 Compound Ceiling:Gypsum Board:187701 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #35783 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:204934 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #35854 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205239 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #36125 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205264 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #36151 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205265 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #36423 M_Vanity Cabinet-Double Door Sink Unit:450 x 450 mm:450 x 450 mm:205548 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcSpace #424 A201 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcSpace #931 B201 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcSpace #1635 A101 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcSpace #2158 B101 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcSpace #3845 B201 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- ... 64 de plus

Mesures (42) :

- IfcRailing #12184 Railing:1100mm Guard Rail:151166 — écart -0.046 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #17341 M_Sofa:1830mm:1830mm:167283 — écart 1.1931 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #17409 M_Sofa:1830mm:1830mm:167426 — écart 1.1931 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #17786 M_Sofa:1830mm:1830mm:168377 — écart 1.1931 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #17815 M_Sofa:1830mm:1830mm:168378 — écart 1.1931 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #19275 M_Bed-Standard:1525 x 2007mm - Queen:1525 x 2007mm - Queen:168449 — écart 3.4087 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20657 M_Bed-Standard:1981 x 2032mm - King:1981 x 2032mm - King:168717 — écart 4.4892 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20726 M_Bed-Standard:1981 x 2032mm - King:1981 x 2032mm - King:168914 — écart 4.4892 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20755 M_Bed-Standard:1525 x 2007mm - Queen:1525 x 2007mm - Queen:169008 — écart 3.4087 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #26941 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191401 — écart 0.3304 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #29098 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191557 — écart 0.3304 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #29127 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191680 — écart 0.3304 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31241 M_Upper Cabinet-Double Door-Wall:1000mm:1000mm:191768 — écart 0.3304 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31313 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192153 — écart 0.3304 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31342 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192331 — écart 0.3304 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31371 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192508 — écart 0.3304 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31400 M_Upper Cabinet-Double Door-Wall:1000mm:1000mm:192610 — écart 0.3304 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcRailing #35163 Railing:1100mm Guard Rail:198972 — écart -0.0599 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcEnergyConversionDevice #6246 M_Hot Water Boiler - 59-440 kW:147 kW:147 kW:530072 — écart 0.2425 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #6651 M_Radiator - Hosted:25:25:535063 — écart 0.2365 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7034 M_Radiator - Hosted:25:25:536357 — écart 0.2061 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7369 M_Radiator - Hosted:25:25:536919 — écart 0.279 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7704 M_Radiator - Hosted:25:25:538562 — écart 0.4511 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7747 M_Radiator - Hosted:25:25:538847 — écart 0.2061 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #19618 M_Radiator - Hosted:25:25:548240 — écart 0.1049 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #20313 M_Radiator - Hosted:25:25:549304 — écart 0.1049 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37587 M_Hot Water Boiler - 59-440 kW:147 kW:147 kW:557516 — écart 0.2425 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37633 M_Radiator - Hosted:25:25:557517 — écart 0.2365 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37676 M_Radiator - Hosted:25:25:557519 — écart 0.2061 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37718 M_Radiator - Hosted:25:25:557520 — écart 0.279 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37761 M_Radiator - Hosted:25:25:557522 — écart 0.4511 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37804 M_Radiator - Hosted:25:25:557524 — écart 0.2061 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #45498 M_Radiator - Hosted:25:25:557620 — écart 0.1049 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #46193 M_Radiator - Hosted:25:25:557628 — écart 0.1049 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFlowMovingDevice #115421 M_Centrifugal Fan -  Rooftop  - Upblast:991-1905 LPS:991-1905 LPS:602113 — écart 0.042 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowMovingDevice #115533 M_Centrifugal Fan -  Rooftop  - Upblast:991-1905 LPS:991-1905 LPS:602396 — écart 0.042 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcEnergyConversionDevice #127046 M_Radiator - Hosted:25:25:629670 — écart 0.2061 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #127088 M_Radiator - Hosted:25:25:630326 — écart 0.279 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #131877 M_Radiator - Hosted:25:25:631726 — écart 0.2365 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #136014 M_Radiator - Hosted:25:25:632215 — écart 0.2061 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- ... 2 de plus

## LateralSurface_triang

Paramètres : `{'surface_min': 0.0, 'surface_max': 1000000000.0, 'direction': [0.0, 1.0, 0.0]}`.

- Phases _triang : `LateralSurface_triang   convert: 810 → 810   narrow: 810 → 810   (4.697 s)`
- Phases origine : `LateralSurface   convert: 810 → 810   narrow: 810 → 792   (3.384 s)`
- Mesures comparées sur 792 éléments communs : 63 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 65 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 16 maillage _triang non fermé une fois réparé

En plus (18) :

- IfcFurnishingElement #15463 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159159 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #15856 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159262 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16149 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160671 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16175 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160717 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16914 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162493 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16971 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162495 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16997 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162496 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #17023 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162497 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcEnergyConversionDevice #6651 M_Radiator - Hosted:25:25:535063 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcEnergyConversionDevice #7034 M_Radiator - Hosted:25:25:536357 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcEnergyConversionDevice #7704 M_Radiator - Hosted:25:25:538562 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcEnergyConversionDevice #20313 M_Radiator - Hosted:25:25:549304 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcEnergyConversionDevice #37718 M_Radiator - Hosted:25:25:557520 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcEnergyConversionDevice #45498 M_Radiator - Hosted:25:25:557620 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcEnergyConversionDevice #127046 M_Radiator - Hosted:25:25:629670 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcEnergyConversionDevice #127088 M_Radiator - Hosted:25:25:630326 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcEnergyConversionDevice #143417 M_Radiator - Hosted:25:25:633263 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFlowFitting #153462 M_Transition - Generic:Standard:Standard:663237 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction

Mesures (63) :

- IfcSpace #819 A201 — écart -5.3804 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcSpace #2412 B201 — écart -5.3804 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 — écart -0.2958 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcRailing #12184 Railing:1100mm Guard Rail:151166 — écart -1.4927 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #16485 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162230 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16563 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162311 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16589 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162357 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16615 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162383 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16641 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162486 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16667 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162487 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16693 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162488 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16719 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162489 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #17409 M_Sofa:1830mm:1830mm:167426 — écart 0.1042 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #17815 M_Sofa:1830mm:1830mm:168378 — écart -0.1042 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20657 M_Bed-Standard:1981 x 2032mm - King:1981 x 2032mm - King:168717 — écart -0.6915 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20726 M_Bed-Standard:1981 x 2032mm - King:1981 x 2032mm - King:168914 — écart 0.6915 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcCovering #23671 Compound Ceiling:Gypsum Board:187149 — écart -0.4541 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 — écart -0.0884 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 — écart -0.0884 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcCovering #23884 Compound Ceiling:Gypsum Board:187483 — écart -0.0884 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcCovering #23992 Compound Ceiling:Gypsum Board:187508 — écart -0.4541 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcCovering #24060 Compound Ceiling:Gypsum Board:187639 — écart -0.2114 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcCovering #24128 Compound Ceiling:Gypsum Board:187649 — écart -0.2114 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcCovering #24186 Compound Ceiling:Gypsum Board:187659 — écart -0.0923 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcCovering #24268 Compound Ceiling:Gypsum Board:187667 — écart -0.1707 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcCovering #24326 Compound Ceiling:Gypsum Board:187675 — écart -0.0923 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcCovering #24408 Compound Ceiling:Gypsum Board:187683 — écart -0.1707 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcCovering #24476 Compound Ceiling:Gypsum Board:187691 — écart -0.2114 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcCovering #24544 Compound Ceiling:Gypsum Board:187701 — écart -0.2114 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #26941 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191401 — écart -1.135 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #29098 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191557 — écart -1.135 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #29127 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191680 — écart -1.135 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31241 M_Upper Cabinet-Double Door-Wall:1000mm:1000mm:191768 — écart -1.135 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31313 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192153 — écart 1.135 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31342 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192331 — écart 1.135 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31371 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192508 — écart 1.135 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31400 M_Upper Cabinet-Double Door-Wall:1000mm:1000mm:192610 — écart 1.135 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcRailing #35163 Railing:1100mm Guard Rail:198972 — écart -1.4895 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #36125 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205264 — écart 0.3758 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #36151 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205265 — écart 0.3758 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- ... 23 de plus

## ProjectedSurface_triang

Paramètres : `{'surface_min': 0.0, 'surface_max': 1000000000.0, 'direction': [0.0, 0.0, 1.0]}`.

- Phases _triang : `ProjectedSurface_triang   convert: 810 → 810   narrow: 810 → 810   (5.241 s)`
- Phases origine : `ProjectedSurface   convert: 810 → 810   narrow: 810 → 706   (3.540 s)`
- Mesures comparées sur 706 éléments communs : 42 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 126 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 20 maillage _triang non fermé une fois réparé

En plus (104) :

- IfcSpace #819 A201 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcSpace #2412 B201 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #15463 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159159 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #15856 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159262 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16149 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160671 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16175 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160717 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16485 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162230 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16563 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162311 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16589 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162357 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16615 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162383 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16641 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162486 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16667 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162487 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16693 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162488 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16719 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162489 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16914 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162493 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16971 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162495 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16997 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162496 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #17023 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162497 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #23884 Compound Ceiling:Gypsum Board:187483 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #24060 Compound Ceiling:Gypsum Board:187639 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #24186 Compound Ceiling:Gypsum Board:187659 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #24268 Compound Ceiling:Gypsum Board:187667 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #24326 Compound Ceiling:Gypsum Board:187675 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #24408 Compound Ceiling:Gypsum Board:187683 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcCovering #24544 Compound Ceiling:Gypsum Board:187701 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #35783 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:204934 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #35854 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205239 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #36125 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205264 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #36151 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205265 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #36423 M_Vanity Cabinet-Double Door Sink Unit:450 x 450 mm:450 x 450 mm:205548 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcSpace #424 A201 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcSpace #931 B201 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcSpace #1635 A101 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcSpace #2158 B101 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcSpace #3845 B201 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- ... 64 de plus

Mesures (42) :

- IfcFurnishingElement #17341 M_Sofa:1830mm:1830mm:167283 — écart 1.0712 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #17409 M_Sofa:1830mm:1830mm:167426 — écart 1.0712 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #17786 M_Sofa:1830mm:1830mm:168377 — écart 1.0712 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #17815 M_Sofa:1830mm:1830mm:168378 — écart 1.0712 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #19275 M_Bed-Standard:1525 x 2007mm - Queen:1525 x 2007mm - Queen:168449 — écart 2.9903 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20657 M_Bed-Standard:1981 x 2032mm - King:1981 x 2032mm - King:168717 — écart 3.9319 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20726 M_Bed-Standard:1981 x 2032mm - King:1981 x 2032mm - King:168914 — écart 3.9319 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20755 M_Bed-Standard:1525 x 2007mm - Queen:1525 x 2007mm - Queen:169008 — écart 2.9903 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #26941 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191401 — écart 0.3121 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #29098 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191557 — écart 0.3121 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #29127 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191680 — écart 0.3121 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31241 M_Upper Cabinet-Double Door-Wall:1000mm:1000mm:191768 — écart 0.3121 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31313 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192153 — écart 0.3121 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31342 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192331 — écart 0.3121 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31371 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192508 — écart 0.3121 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31400 M_Upper Cabinet-Double Door-Wall:1000mm:1000mm:192610 — écart 0.3121 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcEnergyConversionDevice #6246 M_Hot Water Boiler - 59-440 kW:147 kW:147 kW:530072 — écart 0.2652 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #6651 M_Radiator - Hosted:25:25:535063 — écart 0.1303 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7034 M_Radiator - Hosted:25:25:536357 — écart 0.1136 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7369 M_Radiator - Hosted:25:25:536919 — écart 0.1536 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7704 M_Radiator - Hosted:25:25:538562 — écart 0.2481 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7747 M_Radiator - Hosted:25:25:538847 — écart 0.1136 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #19618 M_Radiator - Hosted:25:25:548240 — écart 0.0581 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #20313 M_Radiator - Hosted:25:25:549304 — écart 0.0581 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFlowMovingDevice #32595 M_Inline Pump - Circulator:3.9 LPS - 0.8 Meter Head:3.9 LPS - 0.8 Meter Head:550094 — écart 0.0186 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcEnergyConversionDevice #37587 M_Hot Water Boiler - 59-440 kW:147 kW:147 kW:557516 — écart 0.2652 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37633 M_Radiator - Hosted:25:25:557517 — écart 0.1303 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37676 M_Radiator - Hosted:25:25:557519 — écart 0.1136 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37718 M_Radiator - Hosted:25:25:557520 — écart 0.1536 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37761 M_Radiator - Hosted:25:25:557522 — écart 0.2481 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37804 M_Radiator - Hosted:25:25:557524 — écart 0.1136 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #45498 M_Radiator - Hosted:25:25:557620 — écart 0.0581 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #46193 M_Radiator - Hosted:25:25:557628 — écart 0.0581 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFlowMovingDevice #67719 M_Inline Pump - Circulator:3.9 LPS - 0.8 Meter Head:3.9 LPS - 0.8 Meter Head:580717 — écart 0.0186 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowMovingDevice #115421 M_Centrifugal Fan -  Rooftop  - Upblast:991-1905 LPS:991-1905 LPS:602113 — écart 0.0905 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowMovingDevice #115533 M_Centrifugal Fan -  Rooftop  - Upblast:991-1905 LPS:991-1905 LPS:602396 — écart 0.0905 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcEnergyConversionDevice #127046 M_Radiator - Hosted:25:25:629670 — écart 0.1136 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #127088 M_Radiator - Hosted:25:25:630326 — écart 0.1536 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #131877 M_Radiator - Hosted:25:25:631726 — écart 0.1303 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #136014 M_Radiator - Hosted:25:25:632215 — écart 0.1136 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- ... 2 de plus

## ClearanceAxisToAxis_triang

Paramètres : `{'mode': 'MinDistance', 'min_distance': 0.2, 'max_distance': 5.0, 'tolerance': 0.01, 'linearity_ratio': 1.5, 'on_non_linear': 'Fallback', 'parallel_tolerance': 5.0, 'search_radius': 2.0}`.

- Phases _triang : `ClearanceAxisToAxis_triang   convert: 200 → 200   mid: 10000 → 10000   narrow: 10000 → 157   (1.145 s)`
- Phases origine : `ClearanceAxisToAxis   convert: 200 → 200   mid: 10000 → 10000   narrow: 10000 → 157   (75.700 s)`

## SurfaceRecover_triang

Paramètres : `{'direction': 'Auto', 'reference': 'Source', 'tolerance': 0.01, 'min_covering': ['relative', 101.0], 'max_covering': None}`.

- Phases _triang : `SurfaceRecover_triang   convert: 810 → 810   broad: 149864 → 2446   mid: 2446 → 2446   narrow: 2446 → 64   (4.843 s)`
- Phases origine : `SurfaceRecover   convert: 810 → 810   broad: 149864 → 2446   mid: 2446 → 2446   narrow: 2446 → 58   (37.284 s)`
- Écarts par cause : 7 seuils à ± marge, 1 contact marginal

Manquants (1) :

- IfcSpace #514 A101 → IfcEnergyConversionDevice #7747 M_Radiator - Hosted:25:25:538847 — distance 0.0 — expliqué : contact marginal : 2.9e-04 m² (0.01 % de la face), bande de largeur équivalente 0.2 mm < marge

En plus (7) :

- IfcWallStandardCase #4508 Basic Wall:Interior - Partition (92mm Stud):139682 → IfcFlowSegment #20628 Pipe Types:Mechanical Pipe:549955 — distance 0.005 — expliqué : seuils à ± marge
- IfcWallStandardCase #4508 Basic Wall:Interior - Partition (92mm Stud):139682 → IfcFlowSegment #21445 Pipe Types:Mechanical Pipe:550036 — distance 0.005 — expliqué : seuils à ± marge
- IfcWallStandardCase #4598 Basic Wall:Interior - Partition (92mm Stud):139939 → IfcFlowFitting #129253 M_Tee - Generic:Standard:Standard:631333 — distance 0.0051 — expliqué : seuils à ± marge
- IfcSlab #22492 Basic Roof:Live Roof over Wood Joist Flat Roof:184483 → IfcFlowFitting #115946 M_Rectangular to Round Transition - Angle:45 Degree:45 Degree:602990 — distance 0.001 — expliqué : seuils à ± marge
- IfcSlab #22492 Basic Roof:Live Roof over Wood Joist Flat Roof:184483 → IfcFlowFitting #116242 M_Rectangular to Round Transition - Angle:45 Degree:45 Degree:603490 — distance 0.001 — expliqué : seuils à ± marge
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #44469 M_Tee - Generic:Standard:Standard:557613 — distance 0.0076 — expliqué : seuils à ± marge
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowFitting #44469 M_Tee - Generic:Standard:Standard:557613 — distance 0.0076 — expliqué : seuils à ± marge

## Ray_Check_triang

Paramètres : `{'max_ray_length': 5.0}`.

- Phases _triang : `Ray_Check_triang   convert: 810 → 810   broad: 149864 → 66719   mid: 66719 → 66719   narrow: 66719 → 539   (0.045 s)`
- Phases origine : `Ray_Check   convert: 810 → 810   broad: 149864 → 66719   mid: 66719 → 66719   narrow: 66719 → 539   (34.592 s)`

## OneObjectFace_triang

Paramètres : `{'distance': True, 'min_distance': 0.5, 'max_distance': None, 'intersection': True, 'intersection_tolerance': 0.0, 'orientation': False, 'angle': None, 'angle_tolerance': 0.0, 'face_a_selection': {'orientation': 'Top', 'extreme_faces': True}, 'face_b_selection': {'orientation': 'Bottom', 'extreme_faces': True}, 'skip_adjacent': True}`.

- Phases _triang : `OneObjectFace_triang   convert: 810 → 810   narrow: 810 → 122583   (50.433 s)`
- Phases origine : `OneObjectFace   convert: 810 → 810   narrow: 810 → 99005   (42.232 s)`
- Écarts par cause : 85 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert

Manquants (13) :

- IfcFurnishingElement #17341 M_Sofa:1830mm:1830mm:167283 — distance 0.3784 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #17409 M_Sofa:1830mm:1830mm:167426 — distance 0.3784 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #17786 M_Sofa:1830mm:1830mm:168377 — distance 0.3784 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #17815 M_Sofa:1830mm:1830mm:168378 — distance 0.3784 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #26941 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191401 — distance 0.2276 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #29098 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191557 — distance 0.2276 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #29127 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191680 — distance 0.2276 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #31241 M_Upper Cabinet-Double Door-Wall:1000mm:1000mm:191768 — distance 0.2276 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #31313 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192153 — distance 0.2276 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #31342 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192331 — distance 0.2276 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #31371 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192508 — distance 0.2276 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #31400 M_Upper Cabinet-Double Door-Wall:1000mm:1000mm:192610 — distance 0.2276 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcRailing #35163 Railing:1100mm Guard Rail:198972 — distance 0.0453 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales

En plus (72) :

- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 — distance 0.1782 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 — distance 0.1782 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23884 Compound Ceiling:Gypsum Board:187483 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #24060 Compound Ceiling:Gypsum Board:187639 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #24186 Compound Ceiling:Gypsum Board:187659 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #24268 Compound Ceiling:Gypsum Board:187667 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #24326 Compound Ceiling:Gypsum Board:187675 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #24408 Compound Ceiling:Gypsum Board:187683 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #24544 Compound Ceiling:Gypsum Board:187701 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #6651 M_Radiator - Hosted:25:25:535063 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #7034 M_Radiator - Hosted:25:25:536357 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #7369 M_Radiator - Hosted:25:25:536919 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #7704 M_Radiator - Hosted:25:25:538562 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #7747 M_Radiator - Hosted:25:25:538847 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #8503 Pipe Types:Mechanical Pipe:540200 — distance 0.4878 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #12343 Pipe Types:Mechanical Pipe:546826 — distance 0.3986 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #14366 Pipe Types:Mechanical Pipe:547121 — distance 0.4881 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #15213 Pipe Types:Mechanical Pipe:547247 — distance 0.4052 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #15592 Pipe Types:Mechanical Pipe:547273 — distance 0.4052 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #19618 M_Radiator - Hosted:25:25:548240 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #20313 M_Radiator - Hosted:25:25:549304 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #37633 M_Radiator - Hosted:25:25:557517 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #37676 M_Radiator - Hosted:25:25:557519 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #37718 M_Radiator - Hosted:25:25:557520 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #37761 M_Radiator - Hosted:25:25:557522 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #37804 M_Radiator - Hosted:25:25:557524 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #38513 Pipe Types:Mechanical Pipe:557530 — distance 0.4952 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #40138 Pipe Types:Mechanical Pipe:557563 — distance 0.495 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #41136 Pipe Types:Mechanical Pipe:557570 — distance 0.4953 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #45498 M_Radiator - Hosted:25:25:557620 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #46193 M_Radiator - Hosted:25:25:557628 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #48942 Pipe Types:Mechanical Pipe:577748 — distance 0.4817 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #49626 Pipe Types:Mechanical Pipe:577870 — distance 0.4816 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #51920 Pipe Types:Mechanical Pipe:578143 — distance 0.4057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #52147 Pipe Types:Mechanical Pipe:578188 — distance 0.4052 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #52422 Pipe Types:Mechanical Pipe:578228 — distance 0.3923 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #56474 Pipe Types:Mechanical Pipe:578435 — distance 0.0366 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #56833 Pipe Types:Mechanical Pipe:578485 — distance 0.0352 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- ... 32 de plus

## TwoObjectsFace_triang

Paramètres : `{'distance': True, 'min_distance': 0.3, 'max_distance': None, 'intersection': True, 'intersection_tolerance': 0.0, 'orientation': False, 'angle': None, 'angle_tolerance': 0.0, 'source_face_selection': {'orientation': 'Top', 'extreme_faces': True}, 'target_face_selection': {'orientation': 'Bottom'}}`.

- Phases _triang : `TwoObjectsFace_triang   convert: 810 → 810   broad: 149864 → 1926   mid: 1926 → 1926   narrow: 1926 → 113557   (71.290 s)`
- Phases origine : `TwoObjectsFace   convert: 810 → 773   broad: 131022 → 2195   mid: 2195 → 2195   narrow: 2195 → 117643   (80.396 s)`
- Écarts par cause : 286 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert

Manquants (199) :

- IfcSpace #67 A102 → IfcSpace #1635 A101 — distance 0.124 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #67 A102 → IfcFlowSegment #16429 Pipe Types:Mechanical Pipe:547742 — distance 0.1229 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #67 A102 → IfcFlowSegment #16964 Pipe Types:Mechanical Pipe:547856 — distance 0.2104 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #67 A102 → IfcFlowSegment #127853 Pipe Types:Mechanical Pipe:631121 — distance 0.1464 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #67 A102 → IfcFlowSegment #128958 Pipe Types:Mechanical Pipe:631284 — distance 0.1464 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #212 A103 → IfcSpace #1635 A101 — distance 0.0 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #212 A103 → IfcFlowSegment #16964 Pipe Types:Mechanical Pipe:547856 — distance 0.2375 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #355 A104 → IfcSpace #1635 A101 — distance 0.1386 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #355 A104 → IfcFlowSegment #18179 Pipe Types:Mechanical Pipe:547956 — distance 0.1297 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #355 A104 → IfcFlowSegment #18358 Pipe Types:Mechanical Pipe:548047 — distance 0.1485 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #514 A101 → IfcSpace #1635 A101 — distance 0.0 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #514 A101 → IfcFlowSegment #15805 Pipe Types:Mechanical Pipe:547286 — distance 0.1228 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #514 A101 → IfcFlowSegment #16201 Pipe Types:Mechanical Pipe:547595 — distance 0.123 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #514 A101 → IfcFlowSegment #18179 Pipe Types:Mechanical Pipe:547956 — distance 0.2081 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #514 A101 → IfcFlowSegment #18358 Pipe Types:Mechanical Pipe:548047 — distance 0.2406 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #514 A101 → IfcFlowSegment #127853 Pipe Types:Mechanical Pipe:631121 — distance 0.1364 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #514 A101 → IfcFlowSegment #128958 Pipe Types:Mechanical Pipe:631284 — distance 0.1364 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #514 A101 → IfcFlowSegment #148417 Pipe Types:Mechanical Pipe:649433 — distance 0.1314 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #514 A101 → IfcFlowSegment #149234 Pipe Types:Mechanical Pipe:649463 — distance 0.1314 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1059 A204 → IfcSpace #424 A201 — distance 0.1386 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1059 A204 → IfcSpace #4367 A201 — distance 0.1386 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1218 A203 → IfcSpace #424 A201 — distance 0.1754 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1218 A203 → IfcSpace #4367 A201 — distance 0.1754 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1442 A202 → IfcSpace #424 A201 — distance 0.1754 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1442 A202 → IfcSpace #4367 A201 — distance 0.1754 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1627 B102 → IfcSpace #2158 B101 — distance 0.1402 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1627 B102 → IfcFlowSegment #43285 Pipe Types:Mechanical Pipe:557601 — distance 0.0542 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1627 B102 → IfcFlowSegment #43882 Pipe Types:Mechanical Pipe:557605 — distance 0.0514 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1627 B102 → IfcFlowSegment #139858 Pipe Types:Mechanical Pipe:632744 — distance 0.049 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1627 B102 → IfcFlowSegment #140710 Pipe Types:Mechanical Pipe:632815 — distance 0.0623 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1782 B103 → IfcSpace #2158 B101 — distance 0.1386 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1928 B104 → IfcSpace #2158 B101 — distance 0.124 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1928 B104 → IfcFlowSegment #44059 Pipe Types:Mechanical Pipe:557609 — distance 0.0544 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #1928 B104 → IfcFlowSegment #44238 Pipe Types:Mechanical Pipe:557611 — distance 0.0431 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #2108 B101 → IfcSpace #2158 B101 — distance 0.124 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #2108 B101 → IfcFlowSegment #42359 Pipe Types:Mechanical Pipe:557590 — distance 0.0411 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #2108 B101 → IfcFlowSegment #42799 Pipe Types:Mechanical Pipe:557597 — distance 0.0411 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #2108 B101 → IfcFlowSegment #44059 Pipe Types:Mechanical Pipe:557609 — distance 0.1975 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #2108 B101 → IfcFlowSegment #44238 Pipe Types:Mechanical Pipe:557611 — distance 0.2604 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSpace #2108 B101 → IfcFlowSegment #136525 Pipe Types:Mechanical Pipe:632423 — distance 0.046 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- ... 159 de plus

En plus (87) :

- IfcWallStandardCase #4287 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139234 → IfcFlowFitting #39716 M_Elbow - Generic:Standard:Standard:557556 — distance 0.2995 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcWallStandardCase #4553 Basic Wall:Interior - Partition (92mm Stud):139783 → IfcFlowFitting #51971 M_Elbow - Generic:Standard:Standard:578144 — distance 0.2992 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSlab #22492 Basic Roof:Live Roof over Wood Joist Flat Roof:184483 → IfcFlowFitting #115946 M_Rectangular to Round Transition - Angle:45 Degree:45 Degree:602990 — distance 0.001 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSlab #22492 Basic Roof:Live Roof over Wood Joist Flat Roof:184483 → IfcFlowFitting #116242 M_Rectangular to Round Transition - Angle:45 Degree:45 Degree:603490 — distance 0.001 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 → IfcSpace #4722 A/B — distance 0.1778 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 → IfcSpace #4799 A/B — distance 0.1778 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 → IfcSpace #4722 A/B — distance 0.1778 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 → IfcSpace #4799 A/B — distance 0.1778 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23671 Compound Ceiling:Gypsum Board:187149 → IfcFlowSegment #152559 Pipe Types:Mechanical Pipe:662976 — distance 0.2764 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #39664 Pipe Types:Mechanical Pipe:557555 — distance 0.0632 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #39716 M_Elbow - Generic:Standard:Standard:557556 — distance 0.2969 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #44417 Pipe Types:Mechanical Pipe:557612 — distance 0.0414 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #44469 M_Tee - Generic:Standard:Standard:557613 — distance 0.0447 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #44646 Pipe Types:Mechanical Pipe:557614 — distance 0.0127 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #44826 Pipe Types:Mechanical Pipe:557615 — distance 0.0136 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #44878 M_Tee - Generic:Standard:Standard:557616 — distance 0.0116 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #45055 Pipe Types:Mechanical Pipe:557617 — distance 0.0127 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #45107 M_Elbow - Generic:Standard:Standard:557618 — distance 0.0279 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #45155 M_Elbow - Generic:Standard:Standard:557619 — distance 0.0309 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #46361 Pipe Types:Mechanical Pipe:557644 — distance 0.2153 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #46413 M_Tee - Generic:Standard:Standard:557645 — distance 0.1874 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #46590 Pipe Types:Mechanical Pipe:557646 — distance 0.2166 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #46770 Pipe Types:Mechanical Pipe:557647 — distance 0.0246 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #47002 M_Elbow - Generic:Standard:Standard:557651 — distance 0.1556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #47178 Pipe Types:Mechanical Pipe:557652 — distance 0.0136 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #47230 M_Tee - Generic:Standard:Standard:557653 — distance 0.0116 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #47407 Pipe Types:Mechanical Pipe:557654 — distance 0.0127 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #47587 Pipe Types:Mechanical Pipe:557655 — distance 0.0146 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #47819 M_Elbow - Generic:Standard:Standard:557660 — distance 0.0157 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #60605 Pipe Types:Mechanical Pipe:578830 — distance 0.0224 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #60656 M_Elbow - Generic:Standard:Standard:578831 — distance 0.0182 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #60832 Pipe Types:Mechanical Pipe:578872 — distance 0.0224 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #60883 M_Elbow - Generic:Standard:Standard:578873 — distance 0.0149 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #39664 Pipe Types:Mechanical Pipe:557555 — distance 0.0632 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowFitting #39716 M_Elbow - Generic:Standard:Standard:557556 — distance 0.2969 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #44417 Pipe Types:Mechanical Pipe:557612 — distance 0.0414 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowFitting #44469 M_Tee - Generic:Standard:Standard:557613 — distance 0.0447 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #44646 Pipe Types:Mechanical Pipe:557614 — distance 0.0127 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #44826 Pipe Types:Mechanical Pipe:557615 — distance 0.0136 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowFitting #44878 M_Tee - Generic:Standard:Standard:557616 — distance 0.0116 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- ... 47 de plus

## FreeSpace_triang

Paramètres : `{'diameter': 1.0, 'height': 2.0}`.

- Phases _triang : `FreeSpace_triang   convert: 810 → 810   narrow: 810 → 810   (0.044 s)`
- Phases origine : `FreeSpace   convert: 810 → 810   narrow: 810 → 810   (6.284 s)`
