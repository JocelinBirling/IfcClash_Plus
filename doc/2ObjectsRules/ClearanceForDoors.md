# Description

This rule ensures that nothing obstructs the doors: a clearance zone is built for each door, and any target object penetrating the zone raises a clash.

Usage : s'assurer que rien n'entrave l'ouverture des portes — balayage du vantail, passage des personnes, issues de secours.

## Swing direction detection

The swing direction is not stored in a single attribute, so several methods are tried in order. By proposing several methods, we ensure that at least one works:

1. IfcDoorType.OperationType: the OperationType attribute describes the mechanism (SingleSwingLeft, SingleSwingRight, DoubleDoorSingleSwing, SlidingToLeft...). ParameterTakesPrecedence tells whether these parameters take precedence over the geometry. The left/right convention (IsLeft/IsRight) is defined by the IfcDoorType specification.
2. The geometry (IfcProductDefinitionShape): the swing direction is mainly expressed by the shape representation. The door panel is placed in open or closed position depending on the construction method (SweptSolid, Brep...), and an additional Curve2D representation (usually a plan arc) materializes the leaf sweep. The direction of this arc and the position of the hinge give the swing direction.
3. IfcLocalPlacement: the axis of the door placement gives its orientation in the wall; combined with the operation type, the full direction is derived (inward/outward, hinge left/right).

If no method works, the rule falls back to a conservative default: one rectangle per side of the door (the widest case), so nothing is missed.

## Algorithm

1. For each door, determine the swing direction and the number of leaves: try the detection methods in order, the first that succeeds wins. The number of leaves comes from `Leaves` if provided, otherwise from the operation type.
2. Build one clearance zone per leaf and per checked side, as defined by `Zone_Shape` and `Sides`. If the door has no determined direction, build the conservative rectangles on both sides instead.
3. Check the target objects against the zones: an object penetrating a zone by more than `Tolerance` raises a clash for this door.

# Property

Source: Object A - the doors to be analyzed.

Target: Object B - the objects that must not obstruct the doors. Nothing outside this set counts.

Zone_Shape: the shape of the clearance zone (type: string, default: `Arc`):
- `Arc`: the area swept by each leaf (a quarter to half disk centered on the hinge, radius = leaf width). Sliding doors cannot sweep: they always use `Rectangle`, whatever the value.
- `Rectangle`: a rectangular clearance in front of the door.

Sides: the sides of the door to check (type: string, default: `Swing`):
- `Swing`: only the side where the leaves sweep.
- `Both`: both sides of the door.
- `Front` / `Back`: only the front or the back side, relative to the door placement axis.

Leaves: the number of leaves (type: int, optional, default: derived from the operation type: DoubleDoor* = 2, otherwise 1). A two-leaf door gets one zone per leaf.

Width / Depth / Height: the dimensions of the zone, in meter (type: float, optional). Default: derived from the door geometry — the leaf width for the width, the arc radius and the rectangle depth, the opening height for the height. Provide them to override, for regulatory clearances larger than the physical door.

Tolerance: the maximum penetration depth of a target object into the zone, in meter (type: float, default: 0.001). A shallower penetration is ignored.

## Template

```
{
    "Source": [],
    "Target": [],
    "zone_shape": "Arc",
    "sides": "Swing",
    "leaves": null,
    "width": null,
    "depth": null,
    "height": null,
    "tolerance": 0.001
}
```

# Result

For each door in clash:
- the intruding target objects, with the penetration depth of each into the zone.
- the zone used for the check: shape, dimensions, side, leaf, in order to explain and visualize the clash.

# Example

Nothing may obstruct the swing of an office door: Source = doors, Target = furniture, Zone_Shape = Arc, Sides = Swing. The swept quarter disk of each leaf must stay free.

An accessible landing must stay clear on both sides: Source = doors, Target = furniture, Zone_Shape = Rectangle, Sides = Both, Width = 1.50, Depth = 2.00 — the regulatory clearance overrides the physical door size.

A sliding pocket door must stay clear: Source = doors, Target = furniture, Zone_Shape = Rectangle, Sides = Swing.
