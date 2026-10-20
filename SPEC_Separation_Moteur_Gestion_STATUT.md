# STATUT — Déploiement de SPEC_Separation_Moteur_Gestion.md

Note de reprise rédigée en fin de session. À lire AVANT de continuer le
déploiement. La SPEC de référence est `SPEC_Separation_Moteur_Gestion.md`
(voir son tableau « Décisions d'architecture », arbitrage « déclaration
JSON plate »). La méthodologie est rodée : suivre exactement ce qui a été
fait pour les 26 règles.

## Rappel des règles de travail (agent.md)

- Une commande = UN test (un fichier ou un test seul). Jamais la suite
  entière, jamais `tests/test_Rule_display.py` (GUI bloquante).
- Interpréteur : `/home/jocelin/Documents/07 - Programmation/
  IfcOpenshell/Test_IfcOpenshell/.conda/bin/python` (depuis la racine
  du dépôt, les chemins de modèles sont relatifs).
- Jamais de commit git.
- Code en anglais ; specs/doc en français.

## État de l'infrastructure (étapes 1, 2 et 3 de la SPEC : TERMINÉES)

| Brique | État |
|---|---|
| `pipeline.py` | `ResultPipeline` (Exception → Criticity → Actor → Grouping\|Must → Select) + `RuleOutput`. **Fait.** |
| `compute()` à côté de `run()` | **Fait pour les 26 règles.** `run()` = adaptateur selects → compute → pipeline (l'adaptateur remplit le registre d'affichage dans TOUS les états, comme l'ancien `run()` — voir conventions ci-dessous). |
| Dispatch registre | `registry.engine_params(type)` + `compute_from_config(config, sources, targets, context)` : déclaration JSON plate → appel nommé du compute, piloté par `inspect.signature`. Les 26 règles sont migrées ; la garde `NotImplementedError` reste (robustesse), le test dispatch simule une classe non migrée en retirant `compute` temporairement. |
| Format JSON | Déclaration PLATE actée (SPEC). Séparation uniquement côté code. |
| Contrat `ResultInfo` | Mesures (distance, penetration_depth, contact_area, ratio, offset, hit_ratio, angle, volume, area) ; points/faces/obbs appariés ; blocs propres : `axis` (ClearanceAxisToAxis), `raycast` (DirectView), `zone` (ClearanceForDoors), `axes` (Orientation). |
| Étape 4 | **PAS COMMENCÉE** : bascule `RuleFile.run()`/IPC sur l'orchestrateur explicite (l'étape Select du pipeline reçoit les listes d'entrée). |
| Étape 5 | **PAS COMMENCÉE** : nettoyage (supprimer `state`, `update_file_info`, `produce_select`, `RuleCheckComplex`, les adaptateurs `run()`, l'attribut mort `result_fail_source`, la classe `Template` morte, hissage des moteurs en fonctions module — le hissage se fait à l'étape 5). |

## Conventions des règles migrées (à respecter pour la suite)

- `compute()` est pur : pas d'IFC, pas de sélection, pas de
  post-traitement, ne touche ni `self.result`, ni `self.output`, ni le
  registre display. Exceptions documentées : ClearanceForDoors,
  Alignement, DirectView et FreeSpace POSENT leurs params nommés sur
  l'instance au début du compute (leurs helpers lisent la config sur
  l'instance — le nœud reste porteur de config) ; Alignement et
  FreeSpace laissent en plus leur état moteur sur le nœud
  (`alignment` + `_engine_objects/_engine_groups` ; `placements` +
  `_probe_positions`) : les zones d'alignement et les sondes sont des
  données de display de NIVEAU ENSEMBLE, elles ne peuvent pas vivre
  dans les blocs info par-résultat.
- `run()` (adaptateur) remplit le registre display dans TOUS les
  états, exactement comme l'ancien `run()` : le display est un
  consommateur en lecture du registre (`test_structure_DisplayUpdate::
  test_pilot_rules_fill_the_registry` épingle ce comportement en état
  Final). NE PAS regrouper l'enregistrement sur les états Display_*.
  Les helpers `_register_*_display` reconstruisent les items depuis
  les blocs info ; les données d'entrée non portées par les résultats
  (éléments de contexte, faces sélectionnées de la famille FaceCheck,
  solides de zones, éléments ajustés) restent un travail d'adaptateur.
- Les primitives par liste plate d'entités vivent dans `clash_utils` :
  `element_shapes`, `elements_extrem_data`, `elements_obb_data`,
  `add_elements_to_clash_tree`, `add_elements_to_ray_tree`. Motif
  by_file : chaque entité connaît son fichier (`.file`, ifcopenshell
  0.9), grouper par fichier puis itérer.
- `Select.create_list_of_element()` reconstruit `list_of_elements` à
  chaque appel (plus d'accumulation) : un select partagé entre règles
  dupliquait les éléments et quadruplait les paires — corrigé et
  régressé par les 4 tests `test_Rule_TwoObjects` qui partagent leurs
  selects.

## Règles migrées (26/26) — motif : compute + adaptateur + info + tests

| Règle | Fichier de tests compute | Notes |
|---|---|---|
| Volume, Area, TopOrBottomSurface, Orientation | `test_compute_OneObject.py` (13) | |
| LateralSurface, ProjectedSurface, ObbHigh, ObbLength, OBB_Front_And_Back | `test_compute_LotsAB.py` (19) | Calibration empirique (bruit OCCT ~2,5e-3 : deltas 1e-2, bornes des tests écartées du bruit) ; 45CuboidA documente le fix coordonnées monde |
| Above, Below | `test_compute_Above.py` (10), `test_compute_Below.py` (10) | |
| OBB_Above, OBB_Below | `test_compute_OBB_Above_Below.py` (12) | |
| Intersection, Clearance, Collision | `test_compute_TreeClashes.py` (10) | |
| AngleBetween, ClearanceAxisToAxis | `test_compute_Angles.py` (8) | |
| Ray_Check, OBB_Custom | `test_compute_RaysAndCustom.py` (11) | OBB_Custom : `_modification_value` accepte nombre (m) OU « x% » (CustomOBB parse le pourcentage) |
| SurfaceRecover | `test_compute_SurfaceRecover.py` (14) | Bornes min/max_covering ajoutées au registre (engine_params = 5 clés) ; bornes au format paire parsée («absolute»/«relative»), forme sérialisée |
| OneObjectFace | `test_compute_OneObjectFace.py` (11) | `_run_checks`/`_check_pairs` reçoivent la config en namespace |
| TwoObjectsFace | `test_compute_TwoObjectsFace.py` (12) | `_collect_faces(elements, selection, color, register)` : compute → register=False |
| ClearanceForDoors | `test_compute_ClearanceForDoors.py` (11) | Params posés sur l'instance avant `_build_zones` (documenté) |
| Alignement | `test_compute_Alignement.py` (11) | Params posés + état moteur sur le nœud ; `alignment` consommé par les tests adaptateur |
| DirectView | `test_compute_DirectView.py` (11) | Contexte = 3e liste ; ray tree via `add_elements_to_ray_tree` ; rayons reconstruits de `info.raycast` |
| FreeSpace | `test_compute_FreeSpace.py` (12) | LE cas du contrat 3 listes ; `placements` + `_probe_positions` sur le nœud |

## Corrections de la session (hors migration de règles)

1. `Select.create_list_of_element()` : reconstruction à chaque appel
   (l'accumulation quadruplait les paires des règles partageant un
   select — régression des adaptateurs, vérifiée par worktree HEAD :
   le test passait à HEAD). Régressions vertes : Select (16),
   ProduceSelect (6), RuleFile (13), RuleFolder (13), les 4 tests
   `test_Rule_TwoObjects` à selects partagés.
2. `clash_utils.element_shapes` : garde `shape is None` (create_shape
   renvoie None pour un élément sans représentation, ex. IfcProject) —
   conforme au contrat « élément sans géométrie = sauté ».
3. `OBB_Custom` : la conversion float de la session précédente cassait
   le format « x% » ; `_modification_value` distingue nombre (m) et
   pourcentage (chaîne brute, CustomOBB le parse).
4. Tests adaptateur recalibrés pour le fix coordonnées monde (SPEC
   point 3, changement voulu) : `test_Rule_OneObject.py`
   `test_lateral_rule` 5 → 7, `test_projected_rule` 11 → 9.

## Tests rouges PRÉEXISTANTS (ne pas traiter comme des régressions)

- `test_Rule_IFC_Test_Model.py` : `TestOBB_Front_And_Back::
  test_CubeB_Side_45CuboidA`, `TestAngleBetween::
  test_CuboidA_Orient_45Cuboid_45` (vérifiés par worktree sur HEAD).
- `test_UnitRule_OneObjectFace.py::test_distance_above_max_clashes` et
  `test_UnitRule_TwoObjectsFace.py::{test_distance_above_max_clashes,
  test_whole_target_distance_max,
  test_face_vs_face_pairs_only_the_selected_faces}` : ces tests
  attendent qu'un max_distance SEUL produise un clash, contraire à la
  sémantique « rayon de recherche » du code (identique à HEAD,
  vérifié par worktree). À arbitrer avec le développeur : soit
  corriger la sémantique de max_distance (clash au-dessus du max),
  soit recalibrer les tests.

## Dernière validation connue (toutes vertes à l'arrêt, sauf rouges préexistants ci-dessus)

Compute : SurfaceRecover 14/14, OneObjectFace 11/11, TwoObjectsFace
12/12, ClearanceForDoors 11/11, Alignement 11/11, DirectView 11/11,
FreeSpace 12/12, LotsAB 19/19, RaysAndCustom 11/11.
Adapter/unitaires : test_UnitRule_SurfaceRecover 26/26, Alignement
24/24, DirectView 21/21, FreeSpace 12/12, ClearanceForDoors 14/14,
FaceCheck 19/19 ; test_Rule_OneObject 9/9 (recalibré) ;
test_Rule_TwoObjects_TwoElements 11/11 ; test_Rule_TwoObjects : les
4 tests à selects partagés repassés verts un par un (le fichier
entier n'a pas été rejoué d'une traite — un test par commande).
test_Rule_IFC_Test_Model : toutes les classes passées une par une,
seuls les 2 rouges préexistants restent. Structure : Select 16,
ProduceSelect 6, RuleFile 13, RuleFolder 13, ResultPipeline 4,
ResultShape 15, serialization 17, clash_utils 22, registry_dispatch
6, exception 3, AbsRel 8, save_results 6, BooleanRule 24,
DisplayRegistry 15, DisplayUpdate 6 (6/6 après le retour à
l'enregistrement inconditionnel).
Aucune modification non validée en suspens.

## Prochaines étapes (dans l'ordre de la SPEC)

1. **Étape 4** : `RuleFile.run()` devient l'orchestrateur explicite
   (préparer les sélections → `compute` → pipeline → collecter les
   `RuleOutput`) ; basculer l'IPC ; l'étape Select du pipeline reçoit
   les listes d'entrée. Couper l'ancien `run()` juste après (branche
   dédiée, pas de compatibilité longue). Parité stricte de l'export
   JSON (`save_results_to_json`), clé pour clé (critère d'acceptation
   2). Points d'attention connus : parité extend vs replace par règle ;
   « sources non clashées » (`element_state_to_pass=False`) = éléments
   SANS AUCUN résultat ; le registre display reste rempli par les
   adaptateurs tant que le display n'est pas migré en consommateur des
   blocs info (à trancher à l'étape 4 : le display devient
   consommateur des résultats, voir SPEC « Display »).
2. **Étape 5** : nettoyage — `state`, `update_file_info`,
   `produce_select`, `RuleCheckComplex`, adaptateurs `run()`,
   `result_fail_source`, classe `Template`, hissage des moteurs en
   fonctions module.

## Pièges rencontrés (ne pas reproduire)

- **ifcopenshell 0.9** : une entité ne garde PAS son fichier en vie
  (cache `self.files[model]` à côté des entités). Un itérateur avec
  `include` exige des IfcProduct (ValueError sinon — les listes
  d'entrée sont des produits, par contrat). `kernel.create_shape` rend
  None pour un élément sans représentation (garde dans
  `element_shapes`).
- **Select partagé entre règles** : `create_list_of_element`
  reconstruit maintenant à chaque appel — ne jamais réintroduire
  d'accumulation.
- **Registre display** : l'adaptateur remplit dans TOUS les états
  (parité ancien `run()`, test DisplayUpdate l'épingle) — ne pas
  regrouper sur Display_*.
- **OCCT** : bruit ~2,5e-3 sur les mesures OBB (calibrer avec delta
  1e-2 et écarter les bornes des tests du bruit) ; axes d'OBB
  arbitrairement permutés.
- **Splice par bornes de classes** : vérifier la CONTIGUËTÉ (assert
  count == 1 avant/après).
- **Combinateur `or_`** disparu d'ifctester 0.9 : OR via
  `ids.Attribute(value=Restriction(options={"enumeration": [...]}))`.
- **Appel kernel 0.9** : `kernel.create_shape(inst=entity)` rend une
  shape_tuple (`.geometry`), pas un TopoDS direct.
