# Object sets
In this project, we will give a name to each set used in the rules.
We have three types of elements:
* Source
* Target
* Context

Object sets can come from different models.

## Source
These are the objects we test. They form the main set of the clash. There will always be a source in each clash.
Without a source, there is no rule.

For now, the source is considered the main set of objects. By default, the source is what gets passed on to cascading rules.

## Target
Targets are tested. They form the secondary set of the clash.
For two-object rules, the set of source objects will be checked against the set of target objects.

## Context objects
Context objects are not directly part of the clash, but they will be used as additional information. They must help the rule.
For example, if we want to test the free line of sight between two objects (A and B), the wall and the slab will be used as context elements to determine the free line of sight.




# Rule folders
Rule folders make it possible to gather rules into folders and subfolders. This is a very classic construct and it allows organizing rules by theme.



# The 3 main rule classes
Rules can be classified into several categories. They are organized around the number of elements needed for the clash.
All rules can be run on sets of objects, but in the end, the script will test objects individually, in pairs, or multiple objects against each other.

## One-object rules
This rule will test one object at a time.
The object will be taken in isolation and geometric properties will be checked.

### Example
Object A must have a top surface of 10m2.
Object A must face south.

## Two-object rules
These are the most common rules. They take the form A against B.
They check set A against set B. Each element of set A will be "clashed" against all the elements of set B.

### Example
Object set A must not intersect object set B.

## Complex rules
These are rules that require more than 2 object sets.
They do not fit into the very specific scope of the 2 rule types (1 and 2 objects). Each new rule will require specific development.

### Example
A rule checking the turning circle of a wheelchair will use IfcSpace and the furniture.
* We cannot say whether it is the space or the furniture that is at fault.
Check whether there is a cable tray path between two rooms.
* We cannot really target either a source object or a target.

## Points of attention

### Asymmetric rule
When a rule has two sets (source and target), the rule is not necessarily symmetric. Some rules are symmetric, but this is not the general case.
* Set A against set B does not produce the same result as set B against set A.


# Rule usages
Rules are used and reused in various ways within this project. The same rule can serve different purposes: checking, filtering, activating, etc...
It will always be the same rule, but we will change the way it is used, so the result of the rule will be passed on.



## Select rule
A Select rule is a rule that is used to produce a list of objects. This selection of objects by a rule makes it possible to chain rules one after another. It works the same way as IDS facets: facets are as much a way to select objects as to check them.

### Cascade processing
Using Select rules enables cascade processing. We can select objects based on geometric characteristics and perform other operations. This processing offers great flexibility and multiplies the number of rules that can be imagined. The most complex cases can therefore be built on the basis of a set of simplified rules.


## Activation rule
Rule folders can be enabled or disabled, depending on a rule. In this way, when a rule file is run, some of the rules will only be activated under certain conditions.
Here, we can use any geometric rule, or a rule with an IDS select.



## Boolean rule
Boolean rules are used in folders and in exceptions. A Boolean rule outputs a Boolean value, true or false. This value is obtained by running a predefined set of methods.
The following cases make it possible to determine whether the rule returns true or false:
- "have_result"
- "have_no_result"
- "have_less"
- "have_more"
- "have_more_or_equals"
- "have_less_or_equals"
- "equals"
This is based on the number of sources or targets at the output of the rule.

Boolean rules can be combined with the classic operators AND, OR and NOT.

### Exception rules
"C'est l'exception qui confirme la règle" ("The exception proves the rule") is a French maxim. It describes the philosophy of this implementation well.
There will always be exceptions, however, we want to reduce them to a minimum so they can be handled manually.

Exception rules run at the end of rules, and only for two-object rules.
The two objects A and B are passed to one or more exception rules. With two objects, we can be much more precise in what we ask of the object sets.

The exception rule also makes it possible to discard certain cases that are too troublesome. If two objects are in the same IfcSystem, they can be discarded, as it is most likely a modeling artifact.


# Absolute or relative verification (Must rule)
This verification makes it possible to handle relative or absolute quantities on rule results.
It will always start by grouping all the results.
The goal is to compare the quantity or the number of elements in each of these groups.

Example
In each room (the grouping), we must find exactly one fire extinguisher.
For each door (the grouping), we must have at least two adjacent spaces.
For each floor (the grouping), we must have twice as many toilets as spaces.
For each room (the grouping), we must have more than 10m2 of tiling.


## Absolute number of elements
Once grouped, we must have a number X of elements in each group.
For example, on each floor, we must have 2 doors.
The relation can come from the source.
This will apply, at your choice, to either the source or the target, but not to both.

## Relative number of elements
The number of source elements must be X times the number of target elements.
For example, in each room, we must have at least 2 times more chairs than tables.
This will apply to the source AND the target, in order to have a relative quantity of both.


## Absolute quantity
Here we use a quantity that is stored in a property. This quantity will be summed according to the grouping across the whole result of a rule.
We can therefore measure the window area of a room.
This will apply, at your choice, to either the source or the target, but not to both.

## Relative quantity
The quantity must be relative between the source and the target. A relation will link the two quantities.
The sum of set A must be greater than the sum of set B.

# Result management

## Grouping results
Once the rule has been processed, we need a tool to make filtering and processing the results easier.
We can group by several methods in order to automatically gather objects sharing a common characteristic.

## Group by IfcRelation
Group by IfcSpace
Group by IfcBuildingStorey
Group by IfcBuilding

## Other grouping methods
Group by source object
Group by severity
Group by clustering


# Automatic categorization

## Actor
We can automatically assign an actor to each object based on an IDS specification.
These can be reused in a BCF later.

## Criticality
We can automatically assign a criticality to each object based on an IDS specification.
These can be reused in a BCF later.



# Idea box


## Exception before run
We could run a gathering step before the rule is executed.
If two objects are in the same IfcSystem, then there is no point in checking whether they clash. Most of the time, it is a model issue with very small edge overlaps (a modeling issue, not a real one).
We could also split the check by floor (building storey). This could help reduce the load (or be useless if the tree structure is good).
Nevertheless, it remains useful to implement a "per floor" approach, to avoid issues that would be just above an object through the slab.
