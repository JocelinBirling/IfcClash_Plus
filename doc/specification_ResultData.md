# Spécification — Structure de données des ClashResult

Statut : **proposition à corriger** — les exemples de la section 6
sont le support de relecture.
Date : 2026-10-15
Portée : `ifcclash_plus/RuleClass.py` (classes `ClashResult*`, `ClashResultInfo`),
`ifcclash_plus/Rules.py` (écriture des résultats), `tests/` (feuille de test
du contrat).

---

## 1. Contexte

L'état des lieux des `ClashResult` a montré :

- un noyau commun réel (`id`, `type`, `status`, `criticity`, `actor`,
  `source`/`target`), effectivement consommé par le pipeline ;
- 9 attributs plats déclarés dans `ClashResultTwoObjects`, dont 6 jamais
  remplis ;
- 19 sites dans `Rules.py` où chaque règle « balance » ses mesures en
  attributs dynamiques non déclarés (`axis_mode`, `zone`, `rays_cast`,
  `face_a`, `check`, `value`, `offset`...), lisibles uniquement par les tests ;
- `point1`/`point2` déclarés en annotation seule (attributs inexistants à
  l'exécution), alors que `clash_utils.py:820` produit déjà ces points sans
  les rattacher au résultat ;
- `ClashResultComplex` rendue indépendante : elle porte des listes
  (`sources`, `targets`) et ne partage plus que le noyau commun.

Décisions de conception :

1. **Mutualiser ~80 % des retours** des règles dans un petit nombre de blocs
   standardisés, lisibles par un consommateur générique (BCF, grille de
   sévérité `doc/Idea.md`, export C++). **Les ~20 % restants (les données
   propres à une seule règle) sont déclarés aussi** : des attributs de la
   classe, documentés — fonctionnement, unité et provenance (la règle
   qui les produit). Pas de dict libre.
2. **Ces blocs sont portés par une classe dédiée, `ClashResultInfo`**,
   posée sur le résultat (`result.info`), sans classes auxiliaires
   porteuses de comportement — les `NamedTuple` des entrées ne sont
   que des formes de données.
3. **Pas de dicts dans le stockage** : les mesures scalaires sont des
   **attributs déclarés** de la classe ; les structures (paires de
   points, paires de faces,
   OBB) sont des **NamedTuple** dans des listes annotées — des tuples
   avant tout : indexables, comparables à un tuple littéral, donc un
   `append` direct de tuple nu reste une valeur valide (rattrapé par
   `validate()`), avec en plus l'accès par attribut
   (`entry.face.normal`) et le `_asdict()` gratuit pour `to_dict()`.
   Plus aucun dict dans le stockage : le seul dict est produit à la
   frontière d'export (`to_dict()`, section 4).
4. **Standardiser au minimum** : aucun contrôle à l'exécution — ni
   alarme, ni exception pendant la run ; le contrat est vérifié au
   moment des tests.

Principe directeur : *le standard est défini par les consommateurs, le
propre-à-une-règle est défini par la règle — toujours en attribut déclaré
et documenté.* Une donnée entre dans le vocabulaire standard si plus d'une
règle la produit ou si un consommateur en a besoin ; sinon elle reste un
attribut documenté, produit par une seule règle, ignoré des
consommateurs génériques.

---

## 2. Le noyau commun (inchangé)

Porté par les trois classes `ClashResultOneObject`, `ClashResultTwoObjects`
et `ClashResultComplex` :

```python
result.id          # str — GUID (uuid4), attribué à la création
result.type        # str — "OneObjectResult" | "TwoObjectsResult" | "ComplexResult"
result.status      # bool — verdict du résultat (mis à False par les exceptions)
result.criticity   # list[str] — rempli par run_criticity()
result.actor       # list[str] — rempli par run_actor()
result.info        # ClashResultInfo — la classe porteuse (section 3)
```

Plus, selon la classe :

```python
# ClashResultOneObject
result.source                              # entity_instance

# ClashResultTwoObjects
result.source, result.target               # entity_instance

# ClashResultComplex (indépendante)
result.sources, result.targets             # list[entity_instance]
result.context                             # list[entity_instance] | None
```

Sont supprimés (absorbés par `ClashResultInfo`) : les 9 attributs plats de
`ClashResultTwoObjects` (`distance_between`, `penetration_depth`,
`volume_intersection`, `volume_ratio`, `containement_ratio`,
`surface_contact_area`, `penetration_direction`,
`clearance_violated_volume`) et les annotations `point1`/`point2`.

---

## 3. La classe porteuse `ClashResultInfo`

### 3.1 Les propriétés

Une seule classe, pas de dicts de stockage : tout est attribut annoté.
Les entrées structurées (points, faces, OBB) sont des `NamedTuple`
déclarés au-dessus de la classe — la documentation de chaque champ vit
dans sa définition, la forme d'export reste la table de la section 4.

```python
class PointEntry(NamedTuple):
    """Une entrée de source_points / target_points."""
    number: int                            # le numéro de paire
    point: tuple[float, float, float]
    label: str | None                      # libre (ex. "entry"/"exit")


class FaceData(NamedTuple):
    """Une face d'une paire, côté source ou target."""
    normal: tuple[float, float, float]     # unitaire
    area: float                            # m²
    triangles: list                        # triangles d'origine
                                           # (3 points chacun) ou []


class FaceEntry(NamedTuple):
    """Une entrée de source_faces / target_faces."""
    number: int                            # le numéro de paire
    face: FaceData


class ObbData(NamedTuple):
    """Un OBB porté par le résultat (objet propre ou zone de détection)."""
    center: tuple[float, float, float]
    axes: tuple                            # 3 directions orthonormées
    half_sizes: tuple[float, float, float]
    label: str | None                      # libre ("object", "zone"...)


class RaycastData(NamedTuple):
    """DirectView : le détail du lancer de rayons — provenance : une
    seule règle (DirectView). Les consommateurs ne lisent que
    hit_ratio (hit / planned) ; les segments servent à l'affichage."""
    planned: int          # rayons prévus
    cast: int             # rayons effectivement lancés
    hit: int              # rayons ayant touché un obstacle
    hit_segments: list    # segments origine→but, chaque segment : 2 points
    blocked_segments: list


class ZoneData(NamedTuple):
    """ClearanceForDoors : la zone de dégagement balayée par le
    bloc-porte — provenance : une seule règle (ClearanceForDoors).
    Le solide OCC reste dans le registre d'affichage ; ces seules
    dimensions sérialisables suffisent à le reconstruire."""
    side: str             # côté du bloc-porte (ex. "Front")
    leaf: str             # type de vantail (ex. "SingleSwingLeft")
    width: float          # largeur balayée (m)
    depth: float          # profondeur (m)
    height: float         # hauteur (m)


class ClashResultInfo:
    """Toutes les données qu'une règle attache à un résultat, hors noyau
    commun.

    Les mesures scalaires sont des attributs déclarés (vocabulaire de
    la section 4) : info.distance = 0.42. Les structures sont des
    listes de NamedTuple — des tuples : l'append direct d'un tuple nu
    reste valide. Aucun contrôle à l'écriture ni pendant la run — le
    contrat est vérifié aux tests (section 5). La plupart des
    propriétés restent vides la plupart du temps — la classe existe
    aussi pour porter les méthodes qui dispatchent selon le type de
    règle (section 3.5)."""

    # Le vocabulaire des mesures — étendre ici (section 4)
    MEASURE_ATTRIBUTES = frozenset({
        "distance", "penetration_depth", "contact_area", "ratio",
        "offset", "hit_ratio", "angle",
    })

    def __init__(self):
        # -- Les mesures scalaires : attributs déclarés, None = non
        #    mesurée (mêmes règles que les volumes ci-dessous). Toute
        #    pose passe par __setattr__ (suivie, sans contrôle) ; la
        #    première mesure POSÉE est la mesure nominale du résultat
        #    (ordre suivi par la classe). L'unité est portée par le
        #    vocabulaire (section 4).
        self.distance: float | None = None               # m
        self.penetration_depth: float | None = None       # m
        self.contact_area: float | None = None           # m²
        self.ratio: float | None = None                  # 0..1
        self.offset: float | None = None                 # m
        self.hit_ratio: float | None = None              # %
        self.angle: float | None = None                  # deg

        # -- Les points de contact / proximité, appariés PAR NUMÉRO :
        #    l'entrée n° N de source_points (PointEntry) répond à
        #    l'entrée n° N de target_points. Le numéro est posé par
        #    add_point_pair ; validate() contrôle qu'aucun numéro
        #    n'est orphelin.
        self.source_points: list[PointEntry] = []
        self.target_points: list[PointEntry] = []

        # -- Les faces, appariées PAR NUMÉRO : la face n° N de
        #    source_faces (FaceEntry) est vérifiée contre la face n° N
        #    de target_faces. Le numéro est posé par add_face_pair.
        #    Le centre d'une face se déduit de ses triangles.
        #    Pour une règle mono-objet, les deux côtés de la paire
        #    portent sur le même élément (le source).
        self.source_faces: list[FaceEntry] = []
        self.target_faces: list[FaceEntry] = []

        # -- Les mesures volumiques (grille doc/Idea.md) :
        #    attributs scalaires, None = non mesurée
        self.volume_intersection: float | None = None          # m³
        self.volume_ratio: float | None = None                 # 0..1, relatif au plus petit
        self.containment_ratio: float | None = None            # 0..1
        self.clearance_violated_volume: float | None = None    # m³

        # -- Les OBB, NON appariés : deux listes indépendantes (un
        #    élément peut porter son propre OBB et ses zones de
        #    détection, distinguées par label). ObbData est complet :
        #    le solide OCC se reconstruit depuis ses seules données.
        #    Le Custom_OBB de calcul reste dans le registre
        #    d'affichage.
        self.source_obbs: list[ObbData] = []
        self.target_obbs: list[ObbData] = []

        # -- Les données propres à une seule règle (l'ex « libre ») :
        #    des attributs déclarés comme les autres — pas de dict.
        #    Exigence : la documentation (fonctionnement, unité,
        #    provenance — la règle qui les produit). Un consommateur
        #    générique les ignore ; le test de la règle les assert.
        #    Pour en ajouter : déclarer l'attribut ici et dans la
        #    table d'export (section 4).
        #    ClearanceAxisToAxis :
        self.axis_mode: str | None = None        # "Perpendicular" | "MinDistance" | "Fallback"
        self.axis_degraded: bool | None = None  # True si fallback géométrique
        #    DirectView :
        self.raycast: RaycastData | None = None # détail du lancer de rayons
        #    ClearanceForDoors :
        self.zone: ZoneData | None = None       # la zone de dégagement

        # Ordre de pose des mesures (suivi interne pour la nominale)
        self._measure_order: list[str] = []
```

### 3.2 L'écriture suivie : `__setattr__` (silencieux)

L'écriture d'une mesure est une assignation d'attribut, interceptée
pour suivre l'ordre de pose uniquement — aucune validation, aucune
alarme, aucune exception : la règle écrit librement.

```python
    def __setattr__(self, name, value):
        if name in self.MEASURE_ATTRIBUTES:
            if name not in self._measure_order:
                self._measure_order.append(name)
        object.__setattr__(self, name, value)
```

- `info.distance = 0.42` — conforme : l'attribut est posé, l'ordre
  d'apparition des mesures est suivi ;
- `info.chek = 1.0` — nom hors vocabulaire : l'attribut est posé, mais
  il est invisible (ni suivi, ni exporté par `to_dict()`) — la faute ne
  se voit que dans la feuille de test, jamais pendant la run ;
- `info.ratio = "0.62"` — valeur non numérique : stockée telle quelle —
  faute remontée par `validate()` aux tests.

Pour les listes, que `append` n'intercepte pas, des helpers —
ce sont eux qui posent le **numéro de paire** (compteur propre à chaque
famille, points et faces indépendants) sur les deux côtés :

```python
    def add_point_pair(self, source, target, label=None) -> int:
        """Pose le numéro N sur les deux côtés, retourne N.
        Coerce l'entrée nue : PointEntry(N, tuple(source), label)."""
        ...

    def add_face_pair(self, source_face, target_face) -> int:
        """Coerce via FaceData(*source_face) : un tuple nu passe tel
        quel, aucune forme d'appel à changer dans les règles."""
        ...

    def add_source_obb(self, obb) -> None:
        """Coerce via ObbData(*obb)."""
        ...

    def add_target_obb(self, obb) -> None: ...
```

Le `append` direct reste possible : un NamedTuple **est** un tuple,
donc poser un tuple nu reste structurellement valide ; il échappe à
l'écriture et est rattrapé par `validate()` aux tests (contrôle
structurel, pas `isinstance`).

### 3.3 La lecture et le contrôle

```python
    # ---- lecture
    @property
    def primary_measure(self) -> str | None:
        """Le nom de la mesure nominale (première posée), None sinon."""
        return self._measure_order[0] if self._measure_order else None

    def measure(self, check) -> float | None:
        """La valeur de la mesure demandée, None si non posée."""
        ...

    @property
    def has_volumes(self) -> bool:
        """Vrai si au moins un attribut volumique est renseigné."""
        ...

    # ---- contrôle
    def validate(self) -> list[str]:
        """Passe de contrôle de tout le contenu (mesures posées
        numériques, points 3D, faces bien formées, OBB bien formés,
        blocs propres à une règle (`raycast`, `zone`) bien formés,
        numéros de paires appariés — aucun numéro orphelin d'un seul
        côté —, y compris les appends directs) — liste de fautes.
        Pure, sans effet de bord : appelée par la feuille de test
        (section 5), jamais pendant la run. Les champs NamedTuple
        nomment le fautif dans la faute
        (faces[2].face.area: str != float) au lieu d'un index."""
        ...

    def to_dict(self) -> dict:
        """La forme sérialisable du contrat (section 4) : c'est ici,
        et ici seulement, que les attributs et tuples deviennent des
        dicts."""
        ...
```

### 3.4 Conventions

- les valeurs restent typées (float, tuple, list) — jamais de chaîne pour
  un nombre ;
- `source_points`/`target_points` et `source_faces`/`target_faces` sont
  appariées **par numéro** : chaque entrée porte le numéro de sa paire
  (posé par les helpers, compteur par famille) — la face n° N de la
  source est vérifiée contre la face n° N de la target, le point n° N
  répond au point n° N ; `validate()` contrôle qu'aucun numéro n'est
  orphelin d'un seul côté — la provenance de chaque point/face est
  toujours explicite ; pour une règle mono-objet, les deux côtés de la
  paire portent sur le même élément (le source) ;
- ordre des listes = pertinence décroissante (faces par aire décroissante,
  points par distance croissante, OBB par pertinence) : `[0]` est
  toujours le représentant principal ;
- `measures` : la première mesure posée est la **mesure nominale** (celle
  qui porte le verdict), les suivantes sont des mesures secondaires ;
- l'**unité est portée par le vocabulaire** (section 4), pas par la
  donnée — une mesure est un float nu ;
- les OBB ne sont **pas** appariés : `source_obbs` et `target_obbs` sont
  deux listes indépendantes ;
- les données propres à une seule règle sont des **attributs déclarés**,
  pas un dict : pour en ajouter, déclarer l'attribut dans `__init__` et
  dans la table d'export (section 4), avec sa documentation —
  fonctionnement, unité éventuelle, provenance (la règle qui la
  produit) ; les consommateurs génériques les ignorent.

### 3.5 Les méthodes qui dispatchent par type de règle

Motivation de la classe : même vide, elle est le point d'attache naturel
de fonctions génériques qui adaptent leur comportement au type de
résultat/règle :

- `display_items(info, rule)` — synthèse des items d'affichage depuis les
  blocs (faces → items `"face"`, une couleur par côté source/target —,
  points → `"point"`, `raycast` (RaycastData) → segments,
  `source_obbs`/`target_obbs` → items `"obb"` reconstruits depuis le
  tuple quand le `Custom_OBB` de calcul n'est plus en vie), en lecture
  seule sur les résultats ;
- `to_bcf(info, result)` — le mapping BCF lit les mesures, `points`,
  les attributs volumiques et ignore les attributs propres à une
  règle ;
- la grille de sévérité (`doc/Idea.md`) lit `measure("penetration_depth")`,
  `volume_ratio`, etc.

Le dispatch reste conditionné par le contenu (`info.primary_measure`,
`info.faces`) plus que par `isinstance` sur la règle : un consommateur
teste ce que le résultat porte, pas la règle qui l'a produit.

---

## 4. La frontière d'export : `to_dict()` et `RESULT_SHAPE`

Le stockage est sans dicts (attributs + tuples) ; le dict apparaît à la
frontière d'export : `to_dict()` assemble les attributs et tuples sous les
clés du contrat, en appariant les entrées par leur **numéro de paire**
(de même pour les faces) pour produire les paires du contrat.
`RESULT_SHAPE` documente cette forme — c'est elle que consomment la
sérialisation, le futur C++ et la feuille de test :

```python
POINT = (float, float, float)            # tuple de 3 nombres

RESULT_SHAPE = {
    # measure : une entrée par mesure posée, la clé = le nom du check,
    # dans l'ordre de pose (la première = nominale)
    "measure": {
        "distance": {"value": float},
    },
    "points": [
        {
            "number": int,                # le numéro de paire
            "source": POINT,
            "target": POINT,
            "label": str,               # optionnel, libre
        },
    ],
    "faces": [
        {
            "number": int,                # le numéro de paire
            "source": {
                "normal": POINT,
                "area": float,
                "triangles": list,
            },
            "target": {"...": "..."},   # même forme que source
        },
    ],
    "volumes": {
        "intersection": float,           # m³
        "ratio": float,
        "containment": float,
        "clearance_violated": float,
    },
    "obbs": {
        # deux listes indépendantes, non appariées
        "source": [
            {
                "center": POINT,
                "axes": [POINT, POINT, POINT],
                "half_sizes": (float, float, float),
                "label": str,               # optionnel
            },
        ],
        "target": [ {"...": "..."} ],      # même forme que source
    },
    # -- Les blocs propres à une règle : présents seulement si posés,
    #    documentés dans la classe (fonctionnement + provenance) ;
    #    les consommateurs génériques les ignorent.
    "axis": {                           # ClearanceAxisToAxis
        "mode": str,
        "degraded": bool,
    },
    "raycast": {                        # DirectView
        "planned": int,
        "cast": int,
        "hit": int,                     # hit_ratio = hit / planned
        "hit_segments": [(POINT, POINT)],
        "blocked_segments": [(POINT, POINT)],
    },
    "zone": {                           # ClearanceForDoors
        "side": str,
        "leaf": str,
        "width": float,                 # m
        "depth": float,                 # m
        "height": float,                # m
    },
}
```

Décision FaceCheck (prise à l'implémentation) : les échecs du check « intersection » de la famille FaceCheck posent leur profondeur dans `penetration_depth` ; « distance » → `distance`, « orientation » → `angle`.

Vocabulaire des mesures (attributs déclarés — pour ajouter une mesure :
déclarer l'attribut dans `__init__`, l'ajouter à `MEASURE_ATTRIBUTES` et
à cette table) :

| Mesure | Unité (portée par le vocabulaire) | Produit aujourd'hui par |
|---|---|---|
| `distance` | m | ClearanceAxisToAxis, SurfaceRecover, FaceCheck (check « distance ») |
| `penetration_depth` | m | FaceCheck (check « intersection »), ClearanceForDoors (future : traversante) |
| `contact_area` | m² | SurfaceRecover |
| `ratio` | — (0..1) | SurfaceRecover |
| `offset` | m | Alignement |
| `hit_ratio` | — (0..1) | DirectView |
| `angle` | deg | ClearanceAxisToAxis, FaceCheck (check « orientation ») |
| `count` | — | Must check (non retenu pour l'instant, voir 6.11) |
| `quantity` | (unité de la propriété) | Must check quantités (futur) |

---

## 5. Le contrôle — aux tests uniquement

Aucun contrôle à l'exécution : ni alarme, ni exception, ni log pendant
la run. La règle écrit librement (`__setattr__` ne suit que l'ordre de
pose) ; le contrat est vérifié au moment des tests, par la feuille
`tests/test_structure_ResultShape.py` (section 6.12).

### 5.1 `validate()` — la passe de contrôle pure

`validate()` est une fonction pure : liste de fautes, sans effet de
bord, sans log. C'est le helper `assert_result_shape` de la feuille de
test qui l'appelle sur chaque résultat — aucun code de la run
(`end_rule_action`, `RuleFile.run`) ne l'appelle. Les fautes cherchées :
mesures posées non numériques, points 3D, faces et OBB bien formés (y
compris les appends directs), numéros de paires appariés — aucun numéro
orphelin d'un seul côté —, blocs propres à une règle bien formés.

### 5.2 Le golden test sur `to_dict()`

La feuille de test compare `result.info.to_dict()` à `RESULT_SHAPE`, en
**sous-ensemble** : toute clé écrite doit exister dans la référence avec le
bon type ; les blocs absents sont normaux (une règle remplit ce qu'elle
mesure). Voir 6.12.

Conséquence assumée : une mesure écrite hors vocabulaire
(`info.chek`) est invisible pour les consommateurs et **silencieuse** —
elle n'est détectée que si le test de la règle asserte ses mesures
(nom de la nominale, valeurs). C'est le prix de la simplicité : le
contrôle vit dans les tests, pas dans la run.

---

## 6. Les cas de figure — un exemple par règle

Valeurs illustratives. Ce sont ces remplissages qu'il faut relire et
corriger. On montre l'état final de `result.info` (le noyau du résultat —
`id`, `status`, etc. — est inchangé, section 2). Les tuples nus passés
aux helpers `add_*` sont coercés en NamedTuple (`FaceData(*source_face)`)
— les exemples ci-dessous restent valides tels quels.

### 6.1 Cas général — règle avec une simple mesure scalaire

Exemple : `Alignement` (décalage d'axe). Une seule mesure posée.

```python
result.info = ClashResultInfo()
result.info.offset = 0.42        # m — mesure nominale (première posée)
```

### 6.2 Plusieurs mesures + bloc libre — `ClearanceAxisToAxis`

La distance et l'angle sont deux mesures nommées (l'angle est dans le
vocabulaire) ; le mode d'axe est un attribut déclaré propre à la règle
(une seule règle le produit).

```python
result.info = ClashResultInfo()
result.info.distance = 0.031     # m — mesure nominale (première posée)
result.info.angle = 88.6         # deg — mesure secondaire
n = result.info.add_point_pair(
    (12.41, 3.02, 0.85),         # point sur la source
    (12.44, 3.05, 0.85),         # point sur la target
)
# → n = 1 ; source_points = [(1, (12.41, 3.02, 0.85), None)]
#          target_points = [(1, (12.44, 3.05, 0.85), None)]
result.info.axis_mode = "Perpendicular"   # "Perpendicular" | "MinDistance" | "Fallback"
result.info.axis_degraded = False         # True si fallback géométrique
```

### 6.3 Multi-mesures + multi-triangles — `SurfaceRecover`

Le cas complet : trois mesures posées (la première posée est la mesure
nominale), les triangles de contact dans `source_faces[0]` (entrée n° 1).

```python
result.info = ClashResultInfo()
result.info.contact_area = 0.0312    # m² — mesure nominale (première posée)
result.info.ratio = 0.62             # contact / aire d'appui attendue
result.info.distance = 0.003         # m
result.info.add_face_pair(
    (   # face de la source : (normal, area, triangles) — entrée n° 1
        (0.0, -1.0, 0.0),
        0.0312,
        [
            ((0.10, 2.71, 3.02), (0.34, 2.71, 3.02), (0.10, 2.71, 2.80)),
            ((0.34, 2.71, 3.02), (0.58, 2.71, 2.80), (0.10, 2.71, 2.80)),
        ],
    ),
    (   # face de la target — entrée n° 1 également
        (0.0, 1.0, 0.0),
        0.0312,
        [
            ((0.10, 2.70, 3.02), (0.34, 2.70, 3.02), (0.10, 2.70, 2.80)),
            ((0.34, 2.70, 3.02), (0.58, 2.70, 2.80), (0.10, 2.70, 2.80)),
        ],
    ),
)
```

### 6.4 Deux faces du même objet — `OneObjectFace`

Règle mono-objet : les deux côtés de la paire portent sur le même élément
(le source) — la provenance reste explicite côté stockage.

```python
result.info = ClashResultInfo()
result.info.distance = 0.85     # m — ou "angle" selon le check
result.info.add_face_pair(
    (   # face A de l'élément source
        (0.0, 0.0, 1.0),
        1.25,
        [((0.0, 0.0, 3.0), (2.0, 0.0, 3.0), (0.0, 2.0, 3.0))],
    ),
    (   # face B du même élément
        (1.0, 0.0, 0.0),
        0.95,
        [((2.0, 0.0, 0.0), (2.0, 2.0, 0.0), (2.0, 0.0, 3.0))],
    ),
)
```

### 6.5 Faces de deux objets — `TwoObjectsFace`

```python
result.info = ClashResultInfo()
result.info.angle = 4.2         # deg — écart angulaire
result.info.add_face_pair(
    (   # face de la source
        (0.0, 0.0, 1.0),
        1.25,
        [((0.0, 0.0, 3.0), (2.0, 0.0, 3.0), (0.0, 2.0, 3.0))],
    ),
    (   # face de la target
        (0.07, 0.0, 1.0),
        1.10,
        [((0.0, 0.0, 3.0), (2.0, 0.0, 3.0), (0.0, 2.0, 3.0))],
    ),
)
```

### 6.6 Rayons — `DirectView`

`hit_ratio` est la mesure nominale ; le détail du lancer est un
attribut déclaré propre à la règle (`raycast`, RaycastData) : seul le
ratio intéresse les consommateurs, les segments servent à l'affichage.

```python
result.info = ClashResultInfo()
result.info.hit_ratio = 37.5    # % — mesure nominale
result.info.raycast = RaycastData(
    planned=120,
    cast=118,
    hit=45,                      # hit_ratio = hit / planned
    hit_segments=[
        ((10.0, 2.0, 1.5), (14.0, 2.0, 1.5)),
    ],
    blocked_segments=[
        ((10.0, 2.0, 1.5), (14.0, 2.0, 1.5)),
    ],
)
```

### 6.7 Zone métier — `ClearanceForDoors`

`penetration_depth` en mesure ; la zone est un attribut déclaré propre
à la règle (`zone`, ZoneData). Le solide OCC reste dans le registre
d'affichage : le résultat ne porte que les dimensions sérialisables
(6.13-3 résolu).

```python
result.info = ClashResultInfo()
result.info.penetration_depth = 0.14    # m — mesure nominale
result.info.zone = ZoneData(
    side="Front",               # côté du bloc-porte
    leaf="SingleSwingLeft",
    width=1.0,                  # largeur balayée (m)
    depth=0.9,                  # profondeur (m)
    height=2.1,                 # hauteur (m)
)
```

### 6.8 OBB de détection — `OBB_Above`

Les OBB ne sont pas appariés : deux listes indépendantes. La source porte
sa zone de détection (l'OBB détaché vers le haut) et son propre OBB ;
la target porte son OBB. Le `Custom_OBB` de calcul reste dans le registre
d'affichage — le résultat ne porte que son tuple sérialisable (complet :
le solide OCC se reconstruit depuis `center` + `axes` + `half_sizes`).

```python
result.info = ClashResultInfo()
result.info.source_obbs.append(
    (   # zone de détection : bande de 0.85 m au-dessus de la source
        (4.00, 2.00, 0.95),                                    # center
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),   # axes
        (0.50, 0.40, 0.425),                                   # half_sizes
        "zone",                                                # label
    )
)
result.info.source_obbs.append(
    (   # l'OBB propre de la source
        (4.00, 2.00, 0.00),
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        (0.50, 0.40, 0.10),
        "object",
    )
)
result.info.target_obbs.append(
    (   # l'OBB propre de la target
        (4.10, 2.05, 0.90),
        ((1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)),
        (0.20, 0.15, 0.05),
        "object",
    )
)
```

### 6.9 Intersection traversante (future — `doc/Idea.md`)

Montre l'extensibilité : un label libre sur les paires de points, paires
multiples, mesures volumiques en attributs.

```python
result.info = ClashResultInfo()
result.info.penetration_depth = 0.32        # m — mesure nominale
result.info.add_point_pair(
    (12.41, 3.02, 0.85),                   # point d'entrée, côté source — paire n° 1
    (12.41, 2.80, 0.85),                   # point d'entrée, côté target — paire n° 1
    label="entry",
)
result.info.add_point_pair(
    (12.41, 2.60, 0.85),                   # point de sortie, côté source — paire n° 2
    (12.41, 2.44, 0.85),                   # point de sortie, côté target — paire n° 2
    label="exit",
)
result.info.volume_intersection = 0.0012    # m³
result.info.volume_ratio = 0.012
result.info.containment_ratio = 0.85
result.info.clearance_violated_volume = 0.0
```

### 6.10 Chevauchement volumique (future — `doc/Idea.md`)

Seuls les attributs volumiques remplis ; le seuil « ignorer si < 0,1 % du
plus petit » se règle côté consommateur à partir de `volume_ratio`.

```python
result.info = ClashResultInfo()
result.info.volume_intersection = 0.0004       # m³
result.info.volume_ratio = 0.004               # relatif au plus petit des deux
result.info.containment_ratio = 0.0
result.info.clearance_violated_volume = 0.0
```

### 6.11 Résultat complexe — `ClashResultComplex` (Must check)

`info` vide (instance posée, aucune mesure) : le verdict du groupe est
`status`. Une mesure `count` est envisageable pour l'export mais pas
retenue : le comptage est déjà consommé par le check au moment de la
production.

```python
result.info = ClashResultInfo()
```

### 6.12 La feuille de test du contrat

`tests/test_structure_ResultShape.py` :

1. un test de `RESULT_SHAPE` elle-même (les types déclarés sont bien des
   types) ;
2. un test de `to_dict()` : un `ClashResultInfo` rempli produit exactement
   la forme du contrat (round-trip attributs/tuples → dict) ;
3. un helper `assert_result_shape(rule)` : pour chaque résultat de la
   règle, `to_dict()` comparé à `RESULT_SHAPE` en sous-ensemble — sinon
   échec, avec le chemin exact de chaque faute
   (`faces[0].source.area: str != float`) — et `validate()` vide
   (aucune faute) ;
4. un appel à ce helper dans chaque test de règle existant, après
   `rule_file.run()` — une ligne par test ;
5. des tests négatifs : `info.chek = 1.0` → l'attribut posé mais absent
   de `to_dict()` (hors vocabulaire, invisible) ; `info.ratio = "0.62"`
   → faute au `validate()` (type) ; append direct d'un point non 3D →
   faute au `validate()` ; OBB mal formé (centre non 3D, demi-taille
   négative) → faute au `validate()` ; numéro de paire orphelin (posé
   d'un seul côté source/target) → faute au `validate()` ; un
   `RaycastData`/`ZoneData` mal formé → faute au `validate()`.

### 6.13 Points à corriger — questions ouvertes

| # | Question | Options |
|---|---|---|
| 1 | Nom de la classe porteuse | `ClashResultInfo` / `ClashInfo` / `ResultInfo` |=> Le nom de la classe sera ResultInfo.
| 2 | ~~SurfaceRecover : ratio ou aire en mesure nominale ?~~ | **Résolu** : les deux sont posées, l'ordre de pose désigne la nominale |
| 3 | ~~`specific["zone"]["shape"]` (objet OCC non sérialisable)~~ | **Résolu** (et le `specific` est supprimé) : le solide OCC reste dans le registre d'affichage, `ZoneData` ne porte que les dimensions sérialisables |
| 4 | ~~Provenance des points/faces~~ | **Résolu** : `source_points`/`target_points`, `source_faces`/`target_faces` — mêmes noms que les attributs actuels, appariées par numéro |
| 5 | ~~Unité des mesures~~ | **Résolu** : l'unité est portée par le vocabulaire (section 4), la donnée est un float nu |
| 6 | ~~`hit_ratio` en % (0..100) ou en ratio (0..1) ?~~ | **Résolu** : ratio (0..1), harmonisé avec `volume_ratio` ; le seuil Threshold de DirectView reste en % dans la règle |
| 7 | Emplacement de `ClashResultInfo` | `RuleClass.py` (avec les `ClashResult*`) ou module dédié `ResultInfo.py` | Il sera dans RuleClass.Py
| 8 | ~~Libellés des OBB (`label`)~~ | **Résolu** : champ libre (recommandé : `object` / `zone`), `validate()` n'impose rien |
| 9 | ~~Lisibilité des tuples (`face[0]` = la normale...)~~ | **Résolu** : NamedTuple (`PointEntry`, `FaceData`, `FaceEntry`, `ObbData`) — indexable comme un tuple, lisible par attribut (`entry.face.normal`), `_asdict()` gratuit pour `to_dict()` |
| 10 | `ZoneData` ne porte pas la forme de la zone (Arc / Rectangle) : un consommateur ne peut pas reconstruire le solide balayé depuis les seules dimensions. Ajouter un champ `shape: str` à `ZoneData`, ou laisser la forme dans la règle ? | ouvert — décision à prendre |

---

## 7. Plan de migration

Ordre des étapes, chacune testée indépendamment :

1. `ClashResultInfo` (NamedTuple `PointEntry`/`FaceData`/`FaceEntry`/
   `ObbData`/`RaycastData`/`ZoneData`, attributs annotés, `__setattr__`
   silencieux — suivi de
   l'ordre de pose —, helpers `add_*`, `validate`, `to_dict`) dans
   `RuleClass.py` ; `RESULT_SHAPE` ; `result.info` initialisé dans
   `ClashResult` et `ClashResultComplex`.
2. Suppression des attributs plats absorbés (`ClashResultTwoObjects`,
   `point1`/`point2`).
3. Migration des 19 sites de `Rules.py` (table ci-dessous).
4. Mise à jour des lectures : les tests qui lisent
   `axis_mode`/`check`/`value`/`face_a`/`face_b`
   (`test_Rule_TwoObjects.py`, `test_UnitRule_*`).
5. Feuille de test `tests/test_structure_ResultShape.py` + helper ajouté à
   chaque test de règle.

Table de correspondance (attributs plats → propriétés de
`ClashResultInfo`) :

| Règle | Avant | Après |
|---|---|---|
| ClearanceAxisToAxis | `distance_between`, `axis_mode`, `axis_angle`, `axis_degraded` | `distance`, `angle` (attributs) + `source_points`/`target_points` + `axis_mode`/`axis_degraded` (attributs propres à la règle) |
| SurfaceRecover | `distance_between`, `surface_contact_area`, `ratio`, `source_face`, `target_face`, `source_faces` | `contact_area`, `ratio`, `distance` (attributs) + `source_faces`/`target_faces` |
| OneObjectFace | `check`, `value`, `face_a`, `face_b`, `source_faces`, `target_faces` | mesure (`distance` ou `angle`) + `source_faces`/`target_faces` (les deux faces du même élément) |
| TwoObjectsFace | `check`, `value`, `face_a`, `face_b`, `source_faces`, `target_faces` | mesure (`angle`) + `source_faces`/`target_faces` |
| Alignement | `offset` | `offset` (attribut) |
| DirectView | `rays_planned`, `rays_cast`, `hit_segments`, `blocked_segments`, `hit_ratio` | `hit_ratio` (attribut) + `raycast` (RaycastData) |
| ClearanceForDoors | `penetration_depth`, `zone` | `penetration_depth` (attribut) + `zone` (ZoneData) |
| Règles OBB (OBB_Above, OBB_Below, ObbHigh, ObbLength, OBB_Front_And_Back, OBB_Custom) | rien — OBB uniquement dans le registre d'affichage | `source_obbs` / `target_obbs` avec `label` |

Après migration, toute nouvelle règle écrit exclusivement via
`result.info` ; l'ajout d'un attribut de résultat hors de la classe est
considéré comme une erreur de conception.
