// IfcClash_Plus engine — the IFC semantic queries some rules need
// (materials, door operation, placement axes). Provided by the sources that
// hold the IFC (IfcSource, and ViewerSource through its open file).
#pragma once

#include "../core/ElementKey.h"

#include <array>
#include <optional>
#include <string>
#include <vector>

namespace ifcclash {

class IfcQueries {
public:
    virtual ~IfcQueries() = default;
    // clash_utils.get_element_material_names (ifcopenshell.util.element.get_material,
    // inherited from the type).
    virtual std::vector<std::string> material_names(const ElementKey& key) = 0;
    // The IFC class of the element (entity.is_a()).
    virtual std::string ifc_class(const ElementKey& key) = 0;
    // ifcopenshell.util.placement.get_local_placement(element.ObjectPlacement):
    // row-major 4x4, in the project units (no conversion, as in Python).
    virtual std::array<double, 16> local_placement(const ElementKey& key) = 0;
    // clash_utils.get_door_operation_type
    virtual std::optional<std::string> door_operation_type(const ElementKey& key) = 0;
};

}  // namespace ifcclash
