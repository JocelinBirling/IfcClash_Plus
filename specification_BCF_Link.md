# Spécification : Tri des résultats et lien BCF

Une fois que les `results` et les `grouped_results` ont été produits, une
deuxième phase se met en place : le tri des résultats par l'utilisateur,
leur observation dans le modèle, puis leur regroupement en sujets BCF.

Le vocabulaire renvoie aux objets du code :
- `result` : un `ClashResult` (`ClashResultOneObject`,
  `ClashResultTwoObjects`, `ClashResultComplex`) ;
- `group_result` : un `GroupResult` de `rule.grouped_result` ;
- `subject` : un `BCF_Subject`.

---

## 1. Tri des résultats

Une interface graphique permet à l'utilisateur de valider ou d'invalider
chaque résultat.

### Statut de tri

Le tri est porté par un attribut dédié du `ClashResult` (par exemple
`validation`), séparé du verdict de la règle : `status` reste le verdict
calculé par la règle et n'est jamais modifié par le tri.

Trois valeurs :

| Valeur      | Signification                                            |
|-------------|----------------------------------------------------------|
| `Indéfini`  | Valeur par défaut à la sortie du run de la règle.        |
| `Validé`    | L'utilisateur confirme le clash.                         |
| `Refusé`    | L'utilisateur invalide le clash (faux positif, etc.).    |

### Périmètre du tri

Seuls les `results` en échec (`status` à `False`) entrent dans la phase de
tri. Ils sortent du run en `Indéfini`. Les `results` qui passent ne sont
pas triés.

### Granularité atomique

L'objet atomique du tri est le `result`. C'est lui que l'on valide, que
l'on refuse, et que l'on ajoute à un `subject`.

Pour un groupement classique (`select_grouping` sans MustRule), le
`group_result` reste un facilitateur de tri : le statut de tri reste
individuel, porté par chaque `result` du groupe. Le groupe offre
seulement des actions en masse dans l'interface (tout valider / tout
refuser d'un coup), qui ne sont qu'un raccourci appliquant le même statut
à chaque `result` du groupe. Le groupe ne porte pas de statut propre.

### Cas des MustRules

Si la règle a été passée par un MustRule
(`AbsoluteOrRelativeChecking`), le groupe devient une règle en soi :
l'objet produit est un `result` atomique (`ClashResultComplex`), non
scindable. La validation porte alors sur le groupe entier, jamais sur
ses éléments internes.

Conséquence pour le script initial : une règle avec MustRule ne
produit plus de simples `results` regroupables, mais un `result` par
groupe. Le code doit refléter ce changement (voir `rule.result`
remplacé par les `ClashResultComplex` dans
`AbsoluteOrRelativeChecking.run()`).

---

## 2. Observation du modèle pendant le tri

Pendant le tri, l'utilisateur doit pouvoir observer tous les objets
analysés par la règle, dans le modèle, et pas seulement la liste des
résultats. C'est ce qui permet de constater visuellement qu'un clash
n'a pas été détecté correctement : un faux négatif.

### Affichage

L'interface affiche les objets des sélections de la règle
(source et target), avec :

- les `results` en échec (`status` à `False`) en surbrillance nette,
  objets du tri ;
- les `results` en succès (`status` à `True`) affichables discrètement,
  pour distinguer « détecté et conforme » de « non détecté » ;
- le reste des sélections en affichage neutre.

Par-dessus, si besoin, l'utilisateur peut ajouter d'autres objets du
modèle comme contexte (typiquement les murs et les dalles), pour
situer les clashes dans la maquette.

### Faux négatif

L'observation est visuelle seule. Repérer un faux négatif ne crée pas
de `result` manuel : cela sert à corriger la règle (tolérance,
sélection, exception) et à la relancer.

---

## 3. Les sujets BCF

Pendant qu'il trie, l'utilisateur doit pouvoir ajouter des `results`
(ou des groupes de results) à des sujets.

- Un `BCF_Subject` peut réunir plusieurs `results`.
- Un même `result` appartient au maximum à un seul sujet : l'ajouter à
  un autre sujet le retire du précédent.
- Criticité et acteur : le sujet hérite automatiquement de l'union des
  criticités et des acteurs des `results` qu'il contient.

### Relation avec le BCF

Un `BCF_Subject` correspond à un topic BCF : 1 sujet = 1 topic à
l'export.

---

## 4. Persistance

- Le tri utilisateur et les résultats des clashs sont sauvegardés dans
  un fichier : on doit pouvoir fermer puis rouvrir la session sans
  relancer les calculs.
- Les sujets BCF sont sauvegardés dans un fichier BCF.

---

## 5. Travaux à prévoir

- Ajouter l'attribut de tri sur `ClashResult` (valeur `Indéfini` par
  défaut) et ne peupler le tri que pour les `results` en échec.
- Faire évoluer `BCF_Subject` (actuellement un squelette de
  `RuleClass.py` : ajout/retrait de results, criticité et acteur hérités).
- L'interface graphique de tri (validation, refus, actions en masse par
  groupe, gestion des sujets).
- L'affichage pendant le tri : objets des sélections avec échecs en
  surbrillance, succès affichables discrètement, superposition
  d'objets de contexte choisis par l'utilisateur.
- La sauvegarde des résultats et du tri dans un fichier de session.
- L'export BCF : un topic par sujet, avec les viewpoints des éléments
  des `results` du sujet.
