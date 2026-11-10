// IfcClash_Plus engine — Alignement (Rules.py): the elements that do not
// belong to an aligned group of at least min_group members. Declared here so
// that a variant can read the OBBs elsewhere (Alignement_triang, engine/triang:
// the OBB of the triangles instead of the meshed B-Rep).
#pragma once

#include "RuleBase.h"

#include <Bnd_OBB.hxx>

#include <optional>
#include <string>
#include <vector>

namespace ifcclash {

struct AlignementParams {
    std::optional<std::string> axis;  // None / "" = auto, "Vertical", "Horizontal"
    std::string alignment_type = "Plane";
    std::optional<double> tolerance;
    int min_group = 3;
};

class Alignement : public SetRule<AlignementParams> {
public:
    Variant base_variant() const override { return Variant::BrepWorld; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    void setup() override;
    std::vector<Verdict> narrow_set(const std::vector<ElementGeometry>& elements) const override;

protected:
    // The OBB of an element (nullopt: no geometry, the element is left out):
    // the OBB of the meshed B-Rep, kept in the Session.
    virtual std::optional<Bnd_OBB> element_obb(const ElementGeometry& e) const;
};

}  // namespace ifcclash
