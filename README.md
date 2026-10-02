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
| [Volume](doc/1ObjectsRules/Volume) | One object | OK | KO | OK |
| [Area](doc/1ObjectsRules/Area) | One object | OK | KO | OK |
| [Top Or Bottom Surface](doc/1ObjectsRules/TopOrBottomSurface.md) | One object | OK | KO | OK |
| [Lateral Surface](doc/1ObjectsRules/LateralSurface) | One object | OK | KO | OK |
| [Projected Surface](doc/1ObjectsRules/ProjectedSurface) | One object | OK | KO | OK |
| [Orientation](doc/1ObjectsRules/Orientation) | One object | OK | KO | OK |
| [Object height](doc/1ObjectsRules/ObbHeigh) | One object | OK | OK | OK |
| [Object length](doc/1ObjectsRules/ObbLength) | One object | OK | OK | OK |

### Two-object rules

#### Historical IfcClash rules

| **Rule** | **Type** | **Rule status** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Clearance](doc/2ObjectsRules/Clearance) | Two objects | OK | KO | OK |
| [Intersection](doc/2ObjectsRules/Intersection) | Two objects | OK | KO | OK |
| [Collision](doc/2ObjectsRules/Collision) | Two objects | OK | KO | OK |

#### Advanced clearance rules

| **Rule** | **Type** | **Rule status** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Clearance Above Object](doc/2ObjectsRules/ClearanceAbove.md) | Two objects | OK | KO | OK |
| [Clearance Next To Object](doc/2ObjectsRules/ClearanceNextTo) | Two objects | KO | KO | OK |
| [Clearance Below Object](doc/2ObjectsRules/ClearanceBelow) | Two objects | KO | KO | KO |

#### Clearance with OBB

An Oriented Bounding Box (OBB) is the smallest box enclosing an object. These checks are fast and, most of the time, precise enough to detect a problem.
The OBB has a second advantage: it can easily be enlarged or shrunk. We can have OBBs enlarged around the top, or with one side reduced.

The last benefit is detecting the front and back of an element. Most of the time, this information is not included in the model. We cannot determine the front, back or side of an object. For a door, elements can pass on the sides, but not through the opening (from the front or the back). These methods can help detect objects in front of a door. The OBB is a rectangular cuboid, and the functions to modify or compute it are very simple. It is a degraded method, but it still produces convincing results.


| **Rule** | **Type** | **Rule status** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [OBB Above](doc/2ObjectsRules/OBB_Above) | Two objects | OK | KO | OK |
| [OBB Below](doc/2ObjectsRules/OBB_Below) | Two objects | OK | KO | OK |
| [OBB Front And Back](doc/2ObjectsRules/OBB_Front_And_Back) | Two objects | KO | KO | KO |

#### Other types of rules

| **Rule** | **Type** | **Rule status** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Surface Recover](doc/2ObjectsRules/SurfaceRecover) | Two objects | KO | KO | KO |
| [Angle Between](doc/2ObjectsRules/AngleBetween) | Two objects | KO | KO | KO |
| [Direct View](doc/2ObjectsRules/DirectView) | Two objects | KO | KO | KO |
| [Face Check](doc/2ObjectsRules/FaceCheck) | Two objects | KO | KO | KO |

### Complex rules

| **Rule** | **Type** | **Rule status** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Free Space in Room](doc/ComplexRules/FreeSpaceInRoom) | Complex | KO | KO | KO |
| [Find Path](doc/ComplexRules/FindPath) | Complex | KO | KO | KO |
| [EvacuationDistance](doc/ComplexRules/EvacuationDistance) | Complex | NOK | KO | KO |
| [Alignement](doc/ComplexRules/Alignement) | Complex | NOK | KO | KO |



# Installation
This project uses the following components.
IfcOpenShell
PythonOCC with a Conda installation


# Progress
The first step is to create new rules to extend the possibilities. These rules can be used in any template.

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





# TODO

0. Finish the documentation

1. Finish the grouping (grouping by)

2. Property extraction
When using the relative rule, we can extract values from objects in order to sum quantities.
This has not been tested properly.

3. Orientation rule
We could make the orientation rule easier to check whether it faces north or south, simply by introducing some text.


4. Determine the main side of an OBB
When looking for the main side of an OBB, the Z face is taken into account.
For a slab, this can be useful.
For a wall, this can lead to errors. When a wall is taller than it is long, this can cause inaccuracies.


5. Expand the number of rules and create the base rule structure

6. Create the rule association in Python => DONE

7. Study the implementation in ifcclash
