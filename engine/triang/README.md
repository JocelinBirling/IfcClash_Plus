# Règles `_triang` : les triangles du `.ifcview`, rien d'autre

Trois règles complémentaires, calculées **uniquement** sur les triangles du
`.ifcview` déjà produit par BonsaiViewer :

- `Intersection_triang` ;
- `Above_triang` ;
- `OBB_Above_triang`.

Aucune géométrie IFC n'est convertie. L'IFC n'est ouvert que pour résoudre
les sélections, et le test C++ vérifie `Session::ifc_conversions() == 0`. Le
but : être les règles les plus rapides, avec des résultats proches des règles
d'origine à l'approximation du `.ifcview` près.

Moteur C++ seulement (API `Session`, bindings `_ifcclash_engine`). Ces
règles ne sont pas dans le registre Python ni dans l'interface.

## Fichiers

| Fichier | Rôle |
|---|---|
| `ViewTriangles.{h,cpp}` | Décodage des triangles du `.ifcview` : lecture des seuls chunks utiles, en parallèle ; positions déquantifiées ; sommets soudés ; instances placées. Un maillage monde par élément. |
| `TriangleTests.{h,cpp}` | Tests géométriques : triangle / OBB (axes séparateurs), recouvrement en plan de deux triangles, BVH de boîtes, triangles vus du dessus ou du dessous, OBB optimale de sommets. |
| `HeightMap.{h,cpp}` | Carte de hauteur rasterisée (z-buffer en plan avec le triangle gagnant de chaque maille) et triangles vus du dessus ou du dessous qu'on en déduit. Pas encore utilisée par les règles : voir « Carte de hauteur » plus bas. |
| `TriangRules.cpp` | Les trois règles et leurs `RuleSpec`. |
| `tests/test_triang.cpp` | Tests Catch2 `[triang]`. |
| `compare_triang.py` | Comparaison avec les règles d'origine, à la marge du `.ifcview` près. |
| `comparaison_*.md` | Résultats de cette comparaison sur trois maquettes. |

Accroches dans le moteur existant, réduites au minimum :

- `Variant::ViewMesh` (`core/Geometry.h`) ;
- `GeometrySource::stored_meshes` et `triangulation_native` ;
- dans `GeometryProvider` : cache de session des maillages `.ifcview` et
  second arbre de clash (`view_clash`) ;
- `view_inputs` dans les pipelines : un élément absent du `.ifcview` est
  ignoré avec le diagnostic `not_in_ifcview`. Un `.ifcview` manquant ou
  rejeté lève `ConfigError` ;
- `PairRuleBase::narrow_whole_run`, et le compteur
  `Session::ifc_conversions()`.

## Ce que fait chaque règle

Mêmes paramètres et mêmes blocs de résultat que la règle d'origine. Deux
tolérances de contact sont ajoutées (voir plus bas).

**Intersection_triang.** C'est l'arbre de clash d'IfcOpenShell, le même
algorithme qu'Intersection, alimenté par les triangles du `.ifcview` :
- un élément IfcOpenShell (`triangulation_element`) est construit à partir
  des triangles du `.ifcview` et du produit IFC ;
- il est ajouté à un arbre propre, distinct de celui des triangles IFC ;
- le calcul est le même qu'Intersection : protrusion, sinon perçage, au-delà
  de `tolerance`.

**Above_triang.** La cible est au-dessus de la source quand il existe, en
plan, une zone commune à deux triangles :
- un triangle de la source vu de son côté (du dessus pour `Max`, du dessous
  pour `Min`) ;
- un triangle de la cible vu de son côté ;
- l'écart vertical cible − source sur cette zone atteint `[0, tolerance]`.

« Vu » se teste par recouvrement : centre ou point proche d'un coin non
couvert par un autre triangle de l'objet. L'orientation des triangles n'est
pas utilisée, car de nombreux maillages IFC (MEP Revit) sont orientés vers
l'intérieur. Le préfiltre d'Above est repris : la bande extrudée au-dessus de
l'OBB de la source doit toucher l'OBB de la cible.

**OBB_Above_triang.** Un triangle de la cible touche la bande extrudée de
`tolerance` au-dessus de l'OBB de la source. Le test est exact (axes
séparateurs, 13 axes).

**OBB.** Les OBB sont les boîtes optimales des sommets du `.ifcview`
(`Bnd_OBB::ReBuild` optimal), comme OBB_Above sur son maillage à 0,01 m.
Elles sont gardées en session.

**Paramètres ajoutés.** La géométrie du `.ifcview` est quantifiée à environ
0,1 mm. Deux tolérances de contact sont donc exposées :

| Règle | Paramètre | Défaut | Rôle |
|---|---|---|---|
| `Above_triang` | `plan_tolerance` | 1 mm | Deux faces distantes en plan de moins de cette valeur comptent comme superposées. Above aligne lui aussi ses points à 1 mm près. |
| `OBB_Above_triang` | `contact_tolerance` | 1 mm | Un triangle à moins de cette distance de la bande la touche. |

Ces tolérances sont aussi appliquées aux préfiltres. Une valeur négative
impose au contraire une pénétration de cette profondeur : le script de
comparaison s'en sert pour vérifier la robustesse.

## Vitesse et validation

`compare_triang.py` compare chaque règle à son origine sur la même
sélection :
- **froid** : ouverture de session et première exécution ;
- **chaud** : la même règle relancée dans la session.

Chaque écart est rangé dans une cause mesurée. Il n'est « expliqué » que si
la cause est vérifiée ; sinon il est listé comme inexpliqué.

Duplex Architecture × Mechanical, 286 × 524 éléments
([détail](comparaison_duplex.md)) :

| Règle | Origine | _triang | Communs | Origine froid / chaud | _triang froid / chaud | Gain froid / chaud | Inexpliqués |
|---|---|---|---|---|---|---|---|
| Intersection_triang | 802 | 770 | 730 | 1,73 s / 0,35 s | 0,62 s / 0,34 s | ×2,8 / ×1,0 | 0 |
| Above_triang | 1 359 | 1 420 | 1 296 | 46,4 s / 15,0 s | 0,35 s / 0,12 s | ×133 / ×122 | 0 |
| OBB_Above_triang | 2 259 | 2 108 | 2 078 | 8,57 s / 3,72 s | 0,33 s / 0,05 s | ×26 / ×72 | 0 |

Duplex Architecture × Plumbing ([détail](comparaison_duplex_plomberie.md)) :

| Règle | Gain froid / chaud | Inexpliqués |
|---|---|---|
| Intersection_triang | ×3,3 / ×1,1 | 0 |
| Above_triang | ×71 / ×286 | 0 |
| OBB_Above_triang | ×17,5 / ×96 | 0 |

SampleCastle, 300 éléments par côté ([détail](comparaison_castle.md)) :
- **Intersection_triang** : 0 écart inexpliqué.
- **Above et OBB_Above d'origine** : elles échouent (voir plus bas) ;
  leurs versions `_triang` donnent 120 et 204 résultats en moins de 0,1 s.

**Pourquoi Intersection_triang gagne peu.** Les autres règles convertissent
l'IFC en B-Rep, le maillent à 0,01 m et lancent 2 500 rayons par élément. Pour
Intersection, l'essentiel du temps est le test de pénétration de l'arbre
IfcOpenShell lui-même, identique des deux côtés. `_triang` n'économise que la
triangulation IFC.

**Causes des écarts constatées.** Toutes ont été vérifiées sur les trois
maquettes.

- **Élément absent du `.ifcview`** (surtout des `IfcOpeningElement`) : il
  est ignoré, avec un diagnostic.
- **Au bord du seuil** : pénétration, écart vertical ou contact à moins de la
  marge du seuil, soit 11 mm (flèche du `.ifcview` + flèche IFC). La paire
  revient, ou disparaît, quand le seuil bouge de la marge.
- **Maillage IFC ouvert** (Intersection). La triangulation IFC est souvent
  non fermée : 32 éléments Mechanical sur 524 seulement sont fermés, contre
  256 maillages `.ifcview` sur 286. Or l'arbre IfcOpenShell n'applique son
  test de pénétration qu'aux maillages fermés ; sinon, il fait un test de
  contact qui ignore les faces coplanaires. Exemple : deux copies d'un même
  local dans deux maquettes. Intersection ne les voit pas (angle mort
  « solides coïncidents ») ; Intersection_triang les voit.
- **Faces coïncidentes** (Intersection). Le test de pénétration d'IfcOpenShell
  est instable quand les deux objets ont des faces confondues : un sommet sur
  une face est « dehors », un sommet 0,05 mm à l'intérieur donne toute la
  profondeur. L'écart n'est expliqué que si les deux géométries IFC sont au
  contact, ce qui est vérifié par une Clearance à la marge.
- **OBB optimale non unique** (OBB_Above). Pour une section carrée ou ronde
  (une main courante), l'OBB a les mêmes dimensions mais des axes tournés.
  La bande « au-dessus » suit alors un autre axe.

**Défauts des règles d'origine révélés par la comparaison.** Ils sont
reproduits à l'identique par le portage C++, comme la parité l'exige.

1. **Above ne voit pas les objets fins.** Sa grille de 50 × 50 rayons couvre
   la plus grande dimension de l'objet, hauteur comprise. Pour une colonne
   montante de 2,4 m, les rayons sont espacés de 4,9 cm ; une section de
   3 cm passe entre eux. Le code le signale d'ailleurs lui-même (`@todo`).
2. **Above ne teste que les points les plus proches.** Il ne regarde que la
   paire de points la plus proche des deux faces, puis un rayon depuis ce
   point. Si ce point tombe juste hors de la face source, Above conclut
   « non », même si la cible surplombe la source ailleurs. Exemple : un tuyau
   d'eaux usées en pente au-dessus d'une semelle. Ces paires sont confirmées
   sur l'IFC par une verticale à travers les B-Rep source et cible.
3. **Le test « ray » d'Above utilise une droite infinie.**
   `BRepIntCurveSurface_Inter` est appelé sur une `gp_Lin` sans test de
   `W ≥ 0` : il garde une cible située sous la source.
4. **Above et OBB_Above plantent sur un élément dégénéré.** Sur
   SampleCastle, un axe d'OBB de longueur nulle donne
   `gp_Dir() - input vector has zero norm`.

## Carte de hauteur (essai, non branchée sur les règles)

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

L'atout propre de la carte reste à exploiter : elle donne directement la
surface haute (ou basse) d'un objet, ce qui permettrait de comparer deux
objets maille à maille pour Above sans chercher de faces.

## Lancer

```bash
cmake --build build/engine
./build/engine/engine_tests "[triang]"
PYTHONNOUSERSITE=1 python scripts/benchmark_extreme_faces.py --side top
PYTHONNOUSERSITE=1 python engine/triang/compare_triang.py --output engine/triang/comparaison_duplex.md
```

Depuis Python :

```python
from engine import _ifcclash_engine as native
s = native.Session(ifc_paths=[ifc], geometry_cache="require", ifcview_paths=[ifcview])
s.run(rule_type="Above_triang", params={"above_type": "Above_MaxToMin", "tolerance": 1.0}, selections=...)
```

## Limites

- **Fraîcheur.** Les résultats valent ce que vaut le `.ifcview`. Sans
  manifeste, il n'est accepté que s'il est plus récent que l'IFC.
- **Précision.** Elle est celle du maillage de BonsaiViewer, sans contrôle
  de la flèche utilisée.
- **Éléments non couverts.** Les éléments absents du `.ifcview` (ouvertures,
  et certains espaces selon l'export) ne sont pas testés.
