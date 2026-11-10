# Rapport : portage des règles sur triangulations

Ce rapport clôt la partie C++ du déploiement décrit dans
`PLAN_PortageTriangulation.md`. **26 des 28 règles** du registre ont une
version `_triang`, qui ne lit que des triangles : ceux du `.ifcview`, ou la
triangulation IFC (`triangle_source` = `ifcview`, `auto` ou `ifc`).
ClearanceForDoors et Intersection2 ne sont pas portées (décision du
2026-11-10). Elles restent disponibles dans leur version d'origine.

Chaque règle a été testée, puis comparée seule à sa règle d'origine sur trois
maquettes et deux sources de triangles. **Toutes les différences ont une
cause vérifiée : 0 écart inexpliqué.**

L'exposition au registre Python et à l'interface (« C++ puis Python ») reste
à faire. Rien n'est commité.

## 1. Ce qui a été livré

| Vague | Règles `_triang` | Méthode |
|---|---|---|
| — | Intersection | arbre de clash IfcOpenShell alimenté par les triangles |
| 1 | Above, Below | triangles vus (échantillonnage < 200 triangles, carte de hauteur au-delà), écart vertical exact sur le recouvrement en plan |
| 1 | OBB_Above, OBB_Below, OBB_Front_And_Back, OBB_Custom | zones de l'original sur l'OBB des triangles, triangle contre zone par axes séparateurs |
| 1 | ObbHigh, ObbLength, Orientation, AngleBetween, Alignement | OBB optimale des sommets |
| 2 | Clearance, Collision | arbre de clash, une requête par exécution, narrow sur toute l'exécution |
| 2 | Volume, Area, LateralSurface, ProjectedSurface | `TriMesh` (soudure, enroulement réparé et orienté vers l'extérieur) |
| 2 | TopOrBottomSurface | sélection de faces de l'original (`extreme_faces`) sur les normales réparées |
| 3 | ClearanceAxisToAxis, SurfaceRecover | logique de l'original, distance peau à peau triangle à triangle (BVH, branch and bound) |
| 3 | Ray_Check, DirectView | segments contre un BVH de tous les triangles du contexte |
| 4 | OneObjectFace, TwoObjectsFace | logique de faces de l'original sur les triangles réparés |
| 4 | FreeSpace | emprises : triangles découpés à la bande de hauteur + sections aux limites |

Le code est dans `engine/triang/`, organisé en couches : `mesh/`,
`kernels/`, `spatial/`, `surface/`, `derived/` et `rules/`. Le détail est
dans `engine/triang/README.md`.

**Réutilisation de la logique d'origine.** Six classes d'origine sont passées
dans un en-tête, avec la lecture de la géométrie en méthode virtuelle. Ainsi,
la version `_triang` ne change que la géométrie :

- `Alignement::element_obb` ;
- `ClearanceAxisToAxis::skin_distance` ;
- `SurfaceRecover::skin_distance` ;
- `DirectView::blocked` ;
- `OneObjectFace::face_mesh` et `TwoObjectsFace::face_mesh`.

La parité de ces originaux avec le moteur Python reste vérifiée par
`tests/test_parity_cpp.py`, lancé par petits groupes. Tous les groupes
passent : Alignement et OBB_Custom (4), Above et Below (12), Intersection et
Clearance (15), ClearanceAxisToAxis et SurfaceRecover (9), OneObjectFace et
TwoObjectsFace (4), DirectView (1).

**Moteur.**

- `Variant::Triangles` et `TriangleSource` ; `Session::triangles(file, id)`.
- Les statistiques `triangles_from_view` et `triangles_from_ifc`.
- `PairRuleBase::parallel_narrow()`, et `narrow_whole_run()` pour les règles
  d'arbre.
- Avec `triangle_source="ifcview"`, aucune géométrie IFC n'est convertie.

**Côté Python, pour les tests.** `IFCCLASH_TRIANG=1` fait tourner chaque règle
sous sa jumelle `_triang` (`cpp_backend.engine_rule_type`). La source des
triangles se choisit avec `IFCCLASH_TRIANGLE_SOURCE`.

## 2. Méthode de validation

### Le comparateur

`engine/triang/compare_triang.py` lance chaque règle d'origine et sa version
`_triang` sur la même sélection. Chaque écart est rangé dans une **cause
mesurée** ; sans cause vérifiée, il est « inexpliqué » et le script sort en
erreur.

**Conditions d'exécution.**

- Une règle par processus, l'une après l'autre.
- 2 à 8 threads et `nice`, sous un plafond mémoire de 4 Go
  (`systemd-run -p MemoryMax=4G`).
- Les résultats des règles d'origine sont gardés sur disque
  (`build/engine/triang_original_cache`) : ces règles ne changent pas, elles
  ne sont plus relancées. Leur temps est celui de la première exécution
  froide, faite selon les passes avec 2, 4 ou 8 threads. **Les gains sont donc
  des ordres de grandeur.**

### Les causes

Le détail des causes est dans `engine/triang/README.md`. En voici la liste :

- élément absent du `.ifcview` ;
- au bord du seuil ;
- maillage IFC ouvert, enroulé vers l'intérieur ou incohérent ;
- géométries au contact ;
- OBB non unique, axe ambigu, sens d'axe opposé ;
- propre au maillage `.ifcview` : la même règle sur les triangles IFC donne
  le verdict ou la valeur de l'original ;
- ensemble d'entrée différent ;
- échantillonnage (DirectView, visibilité dense sur 200 rayons) ;
- géométrie sans épaisseur (triangles IFC par paires confondues) ;
- contact marginal ;
- défauts de l'original vérifiés sur les B-Rep IFC.

## 3. Résultats

| Données | 25 règles | Rapport |
|---|---|---|
| Duplex Architecture × Mechanical (286 × 524), `.ifcview` | 0 écart inexpliqué | `engine/triang/comparaison_duplex.md` |
| Duplex Architecture × Plumbing (286 × 499), `.ifcview` | 0 | `engine/triang/comparaison_duplex_plomberie.md` |
| SampleCastle (300 éléments), `.ifcview` | 0 ; 14 règles d'origine échouent | `engine/triang/comparaison_castle.md` |
| Duplex Architecture × Mechanical, triangles IFC | 0 | `engine/triang/comparaison_duplex_ifc.md` |
| DirectView (25 × 25 paires, contexte de 120 éléments) | 0 | `engine/triang/comparaison_directview.md` |

### Duplex Architecture × Mechanical, `.ifcview`

| Règle `_triang` | Origine | _triang | Communs | Origine froid | _triang froid | _triang chaud | Gain froid |
|---|---|---|---|---|---|---|---|
| Intersection | 802 | 770 | 730 | 1,8 s | 0,60 s | 0,33 s | ×2,9 |
| Above | 1 359 | 1 421 | 1 296 | 46,7 s | 0,41 s | 0,06 s | ×115 |
| Below | 967 | 1 034 | 886 | 36,2 s | 0,44 s | 0,05 s | ×83 |
| OBB_Above | 2 259 | 2 108 | 2 078 | 8,6 s | 0,44 s | 0,05 s | ×20 |
| OBB_Below | 1 560 | 1 411 | 1 393 | 8,0 s | 0,40 s | 0,03 s | ×20 |
| OBB_Front_And_Back | 1 683 | 1 595 | 1 537 | 8,9 s | 0,43 s | 0,04 s | ×21 |
| OBB_Custom | 3 369 | 3 159 | 3 157 | 11,7 s | 0,50 s | 0,09 s | ×24 |
| AngleBetween | 64 784 | 53 187 | 51 803 | 6,1 s | 1,51 s | 0,83 s | ×4,0 |
| ObbHigh | 810 | 760 | 760 | 5,2 s | 0,22 s | 0,01 s | ×23 |
| ObbLength | 810 | 760 | 760 | 5,0 s | 0,22 s | 0,01 s | ×23 |
| Orientation | 810 | 760 | 760 | 5,0 s | 0,32 s | 0,01 s | ×15 |
| Alignement | 158 | 150 | 136 | 14,8 s | 0,66 s | 0,28 s | ×22 |
| Clearance | 6 244 | 5 868 | 5 868 | 2,0 s | 0,82 s | 0,51 s | ×2,4 |
| Collision | 491 | 479 | 452 | 1,4 s | 0,27 s | 0,02 s | ×4,9 |
| Volume | 810 | 760 | 760 | 1,3 s | 0,28 s | 0,00 s | ×4,4 |
| Area | 810 | 760 | 760 | 1,3 s | 0,29 s | 0,00 s | ×4,5 |
| TopOrBottomSurface | 704 | 759 | 654 | 6,1 s | 2,68 s | 1,88 s | ×2,3 |
| LateralSurface | 792 | 760 | 742 | 3,5 s | 0,28 s | 0,01 s | ×13 |
| ProjectedSurface | 706 | 760 | 656 | 3,7 s | 0,66 s | 0,38 s | ×5,6 |
| ClearanceAxisToAxis | 157 | 149 | 149 | 75,9 s | 0,39 s | 0,14 s | ×194 |
| SurfaceRecover | 58 | 181 | 57 | 37,4 s | 0,44 s | 0,09 s | ×84 |
| Ray_Check | 539 | 540 | 513 | 37,8 s | 1,03 s | 0,26 s | ×37 |
| OneObjectFace | 473 | 528 | 456 | 44,4 s | 49,6 s | 47,6 s | ×0,9 |
| TwoObjectsFace | 1 868 | 1 734 | 1 649 | 83,2 s | 69,5 s | 67,2 s | ×1,2 |
| FreeSpace | 810 | 760 | 760 | 9,8 s | 0,81 s | 0,03 s | ×12 |

Les « manquants » sont surtout les 50 éléments absents du `.ifcview`
(ouvertures, quelques espaces). Les « en plus » de SurfaceRecover sont des
contacts au bord de la tolérance de 1 cm.

**DirectView.** L'original prend 412 s, la version `_triang` 0,22 s, soit
**×1 900**. Résultats : 31 paires pour l'original, 28 pour `_triang`, 17
communes, 0 écart inexpliqué.

### Les autres jeux de données

- **Plomberie.** Gains à froid de ×44 à ×104 pour Above, Below,
  ClearanceAxisToAxis et SurfaceRecover, et de ×14 à ×35 pour les règles OBB,
  Alignement et Ray_Check. OneObjectFace et TwoObjectsFace sont comparées sur
  100 éléments par côté (section 5).
- **SampleCastle.** 14 règles d'origine échouent sur un élément dégénéré
  (défaut 5) ; leurs versions `_triang` aboutissent toutes en moins d'une
  seconde. Les 11 règles comparables sont à 0 écart inexpliqué.
- **Triangles IFC.** Les résultats sont presque identiques à l'original :
  ObbHigh 810 sur 810, OBB_Custom 3 369 sur 3 369, Clearance 6 244 sur 6 244.
  La triangulation IFC devient alors le coût principal à froid : gains de
  ×0,3 à ×8, ×58 pour ClearanceAxisToAxis.

### Modèles de test (`IFC_Test_Model/`)

Les quatre suites `tests/test_Rule_IFC_Test_Model*.py` ont une copie figée
dans `tests/triang_port/`, qui fait tourner chaque règle sous sa forme
`_triang`. Chaque fichier se lance seul.

| Suite | Résultat |
|---|---|
| `test_triang_Rule_IFC_Test_Model` | tout passe ; 3 attentes adaptées et documentées : défaut 4 de l'original (Suzanne au-dessus de Suzanne), cube à l'axe Wide ambigu, sens d'axe 0° / 180° |
| `_New` | tout passe (26) ; la poutre au-dessus du cube est maintenant trouvée (défaut de l'original) ; la sphère qui traverse la dalle est « au-dessus » par le bord de sa sortie (sémantique gardée, voir section 6) |
| `_Complete` | 19 passent, 1 échec attendu (Alignement : les 45Cuboid sont inclinés à exactement 45°, le seuil horizontal / vertical) |
| `_OneObject` | 14 sur 18 ; les 4 échecs `test_suzanne` sont ceux des moteurs Python et C++ dans cet environnement (`Rapport_PortageCPP.md` §8.1) |

## 4. Défauts trouvés

### Dans les règles d'origine

Ces défauts sont reproduits par le portage C++, comme la parité l'exige, et
corrigés dans les versions `_triang`.

1. **Above ne voit pas les objets fins.** Sa grille de 50 × 50 rayons couvre
   la plus grande dimension de l'objet. Effet : 47 paires manquées sur Duplex
   pour Above, 131 pour Below.
2. **Above ne teste que les points les plus proches** des deux faces.
3. **Le test « ray » d'Above coupe une droite infinie** : il garde une cible
   située sous la source.
4. **Le test « ray » garde la distance des points les plus proches**, pas
   l'écart vertical au point du rayon. Exemples :
   - une cloison et un tuyau : 0,90 m rapporté pour 2,46 m réels ;
   - Suzanne au-dessus de Suzanne : 0,2125 m rapporté pour 0,3255 m.
5. **Échec sur un élément dégénéré** (SampleCastle) : `gp_Dir() - input
   vector has zero norm`, `Bnd_Box is void`. 14 règles sont touchées.
6. **Fausse alerte latente des règles d'arbre** (Intersection, Clearance,
   Collision). Le narrow traite les candidats par lots de 4 096 paires, et
   lève un `prefilter_lost_clash` injustifié pour une paire d'un autre lot.
7. **Les surfaces et les faces lisent les normales de la triangulation
   brute**, souvent enroulée vers l'intérieur ou de façon incohérente.
8. **Volume signé sur maillage ouvert ou sans épaisseur.** Le résultat
   dépend de l'origine du repère. Exemple : des coudes faits de triangles
   doublés.

### Dans le portage C++ d'origine

- **`IfcSource::material_names`** levait une exception sur une
  `IfcMaterialList`, là où Python (`getattr(material, "Name", None)`) rend une
  liste vide. OneObjectFace et TwoObjectsFace échouaient donc sur la plomberie
  et sur SampleCastle, dans leur version d'origine comme dans leur version
  `_triang`. C'est corrigé, et la parité est revérifiée.

### Dans les versions `_triang`, trouvés et corrigés par la comparaison

- **Triangle vu en partie (Above)** : un triangle peut n'être vu que sur une
  partie de sa surface. Corrigé par `gap_candidates` et `point_covered`.
- **Enroulement mal réparé** sur des composants ouverts, et propagation
  arrêtée par les arêtes non manifold (placards).
- **Deux pièces soudées le long d'une arête.** Exemple : deux murs de
  SampleCastle, de 0,0427 et 0,3377 m³, qui tombaient à 0,0220 et 0,2524 m³.
  À une arête utilisée 4 fois, l'appariement angulaire pouvait relier les
  faces à travers le coin vide, et retourner une des deux pièces. Le
  `TriMesh` corrigé procède ainsi :
  - il apparie d'abord par la topologie source, c'est-à-dire les indices
    avant soudure ;
  - à défaut, il choisit les coins pleins par la parité d'un rayon ;
  - il départage deux faces coplanaires par leur normale.

  Deux tests `[triang]` couvrent ce cas.
- **TopOrBottomSurface** : l'échantillonnage, puis la carte de hauteur, ne
  retenaient pas les mêmes faces que l'original (flancs raides, triangles en
  partie couverts). La règle reprend maintenant le choix de faces de
  l'original sur les normales réparées.

## 5. Limites

- **Fidélité au `.ifcview`.** Les résultats valent ce que vaut son maillage :
  ouvertures non découpées (évier), fenêtres non fermées une fois réparées,
  éléments absents. Avec `auto`, ces derniers sont complétés par la
  triangulation IFC.
- **Mémoire.** OneObjectFace et TwoObjectsFace dépassent 4 Go sur toute la
  maquette de plomberie, en version d'origine comme en version `_triang`
  (même logique de faces).
- **Gains faibles** pour TopOrBottomSurface (×1,3 à ×2,3) et pour les règles
  de faces (×1) : elles gardent le coût de la logique d'origine.
- **DirectView** garde l'échantillonnage de 10 rayons de l'original : une
  paire proche du seuil reste instable, d'un côté comme de l'autre.

## 6. Suite

**Décision du 2026-11-10 : sémantique d'Above et de Below gardée.** Une
paire est signalée dès qu'il existe un point où la cible est au-dessus de la
source, ou au-dessous pour Below, dans la tolérance. Une cible qui traverse
la source peut donc être signalée par le bord de sa sortie.

1. **Registre Python et interface, à la fin du projet** : déclarer les 26
   règles `_triang` et leurs paramètres propres (`plan_tolerance`,
   `contact_tolerance`), puis exposer `triangle_source`.
2. **Optionnel : Clearance, Collision et Intersection** : remplacer l'arbre
   IfcOpenShell par le noyau `mesh_distance`, avec un seuil d'arrêt, et
   paralléliser le narrow sur les seuls candidats.
3. **Optionnel : les règles de faces** : sélectionner les faces sur le
   `TriMesh`, indexé par BVH, pour réduire leur coût et leur mémoire.
