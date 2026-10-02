# Description

This rule aims to detect objects based on their top or bottom surface area.

It will identify the faces of each selected object that are at the **extreme position** (topmost or bottommost) in the specified direction. This is determined using `clash_utils.get_extreme_faces()`, which ensures only the faces at the highest (for Top) or lowest (for Bottom) position are considered. This approach **avoids detecting holes or interior features** that may have the correct orientation but are not at the extreme position.

- For **Top**: Faces at the **topmost position** (highest Z coordinate) with upward orientation
- For **Bottom**: Faces at the **bottommost position** (lowest Z coordinate) with downward orientation

The rule uses direction vectors: (0,0,1) for Top and (0,0,-1) for Bottom.

# Property
Source: The objects to be analyzed.

Min: The minimum surface area threshold. Objects with a top/bottom surface area greater than this value will be considered.

Max: The maximum surface area threshold. Objects with a top/bottom surface area less than this value will be considered.

Top or Bottom: The direction to check. "Top" checks the faces at the topmost position, while "Bottom" checks the faces at the bottommost position.

# Result

The result will list all objects whose top or bottom surface area (depending on the selected direction) is between the Min and Max values.

# Example

It can be used to detect objects with specific top or bottom surface characteristics. For instance:
- Find all columns with a top surface area between 0.5 and 1.0 square meters
- Identify beams with a bottom surface area greater than 0.3 square meters (excluding holes)
- Filter slabs based on their bottom surface area for structural analysis
