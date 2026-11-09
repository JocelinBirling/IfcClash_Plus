// IfcClash_Plus engine — cancellation and progress of a run.
// Re-exported by api/Engine.h (the IPC "cancel" request plugs into CancelToken).
#pragma once

#include "Errors.h"

#include <atomic>
#include <cstddef>
#include <string_view>

namespace ifcclash {

class CancelToken {
public:
    void cancel() noexcept { cancelled_.store(true, std::memory_order_relaxed); }
    bool cancelled() const noexcept { return cancelled_.load(std::memory_order_relaxed); }
    void throw_if_cancelled() const {
        if (cancelled()) throw Cancelled();
    }

private:
    std::atomic<bool> cancelled_{false};
};

class ProgressSink {
public:
    virtual ~ProgressSink() = default;
    // done / total within the phase. The engine calls it at a limited rate.
    virtual void report(std::string_view /*phase*/, size_t /*done*/, size_t /*total*/) {}
};

// Cancellation is checked between the phases and every kCheckEvery items.
inline constexpr size_t kCheckEvery = 64;

}  // namespace ifcclash
