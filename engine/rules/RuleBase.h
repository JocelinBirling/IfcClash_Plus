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

#include <TopoDS_Face.hxx>
#include <gp_Dir.hxx>

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

    // The per-element data the rule derived once (element_data), read-only
    // afterwards: OBB, detection zones, extreme faces...
    std::shared_ptr<const void> data;
    // Rank of the element in the inputs of the run (sources then targets,
    // first appearance): the order the Python engines meet the elements in.
    int rank = 0;
    template <class T>
    const T& as() const {
        return *static_cast<const T*>(data.get());
    }

    std::shared_ptr<const Mesh> mesh() const { return provider_->mesh(key); }
    std::shared_ptr<const Mesh> mesh(Variant variant) const { return provider_->mesh(key, variant); }
    std::optional<TopoDS_Shape> brep() const { return provider_->brep(key); }

    // The B-Rep meshed at 0.01 m and its OBB (geometry::obb_of_shape), kept
    // in the Session: one conversion and one meshing per element, shared by
    // every rule and run that needs the OBB. The shape is the meshed one, as
    // in Python where the OBB meshes the shape in place before the other
    // measures; it is shared: read it, never modify it. nullptr: no B-Rep.
    struct MeshedBrep {
        TopoDS_Shape shape;
        Bnd_OBB obb;
    };
    std::shared_ptr<const MeshedBrep> meshed_brep() const;
    // The faces of meshed_brep() seen from `view` (geometry::visible_faces,
    // 2 500 rays), kept in the Session. nullptr: no B-Rep.
    std::shared_ptr<const std::vector<TopoDS_Face>> visible_faces(const gp_Dir& view) const;
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
    // The geometry variants narrow_test reads: converted in one batch, for
    // the survivors of the prefilters only.
    virtual std::vector<Variant> narrow_variants() const { return {Variant::MeshLocal}; }
    // The variant that decides whether an element has geometry, converted
    // for every input element. MeshLocal also gives the raw boxes (the
    // default broad / mid volumes); a rule on another variant derives its
    // own volumes from its element data.
    virtual Variant base_variant() const { return Variant::MeshLocal; }
    // Other variants the element data reads, converted in one batch for
    // every input element before element_data.
    virtual std::vector<Variant> data_variants() const { return {}; }

    // ---- Context (ContextPipeline): the context elements, given once
    // before the phases. The rule builds its read-only index of them (ray
    // tree, boxes...); it never walks the context per element itself.
    virtual bool uses_context() const { return false; }
    virtual void setup_context(const std::vector<ElementKey>& /*context*/, GeometryProvider& /*provider*/) {}

    // true: narrow_test (one-object rules) and element_data (pair rules)
    // may run concurrently on distinct elements, the pipelines spread them
    // over the Session threads. Only for the rules that read nothing but the
    // geometry (brep, mesh, meshed_brep...) through the provider: no
    // IfcParse query, no ray or clash tree, no mutable state. The results do
    // not depend on it (each verdict is written at its element's index).
    virtual bool parallel_safe() const { return false; }
};

// ---- One-object rules: setup -> narrow_test(e) -> report
class ElementRuleBase : public RuleBase {
public:
    PipelineKind kind() const final { return PipelineKind::Element; }
    virtual Verdict narrow_test(const ElementGeometry& element) const = 0;
    // Several verdicts for one element (one per failed face pair:
    // OneObjectFace), in their order. Default: narrow_test alone.
    virtual std::vector<Verdict> narrow_multi(const ElementGeometry& element) const { return {narrow_test(element)}; }
    virtual bool multi_verdicts() const { return false; }
    virtual ResultRecord report(const Verdict& verdict) const;
};

// ---- Two-object rules: broad -> mid -> narrow -> report
class PairRuleBase : public RuleBase {
public:
    PipelineKind kind() const final { return PipelineKind::Pair; }

    virtual BroadMode broad_mode() const { return BroadMode::Spatial; }
    virtual PairSymmetry symmetry() const { return PairSymmetry::Ordered; }
    // An element is not tested against itself — except by the rules whose
    // Python engine does (Above, Below, OBB_*: N x M loops without a check).
    virtual bool skip_self() const { return true; }

    // Derived once per element and role, before the broad phase (OBB,
    // zones...); nullptr drops the element (the Python engines skip the
    // elements whose shape cannot be built).
    virtual bool needs_element_data() const { return false; }
    virtual std::shared_ptr<const void> element_data(const ElementGeometry& /*e*/, Role /*role*/) const {
        return nullptr;
    }

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
    // true: the narrow phase hands EVERY candidate pair of the run to one
    // narrow_batch call (no batches of 4096), in candidate order (source
    // major, then target, as the Python loops): the verdict of a pair
    // depends on the other pairs (ClearanceAxisToAxis: the nearest target
    // of each source, one result per unordered pair).
    virtual bool narrow_whole_run() const { return false; }

    // Several verdicts for one pair (one per detection zone: OBB_Front_And_Back,
    // OBB_Custom), in their order. Default: narrow_test alone.
    virtual std::vector<Verdict> narrow_multi(const ElementGeometry& source, const ElementGeometry& target) const {
        return {narrow_test(source, target)};
    }
    virtual bool multi_verdicts() const { return false; }

    virtual ResultRecord report(const Verdict& verdict) const;
};

// ---- Set rules: the verdict of an element depends on the whole set
// (Alignement): setup -> narrow_set(elements) -> report
class SetRuleBase : public RuleBase {
public:
    PipelineKind kind() const final { return PipelineKind::Set; }
    // One verdict per element, aligned with the input.
    virtual std::vector<Verdict> narrow_set(const std::vector<ElementGeometry>& elements) const = 0;
    virtual ResultRecord report(const Verdict& verdict) const;
};

template <class Params>
class SetRule : public SetRuleBase {
public:
    using params_type = Params;
    const Params& params() const { return params_; }
    Params& mutable_params() { return params_; }  // engine only

private:
    Params params_;
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
