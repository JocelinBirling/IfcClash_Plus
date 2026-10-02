# Description

This rule aims to detect objects that are below each other.

It will first detect, on each object, the face that will be analyzed. The lateral tolerance may be used to consider more faces than the one directly below.
- All faces must point to the top, or bottom.
- The faces must be the highest, or lowest, point of the geometry.

Then it will check the distance between all the faces.

The rule will detect the two faces of the object. Those two faces will be analyzed in order to detect if they are in or out.

# Property
A: Object A

B: Object B

Type: 
- MinToMax: The lower part of A will be collided with the highest part of B.
- MinToMin: The lower part of A will be collided with the lowest part of B.
- MaxToMin: The highest part of A will be collided with the lowest part of B.
- MaxToMax: The highest part of A will be collided with the highest part of B.

Min: If the faces of object B is lower than Min, it will raise a clash.

Max: If the faces of object B is higher than Max, it will raise a clash.

Lateral_Tolerance: 
By default 0, the lateral tolerance aims to detect that the B object may be offset.
If the value is negative, it can enforce that the B object is under A object.

# Result

For now, the result will say if B is below A and give the minimum distance between the two objects.

# Example
It can be used to detect if an electric machine is right below a pipe.
