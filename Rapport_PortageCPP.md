# Rapport — Portage C++ du moteur (SPEC_OptimisationInCPP)

Date : 2026-11-09. Branche : `Switch_Engine` (rien n'est commité).

## 1. Résumé

- Le moteur C++ `libifcclash_engine` (dossier `engine/`) couvre les étapes 1 et 2
  de l'ordre de migration : `Session`, `IfcSource`, `GeometryProvider`,
  registre, `ElementPipeline`, `PairPipeline` avec BVH, bindings pybind11. Il
  porte les règles **Volume, Intersection, Clearance et Collision**.
- La lecture des `.ifcview` (étape 6) est faite : `IfcViewSource`, qui fournit
  les boîtes des phases large et intermédiaire.
- **Parité stricte obtenue** : mêmes paires que Python, règle par règle, sur les
  modèles de `IFC_Test_Model` et sur le Duplex. Les résultats sont identiques
  avec et sans `.ifcview`, et avec et sans préfiltres.
- Les 4 règles basculent sur `implementation: "cpp"` dans le catalogue. Sans
  module compilé (par exemple sous Python 3.14), l'orchestrateur se replie sur
  Python.
- Gains mesurés : Volume ×13. Sur les règles de l'arbre, le premier passage
  coûte autant qu'en Python (conversion de la géométrie), les passages suivants
  dans la même session sont 4 à 60 fois plus rapides. Le `.ifcview` ne fait rien
  gagner sur le Duplex (voir §6).

## 2. Ce qui a été fait, au regard de la SPEC

| Étape SPEC | État |
|---|---|
| 0 — prérequis Python (imports relatifs, découpage de `clash_utils.py`) | **Non fait.** Pas bloquant pour le C++. |
| 1 — squelette + Volume | Fait |
| 2 — `PairPipeline` + Intersection, Clearance, Collision | Fait |
| 3 à 5 — 24 autres règles, `ContextPipeline`, `SetPipeline` | Non fait |
| 6 — `IfcViewSource` | Lecture faite. Écriture du cache et contrôle du hash du manifeste non faits. |
| 7 — parallélisme | Non fait. L'itérateur et l'arbre IfcOpenShell utilisent leurs propres threads. |
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

| Contrôle | Résultat |
|---|---|
| Tests unitaires C++ (Catch2), par groupe : geometry, registry, broad, session, ifcview | 5/5 groupes verts, 2 263 assertions |
| Parité Volume, 107 modèles calibrés + Duplex Architecture et Electrical | 2/2 (16 min) |
| Parité Intersection, Clearance, Collision : 22 modèles calibrés + Duplex Architecture, sélections disjointe et chevauchante, 2 jeux de paramètres par règle | 6/6 |
| Prudence des préfiltres (résultats identiques avec `prefilter=False`) | 6/6 |
| Invariance de source (`.ifcview` Duplex Architecture × Mechanical, 3 règles) | identique, 0 `prefilter_lost_clash` |
| Robustesse du cache : `.ifcview` absent, corrompu, en v6, plus ancien que l'IFC | repli correct, ou `ConfigError` en `require` |
| **Copies C++ des tests** (`tests/cpp_port/`, 63 tests) | voir ci-dessous |

Les copies figent les classes Intersection, Collision, Clearance et Volume de
`test_Rule_IFC_Test_Model.py`, `_New.py` et `_OneObject.py`. Elles passent par
toute la chaîne (`RuleFile`, sélection IDS, orchestrateur, C++), avec
`IFCCLASH_ENGINE=cpp` et sans repli possible vers Python. Comparées
test par test à l'original Python dans le même environnement :

- `test_cpp_Rule_IFC_Test_Model` : 47 réussis + 3 xfail, **identique** à l'original ;
- `test_cpp_Rule_IFC_Test_Model_New` : 11/11, identique ;
- `test_cpp_Rule_IFC_Test_Model_OneObject` : 1 réussi, 1 échec (`test_suzanne`).
  L'**original Python échoue aussi** dans cet environnement (voir §8.1).

La parité complète prend du temps (environ 4 s par modèle et par appel Python).
Par défaut, le test prend un modèle calibré sur cinq.
`IFCCLASH_PARITY_FULL=1` les prend tous, `IFCCLASH_PARITY_HEAVY=1` ajoute les
gros Duplex.

## 6. Benchmark (`scripts/benchmark_engines.py`)

Duplex Architecture (286 éléments) contre Duplex Mechanical (524 éléments),
avec leurs `.ifcview` v19 produits par BonsaiViewer. Le résultat complet est
dans `doc/benchmark_engines.md`.

| Règle | Résultats | Python | C++ froid | C++ chaud | C++ .ifcview froid | Mêmes paires |
|---|---|---|---|---|---|---|
| Volume | 810 | 14,84 s | 1,13 s | 0,00 s | 1,17 s | oui |
| Intersection | 802 | 1,39 s | 1,60 s | 0,33 s | 1,52 s | oui |
| Clearance | 1953 | 1,50 s | 1,31 s | 0,06 s | 1,33 s | oui |
| Collision | 491 | 1,20 s | 1,30 s | 0,02 s | 1,24 s | oui |

« Froid » = nouvelle Session, parse et conversion de la géométrie compris.
C'est le coût de la première règle d'un RuleFile. « Chaud » = la même règle
relancée dans la même Session.

Lecture :

- Python appelle `create_shape` élément par élément, d'où un Volume ×13 en C++.
- Pour les règles de l'arbre, une règle isolée coûte surtout la triangulation
  (environ 1 s), en C++ comme en Python. Le gain vient du cache de session :
  les règles suivantes d'un RuleFile ne paient plus la conversion (×4 à ×60).
- Le `.ifcview` ne fait rien gagner ici. Le Duplex Architecture × Mechanical est
  dense : les paires candidates touchent presque tous les éléments, qu'il faut
  de toute façon trianguler depuis l'IFC pour la phase fine. Son incertitude
  laisse aussi passer un peu plus de paires (1 981 au lieu de 1 600). Le gain
  attendu porte sur des sélections dispersées, où la phase large rejette la
  plupart des éléments.

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
3. Les 3 bogues calibrés documentés en `expectedFailure` (Intersection aveugle à
   1 mm, solides coïncidents) sont reproduits à l'identique par le C++. C'est
   attendu : il utilise le même arbre.

## 9. Limites et reste à faire

- 24 règles restent en Python, ainsi que `ContextPipeline` et `SetPipeline`.
- `IfcSource::brep()` n'est pas implémenté : aucune règle portée n'en a besoin.
- `.ifcview` : pas d'écriture (`write_cache` signale un avertissement), pas de
  contrôle du hash du manifeste. Via l'orchestrateur, le cache est désactivé par
  défaut (`IFCCLASH_GEOMETRY_CACHE=off`, à passer à `auto` pour l'activer).
- `RunMode` : `inputs_only` et `verdicts_and_display` fonctionnent dans
  l'API, mais `cpp_backend` n'utilise que `verdicts` : l'affichage reste produit
  par Python.
- Le plugin IfcConvert `geometry.ifcview` ne se lie pas dans `BUILD/` (son
  `libzstd.a` système n'est pas compilé en PIC). Les `.ifcview` du benchmark
  sont ceux déjà produits par BonsaiViewer. Ce build n'a pas été reconfiguré.
- Packaging scikit-build-core non fait : le module est construit par CMake seul.

## 10. Fichiers

Nouveaux : `engine/` (moteur, tests C++, lecteur `.ifcview`),
`ifcclash_plus/engine/` (backends Python, module compilé ignoré par git),
`tests/test_parity_cpp.py`, `tests/cpp_port/` (copies des tests),
`scripts/benchmark_engines.py`, `doc/benchmark_engines.{md,json}`, ce rapport.

Modifiés : `orchestrator.py` (choix du backend, repli, `IFCCLASH_ENGINE`),
`registry.py` (champ `implementation`), `RuleClass.py` (fermeture des sessions
à la fin d'un RuleFile), `CustomOBB.py` (annotation),
`environment.yml`, `conda/meta.yaml`, `.gitignore`.

## 11. Relancer

```bash
conda activate ifcclash_cpp
cmake -S engine -B build/engine -G Ninja -DCMAKE_BUILD_TYPE=Release && cmake --build build/engine
./build/engine/engine_tests "[session]"
PYTHONNOUSERSITE=1 python -m pytest tests/test_parity_cpp.py -v
PYTHONNOUSERSITE=1 python -m pytest tests/cpp_port/test_cpp_Rule_IFC_Test_Model.py -v
PYTHONNOUSERSITE=1 python scripts/benchmark_engines.py --output doc/benchmark_engines.md
```

`IFCCLASH_ENGINE=python` force le moteur de référence, `IFCCLASH_ENGINE=cpp`
force le C++ sans repli.
