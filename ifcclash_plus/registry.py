# This file was generated with the assistance of an AI coding tool.
"""The rule registry: the catalogue of every rule, facet and select the
engine exposes to a client (BonsaiViewer or any JSON Lines consumer).

One entry per rule of Rules.py, with the exact parameter names understood
by serialization.deserialize_rule_check — the registry is the single source
of truth shared by the client UI (library sections, property editors, slot
placeholders) and the engine (run requests).

A param "kind" selects the client-side editor:
    float        QDoubleSpinBox
    int          QSpinBox
    bool         QCheckBox
    string       QLineEdit
    enum         combo box ("values")
    string_list  a stack of text lines
    direction    three floats (x, y, z)
A "complex": true text param may carry a restriction block instead of a
simple value (Enumeration / Pattern / Bounds / Length), the IDS form.
"""

from typing import Any
import inspect

CATALOGUE_VERSION = 1

FAMILIES = ("OneObjectRule", "TwoObjectRule", "ComplexRule", "IDS Facet")

# The selectable rule states, in UI order. Every rule supports them all.
STATES = ("Final", "Select", "Display_Input", "Display_Result")


def _p(name, kind, default, doc="", values=None, complex_=False, unit=""):
    param: dict[str, Any] = {
        "name": name,
        "kind": kind,
        "default": default,
        "doc": doc,
    }
    if values is not None:
        param["values"] = values
    if complex_:
        param["complex"] = True
    if unit:
        param["unit"] = unit
    return param


def _rule(type_, label, family, slots, doc, params):
    return {
        "type": type_,
        "label": label,
        "family": family,
        "doc": doc,
        "slots": slots,
        "params": params,
        "supports_states": list(STATES),
        "supports_exceptions": True,
        "supports_grouping": True,
        "supports_criticity": True,
        "supports_actor": True,
    }


WIDE_NARROW = ["Wide", "Narrow"]

RULES: list[dict[str, Any]] = [
    # ---- OneObjectRule -----------------------------------------------------
    _rule(
        "Volume",
        "Volume",
        "OneObjectRule",
        ["source"],
        "Flags every source whose volume is outside [volume_min, volume_max].",
        [
            _p("volume_min", "float", 0.0, "Minimum volume", unit="model"),
            _p("volume_max", "float", 100.0, "Maximum volume", unit="model"),
        ],
    ),
    _rule(
        "Area",
        "Area",
        "OneObjectRule",
        ["source"],
        "Flags every source whose area is outside [volume_min, volume_max].",
        [
            _p("volume_min", "float", 0.0, "Minimum area", unit="model"),
            _p("volume_max", "float", 100.0, "Maximum area", unit="model"),
        ],
    ),
    _rule(
        "TopOrBottomSurface",
        "Top Or Bottom Surface",
        "OneObjectRule",
        ["source"],
        "Flags a source whose top (or bottom) face area is outside the bounds.",
        [
            _p("surface_min", "float", 0.0, "Minimum surface", unit="model"),
            _p("surface_max", "float", 100.0, "Maximum surface", unit="model"),
            _p("top_or_bot_method", "enum", "Top", "Which extreme face", ["Top", "Bottom"]),
        ],
    ),
    _rule(
        "LateralSurface",
        "Lateral Surface",
        "OneObjectRule",
        ["source"],
        "Flags a source whose lateral surface is outside the bounds.",
        [
            _p("surface_min", "float", 0.0, "Minimum surface", unit="model"),
            _p("surface_max", "float", 100.0, "Maximum surface", unit="model"),
            _p("direction", "direction", [0.0, 0.0, 1.0], "Measurement direction"),
        ],
    ),
    _rule(
        "ProjectedSurface",
        "Projected Surface",
        "OneObjectRule",
        ["source"],
        "Flags a source whose projected surface is outside the bounds.",
        [
            _p("surface_min", "float", 0.0, "Minimum surface", unit="model"),
            _p("surface_max", "float", 100.0, "Maximum surface", unit="model"),
            _p("direction", "direction", [0.0, 0.0, 1.0], "Projection direction"),
        ],
    ),
    _rule(
        "ObbHigh",
        "Obb High",
        "OneObjectRule",
        ["source"],
        "Flags a source whose OBB height is outside [length_min, length_max].",
        [
            _p("length_min", "float", 0.0, "Minimum height", unit="model"),
            _p("length_max", "float", 100.0, "Maximum height", unit="model"),
        ],
    ),
    _rule(
        "ObbLength",
        "Obb Length",
        "OneObjectRule",
        ["source"],
        "Flags a source whose OBB length is outside [length_min, length_max].",
        [
            _p("length_min", "float", 0.0, "Minimum length", unit="model"),
            _p("length_max", "float", 100.0, "Maximum length", unit="model"),
            _p("direction_method", "enum", "Wide", "OBB axis choice", WIDE_NARROW),
        ],
    ),
    _rule(
        "Orientation",
        "Orientation",
        "OneObjectRule",
        ["source"],
        "Flags a source whose orientation deviates from the reference direction.",
        [
            _p("orientation", "direction", [0.0, 0.0, 1.0], "Reference direction"),
            _p("orientation_type", "enum", "Parrallel", "Relation to the direction", ["Parrallel", "Perpendicular"]),
            _p("direction_method", "enum", "Wide", "OBB axis choice", WIDE_NARROW),
            _p("angular_tolerance", "float", 0.1, "Angular tolerance", unit="deg"),
        ],
    ),
    _rule(
        "OneObjectFace",
        "One Object Face",
        "OneObjectRule",
        ["source"],
        "Face check of one element against itself (distance, intersection, orientation).",
        [
            _p("face_a_selection", "string", "", "First face selection (empty = all)"),
            _p("face_b_selection", "string", "", "Second face selection (empty = all)"),
            _p("distance", "bool", False, "Measure the distance"),
            _p("min_distance", "float", None, "Minimum distance", unit="model"),
            _p("max_distance", "float", None, "Maximum distance", unit="model"),
            _p("skip_adjacent", "bool", True, "Skip adjacent faces"),
            _p("intersection", "bool", False, "Check the intersection"),
            _p("intersection_tolerance", "float", None, "Intersection tolerance", unit="model"),
            _p("orientation", "bool", False, "Check the orientation"),
            _p("angle", "float", None, "Angle", unit="deg"),
            _p("angle_tolerance", "float", None, "Angle tolerance", unit="deg"),
        ],
    ),
    # ---- TwoObjectRule -----------------------------------------------------
    _rule(
        "AngleBetween",
        "Angle Between",
        "TwoObjectRule",
        ["source", "target"],
        "Flags the pairs whose angle between the source and target axes deviates.",
        [
            _p("direction_method_for_source", "enum", "Wide", "Source OBB axis", WIDE_NARROW),
            _p("direction_method_for_target", "enum", "Wide", "Target OBB axis", WIDE_NARROW),
            _p("angle_difference", "float", 0.0, "Expected angle difference", unit="deg"),
            _p("angle_tolerance", "float", 0.0, "Angle tolerance", unit="deg"),
        ],
    ),
    _rule(
        "Intersection",
        "Intersection",
        "TwoObjectRule",
        ["source", "target"],
        "Flags the pairs whose shapes intersect within the tolerance.",
        [
            _p("tolerance", "float", 0.1, "Intersection tolerance", unit="model"),
        ],
    ),
    _rule(
        "Clearance",
        "Clearance",
        "TwoObjectRule",
        ["source", "target"],
        "Flags the pairs closer than the clearance.",
        [
            _p("clearance", "float", 0.05, "Minimum required clearance", unit="model"),
            _p("check_all", "bool", False, "Check all the pairs, not only the closest"),
        ],
    ),
    _rule(
        "ClearanceAxisToAxis",
        "Clearance Axis To Axis",
        "TwoObjectRule",
        ["source", "target"],
        "Flags the pairs of linear elements whose axis-to-axis distance is outside the bounds.",
        [
            _p("mode", "enum", "Perpendicular", "Distance mode", ["Perpendicular", "MinDistance"]),
            _p("min_distance", "float", None, "Minimum distance", unit="model"),
            _p("max_distance", "float", None, "Maximum distance", unit="model"),
            _p("tolerance", "float", 0.0, "Distance tolerance", unit="model"),
            _p("linearity_ratio", "float", 10.0, "Linearity ratio"),
            _p("on_non_linear", "enum", "Skip", "Non linear elements", ["Skip", "Fallback"]),
            _p("parallel_tolerance", "float", 1.0, "Parallelism tolerance", unit="deg"),
        ],
    ),
    _rule(
        "Collision",
        "Collision",
        "TwoObjectRule",
        ["source", "target"],
        "Flags the pairs of colliding shapes; touching may be allowed.",
        [
            _p("allow_touching", "bool", False, "Allow face contact"),
        ],
    ),
    _rule(
        "Above",
        "Above",
        "TwoObjectRule",
        ["source", "target"],
        "Flags the pairs whose source is not above the target, per the bounding method.",
        [
            _p(
                "above_type",
                "enum",
                "Above_MaxToMax",
                "Bounding method",
                ["Above_MinToMax", "Above_MinToMin", "Above_MaxToMin", "Above_MaxToMax"],
            ),
            _p("tolerance", "float", 0.1, "Tolerance", unit="model"),
        ],
    ),
    _rule(
        "Below",
        "Below",
        "TwoObjectRule",
        ["source", "target"],
        "Flags the pairs whose source is not below the target, per the bounding method.",
        [
            _p(
                "below_type",
                "enum",
                "Below_MaxToMax",
                "Bounding method",
                ["Below_MinToMax", "Below_MinToMin", "Below_MaxToMin", "Below_MaxToMax"],
            ),
            _p("tolerance", "float", 0.1, "Tolerance", unit="model"),
        ],
    ),
    _rule(
        "OBB_Above",
        "OBB Above",
        "TwoObjectRule",
        ["source", "target"],
        "Flags a target penetrating the detection band extruded above the source OBB.",
        [
            _p("tolerance", "float", 1.0, "Height of the detection band above the source", unit="model"),
        ],
    ),
    _rule(
        "OBB_Below",
        "OBB Below",
        "TwoObjectRule",
        ["source", "target"],
        "Flags a target penetrating the detection band extruded below the source OBB.",
        [
            _p("tolerance", "float", 1.0, "Height of the detection band below the source", unit="model"),
        ],
    ),
    _rule(
        "OBB_Front_And_Back",
        "OBB Front And Back",
        "TwoObjectRule",
        ["source", "target"],
        "Flags a target penetrating the detection bands in front of and behind the source.",
        [
            _p("tolerance", "float", 0.1, "Depth of the detection bands", unit="model"),
            _p("direction_method", "enum", "Wide", "Front direction", WIDE_NARROW),
        ],
    ),
    _rule(
        "OBB_Custom",
        "OBB Custom",
        "TwoObjectRule",
        ["source", "target"],
        "Flags a target penetrating custom detection zones around the source.",
        [
            _p(
                "list_of_modifications",
                "string_list",
                [],
                "Zone modifications, one per line (ex. 'top 0.5', 'bottom 0.2')",
            ),
        ],
    ),
    _rule(
        "SurfaceRecover",
        "Surface Recover",
        "TwoObjectRule",
        ["source", "target"],
        "Checks that the target surface is covered by the source (ex. a coating).",
        [
            _p("direction", "enum", "Auto", "Recovery direction", ["Auto", "Top", "Bottom"]),
            _p("reference", "enum", "Source", "Reference surface", ["Source", "Target"]),
            _p("tolerance", "float", 0.001, "Tolerance", unit="model"),
            _p(
                "min_covering",
                "string",
                None,
                "Minimum covering: an area (ex. 1.5) or a percentage (ex. '50%')",
            ),
            _p(
                "max_covering",
                "string",
                None,
                "Maximum covering: an area (ex. 1.5) or a percentage (ex. '50%')",
            ),
        ],
    ),
    _rule(
        "TwoObjectsFace",
        "Two Objects Face",
        "TwoObjectRule",
        ["source", "target"],
        "Face check of the source faces against the target faces.",
        [
            _p("source_face_selection", "string", "", "Source face selection (empty = all)"),
            _p("target_face_selection", "string", "", "Target face selection (empty = all)"),
            _p("distance", "bool", False, "Measure the distance"),
            _p("min_distance", "float", None, "Minimum distance", unit="model"),
            _p("max_distance", "float", None, "Maximum distance", unit="model"),
            _p("intersection", "bool", False, "Check the intersection"),
            _p("intersection_tolerance", "float", None, "Intersection tolerance", unit="model"),
            _p("orientation", "bool", False, "Check the orientation"),
            _p("angle", "float", None, "Angle", unit="deg"),
            _p("angle_tolerance", "float", None, "Angle tolerance", unit="deg"),
        ],
    ),
    _rule(
        "ClearanceForDoors",
        "Clearance For Doors",
        "TwoObjectRule",
        ["source", "target"],
        "Checks that the door swing clearance zone is free of target obstacles.",
        [
            _p("zone_shape", "enum", "Arc", "Zone shape", ["Arc", "Rectangle"]),
            _p("sides", "enum", "Swing", "Which side(s)", ["Swing", "Both", "Front", "Back"]),
            _p("leaves", "int", None, "Number of door leaves (empty = auto)"),
            _p("width", "float", None, "Zone width (empty = door width)", unit="model"),
            _p("depth", "float", None, "Zone depth (empty = door width)", unit="model"),
            _p("height", "float", None, "Zone height (empty = door height)", unit="model"),
            _p("tolerance", "float", 0.001, "Tolerance", unit="model"),
        ],
    ),
    # ---- ComplexRule -------------------------------------------------------
    _rule(
        "Alignement",
        "Alignement",
        "ComplexRule",
        ["source"],
        "Flags the groups of sources aligned on a common axis or plane.",
        [
            _p("axis", "enum", "", "Axis (empty = auto)", ["", "Vertical", "Horizontal"]),
            _p("alignment_type", "enum", "Plane", "Alignment type", ["Line", "Plane"]),
            _p("tolerance", "float", None, "Tolerance (empty = auto)", unit="model"),
            _p("min_group", "int", 3, "Minimum group size"),
        ],
    ),
    _rule(
        "Ray_Check",
        "Ray Check",
        "ComplexRule",
        ["source", "target", "context"],
        "Casts rays from the sources to the context obstacles.",
        [
            _p("max_ray_length", "float", 1.0, "Maximum ray length", unit="model"),
        ],
    ),
    _rule(
        "DirectView",
        "Direct View",
        "ComplexRule",
        ["source", "target", "context"],
        "Flags the source/target pairs without a direct line of sight through the context.",
        [
            _p("ray_source", "enum", "Source", "Where the rays start", ["Source", "Target", "Both"]),
            _p("ray_count", "int", 10, "Number of rays per pair"),
            _p("threshold", "float", 100.0, "Visibility threshold", unit="%"),
            _p("max_distance", "float", None, "Maximum distance (empty = none)", unit="model"),
        ],
    ),
    _rule(
        "FreeSpace",
        "Free Space",
        "ComplexRule",
        ["source", "context"],
        "Checks that a free cylinder (ex. evacuation) fits around each source.",
        [
            _p("diameter", "float", 1.5, "Free space diameter", unit="model"),
            _p("height", "float", 2.0, "Free space height", unit="model"),
        ],
    ),
]

CARDINALITIES = ["required", "optional", "prohibited"]

FACETS: list[dict[str, Any]] = [
    {
        "type": "Entity",
        "label": "Entity Facet",
        "family": "IDS Facet",
        "doc": "Selects the elements by IFC class and predefined type.",
        "slots": [],
        "params": [
            _p("name", "string", "IFCWALL", "IFC class name", complex_=True),
            _p("predefinedType", "string", "", "Predefined type", complex_=True),
            _p("instructions", "string", "", "Instructions"),
        ],
    },
    {
        "type": "Attribute",
        "label": "Attribute Facet",
        "family": "IDS Facet",
        "doc": "Filters the elements by an attribute value.",
        "slots": [],
        "params": [
            _p("name", "string", "Name", "Attribute name", complex_=True),
            _p("value", "string", "", "Attribute value", complex_=True),
            _p("cardinality", "enum", "required", "Cardinality", CARDINALITIES),
            _p("instructions", "string", "", "Instructions"),
        ],
    },
    {
        "type": "Property",
        "label": "Property Facet",
        "family": "IDS Facet",
        "doc": "Filters the elements by a property value.",
        "slots": [],
        "params": [
            _p("propertySet", "string", "Property_Set", "Property set", complex_=True),
            _p("baseName", "string", "PropertyName", "Property name", complex_=True),
            _p("value", "string", "", "Property value", complex_=True),
            _p("dataType", "string", "", "Data type"),
            _p("cardinality", "enum", "required", "Cardinality", CARDINALITIES),
            _p("instructions", "string", "", "Instructions"),
        ],
    },
    {
        "type": "Classification",
        "label": "Classification Facet",
        "family": "IDS Facet",
        "doc": "Filters the elements by classification reference.",
        "slots": [],
        "params": [
            _p("value", "string", "", "Classification value", complex_=True),
            _p("system", "string", "", "Classification system", complex_=True),
            _p("cardinality", "enum", "required", "Cardinality", CARDINALITIES),
            _p("instructions", "string", "", "Instructions"),
        ],
    },
    {
        "type": "Material",
        "label": "Material Facet",
        "family": "IDS Facet",
        "doc": "Filters the elements by material.",
        "slots": [],
        "params": [
            _p("value", "string", "", "Material value", complex_=True),
            _p("cardinality", "enum", "required", "Cardinality", CARDINALITIES),
            _p("instructions", "string", "", "Instructions"),
        ],
    },
    {
        "type": "PartOf",
        "label": "PartOf Facet",
        "family": "IDS Facet",
        "doc": "Filters the elements by a relationship to another element.",
        "slots": [],
        "params": [
            _p("name", "string", "IFCWALL", "Related element class", complex_=True),
            _p("predefinedType", "string", "", "Related predefined type", complex_=True),
            _p("relation", "string", "", "Relation", complex_=True),
            _p("cardinality", "enum", "required", "Cardinality", CARDINALITIES),
            _p("instructions", "string", "", "Instructions"),
        ],
    },
]


def catalogue() -> dict[str, Any]:
    """The full catalogue, as sent on the IPC 'catalogue' request."""
    return {
        "catalogue_version": CATALOGUE_VERSION,
        "families": list(FAMILIES),
        "states": list(STATES),
        "rules": RULES,
        "facets": FACETS,
    }


def find_rule(rule_type: str) -> dict[str, Any]:
    for rule in RULES:
        if rule["type"] == rule_type:
            return rule
    raise KeyError(f"Unknown rule type: {rule_type}")


def find_facet(facet_type: str) -> dict[str, Any]:
    for facet in FACETS:
        if facet["type"] == facet_type:
            return facet
    raise KeyError(f"Unknown facet type: {facet_type}")


# ---- The dispatch of a serialized rule declaration to its compute
# (SPEC Separation moteur/gestion).
#
# The JSON declaration of a rule stays FLAT and gathers everything
# under one same rule (arbitration of the SPEC): the selects, the
# engine parameters and the management configuration sit at the same
# level of the dictionary produced by serialize_rule_check. The
# engine/gestion separation lives in the code only: this dispatch
# reads the engine part of the flat declaration and calls compute
# with it, the ResultPipeline reads the management part, the
# orchestrator reads the selects.


def engine_params(rule_type: str) -> list[str]:
    """The engine parameters of a rule, as declared by the catalogue:
    the flat keys of the serialized rule declaration that feed the
    named compute() call of the rule.

    The params of a catalogue entry are the engine parameters of the
    rule, in the signature order of its compute.
    """
    return [param["name"] for param in find_rule(rule_type)["params"]]


def compute_from_config(
    config: dict[str, Any],
    liste_objet_source: list,
    liste_objet_target: list = None,
    liste_objet_contexte: list = None,
) -> list:
    """The dispatch of one serialized rule declaration to its compute.

    The flat declaration (serialize_rule_check, the canonical JSON
    format) is rebuilt into its executable rule, then its engine
    parameters — the ones the catalogue declares — are extracted and
    passed to compute() as the named arguments of the rule. The
    selects, the exceptions, criticity, actor, grouping and Must
    configuration of the same declaration are NOT consumed here:
    they belong to the orchestrator and to the ResultPipeline.

    Only the migrated rules expose a compute: dispatching a rule
    type still waiting for its migration raises NotImplementedError.
    """
    # A local import: the registry stays import-light (the IPC loads
    # it for the catalogue), the serialization pulls the rules.
    from serialization import deserialize_rule_check

    rule_type = config["type"]
    rule = deserialize_rule_check(config)

    if not hasattr(rule, "compute"):
        raise NotImplementedError(
            f"the rule type '{rule_type}' has no compute yet "
            "(SPEC Separation moteur/gestion: migration pending)"
        )

    # The call is driven by the signature of the compute: a
    # one-object rule takes no liste_objet_target, a complex rule
    # takes the liste_objet_contexte of its contract (SPEC).
    parameters = inspect.signature(rule.compute).parameters
    call = {
        name: config[name]
        for name in engine_params(rule_type)
        if name in config
    }
    call["liste_objet_source"] = liste_objet_source
    if "liste_objet_target" in parameters:
        call["liste_objet_target"] = liste_objet_target
    if "liste_objet_contexte" in parameters:
        call["liste_objet_contexte"] = liste_objet_contexte
    return rule.compute(**call)
