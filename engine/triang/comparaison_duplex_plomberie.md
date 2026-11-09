# Règles _triang contre règles d'origine

- Source : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifc` (286 éléments)
- Cible : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Plumbing.ifc` (499 éléments)
- .ifcview : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifcview`, `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Plumbing.ifcview`
- Marge d'explication des écarts : 0.011 m (flèche .ifcview + flèche IFC)

« Froid » : ouverture d'une session (lecture de l'IFC, métadonnées du .ifcview) et première exécution (conversion IFC pour la règle d'origine, décodage du .ifcview pour la règle _triang). « Chaud » : la même règle relancée dans la session.

| Règle | Résultats origine | Résultats _triang | Communs | Manquants | En plus | Inexpliqués | Origine froid | Origine chaud | _triang froid | _triang chaud | Gain froid | Gain chaud |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Intersection_triang | 572 | 572 | 562 | 10 | 10 | 0 | 4.64 s | 0.49 s | 1.40 s | 0.45 s | ×3.3 | ×1.1 |
| Above_triang | 876 | 986 | 851 | 25 | 135 | 0 | 71.68 s | 30.46 s | 1.01 s | 0.11 s | ×71.3 | ×285.5 |
| OBB_Above_triang | 1717 | 1701 | 1692 | 25 | 9 | 0 | 16.34 s | 4.86 s | 0.93 s | 0.05 s | ×17.5 | ×95.6 |

## Intersection_triang

Paramètres : `{'tolerance': 0.002}`.

- Phases _triang : `Intersection_triang   convert: 785 → 735   broad: 117764 → 902   mid: 902 → 902   convert_narrow: 481 → 481   narrow: 902 → 572   (0.607 s)`
- Phases origine : `Intersection   convert: 785 → 785   broad: 142714 → 909   mid: 909 → 908   narrow: 908 → 572   (3.975 s)`
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

- Phases _triang : `Above_triang   convert: 785 → 735   broad: 117764 → 1712   mid: 1712 → 1712   convert_narrow: 618 → 618   narrow: 1712 → 986   (0.166 s)`
- Phases origine : `Above   convert: 785 → 785   broad: 142714 → 1735   mid: 1735 → 1735   narrow: 1735 → 876   (70.764 s)`
- Écarts par cause : 90 faux négatif de l'original, 32 écart vertical au bord de [0, tolérance], 22 absent du .ifcview, 9 faux négatif de l'original, vérifié sur l'IFC, 7 seuils à ± marge
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
- IfcSpace #212 A103 → IfcFlowSegment #92152 Pipe Types:Waste:583036 — distance 0.2549 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.255 m au-dessus de la source en (4.72, -10.56)
- IfcSpace #212 A103 → IfcFlowSegment #110435 Pipe Types:Cold Water:583192 — distance 0.3999 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.399 m au-dessus de la source en (4.70, -10.37)
- IfcSpace #212 A103 → IfcFlowSegment #110745 Pipe Types:Cold Water:583197 — distance 0.4095 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.6 cm) passe à côté d'un objet de 0.6 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #112086 Pipe Types:Hot Water:583202 — distance 0.5095 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.4 cm) passe à côté d'un objet de 0.6 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #123108 Pipe Types:Waste:583319 — distance 0.1635 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.6 cm) passe à côté d'un objet de 4.8 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #191477 Pipe Types:PVC:604577 — distance 0.0457 — expliqué : faux négatif de l'original : sa grille de rayons (pas 3.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #199183 Pipe Types:PVC:605583 — distance 0.0457 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #355 A104 → IfcFlowSegment #518236 Pipe Types:Cold Water:642715 — distance 0.4143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.8 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSpace #355 A104 → IfcFlowSegment #518675 Pipe Types:Hot Water:642757 — distance 0.5143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.6 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSpace #355 A104 → IfcFlowSegment #518846 Pipe Types:Cold Water:642822 — distance 0.4143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.8 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSpace #355 A104 → IfcFlowSegment #519015 Pipe Types:Cold Water:642869 — distance 0.5143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.6 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSpace #1627 B102 → IfcFlowSegment #186965 Pipe Types:PVC:604361 — distance 0.1159 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1782 B103 → IfcFlowSegment #81234 Pipe Types:Waste:582987 — distance 0.2621 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.260 m au-dessus de la source en (4.10, -7.43)
- IfcSpace #1782 B103 → IfcFlowSegment #109656 Pipe Types:Hot Water:583180 — distance 0.4901 — expliqué : faux négatif de l'original : sa grille de rayons (pas 2.7 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSpace #1782 B103 → IfcFlowSegment #113337 Pipe Types:Hot Water:583220 — distance 0.5095 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.4 cm) passe à côté d'un objet de 0.6 cm en plan
- IfcSpace #1782 B103 → IfcFlowSegment #130839 Pipe Types:Waste:583332 — distance 0.1556 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.6 cm) passe à côté d'un objet de 4.8 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #517268 Pipe Types:Cold Water:642079 — distance 0.4143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.6 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #517708 Pipe Types:Hot Water:642220 — distance 0.5143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.4 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #517913 Pipe Types:Cold Water:642353 — distance 0.4143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.6 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #517994 Pipe Types:Hot Water:642376 — distance 0.5143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.3 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcWallStandardCase #4287 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139234 → IfcFlowSegment #109656 Pipe Types:Hot Water:583180 — distance 0.2951 — expliqué : faux négatif de l'original : sa grille de rayons (pas 2.7 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcWallStandardCase #4287 Basic Wall:Party Wall - CMU Residential Unit Dimising Wall:139234 → IfcFlowSegment #113186 Pipe Types:Hot Water:583217 — distance 0.2938 — expliqué : seuils à ± marge
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #76025 Pipe Types:Waste:582975 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #93651 Pipe Types:Cold Water:583055 — distance 0.7377 — expliqué : faux négatif de l'original : sa grille de rayons (pas 2.4 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSlab #5165 Floor:127mm Slab on Grade:141232 → IfcFlowSegment #117083 Pipe Types:Hot Water:583286 — distance 0.5898 — expliqué : faux négatif de l'original : sa grille de rayons (pas 3.5 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSlab #5267 Floor:127mm Slab on Grade:143106 → IfcFlowSegment #114351 Pipe Types:Hot Water:583239 — distance 0.767 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.1 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSlab #5267 Floor:127mm Slab on Grade:143106 → IfcFlowSegment #117695 Pipe Types:Hot Water:583299 — distance 0.5892 — expliqué : faux négatif de l'original : sa grille de rayons (pas 3.5 cm) passe à côté d'un objet de 2.5 cm en plan
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowFitting #112879 M_Tee - Generic:Tee - Generic:Tee - Generic:583213 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowFitting #113108 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583216 — distance 0.0032 — expliqué : écart vertical 0.0032 au bord de [0, tolérance]
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowFitting #130916 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583536 — distance 0.0025 — expliqué : écart vertical 0.0025 au bord de [0, tolérance]
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #517268 Pipe Types:Cold Water:642079 — distance 0.7132 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.6 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #517708 Pipe Types:Hot Water:642220 — distance 0.0143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.4 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #517994 Pipe Types:Hot Water:642376 — distance 0.0143 — expliqué : faux négatif de l'original : sa grille de rayons (pas 1.3 cm) passe à côté d'un objet de 1.3 cm en plan
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #976791 Pipe Types:Hot Water:666333 — distance 0.7375 — expliqué : seuils à ± marge
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowFitting #109185 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583172 — distance 0.0032 — expliqué : écart vertical 0.0032 au bord de [0, tolérance]
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowSegment #109656 Pipe Types:Hot Water:583180 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowFitting #114034 M_Tee - Generic:Tee - Generic:Tee - Generic:583234 — distance 0.0 — expliqué : écart vertical 0.0000 au bord de [0, tolérance]
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowFitting #117768 M_Elbow - Generic:Elbow - Generic:Elbow - Generic:583305 — distance 0.0025 — expliqué : écart vertical 0.0025 au bord de [0, tolérance]
- ... 95 de plus

## OBB_Above_triang

Paramètres : `{'tolerance': 1.0}`.

- Phases _triang : `OBB_Above_triang   convert: 785 → 735   broad: 117764 → 1712   mid: 1712 → 1712   convert_narrow: 618 → 618   narrow: 1712 → 1701   (0.065 s)`
- Phases origine : `OBB_Above   convert: 785 → 785   broad: 142714 → 1735   mid: 1735 → 1735   narrow: 1735 → 1717   (15.572 s)`
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
