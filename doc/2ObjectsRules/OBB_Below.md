# Description

This rule aims to detect objects that are below source objects using Oriented Bounding Box (OBB) detection zones.

It creates an OBB for each source object, then extends the bottom of the OBB downward by the specified tolerance to form a detection zone. The rule then checks if any target objects intersect with these extended OBB zones below the source objects.

# Property
Source: Object A - The objects that will have detection zones created below them.

Target: Object B - The objects to be checked against the detection zones.

Tolerance: The distance to extend the OBB downward from the bottom of the source object, creating the detection zone depth.

# Result

The result will list all pairs of objects where target objects are detected within the OBB detection zones below source objects.

# Example

It can be used to detect if structural elements, equipment, or other components are positioned below beams, slabs, or other source objects within a specified depth range.
