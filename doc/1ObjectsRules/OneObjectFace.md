# Description

Sur un même objet, on peut vérifier que les faces respectent des règles.

This rule runs face-level checks within a single object, instead of between two objects like the FaceCheck family.

Usage : vérifier que les deux faces opposées du chambranle d'une porte sont à au moins 0.90 m (largeur de passage), la hauteur d'une surface vitrée, des faces internes qui se recoupent (erreur de modélisation), ou des faces qui devraient être d'équerre.

Several checks can run at the same time on the same rule, for instance Orientation and Distance: two faces that oppose each other must also be 0.90 m apart.

## Algorithm

1. Select the faces of group A and group B on the object, using `Face_A_Selection` and `Face_B_Selection`. A face can belong to both groups; the two selections are independent.
2. Pair every face of group A with every face of group B (all against all). A face paired with itself is skipped, and each pair is tested once (unordered).
3. Run every enabled check on each pair. A pair must pass all the enabled checks:
    - `distance`: compute the distance between the two faces. The check fails if the distance is outside `[min, max]` (each bound optional). Pairs of adjacent faces (sharing an edge or a vertex) are skipped if `skip_adjacent` is True, since they touch (distance 0) without being a modeling error.
    - `intersection`: check if the two faces intersect. The check fails if they intersect by more than `tolerance` in depth. Faces that exactly touch without overlapping do not fail.
    - `orientation`: the measured value is only the angle difference between the two faces: the angle between their normals, in degrees in [0, 180]. The check fails if the angle differs from the target `angle` by more than `tolerance`. It is not an orientation against a global direction of the model.
4. Raise one clash per pair per failed check.

# Property

Source: the objects to be analyzed, individually.

Face_A_Selection / Face_B_Selection: two FaceSelection dictionaries, using the same schema as the FaceCheck family (see doc/2ObjectsRules/FaceCheck.md). Default: empty dictionary, meaning all faces of the object.

Each check is enabled by its own boolean, False by default. At least one check must be enabled; a rule with no enabled check is invalid. All the enabled checks are evaluated on every pair, and a pair must pass them all.

distance: enables the distance check (type: bool, default: False).
- min: the minimum distance between the two faces, in meter (type: float, optional). The check fails if the pair is closer than min.
- max: the maximum distance between the two faces, in meter (type: float, optional). The check fails if the pair is farther than max.
- skip_adjacent: if True (default), pairs of faces sharing an edge or a vertex are skipped by this check. Adjacent faces touch each other (distance 0) and would fail any min > 0, without being a modeling error.

intersection: enables the intersection check (type: bool, default: False).
- tolerance: the maximum intersection depth, in meter (type: float, default: 0). The check fails if the two faces intersect by more than this depth. Faces that exactly touch without overlapping do not fail.

orientation: enables the orientation check (type: bool, default: False). The measured value is the angle difference between the two faces, obtained from their normals; no global direction is involved.
- angle: the target angle between the two normals, in degrees (type: float, mandatory when the check is enabled). `0` or `180` for parallel or opposing faces, `90` for perpendicular faces.
- tolerance: the maximum deviation from the target angle, in degrees (type: float, default: 0). The check fails if the measured angle differs from `angle` by more than `tolerance`.

The keys of a check are ignored while its boolean is False.

## Template

```
{
    "Source": [],
    "Face_A_Selection": {
        "min_surface": null,
        "max_surface": null,
        "orientation": null,
        "extreme_faces": false,
        "materials": [],
        "interior_exterior": null
    },
    "Face_B_Selection": {
        "min_surface": null,
        "max_surface": null,
        "orientation": null,
        "extreme_faces": false,
        "materials": [],
        "interior_exterior": null
    },
    "distance": false,
    "min": null,
    "max": null,
    "skip_adjacent": true,
    "intersection": false,
    "intersection_tolerance": null,
    "orientation": false,
    "angle": null,
    "angle_tolerance": null
}
```

# Result

For each object, one result per pair per failed check, containing:
- the failed check and its measured value: the distance in meter (`distance`), the intersection status (`intersection`), or the angle between normals in degrees (`orientation`).
- the two faces of the pair: normal and area.

# Example

Two opposing faces of a door frame must be 0.90 m apart: Source = door frames, Face_A_Selection = Face_B_Selection = the two faces of the jambs (orientation = Top, extreme_faces = true), orientation = true with angle = 180, angle_tolerance = 10 (the two faces oppose each other within 10 degrees), distance = true with min = 0.90. A pair that does not oppose fails the orientation check; an opposing pair closer than 0.90 m fails the distance check.

The free height of a glazed surface must be between 2.10 m and 2.50 m: Source = glazed walls, Face_A_Selection = the bottom faces (orientation = Bottom, extreme_faces = true), Face_B_Selection = the top faces (orientation = Top, extreme_faces = true), distance = true with min = 2.10, max = 2.50.

The skin of a wall must not self-intersect: Source = walls, empty face selections, intersection = true with intersection_tolerance = 0.001 (overlaps deeper than 1 mm fail the check).

Two faces of a frame must be perpendicular, within 5 degrees: Source = frames, face selections on the two face groups, orientation = true with angle = 90, angle_tolerance = 5.
