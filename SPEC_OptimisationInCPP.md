# Optimisation et traduction en C++

Je veux optimiser et préparer la traduction du code en C++.

Pour optimiser le script, je prévois d'utiliser le plus possible des parties de la bibliothèque d'OpenCASCADE (OCCT).

## Décisions d'architecture (arrêtées)

| Point | Décision |
|---|---|
| Périmètre | Moteur complet en C++ : étapes 0 à 4, exécution des règles, lecture des IFC. Python ne garde que la sélection IDS et le post-traitement des résultats (criticity, actor, grouping, BCF, display). |
| Géométrie | Le moteur C++ lit les IFC lui-même via les bibliothèques C++ d'ifcopenshell (IfcParse / IfcGeom). Pas de conversion de shapes côté Python. |
| Sélection | ifctester / les facettes IDS restent en Python. Python transmet au moteur C++ les listes de GlobalId sélectionnés (source / target / context) pour chaque fichier. |
| Parallélisme | Séquentiel d'abord, pour valider la correction. Le parallélisme viendra ensuite (candidats : OCCT Parallel / répartition des paires). |
| Validation | Parité stricte avec le Python actuel : sur les modèles de Ifc_Model, le C++ doit produire exactement les mêmes paires source/target, règle par règle. Tout écart est un bug. |

## Pipeline

Le pipeline ci-dessous s'applique aux **règles spatiales 2-objets**
(Intersection, Clearance, ClearanceAxisToAxis, Collision, Above/Below,
OBB_Above, OBB_Below, OBB_Front_And_Back, DirectView, TwoObjectsFace...).
Les règles 1-objet et non spatiales (Volume, Area, TopOrBottomSurface,
ObbHigh, ObbLength, Orientation, AngleBetween, Ray_Check...) ont leur
propre chemin d'exécution : pas de paires, donc pas de BVH ni de filtre
OBB ; elles reçoivent en revanche le même cache de shapes et de boîtes.

### Étape 0 : Calcul des AABB

Pour l'ensemble des objets sélectionnés, on calcule les AABB brutes une
seule fois (voir Cache). En fonction de la règle lancée, la règle dérive
ensuite ses propres AABB modifiées : la transformation est définie
**règle par règle** (gonflée de la tolérance, étendue directionnellement,
etc.).

### Étape 1 : Établissement du BVH

On met en place un BVH pour trouver les paires d'éléments probables, à
partir des AABB modifiées de la règle. Le BVH est donc **reconstruit à
chaque règle** (les boîtes de l'arbre doivent être cohérentes avec la
transformation de l'étape 0).

### Étape 2 : Calcul des OBB

Pour les paires restantes, on calcule les OBB brutes (une seule fois
par objet, voir Cache) et la règle les modifie selon ses besoins
(extrusion, détachement d'une face, gonflement de la tolérance).

### Étape 3 : Règle avec OBB

On applique succinctement la règle avec les OBB : un filtre grossier,
**défini règle par règle** (chevauchement OBB-OBB, distance entre OBB
gonflées, test dédié...), qui retire les paires les moins probables.

### Étape 4 : Lancement de la règle

On lance la règle sur les géométries effectives. C'est normalement la
partie la plus lourde, mais les deux phases de préfiltrage ont dû
permettre de limiter au maximum cette phase.

## Cache (par RuleFile)

Un RuleFile parse les IFC et convertit les shapes **une seule fois** :

- shapes converties (le plus coûteux : la conversion IfcGeom) ;
- AABB brutes de chaque objet ;
- OBB brutes de chaque objet.

Chaque règle dérive ensuite ses boîtes modifiées et reconstruit son BVH
à partir de ces données brutes cachées. Le cache ne franchit pas la
frontière du RuleFile : un RuleFile suivant repart d'un parse complet.

## Interface Python / C++

L'interface d'appel reste à préciser (candidat naturel : pybind11).
Contrat d'entrée : les chemins IFC et les listes de GlobalId
(source / target / context, par fichier). Contrat de sortie : les
résultats (paires source/target, statut, et les données nominales —
distance, points, mode...) sous une forme permettant au post-traitement
Python (criticity, actor, grouping, BCF) de rester inchangé.

## Reste à préciser

1. **Table règle → filtre** : pour chaque règle spatiale 2-objets, la
   transformation d'AABB (étape 0), la transformation d'OBB (étape 2)
   et le test OBB succinct (étape 3). C'est le principal contenu
   manquant de la spec.
2. **Format d'échange** des résultats entre C++ et Python (schéma des
   champs, gestion des données par règle : points d'entrée, distances,
   drapeaux dégradés...).
3. **BVH** : s'appuyer sur un composant existant (BVH d'OCCT,
   opérations de ifcopenshell) ou écrire le nôtre — à trancher pendant
   le prototype, sachant qu'il doit accepter des boîtes modifiées.
4. **Ordre de migration** des règles vers le C++ (candidats pour
   commencer : les règles spatiales 2-objets les plus utilisées, et les
   5 règles sans préfiltre actuel — AngleBetween, ClearanceAxisToAxis,
   Ray_Check, DirectView, TwoObjectsFace — qui gagneront le plus).
