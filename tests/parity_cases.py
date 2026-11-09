"""The parity cases shared by the reference generator
(scripts/make_parity_golden.py, Python engine, run once) and the parity
test (tests/test_parity_cpp.py, C++ engine only).

A case: (rule type, kind, Python rule factory, engine parameters). The kind
picks the selections:
    one       sources = every product
    one_ctx   sources = every product, context = every product
    pair      "disjoint" (even / odd products) and "overlapping" (all / all)
    pair_ctx  sources = even products, targets = odd products, context = all
"""
import glob
import hashlib
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "ifcclash_plus"))

from Rules import (  # noqa: E402
    OBB_Above,
    OBB_Below,
    OBB_Custom,
    OBB_Front_And_Back,
    Above,
    Alignement,
    AngleBetween,
    Area,
    Below,
    Clearance,
    ClearanceAxisToAxis,
    ClearanceForDoors,
    Collision,
    DirectView,
    FreeSpace,
    Intersection,
    Intersection2,
    LateralSurface,
    ObbHigh,
    ObbLength,
    OneObjectFace,
    Orientation,
    ProjectedSurface,
    Ray_Check,
    SurfaceRecover,
    TopOrBottomSurface,
    TwoObjectsFace,
    Volume,
)

GOLDEN_DIR = os.path.join(ROOT, "tests", "parity_golden")
TREE_RULES = ("Intersection", "Clearance", "Collision")

_CALIBRATED = sorted(glob.glob(os.path.join(ROOT, "IFC_Test_Model", "IFC_Model", "*.ifc")))
# Every calibrated model holds the same reference objects in another layout:
# three of them cover the cases; IFCCLASH_PARITY_FULL=1 takes them all.
MODELS = _CALIBRATED if os.environ.get("IFCCLASH_PARITY_FULL") else _CALIBRATED[:: max(1, len(_CALIBRATED) // 3)][:3]
MODELS = [os.path.relpath(m, ROOT) for m in MODELS]

_FACE_OFF = dict(distance=False, min_distance=None, max_distance=None, intersection=False,
                 intersection_tolerance=0.0, orientation=False, angle=None, angle_tolerance=0.0)

CASES = [
    ("Volume", "one", lambda: Volume(None, 0.0, 1e9), {"volume_min": 0.0, "volume_max": 1e9}),
    ("Area", "one", lambda: Area(None, 0.0, 1e9), {"volume_min": 0.0, "volume_max": 1e9}),
    ("TopOrBottomSurface", "one", lambda: TopOrBottomSurface(None, 0.0, 1e9, "Top"),
     {"surface_min": 0.0, "surface_max": 1e9, "top_or_bot_method": "Top"}),
    ("TopOrBottomSurface", "one", lambda: TopOrBottomSurface(None, 0.0, 1e9, "Bottom"),
     {"surface_min": 0.0, "surface_max": 1e9, "top_or_bot_method": "Bottom"}),
    ("LateralSurface", "one", lambda: LateralSurface(None, 0.0, 1e9, (0.0, 1.0, 0.0)),
     {"surface_min": 0.0, "surface_max": 1e9, "direction": [0.0, 1.0, 0.0]}),
    ("ProjectedSurface", "one", lambda: ProjectedSurface(None, 0.0, 1e9, (0.0, 0.0, 1.0)),
     {"surface_min": 0.0, "surface_max": 1e9, "direction": [0.0, 0.0, 1.0]}),
    ("ObbHigh", "one", lambda: ObbHigh(None, 0.0, 1e9), {"length_min": 0.0, "length_max": 1e9}),
    ("ObbLength", "one", lambda: ObbLength(None, 0.0, 1e9, "Narrow"),
     {"length_min": 0.0, "length_max": 1e9, "direction_method": "Narrow"}),
    ("Orientation", "one", lambda: Orientation(None, (0.0, 0.0, 1.0), "Parrallel", "Wide", 0.1),
     {"orientation": [0.0, 0.0, 1.0], "orientation_type": "Parrallel", "direction_method": "Wide",
      "angular_tolerance": 0.1}),
    ("OneObjectFace", "one", lambda: OneObjectFace(None, {"orientation": "Top", "extreme_faces": True},
                                                   {"orientation": "Bottom", "extreme_faces": True},
                                                   orientation=True, angle=180.0, angle_tolerance=1.0),
     dict(_FACE_OFF, face_a_selection={"orientation": "Top", "extreme_faces": True},
          face_b_selection={"orientation": "Bottom", "extreme_faces": True}, skip_adjacent=True,
          orientation=True, angle=180.0, angle_tolerance=1.0)),
    ("OneObjectFace", "one", lambda: OneObjectFace(None, {"orientation": "Top", "extreme_faces": True},
                                                   {"orientation": "Bottom", "extreme_faces": True},
                                                   distance=True, min_distance=0.5, intersection=True),
     dict(_FACE_OFF, face_a_selection={"orientation": "Top", "extreme_faces": True},
          face_b_selection={"orientation": "Bottom", "extreme_faces": True}, skip_adjacent=True,
          distance=True, min_distance=0.5, intersection=True)),
    ("Intersection", "pair", lambda: Intersection(None, None), {"tolerance": 0.002}),
    ("Clearance", "pair", lambda: Clearance(None, None), {"clearance": 0.5, "check_all": True}),
    ("Collision", "pair", lambda: Collision(None, None), {"allow_touching": False}),
    ("Intersection2", "pair", lambda: Intersection2(None, None, 0.0), {"tolerance": 0.0}),
    ("Above", "pair", lambda: Above(None, None, "Above_MaxToMin", 1.0), {"above_type": "Above_MaxToMin", "tolerance": 1.0}),
    ("Below", "pair", lambda: Below(None, None, "Below_MinToMax", 1.0), {"below_type": "Below_MinToMax", "tolerance": 1.0}),
    ("OBB_Above", "pair", lambda: OBB_Above(None, None, 1.0), {"tolerance": 1.0}),
    ("OBB_Below", "pair", lambda: OBB_Below(None, None, 1.0), {"tolerance": 1.0}),
    ("OBB_Front_And_Back", "pair", lambda: OBB_Front_And_Back(None, None, 0.5, "Wide"),
     {"tolerance": 0.5, "direction_method": "Wide"}),
    ("OBB_Custom", "pair", lambda: OBB_Custom(None, None, ["detach_top_by_extrude:0.5", "NEW_OBB", "extend_down:50%"]),
     {"list_of_modifications": ["detach_top_by_extrude:0.5", "NEW_OBB", "extend_down:50%"]}),
    ("AngleBetween", "pair", lambda: AngleBetween(None, None, "Wide", "Wide", 90.0, 5.0),
     {"direction_method_for_source": "Wide", "direction_method_for_target": "Wide",
      "angle_difference": 90.0, "angle_tolerance": 5.0}),
    ("ClearanceAxisToAxis", "pair",
     lambda: ClearanceAxisToAxis(None, None, "MinDistance", 0.2, 5.0, 0.01, 1.5, "Fallback", 5.0),
     {"mode": "MinDistance", "min_distance": 0.2, "max_distance": 5.0, "tolerance": 0.01,
      "linearity_ratio": 1.5, "on_non_linear": "Fallback", "parallel_tolerance": 5.0}),
    # Perpendicular with its facing test, search radius (and its box test
    # on the Fallback pairs), unordered pairs: min_distance 100 m reports
    # every pair the rule keeps, so the reference pins that set (20 m:
    # about 20 of 190 pairs, Perpendicular, MinDistance and Fallback).
    ("ClearanceAxisToAxis", "pair",
     lambda: ClearanceAxisToAxis(None, None, "Perpendicular", 100.0, None, 0.0, 1.5, "Fallback", 2.0,
                                 search_radius=20.0),
     {"mode": "Perpendicular", "min_distance": 100.0, "max_distance": None, "tolerance": 0.0,
      "linearity_ratio": 1.5, "on_non_linear": "Fallback", "parallel_tolerance": 2.0, "search_radius": 20.0}),
    ("TwoObjectsFace", "pair", lambda: TwoObjectsFace(None, None, {"orientation": "Top", "extreme_faces": True},
                                                      {"orientation": "Bottom"}, distance=True, min_distance=0.3,
                                                      intersection=True),
     dict(_FACE_OFF, source_face_selection={"orientation": "Top", "extreme_faces": True},
          target_face_selection={"orientation": "Bottom"}, distance=True, min_distance=0.3, intersection=True)),
    ("SurfaceRecover", "pair", lambda: SurfaceRecover(None, None, "Auto", "Source", 0.001, None, "80%"),
     {"direction": "Auto", "reference": "Source", "tolerance": 0.001, "min_covering": None,
      "max_covering": ["relative", 80.0]}),
    ("ClearanceForDoors", "pair", lambda: ClearanceForDoors(None, None),
     {"zone_shape": "Arc", "sides": "Swing", "leaves": None, "width": None, "depth": None, "height": None,
      "tolerance": 0.001}),
    ("Ray_Check", "pair_ctx", lambda: Ray_Check(None, None, None, 5.0), {"max_ray_length": 5.0}),
    ("DirectView", "pair_ctx", lambda: DirectView(None, None, None, "Source", 10, "50%", None),
     {"ray_source": "Source", "ray_count": 10, "threshold": 50.0, "max_distance": None}),
    ("FreeSpace", "one_ctx", lambda: FreeSpace(None, None, 1.0, 2.0), {"diameter": 1.0, "height": 2.0}),
    ("Alignement", "one", lambda: Alignement(None, None, "Plane", 0.05, 3),
     {"axis": None, "alignment_type": "Plane", "tolerance": 0.05, "min_group": 3}),
]


def case_id(case):
    rule_type, _, _, params = case
    digest = hashlib.md5(json.dumps(params, sort_keys=True).encode()).hexdigest()[:8]
    return f"{rule_type}-{digest}"


def products(ifc_file):
    found = [p for p in ifc_file.by_type("IfcProduct") if p.Representation is not None]
    return sorted(found, key=lambda p: p.id())


def selections(ifc_file, kind):
    """(mode, sources, targets, context) of a case kind."""
    all_ = products(ifc_file)
    if kind == "one":
        yield "all", all_, None, None
    elif kind == "one_ctx":
        yield "all", all_, None, all_
    elif kind == "pair":
        yield "disjoint", all_[0::2], all_[1::2], None
        yield "overlapping", all_, all_, None
    elif kind == "pair_ctx":
        yield "disjoint", all_[0::2], all_[1::2], all_
