
The idea would be to combine those possibility in order to create a bunch a new rule.




# Relative Position
## Above
## Below
## NextTo
## InFront

### Alignated by faces
    The objects must have parrallels face

### Alignated by edges
    The objects edges must not move outside the object side.
    May be, it could be done in 2D by projecting the faces with the face normals.


# Recover Precision

## Recover

The Object A fully recover the Object B.

## Overlaps

The object A recover partially the object B.
Some are inside, some are outside.

## Outside 
The object A does not cover at all object B.



# Object Position (Absolut or Relative)

## Top
## Center
## Bottom
## Sides

# OOBB
For the bouding box, we can define prefined word. 

OBB Z should be always pointing to up.
It depends of the use case. 
For a beam, or a wall, it's fine.
For a rafter, it's a flaw. The tilt of the object need to be taken in account to calculte his length.

## Sides Face
For the side faces, we can define. We will always look at the face by the normals. The right and left will be dependant on the normals direction.
Top and bottom is obvious.

## Top and Bottom Face
This selection is more complexe because we need to determine the front and the back.
Front
Back
Left : Determine by the Front
Right : Determine by the Front

If the parameters are equals, it doesn't matter to know the front.






