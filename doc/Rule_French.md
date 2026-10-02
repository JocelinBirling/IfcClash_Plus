# Ensembles d'objets
Dans ce projet, nous donnerons un nom à chaque ensemble dans les règles.
Nous avons trois types d'éléments
* Source
* Target 
* Context

Les ensembles d'objets peuvent provenir de modèles différents.

## Source
Ce sont les objets que l'on teste. Ils constitueront l'ensemble principal du clash. Il y aura toujours une source dans chaque clash.
Sans source, il n'y a pas de règle.

Pour l'instant, la source sera considérée comme l'ensemble principal d'objets. Par défaut, c'est la source qui sera transmise aux règles en cascade.

## Target
Les targets sont testés. Elles constituent l'ensemble secondaire du clash.
Pour les règles à deux objets, l'ensemble des objets source sera confronté à l'ensemble des objets target.

## Objets de contexte
Les objets de contexte ne sont pas directement dans le clash, mais ils seront utilisés comme information complémentaire. Ils doivent aider la règle.
Par exemple, si nous voulons tester la ligne de vue libre entre deux objets (A et B). Le mur et la dalle seront utilisés comme éléments de contexte pour déterminer la vue libre.




# Les dossiers de règle
Les dossiers de règle permettent de rassembler les règles au sein de dossier et de sous-dossier. C'est une construction très classique et cela permet de ranger les règles par thème.



# Les 3 grandes classes de règle
Les règles peuvent être classées en plusieurs catégories. Elles sont organisées autour du nombre d'éléments nécessaires pour le clash.
Toutes les règles peuvent être lancées sur des ensembles d'objets, mais, au final, le script testera des objets seuls, par paires ou multiples les uns contre les autres.

## Règles à un objet
Cette règle testera un objet à la fois.
L'objet sera pris isolément et des propriétés géométriques seront vérifiées.

### Exemple
L'objet A doit avoir une surface de dessus de 10m2.
L'objet A doit être orienté vers le sud.

## Règles à deux objets
Ces règles sont les plus courantes. Elles prendront la forme A contre B.
Elles vérifieront l'ensemble A par rapport à l'ensemble B. Chaque élément de l'ensemble A sera "clashé" contre tous les éléments de l'ensemble B.

### Exemple
Le set d'objet A ne soit pas intersecté le set d'objet B.

## Règles complexes
Ce sont des règles qui vont nécessiter plus de 2 sets d'objets.
Elles ne rentrent pas dans le cadre bien précis des 2 règles (1 et 2 objets). Elle devra nécessiter des développements spécifiques à chaque nouvelle règle.

### Exemple
Une règle vérifiant le cercle de rotation du fauteuil roulant utilisera les IfcSpace et le mobilier.
* On ne peut pas dire si c'est l'espace qui est fautif ou le mobilier.
Vérifier s'il y a un chemin de porteur de câbles entre deux pièces.
* On ne peut pas vraiment viser un objet source ni une cible.

## Point d'attention

### Règle asymétrique
Quand la règle possède deux ensembles (source et target), la règle n'est pas forcément symétrique. Certaines règles sont symétriques, mais cela n'est pas une généralité.
* L'ensemble A contre l'ensemble B ne produit pas le même résultat que l'ensemble B contre l'ensemble A.


# Les utilisations des règles
Les règles sont utilisées et réutilisées de diverses manières au sein de ce projet. La même règle peut servir à différents objectifs, vérifier, filtrer, activer, etc...
Cela sera toujours la même règle, mais on va changer la manière, donc le résultat de cette règle va se transmettre.



## Règle Select
Une règle Select est une règle qui est utilisée afin de produire une liste d'objet. Cette sélection d'objet par une règle doit permettre d'enchainer les règles les unes après les autres. Cela fonctionne de la même manière que les facettes d'IDS, les facettes sont autant une manière de sélectionner les objets que de vérifier ceux-ci.

### Traitement en cascade
L'utilisation de règle select permet un traitement en cascade. On peut sélectionner des objets sur la base de caractéristiques géométriques et effectuer d'autres opérations. Ce traitement offre une très grande flexibilité et permet de démultiplier le nombre de règles possible à imaginer. Les cas les plus complexes pourront donc être créés sur la base d'un ensemble de règles simplifié.


## Règle d'activation
Les dossiers de règle peuvent être activés ou déactivés, en fonction de règle.De cette manière, au lancement d'un fichier de règle, certaines des règles ne vont pas s'activer que sous condition.
Ici, on peut utiliser n'importe qu'elle règle géométrie ou bien avec un select d'IDS.



## Règle booléenne
Les règles booléennes sont utilisées dans les dossiers et dans les exceptions. Une règle booléenne produit en sortie un booléen, vrai ou faux. Celui-ci est obtenu en lançant un ensemble prédéfini de méthode. 
Les cas de figure suivants permettent de déterminer si la règle renvoie vraie ou faux.
- "have_result"
- "have_no_result"
- "have_less"
- "have_more"
- "have_more_or_equals"
- "have_less_or_equals"
- "equals"
On se base ici sur le nombre de source, ou de target en sortie de la règle. 

Les règles booléennes peuvent être associées avec les opérateurs classiques AND, OR et NOT.

### Les règles d'exceptions
"C'est l'exception qui confirme la règle", est une maxime française. Elle décrit bien la philosophie de cette mise en œuvre.
Il y aura toujours des exceptions, cependant, on souhaite les réduire au minimum afin de les traiter manuellement.

Les règles d'exceptions s'exécutent à la fin des règles et uniquement pour les règles à deux objets.
Les deux objets A et B sont transmis à une ou plusieurs règles d'exceptions. Avec deux objets, on peut être beaucoup plus précis dans ce que l'on va demander à des sets d'objets.

La règle d'exception permet aussi d'écarter certains cas trop gênants. Si deux objets sont dans le même IfcSystem, ils pourront être écartés, car c'est surement une coquille de modélisation.


# Vérification absolue ou relative (règle Must)
Cette vérification doit permettre de traiter des quantités relatives ou absolues sur les résultats des règles.
Elle commencera toujours par un regroupement de tous les résultats.
L'objectif est de comparer la quantité ou le nombre d'éléments dans chacun de ces groupes.

Exemple
Dans chaque pièce (le regroupement), nous devons trouver exactement un extincteur.
Pour chaque porte (le regroupement), nous devons avoir au moins deux espaces à côté.
Pour chaque étage (le regroupement), nous devons avoir deux fois plus de toilettes que d'espaces.
Pour chaque pièce (le regroupement), nous devons avoir plus de 10m2 de carrelage.


## Nombre absolu d'éléments
Une fois regroupés, nous devons avoir un nombre X d'éléments dans chaque groupe.
Par exemple, à chaque étage, nous devons avoir 2 portes.
La relation peut venir de la source.
Cela s'appliquera au choix sur la source ou la target, mais pas sur les deux.

## Nombre relatif d'éléments
Le nombre d'éléments sources doit être X fois le nombre d'éléments target.
Par exemple, dans chaque pièce, nous devons avoir au moins 2 fois plus de chaises que de tables.
Cela s'appliquera sur la source ET la target afin d'avoir une quantité relative des deux.


## Quantité absolue
On utilise ici une quantité qui est stockée dans une propriété. Cette quantité sera additionnée par rapport au regroupement à l'ensemble du résultat d'une règle.
On pourra donc mesure la surface de fenêtre d'une pièce.
Cela s'appliquera au choix sur la source ou la target, mais pas sur les deux.

## Quantité relative
La quantité doit être relative entre la source et la target. On relation va lier les deux quantités. 
La somme du set A doit être supérieure à la somme du set B.

# Gestion des résultats

## Regroupement des résultats
Une fois la règle traitée, nous avons besoin d'un outil pour faciliter le filtrage et le traitement des résultats.
Nous pouvons regrouper par plusieurs méthodes afin de rassembler automatiquement les objets partageant une même caractéristique.

## Regrouper par IfcRelation
Regrouper par IfcSpace
Regrouper par IfcBuildingStorey
Regrouper par IfcBuilding

## Autres méthodes de regroupement
Regrouper par objet source
Regrouper par gravité
Regrouper par clustering


# Catégorisation automatique

## Acteur
Nous pouvons attribuer automatiquement un acteur à chaque objet à partir d'une spécification IDS.
Ceux-ci pourront être réutilisés dans un BCF plus tard.

## Criticité
Nous pouvons attribuer automatiquement une criticité à chaque objet à partir d'une spécification IDS.
Ceux-ci pourront être réutilisés dans un BCF plus tard.



# Boite à idée


## Exception avant lancement
On pourrait lancer un rassemblement avant que la règle ne soit lancée.
Si deux objets sont dans le même IfcSystem, alors c'est inutile de vérifier s'ils entrent en clash. La plupart du temps, c'est un problème de modèle avec de très petits chevauchements d'arêtes (un problème de modèle, pas réel).
On pourrait aussi découper la vérification par étage (building storey). Cela pourrait aider à réduire la charge (ou inutile si l'arborescence est bonne).
Néanmoins, il reste utile d'implémenter un "par étage", pour éviter les problèmes qui seraient juste au-dessus d'un objet à travers la dalle.
