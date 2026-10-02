# Description

This rule aims to detect intersections between objects within a specified tolerance.

It will check if any part of the source objects comes within the specified tolerance distance of any part of the target objects. Unlike collision detection which requires actual geometric overlap, intersection detection identifies objects that are close to each other.

# Property
Source: Object A - The first set of objects to be analyzed.

Target: Object B - The second set of objects to be analyzed.

Tolerance: The maximum distance at which objects are considered to be intersecting. Objects within this distance of each other will trigger a clash result.

# Result

The result will list all pairs of objects where an intersection is detected between source and target within the specified tolerance.

# Example

It can be used to detect objects that are too close to each other, such as identifying potential clearance issues between MEP components or checking if elements maintain required minimum distances.
