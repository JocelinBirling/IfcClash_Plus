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
| Session | Le moteur garde son état dans un objet `Session` qui vit le temps d'un RuleFile : fichiers parsés, `GeometryProvider` et cache. Python l'ouvre une fois puis lance les règles une à une (voir Interface Python / C++). |
| Familles de règles | Quatre pipelines partagent le provider et les statistiques : élément, paire, paire ou élément avec contexte, ensemble (voir Familles de règles). |
| Paramètres | Chaque règle déclare ses paramètres dans une struct typée décrite par une `RuleSpec`. Le registre C++ est la source unique du catalogue (voir Registre des règles). |
| Résultats | Le moteur rend des `ResultRecord` triés, qui reprennent exactement `ResultInfo.to_dict()`, plus la géométrie d'affichage tessellée et des diagnostics (voir Contrat de résultat). |
| Mode d'exécution | Le moteur ne connaît pas `state`. Il reçoit un `RunMode` (`Verdicts`, `InputsOnly`, `VerdictsAndDisplay`). `Final` et `Select` restent des modes de gestion côté Python. |
| Clé d'élément | En interne : `(file_index, entity_id)`. Le GlobalId sert de clé d'échange. Les GlobalId dupliqués sont signalés, jamais fusionnés. |
| Unités | Mètres en interne. La conversion se fait à la lecture de l'IFC. Les paramètres de longueur des règles sont exprimés en mètres. |
| OCCT | Une seule version d'OCCT dans le processus, partagée par `pythonocc-core`, `ifcopenshell` et `libifcclash_engine`. Elle est fixée dans `environment.yml` et `conda/meta.yaml`. |

## Pipeline

Le pipeline ci-dessous s'applique aux **règles spatiales 2-objets**
(Intersection, Clearance, ClearanceAxisToAxis, Collision, Above/Below,
OBB_Above, OBB_Below, OBB_Front_And_Back, DirectView, TwoObjectsFace...).
Les règles 1-objet et non spatiales (Volume, Area, TopOrBottomSurface,
ObbHigh, ObbLength, Orientation, AngleBetween, Ray_Check...) ont leur
propre chemin d'exécution : pas de paires, donc pas de phase large ni
intermédiaire ; elles reçoivent en revanche le même cache de shapes et
de boîtes (voir Règles 1-objet). La répartition complète des 28 règles
entre les quatre pipelines est donnée dans Familles de règles.

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

Le moteur remplit la struct de paramètres typée de la règle à partir de
la déclaration JSON, et la valide d'après sa `RuleSpec` (types, bornes,
valeurs d'enum) **avant** tout calcul (voir Registre des règles). La
règle n'analyse donc aucun paramètre elle-même. `setup` sert seulement à
préparer un état dérivé de ces paramètres (par exemple un angle converti
en cosinus). La règle déclare aussi le niveau de géométrie dont sa phase
fine a besoin (`narrow_level` : `BRep` par défaut, `Mesh` si elle
travaille sur des triangles) et le mode de sa phase large
(`broad_mode` : `Spatial` par défaut, `AllPairs` pour une règle sans
localité spatiale comme AngleBetween, qui teste alors les N×M paires
sans BVH).

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

`report` transforme le verdict en `ResultRecord` (distance, points, mode,
drapeaux...), qui reprend le contenu de `ResultInfo` attendu par le
post-traitement Python (voir Contrat de résultat).

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
| `setup` | rien à préparer |
| `narrow_level` | `Level::BRep` |
| `broad_mode` | `BroadMode::Spatial` |
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
enum class BroadMode { Spatial, AllPairs };

class PairRuleBase {
public:
    virtual ~PairRuleBase() = default;

    // Configuration (les paramètres typés sont déjà remplis et validés)
    virtual void      setup() {}
    virtual Level     narrow_level() const { return Level::BRep; }
    virtual BroadMode broad_mode()   const { return BroadMode::Spatial; }

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
    virtual ResultRecord report(const Verdict& v) const;
};

// Les paramètres typés de la règle, remplis par le moteur à partir de la RuleSpec
template <class Params>
class PairRule : public PairRuleBase {
public:
    const Params& params() const { return params_; }
    Params&       mutable_params() { return params_; }   // réservé au moteur
private:
    Params params_;
};
```

Les hooks sont `const` et une règle ne garde aucun état modifiable après
`setup`. C'est ce qui permettra de paralléliser la phase fine sans
toucher aux règles.

### Exemple : Clearance

```cpp
struct ClearanceParams {
    double clearance = 0.05;   // m : le seul endroit où figure la valeur par défaut
};

class Clearance final : public PairRule<ClearanceParams> {
public:
    Bnd_Box broad_volume(const ElementGeometry& e, Role) const override {
        return inflate(e.boxes.aabb, params().clearance + e.boxes.uncertainty);
    }

    Candidate mid_test(const Bnd_OBB& a, const Bnd_OBB& b) const override {
        return obb_distance(a, b) <= params().clearance ? Candidate::Kept
                                                        : Candidate::Rejected;
    }

    Verdict narrow_test(const ElementGeometry& a, const ElementGeometry& b) const override {
        auto d = exact_distance(a.brep(), b.brep());
        return { d.value < params().clearance, d };
    }
};

RuleSpec spec_clearance();   // voir Registre des règles
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

## Familles de règles

Toutes les règles ne suivent pas le schéma « paire → verdict ». Le
moteur a quatre pipelines. Ils partagent le `GeometryProvider`, les
statistiques par phase, l'annulation et le contrat de résultat.

| Pipeline | Hooks | Règles |
|---|---|---|
| `ElementPipeline` | `setup` → `narrow_test(e)` → `report` | Volume, Area, TopOrBottomSurface, LateralSurface, ProjectedSurface, ObbHigh, ObbLength, Orientation, OneObjectFace |
| `PairPipeline`, `Spatial` | phases large, intermédiaire et fine (ci-dessus) | Intersection, Intersection2, Clearance, Collision, ClearanceAxisToAxis, Above, Below, OBB_Above, OBB_Below, OBB_Front_And_Back, OBB_Custom, SurfaceRecover, TwoObjectsFace, ClearanceForDoors |
| `PairPipeline`, `AllPairs` | sans BVH : `mid_test` → `narrow_test` | AngleBetween |
| `ContextPipeline` | ceux de la paire ou de l'élément, plus `setup_context(const ContextIndex&)` | DirectView, Ray_Check (paires) ; FreeSpace (éléments) |
| `SetPipeline` | `setup` → `narrow_test(std::span<const ElementGeometry>)` → groupes → `report` | Alignement |

- **`ContextIndex`** : le moteur le construit une fois par exécution sur
  la liste contexte (BVH de boîtes, arbre de rayons). La règle le reçoit
  en lecture seule. Elle ne parcourt jamais le contexte élément par
  élément.
- **`SetPipeline`** : une règle d'ensemble voit tous les éléments à la
  fois, parce que son verdict dépend du groupe (Alignement regroupe des
  éléments colinéaires ou coplanaires). Elle rend un `ResultRecord` par
  élément et les groupes dans le bloc `alignment`.
- La table règle → hooks (broad, mid et narrow de chaque règle) reste le
  principal contenu à écrire (voir Reste à préciser).

## Registre des règles

Le registre C++ est la **source unique** de la description d'une règle :
type, famille, slots, paramètres, valeurs par défaut, bornes, unités,
documentation. Le `registry.py` Python ne fait plus qu'assembler le
catalogue.

```cpp
RuleSpec spec_clearance() {
    return RuleSpec::pair<Clearance>(
        "Clearance", "Clearance", {Slot::Source, Slot::Target},
        "Flags the pairs closer than clearance.",
        { param(&ClearanceParams::clearance, "clearance")
              .doc("Minimum clearance").unit(Unit::Metre).min(0.0) });
}

void register_all_rules(Registry& registry) {
    registry.add(spec_volume());
    registry.add(spec_clearance());
    // … une ligne par règle
}
```

- **Pointeurs de membre** : le nom d'un paramètre n'est écrit qu'une
  fois, à côté de son champ. Une faute de frappe ne compile pas. Le
  contrat implicite actuel disparaît (nom identique dans le registre,
  l'attribut de l'instance, la signature de `compute` et la clé JSON).
- **`RuleSpec`** porte la fabrique de la règle, le remplissage de la
  struct depuis le JSON, la validation (types, `min`/`max`, valeurs
  d'enum, nullable) et l'export `to_json()`, au format exact de l'entrée
  de catalogue actuelle.
- **Enregistrement explicite** par `register_all_rules`, pas par des
  variables statiques : dans une bibliothèque statique, l'éditeur de
  liens peut retirer ces objets, et la règle disparaît sans erreur.
- **Répartition C++ / Python du catalogue** :

| Information | Propriétaire |
|---|---|
| type, famille, slots, paramètres, fabrique, validation | C++ (`engine.catalogue_json()`) |
| `supports_grouping`, `supports_criticity`, `supports_actor`, `supports_exceptions` | Python (le post-traitement reste en Python) |
| facettes IDS | Python (ifctester) |
| `STATES`, `CATALOGUE_VERSION` | Python (contrats de l'IPC avec BonsaiViewer) |
| `implementation` : `"cpp"` ou `"python"` | Python, une entrée par règle pendant la migration |

## Contrat de résultat

```cpp
struct ResultRecord {
    ElementKey                source;
    std::optional<ElementKey> target;
    bool                      status;
    Measures                  measures;   // enum fixe : distance, penetration_depth,
                                          // contact_area, ratio, offset, hit_ratio,
                                          // angle, volume, area
    std::vector<PointPair>    points;
    std::vector<FacePair>     faces;      // en triangles
    std::optional<ObbPair>    obbs;
    std::variant<std::monostate, AxisBlock, RaycastBlock, ZoneBlock,
                 AxesBlock, AlignmentBlock> block;
    Flags                     flags;      // degraded, gross_element, fallback_source…
};

struct RunResult {
    std::vector<ResultRecord> results;     // triés par (source, target)
    DisplayPayload            display;     // vide en RunMode::Verdicts
    PhaseStats                stats;
    Diagnostics               diagnostics; // erreurs par élément, GlobalId dupliqués
};
```

- **Même contenu que `ResultInfo.to_dict()`**, champ pour champ. Un
  adaptateur Python reconstruit les `ClashResult` et `ResultInfo`
  actuels : le pipeline de gestion, l'export JSON et l'IPC ne changent
  pas.
- **Tri déterministe** par `(source, target)`. Indispensable pour
  comparer les paires une à une en test de parité, et pour que le
  parallélisme ne change pas l'ordre des résultats.
- **Un élément en échec ne fait pas échouer l'exécution.** Il produit un
  `flag` et une entrée dans `diagnostics`. Seule une configuration
  invalide lève une exception, et `RuleSpec` la détecte avant le calcul.
- **Géométrie d'affichage.** Les OBB, zones de porte, faces de contact,
  rayons et sondes sont produits par le moteur. Si le C++ ne rendait que
  des verdicts, Python devrait les recalculer. `DisplayPayload` porte
  donc des items avec une catégorie (axis, face, obb, zone, context,
  segment, point), une `ElementKey` et une géométrie **tessellée**
  (sommets et indices exposés en tableaux numpy). Aucune `TopoDS_Shape`
  ne traverse la frontière.
- **`RunMode`** remplace `state` côté moteur : `Verdicts` (exécution
  normale), `InputsOnly` (géométrie des entrées, sans calcul — l'ancien
  `Display_Input`), `VerdictsAndDisplay` (l'ancien `Display_Result`, et
  l'aperçu de l'IPC).
- **Schéma versionné** (`result_schema_version`). Un JSON Schema commun,
  testé des deux côtés, empêche les implémentations de diverger.

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
  api/         Session, RunRequest, RunResult, CancelToken, ProgressSink
               ← le seul en-tête public (script et BonsaiViewer)
  registry/    RuleSpec, Registry, register_all_rules, catalogue_json
  pipeline/    ElementPipeline, PairPipeline, ContextPipeline, SetPipeline,
               BVH (OCCT), ContextIndex, PhaseStats
  rules/       une règle = un .cpp (classe + struct de paramètres + RuleSpec)
  geometry/    algorithmes purs : Eigen, OCCT, Clipper2 (aucune notion d'IFC ni de règle)
  provider/    GeometryProvider.{h,cpp}, CachePolicy.h
  sources/
    GeometrySource.h
    IfcSource.{h,cpp}
    ifcview/   IfcViewSource.{h,cpp}, Manifest.{h,cpp}
               third_party/  (IfcViewReader, IfcViewFormat, VertexQuantization — LGPL v3)
  core/        ElementKey, ElementBoxes, Mesh, Units, Verdict, ResultRecord, Diagnostics
  bindings/    pybind11 : couche mince sur api/
tests/         tests unitaires C++ (Catch2 ou GoogleTest)
```

Les dépendances descendent strictement :
`api → registry → pipeline → rules → geometry → core`, et
`pipeline → provider → sources → core`. `geometry/` ne connaît ni l'IFC
ni les règles. `bindings/` n'appelle que `api/`.

Le `geometry/` C++ reprend un à un les modules du `geometry/` Python
issu du découpage de `clash_utils.py` (vecteurs, triangles, polygones,
faces, solides, OBB, arbres). Les tests Python de ces modules servent
d'oracle aux tests unitaires C++.

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
          IdsEngine (sélection) → Session(ViewerSource).run(...)
          → résultats affichés via SelectionService, AppearanceService, Tables
```

Le panneau Rules de la visionneuse (spécification « BonsaiViewer09
Clash Management ») lance ainsi le même moteur que le script, sur les
données déjà chargées.

## Cache (par RuleFile)

Le cache appartient à la `Session`, ouverte une fois par RuleFile (voir
Interface Python / C++). Il parse les IFC et convertit les shapes
**une seule fois** :

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

Liaison : pybind11, en couche mince sur `api/`. Contrat d'entrée : les
chemins IFC et la politique de cache à l'ouverture de la session, puis,
pour chaque règle, son type, ses paramètres moteur et les listes de
GlobalId (source / target / context, par fichier). Contrat de sortie :
le `RunResult` (voir Contrat de résultat), que le post-traitement Python
(criticity, actor, grouping, BCF) consomme sans changement.

### Une session par RuleFile

L'orchestration reste en Python : une règle par appel, plus les
`SelectRule`, les activations de dossier et les exceptions. Un appel
sans état qui recevrait les chemins IFC à chaque règle reparserait les
fichiers à chaque fois, et le cache par RuleFile n'existerait pas. Le
moteur garde donc son état dans une `Session` :

```python
with engine.Session(
    ifc_paths=["archi.ifc", "cvc.ifc"],
    geometry_cache="auto",          # "off" | "auto" | "require"
    cache_dir=None,                 # par défaut, à côté de l'IFC
    write_cache=True,
) as session:                       # parse et provider : une seule fois
    result = session.run(
        rule_type="Clearance",
        params={"clearance": 0.05},  # clés moteur seulement (catalogue)
        selections=selections,       # GlobalIds issus de l'IDS, inchangé
        mode="verdicts",             # "verdicts" | "inputs_only" | "verdicts_and_display"
        cancel=token,
        progress=callback,
    )
```

```cpp
class Session {
public:
    Session(std::vector<std::filesystem::path> ifc_paths, SessionOptions);
    Session(std::unique_ptr<GeometrySource> source, SessionOptions);   // ViewerSource

    RunResult run(const RunRequest&, const CancelToken&, ProgressSink&);

    // Exceptions : une règle évaluée sur un lot de paires, en un appel
    RunResult evaluate_pairs(const RunRequest&, std::span<const KeyPair> pairs);
};
```

- **`evaluate_pairs`** traite les `BooleanLeaf`. Aujourd'hui, une
  exception réexécute une règle sur chaque paire de résultat. Avec un
  appel par paire, la frontière Python/C++ serait traversée des milliers
  de fois : le lot est obligatoire.
- **GIL** : relâché pendant `run` et `evaluate_pairs`.
- **Annulation** : `CancelToken` vérifié entre les phases et toutes les
  N paires (la requête `cancel` de l'IPC s'y branche).
- **Progression** : le moteur la signale à un rythme limité ; le rappel
  Python reprend le GIL.

### Côté Python

```
ifcclash_plus/engine/
├── orchestrator.py        # sélections → GlobalIds → backend → adaptateur → pipeline
└── backends/
    ├── python_backend.py  # les compute() actuels : implémentation de référence
    └── cpp_backend.py     # Session C++, une par RuleFile
```

L'orchestrateur choisit le backend de chaque règle d'après le champ
`implementation` du catalogue. Une règle passe en C++ dès que sa parité
est verte, sans rien changer d'autre. Le backend Python reste disponible
pour les tests de parité.

Coût connu : les IFC sont parsés deux fois, par ifctester en Python pour
la sélection IDS, et par IfcParse en C++ pour la géométrie. C'est
acceptable au départ. Le `IdsEngine` C++ de BonsaiViewer est la piste
pour l'éliminer.

## Choix techniques

| Sujet | Choix | Raison |
|---|---|---|
| BVH | `BVH_BoxSet` + `BVH_PairTraverse` d'OCCT | `doc/IfcGeomTree.h` utilise déjà ce motif. Reconstruire l'arbre à chaque règle coûte O(n log n), négligeable. Pas de BVH maison. |
| Algèbre (remplace numpy) | Eigen | Déjà requis par `IfcViewReader` |
| Polygones 2D (remplace shapely) | Clipper2 | SurfaceRecover (polygones de contact), empreintes de FreeSpace |
| Liaison | pybind11 | nanobind est plus léger, à reconsidérer si les temps de compilation ou la taille du module posent problème |
| Build | CMake + scikit-build-core, dépendances via conda-forge | Cohérent avec `conda/meta.yaml` |
| OCCT | Une seule version dans le processus | `pythonocc-core` et `ifcopenshell` chargent déjà OCCT : une seconde version provoquerait des conflits de symboles |
| Parallélisme (plus tard) | Phase fine parallèle sur les paires candidates (`OSD_Parallel` ou TBB) | Préparé dès maintenant : hooks `const`, règles sans état après `setup`, conversion B-Rep paresseuse protégée par un `once_flag` par clé dans le provider |

## Ordre de migration

| Étape | Contenu | Ce qu'elle valide |
|---|---|---|
| 0 | Prérequis Python : imports relatifs, découpage de `clash_utils.py` en `geometry/` et `ifc/`, séparation de `state` | Le terrain |
| 1 | Squelette : `Session`, `IfcSource`, provider, registre, liaisons, règle **Volume** | Toute la chaîne, de bout en bout, sur la règle la plus simple |
| 2 | `PairPipeline` + Intersection, Clearance, Collision | BVH, statistiques par phase, parité sur les règles les plus utilisées |
| 3 | Above, Below, OBB_* | La table règle → hooks |
| 4 | AngleBetween, ClearanceAxisToAxis, TwoObjectsFace | Le gain le plus net : ces règles n'ont aucun préfiltre aujourd'hui |
| 5 | `ContextPipeline` (DirectView, Ray_Check, FreeSpace), `SetPipeline` (Alignement), SurfaceRecover, OneObjectFace, ClearanceForDoors, Intersection2 | Les règles hors du schéma de paire |
| 6 | `IfcViewSource` | Gain de temps sans effet sur les résultats |
| 7 | Parallélisme | Les résultats triés ne bougent pas |
| 8 | `ViewerSource` et API C++ pour BonsaiViewer | Le moteur reste indépendant de la visionneuse |

Les étapes 1 et 2 sont un **prototype** : elles tranchent le format
d'échange, l'API publique et le comportement du BVH sur des boîtes
modifiées. La SPEC est figée à leur issue.

## Tests

- **Unitaires C++** (Catch2 ou GoogleTest) sur `geometry/`, avec les
  mêmes cas que les tests `test_UnitRule_*` Python.
- **Parité** : mêmes paires que le Python actuel, règle par règle, sur
  `Ifc_Model` et `IFC_Test_Model` (avec `calibration.jsonl`). Les deux
  backends tournent dans le même test ; on compare les paires triées et
  les mesures, avec une tolérance documentée par mesure.
- **Prudence des préfiltres** : une option de debug `prefilter="off"`
  désactive les phases large et intermédiaire. Les résultats doivent
  être identiques avec et sans. C'est la vérification, règle par règle,
  que ces phases ne font qu'éliminer.
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
2. **Format d'échange** : la structure est fixée (voir Contrat de
   résultat). Restent à écrire le JSON Schema commun, le détail de chaque
   bloc (`axis`, `raycast`, `zone`, `axes`, `alignment`) et la tolérance
   de parité de chaque mesure.
3. **BVH** : OCCT retenu (voir Choix techniques). À valider pendant le
   prototype : le coût de la reconstruction par règle sur un gros
   modèle.
4. **Ordre de migration** : proposé (voir Ordre de migration), à
   confirmer à l'issue du prototype.
5. **`uncertainty` du `.ifcview`** : formule exacte (pas de
   quantification `extent / 65535` à confirmer dans
   `VertexQuantization.h`, plus flèche de tessellation lue dans le
   manifeste ou valeur par défaut prudente si absent).
6. **Stabilité du format `.ifcview`** : ses en-têtes ne sont pas
   installés par IfcOpenShell ; suivre les changements de version et
   définir les versions acceptées.
7. **API C++ publique du moteur** pour BonsaiViewer : la forme est
   posée (`Session`, `RunRequest`, `RunResult`, `CancelToken`,
   `ProgressSink` — voir Interface Python / C++). Restent à préciser le
   format des résultats directement exploitable par les services de la
   visionneuse et le comportement de l'annulation et de la progression
   pour un calcul lancé depuis l'interface.
8. **Instantané `ViewerSource`** : périmètre exact des données copiées
   au lancement et stratégie de verrouillage du cache de triangles
   face au thread de streaming.
9. **IfcOpenShell C++ sur conda-forge** : vérifier que le paquet expose
   les en-têtes et les bibliothèques d'IfcParse et d'IfcGeom. Sinon,
   compiler IfcOpenShell en sous-module, dans la même version que le
   paquet Python. C'est le principal risque de build.
10. **GlobalId dupliqués** : choisir le comportement côté Python quand
    un GlobalId de la sélection correspond à plusieurs éléments
    (envoyer toutes les entités, ou ignorer l'élément avec un
    avertissement).
11. **Parité Clipper2 / shapely** : les aires de contact de
    SurfaceRecover peuvent différer à la marge. Fixer la tolérance
    acceptée avant de porter la règle.
