# Description

This rule checks whether a cylinder of free space of a given diameter and height can be found in a room.

Usage : vérifier qu'un fauteuil roulant peut tourner dans un local (cercle de giration de 1.50 m de diamètre).

## Algorithm

1. For each source object (usually an IfcSpace), take its footprint: the cylinder must fit entirely inside it. The base of the cylinder sits at the lowest face of the source (the floor of the space).
2. Build the obstacles: the objects of the Context set. Every object outside Source and Context is ignored.
3. Search a free placement: a regular grid of candidate positions covers the footprint (automatic step, a fraction of the diameter), then a local refinement runs around the best node. The first free placement wins; the search stops there.
4. A placement is free if the cylinder fits entirely inside the footprint and does not intersect any Context object. Touching is allowed: a distance of 0 to the footprint or to an obstacle does not fail the placement.
5. Raise a clash for each source where no free placement is found.

# Property

Source: Object A - the objects defining the available space, most of the time an IfcSpace.

Context: Object C - the objects that can obstruct the placement: walls, furnishing, equipment... Everything outside Source and Context is ignored.

Diameter: the diameter of the circle, in meter (type: float, default: 1.50, the wheelchair turning circle).

Height: the free height to check above the circle, in meter (type: float, mandatory). The cylinder spans from the floor of the space up to this height: a low ceiling, a protruding beam or a suspended luminator inside the cylinder fails the placement.

## Template

```
{
    "Source": [],
    "Context": [],
    "diameter": 1.50,
    "height": null
}
```

# Result

For each source where a free placement is found:
- position: the center of the placed cylinder, to visualize the placement.
- margin: the shortest distance from the placed cylinder to the obstacles and to the footprint. Touching is allowed, so the margin can be 0.

For each source where no free placement is found: a clash is raised.

# Example

A wheelchair must be able to turn in each accessible sanitary room: Source = IfcSpace of the sanitary rooms, Context = fixtures and furniture, Diameter = 1.50, Height = 1.40.

A stretcher must be able to maneuver in the corridors: Source = IfcSpace of the corridors, Context = furniture and equipment, Diameter = 2.20, Height = 2.00.
