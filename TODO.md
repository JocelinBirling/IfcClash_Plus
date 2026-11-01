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
J'ai fait en partien, mais c'est une tâche à refaire.


14. Faire une règle qui vient rechercher les objets les plus proches. => Plutôt une exception ?

15. Faire la règle quality check for One Object
16. Faire la règle StairQuality
17. Faire la règle Stability

18. Faire des test avec des maquettes hors du repo, des maquettes lourdes, des maquettes loins, etc...

19. Le display a un fonctionnement étrange avec des maquettes loins de l'origine. 

20. Vérifier la mise en place de la règle Alignement, surtout la création des plans. 
Il faurait également pouvoir spécifier si l'on cherche un alignement en plan, ou bien en coupe. C'est un peu bizarre de mélanger les deux vérifications en même endroit.

21. Le résultat d'une MustRule doit produire un Result et non un group_result. In fine, après la MustRule le résultat est atomique. On ne peut pas retirer un "ancien" clash du group_result sans lui faire perdre tout son sens. Le group_result devient donc le result de la must_rule.

22. Revoir les paramètres à renseigner dans CustomOBB. Revoir aussi la fonction et l'enchainement des modifications de l'OBB.

23. Réparer la Two Rule Face Object pour afficher les objets.

24. Mettre en place une manière de transmettre en script un json, pour que l'on puisse le lancer depuis BonsaiViewer en C++.


25. Créer un ID pour chaque resultat. L'ID doit être unique sur le projet. On pourrait numéroter les clash de 1 à X, avec le nom de la règle.
On aurait aussi un UniqueID, qui serait générer alétoirement.

26. Le grouping des règles
Faut-il laisser cette fonction au viewer, une visualisation ? Au final, dans l'interface on peut choisir facilement la manière de mettre en forme et on pourra produire un sujet BCF. Cette juste nécéssaire si on veut vraiment industrialiser le procéder et déjà se préfiltrer les éléments.

Si on continue d'utilisation le grouping, il devrait produire un complex_Result. 



27. Comparer Intersection et Intersection2
Il faudrait lancer des tests sur les deux fonctions et vérifier les écarts. Il ne devrait pas y en avoir.

Quel est l'impact de créer un tree sur les fonctions ? et sur les vitesses d'execution ?
Je dois donner des gros modèles et vérifier l'implémentation.

28. Uniformiser la méthode de sélection

Pour volume par exemple, qu'on l'on déclare (min=10,max=50), quel est la logique de sélection des clashs. 

Entre 10 et 50, cela va clasher ?
Hors de 10 et 50, cela va clasher ?

Faut-il inclure 10 et 50 ? ou bien les exclure ? => C'est beaucoup plus logique de les inclures dans le clash [10,50]


Pour le clearance, la zone est bien une zone de clash. On cherche les objets après les min et avant le max. 

[10,50] => Zone de Clash entre 10 et 50. C'est bien ce qu'il faut faire. 

29. Pour les fonctions OBB, il faut ajouter le type de clash. Aujourd'hui, il n'y a pas de clash pour ces types. 


30. Lire et déploiyer Rapport_PostEngine

31. Passer toutes les règles avec if state="Display_Input" pour retourner des valeurs d'affichages.


## Rapport PostEngine.md

32. 2.1 Docstrings du catalogue inversées (MAJEUR)
Je veux que les règles détecte ce que l'on a mis dans les bornes, inclus la borne. Règle[10,20] doit détecter les éléments qui sont entre 10 et 20, et remonte alors ceux-ci en un clash.


33. Optimiser les lourdeurs dans les boucles sans préfiltres.
2.5 Lourdeur : boucles paires sans préfiltre spatial (MAJEUR)


34. Recréer des tests, sur d'autres maquettes. Plus on aura de test, plus on assure que le portage se passera bien.

Je peux facilement recréer des tests entre des maquettes avec des IfcWall avec des IfcBuildingElementproxy.
J'arrive à trouver des couples pour faire des clearances ou biend des intersections.

Slab vs Proxy
Space Vs Proxy



35. Faut-il continuer sur les règles sur les faces d'un objet ?
Typiquement, c'est un problème d'ensolleillement. 