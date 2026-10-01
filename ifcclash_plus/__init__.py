# Package initialization for ifcclash_plus
# This makes the package installable

# Expose main modules for easy importing
from .Rules import (
    Volume, Area,  Intersection, Clearance, Above, 
    OBB_Above, Ray_Check
)
from .RuleClass import SelectFacet, SelectRule, RuleFile
from .CustomOBB import Custom_OBB

# Expose serialization functions
from .serialization import (
    save_to_json, load_from_json,
    save_configuration_to_json, load_configuration_from_json,
    create_configuration_from_rule_file, apply_configuration_to_rule_file,
    serialize_rule_file, deserialize_rule_file,
    serialize_facet, deserialize_facet
)

__all__ = [
    'Volume', 'Area', 'TopSurface', 'Intersection', 'Clearance', 'Above',
    'OBB_Above', 'Ray_Check', 'SelectFacet', 'SelectRule', 'RuleFile',
    'Custom_OBB',
    # Serialization functions
    'save_to_json', 'load_from_json',
    'save_configuration_to_json', 'load_configuration_from_json',
    'create_configuration_from_rule_file', 'apply_configuration_to_rule_file',
    'serialize_rule_file', 'deserialize_rule_file',
    'serialize_facet', 'deserialize_facet'
]

__version__ = "0.3.0"