// IfcClash_Plus engine — DirectView (Rules.py), declared here so that a
// variant can read its geometry elsewhere (DirectView_triang, engine/triang:
// the repaired triangles and a triangle BVH of the context instead of the
// world triangulation and the IfcOpenShell ray tree).
#pragma once

#include "RuleBase.h"
#include "../sources/IfcRayTree.h"

#include <Bnd_Box.hxx>

#include <array>
#include <memory>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace ifcclash {

struct DirectViewParams {
    std::string ray_source = "Source";
    int ray_count = 10;
    double threshold = 100.0;  // %
    std::optional<double> max_distance;
};

// The triangles of an element, their centroid and box.
struct ViewMesh {
    std::vector<Triangle3> triangles;
    std::array<double, 3> centroid{};
    Bnd_Box box;
};

class DirectView : public PairRule<DirectViewParams> {
public:
    using V3 = std::array<double, 3>;
    Variant base_variant() const override { return Variant::MeshWorld; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    bool needs_element_data() const override { return true; }
    bool uses_context() const override { return true; }
    // A pair is flagged by a hit ratio over the threshold: with no maximum
    // distance (or a 0 % threshold) a far pair can be flagged.
    BroadMode broad_mode() const override {
        return params().max_distance && params().threshold > 0.0 ? BroadMode::Spatial : BroadMode::AllPairs;
    }

    void setup() override;
    void setup_context(const std::vector<ElementKey>& context, GeometryProvider& provider) override;
    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override;
    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override;
    Verdict narrow_test(const ElementGeometry& s, const ElementGeometry& t) const override;

protected:
    // Whether a context element stands on the ray from origin along the unit
    // direction, over `length`: the IfcOpenShell ray tree (select_ray).
    virtual bool blocked(const V3& origin, const V3& dir, double length) const;

private:
    static std::vector<Triangle3> faces_toward(const ViewMesh& mesh, const V3& other);
    static std::vector<double> areas_of(const std::vector<Triangle3>& faces);
    std::vector<std::pair<V3, V3>> pair_rays(const ViewMesh& emitter, const ViewMesh& receiver) const;
    bool cast_ray(const V3& origin, const V3& aim) const;

    std::unique_ptr<RayTree> tree_;
};

}  // namespace ifcclash
