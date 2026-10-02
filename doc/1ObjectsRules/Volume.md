# Description

This rule aims to detect objects based on their volume.

It will calculate the volume of each selected object and check if it falls within the specified minimum and maximum range.

# Property
Source: The objects to be analyzed.

Min: The minimum volume threshold. Objects with a volume greater than this value will be considered.

Max: The maximum volume threshold. Objects with a volume less than this value will be considered.

# Result

The result will list all objects whose volume is between the Min and Max values.

# Example

It can be used to detect specific objects based on their size, such as filtering elements by their volume.
