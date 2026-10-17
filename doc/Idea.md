C'est une grande liste d'idée mélangé avec du TODO.



# Idée de Nouveau Clash


## Clash de Face
On peut commencer à faire clasher les faces des objets, entre les objets mais également sur un même objet.
doc/2ObjectsRules/FaceCheck


## Inclusion Totale dans un autre objet
Cette règle doit vérifier qu'un objet est entièrement à l'intérieure d'un autre objet.

Si l'OBB source est dans l'OBB Target, on doit vérifier que l'OBB est dans la geom Target.

## Chevauchement Volumique
Le seuil de tolérance peut être définit en m3.
Usage : les micro-intersections (un mur qui mord 2 cm³ sur une gaine) sont des faux positifs classiques. Un clash pondéré par volume permet de filtrer.
Test : intersection exacte des deux meshes → volume d'intersection (via CGAL, ou voxelisation grossière en grille 3D pour une approximation rapide). On retourne volume_intersection et éventuellement le ratio sur le plus petit des deux objets.
Résultat : volume en m³ et ratio, seuil « ignorer si < 0,1 % du plus petit objet ».
Difficulté : moyenne à élevée (l'intersection booléenne exacte est coûteuse ; la voxelisation est rapide mais approximative). Très bon rapport valeur/effort avec la voxelisation.

Le résultat peut être configuré, absolue, relatif au plus grand, relatif au plus petit, relatif à la source relatif à la target.


## Clash Surfacique

Usage : détecter les objets posés les uns sur les autres mais mal juxtaposés (appui partiel d'une poutre sur un mur : contact réel mais surface d'appui insuffisante).
Test : pour les paires en contact (distance ≈ 0), calculer l'aire de la zone de contact effectif (triangles quasi coplanaires à distance < ε), et la rapporter à la section d'appui attendue.
Résultat : contact_area + ratio.
Difficulté : moyenne à élevée. Très métier mais peu standardisé ; le seuil ε et la notion de « surface attendue » se paramètrent.


## Clash Spécifique et validation spécifique

Pénétration directionnelle — mesurer la profondeur de pénétration le long de la normale de contact (le « combien de mm il faut reculer pour résoudre »), plus actionnable que le simple booléen d'intersection.
Distance maximale d'intersection — le point le plus profond à l'intérieur de B ; distingue un effleurement d'un percement traversant.
Intersection traversante — détecter les objets qui traversent complètement B (point d'entrée ET point de sortie trouvés par ray-casting le long de la trajectoire).

Clearance sphérique vs cylindrique — le clearance natif est minimal entre surfaces ; un test « cône de dégagement » (mobilité d'extraction d'un équipement) est plus métier.
Concavité d'emprise — pour un clash avec surface de contact, la zone de contact est-elle dans une concavité (encoche prévue) ou sur une face plane (défaut) 

## Analyse des paramètres en Exception

Si deux éléments d'un même IfcSystem rentre en clash, alors il faudrait qu'ils possèdent un IfcRelConnects entre eux.
On pourrait aussi vérifier sur des duos d'objets que certaines caractéristiques soient conservées.
A nouveau, on tombe dans un cas de check absolue ou relatif (vérifier l'un para par rapport à l'autre para)

=> Surement déjà possible avec le relative checking initiale, mais cela crée une fin au check.
## Des autos clash
On pourrait vérifier la qualité de la géométrie.

### Clash avec soi-même

### Clash avec ta propre bounding box

### Clash des géométrie dégénéré
Triangle aplatis
faces sans normes
Objetsà  volume nul




# @TODO

0. Terminer la documentation

1. Terminer le regroupement (grouping by)

2. Extraction de propriétés
Lorsqu'on utilise la règle relative, on peut extraire des valeurs des objets afin de sommer des quantités.
Cela n'a pas été testé correctement.
On pourrait aussi vérifier les relations entre les deux objets. Ils doivent avoir un IfcRel entre eux.

3. Règle Orientation
On pourrait faciliter la règle d'orientation pour vérifier si elle fait face au nord ou au sud, en introduisant simplement du texte.


4. Déterminer le côté principal d'une OBB
Quand on cherche le côté principal d'une OBB, la face Z est prise en compte.
Pour une dalle, cela peut être utile. 
Pour un mur, cela peut mener à des erreurs. Quand un mur est plus haut que long, cela peut causer des imprécisions.


5. Étendre le nombre de règles et créer la structure de base des règles

6. Créer l'association de règles en python => FAIT

7. Étudier l'implémentation dans ifcclash

8. Pour le déploiement en C++, il faudrait standardiser les étapes de détection des clashs. Une sorte de template en C++.

Etape 0. Créer les OBB pour les géométries et rentrer cela dans un Tree

Etape 1. Faire des clashes sur les OBB (Ou les AABB, pour gagner du temps)
    - 1 set OBB vs 1 set OBB
    - 1 set OBB vs 1 set 
Etae 2. Filtrer les éléments
Etape 3. Faire Intersect les pairs d'élements entre 
    - 1 geom vs 1 geom
    - 1 Obb et 1 geom
    - 1 Obb vs 1 Obb

Etape 3. Faire Clearance les pairs d'élements entre 
    - 1 geom vs 1 geom
    - 1 Obb et 1 geom
    - 1 Obb vs 1 Obb

Si on fait toutes ces functions de base en C++, on devrait couvrir la pluspart des cas de figure.



9. On pourrait également mettre en place les autres types de géométrie à faire clasher.
Pour l'instant, on utilise uniquement la géométrie ModelView, mais on pourrait en créer d'autres.


10. Passer des propriétés par les règles.
Une règle A pourrait passer un paramètrage à la règle B.
Ce paramétrage serait spécifique à chaque objet.
Ca me semble hyper galère à configurer et à gérer et surement casse gueule.

# Qualitification des clash

Aujourd'hui, IfcClash sort une liste plate : « élément A clash élément B, type intersection, distance X ». Sur un vrai projet, ça donne des milliers de lignes non hiérarchisées. Le test unitaire (intersection oui/non) ne dit pas si c'est grave, ni pourquoi, ni pour qui. La grille de qualification transforme chaque clash brut en un objet riche et comparable.


L'idée : chaque clash détecté n'est plus un booléen mais un vecteur de dimensions mesurées par les tests secondaires. Concrètement, une structure :

    int guid_a, guid_b;
    std::string type_a, type_b;         // IfcWall, IfcPipeSegment...
    std::vector<std::string> systems;   // systèmes/zone/étage

    // Dimensions géométriques (les "mesures")
    int      test_type;                  // intersection / collision / clearance...
    double   distance;                   // mm (clearance ou pénétration)
    double   penetration_depth;         // mm (recul nécessaire pour résoudre)
    double   intersection_volume;        // m³ (voxelisé)
    double   volume_ratio;               // vol_intersection / min(vol_a, vol_b)
    double   containment_ratio;          // 0..1
    double   contact_area;               // m² (contact étendu)
    int      direction_class;           // vertical / horizontal / traversant
    double   clearance_violated_volume;  // m³ (espace de sécurité empiété)
    bool     crosses_boundary;          // périphérique vs interne

    // Dimensions sémantiques (les "filtres")
    bool     same_phase;                // 4D : coexistence temporelle
    bool     logically_connected;       // IfcRelConnects présent ?
    bool     known_accepted;            // présent dans la base d'acceptés
    int      phase_a, phase_b;

    // Dimensions d'agrégation (le "contexte")
    int      cluster_id;                // cluster spatial (DBSCAN)
    std::string spatial_parent;         // étage / zone
    int      typology_count;            // nb d'occurrences du même couple de types

    // Verdict
    double   severity_score;            // score composite 0..100
    std::string priority;              // critique / majeur / mineur / info

severity = w1 · norm(penetration_depth)
         + w2 · norm(volume_ratio)
         + w3 · boundary_penalty
         + w4 · system_criticality      // eau vs élec vs structure
         − w5 · connectivity_bonus      // connectés logiquement
         − w6 · acceptance_bonus        // déjà accepté

avec norm() qui ramène chaque mesure à 0..1 via des seuils métier (ex. pénétration saturée à 100 mm).
Règles expertes (complémentaire) : des règles dures court-circuitent le score — traversant + structure porteuse = critique, quel que soit le volume ; contact + ratio > 0,1 % et non connecté = majeur, etc. Les règles rendent le système prévisible pour les utilisateurs ; le score pondéré gère les cas intermédiaires.



# How to Link Complex Rules to Source and Target system

For complex rules, we can have a result, not grouped, that give a list of element.

Alignement, will produce several list of alignated element.

How can i link a set of element to source and target method ?

Alignement: Several list of element
Evacutation Distance: Like a OneObject Rule.
Find Path: A line probably
FreeSpace: Like a OneObject Rule, with the position of the shape. 

