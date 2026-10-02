# Description

This rule aims to detect objects that are in front of or behind source objects using Oriented Bounding Box (OBB) detection zones.

It creates an OBB for each source object, then identifies the front and back directions based on the OBB's dimensions (using either the "Wide" or "Narrow" method to determine the primary axis). The rule extends the OBB along these directions by the specified tolerance to form two detection zones - one for the front and one for the back. The rule then checks if any target objects intersect with these extended OBB zones in front of or behind the source objects.

# Property
Source: Object A - The objects that will have front and back detection zones created around them.

Target: Object B - The objects to be checked against the detection zones.

Tolerance: The distance to extend the OBB forward and backward from the source object, creating the detection zone depth in both directions.

Direction Method: The method used to determine the front/back axis from the OBB dimensions.
- "Wide": Uses the wider dimension to determine front/back
- "Narrow": Uses the narrower dimension to determine front/back

# Result

The result will list all pairs of objects where target objects are detected within the OBB detection zones in front of or behind source objects.

# Example

It can be used to detect if furniture, equipment, or other components are positioned in front of or behind doors, windows, or other source objects within a specified distance, which could prevent proper access or operation.
