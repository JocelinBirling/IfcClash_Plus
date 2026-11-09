// IfcClash_Plus engine — the result contract (SPEC "Contrat de résultat").
//
// A ResultRecord carries exactly what ResultInfo.to_dict() serialises on the
// Python side, field for field, so that a thin Python adapter rebuilds the
// ClashResult / ResultInfo objects and the management pipeline, the JSON
// export and the IPC stay unchanged.
#pragma once

#include "ElementKey.h"

#include <nlohmann/json.hpp>

#include <array>
#include <cstdint>
#include <optional>
#include <string>
#include <utility>
#include <vector>

namespace ifcclash {

using Json = nlohmann::ordered_json;

// Version of the exchange format. Bump it on any change of the JSON shape.
inline constexpr int kResultSchemaVersion = 1;

// The fixed measure vocabulary (ResultInfo.MEASURE_ATTRIBUTES).
enum class Measure {
    Distance,
    PenetrationDepth,
    ContactArea,
    Ratio,
    Offset,
    HitRatio,
    Angle,
    Volume,
    Area,
};

const char* measure_name(Measure m);

// The measures in their order of pose: the first one is the nominal measure
// (ResultInfo._measure_order).
class Measures {
public:
    void set(Measure m, double value);
    std::optional<double> get(Measure m) const;
    bool empty() const { return values_.empty(); }
    const std::vector<std::pair<Measure, double>>& items() const { return values_; }

private:
    std::vector<std::pair<Measure, double>> values_;
};

using Point3 = std::array<double, 3>;

// One numbered point pair (ResultInfo.add_point_pair): number N on both sides.
struct PointPair {
    Point3 source{};
    Point3 target{};
    std::optional<std::string> label;
};

// The per-result flags (degraded geometry, fallback source...).
struct Flags {
    bool degraded = false;
    bool gross_element = false;
    bool fallback_source = false;
    bool any() const { return degraded || gross_element || fallback_source; }
};

// What narrow_test decides. Only status == true becomes a result (the Python
// engines only append the clashing elements).
struct Verdict {
    bool status = false;
    Measures measures;
    std::vector<PointPair> points;
    Flags flags;
};

struct ResultRecord {
    ElementKey source;
    std::optional<ElementKey> target;
    bool status = true;
    Measures measures;
    std::vector<PointPair> points;
    Flags flags;
};

enum class Severity { Info, Warning, Error };

struct Diagnostic {
    Severity severity = Severity::Info;
    std::string code;      // stable identifier: "no_geometry", "duplicate_global_id"...
    std::string message;
    std::optional<ElementKey> element;
};

struct Diagnostics {
    std::vector<Diagnostic> entries;
    void add(Severity s, std::string code, std::string message,
             std::optional<ElementKey> element = std::nullopt) {
        entries.push_back({s, std::move(code), std::move(message), std::move(element)});
    }
};

// Pairs (or elements) in and out of one phase, and its time.
struct PhaseStat {
    std::string phase;  // "broad", "mid", "narrow"
    size_t in = 0;
    size_t out = 0;
    double seconds = 0.0;
};

struct PhaseStats {
    std::string rule;
    std::vector<PhaseStat> phases;
    double total_seconds = 0.0;
    // "Clearance  broad: 48210 → 1342   mid: 1342 → 187   narrow: 187 → 12   (2.4 s)"
    std::string summary() const;
};

// The tessellated display geometry produced by the engine. No TopoDS_Shape
// crosses the boundary.
struct DisplayItem {
    std::string category;  // input, point, segment, axis, face, obb, zone, context
    std::optional<ElementKey> element;
    std::vector<double> vertices;  // flat x, y, z (world, metres)
    std::vector<int> indices;      // triangles (3 per face) or segments (2 per edge)
};

struct DisplayPayload {
    std::vector<DisplayItem> items;
    bool empty() const { return items.empty(); }
};

// Replaces `state` on the engine side. Final / Select stay management modes
// of the Python side.
enum class RunMode {
    Verdicts,            // normal run
    InputsOnly,          // input geometry, no computation (former Display_Input)
    VerdictsAndDisplay,  // former Display_Result, and the IPC preview
};

RunMode run_mode_from_string(const std::string& s);
const char* run_mode_name(RunMode m);

struct RunResult {
    std::vector<ResultRecord> results;  // sorted by (source, target)
    DisplayPayload display;             // empty in RunMode::Verdicts
    PhaseStats stats;
    Diagnostics diagnostics;
};

// ---- JSON (the exchange format, see SPEC "Format d'échange")
Json to_json(const ElementKey& key);
// The ResultInfo.to_dict() shape of one record (measure, points).
Json info_to_json(const ResultRecord& record);
Json to_json(const ResultRecord& record);
Json to_json(const PhaseStats& stats);
Json to_json(const Diagnostics& diagnostics);
// Everything but the display payload (bindings expose it as numpy arrays).
Json to_json(const RunResult& result);

void sort_results(std::vector<ResultRecord>& results);

}  // namespace ifcclash
