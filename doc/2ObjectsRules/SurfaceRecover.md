# Description

This rule checks that the contact surface between two objects covers an expected value, defined by a min and a max.

Usage : détecter les objets posés les uns sur les autres mais mal juxtaposés (appui partiel d'une poutre sur un mur : contact réel mais surface d'appui insuffisante).

It could be done from top to bottom, but as well from side to side.

## Algorithm

1. Filter pairs: only pairs whose distance is below `Tolerance` are analyzed. Pairs not in contact produce no result.
2. Determine the direction of the check from `Direction`. If `Direction` is a vector, the faces are selected by their normal; if `Direction` is `Auto`, the direction is derived from the paired contact faces. Face pairing in `Auto` mode uses an internal angle tolerance (fixed by the engine).
3. Select faces on each object: the extreme face(s) along the direction (highest or lowest point of the geometry, like ClearanceAbove). Faces of holes pointing to the same direction are ignored.
4. Pair the faces of the two objects facing each other, then compute the contact area: triangles quasi coplanar at a distance below `Tolerance`.
5. If the contact is fragmented into several disjoint zones, all zones of the pair are summed: one single result per pair.
6. Compute the ratio between the contact area and the reference face area, as defined by `Reference`.
7. Raise a clash if the covering value is outside `[Min_Covering, Max_Covering]`. Each bound is optional: only the provided bounds are checked.

# Property

Source: Object A - the objects that rest on (or against) the target objects.

Target: Object B - the objects that support the source objects.

Direction: how the contact direction is determined. One value:
- a 3D vector (type: array of 3 floats): the direction the faces must be aligned with. `Top` and `Bottom` are shortcuts for `[0, 0, 1]` and `[0, 0, -1]`.
- `Auto` (type: string): the direction is derived from the pair itself, by matching faces with opposite normals. Use it for lateral or inclined supports, where no fixed axis fits.

Reference: the face used as denominator when a covering value is relative (a string with %). One value, `Source` or `Target` (default: `Source`). It is the extreme face(s) of the chosen object, as selected in step 3. It is ignored when both covering values are absolute.

Tolerance: the maximum distance, in meter (type: float, default: 0.001), for two objects to be considered in contact, and for two triangles to be counted in the contact area.

Min_Covering: optional (type: float or string). If the covering value is below `Min_Covering`, a clash is raised.

Max_Covering: optional (type: float or string). If the covering value is above `Max_Covering`, a clash is raised.

A covering value can be:
- a float: an absolute area in m² (e.g. `10` for 10 m²).
- a string ending with `%`: a relative value of the reference face area (e.g. `"10%"` for 10% of the reference face).

# Result

For each pair in contact, one result containing:
- contact_area: the summed area of the contact zones, in m².
- ratio: contact_area divided by the reference face area, in %.
- the source and target faces used: normal and area, in order to explain the ratio denominator.

# Example

A beam must rest on a wall with at least 70% of its bottom face in contact: Source = beams, Target = walls, Direction = Bottom, Reference = Source, Min_Covering = "70%".

A bearing plate of 0.05 m² minimum must be in contact with its support: Min_Covering = 0.05.

A pipe support must be laterally in contact with its bracket: Direction = Auto.
