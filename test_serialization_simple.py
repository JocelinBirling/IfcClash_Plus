#!/usr/bin/env python3
"""
Simple test script for serialization module
"""

import sys
sys.path.insert(0, './ifcclash_plus')

from RuleClass import SelectFacet, RuleFile
from Rules import Intersection
from ifctester import ids
from serialization import save_to_json, load_from_json, create_configuration_from_rule_file

def test_simple_serialization():
    """Test basic serialization functionality"""
    
    # Create a simple configuration
    ifc_path = "Ifc_Model/Ifc2x3_Duplex_Architecture.ifc"
    
    OneRuleFile = RuleFile()
    OneRuleFile.list_ifc_path = [ifc_path]

    first_facet = ids.Entity(name="IFCDOOR")
    first_select = SelectFacet()
    first_select.applicability = [first_facet]

    second_facet = ids.Entity(name="IFCWALLSTANDARDCASE")
    second_select = SelectFacet()
    second_select.applicability = [second_facet]

    intersection_rule = Intersection(first_select, second_select, 0.1)
    intersection_rule.select_grouping = "TARGET"

    OneRuleFile.contains = [intersection_rule]

    # Test create_configuration_from_rule_file
    try:
        config = create_configuration_from_rule_file(OneRuleFile)
        print("✓ create_configuration_from_rule_file succeeded")
        print(f"Config: {config}")
    except Exception as e:
        print(f"✗ create_configuration_from_rule_file failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test save_to_json
    try:
        save_to_json(OneRuleFile, "test_simple_config.json")
        print("✓ save_to_json succeeded")
    except Exception as e:
        print(f"✗ save_to_json failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test load_from_json
    try:
        loaded_rule_file = load_from_json("test_simple_config.json")
        print("✓ load_from_json succeeded")
        print(f"Loaded IFC paths: {loaded_rule_file.list_ifc_path}")
        print(f"Number of rules: {len(loaded_rule_file.contains)}")
    except Exception as e:
        print(f"✗ load_from_json failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = test_simple_serialization()
    if success:
        print("\n✓ All tests passed!")
    else:
        print("\n✗ Some tests failed")
        sys.exit(1)
