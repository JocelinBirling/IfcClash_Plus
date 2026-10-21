"""
Serialization module for IfcClash_Plus

This module provides functions to save and load rule configurations to/from
JSON files. It handles the full round-trip of a RuleFile: rules, folders,
selects (SelectFacet and SelectRule), boolean rules (BooleanLeaf, AndRule,
OrRule, NotRule), exceptions, grouping, criticity, actor and absolute or
relative checking.

A rule referenced by a SelectRule or inside a boolean tree is serialized by
value (nested): it is rebuilt as a separate but identical copy when loading.
"""

import json
import os
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from RuleClass import RuleCheck, RuleFile, RuleFolder, Select, SelectFacet, SelectRule

from ifctester.facet import (
    Attribute,
    Classification,
    Entity,
    Facet,
    Material,
    PartOf,
    Property,
    Restriction,
)


def _serialize_facet_param(value) -> Any:
    """A facet parameter: a simple value or a restriction block.

    The restriction block is the IDS form shared with the clients:
    ``{"restriction": "Enumeration"|"Pattern"|"Bounds"|"Length",
    "values": [...]}``.
    """
    if not isinstance(value, Restriction):
        return value
    options = value.options or {}
    if "enumeration" in options:
        enumerated = options["enumeration"]
        if not isinstance(enumerated, list):
            enumerated = [enumerated]
        return {"restriction": "Enumeration", "values": [str(item) for item in enumerated]}
    if "pattern" in options:
        pattern = options["pattern"]
        if not isinstance(pattern, list):
            pattern = [pattern]
        return {"restriction": "Pattern", "values": [str(item) for item in pattern]}
    minimum = options.get("minInclusive", options.get("minExclusive"))
    maximum = options.get("maxInclusive", options.get("maxExclusive"))
    if minimum is not None or maximum is not None:
        return {
            "restriction": "Bounds",
            "values": [
                "" if minimum is None else str(minimum),
                "" if maximum is None else str(maximum),
            ],
        }
    length = options.get("length")
    minimum_length = options.get("minLength")
    maximum_length = options.get("maxLength")
    if length is not None:
        return {"restriction": "Length", "values": [str(length), str(length)]}
    if minimum_length is not None or maximum_length is not None:
        return {
            "restriction": "Length",
            "values": [
                "" if minimum_length is None else str(minimum_length),
                "" if maximum_length is None else str(maximum_length),
            ],
        }
    # An unsupported restriction vocabulary: kept as its options, lossless.
    return {"restriction": "Raw", "values": options}


def _deserialize_facet_param(data) -> Any:
    """The reverse of _serialize_facet_param: a simple value or a
    restriction block becomes an ifctester Restriction."""
    if not isinstance(data, dict) or "restriction" not in data:
        return data
    kind = data["restriction"]
    values = [str(value) for value in data.get("values", [])]
    if kind == "Enumeration":
        return Restriction(options={"enumeration": values})
    if kind == "Pattern":
        return Restriction(options={"pattern": values or [""]})
    if kind == "Bounds":
        options = {}
        if len(values) > 0 and values[0] != "":
            options["minInclusive"] = values[0]
        if len(values) > 1 and values[1] != "":
            options["maxInclusive"] = values[1]
        return Restriction(options=options)
    if kind == "Length":
        options = {}
        for index, key in ((0, "minLength"), (1, "maxLength")):
            if len(values) > index and values[index] != "":
                try:
                    options[key] = int(values[index])
                except ValueError:
                    options[key] = values[index]
        return Restriction(options=options)
    if kind == "Raw":
        return Restriction(options=data.get("values") or {})
    return Restriction()


def serialize_facet(facet: Facet) -> dict[str, Any]:
    """Serialize an ifctester Facet to a dictionary, carrying every
    parameter (value, cardinality, instructions) and the restriction
    blocks of the complex values.

    Args:
        facet: The facet to serialize

    Returns:
        Dictionary representation of the facet
    """
    if isinstance(facet, Entity):
        return {
            "type": "Entity",
            "name": _serialize_facet_param(facet.name),
            "predefined_type": _serialize_facet_param(facet.predefinedType),
            "instructions": facet.instructions,
        }
    elif isinstance(facet, Property):
        return {
            "type": "Property",
            "property_set": _serialize_facet_param(facet.propertySet),
            "base_name": _serialize_facet_param(facet.baseName),
            "value": _serialize_facet_param(facet.value),
            "data_type": facet.dataType,
            "cardinality": facet.cardinality,
            "instructions": facet.instructions,
        }
    elif isinstance(facet, Attribute):
        return {
            "type": "Attribute",
            "name": _serialize_facet_param(facet.name),
            "value": _serialize_facet_param(facet.value),
            "cardinality": facet.cardinality,
            "instructions": facet.instructions,
        }
    elif isinstance(facet, Classification):
        return {
            "type": "Classification",
            "value": _serialize_facet_param(facet.value),
            "system": _serialize_facet_param(facet.system),
            "cardinality": facet.cardinality,
            "instructions": facet.instructions,
        }
    elif isinstance(facet, PartOf):
        return {
            "type": "PartOf",
            "name": _serialize_facet_param(facet.name),
            "predefined_type": _serialize_facet_param(facet.predefinedType),
            "relation": _serialize_facet_param(facet.relation),
            "cardinality": facet.cardinality,
            "instructions": facet.instructions,
        }
    elif isinstance(facet, Material):
        return {
            "type": "Material",
            "value": _serialize_facet_param(facet.value),
            "cardinality": facet.cardinality,
            "instructions": facet.instructions,
        }
    else:
        raise ValueError(f"Unsupported facet type: {type(facet)}")


def deserialize_facet(facet_data: dict[str, Any]) -> Facet:
    """Deserialize a dictionary to an ifctester Facet, restoring the
    restriction blocks of the complex values.

    Args:
        facet_data: Dictionary representation of the facet

    Returns:
        The deserialized Facet object
    """
    facet_type = facet_data.get("type")

    if facet_type == "Entity":
        return Entity(
            name=_deserialize_facet_param(facet_data.get("name", "IFCWALL")),
            predefinedType=_deserialize_facet_param(facet_data.get("predefined_type")),
            instructions=facet_data.get("instructions"),
        )
    elif facet_type == "Property":
        return Property(
            propertySet=_deserialize_facet_param(facet_data.get("property_set", "Property_Set")),
            baseName=_deserialize_facet_param(facet_data.get("base_name", "PropertyName")),
            value=_deserialize_facet_param(facet_data.get("value")),
            dataType=facet_data.get("data_type"),
            cardinality=facet_data.get("cardinality", "required"),
            instructions=facet_data.get("instructions"),
        )
    elif facet_type == "Attribute":
        return Attribute(
            name=_deserialize_facet_param(facet_data.get("name", "Name")),
            value=_deserialize_facet_param(facet_data.get("value")),
            cardinality=facet_data.get("cardinality", "required"),
            instructions=facet_data.get("instructions"),
        )
    elif facet_type == "Classification":
        return Classification(
            value=_deserialize_facet_param(facet_data.get("value")),
            system=_deserialize_facet_param(facet_data.get("system")),
            cardinality=facet_data.get("cardinality", "required"),
            instructions=facet_data.get("instructions"),
        )
    elif facet_type == "PartOf":
        return PartOf(
            name=_deserialize_facet_param(facet_data.get("name", "IFCWALL")),
            predefinedType=_deserialize_facet_param(facet_data.get("predefined_type")),
            relation=_deserialize_facet_param(facet_data.get("relation")),
            cardinality=facet_data.get("cardinality", "required"),
            instructions=facet_data.get("instructions"),
        )
    elif facet_type == "Material":
        return Material(
            value=_deserialize_facet_param(facet_data.get("value")),
            cardinality=facet_data.get("cardinality", "required"),
            instructions=facet_data.get("instructions"),
        )
    else:
        raise ValueError(f"Unknown facet type: {facet_type}")


# ============================================================================
# Boolean rules (BooleanLeaf, AndRule, OrRule, NotRule)
# ============================================================================


def serialize_boolean_rule(node) -> dict[str, Any]:
    """
    Serialize a BooleanRule tree to a dictionary.

    A BooleanLeaf serializes its rule by value (nested). A composite
    (AndRule, OrRule, NotRule) serializes its children recursively.

    Args:
        node: The BooleanRule to serialize, or None

    Returns:
        Dictionary representation, or None
    """
    from booleanrule import AndRule, BooleanLeaf, NotRule, OrRule

    if node is None:
        return None

    if isinstance(node, BooleanLeaf):
        return {
            "type": "BooleanLeaf",
            "mode": node.mode,
            "value": node.value,
            "rule": serialize_rule_check(node.rule),
        }

    if isinstance(node, AndRule):
        return {
            "type": "AndRule",
            "children": [serialize_boolean_rule(child) for child in node.children],
        }

    if isinstance(node, OrRule):
        return {
            "type": "OrRule",
            "children": [serialize_boolean_rule(child) for child in node.children],
        }

    if isinstance(node, NotRule):
        return {
            "type": "NotRule",
            "child": serialize_boolean_rule(node.child),
        }

    raise ValueError(f"Unsupported boolean rule type: {type(node)}")


def deserialize_boolean_rule(data: dict[str, Any]):
    """
    Deserialize a dictionary to a BooleanRule tree.

    Args:
        data: Dictionary representation, or None

    Returns:
        BooleanRule object, or None
    """
    from booleanrule import AndRule, BooleanLeaf, NotRule, OrRule

    if data is None:
        return None

    boolean_type = data.get("type")

    if boolean_type == "BooleanLeaf":
        rule = deserialize_rule_check(data["rule"])
        return BooleanLeaf(rule, data.get("mode", "have_result"), data.get("value"))

    if boolean_type == "AndRule":
        return AndRule(*[deserialize_boolean_rule(child) for child in data.get("children", [])])

    if boolean_type == "OrRule":
        return OrRule(*[deserialize_boolean_rule(child) for child in data.get("children", [])])

    if boolean_type == "NotRule":
        return NotRule(deserialize_boolean_rule(data["child"]))

    raise ValueError(f"Unknown boolean rule type: {boolean_type}")


# ============================================================================
# Exceptions (str or BooleanLeaf)
# ============================================================================


def serialize_exception(exception) -> Any:
    """
    Serialize the select_exception of a rule.

    select_exception is either a relation exception name (str) or a
    BooleanLeaf evaluated result by result.

    Args:
        exception: The exception to serialize

    Returns:
        A string or a dictionary representation
    """
    from booleanrule import BooleanRule

    if isinstance(exception, str):
        return exception
    if isinstance(exception, BooleanRule):
        return serialize_boolean_rule(exception)
    raise ValueError(f"Unsupported exception type: {type(exception)}")


def deserialize_exception(data: Any):
    """
    Deserialize the select_exception of a rule.

    Args:
        data: A string or a dictionary representation

    Returns:
        A str or a BooleanRule
    """
    if isinstance(data, str):
        return data
    return deserialize_boolean_rule(data)


# ============================================================================
# Activation rule of a folder (SelectFacet or BooleanRule)
# ============================================================================


def serialize_activation_rule(activation_rule) -> Any:
    """
    Serialize the activation rule of a RuleFolder.

    The activation rule is either a SelectFacet or a BooleanRule.

    Args:
        activation_rule: The activation rule, or None

    Returns:
        Dictionary representation, or None
    """
    from booleanrule import BooleanRule

    if activation_rule is None:
        return None
    if isinstance(activation_rule, BooleanRule):
        return serialize_boolean_rule(activation_rule)
    return serialize_select(activation_rule)


def deserialize_activation_rule(data: Any):
    """
    Deserialize the activation rule of a RuleFolder.

    Args:
        data: Dictionary representation, or None

    Returns:
        A Select or a BooleanRule, or None
    """
    if data is None:
        return None
    if isinstance(data, dict) and data.get("type") in ("BooleanLeaf", "AndRule", "OrRule", "NotRule"):
        return deserialize_boolean_rule(data)
    return deserialize_select(data)


# ============================================================================
# Absolute or relative checking (Must rule)
# ============================================================================


def serialize_abs_or_rel_check(check) -> dict[str, Any]:
    """
    Serialize an AbsoluteOrRelativeChecking.

    Args:
        check: The AbsoluteOrRelativeChecking to serialize, or None

    Returns:
        Dictionary representation, or None
    """
    from RuleClass import AbsoluteOrRelativeChecking

    if check is None:
        return None

    if not isinstance(check, AbsoluteOrRelativeChecking):
        raise ValueError(f"Unsupported check type: {type(check)}")

    return {
        "class": type(check).__name__,
        "check_type": check.type,
        "quantity_pset": check.quantity_pset,
        "quantity_prop": check.quantity_prop,
        "operation": check.operation,
    }


def deserialize_abs_or_rel_check(data: dict[str, Any]):
    """
    Deserialize an AbsoluteOrRelativeChecking.

    The checks used to be two classes (AbsoluteChecking,
    RelativeChecking) and carried separate focus / aim /
    source_operation / target_operation fields: the old names are
    still accepted, their fields are merged into the new operation
    ("SOURCE=2*TARGET" or "TARGET<=2").

    Args:
        data: Dictionary representation, or None

    Returns:
        An AbsoluteOrRelativeChecking, or None
    """
    from RuleClass import AbsoluteOrRelativeChecking

    if data is None:
        return None

    class_name = data.get("class")

    if class_name not in (
        "AbsoluteOrRelativeChecking",
        "AbsoluteChecking",
        "RelativeChecking",
    ):
        raise ValueError(f"Unknown check class: {class_name}")

    check = AbsoluteOrRelativeChecking(data["check_type"])
    check.quantity_pset = data.get("quantity_pset")
    check.quantity_prop = data.get("quantity_prop")
    check.operation = data.get("operation")

    # The old format: no SOURCE or TARGET keyword in the operation,
    # the comparison was split into focus / operation / aim (absolute)
    # or source_operation / operation / target_operation (relative).
    if check.operation is not None and not ("SOURCE" in check.operation or "TARGET" in check.operation):
        if data["check_type"].startswith("Relative"):
            check.operation = (
                f"SOURCE{data.get('source_operation', '')}"
                f"{data.get('operation', '')}"
                f"TARGET{data.get('target_operation', '')}"
            )
        else:
            measured = "TARGET" if data.get("focus", "source") == "source" else "SOURCE"
            check.operation = f"{measured}{data.get('operation', '')}{data.get('aim', 0)}"

    return check


# ============================================================================
# Grouping (str, raw facet or SelectFacet)
# ============================================================================


def serialize_grouping(grouping) -> Any:
    """
    Serialize the select_grouping of a rule.

    select_grouping is either a grouping method name (str, e.g. "ENTITY"),
    a raw ifctester facet (Property, Attribute, ...) or a SelectFacet.

    Args:
        grouping: The grouping to serialize, or None

    Returns:
        A string or a dictionary representation, or None
    """
    if grouping is None:
        return None
    if isinstance(grouping, str):
        return grouping
    if isinstance(grouping, Facet):
        return serialize_facet(grouping)
    if hasattr(grouping, "applicability"):
        return serialize_select_facet(grouping)
    raise ValueError(f"Unsupported grouping type: {type(grouping)}")


def deserialize_grouping(data: Any):
    """
    Deserialize the select_grouping of a rule.

    Args:
        data: A string or a dictionary representation, or None

    Returns:
        A str, a Facet or a SelectFacet, or None
    """
    if data is None:
        return None
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        if data.get("type") == "SelectFacet":
            return deserialize_select_facet(data)
        return deserialize_facet(data)
    raise ValueError(f"Unsupported grouping data: {data}")


# ============================================================================
# Selects
# ============================================================================


def serialize_select_facet(select_facet: "SelectFacet") -> dict[str, Any]:
    """
    Serialize a SelectFacet to a dictionary.

    Args:
        select_facet: The SelectFacet to serialize

    Returns:
        Dictionary representation
    """
    return {
        "type": "SelectFacet",
        "classification_type": getattr(select_facet, "type", "Facet"),
        "classification_name": getattr(select_facet, "classification_name", ""),
        "applicability": [serialize_facet(f) for f in select_facet.applicability],
    }


def deserialize_select_facet(data: dict[str, Any]) -> "SelectFacet":
    """
    Deserialize a dictionary to a SelectFacet.

    Args:
        data: Dictionary representation

    Returns:
        SelectFacet object
    """
    from RuleClass import SelectFacet

    select = SelectFacet(ClassificationType=data.get("classification_type", "Facet"))
    select.classification_name = data.get("classification_name", "")
    select.applicability = [deserialize_facet(f) for f in data.get("applicability", [])]
    return select


def serialize_select_rule(select_rule: "SelectRule") -> dict[str, Any]:
    """
    Serialize a SelectRule to a dictionary.

    The referenced rule is serialized by value (nested). It is rebuilt as
    an identical copy when loading.

    Args:
        select_rule: The SelectRule to serialize

    Returns:
        Dictionary representation
    """
    return {
        "type": "SelectRule",
        "action_type": getattr(select_rule, "action_type", 1),
        "element_to_pass": getattr(select_rule, "element_to_pass", "source"),
        "element_state_to_pass": getattr(select_rule, "element_state_to_pass", True),
        "rule": serialize_rule_check(select_rule.rule),
    }


def deserialize_select_rule(data: dict[str, Any]) -> "SelectRule":
    """
    Deserialize a dictionary to a SelectRule.

    Args:
        data: Dictionary representation

    Returns:
        SelectRule object
    """
    from RuleClass import SelectRule

    select_rule = SelectRule()
    if "action_type" in data:
        select_rule.action_type = data["action_type"]
    select_rule.element_to_pass = data.get("element_to_pass", "source")
    select_rule.element_state_to_pass = data.get("element_state_to_pass", True)
    select_rule.rule = deserialize_rule_check(data["rule"])
    return select_rule


def serialize_select(select: "Select") -> dict[str, Any]:
    """
    Serialize a Select object to a dictionary.

    Args:
        select: The Select to serialize

    Returns:
        Dictionary representation
    """
    if select is None:
        return None

    if hasattr(select, "applicability"):
        # It's a SelectFacet
        return serialize_select_facet(select)
    elif hasattr(select, "rule"):
        # It's a SelectRule
        return serialize_select_rule(select)
    else:
        return {"type": "Select", "id": getattr(select, "id", None)}


def deserialize_select(data: dict[str, Any]) -> "Select":
    """
    Deserialize a dictionary to a Select object.

    Args:
        data: Dictionary representation

    Returns:
        Select object
    """
    select_type = data.get("type")

    if select_type == "SelectFacet":
        return deserialize_select_facet(data)
    elif select_type == "SelectRule":
        return deserialize_select_rule(data)
    else:
        from RuleClass import Select

        return Select()


# ============================================================================
# Rules
# ============================================================================


def _serialize_rule_specific_data(rule: "RuleCheck") -> dict[str, Any]:
    """
    Serialize the type-specific parameters of a rule.

    Args:
        rule: The RuleCheck to serialize

    Returns:
        Dictionary of the parameters of the rule
    """
    data: dict[str, Any] = {}
    rule_type = type(rule).__name__

    if rule_type == "Volume":
        data["volume_min"] = rule.volume_min
        data["volume_max"] = rule.volume_max
    elif rule_type == "Area":
        # The Area class stores its bounds in volume_min / volume_max
        data["volume_min"] = rule.volume_min
        data["volume_max"] = rule.volume_max
    elif rule_type == "TopOrBottomSurface":
        data["surface_min"] = rule.surface_min
        data["surface_max"] = rule.surface_max
        data["top_or_bot_method"] = rule.top_or_bot_method
    elif rule_type == "LateralSurface":
        data["surface_min"] = rule.surface_min
        data["surface_max"] = rule.surface_max
        data["direction"] = rule.direction
    elif rule_type == "ProjectedSurface":
        data["surface_min"] = rule.surface_min
        data["surface_max"] = rule.surface_max
        data["direction"] = rule.direction
    elif rule_type == "ObbHigh":
        data["length_min"] = rule.length_min
        data["length_max"] = rule.length_max
    elif rule_type == "ObbLength":
        data["length_min"] = rule.length_min
        data["length_max"] = rule.length_max
        data["direction_method"] = rule.direction_method
    elif rule_type == "Orientation":
        data["orientation"] = list(rule.orientation)
        data["orientation_type"] = rule.orientation_type
        data["direction_method"] = rule.direction_method
        data["angular_tolerance"] = rule.angular_tolerance
    elif rule_type == "AngleBetween":
        data["direction_method_for_source"] = rule.direction_method_for_source
        data["direction_method_for_target"] = rule.direction_method_for_target
        data["angle_difference"] = rule.angle_difference
        data["angle_tolerance"] = rule.angle_tolerance
    elif rule_type == "Intersection":
        data["tolerance"] = rule.tolerance
    elif rule_type == "Intersection2":
        data["tolerance"] = rule.tolerance
    elif rule_type == "Clearance":
        data["clearance"] = rule.clearance
        data["check_all"] = rule.check_all
    elif rule_type == "Collision":
        data["allow_touching"] = rule.allow_touching
    elif rule_type == "Ray_Check":
        data["max_ray_length"] = rule.max_ray_length
        if rule.select_context is not None:
            data["select_context"] = serialize_select(rule.select_context)
    elif rule_type == "Above":
        # Above stores its type (e.g. "Above_MaxToMax") in rule.type
        data["above_type"] = rule.type
        data["tolerance"] = rule.tolerance
    elif rule_type == "Below":
        # Below stores its type in rule.type
        data["below_type"] = rule.type
        data["tolerance"] = rule.tolerance
    elif rule_type == "OBB_Above":
        data["tolerance"] = rule.tolerance
    elif rule_type == "OBB_Below":
        data["tolerance"] = rule.tolerance
    elif rule_type == "OBB_Front_And_Back":
        data["tolerance"] = rule.tolerance
        data["direction_method"] = rule.direction_method
    elif rule_type == "OBB_Custom":
        data["list_of_modifications"] = rule.list_of_modifications
    elif rule_type == "Alignement":
        data["axis"] = rule.axis
        data["alignment_type"] = rule.alignment_type
        data["tolerance"] = rule.tolerance
        data["min_group"] = rule.min_group
    elif rule_type == "SurfaceRecover":
        # direction: "Auto" / "Top" / "Bottom" or a 3D vector
        data["direction"] = rule.direction if isinstance(rule.direction, str) else list(rule.direction)
        data["reference"] = rule.reference
        data["tolerance"] = rule.tolerance
        # A covering bound: None or a ("absolute"/"relative", value) pair
        data["min_covering"] = list(rule.min_covering) if rule.min_covering is not None else None
        data["max_covering"] = list(rule.max_covering) if rule.max_covering is not None else None
    elif rule_type == "DirectView":
        data["ray_source"] = rule.ray_source
        data["ray_count"] = rule.ray_count
        data["threshold"] = rule.threshold  # percentage as a float
        data["max_distance"] = rule.max_distance
        if rule.select_context is not None:
            data["select_context"] = serialize_select(rule.select_context)
    elif rule_type == "OneObjectFace":
        data["face_a_selection"] = rule.face_a_selection
        data["face_b_selection"] = rule.face_b_selection
        data["distance"] = rule.distance
        data["min_distance"] = rule.min_distance
        data["max_distance"] = rule.max_distance
        data["skip_adjacent"] = rule.skip_adjacent
        data["intersection"] = rule.intersection
        data["intersection_tolerance"] = rule.intersection_tolerance
        data["orientation"] = rule.orientation
        data["angle"] = rule.angle
        data["angle_tolerance"] = rule.angle_tolerance
    elif rule_type == "TwoObjectsFace":
        data["source_face_selection"] = rule.source_face_selection
        data["target_face_selection"] = rule.target_face_selection
        data["distance"] = rule.distance
        data["min_distance"] = rule.min_distance
        data["max_distance"] = rule.max_distance
        data["intersection"] = rule.intersection
        data["intersection_tolerance"] = rule.intersection_tolerance
        data["orientation"] = rule.orientation
        data["angle"] = rule.angle
        data["angle_tolerance"] = rule.angle_tolerance
    elif rule_type == "ClearanceForDoors":
        data["zone_shape"] = rule.zone_shape
        data["sides"] = rule.sides
        data["leaves"] = rule.leaves
        data["width"] = rule.width
        data["depth"] = rule.depth
        data["height"] = rule.height
        data["tolerance"] = rule.tolerance
    elif rule_type == "FreeSpace":
        data["diameter"] = rule.diameter
        data["height"] = rule.height
        if rule.select_context is not None:
            data["select_context"] = serialize_select(rule.select_context)
    elif rule_type == "ClearanceAxisToAxis":
        data["mode"] = rule.mode
        data["min_distance"] = rule.min_distance
        data["max_distance"] = rule.max_distance
        data["tolerance"] = rule.tolerance
        data["linearity_ratio"] = rule.linearity_ratio
        data["on_non_linear"] = rule.on_non_linear
        data["parallel_tolerance"] = rule.parallel_tolerance

    return data


def serialize_rule_check(rule: "RuleCheck") -> dict[str, Any]:
    """
    Serialize a RuleCheck to a dictionary.

    All the common attributes (id, state, grouping, criticity, actor,
    exception, absolute or relative checking) and the type-specific
    parameters are serialized.

    Args:
        rule: The RuleCheck to serialize

    Returns:
        Dictionary representation
    """
    data = {
        "type": type(rule).__name__,
        "id": rule.id,
        "state": getattr(rule, "state", "Final"),
        "select_grouping": serialize_grouping(getattr(rule, "select_grouping", None)),
        "select_criticity": [serialize_select_facet(s) for s in getattr(rule, "select_criticity", [])],
        "select_actor": [serialize_select_facet(s) for s in getattr(rule, "select_actor", [])],
    }

    data.update(_serialize_rule_specific_data(rule))

    if getattr(rule, "select_source", None) is not None:
        data["select_source"] = serialize_select(rule.select_source)
    if getattr(rule, "select_target", None) is not None:
        data["select_target"] = serialize_select(rule.select_target)

    if getattr(rule, "select_exception", None) is not None:
        data["select_exception"] = serialize_exception(rule.select_exception)

    if getattr(rule, "abs_or_rel_check", None) is not None:
        data["abs_or_rel_check"] = serialize_abs_or_rel_check(rule.abs_or_rel_check)

    return data


def _deserialize_rule_source_target(data: dict[str, Any]):
    """
    Extract the source and target selects of a serialized rule.

    A rule can have no select (an exception rule is created empty: its
    source and target are given at the evaluation of each result).

    Args:
        data: Dictionary representation of the rule

    Returns:
        A (source, target) tuple
    """
    source = None
    if data.get("select_source") is not None:
        source = deserialize_select(data["select_source"])

    target = None
    if data.get("select_target") is not None:
        target = deserialize_select(data["select_target"])

    return source, target


def deserialize_rule_check(data: dict[str, Any], ifc_paths: list[str] = None) -> "RuleCheck":
    """
    Deserialize a dictionary to a RuleCheck.

    All the rule types are rebuilt with their type-specific parameters,
    then the common attributes are restored.

    Args:
        data: Dictionary representation
        ifc_paths: Optional list of IFC paths for the rule file

    Returns:
        RuleCheck object
    """
    from Rules import (
        Above,
        Alignement,
        AngleBetween,
        Intersection2,
        Area,
        Below,
        Clearance,
        ClearanceAxisToAxis,
        ClearanceForDoors,
        Collision,
        DirectView,
        FreeSpace,
        Intersection,
        LateralSurface,
        OBB_Above,
        OBB_Below,
        OBB_Custom,
        OBB_Front_And_Back,
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

    rule_type = data["type"]
    source, target = _deserialize_rule_source_target(data)

    if rule_type == "Volume":
        rule = Volume(source, data.get("volume_min", 0), data.get("volume_max", float("inf")))
    elif rule_type == "Area":
        rule = Area(
            source,
            data.get("volume_min", data.get("area_min", 0)),
            data.get("volume_max", data.get("area_max", float("inf"))),
        )
    elif rule_type == "TopOrBottomSurface":
        rule = TopOrBottomSurface(
            source,
            data.get("surface_min", 0),
            data.get("surface_max", float("inf")),
            data.get("top_or_bot_method", "Top"),
        )
    elif rule_type == "LateralSurface":
        rule = LateralSurface(
            source,
            data.get("surface_min", 0),
            data.get("surface_max", float("inf")),
            data.get("direction", 0),
        )
    elif rule_type == "ProjectedSurface":
        rule = ProjectedSurface(
            source,
            data.get("surface_min", 0),
            data.get("surface_max", float("inf")),
            data.get("direction", 0),
        )
    elif rule_type == "ObbHigh":
        rule = ObbHigh(source, data.get("length_min", 0), data.get("length_max", float("inf")))
    elif rule_type == "ObbLength":
        rule = ObbLength(
            source,
            data.get("length_min", 0),
            data.get("length_max", float("inf")),
            data.get("direction_method", "Wide"),
        )
    elif rule_type == "Orientation":
        rule = Orientation(
            source,
            tuple(data.get("orientation", (0, 0, 1))),
            data.get("orientation_type", "Parrallel"),
            data.get("direction_method", "Wide"),
            data.get("angular_tolerance", 0.1),
        )
    elif rule_type == "AngleBetween":
        rule = AngleBetween(
            source,
            target,
            data.get("direction_method_for_source", "Wide"),
            data.get("direction_method_for_target", "Wide"),
            data.get("angle_difference", 0),
            data.get("angle_tolerance", 0),
        )
    elif rule_type == "Intersection":
        rule = Intersection(source, target, data.get("tolerance", 0.1))
    elif rule_type == "Intersection2":
        rule = Intersection2(source, target, data.get("tolerance", 0.0))
    elif rule_type == "Clearance":
        rule = Clearance(source, target, data.get("clearance", 0.05))
        rule.check_all = data.get("check_all", False)
    elif rule_type == "Collision":
        rule = Collision(source, target, data.get("allow_touching", False))
        # The constructor always sets allow_touching to False
        rule.allow_touching = data.get("allow_touching", False)
    elif rule_type == "Ray_Check":
        context = None
        if data.get("select_context") is not None:
            context = deserialize_select(data["select_context"])
        rule = Ray_Check(source, target, context, data.get("max_ray_length", 1.0))
    elif rule_type == "Above":
        rule = Above(
            source,
            target,
            data.get("above_type", "Above_MaxToMax"),
            data.get("tolerance", 0.1),
        )
    elif rule_type == "Below":
        rule = Below(
            source,
            target,
            data.get("below_type", "Below_MaxToMax"),
            data.get("tolerance", 0.1),
        )
    elif rule_type == "OBB_Above":
        rule = OBB_Above(source, target, data.get("tolerance", 0.1))
    elif rule_type == "OBB_Below":
        rule = OBB_Below(source, target, data.get("tolerance", 0.1))
    elif rule_type == "OBB_Front_And_Back":
        rule = OBB_Front_And_Back(
            source,
            target,
            data.get("tolerance", 0.1),
            data.get("direction_method", "Wide"),
        )
    elif rule_type == "OBB_Custom":
        rule = OBB_Custom(source, target, data.get("list_of_modifications", []))
    elif rule_type == "Alignement":
        rule = Alignement(
            source,
            axis=data.get("axis"),
            alignment_type=data.get("alignment_type", "Plane"),
            tolerance=data.get("tolerance"),
            min_group=data.get("min_group", 3),
        )
    elif rule_type == "SurfaceRecover":
        # direction: "Auto" / "Top" / "Bottom" or a 3D vector (list)
        direction = data.get("direction", "Auto")
        if isinstance(direction, list):
            direction = tuple(direction)
        rule = SurfaceRecover(
            source,
            target,
            direction=direction,
            reference=data.get("reference", "Source"),
            tolerance=data.get("tolerance", 0.001),
        )
        # The covering bounds are restored as parsed pairs: the
        # constructor expects the raw form (a number or a "x%" string),
        # the serialized form is the parsed ("kind", value) pair.
        if data.get("min_covering") is not None:
            rule.min_covering = tuple(data["min_covering"])
        if data.get("max_covering") is not None:
            rule.max_covering = tuple(data["max_covering"])
    elif rule_type == "DirectView":
        context = None
        if data.get("select_context") is not None:
            context = deserialize_select(data["select_context"])
        # The threshold is a percentage as a float; the constructor
        # expects a string ending with '%'.
        threshold = data.get("threshold", 100.0)
        if isinstance(threshold, (int, float)):
            threshold = f"{threshold}%"
        rule = DirectView(
            source,
            target,
            context,
            ray_source=data.get("ray_source", "Source"),
            ray_count=data.get("ray_count", 10),
            threshold=threshold,
            max_distance=data.get("max_distance"),
        )
    elif rule_type == "OneObjectFace":
        rule = OneObjectFace(
            source,
            face_a_selection=data.get("face_a_selection") or None,
            face_b_selection=data.get("face_b_selection") or None,
            distance=data.get("distance", False),
            min_distance=data.get("min_distance"),
            max_distance=data.get("max_distance"),
            skip_adjacent=data.get("skip_adjacent", True),
            intersection=data.get("intersection", False),
            intersection_tolerance=data.get("intersection_tolerance"),
            orientation=data.get("orientation", False),
            angle=data.get("angle"),
            angle_tolerance=data.get("angle_tolerance"),
        )
    elif rule_type == "TwoObjectsFace":
        rule = TwoObjectsFace(
            source,
            target,
            source_face_selection=data.get("source_face_selection") or None,
            target_face_selection=data.get("target_face_selection") or None,
            distance=data.get("distance", False),
            min_distance=data.get("min_distance"),
            max_distance=data.get("max_distance"),
            intersection=data.get("intersection", False),
            intersection_tolerance=data.get("intersection_tolerance"),
            orientation=data.get("orientation", False),
            angle=data.get("angle"),
            angle_tolerance=data.get("angle_tolerance"),
        )
    elif rule_type == "ClearanceForDoors":
        rule = ClearanceForDoors(
            source,
            target,
            zone_shape=data.get("zone_shape", "Arc"),
            sides=data.get("sides", "Swing"),
            leaves=data.get("leaves"),
            width=data.get("width"),
            depth=data.get("depth"),
            height=data.get("height"),
            tolerance=data.get("tolerance", 0.001),
        )
    elif rule_type == "FreeSpace":
        context = None
        if data.get("select_context") is not None:
            context = deserialize_select(data["select_context"])
        rule = FreeSpace(
            source,
            context,
            diameter=data.get("diameter", 1.5),
            height=data.get("height"),
        )
    elif rule_type == "ClearanceAxisToAxis":
        rule = ClearanceAxisToAxis(
            source,
            target,
            mode=data.get("mode", "Perpendicular"),
            min_distance=data.get("min_distance"),
            max_distance=data.get("max_distance"),
            tolerance=data.get("tolerance", 0.0),
            linearity_ratio=data.get("linearity_ratio", 10.0),
            on_non_linear=data.get("on_non_linear", "Skip"),
            parallel_tolerance=data.get("parallel_tolerance", 1.0),
        )
    else:
        raise NotImplementedError(f"Deserialization for {rule_type} not yet implemented")

    # Restore the common attributes
    rule.id = data.get("id")
    rule.state = data.get("state", "Final")
    rule.select_grouping = deserialize_grouping(data.get("select_grouping"))
    rule.select_criticity = [deserialize_select_facet(s) for s in data.get("select_criticity", [])]
    rule.select_actor = [deserialize_select_facet(s) for s in data.get("select_actor", [])]
    if data.get("select_exception") is not None:
        rule.select_exception = deserialize_exception(data["select_exception"])
    if data.get("abs_or_rel_check") is not None:
        rule.abs_or_rel_check = deserialize_abs_or_rel_check(data["abs_or_rel_check"])

    return rule


# ============================================================================
# Folders
# ============================================================================


def serialize_rule_folder(folder: "RuleFolder") -> dict[str, Any]:
    """
    Serialize a RuleFolder to a dictionary.

    Args:
        folder: The RuleFolder to serialize

    Returns:
        Dictionary representation
    """
    return {
        "type": "RuleFolder",
        "id": folder.id,
        "activation_case": folder.activation_case,
        "activation_rule": serialize_activation_rule(folder.activation_rule),
        "contains": [serialize_rule_or_folder(item) for item in folder.contains],
    }


def deserialize_rule_folder(data: dict[str, Any], ifc_paths: list[str] = None) -> "RuleFolder":
    """
    Deserialize a dictionary to a RuleFolder.

    Args:
        data: Dictionary representation
        ifc_paths: Optional list of IFC paths

    Returns:
        RuleFolder object
    """
    from RuleClass import RuleFolder

    folder = RuleFolder()
    folder.id = data.get("id", "")
    folder.activation_case = data.get("activation_case", "ALLTRUE")
    folder.activation_rule = deserialize_activation_rule(data.get("activation_rule"))
    folder.contains = [deserialize_rule_or_folder(item, ifc_paths) for item in data.get("contains", [])]

    return folder


# ============================================================================
# Dispatch between rules and folders
# ============================================================================


def serialize_rule_or_folder(item: Any) -> dict[str, Any]:
    """
    Serialize a rule or folder to a dictionary.

    Args:
        item: The item to serialize (RuleCheck or RuleFolder)

    Returns:
        Dictionary representation
    """
    from RuleClass import RuleCheck, RuleFolder

    if isinstance(item, RuleFolder):
        return serialize_rule_folder(item)
    elif isinstance(item, RuleCheck):
        return serialize_rule_check(item)
    else:
        raise ValueError(f"Unknown item type: {type(item)}")


def deserialize_rule_or_folder(data: dict[str, Any], ifc_paths: list[str] = None) -> Any:
    """
    Deserialize a dictionary to a rule or folder.

    Args:
        data: Dictionary representation
        ifc_paths: Optional list of IFC paths

    Returns:
        RuleCheck or RuleFolder object
    """
    item_type = data.get("type")

    if item_type == "RuleFolder":
        return deserialize_rule_folder(data, ifc_paths)
    else:
        # It's a rule
        return deserialize_rule_check(data, ifc_paths)


# ============================================================================
# Rule files
# ============================================================================


def serialize_rule_file(rule_file: "RuleFile") -> dict[str, Any]:
    """
    Serialize a RuleFile to a dictionary.

    Args:
        rule_file: The RuleFile to serialize

    Returns:
        Dictionary representation
    """
    return {
        "type": "RuleFile",
        "id": rule_file.id,
        "list_ifc_path": rule_file.list_ifc_path,
        "path_to_save": rule_file.path_to_save,
        "contains": [serialize_rule_or_folder(item) for item in rule_file.contains],
    }


def deserialize_rule_file(data: dict[str, Any]) -> "RuleFile":
    """
    Deserialize a dictionary to a RuleFile.

    Args:
        data: Dictionary representation

    Returns:
        RuleFile object
    """
    from RuleClass import RuleFile

    rule_file = RuleFile()
    rule_file.id = data.get("id", "")
    rule_file.list_ifc_path = data.get("list_ifc_path", [])
    rule_file.path_to_save = data.get("path_to_save")

    # Deserialize contains
    for item_data in data.get("contains", []):
        item = deserialize_rule_or_folder(item_data, rule_file.list_ifc_path)
        rule_file.contains.append(item)

    return rule_file


def save_to_json(rule_file: "RuleFile", filepath: str) -> None:
    """
    Save a RuleFile configuration to a JSON file.

    Args:
        rule_file: The RuleFile to save
        filepath: Path to the JSON file
    """
    data = serialize_rule_file(rule_file)

    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


def load_from_json(filepath: str) -> "RuleFile":
    """
    Load a RuleFile configuration from a JSON file.

    Args:
        filepath: Path to the JSON file

    Returns:
        RuleFile object
    """
    with open(filepath) as f:
        data = json.load(f)

    return deserialize_rule_file(data)


# ============================================================================
# Results export
# ============================================================================


def _model_names(rule_file: "RuleFile") -> dict:
    """The {file identity or path key: model name} map joined by the
    element cross-references (see result_export.element_ref).

    The name of a model is the basename of its IFC path. The ifc_file
    wrappers built by ifcopenshell.file.from_pointer have another id()
    than the opened files: they are joined back by pathname.
    """
    names: dict = {}
    for path, ifc_file in zip(rule_file.list_ifc_path, rule_file.list_ifc_file):
        name = os.path.basename(path)
        names[id(ifc_file)] = name
        # ifcopenshell >= 0.9 has no file.pathname anymore and every
        # entity.file access builds a fresh wrapper: the opened files
        # are also joined by their underlying parse file pointer.
        file_pointer = getattr(ifc_file, "file_pointer", None)
        if file_pointer is not None:
            names[("fp", file_pointer())] = name
        pathname = getattr(ifc_file, "pathname", None)
        if pathname:
            names[("path", pathname)] = name
            names[("path", os.path.abspath(pathname))] = name
    return names


def _iter_rules(items):
    """The rules of a contains list, folders flattened in run order."""
    from RuleClass import RuleFolder

    for item in items:
        if isinstance(item, RuleFolder):
            yield from _iter_rules(item.contains)
        else:
            yield item


def rule_results_to_json(rule, model_names: dict) -> dict[str, Any]:
    """One rule's results as JSON: its configuration (the same
    dictionary as save_to_json produces), the plain results and, when a
    grouping or a Must check ran, the grouped results."""
    from result_export import _rule_type, element_ref, results_to_dicts

    data: dict[str, Any] = {
        "node_id": rule.id,
        "rule_type": _rule_type(rule),
        "configuration": serialize_rule_check(rule),
        "results": results_to_dicts(rule.result, rule, model_names),
    }

    groups = []
    for group in getattr(rule, "grouped_result", []) or []:
        groups.append(
            {
                "id": getattr(group, "id", None),
                "sources": [
                    element_ref(element, model_names)
                    for element in getattr(group, "source_set", []) or []
                ],
                "targets": [
                    element_ref(element, model_names)
                    for element in getattr(group, "target_set", []) or []
                ],
                "result_count": len(getattr(group, "result_group", []) or []),
            }
        )
    if groups:
        data["grouped"] = groups
    return data


def results_to_json(rule_file: "RuleFile") -> dict[str, Any]:
    """All the results produced by the rules of a run RuleFile, together
    with the configuration of the RuleFile, as a JSON-ready dictionary.

    Every element reference carries the GUID of the object (global_id)
    and the name of its model (model, the basename of the IFC path).
    The rules of the folders are flattened in run order; each of them
    carries its own configuration. The results are empty unless
    rule_file.run() has been called first.
    """
    model_names = _model_names(rule_file)
    return {
        "type": "RuleFileResults",
        "models": [
            {"name": os.path.basename(path), "path": path}
            for path in rule_file.list_ifc_path
        ],
        "configuration": serialize_rule_file(rule_file),
        "rules": [
            rule_results_to_json(rule, model_names)
            for rule in _iter_rules(rule_file.contains)
        ],
    }


def save_results_to_json(rule_file: "RuleFile", filepath: str) -> None:
    """Save all the results of a run RuleFile to a JSON file, together
    with the configuration of the RuleFile (rules, folders, selects,
    exception, grouping, criticity, actor, Must checks).

    Args:
        rule_file: The run RuleFile whose results are saved
        filepath: Path to the JSON file
    """
    with open(filepath, "w") as f:
        json.dump(results_to_json(rule_file), f, indent=4)


# ============================================================================
# Fonctions simplifiées pour l'exemple.py
# ============================================================================


def save_configuration_to_json(configuration: dict[str, Any], filepath: str) -> None:
    """
    Sauvegarde une configuration de règles dans un fichier JSON.

    Cette fonction est conçue pour être utilisée directement dans exemple.py
    avec une structure de configuration simple.

    Args:
        configuration: Dictionnaire contenant la configuration
        filepath: Chemin vers le fichier JSON
    """
    with open(filepath, "w") as f:
        json.dump(configuration, f, indent=4, default=str)


def load_configuration_from_json(filepath: str) -> dict[str, Any]:
    """
    Charge une configuration de règles depuis un fichier JSON.

    Args:
        filepath: Chemin vers le fichier JSON

    Returns:
        Dictionnaire contenant la configuration
    """
    with open(filepath) as f:
        return json.load(f)


def create_configuration_from_rule_file(rule_file: "RuleFile") -> dict[str, Any]:
    """
    Crée une configuration sérialisable à partir d'un RuleFile.

    Args:
        rule_file: Le RuleFile à sérialiser

    Returns:
        Dictionnaire contenant la configuration
    """
    config = {"ifc_paths": rule_file.list_ifc_path, "rules": []}

    for item in rule_file.contains:
        rule_config = serialize_rule_or_folder(item)
        config["rules"].append(rule_config)

    return config


def apply_configuration_to_rule_file(rule_file: "RuleFile", config: dict[str, Any]) -> "RuleFile":
    """
    Applique une configuration à un RuleFile.

    Args:
        rule_file: Le RuleFile à configurer
        config: La configuration à appliquer

    Returns:
        Le RuleFile configuré
    """
    rule_file.list_ifc_path = config.get("ifc_paths", [])
    rule_file.contains = []

    for rule_config in config.get("rules", []):
        rule = deserialize_rule_or_folder(rule_config, rule_file.list_ifc_path)
        rule_file.contains.append(rule)

    return rule_file


# ============================================================================
# Fonctions utilitaires pour la sérialisation des règles spécifiques
# ============================================================================


def serialize_intersection_rule(rule: "Intersection") -> dict[str, Any]:
    """
    Sérialise une règle Intersection.

    Args:
        rule: La règle Intersection

    Returns:
        Dictionnaire de configuration
    """
    return {
        "type": "Intersection",
        "tolerance": rule.tolerance,
        "source": serialize_select(rule.select_source),
        "target": serialize_select(rule.select_target),
    }


def deserialize_intersection_rule(data: dict[str, Any]) -> "Intersection":
    """
    Désérialise une règle Intersection.

    Args:
        data: Dictionnaire de configuration

    Returns:
        Règle Intersection
    """
    from Rules import Intersection

    source = deserialize_select(data["source"])
    target = deserialize_select(data["target"])
    tolerance = data.get("tolerance", 0.001)

    return Intersection(source, target, tolerance)


def serialize_clearance_rule(rule: "Clearance") -> dict[str, Any]:
    """
    Sérialise une règle Clearance.

    Args:
        rule: La règle Clearance

    Returns:
        Dictionnaire de configuration
    """
    return {
        "type": "Clearance",
        "clearance": rule.clearance,
        "source": serialize_select(rule.select_source),
        "target": serialize_select(rule.select_target),
    }


def deserialize_clearance_rule(data: dict[str, Any]) -> "Clearance":
    """
    Désérialise une règle Clearance.

    Args:
        data: Dictionnaire de configuration

    Returns:
        Règle Clearance
    """
    from Rules import Clearance

    source = deserialize_select(data["source"])
    target = deserialize_select(data["target"])
    clearance = data.get("clearance", 1.0)

    return Clearance(source, target, clearance)


def serialize_above_rule(rule: "Above") -> dict[str, Any]:
    """
    Sérialise une règle Above.

    Args:
        rule: La règle Above

    Returns:
        Dictionnaire de configuration
    """
    return {
        "type": "Above",
        "tolerance": rule.tolerance,
        "above_type": rule.type,
        "source": serialize_select(rule.select_source),
        "target": serialize_select(rule.select_target),
    }


def deserialize_above_rule(data: dict[str, Any]) -> "Above":
    """
    Désérialise une règle Above.

    Args:
        data: Dictionnaire de configuration

    Returns:
        Règle Above
    """
    from Rules import Above

    source = deserialize_select(data["source"])
    target = deserialize_select(data["target"])
    tolerance = data.get("tolerance", 1.0)
    above_type = data.get("above_type", "Above_MaxToMax")

    return Above(source, target, above_type, tolerance)
