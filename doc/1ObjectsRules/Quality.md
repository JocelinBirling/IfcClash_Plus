# Description

This rule validates the geometry quality of the source objects. It is
the upstream quality gate of the whole catalogue: no other rule
checks the geometry itself, and broken solids are a classic source of
false negatives in clash detection (they corrupt the OCC booleans).

It is a one object rule: every source object is checked against a set
of geometry quality controls, powered by BRepCheck_Analyzer and
geometry measurements. The rule never compares two objects: every
control pits one object against itself or against its own data.

# Property

Source: all objects (any type). No target, no context.

Parameters:

- **Checks**: the list of active checks, selected by the user. Only
  the active checks are applied. Available checks:
  - **Watertight**: the solid must be closed (a solid with open
    shells is not watertight).
  - **Self-intersection** (clash with itself): the solid must not
    intersect itself.
  - **Inverted faces** (orientation): the faces must be correctly
    oriented; a solid with inverted faces yields wrong booleans
    downstream.
  - **Clash with its own bounding box**: the solid intersected with
    its own bounding box must give itself back. A boolean failure or
    a lost volume means the shape data is corrupted and unusable for
    the downstream clash rules.
  - **Degenerated geometry**: flat triangles, faces without normals,
    objects with a null volume. These shapes pass through the
    modelers but produce degenerate clashes.
- **Min face area**: the area threshold under which a face counts as
  degenerated.

# Result

One ClashResult per object and per failed check, for instance "wall
W1: not closed" or "slab S2: self-intersection". Each result carries
the evidence of its check (the failed BRepCheck status or the
measured value).

This granularity keeps the result atomic: one result is one
verdictable fact, ready for the sorting phase and the BCF subjects
(see specification_BCF_Link.md).

# Example

- Before a clash run, exclude the open solids which corrupt the OCC
  booleans (a classic source of false negatives).
- In the cascade, the KO objects feed a "model quality" BCF addressed
  to the modeller (maquettiste), not to the trade.
- In Select: pass only the healthy objects to the downstream clash
  rules — the gate of the waterfall.
