# Séparation du moteur de règles et de la gestion des règles

Je veux dissocier le **fonctionnement** des règles (le calcul des clashs)
et la **gestion** des règles (préparation des entrées, post-traitement des
résultats, chaînage, orchestration).

Une règle devient une fonction pure : elle reçoit en entrée
`Liste_Objet_Source`, `Liste_Objet_Target` et ses paramètres, et rend en
sortie une liste de résultats. La liste de résultats subit ensuite, hors de
la règle, les exceptions, les filtres (criticity, actor), le grouping et
les Must rules.

## Décisions d'architecture (arrêtées)

| Point | Décision |
|---|---|
| Contrat de la règle | `compute(liste_objet_source, liste_objet_target, *paramètres_de_la_règle, liste_objet_contexte=None) -> list[ClashResult]`. Les paramètres de la règle sont des **propriétés de la fonction** (arguments nommés), chaque type de règle a sa signature propre. La règle ne charge aucun fichier, ne prépare aucune sélection, ne post-traite aucun résultat. |
| Configuration | Le dictionnaire produit par `serialize_rule_check` (`serialization.py`) reste le format canonique **sur disque** (JSON). **Arbitrage** : la déclaration JSON d'une règle reste **plate** et rassemble tout sous la même règle — selects, paramètres moteur et configuration de gestion au même niveau. La séparation moteur/gestion vit uniquement dans le code : la couche de dispatch (`registry.compute_from_config`) extrait la partie moteur et appelle `compute` en nommé ; le `ResultPipeline` lit la partie gestion ; l'orchestrateur lit les selects. |
| BVH | Le tree est construit **par la règle elle-même** à chaque `compute` : contrat minimal, autonome. Un cache partagé par fichier serait une optimisation future, hors périmètre de cette refonte. |
| Entrées | Des listes d'entités ifcopenshell. Chaque entité connaît son fichier (`.file`) : plus besoin de `update_file_info` ni de `dict_elements` par fichier à l'intérieur des règles. |
| Sortie | Une liste de `ClashResult` brute (OneObject, TwoObjects ou Complex). Aucun post-traitement dans la règle : `status` est le verdict du calcul seul. |
| Post-traitement | Un `ResultPipeline` explicite, hors de la règle : Exception → Criticity → Actor → (Grouping \| Must) → Select. Chaque étape : `apply(results, config) -> results`. |
| Orchestration | `RuleFile.run()` devient l'orchestrateur explicite : préparer les sélections → `compute` → pipeline → collecter les `RuleOutput`. |
| Attribut `state` | Supprimé. Le routage `Final` / `Select` / `Display_Input` / `Display_Result` disparaît : la sélection est une étape du pipeline, le display est un consommateur des résultats. |
| Display | La fonction de règle est **agnostique du display**. Les résultats portent eux-mêmes les données nécessaires à la visualisation (blocs `info` : shapes, points, faces, OBB) : on peut recréer le résultat ou le visualiser dans un autre logiciel sans relancer la règle. |
| Compatibilité | Migration sur une branche dédiée : la double voie ne dure que le temps de la migration. L'ancien `run()` peut être coupé dès que `RuleFile` et l'IPC sont basculés ; pas de période de compatibilité longue. |

## Architecture actuelle (constat)

Aujourd'hui, une règle est à la fois définition de données, moteur de
calcul, sélecteur et gestionnaire de résultats :

```
Intersection(wall_select, furniture_select, 0.01)   ← selects + params mêlés
rule.state = "Final"                                 ← routage par attribut
rule.run()
  ├─ select_source.run()      ← la règle prépare ses propres entrées
  ├─ select_target.run()
  ├─ logique de clash         ← le seul vrai « moteur »
  └─ end_rule_action()        ← exceptions + criticity + actor + grouping/must
```

Conséquences :

- une règle est intestable sans charger un IFC et monter un `RuleFile` ;
- le paramétrage sérialisé (config) n'est pas l'entrée explicite du calcul ;
- l'attribut `state` est un hack de routage (`SelectRule` force
  `rule.state = "Select"` avant d'appeler `run()`) ;
- le chaînage en cascade passe par `produce_select()`, collé à la règle ;
- la plomberie `update_file_info` existe uniquement pour distribuer les
  fichiers aux selects logés dans les règles.

## Architecture cible

```
                    ┌─────────────────────────────────────────┐
  IFC files ──► Select (Source / Target / Context)             │  gestion
                    └──────────────┬──────────────────────────┘
                                   ▼
             ┌──────────────────────────────────────┐
             │  compute(sources, targets, params,   │  moteur PUR
             │         context) → list[ClashResult]  │  testable, sans I/O
             └──────────────┬──────────────────────┘
                            ▼
             ResultPipeline (gestion) :
               Exception → Criticity → Actor → Grouping | Must → Select
                            │
                            ▼
             RuleOutput : results (+ selection, + groups)
```

### Contrat du moteur

```python
def compute(liste_objet_source, liste_objet_target, *paramètres_de_la_règle,
            liste_objet_contexte=None) -> list[ClashResult]
```

- `liste_objet_source` : liste d'entités, toujours requise.
- `liste_objet_target` : liste d'entités, règles 2-objets uniquement.
- `paramètres_de_la_règle` : les propriétés propres à la règle, en
  arguments nommés — `tolerance` pour Intersection, `volume_min` /
  `volume_max` pour Volume, etc. Chaque type de règle a sa signature
  propre ; il n'y a pas d'objet config intermédiaire au niveau du code.
- `liste_objet_contexte` : liste d'entités, règles complexes uniquement
  (FreeSpace, et les futures) ; c'est une troisième entrée, jamais un
  select caché dans la règle.
- Sortie : liste de `ClashResult`, `status` = verdict du calcul seul.

Le registre `registry.py` devient le dispatch `type` → fonction
`compute` : il reçoit le dictionnaire de configuration sérialisé et le
traduit en appel nommé (la sérialisation/désérialisation de
configuration branche directement) — c'est `registry.compute_from_config`,
implanté pour les règles migrées. La déclaration reçue reste la
déclaration JSON plate d'une seule règle (voir l'arbitrage
« Configuration » ci-dessus).

### Données de display portées par les résultats

La fonction de règle n'enregistre plus de `DisplayItem` et ne connaît
aucun état `Display_*`. Les données utiles à la visualisation vivent
dans les résultats, via les blocs `info` (`ResultInfo` : shapes,
points, faces, OBB, rayons, zones). Conséquences :

- la visualisation se **recrée** depuis les résultats, sans relancer
  la règle (OCC en local, ou un autre logiciel) ;
- les règles qui ne portent pas encore assez de données dans leurs
  `info` les complètent pendant leur migration — c'est le seul point où
  la refonte touche le contenu des résultats ;
- l'export JSON (`save_results_to_json`) diffuse déjà les blocs
  `info` (`ResultInfo.to_dict`) : le canal vers un logiciel tiers
  existe et reste inchangé.

### Pipeline de gestion des résultats

Le pipeline reçoit la liste de résultats du `compute` et enchaîne les étapes
configurées dans la configuration de la règle (les mêmes données que
aujourd'hui, mêmes clés de sérialisation) :

| # | Étape | Entrée config | Effet sur la liste de résultats |
|---|---|---|---|
| 1 | Exception | `select_exception` | Invalide en place (`status = False`), ne retire rien. Le `BooleanLeaf` devient `compute(exception_config, [source], [target])` par paire. Relation `Same_IfcSystem` : inchangée. |
| 2 | Criticity | `select_criticity` | Étiquette chaque résultat (`criticity`). |
| 3 | Actor | `select_actor` | Étiquette chaque résultat (`actor`). |
| 4 | Grouping \| Must | `select_grouping` \| `abs_or_rel_check` | Grouping : produit `grouped_result`. Must : consomme les résultats individuels, un `ClashResultComplex` par groupe devient la nouvelle liste de résultats (`result_before_abs_or_rel` conservé dans le `RuleOutput`). Grouping et Must restent exclusifs. |
| 5 | Select | (étape de chaînage) | Produit la `selection` du `RuleOutput` pour les règles en aval (`SelectRule`), à partir des `status` des résultats. |

### Sortie d'un nœud : RuleOutput

```python
class RuleOutput:
    results: list[ClashResult]        # après pipeline
    selection: list[entity] | None    # pour le chaînage (étape Select)
    groups: list[GroupResult] | None  # après Grouping/Must
```

L'export JSON (`save_results_to_json`) et l'IPC consomment le `RuleOutput`
sans changement de format.

## Impact par brique

| Brique | Changement |
|---|---|
| `Rules.py` (~26 règles) | `run()` → `compute(sources, targets, *params[, context])` ; les selects quittent les constructeurs ; `geom_settings` reste interne à la règle ; les `DisplayItem` et les fonctions display quittent les règles (données déplacées dans les blocs `info` des résultats). |
| `RuleClass.py` | `end_rule_action`, `run_exception`, `run_criticity`, `run_actor`, `run_grouping`, `run_abs_or_rel`, `produce_select` migrent vers `ResultPipeline` ; `state` et le hack `SelectRule` disparaissent ; `update_file_info` disparaît ; `RuleCheckComplex` (cassé, Rapport.md §3) est supprimé. |
| Selects (`SelectFacet`, `SelectRule`) | Restent : ils deviennent la couche de préparation d'entrées de l'orchestrateur. `SelectRule` consomme la `selection` d'un `RuleOutput` en aval. |
| `serialization.py` | Déjà aligné : la config sérialisée devient l'entrée de `compute`. Ajout d'un chargement « config → règle exécutable » via le registre. |
| `ipc.py` | Quasi inchangé : il pilote déjà par nœuds avec configuration. |
| Display | Consommateur des résultats : il se reconstruit depuis les blocs `info` des `ClashResult` (ou depuis l'export JSON), sans relancer les règles. Les états `Display_*` et `register_display_item` disparaissent des règles. |
| Règles complexes | Le contrat à 3 listes couvre `FreeSpace` sans détour ; `Alignement` (1-objet complexe) n'utilise que `liste_objet_source`. |
| Tests | Chaque règle testable en direct : entités par `by_id()` + `compute` + assertions ; le pipeline testé séparément avec des listes de résultats fabriquées. Plus besoin de `RuleFile` ni de selects pour tester la logique. |

## Points délicats à trancher

1. **Arbres BVH** : décidé — tree par règle (contrat minimal). Un cache
   partagé par fichier reste une optimisation future, hors périmètre.
2. **Complétude des blocs `info`** : chaque règle doit porter dans ses
   résultats les données de display (shapes, points, faces, OBB).
   Certaines règles remplissent déjà leurs `info`, d'autres non :
   l'inventaire se fait pendant la migration, règle par règle, et la
   parité visuelle avec le display actuel valide chaque complétion.
3. **Coordonnées locales** : bug documenté (LateralSurface, Projected,
   Rapport.md §2). À corriger pendant la migration des règles
   concernées, pas avant.
4. **Sémantique du Must** : « les résultats individuels sont consommés,
   le groupe devient le résultat » reste une décision explicite du
   pipeline (étape 4), pas un effet de bord de la règle.
5. **Exceptions relationnelles** : seul `Same_IfcSystem` est implémenté ;
   `Same_Building` / `Same_Storey` / `Same_Space` migrent tels quels
   (stubs), dans l'étape Exception.
6. **Bug connu `run_actor`** (1-objet, Rapport.md §5) : à corriger dans
   l'étape Actor du pipeline pendant la migration, il en devient le
   test naturel.

## Plan de migration incrémentale

| Étape | Contenu | Réversibilité / validation |
|---|---|---|
| 1 | Extraire `ResultPipeline` du contenu de `end_rule_action`, sans changer les signatures. `run()` appelle le pipeline. | Refactor pur ; les tests existants valident l'équivalence. |
| 2 | Ajouter `compute(sources, targets, *params[, context])` à côté de `run()` ; l'ancien `run()` devient l'adaptateur select → compute → pipeline, le temps de la migration seulement. | Nouvelle API testable ; ancien flux intact. |
| 3 | Migrer les règles une par une (mécanique après les 2-3 premières), en migrant leurs tests en parallèle : test du compute sans `RuleFile`, test du pipeline séparé, complétion des blocs `info` pour le display. | Une règle à la fois ; la suite existante reste verte. |
| 4 | Basculer `RuleFile.run()` et l'IPC sur l'orchestrateur explicite ; couper l'ancien `run()` (branche dédiée : pas de période de compatibilité longue) ; le display devient consommateur des résultats. | IPC et export JSON validés sur le nouveau flux. |
| 5 | Nettoyage : suppression de l'adaptateur, de `state`, de `update_file_info`, de `produce_select`, de `RuleCheckComplex` et des stubs morts. | Fin de la double voie. |

Les étapes 1 et 2 apportent déjà la testabilité ; le big-bang n'arrive
jamais.

## Critères d'acceptation

1. Une règle s'exécute et se teste avec uniquement : ses paramètres
   nommés, des listes d'entités, aucun `RuleFile` ni chargement d'IFC.
2. `RuleFile.run()` produit, pour chaque nœud, un `RuleOutput` dont
   l'export JSON (`save_results_to_json`) est identique, clé pour clé, à
   celui du flux actuel (parité stricte, tout écart est un bug).
3. Les exceptions, criticity, actor, grouping et Must rules se configurent
   et se comportent comme aujourd'hui (mêmes clés de sérialisation).
4. Le chaînage en cascade (SelectRule) fonctionne via la `selection` du
   `RuleOutput`.
5. L'attribut `state` n'existe plus ; aucune fonction de règle ne
   référence le display (pas de `DisplayItem`, pas d'état `Display_*`).
6. Un résultat porte assez de données (blocs `info`) pour recréer sa
   visualisation sans relancer la règle, y compris depuis l'export JSON
   dans un autre logiciel.
7. L'IPC et l'export BCF futurs branchent le `RuleOutput` sans adaptation
   de format.
