// IfcClash_Plus engine — SurfaceRecover (Rules.py), declared here so that a
// variant can read its geometry elsewhere (SurfaceRecover_triang,
// engine/triang: the triangles, their OBB and their skin distance instead of
// the meshed B-Rep and BRepExtrema).
#pragma once

#include "RuleBase.h"

#include <Bnd_Box.hxx>
#include <Bnd_OBB.hxx>
#include <TopoDS_Shape.hxx>

#include <array>
#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace ifcclash {

struct SurfaceRecoverParams {
    Json direction = "Auto";  // "Auto" | "Top" | "Bottom" | a 3D vector
    std::string reference = "Source";
    double tolerance = 0.001;
    Json min_covering = nullptr;
    Json max_covering = nullptr;
};

struct RecoverData {
    TopoDS_Shape occ;                  // the meshed B-Rep (the original rule)
    std::shared_ptr<const void> skin;  // another skin (a variant: its triangles)
    Bnd_OBB obb;
    Bnd_Box box;
    std::vector<double> verts;  // the triangles (world), for the extreme faces
    std::vector<int> faces;
    std::array<double, 3> centroid{};
};

struct Covering {
    bool relative = false;
    double value = 0.0;
};

class SurfaceRecover : public PairRule<SurfaceRecoverParams> {
public:
    using V3 = std::array<double, 3>;
    Variant base_variant() const override { return Variant::BrepWorld; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    bool needs_element_data() const override { return true; }
    bool parallel_safe() const override { return true; }  // element_data: geometry only
    bool skip_self() const override { return false; }    // Python: no self check
    std::vector<Variant> data_variants() const override { return {Variant::MeshWorld}; }

    void setup() override;
    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override;
    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override;
    Verdict narrow_test(const ElementGeometry& source, const ElementGeometry& target) const override;

protected:
    // The distance between the two skins and its closest points:
    // BRepExtrema on the meshed B-Reps.
    virtual double skin_distance(const RecoverData& s, const RecoverData& t, std::optional<V3>& ps,
                                 std::optional<V3>& pt) const;

private:
    bool auto_ = false;
    V3 direction_{0.0, 0.0, 1.0};
    std::optional<Covering> min_, max_;
};

}  // namespace ifcclash
