# Description

This rule aims to detect objects that are too close to each other based on a minimum clearance distance.

It will check the distance between all pairs of source and target objects. If any two objects are closer than the specified clearance distance, a clash will be reported.

# Property
Source: Object A - The first set of objects to be analyzed.

Target: Object B - The second set of objects to be analyzed.

Clearance: The minimum required distance between objects. Objects that are closer than this distance will trigger a clash result.

# Result

The result will list all pairs of objects where the distance between source and target is less than the specified clearance value.

# Example

It can be used to ensure that building elements maintain required minimum distances from each other, such as verifying clearance requirements between structural components or MEP systems.
