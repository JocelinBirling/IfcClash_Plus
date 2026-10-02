# Description

This rule aims to detect objects based on their orientation relative to a specified direction vector.

It calculates the oriented bounding box (OBB) for each selected object and extracts its main directions. These directions are then compared against the target orientation vector to check if objects are aligned as specified (parallel or perpendicular). This allows for filtering elements based on their spatial orientation in the model.

# Property

Source: The objects to be analyzed.

Orientation: A direction vector (X, Y, Z) representing the target orientation to check against. For example, (0, 1, 0) represents North, (1, 0, 0) represents East, (0, 0, 1) represents upward.

Orientation Type: The relationship to check between the object's orientation and the target direction:
- **Parallel**: Objects whose main direction is parallel to the target orientation
- **Perpendicular**: Objects whose main direction is perpendicular to the target orientation

Direction Method: The method used to determine the object's main directions from its oriented bounding box:
- **Wide**: Uses the two widest dimensions of the OBB to determine main directions
- **Narrow**: Uses the longest dimension and its perpendicular to determine main directions

# Result

The result will list all objects whose main direction matches the specified orientation relationship (parallel or perpendicular) with the target direction vector.

# Example

This could be used to check if a window is facing North (or South). Additional use cases include:
- Verify that all windows face a specific cardinal direction for energy analysis
- Identify structural elements oriented in a particular direction
- Filter MEP components based on their alignment in the building
