# Spécification : Règles Must — focus de regroupement (AbsoluteOrRelativeChecking)

Statut : implémenté
Date : 2026-10-13
Portée : `ifcclash_plus/RuleClass.py`, `ifcclash_plus/serialization.py`,
`tests/test_structure_AbsoluteOrRelativeChecking.py`, `tests/test_Rule_AbsRel.py`

---

## 1. Problème

La vérification absolue ou relative (Must rule, doc/Rule.md) devait
permettre, après regroupement des résultats d'une règle, de comparer
un nombre d'éléments ou une quantité sommée à un seuil. L'état
d'origine ne le permettait pas :

- `AbsoluteChecking.eval_check` et `RelativeChecking.eval_check`
  appelaient `number()` / `quantity()` sans le `GroupResult` : tout
  Must rule plantait avant la moindre comparaison ;
- les quantités n'étaient pas sommées (`self.element_number = +value`,
  plus unaire) et le focus target lisait un ensemble inexistant
  (`sourcetarget_set_set`) ;
- le câblage était cassé des deux côtés : `run_abs_or_rel()` appelait
  `run()` sans la liste de groupes (règles 1-objet) ou
  `run_grouping(groupby)` avec un argument non attendu (règles
  2-objets) ;
- le regroupement, quand il a été réparé, était figé « un groupe par
  objet source » : le besoin couvre plusieurs granularités — un
  groupe par objet (« chaque espace doit avoir 2 fenêtres »), par
  objet cible, ou les regroupements de la règle elle-même (« par
  étage ») ;
- les valeurs de propriété peuvent arriver sous des formes non
  numériques : un nombre en chaîne (`"2.5"`) ou du texte pur.

## 2. Choix retenu

Une seule classe `AbsoluteOrRelativeChecking`, où **le type choisit
le check** et **le focus choisit le regroupement**.

| Paramètre | Valeurs | Effet |
|---|---|---|
| `type` | `"Absolute_Number"`, `"Absolute_Quantity"`, `"Relative_Number"`, `"Relative_Quantity"` | `eval_check` dispatche vers le check absolu (préfixe `Absolute`) ou relatif (préfixe `Relative`) ; `_Number` compte les éléments des ensembles, `_Quantity` somme la propriété `quantity_pset` / `quantity_prop` |
| `focus` | `"source"`, `"target"`, `"by_grouping"` | Un groupe par objet source, un groupe par objet cible, ou les groupes du grouping classique de la règle |

Les approches envisagées :

| Approche | Verdict | Motif |
|---|---|---|
| Deux classes (`AbsoluteChecking`, `RelativeChecking`) | Remplacée | Le `@todo` d'origine le demandait : le type suffit à choisir la fonction, une seule classe évite la duplication et simplifie la sérialisation. Les anciens noms restent lus au désérialisation. |
| Un champ `groupby` / `groupby_method` séparé du focus | Remplacée | Un seul paramètre `focus` porte toute la sélection du regroupement ; `groupby_method` (jamais fonctionnel) est retiré. |
| Réutiliser `run_grouping` systématiquement | Rejetée comme défaut, retenue comme `focus="by_grouping"` | Le grouping classique (facettes `select_grouping`) est une fonctionnalité séparée ; il devient une option explicite du Must, pas son comportement par défaut. |
| Une règle de pairing topologique (par ex. `InStorey`) | Écartée pour le regroupement | Elle fige la granularité dans le pairing : un critère de plus exigerait une nouvelle règle. Le pairing reste réutilisable, le Must agrège. |

## 3. Conception

### 3.1 Le regroupement (le focus)

`RuleCheck` fournit le regroupement du Must :

- `focus = "source"` : `_group_abs_or_rel("source")` — un groupe par
  **objet source** ; les cibles de ses résultats vont dans le
  `target_set` du groupe ;
- `focus = "target"` : `_group_abs_or_rel("target")` — un groupe par
  **objet cible** ; ses sources vont dans le `source_set` du groupe ;
- `focus = "by_grouping"` : les groupes viennent du **grouping
  classique de la règle** (`run_grouping`, piloté par son
  `select_grouping` : `ENTITY`, facette `Property` / `Attribute`,
  `SOURCE` / `TARGET`, …). `grouped_result` est remis à zéro avant,
  car le grouping classique accumule. Sans `select_grouping`, aucun
  groupe n'est produit : le check tourne sur une liste vide.

Une règle 1-objet n'a pas de cible : `focus` y vaut `"source"` ou
`"by_grouping"`.

Le regroupement remplace `self.grouped_result` à chaque appel — sauf
`by_grouping`, qui le réinitialise explicitement pour la même raison.

### 3.2 La mesure (l'ensemble mesuré)

Un groupe « par objet focusé » est réduit à sa propre clé : compter
l'ensemble focusé donnerait toujours 1. **L'ensemble mesuré est
l'autre ensemble** :

| focus | Clé du groupe | Ensemble mesuré |
|---|---|---|
| `"source"` | l'objet source | `target_set` (repli `source_set` si le groupe n'a qu'un ensemble — règle 1-objet) |
| `"target"` | l'objet cible | `source_set` (repli `target_set`) |
| `"by_grouping"` | la valeur du grouping classique | l'ensemble **non vide** du groupe (le grouping classique remplit un côté par groupe : les sources dans le groupe de leur classe, les cibles dans le sien) |

Exemple type : pairing `Clearance(IFCWINDOW → IFCSPACE)`,
`focus="target"` — un groupe par espace, ses fenêtres dans le
`source_set` mesuré : « chaque espace doit avoir au moins 2
fenêtres ».

Deux mesures, selon le suffixe du type :

- `_Number` : `number()` compte les éléments des deux ensembles
  (`source_number`, `target_number`) ; le check absolu retient
  l'ensemble mesuré ;
- `_Quantity` : `quantity()` somme la propriété `quantity_pset` /
  `quantity_prop` sur chaque ensemble. `_to_number` accepte toute
  forme de valeur : un nombre tel quel, un nombre écrit en chaîne
  (parsé), tout le reste (texte pur, propriété absente, type non
  convertissable) compte 0.

### 3.3 Les checks

- `absolute_check` (préfixe `Absolute`, « funct 2 ») : l'ensemble
  mesué contre `aim` via `operation` (ex. `">="`, `"=="`) ;
- `relative_check` (préfixe `Relative`, « funct 1 ») : `source_number`
  complété par `source_operation`, `target_number` complété par
  `target_operation`, les deux reliés par `operation` (ex.
  `source_operation="*2"`, `operation=">="` : « deux fois plus de
  sources que de cibles »).

Le verdict est écrit dans `groupresult.abs_or_rel_check`. La
comparaison repose aujourd'hui sur `eval()` de chaînes construites
internes (`operation`, `aim`, `source_operation`…) ; les tests
couvrent `>=`, `>`, `==`, `*2`, `/2`.

### 3.4 Le câblage

`manage_result` exécute le Must **ou** le grouping classique, jamais
les deux : `run_abs_or_rel()` retourne `None` sans check, `True`
sinon. `run_abs_or_rel` dispatche sur `focus` :

```
focus == "by_grouping"  →  grouped_result = [] ; run_grouping()
focus == "target"       →  group_by_target()          (2 objets)
sinon                   →  group_by_source()
```

À noter : `run_exception` s'exécute avant `manage_result` ; les
résultats invalidés par une exception font toujours partie des
groupes et des mesures (aucun filtrage par statut).

### 3.5 Sérialisation

`serialize_abs_or_rel_check` / `deserialize_abs_or_rel_check`
transportent : `check_type`, `focus`, `operation`, `aim`,
`source_operation`, `target_operation`, `quantity_pset`,
`quantity_prop`. Compatibilité : les anciens `"class":
"AbsoluteChecking"` / `"RelativeChecking"` restent acceptés, les
champs manquants retombent sur les défauts.

## 4. Non-buts

- De nouveaux critères du grouping classique (étage, `PartOf`,
  contenance spatiale) : ils enrichiraient `run_grouping`, pas le
  Must. Un grouping « par étage » suppose aujourd'hui un pairing
  topologique (un `IfcBuildingStorey` n'a pas de géométrie).
- Le filtrage des résultats invalidés par les exceptions dans les
  groupes du Must.
- Le remplacement de `eval()` par un parseur d'opérations sûr.

## 5. Tests

- `tests/test_structure_AbsoluteOrRelativeChecking.py` : défauts et
  validation du type, boucle `run()`, mesures (nombres, quantités
  sommées, valeurs en chaîne et texte pur), dispatch du type, checks
  absolu/relatif dans les deux sens de focus, repli 1-objet,
  câblage des deux classes de règles (focus `source`, `target`,
  `by_grouping`, absence de `select_grouping`).
- `tests/test_Rule_AbsRel.py` (maquette Duplex) : pairing
  `Clearance(IFCWINDOW → IFCSPACE)` à 0,10 — « chaque espace doit
  avoir au moins 2 fenêtres » (focus `target`), « la somme des
  `PSet_Revit_Type_Dimensions.Height` des fenêtres > 3 m »
  (`Absolute_Quantity`), grouping par classe d'entité
  (`by_grouping`), et le contenu complet de `grouped_result` sur le
  run réel (check posé avant le run, via `manage_result`).

## 6. Critères d'acceptation

- Un Must rule configuré survit à un run complet : `eval_check` reçoit
  ses groupes, la comparaison est atteinte, le verdict est écrit.
- `focus="source"` produit un groupe par objet source et mesure
  l'ensemble cible ; `focus="target"` est symétrique.
- `focus="by_grouping"` produit les groupes du `select_grouping` de
  la règle, sans les doubler à des appels répétés.
- Une valeur de propriété en chaîne numérique est mesurée ; du texte
  pur ou une propriété absente compte 0.
- Le grouping classique n'est jamais déclenché par un Must dont le
  focus est `source` ou `target`.
- La sérialisation round-trip conserve le type, le focus et les
  opérations.
