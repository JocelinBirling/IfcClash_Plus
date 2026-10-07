# Description

This rule checks that all the objects of a set are aligned: each object must belong to the alignment, and an isolated or off-axis object raises a clash.

Usage : vérifier l'alignement vertical de poteaux empilés sur plusieurs étages (même axe), l'alignement horizontal des poteaux d'un même étage (une file), ou l'alignement de murs d'une même façade (décalage maximum de 1 m par exemple).

## Algorithm

1. Compute the main axis of the OBB of each source object: the alignment is tested on axes, not on points.
2. Determine the orientation of the objects from `Axis`, or auto-detect it from the dominant axis of the set.
3. Fit one single global element on all the objects (least squares). The fitted element depends on the orientation:
    - `Vertical` (columns): each axis is projected onto the horizontal plane, giving one point per object. The points must lie on one common fitted line, whose direction is fitted from the points. The offset of an object is the distance in plan between its projected point and the fitted line. Stacked columns give coincident points (aligned); a row on one storey gives collinear points.
    - `Horizontal` (walls, beams): the axes are compared in 3D, according to `Alignment_Type`:
        - `Line`: the axes must be collinear, on one common fitted line (segments continuing on the same axis).
        - `Plane`: the axes must lie in one common fitted plane, roughly parallel to it (walls of a facade).
4. Build the group: the objects whose offset stays within `Tolerance`.
5. If the group has at least `Min_Group` members, the alignment is valid: the objects outside the group raise a clash. If the group has fewer than `Min_Group` members, no valid alignment exists: all the objects raise a clash.

# Property

Source: Object A - the set of objects to check. There is no Target: the rule works on a single set.

Axis: the orientation of the object axes (type: string, default: auto-detected from the dominant axis of the set):
- `Vertical`: the objects stand vertical (columns). Their plan projections must be aligned, on one common line.
- `Horizontal`: the objects lie horizontally (walls, beams). See `Alignment_Type`.

Alignment_Type: the alignment of horizontal axes (type: string, default: `Plane`). Ignored when the axes are vertical:
- `Line`: the axes must be collinear.
- `Plane`: the axes must lie in one common plane.

Tolerance: the maximum offset of an object (as defined in the algorithm), in meter (type: float, mandatory). An object farther than Tolerance is outside the group.

Min_Group: the minimum number of objects in the alignment for it to be valid (type: int, default: 3).

## Template

```
{
    "Source": [],
    "axis": null,
    "alignment_type": "Plane",
    "tolerance": null,
    "min_group": 3
}
```

# Result

- the alignment found: the fitted line or plane (direction and position) and its member objects.
- for each object outside the alignment: its offset to the fitted line or plane, in order to guide the correction.

# Example

Columns stacked across storeys must share the same vertical axis: Source = columns of all storeys, Axis = Vertical, Tolerance = 0.10, Min_Group = 3. A column offset in plan by more than 10 cm from the fitted line raises a clash.

Columns of one storey must form a clean row: Source = columns of a storey, Axis = Vertical, Tolerance = 0.10. The plan projections of the column axes must lie on one common line; two columns alone always align, hence Min_Group = 3.

Facade walls must be aligned within 1 m: Source = facade walls, Axis = Horizontal, Alignment_Type = Plane, Tolerance = 1.0.

Wall segments must continue on the same axis: Source = walls, Axis = Horizontal, Alignment_Type = Line, Tolerance = 0.10.
