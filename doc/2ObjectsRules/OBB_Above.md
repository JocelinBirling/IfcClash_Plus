# Description

This rule aims to detect objects that are above source objects using Oriented Bounding Box (OBB) detection zones.

It creates an OBB for each source object, then extends the top of the OBB upward by the specified tolerance to form a detection zone. The rule then checks if any target objects intersect with these extended OBB zones above the source objects.

# Property
Source: Object A - The objects that will have detection zones created above them.

Target: Object B - The objects to be checked against the detection zones.

Tolerance: The distance to extend the OBB upward from the top of the source object, creating the detection zone height.

# Result

The result will list all pairs of objects where target objects are detected within the OBB detection zones above source objects.

# Example

It can be used to detect if pipes, ducts, or other MEP components are positioned above structural elements or equipment within a specified height range.
