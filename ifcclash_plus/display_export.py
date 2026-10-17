# This file was generated with the assistance of an AI coding tool.
"""Export of the engine's display registry (RuleCheck.display_items) to
JSON drawing items for the IPC protocol.

The DisplayItem shapes are OCC objects in the engine; the client renders
them with its own overlay pipelines. Three forms are exported:

- the lightweight representations produced by RuleCheck._item_shape:
  ("edge", start, end), ("face", corners), ("axis", center, direction,
  length);
- a Bnd_OBB / Custom_OBB (the detection zones and the object OBBs):
  center, orthonormal axes, half sizes, label — the client rebuilds the
  box wireframe from these;
- any other TopoDS_Shape: the edges are discretized into line segments.
"""

from typing import Any

from OCC.Core.Bnd import Bnd_OBB
from OCC.Core.BRepAdaptor import BRepAdaptor_Curve
from OCC.Core.GCPnts import GCPnts_QuasiUniformDeflection
from OCC.Core.TopAbs import TopAbs_EDGE
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopoDS import TopoDS_Shape

from result_export import element_ref

# Edge discretization of a TopoDS shape, in model units.
EDGE_DEFLECTION = 0.05


def _xyz(point) -> list[float]:
    if isinstance(point, (list, tuple)):
        return [float(point[0]), float(point[1]), float(point[2])]
    return [point.X(), point.Y(), point.Z()]


def _obb_to_json(obb: Bnd_OBB) -> dict[str, Any]:
    center = obb.Center()
    data = {
        "kind": "obb",
        "center": [center.X(), center.Y(), center.Z()],
        "axes": [
            [obb.XDirection().X(), obb.XDirection().Y(), obb.XDirection().Z()],
            [obb.YDirection().X(), obb.YDirection().Y(), obb.YDirection().Z()],
            [obb.ZDirection().X(), obb.ZDirection().Y(), obb.ZDirection().Z()],
        ],
        "half_sizes": [obb.XHSize(), obb.YHSize(), obb.ZHSize()],
    }
    return data


def _shape_edges_to_segments(shape) -> list[list[list[float]]]:
    """The edges of a TopoDS shape, discretized into [start, end] segments."""
    segments: list[list[list[float]]] = []
    explorer = TopExp_Explorer(shape, TopAbs_EDGE)
    while explorer.More():
        curve = BRepAdaptor_Curve(explorer.Current())
        discretizer = GCPnts_QuasiUniformDeflection(curve, EDGE_DEFLECTION)
        if discretizer.IsDone() and discretizer.NbPoints() >= 2:
            previous = None
            for index in range(1, discretizer.NbPoints() + 1):
                current = discretizer.Value(index)
                if previous is not None:
                    segments.append([_xyz(previous), _xyz(current)])
                previous = current
        explorer.Next()
    return segments


def _shape_to_json(shape) -> dict[str, Any] | None:
    """One DisplayItem shape as a JSON drawing item, None when empty."""
    if shape is None:
        return None

    # The lightweight representations: ("edge", start, end),
    # ("face", corners), ("axis", center, direction, length).
    if isinstance(shape, (tuple, list)) and shape and isinstance(shape[0], str):
        kind = shape[0]
        if kind == "edge" and len(shape) == 3:
            return {"kind": "edge", "start": _xyz(shape[1]), "end": _xyz(shape[2])}
        if kind == "face" and len(shape) == 2:
            return {"kind": "face", "corners": [_xyz(corner) for corner in shape[1]]}
        if kind == "axis" and len(shape) == 4:
            return {
                "kind": "axis",
                "center": _xyz(shape[1]),
                "direction": _xyz(shape[2]),
                "length": float(shape[3]),
            }
        return None

    if isinstance(shape, Bnd_OBB):
        return _obb_to_json(shape)

    if isinstance(shape, TopoDS_Shape):
        segments = _shape_edges_to_segments(shape)
        if segments:
            return {"kind": "segments", "segments": segments}
        return None

    return None


def display_items_to_json(items, model_of_file) -> list[dict[str, Any]]:
    """The rule's display registry as a list of JSON drawing items."""
    exported: list[dict[str, Any]] = []
    for item in items or []:
        shape = _shape_to_json(getattr(item, "shape", None))
        if shape is None:
            continue
        entry: dict[str, Any] = {
            "category": item.category,
            "shape": shape,
            "color": [float(channel) for channel in (item.color or (1, 0, 0))],
            "transparency": float(getattr(item, "transparency", 0.6)),
        }
        element = getattr(item, "element", None)
        if element is not None:
            ref = element_ref(element, model_of_file)
            if ref is not None:
                entry["element"] = ref
        exported.append(entry)
    return exported
