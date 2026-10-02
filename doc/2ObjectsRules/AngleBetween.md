# Description

This rule aims to detect pairs of objects based on the angle between their main directions.

It calculates the oriented bounding box (OBB) for each object in both source and target sets, extracts their main directions using the specified method (Wide or Narrow), and then measures the angle between these directions. This allows for identifying object pairs that are aligned at specific angular relationships, such as parallel (0°) or perpendicular (90°) arrangements.

# Property

Source: The first set of objects to analyze.

Target: The second set of objects to compare against the source.

Direction Method: The method used to determine each object's main direction from its oriented bounding box:
- **Wide**: Uses the two widest dimensions of the OBB to determine main directions
- **Narrow**: Uses the longest dimension and its perpendicular to determine main directions

Angle Difference: The target angle in degrees between the two objects' main directions:
- **0**: To find parallel objects (aligned in the same direction)
- **90**: To find perpendicular objects (aligned at right angles)
- Any other value: To find objects at that specific angle

Angle Tolerance: The acceptable deviation in degrees from the target Angle Difference. Objects with angles within ±Tolerance of the target angle will be considered matches.

# Result

The result will list all pairs of objects (Source and Target) where the angle between their main directions is within the Angle Tolerance of the specified Angle Difference.

# Example

This rule can be used for various spatial analysis tasks, such as:
- Verify that walls are perpendicular to doors they contain
- Check that structural elements are aligned as expected
- Identify pairs of elements that should be at specific angles for proper installation
- Detect coordination issues where elements are not oriented as expected relative to each other
