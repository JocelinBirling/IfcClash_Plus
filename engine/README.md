# libifcclash_engine — le moteur C++

Mise en œuvre de [SPEC_OptimisationInCPP.md](../SPEC_OptimisationInCPP.md) :
étapes 1 et 2 de l'ordre de migration (le prototype) et lecture des `.ifcview`
de l'étape 6. Bilan : [Rapport_PortageCPP.md](../Rapport_PortageCPP.md).

## Build

Dans l'environnement conda de [environment.yml](../environment.yml), où un seul
OCCT (8.0.1) est partagé par pythonocc-core, ifcopenshell et le moteur :

```bash
conda activate ifcclash_plus
cmake -S engine -B build/engine -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/engine
```

Le module Python `_ifcclash_engine` est écrit dans `ifcclash_plus/engine/`.

Tests C++ (Catch2), un groupe à la fois :

```bash
./build/engine/engine_tests "[session]"
```

Parité Python / C++, copies C++ des tests des règles portées, benchmark :

```bash
PYTHONNOUSERSITE=1 python -m pytest tests/test_parity_cpp.py -v
PYTHONNOUSERSITE=1 python -m pytest tests/cpp_port/test_cpp_Rule_IFC_Test_Model.py -v
PYTHONNOUSERSITE=1 python scripts/benchmark_engines.py --output doc/benchmark_engines.md
```

## Point de vigilance du build

Les classes d'IfcParse changent de taille selon les macros de compilation
d'IfcOpenShell (`ifcopenshell::file` contient un stockage rocksdb). Les
définitions `IFOPSH_WITH_ROCKSDB IFOPSH_WITH_OPENCASCADE IFOPSH_WITH_CGAL`
(cache CMake `IFCCLASH_IFCOPENSHELL_DEFINITIONS`) correspondent au paquet
conda-forge 0.9.0post1. Une erreur ici corrompt le tas dès l'ouverture d'un IFC.

## Organisation

| Dossier | Contenu |
|---|---|
| `api/` | `Session`, `RunRequest`, `RunResult`, `CancelToken`, `ProgressSink`, `catalogue_json` — le seul en-tête public |
| `registry/` | `RuleSpec` (paramètres par pointeur de membre, validation, export catalogue), `Registry`, `register_all_rules` |
| `pipeline/` | `ElementPipeline`, `PairPipeline`, `SetPipeline`, phase large (BVH OCCT `BVH_BoxSet` + `BVH_PairTraverse`), statistiques |
| `rules/` | les 28 règles : un `.cpp` par règle ou par famille (OneObject, Directional, Axis, Face, Context, Alignement…) |
| `geometry/` | algorithmes purs : mesures de maillage, `Obb`, `Faces`, `Triangles`, `Geos` (API C de GEOS), `Numpy.h` (ordre d'arrondi de numpy/OpenBLAS) |
| `provider/` | `GeometryProvider`, `CachePolicy` |
| `sources/` | `GeometrySource`, `IfcSource` (IfcParse + IfcGeom : maillages, B-Rep, requêtes IFC, arbre de rayons), `IfcClashTree`, `ifcview/IfcViewSource` (+ lecteur `third_party/`, LGPL v3) |
| `core/` | `ElementKey`, `ElementBoxes`, `Mesh`, `ResultRecord`, diagnostics |
| `triang/` | les règles `_triang` sur les seuls triangles du `.ifcview` (`triang/README.md`) |
| `bindings/` | pybind11 |
| `tests/` | tests unitaires C++ |

## Parité des règles de l'arbre

En Python, Intersection, Clearance et Collision interrogent l'arbre de clash
d'IfcOpenShell (backend `opencascade.trianglebvh`). Le moteur C++ pose ses
phases large et intermédiaire devant ce même arbre :
le verdict, la distance et les points viennent du même code. La phase fine
envoie toutes les paires candidates en une seule requête de l'arbre
(`narrow_batch`) ; un clash trouvé hors des candidates lève le diagnostic
`prefilter_lost_clash` (préfiltre non conservatif). Les volumes des
phases large et intermédiaire reprennent les marges de l'arbre (1e-3 par
boîte, plus la clearance d'un côté) : elles n'éliminent que des paires que
l'arbre rejetterait de toute façon.

Une paire rencontrée deux fois (élément présent dans la source et dans la
cible) n'est testée qu'une fois, comme dans l'arbre. Son orientation suit
l'ordre de la source. Côté Python, elle dépend de l'ordre de parcours de
l'arbre : le test de parité compare alors des paires non orientées.

## Cache de session et threads

- `GeometryProvider::derived` garde, pour toute la Session, les données
  dérivées par élément : le B-Rep maillé et son OBB
  (`ElementGeometry::meshed_brep()`), et les faces visibles par direction
  (`ElementGeometry::visible_faces()`). Elles sont partagées entre règles et
  exécutions, en lecture seule.
- Les règles qui ne lisent que la géométrie déclarent `parallel_safe()`. Leur
  phase fine (règles d'un objet) ou leurs `element_data` (règles de paires) se
  répartissent alors sur `SessionOptions::rule_threads` threads, tous les cœurs
  par défaut.
- Les résultats ne dépendent ni du nombre de threads ni du cache. C'est vérifié
  par `test_threads_and_session_cache_change_nothing`.

## Parité avec Python

Les références Python sont figées dans `tests/parity_golden/`. On les
régénère avec `scripts/make_parity_golden.py` après toute modification du
moteur Python. `tests/test_parity_cpp.py` ne lance que le C++ et compare à
1e-9 près. Les cas sont définis dans `tests/parity_cases.py`.

## Ce qui n'est pas encore fait

- États d'affichage (`Display_Input` / `Display_Result`) : restent en Python.
- `.ifcview` : lecture faite (boîtes et OBB des phases large et intermédiaire,
  repli par élément, fraîcheur par mtime). Pas d'écriture (`write_cache`
  ignoré) ni de vérification du hash du manifeste.
- Parallélisme de la phase fine des paires (étape 7), `ViewerSource` (étape 8).
- Packaging scikit-build-core : le module est construit par CMake seul.
