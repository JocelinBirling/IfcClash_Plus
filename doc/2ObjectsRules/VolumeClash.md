# Description

> **Status: Specification** — this rule is not implemented yet; this page describes the target behavior.

This rule checks that the intersection volume between two objects stays below a threshold. It is a classical intersection clash, but the threshold is expressed as a volume to respect instead of a boolean overlap.

Usage : filtrer les micro-intersections (un mur qui mord 2 cm³ sur une gaine), qui sont des faux positifs classiques d'un clash binaire. Un clash pondéré par volume permet de les écarter.

The intersection volume is computed from the exact boolean intersection of the two meshes (or approximated by a coarse 3D voxelization for a faster first pass). The rule returns the intersection volume, and optionally the ratio against the smallest of the two objects.

Open design question: this may be a feature of all the clash rules rather than a dedicated rule (a volume threshold shared by the intersection family), or a candidate for the exception rules (an intersection below the volume threshold is discarded). To be settled at implementation time.

# Property

Source: Object A - the first set of objects to be analyzed.

Target: Object B - the second set of objects to be analyzed.

Tolerance: the maximum intersection volume, in m3, below which the pair is ignored (type: float, mandatory). A pair whose intersection volume is above the Tolerance raises a clash.

Ratio_Type: how the measured volume is compared, when the threshold is relative (type: string, default: absolute):
- `Absolute`: the intersection volume in m3.
- `Smallest`: the ratio of the intersection volume over the smallest of the two objects.
- `Largest`: the ratio over the largest of the two objects.
- `Source` / `Target`: the ratio over the source or the target object.

# Result

The result will list all pairs of objects whose intersection volume exceeds the threshold, each carrying:
- the intersection volume, in m3,
- the ratio according to Ratio_Type, in %.

A pair with an intersection volume below the threshold produces no result.

# Example

A wall biting 2 cm3 into a duct must not be reported, a structural penetration of 0.5 m3 must be: Source = walls, Target = ducts, Tolerance = 0.01 (m3).

Micro-intersections under 0.1% of the smallest object are ignored: Ratio_Type = `Smallest`, Tolerance = 0.001.
