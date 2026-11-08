# Optimisation et traduction en C++

Je veux optimiser et préparer la traduction du code en C++.

Pour optimiser le script, je prévois d'utiliser le plus possible des parties de la bibliothèque d'OpenCASCADE (OCCT).

## Décisions d'architecture (arrêtées)

| Point | Décision |
|---|---|
| Périmètre | Moteur complet en C++ : toutes les phases (large, intermédiaire, fine), exécution des règles, lecture des IFC. Python ne garde que la sélection IDS et le post-traitement des résultats (criticity, actor, grouping, BCF, display). |
| Géométrie | Le moteur C++ lit les IFC lui-même via les bibliothèques C++ d'ifcopenshell (IfcParse / IfcGeom). Pas de conversion de shapes côté Python. |
| Noyau géométrique | OCCT (B-Rep). La phase fine travaille toujours sur les B-Rep issues de l'IFC (voir Sources de géométrie). |
| Sources de géométrie | L'IFC est la source de référence, toujours disponible. Un `.ifcview` existant peut servir de source **optionnelle** pour accélérer les phases large et intermédiaire, sans jamais être requis. Dans BonsaiViewer, les données déjà chargées par la visionneuse servent de troisième source (voir Intégration BonsaiViewer). |
| Bibliothèque | Le moteur est une bibliothèque C++ (`libifcclash_engine`) avec deux façades : bindings pybind11 pour le script, API C++ directe pour BonsaiViewer. |
| Sélection | ifctester / les facettes IDS restent en Python. Python transmet au moteur C++ les listes de GlobalId sélectionnés (source / target / context) pour chaque fichier. |
| Parallélisme | Séquentiel d'abord, pour valider la correction. Le parallélisme viendra ensuite (candidats : OCCT Parallel / répartition des paires). |
| Validation | Parité stricte avec le Python actuel : sur les modèles de Ifc_Model, le C++ doit produire exactement les mêmes paires source/target, règle par règle. Tout écart est un bug. La parité doit tenir avec et sans `.ifcview`. |

## Pipeline

Le pipeline ci-dessous s'applique aux **règles spatiales 2-objets**
(Intersection, Clearance, ClearanceAxisToAxis, Collision, Above/Below,
OBB_Above, OBB_Below, OBB_Front_And_Back, DirectView, TwoObjectsFace...).
Les règles 1-objet et non spatiales (Volume, Area, TopOrBottomSurface,
ObbHigh, ObbLength, Orientation, AngleBetween, Ray_Check...) ont leur
propre chemin d'exécution : pas de paires, donc pas de phase large ni
intermédiaire ; elles reçoivent en revanche le même cache de shapes et
de boîtes (voir Règles 1-objet).

Le pipeline suit le vocabulaire standard de la détection de collision :
**phase large** (broad phase), **phase intermédiaire** (mid phase),
**phase fine** (narrow phase), encadrées par une configuration et une
restitution.

| Phase | Hooks de la règle | Test | Correspondance ancienne numérotation |
|---|---|---|---|
| Configuration | `setup`, `narrow_level` | — | — |
| **Large** | `broad_volume` | Fixe : chevauchement d'AABB (BVH du moteur) | Étapes 0 et 1 |
| **Intermédiaire** | `mid_volume`, `mid_test` | Libre, choisi par la règle | Étapes 2 et 3 |
| **Fine** | `narrow_test` | Libre, verdict exact | Étape 4 |
| Restitution | `report` | — | — |

### Configuration

La règle lit et valide ses paramètres (`setup`) et déclare le niveau de
géométrie dont sa phase fine a besoin (`narrow_level` : `BRep` par
défaut, `Mesh` si la règle travaille sur des triangles).

### Phase large

Pour l'ensemble des objets sélectionnés, les AABB brutes sont calculées
une seule fois (voir Cache). La règle dérive ses propres AABB via
`broad_volume(element, role)` : la transformation est définie **règle par
règle** (gonflée de la tolérance, étendue directionnellement, etc.).
Le rôle (`Source` / `Target`) permet des volumes asymétriques : pour
`Above`, seule la source est étendue vers le haut.

Le moteur construit ensuite un BVH sur ces AABB et en déduit les paires
candidates. Le BVH est **reconstruit à chaque règle** (les boîtes de
l'arbre doivent être cohérentes avec `broad_volume`).

Le test de la phase large est **imposé** (chevauchement d'AABB) et
**n'est pas surchargeable** : un BVH n'accélère que cette question. Un
test arbitraire fourni par la règle empêcherait l'élagage de l'arbre et
ramènerait à tester les N×M paires. Le seul levier de la règle est donc
le volume.

### Phase intermédiaire

Pour les paires candidates, les OBB brutes sont calculées une seule fois
par objet (voir Cache) et la règle les modifie via `mid_volume`
(extrusion, détachement d'une face, gonflement de la tolérance).

`mid_test` applique ensuite un filtre grossier, **défini règle par
règle** (chevauchement OBB-OBB, distance entre OBB gonflées, test
dédié...), qui retire les paires les moins probables. Il n'y a pas
d'arbre à préserver : le test est libre.

### Phase fine

`narrow_test` lance la règle sur les géométries effectives et produit le
verdict. C'est normalement la partie la plus lourde, mais les deux
phases de préfiltrage ont dû permettre de la limiter au maximum.

### Restitution

`report` transforme le verdict en `ResultInfo` (distance, points, mode,
drapeaux...) dans le format attendu par le post-traitement Python.

## Convention de nommage des phases

1. **Préfixe = phase, suffixe = action.** `broad_` / `mid_` / `narrow_`
   disent *quand* le code s'exécute ; `_volume` *construit* un volume
   englobant, `_test` *décide*.
2. **Le suffixe dit aussi le coût.** `_volume` est appelé une fois par
   élément (O(n)) ; `_test` une fois par paire candidate (O(paires)).
3. **Les noms décrivent le rôle, pas la structure de données.** Pas de
   `compute_obb` ni de `bvh_filter` : si une phase change de forme
   englobante (capsule, k-DOP…), le nom reste valable.
4. **Les phases large et intermédiaire ne peuvent qu'éliminer.** Elles
   retournent `Candidate::Rejected` / `Candidate::Kept`, jamais un
   booléen « clash ». Seule `narrow_test` produit un verdict. Elles
   doivent être **conservatrices** : une paire réellement en défaut ne
   doit jamais être rejetée.
5. **Défauts fournis.** Une règle ne surcharge que ce dont elle a besoin :

| Hook | Défaut |
|---|---|
| `setup` | aucun paramètre |
| `narrow_level` | `Level::BRep` |
| `broad_volume` | AABB brute gonflée de l'`uncertainty` de la source |
| `mid_volume` | OBB brute gonflée de l'`uncertainty` de la source |
| `mid_test` | `Candidate::Kept` (aucun filtre) |
| `narrow_test` | **obligatoire** |
| `report` | verdict + données nominales standard |

### Interface de base

```cpp
enum class Candidate { Rejected, Kept };
enum class Role      { Source, Target };
enum class Level     { Boxes, Mesh, BRep };

class PairRule {
public:
    virtual ~PairRule() = default;

    // Configuration
    virtual void  setup(const RuleParams&) {}
    virtual Level narrow_level() const { return Level::BRep; }

    // Phase large (le BVH appartient au moteur)
    virtual Bnd_Box broad_volume(const ElementGeometry& e, Role role) const;

    // Phase intermédiaire
    virtual Bnd_OBB   mid_volume(const ElementGeometry& e, Role role) const;
    virtual Candidate mid_test(const Bnd_OBB& source, const Bnd_OBB& target) const {
        return Candidate::Kept;
    }

    // Phase fine
    virtual Verdict narrow_test(const ElementGeometry& source,
                                const ElementGeometry& target) const = 0;

    // Restitution
    virtual ResultInfo report(const Verdict& v) const;
};
```

### Exemple : Clearance

```cpp
class Clearance : public PairRule {
    double clearance_ = 0.05;
public:
    void setup(const RuleParams& p) override { clearance_ = p.get("clearance", 0.05); }

    Bnd_Box broad_volume(const ElementGeometry& e, Role) const override {
        return inflate(e.boxes.aabb, clearance_ + e.boxes.uncertainty);
    }

    Candidate mid_test(const Bnd_OBB& a, const Bnd_OBB& b) const override {
        return obb_distance(a, b) <= clearance_ ? Candidate::Kept : Candidate::Rejected;
    }

    Verdict narrow_test(const ElementGeometry& a, const ElementGeometry& b) const override {
        auto d = exact_distance(a.brep(), b.brep());
        return { d.value < clearance_, d };
    }
};
```

### Règles 1-objet

Même logique, sans les phases par paires :
`setup` → `narrow_test(element)` → `report`.

### Statistiques par phase

Les noms étant fixes, le moteur trace pour chaque règle le nombre de
paires en entrée et en sortie de chaque phase, et son temps :

```
Clearance  broad: 48 210 → 1 342   mid: 1 342 → 187   narrow: 187 → 12   (2,4 s)
```

On voit immédiatement quelle phase filtre mal ou laquelle coûte le plus.

## Sources de géométrie

Les règles ne connaissent jamais la source de la géométrie : elles
demandent des boîtes, un maillage ou une B-Rep à un `GeometryProvider`,
qui choisit la source par niveau et par élément.

```
Pipeline / Règles
      │  boxes(id) / mesh(id) / brep(id)
      ▼
GeometryProvider  (cache par RuleFile, politique, repli par élément)
      │                      │
      ▼                      ▼
IfcSource               IfcViewSource (optionnelle)
boxes, mesh, brep       boxes, mesh
```

### Le format `.ifcview`

- Le format et son code font partie d'**IfcOpenShell** (`src/ifcviewer`,
  LGPL v3) ; BonsaiViewer n'en est qu'une interface. Il ne crée donc pas
  de dépendance à BonsaiViewer.
- IfcConvert peut le générer via le plugin de sérialisation
  `geometry.ifcview` (sans Qt ni GPU).
- La lecture (`IfcViewReader`, `IfcViewFormat.h`, `VertexQuantization.h`)
  ne dépend que de zstd et d'Eigen.
- Contenu : maillages dédupliqués (instancing), instances (translation en
  double, partie linéaire en float), table des éléments (GUID, nom,
  type), georef. Sommets quantifiés sur u16 relativement à la boîte du
  mesh. Pas de relations ni de propriétés IFC.
- La géométrie est celle de l'itérateur IfcOpenShell (noyau
  `hybrid-cgal-simple-opencascade` par défaut, flèche réglée dans
  l'application qui a produit le fichier). Seul le niveau LOD0 est
  utilisable : le LOD1 est trop décimé pour un clash.

### Données communes

```cpp
struct ElementKey {
    uint32_t    file_index;   // quel IFC du RuleFile
    std::string global_id;    // clé partagée avec Python et le .ifcview
};

struct ElementBoxes {
    Bnd_Box aabb;
    Bnd_OBB obb;
    double  uncertainty;      // 0 pour l'IFC ; quantification + flèche pour le .ifcview
};
```

`uncertainty` garantit que les phases large et intermédiaire restent
conservatrices : les volumes sont gonflés de
`tolérance de la règle + uncertainty`. Une boîte issue du `.ifcview`
peut laisser passer quelques paires en trop, jamais en perdre.

### Interface de source

```cpp
class GeometrySource {
public:
    virtual ~GeometrySource() = default;
    virtual std::string_view name() const = 0;
    virtual bool supports(Level) const = 0;
    virtual bool covers(const ElementKey&) const = 0;

    virtual ElementBoxes                boxes(const ElementKey&) = 0;
    virtual std::shared_ptr<const Mesh> mesh (const ElementKey&) = 0;
    virtual std::optional<TopoDS_Shape> brep (const ElementKey&) { return {}; }
};
```

- **`IfcSource`** : IfcParse + IfcGeom (noyau OCC). Fournit tous les
  niveaux ; seule source de B-Rep. Conversion **à la demande** : un
  élément rejeté en phase large ou intermédiaire n'est jamais converti
  en B-Rep.
- **`IfcViewSource`** : lit les métadonnées à l'ouverture, décompresse
  les chunks à la demande. Fournit boîtes et maillages.

### Choix de la source par phase

| Phase | Demande | Source effective |
|---|---|---|
| Large | `boxes()` | `.ifcview` si valide, sinon IFC |
| Intermédiaire | `boxes()` | `.ifcview` si valide, sinon IFC |
| Fine | `brep()` (ou `mesh()` selon `narrow_level`) | **IFC, toujours** |

Conséquence : **le résultat ne dépend pas de la source**, seul le temps
de calcul change. La parité stricte est conservée.

### Politique et validation

```cpp
enum class CachePolicy { Off, Auto, Require };
```

- **À l'ouverture**, le provider valide le `.ifcview` : version du format
  (actuellement 19), lisibilité, fraîcheur. S'il est rejeté : repli sur
  l'IFC seul avec un avertissement (`Auto`), ou erreur (`Require`).
- **Par élément**, repli sur l'IFC si l'élément est absent du `.ifcview`.
- **Éléments « gross »** : au-delà de la limite d'ouvertures
  (`voidLimit`), BonsaiViewer enregistre l'élément sans soustraire les
  ouvertures. Ses boîtes restent utilisables (plus grandes, donc
  conservatrices), mais son maillage ne doit pas servir en phase fine.

### Fraîcheur

Le `.ifcview` ne contient aucun lien vérifiable avec l'IFC source. Un
manifeste est écrit à côté du fichier quand le moteur produit lui-même
le cache :

```json
// modele.ifcview.manifest.json
{
  "ifc_sha256": "…",
  "ifcopenshell_version": "0.9.x",
  "kernel": "hybrid-cgal-simple-opencascade",
  "linear_deflection": 0.001,
  "angular_deflection": 0.5,
  "ifcview_version": 19
}
```

- **Avec manifeste** : comparaison du hash de l'IFC (coût négligeable
  devant la géométrie).
- **Sans manifeste** (fichier produit par BonsaiViewer) : option
  `trust` / `mtime` / `reject`. Défaut proposé : `mtime` (le `.ifcview`
  doit être plus récent que l'IFC), avec avertissement.

### Écriture du cache (optionnelle)

Après un calcul depuis l'IFC, le moteur peut écrire `modele.ifcview` et
son manifeste en réutilisant les sources du plugin IfcConvert
(`IfcViewAssembler`, `IfcViewWriter`). Le lancement suivant est plus
rapide, et le fichier s'ouvre aussi dans BonsaiViewer.

### Compilation

Option CMake `IFCCLASH_WITH_IFCVIEW` (activée par défaut). Désactivée,
elle retire zstd et le dossier `sources/ifcview/` : le moteur fonctionne
en IFC seul. Les fichiers repris d'IfcOpenShell restent sous LGPL v3,
en-têtes conservés, ce qui est compatible avec la licence Apache 2.0 du
projet.

### Organisation du code

```
engine/
  core/        ElementKey, ElementBoxes, Mesh
  sources/
    GeometrySource.h
    IfcSource.{h,cpp}
    ifcview/   IfcViewSource.{h,cpp}, Manifest.{h,cpp}
               third_party/  (IfcViewReader, IfcViewFormat, VertexQuantization — LGPL v3)
  provider/    GeometryProvider.{h,cpp}, CachePolicy.h
  pipeline/    phases large, intermédiaire, fine
  rules/
  bindings/    pybind11
```

## Intégration BonsaiViewer

Dans BonsaiViewer PLUS, le moteur peut réutiliser les données déjà
chargées par la visionneuse au lieu de relire les fichiers. C'est une
troisième source, `ViewerSource`, qui s'insère dans le
`GeometryProvider` comme les deux autres.

```
                 GeometryProvider
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
    IfcSource     IfcViewSource     ViewerSource   (côté BonsaiViewer)
  (fichier IFC)   (fichier .ifcview) (mémoire de la visionneuse)
```

### Données réutilisables

| Donnée en mémoire | Où (IfcOpenShell `src/`) | Utile pour |
|---|---|---|
| `elements` : GUID, nom, type | `ifcviewer/ModelGpuData.h` | Correspondance GlobalId ↔ objet |
| `instances[]` avec `world_aabb_min/max` | `ifcviewer/InstancedGeometry.h` (`InstanceInfo`) | Phase large directement |
| `placement_transformation` (double), `transform` composé (float) | `InstanceInfo` | Placement des maillages en repère monde |
| `mesh_triangles_cache` : positions + indices LOD0 sur CPU | `ModelGpuData` | OBB (phase intermédiaire), règles sur maillage |
| `mesh_local_volumes` | `ModelGpuData` | Pré-filtre de la règle Volume |
| Fichier IFC parsé (`ifcopenshell::file*`) | `bonsaiviewer/services/IfcDataAccess` | Phase fine : B-Rep sans reparser l'IFC |
| Moteur IDS C++ | `bonsaiviewer/ports/ifctester`, `services/IdsEngine` | Sélection source / target / context sans Python |

Gain principal : ni parsing IFC, ni passage par Python pour la
sélection. Il ne reste que la conversion IfcGeom des éléments qui
atteignent la phase fine.

### Comportement de `ViewerSource`

- **`boxes()`** : lit `world_aabb` dans `InstanceInfo`, sans copie. L'OBB
  est calculée à la demande depuis `mesh_triangles_cache`.
- **`mesh()`** : vue sur `mesh_triangles_cache` plus la transformation de
  l'instance.
- **`brep()`** : délègue à une `IfcSource` construite sur le
  `ifcopenshell::file*` déjà ouvert par la visionneuse.

### Contraintes

1. **Résidence du cache de triangles.** En streaming,
   `mesh_triangles_cache` est libéré quand un chunk sort de la mémoire
   GPU (`unloadChunk`) : son contenu dépend de la caméra. Si un mesh
   n'est pas résident, `ViewerSource` relit le chunk depuis le
   `.ifcview` (`IfcViewReader`) ou revient à l'IFC. `instances`,
   `world_aabb` et `elements` restent toujours en mémoire : la phase
   large est toujours disponible.
2. **Cache désactivable.** `ViewportHost::wantsCpuMeshTriangles()` peut
   renvoyer `false` (cas de la version web) : `ViewerSource` doit le
   vérifier et se replier.
3. **Concurrence.** Le thread de streaming modifie ces structures. Le
   moteur tourne dans un thread de travail, avec un instantané des
   données stables (instances, AABB, éléments) pris au lancement, et un
   accès verrouillé au cache de triangles.
4. **Repère et précision.** `world_aabb` et `transform` sont en float et
   incluent la fédération telle qu'affichée. Pour garantir l'invariance
   de source, les résultats sont exprimés dans le même repère que le
   chemin IFC : `placement_transformation` (double) avec la même
   composition de fédération. L'arrondi float s'ajoute à
   l'`uncertainty` de `ViewerSource`.
5. **La visibilité ne filtre pas.** Masquer ou isoler des éléments dans
   la vue ne change pas les résultats. La sélection vient uniquement de
   l'IDS.
6. **Sens de la dépendance.** Le moteur ne connaît que l'interface
   `GeometrySource` et n'inclut aucun en-tête de la visionneuse.
   `ViewerSource` vit dans BonsaiViewer et implémente cette interface :
   la visionneuse dépend du moteur, jamais l'inverse. C'est ce qui garde
   le moteur utilisable hors de BonsaiViewer.

### Architecture d'ensemble

```
libifcclash_engine (C++, sans dépendance à la visionneuse)
   ├── bindings pybind11  → script Python : IFC (+ .ifcview optionnel)
   └── API C++ directe    → BonsaiViewer PLUS :
          IdsEngine (sélection) → engine.run(ViewerSource)
          → résultats affichés via SelectionService, AppearanceService, Tables
```

Le panneau Rules de la visionneuse (spécification « BonsaiViewer09
Clash Management ») lance ainsi le même moteur que le script, sur les
données déjà chargées.

## Cache (par RuleFile)

Un RuleFile parse les IFC et convertit les shapes **une seule fois** :

- shapes converties (le plus coûteux : la conversion IfcGeom), à la
  demande, seulement pour les éléments qui atteignent la phase fine ;
- AABB brutes de chaque objet (depuis le `.ifcview` si valide) ;
- OBB brutes de chaque objet (depuis le `.ifcview` si valide).

Chaque règle dérive ensuite ses volumes (`broad_volume`, `mid_volume`)
et le moteur reconstruit son BVH à partir de ces données brutes cachées.
Le cache mémoire ne franchit pas la frontière du RuleFile : un RuleFile
suivant repart d'un parse complet (le `.ifcview` sur disque, lui,
persiste).

## Interface Python / C++

L'interface d'appel reste à préciser (candidat naturel : pybind11).
Contrat d'entrée : les chemins IFC et les listes de GlobalId
(source / target / context, par fichier), plus la politique de cache.
Contrat de sortie : les résultats (paires source/target, statut, et les
données nominales — distance, points, mode...) sous une forme
permettant au post-traitement Python (criticity, actor, grouping, BCF)
de rester inchangé.

```python
results = engine.run(
    ifc_paths=["archi.ifc", "cvc.ifc"],
    selections=selections,          # GlobalIds issus de l'IDS, inchangé
    geometry_cache="auto",          # "off" | "auto" | "require"
    cache_dir=None,                 # par défaut, à côté de l'IFC
    write_cache=True,
)
```

## Tests

- **Parité** : mêmes paires que le Python actuel, règle par règle, sur
  `Ifc_Model` et `IFC_Test_Model`.
- **Invariance de source** : chaque règle tourne avec
  `geometry_cache="off"` puis `"require"`. Les paires doivent être
  identiques. Un écart signifie une `uncertainty` trop faible ou un
  repli par élément manquant.
- **Robustesse du cache** : `.ifcview` absent, corrompu, de version
  inconnue, plus ancien que l'IFC, ou incomplet → repli correct sur
  l'IFC (ou erreur en `Require`).

## Reste à préciser

1. **Table règle → hooks** : pour chaque règle spatiale 2-objets,
   `broad_volume` (par rôle), `mid_volume` et `mid_test`. C'est le
   principal contenu manquant de la spec.
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
5. **`uncertainty` du `.ifcview`** : formule exacte (pas de
   quantification `extent / 65535` à confirmer dans
   `VertexQuantization.h`, plus flèche de tessellation lue dans le
   manifeste ou valeur par défaut prudente si absent).
6. **Stabilité du format `.ifcview`** : ses en-têtes ne sont pas
   installés par IfcOpenShell ; suivre les changements de version et
   définir les versions acceptées.
7. **API C++ publique du moteur** pour BonsaiViewer : signature de
   `engine.run(...)` côté C++, format des résultats directement
   exploitable par les services de la visionneuse, annulation et
   progression d'un calcul lancé depuis l'interface.
8. **Instantané `ViewerSource`** : périmètre exact des données copiées
   au lancement et stratégie de verrouillage du cache de triangles
   face au thread de streaming.
