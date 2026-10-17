# IfcClash_Plus

## Project Purpose
This project aims to extend the capabilities of IfcClash. The goal is to provide a stable foundation for adding geometric rules of varying complexity, resulting in a broader set of rules. There are therefore 3 distinct goals:

### Rules for model quality
First, these rules must be usable to check the geometry of models. The more refined the rules we create, the lower the number of false positives and true negatives. This limits the human sorting time required after each rule run. However, these rules must be complex enough to cover all the possible situations that can occur in a project.

### Rules for selecting models
Second, these rules must make it possible to select objects based on geometric criteria. Today, we have IDS to select objects according to their properties. Here, we want a common set of rules to specify relationships between objects. For example, I must be able to easily select the walls that are in contact with a door, even if the walls and the door are in two different models.

### Standardization
I also want to add my contribution to the standardization of definitions. Today, we have IDS to unify our definitions regarding the management of "textual data", but nothing for geometric data.
I have noticed that the various clash tools are not exactly aligned on the definition of an intersection, for example. Likewise, the classic rule duo of intersection and distance is quite poor for describing the richness of the relative positions between two objects.


# Main features

1. A rule catalog and a canvas to fill in
The goal is to provide a working foundation on which other rules can easily be added.
In any case, 50% of rule management is similar from one rule to another: handling inputs, handling outputs, etc.
So this is a big sandbox.

2. An easy-to-use foundation
The rules must remain easy to pick up; if we want to quickly run a single rule, it should be easy.
I like the following philosophy: "Easy to use, hard to master".
Is it easy to use today? To be determined...

3. Link with IDS
I reused the IDS facets to select objects. The goal is to interconnect the validation of textual data and the validation of geometric data.

4. The rule cascade
A rule needs one or more lists of objects as input. This can be an IDS facet that selects objects, but it can also be another rule. Each rule can output a list of objects. In this way, rules can be chained one after another to refine the list of objects to obtain, using geometric filters.

5. Folders
Rules can be organized into folders. These folders can contain subfolders, and so on. This way, we can have a complex file with several hundred rules without it being a problem to manage.

These folders can be enabled or disabled with rules. They can therefore be conditioned on the success of a rule or not. In this way, we can have a very large set of rules that will choose by themselves whether to run, depending on the situation. For example, if I have no balconies, there is no point in checking whether the beams are cantilevered.

6. Exceptions everywhere
There are always special cases that we have not managed to take into account. The idea here is to allow filtering special cases at the lowest level of the rule run.

For two-object rules, the result is necessarily a list of pairs of objects, for example a pipe that enters a beam. These two objects can then be subject to a specific rule that will only run on this sample of two objects. This should allow more precise application of the rule, since we only have two objects to analyze, so we can check their positions relative to each other. Something that is not possible with lists of several hundred elements.

7. Automating result processing
In most cases, results can already be sorted semi-automatically. An intersection between a pipe and a beam must be sent to the structural engineer and the MEP engineer. The idea here is again to connect the rules to different topics in order to sort by actor, by criticality.

8. BCF
It must be possible to create BCFs.

9. Grouping of results
Again, the idea is to make it easier to transfer information. In 90% of cases, we should be able to gather the issues within a room or a floor together. Otherwise, we end up with thousands of clashes that are hard to analyze.

10. Absolute or relative verification
This verification must make it possible to define a quantity, either the number of objects in the clash or the sum of a property, and to compare this value with a target.
This quantity can be absolute: I must find X elements in this model that satisfy the rule.
This quantity can be relative (for a two-object rule): I must have X times more source objects than target objects in my results.

Typically, this can be used to check that there are indeed 2 electrical outlets per 10m2 of office space, for example.



# Rule catalog
Each rule has a sheet presenting the rule, its parameters and its special cases.


## List of rules

### One-object rules

| **Rule** | **Type** | **Rule status** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Volume](doc/1ObjectsRules/Volume.md) | One object | OK | OK | OK |
| [Area](doc/1ObjectsRules/Area.md) | One object | OK | OK | OK |
| [Top Or Bottom Surface](doc/1ObjectsRules/TopOrBottomSurface.md) | One object | OK | OK | OK |
| [Lateral Surface](doc/1ObjectsRules/LateralSurface.md) | One object | OK | OK | OK |
| [Projected Surface](doc/1ObjectsRules/ProjectedSurface.md) | One object | OK | OK | OK |
| [Orientation](doc/1ObjectsRules/Orientation.md) | One object | OK | OK | OK |
| [Object height](doc/1ObjectsRules/ObbHeigh.md) | One object | OK | OK | OK |
| [Object length](doc/1ObjectsRules/ObbLength.md) | One object | OK | OK | OK |
| [Geometry Quality](doc/1ObjectsRules/Quality.md) | One object | KO | OK | KO |
| [Stair Quality](doc/1ObjectsRules/StairQuality.md) | One object | KO | OK | KO |
| [Stability](doc/1ObjectsRules/Stability.md) | One object | KO | OK | KO |
| [Face Check](doc/1ObjectsRules/OneObjectFace.md) | One object | OK | OK | OK |

### Two-object rules

#### Historical IfcClash rules

| **Rule** | **Type** | **Rule status** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Clearance](doc/2ObjectsRules/Clearance.md) | Two objects | OK | OK | OK |
| [Intersection](doc/2ObjectsRules/Intersection.md) | Two objects | OK | OK | OK |
| [Collision](doc/2ObjectsRules/Collision.md) | Two objects | OK | OK | OK |

#### Advanced clearance rules

| **Rule** | **Type** | **Rule status** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Clearance Above Object](doc/2ObjectsRules/ClearanceAbove.md) | Two objects | OK | OK | OK |
| [Clearance Next To Object](doc/2ObjectsRules/ClearanceNextTo.md) | Two objects | OK | OK | OK |
| [Clearance Below Object](doc/2ObjectsRules/ClearanceBelow.md) | Two objects | OK | OK | OK |

#### Clearance with OBB

An Oriented Bounding Box (OBB) is the smallest box enclosing an object. These checks are fast and, most of the time, precise enough to detect a problem.
The OBB has a second advantage: it can easily be enlarged or shrunk. We can have OBBs enlarged around the top, or with one side reduced.

The last benefit is detecting the front and back of an element. Most of the time, this information is not included in the model. We cannot determine the front, back or side of an object. For a door, elements can pass on the sides, but not through the opening (from the front or the back). These methods can help detect objects in front of a door. The OBB is a rectangular cuboid, and the functions to modify or compute it are very simple. It is a degraded method, but it still produces convincing results.


| **Rule** | **Type** | **Rule status** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [OBB Above](doc/2ObjectsRules/OBB_Above.md) | Two objects | OK | OK | OK |
| [OBB Below](doc/2ObjectsRules/OBB_Below.md) | Two objects | OK | OK | OK |
| [OBB Front And Back](doc/2ObjectsRules/OBB_Front_And_Back.md) | Two objects | OK | OK | OK |
| [OBB Custom](doc/2ObjectsRules/OBB_Custom.md) | Two objects | OK | OK | OK |

#### Other types of rules

| **Rule** | **Type** | **Rule status** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Surface Recover](doc/2ObjectsRules/SurfaceRecover.md) | Two objects | OK | OK | OK |
| [Angle Between](doc/2ObjectsRules/AngleBetween.md) | Two objects | OK | OK | OK |
| [Clearance Axis To Axis](doc/2ObjectsRules/ClearanceAxisToAxis.md) | Two objects | OK | OK | OK |
| [Direct View](doc/2ObjectsRules/DirectView.md) | Two objects | OK | OK | KO |
| [Two Objects Face](doc/2ObjectsRules/TwoObjectsFace.md) | Two objects | OK | OK | OK |
| [Volume Clash](doc/2ObjectsRules/VolumeClash.md) | Two objects | KO | OK | KO |
| [Inside](doc/2ObjectsRules/Inside.md) | Two objects | KO | OK | KO |
| [Clearance For Doors](doc/2ObjectsRules/ClearanceForDoors.md) | Two objects | OK | OK | OK |
| [Face Check](doc/2ObjectsRules/TwoObjectsFace.md) | Two objects | OK | OK | OK |


### Complex rules

| **Rule** | **Type** | **Rule status** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Free Space in Room](doc/ComplexRules/FreeSpace.md) | Complex | OK | OK | OK |
| [Alignement](doc/ComplexRules/Alignement.md) | Complex | OK | OK | OK |
| [Find Path](doc/ComplexRules/FindPath.md) | Complex | KO | KO | KO |
| [EvacuationDistance](doc/ComplexRules/EvacuationDistance.md) | Complex | KO | OK | KO |



# Installation
This project uses IfcOpenShell and PythonOCC. PythonOCC is only distributed via the conda-forge channel: installation therefore goes through Conda.

```bash
conda env create -f environment.yml
conda activate ifcclash_plus
pip install -e .
```

The development environment is described in environment.yml, the Conda deployment recipe in conda/meta.yaml.


# Progress
The first step is to create new rules to extend the possibilities. These rules can be used in any template.

## V0.5

#### Major update

- ClashResult overhaul and ResultInfo class
    The common core of results (id, type, status, criticity, actor, source/target) is now separated from the data specific to each rule, which migrates to a new ResultInfo class. Scalar measurements become declared attributes (distance, penetration_depth, contact_area, ratio, offset, hit_ratio, angle) instead of undeclared dynamic attributes, completed by structured per-rule blocks (RaycastData for DirectView, ZoneData for ClearanceForDoors, axis_mode for ClearanceAxisToAxis). Each ClashResult now carries a GUID, and ClashResultComplex no longer inherits from ClashResult. The new specification (specification_ResultData.md) documents this data contract, with its dedicated test sheet.

- Rule serialization
    The serialization.py module can now save and reload the rules themselves, not only the results: a complete RuleFile can be written to a JSON file and replayed elsewhere, in particular by another process.

- IPC for BonsaiViewer
    Four new modules open the engine to an external client: ipc.py (JSON Lines server on stdin/stdout, hello, catalogue and run requests), registry.py (catalogue of all rules, facets and selects with their exact parameters, single source of truth shared between the client UI and the engine), result_export.py (JSON export of results, elements becoming cross-references: model index + STEP id) and display_export.py. This is the foundation of the BonsaiViewer integration mock-up.

#### Minor update

- Two Objects Face rule
    The rule has been reworked, with a new triangles_bbox_distance function in clash_utils.py: a fast lower bound of the distance between two triangles, computed from their bounding boxes.

- Documentation
    The rule pages of doc/ have been enriched (BasicRayCheck, Clearance Above, Below and Next To, Inside, VolumeClash, Quality, Stability, StairQuality, ObbHeigh, ObbLength), and the display tests updated accordingly.

## V0.4

#### Major update

- New rules
    Several rules have been added: ObbHigh, AngleBetween and CustomOBB, each with its own set of exceptions.

- BooleanRule
    A new booleanrule.py module has been created, with the ability to enable or disable rules for a folder.

- Display
    Functions to display inputs and results have been added, with grouping support and several series of improvements. Each rule can be viewed in a small viewer. This helps to detect problems.

- Tests
    The test suite has grown by about 3500 lines: new files for one-object rules, two-object rules, rule files and folders, Select, ProduceSelect, BooleanRule, clash_utils, display, exceptions and serialization.

- Serialization
    A new serialization.py module has been created, with tests. All classes can be saved to a json file in order to reuse them elsewhere.

- Absolute or relative result verification
    The Must check (AbsoluteOrRelativeChecking) is now a rule in its own right: once groups have been evaluated, it produces its own complex result (sources, targets and verdict state) and keeps the original individual results, so that it can be re-run on the same rule. The ResultAnalyze and BCF_Subject classes were created to group results by BCF subject. The AbsOrRel tests were extended accordingly.

- BCF link specification
    A specification (specification_BCF_Link.md) describes how rule results are grouped into BCF subjects: actor, criticality and references to the objects involved.

- Conda / Pip packaging
    The project is now installable and deployable: environment.yml provides the development environment (PythonOCC via conda-forge), conda/meta.yaml the Conda deployment recipe. setup.py has been repaired (pip installation installed no module) and requirements.txt has been cleaned of its local build paths.

#### Minor update

- Repair of the Above and Below rules
    Both rules have been completely overhauled: direction handling has been fixed, clash boundaries are now handled correctly, and OBB_Above / OBB_Below have been fully converted to the new system.

- Front and back OBB
    The OBB used for front/back detection has been repaired, and the OBB length has been added. A dedicated test has been created for this rule.

- Select rule
    A new Produce_Select function has been created, then extended to handle many cases. It is covered by tests.

- Ray Check repair
    The Ray Check rule has been fixed in three successive steps.

- IfcSystem exception
    An exception based on IfcSystem has been added.

- End-of-rule refactor
    end_rule_action has been updated to unify the end of each rule. Failed results now go through a single, unified source.

- Major overhaul of the core code
    Rules.py, RuleClass.py, clash_utils.py and CustomOBB.py have been heavily refactored.
    IfcModel has been moved, then removed.

- Code cleanup
    The whole codebase has been formatted with Ruff, comments have been removed and the .gitignore has been updated several times.

- Documentation
    The README and many pages of doc/ have been updated, including new pages for ObbHeigh and ObbLength. A new agent.md and a complex_configuration.json have been added. A large test IFC file (44000 lines) has been removed from the repository.

- Fix of the ObbHigh and ObbLength rules
    The axis order of an OBB computed by OCC is arbitrary: the Z axis is not always the height of the object. The vertical axis is now determined as the most vertical axis of the box, and the plan dimensions carry wide/narrow. The faces of both groups are recorded for display (blue/orange).

- Illustrated documentation
    Every rule page of doc/ now has a screenshot of the displayed result. A page was created for OBB Custom, and the pages of future rules (Quality, StairQuality, Stability) were specified. The Blender image template was moved to doc/.

- Code audit report
    A static analysis report (Rapport.md) lists blocking bugs, questionable logic and structural debt by severity.

- agent.md overhaul
    The agent development guide (agent.md) has been reworked to reflect the current architecture.

- Display tests
    Display tests have been made more reliable, with colors harmonized between one-object and two-object rules.

## V0.3
- Using AI
I started using AI to create functions. Before that, it was much more sporadic.

- Creation of the Custom OBB class
This is a customOBB class built with the OCC Bnd_OBB() class. It allows modifying existing OBBs, to enlarge them, or to detach a side or the top.
This new OBB then creates a new space that can clash with objects.
The OBB is very easy to modify, and simple enough to apply transformations to it.

- OBB generation functions
I created several functions to generate OBBs from objects. Some are better than others.
One of them is interesting because it creates an OBB whose Z axis is locked to (0,0,1). This is useful for box-type objects.

- Adding a display function
This function should help visualize what is supposed to happen in the rule. It will display the OBB box, where the clash should appear.
It will show the objects that are

- Top and bottom OBB
This rule checks whether something is located above or below an object. It creates a new OBB above (or below) the object and checks whether anything clashes with it.
This is a bit different from the Above or Below rule, since the size of the OBB can be adjusted more precisely.

- Front and back OBB
This rule checks whether something is located in front of or behind the object.
It is quite difficult to detect what is the front and the back. I use the OBB size to detect them. It therefore depends on each object.
For a door, the front is the wide part. For other objects, it will be the narrow part.

- Adding some test cases to help debug everything
still in progress

## V0.2
- Creation of the Above rule
    This rule checks that there is nothing above an object.

- Creation of several grouping functions
    The rule produces a list of results. This list can be grouped in different ways. I have implemented several ways to group objects.
- Creation of absolute and relative verification
    By grouping objects, we create sets of objects. It is important to check that these sets comply with a rule.
    I must have at least one door intersecting each space.
    I must have exactly 1 drain under a shower tray.

- Creation of an automatic criticality classification
    Each result can be automatically classified to determine its criticality. This can be exported to a BCF.
- Update of the automatic actor classification
    Each result can be automatically classified to determine an actor to tag. This can be exported to a BCF.



## V0.1
Creation of the main structure of the script









