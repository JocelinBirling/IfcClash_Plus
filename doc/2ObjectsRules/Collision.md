# Description

This rule aims to detect collisions between objects.

It will check if any part of the source objects intersects with any part of the target objects. A collision is detected when the geometries of two objects overlap in space.

# Property
Source: Object A - The first set of objects to be analyzed.

Target: Object B - The second set of objects to be analyzed.

Allow Touching: If True, objects that are exactly touching (but not overlapping) will be considered as a collision. If False, only actual geometric overlaps will be detected.

# Result

The result will list all pairs of objects where a collision is detected between source and target.

# Example

It can be used to detect any unintended intersections between structural elements, pipes, ducts, or any other building components that should not overlap.
