# Rapport — Portage C++ du moteur (SPEC_OptimisationInCPP)

Date : 2026-11-09. Branche : `Switch_Engine` (rien n'est commité).

## 1. Résumé

- Le moteur C++ `libifcclash_engine` (dossier `engine/`) porte **les 28 règles**
  du registre. Il comprend `Session`, `IfcSource`, `GeometryProvider`, le
  registre, `ElementPipeline`, `PairPipeline` avec BVH, `SetPipeline`, le
  contexte des règles complexes et les bindings pybind11.
- La lecture des `.ifcview` (étape 6) est faite : `IfcViewSource` fournit les
  boîtes des phases large et intermédiaire.
- **Parité stricte obtenue sur les 28 règles** : 31 cas de référence, mêmes
  paires (ou éléments) et mêmes blocs d'information que Python, flottants à
  1e-9 près. Les résultats sont identiques avec et sans préfiltres.
- Les 28 règles passent à `implementation: "cpp"` dans le catalogue
  (`CPP_RULES`). Deux cas restent en Python : les états d'affichage
  (`Display_Input`, `Display_Result`), et l'absence de module compilé (par
  exemple sous Python 3.14). Dans ces cas, l'orchestrateur se replie sur Python.
- Les copies C++ des 4 fichiers de tests calibrés (156 tests) donnent le même
  résultat que les originaux Python. Les seuls échecs sont 4 `test_suzanne`,
  qui échouent aussi en Python dans cet environnement.
- **Benchmark sur les 28 règles** (Duplex, 100 × 100 éléments, §6) : sur les
  26 règles qui finissent, le C++ prend 76 s pour une règle seule et 31 s
  relancé dans une session, contre 1 040 s en Python, soit ×14 et ×34.
  - **Cache de session, calcul parallèle par élément, lancer de rayons** : ces
    trois optimisations ont fait passer Above et Below de 54 s à 7 s.
  - **Parité** : les résultats restent identiques à l'octet.
  - **`.ifcview`** : divise par deux le temps froid d'Intersection et de
    Collision, et ne change rien aux autres règles.

## 2. Ce qui a été fait, au regard de la SPEC

| Étape SPEC | État |
|---|---|
| 0 — prérequis Python (imports relatifs, découpage de `clash_utils.py`) | **Non fait.** Pas bloquant pour le C++. |
| 1 — squelette + Volume | Fait |
| 2 — `PairPipeline` + Intersection, Clearance, Collision | Fait |
| 3 à 5 — 24 autres règles, contexte, `SetPipeline` | **Fait** (28/28 règles). Le contexte passe par `setup_context` des pipelines existants : pas de `ContextPipeline` séparé. |
| 6 — `IfcViewSource` | Lecture faite. Écriture du cache et contrôle du hash du manifeste non faits. |
| 7 — parallélisme | **Partiel** : données par élément et phase fine des règles d'un objet (`rule_threads`, règles `parallel_safe`). La phase fine des paires reste séquentielle. |
| 8 — `ViewerSource` | Non fait. L'interface `GeometrySource` et le constructeur `Session(source)` sont prêts. |

## 3. Environnement

La SPEC impose une seule version d'OCCT dans le processus. Sur conda-forge,
ifcopenshell 0.9.0post1 n'existe qu'avec **OCCT 8.0.1**, ce qui impose
**pythonocc-core 8.0.1.2**. Conséquences :

- Nouvel environnement conda `ifcclash_cpp` (Python 3.12). Les environnements
  existants n'ont pas été touchés. `environment.yml` et `conda/meta.yaml`
  fixent désormais ces versions.
- ifctester, ifcclash et bcf-client viennent de PyPI avec `--no-deps` : sinon
  pip installe un second ifcopenshell, avec son propre OCCT.
- Sur cette machine, un vieil ifcopenshell traîne dans `~/.local` : il faut
  lancer Python avec `PYTHONNOUSERSITE=1`.
- L'environnement de référence actuel (`Test_IfcOpenshell/.conda`, Python 3.14,
  ifcopenshell en wheel pip) contient déjà **deux OCCT** : 7.9.3 pour
  pythonocc, 7.8 embarqué dans la wheel.

## 4. Architecture livrée

Elle suit la SPEC (`engine/README.md` détaille les dossiers) :

- `rules/` : une règle = un `.cpp`, paramètres déclarés par pointeur de membre
  dans une `RuleSpec` validée avant tout calcul. Un paramètre inconnu, d'un
  mauvais type ou hors bornes lève `ConfigError`.
- **Règles de l'arbre** : la phase fine interroge le même arbre IfcOpenShell
  (`opencascade.trianglebvh`) que Python, en une requête par lot de paires
  candidates (`narrow_batch`). Les phases large (BVH OCCT) et intermédiaire
  (OBB) reprennent les marges de l'arbre. Un clash trouvé hors des candidates
  lève le diagnostic `prefilter_lost_clash` (jamais observé).
- **Les 24 autres règles**, regroupées par famille :
  - `OneObjectRules.cpp` : Area, TopOrBottomSurface, LateralSurface,
    ProjectedSurface, ObbHigh, ObbLength, Orientation ;
  - `DirectionalRules.cpp` : Above, Below, OBB_Above, OBB_Below,
    OBB_Front_And_Back, OBB_Custom ;
  - `AxisRules.cpp` : AngleBetween, ClearanceAxisToAxis, Intersection2 ;
  - `FaceRules.cpp` : OneObjectFace, TwoObjectsFace ;
  - `SurfaceRecover.cpp`, `ClearanceForDoors.cpp` ;
  - `ContextRules.cpp` : Ray_Check, DirectView, FreeSpace ;
  - `Alignement.cpp` (`SetPipeline`).

  Elles s'appuient sur des modules géométriques communs (`geometry/`) :
  - `Obb` : OBB OCCT avec les mêmes options que pythonocc, extrusions,
    décalages ;
  - `Faces` : normales, aires, faces extrêmes, faces visibles par lancer de
    rayons ;
  - `Triangles` : `FaceSelection` et tests triangle/triangle ;
  - `Geos` : API C de GEOS, la même version que shapely, pour les unions,
    intersections et buffers de polygones ;
  - `Numpy.h` : reproduit l'ordre des opérations de numpy et d'OpenBLAS (FMA,
    sommes par paires), ce qui est nécessaire pour tenir 1e-9.

  La B-Rep (`IfcSource::brep()`), les requêtes IFC (matériaux, classe,
  placement local, type d'ouverture des portes) et l'arbre de rayons
  (`opencascade.brep`) sont fournis par `IfcSource`.
- `ResultRecord` reprend la forme de `ResultInfo.to_dict()`.
  `cpp_backend.to_clash_results` reconstruit les `ClashResult` : le pipeline de
  gestion, l'export JSON et l'IPC ne changent pas.
- Une `Session` par RuleFile : fichiers parsés, géométrie convertie une seule
  fois, fermée à la fin de `RuleFile.run()`.
- `IfcViewSource` : boîtes par élément (union des instances placées en double)
  gonflées d'une `uncertainty` égale à la somme des deux flèches linéaires plus
  l'arrondi float. Repli sur l'IFC par élément (élément absent ou GlobalId
  différent) et par fichier (illisible, mauvaise version, plus ancien que l'IFC).
  Le lecteur est copié d'IfcOpenShell (`src/ifcviewer`, LGPL v3, en-têtes
  conservés).

## 5. Validation

### 5.1 Méthode de parité : références figées

La première méthode recalculait Python et C++ à chaque test, ce qui prenait trop
de temps. Elle est remplacée par des références figées :

1. `scripts/make_parity_golden.py` calcule une fois les résultats Python des
   31 cas de `tests/parity_cases.py`. Les tâches (cas × modèle) tournent en
   parallèle, et le résultat est écrit dans `tests/parity_golden/` (31 JSON,
   3,3 Mo, environ 4 min). Il faut le relancer après toute modification du
   moteur Python, éventuellement en filtrant les règles :
   `make_parity_golden.py Above Below`.
2. `tests/test_parity_cpp.py` ne lance que le C++ et compare récursivement aux
   références : mêmes paires, mêmes blocs (mesures, points, faces, OBB, axes,
   zones, rayons), flottants à 1e-9 près. Pour les règles de l'arbre en
   sélection chevauchante, les paires sont comparées sans orientation (§8.2).
3. `test_prefilters_only_remove` (C++ seul) vérifie que les phases large et
   intermédiaire ne font que retirer des paires.

Les 31 cas couvrent les 28 règles et quatre types : un objet, un objet avec
contexte, paire, paire avec contexte. Chacun tourne sur 3 modèles calibrés,
ou sur tous avec `IFCCLASH_PARITY_FULL=1`.

### 5.2 Résultats (un fichier ou un groupe à la fois)

| Contrôle | Résultat |
|---|---|
| Tests unitaires C++ (Catch2), par groupe : geometry, registry, broad, session, ifcview | 5/5 groupes verts, 2 263 assertions |
| `test_parity` : 31 cas, 28 règles | 31/31 |
| `test_prefilters_only_remove` : 16 cas de paires | 16/16 |
| `test_threads_and_session_cache_change_nothing` : 20 cas | 20/20, résultats identiques à l'octet |
| Invariance de source (`.ifcview` Duplex Architecture × Mechanical, règles de l'arbre) | identique, 0 `prefilter_lost_clash` |
| Robustesse du cache : `.ifcview` absent, corrompu, en v6, plus ancien que l'IFC | repli correct, ou `ConfigError` en `require` |

Avant la fin du portage, Volume avait aussi été validé sur les 107 modèles
calibrés et le Duplex, et les règles de l'arbre sur 22 modèles et le Duplex.

### 5.3 Copies C++ des tests (`tests/cpp_port/`)

Les 4 fichiers de tests calibrés sont copiés en entier, toutes classes et toutes
règles :

- `test_Rule_IFC_Test_Model` ;
- `_New` ;
- `_OneObject` ;
- `_Complete`.

Les copies passent par toute la chaîne : `RuleFile`, sélection IDS,
orchestrateur, puis C++. Elles tournent avec `IFCCLASH_ENGINE=cpp`, sans repli
possible vers Python.

| Copie | Résultat C++ | Original Python |
|---|---|---|
| `test_cpp_Rule_IFC_Test_Model` (92) | 87 réussis, 2 skip, 3 xfail (1 min 28) | identiques |
| `test_cpp_Rule_IFC_Test_Model_New` (26) | 26/26 (18 s) | identique |
| `test_cpp_Rule_IFC_Test_Model_Complete` (20) | 20/20 (12 s) | identique |
| `test_cpp_Rule_IFC_Test_Model_OneObject` (18) | 14 réussis, 4 échecs `test_suzanne` | les mêmes 4 échecs (§8.1) |

## 6. Benchmark (`scripts/benchmark_engines.py`) et optimisations

### 6.1 Protocole

- **Maquettes** : Duplex Architecture (source) contre Duplex Mechanical (cible),
  d'IfcSampleFiles. Les `.ifcview` v19 sont ceux produits par BonsaiViewer.
- **Sélection** : 100 éléments par côté, pris régulièrement le long de chaque
  fichier (`--max-elements 100`). Sur le Duplex complet (286 × 524),
  Intersection2 prend à elle seule plus de 13 min en C++.
- **Paramètres** : ceux du premier cas de parité de chaque règle
  (`tests/parity_cases.py`).
- **Sélections par type de règle** :
  - règles d'un objet : les 200 éléments ;
  - règles de paires : 100 × 100 paires possibles ;
  - règles à contexte : les mêmes, avec les 200 éléments comme contexte.
- **Isolement** : chaque exécution tourne dans un processus séparé, limité à
  10 min.
- **Mesures** :
  - « froid » = nouvelle Session (parse et conversion compris), soit le coût
    d'une règle seule ;
  - « chaud » = la même règle relancée dans la même Session, soit le coût
    d'une règle de plus dans un RuleFile.

Le rapport complet est dans `doc/benchmark_engines.md`. La mesure avant
optimisation est dans `doc/benchmark_engines_avant_optimisation.md`.

### 6.2 Résultats

**Les 3 moteurs donnent les mêmes résultats sur les 26 règles qui finissent**
(mêmes éléments ou paires, même nombre de résultats).

| Règle | Python | C++ froid avant | C++ froid après | C++ chaud avant | C++ chaud après |
|---|---|---|---|---|---|
| Volume | 3.50 s | 0.73 s | 0.84 s | 1.4 ms | 2.5 ms |
| Area | 3.46 s | 0.73 s | 0.82 s | 1.4 ms | 1.9 ms |
| TopOrBottomSurface | 7.67 s | 2.67 s | 1.87 s | 1.71 s | 0.89 s |
| LateralSurface | 3.43 s | 1.01 s | 1.03 s | 1.8 ms | 5.7 ms |
| ProjectedSurface | 3.86 s | 1.15 s | 1.04 s | 0.19 s | 0.05 s |
| ObbHigh | 5.05 s | 3.40 s | 1.31 s | 2.73 s | 2.7 ms |
| ObbLength | 5.06 s | 3.40 s | 1.37 s | 2.66 s | 2.5 ms |
| Orientation | 5.09 s | 3.42 s | 1.38 s | 2.70 s | 5.5 ms |
| OneObjectFace | 6.17 s | 1.48 s | 1.50 s | 0.50 s | 0.50 s |
| Intersection | 0.69 s | 0.90 s | 0.88 s | 0.03 s | 0.03 s |
| Clearance | 0.76 s | 0.90 s | 0.90 s | 0.05 s | 0.06 s |
| Collision | 0.69 s | 0.86 s | 0.84 s | 3.2 ms | 3.9 ms |
| Intersection2 | 4.79 s | 5.17 s | 4.49 s | 4.21 s | 3.79 s |
| Above | 67.39 s | 54.45 s | 7.38 s | 54.38 s | 0.83 s |
| Below | 66.93 s | 55.00 s | 7.06 s | 53.41 s | 0.48 s |
| OBB_Above | 5.42 s | 3.64 s | 1.71 s | 2.88 s | 0.30 s |
| OBB_Below | 5.26 s | 3.60 s | 1.57 s | 2.84 s | 0.19 s |
| OBB_Front_And_Back | 5.32 s | 3.69 s | 1.68 s | 2.93 s | 0.28 s |
| OBB_Custom | 5.92 s | 4.12 s | 1.90 s | 3.43 s | 0.51 s |
| AngleBetween | 5.14 s | 3.38 s | 1.49 s | 2.64 s | 0.06 s |
| ClearanceAxisToAxis | > 600 s | > 600 s | > 600 s | > 600 s | > 600 s |
| TwoObjectsFace | 228.58 s | 6.92 s | 6.91 s | 5.94 s | 5.88 s |
| SurfaceRecover | 8.80 s | 5.49 s | 3.29 s | 3.90 s | 1.10 s |
| ClearanceForDoors | 214.79 s | 12.01 s | 12.60 s | 9.98 s | 10.41 s |
| Ray_Check | 363.89 s | 4.21 s | 4.15 s | 2.60 s | 2.58 s |
| DirectView | > 600 s | > 600 s | > 600 s | > 600 s | > 600 s |
| FreeSpace | 8.26 s | 4.20 s | 4.21 s | 2.58 s | 2.59 s |
| Alignement | 3.77 s | 3.49 s | 3.49 s | 2.75 s | 4.3 ms |

Totaux sur ces 26 règles :

| | Python | C++ froid | C++ chaud |
|---|---|---|---|
| Avant optimisation | 1 036 s | 190 s | 165 s |
| **Après optimisation** | 1 040 s | **76 s (×14)** | **31 s (×34)** |

Le `.ifcview` donne aussi des résultats identiques sur les 26 règles. Il ne
fait gagner du temps que là où la phase large écarte des éléments avant leur
conversion :

- **Intersection et Collision** : environ −46 % en froid (0,88 s → 0,47 s et
  0,84 s → 0,45 s). Sur cet échantillon de 100 × 100, plus clairsemé que le
  Duplex complet, beaucoup d'éléments ne sont jamais triangulés.
- **Clearance** : pas de gain. Sa marge de 0,5 m garde presque tous les
  éléments.
- **Autres règles** : écart de −6 % à +6 %, c'est-à-dire du bruit. Elles ont
  besoin du B-Rep de chaque élément pour les OBB, les faces ou les mesures, et
  le `.ifcview` ne le fournit pas.

### 6.3 Les optimisations

Le premier benchmark montrait que le C++ gagnait peu sur les règles à OBB, et
pas du tout sur Above et Below. Ces règles passent leur temps dans OCCT, qui
fait les mêmes appels en C++ qu'en Python :

- **Maillage à 0,01 m pour l'OBB** : 2,65 s sur 3,05 s pour ObbHigh.
- **Faces visibles d'Above et Below** : une grille de 2 500 rayons par élément.
  Chaque rayon rechargeait la forme entière (`Init(forme, rayon)`), pour un coût
  en rayons × faces. Un `IfcFlowMovingDevice` de 2 818 faces représentait 7
  millions de tests et 3,5 s. Au total, 65,5 s sur 71 s.
- **Rien n'était gardé entre deux exécutions** : le chaud valait le froid.

Trois changements, sans modifier les résultats :

1. **Cache de session des données par élément.**
   `GeometryProvider::derived(clé, tag, calcul)` garde, pour toute la Session,
   le B-Rep maillé et son OBB (`ElementGeometry::meshed_brep()`) ainsi que les
   faces visibles par direction (`ElementGeometry::visible_faces(dir)`).
   - **Règles concernées** : ObbHigh, ObbLength, Orientation, Above, Below,
     OBB_*, AngleBetween, ClearanceAxisToAxis, SurfaceRecover et Alignement.
   - **Forme maillée** : la forme partagée est la forme maillée, comme en
     Python où l'OBB maille la forme en place avant les autres mesures. Les
     règles ne font que la lire.
   - **NEW_OBB d'OBB_Custom** : il reprend l'OBB en cache, identique à celle
     que Python recalcule sur la forme déjà maillée.
2. **Calcul parallèle par élément.** La phase fine des règles d'un objet et le
   calcul des données par élément des règles de paires se répartissent sur les
   threads de la Session (`rule_threads`, 0 = tous les cœurs).
   - **Seules les règles qui le déclarent** (`RuleBase::parallel_safe`) en
     profitent. Elles ne lisent que la géométrie : pas de requête IfcParse, pas
     d'arbre de rayons. ClearanceForDoors, les règles de faces et les règles à
     contexte restent séquentielles.
   - **Résultats inchangés** : chaque verdict est écrit à l'index de son
     élément.
   - **Annulation et progression** : elles restent gérées par le thread
     appelant.
3. **Forme chargée une fois pour ses 2 500 rayons.**
   `BRepIntCurveSurface_Inter::Init(forme, rayon, tol)` équivaut à
   `Load(forme, tol)` suivi de `Init(courbe)`. `Load` est maintenant fait une
   seule fois par élément : mêmes faces, même ordre, mêmes intersections.

**Validation**, avec `tests/test_parity_cpp.py`, 64 tests verts en 13 min (avant l'ajout du second cas ClearanceAxisToAxis, §8.7) :
- 30 cas de parité ;
- 15 vérifications que les préfiltres ne font que retirer des paires ;
- 19 tests `test_threads_and_session_cache_change_nothing` : avec tous les
  threads, en séquentiel (`rule_threads=1`) et relancés depuis le cache de
  Session, les résultats JSON sont **identiques à l'octet**.

### 6.4 Lecture

- **Above et Below** passent de 54 s à 7 s en froid (×9 face à Python) et à
  moins d'1 s en chaud (×80 à ×140).
- **Règles à OBB** : ×3 à ×4 en froid face à Python. En chaud, elles tombent
  à quelques millisecondes, ou quelques centaines de millisecondes pour les
  règles de zones.
- **Règles de faces et à contexte** : le C++ était déjà très en avance.
  TwoObjectsFace va ×33 plus vite, ClearanceForDoors ×18 et Ray_Check ×87.
- **Règles de l'arbre** (Intersection, Clearance, Collision) : une règle seule
  coûte autant qu'en Python, le temps allant à la triangulation. Elles sont ×13
  à ×170 plus rapides en chaud.
- **Intersection2** n'est pas accélérée (4,5 s contre 4,8 s). Le temps va aux
  `BRepAlgoAPI_Common` entre solides, le même code OCCT qu'en Python. Paralléliser
  ces booléens demanderait de vérifier qu'OCCT ne modifie pas les arguments
  partagés (mode non destructif).
- **ClearanceAxisToAxis et DirectView** dépassent 10 min dans les trois moteurs.
  - ClearanceAxisToAxis, avec le cas de parité (`Fallback`, ratio de
    linéarité 1,5), mesure presque toutes les paires d'un bâtiment peau à
    peau (`BRepExtrema_DistShapeShape`, environ 73 ms par paire), sans
    filtrage spatial : 10 000 paires.
  - DirectView lance 10 rayons par paire contre le contexte.
  - Ces deux règles n'ont pas été relancées après optimisation : leur partie
    lente n'est pas touchée.
  - Après la correction de ClearanceAxisToAxis (§8.7), le même cas avec
    `search_radius = 2 m` prend 78 s en C++ et 83 s en Python, avec 157
    résultats identiques. Le test des boîtes évite la distance exacte pour
    les paires lointaines.

## 7. Problèmes rencontrés et corrigés

1. **Corruption du tas à l'ouverture d'un IFC.** Les classes d'IfcParse
   dépendent des macros de compilation d'IfcOpenShell. Il faut
   `IFOPSH_WITH_ROCKSDB` (plus OpenCASCADE et CGAL), comme le paquet
   conda-forge : c'est fixé dans le CMake (`IFCCLASH_IFCOPENSHELL_DEFINITIONS`).
2. **Piège C++20 dans le batch.** `std::pair<express::base, …>` se compare via un
   `operator<=>` synthétisé, et `express::base` se convertit implicitement en
   `bool` : toutes les paires étaient « égales ». Une seule paire sortait au lieu
   de 491. Corrigé par un comparateur explicite.
   Les tests de session ne le voyaient pas (une seule paire par modèle) ; le test
   d'invariance sur le Duplex l'a révélé.
3. **Lenteur par paire.** Chaque requête de l'arbre reconstruit ses ensembles et
   lance ses threads. Une requête par lot divise le temps chaud par 2 à 20.
4. **Incertitude du `.ifcview` trop pessimiste.** Un terme de flèche angulaire
   proportionnel à la taille de l'élément doublait les candidates. La flèche
   linéaire suffit : le mailleur la respecte toujours.
5. **`W.Triangulation` dans `CustomOBB.py`.** Cette classe n'existe pas, le nom
   correct est `W.triangulation`. Python 3.14 n'évalue plus les annotations à la
   définition des fonctions et masquait l'erreur ; elle casse tout import sous
   3.12. Corrigé (2 annotations).
6. **Arrondis de numpy.** Pour OneObjectFace et les règles d'axes, les écarts
   étaient de l'ordre de 1e-16, mais suffisants pour basculer un test
   d'intersection. OpenBLAS calcule les produits scalaires avec des FMA, dans
   un ordre qui lui est propre. `np.sum` fait une somme par paires, et `einsum`
   a son propre ordre. `geometry/Numpy.h` reproduit ces formes exactement.
7. **Préfiltres OBB de Python.** Dans Above, Below et Intersection2, le test
   OBB de Python fait partie du verdict. En C++, il était seulement dans la
   phase intermédiaire, donc avec `prefilter=False` des paires en plus
   sortaient. Il est maintenant repris dans la phase fine.
8. **Paramètres `null`.** Les paramètres structurés (`FaceSelection`,
   directions) acceptent `null`, comme en Python.

## 8. Constats sur le code existant

1. **Volume de Suzanne dépendant de l'environnement.** Le maillage est le même
   (514 sommets, 978 triangles), mais le volume vaut 0,59 m³ en pip/OCCT 7.8 et
   2,38 m³ en conda/OCCT 8. Suzanne est un maillage ouvert : son volume signé
   dépend de l'origine du repère local, et les deux builds d'IfcOpenShell ne
   placent pas les sommets dans le même repère. `get_volume` le prévient
   (« unpredictable » pour un non-manifold). Le C++ reproduit la valeur de son
   environnement à 1e-15 près. Le test `test_suzanne` est donc fragile : il est
   calé sur un build.
2. **Orientation non déterministe des paires.** Quand un élément est à la fois
   source et cible, l'arbre Python teste la paire dans l'orientation donnée par
   son parcours, et la distance et les points en dépendent. Le C++ suit l'ordre
   de la source ; le test de parité revérifie ces paires une à une.
3. **Ordre non déterministe dans Alignement.** Python prend les éléments dans
   l'ordre de l'itérateur multi-thread d'IfcOpenShell, qui change d'une
   exécution à l'autre. Or les germes de regroupement en dépendent. Le C++ suit
   l'ordre de la sélection, ce qui est déterministe. Les modèles de référence
   ne sont pas sensibles à cet ordre.
4. **OBB_Custom, `expand_sides`.** Python affecte le `None` renvoyé par
   `expand_sides`, puis échoue. Le C++ applique l'agrandissement en place, qui
   est l'intention du code.
5. **ClearanceForDoors en IFC2x3.** `get_door_operation_type` lit
   `IfcDoorPanelProperties.OperationType`, un attribut qui n'existe pas (c'est
   `PanelOperation`), et Python lève une erreur. Le C++ ignore cette source.
6. Les 3 bogues calibrés documentés en `expectedFailure` (Intersection aveugle à
   1 mm, solides coïncidents) sont reproduits à l'identique par le C++. C'est
   attendu : il utilise le même arbre.
7. **ClearanceAxisToAxis, corrigée le 2026-11-09.** Le calcul était conforme
   à l'algorithme documenté, mais la règle ne faisait pas ce que sa
   documentation promettait dès qu'une sélection contenait plus de deux
   objets.

   **Ce qui sortait à tort**, sur un réseau mis à la fois en source et en
   cible :
   - un prolongement colinéaire, sorti « trop proche » avec un écart nul ;
   - tout réseau sans rapport, sorti « trop loin » ;
   - les tuyaux extérieurs d'une nappe correcte (0,30 m), sortis « trop
     loin » ;
   - chaque paire, sortie deux fois.

   Sur l'exemple « nappe à 15 cm » de la documentation : 14 résultats pour 0
   défaut. Sur l'exemple « coaxialité d'un raccord » : 8 faux défauts autour du
   vrai.

   **La correction**, portée dans les deux moteurs et en parité :
   - **vis-à-vis :** en mode Perpendicular, seuls les segments qui se font
     face sur une longueur (recouvrement des projections supérieur à 1e-6 m)
     sont comparés ;
   - **voisin le plus proche :** « trop proche » est vérifié sur toutes les
     paires, « trop loin » seulement entre chaque source et sa cible la plus
     proche ;
   - **nouveau paramètre `search_radius` :** une paire mesurée au-delà n'est
     pas comparée. En `Fallback`, les boîtes sont testées d'abord, ce qui
     évite la distance peau à peau pour les paires lointaines ;
   - **paires non orientées :** chaque paire ne sort qu'une fois, dans sa
     première orientation ;
   - **bissectrice :** elle est prise après avoir remis les deux axes dans le
     même sens. Avec deux axes quasi parallèles de sens opposés (le signe d'un
     axe d'OBB est arbitraire), elle était perpendiculaire aux tuyaux, et
     l'« écart » devenait la distance le long des axes.

   **Côté C++**, `PairRuleBase::narrow_whole_run` permet à une règle de voir
   toutes les paires candidates en un seul `narrow_batch`, dans l'ordre des
   boucles Python.

   **Tests :**
   - 9 tests ajoutés à `test_UnitRule_ClearanceAxisToAxis.py` (réseaux,
     doublons, rayon, bissectrice, recouvrement) ; 31 tests passent sur les
     deux moteurs ;
   - 4 attentes mises à jour, qui figeaient l'ancien comportement (Duplex :
     poutres, escaliers, colinéaires ; liste des paramètres) ;
   - références de parité régénérées, plus un cas Perpendicular avec
     `search_radius`.

## 9. Limites et reste à faire

- **États d'affichage** (`Display_Input`, `Display_Result`) : les géométries
  d'affichage émises par `compute()` ne sont pas portées. `cpp_backend` lève
  `Unsupported` et l'orchestrateur repasse sur Python. FreeSpace ne remplit
  pas non plus les placements trouvés : le verdict est porté, mais pas la
  géométrie du placement.
- `.ifcview` : pas d'écriture (`write_cache` signale un avertissement), pas de
  contrôle du hash du manifeste. Via l'orchestrateur, le cache est désactivé par
  défaut (`IFCCLASH_GEOMETRY_CACHE=off`, à passer à `auto` pour l'activer).
- Parallélisme (étape 7) : partiel. La phase fine des paires reste séquentielle.
- `ViewerSource` (étape 8) : non fait.
- DirectView est très lente sur des sélections denses dans les trois
  moteurs (§6.4), comme ClearanceAxisToAxis en `Fallback` sans
  `search_radius`. Intersection2 n'est pas accélérée (booléens OCCT).
- La phase fine de ClearanceAxisToAxis (distances peau à peau) reste
  séquentielle ; elle pourrait être répartie sur les threads.
- Le plugin IfcConvert `geometry.ifcview` ne se lie pas dans `BUILD/` (son
  `libzstd.a` système n'est pas compilé en PIC). Les `.ifcview` du benchmark
  sont ceux déjà produits par BonsaiViewer.
- Packaging scikit-build-core non fait : le module est construit par CMake seul.
- Étape 0 de la SPEC (imports relatifs, découpage de `clash_utils.py`) non
  faite.

## 10. Fichiers

Nouveaux : `engine/` (moteur, tests C++, lecteur `.ifcview`),
`ifcclash_plus/engine/` (backends Python, module compilé ignoré par git),
`tests/test_parity_cpp.py`, `tests/parity_cases.py`, `tests/parity_golden/`,
`scripts/make_parity_golden.py`, `tests/cpp_port/` (copies des tests),
`scripts/benchmark_engines.py`, `doc/benchmark_engines.{md,json}`,
`doc/benchmark_engines_avant_optimisation.{md,json}`, ce rapport.

Modifiés : `orchestrator.py` (choix du backend, repli, `IFCCLASH_ENGINE`),
`registry.py` (champ `implementation`, 28 règles dans `CPP_RULES`), `RuleClass.py` (fermeture des sessions
à la fin d'un RuleFile), `CustomOBB.py` (annotation),
`environment.yml`, `conda/meta.yaml`, `.gitignore`.

## 11. Relancer

```bash
conda activate ifcclash_cpp
cmake -S engine -B build/engine -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build build/engine
./build/engine/engine_tests "[session]"
PYTHONNOUSERSITE=1 python scripts/make_parity_golden.py      # après une modification du Python
PYTHONNOUSERSITE=1 python -m pytest tests/test_parity_cpp.py -q
PYTHONNOUSERSITE=1 python -m pytest tests/cpp_port/test_cpp_Rule_IFC_Test_Model.py -v
PYTHONNOUSERSITE=1 python scripts/benchmark_engines.py --max-elements 100 --output doc/benchmark_engines.md
```

`IFCCLASH_ENGINE=python` force le moteur de référence, `IFCCLASH_ENGINE=cpp`
force le C++ sans repli.
