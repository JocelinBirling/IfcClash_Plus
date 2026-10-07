# Méthodologie de déploiement des règles

Cette méthodologie s'applique aux règles dont la spécification est validée dans `doc/1ObjectsRules/`, `doc/2ObjectsRules/` et `doc/ComplexRules/`. Le fichier `.md` de chaque règle est la référence figée : structure des paramètres (template), valeurs par défaut, sémantique du clash. Les conventions laissées ouvertes dans les specs se tranchent pendant le développement et se consignent dans le rapport (étape 3).

Une seule règle à la fois : les étapes 1, 2 et 3 sont enchaînées pour une règle avant de passer à la suivante.

## Règles concernées

Ordre de déploiement par difficulté croissante (les règles rebasées sur l'existant d'abord, les algorithmes de recherche ensuite) :

| # | Règle | Type | Doc | Prérequis |
|---|---|---|---|---|
| 1 | Alignement | Complexe | doc/ComplexRules/Alignement.md | CustomOBB existant (axes d'OBB), math pure |
| 2 | SurfaceRecover | 2 objets | doc/2ObjectsRules/SurfaceRecover.md | clash_utils (faces, distances) |
| 3 | DirectView | 2 objets + context | doc/2ObjectsRules/DirectView.md | Ray_Check existant comme socle de rayons |
| 4 | FaceCheck | 2 objets | doc/2ObjectsRules/FaceCheck.md | Moteur de sélection FaceSelection (dictionnaire partagé) ; les membres (FaceClearance, FaceIntersect, FaceOBB, FaceOrient) seront déployés chacun quand leur spec sera écrite |
| 5 | OneObjectFace | 1 objet | doc/1ObjectsRules/OneObjectFace.md | Réutilise le moteur FaceSelection de l'étape 4 |
| 6 | ClearanceForDoors | 2 objets | doc/2ObjectsRules/ClearanceForDoors.md | Chaîne de détection IFC (OperationType, arc 2D, placement) + construction de zones |
| 7 | FreeSpace | Complexe | doc/ComplexRules/FreeSpace.md | Recherche grille + affinage, intersection cylindre/context |
| 8 | EvacuationDistance | Complexe | doc/ComplexRules/EvacuationDistance.md | Ligne brisée sur tranche, pire point, portes/obstacles (ajoutée à la liste après sa spécification) |

## Etape 1 : Écrire la règle dans Rules.py

La règle est une classe dans `ifcclash_plus/Rules.py` (le brouillon disait `Rule.py` : le fichier réel est `Rules.py`).

Checklist :

1. Hériter de la bonne base de `RuleClass.py` : `RuleCheckOneObject`, `RuleCheckTwoObjects` ou `RuleCheckComplex`, selon la catégorie de la règle dans sa spec.
2. Appeler `super().__init__(state, source[, target])`, puis `self.type = "NomRegle"` (identifiant unique) et `self.geom_settings = ifcopenshell.geom.settings()`.
3. Les paramètres du constructeur reprennent le template du `.md` : mêmes noms, mêmes types, mêmes valeurs par défaut (dictionnaires FaceSelection compris).
4. Implémenter `run()` : `select_source.run()` (et `select_target.run()` si deux objets), la logique propre, le remplissage de `self.result` avec les `ClashResult*`, puis `self.manage_result()` à l'état Final ou `self.produce_select()` à l'état Select.
5. Brancher les exceptions, criticité et acteur via `select_exception`, `select_criticity`, `select_actor` si la règle les utilise.
6. Exporter la classe dans `ifcclash_plus/__init__.py`.
7. Réutiliser l'existant avant d'écrire du nouveau : `clash_utils.py` (`get_extreme_faces()`, calculs de distance), `CustomOBB.py`, le socle `Ray_Check`. Une fonction utilitaire nouvelle va dans `clash_utils.py`, avec son propre test.

## Etape 2 : Écrire les tests pour cette règle

Un fichier `tests/test_<Rule>.py` par règle, sur le modèle des tests existants (`unittest`, sélection par `SelectFacet`, modèles dans `Ifc_Model/` et `IFC_Test_Model/`). Plusieurs tests par règle, jeu standard :

1. **Nominal** : un cas de clash connu, présent dans le modèle de test ; la règle doit le trouver.
2. **Négatif** : une configuration saine ne doit lever aucun clash.
3. **Bornes** : la valeur exactement à la limite (min, max, tolérance) doit avoir le comportement défini par la spec (strict ou inclusif).
4. **Cas limites** : set vide, géométrie dégénérée (volume nul, face sans normale), paramètre absent ou invalide — la règle ne doit pas planter.
5. **Exception** : si la règle a des exceptions, vérifier que le filtrage s'applique.

Exécution depuis la racine du dépôt :

```bash
python -m pytest tests/test_<Rule>.py -v
python -m pytest tests/            # la suite entière doit rester verte
```

Si le modèle de test ne contient pas le cas nécessaire, le cas est construit dans le test (géométrie OCC) ou ajouté à `IFC_Test_Model/`.

## Etape 3 : Écrire un rapport dans ce fichier

Une section par règle, ajoutée quand la règle est terminée, sous la forme :

```
## Rapport — <Règle> (<date>)

Décisions d'implémentation :
- ...

Écarts et conventions tranchées (vs le .md de la règle) :
- ...

Problématiques rencontrées et solutions :
- ...

Temps de calcul constaté :
- ...
```

## Définition du terminé

Une règle est déployée quand :

1. Tous ses tests passent, et la suite complète `python -m pytest tests/` reste verte.
2. La spec `.md` est respectée ; tout écart est consigné dans le rapport et répercuté dans le `.md`.
3. Le rapport (étape 3) est écrit dans ce fichier.
4. La roadmap de `agent.md` (statut de la règle, test, doc) est mise à jour.

## Rapports

(les rapports s'ajoutent ici, une section par règle)
