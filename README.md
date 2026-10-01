# IfcClash_Plus
This is a test to find the best solution before trying to implement directly into IfcClash.
We have 4 type of rule that exist inside IfcClash.
-Intersection
-Collision 
-Clearance
-Ray Check 
The idea is to create a lego set of rule that can be used together.


# Main functionality
- Create a template to standardize rule creation
    I want to create a catalog of rule. In order for them to work, i need a standardization of the functionality to expand them and make them work all together.
    For the standardisation, i started a dictionnary to explain my vocabulary. 
    [Vocabulary](doc/Rule.md)
- Use IDS to select
    The idea is to reuse IDS Facet to select list of elements. I am pretty sure more and more people are starting to use it, so it will be easier for everyone with time.
- Waterfall of Rule
    The result of a rule will produce a list of object. This list of object can be used in another rule. This can be used to expand the rule functionnality, and complexity.
    With rule in waterfall, you can produce some complexe case.
- Authorize exception
    In real life, there is edge case in everywhere. You can either select them by hand or reduce them. This aim to reduce the edge case to the bare minimum.
- Categorize result
    The BCF can carry information like actor, or criticity. Sometime, these can be done with a script.
    - by actor
    - by criticity
    - etc...
- Regroup result by several way
    I want to expand the way to regroup result of clash.
- Group rule in folder
    You can gather rule together in a folder of rule. This folder can be activated or desactivated by a rule, or by an ids selection.
    This can prevent from launching rule that are not coherent with the model. 

- Relative or absolute result
    The absolute or relative checking functionality allows users tod efine quantitative or relative quantities for clash detection result.
    For absolute checking, it use a fixed threshold, a number of result, or the value of a property.
    For relative checking, it compare the source and target element using some arithmetics (eg the number of source elements versus the number of target elements). This allows for dynamix validation, such as ensuring that the ratio or difference between two sets of elements meets the criteria.


# Catalog of rule
There is a sheet for every rule, that present the rule, the parameters and the edge case.


## List of Rule

### One Object Rule

| **Règle** | **Type** | **Règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Volume](doc/1ObjectsRules/Volume) | One Object | OK | KO | OK |
| [Area](doc/1ObjectsRules/Area) | One Object | OK | KO | OK |
| [Top Or Bottom Surface](doc/1ObjectsRules/TopOrBottomSurface.md) | One Object | OK | KO | OK |
| [Lateral Surface](doc/1ObjectsRules/LateralSurface) | One Object | OK | KO | OK |
| [Projected Surface](doc/1ObjectsRules/ProjectedSurface) | One Object | OK | KO | OK |
| [Orientation](doc/1ObjectsRules/Orientation) | One Object | OK | KO | OK |
| [Object height](doc/1ObjectsRules/ObbHeigh) | One Object | OK | OK | OK |
| [Object length](doc/1ObjectsRules/ObbLength) | One Object | OK | OK | OK |

### Two Object Rule

#### Historic IfcClash Rule

| **Règle** | **Type** | **Règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Clearance](doc/2ObjectsRules/Clearance) | Two Objects | OK | KO | OK |
| [Intersection](doc/2ObjectsRules/Intersection) | Two Objects | OK | KO | OK |
| [Collision](doc/2ObjectsRules/Collision) | Two Objects | OK | KO | OK |

#### Advance Clearance Rule

| **Règle** | **Type** | **Règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Clearance Above Object](doc/2ObjectsRules/ClearanceAbove.md) | Two Objects | OK | KO | OK |
| [Clearance Next To Object](doc/2ObjectsRules/ClearanceNextTo) | Two Objects | KO | KO | OK |
| [Clearance Below Object](doc/2ObjectsRules/ClearanceBelow) | Two Objects | KO | KO | KO |

#### Clearance with OBB

Oriented Bouding Box (OBB) is smallest box that surround an object. Those check are fast and most of the time, they are precise enough to detect a problem.
OBB has a 2nd advantages, it can be expanded or reduced easily. We can have obb that are expended around the top, or the side is reduced.

The last benefits is to detect the front or back of an item. Most of time, the information is not included in the model. You can not determine the front, the back, or the side of an object. For a door, you can have thing passing by the side, but not in the doorway (in the front or back). These method can help detect objects in front of a door. The OBB is a cuboid, the function to modify it, or to calculate it are very simple.


| **Règle** | **Type** | **Règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [OBB Above](doc/2ObjectsRules/OBB_Above) | Two Objects | OK | KO | OK |
| [OBB Below](doc/2ObjectsRules/OBB_Below) | Two Objects | OK | KO | OK |
| [OBB Front And Back](doc/2ObjectsRules/OBB_Front_And_Back) | Two Objects | KO | KO | KO |

#### Other type of rule

| **Règle** | **Type** | **Règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Surface Recover](doc/2ObjectsRules/SurfaceRecover) | Two Objects | KO | KO | KO |
| [Angle Between](doc/2ObjectsRules/AngleBetween) | Two Objects | KO | KO | KO |
| [Direct View](doc/2ObjectsRules/DirectView) | Two Objects | KO | KO | KO |
| [Face Check](doc/2ObjectsRules/FaceCheck) | Two Objects | KO | KO | KO |

### Complex Rule

| **Règle** | **Type** | **Règle** | **Doc** | **Test** |
|-----------|----------|-----------|---------|----------|
| [Free Space in Room](doc/ComplexRules/FreeSpaceInRoom) | Complex | KO | KO | KO |
| [Find Path](doc/ComplexRules/FindPath) | Complex | KO | KO | KO |
| [EvacuationDistance](doc/ComplexRules/EvacuationDistance) | Complex | NOK | KO | KO |
| [Alignement](doc/ComplexRules/Alignement) | Complex | NOK | KO | KO |



# Install
This project is using the following.
IfcOpenShell


# Progress
The first step is to create new rule to expand possibilities. Those rule can be used in any template.

V0.1
Create the main structure of script

V0.2
- Create Above Rule
    This rule check if there is nothing above an object.

- Create several grouping function
    The rule create a list of result. This list of result can be grouped by different way. I implemented several way of grouping object. 
- Create absolute and relative check
    By grouping object, you create a sets of object. It's important to check if these set respect a rule. 
    I must have at least one door intersecting with each space. 
    I must have at exactly 1 drain below a shower drain. 

- Create a criticity automatic classification
    Each result can be automaticaly classified in order to determine it's criticity.This could be exporter toward a BCF. 
- Update the actor automatic classification
    Each result can be automaticaly classified in order to determine an actor to tag. This could be exporter toward a BCF. 

V0.3
- IA Use
I have started to use IA to create function. Previously, it was way more sporadic.

- Create custom OBB Class
This is a customOBB class made with the Bnd_OBB() class from OCC. It will help to modify existing OBB, in order to expand, detach side or top. 
This new OBB will then create a new space that can clash with objects.
The obb is very convienent to modify, and easy enough to apply transformation.

- Function to generate OBB
I created several function to generate OBB from object. Some of them are better than other.
One of them, is interessting, because it create an OBB with the Z axis stuck to (0,0,1). It's helpful for box like object.

- Add a display function
This function should help to see, what should happen in the rule. It will print OBB Box, where the clash should appear.
It will show the object that are 

- OBB Top and bottom
This rule will check if something is above or below an object. It will create a new obb in the top (or bottom) of the object and check if something clash with it.
It's a little bit different from Above or Below rule, because you can modify the size of the OBB more precisely. 

- OBB Front and Back
This rule will check if something is in front or in the back of the object.
It's quite hard to detect what is the front and back. I am using the size of the OBB to detect that. It will be then dependent to each objects.
For a door, the front is the wide part. For some other object, it will be the narrow part.

- Added a few test case to help debug everything
still WIP

1. Expand number of rule and create the base structure for rules
2. Create association of rule in python
3. Studies implementation in ifcclash



V0.4







# TODO


1. Exception for IfcSystem or same IfcBuildingStorey
Before launching the rule, we could exclude object that have the same IfcSystem, or that are not in the same level.

2. Finish the Grouping by

3. Property extraction
When we use the relative rule, we can extract value from objects in order to sum quantites.
This was not tested properly.

4. Create a system to dispatch result
We could want to have the source object that failed, or pass the test only.


5. Orientation Rule
We could facilitate the orientation rule to check if it face the north or south, by simply introducing text.


6. Determine main side in OBB
When we try to find the main side of an OBB, the Z face is taken into account.
For a slab, it could be usefull. 
For a wall, it could get to error. When a wall is higher than longer, it can cause inacuracy.




