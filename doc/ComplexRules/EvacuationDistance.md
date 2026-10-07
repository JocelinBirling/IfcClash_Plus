# Description

This rule checks that the evacuation distance from a space to the nearest exit stays below a maximum value.

Usage : vérifier la distance d'évacuation réglementaire d'un local vers une sortie de sécurité (ou une porte d'escalier, prise comme arrivée), sur un seul étage.

Scope: the path stays on one storey. Stairs are never traversed: a stair door is an exit like any other, the path stops there.

## Algorithm

1. Build the traversable domain on the storey: the spaces of `Spaces`, connected only through the doors of `Doors`. The walls of `Walls` and the slabs of `Slabs` block the path; everything else is ignored.
2. For each starting space of `Starting_Space`, find the worst point: the point of the space whose path to the nearest exit is the longest. The distance of the space is measured from this point.
3. On the horizontal slice at `Height` above the space floor, search the path from the worst point to the nearest exit of `Exit_Doors`. The path is a broken line within the slice: it is not a straight ray, it bends to bypass the obstacles. The engine tries the path with 1 bend, then 2, then 3, then 4 bends, and stops at the first success. The path avoids `Walls` and `Slabs`, only crosses `Doors`, and ends at an exit door. The distance is the length of the broken line.
4. Raise a clash for each starting space whose distance is above `Max_Distance`.
5. If no path exists from a space to any exit (all blocked, or all paths need more than 4 bends), raise a specific clash: a blocked evacuation is worse than an excessive distance.

# Property

Starting_Space: the spaces from which the evacuation is measured, one or several (most of the time an IfcSpace).

Spaces: the spaces forming the traversable domain of the storey.

Doors: the only passages between the spaces. Outside a door, the walls close the path.

Walls / Slabs: the obstacles blocking the path. Everything outside the declared sets is ignored.

Exit_Doors: the exits of the storey: safety exits and stair doors, taken as arrival points.

Height: the height of the horizontal slice on which the path is computed, in meter (type: float, default: 1.0, shoulder height of an evacuee).

Max_Distance: the maximum evacuation distance, in meter (type: float, mandatory). A space whose distance is above Max_Distance raises a clash.

## Template

```
{
    "Starting_Space": [],
    "Spaces": [],
    "Doors": [],
    "Walls": [],
    "Slabs": [],
    "Exit_Doors": [],
    "height": 1.0,
    "max_distance": null
}
```

# Result

For each starting space:
- distance: the retained distance, from the worst point of the space to the nearest exit, and the margin against `Max_Distance` (useful for severity).
- path: the broken line (segments and bend points) and the doors crossed, in order, to explain and visualize the trajectory.

For each starting space with no path: the specific no-path clash, with the explored dead ends.

# Example

The regulatory evacuation distance must not exceed 40 m: Starting_Space = all IfcSpace of the storey, Spaces = the same spaces, Doors = all IfcDoor of the storey, Walls = IfcWall, Slabs = IfcSlab, Exit_Doors = the exit doors and the stair doors, Max_Distance = 40.

A single meeting room must be checked: Starting_Space = [meeting room], the other sets covering the whole storey, Max_Distance = 30.
