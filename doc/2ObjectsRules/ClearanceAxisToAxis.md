# Description

This rule measures the distance between the axes of two linear objects and validates it against an interval. The axis of an object is the support line of the long dimension of its OBB passing through the centroid, truncated at the OBB extents to form a finite segment.

Usage : réseaux (tuyauteries, gaines, chemins de câbles, tronçons) — les cotes d'exécution et les espacements réglementaires s'expriment en axe-axe (attelage, alignement de pots), pas en espace libre entre peaux. It is the axis counterpart of Clearance, which measures skin to skin: an axis-to-axis rule stays at the regulatory value whatever the couple of diameters, where a skin-to-skin Clearance threshold should be recomputed per Ø/Ø pair.

The rule produces a scalar (the measured distance), not a binary: the result feeds the gravity sorting, the quantitative Must checks and the exceptions. The interval [min, max] detects "too close" as well as "too far" (coverage holes).

The rule is made for networks: Source and Target usually hold every pipe of a bundle or of a network. It therefore only checks the pairs that are neighbours: "too close" on every pair of objects running side by side or meeting, "too far" between each source and its nearest target only (a hole next to it), each pair reported once.

Limitation: the directional condition (parallelism) is not tested here. It combines by AND with AngleBetween, notably as an exception, to produce a full coaxiality (parallel axes AND merged axes).

![alt text](image/Clearance_AxisToAxis.png)

## Algorithm

1. Compute the OBB of each object (method of the project).
2. Extract the axis of each object: the largest dimension of the OBB passing through the centroid, truncated at the OBB extents to form a finite segment.
3. Check the linearity of each object (OBB length / thickness ratio >= `Linearity_Ratio`, thickness = second largest OBB size). A non-linear object (an L-shaped elbow) is not measured axis to axis: the pair is skipped (`On_Non_Linear` = `Skip`) or falls back to the classical skin-to-skin distance (`On_Non_Linear` = `Fallback`), the result then carries the degraded flag.
4. Measure the axis-to-axis distance, in one of the two modes:
   - mode `Perpendicular` (a): the perpendicular offset between the support lines, for objects running side by side (attelage). The offset is only meaningful for quasi-parallel axes (`Axis_Angle` <= `Parallel_Tolerance`); a non-parallel pair automatically falls back to mode (b).
   - mode `MinDistance` (b): always the minimum distance between the two finite segments (analytic), which covers the lateral misalignment of a connection and the end-to-end gap of two runs butted end to end.

   In mode (a), the two segments must face each other over some length (their projections on the common direction overlap): a collinear continuation of a run, or a parallel run shifted along its axis (another room), is not a side-by-side pair and is not measured.
5. Keep the neighbours only: with `Search_Radius`, a pair measured beyond it is left out (for the Fallback pairs, the bounding boxes are tested first, so the costly skin distance is not computed for far pairs).
6. Compare the measured scalar to the interval widened by `Tolerance`:
   - "too close": every remaining pair below `Min_Distance - Tolerance`;
   - "too far": each source against its NEAREST remaining target only, above `Max_Distance + Tolerance` (ties within 1e-9 m: the first target of the selection).
7. Output: the pair when the distance leaves the interval, with the measured value as an attribute (the distance feeds the criticity and the Must checks). A pair met in both orientations (Source and Target selections overlapping) is reported once, in its first orientation.

# Property

Source: the linear objects checked. "Too close" is symmetric; "too far" is checked from each source to its nearest target (a reservation against the duct it receives, a pipe against its neighbour in the bundle).

Target: the linear objects the sources are measured against (often the same selection as Source).

Mode: the measurement mode (type: string, default: `Perpendicular`):
- `Perpendicular`: the perpendicular offset between the support lines of two objects running side by side; non-parallel pairs automatically fall back to the minimum distance between segments (the offset is meaningless for converging lines).
- `MinDistance`: always the minimum distance between the finite segments, whatever the angle of the axes.

Min_Distance: the lower bound of the valid axis-to-axis distance interval, in meter (type: float, optional, default: no lower bound). A measured distance below `Min_Distance - Tolerance` clashes ("too close").

Max_Distance: the upper bound of the interval, in meter (type: float, optional, default: no upper bound). A measured distance above `Max_Distance + Tolerance` clashes ("too far", coverage hole). At least one of `Min_Distance` / `Max_Distance` must be set.

Tolerance: the widening of the interval bounds, in meter (type: float, default: 0).

Linearity_Ratio: the minimum OBB length / thickness ratio for an object to be linear (type: float, default: 10). The thickness is the second largest OBB size. An object below the ratio (an elbow, a compact piece) is not measured axis to axis.

On_Non_Linear: the behavior on a pair containing a non-linear object (type: string, default: `Skip`):
- `Skip`: the pair is left out, no result.
- `Fallback`: the pair is measured with the classical skin-to-skin distance and validated against the same interval; the result carries the degraded flag (`axis_degraded = True`), the measurement is signaled as degraded.

Parallel_Tolerance: the maximum angle between the axes for the Perpendicular mode to apply, in degrees (type: float, default: 1.0). Above it, the pair is measured with the minimum distance between segments.

Search_Radius: the neighbourhood of an object, in meter (type: float, optional, default: no limit). A pair measured beyond it is not checked at all: an isolated object far from the others is neither "too close" nor "too far". Recommended with `Max_Distance` (else an isolated run is "too far" from its nearest, distant, neighbour) and with `On_Non_Linear` = `Fallback` (the skin distance is then only computed for the near pairs).

# Result

For each neighbour pair whose axis-to-axis distance leaves the interval (every pair for "too close", the nearest target of each source for "too far"), one result, once per unordered pair, containing:
- distance_between: the measured axis-to-axis distance (m), the scalar that feeds the criticity sorting, the quantitative Must checks and the exceptions.
- axis_mode: the measurement actually used (`Perpendicular`, `MinDistance` or `Fallback`), since the Perpendicular mode falls back to the segments on non-parallel axes.
- axis_degraded: True when the pair was measured skin to skin (non-linear object, `Fallback`), the measurement is not an axis-to-axis one.
- axis_angle: the angle between the two axes (degrees).

# Example

The pipes of a bundle laid on a cable tray must be spaced 15 cm axis-to-axis ± 1 cm, whatever the couple of diameters: Source = pipes, Target = pipes, Mode = `Perpendicular`, Min_Distance = 0.14, Max_Distance = 0.16, Search_Radius = 0.5. Each pipe is checked against its nearest neighbour: the outer pipes of the bundle (0.30 m apart) are not a hole, a pipe 0.40 m from its neighbour is; the next run on the same line and the bundles of other rooms are not compared.

Coaxiality of a connection: two pipe runs butted end to end must have an axis distance below 5 mm — the good connections are left out, the misaligned ones come out with the offset value for the criticity: Mode = `MinDistance`, Max_Distance = 0.005, Search_Radius = 0.1 (the runs without a partner nearby are not checked). An exception with AngleBetween (angle <= 0.5 degree) adds the parallelism condition.

Every reservation crossing a slab must be coaxial with the vertical duct it receives: axis distance below 1 cm over the full height: Source = reservations, Target = ducts, Mode = `MinDistance`, Max_Distance = 0.01 — each reservation against its nearest duct.

## Implementation notes

Conventions left open by the proposal, as implemented (2026-10-13):

- The axis of an object is the primitive shared with AngleBetween (largest OBB dimension through the centroid): the two rules impose the same axis definition, so a full coaxiality combines coherently.
- The segment of an object is truncated at the OBB extents (center ± half length along the axis): for a straight run, the segment spans the object; the linearity ratio guards the bent or compact shapes for which this approximation would drift.
- The axes are unsigned: parallel and anti-parallel axes both give an angle of 0 degree, the direction sign of the OBB axis carries no meaning.
- The offset of the Perpendicular mode uses the bisector of the two axis directions as the common direction, so the offset stays meaningful for slightly converging axes. The bisector is taken after turning the second axis to the sense of the first: two quasi-parallel axes given with opposite senses would otherwise give a bisector perpendicular to them (fixed 2026-11-09).
- The facing test of the Perpendicular mode uses the same common direction: the overlap of the two segments projected on it must exceed 1e-6 m (two runs butted end to end, overlap 0, are not side by side).
- The pair of a selection with itself skips the identity pair (an object is not compared to itself), like the other two-object rules.
- Neighbourhood (2026-11-09): before, every pair of the two selections was checked against the whole interval, so a network produced mostly false results (a collinear continuation "too close" with an offset 0, every unrelated run "too far", the outer pipes of a correct bundle "too far", each pair twice). The facing test, the nearest target for "too far", Search_Radius and the unordered pairs fix it. A pair given alone (an exception) is its source's only, so nearest, pair: its verdict is unchanged.
- The skin-to-skin fallback (BRepExtrema between the two shapes) validates against the same interval: the degraded measurement is a distance between skins, not between axes, flagged so the result can be told apart in the post-processing.

## Consolidation remarks

- This sheet assumes the "parametrable measure point" engine (skin / axis / centroid) evoked previously: the day an axis-to-skin mode is implemented, it will cover the sprinkler/wall case (the dimension from the axis of the diffuser to the skin of the wall) without new development — only this sheet gains a documented mode.
- Catalog consistency: AngleBetween references its axes by "chosen OBB axis"; this rule imposes the same axis definition (largest OBB dimension x centroid). Raising this axis definition into the shared primitives of linear objects, like the OBB, would fix the semantics once and for all, in the standardization spirit of the project.
