# Description

This rule determines if the direct view between two objects is free, by casting rays between them.

Usage : vérifier qu'un objet reste visible depuis un point d'observation (poste de supervision, emplacement d'opérateur), malgré les obstacles du modèle.

Limitation: this rule tests the mutual geometric visibility between two objects. It does not model an oriented device: no direction of view, no field of view, no viewing cone. A camera check would need the orientation of the device as an input and is out of scope here.

## Algorithm

1. Select faces on each object: only the faces oriented toward the other object (normal facing the other object) emit or receive rays.
2. Determine the emitting objects from `Ray_Source` (default: both source and target).
3. Distribute `Ray_Count` rays per emitting object: the rays are spread over the selected faces proportionally to their area, so large faces get several rays. The rays of one object are aimed at the other object.
4. Each ray is cast from a sampled point of an emitting face toward a sampled point of the paired receiving face of the other object (face-to-face aiming).
5. A ray is cast up to `Max_Distance`. Only Context objects block a ray: if a ray hits a Context object, it does not touch the target. Source and target are transparent to their own rays (concave geometry does not block its own emission).
6. Cast the rays one by one and stop as soon as the outcome of the pair is already decided (early termination, to limit the number of rays cast):
   - clash guaranteed: even if all the remaining rays touched the target, the ratio would stay below `Threshold` → stop.
   - clash impossible: the number of touches has already reached `Threshold` of the planned rays → stop.
7. Compute the hit ratio over the rays actually cast: the number of rays touching the target divided by the number of rays cast, all emitting objects combined in a single ratio.
8. Raise a clash if the hit ratio is below `Threshold`: the expected view is not achieved.

# Property

Source: Object A - the objects from which the view is tested.

Target: Object B - the objects that must be seen.

Context: Object C - the objects acting as walls. If a ray hits a Context object, the view is blocked. If the Context set is empty, nothing can block the rays.

Ray_Source: which object casts the rays. One value (type: string, default: `Source`):
- `Both`: the source and the target both cast rays at each other. More coverage, but twice as many rays.
- `Source`: only the source casts rays toward the target. Fits the observation point use case, where the target has no reason to emit.
- `Target`: only the target casts rays toward the source.

Ray_Count: the number of rays cast per emitting object (type: int, default: 10). Rays are distributed on the selected faces proportionally to their area.

Threshold: the minimum percentage of rays that must touch the target (type: string ending with %, default: "100%"). If the hit ratio is below `Threshold`, a clash is raised. "100%" means a total view is required; "10%" means at least 10% of the emitted rays must touch the target.

Max_Distance: the maximum length of a ray, in meter (type: float, optional, default: no limit). A ray that reaches this distance without touching the target counts as a miss.

# Result

For each source/target pair, one result containing:
- hit_ratio: the percentage of rays touching the target, over the rays actually cast (all emitting objects combined).
- the seen zones: the extent of the hit shot points and of the blocked shot points, in order to visualize which part of each object is seen or hidden.

If the pair stopped early (step 6), hit_ratio and the seen zones reflect only the rays actually cast, not the full planned `Ray_Count`: they are conclusive for the clash decision, but partial as a coverage map.

# Example

A supervision desk must see the entrance area: Source = desks, Target = entrance doors, Context = walls and partitions, Ray_Source = Source, Threshold = "100%". Only the desk casts rays, since the doors have no reason to emit.

Partial occlusion accepted: an operator position must see at least 60% of a machine: Source = operator positions, Target = machines, Context = walls and slabs, Ray_Source = Source, Threshold = "60%", Ray_Count = 20.

## Implementation notes

Conventions left open by this specification, as implemented (2026-10-07):

- A clash result is raised only for the pairs whose hit ratio is below the Threshold; a compliant pair produces no result.
- The sampling is deterministic (R2 low-discrepancy sequence): a given model always gives the same hit ratio. The aim point of a ray uses a shifted sampling index so that origins and aims are decorrelated.
- The receiving face of a ray is chosen with an area-weighted deterministic pick; the aim point is sampled inside that face (face-to-face aiming).
- A zero-length ray (the faces touch) counts as a touch; a ray longer than Max_Distance is a miss and still counts as cast.
- A pair with no castable ray (no face turned toward the other object) has a 0% hit ratio: it clashes for any Threshold above 0%.
- The threshold is exclusive on the clash side: a ratio exactly at the Threshold is compliant, "0%" never clashes.
- The early termination guarantees the same decision as a full cast: "clash" when (touches + remaining) / planned < Threshold (the maximum possible ratio over the cast rays), "ok" when touches / planned >= Threshold (the minimum possible final ratio).
- A face is oriented toward the other object when its normal has a positive dot product with the vector from the face center to the other object's centroid.
