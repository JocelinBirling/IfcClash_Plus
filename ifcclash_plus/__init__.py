# Package initialization for ifcclash_plus
# This makes the package installable

# Expose main modules for easy importing
from .Rules import (
    Volume, Area,  Intersection, Clearance, Above, 
    OBB_Above, Ray_Check, TopOrBottomSurface, Alignement, SurfaceRecover,
    DirectView, OneObjectFace, ClearanceForDoors, FreeSpace
)
from .RuleClass import SelectFacet, SelectRule, RuleFile
from .CustomOBB import Custom_OBB

# Create aliases for TopSurface and BottomSurface for backward compatibility
TopSurface = lambda source, surface_min, surface_max: TopOrBottomSurface(source, surface_min, surface_max, "Top")
BottomSurface = lambda source, surface_min, surface_max: TopOrBottomSurface(source, surface_min, surface_max, "Bottom")

# Expose serialization functions
from .serialization import (
    save_to_json, load_from_json,
    save_configuration_to_json, load_configuration_from_json,
    create_configuration_from_rule_file, apply_configuration_to_rule_file,
    serialize_rule_file, deserialize_rule_file,
    serialize_facet, deserialize_facet
)

__all__ = [
    'Volume', 'Area', 'TopOrBottomSurface', 'TopSurface', 'BottomSurface',
    'Intersection', 'Clearance', 'Above',
    'OBB_Above', 'Ray_Check', 'SelectFacet', 'SelectRule', 'RuleFile',
    'Custom_OBB', 'Alignement', 'SurfaceRecover', 'DirectView', 'OneObjectFace', 'ClearanceForDoors', 'FreeSpace',
    # Serialization functions
    'save_to_json', 'load_from_json',
    'save_configuration_to_json', 'load_configuration_from_json',
    'create_configuration_from_rule_file', 'apply_configuration_to_rule_file',
    'serialize_rule_file', 'deserialize_rule_file',
    'serialize_facet', 'deserialize_facet'
]

__version__ = "0.3.0"