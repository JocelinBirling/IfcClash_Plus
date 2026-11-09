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
#include "IfcQueries.h"
#include "IfcRayTree.h"

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
namespace express {
class entity;
}

namespace ifcclash {

struct IfcSourceOptions {
    // Threads of the IfcOpenShell iterator (0 = hardware concurrency, like
    // the multiprocessing.cpu_count() of the Python engine). The output does
    // not depend on it.
    int iterator_threads = 0;
};

class IfcSource final : public GeometrySource, public IfcQueries, public RayTreeService {
public:
    // Throws ConfigError when a file cannot be opened.
    IfcSource(const std::vector<std::filesystem::path>& paths, IfcSourceOptions options = {});
    ~IfcSource() override;

    std::string_view name() const override { return "ifc"; }
    bool supports(Level) const override { return true; }
    bool covers(const ElementKey& key) const override;

    void prepare(const std::vector<ElementKey>& keys, Variant variant = Variant::MeshLocal) override;
    std::optional<ElementBoxes> boxes(const ElementKey& key) override;
    std::shared_ptr<const Mesh> mesh(const ElementKey& key) override;
    std::shared_ptr<const Mesh> mesh(const ElementKey& key, Variant variant) override;
    std::optional<TopoDS_Shape> brep(const ElementKey& key) override;
    TriangleClashService* triangle_clash() override { return clash_tree_.get(); }
    std::shared_ptr<const void> triangulation_native(const ElementKey& key, const Mesh& world_mesh) override;
    IfcQueries* ifc_queries() override { return this; }
    RayTreeService* ray_trees() override { return this; }
    std::unique_ptr<RayTree> build_ray_tree(const std::vector<ElementKey>& keys) override;
    std::vector<std::string> material_names(const ElementKey& key) override;
    std::string ifc_class(const ElementKey& key) override;
    std::array<double, 16> local_placement(const ElementKey& key) override;
    std::optional<std::string> door_operation_type(const ElementKey& key) override;
    // The entity of a key (null when unknown), for the IFC queries.
    express::entity entity(const ElementKey& key);

    size_t file_count() const { return files_.size(); }
    // Elements converted by the iterator since the opening, all variants
    // (the _triang rules must leave it unchanged).
    size_t converted_elements() const { return converted_elements_; }
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
    void convert(uint32_t file_index, const std::vector<int>& entity_ids, Variant variant);

    IfcSourceOptions options_;
    // Declared before the tree: the tree refers to the entities of the files
    // and is destroyed first.
    std::vector<std::unique_ptr<FileEntry>> files_;
    std::unique_ptr<IfcClashTree> clash_tree_;

    std::mutex mutex_;
    size_t converted_elements_ = 0;
    // Per variant (MeshLocal, MeshWorld): the triangulations.
    std::unordered_map<ElementKey, std::shared_ptr<const Mesh>, ElementKeyHash> meshes_[kVariantCount];
    // BrepWorld: the serialized OCC B-Rep (parsed afresh at each brep()).
    std::unordered_map<ElementKey, std::string, ElementKeyHash> breps_;
    // The raw boxes, from the MeshLocal triangulation.
    std::unordered_map<ElementKey, ElementBoxes, ElementKeyHash> boxes_;
    // Elements already submitted to the iterator, per variant (with or
    // without geometry).
    std::unordered_set<ElementKey, ElementKeyHash> converted_[kVariantCount];
};

}  // namespace ifcclash
