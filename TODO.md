# TODO

0. Finish the documentation

1. Finish the grouping (grouping by)

3. Orientation rule
We could make the orientation rule easier to check whether it faces north or south, simply by introducing some text.

4. Determine the main side of an OBB
When looking for the main side of an OBB, the Z face is taken into account.
For a slab, this can be useful.
For a wall, this can lead to errors. When a wall is taller than it is long, this can cause inaccuracies.
If a slab is tilded to 45 degres, it's an edge case. It should be taken into account by the user, not the software.


7. Study the implementation in ifcclash

10. Etat des lieux des résultats
Quels sont les données de sorties pour chacune des règles ?
Il faut uniformiser les possibilités de sorties de chaque règle, afin d'en faciliter l'affichage.

11. Volume du resultat 
Pour détecter un clash, on pourrait aussi analyser le volume du clash afin d'en déterminer la gravité.
Toutes les fonctions ne pourraient pas en bénéficier. On peut cependant rapidement voir qu'une fonction unique pour faire ca serait bien pratique.
- Calcul du volume de source 
- Calcul du volume de target
- Calculd du volume de l'interaction

12. Nettoyage des tests
Il faudrait faire un nettoyage des tests afin de vérifier qu'ils soient tous bons.


14. Faire une règle qui vient rechercher les objets les plus proches. => Plutôt une exception ?

15. Faire la règle quality check for One Object
16. Faire la règle StairQuality
17. Faire la règle Stability

18. Faire des test avec des maquettes hors du repo, des maquettes lourdes, des maquettes loins, etc...




