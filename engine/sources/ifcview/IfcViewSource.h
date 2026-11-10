// IfcClash_Plus engine — the optional .ifcview source (SPEC "Le format .ifcview",
// migration step 6).
//
// Reads the metadata of a .ifcview (BonsaiViewer cache, IfcOpenShell
// src/ifcviewer format v19) once at the opening and gives the broad and mid
// phases their boxes without converting any IFC geometry. The narrow phase
// still asks the IFC (GeometryProvider): the results do not depend on this
// source, only the time does.
//
// Boxes: per element, the union of its instances' local mesh AABBs placed by
// the double placement; the OBB is rebuilt on the same corners. Both are
// inflated by `uncertainty`, which covers the difference between the
// .ifcview tessellation and the IFC one (see IfcViewOptions).
#pragma once

#include "../GeometrySource.h"
#include "../../core/Result.h"
#include "../../triang/mesh/ViewTriangles.h"

#include <filesystem>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

namespace ifcclash {

enum class Freshness {
    Mtime,   // the .ifcview must be newer than the IFC (default, SPEC)
    Trust,   // accept any readable .ifcview
    Reject,  // never accept a .ifcview without a manifest
};

Freshness freshness_from_string(const std::string& s);

struct IfcViewOptions {
    Freshness freshness = Freshness::Mtime;
    // Linear deflection of the producer when no manifest says otherwise.
    // The IfcOpenShell default is 0.001 m; BonsaiViewer may be coarser,
    // hence a prudent default. The mesher keeps every chord within the
    // linear deflection of the surface (the angular criterion only adds
    // triangles), so two tessellations of one surface differ by at most
    // the sum of their linear deflections.
    double linear_deflection = 0.01;   // m
};

// One IFC file and its .ifcview.
struct IfcViewFile {
    uint32_t file_index = 0;
    std::filesystem::path ifc_path;
    std::filesystem::path ifcview_path;
};

class IfcViewSource final : public GeometrySource {
public:
    // The .ifcview of each file is validated (format version, readability,
    // freshness, GlobalId consistency). A rejected file gets a diagnostic
    // and is simply not covered (per-file fallback on the IFC).
    IfcViewSource(const std::vector<IfcViewFile>& files, const IfcViewOptions& options, Diagnostics& diagnostics);

    std::string_view name() const override { return "ifcview"; }
    bool supports(Level level) const override { return level == Level::Boxes; }
    bool covers(const ElementKey& key) const override;

    std::optional<ElementBoxes> boxes(const ElementKey& key) override;
    std::shared_ptr<const Mesh> mesh(const ElementKey&) override { return nullptr; }

    // Variant::Triangles (engine/triang): the world triangles of the
    // .ifcview, decoded on demand.
    bool accepts_file(uint32_t file_index) const override { return files_.count(file_index) != 0; }
    std::vector<std::shared_ptr<const Mesh>> stored_meshes(const std::vector<ElementKey>& keys,
                                                           unsigned threads) override;

    size_t accepted_files() const { return files_.size(); }
    size_t element_count() const;

    // The default path of the .ifcview of an IFC: foo.ifc -> foo.ifcview
    // (IfcOpenShell ifcViewPathFor), else foo.ifc.ifcview; in cache_dir when
    // given. Empty when none exists.
    static std::filesystem::path locate(const std::filesystem::path& ifc_path,
                                        const std::optional<std::filesystem::path>& cache_dir);

private:
    struct Entry {
        std::string global_id;
        ElementBoxes boxes;
        std::vector<triang::ViewInstance> instances;  // its meshes, placed
    };
    // file_index -> (STEP id -> boxes)
    std::unordered_map<uint32_t, std::unordered_map<int, Entry>> files_;
    // file_index -> what decoding the triangles needs
    std::unordered_map<uint32_t, triang::ViewGeometry> geometry_;
};

}  // namespace ifcclash
