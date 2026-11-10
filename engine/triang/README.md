# Règles `_triang` : les règles du moteur calculées sur des triangles

Les règles `_triang` reprennent les règles du registre en ne lisant que des
**triangles** (`Variant::Triangles`), jamais de B-Rep. Le plan de
déploiement est dans `PLAN_PortageTriangulation.md` (racine du dépôt).

**Source des triangles** (`SessionOptions::triangle_source`, paramètre
`triangle_source` de `Session` en Python) :

| Valeur | Triangles | Élément absent du `.ifcview` |
|---|---|---|
| `auto` (défaut) | ceux du `.ifcview` quand il contient l'élément, sinon la triangulation IFC | triangulation IFC |
| `ifcview` | ceux du `.ifcview` seulement ; pas de `.ifcview` accepté : `ConfigError` | ignoré, diagnostic `not_in_ifcview` |
| `ifc` | la triangulation IFC (coordonnées monde) seulement | — |

Avec `ifcview`, aucune géométrie IFC n'est convertie : l'IFC n'est ouvert que
pour résoudre les sélections, et le test C++ vérifie
`Session::ifc_conversions() == 0`. Les statistiques de chaque exécution
comptent les éléments servis par chaque source (`triangles_from_view`,
`triangles_from_ifc`).

Moteur C++ seulement pour l'instant (API `Session`, bindings
`_ifcclash_engine`). Côté Python, `IFCCLASH_TRIANG=1` fait tourner chaque
règle sous sa jumelle `_triang` (`cpp_backend.engine_rule_type`), pour les
tests `tests/triang_port/`.

## Règles disponibles

26 des 28 règles du registre ont leur version `_triang` (vagues du plan) ;
ClearanceForDoors et Intersection2 ne sont pas portées (décision du
2026-11-10) :

| Vague | Règle `_triang` | Méthode sur triangles |
|---|---|---|
| — | Intersection | arbre de clash IfcOpenShell, alimenté par les triangles |
| 1 | Above, Below | triangles vus de chaque côté, écart vertical exact sur leur recouvrement en plan, point vu des deux côtés |
| 1 | OBB_Above, OBB_Below, OBB_Front_And_Back, OBB_Custom | zones de l'original sur l'OBB des triangles ; triangle contre zone par axes séparateurs |
| 1 | ObbHigh, ObbLength, Orientation, AngleBetween | OBB optimale des sommets |
| 1 | Alignement | regroupement de l'original (`rules/Alignement.h`) sur l'OBB des sommets |
| 2 | Clearance, Collision | arbre de clash IfcOpenShell, une seule requête par exécution |
| 2 | Volume, Area | `TriMesh` (enroulement réparé) |
| 2 | TopOrBottomSurface | faces de l'original (`extreme_faces` : tournées vers le haut / le bas, non couvertes par une face plus haute) sur les normales réparées |
| 2 | LateralSurface, ProjectedSurface | normales réparées vers l'extérieur ; union des projections de tous les triangles |
| 3 | ClearanceAxisToAxis, SurfaceRecover | logique de l'original (`rules/AxisRules.h`, `rules/SurfaceRecover.h`), distance peau à peau triangle à triangle par BVH |
| 3 | Ray_Check, DirectView | rayons contre un BVH de tous les triangles du contexte (`TriangleSoup`) ; DirectView reprend l'original (`rules/ContextRules.h`) |
| 4 | OneObjectFace, TwoObjectsFace | logique de l'original (`rules/FaceRules.h`) sur les triangles réparés |
| 4 | FreeSpace | emprises des obstacles : triangles découpés à la bande de hauteur + sections aux limites de la bande |

Mêmes paramètres et mêmes blocs de résultat que la règle d'origine. Les
règles de contact ajoutent une tolérance (voir plus bas).

## Organisation du code

```
engine/triang/
  mesh/      ViewTriangles   décodage des triangles du .ifcview
             TriMesh         maillage soudé, enroulement réparé (arêtes non
                             manifold appariées par la topologie source, sinon
                             par angle avec test de matière), test « fermé »,
                             volume, données par triangle, BVH à la demande
             Obb             OBB optimale des sommets
  kernels/   TriangleTests   triangle / OBB (axes séparateurs), recouvrement en plan
             Distance        point / triangle, segment / segment, segment /
                             triangle (Möller-Trumbore avec marge), triangle / triangle
             Slices          triangle découpé à une bande de hauteur, sections
  spatial/   BoxTree         BVH de boîtes (OCCT BVH_BoxSet), requêtes boîte et segment
             Proximity       distance maillage / maillage (branch and bound),
                             TriangleSoup (BVH d'un contexte, segment bloqué)
  surface/   Visibility      triangles vus (échantillonnage, auto), point couvert
             HeightMap       carte de hauteur rasterisée
  derived/   ElementData     données par élément gardées en session (tri_mesh,
                             tri_obb, seen_triangles), étiquettes « tri_* »
  rules/     Common.h        bases TriElementRule / TriPairRule
             TriangRules     enregistrement de toutes les règles _triang
             TreeTriang      Intersection, Clearance, Collision
             DirectionalTriang  Above, Below, OBB_Above, OBB_Below,
                             OBB_Front_And_Back, OBB_Custom
             ObbTriang       ObbHigh, ObbLength, Orientation, AngleBetween, Alignement
             SurfaceTriang   Volume, Area, TopOrBottomSurface, LateralSurface,
                             ProjectedSurface
             SkinTriang      ClearanceAxisToAxis, SurfaceRecover
             ContextTriang   Ray_Check, DirectView, FreeSpace
             FaceTriang      OneObjectFace, TwoObjectsFace
  tests/     test_triang.cpp Catch2 [triang]
  compare_triang.py          comparaison avec les règles d'origine
```

Accroches dans le moteur, réduites au minimum :

- `Variant::Triangles` (`core/Geometry.h`) et `TriangleSource`
  (`provider/CachePolicy.h`) ;
- `GeometryProvider` : triangles par élément selon la source, cache de
  session, second arbre de clash (`view_clash`) ;
- `triangle_inputs` dans les pipelines : boîtes du `.ifcview`, ou calculées
  sur les triangles IFC ;
- `PairRuleBase::parallel_narrow()` : la phase fine des paires répartie sur
  les threads de la session, pour les règles qui ne lisent que leurs données
  (les règles `_triang` de paires). Les résultats ne dépendent pas du nombre
  de threads (test `[triang]`) ;
- les classes d'origine déplacées dans un en-tête, la géométrie en méthode
  virtuelle, pour que la version `_triang` ne change que la géométrie :
  `rules/Alignement.h` (`element_obb`), `rules/AxisRules.h` et
  `rules/SurfaceRecover.h` (`skin_distance`), `rules/ContextRules.h`
  (`DirectView::blocked`), `rules/FaceRules.h` (`face_mesh`).

## Principes

- **Une géométrie par élément et par session.** `tri_mesh`, `tri_obb`,
  `seen_triangles` sont calculés une fois et partagés par toutes les règles
  et toutes les exécutions de la session.
- **Pas de confiance dans l'enroulement.** Beaucoup de maillages IFC sont
  orientés vers l'intérieur et les normales stockées du `.ifcview` ne sont
  pas fiables : `TriMesh` soude les sommets, rend l'enroulement cohérent par
  propagation sur les arêtes, puis l'oriente vers l'extérieur ; les tests de
  visibilité sont des tests de recouvrement.
- **BVH partout** où l'on cherche des voisins (triangles d'un élément,
  triangles vus de la cible).

## Ce que fait chaque règle

**Intersection_triang.** C'est l'arbre de clash d'IfcOpenShell, le même
algorithme qu'Intersection (protrusion, sinon perçage, au-delà de
`tolerance`), alimenté par les triangles dans un arbre propre.

**Above_triang, Below_triang.** La cible est au-dessus (au-dessous) de la
source quand il existe, en plan, une zone commune à :
- un triangle de la source vu de son côté (du dessus pour `Max`, du dessous
  pour `Min`) ;
- un triangle de la cible vu de son côté ;
- où l'écart vertical (cible − source pour Above, source − cible pour Below)
  est dans `[0, tolerance]`.

L'écart est linéaire sur le recouvrement de deux triangles : la région où il
est dans l'intervalle est un polygone convexe, calculé exactement. Un
triangle peut n'être vu qu'en partie : le point retenu doit être vu des deux
côtés (`point_covered`), en commençant par le plus petit écart. Les
triangles vus viennent de `visible_triangles_auto` (échantillonnage sous
200 triangles, carte de hauteur au-delà). Le préfiltre d'Above est repris :
la bande extrudée au-dessus (au-dessous) de l'OBB de la source doit toucher
l'OBB de la cible.

**OBB_*_triang.** Un triangle de la cible touche une zone de détection de la
source (axes séparateurs, 13 axes, exact) : un verdict par zone touchée. Les
zones sont exactement celles des règles d'origine, construites sur l'OBB des
triangles.

**ObbHigh, ObbLength, Orientation, AngleBetween, Alignement (_triang).** Les
calculs des règles d'origine, sur l'OBB optimale des sommets
(`Bnd_OBB::ReBuild` optimal, comme `BRepBndLib::AddOBB` sur le maillage à
0,01 m de l'original). Le centre est celui de la boîte des triangles.

**Paramètres ajoutés.** Les triangles sont une tessellation (le `.ifcview`
est aussi quantifié à environ 0,1 mm) : un contact ne peut pas être un 0
exact.

| Règle | Paramètre | Défaut | Rôle |
|---|---|---|---|
| `Above_triang`, `Below_triang` | `plan_tolerance` | 1 mm | Deux faces distantes en plan de moins de cette valeur comptent comme superposées. |
| `OBB_*_triang` | `contact_tolerance` | 1 mm | Un triangle à moins de cette distance d'une zone la touche. |

Ces tolérances s'appliquent aussi aux préfiltres. Une valeur négative impose
au contraire une pénétration de cette profondeur : le comparateur s'en sert
pour vérifier la robustesse.

## Vitesse et validation

`compare_triang.py` compare chaque règle à son origine sur la même
sélection et range chaque écart dans une **cause mesurée** ; un écart n'est
« expliqué » que si la cause est vérifiée, sinon le script sort en erreur.
Les règles sont lancées une par processus (`--rules`), l'une après l'autre ;
les résultats des règles d'origine, qui ne changent pas, sont gardés sur
disque (`build/engine/triang_original_cache`, `--no-original-cache` pour les
relancer).

**25 règles sur 4 jeux de données, 0 écart inexpliqué** (DirectView à part,
0 aussi) :

| Données | Rapport | Gains à froid typiques |
|---|---|---|
| Duplex Architecture × Mechanical, `.ifcview` | [comparaison_duplex.md](comparaison_duplex.md) | ×80–×195 (Above, Below, ClearanceAxisToAxis, SurfaceRecover), ×20–×37 (OBB, Alignement, Ray_Check), ×4–×13 (surfaces), ×1 (faces) |
| Duplex Architecture × Plumbing, `.ifcview` | [comparaison_duplex_plomberie.md](comparaison_duplex_plomberie.md) | ×44–×104 (Above, Below, ClearanceAxisToAxis, SurfaceRecover), ×14–×35 (OBB, Alignement, Ray_Check) |
| SampleCastle, 300 éléments, `.ifcview` | [comparaison_castle.md](comparaison_castle.md) | 14 règles d'origine échouent (`gp_Dir` de norme nulle, `Bnd_Box` vide) ; les `_triang` aboutissent en moins d'une seconde |
| Duplex Architecture × Mechanical, triangles IFC | [comparaison_duplex_ifc.md](comparaison_duplex_ifc.md) | résultats quasi identiques à l'origine (ObbHigh 810 / 810, OBB_Custom 3 369 / 3 369) ; à froid la triangulation IFC domine (×0,3–×8 ; ×58 pour ClearanceAxisToAxis) |
| DirectView, 25 × 25 paires, contexte 120 éléments | [comparaison_directview.md](comparaison_directview.md) | ×1 900 |

Les gains de TopOrBottomSurface (×1,3–×2,3) et des règles de faces (×1)
sont faibles : ces versions reprennent la logique de l'original (sélection
de faces en O(n²)) sur les triangles réparés ; seule la conversion IFC est
économisée.

**Causes des écarts vérifiées.**

- **Élément absent du `.ifcview`** (surtout des `IfcOpeningElement`) : ignoré,
  avec un diagnostic.
- **Au bord du seuil** : le verdict change quand le seuil bouge de la marge
  (11 mm = flèche du `.ifcview` + flèche IFC ; un rayon pour DirectView).
- **Maillage IFC ouvert, enroulé vers l'intérieur ou incohérent** : les
  originaux lisent la parité ou les normales de la triangulation brute
  (Intersection, surfaces, faces, DirectView).
- **Géométries IFC au contact** (Intersection, Collision) : test de
  pénétration instable sur faces confondues.
- **OBB optimale non unique** (mêmes dimensions, axes tournés), **axe
  principal ambigu** (deux dimensions égales à la marge près), **même axe,
  sens opposé** : règles OBB, AngleBetween, Orientation, Alignement et
  ClearanceAxisToAxis (une évacuation de toiture compacte : l'axe suit un
  autre côté de la boîte, distance 0,149 contre 0,238 m).
- **Propre au maillage `.ifcview`** : la même règle `_triang` sur les
  triangles IFC de l'élément ou de la paire redonne la valeur ou le verdict
  de l'original.
- **Ensemble d'entrée différent, groupe recomposé** : l'original relancé sans
  les éléments absents du `.ifcview` (ou sans ceux à l'axe ambigu) donne le
  même verdict.
- **Échantillonnage** (DirectView) : visibilité mesurée sur 200 rayons par
  l'original et par `_triang`, d'accord à 10 points près ; seuls les 10
  rayons tirés diffèrent.
- **Géométrie sans épaisseur** (Volume) : les triangles IFC vont par paires
  confondues (coudes, raccords) ; le maillage réparé n'enclôt rien, l'original
  garde le volume signé de la surface doublée, qui dépend de l'origine.
- **Contact marginal** (SurfaceRecover) : bande de contact de largeur
  équivalente sous la marge.
- **Défauts de l'original vérifiés indépendamment** (liste ci-dessous) :
  verticale à travers les B-Rep IFC (Above, Below).

**Défauts des règles d'origine révélés par la comparaison** (reproduits par
le portage C++, parité oblige, corrigés dans les versions `_triang`) :

1. **Above ne voit pas les objets fins** : sa grille de 50 × 50 rayons
   couvre la plus grande dimension de l'objet ; une section de 3 cm passe
   entre deux rayons.
2. **Above ne teste que les points les plus proches** des deux faces, puis
   un rayon depuis ce point.
3. **Le test « ray » d'Above coupe une droite infinie** (pas de `W ≥ 0`) :
   il garde une cible située sous la source.
4. **Le test « ray » garde la distance des points les plus proches** (Above,
   Below), pas l'écart vertical au point du rayon. Exemples : une cloison et
   un tuyau, 0,90 m rapporté pour 2,46 m réels ; Suzanne au-dessus de
   Suzanne (modèle de test), 0,2125 m rapporté pour 0,3255 m au point du
   rayon.
5. **Règles OBB d'origine en échec sur un élément dégénéré** (SampleCastle :
   `gp_Dir() - input vector has zero norm`, `Bnd_Box is void`).
6. **Fausse alerte latente des règles d'arbre** (Intersection, Clearance,
   Collision) : le narrow par lots de 4 096 paires lève un
   `prefilter_lost_clash` pour une paire d'un autre lot (`narrow_whole_run`
   dans les versions `_triang`).
7. **Les surfaces et les faces lisent les normales de la triangulation
   brute** : beaucoup de maillages IFC sont enroulés vers l'intérieur ou de
   façon incohérente (première cause d'écart des vagues 2 à 4).
8. **Volume signé sur maillage ouvert ou sans épaisseur** : la valeur dépend
   de l'origine du repère.

**Défaut du portage C++ trouvé** : `IfcSource::material_names` levait une
exception sur une `IfcMaterialList` (pas d'attribut `Name`) là où Python
(`getattr(material, "Name", None)`) rend une liste vide ; OneObjectFace et
TwoObjectsFace échouaient sur la plomberie et SampleCastle. Corrigé, parité
revérifiée.

**Tests de non-régression sur les modèles de test** (`IFC_Test_Model/`) :
les quatre suites `tests/test_Rule_IFC_Test_Model*.py` sont copiées dans
`tests/triang_port/`, chaque règle remplacée par sa jumelle `_triang`
(`IFCCLASH_TRIANG=1`, triangles IFC). Les écarts avec les valeurs calibrées
sont documentés dans les copies : défaut 4 de l'original (Suzanne), axe
ambigu (cube), sens d'axe (0° / 180°), poutre au-dessus du cube trouvée,
45Cuboid à exactement 45° (Alignement, échec attendu), sphère qui traverse
une dalle (voir ci-dessous). Les 4 échecs `test_suzanne` de `_OneObject` sont
ceux du moteur Python et du moteur C++ dans cet environnement
(`Rapport_PortageCPP.md` §8.1).

**Sémantique d'Above_triang et Below_triang** (décision du 2026-11-10) : une
paire est signalée dès qu'il existe un point où la cible est au-dessus
(au-dessous) de la source, dans la tolérance. Une cible qui traverse la source
peut donc être signalée par le bord de sa sortie (`SphereA_NotAbove_SlabA` :
0,5 mm au-dessus de la dalle là où la sphère en ressort).

## Carte de hauteur

`HeightMap.{h,cpp}` détermine les triangles vus du dessus (ou du dessous)
avec un z-buffer en plan :
- chaque maille garde le z le plus haut (ou le plus bas) des triangles non
  verticaux qui contiennent son centre, et le triangle qui le donne ;
- un triangle est vu s'il gagne une maille, ou s'il est à égalité (à
  1e-6 près) avec le gagnant sur l'une de ses mailles ;
- un triangle plus petit qu'une maille est testé à son barycentre contre les
  gagnants des 3 × 3 mailles voisines.

Remplissage ligne par ligne (balayage), sans test triangle à triangle :
coût = triangles + mailles couvertes. L'orientation des triangles n'est
pas utilisée. Grille : maille de 1 cm, entre 64 et 1 024 mailles sur le
plus grand côté de l'objet (les petits raccords sont affinés, les grandes
dalles grossies).

Comparaison sur les 810 éléments du Duplex Architecture + Mechanical, côté
dessus (`scripts/benchmark_extreme_faces.py`,
[rapport](../../doc/benchmark_extreme_faces.md)) :

| Méthode | Total | Gain de la carte |
|---|---|---|
| Rayons sur B-Rep, Python (`get_faces_visible_from_direction_with_plane`, méthode d'Above) | 487 s | ×2 593 |
| Même méthode, portage C++ (`geometry::visible_faces`) | 136 s | ×725 |
| Recouvrement shapely, Python (`get_extreme_faces`) | 18,0 s | ×96 |
| Même méthode, portage C++ GEOS (`geometry::extreme_faces`) | 6,8 s | ×36 |
| Échantillonnage 4 points + BVH (`visible_triangles`, Above_triang) | 0,20 s | ×1,07 |
| **Carte de hauteur** (`visible_triangles_raster`) | **0,19 s** | — |
| **Hybride** (`visible_triangles_auto` : échantillonnage sous 200 triangles, carte au-delà) | **0,06 s** | ×0,31 |

- **Face aux fonctions existantes**, le gain vient surtout du passage aux
  triangles : plus de rayons sur B-Rep, plus de shapely.
- **Face à `visible_triangles`**, la carte n'est pas plus rapide au total.
  Elle gagne sur les maillages riches (×2,6 de 100 à 999 triangles, ×6 au-delà
  de 1 000) et perd sur les maillages pauvres (×9 plus lente sous 100
  triangles), où le coût des mailles domine.
- **Qualité**, mesurée contre une carte fine à 2 mm (surface en plan des
  triangles manqués ou en trop) :
  - carte à 1 cm : 0,003 % manqué, 0,125 % en trop ;
  - `visible_triangles` : 0,016 % manqué, 0 % en trop ;
  - `get_extreme_faces` : 14,7 % manqué, 4,8 % en trop. Elle filtre d'abord
    sur la normale, faussée par les maillages tournés vers l'intérieur.
- **Le surplus de la carte** vient du test des petits triangles (barycentre
  contre les gagnants voisins), qui déclare vu un triangle quand aucun voisin
  ne le contient.

**Méthode hybride.** `visible_triangles_auto` choisit selon le nombre de
triangles : l'échantillonnage sous `kHeightMapFromTriangles` (200), la carte
au-delà. Mesures du second passage (même banc) :

- 62 ms au total, contre 209 ms pour l'échantillonnage seul et 203 ms pour la
  carte seule, soit ×3,3. Le meilleur choix élément par élément donnerait
  66 ms (recalculé à partir des deux mesures) : le seuil fixe en est à 10 %
  près ;
- le total varie peu entre 150 et 300 triangles (76 à 74 ms) ;
- qualité : 0,013 % de surface manquée et 0,025 % en trop, entre les deux
  méthodes.

`Above_triang` et `Below_triang` utilisent la méthode hybride pour leurs
triangles vus. L'atout propre de la carte reste à exploiter : elle donne directement la
surface haute (ou basse) d'un objet, ce qui permettrait de comparer deux
objets maille à maille pour Above sans chercher de faces.

## Lancer

```bash
cmake --build build/engine -j6
./build/engine/engine_tests "[triang]"
PYTHONNOUSERSITE=1 python scripts/benchmark_extreme_faces.py --side top
# une règle par processus, l'une après l'autre (mémoire : plafond conseillé de 4 Go)
PYTHONNOUSERSITE=1 python engine/triang/compare_triang.py --threads 4 --rules Above_triang --output above.md
PYTHONNOUSERSITE=1 python engine/triang/compare_triang.py --threads 4 --triangles ifc --rules Volume_triang \
    --output volume_ifc.md
# les modèles de test, un fichier à la fois
PYTHONNOUSERSITE=1 python -m pytest tests/triang_port/test_triang_Rule_IFC_Test_Model.py
```

Depuis Python :

```python
from engine import _ifcclash_engine as native
s = native.Session(ifc_paths=[ifc], geometry_cache="require", ifcview_paths=[ifcview],
                   triangle_source="auto")  # "ifcview", "ifc"
s.run(rule_type="Above_triang", params={"above_type": "Above_MaxToMin", "tolerance": 1.0}, selections=...)
```

## Limites

- **Fraîcheur.** Les résultats valent ce que vaut le `.ifcview`. Sans
  manifeste, il n'est accepté que s'il est plus récent que l'IFC.
- **Précision.** Elle est celle du maillage de BonsaiViewer, sans contrôle
  de la flèche utilisée.
- **Éléments non couverts.** Avec `triangle_source="ifcview"`, les éléments
  absents du `.ifcview` (ouvertures, et certains espaces selon l'export) ne
  sont pas testés ; `auto` les complète par la triangulation IFC.
- **Mémoire.** OneObjectFace et TwoObjectsFace (origine et `_triang`, même
  logique de faces) dépassent 4 Go sur toute la maquette de plomberie : la
  comparaison y est faite sur 100 éléments par côté.
- **Coût des règles reprises telles quelles.** TopOrBottomSurface (sélection
  de faces de l'original) et les règles de faces gardent le coût de leur
  logique d'origine.
- **DirectView** garde l'échantillonnage de l'original (10 rayons) : une
  paire proche du seuil reste instable, d'un côté comme de l'autre.
- **Non portées** : ClearanceForDoors et Intersection2.
