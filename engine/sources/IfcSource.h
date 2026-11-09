// IfcClash_Plus engine — the IFC source: IfcParse + IfcGeom (SPEC "Sources de géométrie").
//
// The reference source, always available. It parses each IFC once per
// Session and converts the geometry on demand: only the elements a run asks
// for are triangulated, in one iterator pass per batch, with the same
// settings and the same geometry library ("opencascade") as the Python
// engine (ifcopenshell.geom.settings() defaults).
#pragma once

#include "GeometrySource.h"
#include "IfcClashTree.h"

#include "../core/Result.h"

#include <filesystem>
#include <map>
#include <memory>
#include <mutex>
#include <string>
#include <unordered_map>
#include <unordered_set>
#include <vector>

namespace ifcopenshell {
class file;
}

namespace ifcclash {

struct IfcSourceOptions {
    // Threads of the IfcOpenShell iterator (0 = hardware concurrency, like
    // the multiprocessing.cpu_count() of the Python engine). The output does
    // not depend on it.
    int iterator_threads = 0;
};

class IfcSource final : public GeometrySource {
public:
    // Throws ConfigError when a file cannot be opened.
    IfcSource(const std::vector<std::filesystem::path>& paths, IfcSourceOptions options = {});
    ~IfcSource() override;

    std::string_view name() const override { return "ifc"; }
    bool supports(Level) const override { return true; }
    bool covers(const ElementKey& key) const override;

    void prepare(const std::vector<ElementKey>& keys) override;
    std::optional<ElementBoxes> boxes(const ElementKey& key) override;
    std::shared_ptr<const Mesh> mesh(const ElementKey& key) override;
    TriangleClashService* triangle_clash() override { return clash_tree_.get(); }

    size_t file_count() const { return files_.size(); }
    const std::filesystem::path& path(uint32_t file_index) const;

    // Selection resolution. A GlobalId shared by several entities resolves
    // to all of them, with a "duplicate_global_id" diagnostic: duplicates are
    // signalled, never merged. An unknown GlobalId / id is a diagnostic too.
    std::vector<ElementKey> resolve_global_ids(uint32_t file_index,
                                               const std::vector<std::string>& global_ids,
                                               Diagnostics& diagnostics);
    std::vector<ElementKey> resolve_entity_ids(uint32_t file_index,
                                               const std::vector<int>& entity_ids,
                                               Diagnostics& diagnostics);
    // Completes a key given by GlobalId or by id (whichever is set).
    std::optional<ElementKey> resolve(const ElementKey& partial, Diagnostics& diagnostics);

private:
    struct FileEntry;

    void index_global_ids(FileEntry& entry);
    void triangulate(uint32_t file_index, const std::vector<int>& entity_ids);

    IfcSourceOptions options_;
    // Declared before the tree: the tree refers to the entities of the files
    // and is destroyed first.
    std::vector<std::unique_ptr<FileEntry>> files_;
    std::unique_ptr<IfcClashTree> clash_tree_;

    std::mutex mutex_;
    std::unordered_map<ElementKey, std::shared_ptr<const Mesh>, ElementKeyHash> meshes_;
    std::unordered_map<ElementKey, ElementBoxes, ElementKeyHash> boxes_;
    // Elements already submitted to the iterator (with or without geometry).
    std::unordered_set<ElementKey, ElementKeyHash> converted_;
};

}  // namespace ifcclash
