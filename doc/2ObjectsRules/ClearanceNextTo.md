# Description

> **Status: Specification** — this rule is not implemented yet; this page describes the target behavior.

This rule checks that objects stand next to each other: the target must be beside the source, on the same level, not above or below it. It is the lateral counterpart of ClearanceAbove and ClearanceBelow.

The distance is measured between the selected extreme parts of the two objects, on the horizontal plane. The Top_Tolerance and Bottom_Tolerance allow the target to sit slightly above or below the level of the source without invalidating the "next to" relation.

# Property

Source: Object A - the reference objects.

Target: Object B - the objects checked next to the source.

Type: the parts of the two objects the distance is measured between:
- MinToMin: the shortest distance between the two objects (the nearest points).
- MinToMax / MaxToMin: the distance between the nearest part of one object and the farthest part of the other (reserved, to be defined).
- MaxToMax: the biggest distance between the two objects (the farthest points).

Min: the minimum distance, in meter. If the measured distance is below Min, it will raise a clash (too close).

Max: the maximum distance, in meter. If the measured distance is above Max, it will raise a clash (too far).

Top_Tolerance: by default 0, it allows the target object to be a little bit above the source object without counting as "above".

Bottom_Tolerance: by default 0, it allows the target object to be a little bit below the source object without counting as "below".

# Result

The result will list all pairs of objects where the measured distance is outside the [Min, Max] interval, or where the vertical offset between the two objects exceeds the Top_Tolerance / Bottom_Tolerance.

# Example

Two switchboards standing next to each other must keep a 10 cm maintenance gap: Source = switchboards, Target = switchboards, Type = MinToMin, Min = 0.10.

A piece of furniture must not stand farther than 0.50 m from its desk: Type = MinToMin, Max = 0.50.
