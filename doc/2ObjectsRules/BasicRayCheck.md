# Description

This rule checks the direct line between two objects: a single ray is cast from the center of each source object to the center of each target object, and the Context objects are tested against this ray.

A clash (result) is raised for the pairs in direct view: no Context object stands between the source and the target. The pairs whose ray is blocked by a Context object produce no result.

It is the simplest ray-based rule of the catalogue, the ancestor of the DirectView family: one ray per pair, center to center, binary outcome. Use it for a quick visibility test; use DirectView when a hit ratio or a face-level sampling is needed.

![alt text](image/RayCheck.png)

# Property

Source: Object A - the first set of objects. The ray starts at the center of each source object (the center of its bounding box, in world coordinates).

Target: Object B - the second set of objects. The ray ends at the center of each target object.

Context: Object C - the objects that can block the ray (walls, slabs, partitions...). Source and target objects never block their own ray; everything outside the Context set is transparent to the ray.

Max_Ray_Length: the maximum distance between the two centers, in meter. A pair whose centers are farther apart than this value is not tested at all.

# Result

The result will list all pairs of objects (source, target) that are in direct view: the ray between their centers reaches the target without being intercepted by a Context object.

Each result is one pair; a blocked pair produces no result.

# Example

A supervision station must see a fire door: Source = supervision stations, Target = fire doors, Context = walls and partitions, Max_Ray_Length = 30. A clash is raised for every station in direct view of a fire door; a door hidden behind a wall does not raise a result.

A quick line-of-sight check between an equipment and a sensor, before running the full DirectView analysis.

## Implementation notes

Conventions left open by this specification, as implemented (class `Ray_Check` in Rules.py):

- The ray runs between the centers of the bounding boxes of the objects, not between their placement origins: the origins often lie on the floor plane, where the ray intersection cannot detect the context faces grazed by the ray.
- Pairs are skipped when the two centers coincide (same object) or when the distance between the centers exceeds `Max_Ray_Length`.
- A pair where one of the objects has no geometry is skipped.
- Only the Context objects are loaded into the ray tree: a ray touching only the source or the target object does not block the view.
- An element present in both Source and Target is not checked against itself.
