#include "IfcSource.h"

#include "../core/Errors.h"
#include "../geometry/MeshMeasures.h"

#include <ifcgeom/element.h>
#include <ifcgeom/filter.h>
#include <ifcgeom/iterator.h>
#include <ifcgeom/kernel_registry.h>
#include <ifcparse/file.h>

#include <Eigen/Dense>

#include <algorithm>
#include <set>
#include <thread>

namespace ifcclash {

struct IfcSource::FileEntry {
    std::filesystem::path path;
    std::unique_ptr<ifcopenshell::file> file;
    bool guid_index_built = false;
    std::unordered_map<std::string, std::vector<int>> by_guid;
};

namespace {

std::string global_id_of(const express::base& instance) {
    try {
        if (instance.declaration().is("IfcRoot")) {
            return static_cast<std::string>(instance.get_attribute_value(0));
        }
    } catch (const std::exception&) {
    }
    return {};
}

bool is_product(const express::base& instance) {
    return instance.declaration().is("IfcProduct");
}

std::shared_ptr<const Mesh> make_mesh(std::shared_ptr<ifcopenshell::geom::triangulation_element> element) {
    auto mesh = std::make_shared<Mesh>();
    const auto& geometry = element->geometry();
    mesh->local_verts = geometry.verts();
    mesh->faces = geometry.faces();

    const auto& matrix = element->transformation().data();
    const Eigen::Matrix4d m = matrix->ccomponents();
    std::copy(m.data(), m.data() + 16, mesh->placement.begin());

    // Same transformation as the clash tree (apply_matrix_to_flat_verts).
    mesh->world_verts.reserve(mesh->local_verts.size());
    Eigen::Vector3d v;
    for (size_t i = 0; i + 2 < mesh->local_verts.size(); i += 3) {
        v << mesh->local_verts[i], mesh->local_verts[i + 1], mesh->local_verts[i + 2];
        const Eigen::Vector4d w = m * v.homogeneous();
        mesh->world_verts.push_back(w(0));
        mesh->world_verts.push_back(w(1));
        mesh->world_verts.push_back(w(2));
    }
    mesh->native = std::static_pointer_cast<const void>(
        std::shared_ptr<const ifcopenshell::geom::triangulation_element>(std::move(element)));
    return mesh;
}

}  // namespace

IfcSource::IfcSource(const std::vector<std::filesystem::path>& paths, IfcSourceOptions options)
    : options_(options) {
    for (const auto& path : paths) {
        if (!std::filesystem::exists(path)) {
            throw ConfigError("IFC file not found: " + path.string());
        }
        auto entry = std::make_unique<FileEntry>();
        entry->path = path;
        entry->file = std::make_unique<ifcopenshell::file>(path.string());
        if (!entry->file->good()) {
            throw ConfigError("IFC file could not be parsed: " + path.string());
        }
        files_.push_back(std::move(entry));
    }
    clash_tree_ = std::make_unique<IfcClashTree>();
}

IfcSource::~IfcSource() {
    // The tree, the meshes and their native elements refer to the files:
    // release them first.
    clash_tree_.reset();
    meshes_.clear();
}

const std::filesystem::path& IfcSource::path(uint32_t file_index) const {
    return files_.at(file_index)->path;
}

bool IfcSource::covers(const ElementKey& key) const {
    return key.file_index < files_.size();
}

void IfcSource::index_global_ids(FileEntry& entry) {
    if (entry.guid_index_built) return;
    for (const auto& instance : entry.file->instances_by_type("IfcRoot")) {
        const std::string gid = global_id_of(instance);
        if (!gid.empty()) entry.by_guid[gid].push_back(instance.id());
    }
    for (auto& [gid, ids] : entry.by_guid) std::sort(ids.begin(), ids.end());
    entry.guid_index_built = true;
}

std::vector<ElementKey> IfcSource::resolve_global_ids(uint32_t file_index,
                                                      const std::vector<std::string>& global_ids,
                                                      Diagnostics& diagnostics) {
    if (file_index >= files_.size()) {
        throw ConfigError("selection refers to file index " + std::to_string(file_index) +
                          " but the session has " + std::to_string(files_.size()) + " file(s)");
    }
    FileEntry& entry = *files_[file_index];
    index_global_ids(entry);
    std::vector<ElementKey> keys;
    for (const auto& gid : global_ids) {
        auto it = entry.by_guid.find(gid);
        if (it == entry.by_guid.end()) {
            diagnostics.add(Severity::Warning, "unknown_global_id",
                            "GlobalId " + gid + " not found in " + entry.path.filename().string());
            continue;
        }
        if (it->second.size() > 1) {
            diagnostics.add(Severity::Warning, "duplicate_global_id",
                            "GlobalId " + gid + " is shared by " + std::to_string(it->second.size()) +
                                " entities in " + entry.path.filename().string() +
                                "; every one is kept");
        }
        for (int id : it->second) {
            express::base instance = entry.file->instance_by_id(id);
            if (!is_product(instance)) continue;
            keys.push_back(ElementKey{file_index, id, gid});
        }
    }
    return keys;
}

std::vector<ElementKey> IfcSource::resolve_entity_ids(uint32_t file_index,
                                                      const std::vector<int>& entity_ids,
                                                      Diagnostics& diagnostics) {
    if (file_index >= files_.size()) {
        throw ConfigError("selection refers to file index " + std::to_string(file_index) +
                          " but the session has " + std::to_string(files_.size()) + " file(s)");
    }
    FileEntry& entry = *files_[file_index];
    std::vector<ElementKey> keys;
    for (int id : entity_ids) {
        express::base instance;
        try {
            instance = entry.file->instance_by_id(id);
        } catch (const std::exception&) {
        }
        if (!instance) {
            diagnostics.add(Severity::Warning, "unknown_entity_id",
                            "#" + std::to_string(id) + " not found in " + entry.path.filename().string());
            continue;
        }
        if (!is_product(instance)) {
            diagnostics.add(Severity::Warning, "not_a_product",
                            "#" + std::to_string(id) + " is not an IfcProduct: ignored");
            continue;
        }
        keys.push_back(ElementKey{file_index, id, global_id_of(instance)});
    }
    return keys;
}

std::optional<ElementKey> IfcSource::resolve(const ElementKey& partial, Diagnostics& diagnostics) {
    std::vector<ElementKey> keys =
        partial.entity_id != 0
            ? resolve_entity_ids(partial.file_index, {partial.entity_id}, diagnostics)
            : resolve_global_ids(partial.file_index, {partial.global_id}, diagnostics);
    if (keys.empty()) return std::nullopt;
    return keys.front();
}

void IfcSource::triangulate(uint32_t file_index, const std::vector<int>& entity_ids) {
    if (entity_ids.empty()) return;
    FileEntry& entry = *files_[file_index];

    // The defaults of ifcopenshell.geom.settings(), the geometry library of
    // the Python iterator / kernel ("opencascade").
    ifcopenshell::geom::settings settings;
    auto kernel = ifcopenshell::geom::kernels::construct(entry.file.get(), "opencascade", settings);

    ifcopenshell::geom::instance_id_filter include(true, false,
                                                   std::set<int>(entity_ids.begin(), entity_ids.end()));
    std::vector<ifcopenshell::geom::filter_function> filters{include};

    int threads = options_.iterator_threads;
    if (threads <= 0) threads = static_cast<int>(std::max(1u, std::thread::hardware_concurrency()));

    ifcopenshell::geom::iterator iterator(std::move(kernel), settings, entry.file.get(), filters, threads);
    if (!iterator.initialize()) return;  // nothing with geometry in the batch

    do {
        std::unique_ptr<ifcopenshell::geom::element> element = iterator.get();
        auto* triangulation = dynamic_cast<ifcopenshell::geom::triangulation_element*>(element.get());
        if (!triangulation) continue;
        element.release();
        std::shared_ptr<ifcopenshell::geom::triangulation_element> owned(triangulation);

        ElementKey key{file_index, owned->id(), owned->guid()};
        auto mesh = make_mesh(std::move(owned));

        ElementBoxes boxes;
        boxes.aabb = geometry::aabb_of(mesh->world_verts);
        boxes.obb = geometry::obb_of(mesh->world_verts);
        boxes.uncertainty = 0.0;

        boxes_[key] = boxes;
        meshes_[key] = std::move(mesh);
    } while (iterator.next());
}

void IfcSource::prepare(const std::vector<ElementKey>& keys) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::map<uint32_t, std::vector<int>> pending;
    for (const auto& key : keys) {
        if (!covers(key) || converted_.count(key)) continue;
        converted_.insert(key);
        pending[key.file_index].push_back(key.entity_id);
    }
    for (auto& [file_index, ids] : pending) triangulate(file_index, ids);
}

std::optional<ElementBoxes> IfcSource::boxes(const ElementKey& key) {
    prepare({key});
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = boxes_.find(key);
    if (it == boxes_.end()) return std::nullopt;
    return it->second;
}

std::shared_ptr<const Mesh> IfcSource::mesh(const ElementKey& key) {
    prepare({key});
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = meshes_.find(key);
    if (it == meshes_.end()) return nullptr;
    return it->second;
}

}  // namespace ifcclash
