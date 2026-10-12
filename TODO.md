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


13. Faire des tests pour les règles must et les rel ABS 


14. Law Check (moteur de loi utilisateur, règle mesurée)

**Principe** : une valeur x (primitive géométrique mesurée OU propriété d'un objet)
confrontée à une limite f(x) saisie par l'utilisateur, via une loi f définie :
- en polynôme (coefficients a₀…a₅), OU

**Composition** : x = distance, axis_distance, delta_z, angle, projected_area…
ou property(source/target) ; y = property/quantity ; paramètres : domaine de
validité [x_min, x_max], marge de sécurité (%), unités (normalisation SI).

**Verdicts** : conforme / dépassement / hors domaine (jamais extrapolé) /
non évaluable (propriété absente → BCF qualité, pas de faux négatif).

**Sortie** : scalaire (ex. taux de charge = y / f(x)) → criticité, Must
quantitatifs, regroupements, exceptions ; aux frontières de paliers,
le segment le plus restrictif est retenu.

**Sécurité** : évaluateur AST en whitelist (pas d'eval() brut) ;
toutes les primitives en SI.

**Presets** (catalogués avec fiche propre, implémentés sur le moteur) :
- [ ] Weight Capacity By Distance — grutage, abaque par paliers (2 objets)
- [ ] Entraxe max entre supports de tuyauterie : f(Ø) constructeur
- [ ] Épaisseur d'isolant min selon diamètre : e(Ø)
- [ ] Flèche admissible : f(L) = L/250

** jalons** :
- [ ] v1 : moteur 1-objet (y = property(source), x = propriété) + preset grutage
- [ ] v2 : x = primitive géométrique 2-objets (portée, axis_distance)
- [ ] v3 : Lois par morceaux (multi-segments) et Must groupés par cible