# IfcClash_Plus - Agent Onboarding Guide

## Project Overview

**Purpose**: IfcClash_Plus extends IfcClash with a modular, composable rule system for BIM/IFC model clash detection. It enables creating complex validation workflows by chaining simple rules together like "lego blocks."

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
├── Rules.py             # Rule implementations (Volume, Clearance, OBB_Above, etc.)
├── CustomOBB.py          # Custom OBB generation and manipulation
├── clash_utils.py       # Geometry utilities (face extraction, distance calc)
├── construct_display_function.py  # Visualization helpers
└── exemple.py            # Example scripts

tests/
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
├── activation_rule
├── activation_case  # ALLTRUE, ANYTRUE, etc.
└── contains: [Rule|Folder]

Select            # Base selection class
├── SelectFacet   # IDS-based element selection
│   └── applicability: [Facet]
└── SelectRule    # Selection based on rule results

RuleCheck         # Abstract base for all rules
├── RuleCheckOneObject    # Single element validation
├── RuleCheckTwoObjects   # Pairwise element validation
└── RuleCheckComplex      # Multi-set validation
```

#### 2. Rule Categories

| Type | Purpose | State | Examples |
|------|---------|-------|----------|
| **One Object** | Validate single elements | Geometry/Property checks | Volume, Area, Orientation, TopOrBottomSurface |
| **Two Objects** | Validate element pairs | Spatial relationships | Clearance, Intersection, Collision, Above, Below, OBB_Above |
| **Complex** | Multi-set validation | Complex scenarios | FreeSpace, FindPath, EvacuationDistance |

#### 3. Rule Execution Flow
```
RuleFile.run()
  ├─ Load IFC files
  ├─ Update file info to all contains
  └─ Execute each rule/folder

RuleCheck.run(state="Final")
  ├─ select_source.run()     # Get source elements
  ├─ select_target.run()     # Get target elements (if 2-objects)
  ├─ Run rule-specific logic # Generate self.result
  ├─ manage_result()        # Post-processing
  │   ├─ run_exception()     # Filter out exceptions
  │   ├─ run_criticity()     # Auto-classify criticity
  │   ├─ run_actor()         # Auto-classify actor
  │   └─ run_grouping() or run_abs_or_rel()
  └─ Return ClashResult[]
```

---

## Rule System Deep Dive

### Vocabulary (from doc/Rule.md)

| Term | Definition |
|------|------------|
| **Source** | Primary set of objects being tested. Always required. |
| **Target** | Secondary set being tested against. For 2-object rules. |
| **Context** | Auxiliary objects (not directly clashed). Used in complex rules. |
| **Select** | Process of filtering elements using IDS facets or previous rule results |
| **Grouping** | Organizing results by Entity, Property, Attribute, PartOf, Material, Classification, or Closeness |
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
volume_rule = Volume(wall_selector, min=0, max=10)

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
# In Rules.py
from RuleClass import RuleCheckOneObject, ClashResultOneObject
import ifcopenshell
import multiprocessing

class NewRule(RuleCheckOneObject):
    def __init__(self, source, param1, param2):
        super().__init__(state,source)
        self.type = "NewRule"
        self.param1 = param1
        self.param2 = param2
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()

        for ifc_file in self.select_source.dict_elements.keys():
            iterator = ifcopenshell.geom.iterator(
                self.geom_settings,
                ifc_file,
                multiprocessing.cpu_count(),
                include=self.select_source.dict_elements[ifc_file],
            )

            if iterator.initialize():
                while True:
                    shape = iterator.get()
                    geom = shape.geometry
                    entity = ifc_file.by_id(shape.id)
                    
                    # Your rule logic here
                    if condition_met:
                        result = ClashResultOneObject(source=entity, state=True)
                        self.result.append(result)
                    
                    if not iterator.next():
                        break

        if self.state == "Final":
            self.manage_result()
        else:
            self.produce_select()
```

**Template for Two-Objects Rule**:

```python
from RuleClass import RuleCheckTwoObjects, ClashResultTwoObjects

class NewTwoObjectRule(RuleCheckTwoObjects):
    def __init__(self, source, target, tolerance=0.1):
        super().__init__(state,source, target)
        self.type = "NewTwoObjectRule"
        self.tolerance = tolerance
        self.geom_settings = ifcopenshell.geom.settings()

    def run(self):
        self.tree = ifcopenshell.geom.tree()
        self.select_source.run()
        self.select_target.run()

        self.add_to_tree(self.select_source, "BVH")
        self.add_to_tree(self.select_target, "BVH")

        # Your clash logic here
        # Use self.tree.clash_intersection_many(), clash_clearance_many(), etc.
        
        temp_result = self.tree.clash_intersection_many(
            self.select_source.list_of_elements,
            self.select_target.list_of_elements,
            tolerance=self.tolerance,
        )

        # Process results
        for result in temp_result:
            # Extract source/target entities
            # Create ClashResultTwoObjects
            pass

        if self.state == "Final":
            self.manage_result()
        else:
            self.produce_select()
```

### Key Patterns

1. **Always inherit from RuleCheckOneObject or RuleCheckTwoObjects**
2. **Call super().__init__(source[, target]) first**
3. **Set self.type to a unique string identifier**
4. **Set self.geom_settings with appropriate settings**
5. **Implement run(state="Final") method**
6. **Populate self.result with ClashResult objects**
7. **Call self.manage_result() for final state**
8. **Call self.produce_select() for Select state**
9. **Add to __init__.py exports**

### Reusing Exceptions

```python
# Main rule
door_wall_intersection = Intersection(wall_selector, door_selector)

# Exception: Ignore if door and wall are in same IfcSystem
exception_rule = Intersection(
    SelectRule(door_wall_intersection),  # Source from main rule
    SelectRule(door_wall_intersection),  # Target from main rule
)
# Configure exception to filter same-system pairs

# Apply exception
door_wall_intersection.select_exception = [SelectRule(exception_rule)]
```

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
pip install ifcopenshell==0.8.4.post1 ifctester==0.8.4 ifcpatch numpy shapely trimesh pytest

# 3. The project itself, editable
pip install -e .

# 4. Check the installation
python -c "import OCC, ifcopenshell, ifctester; print('environment OK')"
```

`requirements.txt` pins the exact versions of the working environment
(it also contains optional web/UI dependencies such as Flask).

### Running the tests

Tests must be run from the repository root (the IFC model paths are relative):

```bash
python -m pytest tests/            # all tests
python -m pytest tests/test_RuleFile.py -v
python -m unittest tests.test_RuleFile.TestRuleFileWithSelectRule -v
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
(Python 3.14.3, pythonocc-core 7.9.3-novtk, ifcopenshell 0.8.4.post1) —
this is the interpreter used to run the test suite.

Do not use:
- `.venv/` (project): has ifcopenshell but no PythonOCC.
- `~/miniconda3/envs/IfcClash_Plus`: has PythonOCC but an ifcopenshell wheel
  built for a different Python.

## Testing

### Test Structure

```python
import unittest
import sys
sys.path.insert(0, './ifcclash_plus')

from Rules import YourNewRule
from RuleClass import SelectFacet, RuleFile
from ifctester import ids

class TestYourNewRule(unittest.TestCase):
    def setUp(self):
        self.ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
        self.ifc_file = ifcopenshell.open(self.ifc_path)

    def test_your_rule(self):
        rule_file = RuleFile()
        rule_file.list_ifc_path = [self.ifc_path]

        # Setup selection
        facet = ids.Entity(name="IFCEENTITY")
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
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_Rule_OneObject.py

# Verbose output
python -m pytest -v tests/
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
| Volume | 1-Object | ✅ | ❌ | ✅ |
| Area | 1-Object | ✅ | ❌ | ✅ |
| TopSurface | 1-Object | ✅ | ❌ | ✅ |
| BottomSurface | 1-Object | ✅ | ❌ | ❌ |
| LateralSurface | 1-Object | ✅ | ❌ | ❌ |
| ProjectedSurface | 1-Object | ✅ | ❌ | ❌ |
| Orientation | 1-Object | ✅ | ❌ | ✅ |
| Intersection | 2-Objects | ✅ | ❌ | ✅ |
| Clearance | 2-Objects | ✅ | ❌ | ✅ |
| Collision | 2-Objects | ✅ | ❌ | ✅ |
| Above | 2-Objects | ✅ | ❌ | ❌ |
| Below | 2-Objects | ✅ | ❌ | ❌ |
| Ray_Check | 2-Objects | ⚠️ | ❌ | ❌ |
| OBB_Above | 2-Objects | ✅ | ❌ | ✅ |
| OBB_Below | 2-Objects | ✅ | ❌ | ⚠️ |
| OBB_Front_And_Back | 2-Objects | ⚠️ | ❌ | ❌ |
| Alignement | 1-Object (Complexe) | ✅ | ✅ | ✅ |
| SurfaceRecover | 2-Objects | ✅ | ✅ | ✅ |
| DirectView | 2-Objects + context | ✅ | ✅ | ✅ |
| FaceCheck (moteur FaceSelection) | 2-Objects (famille) | ⚠️ | ✅ | ✅ |
| OneObjectFace | 1-Object | ✅ | ✅ | ✅ |
| ClearanceForDoors | 2-Objects | ✅ | ✅ | ✅ |
| FreeSpace | Complexe (1-Object + context) | ✅ | ✅ | ✅ |

### Priority Development Areas

1. **Documentation** (HIGH)
   - Complete doc/Rule.md explanations
   - Add docstrings to all classes/methods
   - Document all rule parameters and edge cases

2. **Testing** (HIGH)
   - Add tests for missing rules
   - Test edge cases (empty selections, single elements, etc.)
   - Test exception handling
   - Test grouping and classification

3. **Rule Completion** (MEDIUM)
   - Fix OBB_Front_And_Back
   - Fix Ray_Check
   - Complete Below rule
   - Add ClearanceNextTo, ClearanceAbove, ClearanceBelow

4. **New Features** (MEDIUM)
   - AngleBetween rule
   - FaceCheck member rules (FaceClearance, FaceIntersect, FaceOBB, FaceOrient — engine deployed, specs pending)
   - EvacuationDistance rule (FindPath not in the deployment list)

5. **Performance** (LOW)
   - Optimize OBB generation
   - Implement BVH vs UB tree selection logic
   - Add parallel processing where possible

6. **Visualization** (LOW)
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

1. **Visualize elements**: Use OCC.Display.SimpleGui to see what you're working with
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
7. **Run all tests**: `python -m pytest tests/`
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

# Create rule: Check if anything is > 0.85m above furniture
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
