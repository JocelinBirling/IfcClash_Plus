# Description

This rule aims to detect objects based on their surface area in a specific lateral direction.

It will identify the faces of each selected object that are oriented within 45 degrees of the specified direction vector. These faces are then measured to calculate their combined surface area. This allows for detecting objects based on the area of their faces facing a particular sideways direction.

# Property

Source: The objects to be analyzed.

Min: The minimum surface area threshold. Objects with a lateral surface area greater than this value will be considered.

Max: The maximum surface area threshold. Objects with a lateral surface area less than this value will be considered.

Direction: A direction vector (X, Y, Z) specifying which lateral direction to measure surface area against. The rule will calculate the area of all faces oriented within 45 degrees of this direction.

# Result

The result will list all objects whose lateral surface area in the specified direction is between the Min and Max values.

# Example

It can be used to detect objects with specific lateral surface characteristics, such as:
- Filtering elements by their side surface area facing a particular direction
- Identifying walls or other vertical elements based on their facade area
- Detecting objects with significant surface area oriented toward a specific compass direction
