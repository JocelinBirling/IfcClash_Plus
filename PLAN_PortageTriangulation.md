# Plan de déploiement : les 28 règles sur triangulations

Objectif : porter l'ensemble des règles de `libifcclash_engine` pour qu'elles
calculent sur des **triangles** au lieu de B-Rep OpenCascade, avec le code le
plus rapide possible et sans perdre la justesse des règles d'origine.

Ce plan s'appuie sur l'existant :
- le portage C++ des 28 règles (`Rapport_PortageCPP.md`) ;
- les trois règles `_triang` (`engine/triang/README.md`) : `Intersection_triang`,
  `Above_triang`, `OBB_Above_triang` ;
- les bancs `doc/benchmark_engines.md` et `doc/benchmark_extreme_faces.md`.

---

## 1. Constat de départ

### 1.1 Où sont les B-Rep aujourd'hui

| Règle | Géométrie actuelle | Opérations B-Rep (C++) |
|---|---|---|
| Volume, Area | triangles (`MeshLocal`) | — |
| TopOrBottomSurface, LateralSurface, ProjectedSurface | triangles (`MeshWorld`) | — (faces extrêmes et unions GEOS) |
| OneObjectFace, TwoObjectsFace | triangles (`MeshWorld`) | — |
| Intersection, Clearance, Collision | triangles (arbre IfcOpenShell) | — |
| Ray_Check, DirectView | triangles (`MeshWorld`) | segment contre forme : `BRepExtrema_DistShapeShape` sur une arête |
| FreeSpace | triangles (`MeshWorld`) | `BRepPrimAPI_MakeBox`, `BRepAlgoAPI_Common`, `BRepMesh_IncrementalMesh` |
| ObbHigh, ObbLength, Orientation | B-Rep (`BrepWorld`) | maillage à 1 cm (`meshed_brep`), puis OBB |
| AngleBetween, Alignement | B-Rep | `meshed_brep`, puis OBB |
| ClearanceAxisToAxis | B-Rep | OBB, `BRepExtrema_DistShapeShape` |
| Intersection2 | B-Rep | couture, `MakeSolid`, `BRepAlgoAPI_Common`, `BRepGProp` (volume commun) |
| Above, Below | B-Rep | `meshed_brep`, 50 × 50 rayons `BRepIntCurveSurface_Inter` |
| OBB_Above, OBB_Below, OBB_Front_And_Back, OBB_Custom | B-Rep | `meshed_brep`, OBB, zone extrudée, test de la zone contre la forme |
| SurfaceRecover | B-Rep + triangles | `BRepExtrema_DistShapeShape` entre faces |
| ClearanceForDoors | B-Rep + triangles | prisme `BRepPrimAPI_MakePrism`, `BRepClass3d_SolidClassifier`, `BRepExtrema_DistShapeShape` |

Bilan :
- **10 règles** sont déjà sur triangles (seule leur source peut changer) ;
- **13 règles** reposent sur un B-Rep ;
- **5 règles** mélangent les deux : Ray_Check, DirectView, FreeSpace,
  SurfaceRecover, ClearanceForDoors.

### 1.2 Ce qu'on sait déjà

- **Le coût dominant est la conversion IFC en B-Rep**, puis les opérations
  OpenCascade (rayons, extrema, booléens). Exemples mesurés :
  - Above passe de 46 s à 0,35 s avec `Above_triang` (×133) ;
  - OBB_Above passe de 8,6 s à 0,33 s avec `OBB_Above_triang` (×26) ;
  - Intersection ne gagne que ×2,8, car elle est déjà sur triangles.
- **Les triangulations sont imparfaites** :
  - la triangulation IFC est souvent ouverte : 32 éléments Mechanical sur
    524 sont fermés, contre 256 maillages `.ifcview` sur 286 ;
  - beaucoup de maillages sont orientés vers l'intérieur ;
  - les normales stockées du `.ifcview` ne sont pas fiables.

  Tout algorithme qui dépend de l'orientation ou de la fermeture doit
  donc s'en passer, ou réparer le maillage d'abord.
- **Les briques existent déjà en partie dans `engine/triang`** : test
  triangle contre OBB (axes séparateurs), découpage en plan, BVH de boîtes,
  triangles vus (échantillonnage et carte de hauteur), OBB optimale.

---

## 2. Principes d'optimisation

Ils s'appliquent à tout le code produit.

1. **Une seule géométrie par élément et par session.** Le maillage est
   décodé, soudé et indexé une fois, puis partagé par toutes les règles du
   fichier de règles. Il est servi par le cache de session existant
   (`GeometryProvider::derived`).
2. **Toute donnée dérivée est calculée une fois, à la demande, et gardée**,
   pour chaque élément :
   - les OBB (optimale, debout) ;
   - les cartes de hauteur et les triangles vus par côté ;
   - les faces planes regroupées ;
   - l'axe principal ;
   - le volume et l'aire ;
   - le BVH de triangles.

   Plusieurs règles du même fichier se partagent ainsi le travail.
3. **Pas d'objet OpenCascade dans les boucles chaudes.** Pas de `TopoDS_*`,
   pas de `BRep*` ; des tableaux contigus de `double` et d'`int`. OCCT ne
   sert plus que pour `Bnd_OBB::ReBuild` et les BVH génériques.
4. **BVH partout où l'on cherche des voisins** : triangles d'un élément,
   éléments d'un fichier, faces d'un élément. Jamais de double boucle sur
   des triangles.
5. **Sortie au premier résultat** quand la règle ne demande qu'un oui ou
   un non. Le calcul complet n'est fait que pour la mesure rapportée.
6. **Préfiltres en cascade, du moins cher au plus cher** : boîte alignée,
   puis OBB, puis triangles. Les préfiltres ne font qu'éliminer des
   paires, jamais en ajouter ; c'est vérifié par un test.
7. **Parallélisme à deux niveaux** :
   - les données par élément (déjà en place : `parallel_safe`,
     `for_each_element`) ;
   - **la phase fine des paires**, à paralléliser dans ce chantier : c'est
     aujourd'hui la partie séquentielle des règles de paires.
8. **Méthode choisie selon la taille quand deux méthodes existent.**
   Exemple : `visible_triangles_auto` prend l'échantillonnage sous 200
   triangles et la carte de hauteur au-delà. Le seuil est mesuré, pas deviné.
9. **Indépendance de l'orientation et de la fermeture** :
   - les tests intérieur/extérieur passent par un nombre d'enroulement
     généralisé (*winding number*), qui tolère les maillages ouverts, ou
     par la parité de rayons sur maillage soudé ;
   - aucun test ne lit les normales stockées.

---

## 3. Architecture cible

### 3.1 Une seule implémentation par règle, deux sources de triangles

Chaque règle `_triang` lit un maillage monde par élément, sans savoir
d'où il vient :

| Source | Variante | Usage |
|---|---|---|
| `.ifcview` (BonsaiViewer) | `Variant::ViewMesh` | le plus rapide : aucune conversion IFC |
| Triangulation IFC à la volée | `Variant::MeshWorld` | sans `.ifcview`, ou pour la précision de l'IFC |

La source est choisie à la session, par un paramètre commun, sans
dupliquer de code. La convention de nommage reste celle déjà en place :
le suffixe `_triang`, à côté des règles d'origine, qui gardent leur parité
avec Python.

### 3.2 Couches de code (`engine/triang/`)

```
engine/triang/
  mesh/        TriMesh : sommets, triangles, données par triangle (normale,
               aire, boîte), soudure, réorientation, test « fermé »
  spatial/     BVH de triangles et d'éléments, requêtes boîte, rayon, distance
  kernels/     tests élémentaires, sans allocation :
                 triangle / OBB, triangle / triangle (intersection, distance),
                 point / triangle, rayon / triangle, découpage plan et 3D,
                 winding number, volume signé
  derived/     données dérivées gardées en session :
                 OBB optimale et OBB debout, cartes de hauteur, triangles vus,
                 faces planes regroupées, axe principal, volume, aire
  rules/       les règles _triang, une par fichier ou par famille
  tests/       Catch2 [triang] par couche et par règle
  bench/       comparaison avec les règles d'origine et chronométrage
```

Les fichiers actuels (`ViewTriangles`, `TriangleTests`, `HeightMap`,
`TriangRules`) sont répartis dans ces couches à la phase 0, sans changer
leur comportement.

### 3.3 Les briques à écrire

| Brique | Algorithme | Sert à |
|---|---|---|
| `TriMesh` | soudure des sommets, réorientation par propagation sur les arêtes, détection de maillage fermé | toutes |
| BVH de triangles | `BVH_BoxSet` OCCT ou BVH maison à plat (tableau de nœuds) | distance, rayons, intersection |
| Distance triangle / triangle | Eberly ou Lin-Canny, avec élagage par BVH contre BVH | Clearance, ClearanceAxisToAxis, SurfaceRecover, ClearanceForDoors |
| Intersection triangle / triangle | Möller ou Guigue-Devillers | Collision, OneObjectFace, TwoObjectsFace |
| Rayon / triangle | Möller-Trumbore, parcours de BVH | Ray_Check, DirectView, intérieur/extérieur |
| Winding number | somme des angles solides, accélérée par BVH | intérieur/extérieur, volume commun |
| Découpage 3D | Sutherland-Hodgman sur les plans d'un polyèdre convexe | FreeSpace, ClearanceForDoors, OBB_Custom |
| Polyèdre convexe / triangle | axes séparateurs généralisés (faces et arêtes du polyèdre) | zones de détection non boîtes (portes) |
| OBB debout | rectangle d'aire minimale de l'emprise (calipers tournants), hauteur de z min à z max | règles directionnelles, ObbHigh |
| Faces planes | regroupement de triangles voisins coplanaires (croissance de région) | règles de faces, SurfaceRecover, TopOrBottomSurface |
| Axe principal | axe de l'OBB, ou ACP pondérée par l'aire | AngleBetween, ClearanceAxisToAxis, Alignement, Orientation |
| Volume commun | intégration par colonnes : sur une grille en plan, intervalles intérieurs de A et de B le long de chaque verticale (parité des croisements), produit des longueurs communes par l'aire de la maille | Intersection2 |

---

## 4. Correspondance règle par règle

Légende de difficulté : **S** simple (briques existantes), **M** moyen
(une brique nouvelle), **L** lourd (algorithme nouveau ou sémantique à
revoir).

| Règle | Méthode sur triangles | Briques | Diff. | Risque d'écart |
|---|---|---|---|---|
| Volume | volume signé du maillage soudé, réorienté | `TriMesh` | S | maillages ouverts : volume non défini, à signaler en diagnostic |
| Area | somme des aires | — | S | aucun |
| TopOrBottomSurface | aire des triangles vus (`visible_triangles_auto`) | dérivées | S | la méthode actuelle filtre sur les normales : 14,7 % de surface manquée mesurée |
| LateralSurface | aire des triangles vus selon la direction horizontale demandée | carte de hauteur orientée | M | même cause |
| ProjectedSurface | aire de l'union projetée (GEOS gardé, ou nombre de mailles de la carte) | carte de hauteur | S | précision de la maille si la carte est utilisée |
| ObbHigh, ObbLength | OBB optimale des sommets | `optimal_obb` | S | OBB non unique pour les sections carrées ou rondes |
| Orientation | axes de l'OBB | `optimal_obb` | S | idem |
| OneObjectFace, TwoObjectsFace | faces planes regroupées, puis distance, intersection et angle entre faces | faces planes, distance, intersection | M | définition d'une « face » : regroupement à valider |
| AngleBetween | axes des OBB | `optimal_obb` | S | OBB non unique |
| Intersection | arbre IfcOpenShell (déjà fait : `Intersection_triang`) | — | fait | maillages ouverts (expliqué) |
| Clearance | arbre IfcOpenShell, `clash_clearance_many` | — | S | flèche de maillage au bord du seuil |
| Collision | arbre IfcOpenShell, `clash_collision_many` | — | S | idem |
| Intersection2 | volume commun par intégration en colonnes | winding number ou parité, grille | L | maillages ouverts ; précision de la grille |
| ClearanceAxisToAxis | axes d'OBB, distance triangle / triangle par BVH en repli | axe, distance | M | flèche |
| Above | fait (`Above_triang`) | — | fait | expliqué |
| Below | `Above_triang` avec les côtés inversés | — | S | idem |
| OBB_Above | fait (`OBB_Above_triang`) | — | fait | expliqué |
| OBB_Below, OBB_Front_And_Back | même noyau, autre bande extrudée | triangle / OBB | S | OBB non unique (Front_And_Back) |
| OBB_Custom | zones issues de l'OBB, éventuellement non boîtes | polyèdre convexe / triangle | M | — |
| SurfaceRecover | faces planes de la cible, couverture par projection des triangles de la source à moins de la tolérance | faces planes, distance, GEOS | M | définition des faces |
| ClearanceForDoors | zone de débattement en polyèdre convexe, triangles des obstacles découpés et testés, profondeur par distance aux plans | découpage 3D, polyèdre / triangle | L | zone en arc (`zone_shape`) à approcher par polyèdre |
| Ray_Check, DirectView | rayons contre BVH de triangles des obstacles | rayon / triangle | M | gain attendu très fort (plus d'arête OCCT par rayon) |
| FreeSpace | découpage des triangles par la tranche de hauteur, puis unions GEOS existantes | découpage 3D | M | — |
| Alignement | axes d'OBB, puis le regroupement existant | `optimal_obb` | S | OBB non unique |

---

## 5. Déploiement par vagues

L'ordre suit le rapport **gain × réutilisation / risque**. Chaque vague
produit des règles complètes, testées et comparées, et réutilise les
briques des vagues précédentes.

### Phase 0 : fondations

- Réorganiser `engine/triang` selon §3.2, sans changer le comportement
  (tests `[triang]` identiques).
- `TriMesh` : soudure, réorientation, détection de maillage fermé.
- Cache des données dérivées par élément (OBB optimale et debout, triangles
  vus, BVH).
- Source de triangles commune : `ViewMesh` ou `MeshWorld`, au choix de la
  session.
- **Parallélisation de la phase fine des paires**, utile à toutes les règles
  de paires.
- Généraliser `compare_triang.py` en un comparateur unique : une règle
  d'origine, sa version `_triang`, trois maquettes, chaque écart rangé dans
  une cause vérifiée.

Fin de phase : tests `[triang]` verts, les trois règles `_triang` existantes
inchangées (mêmes résultats), comparateur prêt.

### Vague 1 : les règles OBB (gain fort, risque faible)

ObbHigh, ObbLength, Orientation, AngleBetween, Alignement, OBB_Below,
OBB_Front_And_Back, Below.

- Briques : `optimal_obb`, OBB debout, triangle / OBB, `Above_triang`.
- Gain attendu de l'ordre de celui d'`OBB_Above_triang` (×26 à froid) : ces
  règles ne paient aujourd'hui que la conversion B-Rep et le maillage à 1 cm.

### Vague 2 : les règles déjà sur triangles

Volume, Area, TopOrBottomSurface, LateralSurface, ProjectedSurface,
Clearance, Collision.

- Elles passent sur les briques communes et la source `.ifcview`.
- TopOrBottomSurface et LateralSurface passent aux triangles vus,
  indépendants de l'orientation. C'est un **changement de résultat
  volontaire** : la méthode actuelle manque 14,7 % de la surface vue sur le
  Duplex.

### Vague 3 : rayons et distances

Ray_Check, DirectView, ClearanceAxisToAxis, SurfaceRecover, OBB_Custom.

- Briques nouvelles : BVH de triangles, rayon / triangle, distance
  triangle / triangle, polyèdre convexe / triangle, faces planes.

### Vague 4 : faces et zones complexes

OneObjectFace, TwoObjectsFace, FreeSpace, ClearanceForDoors.

- Briques nouvelles : regroupement en faces planes (déjà prêt en vague 3),
  découpage 3D.

### Vague 5 : Intersection2

- Volume commun par intégration en colonnes, avec winding number pour les
  maillages ouverts.
- Seule règle dont l'algorithme est entièrement nouveau ; elle passe en
  dernier pour bénéficier de toutes les briques et du recul des autres
  vagues.

### Phase finale : intégration et rapport

- Benchmark complet : règles d'origine, C++ B-Rep et `_triang`, à froid et
  à chaud, sur le Duplex et une seconde maquette.
- Rapport des écarts par règle, et mise à jour de `engine/triang/README.md`
  et de `Rapport_PortageCPP.md`.
- Exposition Python et interface : selon la décision §7.

---

## 6. Validation

Pour chaque règle portée :

1. **Tests unitaires Catch2** sur des cas construits à la main : boîtes,
   bandes, pentes, maillages ouverts, triangles minuscules, faces confondues.
2. **Comparaison avec la règle d'origine**, à tolérance, sur trois maquettes
   (Duplex Architecture × Mechanical, Duplex Architecture × Plumbing,
   SampleCastle).
   - Chaque écart doit être rangé dans une cause mesurée et vérifiée : seuil
     ± marge de flèche, maillage ouvert, élément absent du `.ifcview`, OBB non
     unique, défaut connu de la règle d'origine, etc.
   - **Objectif : 0 écart inexpliqué**, comme pour les trois premières règles.
3. **Test « les préfiltres ne font qu'éliminer »** : la règle avec et sans
   préfiltre donne le même résultat.
4. **Chronométrage** avec le comparateur, à froid et à chaud.
5. **Non-régression** : les groupes de tests C++ concernés et
   `tests/test_parity_cpp.py`, **lancés groupe par groupe, jamais tous en
   une fois**.

Les défauts connus des règles d'origine (grille de rayons d'Above, droite
infinie, plantage `gp_Dir` sur élément dégénéré, etc.) ne sont **pas
reproduits** dans les versions `_triang`. Ils sont listés comme causes
d'écart.

---

## 7. Décisions à prendre avant de démarrer

| Question | Proposition |
|---|---|
| Nom des nouvelles règles | suffixe `_triang`, à côté des règles d'origine |
| Source des triangles | les deux (`.ifcview` et IFC), une seule implémentation |
| Exposition | moteur C++ seul (comme aujourd'hui), puis registre Python et interface une fois toutes les vagues validées |
| Changements de résultat volontaires (TopOrBottomSurface, LateralSurface, défauts d'Above) | acceptés et documentés, pas reproduits |
| Validation | comparaison à tolérance avec écarts expliqués, comme pour les trois premières règles |
| Ordre | vagues 0 → 5 ci-dessus |

---

## 8. Risques et parades

| Risque | Parade |
|---|---|
| Maillages ouverts ou mal orientés | soudure, réorientation, winding number ; aucun test sur les normales stockées |
| Flèche de maillage au bord des seuils | marge de comparaison explicite ; tolérances de contact exposées en paramètres (comme `plan_tolerance`) |
| Faces « B-Rep » sans équivalent direct | regroupement en faces planes, validé sur les cas de test des règles de faces |
| OBB non unique (sections carrées ou rondes) | OBB debout pour les règles directionnelles ; écart rangé dans une cause à part |
| `.ifcview` absent ou périmé | source IFC en repli ; `ConfigError` explicite si `.ifcview` est demandé et rejeté |
| Coût mémoire des données dérivées | calcul à la demande, uniquement pour les règles qui les lisent |
| Résultats qui dérivent entre vagues | les règles déjà portées restent dans le comparateur à chaque vague |
