// IfcClash_Plus engine — the rule interfaces (SPEC "Convention de nommage des phases").
//
// Prefix = phase (broad_ / mid_ / narrow_), suffix = action (_volume builds a
// bounding volume, once per element; _test decides, once per candidate pair).
// The broad and mid phases can only eliminate (Candidate::Rejected / Kept)
// and must be conservative; only narrow_test produces a verdict.
//
// The hooks are const and a rule keeps no mutable state after setup(): this
// is what will let the narrow phase run in parallel without touching the
// rules (SPEC "Parallélisme").
#pragma once

#include "../core/Geometry.h"
#include "../core/Result.h"
#include "../geometry/MeshMeasures.h"
#include "../provider/GeometryProvider.h"

#include <memory>
#include <optional>
#include <utility>
#include <vector>

namespace ifcclash {

enum class Candidate { Rejected, Kept };
enum class Role { Source, Target };
enum class BroadMode { Spatial, AllPairs };
enum class PipelineKind { Element, Pair, Context, Set };

// How a pair met twice is treated. Ordered: (A, B) and (B, A) are two
// pairs. Unordered: tested once — the semantics of the IfcOpenShell clash
// tree (its tested_pairs set), kept by the rules that delegate to it.
enum class PairSymmetry { Ordered, Unordered };

// The view of one element handed to the hooks. The geometry is converted on
// demand: an element rejected by the broad or mid phase is never asked for
// its mesh / B-Rep.
class ElementGeometry {
public:
    ElementGeometry(const ElementKey& key, const ElementBoxes& boxes, GeometryProvider& provider)
        : key(key), boxes(boxes), provider_(&provider) {}

    const ElementKey& key;
    const ElementBoxes& boxes;

    std::shared_ptr<const Mesh> mesh() const { return provider_->mesh(key); }
    std::optional<TopoDS_Shape> brep() const { return provider_->brep(key); }
    // Engine-side services (the IFC triangle clash queries). Not for rules
    // that only need geometry.
    GeometryProvider& provider() const { return *provider_; }

private:
    GeometryProvider* provider_;
};

class RuleBase {
public:
    virtual ~RuleBase() = default;
    virtual PipelineKind kind() const = 0;
    // Prepares a state derived from the typed parameters (already filled and
    // validated by the RuleSpec). Called once, before any phase.
    virtual void setup() {}
    virtual Level narrow_level() const { return Level::BRep; }
};

// ---- One-object rules: setup -> narrow_test(e) -> report
class ElementRuleBase : public RuleBase {
public:
    PipelineKind kind() const final { return PipelineKind::Element; }
    virtual Verdict narrow_test(const ElementGeometry& element) const = 0;
    virtual ResultRecord report(const Verdict& verdict) const;
};

// ---- Two-object rules: broad -> mid -> narrow -> report
class PairRuleBase : public RuleBase {
public:
    PipelineKind kind() const final { return PipelineKind::Pair; }

    virtual BroadMode broad_mode() const { return BroadMode::Spatial; }
    virtual PairSymmetry symmetry() const { return PairSymmetry::Ordered; }

    // Broad phase (the BVH belongs to the engine; its test, AABB overlap,
    // is fixed). Default: raw AABB inflated by the uncertainty.
    virtual Bnd_Box broad_volume(const ElementGeometry& e, Role role) const;

    // Mid phase. Default volume: raw OBB inflated by the uncertainty;
    // default test: keep everything.
    virtual Bnd_OBB mid_volume(const ElementGeometry& e, Role role) const;
    virtual Candidate mid_test(const Bnd_OBB& /*source*/, const Bnd_OBB& /*target*/) const {
        return Candidate::Kept;
    }

    // Narrow phase: the exact verdict (mandatory).
    virtual Verdict narrow_test(const ElementGeometry& source, const ElementGeometry& target) const = 0;

    // Narrow phase on a batch of candidate pairs, verdicts aligned with the
    // input. Default: narrow_test on each pair. A rule whose exact test has
    // a cheaper batched form (one IfcOpenShell tree query) overrides it; the
    // verdicts must be those of narrow_test.
    using GeometryPair = std::pair<const ElementGeometry*, const ElementGeometry*>;
    virtual std::vector<Verdict> narrow_batch(const std::vector<GeometryPair>& pairs) const;

    virtual ResultRecord report(const Verdict& verdict) const;
};

// The typed parameters of a rule, filled by the engine from its RuleSpec.
template <class Params>
class ElementRule : public ElementRuleBase {
public:
    using params_type = Params;
    const Params& params() const { return params_; }
    Params& mutable_params() { return params_; }  // engine only

private:
    Params params_;
};

template <class Params>
class PairRule : public PairRuleBase {
public:
    using params_type = Params;
    const Params& params() const { return params_; }
    Params& mutable_params() { return params_; }  // engine only

private:
    Params params_;
};

}  // namespace ifcclash
