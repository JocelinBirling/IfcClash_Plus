// IfcClash_Plus engine — the exceptions.
//
// Only an invalid configuration raises (SPEC: "Seule une configuration
// invalide lève une exception"); an element in failure produces a flag and a
// diagnostic, never an exception.
#pragma once

#include <stdexcept>
#include <string>

namespace ifcclash {

// Invalid rule type, parameter, selection or session option: detected before
// any computation.
struct ConfigError : std::runtime_error {
    using std::runtime_error::runtime_error;
};

// The CancelToken was triggered: the run stops between phases / batches.
struct Cancelled : std::runtime_error {
    Cancelled() : std::runtime_error("run cancelled") {}
};

}  // namespace ifcclash
