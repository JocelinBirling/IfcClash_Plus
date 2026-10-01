"""
Serialization module for IfcClash_Plus

This module provides functions to save and load rule configurations to/from JSON files.
It handles the serialization of RuleFile, RuleFolder, SelectFacet, SelectRule, and various rule types.
"""

import json
import importlib
from typing import Any, Dict, List, Union, Type
from ifctester import ids
from ifctester.facet import (
    Facet,
    Entity,
    Property,
    Attribute,
    Classification,
    PartOf,
    Material,
)


def serialize_facet(facet: Facet) -> Dict[str, Any]:
    """
    Serialize an ifctester Facet to a dictionary.
    
    Args:
        facet: The facet to serialize
        
    Returns:
        Dictionary representation of the facet
    """
    if isinstance(facet, Entity):
        return {
            "type": "Entity",
            "name": facet.name,
            "ifc_version": facet.ifc_version
        }
    elif isinstance(facet, Property):
        return {
            "type": "Property",
            "property_set": facet.propertySet,
            "base_name": facet.baseName,
            "value": facet.value,
            "ifc_version": facet.ifc_version
        }
    elif isinstance(facet, Attribute):
        return {
            "type": "Attribute",
            "name": facet.name,
            "value": facet.value,
            "ifc_version": facet.ifc_version
        }
    elif isinstance(facet, Classification):
        return {
            "type": "Classification",
            "name": facet.name,
            "value": facet.value,
            "ifc_version": facet.ifc_version
        }
    elif isinstance(facet, PartOf):
        return {
            "type": "PartOf",
            "name": facet.name,
            "ifc_version": facet.ifc_version
        }
    elif isinstance(facet, Material):
        return {
            "type": "Material",
            "name": facet.name,
            "ifc_version": facet.ifc_version
        }
    else:
        raise ValueError(f"Unsupported facet type: {type(facet)}")


def deserialize_facet(facet_data: Dict[str, Any]) -> Facet:
    """
    Deserialize a dictionary to an ifctester Facet.
    
    Args:
        facet_data: Dictionary representation of the facet
        
    Returns:
        The deserialized Facet object
    """
    facet_type = facet_data.get("type")
    ifc_version = facet_data.get("ifc_version", None)
    
    if facet_type == "Entity":
        return Entity(name=facet_data["name"], ifc_version=ifc_version)
    elif facet_type == "Property":
        return Property(
            propertySet=facet_data["property_set"],
            baseName=facet_data["base_name"],
            value=facet_data["value"],
            ifc_version=ifc_version
        )
    elif facet_type == "Attribute":
        return Attribute(
            name=facet_data["name"],
            value=facet_data["value"],
            ifc_version=ifc_version
        )
    elif facet_type == "Classification":
        return Classification(
            name=facet_data["name"],
            value=facet_data["value"],
            ifc_version=ifc_version
        )
    elif facet_type == "PartOf":
        return PartOf(name=facet_data["name"], ifc_version=ifc_version)
    elif facet_type == "Material":
        return Material(name=facet_data["name"], ifc_version=ifc_version)
    else:
        raise ValueError(f"Unknown facet type: {facet_type}")


def serialize_select_facet(select_facet: 'SelectFacet') -> Dict[str, Any]:
    """
    Serialize a SelectFacet to a dictionary.
    
    Args:
        select_facet: The SelectFacet to serialize
        
    Returns:
        Dictionary representation
    """
    return {
        "type": "SelectFacet",
        "classification_type": select_facet.type,
        "classification_name": select_facet.classification_name,
        "applicability": [serialize_facet(f) for f in select_facet.applicability]
    }


def deserialize_select_facet(data: Dict[str, Any]) -> 'SelectFacet':
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


def serialize_select_rule(select_rule: 'SelectRule') -> Dict[str, Any]:
    """
    Serialize a SelectRule to a dictionary.
    
    Args:
        select_rule: The SelectRule to serialize
        
    Returns:
        Dictionary representation
    """
    # Note: We don't serialize the actual rule object, just its type and parameters
    # The rule will need to be reconstructed during deserialization
    return {
        "type": "SelectRule",
        "action_type": select_rule.action_type,
        "rule_type": getattr(select_rule.rule, 'type', None),
        "rule_params": {}  # Will be populated based on rule type
    }


def serialize_rule_check(rule: 'RuleCheck') -> Dict[str, Any]:
    """
    Serialize a RuleCheck to a dictionary.
    
    Args:
        rule: The RuleCheck to serialize
        
    Returns:
        Dictionary representation
    """
    rule_type = type(rule).__name__
    
    # Common attributes
    data = {
        "type": rule_type,
        "id": rule.id,
        "select_grouping": serialize_select_facet(rule.select_grouping) if rule.select_grouping else None,
        "select_criticity": [serialize_select_facet(s) for s in rule.select_criticity],
        "select_actor": [serialize_select_facet(s) for s in rule.select_actor],
    }
    
    # Add type-specific parameters
    if rule_type == "Volume":
        data["volume_min"] = rule.volume_min
        data["volume_max"] = rule.volume_max
    elif rule_type == "Area":
        data["area_min"] = rule.volume_min  # Note: misnamed in original class
        data["area_max"] = rule.volume_max
    elif rule_type == "TopSurface":
        data["surface_min"] = rule.surface_min
        data["surface_max"] = rule.surface_max
    elif rule_type == "BottomSurface":
        data["surface_min"] = rule.surface_min
        data["surface_max"] = rule.surface_max
    elif rule_type == "LateralSurface":
        data["surface_min"] = rule.surface_min
        data["surface_max"] = rule.surface_max
        data["direction"] = rule.direction
    elif rule_type == "Intersection":
        data["tolerance"] = rule.tolerance
    elif rule_type == "Clearance":
        data["clearance"] = rule.clearance
    elif rule_type == "Above":
        data["tolerance"] = rule.tolerance
        data["above_type"] = rule.above_type
    elif rule_type == "Below":
        data["tolerance"] = rule.tolerance
    elif rule_type == "OBB_Above":
        data["tolerance"] = rule.tolerance
        data["obb_tolerance"] = getattr(rule, 'obb_tolerance', None)
    elif rule_type == "Collision":
        data["tolerance"] = rule.tolerance
    
    return data


def deserialize_rule_check(data: Dict[str, Any], ifc_paths: List[str] = None) -> 'RuleCheck':
    """
    Deserialize a dictionary to a RuleCheck.
    
    Args:
        data: Dictionary representation
        ifc_paths: Optional list of IFC paths for the rule file
        
    Returns:
        RuleCheck object
    """
    from RuleClass import (
        RuleCheckOneObject,
        RuleCheckTwoObjects,
        SelectFacet,
        SelectRule
    )
    from Rules import (
        Volume, Area, TopSurface, BottomSurface, LateralSurface,
        Intersection, Clearance, Above, Below, OBB_Above, Collision
    )
    
    rule_type = data["type"]
    
    # Get the rule class
    rule_class = None
    if rule_type in globals():
        rule_class = globals()[rule_type]
    else:
        # Try to import from Rules module
        try:
            rules_module = importlib.import_module('Rules')
            if hasattr(rules_module, rule_type):
                rule_class = getattr(rules_module, rule_type)
        except:
            pass
    
    if rule_class is None:
        raise ValueError(f"Unknown rule type: {rule_type}")
    
    # For now, we'll handle specific rule types
    # This is a simplified version - in practice, you'd need to handle each rule type
    
    if rule_type == "Volume":
        # Need source select
        source = deserialize_select(data.get("select_source"))
        return Volume(source, data["volume_min"], data["volume_max"])
    
    elif rule_type == "Intersection":
        source = deserialize_select(data.get("select_source"))
        target = deserialize_select(data.get("select_target"))
        return Intersection(source, target, data.get("tolerance", 0.001))
    
    elif rule_type == "Clearance":
        source = deserialize_select(data.get("select_source"))
        target = deserialize_select(data.get("select_target"))
        return Clearance(source, target, data.get("clearance", 1.0))
    
    elif rule_type == "Above":
        source = deserialize_select(data.get("select_source"))
        target = deserialize_select(data.get("select_target"))
        return Above(source, target, data.get("tolerance", 1.0), data.get("above_type", "Above_MaxToMax"))
    
    else:
        raise NotImplementedError(f"Deserialization for {rule_type} not yet implemented")


def serialize_select(select: 'Select') -> Dict[str, Any]:
    """
    Serialize a Select object to a dictionary.
    
    Args:
        select: The Select to serialize
        
    Returns:
        Dictionary representation
    """
    if hasattr(select, 'applicability'):
        # It's a SelectFacet
        return serialize_select_facet(select)
    elif hasattr(select, 'rule'):
        # It's a SelectRule
        return serialize_select_rule(select)
    else:
        return {"type": "Select", "id": select.id}


def deserialize_select(data: Dict[str, Any]) -> 'Select':
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
        # For SelectRule, we need to reconstruct the rule first
        # This is complex and may require additional context
        from RuleClass import SelectRule
        select_rule = SelectRule()
        select_rule.action_type = data.get("action_type", 1)
        # The rule itself would need to be deserialized separately
        return select_rule
    else:
        from RuleClass import Select
        return Select()


def serialize_rule_folder(folder: 'RuleFolder') -> Dict[str, Any]:
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
        "activation_rule": serialize_select(folder.activation_rule) if folder.activation_rule else None,
        "contains": [serialize_rule_or_folder(item) for item in folder.contains]
    }


def deserialize_rule_folder(data: Dict[str, Any], ifc_paths: List[str] = None) -> 'RuleFolder':
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
    
    if data.get("activation_rule"):
        folder.activation_rule = deserialize_select(data["activation_rule"])
    
    folder.contains = [deserialize_rule_or_folder(item, ifc_paths) for item in data.get("contains", [])]
    
    return folder


def serialize_rule_or_folder(item: Any) -> Dict[str, Any]:
    """
    Serialize a rule or folder to a dictionary.
    
    Args:
        item: The item to serialize (RuleCheck or RuleFolder)
        
    Returns:
        Dictionary representation
    """
    from RuleClass import RuleFolder, RuleCheck
    
    if isinstance(item, RuleFolder):
        return serialize_rule_folder(item)
    elif isinstance(item, RuleCheck):
        return serialize_rule_check(item)
    else:
        raise ValueError(f"Unknown item type: {type(item)}")


def deserialize_rule_or_folder(data: Dict[str, Any], ifc_paths: List[str] = None) -> Any:
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


def serialize_rule_file(rule_file: 'RuleFile') -> Dict[str, Any]:
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
        "contains": [serialize_rule_or_folder(item) for item in rule_file.contains]
    }


def deserialize_rule_file(data: Dict[str, Any]) -> 'RuleFile':
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


def save_to_json(rule_file: 'RuleFile', filepath: str) -> None:
    """
    Save a RuleFile configuration to a JSON file.
    
    Args:
        rule_file: The RuleFile to save
        filepath: Path to the JSON file
    """
    data = serialize_rule_file(rule_file)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=4)


def load_from_json(filepath: str) -> 'RuleFile':
    """
    Load a RuleFile configuration from a JSON file.
    
    Args:
        filepath: Path to the JSON file
        
    Returns:
        RuleFile object
    """
    with open(filepath, 'r') as f:
        data = json.load(f)
    
    return deserialize_rule_file(data)


# ============================================================================
# Fonctions simplifiées pour l'exemple.py
# ============================================================================

def save_configuration_to_json(configuration: Dict[str, Any], filepath: str) -> None:
    """
    Sauvegarde une configuration de règles dans un fichier JSON.
    
    Cette fonction est conçue pour être utilisée directement dans exemple.py
    avec une structure de configuration simple.
    
    Args:
        configuration: Dictionnaire contenant la configuration
        filepath: Chemin vers le fichier JSON
    """
    with open(filepath, 'w') as f:
        json.dump(configuration, f, indent=4, default=str)


def load_configuration_from_json(filepath: str) -> Dict[str, Any]:
    """
    Charge une configuration de règles depuis un fichier JSON.
    
    Args:
        filepath: Chemin vers le fichier JSON
        
    Returns:
        Dictionnaire contenant la configuration
    """
    with open(filepath, 'r') as f:
        return json.load(f)


def create_configuration_from_rule_file(rule_file: 'RuleFile') -> Dict[str, Any]:
    """
    Crée une configuration sérialisable à partir d'un RuleFile.
    
    Args:
        rule_file: Le RuleFile à sérialiser
        
    Returns:
        Dictionnaire contenant la configuration
    """
    config = {
        "ifc_paths": rule_file.list_ifc_path,
        "rules": []
    }
    
    for item in rule_file.contains:
        rule_config = serialize_rule_or_folder(item)
        config["rules"].append(rule_config)
    
    return config


def apply_configuration_to_rule_file(rule_file: 'RuleFile', config: Dict[str, Any]) -> 'RuleFile':
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

def serialize_intersection_rule(rule: 'Intersection') -> Dict[str, Any]:
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
        "target": serialize_select(rule.select_target)
    }


def deserialize_intersection_rule(data: Dict[str, Any]) -> 'Intersection':
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


def serialize_clearance_rule(rule: 'Clearance') -> Dict[str, Any]:
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
        "target": serialize_select(rule.select_target)
    }


def deserialize_clearance_rule(data: Dict[str, Any]) -> 'Clearance':
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


def serialize_above_rule(rule: 'Above') -> Dict[str, Any]:
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
        "above_type": rule.above_type,
        "source": serialize_select(rule.select_source),
        "target": serialize_select(rule.select_target)
    }


def deserialize_above_rule(data: Dict[str, Any]) -> 'Above':
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
    
    return Above(source, target, tolerance, above_type)
