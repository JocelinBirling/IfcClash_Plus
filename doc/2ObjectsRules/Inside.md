# Description

> **Status: Specification** — this rule is not implemented yet; this page describes the target behavior.

This rule checks that a source object lies entirely inside a target object.

It is not the same test as Intersection: Intersection reports any pair closer than a tolerance (an overlap or a proximity), it does not verify the containment. Inside measures the containment itself: the whole geometry of the source must be within the geometry of the target.

The test is planned as a two-step filter, from cheap to exact:
1. OBB pre-filter: the OBB of the source must be inside the OBB of the target (a source OBB sticking out of the target OBB means the containment is already impossible).
2. Exact check: the source geometry intersected with the complement of the target must be empty (within a tolerance); the volume of the source outside the target must be 0.

# Property

Source: Object A - the objects that must be entirely contained.

Target: Object B - the containing objects.

Tolerance: the maximum volume of the source allowed outside the target, in m3 (type: float, default: 0). A source sticking out by less than this volume counts as inside.

# Result

The result will list all pairs of objects where the source is not entirely inside the target: a partially or fully outside source raises a clash, with the outside volume as the measured value.

A source fully inside a target produces no result.

# Example

A equipment box must fit entirely inside its reservation: Source = equipment, Target = reservation voids.

A terminal unit must be entirely within the ceiling void: Source = terminal units, Target = ceiling spaces.
