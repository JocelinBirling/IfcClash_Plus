# IfcClash_Plus

## Objectif du projet
Ce projet a pour but d'étendre les capacités d'IfcClash. L'objectif est de proposer une base stable afin d'ajouter des règles géométriques plus ou moins complexes,afin d'avoir un ensemble élargi de règles. Il y a donc 3 buts distincts:

### Des règles pour la qualité des maquettes
Premièrement, on doit pouvoir utiliser ces règles afin de vérifier la géométrie des maquettes. Plus les règles que l'on va créer seront fines, plus le nombre de faux positifs, vrais négatifs sera faible. On limite de la sorte le temps de tri humain, que l'on doit effectuer après chaque lancement de règle. Ces règles doivent être cependant assez complexes afin de prendre en compte l'ensemble des cas de figure que l'on peut avoir dans un projet.

### Des règles pour sélectionner des maquettes
Deuxièmement, ces règles doivent permettre de sélectionner des objets sur des critères géométriques. À date, nous avons l'IDS, afin de sélectionner des objets par rapport à leurs propriétés. Ici, on veut un ensemble de règles communes afin de spécifier des relations entre des objets. Par exemple, je dois pouvoir sélectionner facilement les murs qui sont en contact avec une porte, et ce, même si les murs et la porte sont dans deux modèles différents.

### Standardisation 
Je souhaite également ajouter ma pierre à l'édifice par rapport à la normalisation des définitions. A ce jour, nous avons l'IDS afin d'unifier nos définitions en ce qui concerne la gestion des "données textuelles" mais rien pour ce qui est des données géométriques. 
J'ai remarqué que les différents outils de clash ne sont pas exactement alignés sur la définition d'une intersection, par exemple. De même, le duo de règle classique intersection et distance est assez pauvre pour décrire la richesse des positions relatives entre deux objets.


# Les fonctionnalités principales

1. Un catalogue de règle et une toile à compléter
Le but est de fournir une base de travail sur laquelle on peut facilement rajouter d'autres règles. 
Dans tous les cas de figure, 50% de la gestion de règle est similaire d'une règle à l'autre, gérer les entrées, gérer les sorties, etc.
C'est donc un grand bac à sable.

2. Une base facile à utiliser
Les règles doivent rester simple à prendre en main, si l'on lancer une seule règle rapidement, cela devrait être facile.
J'aime bien la logique suivante:"Easy to use, hard to master".
Est-ce aujourd'hui facile à utiliser ? A determiner...

3. Lien avec l'IDS
J'ai réutilisé les facettes de l'IDS afin de sélectionner les objets. L'objectif est bien d'interconnecter la validation des données textuelles et la validation des données géométriques.

4. La cascade de règle
Une règle a besoin d'une à plusieurs listes d'objets en donnée d'entrée. Cela peut être une facette IDS qui va sélectionner des objets, mais cela peut également être une autre règle. Chaque règle peut produire en sortie une liste d'objet. De cette manière, on peut enchainer les règles les une à la suite des autres afin de raffiner la liste d'objet à obtenir, par des filtres géométriques.

5. Les dossiers
Les règles peuvent être rangées dans des dossiers. Ces dossiers peuvent contenir des sous-dossiers, etc. De la sorte, on peut avoir un fichier complexe avec plusieurs centaines de règles sans que cela soit un problème à gérer. 

Ces dossiers sont activables ou désactivables avec des règles. Ils peuvent donc être conditionnés à la réussite d'une règle ou non. De cette manière, on peut avoir un ensemble très important de règles qui choisiront elles-mêmes de s'activer ou non en fonction du cas de figure. Par exemple, si je n'ai pas de balcon, il est inutile de vérifier si les poutres sont en porte-à-faux.

6. Des exceptions partout
On trouve toujours des cas particuliers que l'on n'a pas réussi à prendre en considération. L'idée ici est de permettre de filtrer les cas particuliers au plus bas niveau du lancement de la règle.

Pour les règles à deux objets, le résultat sera forcément une liste de paire d'objets, un tuyau qui rentre dans une poutre, par exemple. Ces deux objets pourront faire l'objet d'une règle spécifique qui ne se lancera que sur l'échantillon de deux objets. Cela doit permettre d'être plus précis dans l'application de la règle, car on ne possède là que deux objets à analyser, on peut donc vérifier leurs positions relatives l'un de l'autre. Ce qui n'est pas possible avec des listes de plusieurs centaines d'éléments.

7. Automatiser le traitement des résultats
Dans la majorité des cas, on peut déjà trier les résultats de façon semi-automatique. Une intersection entre un tuyau et une poutre devra être envoyé à l'ingénieur structure et l'ingénieur MEP. L'idée ici est à nouveau de brancher les règles sur différents sujets afin de pouvoir trier, par acteur, par criticité.

8. BCF
On doit pouvoir créer des BCF

9. Regroupement des résultats
À nouveau, l'idée est de faciliter le transfert des informations. Dans 90% des cas, on doit pouvoir rassembler les problèmes au sein d'une pièce ou bien d'un étage ensemble. Autrement, on se retrouve avec des milliers de clashs qu'il est complexe d'analyser.

10. Vérification absolue ou relative
Cette vérification doit permettre de définir une quantité, le nombre d'objets du clash ou bien la somme d'une propriété, et de comparer cette valeur avec un objectif.
Cette quantité peut être absolue, il faut que je trouve X éléments qui répondent à la règle dans cette maquette.
Cette quantité peut être relative (pour une règle à deux objets), je dois avoir X fois plus d'objets source que d'objet target dans mes résultats.

Typiquement, cela peut permettre de vérifier que l'on a bien mis 2 prises électriques par 10m2 de bureau par exemple.



# Catalogue de règles
Chaque règle dispose d'une fiche qui présente la règle, ses paramètres et ses cas particuliers.


## Liste des règles

### Règles à un objet

| **Règle** | **Type** | **État de la règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Volume](doc/1ObjectsRules/Volume) | Un objet | OK | KO | OK |
| [Area](doc/1ObjectsRules/Area) | Un objet | OK | KO | OK |
| [Top Or Bottom Surface](doc/1ObjectsRules/TopOrBottomSurface.md) | Un objet | OK | KO | OK |
| [Lateral Surface](doc/1ObjectsRules/LateralSurface) | Un objet | OK | KO | OK |
| [Projected Surface](doc/1ObjectsRules/ProjectedSurface) | Un objet | OK | KO | OK |
| [Orientation](doc/1ObjectsRules/Orientation) | Un objet | OK | KO | OK |
| [Object height](doc/1ObjectsRules/ObbHeigh) | Un objet | OK | OK | OK |
| [Object length](doc/1ObjectsRules/ObbLength) | Un objet | OK | OK | OK |
| [Quality Geometrie](doc/1ObjectsRules/Quality) | Un objet | KO | KO | KO |
| [Face Check](doc/1ObjectsRules/OneObjectFace) | Un objet | KO | KO | KO |

### Règles à deux objets

#### Règles historiques d'IfcClash

| **Règle** | **Type** | **État de la règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Clearance](doc/2ObjectsRules/Clearance) | Deux objets | OK | KO | OK |
| [Intersection](doc/2ObjectsRules/Intersection) | Deux objets | OK | KO | OK |
| [Collision](doc/2ObjectsRules/Collision) | Deux objets | OK | KO | OK |

#### Règles de clearance avancées

| **Règle** | **Type** | **État de la règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Clearance Above Object](doc/2ObjectsRules/ClearanceAbove.md) | Deux objets | OK | KO | OK |
| [Clearance Next To Object](doc/2ObjectsRules/ClearanceNextTo) | Deux objets | KO | KO | OK |
| [Clearance Below Object](doc/2ObjectsRules/ClearanceBelow) | Deux objets | OK | KO | OK |

#### Clearance avec OBB

Une Oriented Bounding Box (OBB) est la plus petite boite qui entoure un objet. Ces vérifications sont rapides et, la plupart du temps, suffisamment précises pour détecter un problème.
L'OBB a un second avantage : elle peut facilement être agrandie ou réduite. On peut avoir des OBB agrandies autour du dessus, ou dont le côté est réduit.

Le dernier bénéfice est la détection de l'avant et de l'arrière d'un élément. La plupart du temps, cette information n'est pas incluse dans la maquette. On ne peut pas déterminer l'avant, l'arrière ou le côté d'un objet. Pour une porte, des éléments peuvent passer sur les côtés, mais pas dans l'embrasure (par l'avant ou l'arrière). Ces méthodes peuvent aider à détecter les objets devant une porte. L'OBB est un parallélépipède, les fonctions pour la modifier ou la calculer sont très simples. C'est une méthode dégradée, mais qui permet tout de même d'obtenir des résultats convaincants.

| **Règle** | **Type** | **État de la règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [OBB Above](doc/2ObjectsRules/OBB_Above) | Deux objets | OK | KO | OK |
| [OBB Below](doc/2ObjectsRules/OBB_Below) | Deux objets | OK | KO | OK |
| [OBB Front And Back](doc/2ObjectsRules/OBB_Front_And_Back) | Deux objets | OK | KO | OK |






#### Autres types de règles

| **Règle** | **Type** | **État de la règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Surface Recover](doc/2ObjectsRules/SurfaceRecover) | Deux objets | KO | KO | KO |
| [Angle Between](doc/2ObjectsRules/AngleBetween) | Deux objets | OK | KO | OK |
| [Direct View](doc/2ObjectsRules/DirectView) | Deux objets | OK | KO | KO |
| [Face Check](doc/2ObjectsRules/FaceCheck) | Deux objets | KO | KO | KO |
| [Volume Clash](doc/2ObjectsRules/VolumeClash) | Deux objets | KO | KO | KO |
| [Inside](doc/2ObjectsRules/Inside) | Deux objets | KO | KO | KO |
| [Door Check](doc/2ObjectsRules/Door) | Deux objets | KO | KO | KO |

#### Les règles sur les faces
| **Règle** | **Type** | **État de la règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Face Intersection](doc/2ObjectsRules/FaceIntersect) | Deux objets | KO | KO | KO |
| [Face Clearance](doc/2ObjectsRules/FaceClearance) | Deux objets | OK | KO | OK |
| [Face OBB](doc/2ObjectsRules/FaceOBB) | Deux objets | OK | KO | OK |
| [Face Orient](doc/2ObjectsRules/FaceOrient) | Deux objets | KO | KO | KO |



### Règles complexes

| **Règle** | **Type** | **État de la règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Free Space in Room](doc/ComplexRules/FreeSpaceInRoom) | Complexe | KO | KO | KO |
| [Find Path](doc/ComplexRules/FindPath) | Complexe | KO | KO | KO |
| [EvacuationDistance](doc/ComplexRules/EvacuationDistance) | Complexe | NOK | KO | KO |
| [Alignement](doc/ComplexRules/Alignement) | Complexe | NOK | KO | KO |



# Installation
Ce projet utilise les éléments suivants.
IfcOpenShell
PythonOCC avec une installation avec Conda


# Progression
La première étape est de créer de nouvelles règles afin d'étendre les possibilités. Ces règles peuvent être utilisées dans n'importe quel gabarit.

## V0.4

#### Mise à jour majeure

- Nouvelles règles
    Plusieurs règles ont été ajoutées : ObbHigh, AngleBetween et CustomOBB, chacune avec son propre ensemble d'exceptions.

- BooleanRule
    Un nouveau module booleanrule.py a été créé, avec la possibilité d'activer ou de désactiver des règles pour un dossier.

- Affichage
    Des fonctions d'affichage des entrées et des résultats ont été ajoutées, avec la prise en charge du regroupement et plusieurs séries d'améliorations. Chaque règle peut être visualisée dans un petit visualiseur. Cela aide à détecter les problèmes.

- Tests
    La suite de tests s'est agrandie d'environ 3500 lignes : nouveaux fichiers pour les règles à un objet, les règles à deux objets, les fichiers et dossiers de règles, Select, ProduceSelect, BooleanRule, clash_utils, l'affichage, les exceptions et la sérialisation. 

- Sérialisation
    Un nouveau module serialization.py a été créé, avec des tests. Toutes les classes peuvent être sauvegardées dans un json afin de les réutiliser ailleurs.

#### Mise à jour mineure

- Réparation des règles Above et Below
    Les deux règles ont fait l'objet d'une refonte complète : la gestion des directions a été corrigée, les limites de clash sont désormais gérées correctement, et OBB_Above / OBB_Below ont été entièrement converties au nouveau système.

- OBB avant et arrière
    L'OBB utilisée pour la détection avant/arrière a été réparée, et la longueur d'OBB a été ajoutée. Un test dédié a été créé pour cette règle.

- Règle Select
    Une nouvelle fonction Produce_Select a été créée, puis étendue pour gérer de nombreux cas. Elle est couverte par des tests.

- Réparation du Ray Check
    La règle Ray Check a été corrigée en trois étapes successives.

- Exception IfcSystem
    Une exception basée sur l'IfcSystem a été ajoutée.

- Refactor de fin de règle
    end_rule_action a été mis à jour afin d'unifier la fin de chaque règle. Les résultats en échec passent désormais par une source unique et unifiée.

- Grande refonte du cœur du code
    Rules.py, RuleClass.py, clash_utils.py et CustomOBB.py ont été fortement refactorés.
    IfcModel a été déplacé, puis supprimé.

- Nettoyage du code
    L'ensemble du code a été formaté avec Ruff, les commentaires ont été supprimés et le .gitignore a été mis à jour plusieurs fois.

- Documentation
    Le README et de nombreuses pages de doc/ ont été mises à jour, dont de nouvelles pages pour ObbHeigh et ObbLength. Un nouveau agent.md et un complex_configuration.json ont été ajoutés. Un gros fichier IFC de test (44000 lignes) a été supprimé du dépôt.

## V0.3
- Utilisation de l'IA
J'ai commencé à utiliser l'IA pour créer des fonctions. Auparavant, c'était beaucoup plus sporadique.

- Création de la classe Custom OBB
C'est une classe customOBB construite avec la classe Bnd_OBB() d'OCC. Elle permet de modifier des OBB existantes, afin de les agrandir, de détacher un côté ou le dessus. 
Cette nouvelle OBB crée ensuite un nouvel espace qui peut entrer en clash avec des objets.
L'OBB est très pratique à modifier, et suffisamment simple pour y appliquer des transformations.

- Fonctions de génération d'OBB
J'ai créé plusieurs fonctions pour générer des OBB à partir d'objets. Certaines sont meilleures que d'autres.
L'une d'elles est intéressante, car elle crée une OBB dont l'axe Z est bloqué sur (0,0,1). C'est utile pour les objets de type boite.

- Ajout d'une fonction d'affichage
Cette fonction doit aider à visualiser ce qui doit se passer dans la règle. Elle affichera la boite OBB, là où le clash devrait apparaitre.


- OBB haut et bas
Cette règle vérifie si quelque chose se trouve au-dessus ou en dessous d'un objet. Elle crée une nouvelle OBB au-dessus (ou en dessous) de l'objet et vérifie si quelque chose entre en clash avec elle.
C'est un peu différent de la règle Above ou Below, car on peut modifier la taille de l'OBB plus précisément. 

- OBB avant et arrière
Cette règle vérifie si quelque chose se trouve devant ou derrière l'objet.
Il est assez difficile de détecter ce qui est l'avant et l'arrière. J'utilise la taille de l'OBB pour les détecter. Cela dépend donc de chaque objet.
Pour une porte, l'avant est la partie large. Pour d'autres objets, ce sera la partie étroite.

- Ajout de quelques cas de test pour aider à tout déboguer
toujours en cours

## V0.2
- Création de la règle Above
    Cette règle vérifie qu'il n'y a rien au-dessus d'un objet.

- Création de plusieurs fonctions de regroupement
    La règle produit une liste de résultats. Cette liste peut être regroupée de différentes manières. J'ai implémenté plusieurs façons de regrouper les objets. 
- Création de la vérification absolue et relative
    En regroupant les objets, on crée des ensembles d'objets. Il est important de vérifier que ces ensembles respectent une règle. 
    Je dois avoir au moins une porte qui intersecte chaque espace. 
    Je dois avoir exactement 1 siphon sous un receveur de douche. 

- Création d'une classification automatique de la criticité
    Chaque résultat peut être classé automatiquement afin de déterminer sa criticité. Cela pourra être exporté vers un BCF. 
- Mise à jour de la classification automatique des acteurs
    Chaque résultat peut être classé automatiquement afin de déterminer un acteur à étiqueter. Cela pourra être exporté vers un BCF. 



## V0.1
Création de la structure principale du script







