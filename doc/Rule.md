# Set of Objects
In this project, we will give name to each set in the rules.
We have three type of elements
* Source
* Target
* Context

The set of objects may be from differents models.

## Source
Those are the objects we are testing. They will be our primary set for the clash. There will always be a source in any clash. 
Without source, you don't have a rule.

For now, the source will be considered the main set of object. It wil always be the source that is passed to other rule.

## Target
The targets are beeing tested. They will be the secondary set for the clash.
For 2 objects rules, the source objects set will be clashed against the target set.

## Context Objects
The context objects are not directly in the clash, but they will be used as complementary information.
For example, if we want to test free sight between two objects (A and B). The wall and slab will be used as context elements to determine free sight.

# ASymetric Rule
When the rule has two sets (source and target), the rule is not symetric. 
* Set A vs Set B does not produce the same result as Set B vs Set A.

Set A vs Set B will produce the Set A as the main result for futher clash.

# Rule Select
The rule can be used to select object. The objects selected by the rule, the source objects that fail, will be passed down to become the set of object for another rule. 

This cascade of rule can be used to create complexe pattern and detect specific edge case. 


# Type Of Rule
Rule can be classified into several categories. They are centered with the number of elements needed for the clash.
All rule can be launched on set of objects, but at the end, the script will test single, pair or multiple objects against each other.

## One Object Rules
This rule will only test one object by one object.
The object will be taken alone and some geometrical properties will be checked.

### Example
The object must have a top surface of 10m2.
The object must be oriented to the south.

## Two Objects Rules
These rules are the most common one. They will take the form A vs B.
They will check the Set A compared to the Set B. Each element of Set A will be "clash" against all element of Set B.


## Two Faces Rules
WORK IN PROGRESS
This rule work on a face level. It can restrict rule application to certains cases.
If the Object Rule find a relevant face, i can still pass it threw Faces Rule to check if the restriction is OK.
I need to pass the faces with the result.

## OBB
WIP
Define OBB

Above and below are easy to produce
Front and back is not always given in the IFC file.
I want to provide way to determine front and back.
We can determine OBB front or back with the size of the OBB.

A wall is thin and long. We can then determine the direction of the wall with that.
It's similar with a door. It's not clean, but it can help in tricky situation. It must be adapted to every use case.

### Example
The table is below the light.
The wall is at one meter of a chair
The top of the light is below a slab.

## Complex Rules
Complex rules will need several set of objects.

### Example
Rule to check the wheelchair circle will use IfcSpace and furniture.
* We can't say if the space is falty or the furniture.
Check if there is a cable carrier path in between two room.
* We can't really aim for a source object, nor a target.

# Grouping Result
Once the rule has been processed, we need a tool to ease the filtering and the processing of the result. 
We can group by several method to autmaticaly gather object by a same characteristic. 

## Group by IfcRelation
Group by IfcSpace
Group by IfcBuildingStorey
Group by IfcBuilding

## Other Group Method
Group by Source Object
Group by Gravity
Group with clustering


# Boolean Rule
A boolean rule can be set. It will use classic rule and produce a True or False result.
It have several mode to detect a True or False
have_result
have_no_result etc...

It usefull in the activation rule, or the exception rule to produce a value.

# Activation of a Rule
WORK IN PROGRESS


# Exceptions
"Exception that proves the rule"
With every rule, we need to consider exceptions. Edge case are everywhere.
There will always be exceptions, but we can at least reduce them.
The idea is to give the same rule in exception as we can check. 




## Geometry Exception
If we have a 2 objects Rule, that will produce a pair of two objects, we can reuse existing 2 objects rules to make futher check.

## Relation Exception
IfcSystem Exception
Same BuildingStorey Exception


## Example
If we detect collision between two cable carrier, we must check if they are in the same IfcSystem. 
If they are, that's probably only a modeling problem, not a real world issue.






# Absolute Or Relative Check (Must Rule)
It will always start by a grouping of all result. 
The aim is to compare the quantity or number of element in each of these group.

Example
In every room (the grouping), we must find exactly one fire extinguisher. 
For every door (the grouping), we must have at least two spaces next to it.
For every Storey, we must have two times the number toilet per number of space.
For every room (the grouping), we must have more than 10m2 of tiles.  


## Absolute Number of Elements
Once grouped, we must have a X number of element in each group.
By example, in each floor, we must have 2 doors.
The relation can be from source.
This will apply on source or target at will, not both of them. 


## Relative Number of Elements
The number of source element must be X times the number of target elements. 
By example, in each room, we must have at least 2 times more chair than table.
This will be apply on source AND target in order to have a relitve amount of both.



## Absolute Quantity

## Relative Quantity


# Automatic Category

## Actor
We can automaticaly attribute an actor to each object based on an IDS specification. 
These an be reused in a BCF later. 

## Criticity
We can automaticaly attribute a criticity to each object based on an IDS specification.
These an be reused in a BCF later. 


# Folder of Rule
WORK IN PROGRESS




# Idea


## Exception Before Launching
We could run a gathering before that is rule is launched. 
If two objects are in the same IfcSystem, then it's useless to check if they clash. Most of time, it's a model problem with very small edges overlaping (a model issue, not a real one)
We could has well slice the check by building storey. It could help reduce the load (or useless if the tree is good).
Noneless, it still usefullt to implemented a "by building storey", to avoid issues that would by right above an object threw the slab.





