# Description

This rule aims to detect objects based on their projected surface area onto a plane.

It will calculate the footprint area of each selected object by projecting its geometry onto a plane perpendicular to the specified direction vector. This projection creates a 2D silhouette of the object as seen from that direction, and the area of this silhouette is measured. Unlike surface area measurements that sum all faces, the projected area represents the object's "shadow" or outline when viewed from a particular direction.

# Property

Source: The objects to be analyzed.

Min: The minimum projected area threshold. Objects with a projected area greater than this value will be considered.

Max: The maximum projected area threshold. Objects with a projected area less than this value will be considered.

Direction: A direction vector (X, Y, Z) specifying the projection direction. The geometry will be projected onto a plane perpendicular to this vector. For example:
- (0, 0, 1) for projecting onto the XY plane (top-down view)
- (0, 0, -1) for projecting onto the XY plane from below
- (1, 0, 0) for projecting onto the YZ plane (view from West)

# Result

The result will list all objects whose projected surface area onto the specified plane is between the Min and Max values.

# Example

It can be used to detect objects with specific footprint characteristics, such as:
- Finding objects with a particular footprint area on the ground plane for spatial analysis
- Identifying elements based on their Shadow area when viewed from above
- Filtering objects by their cross-sectional area when projected onto a vertical plane
