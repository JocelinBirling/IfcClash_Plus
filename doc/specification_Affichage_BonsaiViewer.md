# Spécification : ce que le moteur donne à BonsaiViewer pour afficher les résultats

## 1. Objet et décision

Les états d'affichage `Display_Input` et `Display_Result` étaient un outil
de développement : une fenêtre OCC ouverte par le moteur, et un registre
d'affichage exporté en mode `preview`. Ils sont abandonnés. **BonsaiViewer
décide seul de ce qu'il affiche**, à partir des résultats que le moteur lui
envoie.

Ce document fixe ce contrat :

- quels messages BonsaiViewer reçoit ;
- ce que contient chaque résultat ;
- comment dessiner chaque bloc ;
- ce que pose chaque règle ;
- ce qui manque encore.

Les blocs d'un résultat sont définis dans `doc/specification_ResultData.md`
§4 (`RESULT_SHAPE`). Ce document décrit leur usage pour l'affichage. Il vaut
pour les règles d'origine et pour les règles `_triang` : elles posent les
mêmes blocs.

## 2. Le canal : l'IPC JSON Lines (`ifcclash_plus/ipc.py`)

Une requête `run` (un RuleFile sérialisé et les chemins des IFC) produit
des événements, tous porteurs de l'identifiant du job :

| Événement | Contenu | Usage dans BonsaiViewer |
|---|---|---|
| `progress` | `percent`, `message` | barre de progression |
| `rule_start` | `node_id`, `rule_type` | règle en cours |
| `rule_result` | `node_id`, `rule_type`, `results` (liste), `grouped` (optionnel) | **les résultats à afficher** |
| `log` | `level`, `message`, `trace` | erreurs d'une règle (la suite du run continue) |
| `run_done` | `cancelled`, `percent`, `rule_count`, `result_count`, `error` | fin du run |

À retirer avec les états d'affichage :

- l'événement `display` ;
- le mode `preview` ;
- l'export `display_export.py`, en PythonOCC.

## 3. Un résultat (`result_export.result_to_dict`)

```json
{
  "id": "…", "type": "TwoObjects", "rule": "Clearance", "rule_type": "Clearance", "node_id": "…",
  "status": true, "criticity": ["…"], "actor": ["…"],
  "source": {"step_id": 1234, "ifc_type": "IfcFlowSegment", "model": 0, "global_id": "3x…", "name": "…"},
  "target": {"step_id": 5678, "ifc_type": "IfcCableCarrierSegment", "model": 1, "global_id": "1a…", "name": "…"},
  "info": { "measure": {…}, "points": […], "faces": […], "obbs": {…}, "axes": […], "raycast": {…} }
}
```

**Les éléments.**

- `source` et `target` désignent les éléments du clash. Il n'y a pas de
  `target` pour une règle sur un seul objet.
- Un résultat complexe donne des listes : `sources`, `targets` et
  `context`.
- `model` est l'index de la maquette dans `list_ifc_path`. `global_id` est
  la clé stable à utiliser pour surligner et pour le BCF.

**Les éléments eux-mêmes ne sont pas envoyés.** BonsaiViewer les affiche
déjà, avec son propre `.ifcview`. Les règles `_triang` calculent sur ces
mêmes triangles : ce qui est mesuré correspond exactement à ce qui est
affiché.

## 4. Les blocs de `info` et comment les dessiner

Toutes les coordonnées sont en **coordonnées monde de la maquette, en
mètres**. C'est le repère de la triangulation IfcOpenShell (`use-world-coords`)
et du `.ifcview`. Un bloc n'est présent que s'il est posé.

| Bloc | Forme | À dessiner |
|---|---|---|
| `measure` | `{nom: {"value": float}}` ; la première mesure est la mesure nominale | texte (étiquette, panneau) ; unités dans `specification_ResultData.md` §4 |
| `points` | `[{"number", "source": P, "target": P, "label"?}]` | un segment de `source` à `target`, avec deux marqueurs ; un seul marqueur si les points sont confondus ; `label` donne le sens (`above`, `below`, `ray`…) |
| `faces` | `[{"number", "source": {"normal", "area", "triangles": [[P,P,P]…]}, "target": {…}}]` | les triangles, en surbrillance ; `source` et `target` peuvent être la même face (règles sur un seul objet) |
| `obbs` | `{"source": [OBB], "target": [OBB]}`, OBB = `{"center", "axes": [3 × P], "half_sizes": [3], "label"?}` | une boîte en fil de fer : centre ± demi-taille × axe ; `label` vaut `object` (la boîte de l'élément) ou `zone` (la zone de détection) |
| `axes` | `[{"center", "direction", "length", "label"?}]` | une droite de longueur `length` centrée en `center` ; `label` : `source`, `target`, `expected`, `obb` |
| `raycast` | `{"planned", "cast", "hit", "hit_segments": [[P,P]…], "blocked_segments": [[P,P]…]}` | les rayons non bloqués (`hit_segments`) et bloqués (`blocked_segments`), de deux couleurs |
| `volumes` | `{"intersection", "ratio", "containment", "clearance_violated"}` | texte |
| `axis` | `{"mode", "degraded"}` | texte (ClearanceAxisToAxis : mode de mesure, et si l'axe a été remplacé par un repli) |
| `zone` | `{"side", "leaf", "width", "depth", "height"}` | texte (ClearanceForDoors, règle d'origine seulement) |

**Cadrage d'un résultat** (zoom, point de vue BCF) : on prend le milieu de
`points[0]`, sinon le centre des `faces` ou des `obbs`, sinon la boîte des
éléments de `source` et `target`.

## 5. Ce que pose chaque règle

Relevé sur les 26 règles `_triang`, avec la maquette PN1537 AB (696
éléments) : « Taille JSON » est la taille des résultats de la règle sur
cette maquette.

| Règle | Blocs posés | Libellés | Taille JSON (AB) |
|---|---|---|---|
| Intersection | `measure.distance`, `points` | — | 0,1 Mo (152 résultats) |
| Collision | `measure.distance`, `points` | — | 0,2 Mo |
| Clearance | `measure.distance`, `points` | — | 0,5 Mo |
| Above, Below | `measure.distance`, `points`, `faces`, `obbs` | points `above` / `below` ; obbs `object`, `zone` | 0,5 Mo |
| OBB_Above, OBB_Below, OBB_Front_And_Back, OBB_Custom | `measure.distance`, `obbs` | `object`, `zone` | 0,7 à 1,8 Mo |
| AngleBetween | `measure.angle`, `axes` | `source`, `target` | 7,2 Mo (11 578 résultats) |
| Orientation | `measure.angle`, `axes` | `expected`, `obb` | 0,3 Mo |
| ObbHigh, ObbLength | `measure.offset`, `obbs` | `object` | 0,3 Mo |
| Alignement | `measure.offset` | — | < 0,1 Mo |
| Volume, Area, LateralSurface, ProjectedSurface | `measure.volume` ou `measure.area` | — | 0,1 Mo |
| TopOrBottomSurface | `measure.area`, `faces` | — | 6,2 Mo (10 112 faces) |
| ClearanceAxisToAxis | `measure.distance` et `measure.angle`, `points`, `axes`, `axis` | axes `source`, `target` | 0,4 Mo |
| SurfaceRecover | `measure.contact_area`, `ratio` et `distance`, `faces` | — | 0,9 Mo |
| Ray_Check | `measure.distance`, `points` | `ray` | 0,2 Mo |
| DirectView | `measure.hit_ratio`, `raycast` | — | 3,9 Mo |
| OneObjectFace, TwoObjectsFace | `measure.distance`, `faces` | — | 12,1 Mo et 5,0 Mo |
| FreeSpace | (rien) | — | 0,1 Mo |

Les règles ClearanceForDoors et Intersection2 n'ont pas de version
`_triang`. Elles posent, dans leur version d'origine, les blocs décrits dans
`specification_ResultData.md` §6.

## 6. Ce qui manque

### 6.1 Les diagnostics ne sont pas transmis (à corriger en premier)

Le moteur C++ renvoie des diagnostics : un élément absent du `.ifcview`
(`not_in_ifcview`), un élément sans géométrie, etc. Mais `cpp_backend` les
ignore et l'IPC n'en transmet aucun. **BonsaiViewer ne sait donc pas qu'un
élément n'a pas été contrôlé** : sur CVC × ELEC, 9 éléments sont dans ce cas.

Proposition : un champ `diagnostics` dans `rule_result`, avec les champs
`code`, `message` et `element` (la même référence que `source`). BonsaiViewer
les signale ; il peut par exemple griser les éléments non contrôlés.

### 6.2 Les résultats sans géométrie

| Règle | Ce qui est envoyé | Ce qu'il faudrait pour l'afficher |
|---|---|---|
| Alignement | un décalage par élément | les membres du groupe et l'axe ou le plan d'alignement (`axes`) |
| FreeSpace | rien | la zone cherchée (cylindre : centre, rayon, hauteur) et les obstacles qui la bloquent |
| Volume, Area | la mesure | rien de plus : on surligne l'élément |
| LateralSurface | la mesure | les faces comptées (`faces`) |
| ProjectedSurface | la mesure | le contour projeté (un polygone, ou des triangles dans `faces`) |
| OBB_Above, OBB_Below, OBB_Front_And_Back, OBB_Custom | les zones et l'OBB de la cible | le point, ou le triangle, de la cible qui touche la zone (`points`) |
| Intersection, Collision | une paire de points | la profondeur de pénétration (`measure.penetration_depth`) et, si besoin, la zone commune |

### 6.3 Le repère des maquettes géoréférencées

Les coordonnées envoyées sont celles de l'IFC et du `.ifcview`. Si
BonsaiViewer recentre les maquettes à grandes coordonnées, comme le sont
sans doute les projets IGR, il doit appliquer le même décalage à tous les
blocs de la section 4. **C'est à vérifier dans BonsaiViewer.**

### 6.4 Le volume des données

Sur la seule maquette AB, OneObjectFace renvoie 12 Mo de résultats et
AngleBetween 7 Mo. Sur CVC × ELEC, Clearance renvoie 31 333 résultats. Pistes :

- envoyer la géométrie détaillée (`faces`, `raycast`) à la demande, par
  résultat ;
- ou la limiter aux N premiers résultats, avec le reste en mesures seules ;
- découper `rule_result` en plusieurs événements pour une grosse règle.

## 7. Retrait des états d'affichage

| Où | Quoi |
|---|---|
| `ifcclash_plus/ipc.py` | le mode `preview`, l'événement `display`, la bascule `Display_*` vers `Final` |
| `ifcclash_plus/display_export.py` | le fichier entier (export des formes OCC) |
| `RuleClass` / `orchestrator.run_rule` | le registre `display_items`, `register_display_items`, la fenêtre OCC de `end_rule_action` |
| `registry.STATES` | `Display_Input` et `Display_Result` (il reste `Final` et `Select`) |
| `engine/backends/cpp_backend.compute` | le renvoi des états d'affichage vers le moteur Python |
| tests | `test_Rule_display`, `test_structure_DisplayRegistry`, `test_structure_DisplayUpdate`, `test_display_Intersection2_artefacts` |

Une fois ce retrait fait, le contrat se réduit à `rule_result`, complété
par les diagnostics (§6.1).
