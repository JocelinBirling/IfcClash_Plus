// IfcClash_Plus engine — ClearanceAxisToAxis (Rules.py), declared here so that
// a variant can read its geometry elsewhere (ClearanceAxisToAxis_triang,
// engine/triang: the OBB of the triangles and their skin distance instead of
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

struct AxisToAxisParams {
    std::string mode = "Perpendicular";
    std::optional<double> min_distance;
    std::optional<double> max_distance;
    double tolerance = 0.0;
    double linearity_ratio = 10.0;
    std::string on_non_linear = "Skip";
    double parallel_tolerance = 1.0;
    std::optional<double> search_radius;  // m; beyond it a pair is not a neighbour
};

// The long axis of an element and what its skin distance needs.
struct LongAxis {
    TopoDS_Shape shape;               // the meshed B-Rep (the original rule)
    std::shared_ptr<const void> skin;  // another skin (a variant: its triangles)
    Bnd_Box box;                       // bounds the skin (Fallback radius test)
    std::array<double, 3> center{};
    std::array<double, 3> direction{};
    double half_length = 0.0;
    double linearity = 0.0;
};

// clash_utils.obb_long_axis: center, direction, half length and linearity of
// the longest OBB axis.
void long_axis(const Bnd_OBB& obb, LongAxis& out);

struct AxisMeasure {
    double distance = 0.0;
    double angle = 0.0;
    std::optional<std::array<double, 3>> source_point, target_point;
    std::string mode;
    bool degraded = false;
};

class ClearanceAxisToAxis : public PairRule<AxisToAxisParams> {
public:
    Variant base_variant() const override { return Variant::BrepWorld; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    // A distance OUTSIDE the interval is flagged: a far pair can be a
    // result (max_distance), so no spatial prefilter.
    BroadMode broad_mode() const override { return BroadMode::AllPairs; }
    bool needs_element_data() const override { return true; }
    bool parallel_safe() const override { return true; }  // element_data: geometry only
    // The nearest target of each source and the unordered pairs: a verdict
    // depends on the other pairs of the run.
    bool narrow_whole_run() const override { return true; }

    void setup() override;
    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override;
    Verdict narrow_test(const ElementGeometry& source, const ElementGeometry& target) const override;
    std::vector<Verdict> narrow_batch(const std::vector<GeometryPair>& pairs) const override;

protected:
    // The distance between the skins of two non-linear elements (Fallback)
    // and its closest points: BRepExtrema on the meshed B-Reps.
    virtual double skin_distance(const LongAxis& s, const LongAxis& t, std::optional<std::array<double, 3>>& ps,
                                 std::optional<std::array<double, 3>>& pt) const;

private:
    std::optional<AxisMeasure> measure(const LongAxis& s, const LongAxis& t) const;
    Verdict verdict(const AxisMeasure& m, const LongAxis& s, const LongAxis& t, bool is_nearest) const;
};

}  // namespace ifcclash
