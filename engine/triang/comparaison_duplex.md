# Règles _triang contre règles d'origine

- Source : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifc` (286 éléments)
- Cible : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifc` (524 éléments)
- .ifcview : `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Architecture.ifcview`, `/home/jocelin/Documents/200 - IFC/IfcSampleFiles-main/Ifc2x3_Duplex_Mechanical.ifcview`
- Marge d'explication des écarts : 0.011 m (flèche .ifcview + flèche IFC)

« Froid » : ouverture d'une session (lecture de l'IFC, métadonnées du .ifcview) et première exécution (conversion IFC pour la règle d'origine, décodage du .ifcview pour la règle _triang). « Chaud » : la même règle relancée dans la session.

| Règle | Résultats origine | Résultats _triang | Communs | Manquants | En plus | Inexpliqués | Origine froid | Origine chaud | _triang froid | _triang chaud | Gain froid | Gain chaud |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Intersection_triang | 802 | 770 | 730 | 72 | 40 | 0 | 1.73 s | 0.35 s | 0.62 s | 0.34 s | ×2.8 | ×1.0 |
| Above_triang | 1359 | 1420 | 1296 | 63 | 124 | 0 | 46.36 s | 15.03 s | 0.35 s | 0.12 s | ×133.4 | ×122.0 |
| OBB_Above_triang | 2259 | 2108 | 2078 | 181 | 30 | 0 | 8.57 s | 3.72 s | 0.33 s | 0.05 s | ×26.1 | ×71.6 |

## Intersection_triang

Paramètres : `{'tolerance': 0.002}`.

- Phases _triang : `Intersection_triang   convert: 810 → 760   broad: 123664 → 1454   mid: 1454 → 1454   convert_narrow: 691 → 691   narrow: 1454 → 770   (0.427 s)`
- Phases origine : `Intersection   convert: 810 → 810   broad: 149864 → 1600   mid: 1600 → 1590   narrow: 1590 → 802   (1.552 s)`
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

- Phases _triang : `Above_triang   convert: 810 → 760   broad: 123664 → 2207   mid: 2207 → 2189   convert_narrow: 687 → 687   narrow: 2189 → 1420   (0.096 s)`
- Phases origine : `Above   convert: 810 → 810   broad: 149864 → 2394   mid: 2394 → 2346   narrow: 2346 → 1359   (46.098 s)`
- Écarts par cause : 61 absent du .ifcview, 52 faux négatif de l'original, 52 écart vertical au bord de [0, tolérance], 12 faux négatif de l'original, vérifié sur l'IFC, 8 seuils à ± marge, 2 faux positif de l'original
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

En plus (124) :

- IfcSpace #67 A102 → IfcFlowSegment #38151 Pipe Types:Mechanical Pipe:557527 — distance 0.0588 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.7 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #67 A102 → IfcFlowSegment #132471 Pipe Types:Mechanical Pipe:631911 — distance 0.144 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.6 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #11485 Pipe Types:Mechanical Pipe:546131 — distance 0.1443 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #38151 Pipe Types:Mechanical Pipe:557527 — distance 0.0527 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.7 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #212 A103 → IfcFlowSegment #135882 Pipe Types:Mechanical Pipe:631996 — distance 0.1392 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #355 A104 → IfcFlowSegment #21037 Pipe Types:Mechanical Pipe:550018 — distance 0.1444 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.144 m au-dessus de la source en (6.23, -9.95)
- IfcSpace #355 A104 → IfcFlowSegment #21217 Pipe Types:Mechanical Pipe:550028 — distance 0.5869 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.590 m au-dessus de la source en (6.23, -9.91)
- IfcSpace #355 A104 → IfcFlowSegment #22034 Pipe Types:Mechanical Pipe:550077 — distance 0.5869 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.590 m au-dessus de la source en (6.23, -9.24)
- IfcSpace #514 A101 → IfcFlowSegment #128136 Pipe Types:Mechanical Pipe:631126 — distance 0.1437 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.5 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #514 A101 → IfcFlowSegment #135882 Pipe Types:Mechanical Pipe:631996 — distance 0.1444 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1627 B102 → IfcFlowSegment #8141 Pipe Types:Mechanical Pipe:540175 — distance 0.1487 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1627 B102 → IfcFlowSegment #143609 Pipe Types:Mechanical Pipe:633327 — distance 0.0544 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1627 B102 → IfcFlowSegment #144732 Pipe Types:Mechanical Pipe:633360 — distance 0.0544 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1782 B103 → IfcFlowSegment #8141 Pipe Types:Mechanical Pipe:540175 — distance 0.1427 — expliqué : faux négatif de l'original : sa grille de rayons (pas 6.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1782 B103 → IfcFlowSegment #39436 Pipe Types:Mechanical Pipe:557553 — distance 0.0544 — expliqué : faux négatif de l'original : sa grille de rayons (pas 8.8 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #1928 B104 → IfcFlowSegment #46770 Pipe Types:Mechanical Pipe:557647 — distance 0.0505 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.053 m au-dessus de la source en (2.57, -7.55)
- IfcSpace #1928 B104 → IfcFlowSegment #46950 Pipe Types:Mechanical Pipe:557648 — distance 0.5869 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.590 m au-dessus de la source en (2.57, -7.87)
- IfcSpace #1928 B104 → IfcFlowSegment #47767 Pipe Types:Mechanical Pipe:557656 — distance 0.5869 — expliqué : seuils à ± marge
- IfcSpace #2108 B101 → IfcFlowSegment #139518 Pipe Types:Mechanical Pipe:632681 — distance 0.0526 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.4 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcSpace #2108 B101 → IfcFlowSegment #143609 Pipe Types:Mechanical Pipe:633327 — distance 0.0544 — expliqué : faux négatif de l'original : sa grille de rayons (pas 7.3 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4643 Basic Wall:Foundation - Concrete (417mm):140479 → IfcFlowSegment #42359 Pipe Types:Mechanical Pipe:557590 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4643 Basic Wall:Foundation - Concrete (417mm):140479 → IfcFlowSegment #42799 Pipe Types:Mechanical Pipe:557597 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4818 Basic Wall:Foundation - Concrete (417mm):140520 → IfcFlowSegment #43285 Pipe Types:Mechanical Pipe:557601 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4818 Basic Wall:Foundation - Concrete (417mm):140520 → IfcFlowSegment #43882 Pipe Types:Mechanical Pipe:557605 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 4.9 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4818 Basic Wall:Foundation - Concrete (417mm):140520 → IfcFlowSegment #148417 Pipe Types:Mechanical Pipe:649433 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4818 Basic Wall:Foundation - Concrete (417mm):140520 → IfcFlowSegment #149234 Pipe Types:Mechanical Pipe:649463 — distance 0.1984 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.0 cm) passe à côté d'un objet de 3.3 cm en plan
- IfcWallStandardCase #4868 Basic Wall:Foundation - Concrete (417mm):140554 → IfcFlowSegment #15805 Pipe Types:Mechanical Pipe:547286 — distance 0.1158 — expliqué : faux négatif de l'original : sa grille de rayons (pas 5.2 cm) passe à côté d'un objet de 3.3 cm en plan
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
- IfcSlab #6132 Floor:Residential - Wood Joist with Subflooring:144800 → IfcFlowSegment #40138 Pipe Types:Mechanical Pipe:557563 — distance 0.0744 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.034 m au-dessus de la source en (2.46, -10.88)
- IfcSlab #6247 Floor:Residential - Wood Joist with Subflooring:144872 → IfcFlowSegment #12343 Pipe Types:Mechanical Pipe:546826 — distance 0.068 — expliqué : faux négatif de l'original, vérifié sur l'IFC : la cible est 0.068 m au-dessus de la source en (6.34, -6.89)
- ... 84 de plus

## OBB_Above_triang

Paramètres : `{'tolerance': 1.0}`.

- Phases _triang : `OBB_Above_triang   convert: 810 → 760   broad: 123664 → 2207   mid: 2207 → 2189   convert_narrow: 687 → 687   narrow: 2189 → 2108   (0.078 s)`
- Phases origine : `OBB_Above   convert: 810 → 810   broad: 149864 → 2394   mid: 2394 → 2394   narrow: 2394 → 2259   (8.347 s)`
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
- IfcRailing #32346 Railing:900mm Handrail Only:198880 → IfcFlowSegment #143872 Pipe Types:Mechanical Pipe:633332 — distance 0.0 — expliqué : OBB optimale non unique (mêmes dimensions, axes tournés) : la bande « au-dessus » suit un autre axe
