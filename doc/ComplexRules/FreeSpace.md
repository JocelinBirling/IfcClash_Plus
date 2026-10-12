# Description

This rule checks whether a cylinder of free space of a given diameter and height can be found in a room.

Usage : vérifier qu'un fauteuil roulant peut tourner dans un local (cercle de giration de 1.50 m de diamètre).

## Algorithm

1. For each source object (usually an IfcSpace), take its footprint: the cylinder must fit entirely inside it. The base of the cylinder sits at the lowest face of the source (the floor of the space).
2. Build the obstacles: the objects of the Context set. Every object outside Source and Context is ignored.
3. Compute the region of the free placements: the footprint eroded by the cylinder radius (where the disk center may lie), minus the 2D projection of each obstacle clipped to the height slab of the cylinder [floor, floor + height], each projection grown by the radius. A free placement exists as soon as this region is not empty.
4. A placement is free if the cylinder fits entirely inside the footprint and does not intersect any Context object. Touching is allowed: a distance of 0 to the footprint or to an obstacle does not fail the placement.
5. The reported placement is the point of the region with the largest clearance (binary search on the erosion depth of the region).
6. Raise a clash for each source where no free placement is found.

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

## Implementation notes

Conventions left open by this specification, as implemented (updated 2026-10-12):

- The rule is a one-object rule with an additional Context selection (no target set): RuleCheckComplex is an unusable draft in RuleClass.py.
- The footprint is the union of the projections of the triangles lying in the lowest slab (1 mm) of the source mesh; its base height is the floor. A source without footprint clashes.
- The free placements are computed exactly as a 2D region (footprint eroded by the radius, minus the obstacle projections of the height slab grown by the radius), not sampled on a grid: no feasible placement, however small, can be missed. The obstacle projection of the slab is the meshed boolean intersection of the obstacle with the slab box (mesh deflection: radius / 25).
- An obstacle blocks a placement only when the intersection has a positive volume: tangential contacts are free (the blocking zones are shrunk by a touch epsilon).
- Obstacles are pre-filtered per source by bounding box (horizontal and vertical) before the projection is computed.
- The reported placement is the point of the free region with the largest clearance (binary search on the erosion depth), not the first one found.
- Free placements (position on the floor and margin) are exposed in rule.placements per source entity; only the sources without any placement raise a clash result.
