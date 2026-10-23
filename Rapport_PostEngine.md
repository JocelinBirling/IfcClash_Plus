# Rapport_PostEngine — Revue des règles après la migration moteur

**Date** : 2026-10-21
**Branche** : `Switch_Engine`
**Périmètre** : les 28 règles de `ifcclash_plus/Rules.py` (5 395 lignes), croisées avec
`RuleClass.py` (classes de base), `clash_utils.py` (primitives géométriques),
`registry.py` (catalogue) et `serialization.py` (aller/retour JSON).
**Objet** : détection de **lourdeur** (coûts de calcul évitables) et d'**incohérence**
(conventions contradictoires entre règles, entre code et catalogue, entre code et docs).

**Criticité utilisée** : CRITIQUE (plante ou faux résultat), MAJEUR (comportement
surprenant ou coût disproportionné), MOYEN (à corriger au prochain passage),
MINEUR (confort / style).

---

## 1. Synthèse

| # | Constat | Criticité | Où |
|---|---------|-----------|-----|
| S1 | Docstrings du catalogue (`registry.py`) **inversées** par rapport au code pour 8 règles : Volume, Area, TopOrBottomSurface, ObbHigh, ObbLength, Above, Below, DirectView | MAJEUR | §2.1 |
| S2 | Attribut `rule.type` incohérent : jamais posé pour 4 règles, différent du nom de catalogue pour 4 autres | MOYEN | §2.2 |
| S3 | Sémantique du paramètre `tolerance` différente selon la règle (distance, hauteur, volume, liste de strings) ; défauts divergents registry vs serialization | MAJEUR | §2.3 |
| S4 | Deux patrons d'affichage coexistent dans les moteurs (display dans `compute()` vs hook `register_display_items`), alors que la SPEC moteur/gestion revendique un compute « pur » | MAJEUR | §2.4 |
| S5 | Boucles paires O(n²) sans préfiltre spatial sur 3 familles (AngleBetween, Ray_Check, FaceCheck) ; `Ray_Check` est le pire cas : O(S·T·C) en intersection exacte | MAJEUR | §2.5 |
| S6 | `BRepExtrema_DistShapeShape` instancié dans des boucles internes (Above/Below par paire de faces, OBB_* par paire, ClearanceForDoors par porte×cible×zone, FreeSpace par obstacle) | MAJEUR | §2.6 |
| S7 | Itérateurs de géométrie créés **par élément** avec `multiprocessing.cpu_count()` (ClearanceForDoors, FreeSpace) ; double passe OCC + mesh (SurfaceRecover, ClearanceForDoors) ; arbre BVH reconstruit à chaque compute | MAJEUR | §2.7 |
| S8 | Validation des paramètres hétérogène : 8 règles valident tout, les autres acceptent n'importe quoi — dont 2 avec crash différé (`Orientation`, `TopOrBottomSurface`) | MAJEUR | §2.8 |
| S9 | Duplication/divergence : `OneObjectFace._run_checks` vs `TwoObjectsFace._run_checks` (le préfiltre bbox de la seconde manque à la première) ; `Above`/`Below` quasi dupliqués ; `Intersection2` étend les résultats là où `Intersection` remplace | MAJEUR | §2.9 |
| S10 | Nommage : mélange fr/en, « Parrallel » (typo figée dans l'API), doc `ObbHeigh.md` vs classe `ObbHigh`, `max_ray_length` vs `max_distance`, mesure « offset » pour une hauteur | MOYEN | §2.10 |

Aucune règle ne bloque la migration : tous les moteurs `compute()` existent et sont
testés (`tests/test_compute_*.py`). Les points ci-dessus sont des dettes de
cohérence et de performance, pas des régressions de la migration.

---

## 2. Constats transversaux

### 2.1 Docstrings du catalogue inversées (MAJEUR)

`registry.py` décrit 8 règles à contre-sens du comportement réel du `compute()` :

| Règle | registry.py dit | compute() fait |
|-------|-----------------|----------------|
| Volume | « Flags every source whose volume is **outside** [volume_min, volume_max] » | flagge les sources **dans** `]volume_min, volume_max[` (Rules.py:66) — conforme à `doc/1ObjectsRules/Volume.md` |
| Area | idem « outside » | **dans** les bornes (Rules.py:101) |
| TopOrBottomSurface | « outside the bounds » | **dans** les bornes |
| ObbHigh | « outside [length_min, length_max] » | **dans** les bornes |
| ObbLength | idem | **dans** les bornes |
| Above | « Flags the pairs whose **source is not above** the target » | flagge les paires dont la **cible est au-dessus** de la source (Rules.py:1858) |
| Below | « source is not below the target » | flagge les paires dont la **cible est en dessous** |
| DirectView | « Flags the pairs **without** a direct line of sight » | flagge les paires **avec** vue directe établie (`hit_ratio >= threshold`, Rules.py:3963) ; une paire totalement occultée ne produit **aucun** résultat |

Un client qui construit son UI sur le catalogue affiche donc le contraire de ce que
le moteur fait. Volume/Area/TopOrBottom/ObbHigh/ObbLength ont de plus une sémantique
de **détection dans une plage** (filtre), pas de « clash » : le mot « flags … outside »
était probablement le reste d'une intention antérieure.

`Ray_Check` : la doc du catalogue « Casts rays from the sources to the **context
obstacles** » est également fausse — les rayons vont des sources vers les **cibles**,
le contexte ne fait que bloquer.

### 2.2 Attribut `rule.type` incohérent (MOYEN)

La classe de base pose `self.type = None` (RuleClass.py:345). En pratique :

| Règle | `self.type` posé ? | Valeur | Type catalogue |
|-------|-------------------|--------|----------------|
| Volume, Area, ObbHigh, ObbLength, Orientation, AngleBetween, Intersection, Intersection2, Clearance, ClearanceAxisToAxis, Collision, SurfaceRecover, One/TwoObjectsFace, ClearanceForDoors, Alignement, DirectView, FreeSpace | oui | = nom du type | cohérent |
| TopOrBottomSurface | oui | `"TopSurface"` / `"BottomSurface"` | `TopOrBottomSurface` |
| ProjectedSurface | oui | `"Projected"` | `ProjectedSurface` |
| Above / Below | oui | `"Above_MinToMax"`… (la méthode de bornage) | `Above` / `Below` |
| Ray_Check | oui | `"RayCheck"` (sans underscore) | `Ray_Check` |
| OBB_Above, OBB_Below, OBB_Front_And_Back, OBB_Custom | **non** | `None` | — |

La sérialisation compense en sérialisant sur `type(rule).__name__`
(serialization.py:674), donc l'aller/retour JSON fonctionne — mais tout consommateur
de `rule.type` (display, export, logs) obtient une valeur imprévisible. La convention
devrait être : `type` = nom du type catalogue, le paramètre de variante
(`above_type`, `top_or_bot_method`…) porté séparément.

### 2.3 Le paramètre `tolerance` veut dire 5 choses différentes (MAJEUR)

| Règle | Sens de `tolerance` | Défaut registry | Défaut serialization |
|-------|---------------------|-----------------|----------------------|
| Intersection | distance (m) | 0.1 | 0.1 |
| Intersection2 | **volume d'overlap minimal (m³)** | 0.0 | 0.0 |
| Above / Below | hauteur de zone de détection + distance de contact (m) | 0.1 | 0.1 |
| OBB_Above / OBB_Below | hauteur de bande (m) | **1.0** | **0.1** — divergent |
| OBB_Front_And_Back | profondeur de bande (m) | 0.1 | 0.1 |
| OBB_Custom | **liste de strings de modifications** (nom trompeur, documenté) | `[]` | `[]` |
| SurfaceRecover | distance de contact (m) | **0.001** | 0.001 |
| ClearanceForDoors | pénétration négligeable (m) | **0.001** | 0.001 |
| ClearanceAxisToAxis | élargissement d'intervalle (m) | 0.0 | 0.0 |

Divergences de défauts : **OBB_Above/OBB_Below** — le catalogue annonce 1.0,
`deserialize_rule_check` applique 0.1 si la clé manque (serialization.py:1017-1019) ;
le constructeur, lui, n'a **pas de défaut du tout** (paramètre positionnel obligatoire),
contrairement à Above (0.1). Trois valeurs selon le chemin d'entrée.

**FreeSpace.height** : défaut catalogue 2.0, mais `deserialize` passe
`data.get("height")` sans défaut (serialization.py:1113) et le constructeur
**lève ValueError sur None** (paramètre obligatoire). Un client qui omet `height`
en se fiant au catalogue obtient une exception.

**DirectView.threshold** : le catalogue le déclare `float` (défaut 100.0) alors que le
constructeur exige une **chaîne terminée par « % »** (Rules.py:3728). La couche
serialization convertit (serialization.py:1062-1064), mais tout appel direct du
constructeur avec le défaut du catalogue plante.

**OBB_Custom** : le catalogue illustre les modifications par « ex. 'top 0.5',
'bottom 0.2' » — or `_modification_value` fait `modification.split(":")[1]`
(Rules.py:2373-2383) : sans « : », **IndexError** ; et les mots-clés reconnus sont
`expand_sides`, `detach_top_by_extrude`, `detach_bottom_by_extrude`, `extend_up`,
`extend_down`, `NEW_OBB` — « top 0.5 » ne correspond à rien. Pire : une chaîne de
modification inconnue est **silencieusement ignorée** (pas de `else`, pas de
validation), donc une faute de frappe dans une config produit des zones fausses sans
aucune erreur.

### 2.4 Deux patrons d'affichage coexistent dans les moteurs (MAJEUR)

La SPEC moteur/gestion (reprise dans chaque docstring) dit : « nothing is registered
for the display: the display data travels in the info blocks ». Deux familles
violent ce principe de façons opposées :

- **Display dans `compute()`** (branches `if self.state in ("Display_Input",
  "Display_Result")`, `register_display_item` + `return []`) :
  TopOrBottomSurface, ObbHigh, ObbLength, Orientation, AngleBetween,
  ClearanceAxisToAxis, OBB_Above, OBB_Below, OBB_Front_And_Back, OBB_Custom.
  Le header de Rules.py le documente comme « exception » pour les règles à display
  conditionné par l'état, mais il concerne aujourd'hui **10 règles sur 28** — ce
  n'est plus une exception, c'est un second patron.
- **Hook `register_display_items(results)`** (appelé par l'orchestrateur) :
  Ray_Check, Above, Below, SurfaceRecover, DirectView, OneObjectFace,
  TwoObjectsFace, ClearanceForDoors, FreeSpace, Alignement.

Conséquence concrète : dans l'état `Display_Input`, les règles du premier groupe
**exécutent quand même la moitié du moteur** (collecte des OBB/zones/axes de chaque
élément) avant de jeter les résultats ; les secondes court-circuitent le moteur
avant l'appel au compute. Le contrat « Display_Input ne lance pas le moteur »
n'est vrai que pour la moitié du parc.

Autres violations ponctuelles du « compute pur » (toutes documentées comme
exceptions, donc traçables) : `Alignement`, `DirectView`, `FreeSpace` et
`ClearanceForDoors` **posent leurs paramètres sur l'instance** dans `compute()`
(`self.axis = axis`, `self.tree = …`, etc.) — le nœud reste porteur de config et
d'état moteur, ce qui rend ces moteurs non rejouables en parallèle sur la même
instance.

### 2.5 Lourdeur : boucles paires sans préfiltre spatial (MAJEUR)

| Règle | Boucle | Coût | Préfiltre |
|-------|--------|------|-----------|
| AngleBetween | S×T | OBB par objet (précalculé, bien) puis test trigonométrique par paire | aucun (documenté Rapport.md) |
| Ray_Check | S×T×C | **intersection exacte segment/shape OCC pour chaque paire × chaque objet de contexte** (`segment_hits_shape`) | aucun |
| OneObjectFace | faces A×faces B par objet | `distance_between_triangles` = **2 faces OCC + BRepExtrema par paire** si `min_distance` actif sans `max_distance` | bbox seulement sur `max_distance` |
| TwoObjectsFace | faces source×faces target par paire d'objets | idem | bbox sur `max_distance` **et** sur `min_distance` (absent de OneObjectFace) |
| DirectView | S×T×ray_count | ray tree BVH (bien) + early-stop (bien) | oui |
| Above/Below | S×T | préfiltre OBB zone/cible (bien), **mais** `check_extrem_face_distance` fait un `BRepExtrema` **par paire de faces extrêmes** à l'intérieur de chaque paire retenue | oui (grossier) |
| Intersection2 | S×T | `BRepAlgoAPI_Common` par paire après préfiltre bbox | oui |

`Ray_Check` est le pire cas du projet : N sources × M cibles × K objets de contexte
intersections exactes, alors que `DirectView` résout le même problème avec un
**arbre de rayons** (`clash_utils.make_ray_tree`). Les deux règles coexistent avec
deux moteurs différents pour un besoin identique — Ray_Check devrait être porté sur
le ray tree (l'upstream ifcopenshell #9755 sur `select_ray` ne concerne que la
résolution d'entité, pas le hit-test).

Détail : `_tree_clash_results` restaure l'ordre source/cible avec
`a_object in source_elements` (Rules.py:833) — appartenance en **O(n)** par
verdict sur une **liste** ; à convertir en `set` (O(1)). Peu coûteux face aux
géométries, mais gratuit à corriger.

### 2.6 Lourdeur : `BRepExtrema_DistShapeShape` en boucle interne (MAJEUR)

- **Above / Below** : un `BRepExtrema` par paire (face source × face cible) dans
  `check_extrem_face_distance` (clash_utils.py:952-958) — pour deux objets de 200
  faces extrêmes chacun, 40 000 constructions d'outil pour une seule paire d'objets.
- **OBB_Above / OBB_Below / OBB_Front_And_Back / OBB_Custom** : un `BRepExtrema`
  par (zone, cible) après le préfiltre `IsOut` — acceptable, mais l'outil est
  reconstruit à chaque itération (l'API permet de recharger S2 seulement).
- **ClearanceForDoors** : un `BRepExtrema` par (porte, cible, zone) **sans préfiltre
  bbox zone/cible** avant la mesure exacte (Rules.py:5038-5045).
- **FreeSpace._placement_margin** : `BRepExtrema` cylindre×obstacle pour **tous**
  les obstacles du contexte, sans le filtre de boîte déjà calculé dans
  `_search_placement` (Rules.py:5085-5096).
- **OneObjectFace / TwoObjectsFace** : `distance_between_triangles` construit
  2 faces OCC + un `BRepExtrema` **par paire de triangles** (clash_utils.py:3241).
  Un calcul triangle-triangle vectorisé (numpy) serait d'un ordre de grandeur
  plus rapide.

Le seuil de contact « touche/pénètre » est codé en dur à `1e-6` dans les 4 règles
OBB_* (Rules.py:2055, 2322, 2527) — indépendant de la `tolerance` de la règle,
contrairement à Above/Below qui l'utilisent comme distance de contact. Deux
conventions pour le même concept.

### 2.7 Lourdeur : itérateurs de géométrie (MAJEUR)

- **ClearanceForDoors._door_dimensions** (Rules.py:4754) : crée un
  `ifcopenshell.geom.iterator(settings, file, multiprocessing.cpu_count(),
  include=[porte])` **par porte** — un pool multi-process pour un seul élément.
  Sur 500 portes : 500 initialisations d'itérateur. Le pattern « kernel réutilisable
  par fichier » (`clash_utils.element_shapes`, `ifcopenshell.geom.kernel`) existe
  déjà et devrait servir ici.
- **FreeSpace.compute** : même pattern — un itérateur complet par source
  (Rules.py:5339-5347).
- **SurfaceRecover._collect_geometry** et **ClearanceForDoors._collect_targets** :
  **double passe** d'itération par fichier (une passe OCC, une passe mesh) — deux
  tessellations des mêmes éléments. À noter : la passe OCC de SurfaceRecover ne
  demande pas `USE_WORLD_COORDS`, contrairement à la passe mesh — les shapes OCC
  servent au `BRepExtrema` par paire alors que les triangles du contact sont en
  coordonnées monde : à vérifier, c'est le schéma exact du bug de coordonnées
  locales corrigé pour LateralSurface/ProjectedSurface pendant la migration.
- **Arbre BVH** : `Intersection`/`Clearance`/`Collision` reconstruisent chacun leur
  arbre **à chaque compute** (`make_clash_tree` + `add_elements_to_clash_tree`),
  même quand plusieurs règles de la session partagent les mêmes listes. Un cache
  par (fichier, liste d'éléments) éliminerait la moitié du coût des sessions
  multi-règles.
- **Ray_Check vs DirectView** : cf. §2.5.

### 2.8 Validation des paramètres hétérogène (MAJEUR)

Valident exhaustivement leurs paramètres au constructeur :
**ClearanceAxisToAxis, Alignement, SurfaceRecover, DirectView, OneObjectFace,
TwoObjectsFace, ClearanceForDoors, FreeSpace**.

N'ont **aucune** validation : Volume, Area, TopOrBottomSurface, LateralSurface,
ProjectedSurface, ObbHigh, ObbLength, Orientation, AngleBetween, Intersection,
Intersection2, Clearance, Collision, Ray_Check, Above, Below, OBB_Above, OBB_Below,
OBB_Front_And_Back, OBB_Custom.

Deux cas produisent un **crash différé** plutôt qu'une erreur claire :
- `Orientation.compute` : `check_direction` n'est assigné dans aucune branche si
  `orientation_type` ∉ {"Parrallel", "Perpendicular"} → `UnboundLocalError`
  au milieu de la boucle (Rules.py:594-599).
- `TopOrBottomSurface.compute` : `direction` non défini si
  `top_or_bot_method` ∉ {"Top", "Bottom"} → `NameError` (Rules.py:156-159).

Typo figée dans l'API publique : litéral `"Parrallel"` (double r) dans
`ORIENTATION_TYPE` et le catalogue.

### 2.9 Duplication et divergence (MAJEUR)

- **OneObjectFace._run_checks vs TwoObjectsFace._run_checks** : deux implémentations
  du même moteur de checks. La version TwoObjects contient un préfiltre
  `triangles_bbox_distance >= min_distance → skip` absent de la version
  OneObject (Rules.py:4256-4267 vs 4651-4666). Résultat : **la même vérification
  de distance est beaucoup plus chère sur OneObjectFace** et les deux moteurs
  peuvent diverger silencieusement à l'avenir. `_triangle_data` est dupliqué à
  l'identique dans les deux classes.
- **Above vs Below** : moteurs quasi identiques (~130 lignes chacun, Rules.py:1855-1900
  et 1907-2030), diffèrent par `zone_side`, `side`, le sens du rayon et le label.
  La famille OBB_Above/OBB_Below montre le patron correct : un
  `_compute_obb_zone_penetration` partagé, paramétré par côté. Above/Below devraient
  suivre le même schéma.
- **collect_results** : `Intersection`, `Clearance`, `Collision` surchargent
  `collect_results` pour **remplacer** la liste (sémantique de l'ancien `run()`) ;
  **Intersection2** — présentée comme l'alternative d'Intersection — ne le fait pas
  et **étend**. Deux sémantiques d'accumulation pour deux règles interchangeables.
- Duplication des patterns de collecte par fichier (`by_file` + itérateur) dans
  6 règles (Alignement, SurfaceRecover, DirectView, ClearanceForDoors, FreeSpace,
  Ray_Check) alors que `clash_utils.element_shapes` (kernel réutilisable) centralise
  déjà le besoin pour les autres.

### 2.10 Nommage et conventions (MOYEN)

- `Area` réutilise les clés `volume_min`/`volume_max` pour une surface (documenté,
  mais trompeur dans les exports JSON).
- `LateralSurface.direction` et `ProjectedSurface.direction` annotés `: float` alors
  que ce sont des vecteurs 3D (Rules.py:246, 295).
- Doc `doc/1ObjectsRules/ObbHeigh.md` vs classe `ObbHigh` (fichier mal orthographié).
- `Ray_Check.max_ray_length` vs `DirectView.max_distance` : même concept, deux noms.
- Mesure « offset » dans les info blocks pour une **hauteur** (ObbHigh), une
  **dimension** (ObbLength) et un décalage d'alignement (Alignement) : la clé
  `info.offset` porte trois sens.
- `Intersection` hardcode `check_all=True` alors que `Clearance` expose `check_all`
  dans le catalogue — asymétrie non documentée.
- Transparence des items « context » : 0.9 dans Ray_Check (Rules.py:1568), 0.85 dans
  DirectView et FreeSpace.
- `ProjectedSurface.type = "Projected"` : le seul 1-objet dont le type ≠ nom de classe.
- Mélange `self.geom_settings.set(self.geom_settings.USE_WORLD_COORDS, True)` et
  `set("USE_WORLD_COORDS", True)` (chaîne en dur) selon les règles — les deux
  fonctionnent mais le style diverge, et la forme chaîne est fragile à un rename
  upstream.
- `SurfaceRecover` : passe OCC indexée par `shape.data.id`, passe mesh par
  `shape.id` — deux API différentes pour appairer le même élément (Rules.py:3384/3394).
- `OneObjectFace`/`TwoObjectsFace` : le catalogue déclare les sélections de faces
  `kind: "string"` alors que le contrat du constructeur est un **dictionnaire**
  FaceSelection — seule la chaîne vide passe (convertie en None par
  `data.get(...) or None`, serialization.py:1077). Un client qui envoie une vraie
  chaîne descriptive plante sur `validate_face_selection`.

---

## 3. Analyse règle par règle

### 3.1 Règles 1-objet

**Volume** (Rules.py:47)
- Lourdeur : négligeable (`get_volume` par élément, séquentiel mais bon marché).
- Incohérence : docstring catalogue inversée (S1) ; sémantique « détection dans une
  plage » à documenter (le résultat `state=True` désigne un objet *conforme* à la
  plage, ce que les autres règles appellent un *clash*).

**Area** (Rules.py:83)
- Lourdeur : négligeable.
- Incohérence : params `volume_min`/`volume_max` pour une aire ; doc catalogue
  inversée (S1).

**TopOrBottomSurface** (Rules.py:122)
- Lourdeur : moyenne — extraction des faces extrêmes + `get_vertices` par élément ;
  en Display_Input le moteur tourne quand même intégralement (§2.4).
- Incohérence : `NameError` si méthode invalide (§2.8) ; `self.type` = « TopSurface »/
  « BottomSurface » ; display dans compute (§2.4).

**LateralSurface** (Rules.py:224)
- Lourdeur : négligeable.
- Incohérence : `direction: float` (annotation fausse) ; angle du cône 45° codé en
  dur, non paramétrable.

**ProjectedSurface** (Rules.py:272)
- Lourdeur : négligeable.
- Incohérence : `self.type = "Projected"` ; annotation `direction: float` fausse.

**ObbHigh** (Rules.py:319)
- Lourdeur : faible — OBB par élément ; `min_z`/`max_z` calculés en boucle manuelle
  alors que `min(...)`/`max(...)` natifs suffiraient (cosmétique).
- Incohérence : doc `ObbHeigh.md` mal orthographiée ; `info.offset` pour une hauteur ;
  display dans compute.

**ObbLength** (Rules.py:388)
- Lourdeur : faible.
- Incohérence : `direction_method.lower() == "wide"` mais tout ce qui n'est pas
  « wide » est silencieusement traité comme « Narrow » (pas de validation, pas
  d'else) ; heuristique d'axe vertical arbitraire à 45° (documentée `@todo`).

**Orientation** (Rules.py:487)
- Lourdeur : faible (OBB + centre par élément).
- Incohérence : `UnboundLocalError` si `orientation_type` invalide (§2.8) ; typo
  « Parrallel » figée dans l'API et le catalogue.

### 3.2 Règles 2-objets

**AngleBetween** (Rules.py:616)
- Lourdeur : MAJEUR — S×T sans préfiltre spatial (documenté) ; les directions OBB
  sont pourtant précalculées par objet (bien), le coût par paire est faible mais
  le nombre de paires ne l'est pas.
- Incohérence : symétrie 180° non pliée (documentée) ; display en double code
  (bloc Display_Input + bloc Display_Result copié-collé).

**Intersection** (Rules.py:863)
- Lourdeur : arbre reconstruit à chaque compute (§2.7) ; `_tree_clash_results`
  membership O(n) (§2.5).
- Incohérence : `check_all=True` hardcodé ; `collect_results` remplace la liste.

**Intersection2** (Rules.py:914)
- Lourdeur : MAJEUR par conception (booléen OCC par paire, expérimental), préfiltre
  bbox présent (bien) ; `mesh_to_solid` (couture de mesh en solide) par élément à
  chaque compute — cacheable.
- Incohérence : `tolerance` = volume minimal (m³) vs distance (m) pour Intersection ;
  `collect_results` étend au lieu de remplacer (S9).

**Clearance** (Rules.py:1048)
- Lourdeur : idem Intersection.
- Incohérence : aucune — c'est la seule règle BVH à exposer `check_all`.

**ClearanceAxisToAxis** (Rules.py:1176)
- Lourdeur : moyenne — S×T mais avec porte de linéarité et fallback DistShapeShape
  seulement sur demande ; `parallel_line_offset_closest` par paire quasi parallèle.
- Incohérence : aucune notable — c'est le **modèle** du parc (validation complète,
  info blocks riches, fallback documenté). Les autres règles devraient s'y aligner.

**Collision** (Rules.py:1106)
- Lourdeur : idem Intersection.
- Incohérence : rien à signaler (`allow_touching` correctement exposé).

**Ray_Check** (Rules.py:1492)
- Lourdeur : CRITIQUE en volume — O(S·T·C) intersections exactes, cf. §2.5 ; à
  porter sur le ray tree de DirectView.
- Incohérence : `self.type = "RayCheck"` ≠ catalogue `Ray_Check` ; le contexte vit
  en **double source de vérité** (un `Select` sur le nœud pour le display,
  `liste_objet_contexte` pour le moteur) ; doc catalogue fausse ; commentaire
  « It's the same object » sur `distance == 0` trompeur (centres confondus ≠ même
  objet) ; famille « ComplexRule » au catalogue mais classe `RuleCheckTwoObjects`.

**Above** (Rules.py:1768) / **Below** (Rules.py:1900)
- Lourdeur : MAJEUR — `check_extrem_face_distance` fait un `BRepExtrema` **par paire
  de faces extrêmes** dans chaque paire d'objets retenue par le préfiltre OBB
  (§2.6) ; le fallback « Need_More_Check » relance un ray test par candidate.
- Incohérence : conventions directionnelles contradictoires (documentées Rapport.md
  §2) ; doc catalogue inversée (S1) ; duplication Above/Below (S9) ; `self.type`
  = méthode de bornage.

**OBB_Above** (Rules.py:2088) / **OBB_Below** (Rules.py:2167)
- Lourdeur : moyenne — `BRepExtrema` par paire après préfiltre `IsOut` (correct),
  outil reconstruit à chaque itération.
- Incohérence : `self.type` jamais posé ; défauts de tolerance divergents
  (registry 1.0 / serialization 0.1 / constructeur : aucun) ; epsilon de contact
  1e-6 codé en dur ; le paramètre « tolerance » est ici une **hauteur de bande**,
  pas une tolérance — la docstring du catalogue le dit, le nom non.

**OBB_Front_And_Back** (Rules.py:2245)
- Lourdeur : idem OBB_Above ×2 (deux bandes par source) ; une cible touchant les
  deux bandes produit **deux verdicts** pour la même paire (pas de déduplication).
- Incohérence : défaut connu documenté (test rouge préexistant
  `TestOBB_Front_And_Back::test_CubeB_Side_45CuboidA`) ; `self.type` jamais posé ;
  commentaire « It's the old way, but it can create faces toward Z » : dette
  assumée à retracer dans le moteur.

**OBB_Custom** (Rules.py:2383)
- Lourdeur : idem OBB_Front_And_Back, multipliée par le nombre de zones déclarées.
- Incohérence : paramètre `tolerance` = liste de strings (documenté trompeur) ;
  exemple du catalogue incompatible avec le parseur (`'top 0.5'` → IndexError,
  cf. §2.3) ; modifications inconnues **silencieusement ignorées** ; `self.type`
  jamais posé.

### 3.3 Règles complexes

**Alignement** (Rules.py:2549)
- Lourdeur : moyenne — itérateur multi-process par fichier (bien), ajustements
  moindres carrés par groupe ; `_fit_group_element` recalculé pour **tous** les
  groupes dans `_fitted_zone_shapes` (display) alors que `_build_alignment_info`
  vient de le faire pour le meilleur groupe (double travail au display).
- Incohérence : compute pose les paramètres sur l'instance (exception documentée) ;
  `_fitted`/`_orientation` posés comme états internes sans préfixe `_engine_`
  contrairement à `_engine_objects`/`_engine_groups` ; `info.offset` réutilisé.

**SurfaceRecover** (Rules.py:3264)
- Lourdeur : MAJEUR — double passe d'itération par fichier (OCC + mesh, §2.7) ;
  `BRepExtrema` exact par paire d'objets après le préfiltre OBB (acceptable) ;
  polygones de contact par paire coûteux mais c'est le cœur de la règle.
- Incohérence : `tolerance` par défaut 0.001 (1 mm) là où Above/Below utilisent
  0.1 (10 cm) pour le même concept de contact ; `shape.data.id` vs `shape.id` ;
  passe OCC sans coordonnées monde alors que les triangles du contact en sont
  (cf. §2.7) ; la direction accepte un vecteur 3D au constructeur mais le
  catalogue n'expose que Auto/Top/Bottom.

**DirectView** (Rules.py:3671)
- Lourdeur : bien maîtrisée — ray tree BVH, early-stop déterministe, sampling R2.
- Incohérence : doc catalogue inversée (S1) ; `threshold` float au catalogue vs
  chaîne "%" au constructeur (§2.3) ; `self.tree` état moteur sur le nœud ;
  `max_distance` vs `max_ray_length` (Ray_Check) ; transparence contexte 0.85
  vs 0.9.

**OneObjectFace** (Rules.py:4014)
- Lourdeur : MAJEUR — sans `max_distance`, le check distance appelle
  `distance_between_triangles` (2 faces OCC + BRepExtrema) sur **chaque** paire de
  triangles A×B ; les checks intersection/orientation tournent aussi sur toutes
  les paires sans préfiltre bbox.
- Incohérence : préfiltre bbox de `min_distance` absent (présent dans
  TwoObjectsFace — S9) ; sélections de faces déclarées `string` au catalogue alors
  que le contrat est un dictionnaire FaceSelection (seule la chaîne vide passe) ;
  `seen_pairs` déduplique sur géométrie (OK) mais `skip_adjacent` ne s'applique
  qu'au check distance.

**TwoObjectsFace** (Rules.py:4334)
- Lourdeur : MAJEUR — même schéma que OneObjectFace mais avec le préfiltre bbox
  (donc moins pire) ; intersection/orientation sur toutes les paires.
- Incohérence : duplication `_triangle_data`/`_run_checks` avec divergence de
  comportement (S9) ; param `skip_adjacent` absent (justifié par la doc) — à
  documenter dans le catalogue.

**ClearanceForDoors** (Rules.py:4690)
- Lourdeur : MAJEUR — itérateur multi-process **par porte** pour `_door_dimensions`
  (§2.7) ; double passe par fichier pour les cibles ; `BRepExtrema` par
  (porte, cible, zone) **sans préfiltre bbox** ; `register_display_items` reconstruit
  toutes les zones des portes (rebuild complet au display).
- Incohérence : **code mort** dans `_build_zones` : `leaf_origin` calculé
  identiquement dans les deux branches du if/else hinge et **jamais utilisé**
  (Rules.py:4932-4935) ; `tolerance` défaut 0.001 (1 mm).

**FreeSpace** (Rules.py:5065)
- Lourdeur : MAJEUR — itérateur complet **par source** (§2.7) ; par source × par
  obstacle : un booléen OCC (`BRepAlgoAPI_Common`) + maillage à la déflexion r/25 ;
  `_placement_margin` re-teste **tous** les obstacles au `BRepExtrema` sans
  le filtre de boîte déjà calculé ; `register_display_items` ré-itère tout le
  contexte (`_collect_context` appelé une 2e fois).
- Incohérence : `height` obligatoire mais défaut `None` au constructeur → toute
  instanciation sans height lève, alors que le catalogue annonce un défaut 2.0
  (§2.3) ; pas de vérification que le contexte est fourni (un `context=None`
  donne une règle qui ne détecte jamais d'obstacle → toujours « libre »,
  silencieusement).

---

## 4. Recommandations priorisées

### P1 — Cohérence client/moteur (avant toute ouverture du catalogue)
1. Réécrire les docstrings `registry.py` des 8 règles inversées (S1) — c'est le
   contrat de l'UI.
2. Aligner les défauts : OBB_Above/OBB_Below (1.0 vs 0.1 vs aucun), FreeSpace.height
   (2.0 annoncé / None appliqué), DirectView.threshold (float vs "%").
3. Corriger l'exemple OBB_Custom du catalogue et ajouter une ValueError sur les
   modifications non reconnues dans `create_list_of_obb`.
4. Corriger les deux crashs différés : branche `else` explicite dans
   `Orientation.compute` et `TopOrBottomSurface.compute`.

### P2 — Lourdeur
5. Porter `Ray_Check` sur le ray tree (`clash_utils.make_ray_tree`) — même moteur
   que DirectView, suppression du O(S·T·C) exact.
6. Factoriser le préfiltre bbox `min_distance` de TwoObjectsFace vers
   OneObjectFace, et vectoriser `distance_between_triangles` (numpy) ou
   pré-grouper les triangles par grille spatiale.
7. Remplacer les itérateurs par élément (ClearanceForDoors `_door_dimensions`,
   FreeSpace par source) par le kernel réutilisable par fichier
   (`clash_utils.element_shapes`).
8. Cache d'arbre BVH par (fichier, sélection) pour Intersection/Clearance/Collision ;
   `_tree_clash_results` avec des `set` pour l'appartenance.
9. Partager le moteur Above/Below à la manière de `_compute_obb_zone_penetration`
   (supprime ~130 lignes et garantit la symétrie des deux règles).
10. Supprimer le code mort `leaf_origin` de ClearanceForDoors et préfiltre bbox
    zone/cible avant le `BRepExtrema`.

### P3 — Hygiène
11. Unifier `self.type` sur le nom du type catalogue (paramètre de variante porté
    séparément) ; renommer la doc `ObbHeigh.md` → `ObbHigh.md`.
12. Décider du patron d'affichage unique (hook `register_display_items` recommandé
    par la SPEC) et migrer les 10 règles qui affichent dans `compute()`.
13. Généraliser la validation des paramètres à partir du catalogue (le registry
    porte déjà types et défauts : la validation peut en être dérivée) — le patron
    de ClearanceAxisToAxis est le modèle.
14. Renommer `Area.volume_min/volume_max` (avec alias de désérialisation pour les
    sessions existantes) ; nommer les mesures (`height`, `dimension`, `offset`)
    au lieu d'un `info.offset` unique.

---

## Annexe A — Inventaire des préfiltres spatiaux par paire

| Règle | Préfiltre avant mesure exacte |
|-------|-------------------------------|
| Intersection / Clearance / Collision | arbre BVH (`tree.clash_*_many`) |
| Intersection2 | bbox `Bnd_Box.IsOut` |
| AngleBetween | aucun |
| ClearanceAxisToAxis | aucun (mesure algébrique par paire, coût faible) |
| Ray_Check | aucun (test exact par objet de contexte) |
| Above / Below | OBB zone/cible (`IsOut`), puis ray fallback |
| OBB_Above / OBB_Below / OBB_Front_And_Back / OBB_Custom | OBB zone/cible (`IsOut`) |
| SurfaceRecover | OBB `min_distance_to_obb` |
| DirectView | ray tree + early-stop |
| OneObjectFace | bbox sur `max_distance` seulement |
| TwoObjectsFace | bbox sur `max_distance` et `min_distance` |
| ClearanceForDoors | aucun avant le `BRepExtrema` |
| FreeSpace | bbox obstacles vs empreinte (mais pas dans `_placement_margin`) |

## Annexe B — Points déjà documentés, non re-comptés comme nouveaux

- Permutation arbitraire des axes OBB par OCCT (ObbHigh/ObbLength) — Rapport.md.
- Symétrie 180° d'AngleBetween ; absence de préfiltre d'AngleBetween — Rapport.md §1.1.
- Conventions Above/Below et défaut OBB_Front_And_Back — Rapport.md §2, test rouge.
- `OBB_Custom.tolerance` nom trompeur — Rapport.md + agent.md.
- Exceptions documentées « compute pose les params sur l'instance »
  (Alignement, DirectView, FreeSpace, ClearanceForDoors) — SPEC moteur/gestion.
- Bug upstream ifcopenshell #9755 (`select_ray` ne résout plus l'entité touchée),
  qui a motivé le moteur exact de Ray_Check — le hit-test par ray tree reste
  possible sans résolution d'entité.
