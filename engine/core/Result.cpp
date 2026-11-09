#include "Result.h"

#include "Errors.h"

#include <algorithm>
#include <cstdio>
#include <sstream>

namespace ifcclash {

const char* measure_name(Measure m) {
    switch (m) {
        case Measure::Distance: return "distance";
        case Measure::PenetrationDepth: return "penetration_depth";
        case Measure::ContactArea: return "contact_area";
        case Measure::Ratio: return "ratio";
        case Measure::Offset: return "offset";
        case Measure::HitRatio: return "hit_ratio";
        case Measure::Angle: return "angle";
        case Measure::Volume: return "volume";
        case Measure::Area: return "area";
    }
    return "?";
}

void Measures::set(Measure m, double value) {
    for (auto& [name, v] : values_) {
        if (name == m) {
            v = value;  // a re-pose keeps the order (ResultInfo.__setattr__)
            return;
        }
    }
    values_.emplace_back(m, value);
}

std::optional<double> Measures::get(Measure m) const {
    for (const auto& [name, v] : values_) {
        if (name == m) return v;
    }
    return std::nullopt;
}

std::string PhaseStats::summary() const {
    std::ostringstream out;
    out << rule;
    for (const auto& p : phases) {
        out << "   " << p.phase << ": " << p.in << " \xE2\x86\x92 " << p.out;
    }
    char buffer[32];
    std::snprintf(buffer, sizeof buffer, "   (%.3f s)", total_seconds);
    out << buffer;
    return out.str();
}

RunMode run_mode_from_string(const std::string& s) {
    if (s == "verdicts") return RunMode::Verdicts;
    if (s == "inputs_only") return RunMode::InputsOnly;
    if (s == "verdicts_and_display") return RunMode::VerdictsAndDisplay;
    throw ConfigError("unknown run mode '" + s +
                      "' (expected verdicts, inputs_only or verdicts_and_display)");
}

const char* run_mode_name(RunMode m) {
    switch (m) {
        case RunMode::Verdicts: return "verdicts";
        case RunMode::InputsOnly: return "inputs_only";
        case RunMode::VerdictsAndDisplay: return "verdicts_and_display";
    }
    return "?";
}

Json to_json(const ElementKey& key) {
    return Json{{"file_index", key.file_index},
                {"entity_id", key.entity_id},
                {"global_id", key.global_id}};
}

static Json point_json(const Point3& p) { return Json::array({p[0], p[1], p[2]}); }

Json info_to_json(const ResultRecord& record) {
    Json info = Json::object();
    if (!record.measures.empty()) {
        Json measure = Json::object();
        for (const auto& [m, value] : record.measures.items()) {
            measure[measure_name(m)] = Json{{"value", value}};
        }
        info["measure"] = std::move(measure);
    }
    if (!record.points.empty()) {
        Json points = Json::array();
        int number = 1;
        for (const auto& pair : record.points) {
            Json entry{{"number", number++},
                       {"source", point_json(pair.source)},
                       {"target", point_json(pair.target)}};
            if (pair.label) entry["label"] = *pair.label;
            points.push_back(std::move(entry));
        }
        info["points"] = std::move(points);
    }
    auto face_json = [](const FaceData& f) {
        Json triangles = Json::array();
        for (const auto& t : f.triangles) {
            triangles.push_back(Json::array({point_json(t[0]), point_json(t[1]), point_json(t[2])}));
        }
        return Json{{"normal", point_json(f.normal)}, {"area", f.area}, {"triangles", std::move(triangles)}};
    };
    if (!record.faces.empty()) {
        Json faces = Json::array();
        int number = 1;
        for (const auto& pair : record.faces) {
            faces.push_back(Json{{"number", number++},
                                 {"source", face_json(pair.source)},
                                 {"target", face_json(pair.target)}});
        }
        info["faces"] = std::move(faces);
    }
    if (record.volumes.any()) {
        Json volumes = Json::object();
        if (record.volumes.intersection) volumes["intersection"] = *record.volumes.intersection;
        if (record.volumes.ratio) volumes["ratio"] = *record.volumes.ratio;
        if (record.volumes.containment) volumes["containment"] = *record.volumes.containment;
        if (record.volumes.clearance_violated) volumes["clearance_violated"] = *record.volumes.clearance_violated;
        info["volumes"] = std::move(volumes);
    }
    auto obb_json = [](const ObbData& o) {
        Json out{{"center", point_json(o.center)},
                 {"axes", Json::array({point_json(o.axes[0]), point_json(o.axes[1]), point_json(o.axes[2])})},
                 {"half_sizes", point_json(o.half_sizes)}};
        if (o.label) out["label"] = *o.label;
        return out;
    };
    if (!record.source_obbs.empty() || !record.target_obbs.empty()) {
        Json obbs = Json::object();
        if (!record.source_obbs.empty()) {
            obbs["source"] = Json::array();
            for (const auto& o : record.source_obbs) obbs["source"].push_back(obb_json(o));
        }
        if (!record.target_obbs.empty()) {
            obbs["target"] = Json::array();
            for (const auto& o : record.target_obbs) obbs["target"].push_back(obb_json(o));
        }
        info["obbs"] = std::move(obbs);
    }
    if (record.axis) {
        info["axis"] = Json{{"mode", record.axis->mode ? Json(*record.axis->mode) : Json(nullptr)},
                            {"degraded", record.axis->degraded ? Json(*record.axis->degraded) : Json(nullptr)}};
    }
    if (record.raycast) {
        auto segments = [](const std::vector<std::pair<Point3, Point3>>& list) {
            Json out = Json::array();
            for (const auto& [a, b] : list) out.push_back(Json::array({point_json(a), point_json(b)}));
            return out;
        };
        info["raycast"] = Json{{"planned", record.raycast->planned},
                               {"cast", record.raycast->cast},
                               {"hit", record.raycast->hit},
                               {"hit_segments", segments(record.raycast->hit_segments)},
                               {"blocked_segments", segments(record.raycast->blocked_segments)}};
    }
    if (record.zone) {
        info["zone"] = Json{{"side", record.zone->side},     {"leaf", record.zone->leaf},
                            {"width", record.zone->width},   {"depth", record.zone->depth},
                            {"height", record.zone->height}};
    }
    if (!record.axes.empty()) {
        Json axes = Json::array();
        for (const auto& a : record.axes) {
            Json entry{{"center", point_json(a.center)}, {"direction", point_json(a.direction)}, {"length", a.length}};
            if (a.label) entry["label"] = *a.label;
            axes.push_back(std::move(entry));
        }
        info["axes"] = std::move(axes);
    }
    return info;
}

Json to_json(const ResultRecord& record) {
    Json flags = Json::array();
    if (record.flags.degraded) flags.push_back("degraded");
    if (record.flags.gross_element) flags.push_back("gross_element");
    if (record.flags.fallback_source) flags.push_back("fallback_source");
    return Json{{"source", to_json(record.source)},
                {"target", record.target ? to_json(*record.target) : Json(nullptr)},
                {"status", record.status},
                {"info", info_to_json(record)},
                {"flags", std::move(flags)}};
}

Json to_json(const PhaseStats& stats) {
    Json phases = Json::array();
    for (const auto& p : stats.phases) {
        phases.push_back(Json{{"phase", p.phase}, {"in", p.in}, {"out", p.out}, {"seconds", p.seconds}});
    }
    return Json{{"rule", stats.rule},
                {"phases", std::move(phases)},
                {"total_seconds", stats.total_seconds},
                {"summary", stats.summary()}};
}

static const char* severity_name(Severity s) {
    switch (s) {
        case Severity::Info: return "info";
        case Severity::Warning: return "warning";
        case Severity::Error: return "error";
    }
    return "?";
}

Json to_json(const Diagnostics& diagnostics) {
    Json out = Json::array();
    for (const auto& d : diagnostics.entries) {
        out.push_back(Json{{"severity", severity_name(d.severity)},
                           {"code", d.code},
                           {"message", d.message},
                           {"element", d.element ? to_json(*d.element) : Json(nullptr)}});
    }
    return out;
}

Json to_json(const RunResult& result) {
    Json results = Json::array();
    for (const auto& r : result.results) results.push_back(to_json(r));
    return Json{{"result_schema_version", kResultSchemaVersion},
                {"results", std::move(results)},
                {"stats", to_json(result.stats)},
                {"diagnostics", to_json(result.diagnostics)}};
}

void sort_results(std::vector<ResultRecord>& results) {
    std::stable_sort(results.begin(), results.end(), [](const ResultRecord& a, const ResultRecord& b) {
        if (a.source != b.source) return a.source < b.source;
        if (a.target.has_value() != b.target.has_value()) return !a.target.has_value();
        if (!a.target) return false;
        return *a.target < *b.target;
    });
}

}  // namespace ifcclash
