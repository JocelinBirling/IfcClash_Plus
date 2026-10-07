# Méthodologie de déploiement des règles

Cette méthodologie s'applique aux règles dont la spécification est validée dans `doc/1ObjectsRules/`, `doc/2ObjectsRules/` et `doc/ComplexRules/`. Le fichier `.md` de chaque règle est la référence figée : structure des paramètres (template), valeurs par défaut, sémantique du clash. Les conventions laissées ouvertes dans les specs se tranchent pendant le développement et se consignent dans le rapport (étape 3).

Tu trouveras les instructions pour monter l'environnement dans agents.md.

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
```
Seuls les règles que tu as écrites doivent passé. Il ne faut pas toucher aux règles déjà écrites.

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

## Rapport — Alignement (2026-10-07)

Décisions d'implémentation :
- Classe `Alignement(RuleCheckOneObject)` dans `ifcclash_plus/Rules.py`, `type = "Alignement"`, exportée dans `ifcclash_plus/__init__.py`. Base one-object : la spec dit explicitement « There is no Target: the rule works on a single set » et les résultats sont des `ClashResultOneObject` (un par objet hors alignement).
- Axe principal de chaque objet = axe de l'OBB (`create_obb_from_TopoDs_Shape`) de plus grande demi-taille ; le segment d'axe (centre ± direction * demi-taille) porte les données géométriques de l'alignement.
- Nouvelles fonctions dans `clash_utils.py`, chacune testée unitairement : `least_squares_line_2d`, `least_squares_line_3d`, `least_squares_plane_3d`, `point_line_distance`, `point_plane_distance`, et `alignment_clash_flags` (décision de groupe pure : groupe, Min_Group, clash).
- Résultats : `ClashResultOneObject` avec l'attribut supplémentaire `offset` (décalage de l'objet au fit, pour guider la correction). L'alignement trouvé (élément ajusté, direction, position, membres) est exposé dans `rule.alignment`.
- Validation des paramètres au constructeur : `axis` / `alignment_type` inconnus, `tolerance` absente ou négative, `min_group` non entier < 1 → `ValueError`.
- Les modèles de test sont générés par l'API ifcopenshell dans `tests/test_Alignement.py` (fichiers temporaires) : `IFC_Test_Model/` ne contient pas de cas d'alignement connus (rangée de poteaux, façade, murs en prolongement d'axe).

Écarts et conventions tranchées (vs le .md de la règle) :
- Catégorie : le tableau de déploiement classe la règle « Complexe », mais la spec travaille sur un seul set. Implémentée sur `RuleCheckOneObject` ; `RuleCheckComplex` (brouillon inutilisable : son `__init__` casse l'appel au super) n'a pas été modifié. Précisé dans `doc/ComplexRules/Alignement.md`.
- « Least squares » = TLS (ACP) sur les distances perpendiculaires, cohérent avec la définition de l'offset. Conséquence assumée : un objet aberrant partage son erreur avec le fit (6 poteaux alignés + 1 décalé de 0,5 m : offsets inliers ~0,07 m, outlier ~0,43 m).
- `Alignment_Type = Plane` : le plan ajusté est contraint **vertical** (extrusion Z d'une droite de plan TLS sur les centres projetés des axes), offset mesuré en plan. Sans cette contrainte, des murs de même hauteur seraient coplanaires dans un plan horizontal et l'exemple « façade » ne détecterait rien. Précisé dans le .md.
- `Axis` auto-détecté : vote par objet (|dot(axe, Z)| >= cos 45°), à la majorité, égalité → Vertical.
- `Alignment_Type = Line` horizontal : la droite 3D est ajustée sur l'union des extrémités des segments d'axes ; l'offset d'un objet = distance max de ses extrémités à la droite (un mur perpendiculaire qui traverse l'axe est ainsi détecté, alors que son centre est sur la droite).
- Bornes : offset == Tolerance → dans le groupe (inclusif, « farther than Tolerance is outside ») ; groupe == Min_Group → alignement valide.
- Sets dégénérés : 0 objet → aucun résultat ; 1 objet → clash (groupe < Min_Group) ; points confondus (poteaux empilés) → offsets 0 ; 2 positions plan distinctes → la droite passe exactement par les deux, aucun clash possible (limination qui motive Min_Group = 3, documentée en test).
- Pas d'exception, criticité ni acteur pour cette règle (spec muette) : les branchements `select_exception` / criticité / acteur restent disponibles par héritage.

Problématiques rencontrées et solutions :
- Unités du fichier IFC généré : `unit.assign_unit` crée des millimètres par défaut ; la profondeur d'extrusion est convertie en mm mais pas le profil → géométrie dégénérée (OBB de section nulle). Solution : assigner `length={"raw": "METERS"}`.
- `shape.id` n'existe pas avec `USE_PYTHON_OPENCASCADE` sous ifcopenshell 0.8 : utiliser `shape.data.id`.
- Pas de `geometry.add_box_representation` en 0.8.4 : représentations créées via `IfcRectangleProfileDef` + `geometry.add_profile_representation` + `assign_representation`.
- Le plan libre (PCA 3D) sur des murs de façade de même hauteur donne un plan horizontal (offsets tous 0) → contrainte « plan vertical » (voir écarts).
- Vérification limitée à `tests/test_Alignement.py` (consigne de la session : ne lancer que les tests écrits pour la règle) ; la suite complète n'a pas été relancée.

Temps de calcul constaté :
- `python -m pytest tests/test_Alignement.py -v` : 24 tests en ~0,8 s. Le fit (numpy, quelques points) est négligeable devant l'itération géométrique (OBB par objet).

## Rapport — SurfaceRecover (2026-10-07)

Décisions d'implémentation :
- Classe `SurfaceRecover(RuleCheckTwoObjects)` dans `ifcclash_plus/Rules.py`, `type = "SurfaceRecover"`, exportée dans `ifcclash_plus/__init__.py`.
- Pipeline à deux itérateurs par sélection : `USE_PYTHON_OPENCASCADE` pour les shapes OCC (OBB préfiltre, distance exacte `BRepExtrema_DistShapeShape`), natif + `USE_WORLD_COORDS` pour les maillages triangulés (`get_vertices` / `get_faces`), rapprochés par id d'entité (`shape.data.id` côté OCC, `shape.id` côté natif).
- Nouvelles fonctions dans `clash_utils.py`, chacune testée unitairement : `extreme_triangles` (triangles dont la normale est alignée sur la direction, retenus s'ils sont dans une tranche d'épaisseur Tolerance au plan extrême — les faces de trous pointant dans le même sens sont ignorées), `triangles_projected_area`, `contact_area_between_triangle_sets` (paires quasi coplanaires, distance le long de la direction sous Tolerance, aire = intersection des projections shapely, zones disjointes sommées), `covering_out_of_bounds` (décision pure sur les bornes, testée à la borne exacte).
- Résultat : `ClashResultTwoObjects` avec `surface_contact_area` (contact, m²), `distance_between` (distance de la paire) et les attributs `ratio` (%, None si la face de référence est vide), `source_face` / `target_face` (normale et aire des faces extrêmes utilisées, pour expliquer le dénominateur).
- Modèles de test : `IFC_Test_Model/IFC_Model/` contient déjà les cas dédiés (`SlabA_RecoverTop_CuboidB/CylinderA_100%/50%`, dalle à 0,9 m au-dessus de son support → tests avec Tolerance 1.0) ; cas latéral et hors contact via `CubeA_TouchFace_CubeB` et `CubeA_NextTo_CubeB_1m`. Sélection par facette `Attribute(Name)`.

Écarts et conventions tranchées (vs le .md de la règle) :
- Résultat seulement pour les paires hors bornes : la spec (« For each pair in contact, one result containing... ») se lit comme la description du contenu du résultat ; l'étape 7 ne lève un clash que si la valeur est hors [Min_Covering, Max_Covering]. Une paire conforme ne produit donc rien.
- « Distance below Tolerance » : inclusif (distance == Tolerance = contact), pour les paires comme pour les triangles.
- `Direction = Auto` : vecteur du point le plus proche de la source vers celui de la cible (`BRepExtrema`) ; si les points coïncident (objets qui se touchent/s'intersectent), repli sur le vecteur centroïde→centroïde des maillages ; dégénéré aussi → paire ignorée.
- Appariement « quasi coplanair » : normales opposées à 25° près (constante `PAIRING_COSINE`), alignement des candidats à 45° ; la distance entre triangles est mesurée le long de la direction (projection des centroïdes).
- Aires mesurées en projection sur le plan de contact (⊥ direction) : cohérent pour le contact comme pour le dénominateur de référence ; pour des faces quasi perpendiculaires à la direction elles sont exclues de toute façon par le filtre de normales.
- `ratio` en % de la face de référence (aire des triangles extrêmes de l'objet choisi) ; face de référence vide + borne relative → clash (la couverture ne peut pas être vérifiée).
- Aucune borne fournie → aucune vérification, aucun clash (spec : « only the provided bounds are checked ») ; testé explicitement.
- Bornes inclusives : une valeur exactement à une borne est conforme ; strictement en dessous de Min ou au-dessus de Max → clash.
- Valeur de couverture str : uniquement les chaînes finissant par `%` sont relatives ; une chaîne numérique sans `%` (ex. "10") est refusée (ValueError), la spec ne définit que nombre (m²) ou chaîne en %.

Problématiques rencontrées et solutions :
- Préfiltre `IsOut` des OBB : il élimine toute paire d'OBB disjointes, donc aussi les paires à distance < Tolerance (dalle à 0,9 m avec Tolerance 1.0) → remplacé par `min_distance_to_obb` (SAT, CustomOBB existant), comparé à la Tolerance.
- Bug initial dans `contact_area_between_triangle_sets` : les triangles étaient recentrés sur leur centroïde avant projection, ce qui détruisait leurs positions relatives (les modèles 100% et 50% donnaient le même contact) ; corrigé en projetant les points monde.
- Direction `Auto` sur objets qui se touchent : les points les plus proches coïncident, le vecteur est nul → repli centroïdes (voir écarts).
- `shape.id` n'existe qu'en itérateur natif ; en pythonocc c'est `shape.data.id` — les deux itérateurs sont appariés par `entity.id()`.
- Test de `extreme_triangles` : la face « plafond intérieur » d'une boîte ouverte pointe vers le bas comme le fond mais n'est pas extrême ; maillage construit à la main dans le test pour le vérifier.

Temps de calcul constaté :
- `python -m pytest tests/test_SurfaceRecover.py -v` : 26 tests en ~1,7 s (paires simples ; le coût domine par l'ouverture des IFC et l'itérateur, pas par shapely).

## Rapport — DirectView (2026-10-07)

Décisions d'implémentation :
- Classe `DirectView(RuleCheckTwoObjects)` dans `ifcclash_plus/Rules.py`, `type = "DirectView"`, exportée dans `ifcclash_plus/__init__.py`. Le Context est un `Select` passé au constructeur, sur le modèle de `Ray_Check` (dont le socle est réutilisé : `ifcopenshell.geom.tree()` + `add_to_tree(context, "UB")` + `tree.select_ray(origin, direction, length)`).
- Nouvelles fonctions dans `clash_utils.py`, chacune testée unitairement : `r2_sequence` / `sample_point_in_triangle` (échantillonnage déterministe basse discrépance R2 dans un triangle, avec miroir dans le demi-carré pour rester barycentrique), `plan_ray_counts` (répartition des rayons sur les faces au prorata des aires, méthode du plus fort reste, somme exacte), `direct_view_early_stop` (décision pure de terminaison anticipée, testée aux bornes).
- Faces émettrices/réceptrices : triangles du maillage monde (itérateur natif + `USE_WORLD_COORDS`) dont la normale fait face à l'autre objet (produit scalaire avec le vecture centre de triangle → centre de l'autre objet > 0).
- Résultat : `ClashResultTwoObjects` avec `hit_ratio` (%), `rays_cast`, `rays_planned`, `hit_segments` / `blocked_segments` (les couples (origine, point visé) des rayons touchés/bloqués — les « seen zones » de la spec).
- Modèles générés par API ifcopenshell dans `tests/test_DirectView.py` (observateur, cible à 8 m, mur bloquant total ou partiel) : `IFC_Test_Model/` ne contient pas de cas de visée directe.

Écarts et conventions tranchées (vs le .md de la règle) :
- Résultat levé uniquement pour les paires dont le ratio est sous le seuil (spec : « Raise a clash if the hit ratio is below Threshold ») ; les paires conformes ne produisent rien.
- Échantillonnage déterministe (séquence R2), pas aléatoire : un même modèle donne toujours le même ratio — indispensable pour des tests reproductibles. Le point visé utilise un index décalé (+1 000 007) pour décorréler origine et cible (sinon les rayons apparient des positions d'échantillonnage identiques et couvrent mal).
- Face réceptrice d'un rayon : choix pondéré par les aires (déterministe via R2) ; le point visé est échantillonné dans cette face (visée « face à face »).
- Rayon de longueur nulle (les faces se touchent) : compté comme touché ; rayon plus long que `Max_Distance` : raté sans être tiré dans l'arbre (il comptabilise quand même comme rayon tiré).
- Aucun rayon tirable pour la paire (aucune face tournée vers l'autre) : ratio 0 % → clash si le seuil > 0.
- Seuil strictement en dessous : ratio == Threshold → pas de clash ; Threshold « 0% » → jamais de clash.
- La terminaison anticipée garantit la même décision qu'un tir complet : « clash » quand (touches + restants)/prévus < seuil (le ratio max possible sur les rayons tirés) ; « ok » quand touches/prévus >= seuil (le ratio min possible). Le ratio rapporté porte sur les rayons réellement tirés (spec, étape 7).
- Le Context reçoit les fichiers du Source dans `run()` (pas de branchement dans `update_file_info` de la base, sur le modèle de `Ray_Check`).

Problématiques rencontrées et solutions :
- `tree.select_ray` exige des `gp_Pnt`/`gp_Dir` : les tuples de `float` Python sont acceptés, mais pas les tuples de `numpy.float64` — la règle convertit explicitement (`float(v) for v in ...`).
- `add_to_tree(..., "UB")` appelle `iterator.get_native()` (méthode de l'itérateur, pas de la shape).
- Un rayon exactement dans le plan d'une face du mur (y = bord) n'est pas détecté par l'arbre : éviter les configurations strictement rasantes dans les modèles de test.
- Le profil `IfcRectangleProfileDef` est CENTRÉ sur le placement en x,y (pas en coin) : mon premier mur « partiel » ne coupait pas le corridor (il commençait à la frontière y = 0.5 des boîtes centrées) ; recalibré après vérification numérique du ratio.
- Le socle `Ray_Check` ajoute le Context à l'arbre SANS `USE_WORLD_COORDS` (placements locaux) alors que ses rayons sont en coordonnées monde — non touché (règle existante), mais `DirectView` ajoute le contexte en coordonnées monde.

Temps de calcul constaté :
- `python -m pytest tests/test_DirectView.py -v` : 21 tests en ~1,1 s. La terminaison anticipée joue fortement : la paire totalement bloquée à seuil 100 % s'arrête au premier rayon bloqué (1 rayon tiré sur 10 prévus).

## Rapport — FaceCheck / moteur FaceSelection (2026-10-07)

Décisions d'implémentation :
- `FaceCheck.md` est le résumé de la famille : aucun fichier membre n'existe encore (FaceClearance, FaceIntersect, FaceOBB, FaceOrient seront déployés quand leur spec sera écrite). Conformément à la méthodologie, seul le moteur de sélection partagé est déployé ici, dans `clash_utils.py` :
  - `validate_face_selection(selection)` : validation/normalisation du dictionnaire (clés autorisées, types, presets d'orientation, vecteur normalisé) ; `None` et `{}` = sélection vide (toutes les faces) ;
  - `select_faces(vertices, faces, selection, material_names, extreme_tolerance)` : application des filtres (AND) sur le maillage triangulé d'un objet, retourne les triangles sélectionnés ;
  - `get_element_material_names(element)` : noms de matériaux d'un élément IFC (`IfcMaterial`, couches d'un `IfcMaterialLayerSet`/`Usage`, constituants d'un `IfcMaterialConstituentSet`).
- Pas de classe dans `Rules.py` à ce stade : les membres hériteront du moteur quand leurs specs existeront. Tests dans `tests/test_FaceCheck.py` (19 tests : schéma, filtres sur maillages construits à la main, matériaux sur modèles IFC générés).

Écarts et conventions tranchées (vs le .md de la famille) :
- Bornes de surface : strictes (« area above/below this bound ») — une aire exactement à la borne est exclue.
- Alignement d'orientation : normale à moins de 45° de la direction (constante partagée avec le reste du moteur). Preset `Side` : normale à moins de 45° du plan horizontal (|n_z| <= cos 45°), car « Side » n'est pas une direction unique.
- `extreme_faces` : réutilise `extreme_triangles` (slab extrême d'épaisseur 1 mm par défaut, faces de trous ignorées) restreint aux faces déjà sélectionnées ; ignoré sans `orientation` (spec).
- `materials` : V1 résout les matériaux au niveau de l'OBJET, pas de la face (le nom de la couche doit correspondre à un nom de matériau de l'élément) ; correspondance exacte, sensible à la casse. La granularité par face (style_index) attendra les règles membres.
- `interior_exterior` : fourni → `ValueError` explicite (spec : « kept in the specification, not implemented in V1 ») — refuser vaut mieux que retourner silencieusement des faces fausses.
- Clé inconnue → `ValueError` (attrape les fautes de frappe du dictionnaire).
- Triangles dégénérés (aire nulle) toujours exclus.

Problématiques rencontrées et solutions :
- L'API matériaux de ifcopenshell 0.8.4 : `material.add_layer` n'a pas de paramètre `thickness`, et `material.assign_material` prend `type=`/`material=` (pas `material_set=`) ; `material.add_material_set` crée par défaut un `IfcMaterialConstituentSet` (préciser `set_type="IfcMaterialLayerSet"` pour un jeu de couches).
- Le filtre `extreme_faces` réutilise `extreme_triangles`, qui travaille sur le maillage entier : le résultat est réintersecté avec la sélection courante via les coordonnées des triangles.

Temps de calcul constaté :
- `python -m pytest tests/test_FaceCheck.py -v` : 19 tests en ~0,5 s (maillages unitaires + petits IFC générés ; filtres vectorisés numpy).

## Rapport — OneObjectFace (2026-10-07)

Décisions d'implémentation :
- Classe `OneObjectFace(RuleCheckOneObject)` dans `ifcclash_plus/Rules.py`, `type = "OneObjectFace"`, exportée dans `ifcclash_plus/__init__.py`. Réutilise le moteur FaceSelection de l'étape 4 (`validate_face_selection`, `select_faces`, `get_element_material_names`).
- Nouvelles fonctions dans `clash_utils.py`, chacune testée unitairement : `triangles_share_geometry` (adjacence par sommet partagé, coordonnées exactes), `triangles_cross_properly` (croisement strict Möller–Trumbore : un segment traverse l'intérieur de l'autre triangle ; le contact arête/sommet ne compte pas), `triangle_penetration_depth` (profondeur = distance max d'un sommet au plan de l'autre), `distance_between_triangles` (distance exacte via faces OCC, `triangle_to_occ_face` existant).
- Groupes A et B appariés « all against all » : paire avec elle-même ignorée, chaque paire testée une fois (déduplication par identité géométrique, ordre indifférent), un clash par paire par check échoué.
- Résultat : `ClashResultOneObject` avec `check` ("distance"/"intersection"/"orientation"), `value` (la valeur mesurée : distance en m, profondeur d'intersection en m, angle en degrés) et `face_a`/`face_b` (normale et aire des deux faces de la paire).
- Modèles générés dans `tests/test_OneObjectFace.py` : cube unitaire (distances, orientations, adjacence) et élément « croisé » (deux plaques qui se traversent, une seule représentation à deux solides) pour l'auto-intersection.

Écarts et conventions tranchées (vs le .md de la règle) :
- Bornes inclusives : distance == min ou == max → conforme (seulement plus proche/plus loin échoue) ; écart d'angle == angle_tolerance → conforme.
- `skip_adjacent` ne s'applique qu'au check distance (spec : « skipped by this check ») ; l'adjacence se détecte par sommet partagé du maillage.
- « Intersection by more than tolerance in depth » : un croisement STRICT des triangles (segment traversant l'intérieur) échoue si la profondeur de pénétration (distance max d'un sommet au plan de l'autre) dépasse la tolérance ; les triangles qui se touchent par une arête ou un sommet ne croisent pas et passent. La « profondeur » au niveau triangle est une convention (voir helper), elle filtre les contacts rasants numériques.
- L'angle mesuré est l'angle entre les normales des deux faces appariées (spec) ; noter que l'exemple « chambranle » de la spec (sélection `orientation = Top` + `angle = 180`) est incohérent en lui-même (deux faces du haut ont des normales parallèles, l'angle serait 0) — la sélection des faces et l'angle visé restent à la charge de l'utilisateur.
- `intersection_tolerance` absent → 0 ; `angle_tolerance` absent → 0 ; `min` > `max` → ValueError ; aucun check activé → ValueError ; `angle` obligatoire si `orientation` activé.

Problématiques rencontrées et solutions :
- `triangle_to_occ_face` (existant) n'accepte pas les tableaux numpy (`if not triangle` ambigu) : `distance_between_triangles` convertit en listes Python avant l'appel, sans modifier la fonction existante.
- Un élément avec deux représentations assignées ne produit que la première dans l'itérateur : l'élément auto-intersecté est construit avec UNE représentation contenant deux `IfcExtrudedAreaSolid` (le maillage contient bien les triangles des deux plaques).
- Le check d'intersection en « all against all » est en O(n²) par objet avec préfiltres absents en V1 : acceptable pour les peaux de test (24 triangles) ; à surveiller pour de gros maillages (une préselection par FaceSelection réduit n).

Temps de calcul constaté :
- `python -m pytest tests/test_OneObjectFace.py -v` : 22 tests en ~0,95 s (les checks par paire dominent : distance OCC par paire sur le cube complet sans skip = 46 paires).

## Rapport — ClearanceForDoors (2026-10-07)

Décisions d'implémentation :
- Classe `ClearanceForDoors(RuleCheckTwoObjects)` dans `ifcclash_plus/Rules.py`, `type = "ClearanceForDoors"`, exportée dans `ifcclash_plus/__init__.py`.
- Nouvelles fonctions dans `clash_utils.py`, chacune testée unitairement : `get_local_placement_axes` (origine + axes X/Y/Z du placement, via `ifcopenshell.util.placement`), `get_door_operation_type` (OperationType via `IsTypedBy`→`IfcDoorType` en IFC4, via `IsDefinedBy`→`IfcDoorPanelProperties` en IFC2x3), `parse_door_operation` (classification V1 : swing/sliding/unknown, feuilles, côté des paumelles), `make_box_zone` / `make_arc_zone` (zones OCC construites en coordonnées monde : prisme rectangulaire, quart de disque approché par 16 segments, extrudés en hauteur), `max_penetration_depth` (classifieur `BRepClass3d_SolidClassifier` + distance sommet↔enveloppe).
- Dimensions par défaut issues de la géométrie : maillage LOCAL de la porte (itérateur natif sans `USE_WORLD_COORDS`) → largeur selon X, hauteur selon Z ; largeur de vantail = largeur / feuilles.
- Cibles : shape OCC (préfiltre distance `BRepExtrema` avec la zone) + sommets monde (profondeur de pénétration). Clash si profondeur > tolérance ; un résultat par (porte, objet), portant la pire zone.
- Résultat : `ClashResultTwoObjects` avec `penetration_depth` (m) et `zone` (shape, side, leaf, width, depth, height).
- Modèles générés dans `tests/test_ClearanceForDoors.py` : porte IFC4 0,90×2,10 avec `IfcDoorType.OperationType`, trois blocs (dans le balayage, derrière, loin).

Écarts et conventions tranchées (vs le .md de la règle) :
- Méthode 2 (géométrie / arc Curve2D) NON implémentée en V1 : sans OperationType exploitable → repli conservateur (rectangles des deux côtés), conformément à la spec. `ParameterTakesPrecedence` = False (la géométrie devrait gagner) n'est pas distingué : sans lecture géométrique, l'OperationType reste utilisé s'il existe (consigné).
- Convention de placement : l'origine locale de la porte est au bord de l'ouverture (côté paumelle gauche), X le long du mur, Y à travers, Z vertical ; le vantail balaie vers le local +Y (« Front »). Les côtés Front/Back suivent cet axe (spec : « relative to the door placement axis »).
- Paumelles : `SingleSwingLeft` → paumelle à x=0 ; `Right` → à x=largeur ; `DoubleDoorSingleSwing` → 2 feuilles, paumelles gauche et droite (convention IFC).
- Sides : Swing = côté du balayage (+Y) ; Both = arc devant + rectangle derrière ; Front = arc ; Back = rectangle derrière. Porte à direction inconnue : rectangles des deux côtés, quel que soit Sides (spec).
- Portes coulissantes : Swing = rectangles de PASSAGE devant ET derrière l'ouverture (V1 : le coulisseau est dans le mur, la contrainte utile est le passage) ; Front/Back = rectangle du côté demandé.
- `Zone_Shape = Rectangle` : une zone par côté (l'ouverture, pas par vantail), contrairement à l'arc qui a une zone par vantail.
- Profondeur de pénétration : max sur les sommets de la cible strictement intérieurs à la zone, de leur distance à l'enveloppe ; contact tangent (aucun sommet strictement intérieur) → profondeur 0 → ignoré.

Problématiques rencontrées et solutions :
- `BRepExtrema` entre un sommet INTÉRIEUR et le solide renvoie 0 : la profondeur doit se mesurer contre l'ENVELOPPE (composé des faces de la zone, `TopExp_Explorer`).
- `BRepPrimAPI_MakeBox` avec `gp_Ax2` mélange les axes (direction principale = Z du repère) : zones rectangulaires reconstruites en prisme `MakePolygon`+`MakeFace`+`MakePrism`, comme les zones en arc.
- L'énumération IFC4 s'écrit `SINGLE_SWING_LEFT` (pas `SingleSwingLeft`, style 4x3) ; `type.assign_type` prend `related_objects`/`relating_type`.
- `IsTypedBy[i].RelatingType` est une entité unique (pas une liste).

Temps de calcul constaté :
- `python -m pytest tests/test_ClearanceForDoors.py -v` : 14 tests en ~1,2 s. Par porte : construction des zones (OCC, négligeable) puis par (objet, zone) une distance `BRepExtrema` et, si contact, un classifieur par sommet — adapté aux petits ensembles de cibles.

## Rapport — FreeSpace (2026-10-07)

Décisions d'implémentation :
- Classe `FreeSpace(RuleCheckOneObject)` dans `ifcclash_plus/Rules.py`, `type = "FreeSpace"`, exportée dans `ifcclash_plus/__init__.py`. Pas de Target : le Context est un `Select` passé au constructeur (fichiers propagés depuis le Source dans `run()`, sur le modèle de `Ray_Check`). `RuleCheckComplex` (brouillon cassé) n'a pas été modifié.
- Nouvelles fonctions dans `clash_utils.py`, chacune testée unitairement : `lowest_footprint` (empreinte horizontale = union shapely des triangles du slab le plus bas, z du sol), `cylinder_solid` (sonde cylindre OCC), `shapes_intersect_volume` (volume de l'intersection booléenne : 0 = pas de chevauchement, les contacts tangents n'ont pas de volume).
- Empreinte : le cylindre doit tenir DANS l'empreinte (shapely `contains`, la tangence intérieure passe) ; les obstacles sont testés en 3D : distance `BRepExtrema` > 0 → libre, sinon intersection booléenne (volume > 1e-9 → bloqué, volume nul → contact tangent autorisé).
- Recherche : grille régulière de pas D/4 couvrant l'empreinte, DÉMARRÉE à rayon des murs (les placements tangents sont des candidates à part entière) ; premier placement libre gagne (arrêt immédiat). Sans candidate : affinage local (pas D/16) autour du meilleur nœud (distance max du centre au bord de l'empreinte) ; toujours rien → clash.
- Résultat : clash (`ClashResultOneObject`) par source sans placement ; les placements trouvés (position au sol + marge minimale aux obstacles et au bord de l'empreinte) sont exposés dans `rule.placements` (dictionnaire par entité source) — pas de résultat de clash pour une source libre, conformément à « a clash is raised » uniquement quand rien n'est trouvé.

Écarts et conventions tranchées (vs le .md de la règle) :
- Catégorie : « Complexe » dans le tableau de déploiement, mais la règle travaille sur un set Source + un set Context sans Target → `RuleCheckOneObject` + Context (même tranch que `Ray_Check`, qui est TwoObjects + context).
- Pas de pas de grille spécifié : D/4 (constantes `GRID_FRACTION`/`REFINEMENT_FRACTION`), affinage D/16 autour du meilleur nœud échoué.
- « The first free placement wins » : la grille démarre à `min + rayon` pour que les positions tangentielles (autorised par « touching is allowed ») soient réellement des candidates — sinon elles sont de mesure nulle et jamais atteintes.
- La marge rapportée est la distance du cylindre placé aux obstacles et au bord de l'empreinte (0 pour un placement tangent).
- Source sans géométrie/empreinte → clash (aucun placement évaluable).

Problématiques rencontrées et solutions :
- pythonocc 7.9 : le volume d'intersection se calcule par `BRepGProp.brepgprop.VolumeProperties` (les noms `VolumeProperties_s`/`brepgprop_VolumeProperties` n'existent pas dans cette version) ; shapely : `buffer(..., quad_segs=)` (pas `resolution=`).
- Le test « tangence » initial était mal conçu : couloirs de 0,75 m (bloc 1,5 dans une salle 3×3) ; avec un couloir d'exactement 1,50 m le placement tangent est trouvé par la grille. Un disque de 1,60 m passe par les zones d'angle diagonales (distance au coin du bloc > rayon) — le cas « clash » de la tangence utilise un couloir de 1,50 m avec D=1,60.

Temps de calcul constaté :
- `python -m pytest tests/test_FreeSpace.py -v` : 12 tests en ~2,7 s. La grille d'une salle 4×4 avec D=1,5 (≈ 10×10 nœuds) s'arrête au premier nœud libre ; le coût dominant est l'ouverture IFC + itérateurs, pas la recherche.
