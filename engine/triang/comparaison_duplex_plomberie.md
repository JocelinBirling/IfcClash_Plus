# Règles _triang contre règles d'origine
- Source : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifc` (286 éléments)
- Cible : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Plumbing.ifc` (499 éléments)
- Triangles des règles _triang : `ifcview` (.ifcview : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifcview`, `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Plumbing.ifcview`)
- Marge d'explication des écarts : 0.011 m (flèche .ifcview + flèche IFC)

25 règles `_triang`, une par processus (`compare_triang.py --rules`, 4 à 8 threads, une à la fois). **0 écart(s) inexpliqué(s).** ClearanceForDoors et Intersection2 ne sont plus portées ; DirectView est comparée à part (`comparaison_directview.md`).

OneObjectFace et TwoObjectsFace : 100 éléments par côté (sur toute la maquette, l'original dépasse 4 Go de mémoire, et la version _triang, qui reprend sa logique de faces, aussi).

Temps de l'origine : sa première exécution, froide (ouverture de session et conversion IFC comprises), lue ensuite dans le cache du comparateur (`build/engine/triang_original_cache`) : les règles d'origine ne changent pas, elles ne sont plus relancées. Ces premières exécutions ont tourné avec 2, 4 ou 8 threads selon les passes : les gains sont des ordres de grandeur. `_triang` : froid = ouverture de session et première exécution, chaud = la règle relancée dans la session.

| Règle | Origine | _triang | Communs | Manquants | En plus | Inexpliqués | Origine froid | _triang froid | _triang chaud | Gain froid |
|---|---|---|---|---|---|---|---|---|---|---|
| Intersection_triang | 572 | 572 | 562 | 10 | 10 | 0 | 4.36 s | 1.31 s | 0.42 s | ×3.3 |
| Above_triang | 876 | 986 | 851 | 25 | 135 | 0 | 69.21 s | 1.07 s | 0.15 s | ×65.0 |
| Below_triang | 601 | 668 | 565 | 36 | 103 | 0 | 57.59 s | 1.05 s | 0.13 s | ×54.9 |
| OBB_Above_triang | 1717 | 1701 | 1692 | 25 | 9 | 0 | 23.62 s | 1.28 s | 0.12 s | ×18.5 |
| OBB_Below_triang | 1165 | 1167 | 1154 | 11 | 13 | 0 | 15.12 s | 1.06 s | 0.10 s | ×14.2 |
| OBB_Front_And_Back_triang | 1255 | 1273 | 1245 | 10 | 28 | 0 | 29.29 s | 1.24 s | 0.10 s | ×23.6 |
| OBB_Custom_triang | 2131 | 2130 | 2117 | 14 | 13 | 0 | 26.41 s | 1.29 s | 0.15 s | ×20.5 |
| AngleBetween_triang | 53933 | 43411 | 39907 | 14026 | 3504 | 0 | 18.65 s | 2.11 s | 1.30 s | ×8.9 |
| ObbHigh_triang | 785 | 735 | 735 | 50 | 0 | 0 | 17.82 s | 0.70 s | 0.06 s | ×25.4 |
| ObbLength_triang | 785 | 735 | 735 | 50 | 0 | 0 | 17.34 s | 0.82 s | 0.06 s | ×21.2 |
| Orientation_triang | 785 | 735 | 735 | 50 | 0 | 0 | 17.85 s | 1.17 s | 0.06 s | ×15.3 |
| Alignement_triang | 185 | 188 | 147 | 38 | 41 | 0 | 39.18 s | 1.11 s | 0.11 s | ×35.5 |
| Clearance_triang | 4904 | 4839 | 4839 | 65 | 0 | 0 | 5.91 s | 1.96 s | 1.15 s | ×3.0 |
| Collision_triang | 382 | 380 | 378 | 4 | 2 | 0 | 4.34 s | 0.87 s | 0.03 s | ×5.0 |
| Volume_triang | 785 | 735 | 735 | 50 | 0 | 0 | 4.13 s | 0.98 s | 0.01 s | ×4.2 |
| Area_triang | 785 | 735 | 735 | 50 | 0 | 0 | 4.04 s | 0.97 s | 0.01 s | ×4.2 |
| TopOrBottomSurface_triang | 750 | 735 | 700 | 50 | 35 | 0 | 25.12 s | 19.29 s | 19.20 s | ×1.3 |
| LateralSurface_triang | 766 | 724 | 716 | 50 | 8 | 0 | 12.14 s | 1.00 s | 0.01 s | ×12.1 |
| ProjectedSurface_triang | 750 | 735 | 700 | 50 | 35 | 0 | 12.79 s | 2.59 s | 1.50 s | ×4.9 |
| ClearanceAxisToAxis_triang | 119 | 117 | 117 | 2 | 0 | 0 | 85.40 s | 0.82 s | 0.15 s | ×104.0 |
| SurfaceRecover_triang | 52 | 76 | 49 | 3 | 27 | 0 | 61.31 s | 1.40 s | 0.13 s | ×43.9 |
| Ray_Check_triang | 667 | 669 | 657 | 10 | 12 | 0 | 62.69 s | 2.19 s | 0.50 s | ×28.6 |
| OneObjectFace_triang | 110 | 108 | 104 | 6 | 4 | 0 | 13.10 s | 8.53 s | 7.77 s | ×1.5 |
| TwoObjectsFace_triang | 101 | 114 | 98 | 3 | 16 | 0 | 3.90 s | 3.46 s | 2.65 s | ×1.1 |
| FreeSpace_triang | 785 | 735 | 735 | 50 | 0 | 0 | 22.57 s | 1.67 s | 0.04 s | ×13.5 |

## Intersection_triang

Paramètres : `{'tolerance': 0.002}`.

- Phases _triang : `Intersection_triang   convert: 785 → 735   broad: 117764 → 902   mid: 902 → 902   convert_narrow: 481 → 481   narrow: 902 → 572   (0.586 s)`
- Phases origine : `Intersection   convert: 785 → 785   broad: 142714 → 909   mid: 909 → 908   narrow: 908 → 572   (3.799 s)`
- Écarts par cause : 10 maillage IFC ouvert, 6 absent du .ifcview, 3 géométries IFC au contact, 1 pénétration ≤ tolérance + marge
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (10) :

- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #80835 Pipe Types:Waste:582982 — distance 0.305 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowSegment #92551 Pipe Types:Waste:583041 — distance 0.305 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.2252 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 0.0352 — expliqué : absent du .ifcview
- IfcSlab #21497 Floor:Finish Floor - Ceramic Tile:171230 → IfcFlowTerminal #28561 M_Shower Stall - Rectangular:865 mmx815 mm - Private:865 mmx815 mm - Private:582914 — distance 0.013 — expliqué : pénétration 0.0130 ≤ tolérance + marge
- IfcOpeningElement #22506 → IfcSpace #125 R301 — distance 1.019 — expliqué : absent du .ifcview
- IfcOpeningElement #22520 → IfcSpace #125 R301 — distance 1.019 — expliqué : absent du .ifcview
- IfcOpeningElement #22533 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:2 → IfcSpace #125 R301 — distance 0.457 — expliqué : absent du .ifcview
- IfcOpeningElement #22546 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:3 → IfcSpace #125 R301 — distance 0.457 — expliqué : absent du .ifcview
- IfcCovering #23992 Compound Ceiling:Gypsum Board:187508 → IfcFlowFitting #199671 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605616 — distance 0.05 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration

En plus (10) :

- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowSegment #113186 Pipe Types:Hot Water:583217 — distance 0.0241 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowSegment #186965 Pipe Types:PVC:604361 — distance 0.55 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowSegment #191396 Pipe Types:PVC:604556 — distance 0.55 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcFurnishingElement #16802 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.2252 — expliqué : géométries IFC au contact : test de pénétration instable sur faces coïncidentes
- IfcFurnishingElement #16802 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 0.0352 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcCovering #23768 Compound Ceiling:Gypsum Board:187462 → IfcFlowSegment #76025 Pipe Types:Waste:582975 — distance 0.057 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #76025 Pipe Types:Waste:582975 — distance 0.057 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcCovering #24186 Compound Ceiling:Gypsum Board:187659 → IfcFlowSegment #130839 Pipe Types:Waste:583332 — distance 0.057 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcCovering #24326 Compound Ceiling:Gypsum Board:187675 → IfcFlowSegment #123108 Pipe Types:Waste:583319 — distance 0.057 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowTerminal #42713 M_Water Closet - Flush Tank:Private - 6.1 Lpf:Private - 6.1 Lpf:582925 — distance 0.1505 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration

## Above_triang

Paramètres : `{'above_type': 'Above_MaxToMin', 'tolerance': 1.0}`.

- Phases _triang : `Above_triang   convert: 785 → 735   broad: 117764 → 1712   mid: 1712 → 1712   convert_narrow: 618 → 618   narrow: 1712 → 986   (0.322 s)`
- Phases origine : `Above   convert: 785 → 785   broad: 142714 → 1735   mid: 1735 → 1735   narrow: 1735 → 876   (68.550 s)`
- Écarts par cause : 74 faux négatif de l'original : grille de rayons, 51 écart vertical au bord de [0, tolérance], 22 absent du .ifcview, 7 faux négatif de l'original, vérifié sur l'IFC, 4 seuils à ± marge, 2 géométrie du .ifcview différente de l'IFC
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (25) :

- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowTerminal #31535 M_Shower Stall - Rectangular:865 mmx815 mm - Private:865 mmx815 mm - Private:582917 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #5267 Floor:127mm Slab on Grade:143106 → IfcFlowTerminal #28561 M_Shower Stall - Rectangular:865 mmx815 mm - Private:865 mmx815 mm - Private:582914 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 → IfcSpace #125 R301 — distance 0.868 — expliqué : absent du .ifcview
- IfcOpeningElement #8372 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150478:1 → IfcSpace #125 R301 — distance 0.868 — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 → IfcFlowSegment #186843 Pipe Types:PVC:604332 — distance 0.6611 — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 → IfcFlowSegment #192269 Pipe Types:PVC:605354 — distance 0.6611 — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 → IfcFlowFitting #198294 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605365 — distance 0.66 — expliqué : absent du .ifcview
- IfcOpeningElement #15885 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734:1 → IfcSpace #125 R301 — distance 0.868 — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 → IfcSpace #125 R301 — distance 0.868 — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 → IfcSpace #125 R301 — distance 0.868 — expliqué : absent du .ifcview
- IfcOpeningElement #16101 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208:1 → IfcSpace #125 R301 — distance 0.868 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 0.0735 — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #22382 M_Fixed:750mm x 2200mm:750mm x 2200mm:181930:1 → IfcSpace #125 R301 — distance 0.6 — expliqué : absent du .ifcview
- IfcOpeningElement #22434 M_Fixed:750mm x 2200mm:750mm x 2200mm:182101:1 → IfcSpace #125 R301 — distance 0.6 — expliqué : absent du .ifcview
- IfcWallStandardCase #24680 Basic Wall:Interior - Furring (152 mm Stud):189901 → IfcFlowSegment #113186 Pipe Types:Hot Water:583217 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcOpeningElement #35241 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:203720:1 → IfcSpace #125 R301 — distance 0.868 — expliqué : absent du .ifcview
- IfcOpeningElement #35399 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:204034:1 → IfcSpace #125 R301 — distance 0.868 — expliqué : absent du .ifcview

En plus (135) :

- IfcSpace #67 A102 → IfcFlowSegment #191396 Pipe Types:PVC:604556 — distance 0.1159 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #67 A102 → IfcFlowSegment #191477 Pipe Types:PVC:604577 — distance 0.0457 — expliqué : faux négatif de l'original : sa grille de rayons (pas 3.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #92152 Pipe Types:Waste:583036 — distance 0.255 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.255 m au-dessus de la source en (4.72, -10.56)
- IfcSpace #212 A103 → IfcFlowSegment #110435 Pipe Types:Cold Water:583192 — distance 0.3999 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.399 m au-dessus de la source en (4.70, -10.37)
- IfcSpace #212 A103 → IfcFlowSegment #110745 Pipe Types:Cold Water:583197 — distance 0.4095 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.6 cm) passe à côté d'un objet de 0.6 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #112086 Pipe Types:Hot Water:583202 — distance 0.5095 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.4 cm) passe à côté d'un objet de 0.6 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #123108 Pipe Types:Waste:583319 — distance 0.1635 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.6 cm) passe à côté d'un objet de 4.8 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #191477 Pipe Types:PVC:604577 — distance 0.0457 — expliqué : faux négatif de l'original : sa grille de rayons (pas 3.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #199183 Pipe Types:PVC:605583 — distance 0.0458 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #355 A104 → IfcFlowSegment #518236 Pipe Types:Cold Water:642715 — distance 0.0047 — expliqué : écart vertical 0.0047 au bord de [0, tolérance]
- IfcSpace #355 A104 → IfcFlowSegment #518675 Pipe Types:Hot Water:642757 — distance 0.005 — expliqué : écart vertical 0.0050 au bord de [0, tolérance]
- IfcSpace #355 A104 → IfcFlowSegment #518846 Pipe Types:Cold Water:642822 — distance 0.4172 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.8 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSpace #355 A104 → IfcFlowSegment #519015 Pipe Types:Cold Water:642869 — distance 0.005 — expliqué : écart vertical 0.0050 au bord de [0, tolérance]
- IfcSpace #1627 B102 → IfcFlowSegment #186965 Pipe Types:PVC:604361 — distance 0.1159 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1782 B103 → IfcFlowSegment #81234 Pipe Types:Waste:582987 — distance 0.2621 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.260 m au-dessus de la source en (4.10, -7.43)
- IfcSpace #1782 B103 → IfcFlowSegment #109656 Pipe Types:Hot Water:583180 — distance 0.4901 — expliqué : faux négatif de l'original : sa grille de rayons (pas 2.7 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSpace #1782 B103 → IfcFlowSegment #113337 Pipe Types:Hot Water:583220 — distance 0.5095 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.4 cm) passe à côté d'un objet de 0.6 cm en plan
- IfcSpace #1782 B103 → IfcFlowSegment #130839 Pipe Types:Waste:583332 — distance 0.1613 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.6 cm) passe à côté d'un objet de 4.8 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #517268 Pipe Types:Cold Water:642079 — distance 0.4172 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.6 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #517708 Pipe Types:Hot Water:642220 — distance 0.5143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.4 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #517913 Pipe Types:Cold Water:642353 — distance 0.4143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.6 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #517994 Pipe Types:Hot Water:642376 — distance 0.5143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.3 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcWallStandardCase #4287 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139234 → IfcFlowSegment #109656 Pipe Types:Hot Water:583180 — distance 0.2951 — expliqué : faux négatif de l'original : sa grille de rayons (pas 2.7 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcWallStandardCase #4287 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139234 → IfcFlowSegment #113186 Pipe Types:Hot Water:583217 — distance 0.2938 — expliqué : géométrie du .ifcview différente de l'IFC : la cible n'a pas de surface à ce point dans l'IFC (ouverture non soustraite dans le .ifcview)
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #76025 Pipe Types:Waste:582975 — distance 0.005 — expliqué : écart vertical 0.0050 au bord de [0, tolérance]
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #93651 Pipe Types:Cold Water:583055 — distance 0.0025 — expliqué : écart vertical 0.0025 au bord de [0, tolérance]
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #117083 Pipe Types:Hot Water:583286 — distance 0.5898 — expliqué : faux négatif de l'original : sa grille de rayons (pas 3.5 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSlab #5267 Floor:127mm Slab on Grade:143106 → IfcFlowSegment #114351 Pipe Types:Hot Water:583239 — distance 0.767 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.1 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSlab #5267 Floor:127mm Slab on Grade:143106 → IfcFlowSegment #117695 Pipe Types:Hot Water:583299 — distance 0.5892 — expliqué : faux négatif de l'original : sa grille de rayons (pas 3.5 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowFitting #112879 M_Tee - Generic:Tee - Generic:Tee - Generic:583213 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowFitting #113108 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583216 — distance 0.0032 — expliqué : écart vertical 0.0032 au bord de [0, tolérance]
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowFitting #130916 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583536 — distance 0.0025 — expliqué : écart vertical 0.0025 au bord de [0, tolérance]
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #517268 Pipe Types:Cold Water:642079 — distance 0.0024 — expliqué : écart vertical 0.0024 au bord de [0, tolérance]
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #517708 Pipe Types:Hot Water:642220 — distance 0.0143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.4 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #517994 Pipe Types:Hot Water:642376 — distance 0.0143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.3 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #976791 Pipe Types:Hot Water:666333 — distance 0.7375 — expliqué : seuils à ± marge
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowFitting #109185 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583172 — distance 0.0032 — expliqué : écart vertical 0.0032 au bord de [0, tolérance]
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowSegment #109656 Pipe Types:Hot Water:583180 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowFitting #114034 M_Tee - Generic:Tee - Generic:Tee - Generic:583234 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowFitting #117768 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583305 — distance 0.0025 — expliqué : écart vertical 0.0025 au bord de [0, tolérance]
- ... 95 de plus

## Below_triang

Paramètres : `{'below_type': 'Below_MinToMax', 'tolerance': 1.0}`.

- Phases _triang : `Below_triang   convert: 785 → 735   broad: 117764 → 1192   mid: 1192 → 1174   convert_narrow: 412 → 412   narrow: 1174 → 668   (0.313 s)`
- Phases origine : `Below   convert: 785 → 785   broad: 142714 → 1202   mid: 1202 → 1177   narrow: 1177 → 601   (56.919 s)`
- Écarts par cause : 65 faux négatif de l'original : grille de rayons, 55 écart vertical au bord de [0, tolérance], 8 absent du .ifcview, 6 géométrie du .ifcview différente de l'IFC, 3 faux négatif de l'original, vérifié sur l'IFC, 2 faux positif de l'original
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (36) :

- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowSegment #113186 Pipe Types:Hot Water:583217 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcFurnishingElement #15463 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159159 → IfcFlowSegment #75696 Pipe Types:Waste:582962 — distance 0.3699 — expliqué : faux positif de l'original : son test « ray » coupe une droite infinie (cible sur la source)
- IfcFurnishingElement #16641 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162486 → IfcFlowSegment #208013 Pipe Types:Waste:612522 — distance 0.3699 — expliqué : faux positif de l'original : son test « ray » coupe une droite infinie (cible sur la source)
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowSegment #176366 Pipe Types:Hot Water:599791 — distance 0.0542 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowSegment #176448 Pipe Types:Hot Water:599795 — distance 0.2537 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowSegment #208013 Pipe Types:Waste:612522 — distance 0.1725 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 0.0016 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowFitting #855036 M_Transition - Generic:Transition - Generic:Transition - Generic:645830 — distance 0.0478 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowFitting #856851 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:645876 — distance 0.2457 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowFitting #857192 M_Transition - Generic:Transition - Generic:Transition - Generic:645881 — distance 0.0478 — expliqué : absent du .ifcview
- IfcSlab #21195 Floor:Finish Floor - Ceramic Tile:169772 → IfcFlowSegment #107942 Pipe Types:Hot Water:583153 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #21195 Floor:Finish Floor - Ceramic Tile:169772 → IfcFlowSegment #108329 Pipe Types:Hot Water:583159 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #21195 Floor:Finish Floor - Ceramic Tile:169772 → IfcFlowSegment #131223 Pipe Types:Hot Water:583557 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #21336 Floor:Finish Floor - Ceramic Tile:169866 → IfcFlowSegment #109112 Pipe Types:Hot Water:583171 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #21336 Floor:Finish Floor - Ceramic Tile:169866 → IfcFlowSegment #109506 Pipe Types:Hot Water:583177 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #21336 Floor:Finish Floor - Ceramic Tile:169866 → IfcFlowSegment #109817 Pipe Types:Hot Water:583183 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowSegment #109112 Pipe Types:Hot Water:583171 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowSegment #109506 Pipe Types:Hot Water:583177 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowSegment #109817 Pipe Types:Hot Water:583183 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowSegment #109894 Pipe Types:Hot Water:583184 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowSegment #110045 Pipe Types:Hot Water:583187 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowSegment #110206 Pipe Types:Hot Water:583189 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowSegment #110284 Pipe Types:Hot Water:583190 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowSegment #114112 Pipe Types:Hot Water:583235 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowSegment #107942 Pipe Types:Hot Water:583153 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowSegment #108021 Pipe Types:Hot Water:583154 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowSegment #108329 Pipe Types:Hot Water:583159 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowSegment #108406 Pipe Types:Hot Water:583160 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowSegment #108557 Pipe Types:Hot Water:583163 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowSegment #112957 Pipe Types:Hot Water:583214 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowSegment #113035 Pipe Types:Hot Water:583215 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowSegment #113186 Pipe Types:Hot Water:583217 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowSegment #130994 Pipe Types:Hot Water:583544 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowSegment #131072 Pipe Types:Hot Water:583550 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowSegment #131223 Pipe Types:Hot Water:583557 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]

En plus (103) :

- IfcSpace #1059 A204 → IfcFlowSegment #518236 Pipe Types:Cold Water:642715 — distance 0.0003 — expliqué : écart vertical 0.0003 au bord de [0, tolérance]
- IfcSpace #1059 A204 → IfcFlowSegment #518846 Pipe Types:Cold Water:642822 — distance 0.0003 — expliqué : écart vertical 0.0003 au bord de [0, tolérance]
- IfcSpace #1928 B104 → IfcFlowSegment #93651 Pipe Types:Cold Water:583055 — distance 0.0015 — expliqué : écart vertical 0.0015 au bord de [0, tolérance]
- IfcSpace #1928 B104 → IfcFlowSegment #98788 Pipe Types:Cold Water:583067 — distance 0.4606 — expliqué : faux négatif de l'original : sa grille de rayons (pas 9.0 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #169681 Pipe Types:Waste:594985 — distance 0.5828 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.9 cm) passe à côté d'un objet de 4.8 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #198931 Pipe Types:PVC:605401 — distance 0.7161 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2108 B101 → IfcFlowSegment #98788 Pipe Types:Cold Water:583067 — distance 0.4666 — expliqué : faux négatif de l'original : sa grille de rayons (pas 9.0 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSpace #2108 B101 → IfcFlowSegment #107188 Pipe Types:Cold Water:583140 — distance 0.4666 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.4 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSpace #2108 B101 → IfcFlowSegment #169681 Pipe Types:Waste:594985 — distance 0.6007 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.9 cm) passe à côté d'un objet de 4.8 cm en plan
- IfcSpace #2412 B201 → IfcFlowSegment #199183 Pipe Types:PVC:605583 — distance 0.4439 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2412 B201 → IfcFlowSegment #199596 Pipe Types:PVC:605615 — distance 0.5174 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2637 B204 → IfcFlowSegment #198681 Pipe Types:PVC:605397 — distance 0.5114 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2637 B204 → IfcFlowSegment #517268 Pipe Types:Cold Water:642079 — distance 0.0003 — expliqué : écart vertical 0.0003 au bord de [0, tolérance]
- IfcSpace #3197 A205 → IfcFlowSegment #169004 Pipe Types:Cold Water:593588 — distance 0.0003 — expliqué : écart vertical 0.0003 au bord de [0, tolérance]
- IfcSpace #3325 B205 → IfcFlowSegment #199183 Pipe Types:PVC:605583 — distance 0.4379 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #3586 B105 → IfcFlowSegment #98788 Pipe Types:Cold Water:583067 — distance 0.4666 — expliqué : faux négatif de l'original : sa grille de rayons (pas 9.0 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSpace #3586 B105 → IfcFlowSegment #107188 Pipe Types:Cold Water:583140 — distance 0.4666 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.4 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSpace #3586 B105 → IfcFlowSegment #169681 Pipe Types:Waste:594985 — distance 0.6014 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.9 cm) passe à côté d'un objet de 4.8 cm en plan
- IfcSpace #3707 R301 → IfcFlowSegment #130839 Pipe Types:Waste:583332 — distance 0.005 — expliqué : écart vertical 0.0050 au bord de [0, tolérance]
- IfcWallStandardCase #4087 Basic Wall:Exterior - Brick on Block:138310 → IfcFlowSegment #86043 Pipe Types:Waste:582999 — distance 0.5837 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.1 cm) passe à côté d'un objet de 4.8 cm en plan
- IfcWallStandardCase #4087 Basic Wall:Exterior - Brick on Block:138310 → IfcFlowSegment #98788 Pipe Types:Cold Water:583067 — distance 0.4476 — expliqué : faux négatif de l'original : sa grille de rayons (pas 9.0 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcWallStandardCase #4087 Basic Wall:Exterior - Brick on Block:138310 → IfcFlowSegment #107188 Pipe Types:Cold Water:583140 — distance 0.4476 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.4 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcWallStandardCase #4087 Basic Wall:Exterior - Brick on Block:138310 → IfcFlowSegment #169681 Pipe Types:Waste:594985 — distance 0.5872 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.9 cm) passe à côté d'un objet de 4.8 cm en plan
- IfcWallStandardCase #4087 Basic Wall:Exterior - Brick on Block:138310 → IfcFlowSegment #192187 Pipe Types:PVC:604739 — distance 0.7032 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4219 Basic Wall:Interior - Partition (92mm Stud):139143 → IfcFlowSegment #98788 Pipe Types:Cold Water:583067 — distance 0.4476 — expliqué : faux négatif de l'original : sa grille de rayons (pas 9.0 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcWallStandardCase #4219 Basic Wall:Interior - Partition (92mm Stud):139143 → IfcFlowSegment #169681 Pipe Types:Waste:594985 — distance 0.577 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.9 cm) passe à côté d'un objet de 4.8 cm en plan
- IfcWallStandardCase #4399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139347 → IfcFlowSegment #192187 Pipe Types:PVC:604739 — distance 0.7031 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139347 → IfcFlowSegment #198931 Pipe Types:PVC:605401 — distance 0.7031 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #76025 Pipe Types:Waste:582975 — distance 0.0008 — expliqué : écart vertical 0.0008 au bord de [0, tolérance]
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #93651 Pipe Types:Cold Water:583055 — distance 0.0011 — expliqué : écart vertical 0.0011 au bord de [0, tolérance]
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #98788 Pipe Types:Cold Water:583067 — distance 0.3206 — expliqué : faux négatif de l'original : sa grille de rayons (pas 9.0 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #98869 Pipe Types:Cold Water:583068 — distance 0.0706 — expliqué : faux négatif de l'original : sa grille de rayons (pas 3.1 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #107188 Pipe Types:Cold Water:583140 — distance 0.3206 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.4 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #169681 Pipe Types:Waste:594985 — distance 0.4587 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.9 cm) passe à côté d'un objet de 4.8 cm en plan
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #198931 Pipe Types:PVC:605401 — distance 0.5761 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSlab #5267 Floor:127mm Slab on Grade:143106 → IfcFlowSegment #86043 Pipe Types:Waste:582999 — distance 0.4404 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.1 cm) passe à côté d'un objet de 4.8 cm en plan
- IfcSlab #5267 Floor:127mm Slab on Grade:143106 → IfcFlowSegment #192022 Pipe Types:Cold Water:604667 — distance 0.3206 — expliqué : faux négatif de l'original : sa grille de rayons (pas 3.1 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowSegment #191477 Pipe Types:PVC:604577 — distance 0.425 — expliqué : faux négatif de l'original : sa grille de rayons (pas 3.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowSegment #199183 Pipe Types:PVC:605583 — distance 0.425 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #5687 Basic Wall:Interior - Partition (92mm Stud):143921 → IfcFlowSegment #199183 Pipe Types:PVC:605583 — distance 0.4249 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- ... 63 de plus

## OBB_Above_triang

Paramètres : `{'tolerance': 1.0}`.

- Phases _triang : `OBB_Above_triang   convert: 785 → 735   broad: 117764 → 1712   mid: 1712 → 1712   convert_narrow: 618 → 618   narrow: 1712 → 1701   (0.505 s)`
- Phases origine : `OBB_Above   convert: 785 → 785   broad: 142714 → 1735   mid: 1735 → 1735   narrow: 1735 → 1717   (22.899 s)`
- Écarts par cause : 25 absent du .ifcview, 9 seuils à ± marge
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (25) :

- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #8206 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150378:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #8372 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:150478:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 → IfcFlowSegment #199183 Pipe Types:PVC:605583 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 → IfcFlowSegment #191477 Pipe Types:PVC:604577 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 → IfcFlowSegment #186843 Pipe Types:PVC:604332 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 → IfcFlowSegment #192269 Pipe Types:PVC:605354 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #14758 M_Tall Cabinet-Single Door(2):800 mm:800 mm:158080:1 → IfcFlowFitting #198294 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605365 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #15885 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159734:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #15999 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:159834:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16050 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160065:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16101 M_Single-Flush:0864 x 2032mm:0864 x 2032mm:160208:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22382 M_Fixed:750mm x 2200mm:750mm x 2200mm:181930:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22434 M_Fixed:750mm x 2200mm:750mm x 2200mm:182101:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #35241 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:203720:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #35399 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:204034:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview

En plus (9) :

- IfcWallStandardCase #4465 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139374 → IfcFlowFitting #104712 M_Transition - Generic:Transition - Generic:Transition - Generic:583094 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4465 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139374 → IfcFlowFitting #107729 M_Transition - Generic:Transition - Generic:Transition - Generic:583148 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #976791 Pipe Types:Hot Water:666333 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21147 Floor:Finish Floor - Wood:169701 → IfcFlowTerminal #42582 M_Bath Tub:1525 mmx760 mm - Private:1525 mmx760 mm - Private:582924 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21195 Floor:Finish Floor - Ceramic Tile:169772 → IfcFlowSegment #131223 Pipe Types:Hot Water:583557 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21336 Floor:Finish Floor - Ceramic Tile:169866 → IfcFlowSegment #109112 Pipe Types:Hot Water:583171 — distance 0.0 — expliqué : seuils à ± marge
- IfcCovering #23884 Compound Ceiling:Gypsum Board:187483 → IfcFlowFitting #106864 M_Tee - Generic:Tee - Generic:Tee - Generic:583135 — distance 0.0 — expliqué : seuils à ± marge
- IfcCovering #23884 Compound Ceiling:Gypsum Board:187483 → IfcFlowFitting #108713 M_Tee - Generic:Tee - Generic:Tee - Generic:583166 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #24813 Basic Wall:Interior - Furring (152 mm Stud):190933 → IfcFlowSegment #131072 Pipe Types:Hot Water:583550 — distance 0.0 — expliqué : seuils à ± marge

## OBB_Below_triang

Paramètres : `{'tolerance': 1.0}`.

- Phases _triang : `OBB_Below_triang   convert: 785 → 735   broad: 117764 → 1192   mid: 1192 → 1174   convert_narrow: 412 → 412   narrow: 1174 → 1167   (0.400 s)`
- Phases origine : `OBB_Below   convert: 785 → 785   broad: 142714 → 1202   mid: 1202 → 1202   narrow: 1202 → 1165   (14.452 s)`
- Écarts par cause : 13 seuils à ± marge, 11 absent du .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (11) :

- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowSegment #176366 Pipe Types:Hot Water:599791 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowSegment #176448 Pipe Types:Hot Water:599795 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowSegment #191705 Pipe Types:Cold Water:604652 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowSegment #208013 Pipe Types:Waste:612522 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowFitting #855036 M_Transition - Generic:Transition - Generic:Transition - Generic:645830 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowFitting #856851 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:645876 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowFitting #857192 M_Transition - Generic:Transition - Generic:Transition - Generic:645881 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22533 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:2 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22546 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:3 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview

En plus (13) :

- IfcWallStandardCase #4287 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139234 → IfcFlowTerminal #28561 M_Shower Stall - Rectangular:865 mmx815 mm - Private:865 mmx815 mm - Private:582914 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139347 → IfcFlowTerminal #31535 M_Shower Stall - Rectangular:865 mmx815 mm - Private:865 mmx815 mm - Private:582917 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4465 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139374 → IfcFlowFitting #96240 M_Transition - Generic:Transition - Generic:Transition - Generic:583060 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4465 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139374 → IfcFlowSegment #98788 Pipe Types:Cold Water:583067 — distance 0.0 — expliqué : seuils à ± marge
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowFitting #104712 M_Transition - Generic:Transition - Generic:Transition - Generic:583094 — distance 0.0 — expliqué : seuils à ± marge
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowFitting #107729 M_Transition - Generic:Transition - Generic:Transition - Generic:583148 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #5948 Basic Wall:Interior - Partition (92mm Stud):144586 → IfcFlowTerminal #42582 M_Bath Tub:1525 mmx760 mm - Private:1525 mmx760 mm - Private:582924 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21147 Floor:Finish Floor - Wood:169701 → IfcFlowTerminal #42582 M_Bath Tub:1525 mmx760 mm - Private:1525 mmx760 mm - Private:582924 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #22492 Basic Roof:Live Roof over Wood Joist Flat Roof:184483 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #22663 Basic Wall:Exterior - Brick on Block:184944 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #22708 Basic Wall:Exterior - Brick on Block:185014 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #22753 Basic Wall:Exterior - Brick on Block:185064 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #22798 Basic Wall:Exterior - Brick on Block:185101 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge

## OBB_Front_And_Back_triang

Paramètres : `{'tolerance': 0.5, 'direction_method': 'Wide'}`.

- Phases _triang : `OBB_Front_And_Back_triang   convert: 785 → 735   broad: 117764 → 1979   mid: 1979 → 1979   convert_narrow: 591 → 591   narrow: 1979 → 1313   (0.501 s)`
- Phases origine : `OBB_Front_And_Back   convert: 785 → 785   broad: 142714 → 1995   mid: 1995 → 1995   narrow: 1995 → 1296   (28.599 s)`
- Écarts par cause : 28 seuils à ± marge, 10 absent du .ifcview
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (10) :

- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 → IfcFlowSegment #117695 Pipe Types:Hot Water:583299 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 → IfcFlowTerminal #40786 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582922 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22506 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22520 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22533 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:2 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22546 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:3 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #35241 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:203720:1 → IfcFlowController #27611 M_Ball Valve - 50-150 mm:50 mm:50 mm:579237 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #35241 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:203720:1 → IfcFlowController #150079 M_Backflow Preventer_ DCW to Hydronic Supply_15-50 mm_:25 mm:25 mm:591225 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #35399 M_Single-Flush:0762 x 2032mm:0762 x 2032mm:204034:1 → IfcFlowController #169477 M_Backflow Preventer_ DCW to Hydronic Supply_15-50 mm_:25 mm:25 mm:593973 — distance 0.0 — expliqué : absent du .ifcview

En plus (28) :

- IfcSpace #1059 A204 → IfcFlowTerminal #45502 M_Lavatory - Oval:650 mmx485 mm - Private:650 mmx485 mm - Private:582926 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1059 A204 → IfcFlowTerminal #45641 M_Lavatory - Oval:650 mmx485 mm - Private:650 mmx485 mm - Private:582927 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1059 A204 → IfcFlowSegment #109656 Pipe Types:Hot Water:583180 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1059 A204 → IfcFlowSegment #109894 Pipe Types:Hot Water:583184 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1059 A204 → IfcFlowSegment #110045 Pipe Types:Hot Water:583187 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1059 A204 → IfcFlowSegment #110206 Pipe Types:Hot Water:583189 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1059 A204 → IfcFlowSegment #110284 Pipe Types:Hot Water:583190 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1059 A204 → IfcFlowSegment #114112 Pipe Types:Hot Water:583235 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2637 B204 → IfcFlowSegment #108021 Pipe Types:Hot Water:583154 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2637 B204 → IfcFlowSegment #108406 Pipe Types:Hot Water:583160 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2637 B204 → IfcFlowSegment #108557 Pipe Types:Hot Water:583163 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2637 B204 → IfcFlowSegment #112957 Pipe Types:Hot Water:583214 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2637 B204 → IfcFlowSegment #113035 Pipe Types:Hot Water:583215 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #2637 B204 → IfcFlowSegment #113186 Pipe Types:Hot Water:583217 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4465 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139374 → IfcFlowFitting #115383 M_Tee - Generic:Tee - Generic:Tee - Generic:583259 — distance 0.0 — expliqué : seuils à ± marge
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowSegment #976791 Pipe Types:Hot Water:666333 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #5775 Basic Wall:Interior - Plumbing (152mm Stud):144138 → IfcFlowSegment #976791 Pipe Types:Hot Water:666333 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowFitting #104712 M_Transition - Generic:Transition - Generic:Transition - Generic:583094 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowFitting #107729 M_Transition - Generic:Transition - Generic:Transition - Generic:583148 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21545 Floor:Finish Floor - Ceramic Tile:171261 → IfcFlowTerminal #31535 M_Shower Stall - Rectangular:865 mmx815 mm - Private:865 mmx815 mm - Private:582917 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #35783 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:204934 → IfcFlowSegment #108406 Pipe Types:Hot Water:583160 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #35783 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:204934 → IfcFlowSegment #108557 Pipe Types:Hot Water:583163 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #35854 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205239 → IfcFlowSegment #108406 Pipe Types:Hot Water:583160 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #35854 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205239 → IfcFlowSegment #112957 Pipe Types:Hot Water:583214 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #36125 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205264 → IfcFlowSegment #110045 Pipe Types:Hot Water:583187 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #36125 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205264 → IfcFlowSegment #114112 Pipe Types:Hot Water:583235 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #36151 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205265 → IfcFlowSegment #109656 Pipe Types:Hot Water:583180 — distance 0.0 — expliqué : seuils à ± marge
- IfcFurnishingElement #36151 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205265 → IfcFlowSegment #110045 Pipe Types:Hot Water:583187 — distance 0.0 — expliqué : seuils à ± marge

## OBB_Custom_triang

Paramètres : `{'list_of_modifications': ['detach_top_by_extrude:0.5', 'NEW_OBB', 'extend_down:50%']}`.

- Phases _triang : `OBB_Custom_triang   convert: 785 → 735   broad: 117764 → 2186   mid: 2186 → 2186   convert_narrow: 628 → 628   narrow: 2186 → 2408   (0.500 s)`
- Phases origine : `OBB_Custom   convert: 785 → 785   broad: 142714 → 2191   mid: 2191 → 2191   narrow: 2191 → 2408   (25.707 s)`
- Écarts par cause : 14 absent du .ifcview, 13 seuils à ± marge
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (14) :

- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22174 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:181096:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22226 M_Fixed:819mm x 759mm:819mm x 759mm:181285:1 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22506 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22520 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22533 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:2 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22546 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:3 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview

En plus (13) :

- IfcWallStandardCase #4465 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139374 → IfcFlowFitting #96240 M_Transition - Generic:Transition - Generic:Transition - Generic:583060 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4465 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139374 → IfcFlowSegment #98788 Pipe Types:Cold Water:583067 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4465 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139374 → IfcFlowFitting #104712 M_Transition - Generic:Transition - Generic:Transition - Generic:583094 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #4465 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139374 → IfcFlowFitting #107729 M_Transition - Generic:Transition - Generic:Transition - Generic:583148 — distance 0.0 — expliqué : seuils à ± marge
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowFitting #104712 M_Transition - Generic:Transition - Generic:Transition - Generic:583094 — distance 0.0 — expliqué : seuils à ± marge
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowFitting #107729 M_Transition - Generic:Transition - Generic:Transition - Generic:583148 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #5948 Basic Wall:Interior - Partition (92mm Stud):144586 → IfcFlowTerminal #42582 M_Bath Tub:1525 mmx760 mm - Private:1525 mmx760 mm - Private:582924 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowFitting #106864 M_Tee - Generic:Tee - Generic:Tee - Generic:583135 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowFitting #108713 M_Tee - Generic:Tee - Generic:Tee - Generic:583166 — distance 0.0 — expliqué : seuils à ± marge
- IfcSlab #21147 Floor:Finish Floor - Wood:169701 → IfcFlowTerminal #42582 M_Bath Tub:1525 mmx760 mm - Private:1525 mmx760 mm - Private:582924 — distance 0.0 — expliqué : seuils à ± marge
- IfcCovering #23884 Compound Ceiling:Gypsum Board:187483 → IfcFlowFitting #106864 M_Tee - Generic:Tee - Generic:Tee - Generic:583135 — distance 0.0 — expliqué : seuils à ± marge
- IfcCovering #23884 Compound Ceiling:Gypsum Board:187483 → IfcFlowFitting #108713 M_Tee - Generic:Tee - Generic:Tee - Generic:583166 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #24813 Basic Wall:Interior - Furring (152 mm Stud):190933 → IfcFlowSegment #131072 Pipe Types:Hot Water:583550 — distance 0.0 — expliqué : seuils à ± marge

## AngleBetween_triang

Paramètres : `{'direction_method_for_source': 'Wide', 'direction_method_for_target': 'Wide', 'angle_difference': 90.0, 'angle_tolerance': 5.0}`.

- Phases _triang : `AngleBetween_triang   convert: 785 → 735   mid: 117764 → 117764   convert_narrow: 735 → 735   narrow: 117764 → 43411   (0.497 s)`
- Phases origine : `AngleBetween   convert: 785 → 785   mid: 142714 → 142714   narrow: 142714 → 53933   (17.194 s)`
- Écarts par cause : 9510 absent du .ifcview, 5543 axe principal ambigu, 2463 OBB optimale non unique, 14 seuils à ± marge
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (14026) :

- IfcSpace #67 A102 → IfcFlowFitting #75616 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:582961 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowFitting #85962 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:582994 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowFitting #123263 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583321 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowFitting #198511 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605374 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowFitting #199006 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605540 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowFitting #75616 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:582961 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowFitting #85962 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:582994 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowFitting #123263 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583321 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowFitting #198511 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605374 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowFitting #199006 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605540 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowSegment #76025 Pipe Types:Waste:582975 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowSegment #81319 Pipe Types:Waste:582988 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowSegment #92069 Pipe Types:Waste:583035 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowSegment #107820 Pipe Types:Hot Water:583151 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowSegment #109344 Pipe Types:Hot Water:583174 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowFitting #110357 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583191 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowFitting #110511 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583193 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowFitting #113108 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583216 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowSegment #114351 Pipe Types:Hot Water:583239 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowFitting #116705 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583281 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowSegment #117462 Pipe Types:Hot Water:583296 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowFitting #118224 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583311 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowFitting #130916 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583536 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowSegment #131374 Pipe Types:Hot Water:583768 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowFitting #131530 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:584031 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowFitting #180790 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:599803 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowFitting #191626 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:604624 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowFitting #199259 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605591 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowSegment #518675 Pipe Types:Hot Water:642757 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowSegment #518846 Pipe Types:Cold Water:642822 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowSegment #853012 Pipe Types:Cold Water:644980 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowSegment #977776 Pipe Types:Cold Water:672892 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowSegment #981332 Pipe Types:Hot Water:673611 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #355 A104 → IfcFlowFitting #984096 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:674868 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #514 A101 → IfcFlowSegment #76025 Pipe Types:Waste:582975 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #514 A101 → IfcFlowSegment #81319 Pipe Types:Waste:582988 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #514 A101 → IfcFlowSegment #92069 Pipe Types:Waste:583035 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #514 A101 → IfcFlowSegment #107820 Pipe Types:Hot Water:583151 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #514 A101 → IfcFlowSegment #109344 Pipe Types:Hot Water:583174 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #514 A101 → IfcFlowFitting #110357 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583191 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- ... 13986 de plus

En plus (3504) :

- IfcSpace #67 A102 → IfcFlowFitting #110357 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583191 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowFitting #110511 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583193 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowSegment #112086 Pipe Types:Hot Water:583202 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #67 A102 → IfcFlowFitting #113108 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583216 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowFitting #116705 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583281 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowFitting #118224 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583311 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowFitting #130916 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583536 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowFitting #131530 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:584031 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowSegment #131609 Pipe Types:Cold Water:584048 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #67 A102 → IfcFlowFitting #180790 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:599803 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowSegment #186965 Pipe Types:PVC:604361 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #67 A102 → IfcFlowSegment #191396 Pipe Types:PVC:604556 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #67 A102 → IfcFlowFitting #191626 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:604624 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowSegment #198681 Pipe Types:PVC:605397 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #67 A102 → IfcFlowFitting #199259 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605591 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #67 A102 → IfcFlowSegment #199596 Pipe Types:PVC:605615 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #67 A102 → IfcFlowFitting #984096 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:674868 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowFitting #110357 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583191 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowFitting #110511 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583193 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowSegment #112086 Pipe Types:Hot Water:583202 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #212 A103 → IfcFlowFitting #113108 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583216 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowFitting #116705 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583281 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowFitting #118224 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583311 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowFitting #130916 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583536 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowFitting #131530 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:584031 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowSegment #131609 Pipe Types:Cold Water:584048 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #212 A103 → IfcFlowFitting #180790 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:599803 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowSegment #186965 Pipe Types:PVC:604361 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #212 A103 → IfcFlowSegment #191396 Pipe Types:PVC:604556 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #212 A103 → IfcFlowFitting #191626 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:604624 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowSegment #198681 Pipe Types:PVC:605397 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #212 A103 → IfcFlowFitting #199259 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605591 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #212 A103 → IfcFlowSegment #199596 Pipe Types:PVC:605615 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcSpace #212 A103 → IfcFlowFitting #984096 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:674868 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowFitting #75616 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:582961 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowFitting #85962 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:582994 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowFitting #123263 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583321 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowFitting #198511 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605374 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #355 A104 → IfcFlowFitting #199006 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605540 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSpace #514 A101 → IfcFlowFitting #75616 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:582961 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- ... 3464 de plus

## ObbHigh_triang

Paramètres : `{'length_min': 0.0, 'length_max': 1000000000.0}`.

- Phases _triang : `ObbHigh_triang   convert: 785 → 735   narrow: 735 → 735   (0.082 s)`
- Phases origine : `ObbHigh   convert: 785 → 785   narrow: 785 → 785   (17.070 s)`
- Mesures comparées sur 735 éléments communs : 12 écart(s) au-delà de 0.011 m
- Écarts par cause : 50 absent du .ifcview, 12 OBB optimale non unique
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

Mesures (12) :

- IfcFlowSegment #115935 Pipe Types:Hot Water:583271 — écart -0.0112 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #117381 Pipe Types:Hot Water:583295 — écart -0.0112 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #169159 Pipe Types:Hot Water:593619 — écart -0.0112 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowFitting #181869 M_Transition - Generic:Transition - Generic:Transition - Generic:599804 — écart -0.0219 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowFitting #186519 M_Transition - Generic:Transition - Generic:Transition - Generic:600115 — écart -0.0219 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowFitting #186753 M_Transition - Generic:Transition - Generic:Transition - Generic:600138 — écart -0.0219 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowFitting #192098 M_Transition - Generic:Transition - Generic:Transition - Generic:604670 — écart -0.0219 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #199183 Pipe Types:PVC:605583 — écart -0.0126 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowController #515092 Lavatory Faucet:Lavatory Faucet:Lavatory Faucet:637570 — écart 0.0153 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowController #515298 Lavatory Faucet:Lavatory Faucet:Lavatory Faucet:640173 — écart 0.0153 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowController #521432 Lavatory Faucet:Lavatory Faucet:Lavatory Faucet:643784 — écart 0.0153 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowController #976738 Bath Tub Faucet:PT:PT:665921 — écart 0.033 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)

## ObbLength_triang

Paramètres : `{'length_min': 0.0, 'length_max': 1000000000.0, 'direction_method': 'Narrow'}`.

- Phases _triang : `ObbLength_triang   convert: 785 → 735   narrow: 735 → 735   (0.084 s)`
- Phases origine : `ObbLength   convert: 785 → 785   narrow: 785 → 785   (16.755 s)`
- Mesures comparées sur 735 éléments communs : 1 écart(s) au-delà de 0.011 m
- Écarts par cause : 50 absent du .ifcview, 1 OBB optimale non unique
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

- IfcEnergyConversionDevice #3691 M_Hot Water Boiler - 59-440 kW:147 kW:147 kW:530072 — écart -0.0123 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)

## Orientation_triang

Paramètres : `{'orientation': [0.0, 0.0, 1.0], 'orientation_type': 'Perpendicular', 'direction_method': 'Wide', 'angular_tolerance': 0.1}`.

- Phases _triang : `Orientation_triang   convert: 785 → 735   narrow: 735 → 735   (0.418 s)`
- Phases origine : `Orientation   convert: 785 → 785   narrow: 785 → 785   (17.232 s)`
- Mesures comparées sur 735 éléments communs : 141 écart(s) au-delà de 1.0°
- Écarts par cause : 141 OBB optimale non unique, 50 absent du .ifcview
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

Mesures (141) :

- IfcRailing #9326 Railing:900mm Handrail Only:151162 — écart -23.5067 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcRailing #32346 Railing:900mm Handrail Only:198880 — écart 23.5066 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #55105 Pipe Types:Waste:582941 — écart 50.1927 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #59844 Pipe Types:Waste:582946 — écart 22.5004 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #59927 Pipe Types:Waste:582947 — écart -1.7326 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #67580 Pipe Types:Waste:582952 — écart -50.1908 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #67663 Pipe Types:Waste:582953 — écart -43.2706 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #72337 Pipe Types:Waste:582956 — écart -22.5012 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #72421 Pipe Types:Waste:582958 — écart -1.7327 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #75781 Pipe Types:Waste:582963 — écart -43.2679 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #75865 Pipe Types:Waste:582967 — écart 1.7316 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #76189 Pipe Types:Waste:582977 — écart 22.5004 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #80753 Pipe Types:Waste:582980 — écart -50.1937 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #80915 Pipe Types:Waste:582983 — écart -22.4985 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #81150 Pipe Types:Waste:582986 — écart -43.2699 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #81234 Pipe Types:Waste:582987 — écart -1.7329 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #81484 Pipe Types:Waste:582990 — écart 64.0389 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #81648 Pipe Types:Waste:582992 — écart -22.5004 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #86043 Pipe Types:Waste:582999 — écart 22.5009 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #86127 Pipe Types:Waste:583001 — écart -1.7321 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #86288 Pipe Types:Waste:583004 — écart 22.5004 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #91035 Pipe Types:Waste:583009 — écart 5.1938 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #91269 Pipe Types:Waste:583012 — écart -50.1935 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #91429 Pipe Types:Waste:583015 — écart -5.1919 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #91664 Pipe Types:Waste:583018 — écart -43.2706 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #91909 Pipe Types:Waste:583033 — écart -50.1932 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #92152 Pipe Types:Waste:583036 — écart -50.1932 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #92396 Pipe Types:Waste:583039 — écart -5.1936 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #92630 Pipe Types:Waste:583042 — écart 43.268 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #92865 Pipe Types:Waste:583045 — écart -1.733 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #93028 Pipe Types:Waste:583047 — écart -50.1908 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #93263 Pipe Types:Waste:583050 — écart -1.7325 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #93430 Pipe Types:Waste:583053 — écart 43.2677 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #93514 Pipe Types:Cold Water:583054 — écart 10.8799 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #93734 Pipe Types:Cold Water:583056 — écart 38.5731 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #95881 Pipe Types:Cold Water:583059 — écart 19.7797 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #96379 Pipe Types:Cold Water:583061 — écart 80.1096 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #98340 Pipe Types:Cold Water:583065 — écart 54.3951 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #98788 Pipe Types:Cold Water:583067 — écart 59.3403 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- IfcFlowSegment #98869 Pipe Types:Cold Water:583068 — écart 38.5711 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés)
- ... 101 de plus

## Alignement_triang

Paramètres : `{'axis': None, 'alignment_type': 'Plane', 'tolerance': 0.05, 'min_group': 3}`.

- Phases _triang : `Alignement_triang   convert: 785 → 735   narrow: 735 → 188   (0.380 s)`
- Phases origine : `Alignement   convert: 785 → 785   narrow: 785 → 185   (38.615 s)`
- Écarts par cause : 33 axe principal ambigu, 26 OBB optimale non unique, 16 absent du .ifcview, 3 groupe recomposé, 1 ensemble d'entrée différent
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (38) :

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
- IfcFlowTerminal #28561 M_Shower Stall - Rectangular:865 mmx815 mm - Private:865 mmx815 mm - Private:582914 — distance None — expliqué : groupe recomposé : sans les éléments aux axes ambigus ou tournés, les deux règles donnent le même verdict
- IfcFlowTerminal #31408 M_Water Closet - Flush Tank:Private - 6.1 Lpf:Private - 6.1 Lpf:582915 — distance None — expliqué : groupe recomposé : sans les éléments aux axes ambigus ou tournés, les deux règles donnent le même verdict
- IfcFlowTerminal #42713 M_Water Closet - Flush Tank:Private - 6.1 Lpf:Private - 6.1 Lpf:582925 — distance None — expliqué : groupe recomposé : sans les éléments aux axes ambigus ou tournés, les deux règles donnent le même verdict
- IfcFlowFitting #64333 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:582948 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowSegment #86209 Pipe Types:Waste:583003 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowSegment #91350 Pipe Types:Waste:583014 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowSegment #92551 Pipe Types:Waste:583041 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowSegment #105368 Pipe Types:Cold Water:583112 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowSegment #113574 Pipe Types:Cold Water:583224 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowSegment #115225 Pipe Types:Hot Water:583256 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowSegment #169004 Pipe Types:Cold Water:593588 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #181869 M_Transition - Generic:Transition - Generic:Transition - Generic:599804 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #186519 M_Transition - Generic:Transition - Generic:Transition - Generic:600115 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #186753 M_Transition - Generic:Transition - Generic:Transition - Generic:600138 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #192098 M_Transition - Generic:Transition - Generic:Transition - Generic:604670 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #199671 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605616 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #203575 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:610191 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #207933 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:612458 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowSegment #517708 Pipe Types:Hot Water:642220 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowSegment #519229 Pipe Types:Cold Water:643328 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowSegment #981332 Pipe Types:Hot Water:673611 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowSegment #985555 Pipe Types:Hot Water:675497 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change

En plus (41) :

- IfcFurnishingElement #17532 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:167584 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFurnishingElement #17602 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:167655 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFurnishingElement #17844 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:168379 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFurnishingElement #17873 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:168380 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcSlab #22492 Basic Roof:Live Roof over Wood Joist Flat Roof:184483 — distance None — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #36497 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206283 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFurnishingElement #36526 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206502 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFurnishingElement #36555 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206675 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFurnishingElement #36584 M_Table-Coffee:0610 x 0610 x 0610mm:0610 x 0610 x 0610mm:206876 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #91110 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583010 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #92472 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583040 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #93104 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583048 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #98187 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583063 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #104089 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583085 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowSegment #105923 Pipe Types:Cold Water:583120 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #105999 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583121 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #106790 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583134 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #113960 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583233 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowSegment #114909 Pipe Types:Hot Water:583251 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #114984 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583252 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowSegment #115307 Pipe Types:Hot Water:583257 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #115782 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583269 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #127559 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583324 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowSegment #131609 Pipe Types:Cold Water:584048 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #131685 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:584049 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #186371 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:600112 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #198841 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605399 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #199756 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:605617 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #203490 M_Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:Bend - PVC - Sch 40 - DWV:610174 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #212365 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:612528 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #517187 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:641460 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #518155 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:642465 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #856851 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:645876 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #922797 M_Transition - Generic:Transition - Generic:Transition - Generic:652957 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #976567 M_Transition - Generic:Transition - Generic:Transition - Generic:665879 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #976651 M_Transition - Generic:Transition - Generic:Transition - Generic:665882 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #977613 M_Transition - Generic:Transition - Generic:Transition - Generic:666643 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #983938 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:674797 — distance None — expliqué : axe principal ambigu : deux dimensions de l'OBB égales à la marge près
- IfcFlowFitting #984012 M_Transition - Generic:Transition - Generic:Transition - Generic:674801 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- IfcFlowFitting #984170 M_Transition - Generic:Transition - Generic:Transition - Generic:674870 — distance None — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe principal change
- ... 1 de plus

## Clearance_triang

Paramètres : `{'clearance': 0.5, 'check_all': True}`.

- Phases _triang : `Clearance_triang   convert: 785 → 735   broad: 117764 → 5711   mid: 5711 → 5711   convert_narrow: 653 → 653   narrow: 5711 → 4839   (1.221 s)`
- Phases origine : `Clearance   convert: 785 → 785   broad: 142714 → 5788   mid: 5788 → 5778   narrow: 5778 → 4904   (5.288 s)`
- Écarts par cause : 59 absent du .ifcview, 6 distance au bord du seuil
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (65) :

- IfcSpace #212 A103 → IfcFlowTerminal #42582 M_Bath Tub:1525 mmx760 mm - Private:1525 mmx760 mm - Private:582924 — distance 0.5 — expliqué : distance 0.5000 au bord du seuil (± marge)
- IfcSpace #355 A104 → IfcFlowTerminal #42582 M_Bath Tub:1525 mmx760 mm - Private:1525 mmx760 mm - Private:582924 — distance 0.5 — expliqué : distance 0.5000 au bord du seuil (± marge)
- IfcSpace #355 A104 → IfcFlowTerminal #42713 M_Water Closet - Flush Tank:Private - 6.1 Lpf:Private - 6.1 Lpf:582925 — distance 0.5 — expliqué : distance 0.5000 au bord du seuil (± marge)
- IfcSpace #1782 B103 → IfcFlowTerminal #45821 M_Bath Tub:1525 mmx760 mm - Private:1525 mmx760 mm - Private:582931 — distance 0.5 — expliqué : distance 0.5000 au bord du seuil (± marge)
- IfcSpace #1928 B104 → IfcFlowTerminal #45776 M_Water Closet - Flush Tank:Private - 6.1 Lpf:Private - 6.1 Lpf:582930 — distance 0.5 — expliqué : distance 0.5000 au bord du seuil (± marge)
- IfcSpace #1928 B104 → IfcFlowTerminal #45821 M_Bath Tub:1525 mmx760 mm - Private:1525 mmx760 mm - Private:582931 — distance 0.5 — expliqué : distance 0.5000 au bord du seuil (± marge)
- IfcOpeningElement #7063 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:147686:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #7729 M_Fixed:819mm x 759mm:819mm x 759mm:148722:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #7781 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:149278:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #7937 M_Fixed:819mm x 759mm:819mm x 759mm:149924:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 → IfcFlowSegment #92069 Pipe Types:Waste:583035 — distance 0.4862 — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 → IfcFlowSegment #117695 Pipe Types:Hot Water:583299 — distance 0.3501 — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 → IfcFlowFitting #117992 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583308 — distance 0.3659 — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 → IfcFlowSegment #118070 Pipe Types:Hot Water:583309 — distance 0.4016 — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 → IfcFlowTerminal #40786 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582922 — distance 0.2924 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowTerminal #40786 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582922 — distance 0.2447 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowSegment #117083 Pipe Types:Hot Water:583286 — distance 0.4151 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowSegment #186608 Pipe Types:Hot Water:600130 — distance 0.3938 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowFitting #186680 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:600137 — distance 0.3854 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowFitting #186753 M_Transition - Generic:Transition - Generic:Transition - Generic:600138 — distance 0.4036 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowController #852873 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:644888 — distance 0.3164 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowSegment #977776 Pipe Types:Cold Water:672892 — distance 0.3744 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowSegment #977856 Pipe Types:Cold Water:672960 — distance 0.3689 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowFitting #978841 M_Transition - Generic:Transition - Generic:Transition - Generic:672962 — distance 0.3729 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowFitting #980654 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:672968 — distance 0.4433 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowFitting #981005 M_Transition - Generic:Transition - Generic:Transition - Generic:672971 — distance 0.4342 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowSegment #117695 Pipe Types:Hot Water:583299 — distance 0.3076 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowSegment #176366 Pipe Types:Hot Water:599791 — distance 0.0542 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowSegment #176448 Pipe Types:Hot Water:599795 — distance 0.2537 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowFitting #180790 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:599803 — distance 0.2967 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowFitting #181869 M_Transition - Generic:Transition - Generic:Transition - Generic:599804 — distance 0.2946 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowSegment #191705 Pipe Types:Cold Water:604652 — distance 0.0542 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowSegment #208013 Pipe Types:Waste:612522 — distance 0.1725 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 0.0001 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowFitting #855036 M_Transition - Generic:Transition - Generic:Transition - Generic:645830 — distance 0.0478 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowFitting #856851 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:645876 — distance 0.2457 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowFitting #857192 M_Transition - Generic:Transition - Generic:Transition - Generic:645881 — distance 0.0478 — expliqué : absent du .ifcview
- IfcOpeningElement #21966 M_Fixed:2800mm x 2410mm:2800mm x 2410mm:180318:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- IfcOpeningElement #22018 M_Fixed:819mm x 759mm:819mm x 759mm:180663:1 → IfcSpace #125 R301 — distance 0.39 — expliqué : absent du .ifcview
- ... 25 de plus

## Collision_triang

Paramètres : `{'allow_touching': False}`.

- Phases _triang : `Collision_triang   convert: 785 → 735   broad: 117764 → 902   mid: 902 → 902   convert_narrow: 481 → 481   narrow: 902 → 380   (0.176 s)`
- Phases origine : `Collision   convert: 785 → 785   broad: 142714 → 909   mid: 909 → 908   narrow: 908 → 382   (3.769 s)`
- Écarts par cause : 4 absent du .ifcview, 1 géométries IFC au contact, 1 maillage IFC ouvert
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (4) :

- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22506 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview
- IfcOpeningElement #22520 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview

En plus (2) :

- IfcFurnishingElement #16802 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.0 — expliqué : géométries IFC au contact (à la marge près) : collision ou simple contact selon la tessellation
- IfcFurnishingElement #16802 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 0.0 — expliqué : maillage IFC ouvert : test de contact au lieu de la pénétration

## Volume_triang

Paramètres : `{'volume_min': 0.0, 'volume_max': 1000000000.0}`.

- Phases _triang : `Volume_triang   convert: 785 → 735   narrow: 735 → 735   (0.274 s)`
- Phases origine : `Volume   convert: 785 → 785   narrow: 785 → 785   (3.549 s)`
- Mesures comparées sur 735 éléments communs : 70 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 59 maillage IFC ouvert, 50 absent du .ifcview, 9 maillage _triang non fermé une fois réparé, 2 propre au maillage .ifcview
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

Mesures (70) :

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
- ... 30 de plus

## Area_triang

Paramètres : `{'volume_min': 0.0, 'volume_max': 1000000000.0}`.

- Phases _triang : `Area_triang   convert: 785 → 735   narrow: 735 → 735   (0.272 s)`
- Phases origine : `Area   convert: 785 → 785   narrow: 785 → 785   (3.466 s)`
- Mesures comparées sur 735 éléments communs : 7 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 50 absent du .ifcview, 7 propre au maillage .ifcview
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

Mesures (7) :

- IfcFurnishingElement #16802 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490 — écart 0.2619 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (4.3916)
- IfcFlowSegment #86043 Pipe Types:Waste:582999 — écart -0.0111 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.4671)
- IfcFlowSegment #92069 Pipe Types:Waste:583035 — écart -0.0115 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.4868)
- IfcFlowSegment #98788 Pipe Types:Cold Water:583067 — écart -0.0112 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.3604)
- IfcFlowSegment #123108 Pipe Types:Waste:583319 — écart -0.0136 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.5776)
- IfcFlowSegment #130839 Pipe Types:Waste:583332 — écart -0.0136 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.5788)
- IfcFlowSegment #169681 Pipe Types:Waste:594985 — écart -0.0158 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.6742)

## TopOrBottomSurface_triang

Paramètres : `{'surface_min': 0.0, 'surface_max': 1000000000.0, 'top_or_bot_method': 'Top'}`.

- Phases _triang : `TopOrBottomSurface_triang   convert: 785 → 735   narrow: 735 → 735   (17.131 s)`
- Phases origine : `TopOrBottomSurface   convert: 785 → 785   narrow: 785 → 750   (23.406 s)`
- Mesures comparées sur 700 éléments communs : 46 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 50 absent du .ifcview, 35 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 35 maillage _triang non fermé une fois réparé, 11 propre au maillage .ifcview
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

En plus (35) :

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

Mesures (46) :

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
- IfcEnergyConversionDevice #3691 M_Hot Water Boiler - 59-440 kW:147 kW:147 kW:530072 — écart 0.0206 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowMovingDevice #22463 M_Inline Pump - Circulator:3.9 LPS - 0.8 Meter Head:3.9 LPS - 0.8 Meter Head:550094 — écart 0.02 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowMovingDevice #27726 M_Inline Pump - Circulator:3.9 LPS - 0.8 Meter Head:3.9 LPS - 0.8 Meter Head:580717 — écart 0.02 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — écart 0.0114 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowFitting #67372 M_Tee - Generic:Tee - Generic:Tee - Generic:582949 — écart 0.0142 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowFitting #72254 M_Tee - Generic:Tee - Generic:Tee - Generic:582955 — écart 0.0161 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowFitting #80672 M_Tee - Generic:Tee - Generic:Tee - Generic:582979 — écart 0.0139 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowFitting #81069 M_Tee - Generic:Tee - Generic:Tee - Generic:582985 — écart 0.0134 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowFitting #91188 M_Tee - Generic:Tee - Generic:Tee - Generic:583011 — écart 0.015 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowFitting #91583 M_Tee - Generic:Tee - Generic:Tee - Generic:583017 — écart 0.0141 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowFitting #92784 M_Tee - Generic:Tee - Generic:Tee - Generic:583044 — écart 0.0123 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowFitting #93182 M_Tee - Generic:Tee - Generic:Tee - Generic:583049 — écart 0.0122 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- IfcFlowSegment #98788 Pipe Types:Cold Water:583067 — écart -0.0304 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.1797)
- IfcFlowSegment #107188 Pipe Types:Cold Water:583140 — écart -0.0148 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.0872)
- IfcFlowSegment #117083 Pipe Types:Hot Water:583286 — écart -0.0116 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.0688)
- IfcFlowSegment #117695 Pipe Types:Hot Water:583299 — écart -0.0116 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC donne la valeur de l'original (0.0687)
- IfcFlowFitting #130672 M_Tee - Generic:Tee - Generic:Tee - Generic:583327 — écart 0.013 — expliqué : maillage _triang non fermé une fois réparé (jonctions en T entre pièces) : orientation ou volume incertains
- ... 6 de plus

## LateralSurface_triang

Paramètres : `{'surface_min': 0.0, 'surface_max': 1000000000.0, 'direction': [0.0, 1.0, 0.0]}`.

- Phases _triang : `LateralSurface_triang   convert: 785 → 735   narrow: 735 → 724   (0.279 s)`
- Phases origine : `LateralSurface   convert: 785 → 785   narrow: 785 → 766   (11.501 s)`
- Mesures comparées sur 716 éléments communs : 62 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 50 absent du .ifcview, 33 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 27 maillage _triang non fermé une fois réparé, 10 propre au maillage .ifcview
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

En plus (8) :

- IfcFurnishingElement #15463 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159159 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #15856 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:159262 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16149 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160671 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16175 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:160717 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16914 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162493 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16971 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162495 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #16997 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162496 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction
- IfcFurnishingElement #17023 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162497 — distance None — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : l'original ne garde aucun triangle orienté dans la direction

Mesures (62) :

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
- ... 22 de plus

## ProjectedSurface_triang

Paramètres : `{'surface_min': 0.0, 'surface_max': 1000000000.0, 'direction': [0.0, 0.0, 1.0]}`.

- Phases _triang : `ProjectedSurface_triang   convert: 785 → 735   narrow: 735 → 735   (1.814 s)`
- Phases origine : `ProjectedSurface   convert: 785 → 785   narrow: 785 → 750   (12.149 s)`
- Mesures comparées sur 700 éléments communs : 17 écart(s) au-delà de 2 % (au moins 0.011)
- Écarts par cause : 50 absent du .ifcview, 35 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 16 maillage _triang non fermé une fois réparé, 1 propre au maillage .ifcview
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

En plus (35) :

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

Mesures (17) :

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

## ClearanceAxisToAxis_triang

Paramètres : `{'mode': 'MinDistance', 'min_distance': 0.2, 'max_distance': 5.0, 'tolerance': 0.01, 'linearity_ratio': 1.5, 'on_non_linear': 'Fallback', 'parallel_tolerance': 5.0, 'search_radius': 2.0}`.

- Phases _triang : `ClearanceAxisToAxis_triang   convert: 200 → 187   mid: 8700 → 8700   convert_narrow: 187 → 187   narrow: 8700 → 117   (0.199 s)`
- Phases origine : `ClearanceAxisToAxis   convert: 200 → 200   mid: 10000 → 10000   narrow: 10000 → 119   (84.791 s)`
- Écarts par cause : 1 OBB optimale non unique, 1 absent du .ifcview
- 13 élément(s) absent(s) du .ifcview, ignorés (ex. #6743 1xS3BCk291UvhgP2dvNrZJ is not in the .ifcview: skipped)

Manquants (2) :

- IfcSlab #22492 Basic Roof:Live Roof over Wood Joist Flat Roof:184483 → IfcFlowFitting #203298 M_Roof Drain:380 mm Strainer - 25 mm Drain:380 mm Strainer - 25 mm Drain:610131 — distance 0.1487 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : l'axe de la cible suit un autre axe de la boîte
- IfcOpeningElement #22533 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:2 → IfcSpace #125 R301 — distance 0.0 — expliqué : absent du .ifcview

## SurfaceRecover_triang

Paramètres : `{'direction': 'Auto', 'reference': 'Source', 'tolerance': 0.01, 'min_covering': ['relative', 101.0], 'max_covering': None}`.

- Phases _triang : `SurfaceRecover_triang   convert: 785 → 735   broad: 117764 → 1468   mid: 1468 → 1468   convert_narrow: 543 → 543   narrow: 1468 → 76   (0.707 s)`
- Phases origine : `SurfaceRecover   convert: 785 → 785   broad: 142714 → 1492   mid: 1492 → 1492   narrow: 1492 → 52   (60.695 s)`
- Écarts par cause : 27 seuils à ± marge, 3 contact marginal
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (3) :

- IfcWallStandardCase #4465 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139374 → IfcFlowSegment #91909 Pipe Types:Waste:583033 — distance 0.0082 — expliqué : contact marginal : 3.8e-03 m² (0.25 % de la face), bande de largeur équivalente 3.1 mm < marge
- IfcWallStandardCase #4465 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139374 → IfcFlowSegment #92865 Pipe Types:Waste:583045 — distance 0.0082 — expliqué : contact marginal : 4.3e-03 m² (0.28 % de la face), bande de largeur équivalente 3.5 mm < marge
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowSegment #130839 Pipe Types:Waste:583332 — distance 0.0082 — expliqué : contact marginal : 5.2e-03 m² (0.01 % de la face), bande de largeur équivalente 0.8 mm < marge

En plus (27) :

- IfcSpace #1928 B104 → IfcFlowFitting #922797 M_Transition - Generic:Transition - Generic:Transition - Generic:652957 — distance 0.0 — expliqué : seuils à ± marge
- IfcSpace #1928 B104 → IfcFlowFitting #984012 M_Transition - Generic:Transition - Generic:Transition - Generic:674801 — distance 0.0 — expliqué : seuils à ± marge
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #5687 Basic Wall:Interior - Partition (92mm Stud):143921 → IfcFlowTerminal #45821 M_Bath Tub:1525 mmx760 mm - Private:1525 mmx760 mm - Private:582931 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #24680 Basic Wall:Interior - Furring (152 mm Stud):189901 → IfcFlowTerminal #31535 M_Shower Stall - Rectangular:865 mmx815 mm - Private:865 mmx815 mm - Private:582917 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #24680 Basic Wall:Interior - Furring (152 mm Stud):189901 → IfcFlowTerminal #31581 M_Water Closet - Flush Tank:Private - 6.1 Lpf:Private - 6.1 Lpf:582918 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #24680 Basic Wall:Interior - Furring (152 mm Stud):189901 → IfcFlowTerminal #34370 M_Lavatory - Oval:535 mmx485 mm - Private:535 mmx485 mm - Private:582919 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #24680 Basic Wall:Interior - Furring (152 mm Stud):189901 → IfcFlowTerminal #45821 M_Bath Tub:1525 mmx760 mm - Private:1525 mmx760 mm - Private:582931 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #24768 Basic Wall:Interior - Furring (152 mm Stud):190774 → IfcFlowTerminal #28561 M_Shower Stall - Rectangular:865 mmx815 mm - Private:865 mmx815 mm - Private:582914 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #24768 Basic Wall:Interior - Furring (152 mm Stud):190774 → IfcFlowTerminal #31408 M_Water Closet - Flush Tank:Private - 6.1 Lpf:Private - 6.1 Lpf:582915 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #24768 Basic Wall:Interior - Furring (152 mm Stud):190774 → IfcFlowTerminal #519179 M_Lavatory - Oval:535 mmx485 mm - Private:535 mmx485 mm - Private:643259 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowTerminal #45502 M_Lavatory - Oval:650 mmx485 mm - Private:650 mmx485 mm - Private:582926 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowTerminal #45641 M_Lavatory - Oval:650 mmx485 mm - Private:650 mmx485 mm - Private:582927 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowSegment #109894 Pipe Types:Hot Water:583184 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowTerminal #45686 M_Lavatory - Oval:650 mmx485 mm - Private:650 mmx485 mm - Private:582928 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowTerminal #45731 M_Lavatory - Oval:650 mmx485 mm - Private:650 mmx485 mm - Private:582929 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowTerminal #45776 M_Water Closet - Flush Tank:Private - 6.1 Lpf:Private - 6.1 Lpf:582930 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #35199 Basic Wall:Interior - Partition (92mm Stud):203347 → IfcFlowTerminal #45686 M_Lavatory - Oval:650 mmx485 mm - Private:650 mmx485 mm - Private:582928 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #35357 Basic Wall:Interior - Partition (92mm Stud):203998 → IfcFlowTerminal #45641 M_Lavatory - Oval:650 mmx485 mm - Private:650 mmx485 mm - Private:582927 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #37913 Basic Wall:Interior - Furring (38 mm Stud):217414 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #37970 Basic Wall:Interior - Furring (38 mm Stud):217415 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #38015 Basic Wall:Interior - Furring (38 mm Stud):217416 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #38060 Basic Wall:Interior - Furring (38 mm Stud):217417 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #38105 Basic Wall:Interior - Furring (38 mm Stud):217577 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #38150 Basic Wall:Interior - Furring (38 mm Stud):217578 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #38195 Basic Wall:Interior - Furring (38 mm Stud):217579 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge
- IfcWallStandardCase #38240 Basic Wall:Interior - Furring (38 mm Stud):217580 → IfcSpace #125 R301 — distance 0.0 — expliqué : seuils à ± marge

## Ray_Check_triang

Paramètres : `{'max_ray_length': 5.0}`.

- Phases _triang : `Ray_Check_triang   convert: 785 → 735   broad: 117764 → 78527   mid: 78527 → 78527   convert_narrow: 733 → 733   narrow: 78527 → 669   (0.064 s)`
- Phases origine : `Ray_Check   convert: 785 → 785   broad: 142714 → 92424   mid: 92424 → 92424   narrow: 92424 → 667   (53.027 s)`
- Écarts par cause : 10 propre au maillage .ifcview, 8 absent du .ifcview, 4 ensemble d'entrée différent
- 50 élément(s) absent(s) du .ifcview, ignorés (ex. #6293 1xS3BCk291UvhgP2dvNrrP is not in the .ifcview: skipped)

Manquants (10) :

- IfcOpeningElement #12583 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157200:1 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 1.4548 — expliqué : absent du .ifcview
- IfcOpeningElement #12985 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157607:1 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 1.2177 — expliqué : absent du .ifcview
- IfcOpeningElement #13340 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157950:1 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 2.2231 — expliqué : absent du .ifcview
- IfcOpeningElement #14049 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157983:1 → IfcFlowController #852873 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:644888 — distance 1.0059 — expliqué : absent du .ifcview
- IfcOpeningElement #14403 M_Tall Cabinet-Single Door(2):800 mm:800 mm:157984:1 → IfcFlowController #852873 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:644888 — distance 1.4101 — expliqué : absent du .ifcview
- IfcOpeningElement #16306 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:161165:1 → IfcFlowSegment #91909 Pipe Types:Waste:583033 — distance 2.5321 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.0799 — expliqué : absent du .ifcview
- IfcOpeningElement #16847 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490:1 → IfcFlowController #853177 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:645545 — distance 0.1737 — expliqué : absent du .ifcview
- IfcBeam #36686 M_W-Wide Flange:W310X60:W310X60:207325 → IfcFlowSegment #106634 Pipe Types:Cold Water:583131 — distance 3.5906 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcBeam #37325 M_W-Wide Flange:W310X60:W310X60:209260 → IfcFlowSegment #106324 Pipe Types:Cold Water:583127 — distance 3.7973 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original

En plus (12) :

- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowFitting #186519 M_Transition - Generic:Transition - Generic:Transition - Generic:600115 — distance 2.737 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcFurnishingElement #16531 M_Counter Top:600mm Depth:600mm Depth:162231 → IfcFlowController #852873 Kitchen Sink Faucet:Kitchen Sink Faucet:Kitchen Sink Faucet:644888 — distance 2.1631 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFurnishingElement #16802 M_Counter Top w Sink Hole:600mm Depth:600mm Depth:162490 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.1329 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWindow #23162 M_Skylight:1180 x 1170mm:1180 x 1170mm:185337 → IfcSpace #125 R301 — distance 3.6291 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcWindow #23251 M_Skylight:1180 x 1170mm:1180 x 1170mm:185718 → IfcSpace #125 R301 — distance 3.6166 — expliqué : ensemble d'entrée différent : sans les éléments absents du .ifcview (obstacles, membres d'un groupe), l'original donne le même verdict
- IfcFooting #23562 Wall Foundation:Bearing Footing - 900 x 300:186656 → IfcFlowFitting #75616 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:582961 — distance 3.2164 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcFooting #23562 Wall Foundation:Bearing Footing - 900 x 300:186656 → IfcFlowFitting #103531 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583073 — distance 3.3487 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcWallStandardCase #24768 Basic Wall:Interior - Furring (152 mm Stud):190774 → IfcFlowSegment #104962 Pipe Types:Cold Water:583107 — distance 1.0909 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcWallStandardCase #31431 Basic Wall:Interior - Furring (152 mm Stud):193247 → IfcFlowSegment #112645 Pipe Types:Cold Water:583210 — distance 1.6684 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowSegment #113035 Pipe Types:Hot Water:583215 — distance 1.6061 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowFitting #113259 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583218 — distance 1.6095 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcWallStandardCase #31476 Basic Wall:Interior - Furring (152 mm Stud):194166 → IfcFlowFitting #131296 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583561 — distance 2.4187 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original

## OneObjectFace_triang

Paramètres : `{'distance': True, 'min_distance': 0.5, 'max_distance': None, 'intersection': True, 'intersection_tolerance': 0.0, 'orientation': False, 'angle': None, 'angle_tolerance': 0.0, 'face_a_selection': {'orientation': 'Top', 'extreme_faces': True}, 'face_b_selection': {'orientation': 'Bottom', 'extreme_faces': True}, 'skip_adjacent': True}`.

- Phases _triang : `OneObjectFace_triang   convert: 200 → 187   narrow: 187 → 22343   (7.090 s)`
- Phases origine : `OneObjectFace   convert: 200 → 200   narrow: 200 → 33162   (11.795 s)`
- Écarts par cause : 9 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 1 absent du .ifcview
- 13 élément(s) absent(s) du .ifcview, ignorés (ex. #6743 1xS3BCk291UvhgP2dvNrZJ is not in the .ifcview: skipped)

Manquants (6) :

- IfcFurnishingElement #17341 M_Sofa:1830mm:1830mm:167283 — distance 0.3784 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #17815 M_Sofa:1830mm:1830mm:168378 — distance 0.3784 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcOpeningElement #22533 Basic Roof:Live Roof over Wood Joist Flat Roof:184483:2 — distance 0.457 — expliqué : absent du .ifcview
- IfcFurnishingElement #29098 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:191557 — distance 0.2276 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #31313 M_Upper Cabinet-Double Door-Wall:1000 mm:1000 mm:192153 — distance 0.2276 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #31400 M_Upper Cabinet-Double Door-Wall:1000mm:1000mm:192610 — distance 0.2276 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales

En plus (4) :

- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #24060 Compound Ceiling:Gypsum Board:187639 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #24186 Compound Ceiling:Gypsum Board:187659 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #24408 Compound Ceiling:Gypsum Board:187683 — distance 0.057 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales

## TwoObjectsFace_triang

Paramètres : `{'distance': True, 'min_distance': 0.3, 'max_distance': None, 'intersection': True, 'intersection_tolerance': 0.0, 'orientation': False, 'angle': None, 'angle_tolerance': 0.0, 'source_face_selection': {'orientation': 'Top', 'extreme_faces': True}, 'target_face_selection': {'orientation': 'Bottom'}}`.

- Phases _triang : `TwoObjectsFace_triang   convert: 200 → 185   broad: 8526 → 128   mid: 128 → 128   convert_narrow: 89 → 89   narrow: 128 → 5537   (2.579 s)`
- Phases origine : `TwoObjectsFace   convert: 200 → 185   broad: 8526 → 113   mid: 113 → 113   narrow: 113 → 4814   (3.212 s)`
- Écarts par cause : 15 enroulement IFC vers l'intérieur, incohérent ou maillage ouvert, 4 propre au maillage .ifcview
- 13 élément(s) absent(s) du .ifcview, ignorés (ex. #6743 1xS3BCk291UvhgP2dvNrZJ is not in the .ifcview: skipped)

Manquants (3) :

- IfcSpace #1059 A204 → IfcSpace #125 R301 — distance 0.3 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcSpace #2789 B203 → IfcSpace #125 R301 — distance 0.3 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original
- IfcSpace #3325 B205 → IfcSpace #125 R301 — distance 0.3 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original

En plus (16) :

- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcSpace #125 R301 — distance 0.0 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcWall #5399 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:143239 → IfcFlowFitting #203298 M_Roof Drain:380 mm Strainer - 25 mm Drain:380 mm Strainer - 25 mm Drain:610131 — distance 0.1185 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #16667 M_Base Cabinet-Double Door & 2 Drawer:1000mm:1000mm:162487 → IfcFlowTerminal #40654 M_Sink - Island - Single:455 mmx455 mm - Private:455 mmx455 mm - Private:582920 — distance 0.287 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #76106 Pipe Types:Waste:582976 — distance 0.2231 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #80835 Pipe Types:Waste:582982 — distance 0.1183 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowSegment #81234 Pipe Types:Waste:582987 — distance 0.1988 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #23826 Compound Ceiling:Gypsum Board:187470 → IfcFlowFitting #122783 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583314 — distance 0.0634 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #24060 Compound Ceiling:Gypsum Board:187639 → IfcSpace #125 R301 — distance 0.243 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #24186 Compound Ceiling:Gypsum Board:187659 → IfcSpace #125 R301 — distance 0.243 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcCovering #24408 Compound Ceiling:Gypsum Board:187683 → IfcSpace #125 R301 — distance 0.243 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #35854 M_Vanity Cabinet-Double Door Sink Unit:650 x 450 mm:650 x 450 mm:205239 → IfcFlowFitting #982544 M_Transition - Generic:Transition - Generic:Transition - Generic:673888 — distance 0.2466 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #36423 M_Vanity Cabinet-Double Door Sink Unit:450 x 450 mm:450 x 450 mm:205548 → IfcFlowFitting #115782 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583269 — distance 0.1759 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #36423 M_Vanity Cabinet-Double Door Sink Unit:450 x 450 mm:450 x 450 mm:205548 → IfcFlowFitting #117302 M_Tee - Generic:Tee - Generic:Tee - Generic:583294 — distance 0.1643 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #36423 M_Vanity Cabinet-Double Door Sink Unit:450 x 450 mm:450 x 450 mm:205548 → IfcFlowFitting #520587 M_Transition - Generic:Transition - Generic:Transition - Generic:643346 — distance 0.2446 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcFurnishingElement #36423 M_Vanity Cabinet-Double Door Sink Unit:450 x 450 mm:450 x 450 mm:205548 → IfcFlowFitting #521264 M_Transition - Generic:Transition - Generic:Transition - Generic:643752 — distance 0.1565 — expliqué : enroulement IFC vers l'intérieur, incohérent ou maillage ouvert : la sélection de faces par orientation (Top, Bottom) lit les normales
- IfcBeam #36686 M_W-Wide Flange:W310X60:W310X60:207325 → IfcFlowFitting #123184 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583320 — distance 0.2689 — expliqué : propre au maillage .ifcview : la même règle sur les triangles IFC de la paire donne le verdict de l'original

## FreeSpace_triang

Paramètres : `{'diameter': 1.0, 'height': 2.0}`.

- Phases _triang : `FreeSpace_triang   convert: 785 → 735   narrow: 735 → 735   (0.046 s)`
- Phases origine : `FreeSpace   convert: 785 → 785   narrow: 785 → 785   (13.351 s)`
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
