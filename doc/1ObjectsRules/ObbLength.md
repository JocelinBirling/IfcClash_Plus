# Description

This rule aims to detect objects based on the length of the obb.


# Property
Source: The objects to be analyzed.

Min: The minimum length threshold. Objects with a volume greater than this value will be considered.

Max: The maximum length threshold. Objects with a volume less than this value will be considered.

Direction Method: The method used to determine the object's main directions from its oriented bounding box:
- **Wide**: Uses the two widest dimensions of the OBB to determine main directions
- **Narrow**: Uses the longest dimension and its perpendicular to determine main directions

# Result

The result will list all objects whose length is between the Min and Max values.

# Example

It can be used to detect specific objects based on their size, such as filtering elements by their length.