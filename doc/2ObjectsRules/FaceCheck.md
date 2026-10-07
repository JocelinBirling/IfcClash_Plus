# Description

The FaceCheck family descends to the face level to run checks between objects.

Instead of clashing whole geometries, a member rule first selects a set of faces on the source objects, then tests these faces against faces or objects of the target set.

Usage : descendre au niveau des faces pour effectuer des tests plus fins que les règles d'objets : intersections, clearances, zones OBB, orientations.

This file is the family summary: it defines the face selection shared by all members. Each member rule gets its own file in this folder when it is specified.

# Member rules

All members follow the Source/Target structure: faces are selected on the source objects, the target provides what they are checked against.

Each member covers both the former Face and Object variants: if `Target_Face_Selection` is provided, the check runs face-to-face against the selected target faces; if not, it runs against the whole target objects.

| Member | Check |
|---|---|
| FaceClearance | the selected source faces must keep a minimum distance from the target (faces or objects) |
| FaceIntersect | the selected source faces must not intersect the target (faces or objects) |
| FaceOBB | the selected source faces against OBB detection zones built from the target (faces or objects) |
| FaceOrient | the orientation of the selected source faces relative to the target (faces or objects) |

Pending: no member file exists yet. The Distance property (minimum distance or intersection length, in meter) belongs to the member rules, not to the family.

# Property

Source: Object A - the objects whose faces are selected and checked.

Target: Object B - the objects checked against.

Source_Face_Selection: a FaceSelection dictionary (schema below) applied to the source objects. Default: empty dictionary, meaning all faces of the source objects are selected.

Target_Face_Selection: an optional FaceSelection dictionary (schema below) applied to the target objects. If provided, the check runs face-to-face against the selected target faces. If omitted, the check runs against the whole target objects.

## The FaceSelection dictionary

`Source_Face_Selection` and `Target_Face_Selection` share the same schema. The function receives two dictionaries with the following keys; all provided keys combine with AND, and an empty dictionary selects all faces.

| Key | Type | Default | Effect |
|---|---|---|---|
| min_surface | float, m², optional | none | keep only the faces with an area above this bound |
| max_surface | float, m², optional | none | keep only the faces with an area below this bound |
| orientation | 3D vector, optional (`Top`/`Bottom`/`Side` presets) | none | keep only the faces whose normal is aligned with this direction |
| extreme_faces | bool, optional | false | keep only the extreme faces of the geometry along `orientation` (highest or lowest, like ClearanceAbove; faces of holes are ignored). Requires `orientation`, otherwise ignored |
| materials | array of strings, optional, inclusion | none | keep only the faces whose material layer matches one of the listed names |
| interior_exterior | string (`Interior`/`Exterior`), optional | none | keep only interior or exterior faces. Deferred to V2: kept in the specification, not implemented in V1 |

## Template

The default parameters of a member rule, as received by the function:

```
 {
        "min_surface": null,
        "max_surface": null,
        "orientation": null,
        "extreme_faces": false,
        "materials": [],
        "interior_exterior": null
}

`Source` and `Target` are mandatory and filled by the user; an empty array is invalid. `Source_Face_Selection` defaults to the empty selection above (all faces). `Target_Face_Selection` defaults to null: the whole target objects are used; when provided, it takes the same template as `Source_Face_Selection`.


# Result

Each member rule defines its own result section.

# Example

The passage space of a door must stay free: FaceClearance, Source_Face_Selection = the two top faces of the door jamb (orientation = Top, extreme_faces = true), Target_Face_Selection omitted, Target = furniture.

The free height of a glazed surface must be checked against the surrounding walls face-to-face: FaceClearance, Source_Face_Selection = the glazed faces (materials = ["glass"]), Target_Face_Selection = the faces of the walls facing the glazing (orientation toward the source).

# Intra-object checks

The intra-object cases (the passage space of a door, the height of a glazed surface, two opposing faces of a door jamb at least 0.90 m apart) do not belong to this family: they require filtering faces within a single object and are specified in the OneObjectFace rule, in doc/1ObjectsRules/OneObjectFace.md.

# Idea box

Should we add a geometry to test: check the selected faces against a user-provided geometry (a box, a shape) instead of a target object set.

Exception rules must be redone at the face level, once the member rules exist.
