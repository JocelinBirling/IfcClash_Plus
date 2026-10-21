# IfcClash_Plus - Agent Onboarding Guide

## Project Overview

**Purpose**: IfcClash_Plus extends IfcClash with a modular, composable rule system for BIM/IFC model clash detection. It enables creating complex validation workflows by chaining simple rules together like "lego blocks."

The code writtent will always be in english. The specification are allowed in french.

You will never commit in git.

**Domain**: Architecture/Engineering/Construction (AEC) - BIM Model Checking
**Tech Stack**: Python, ifcopenshell, ifcclash, OpenCASCADE (OCC), numpy, shapely, ifctester

**Core Value Proposition**: 
- Create reusable, standardizeable clash detection rules
- Chain rules together (waterfall-pattern) for complex validation logic
- Classify results automatically (criticity, actor)
- Reduce edge cases through exception handling

---

## Architecture

### Directory Structure
```
ifcclash_plus/
├── __init__.py          # Package exports
├── RuleClass.py         # Base classes (RuleCheck, Select, Grouping, etc.)
├── orchestrator.py      # run_rule: the explicit node orchestration (SPEC step 4)
├── pipeline.py          # ResultPipeline + RuleOutput (SPEC moteur/gestion)
├── Rules.py             # Rule implementations (Volume, Clearance, OBB_Above, etc.)
├── CustomOBB.py          # Custom OBB generation and manipulation
├── clash_utils.py       # Geometry utilities (face extraction, distance calc)
├── construct_display_function.py  # Visualization helpers
└── exemple.py            # Example scripts

tests/
├── test_Rule_display.py  # MANUAL ONLY: opens a GUI window (see Running the tests)
├── test_Rule_OneObject.py
├── test_Rule_TwoObjects.py
├── test_RuleFile.py
├── test_Select.py
└── test_custom_obb.py

doc/
├── Rule.md              # Rule system documentation
├── Dictionnary.md       # Terminology
├── 1ObjectsRules/       # One-object rule docs
├── 2ObjectsRules/       # Two-object rule docs
└── ComplexRules/        # Complex rule docs

Ifc_Model/              # Test IFC files
```

### Core Components

#### 1. RuleClass.py - Foundation
```
RuleFile          # Root container for rules and IFC files
├── list_ifc_path
├── list_ifc_file
└── contains: [Rule|Folder]

RuleFolder        # Organize rules into folders
├── id
├── activation_rule  # SelectFacet (run if non-empty) or BooleanRule (rules run first, then evaluate)
├── activation_case  # Declared but NOT used by the code yet
└── contains: [Rule|Folder]

Select            # Base selection class
├── SelectFacet   # IDS-based element selection
│   └── applicability: [Facet]
└── SelectRule    # Selection based on rule results
                    # (element_to_pass / element_state_to_pass configure it)

RuleCheck         # Abstract base for all rules
├── RuleCheckOneObject    # Single element validation
└── RuleCheckTwoObjects   # Pairwise element validation
                          # (real complex rules — FreeSpace — inherit
                          # RuleCheckOneObject plus a context Select;
                          # RuleCheckComplex was removed at step 5)
```

#### 2. Rule Categories

| Type | Purpose | State | Examples |
|------|---------|-------|----------|
| **One Object** | Validate single elements | Geometry/Property checks | Volume, Area, Orientation, TopOrBottomSurface |
| **Two Objects** | Validate element pairs | Spatial relationships | Clearance, Intersection, Collision, Above, Below, OBB_Above |
| **Complex** | Multi-set validation | Complex scenarios | FreeSpace (FindPath and EvacuationDistance are NOT implemented) |

#### 3. Rule Execution Flow (SPEC step 4 — the explicit orchestrator)
```
RuleFile.run()                      # the orchestrator
  ├─ Load IFC files
  ├─ distribute_files: give the opened files to every select of the tree
  └─ For each node:
     ├─ RuleFolder  -> activation, then recurse
     ├─ Select node -> node.run() (a SelectRule drives its own rule)
     └─ Rule       -> orchestrator.run_rule(rule):
        ├─ _prepare_selections   # select_source/target/context.run()
        │                        #   + create_list_of_element -> 3 input lists
        ├─ compute_rule          # named compute call, catalogue-driven
        │                        #   (engine_params == instance attributes)
        ├─ rule.collect_results  # extend (or replace: Intersection/Clearance/Collision)
        ├─ rule.register_display_items(results)  # the display hook
        └─ rule.end_rule_action()  # ResultPipeline -> rule.output
                                   #   + Display_* state GUI routing
```

The rules have NO run() anymore: a rule node keeps its engine
(`compute`), its display hook (`register_display_items`) and its
result collection semantics (`collect_results`). Every driver goes
through `orchestrator.run_rule`: `RuleFile.run`, the folder
activations, `SelectRule` (state="Select"), the exception leaves
(`BooleanLeaf.evaluate_result`) and the IPC.

`rule.state` is still an attribute ("Final" | "Select" |
"Display_Input" | "Display_Result"), routed by `end_rule_action` —
it disappears at step 5 of the SPEC.

### Rule Declaration (JSON) — SPEC moteur/gestion

The engine/management separation lives in the CODE only. The JSON
declaration of a rule (`serialize_rule_check`, the canonical on-disk
format) stays FLAT and gathers everything under ONE rule: the selects
(`select_source`, `select_target`), the engine parameters
(`above_type`, `tolerance`...) and the management configuration
(`select_exception`, `select_criticity`, `select_actor`,
`select_grouping`, `abs_or_rel_check`) sit at the same level.

- `registry.engine_params(rule_type)`: the flat keys of a rule
  declaration that feed its named `compute()` call (from the
  catalogue `params`).
- `registry.compute_from_config(config, sources, targets, context)`:
  the dispatch — flat declaration → named `compute()` call. The
  selects/management keys of the same declaration are not consumed
  here (orchestrator and `ResultPipeline` respectively).
- Only migrated rules (a `compute`) can be dispatched; the others
  raise `NotImplementedError` until their migration. All the rules of
  the catalogue are migrated (the guard is kept for robustness —
  `tests/test_registry_dispatch.py::test_unmigrated_rule_raises`
  simulates an unmigrated class).

### Conventions of the migrated rules (SPEC moteur/gestion)

- The `compute()` is pure: no IFC loading, no selection, no
  post-processing, it never touches `self.result`, `self.output` or
  the display registry. Two documented exceptions: a few engines whose
  helpers read their config off the instance (ClearanceForDoors,
  Alignement, DirectView, FreeSpace) POSE the named parameters on the
  instance at the start of the compute — the node remains the config
  carrier.
- The rules have NO run(): the explicit orchestrator
  (`orchestrator.run_rule`) prepares the selections, calls the
  compute (catalogue-driven named call), collects the results
  (`collect_results`: extend, or replace for Intersection/Clearance/
  Collision), fills the DISPLAY REGISTRY through the rule's
  `register_display_items` hook — in every state, exactly as the old
  run() did, the display is a read-only consumer of the registry
  (`tests/test_structure_DisplayUpdate.py` pins this behavior) — then
  runs the pipeline. The data rebuilt from the info blocks travels
  through the `_register_*_display_items` helpers; input data not
  carried by the results (context elements, selected faces of the
  FaceCheck family, zone solids, fitted elements) stays a rule-side
  display concern.
- `Select.create_list_of_element()` rebuilds `list_of_elements` fresh
  on every call: the same select instance feeds several rules, an
  accumulated list would duplicate the elements (a select shared by
  two rules used to quadruple the pairs — fixed with a regression
  test).

---

## Rule System Deep Dive

### Vocabulary (from doc/Rule.md)

| Term | Definition |
|------|------------|
| **Source** | Primary set of objects being tested. Always required. |
| **Target** | Secondary set being tested against. For 2-object rules. |
| **Context** | Auxiliary objects (not directly clashed). Used in complex rules. |
| **Select** | Process of filtering elements using IDS facets or previous rule results |
| **Grouping** | Organizing results by Entity, Property, Attribute, PartOf, Material, Classification, or Closeness — only Entity, Property, Attribute and Source/Target are implemented; PartOf, Material, Classification and Closeness are silent stubs |
| **Exception** | Edge case handling - rules that invalidate other rule results |
| **Must Rule** | Absolute/Relative checks on grouped results |

### Must Rule (Absolute/Relative Checking)

Two types of post-rule validation on grouped results:

**Absolute Checking**:
- `Absolute_Number`: Group must have exactly X elements
- `Absolute_Quantity`: Group must have property value matching criteria
- Example: "Each room must have exactly 1 fire extinguisher"

**Relative Checking**:
- `Relative_Number`: Source count must be X times target count
- `Relative_Quantity`: Source property value relates to target property value
- Example: "Each room must have 2x more chairs than tables"

### Result Classification

**Criticity**: Automatic classification of results based on IDS specifications
```python
rule.select_criticity = [SelectFacet(...)]
# Each result.source/target matching facet gets criticism label
```

**Actor**: Automatic assignment of responsible party
```python
rule.select_actor = [SelectFacet(...)]
# Each result.source/target matching facet gets actor label
```

Both can be exported to BCF (BIM Collaboration Format).

### Rule Chaining (Waterfall)

Rules can be chained where one rule's output becomes another's input:

```python
# Rule 1: Select all walls
wall_selector = SelectFacet(applicability=[Entity(name="IFCWALL")])

# Rule 2: Find walls with volume issues
# (signature: Volume(source, volume_min, volume_max, state="Final"))
volume_rule = Volume(wall_selector, 0, 10)

# Rule 3: Select only problematic walls from Rule 2
problematic_walls = SelectRule()
problematic_walls.rule = volume_rule

# Rule 4: Check if problematic walls intersect with doors
door_selector = SelectFacet(applicability=[Entity(name="IFCDOOR")])
intersection_rule = Intersection(problematic_walls, door_selector)
```

This creates a waterfall: IFC → Walls → Walls with bad volume → Walls with bad volume AND intersecting doors.

---

## Development Guidelines

### Adding a New Rule

**Template for One-Object Rule**:

```python
# In Rules.py — a rule node keeps its engine, its display hook and
# (only when needed) its result collection semantics. No run().
from RuleClass import RuleCheckOneObject, ClashResultOneObject
import clash_utils
import ifcopenshell

class NewRule(RuleCheckOneObject):
    def __init__(self, source, param1, param2, state="Final"):
        super().__init__(state, source)   # state FIRST, then source
        self.type = "NewRule"
        # The engine parameters carry their registry names
        # (engine_params) as instance attributes: the orchestrator
        # reads them by name (compute_from_config parity).
        self.param1 = param1
        self.param2 = param2
        self.geom_settings = ifcopenshell.geom.settings()
        # Note: without USE_WORLD_COORDS or USE_PYTHON_OPENCASCADE the
        # shapes are in LOCAL coordinates. Setting USE_PYTHON_OPENCASCADE
        # also forces world coordinates (see Common Operations).

    # Optional: only to REPLACE the result list on re-run
    # (Intersection/Clearance/Collision do); default extends.
    # def collect_results(self, results):
    #     self.result = results

    # Optional: only for auxiliary display geometry.
    # def register_display_items(self, results):
    #     if self.state in ("Display_Input", "Display_Result"):
    #         _register_my_display_items(self, results)

    # ---- The engine (SPEC: pure computation, testable without any IFC)

    def compute(
        self, liste_objet_source, param1, param2, liste_objet_contexte=None
    ):
        """Pure: no IFC loading, no selection, no post-processing, it
        never touches self.result / self.output / the display registry.
        Each verdict carries its display data in its info blocks."""
        results = []
        for entity, geom in clash_utils.element_shapes(
            liste_objet_source, self.geom_settings
        ):
            # Your rule logic here
            if condition_met:
                result = ClashResultOneObject(source=entity, state=True)
                result.info.distance = measured  # the nominal measure
                results.append(result)
        return results
```

Add the rule to the registry catalogue (`registry.RULES`, the params in
the `compute` signature order) and to the serialization; the
orchestrator and the dispatch then drive it with no further wiring.
See an existing rule (e.g. Volume) and its compute test
(tests/test_compute_OneObject.py) for the full pattern.

### Key Patterns

1. **Always inherit from RuleCheckOneObject or RuleCheckTwoObjects**
2. **Call `super().__init__(state, source[, target])` first** (state first, then the selections)
3. **Set self.type to a unique string identifier**
4. **Set self.geom_settings with appropriate settings** (see the coordinate-system note in Common Operations)
5. **Implement `compute(...)`** — the pure engine: entity lists and
   named parameters in, raw results out; the named parameters carry
   the registry (`engine_params`) names as instance attributes
6. **Implement `register_display_items(results)`** when the rule has
   auxiliary display geometry (rebuilt from the info blocks); override
   `collect_results` only to REPLACE the result list (Intersection,
   Clearance, Collision) — the orchestrator does the rest
7. **Prefer a spatial prefilter** (OBB `IsOut` or the BVH tree) before any per-pair `BRepExtrema` call — five rules still lack one (see Rapport.md §1.1)
8. **Add to __init__.py exports**

### Reusing Exceptions

`select_exception` accepts a `BooleanLeaf` (from booleanrule) whose rule is
evaluated per result pair, or one of the built-in relation methods — it does
NOT accept a list:

```python
# Built-in relation exception: two objects of the same IfcSystem may clash
door_wall_intersection = Intersection(wall_selector, door_selector)
door_wall_intersection.select_exception = "Same_IfcSystem"

# Custom exception: a BooleanLeaf wrapping a rule evaluated on each pair
from booleanrule import BooleanLeaf  # see RuleClass.run_exception
# (the leaf's rule must be able to run on the pair of elements of a result)
```

Only `"Same_IfcSystem"` is implemented; `"Same_Building"`, `"Same_Storey"`
and `"Same_Space"` are stubs that currently raise a TypeError (see
Rapport.md §3, run_exception). Exceptions invalidate results in place
(`status = False`) without removing them from `self.result`.

---

## Environment Setup

The project needs **PythonOCC** (Open CASCADE bindings) and **IfcOpenShell**.
These two libraries do not come from the same package source, which is the
main pitfall when building the environment:

- `pythonocc-core` has no pip wheel: it must come from **conda-forge**
  (it also installs `occt`). Use a `novtk` build to avoid the heavy
  VTK/GUI dependencies.
- `ifcopenshell`, `ifctester` and the other Python dependencies are **pip**
  packages, and their wheels are built for one exact Python version. They
  must be installed with the `pip` of the conda environment.

### Creating the environment

```bash
# 1. Conda environment with Python and PythonOCC, from conda-forge
conda create -c conda-forge -n ifcclash_plus python=3.14 "pythonocc-core=7.9.3=novtk*"
conda activate ifcclash_plus

# 2. IfcOpenShell and the Python dependencies (wheels matching this Python)
pip install ifcopenshell==0.9.0.post1 ifctester==0.9.0 ifcclash==0.9.0 ifcpatch numpy shapely trimesh pytest

# 3. The project itself, editable
pip install -e .

# 4. Check the installation
python -c "import OCC, ifcopenshell, ifctester; print('environment OK')"
```

`requirements.txt` pins the exact versions of the working environment
(it also contains optional web/UI dependencies such as Flask).

### Running the tests

Tests must be run from the repository root (the IFC model paths are relative).

> **WARNING — never run the whole test suite blindly.** Run ONE test file
> (or one single test) at a time, and NEVER run tests whose rule uses
> `state="Display_Input"` or `state="Display_Result"` (the whole of
> `tests/test_Rule_display.py`): they open an OCC GUI window that ONLY
> the human developer can close. An automated run of a display test
> blocks the session until the window is closed by hand — it hangs and
> wastes time. Display tests exist for manual, visual verification only.
>
> **One command = one test.** Never batch: no loop over several test
> files in one shell command, no several paths in one pytest call.
> Launch each test file (or single test) in its own command, check its
> result, then move to the next one.

```bash
# One test file at a time, display tests excluded
python -m pytest tests/test_RuleFile.py -v
python -m pytest tests/test_Rule_OneObject.py

# One single test
python -m pytest "tests/test_RuleFile.py::TestRuleFileWithSelectRule" -v
python -m unittest tests.test_RuleFile.TestRuleFileWithSelectRule -v

# NEVER (opens GUI windows that only the developer can close):
#   python -m pytest tests/
#   python -m pytest tests/test_Rule_display.py
#   any test constructing a rule with state="Display_Input"/"Display_Result"
```

### Pitfalls

- `ImportError: IfcOpenShell not built for 'linux/64bit/pythonX'`:
  the ifcopenshell wheel does not match the Python of the environment
  (typical when reusing an environment created for another Python version).
  Recreate the environment and reinstall with its own `pip`.
- Never install pythonocc-core with pip: it does not exist as a wheel.
- A plain `python -m venv` environment cannot work: there is no pip wheel
  for PythonOCC.

### Known working environment on this machine

`/home/jocelin/Documents/07 - Programmation/IfcOpenshell/Test_IfcOpenshell/.conda`
(Python 3.14.3, pythonocc-core 7.9.3-novtk, ifcopenshell 0.9.0.post1,
ifctester 0.9.0, ifcclash 0.9.0) —
this is the interpreter used to run the test suite.

Do not use:
- `.venv/` (project): has ifcopenshell but no PythonOCC.
- `~/miniconda3/envs/IfcClash_Plus`: has PythonOCC but an ifcopenshell wheel
  built for a different Python.

### IfcOpenShell 0.9 specifics (breaking changes handled by the code)

- `import ifcopenshell.geom` (and `ifcopenshell.api`, `ifcopenshell.util.*`)
  is no longer implicit: `import ifcopenshell` alone does not expose `geom`.
  The project modules import them explicitly; a script doing only
  `import ifcopenshell` must add `import ifcopenshell.geom`.
- The geometry tree has typed backends: `geom.tree()` defaults to
  `opencascade.brep`, which refuses the elements of a plain-settings
  iterator and supports neither `clash_*_many` nor the same element kinds
  as 0.8. The clash queries live on `opencascade.trianglebvh`
  (see `clash_utils.make_clash_tree`, fed by `RuleCheck.add_to_tree`
  with `"BVH"`), and `select_ray` lives on `opencascade.brep`
  (`clash_utils.make_ray_tree`, fed with `"UB"`). `Ray_Check` no longer
  uses the tree at all: its blocking test is an exact OCC segment
  intersection (`clash_utils.segment_hits_shape`), because 0.9.0
  `select_ray` exposes the hit entity as an opaque SwigPyObject
  (upstream issue #9755).
- `tree.clash_*_many` results expose `a`/`b` as entity instances, but
  the wrappers are owned by the tree and dangle once the tree is
  released: `clash_utils.clash_entity(result.a)` re-resolves them
  through their file.
- `ifcopenshell.file.from_pointer` is gone; `file.pathname` is gone.
  The element/model joins use `file.file_pointer()` (see
  `result_export.element_ref`, `serialization._model_names`, `ipc._model_index`).
- An entity no longer keeps its file alive: keep the `ifcopenshell.file`
  objects alive as long as their entities are used (the tests cache them
  next to the cached elements).
- ifctester 0.9 matches the name of an Entity facet case-sensitively
  against the uppercased IFC classes: `SelectFacet.run` normalizes the
  entity names to uppercase (IDS names are case-insensitive).
- The 0.9 shapes resolve coplanar touching at an exact 0 distance
  where 0.8 returned a 1e-5 noise, and its collision backend honors
  `allow_touching` (edge/point contacts now detected): a few
  border-line test expectations were recalibrated accordingly.

## Testing

### Test Structure

```python
import unittest
import sys
sys.path.insert(0, './ifcclash_plus')

import ifcopenshell
from Rules import YourNewRule
from RuleClass import SelectFacet, RuleFile, ClashResultOneObject
from ifctester import ids

class TestYourNewRule(unittest.TestCase):
    def setUp(self):
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
        self.ifc_file = ifcopenshell.open(self.ifc_path)

    def test_your_rule(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]

        # Setup selection
        facet = ids.Entity(name="IFCWALL")
        select = SelectFacet()
        select.applicability = [facet]

        # Create rule
        rule = YourNewRule(select, param1, param2)
        rule_file.contains = [rule]
        rule_file.run()

        # Assertions
        self.assertEqual(len(rule.result), expected_count)
        for result in rule.result:
            self.assertIsInstance(result, ClashResultOneObject)
            self.assertTrue(result.status)
```

### Running Tests
```bash
# One test file per command — NOT the whole tests/ directory, NOT a
# batch of several files in one command
python -m pytest tests/test_Rule_OneObject.py

# One single test, verbose
python -m pytest -v "tests/test_Rule_OneObject.py::TestRules::test_obb_high_rule"

# FORBIDDEN for an agent: the display tests (any rule with
# state="Display_Input"/"Display_Result", i.e. all of
# tests/test_Rule_display.py). They open a GUI window that only the
# human developer can close; an automated run hangs until then.
```

---

## Common Operations

### Working with IFC Geometry

```python
import ifcopenshell
import ifcopenshell.geom
import multiprocessing

# Load file
ifc_file = ifcopenshell.open("model.ifc")

# Get geometry settings
settings = ifcopenshell.geom.settings()
settings.set("USE_WORLD_COORDS", True)  # Important for correct positioning
# COORDINATE SYSTEMS — critical facts (verified against ifcopenshell 0.8):
# - Default: shapes come in LOCAL coordinates (element placement not applied)
# - Setting "USE_PYTHON_OPENCASCADE" to True ALSO forces "use-world-coords"
#   to True (implicit side effect in ifcopenshell.geom.settings.set)
# - Any rule comparing two objects' shapes (BRepExtrema, OBB.IsOut) MUST
#   work in world coordinates, or the distances are meaningless
# - LateralSurface and ProjectedSurface currently lack this setting and
#   apply a world direction to local geometry (see Rapport.md §2)

# Iterate through elements
iterator = ifcopenshell.geom.iterator(
    settings,
    ifc_file,
    multiprocessing.cpu_count(),
    include=[entity1, entity2],  # Specific elements
)

if iterator.initialize():
    while True:
        shape = iterator.get()
        geom = shape.geometry  # OCCshape
        entity = ifc_file.by_id(shape.id)
        
        # Process geometry
        
        if not iterator.next():
            break
```

### Using IDS for Selection

```python
from ifctester import ids

# Entity facet
facet = ids.Entity(name="IFCWALLSTANDARDCASE")

# Property facet
facet = ids.Property(
    property_set="Pset_WallCommon",
    base_name="IsExternal",
    value="TRUE"
)

# Attribute facet
facet = ids.Attribute(name="GlobalId", value="12345")

# Combine with AND/OR
from ifctester import and_, or_
combined = and_(
    ids.Entity(name="IFCWALL"),
    ids.Property(property_set="Pset_WallCommon", base_name="LoadBearing", value="TRUE")
)

# Apply to selector
select = SelectFacet()
select.applicability = [combined]
```

### Working with OBB

```python
from CustomOBB import create_obb_from_TopoDs_Shape, create_obb_with_fixed_z

# Create OBB from geometry
obb = create_obb_from_TopoDs_Shape(geom)

# Detach sides to create detection zones
obb_above = obb.detach_top_by_extrude(0.5)  # Extend 0.5m above
obb_below = obb.detach_bottom_by_extrude(0.5)
obb_front = obb.detach_side_by_extrude(direction, 0.5)

# Get OBB dimensions/properties
center = obb.obb.Center()
x_dir, y_dir, z_dir = obb.get_axes()
extents = obb.obb.Extents()  # [x_min, y_min, z_min, x_max, y_max, z_max]

# Convert to compound for visualization/clashing
compound = obb.to_TopoDS_Compound()
```

### Distance Calculations

```python
from OCC.Core.BRepExtrema import BRepExtrema_DistShapeShape

# Between two OCC shapes
dist_tool = BRepExtrema_DistShapeShape()
dist_tool.LoadS1(shape1)
dist_tool.LoadS2(shape2)
dist_tool.Perform()
distance = dist_tool.Value()
point1 = dist_tool.PointOnShape1()
point2 = dist_tool.PointOnShape2()
```

---

## Current State & Roadmap

### Implemented Rules

| Rule | Type | Status | Doc | Test |
|------|------|--------|-----|------|
| Volume | 1-Object | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_OneObject.py) | ❌ | ✅ |
| Area | 1-Object | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_OneObject.py) | ❌ | ✅ |
| TopOrBottomSurface | 1-Object | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_OneObject.py) | ❌ | ✅ |
| LateralSurface | 1-Object | ⚠️ → ✅ — engine migrated to `compute()` ; le bug coordonnées locales est CORRIGÉ pendant la migration (SPEC point 3) : shapes en coordonnées monde ; tests compute : `tests/test_compute_LotsAB.py` (le test adaptateur `test_Rule_OneObject.py::test_lateral_rule` est recalibré pour le comportement corrigé : 5 → 7) | ❌ | ✅ |
| ProjectedSurface | 1-Object | ⚠️ → ✅ — engine migrated to `compute()` ; le bug coordonnées locales est CORRIGÉ pendant la migration (SPEC point 3) ; tests compute : `tests/test_compute_LotsAB.py` (test adaptateur recalibré : 11 → 9) | ❌ | ✅ |
| ObbHigh | 1-Object | ⚠️ → ✅ (OBB axes arbitrarily permuted by OCCT — confirmed, see Rapport.md) — engine migrated to `compute()` (hauteur mesurée par l'étendue Z des coins, axes OCCT non fiables) ; tests compute : `tests/test_compute_LotsAB.py` | ❌ | ✅ |
| ObbLength | 1-Object | ⚠️ → ✅ (Z exclusion assumption, see Rapport.md) — engine migrated to `compute()` (axe vertical = axe le plus vertical de l'OBB) ; tests compute : `tests/test_compute_LotsAB.py` | ❌ | ✅ |
| Orientation | 1-Object | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_OneObject.py) | ❌ | ✅ |
| Intersection | 2-Objects | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_TreeClashes.py) | ❌ | ✅ |
| Clearance | 2-Objects | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_TreeClashes.py) | ❌ | ✅ |
| ClearanceAxisToAxis | 2-Objects | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_Angles.py) | ✅ | ✅ |
| Collision | 2-Objects | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_TreeClashes.py) | ❌ | ✅ |
| Above | 2-Objects | ⚠️ (contradictory conventions, see Rapport.md §2) — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_Above.py) | ❌ | ✅ |
| Below | 2-Objects | ⚠️ (semantics to clarify, see Rapport.md §2) — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_Below.py) | ❌ | ✅ |
| Ray_Check | 2-Objects | ⚠️ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_RaysAndCustom.py) ; le contexte est une 3e liste d'entrée (liste_objet_contexte) | ❌ | ❌ |
| OBB_Above | 2-Objects | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_OBB_Above_Below.py) | ❌ | ✅ |
| OBB_Below | 2-Objects | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_OBB_Above_Below.py) | ❌ | ✅ |
| OBB_Front_And_Back | 2-Objects | ⚠️ — engine migrated to `compute()` (comportement préservé, défaut documenté : le test rouge préexistant reste rouge) ; tests compute : `tests/test_compute_LotsAB.py` | ❌ | ✅ |
| OBB_Custom | 2-Objects | ✅ (API misleading: `tolerance` is a list of modification strings) — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_RaysAndCustom.py) ; les valeurs de modification acceptent un nombre (m) ou un pourcentage ("x%") : `_modification_value` | ❌ | ✅ |
| AngleBetween | 2-Objects | ✅ (no spatial prefilter, 180° symmetry unhandled, see Rapport.md) — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_Angles.py) | ❌ | ❌ |
| Alignement | 1-Object (Complexe) | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_Alignement.py) ; les params sont posés sur l'instance par le compute (exception documentée : le nœud reste porteur de config), l'état moteur (alignment + objects/groups des zones) reste sur le nœud pour l'affichage | ✅ | ✅ |
| SurfaceRecover | 2-Objects | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_SurfaceRecover.py) ; bornes min_covering/max_covering au registre ; display des faces de contact reconstruit des blocs info (`_register_contact_faces_display`) | ✅ | ✅ |
| DirectView | 2-Objects + context | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_DirectView.py) ; le contexte est une 3e liste d'entrée ; ray tree alimenté par `clash_utils.add_elements_to_ray_tree` ; display des rayons reconstruit des blocs info (`_register_raycast_display`) | ✅ | ✅ |
| OneObjectFace | 1-Object | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_OneObjectFace.py) ; `_run_checks`/`_check_pairs` reçoivent la config en paramètre (namespace), les faces des groupes restent un display d'adaptateur | ✅ | ✅ |
| TwoObjectsFace | 2-Objects (famille FaceCheck) | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_TwoObjectsFace.py) ; `_collect_faces` prend une liste plate + `register=True` : le compute passe register=False, l'enregistrement display reste à l'adaptateur | ✅ | ✅ |
| ClearanceForDoors | 2-Objects | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_ClearanceForDoors.py) ; le compute POSE les params sur l'instance avant `_build_zones` (le nœud reste porteur de config) ; les solides de zones sont reconstruits à l'adaptateur | ✅ | ✅ |
| FreeSpace | Complexe (1-Object + context) | ✅ — engine migrated to `compute()` (SPEC moteur/gestion, tests/test_compute_FreeSpace.py) ; LE cas du contrat 3 listes ; l'état moteur (placements + positions de sondes) reste sur le nœud pour l'affichage | ✅ | ✅ |

See `Rapport.md` at the repository root for the full per-rule analysis:
blocking bugs, doubtful logic and the spatial-prefilter inventory (§1.1).

### Priority Development Areas

1. **Fix blocking bugs** (HIGH — from Rapport.md §5)
   - `RuleCheckOneObject.run_actor`: crashes as soon as an actor is set
   - `run_exception`: Same_Building/Same_Storey/Same_Space raise TypeError
   - `Select.create_list_of_element` with an empty SelectFacet

2. **Documentation** (HIGH)
   - Complete doc/Rule.md explanations
   - Add docstrings to all classes/methods
   - Document all rule parameters and edge cases

3. **Testing** (HIGH)
   - Add tests for missing rules
   - Test edge cases (empty selections, single elements, etc.)
   - Test exception handling
   - Test grouping and classification

4. **Rule Completion** (MEDIUM)
   - Fix OBB_Front_And_Back
   - Fix Ray_Check
   - Clarify Above/Below semantics (contradictory conventions, see Rapport.md §2)
   - Add ClearanceNextTo, ClearanceAbove, ClearanceBelow

5. **New Features** (MEDIUM)
   - FaceCheck member rules (FaceClearance, FaceIntersect, FaceOBB, FaceOrient — family deployed as TwoObjectsFace, member specs pending)
   - EvacuationDistance rule (FindPath not in the deployment list)

6. **Performance** (MEDIUM)
   - Add a spatial prefilter (OBB `IsOut`) to the 5 rules without one:
     AngleBetween, ClearanceAxisToAxis, Ray_Check, DirectView, TwoObjectsFace
     (see Rapport.md §1.1 — ClearanceAxisToAxis already holds the OBBs)
   - Optimize OBB generation
   - Implement BVH vs UB tree selection logic
   - Add parallel processing where possible

7. **Visualization** (LOW)
   - Complete display() for all rules
   - Add OBB visualization options
   - Export clash visualization to BCF

---

## Troubleshooting

### Common Issues

**"USE_WORLD_COORDS setting not working"**
```python
# Always set this BEFORE creating iterator
settings = ifcopenshell.geom.settings()
settings.set("USE_WORLD_COORDS", True)
```

**"AttributeError: 'NoneType' object has no attribute 'geometry'"**
```python
# Check if iterator.initialize() returns True
if iterator.initialize():
    shape = iterator.get()
    # Now safe to access shape.geometry
```

**"Elements not found in selection"**
```python
# Verify your IDS facets are correct
# Use ifctester to test facets independently
from ifctester import ids
facet = ids.Entity(name="IFCWALLSTANDARDCASE")
results = facet.filter(ifc_file)
print(f"Found {len(results)} elements")
```

**"OBB generation fails"**
```python
# Some geometries can't create OBB
# Use try/except or check geometry type first
from ifcopenshell.geom import ShapeElementType
if shape.type == ShapeElementType.BREP:
    obb = create_obb_from_TopoDs_Shape(geom)
else:
    # Handle non-BREP geometry
```

### Debugging Tips

1. **Visualize elements**: Use OCC.Display.SimpleGui to see what you're working with — manual only, never in an automated test run (see Running the tests)
2. **Check geometry types**: Not all IFC elements have geometry
3. **Validate IFC files**: Use ifcopenshell file validation
4. **Test with small files**: Ifc_Model/ has small test files
5. **Use assertions**: Validate inputs in rule constructors

### Logging

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In rules
logger.info(f"Processing {len(elements)} elements")
logger.debug(f"Element: {entity}, Geometry: {geom}")
```

---

## Contribution Workflow

1. **Pick an issue** from Priority Development Areas above
2. **Read relevant code** in Rules.py or RuleClass.py
3. **Check existing tests** for pattern guidance
4. **Implement the change**
5. **Add tests** for new functionality
6. **Update documentation** in doc/ or docstrings
7. **Run the relevant tests, one file at a time** (never the whole suite,
   never the display tests — see Running the tests)
8. **Commit with descriptive message**

---

## Quick Start Example

```python
#!/usr/bin/env python3
import sys
sys.path.insert(0, './ifcclash_plus')

from ifcclash_plus import RuleFile, SelectFacet
from ifcclash_plus.Rules import OBB_Above
from ifctester import ids

# Setup
rule_file = RuleFile()
rule_file.list_ifc_path = ["Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"]

# Select furniture as source
source_select = SelectFacet()
source_select.applicability = [ids.Entity(name="IFCFURNISHINGELEMENT")]

# Select slabs as target
target_select = SelectFacet()
target_select.applicability = [ids.Entity(name="IFCSLAB")]

# Create rule: detect a target penetrating the 0.85m band above the source
# (i.e. an object LESS than 0.85m above the furniture and touching the band,
# NOT "> 0.85m above" — see Rapport.md §2, OBB_Above)
rule = OBB_Above(source_select, target_select, tolerance=0.85)
rule_file.contains = [rule]
rule_file.run()

# Display results
for result in rule.result:
    print(f"Source: {result.source.is_a()}#{result.source.GlobalId}")
    print(f"Target: {result.target.is_a()}#{result.target.GlobalId}")
    print(f"Status: {result.status}")
    print()
```

---

## Additional Resources

- **ifcopenshell docs**: https://ifcopenshell.org/python
- **ifcclash docs**: https://github.com/IfcClash/ifcclash
- **ifctester docs**: https://github.com/IfcTester/ifctester
- **IFC specification**: https://standards.buildingsmart.org/IFC/RELEASE/IFC4/ADD2_TC1/FINAL
- **BCF format**: https://github.com/BuildingSMART/BCF-API
- **Python OCC**: https://pythonocc-documentation.readthedocs.io/en/review-gen-apidoc-rtd/genindex.html



---

## Contacts

- **Main Developer**: Jocelin
- **GitHub**: (URL to be added)
- **Issues**: Use GitHub issues for bug reports and feature requests
