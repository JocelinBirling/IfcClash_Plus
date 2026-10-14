# Description

This rule checks the static stability of placed objects: an object
standing on its own must not tip over under its own weight.

The center of mass is computed from the geometry (BRepGProp), then
projected along the vertical axis of the object (the vertical axis of
its OBB, not the global Z: an object tilted or placed on a slope is
checked along its own standing direction). The projection must fall
inside the footprint of the object, with a safety margin.

The footprint is the real projection of the solid on the ground
plane, not the bottom face of its OBB: the stability zone follows the
actual shape of the object, which is stricter than a bounding
rectangle for L-shaped or cantilevered footprints.

It is a one object rule: one object is checked against its own
geometry, no target and no context selection are involved.

# Property

Source: the placed objects to check (technical cabinets, equipment,
furniture, precast elements, anything standing free on a support).

Parameters:

- **Stability margin (m)**: the required distance between the
  projected center of mass and the nearest edge of the footprint.
  Default 0: the plain stability condition.
- **Safety factor (k)**: the margin is scaled by the safety factor.
  The check passes when the measured distance from the projection to
  the nearest edge of the footprint is at least k × m. Default 1.0.

# Result

One ClashResult per unstable object, carrying the center of mass, its
projection on the ground plane, the measured distance to the nearest
footprint edge and the required margin. The rule has a single check,
so one result is one unstable object — one verdictable fact, ready
for the sorting phase and the BCF subjects (see
specification_BCF_Link.md).

# Example

- A 2.10 m high, shallow technical cabinet must not tip: its center
  of gravity must stay inside its footprint.
- Check the cantilevered equipment before issuing the lifting
  instructions.
- In Select: output the unstable objects for rework or for the
  lifting study.
