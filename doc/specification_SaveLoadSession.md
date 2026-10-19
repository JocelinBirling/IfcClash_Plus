# Spécification — Sauvegarde / chargement d'une session de travail (règle créée, règle lancée, résultats, triage)

Statut : **proposition à corriger** — les questions ouvertes de la
section 8 conditionnent la forme finale.
Date : 2026-10-19
Portée : `ifcclash_plus/serialization.py`, `ifcclash_plus/result_export.py`,
`ifcclash_plus/RuleClass.py` (round-trip des résultats),
`ifcclash_plus/ipc.py` (points d'entrée IPC), `tests/`.

---

## 1. Contexte

L'existant couvre déjà deux des trois morceaux du problème :

- **la définition des règles** : `serialization.py` fait le round-trip
  complet d'un `RuleFile` (règles, dossiers, selects, booléens,
  exceptions, grouping, criticité, acteur, Must check) vers JSON
  (`save_to_json` / `load_from_json`) — mais **sans les résultats** ;
- **les résultats** : `result_export.py` produit des dicts JSON-safe
  (noyau commun + `ResultInfo.to_dict()` + cross-refs d'éléments
  `step_id` / `global_id` / `model`) — mais **sans round-trip** :
  c'est une export à sens unique pour l'IPC, rien ne relit ce JSON
  pour reconstruire des objets moteur.

Ce qui manque — et que cette SPEC définit — c'est le **dossier de
travail** (session) : un fichier JSON qui porte, en un seul artefact :

1. la **règle créée** (la définition — déjà sérialisable) ;
2. la **règle lancée** : le contexte de run (fichiers IFC, version,
   horodatage) et les **résultats** produits ;
3. **l'état de triage** du travail en cours : quels résultats ont été
   revus, ignorés, validés, commentés — pour reprendre le
triage/filtrage plus tard, là où on l'a laissé.

Décisions de principe :

1. **Un seul artefact** : la session est un fichier JSON unique
   (extension proposée `.ifcclash_session.json` ou `.icps.json`). La
   définition de règle et les résultats sont des blocs **imbriqués**
   dans ce fichier, pas des fichiers séparés à jumeler à la main.
   (Question 8.1 — une variante multi-fichiers reste ouverte.)
2. **Réutiliser, ne pas refaire** : le bloc règle est la sortie exacte
   de `serialize_rule_file()` ; le bloc résultat est la forme exacte
   de `result_export.result_to_dict()`. La session n'introduit **aucun
   format parallèle** : elle emballe les formes existantes.
3. **L'état de triage vit dans la session, pas sur les résultats
   moteur** : le moteur produit des résultats, le triage est le
   travail de l'utilisateur par-dessus. La session l'associe par
   l'ID stable du résultat (GUID `uuid4`, déjà posé à la création).
4. **La reprise dégrade proprement** : au chargement, les fichiers IFC
   sont ré-ouverts et comparés (empreinte) ; si le modèle a changé
   depuis le run, la session le **signale** et propose une reprise
   best-effort (mapping par `GlobalId`), jamais un silence trompeur.

---

## 2. Cas d'usage

| # | Scénario | Ce qui est sauvegardé | Ce qui est rechargé |
|---|---|---|---|
| U1 | J'écris une règle, je ne l'ai pas encore lancée | le bloc règle seul (session sans `runs`) | la règle, prête à lancer |
| U2 | Je lance la règle sur ma maquette, le calcul est long | la règle + le run + les résultats | les résultats **sans relancer** le calcul |
| U3 | Je trie/filtre les résultats (je les passe en revue) | U2 + l'état de triage, incrémental | les résultats **et** mon avancement de triage |
| U4 | Je reprends à J+3, la maquette a bougé | — | avertissement de péremption ; reprise best-effort ou re-run proposé |
| U5 | Je veux relancer depuis les résultats d'hier (cascade) | — | **hors périmètre** (8.3 résolu) : les résultats restent des données ; seules les **règles** sont réhydratées — le rechaînage exige un re-run |

Décisions actées à la relecture du 2026-10-19 :

- **8.1 — un seul fichier** : la session est un artefact JSON unique,
  réécrit à chaque sauvegarde incrémentale ;
- **8.3 — les résultats sont en lecture seule**, les **règles** sont
  réhydratées : au chargement, le bloc `rule_file` est reconstruit en
  objets vivants (`deserialize_rule_file`, déjà existant) et les
  résultats restent des dicts JSON relus pour l'affichage et le
  triage. Pas de re-attachement d'`entity_instance`, pas de
  reconstruction de `ClashResult` — un rechaînage en cascade exige de
  relancer la règle ;
- **8.4 — choix à l'ouverture** : le moteur expose les deux modes
  (charger quand même / ne charger que la règle), le client demande à
  l'utilisateur à chaque session périmée ;
- **8.2 — trois statuts** : `ignored`, `validated`, `to_review`, avec
  commentaire et tags libres.

---

## 3. Le fichier session — forme JSON

```json
{
  "format": "IfcClashPlus-Session",
  "version": 1,
  "created": "2026-10-19T14:32:01Z",
  "updated": "2026-10-19T17:03:44Z",
  "ifc_files": [
    {
      "path": "/models/archi_v12.ifc",
      "file_name": "archi_v12.ifc",
      "sha256": "ab3f…",
      "size_bytes": 48210304,
      "schema": "IFC4"
    }
  ],
  "rule_file": {
    "//": "sortie exacte de serialize_rule_file() — RuleFile, dossiers, règles, selects",
    "type": "RuleFile",
    "id": "…",
    "list_ifc_path": ["/models/archi_v12.ifc"],
    "contains": [ … ]
  },
  "runs": [
    {
      "id": "run-8f2a…",
      "started_at": "2026-10-19T14:40:12Z",
      "finished_at": "2026-10-19T15:02:37Z",
      "engine_version": "0.5.0",
      "run_scope": [
        { "node_id": "la-regle-1", "result_count": 214 }
      ],
      "results": [
        {
          "//": "forme exacte de result_export.result_to_dict()",
          "id": "4f1e-… (GUID uuid4 du résultat)",
          "type": "TwoObjectsResult",
          "rule": "Intersection",
          "node_id": "la-regle-1",
          "status": true,
          "criticity": ["High"],
          "actor": ["Architecte"],
          "source": { "step_id": 5312, "model": 0, "global_id": "2Xvg$…", "name": "Wall_12", "ifc_type": "IFCWALL" },
          "target": { "step_id": 7708, "model": 0, "global_id": "3RjQ9…", "name": "Pipe-45", "ifc_type": "IFCPIPE" },
          "info": { … RESULT_SHAPE … }
        }
      ]
    }
  ],
  "triage": {
    "//": "clé = GUID du résultat, toutes les clés optionnelles sauf status",
    "4f1e-…": {
      "status": "ignored",
      "comment": "modélisation, pas un vrai clash",
      "tags": ["artifact"],
      "updated_at": "2026-10-19T16:58:02Z"
    }
  }
}
```

### 3.1 `ifc_files` — le contexte de run

Chaque fichier consommé au moment du run porte :

- `path` + `file_name` : pour ré-ouvrir ;
- `sha256` (+ `size_bytes`, `schema`) : l'**empreinte de péremption** —
  au chargement, le fichier ré-ouvert est re-haché ; tout écart marque
  la session (et les résultats qu'elle porte) comme *potentiellement
  périmés* ;
- `model` : l'index de modèle utilisé dans les cross-refs (l'ordre de
  `ifc_files` fixe l'index — il ne doit pas être réordonné).

### 3.2 `rule_file` — la règle créée

Sortie exacte de `serialize_rule_file()`, sans adaptation. Une session
« règle seule » (U1) est un fichier dont `runs` est vide. L'unité de
sauvegarde est **toujours le `RuleFile` complet** (8.7) — pas
d'export/import d'une règle isolée au sein de la session.

### 3.3 `runs[]` — la règle lancée

Un run = une exécution (pas une règle) : relancer la même règle après
modification de la maquette ajoute un **nouveau** run à la liste, il
ne remplace pas l'ancien — l'historique des runs fait partie du
travail. Chaque run référence ses règles par `node_id` (l'`id` du
`RuleCheck`, déjà sérialisé dans le bloc règle).

Les résultats sont la forme de `result_export.result_to_dict()` :
noyau commun + cross-refs (`step_id`, `global_id`, `model`, `name`,
`ifc_type`) + `info` (RESULT_SHAPE, `doc/specification_ResultData.md`
section 4). Aucune géomé OCC n'est sérialisée : les `DisplayItem` ne
sont **pas** dans la session — l'affichage à la reprise se
reconstruit depuis les données sérialisables (points, faces, OBB,
segments), comme le prévoit déjà `display_items(info, rule)`.

### 3.4 `triage` — l'état du travail de triage/filtrage

- clé : le **GUID du résultat** — stable, déjà posé à la création du
  résultat, inchangé au fil des sauvegardes incrémentales ;
- `status` : le verdict de triage — vocabulaire fixé (8.2) :
  `"pending"` (défaut, implicite — absent du fichier), `"ignored"`,
  `"validated"`, `"to_review"` ;
- `comment`, `tags[]` : libres ;
- `updated_at` : horodatage du dernier changement.

La session est **ré-écrite à chaque sauvegarde incrémentale** : le
triage avance, on sauvegarde, le fichier est réécrit (règle + run +
triage à jour). Pas de fichier annexe ni de diff. Le triage est
strictement **mono-utilisateur** (8.8) : pas de champ auteur, pas de
verrou — un seul profil de travail.

---

## 4. La relecture — résultats en lecture seule, règles réhydratées

8.3 résolu : **aucun round-trip objet des résultats**. Au chargement :

1. `rule_file` → objets vivants : `deserialize_rule_file()` (existant) ;
2. `ifc_files` → ré-ouverture des fichiers IFC + contrôle d'empreinte
   (`sha256` recalculé, comparé à la session) — les fichiers ré-ouverts
   servent à la détection de péremption et au re-run, pas à ré-attacher
   les résultats ;
3. `runs[]` et `triage` → **lus comme données** : les dicts de résultats
   et l'état de triage sont exposés tels quels à l'appelant (client),
   sans reconstruction de `ClashResult` ni de `ResultInfo`.

Conséquence : aucun mapping `(model, step_id)` / `global_id` au
chargement — les cross-refs restent des références de données. Le
client qui veut isoler visuellement un élément le résout dans **sa**
registry d'éléments, comme il le fait déjà pour l'IPC.

En cas de péremption (empreinte différente), le chargement expose le
choix (8.4) :

- **charger quand même** : les résultats sont relus tels quels,
  marqués *potentiellement périmés* — à l'utilisateur d'en juger
  pendant le triage ;
- **ne charger que la règle** : `runs` et `triage` sont ignorés, la
  règle est prête à être relancée sur la nouvelle maquette (un nouveau
  run s'ajoutera à la session).

---

## 5. L'API

Côté moteur (`serialization.py`, section session) :

```python
save_session(session, filepath)          # ré-écriture complète (atomique : .tmp + rename)
load_session(filepath, on_stale=…) -> Session
                                         # on_stale ("keep_results" | "rule_only") :
                                         # le choix à l'ouverture (8.4), donné par
                                         # l'appelant après demande à l'utilisateur
Session.run_stale() -> bool              # True si un ifc_files a changé
Session.rule_file -> RuleFile            # réhydraté (deserialize_rule_file)
Session.runs -> list[dict]               # lecture seule : les dicts de résultats
Session.triage -> dict[str, dict]        # lecture/écriture : l'état de triage
```

Côté IPC (`ipc.py`) : deux messages miroir — `save_session` /
`load_session` — plus un événement de péremption au chargement
(session marquée *stale*). Le triage reste piloté par le client, qui
écrit dans la session via l'API.

---

## 6. Le contrôle — aux tests uniquement

Mêmes principes que la SPEC des résultats : aucun contrôle à
l'exécution, le contrat vit dans les tests
(`tests/test_session_roundtrip.py`) :

1. **round-trip complet** : une session construite en mémoire
   (règle + un run + triage) → `save_session` → `load_session` → les
   objets reconstruits sont identiques (règle par `serialize` →
   comparaison des dicts ; résultats/triage par comparaison des dicts
   relus) ;
2. **triage incrémental** : sauvegarder, changer un statut de triage,
   re-sauvegarder, recharger — le triage survit ;
3. **péremption** : une session avec un fichier IFC modifié après le
   run → `run_stale()` à True ; les deux modes de chargement
   (`keep_results` / `rule_only`) se comportent comme spécifié ;
4. **version future** : `"version": 2` inconnue → erreur explicite
   (jamais de lecture silencieuse au format deviné).

---

## 7. Plan d'implémentation

1. la classe `Session` : assemblage (serialize_rule_file +
   result_to_dict + triage), sauvegarde atomique, chargement
   (réhydratation des règles par `deserialize_rule_file`, runs et
   triage en lecture de données) ;
2. le contrôle d'empreinte (`sha256`) et la signalisation *stale* +
   les deux modes de chargement ;
3. les messages IPC ;
4. la feuille de test du round-trip.

---

## 8. Questions ouvertes

| # | Question | Options |
|---|---|---|
| 1 | ~~Un seul fichier session ou des fichiers séparés ?~~ | **Résolu** : un seul fichier JSON, réécrit à chaque sauvegarde incrémentale |
| 2 | ~~Le vocabulaire du statut de triage ?~~ | **Résolu** : trois statuts — `ignored`, `validated`, `to_review` — avec commentaire et tags libres |
| 3 | ~~Réhydratation des résultats ou lecture seule ?~~ | **Résolu** : les résultats sont en lecture seule (données pour l'affichage et le triage) ; seules les règles sont réhydratées — le rechaînage en cascade exige un re-run |
| 4 | ~~Comportement par défaut sur maquette changée ?~~ | **Résolu** : choix à l'ouverture — le moteur expose `keep_results` / `rule_only`, le client demande à l'utilisateur |
| 5 | ~~Sauvegarder aussi l'état de filtrage du client ?~~ | **Résolu** : triage seul — pas de bloc `view_state`, le client reconstruit ses filtres lui-même |
| 6 | ~~Affichage à la reprise : reconstruction ou re-run léger ?~~ | **Résolu** : reconstruction depuis les données sérialisables du résultat (points, faces, OBB, segments) — aucun recalcul |
| 7 | ~~Unité de sauvegarde : RuleFile complet ou règle seule ?~~ | **Résolu** : le RuleFile complet, toujours |
| 8 | ~~Triage mono-utilisateur ou multi-utilisateurs ?~~ | **Résolu** : strictement mono-utilisateur — pas de champ auteur, pas de verrou |
