// Volume — flags the sources whose volume is inside ]volume_min, volume_max[.
//
// Parity with Rules.Volume.compute: the volume is
// ifcopenshell.util.shape.get_volume of the triangulation (local frame), and
// the bounds are open (strict comparisons), as in Python today.
#include "AllRules.h"

namespace ifcclash {

namespace {

struct VolumeParams {
    double volume_min = 0.0;    // m3
    double volume_max = 100.0;  // m3
};

class Volume final : public ElementRule<VolumeParams> {
public:
    bool parallel_safe() const override { return true; }
    Level narrow_level() const override { return Level::Mesh; }

    Verdict narrow_test(const ElementGeometry& e) const override {
        Verdict v;
        const auto mesh = e.mesh();
        if (!mesh) return v;
        const double volume = geometry::mesh_volume(mesh->local_verts, mesh->faces);
        v.status = params().volume_min < volume && volume < params().volume_max;
        v.measures.set(Measure::Volume, volume);
        return v;
    }
};

}  // namespace

RuleSpec spec_volume() {
    return RuleSpec::element<Volume>(
        "Volume", "Volume", {Slot::Source},
        "Flags every source whose volume is inside ]volume_min, volume_max[.",
        {param(&VolumeParams::volume_min, "volume_min").doc("Minimum volume").unit(Unit::CubicMetre),
         param(&VolumeParams::volume_max, "volume_max").doc("Maximum volume").unit(Unit::CubicMetre)});
}

}  // namespace ifcclash
