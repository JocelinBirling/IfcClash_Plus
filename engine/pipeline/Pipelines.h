// IfcClash_Plus engine — the pipelines (SPEC "Familles de règles").
//
// They share the GeometryProvider, the per-phase statistics, the
// cancellation and the result contract.
#pragma once

#include "../core/Control.h"
#include "../core/Result.h"
#include "../provider/GeometryProvider.h"
#include "../rules/RuleBase.h"

#include <utility>
#include <vector>

namespace ifcclash {

struct RunContext {
    GeometryProvider& provider;
    const CancelToken& cancel;
    ProgressSink& progress;
    Diagnostics& diagnostics;
    PhaseStats& stats;
    // false: debug option prefilter="off", the broad and mid phases are
    // skipped (every pair reaches the narrow phase). The results must be
    // identical with and without: the check that these phases only remove.
    bool prefilter = true;
};

// The elements that have geometry, in input order, duplicates removed. The
// others get a "no_geometry" diagnostic (the Python engines skip them
// silently).
std::vector<ElementKey> with_geometry(const std::vector<ElementKey>& keys, RunContext& ctx,
                                      std::vector<ElementBoxes>& boxes_out);

class ElementPipeline {
public:
    static std::vector<ResultRecord> run(const ElementRuleBase& rule, const std::vector<ElementKey>& elements,
                                         RunContext& ctx);
};

class PairPipeline {
public:
    static std::vector<ResultRecord> run(const PairRuleBase& rule, const std::vector<ElementKey>& sources,
                                         const std::vector<ElementKey>& targets, RunContext& ctx);

    // A rule evaluated on a batch of given pairs (the BooleanLeaf
    // exceptions): the per-pair broad and mid tests, then the narrow test.
    static std::vector<ResultRecord> evaluate(const PairRuleBase& rule, const std::vector<KeyPair>& pairs,
                                              RunContext& ctx);
};

}  // namespace ifcclash
