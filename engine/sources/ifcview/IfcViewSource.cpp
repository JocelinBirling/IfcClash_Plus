#include "IfcViewSource.h"

#include "third_party/IfcViewReader.h"

#include "../../core/Errors.h"
#include "../../geometry/MeshMeasures.h"

#include <NCollection_Array1.hxx>
#include <gp_Pnt.hxx>

#include <algorithm>
#include <cmath>
#include <fstream>

namespace ifcclash {

Freshness freshness_from_string(const std::string& s) {
    if (s == "mtime") return Freshness::Mtime;
    if (s == "trust") return Freshness::Trust;
    if (s == "reject") return Freshness::Reject;
    throw ConfigError("unknown ifcview_freshness '" + s + "' (expected mtime, trust or reject)");
}

std::filesystem::path IfcViewSource::locate(const std::filesystem::path& ifc_path,
                                            const std::optional<std::filesystem::path>& cache_dir) {
    const std::filesystem::path dir = cache_dir ? *cache_dir : ifc_path.parent_path();
    for (const auto& candidate : {dir / (ifc_path.stem().string() + ".ifcview"),
                                  dir / (ifc_path.filename().string() + ".ifcview")}) {
        if (std::filesystem::exists(candidate)) return candidate;
    }
    return {};
}

namespace {

// Manifest written next to a .ifcview produced by the engine (SPEC
// "Fraîcheur"). Only the tessellation fields are used for now.
struct Manifest {
    std::optional<double> linear_deflection;
};

std::optional<Manifest> read_manifest(const std::filesystem::path& ifcview) {
    std::ifstream in(ifcview.string() + ".manifest.json");
    if (!in) return std::nullopt;
    Manifest m;
    try {
        const Json j = Json::parse(in);
        if (j.contains("linear_deflection")) m.linear_deflection = j["linear_deflection"].get<double>();
    } catch (const std::exception&) {
        return std::nullopt;
    }
    return m;
}

// Linear deflection of the IFC triangulation (ifcopenshell.geom.settings()
// default, the settings of IfcSource).
constexpr double kIfcLinearDeflection = 0.001;

void transform_point(const double* m, const double in[3], double out[3]) {
    for (int r = 0; r < 3; ++r) out[r] = m[r] * in[0] + m[4 + r] * in[1] + m[8 + r] * in[2] + m[12 + r];
}

}  // namespace

IfcViewSource::IfcViewSource(const std::vector<IfcViewFile>& files, const IfcViewOptions& options,
                             Diagnostics& diagnostics) {
    for (const auto& file : files) {
        const std::string name = file.ifcview_path.filename().string();
        auto reject = [&](const std::string& why) {
            diagnostics.add(Severity::Warning, "ifcview_rejected", name + ": " + why + "; boxes from the IFC");
        };

        // ---- Freshness
        const auto manifest = read_manifest(file.ifcview_path);
        std::error_code ec;
        if (options.freshness == Freshness::Reject && !manifest) {
            reject("no manifest (ifcview_freshness=reject)");
            continue;
        }
        if (options.freshness == Freshness::Mtime && !manifest) {
            const auto t_view = std::filesystem::last_write_time(file.ifcview_path, ec);
            const auto t_ifc = std::filesystem::last_write_time(file.ifc_path, ec);
            if (ec || t_view < t_ifc) {
                reject("older than the IFC (ifcview_freshness=mtime)");
                continue;
            }
            diagnostics.add(Severity::Info, "ifcview_no_manifest",
                            name + ": no manifest, accepted because it is newer than the IFC");
        }

        // ---- Format (version, readability)
        auto view = readIfcViewMetadata(file.ifcview_path.string());
        if (!view) {
            reject("unreadable, corrupted or not version " + std::to_string(IFCVIEW_VERSION));
            continue;
        }
        const IfcViewData& meta = view->meta;

        const double linear = manifest && manifest->linear_deflection ? *manifest->linear_deflection
                                                                       : options.linear_deflection;

        // object_id -> element record
        std::unordered_map<uint32_t, const ElementTableRecord*> by_object;
        for (const auto& e : meta.elements) by_object[e.object_id] = &e;

        struct Acc {
            Bnd_Box aabb;
            std::vector<gp_Pnt> corners;
            double size = 0.0;   // largest local extent
            double scale = 0.0;  // largest coordinate magnitude (float rounding)
        };
        std::unordered_map<uint32_t, Acc> acc;
        for (const auto& inst : meta.instances) {
            if (inst.mesh_id >= meta.meshes.size()) continue;
            const MeshInfo& mesh = meta.meshes[inst.mesh_id];
            Acc& a = acc[inst.object_id];
            for (int c = 0; c < 8; ++c) {
                const double local[3] = {(c & 1) ? mesh.local_aabb_max[0] : mesh.local_aabb_min[0],
                                         (c & 2) ? mesh.local_aabb_max[1] : mesh.local_aabb_min[1],
                                         (c & 4) ? mesh.local_aabb_max[2] : mesh.local_aabb_min[2]};
                double world[3];
                transform_point(inst.placement_transformation, local, world);
                a.aabb.Add(gp_Pnt(world[0], world[1], world[2]));
                a.corners.emplace_back(world[0], world[1], world[2]);
                for (int k = 0; k < 3; ++k) a.scale = std::max({a.scale, std::abs(local[k]), std::abs(world[k])});
            }
            for (int k = 0; k < 3; ++k)
                a.size = std::max(a.size, double(mesh.local_aabb_max[k]) - double(mesh.local_aabb_min[k]));
        }

        auto& entries = files_[file.file_index];
        for (auto& [object_id, a] : acc) {
            auto it = by_object.find(object_id);
            if (it == by_object.end()) continue;
            const ElementTableRecord& rec = *it->second;
            Entry entry;
            entry.global_id = meta.string_table.substr(rec.guid_offset, rec.guid_length);
            entry.boxes.aabb = a.aabb;
            NCollection_Array1<gp_Pnt> points(1, static_cast<int>(a.corners.size()));
            for (int i = 0; i < static_cast<int>(a.corners.size()); ++i) points.SetValue(i + 1, a.corners[i]);
            entry.boxes.obb.ReBuild(points);
            // Tessellation gap (both linear deflections) + float storage
            // of the local boxes and of the rotation.
            entry.boxes.uncertainty = linear + kIfcLinearDeflection + 1e-6 * (1.0 + a.scale + a.size);
            entries[rec.ifc_id] = std::move(entry);
        }
        diagnostics.add(Severity::Info, "ifcview_accepted",
                        name + ": " + std::to_string(entries.size()) + " elements, boxes from the .ifcview");
    }
}

size_t IfcViewSource::element_count() const {
    size_t n = 0;
    for (const auto& [i, entries] : files_) n += entries.size();
    return n;
}

bool IfcViewSource::covers(const ElementKey& key) const {
    auto f = files_.find(key.file_index);
    if (f == files_.end()) return false;
    auto e = f->second.find(key.entity_id);
    if (e == f->second.end()) return false;
    // Same STEP id but another GlobalId: the .ifcview describes another
    // version of the file for this element -> fallback on the IFC.
    return key.global_id.empty() || e->second.global_id == key.global_id;
}

std::optional<ElementBoxes> IfcViewSource::boxes(const ElementKey& key) {
    if (!covers(key)) return std::nullopt;
    const Entry& e = files_.at(key.file_index).at(key.entity_id);
    ElementBoxes out = e.boxes;
    // The raw boxes carry the uncertainty in the pipeline: the rules inflate
    // by it (default volumes), so the raw ones stay the .ifcview ones.
    return out;
}

}  // namespace ifcclash
