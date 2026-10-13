# Specification : Registre de géométries d'affichage (DisplayItem)

Statut : proposé
Date : 2026-10-13
Portée : `ifcclash_plus/RuleClass.py`, `ifcclash_plus/Rules.py`, tests d'affichage

---

## 1. Problème

Chaque règle de contrôle peut produire, en plus de ses sources et targets,
des géométries annexes à afficher : axes (Alignement, ClearanceAxisToAxis),
listes de faces (SurfaceRecover, OneObjectFace, TwoObjectsFace), OBB
(OBB_Above, OBB_Below, OBB_Front_And_Back, OBB_Custom), zones de détection
(ClearanceForDoors, FreeSpace, Alignement), éléments de contexte (DirectView,
FreeSpace), segments de rayon (DirectView).

Le mécanisme d'affichage actuel ne sait pas conserver ces géométries :

- chaque règle recalcule sa géométrie dans ses hooks `_display_*` ; le code
  de calcul est donc dupliqué entre `run()` et le display et peut diverger
  (ex. `Alignement._display_input_zone` refait tout le fitting) ;
- certaines règles stockent ces données de façon ad hoc et non uniforme sur
  les résultats (`result.zone["shape"]`, `result.source_faces`,
  `result.axis_mode`) ou sur la règle (`FreeSpace.placements`) ;
- il n'existe aucun moyen de choisir, à l'affichage, quelles catégories de
  géométries afficher ou masquer.

Objectif : conserver ces géométries, au moins temporairement, et permettre
d'activer/désactiver leur affichage par catégorie.

## 2. État actuel concerné

Dans `RuleClass.py` :

- helpers d'affichage : `_add_obb_to_display`, `_add_face_to_display`,
  `_add_gp_Dir_to_display` (affichent immédiatement dans `self.display`,
  donc inutilisables avant l'initialisation du display) ;
- hooks à surcharger : `_display_input_zone`, `_display_input_context`,
  `_display_result_specific`, `_display_input_specific` ;
- la gestion de l'état `Display_Input` est recopiée dans chaque `run()`
  (`if self.state == "Display_Input": self._display_input_generic()`), sauf
  pour `Ray_Check` qui possède son propre `_display_context` ;
- `Select` contient des placeholders jamais utilisés (`list_of_vertex`,
  `list_of_edges`, `list_of_faces`, `list_of_obb`).

## 3. Choix retenu

Un **registre d'annotations géométriques par règle** : une liste typée
`display_items` sur `RuleCheck`, remplie pendant `run()` comme produit
dérivé du calcul, parcourue par un display générique unique qui filtre
par catégorie.

Les trois approches envisagées :

| Approche | Verdict | Motif |
|---|---|---|
| Stocker sur `ClashResult` | Partiellement retenue | Adapté à une géométrie 1:1 avec un résultat (faces de contact, axe d'une paire). Insuffisant seul : zones, contexte et axes existent même sans résultat. |
| Recalculer dans les hooks `_display_*` | Rejetée | Duplication du code de calcul entre `run()` et le display, risque de divergence, coût de recalcul. |
| Registre central rempli pendant `run()` | Retenue | Un seul chemin de calcul, display en lecture seule, filtrage par catégorie gratuit. |

Les deux premières lignes ne sont pas exclusives : les données par résultat
restent légitimes sur `ClashResult` et peuvent être converties en
`DisplayItem` au moment de l'affichage.

## 4. Conception

### 4.1 Structure de données

```python
DISPLAY_CATEGORY = Literal[
    "axis", "face", "obb", "zone", "context", "segment", "point"
]

@dataclass
class DisplayItem:
    category: DISPLAY_CATEGORY
    shape: TopoDS_Shape        # ou données légères, voir 4.2
    color: tuple = (1, 0, 0)   # RGB normalisé 0-1
    transparency: float = 0.6
    element: object = None     # entité IFC source/target liée, optionnelle
```

### 4.2 Choix de représentation

- `TopoDS_Shape` est la représentation par défaut : objets C++ à comptage de
  références, peu coûteux à conserver en Python, aucun recalcul à
  l'affichage.
- Pour les axes, la représentation légère est privilégiée : une paire
  origine + direction (`np.array` ou `gp_Pnt` + `gp_Dir`) ; l'arête est
  construite seulement au moment d'afficher, car les axes sont nombreux et
  légers. Dans ce cas, `shape` contient la donnée brute et la conversion
  en `TopoDS_Shape` est faite par le display générique.
- Le champ `element` garde le lien avec l'entité IFC pour la coloration par
  résultat (rouge/vert via `_result_color_map`, couleurs par paire via
  `_pair_colors`) sans recalculer les centres.

### 4.3 API sur `RuleCheck`

```python
def __init__(self, ...):
    self.display_items: list[DisplayItem] = []
    self.display_options: dict[DISPLAY_CATEGORY, bool] = {
        "axis": True, "face": True, "obb": True,
        "zone": True, "context": True, "segment": True, "point": True,
    }

def register_display_item(self, category, shape, color=(1, 0, 0),
                          transparency=0.6, element=None):
    """Ajoute une géométrie au registre de la règle."""
    self.display_items.append(DisplayItem(...))

def available_display_categories(self) -> set[DISPLAY_CATEGORY]:
    """Les catégories réellement présentes dans le registre."""
    return {item.category for item in self.display_items}
```

Les helpers `_add_obb_to_display`, `_add_face_to_display` et
`_add_gp_Dir_to_display` deviennent des fabriques internes de
`TopoDS_Shape` (resp. composé OBB, face, arête orientée) appelées avant
`register_display_item` ; ils n'affichent plus directement.

### 4.4 Display générique

Un seul point d'affichage remplace les boucles spécifiques :

```python
def display_result(self):
    self._display_result_generic()   # sources/targets, déjà en place
    self._display_registered_items() # registre filtré (nouveau)
    self.display.FitAll()
    self.start_display()

def _display_registered_items(self):
    for item in self.display_items:
        if not self.display_options.get(item.category, True):
            continue
        ais = AIS_Shape(self._item_shape(item))
        ais.SetColor(Quantity_Color(*item.color, Quantity_TOC_RGB))
        ais.SetTransparency(item.transparency)
        self.display.Context.Display(ais, True)
```

Même principe pour `_display_input_generic` : les hooks
`_display_input_zone` et `_display_input_context` sont remplacés par la
lecture du registre filtrée sur les catégories `zone` et `context`.

### 4.5 Cycle de vie

1. `run()` : `self.display_items.clear()` en tête, puis remplissage au fil
   du calcul (zones construites, axes collectés, OBB calculés...).
2. Après `run()` : le registre survit tant que la règle existe — c'est la
   durée "temporaire" recherchée. Un display peut être déclenché plusieurs
   fois sans recalcul.
3. En sortie de `display_result()` / `display_input()` : vidage optionnel
   du registre pour libérer la mémoire sur les gros modèles, piloté par
   un drapeau `keep_display_items` (par défaut `True` pour permettre des
   affichages répétés).

### 4.6 Filtrage

Le choix d'affichage se fait avant l'appel au display :

```python
rule.display_options["obb"] = False   # masquer les OBB
rule.display_result()
```

Une interface utilisateur peut lister les catégories disponibles via
`rule.available_display_categories()`.

### 4.7 Uniformisation des états

La gestion de `Display_Input` est retirée des `run()` individuels et
centralisée dans `end_rule_action` (symétrique de `Display_Result` déjà
présent), ce qui élimine au passage le cas divergent `Ray_Check`.

## 5. Non-buts

- Persistance du registre (sérialisation JSON, BCF) : hors périmètre.
- Interaction clavier/souris dans le viewer pour basculer les catégories :
  le filtrage est d'abord programmatique via `display_options`.
- Refonte du display générique sources/targets (rouge/vert, lignes par
  paire) : conservé tel quel.

## 6. Plan de migration incrémentale

1. Introduire `DisplayItem`, `display_items`, `display_options`,
   `register_display_item` et `_display_registered_items` dans
   `RuleClass.py`, sans toucher les règles.
2. Règles pilotes : `Alignement` (axes + zones), `ClearanceForDoors`
   (zones, migration de `result.zone["shape"]`), `SurfaceRecover` (faces,
   migration de `result.source_faces`). Les hooks `_display_*` de ces
   règles sont supprimés ; leurs `run()` alimentent le registre.
3. Migration des règles restantes (`FreeSpace`, `DirectView`,
   `ClearanceAxisToAxis`, `OBB_*`, `OneObjectFace`, `TwoObjectsFace`,
   `Ray_Check`, `Above`/`Below`) une par une.
4. Suppression des helpers directs `_add_*_to_display` et des placeholders
   `list_of_*` de `Select` une fois toutes les règles migrées.
5. Centralisation de l'état `Display_Input` dans `end_rule_action`.

Chaque étape doit laisser la suite de tests d'affichage
(`test_Rule_display.py`, `test_structure_DisplayUpdate.py`) au vert ; les
tests doivent être étendus pour couvrir le remplissage du registre et le
filtrage par catégorie.

## 7. Critères d'acceptation

- Aucune règle ne recalcule de géométrie dans ses hooks d'affichage : les
  méthodes `_display_input_zone`, `_display_result_specific` et équivalents
  ont disparu ou ne font que lire le registre.
- `display_options[category] = False` masque la catégorie sans erreur ni
  recalcul.
- Le registre est vide après un run en état `Final` sans display si
  `keep_display_items` est faux, et conservé sinon.
- Les tests d'affichage existants et les nouveaux tests du registre
  passent.
