# Règles _triang contre règles d'origine
- Source : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifc` (286 éléments)
- Cible : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifc` (524 éléments)
- Triangles des règles _triang : `ifcview` (.ifcview : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifcview`, `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifcview`)
- Marge d'explication des écarts : 0.011 m (flèche .ifcview + flèche IFC)

25 règles `_triang`, une par processus (`compare_triang.py --rules`, 4 à 8 threads, une à la fois). **0 écart(s) inexpliqué(s).** ClearanceForDoors et Intersection2 ne sont plus portées ; DirectView est comparée à part (`comparaison_directview.md`).

Temps de l'origine : sa première exécution, froide (ouverture de session et conversion IFC comprises), lue ensuite dans le cache du comparateur (`build/engine/triang_original_cache`) : les règles d'origine ne changent pas, elles ne sont plus relancées. Ces premières exécutions ont tourné avec 2, 4 ou 8 threads selon les passes : les gains sont des ordres de grandeur. `_triang` : froid = ouverture de session et première exécution, chaud = la règle relancée dans la session.

| Règle | Origine | _triang | Communs | Manquants | En plus | Inexpliqués | Origine froid | _triang froid | _triang chaud | Gain froid |
|---|---|---|---|---|---|---|---|---|---|---|
| Intersection_triang | 802 | 770 | 730 | 72 | 40 | 0 | 1.77 s | 0.60 s | 0.33 s | ×2.9 |
| Above_triang | 1359 | 1421 | 1296 | 63 | 125 | 0 | 46.66 s | 0.41 s | 0.06 s | ×114.6 |
| Below_triang | 967 | 1034 | 886 | 81 | 148 | 0 | 36.18 s | 0.44 s | 0.05 s | ×82.6 |
| OBB_Above_triang | 2259 | 2108 | 2078 | 181 | 30 | 0 | 8.60 s | 0.44 s | 0.05 s | ×19.6 |
| OBB_Below_triang | 1560 | 1411 | 1393 | 167 | 18 | 0 | 8.02 s | 0.40 s | 0.03 s | ×19.9 |
| OBB_Front_And_Back_triang | 1683 | 1595 | 1537 | 146 | 58 | 0 | 8.92 s | 0.43 s | 0.04 s | ×20.7 |
| OBB_Custom_triang | 3369 | 3159 | 3157 | 212 | 2 | 0 | 11.71 s | 0.50 s | 0.09 s | ×23.5 |
| AngleBetween_triang | 64784 | 53187 | 51803 | 12981 | 1384 | 0 | 6.10 s | 1.51 s | 0.83 s | ×4.0 |
| ObbHigh_triang | 810 | 760 | 760 | 50 | 0 | 0 | 5.15 s | 0.22 s | 0.01 s | ×23.3 |
| ObbLength_triang | 810 | 760 | 760 | 50 | 0 | 0 | 4.95 s | 0.22 s | 0.01 s | ×22.8 |
| Orientation_triang | 810 | 760 | 760 | 50 | 0 | 0 | 4.96 s | 0.32 s | 0.01 s | ×15.3 |
| Alignement_triang | 158 | 150 | 136 | 22 | 14 | 0 | 14.81 s | 0.66 s | 0.28 s | ×22.4 |
| Clearance_triang | 6244 | 5868 | 5868 | 376 | 0 | 0 | 1.97 s | 0.82 s | 0.51 s | ×2.4 |
| Collision_triang | 491 | 479 | 452 | 39 | 27 | 0 | 1.36 s | 0.27 s | 0.02 s | ×4.9 |
| Volume_triang | 810 | 760 | 760 | 50 | 0 | 0 | 1.26 s | 0.28 s | 0.00 s | ×4.4 |
| Area_triang | 810 | 760 | 760 | 50 | 0 | 0 | 1.28 s | 0.29 s | 0.00 s | ×4.5 |
| TopOrBottomSurface_triang | 704 | 759 | 654 | 50 | 105 | 0 | 6.09 s | 2.68 s | 1.88 s | ×2.3 |
| LateralSurface_triang | 792 | 760 | 742 | 50 | 18 | 0 | 3.54 s | 0.28 s | 0.01 s | ×12.6 |
| ProjectedSurface_triang | 706 | 760 | 656 | 50 | 104 | 0 | 3.70 s | 0.66 s | 0.38 s | ×5.6 |
| ClearanceAxisToAxis_triang | 157 | 149 | 149 | 8 | 0 | 0 | 75.85 s | 0.39 s | 0.14 s | ×194.2 |
| SurfaceRecover_triang | 58 | 181 | 57 | 1 | 124 | 0 | 37.44 s | 0.44 s | 0.09 s | ×84.2 |
| Ray_Check_triang | 539 | 540 | 513 | 26 | 27 | 0 | 37.82 s | 1.03 s | 0.26 s | ×36.6 |
| OneObjectFace_triang | 473 | 528 | 456 | 17 | 72 | 0 | 44.40 s | 49.56 s | 47.63 s | ×0.9 |
| TwoObjectsFace_triang | 1868 | 1734 | 1649 | 219 | 85 | 0 | 83.16 s | 69.53 s | 67.16 s | ×1.2 |
| FreeSpace_triang | 810 | 760 | 760 | 50 | 0 | 0 | 9.77 s | 0.81 s | 0.03 s | ×12.1 |

## Intersection_triang

Paramètres : `{'tolerance': 0.002}`.

- Phases _triang : `Intersection_triang   convert: 810 → 760   broad: 123664 → 1454   mid: 1454 → 1454   convert_narrow: 691 → 691   narrow: 1454 → 770   (0.412 s)`
- Phases origine : `Intersection   convert: 810 → 810   broad: 149864 → 1600   mid: 1600 → 1590   narrow: 1590 → 802   (1.589 s)`
- Écarts par cause : 40 pénétration ≤ tolérance + marge, 30 absent du .ifcview, 25 maillage IFC ouvert, 17 géométries IFC au contact
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (72) :

- IfcSpace #819 A201 → IfcFlowSegment #15003 Pipe Types:Mechanical Pipe:547183 — distance 0.0 — expliqué : pénétration 0.0000 ≤ tolérance + marge
- IfcSpace #819 A201 → IfcFlowSegment #19966 Pipe Types:Mechanical Pipe:549038 — distance 0.0 — expliqué : pénétration 0.0000 ≤ tolérance + marge
- IfcSpace #2108 B101 → IfcSpace #2747 B101 — distance 0.124 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcSpace #2108 B101 → IfcSpace #2959 B103 — distance 0.026 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcSpace #2412 B201 → IfcSpace #2158 B101 — distance 0.0 — expliqué : pénétration 0.0000 ≤ tolérance + marge
- IfcSpace #2412 B201 → IfcFlowSegment #41773 Pipe Types:Mechanical Pipe:557576 — distance 0.0 — expliqué : pénétration 0.0000 ≤ tolérance + marge
- IfcSpace #2412 B201 → IfcFlowSegment #45846 Pipe Types:Mechanical Pipe:557623 — distance 0.0 — expliqué : pénétration 0.0000 ≤ tolérance + marge
- IfcWallStandardCase #4043 Basic Wall:Exterior - Brick on Block:138237 → IfcSpace #1635 A101 — distance 0.019 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcDoor #8386 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150478 → IfcSpace #1635 A101 — distance 0.026 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcRailing #12184 Railing:1100mm Guard Rail:151166 → IfcSpace #1635 A101 — distance 0.0 — expliqué : pénétration 0.0000 ≤ tolérance + marge
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 → IfcSpace #1942 A103 — distance 0.4197 — expliqué : absent du .ifcview
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 → IfcSpace #3276 A103 — distance 0.4197 — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 → IfcSpace #1942 A103 — distance 0.263 — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 → IfcSpace #3276 A103 — distance 0.263 — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 → IfcSpace #1942 A103 — distance 0.4196 — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 → IfcSpace #3276 A103 — distance 0.4196 — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 → IfcSpace #1635 A101 — distance 0.5009 — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 → IfcSpace #1942 A103 — distance 0.3052 — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 → IfcSpace #3154 A101 — distance 0.4567 — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 → IfcSpace #3276 A103 — distance 0.3052 — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 → IfcSpace #2462 B103 — distance 0.8084 — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 → IfcSpace #2959 B103 — distance 0.8084 — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 → IfcSpace #2462 B103 — distance 0.764 — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 → IfcSpace #2959 B103 — distance 0.764 — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 → IfcSpace #2462 B103 — distance 0.8084 — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 → IfcSpace #2959 B103 — distance 0.8084 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcSpace #2158 B101 — distance 0.5009 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcSpace #2462 B103 — distance 0.3427 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcSpace #2747 B101 — distance 0.4192 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcSpace #2959 B103 — distance 0.3427 — expliqué : absent du .ifcview
- IfcFurnishingElement #16485 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162230 → IfcSpace #2158 B101 — distance 0.0 — expliqué : pénétration 0.0000 ≤ tolérance + marge
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcSpace #1942 A103 — distance 0.847 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcSpace #3276 A103 — distance 0.847 — expliqué : absent du .ifcview
- IfcOpeningElement #22506 → IfcSpace #931 B201 — distance 1.0291 — expliqué : absent du .ifcview
- IfcOpeningElement #22506 → IfcSpace #3845 B201 — distance 1.0291 — expliqué : absent du .ifcview
- IfcOpeningElement #22506 → IfcSpace #4722 A/B — distance 1.524 — expliqué : absent du .ifcview
- IfcOpeningElement #22506 → IfcSpace #4799 A/B — distance 1.524 — expliqué : absent du .ifcview
- IfcOpeningElement #22520 → IfcSpace #424 A201 — distance 1.0291 — expliqué : absent du .ifcview
- IfcOpeningElement #22520 → IfcSpace #4367 A201 — distance 1.0291 — expliqué : absent du .ifcview
- IfcOpeningElement #22520 → IfcSpace #4722 A/B — distance 1.524 — expliqué : absent du .ifcview
- ... 32 de plus

En plus (40) :

- IfcSpace #514 A101 → IfcSpace #1635 A101 — distance 2.183 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSpace #1928 B104 → IfcSpace #2604 B104 — distance 1.456 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcSpace #2108 B101 → IfcSpace #2158 B101 — distance 2.183 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSpace #3456 A105 → IfcSpace #424 A201 — distance 0.016 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSpace #3456 A105 → IfcSpace #1635 A101 — distance 2.183 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSpace #3456 A105 → IfcSpace #4367 A201 — distance 0.016 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSpace #3586 B105 → IfcSpace #2158 B101 — distance 2.183 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWallStandardCase #4553 Basic Wall:Interior - Partition (92mm Stud):139783 → IfcFlowSegment #21037 Pipe Types:Mechanical Pipe:550018 — distance 0.0111 — expliqué : pénétration 0.0111 ≤ tolérance + marge
- IfcWallStandardCase #5642 Basic Wall:Interior - Partition (92mm Stud):143856 → IfcSpace #730 B203 — distance 0.124 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcWallStandardCase #5642 Basic Wall:Interior - Partition (92mm Stud):143856 → IfcSpace #3553 B203 — distance 0.124 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcWallStandardCase #5687 Basic Wall:Interior - Partition (92mm Stud):143921 → IfcSpace #223 B202 — distance 2.581 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcWallStandardCase #5687 Basic Wall:Interior - Partition (92mm Stud):143921 → IfcSpace #4614 B202 — distance 2.581 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcWallStandardCase #5731 Basic Wall:Interior - Partition (92mm Stud):143960 → IfcSpace #223 B202 — distance 0.124 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcWallStandardCase #5731 Basic Wall:Interior - Partition (92mm Stud):143960 → IfcSpace #4614 B202 — distance 0.124 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcWallStandardCase #5903 Basic Wall:Interior - Partition (92mm Stud):144518 → IfcSpace #70 A203 — distance 0.124 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcWallStandardCase #5903 Basic Wall:Interior - Partition (92mm Stud):144518 → IfcSpace #4491 A203 — distance 0.124 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcWallStandardCase #5948 Basic Wall:Interior - Partition (92mm Stud):144586 → IfcSpace #581 A202 — distance 2.581 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcWallStandardCase #5948 Basic Wall:Interior - Partition (92mm Stud):144586 → IfcSpace #3677 A202 — distance 2.581 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcWallStandardCase #5992 Basic Wall:Interior - Partition (92mm Stud):144633 → IfcSpace #581 A202 — distance 0.124 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcWallStandardCase #5992 Basic Wall:Interior - Partition (92mm Stud):144633 → IfcSpace #3677 A202 — distance 0.124 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcSpace #2158 B101 — distance 0.305 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcSpace #1635 A101 — distance 0.305 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcDoor #8066 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173 → IfcSpace #1635 A101 — distance 0.029 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcDoor #8283 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378 → IfcSpace #931 B201 — distance 0.568 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcDoor #8283 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378 → IfcSpace #3845 B201 — distance 0.568 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcDoor #15962 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734 → IfcSpace #931 B201 — distance 0.025 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcDoor #15962 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734 → IfcSpace #3845 B201 — distance 0.025 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcDoor #16013 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834 → IfcSpace #424 A201 — distance 0.568 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcDoor #16013 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834 → IfcSpace #4367 A201 — distance 0.568 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcDoor #16064 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065 → IfcSpace #931 B201 — distance 0.025 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcDoor #16064 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065 → IfcSpace #3845 B201 — distance 0.025 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcDoor #16115 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208 → IfcSpace #424 A201 — distance 0.025 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcDoor #16115 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208 → IfcSpace #4367 A201 — distance 0.025 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSlab #21080 Floor:Finish Floor - Wood:169395 → IfcSpace #2158 B101 — distance 0.019 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSlab #21336 Floor:Finish Floor - Ceramic Tile:169866 → IfcFlowMovingDevice #32595 M_Inline Pump - Circulator:3.9 LPS - 0.8 Meter Head:3.9 LPS - 0.8 Meter Head:550094 — distance 0.0126 — expliqué : pénétration 0.0126 ≤ tolérance + marge
- IfcSlab #21401 Floor:Finish Floor - Wood:170352 → IfcSpace #1942 A103 — distance 1.8344 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcSlab #21401 Floor:Finish Floor - Wood:170352 → IfcSpace #3276 A103 — distance 1.8344 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcWallStandardCase #24596 Basic Wall:Interior - Furring (152 mm Stud):189074 → IfcFlowSegment #11665 Pipe Types:Mechanical Pipe:546374 — distance 0.0607 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWallStandardCase #24723 Basic Wall:Interior - Partition (92mm Stud):190140 → IfcFlowSegment #46770 Pipe Types:Mechanical Pipe:557647 — distance 0.0096 — expliqué : pénétration 0.0096 ≤ tolérance + marge
- IfcWallStandardCase #35452 Basic Wall:Interior - Partition (92mm Stud):204300 → IfcSpace #2158 B101 — distance 0.124 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration

## Above_triang

Paramètres : `{'above_type': 'Above_MaxToMin', 'tolerance': 1.0}`.

- Phases _triang : `Above_triang   convert: 810 → 760   broad: 123664 → 2207   mid: 2207 → 2189   convert_narrow: 687 → 687   narrow: 2189 → 1421   (0.196 s)`
- Phases origine : `Above   convert: 810 → 810   broad: 149864 → 2394   mid: 2394 → 2346   narrow: 2346 → 1359   (46.423 s)`
- Écarts par cause : 61 absent du .ifcview, 61 écart vertical au bord de [0, tolérance], 47 faux négatif de l'original : grille de rayons, 11 faux négatif de l'original, vérifié sur l'IFC, 4 géométrie du .ifcview différente de l'IFC, 2 faux positif de l'original, 2 seuils à ± marge
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (63) :

- IfcSpace #3456 A105 → IfcSpace #424 A201 — distance 0.5192 — expliqué : faux positif de l'original : son test « ray » coupe une droite infinie (cible sous la source)
- IfcSpace #3586 B105 → IfcSpace #931 B201 — distance 0.5192 — expliqué : faux positif de l'original : son test « ray » coupe une droite infinie (cible sous la source)
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #581 A202 — distance 0.599 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #730 B203 — distance 0.599 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #3553 B203 — distance 0.599 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #3677 A202 — distance 0.599 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowFitting #147550 M_Tee - Generic:Standard:Standard:633378 — distance 0.1316 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowSegment #147721 Pipe Types:Mechanical Pipe:633379 — distance 0.1304 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #70 A203 — distance 0.599 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #223 B202 — distance 0.599 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #4491 A203 — distance 0.599 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #4614 B202 — distance 0.599 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowFitting #132513 M_Tee - Generic:Standard:Standard:631966 — distance 0.2216 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowSegment #132684 Pipe Types:Mechanical Pipe:631967 — distance 0.2204 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcFlowSegment #85608 Pipe Types:Mechanical Pipe:600257 — distance 0.7344 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcFlowFitting #85660 M_Tee - Generic:Standard:Standard:600265 — distance 0.7316 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcFlowSegment #85837 Pipe Types:Mechanical Pipe:600266 — distance 0.7226 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcFlowSegment #88704 Pipe Types:Mechanical Pipe:600279 — distance 0.7269 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcFlowSegment #100447 Pipe Types:Mechanical Pipe:600896 — distance 0.6444 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcFlowFitting #102896 M_Tee - Generic:Standard:Standard:600910 — distance 0.6416 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcFlowSegment #103103 Pipe Types:Mechanical Pipe:600911 — distance 0.6369 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #581 A202 — distance 0.819 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #3677 A202 — distance 0.819 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcEnergyConversionDevice #7704 M_Radiator - Hosted:25:25:538562 — distance 0.9016 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #223 B202 — distance 0.819 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #4614 B202 — distance 0.819 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcFlowSegment #11305 Pipe Types:Mechanical Pipe:546125 — distance 0.4369 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcEnergyConversionDevice #37761 M_Radiator - Hosted:25:25:557522 — distance 0.819 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #4722 A/B — distance 0.847 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #4799 A/B — distance 0.847 — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 → IfcSpace #4722 A/B — distance 0.847 — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 → IfcSpace #4799 A/B — distance 0.847 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcSpace #4722 A/B — distance 0.847 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcSpace #4799 A/B — distance 0.847 — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 → IfcSpace #4722 A/B — distance 0.847 — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 → IfcSpace #4799 A/B — distance 0.847 — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 → IfcFlowSegment #21037 Pipe Types:Mechanical Pipe:550018 — distance 0.7084 — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 → IfcFlowSegment #51920 Pipe Types:Mechanical Pipe:578143 — distance 0.7374 — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 → IfcFlowFitting #51971 M_Elbow - Generic:Standard:Standard:578144 — distance 0.7096 — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 → IfcFlowSegment #46770 Pipe Types:Mechanical Pipe:557647 — distance 0.615 — expliqué : absent du .ifcview
- ... 23 de plus

En plus (125) :

- IfcSpace #67 A102 → IfcFlowSegment #38151 Pipe Types:Mechanical Pipe:557527 — distance 0.0588 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.7 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #67 A102 → IfcFlowSegment #132471 Pipe Types:Mechanical Pipe:631911 — distance 0.144 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #11485 Pipe Types:Mechanical Pipe:546131 — distance 0.1443 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #38151 Pipe Types:Mechanical Pipe:557527 — distance 0.0527 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.7 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #135882 Pipe Types:Mechanical Pipe:631996 — distance 0.1392 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #355 A104 → IfcFlowSegment #21037 Pipe Types:Mechanical Pipe:550018 — distance 0.1444 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.144 m au-dessus de la source en (6.23, -9.95)
- IfcSpace #355 A104 → IfcFlowSegment #21217 Pipe Types:Mechanical Pipe:550028 — distance 0.587 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.590 m au-dessus de la source en (6.23, -9.91)
- IfcSpace #355 A104 → IfcFlowSegment #22034 Pipe Types:Mechanical Pipe:550077 — distance 0.587 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.590 m au-dessus de la source en (6.23, -9.24)
- IfcSpace #514 A101 → IfcFlowSegment #128136 Pipe Types:Mechanical Pipe:631126 — distance 0.1437 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #514 A101 → IfcFlowSegment #135882 Pipe Types:Mechanical Pipe:631996 — distance 0.1444 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1627 B102 → IfcFlowSegment #8141 Pipe Types:Mechanical Pipe:540175 — distance 0.1488 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1627 B102 → IfcFlowSegment #143609 Pipe Types:Mechanical Pipe:633327 — distance 0.0544 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1627 B102 → IfcFlowSegment #144732 Pipe Types:Mechanical Pipe:633360 — distance 0.0544 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1782 B103 → IfcFlowSegment #8141 Pipe Types:Mechanical Pipe:540175 — distance 0.1427 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1782 B103 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.0545 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #46770 Pipe Types:Mechanical Pipe:557647 — distance 0.0505 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.053 m au-dessus de la source en (2.57, -7.55)
- IfcSpace #1928 B104 → IfcFlowSegment #46950 Pipe Types:Mechanical Pipe:557648 — distance 0.587 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.590 m au-dessus de la source en (2.57, -7.87)
- IfcSpace #1928 B104 → IfcFlowSegment #47767 Pipe Types:Mechanical Pipe:557656 — distance 0.587 — expliqué : géométrie du .ifcview différente de l'IFC : la cible n'a pas de surface à ce point dans l'IFC (ouverture non soustraite dans le .ifcview)
- IfcSpace #2108 B101 → IfcFlowSegment #139518 Pipe Types:Mechanical Pipe:632681 — distance 0.0526 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2108 B101 → IfcFlowSegment #143609 Pipe Types:Mechanical Pipe:633327 — distance 0.0544 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
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
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #40138 Pipe Types:Mechanical Pipe:557563 — distance 0.0002 — expliqué : écart vertical 0.0002 au bord de [0, tolérance]
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowSegment #12343 Pipe Types:Mechanical Pipe:546826 — distance 0.0006 — expliqué : écart vertical 0.0006 au bord de [0, tolérance]
- ... 85 de plus

## Below_triang

Paramètres : `{'below_type': 'Below_MinToMax', 'tolerance': 1.0}`.

- Phases _triang : `Below_triang   convert: 810 → 760   broad: 123664 → 1503   mid: 1503 → 1485   convert_narrow: 454 → 454   narrow: 1485 → 1034   (0.184 s)`
- Phases origine : `Below   convert: 810 → 810   broad: 149864 → 1701   mid: 1701 → 1663   narrow: 1663 → 967   (35.976 s)`
- Écarts par cause : 131 faux négatif de l'original : grille de rayons, 75 absent du .ifcview, 15 écart vertical au bord de [0, tolérance], 6 faux positif de l'original, 1 seuils à ± marge, 1 faux négatif de l'original, vérifié sur l'IFC
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (81) :

- IfcWallStandardCase #5731 Basic Wall:Interior - Partition (92mm Stud):143960 → IfcFlowSegment #37971 Pipe Types:Mechanical Pipe:557526 — distance 0.8963 — expliqué : faux positif de l'original : son test « ray » garde la distance des points les plus proches, l'écart vertical au point du rayon (2.457 m) dépasse la tolérance
- IfcWallStandardCase #5731 Basic Wall:Interior - Partition (92mm Stud):143960 → IfcFlowFitting #38792 M_Elbow - Generic:Standard:Standard:557546 — distance 0.9106 — expliqué : faux positif de l'original : son test « ray » garde la distance des points les plus proches, l'écart vertical au point du rayon (2.470 m) dépasse la tolérance
- IfcWallStandardCase #5992 Basic Wall:Interior - Partition (92mm Stud):144633 → IfcFlowSegment #7915 Pipe Types:Mechanical Pipe:540160 — distance 0.3572 — expliqué : faux positif de l'original : son test « ray » garde la distance des points les plus proches, l'écart vertical au point du rayon (2.367 m) dépasse la tolérance
- IfcWallStandardCase #5992 Basic Wall:Interior - Partition (92mm Stud):144633 → IfcFlowFitting #10911 M_Elbow - Generic:Standard:Standard:545367 — distance 0.373 — expliqué : faux positif de l'original : son test « ray » garde la distance des points les plus proches, l'écart vertical au point du rayon (2.380 m) dépasse la tolérance
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #2158 B101 — distance 0.6 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #2329 B102 — distance 0.6 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #2747 B101 — distance 0.6699 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #2869 B102 — distance 0.6699 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowFitting #42850 M_Tee - Generic:Standard:Standard:557598 — distance 0.5341 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #43075 Pipe Types:Mechanical Pipe:557599 — distance 0.5268 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowFitting #139161 M_Tee - Generic:Standard:Standard:632678 — distance 0.5341 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #139332 Pipe Types:Mechanical Pipe:632679 — distance 0.5294 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #140540 Pipe Types:Mechanical Pipe:632808 — distance 0.5268 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowFitting #140793 M_Tee - Generic:Standard:Standard:632819 — distance 0.5341 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #140964 Pipe Types:Mechanical Pipe:632820 — distance 0.5294 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowFitting #147550 M_Tee - Generic:Standard:Standard:633378 — distance 0.5341 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #147721 Pipe Types:Mechanical Pipe:633379 — distance 0.5329 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcSpace #2158 B101 — distance 0.6 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcSpace #2747 B101 — distance 0.6699 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcFlowSegment #43075 Pipe Types:Mechanical Pipe:557599 — distance 0.5268 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcFlowFitting #60248 M_Tee - Generic:Standard:Standard:578774 — distance 0.5341 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcFlowSegment #60425 Pipe Types:Mechanical Pipe:578775 — distance 0.5294 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcSpace #1635 A101 — distance 0.6 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcSpace #1812 A102 — distance 0.6 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcSpace #3154 A101 — distance 0.6699 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcSpace #3365 A102 — distance 0.6699 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcFlowFitting #16252 M_Tee - Generic:Standard:Standard:547619 — distance 0.4441 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcFlowSegment #50163 Pipe Types:Mechanical Pipe:577911 — distance 0.4368 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcFlowFitting #128178 M_Tee - Generic:Standard:Standard:631162 — distance 0.4441 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcFlowSegment #128349 Pipe Types:Mechanical Pipe:631163 — distance 0.4429 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcFlowSegment #129211 Pipe Types:Mechanical Pipe:631288 — distance 0.4368 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcFlowFitting #129253 M_Tee - Generic:Standard:Standard:631333 — distance 0.4441 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcFlowSegment #129424 Pipe Types:Mechanical Pipe:631334 — distance 0.4469 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcFlowFitting #132513 M_Tee - Generic:Standard:Standard:631966 — distance 0.4441 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcFlowSegment #132684 Pipe Types:Mechanical Pipe:631967 — distance 0.4429 — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 → IfcSpace #1635 A101 — distance 0.6 — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 → IfcSpace #3154 A101 — distance 0.6699 — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 → IfcFlowSegment #50163 Pipe Types:Mechanical Pipe:577911 — distance 0.4368 — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 → IfcFlowFitting #50216 M_Tee - Generic:Standard:Standard:577919 — distance 0.4441 — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 → IfcFlowSegment #50423 Pipe Types:Mechanical Pipe:577920 — distance 0.4395 — expliqué : absent du .ifcview
- ... 41 de plus

En plus (148) :

- IfcSpace #819 A201 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.4447 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1059 A204 → IfcFlowSegment #11485 Pipe Types:Mechanical Pipe:546131 — distance 0.3481 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1059 A204 → IfcFlowSegment #18179 Pipe Types:Mechanical Pipe:547956 — distance 0.3849 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.2 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1059 A204 → IfcFlowSegment #18358 Pipe Types:Mechanical Pipe:548047 — distance 0.3849 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.2 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1218 A203 → IfcFlowSegment #15213 Pipe Types:Mechanical Pipe:547247 — distance 0.0012 — expliqué : écart vertical 0.0012 au bord de [0, tolérance]
- IfcSpace #1218 A203 → IfcFlowSegment #15592 Pipe Types:Mechanical Pipe:547273 — distance 0.0017 — expliqué : écart vertical 0.0017 au bord de [0, tolérance]
- IfcSpace #1218 A203 → IfcFlowSegment #127853 Pipe Types:Mechanical Pipe:631121 — distance 0.3909 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.1 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1218 A203 → IfcFlowSegment #128136 Pipe Types:Mechanical Pipe:631126 — distance 0.3536 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1218 A203 → IfcFlowSegment #128958 Pipe Types:Mechanical Pipe:631284 — distance 0.3909 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.1 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1218 A203 → IfcFlowSegment #132471 Pipe Types:Mechanical Pipe:631911 — distance 0.3536 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1218 A203 → IfcFlowSegment #135882 Pipe Types:Mechanical Pipe:631996 — distance 0.3536 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1442 A202 → IfcFlowSegment #8141 Pipe Types:Mechanical Pipe:540175 — distance 0.3541 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2412 B201 → IfcFlowSegment #11485 Pipe Types:Mechanical Pipe:546131 — distance 0.3551 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2637 B204 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.4398 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2637 B204 → IfcFlowSegment #44059 Pipe Types:Mechanical Pipe:557609 — distance 0.4749 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2637 B204 → IfcFlowSegment #44238 Pipe Types:Mechanical Pipe:557611 — distance 0.4749 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2789 B203 → IfcFlowSegment #139518 Pipe Types:Mechanical Pipe:632681 — distance 0.4442 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2789 B203 → IfcFlowSegment #139858 Pipe Types:Mechanical Pipe:632744 — distance 0.4809 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2789 B203 → IfcFlowSegment #140710 Pipe Types:Mechanical Pipe:632815 — distance 0.4809 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2789 B203 → IfcFlowSegment #143609 Pipe Types:Mechanical Pipe:633327 — distance 0.4447 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2789 B203 → IfcFlowSegment #144732 Pipe Types:Mechanical Pipe:633360 — distance 0.4436 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #3013 B202 → IfcFlowSegment #38151 Pipe Types:Mechanical Pipe:557527 — distance 0.4441 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.7 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #3197 A205 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.4389 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #3325 B205 → IfcFlowSegment #11485 Pipe Types:Mechanical Pipe:546131 — distance 0.3486 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowSegment #11485 Pipe Types:Mechanical Pipe:546131 — distance 0.3352 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.4267 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowSegment #39016 Pipe Types:Mechanical Pipe:557550 — distance 0.4264 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowSegment #42359 Pipe Types:Mechanical Pipe:557590 — distance 0.4682 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowSegment #42799 Pipe Types:Mechanical Pipe:557597 — distance 0.4682 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowSegment #43524 Pipe Types:Mechanical Pipe:557603 — distance 0.4329 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowSegment #139518 Pipe Types:Mechanical Pipe:632681 — distance 0.4268 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowSegment #144732 Pipe Types:Mechanical Pipe:633360 — distance 0.4246 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #39256 Pipe Types:Mechanical Pipe:557552 — distance 0.4251 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.1 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.4251 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #43285 Pipe Types:Mechanical Pipe:557601 — distance 0.4682 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #43524 Pipe Types:Mechanical Pipe:557603 — distance 0.4246 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #43882 Pipe Types:Mechanical Pipe:557605 — distance 0.4682 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #49169 Pipe Types:Mechanical Pipe:577808 — distance 0.3351 — expliqué : faux négatif de l'original : sa grille de rayons (pas 9.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #50423 Pipe Types:Mechanical Pipe:577920 — distance 0.3429 — expliqué : seuils à ± marge
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowSegment #135882 Pipe Types:Mechanical Pipe:631996 — distance 0.3346 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- ... 108 de plus

## OBB_Above_triang

Paramètres : `{'tolerance': 1.0}`.

- Phases _triang : `OBB_Above_triang   convert: 810 → 760   broad: 123664 → 2207   mid: 2207 → 2189   convert_narrow: 687 → 687   narrow: 2189 → 2108   (0.181 s)`
- Phases origine : `OBB_Above   convert: 810 → 810   broad: 149864 → 2394   mid: 2394 → 2394   narrow: 2394 → 2259   (8.389 s)`
- Écarts par cause : 181 absent du .ifcview, 29 seuils à ± marge, 1 OBB optimale non unique
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (181) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #581 A202 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #730 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2329 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2869 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #3553 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #3677 A202 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowSegment #39016 Pipe Types:Mechanical Pipe:557550 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowSegment #144732 Pipe Types:Mechanical Pipe:633360 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowFitting #147550 M_Tee - Generic:Standard:Standard:633378 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowSegment #147721 Pipe Types:Mechanical Pipe:633379 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #70 A203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #223 B202 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #1812 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #3365 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #4491 A203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #4614 B202 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowSegment #11125 Pipe Types:Mechanical Pipe:545888 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowSegment #132471 Pipe Types:Mechanical Pipe:631911 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowFitting #132513 M_Tee - Generic:Standard:Standard:631966 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowSegment #132684 Pipe Types:Mechanical Pipe:631967 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcSpace #1635 A101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcSpace #3154 A101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcFlowSegment #85608 Pipe Types:Mechanical Pipe:600257 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcFlowFitting #85660 M_Tee - Generic:Standard:Standard:600265 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcFlowSegment #85837 Pipe Types:Mechanical Pipe:600266 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcFlowSegment #88704 Pipe Types:Mechanical Pipe:600279 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcSpace #2158 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcSpace #2747 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcFlowSegment #100447 Pipe Types:Mechanical Pipe:600896 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcFlowFitting #102896 M_Tee - Generic:Standard:Standard:600910 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcFlowSegment #103103 Pipe Types:Mechanical Pipe:600911 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #581 A202 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2329 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2462 B103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2869 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2959 B103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #3677 A202 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcEnergyConversionDevice #7704 M_Radiator - Hosted:25:25:538562 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowSegment #39256 Pipe Types:Mechanical Pipe:557552 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #223 B202 — distance 0.0 — expliqué : absent du .ifcview
- ... 141 de plus

En plus (30) :

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
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #143872 Pipe Types:Mechanical Pipe:633332 — distance 0.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : la zone suit un autre axe

## OBB_Below_triang

Paramètres : `{'tolerance': 1.0}`.

- Phases _triang : `OBB_Below_triang   convert: 810 → 760   broad: 123664 → 1503   mid: 1503 → 1485   convert_narrow: 454 → 454   narrow: 1485 → 1411   (0.167 s)`
- Phases origine : `OBB_Below   convert: 810 → 810   broad: 149864 → 1701   mid: 1701 → 1701   narrow: 1701 → 1560   (7.831 s)`
- Écarts par cause : 164 absent du .ifcview, 18 seuils à ± marge, 3 OBB optimale non unique
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (167) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2329 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2869 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #1812 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #3365 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2329 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2462 B103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2869 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2959 B103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #1812 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #1942 A103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #3276 A103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #3365 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #730 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #2158 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #2329 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #2747 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #2869 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #3553 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #39016 Pipe Types:Mechanical Pipe:557550 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #42799 Pipe Types:Mechanical Pipe:557597 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowFitting #42850 M_Tee - Generic:Standard:Standard:557598 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #43075 Pipe Types:Mechanical Pipe:557599 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowFitting #139161 M_Tee - Generic:Standard:Standard:632678 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #139332 Pipe Types:Mechanical Pipe:632679 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #139518 Pipe Types:Mechanical Pipe:632681 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #140540 Pipe Types:Mechanical Pipe:632808 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowFitting #140793 M_Tee - Generic:Standard:Standard:632819 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #140964 Pipe Types:Mechanical Pipe:632820 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #144732 Pipe Types:Mechanical Pipe:633360 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowFitting #147550 M_Tee - Generic:Standard:Standard:633378 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #147721 Pipe Types:Mechanical Pipe:633379 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcSpace #730 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcSpace #2158 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcSpace #2747 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcSpace #3553 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcFlowSegment #42359 Pipe Types:Mechanical Pipe:557590 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcFlowSegment #43075 Pipe Types:Mechanical Pipe:557599 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcFlowFitting #60248 M_Tee - Generic:Standard:Standard:578774 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcFlowSegment #60425 Pipe Types:Mechanical Pipe:578775 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7497 M_Casement:819mm x 759mm:819mm x 759mm:148607:1 → IfcSpace #730 B203 — distance 0.0 — expliqué : absent du .ifcview
- ... 127 de plus

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

- Phases _triang : `OBB_Front_And_Back_triang   convert: 810 → 760   broad: 123664 → 2208   mid: 2208 → 2208   convert_narrow: 724 → 724   narrow: 2208 → 1860   (0.179 s)`
- Phases origine : `OBB_Front_And_Back   convert: 810 → 810   broad: 149864 → 2369   mid: 2369 → 2369   narrow: 2369 → 1888   (8.718 s)`
- Écarts par cause : 144 absent du .ifcview, 58 seuils à ± marge, 2 axe principal ambigu
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (146) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2329 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2869 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #1812 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #3365 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcSpace #1635 A101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcSpace #3154 A101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcSpace #2158 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcSpace #2747 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2329 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2462 B103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2869 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2959 B103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #1812 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #1942 A103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #3276 A103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #3365 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #730 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #3553 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcSpace #730 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 → IfcSpace #3553 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7497 M_Casement:819mm x 759mm:819mm x 759mm:148607:1 → IfcSpace #730 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7497 M_Casement:819mm x 759mm:819mm x 759mm:148607:1 → IfcSpace #3553 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 → IfcSpace #730 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 → IfcSpace #3553 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcSpace #70 A203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcSpace #4491 A203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 → IfcSpace #70 A203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 → IfcSpace #4491 A203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7885 M_Casement:819mm x 759mm:819mm x 759mm:149736:1 → IfcSpace #70 A203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7885 M_Casement:819mm x 759mm:819mm x 759mm:149736:1 → IfcSpace #4491 A203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 → IfcSpace #70 A203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 → IfcSpace #4491 A203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 → IfcSpace #1635 A101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 → IfcSpace #3154 A101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 → IfcSpace #3454 A104 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 → IfcSpace #2158 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 → IfcSpace #2604 B104 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 → IfcSpace #2747 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 → IfcSpace #3048 B104 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 → IfcSpace #730 B203 — distance 0.0 — expliqué : absent du .ifcview
- ... 106 de plus

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

- Phases _triang : `OBB_Custom_triang   convert: 810 → 760   broad: 123664 → 3310   mid: 3310 → 3310   convert_narrow: 743 → 743   narrow: 3310 → 3769   (0.182 s)`
- Phases origine : `OBB_Custom   convert: 810 → 810   broad: 149864 → 3529   mid: 3529 → 3529   narrow: 3529 → 4056   (11.443 s)`
- Écarts par cause : 210 absent du .ifcview, 2 seuils à ± marge, 2 OBB optimale non unique
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (212) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2329 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2869 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowSegment #39016 Pipe Types:Mechanical Pipe:557550 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowSegment #144732 Pipe Types:Mechanical Pipe:633360 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowFitting #147550 M_Tee - Generic:Standard:Standard:633378 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowSegment #147721 Pipe Types:Mechanical Pipe:633379 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #1812 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #3365 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowSegment #11125 Pipe Types:Mechanical Pipe:545888 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowSegment #132471 Pipe Types:Mechanical Pipe:631911 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowFitting #132513 M_Tee - Generic:Standard:Standard:631966 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowSegment #132684 Pipe Types:Mechanical Pipe:631967 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcSpace #1635 A101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcSpace #3154 A101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcSpace #2158 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcSpace #2747 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2329 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2462 B103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2869 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2959 B103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowSegment #39256 Pipe Types:Mechanical Pipe:557552 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #1812 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #1942 A103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #3276 A103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #3365 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcFlowSegment #11305 Pipe Types:Mechanical Pipe:546125 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #730 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #2158 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #2329 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #2747 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #2869 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #3553 B203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #39016 Pipe Types:Mechanical Pipe:557550 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #42799 Pipe Types:Mechanical Pipe:557597 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowFitting #42850 M_Tee - Generic:Standard:Standard:557598 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #43075 Pipe Types:Mechanical Pipe:557599 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowFitting #139161 M_Tee - Generic:Standard:Standard:632678 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #139332 Pipe Types:Mechanical Pipe:632679 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #139518 Pipe Types:Mechanical Pipe:632681 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcFlowSegment #140540 Pipe Types:Mechanical Pipe:632808 — distance 0.0 — expliqué : absent du .ifcview
- ... 172 de plus

En plus (2) :

- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowFitting #49677 M_Tee - Generic:Standard:Standard:577871 — distance 0.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : la zone suit un autre axe
- IfcRailing #9326 Railing:900mm Handrail Only:151162 → IfcFlowSegment #49854 Pipe Types:Mechanical Pipe:577872 — distance 0.0 — expliqué : seuils à ± marge

## AngleBetween_triang

Paramètres : `{'direction_method_for_source': 'Wide', 'direction_method_for_target': 'Wide', 'angle_difference': 90.0, 'angle_tolerance': 5.0}`.

- Phases _triang : `AngleBetween_triang   convert: 810 → 760   mid: 123664 → 123664   convert_narrow: 760 → 760   narrow: 123664 → 53187   (0.266 s)`
- Phases origine : `AngleBetween   convert: 810 → 810   mid: 149864 → 149864   narrow: 149864 → 64784   (4.930 s)`
- Écarts par cause : 11534 absent du .ifcview, 2499 axe principal ambigu, 288 OBB optimale non unique, 44 seuils à ± marge
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (12981) :

- IfcSpace #67 A102 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #1627 B102 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #1782 B103 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #3197 A205 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #3325 B205 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #3797 Basic Wall:Exterior - Brick on Block:138062 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4043 Basic Wall:Exterior - Brick on Block:138237 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4287 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139234 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139347 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4553 Basic Wall:Interior - Partition (92mm Stud):139783 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4643 Basic Wall:Foundation - Concrete (417mm):140479 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4868 Basic Wall:Foundation - Concrete (417mm):140554 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4968 Basic Wall:Foundation - Concrete (435mm):140913 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5057 Basic Wall:Foundation - Concrete (435mm):140987 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5548 Basic Wall:Exterior - Brick on Block:143534 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5642 Basic Wall:Interior - Partition (92mm Stud):143856 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5731 Basic Wall:Interior - Partition (92mm Stud):143960 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5775 Basic Wall:Interior - Plumbing (152mm Stud):144138 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5859 Basic Wall:Interior - Partition (92mm Stud):144301 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5903 Basic Wall:Interior - Partition (92mm Stud):144518 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5992 Basic Wall:Interior - Partition (92mm Stud):144633 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #6036 Basic Wall:Interior - Partition (92mm Stud):144684 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #6080 Basic Wall:Interior - Plumbing (152mm Stud):144783 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #70 A203 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #223 B202 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #424 A201 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #581 A202 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #730 B203 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #931 B201 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #1080 B204 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #1308 A204 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #1635 A101 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2158 B101 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2604 B104 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2747 B101 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #3048 B104 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #3154 A101 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #3454 A104 — distance None — expliqué : absent du .ifcview
- ... 12941 de plus

En plus (1384) :

- IfcSpace #355 A104 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #514 A101 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #819 A201 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #1059 A204 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #1218 A203 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #1442 A202 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #1928 B104 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #2108 B101 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #2412 B201 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #2637 B204 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #2789 B203 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #3013 B202 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #3456 A105 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #3586 B105 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #3707 R301 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #3999 Basic Wall:Exterior - Brick on Block:138157 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4087 Basic Wall:Exterior - Brick on Block:138310 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4131 Basic Wall:Interior - Partition (92mm Stud):138584 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4219 Basic Wall:Interior - Partition (92mm Stud):139143 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4465 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139374 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4508 Basic Wall:Interior - Partition (92mm Stud):139682 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4598 Basic Wall:Interior - Partition (92mm Stud):139939 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4818 Basic Wall:Foundation - Concrete (417mm):140520 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #4918 Basic Wall:Foundation - Concrete (417mm):140602 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5106 Basic Wall:Foundation - Concrete (435mm):141018 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSlab #5267 Floor:127mm Slab on Grade:143106 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5598 Basic Wall:Exterior - Brick on Block:143590 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5687 Basic Wall:Interior - Partition (92mm Stud):143921 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWallStandardCase #5948 Basic Wall:Interior - Partition (92mm Stud):144586 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcDoor #6652 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcDoor #6757 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWindow #6921 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcWindow #7025 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcDoor #8066 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcDoor #8169 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257 → IfcFlowFitting #118929 M_Elbow - Generic:Standard:Standard:606592 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- ... 1344 de plus

## ObbHigh_triang

Paramètres : `{'length_min': 0.0, 'length_max': 1000000000.0}`.

- Phases _triang : `ObbHigh_triang   convert: 810 → 760   narrow: 760 → 760   (0.041 s)`
- Phases origine : `ObbHigh   convert: 810 → 810   narrow: 810 → 810   (4.989 s)`
- Mesures comparées sur 760 éléments communs : 0 écart(s) au-delà de 0.011 m
- Écarts par cause : 50 absent du .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (50) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7497 M_Casement:819mm x 759mm:819mm x 759mm:148607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7885 M_Casement:819mm x 759mm:819mm x 759mm:149736:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8372 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150478:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15885 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16101 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21705 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171853:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21915 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171975:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22070 M_Fixed:819mm x 759mm:819mm x 759mm:180864:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22122 M_Casement:819mm x 759mm:819mm x 759mm:180994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 — distance None — expliqué : absent du .ifcview
- ... 10 de plus

## ObbLength_triang

Paramètres : `{'length_min': 0.0, 'length_max': 1000000000.0, 'direction_method': 'Narrow'}`.

- Phases _triang : `ObbLength_triang   convert: 810 → 760   narrow: 760 → 760   (0.044 s)`
- Phases origine : `ObbLength   convert: 810 → 810   narrow: 810 → 810   (4.785 s)`
- Mesures comparées sur 760 éléments communs : 0 écart(s) au-delà de 0.011 m
- Écarts par cause : 50 absent du .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (50) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7497 M_Casement:819mm x 759mm:819mm x 759mm:148607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7885 M_Casement:819mm x 759mm:819mm x 759mm:149736:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8372 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150478:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15885 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16101 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21705 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171853:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21915 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171975:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22070 M_Fixed:819mm x 759mm:819mm x 759mm:180864:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22122 M_Casement:819mm x 759mm:819mm x 759mm:180994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 — distance None — expliqué : absent du .ifcview
- ... 10 de plus

## Orientation_triang

Paramètres : `{'orientation': [0.0, 0.0, 1.0], 'orientation_type': 'Perpendicular', 'direction_method': 'Wide', 'angular_tolerance': 0.1}`.

- Phases _triang : `Orientation_triang   convert: 810 → 760   narrow: 760 → 760   (0.150 s)`
- Phases origine : `Orientation   convert: 810 → 810   narrow: 810 → 810   (4.802 s)`
- Mesures comparées sur 760 éléments communs : 110 écart(s) au-delà de 1.0°
- Écarts par cause : 55 OBB optimale non unique, 55 même axe, sens opposé, 50 absent du .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (50) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7497 M_Casement:819mm x 759mm:819mm x 759mm:148607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7885 M_Casement:819mm x 759mm:819mm x 759mm:149736:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8372 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150478:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15885 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16101 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21705 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171853:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21915 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171975:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22070 M_Fixed:819mm x 759mm:819mm x 759mm:180864:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22122 M_Casement:819mm x 759mm:819mm x 759mm:180994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 — distance None — expliqué : absent du .ifcview
- ... 10 de plus

Mesures (110) :

- IfcRailing #9326 Railing:900mm Handrail Only:151162 — écart -23.5067 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcRailing #32346 Railing:900mm Handrail Only:198880 — écart 23.5066 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #7915 Pipe Types:Mechanical Pipe:540160 — écart 44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #8322 Pipe Types:Mechanical Pipe:540182 — écart -15.0016 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #11305 Pipe Types:Mechanical Pipe:546125 — écart -44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #11485 Pipe Types:Mechanical Pipe:546131 — écart 44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #12121 Pipe Types:Mechanical Pipe:546819 — écart 44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #12522 Pipe Types:Mechanical Pipe:546828 — écart -15.0016 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #13824 Pipe Types:Mechanical Pipe:546906 — écart 59.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #14004 Pipe Types:Mechanical Pipe:546969 — écart -44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #14185 Pipe Types:Mechanical Pipe:547114 — écart 29.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #14546 Pipe Types:Mechanical Pipe:547146 — écart 59.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #14823 Pipe Types:Mechanical Pipe:547150 — écart 59.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #15003 Pipe Types:Mechanical Pipe:547183 — écart 59.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #16606 Pipe Types:Mechanical Pipe:547784 — écart 44.9986 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #16786 Pipe Types:Mechanical Pipe:547802 — écart 44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #18537 Pipe Types:Mechanical Pipe:548082 — écart 59.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #18766 Pipe Types:Mechanical Pipe:548089 — écart 14.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #19786 Pipe Types:Mechanical Pipe:548835 — écart -14.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #19966 Pipe Types:Mechanical Pipe:549038 — écart -15.0016 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #20857 Pipe Types:Mechanical Pipe:549960 — écart 14.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #21037 Pipe Types:Mechanical Pipe:550018 — écart -14.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #21217 Pipe Types:Mechanical Pipe:550028 — écart 44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #21674 Pipe Types:Mechanical Pipe:550041 — écart 44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #22034 Pipe Types:Mechanical Pipe:550077 — écart 44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #36993 Pipe Types:Mechanical Pipe:554580 — écart 15.0016 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #37532 Pipe Types:Mechanical Pipe:555856 — écart 44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #39256 Pipe Types:Mechanical Pipe:557552 — écart -44.9989 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — écart 59.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #40317 Pipe Types:Mechanical Pipe:557564 — écart 44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #41953 Pipe Types:Mechanical Pipe:557586 — écart 29.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #43524 Pipe Types:Mechanical Pipe:557603 — écart -44.999 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #44417 Pipe Types:Mechanical Pipe:557612 — écart 15.0016 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #44646 Pipe Types:Mechanical Pipe:557614 — écart 59.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #45666 Pipe Types:Mechanical Pipe:557622 — écart -44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #45846 Pipe Types:Mechanical Pipe:557623 — écart 59.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #46590 Pipe Types:Mechanical Pipe:557646 — écart 14.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #46770 Pipe Types:Mechanical Pipe:557647 — écart 15.0016 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #47407 Pipe Types:Mechanical Pipe:557654 — écart 44.9984 — expliqué : même axe, sens opposé : le sens d'un axe d'OBB est arbitraire (angles supplémentaires)
- IfcFlowSegment #48045 Pipe Types:Mechanical Pipe:557685 — écart -59.9984 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- ... 70 de plus

## Alignement_triang

Paramètres : `{'axis': None, 'alignment_type': 'Plane', 'tolerance': 0.05, 'min_group': 3}`.

- Phases _triang : `Alignement_triang   convert: 810 → 760   narrow: 760 → 150   (0.501 s)`
- Phases origine : `Alignement   convert: 810 → 810   narrow: 810 → 158   (14.652 s)`
- Écarts par cause : 16 absent du .ifcview, 14 axe principal ambigu, 3 OBB optimale non unique, 2 groupe recomposé, 1 ensemble d'entrée différent
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (22) :

- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21705 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171853:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21915 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171975:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22382 M_Fixed:750mm x 2200mm:750mm x 2200mm:181930:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22434 M_Fixed:750mm x 2200mm:750mm x 2200mm:182101:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22506 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22520 — distance None — expliqué : absent du .ifcview
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 — distance None — expliqué : groupe recomposé : sans les éléments aux axes ambigus ou tournés, les deux règles donnent le même verdict
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 — distance None — expliqué : groupe recomposé : sans les éléments aux axes ambigus ou tournés, les deux règles donnent le même verdict
- IfcFlowFitting #93872 M_Elbow - Generic:Standard:Standard:600493 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #96459 M_Elbow - Generic:Standard:Standard:600509 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #115946 M_Rectangular to Round Transition - Angle:45 Degree:45 Degree:602990 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #116242 M_Rectangular to Round Transition - Angle:45 Degree:45 Degree:603490 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près

En plus (14) :

- IfcFurnishingElement #17532 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:167584 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFurnishingElement #17602 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:167655 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFurnishingElement #17844 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:168379 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFurnishingElement #17873 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:168380 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSlab #22492 Basic Roof:Live Roof over Wood Joist Flat Roof:184483 — distance None — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #36497 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206283 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFurnishingElement #36526 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206502 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFurnishingElement #36555 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206675 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFurnishingElement #36584 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206876 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowSegment #36635 Pipe Types:Mechanical Pipe:554197 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowSegment #40138 Pipe Types:Mechanical Pipe:557563 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowSegment #45055 Pipe Types:Mechanical Pipe:557617 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #70898 M_Elbow - Generic:Standard:Standard:581029 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #135092 M_Elbow - Generic:Standard:Standard:631971 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près

## Clearance_triang

Paramètres : `{'clearance': 0.5, 'check_all': True}`.

- Phases _triang : `Clearance_triang   convert: 810 → 760   broad: 123664 → 6404   mid: 6404 → 6404   convert_narrow: 753 → 753   narrow: 6404 → 5868   (0.551 s)`
- Phases origine : `Clearance   convert: 810 → 810   broad: 149864 → 6835   mid: 6835 → 6803   narrow: 6803 → 6244   (1.765 s)`
- Écarts par cause : 376 absent du .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (376) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2329 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcSpace #2869 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowSegment #39016 Pipe Types:Mechanical Pipe:557550 — distance 0.122 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowFitting #39068 M_Elbow - Generic:Standard:Standard:557551 — distance 0.125 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowSegment #43524 Pipe Types:Mechanical Pipe:557603 — distance 0.1257 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowSegment #144732 Pipe Types:Mechanical Pipe:633360 — distance 0.122 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowFitting #147550 M_Tee - Generic:Standard:Standard:633378 — distance 0.1245 — expliqué : absent du .ifcview
- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 → IfcFlowSegment #147721 Pipe Types:Mechanical Pipe:633379 — distance 0.122 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #1812 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcSpace #3365 A102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowSegment #11125 Pipe Types:Mechanical Pipe:545888 — distance 0.212 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowFitting #50477 M_Elbow - Generic:Standard:Standard:577966 — distance 0.2147 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowSegment #51691 Pipe Types:Mechanical Pipe:577991 — distance 0.2143 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowSegment #132471 Pipe Types:Mechanical Pipe:631911 — distance 0.212 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowFitting #132513 M_Tee - Generic:Standard:Standard:631966 — distance 0.2144 — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 → IfcFlowSegment #132684 Pipe Types:Mechanical Pipe:631967 — distance 0.212 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcSpace #1635 A101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 → IfcSpace #3154 A101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcSpace #2158 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 → IfcSpace #2747 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2329 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2462 B103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2869 B102 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcSpace #2959 B103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowSegment #8141 Pipe Types:Mechanical Pipe:540175 — distance 0.4874 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowSegment #14004 Pipe Types:Mechanical Pipe:546969 — distance 0.4352 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowSegment #14366 Pipe Types:Mechanical Pipe:547121 — distance 0.4707 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowSegment #14546 Pipe Types:Mechanical Pipe:547146 — distance 0.491 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowFitting #14598 M_Elbow - Generic:Standard:Standard:547147 — distance 0.4376 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowFitting #14646 M_Tee - Generic:Standard:Standard:547149 — distance 0.4855 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowSegment #14823 Pipe Types:Mechanical Pipe:547150 — distance 0.4973 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcEnergyConversionDevice #37718 M_Radiator - Hosted:25:25:557520 — distance 0.4948 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowSegment #39256 Pipe Types:Mechanical Pipe:557552 — distance 0.3421 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowSegment #43704 Pipe Types:Mechanical Pipe:557604 — distance 0.4452 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowSegment #43882 Pipe Types:Mechanical Pipe:557605 — distance 0.4064 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowFitting #48993 M_Elbow - Generic:Standard:Standard:577791 — distance 0.4934 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowSegment #111851 Pipe Types:Mechanical Pipe:601282 — distance 0.4064 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowFitting #111906 M_Elbow - Generic:Standard:Standard:601283 — distance 0.41 — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 → IfcFlowFitting #113202 M_Elbow - Generic:Standard:Standard:601288 — distance 0.4088 — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 → IfcSpace #1812 A102 — distance 0.0 — expliqué : absent du .ifcview
- ... 336 de plus

## Collision_triang

Paramètres : `{'allow_touching': False}`.

- Phases _triang : `Collision_triang   convert: 810 → 760   broad: 123664 → 1454   mid: 1454 → 1454   convert_narrow: 691 → 691   narrow: 1454 → 479   (0.105 s)`
- Phases origine : `Collision   convert: 810 → 810   broad: 149864 → 1600   mid: 1600 → 1590   narrow: 1590 → 491   (1.200 s)`
- Écarts par cause : 23 maillage IFC ouvert, 22 absent du .ifcview, 21 géométries IFC au contact
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (39) :

- IfcSpace #1442 A202 → IfcEnergyConversionDevice #7704 M_Radiator - Hosted:25:25:538562 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWallStandardCase #4131 Basic Wall:Interior - Partition (92mm Stud):138584 → IfcSpace #2158 B101 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWallStandardCase #4219 Basic Wall:Interior - Partition (92mm Stud):139143 → IfcSpace #2158 B101 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcSpace #581 A202 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcSpace #3677 A202 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5548 Basic Wall:Exterior - Brick on Block:143534 → IfcSpace #70 A203 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5548 Basic Wall:Exterior - Brick on Block:143534 → IfcSpace #4491 A203 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5598 Basic Wall:Exterior - Brick on Block:143590 → IfcSpace #730 B203 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5598 Basic Wall:Exterior - Brick on Block:143590 → IfcSpace #3553 B203 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5642 Basic Wall:Interior - Partition (92mm Stud):143856 → IfcSpace #931 B201 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWallStandardCase #5642 Basic Wall:Interior - Partition (92mm Stud):143856 → IfcSpace #3845 B201 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWallStandardCase #5859 Basic Wall:Interior - Partition (92mm Stud):144301 → IfcSpace #223 B202 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5859 Basic Wall:Interior - Partition (92mm Stud):144301 → IfcSpace #4614 B202 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 → IfcSpace #931 B201 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 → IfcSpace #3845 B201 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 → IfcSpace #1635 A101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 → IfcSpace #1942 A103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 → IfcSpace #3154 A101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 → IfcSpace #3276 A103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcSpace #2158 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcSpace #2462 B103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcSpace #2747 B101 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcSpace #2959 B103 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 → IfcSpace #581 A202 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 → IfcSpace #3677 A202 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 → IfcSpace #931 B201 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 → IfcSpace #3845 B201 — distance 0.0 — expliqué : absent du .ifcview
- IfcFurnishingElement #16914 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162493 → IfcSpace #1812 A102 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcFurnishingElement #16914 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162493 → IfcSpace #3365 A102 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcFurnishingElement #16971 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162495 → IfcSpace #1812 A102 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcFurnishingElement #16971 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162495 → IfcSpace #3365 A102 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcOpeningElement #22506 → IfcSpace #931 B201 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22506 → IfcSpace #3845 B201 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22506 → IfcSpace #4722 A/B — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22506 → IfcSpace #4799 A/B — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22520 → IfcSpace #424 A201 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22520 → IfcSpace #4367 A201 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22520 → IfcSpace #4722 A/B — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22520 → IfcSpace #4799 A/B — distance 0.0 — expliqué : absent du .ifcview

En plus (27) :

- IfcSpace #212 A103 → IfcSpace #3154 A101 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcSpace #514 A101 → IfcSpace #1635 A101 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSpace #819 A201 → IfcSpace #424 A201 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSpace #819 A201 → IfcSpace #1635 A101 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSpace #819 A201 → IfcSpace #4367 A201 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSpace #1782 B103 → IfcSpace #2158 B101 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSpace #1782 B103 → IfcSpace #2747 B101 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcSpace #1928 B104 → IfcSpace #2604 B104 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcSpace #2108 B101 → IfcSpace #2158 B101 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSpace #2108 B101 → IfcSpace #2462 B103 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcSpace #2108 B101 → IfcSpace #2959 B103 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcSpace #2412 B201 → IfcSpace #931 B201 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSpace #2412 B201 → IfcSpace #3845 B201 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcSpace #730 B203 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcSpace #4614 B202 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWallStandardCase #5642 Basic Wall:Interior - Partition (92mm Stud):143856 → IfcSpace #730 B203 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5642 Basic Wall:Interior - Partition (92mm Stud):143856 → IfcSpace #3553 B203 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5687 Basic Wall:Interior - Partition (92mm Stud):143921 → IfcSpace #223 B202 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5687 Basic Wall:Interior - Partition (92mm Stud):143921 → IfcSpace #4614 B202 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5903 Basic Wall:Interior - Partition (92mm Stud):144518 → IfcSpace #70 A203 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5903 Basic Wall:Interior - Partition (92mm Stud):144518 → IfcSpace #4491 A203 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5948 Basic Wall:Interior - Partition (92mm Stud):144586 → IfcSpace #581 A202 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcWallStandardCase #5948 Basic Wall:Interior - Partition (92mm Stud):144586 → IfcSpace #3677 A202 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcSpace #2158 B101 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcFurnishingElement #16914 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162493 → IfcSpace #1635 A101 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcFurnishingElement #16914 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162493 → IfcSpace #3154 A101 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcSlab #21147 Floor:Finish Floor - Wood:169701 → IfcSpace #1635 A101 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration

## Volume_triang

Paramètres : `{'volume_min': 0.0, 'volume_max': 1000000000.0}`.

- Phases _triang : `Volume_triang   convert: 810 → 760   narrow: 760 → 760   (0.106 s)`
- Phases origine : `Volume   convert: 810 → 810   narrow: 810 → 810   (1.099 s)`
- Mesures comparées sur 760 éléments communs : 89 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 81 maillage IFC ouvert, 50 absent du .ifcview, 6 maillage _triang non fermé une fois réparé, 2 propre au maillage .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (50) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7497 M_Casement:819mm x 759mm:819mm x 759mm:148607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7885 M_Casement:819mm x 759mm:819mm x 759mm:149736:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8372 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150478:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15885 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16101 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21705 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171853:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21915 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171975:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22070 M_Fixed:819mm x 759mm:819mm x 759mm:180864:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22122 M_Casement:819mm x 759mm:819mm x 759mm:180994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 — distance None — expliqué : absent du .ifcview
- ... 10 de plus

Mesures (89) :

- IfcSpace #819 A201 — écart 17.3942 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcSpace #2412 B201 — écart 5.9865 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 — écart 23.7468 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcRailing #12184 Railing:1100mm Guard Rail:151166 — écart -2.2324 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #12574 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200 — écart 0.0768 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #12976 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607 — écart 0.0863 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #13331 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950 — écart 0.0768 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #13685 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951 — écart 0.0863 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #14040 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983 — écart -0.0573 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #14394 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984 — écart -0.0675 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.1529)
- IfcFurnishingElement #14749 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080 — écart -0.0573 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #15103 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081 — écart -0.0675 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.1529)
- IfcFurnishingElement #15463 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159159 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #15856 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159262 — écart -0.2381 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16149 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160671 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16175 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160717 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16485 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162230 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16563 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162311 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16589 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162357 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16615 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162383 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16641 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162486 — écart -0.4704 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcFurnishingElement #16667 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162487 — écart -0.2587 — expliqué : maillage IFC ouvert : volume non défini pour l'original
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
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 — écart -4.4997 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 — écart -4.4997 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #23671 Compound Ceiling:Gypsum Board:187149 — écart -0.8384 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 — écart -6.1586 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 — écart -6.1586 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #23884 Compound Ceiling:Gypsum Board:187483 — écart -6.6981 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #23992 Compound Ceiling:Gypsum Board:187508 — écart -4.7294 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- IfcCovering #24060 Compound Ceiling:Gypsum Board:187639 — écart -38.4089 — expliqué : maillage IFC ouvert : volume non défini pour l'original
- ... 49 de plus

## Area_triang

Paramètres : `{'volume_min': 0.0, 'volume_max': 1000000000.0}`.

- Phases _triang : `Area_triang   convert: 810 → 760   narrow: 760 → 760   (0.108 s)`
- Phases origine : `Area   convert: 810 → 810   narrow: 810 → 810   (1.116 s)`
- Mesures comparées sur 760 éléments communs : 1 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 50 absent du .ifcview, 1 propre au maillage .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (50) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7497 M_Casement:819mm x 759mm:819mm x 759mm:148607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7885 M_Casement:819mm x 759mm:819mm x 759mm:149736:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8372 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150478:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15885 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16101 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21705 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171853:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21915 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171975:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22070 M_Fixed:819mm x 759mm:819mm x 759mm:180864:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22122 M_Casement:819mm x 759mm:819mm x 759mm:180994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 — distance None — expliqué : absent du .ifcview
- ... 10 de plus

Mesures (1) :

- IfcFurnishingElement #16802 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490 — écart 0.2619 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (4.3916)

## TopOrBottomSurface_triang

Paramètres : `{'surface_min': 0.0, 'surface_max': 1000000000.0, 'top_or_bot_method': 'Top'}`.

- Phases _triang : `TopOrBottomSurface_triang   convert: 810 → 760   narrow: 760 → 759   (1.308 s)`
- Phases origine : `TopOrBottomSurface   convert: 810 → 810   narrow: 810 → 704   (5.134 s)`
- Mesures comparées sur 654 éléments communs : 49 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 125 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 50 absent du .ifcview, 28 maillage _triang non fermé une fois réparé, 1 propre au maillage .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (50) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7497 M_Casement:819mm x 759mm:819mm x 759mm:148607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7885 M_Casement:819mm x 759mm:819mm x 759mm:149736:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8372 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150478:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15885 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16101 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21705 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171853:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21915 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171975:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22070 M_Fixed:819mm x 759mm:819mm x 759mm:180864:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22122 M_Casement:819mm x 759mm:819mm x 759mm:180994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 — distance None — expliqué : absent du .ifcview
- ... 10 de plus

En plus (105) :

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
- ... 65 de plus

Mesures (49) :

- IfcRailing #12184 Railing:1100mm Guard Rail:151166 — écart -0.0456 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #12574 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200 — écart 0.1929 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #12976 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607 — écart 0.1971 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #13331 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950 — écart 0.1929 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #13685 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951 — écart 0.1971 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #16802 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490 — écart 0.1616 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (1.7134)
- IfcFurnishingElement #17341 M_Sofa:1830mm:1830mm:167283 — écart 1.1931 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #17409 M_Sofa:1830mm:1830mm:167426 — écart 1.1931 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #17786 M_Sofa:1830mm:1830mm:168377 — écart 1.1931 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #17815 M_Sofa:1830mm:1830mm:168378 — écart 1.1931 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #19275 M_Bed-Standard:1525 x 2007mm - Queen:1525 x 2007mm - Queen:168449 — écart 3.4086 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20657 M_Bed-Standard:1981 x 2032mm - King:1981 x 2032mm - King:168717 — écart 4.4892 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20726 M_Bed-Standard:1981 x 2032mm - King:1981 x 2032mm - King:168914 — écart 4.4892 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20755 M_Bed-Standard:1525 x 2007mm - Queen:1525 x 2007mm - Queen:169008 — écart 3.4086 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #26941 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191401 — écart 0.3189 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #29098 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191557 — écart 0.3189 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #29127 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191680 — écart 0.3189 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31241 M_Upper Cabinet-Double Door-Wall:1000mm:1000mm:191768 — écart 0.3189 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31313 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192153 — écart 0.3304 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31342 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192331 — écart 0.3304 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31371 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192508 — écart 0.3304 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #31400 M_Upper Cabinet-Double Door-Wall:1000mm:1000mm:192610 — écart 0.3304 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcRailing #35163 Railing:1100mm Guard Rail:198972 — écart -0.0594 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcEnergyConversionDevice #6246 M_Hot Water Boiler - 59-440 kW:147 kW:147 kW:530072 — écart 0.2425 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcEnergyConversionDevice #6651 M_Radiator - Hosted:25:25:535063 — écart 0.2365 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7034 M_Radiator - Hosted:25:25:536357 — écart 0.2061 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7369 M_Radiator - Hosted:25:25:536919 — écart 0.279 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7704 M_Radiator - Hosted:25:25:538562 — écart 0.4511 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7747 M_Radiator - Hosted:25:25:538847 — écart 0.2061 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #19618 M_Radiator - Hosted:25:25:548240 — écart 0.1049 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #20313 M_Radiator - Hosted:25:25:549304 — écart 0.1049 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFlowMovingDevice #32595 M_Inline Pump - Circulator:3.9 LPS - 0.8 Meter Head:3.9 LPS - 0.8 Meter Head:550094 — écart -0.0156 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcEnergyConversionDevice #37587 M_Hot Water Boiler - 59-440 kW:147 kW:147 kW:557516 — écart 0.2423 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcEnergyConversionDevice #37633 M_Radiator - Hosted:25:25:557517 — écart 0.2365 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37676 M_Radiator - Hosted:25:25:557519 — écart 0.2061 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37718 M_Radiator - Hosted:25:25:557520 — écart 0.279 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37761 M_Radiator - Hosted:25:25:557522 — écart 0.4511 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #37804 M_Radiator - Hosted:25:25:557524 — écart 0.2061 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #45498 M_Radiator - Hosted:25:25:557620 — écart 0.1049 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #46193 M_Radiator - Hosted:25:25:557628 — écart 0.1049 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- ... 9 de plus

## LateralSurface_triang

Paramètres : `{'surface_min': 0.0, 'surface_max': 1000000000.0, 'direction': [0.0, 1.0, 0.0]}`.

- Phases _triang : `LateralSurface_triang   convert: 810 → 760   narrow: 760 → 760   (0.101 s)`
- Phases origine : `LateralSurface   convert: 810 → 810   narrow: 810 → 792   (3.384 s)`
- Mesures comparées sur 742 éléments communs : 74 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 60 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 50 absent du .ifcview, 31 maillage _triang non fermé une fois réparé, 1 propre au maillage .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (50) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7497 M_Casement:819mm x 759mm:819mm x 759mm:148607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7885 M_Casement:819mm x 759mm:819mm x 759mm:149736:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8372 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150478:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15885 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16101 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21705 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171853:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21915 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171975:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22070 M_Fixed:819mm x 759mm:819mm x 759mm:180864:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22122 M_Casement:819mm x 759mm:819mm x 759mm:180994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 — distance None — expliqué : absent du .ifcview
- ... 10 de plus

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

Mesures (74) :

- IfcSpace #819 A201 — écart -5.3804 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcSpace #2412 B201 — écart -5.3804 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 — écart -0.2958 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcRailing #12184 Railing:1100mm Guard Rail:151166 — écart -1.4927 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #12574 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200 — écart 1.3716 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #12976 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607 — écart 1.3047 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #13331 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950 — écart 1.3716 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #13685 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951 — écart 1.3047 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #14040 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983 — écart 0.1013 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #14749 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080 — écart 0.1013 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #16485 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162230 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16563 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162311 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16589 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162357 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16615 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162383 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16641 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162486 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16667 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162487 — écart -2.2772 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #16693 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162488 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16719 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162489 — écart -2.2772 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFurnishingElement #16802 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490 — écart -0.0149 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.4397)
- IfcFurnishingElement #17409 M_Sofa:1830mm:1830mm:167426 — écart 0.1042 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #17815 M_Sofa:1830mm:1830mm:168378 — écart -0.1042 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20657 M_Bed-Standard:1981 x 2032mm - King:1981 x 2032mm - King:168717 — écart -0.6915 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #20726 M_Bed-Standard:1981 x 2032mm - King:1981 x 2032mm - King:168914 — écart 0.6916 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 — écart -0.1016 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 — écart -0.1016 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
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
- IfcFurnishingElement #26941 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191401 — écart -1.0942 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFurnishingElement #29098 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191557 — écart -1.0942 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- ... 34 de plus

## ProjectedSurface_triang

Paramètres : `{'surface_min': 0.0, 'surface_max': 1000000000.0, 'direction': [0.0, 0.0, 1.0]}`.

- Phases _triang : `ProjectedSurface_triang   convert: 810 → 760   narrow: 760 → 760   (0.477 s)`
- Phases origine : `ProjectedSurface   convert: 810 → 810   narrow: 810 → 706   (3.540 s)`
- Mesures comparées sur 656 éléments communs : 43 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 124 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 50 absent du .ifcview, 22 maillage _triang non fermé une fois réparé, 1 propre au maillage .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (50) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7497 M_Casement:819mm x 759mm:819mm x 759mm:148607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7885 M_Casement:819mm x 759mm:819mm x 759mm:149736:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8372 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150478:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15885 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16101 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21705 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171853:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21915 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171975:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22070 M_Fixed:819mm x 759mm:819mm x 759mm:180864:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22122 M_Casement:819mm x 759mm:819mm x 759mm:180994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 — distance None — expliqué : absent du .ifcview
- ... 10 de plus

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

Mesures (43) :

- IfcFurnishingElement #16802 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490 — écart 0.1616 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (1.7134)
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
- IfcEnergyConversionDevice #6246 M_Hot Water Boiler - 59-440 kW:147 kW:147 kW:530072 — écart 0.2652 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcEnergyConversionDevice #6651 M_Radiator - Hosted:25:25:535063 — écart 0.1303 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7034 M_Radiator - Hosted:25:25:536357 — écart 0.1136 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7369 M_Radiator - Hosted:25:25:536919 — écart 0.1536 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7704 M_Radiator - Hosted:25:25:538562 — écart 0.2481 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #7747 M_Radiator - Hosted:25:25:538847 — écart 0.1136 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #19618 M_Radiator - Hosted:25:25:548240 — écart 0.0581 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcEnergyConversionDevice #20313 M_Radiator - Hosted:25:25:549304 — écart 0.0581 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original filtre les triangles sur leur normale
- IfcFlowMovingDevice #32595 M_Inline Pump - Circulator:3.9 LPS - 0.8 Meter Head:3.9 LPS - 0.8 Meter Head:550094 — écart 0.0186 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcEnergyConversionDevice #37587 M_Hot Water Boiler - 59-440 kW:147 kW:147 kW:557516 — écart 0.2652 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
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
- ... 3 de plus

## ClearanceAxisToAxis_triang

Paramètres : `{'mode': 'MinDistance', 'min_distance': 0.2, 'max_distance': 5.0, 'tolerance': 0.01, 'linearity_ratio': 1.5, 'on_non_linear': 'Fallback', 'parallel_tolerance': 5.0, 'search_radius': 2.0}`.

- Phases _triang : `ClearanceAxisToAxis_triang   convert: 200 → 187   mid: 8700 → 8700   convert_narrow: 187 → 187   narrow: 8700 → 149   (0.228 s)`
- Phases origine : `ClearanceAxisToAxis   convert: 200 → 200   mid: 10000 → 10000   narrow: 10000 → 157   (75.700 s)`
- Écarts par cause : 8 absent du .ifcview
- 13 élément(s) absent(s) du .ifcview, ignorés (ex. #6743 1xS3BCk291UvhgP2dvNrZJ is not in the .ifcview: skipped)

Manquants (8) :

- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 → IfcSpace #70 A203 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 → IfcSpace #2462 B103 — distance 0.1005 — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 → IfcEnergyConversionDevice #37761 M_Radiator - Hosted:25:25:557522 — distance 0.1031 — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 → IfcSpace #3677 A202 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 → IfcEnergyConversionDevice #7704 M_Radiator - Hosted:25:25:538562 — distance 0.0399 — expliqué : absent du .ifcview
- IfcOpeningElement #22330 M_Fixed:819mm x 759mm:819mm x 759mm:181583:1 → IfcSpace #3677 A202 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22330 M_Fixed:819mm x 759mm:819mm x 759mm:181583:1 → IfcEnergyConversionDevice #7704 M_Radiator - Hosted:25:25:538562 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22533 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:2 → IfcSpace #4799 A/B — distance 0.0 — expliqué : absent du .ifcview

## SurfaceRecover_triang

Paramètres : `{'direction': 'Auto', 'reference': 'Source', 'tolerance': 0.01, 'min_covering': ['relative', 101.0], 'max_covering': None}`.

- Phases _triang : `SurfaceRecover_triang   convert: 810 → 760   broad: 123664 → 2281   mid: 2281 → 2281   convert_narrow: 742 → 742   narrow: 2281 → 181   (0.277 s)`
- Phases origine : `SurfaceRecover   convert: 810 → 810   broad: 149864 → 2446   mid: 2446 → 2446   narrow: 2446 → 58   (37.284 s)`
- Écarts par cause : 124 seuils à ± marge, 1 contact marginal
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (1) :

- IfcSpace #514 A101 → IfcEnergyConversionDevice #7747 M_Radiator - Hosted:25:25:538847 — distance 0.0 — expliqué : contact marginal : 2.9e-04 m² (0.01 % de la face), bande de largeur équivalente 0.2 mm < marge

En plus (124) :

- IfcSpace #67 A102 → IfcSpace #1635 A101 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1627 B102 → IfcSpace #2158 B101 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1627 B102 → IfcSpace #2747 B101 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2108 B101 → IfcSpace #2329 B102 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #3797 Basic Wall:Exterior - Brick on Block:138062 → IfcSpace #2158 B101 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #3797 Basic Wall:Exterior - Brick on Block:138062 → IfcSpace #2329 B102 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #3797 Basic Wall:Exterior - Brick on Block:138062 → IfcEnergyConversionDevice #37804 M_Radiator - Hosted:25:25:557524 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #3999 Basic Wall:Exterior - Brick on Block:138157 → IfcSpace #424 A201 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #3999 Basic Wall:Exterior - Brick on Block:138157 → IfcSpace #4367 A201 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #3999 Basic Wall:Exterior - Brick on Block:138157 → IfcEnergyConversionDevice #37718 M_Radiator - Hosted:25:25:557520 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #3999 Basic Wall:Exterior - Brick on Block:138157 → IfcEnergyConversionDevice #127046 M_Radiator - Hosted:25:25:629670 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4043 Basic Wall:Exterior - Brick on Block:138237 → IfcSpace #1635 A101 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4043 Basic Wall:Exterior - Brick on Block:138237 → IfcSpace #1812 A102 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4043 Basic Wall:Exterior - Brick on Block:138237 → IfcSpace #3154 A101 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4043 Basic Wall:Exterior - Brick on Block:138237 → IfcSpace #3365 A102 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4043 Basic Wall:Exterior - Brick on Block:138237 → IfcEnergyConversionDevice #7747 M_Radiator - Hosted:25:25:538847 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4087 Basic Wall:Exterior - Brick on Block:138310 → IfcSpace #2158 B101 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4087 Basic Wall:Exterior - Brick on Block:138310 → IfcEnergyConversionDevice #7369 M_Radiator - Hosted:25:25:536919 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4087 Basic Wall:Exterior - Brick on Block:138310 → IfcEnergyConversionDevice #136014 M_Radiator - Hosted:25:25:632215 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4131 Basic Wall:Interior - Partition (92mm Stud):138584 → IfcSpace #2329 B102 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4131 Basic Wall:Interior - Partition (92mm Stud):138584 → IfcEnergyConversionDevice #138736 M_Radiator - Hosted:25:25:632515 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4219 Basic Wall:Interior - Partition (92mm Stud):139143 → IfcSpace #2462 B103 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4219 Basic Wall:Interior - Partition (92mm Stud):139143 → IfcEnergyConversionDevice #45498 M_Radiator - Hosted:25:25:557620 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4287 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139234 → IfcSpace #1635 A101 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4508 Basic Wall:Interior - Partition (92mm Stud):139682 → IfcSpace #1942 A103 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4508 Basic Wall:Interior - Partition (92mm Stud):139682 → IfcEnergyConversionDevice #19618 M_Radiator - Hosted:25:25:548240 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4508 Basic Wall:Interior - Partition (92mm Stud):139682 → IfcFlowSegment #20628 Pipe Types:Mechanical Pipe:549955 — distance 0.005 — expliqué : seuils à ± marge
- IfcWallStandardCase #4508 Basic Wall:Interior - Partition (92mm Stud):139682 → IfcFlowSegment #21445 Pipe Types:Mechanical Pipe:550036 — distance 0.005 — expliqué : seuils à ± marge
- IfcWallStandardCase #4553 Basic Wall:Interior - Partition (92mm Stud):139783 → IfcSpace #3276 A103 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4598 Basic Wall:Interior - Partition (92mm Stud):139939 → IfcSpace #1812 A102 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4598 Basic Wall:Interior - Partition (92mm Stud):139939 → IfcEnergyConversionDevice #127088 M_Radiator - Hosted:25:25:630326 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4598 Basic Wall:Interior - Partition (92mm Stud):139939 → IfcFlowFitting #129253 M_Tee - Generic:Standard:Standard:631333 — distance 0.0051 — expliqué : seuils à ± marge
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcSpace #70 A203 — distance 0.0 — expliqué : seuils à ± marge
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcSpace #581 A202 — distance 0.0 — expliqué : seuils à ± marge
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcSpace #3677 A202 — distance 0.0 — expliqué : seuils à ± marge
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcSpace #4491 A203 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcSpace #581 A202 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #5448 Basic Wall:Exterior - Brick on Block:143410 → IfcSpace #730 B203 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcEnergyConversionDevice #6651 M_Radiator - Hosted:25:25:535063 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #5498 Basic Wall:Exterior - Brick on Block:143478 → IfcEnergyConversionDevice #7034 M_Radiator - Hosted:25:25:536357 — distance 0.0 — expliqué : seuils à ± marge
- ... 84 de plus

## Ray_Check_triang

Paramètres : `{'max_ray_length': 5.0}`.

- Phases _triang : `Ray_Check_triang   convert: 810 → 760   broad: 123664 → 56450   mid: 56450 → 56450   convert_narrow: 760 → 760   narrow: 56450 → 540   (0.027 s)`
- Phases origine : `Ray_Check   convert: 810 → 810   broad: 149864 → 66719   mid: 66719 → 66719   narrow: 66719 → 539   (34.592 s)`
- Écarts par cause : 27 ensemble d'entrée différent, 26 absent du .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (26) :

- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 → IfcSpace #1942 A103 — distance 0.9333 — expliqué : absent du .ifcview
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 → IfcSpace #3276 A103 — distance 0.9254 — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 → IfcSpace #1942 A103 — distance 1.0348 — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 → IfcSpace #3276 A103 — distance 1.0278 — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 → IfcSpace #1942 A103 — distance 1.4676 — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 → IfcSpace #3276 A103 — distance 1.4627 — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 → IfcFlowSegment #21037 Pipe Types:Mechanical Pipe:550018 — distance 1.8427 — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 → IfcFlowFitting #21269 M_Elbow - Generic:Standard:Standard:550034 — distance 1.7773 — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 → IfcFlowFitting #51971 M_Elbow - Generic:Standard:Standard:578144 — distance 1.9239 — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 → IfcSpace #2462 B103 — distance 0.8583 — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 → IfcSpace #2959 B103 — distance 0.8498 — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 → IfcSpace #2462 B103 — distance 0.8123 — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 → IfcSpace #2959 B103 — distance 0.8032 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcSpace #2158 B101 — distance 1.9301 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcSpace #2747 B101 — distance 1.7031 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcEnergyConversionDevice #136014 M_Radiator - Hosted:25:25:632215 — distance 3.4006 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcFlowSegment #136181 Pipe Types:Mechanical Pipe:632407 — distance 3.0166 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcFlowSegment #136353 Pipe Types:Mechanical Pipe:632415 — distance 3.0164 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcFlowFitting #137825 M_Elbow - Generic:Standard:Standard:632430 — distance 2.9893 — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 → IfcFlowSegment #137995 Pipe Types:Mechanical Pipe:632436 — distance 3.894 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowSegment #11665 Pipe Types:Mechanical Pipe:546374 — distance 2.4811 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowSegment #18179 Pipe Types:Mechanical Pipe:547956 — distance 0.6814 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowSegment #18537 Pipe Types:Mechanical Pipe:548082 — distance 2.1171 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowFitting #18589 M_Tee - Generic:Standard:Standard:548088 — distance 2.4964 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcSpace #1942 A103 — distance 0.9952 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcSpace #3276 A103 — distance 0.9808 — expliqué : absent du .ifcview

En plus (27) :

- IfcWallStandardCase #4508 Basic Wall:Interior - Partition (92mm Stud):139682 → IfcFlowSegment #18358 Pipe Types:Mechanical Pipe:548047 — distance 0.5192 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #15856 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159262 → IfcSpace #2462 B103 — distance 1.8028 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #15856 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159262 → IfcSpace #2959 B103 — distance 1.786 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #16175 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160717 → IfcSpace #2462 B103 — distance 2.6821 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #16175 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160717 → IfcSpace #2959 B103 — distance 2.6709 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #16411 M_Counter Top:600mm Depth:600mm Depth:161646 → IfcSpace #2462 B103 — distance 2.5626 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #16411 M_Counter Top:600mm Depth:600mm Depth:161646 → IfcSpace #2959 B103 — distance 2.5577 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #16693 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162488 → IfcSpace #1942 A103 — distance 1.3518 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #16693 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162488 → IfcSpace #3276 A103 — distance 1.3294 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #16719 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162489 → IfcSpace #1942 A103 — distance 2.6821 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #16719 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162489 → IfcSpace #3276 A103 — distance 2.6709 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #16884 M_Counter Top:600mm Depth:600mm Depth:162491 → IfcSpace #1942 A103 — distance 2.5626 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #16884 M_Counter Top:600mm Depth:600mm Depth:162491 → IfcSpace #3276 A103 — distance 2.5577 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #17023 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162497 → IfcSpace #1942 A103 — distance 1.3291 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #17023 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162497 → IfcSpace #3276 A103 — distance 1.3063 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 → IfcSpace #4722 A/B — distance 3.8847 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 → IfcSpace #4799 A/B — distance 3.8847 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 → IfcFlowMovingDevice #115533 M_Centrifugal Fan -  Rooftop  - Upblast:991-1905 LPS:991-1905 LPS:602396 — distance 2.3381 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 → IfcSpace #4722 A/B — distance 3.873 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 → IfcSpace #4799 A/B — distance 3.873 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 → IfcFlowMovingDevice #115421 M_Centrifugal Fan -  Rooftop  - Upblast:991-1905 LPS:991-1905 LPS:602113 — distance 2.3231 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #26941 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191401 → IfcSpace #1942 A103 — distance 2.6125 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #26941 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191401 → IfcSpace #3276 A103 — distance 2.618 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #29098 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191557 → IfcSpace #1942 A103 — distance 1.2079 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #29098 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191557 → IfcSpace #3276 A103 — distance 1.2197 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #31313 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192153 → IfcSpace #2462 B103 — distance 2.6125 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #31313 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192153 → IfcSpace #2959 B103 — distance 2.618 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict

## OneObjectFace_triang

Paramètres : `{'distance': True, 'min_distance': 0.5, 'max_distance': None, 'intersection': True, 'intersection_tolerance': 0.0, 'orientation': False, 'angle': None, 'angle_tolerance': 0.0, 'face_a_selection': {'orientation': 'Top', 'extreme_faces': True}, 'face_b_selection': {'orientation': 'Bottom', 'extreme_faces': True}, 'skip_adjacent': True}`.

- Phases _triang : `OneObjectFace_triang   convert: 810 → 760   narrow: 760 → 126300   (45.940 s)`
- Phases origine : `OneObjectFace   convert: 810 → 810   narrow: 810 → 99005   (42.232 s)`
- Écarts par cause : 85 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 4 absent du .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (17) :

- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 — distance 0.04 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 — distance 0.04 — expliqué : absent du .ifcview
- IfcFurnishingElement #17341 M_Sofa:1830mm:1830mm:167283 — distance 0.3784 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #17409 M_Sofa:1830mm:1830mm:167426 — distance 0.3784 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #17786 M_Sofa:1830mm:1830mm:168377 — distance 0.3784 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #17815 M_Sofa:1830mm:1830mm:168378 — distance 0.3784 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcOpeningElement #22533 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:2 — distance 0.457 — expliqué : absent du .ifcview
- IfcOpeningElement #22546 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:3 — distance 0.457 — expliqué : absent du .ifcview
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

- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 — distance 0.0508 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 — distance 0.0508 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
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
- IfcFlowSegment #8503 Pipe Types:Mechanical Pipe:540200 — distance 0.4879 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #12343 Pipe Types:Mechanical Pipe:546826 — distance 0.3987 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #14366 Pipe Types:Mechanical Pipe:547121 — distance 0.4879 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #15213 Pipe Types:Mechanical Pipe:547247 — distance 0.4052 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #15592 Pipe Types:Mechanical Pipe:547273 — distance 0.4054 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #19618 M_Radiator - Hosted:25:25:548240 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #20313 M_Radiator - Hosted:25:25:549304 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #37633 M_Radiator - Hosted:25:25:557517 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #37676 M_Radiator - Hosted:25:25:557519 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #37718 M_Radiator - Hosted:25:25:557520 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #37761 M_Radiator - Hosted:25:25:557522 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #37804 M_Radiator - Hosted:25:25:557524 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #38513 Pipe Types:Mechanical Pipe:557530 — distance 0.4952 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #40138 Pipe Types:Mechanical Pipe:557563 — distance 0.495 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #41136 Pipe Types:Mechanical Pipe:557570 — distance 0.4952 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #45498 M_Radiator - Hosted:25:25:557620 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcEnergyConversionDevice #46193 M_Radiator - Hosted:25:25:557628 — distance 0.3556 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #48942 Pipe Types:Mechanical Pipe:577748 — distance 0.4815 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #49626 Pipe Types:Mechanical Pipe:577870 — distance 0.4817 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #51920 Pipe Types:Mechanical Pipe:578143 — distance 0.4055 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #52147 Pipe Types:Mechanical Pipe:578188 — distance 0.4055 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #52422 Pipe Types:Mechanical Pipe:578228 — distance 0.3924 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #56474 Pipe Types:Mechanical Pipe:578435 — distance 0.0366 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFlowSegment #56833 Pipe Types:Mechanical Pipe:578485 — distance 0.0368 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- ... 32 de plus

## TwoObjectsFace_triang

Paramètres : `{'distance': True, 'min_distance': 0.3, 'max_distance': None, 'intersection': True, 'intersection_tolerance': 0.0, 'orientation': False, 'angle': None, 'angle_tolerance': 0.0, 'source_face_selection': {'orientation': 'Top', 'extreme_faces': True}, 'target_face_selection': {'orientation': 'Bottom'}}`.

- Phases _triang : `TwoObjectsFace_triang   convert: 810 → 760   broad: 123664 → 1905   mid: 1905 → 1905   convert_narrow: 572 → 572   narrow: 1905 → 112128   (65.675 s)`
- Phases origine : `TwoObjectsFace   convert: 810 → 773   broad: 131022 → 2195   mid: 2195 → 2195   narrow: 2195 → 117643   (80.396 s)`
- Écarts par cause : 282 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 22 absent du .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (219) :

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
- ... 179 de plus

En plus (85) :

- IfcWallStandardCase #4287 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139234 → IfcFlowFitting #39716 M_Elbow - Generic:Standard:Standard:557556 — distance 0.2967 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSlab #22492 Basic Roof:Live Roof over Wood Joist Flat Roof:184483 → IfcFlowFitting #115946 M_Rectangular to Round Transition - Angle:45 Degree:45 Degree:602990 — distance 0.0635 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcSlab #22492 Basic Roof:Live Roof over Wood Joist Flat Roof:184483 → IfcFlowFitting #116242 M_Rectangular to Round Transition - Angle:45 Degree:45 Degree:603490 — distance 0.001 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 → IfcSpace #4722 A/B — distance 0.1778 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 → IfcSpace #4799 A/B — distance 0.1778 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 → IfcSpace #4722 A/B — distance 0.1778 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 → IfcSpace #4799 A/B — distance 0.1778 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23671 Compound Ceiling:Gypsum Board:187149 → IfcFlowSegment #152559 Pipe Types:Mechanical Pipe:662976 — distance 0.2667 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #39664 Pipe Types:Mechanical Pipe:557555 — distance 0.0628 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #39716 M_Elbow - Generic:Standard:Standard:557556 — distance 0.2971 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #44417 Pipe Types:Mechanical Pipe:557612 — distance 0.0414 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #44469 M_Tee - Generic:Standard:Standard:557613 — distance 0.0113 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #44646 Pipe Types:Mechanical Pipe:557614 — distance 0.0127 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #44826 Pipe Types:Mechanical Pipe:557615 — distance 0.0127 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #44878 M_Tee - Generic:Standard:Standard:557616 — distance 0.0083 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #45055 Pipe Types:Mechanical Pipe:557617 — distance 0.0127 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #45107 M_Elbow - Generic:Standard:Standard:557618 — distance 0.0163 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #45155 M_Elbow - Generic:Standard:Standard:557619 — distance 0.043 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #46361 Pipe Types:Mechanical Pipe:557644 — distance 0.1455 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #46413 M_Tee - Generic:Standard:Standard:557645 — distance 0.1265 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #46590 Pipe Types:Mechanical Pipe:557646 — distance 0.1807 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #46770 Pipe Types:Mechanical Pipe:557647 — distance 0.0246 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #47002 M_Elbow - Generic:Standard:Standard:557651 — distance 0.1338 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #47178 Pipe Types:Mechanical Pipe:557652 — distance 0.0127 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #47230 M_Tee - Generic:Standard:Standard:557653 — distance 0.0083 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #47407 Pipe Types:Mechanical Pipe:557654 — distance 0.0127 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #47587 Pipe Types:Mechanical Pipe:557655 — distance 0.0146 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #47819 M_Elbow - Generic:Standard:Standard:557660 — distance 0.0148 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #60605 Pipe Types:Mechanical Pipe:578830 — distance 0.0375 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #60656 M_Elbow - Generic:Standard:Standard:578831 — distance 0.0182 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #60832 Pipe Types:Mechanical Pipe:578872 — distance 0.0375 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowFitting #60883 M_Elbow - Generic:Standard:Standard:578873 — distance 0.0149 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #39664 Pipe Types:Mechanical Pipe:557555 — distance 0.0628 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowFitting #39716 M_Elbow - Generic:Standard:Standard:557556 — distance 0.2971 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #44417 Pipe Types:Mechanical Pipe:557612 — distance 0.0414 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowFitting #44469 M_Tee - Generic:Standard:Standard:557613 — distance 0.0113 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #44646 Pipe Types:Mechanical Pipe:557614 — distance 0.0127 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #44826 Pipe Types:Mechanical Pipe:557615 — distance 0.0127 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowFitting #44878 M_Tee - Generic:Standard:Standard:557616 — distance 0.0083 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #45055 Pipe Types:Mechanical Pipe:557617 — distance 0.0127 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- ... 45 de plus

## FreeSpace_triang

Paramètres : `{'diameter': 1.0, 'height': 2.0}`.

- Phases _triang : `FreeSpace_triang   convert: 810 → 760   narrow: 760 → 760   (0.028 s)`
- Phases origine : `FreeSpace   convert: 810 → 810   narrow: 810 → 810   (6.284 s)`
- Écarts par cause : 50 absent du .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (50) :

- IfcOpeningElement #6293 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:145788:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6517 M_Fixed:4835mm x 2420mm:4835mm x 2420mm:146016:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6569 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146596:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6743 M_Single-Flush:1250mm x 2010mm:1250mm x 2010mm:146678:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #6794 M_Fixed:750mm x 2200mm:750mm x 2200mm:146885:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7011 M_Fixed:750mm x 2200mm:750mm x 2200mm:147051:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7280 M_Fixed:819mm x 759mm:819mm x 759mm:147994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7497 M_Casement:819mm x 759mm:819mm x 759mm:148607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7833 M_Fixed:819mm x 759mm:819mm x 759mm:149537:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7885 M_Casement:819mm x 759mm:819mm x 759mm:149736:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #7989 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150173:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8155 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:150257:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #8372 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150478:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #13694 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157951:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15112 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158081:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15885 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16101 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21705 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171853:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21915 M_Single-Glass 1:0813 x 2420mm:0813 x 2420mm:171975:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22070 M_Fixed:819mm x 759mm:819mm x 759mm:180864:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22122 M_Casement:819mm x 759mm:819mm x 759mm:180994:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 — distance None — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 — distance None — expliqué : absent du .ifcview
- ... 10 de plus
