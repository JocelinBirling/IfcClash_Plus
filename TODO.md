# TODO

0. Finish the documentation

1. Finish the grouping (grouping by)

2. Property extraction
When using the relative rule, we can extract values from objects in order to sum quantities.
This has not been tested properly.

3. Orientation rule
We could make the orientation rule easier to check whether it faces north or south, simply by introducing some text.


4. Determine the main side of an OBB
When looking for the main side of an OBB, the Z face is taken into account.
For a slab, this can be useful.
For a wall, this can lead to errors. When a wall is taller than it is long, this can cause inaccuracies.


5. Expand the number of rules and create the base rule structure

6. Create the rule association in Python => DONE

7. Study the implementation in ifcclash

8. Review the new rule Alignement, FreeSpace, SurfaceRecover, OneFaceCheck, TwoFaceCheck, DirectView
None of them is truly functionnal.

9. Refactor Face Display
Now, a lot of rule can return a triangle (or a face), from the execution. 
It would be usefull to refactor this fonction to display the result.

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