#include "IfcSource.h"

#include "../core/Errors.h"
#include "../geometry/MeshMeasures.h"

#include <ifcgeom/element.h>
#include <ifcgeom/filter.h>
#include <ifcgeom/iterator.h>
#include <ifcgeom/kernel_registry.h>
#include <ifcgeom/tree.h>
#include <ifcgeom/tree_registry.h>
#include <ifcparse/file.h>

#include <Eigen/Dense>

#include <BRepTools.hxx>
#include <BRep_Builder.hxx>

#include <sstream>

#include <algorithm>
#include <cmath>
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
    for (auto& m : meshes_) m.clear();
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

void IfcSource::convert(uint32_t file_index, const std::vector<int>& entity_ids, Variant variant) {
    if (entity_ids.empty()) return;
    FileEntry& entry = *files_[file_index];

    // The defaults of ifcopenshell.geom.settings(), the geometry library of
    // the Python iterator / kernel ("opencascade"), plus the flags of the
    // variant (USE_WORLD_COORDS; USE_PYTHON_OPENCASCADE sets SERIALIZED and
    // world coordinates, see ifcopenshell.geom.settings.set).
    ifcopenshell::geom::settings settings;
    if (variant != Variant::MeshLocal) {
        settings.get<ifcopenshell::geom::settings::UseWorldCoords>().value = true;
    }
    if (variant == Variant::BrepWorld) {
        settings.get<ifcopenshell::geom::settings::IteratorOutput>().value = ifcopenshell::geom::settings::SERIALIZED;
    }
    auto kernel = ifcopenshell::geom::kernels::construct(entry.file.get(), "opencascade", settings);

    ifcopenshell::geom::instance_id_filter include(true, false,
                                                   std::set<int>(entity_ids.begin(), entity_ids.end()));
    std::vector<ifcopenshell::geom::filter_function> filters{include};

    int threads = options_.iterator_threads;
    if (threads <= 0) threads = static_cast<int>(std::max(1u, std::thread::hardware_concurrency()));

    ifcopenshell::geom::iterator iterator(std::move(kernel), settings, entry.file.get(), filters, threads);
    if (!iterator.initialize()) return;  // nothing with geometry in the batch

    const int v = static_cast<int>(variant);
    do {
        std::unique_ptr<ifcopenshell::geom::element> element = iterator.get();
        if (variant == Variant::BrepWorld) {
            auto* serialized = dynamic_cast<ifcopenshell::geom::serialized_element*>(element.get());
            if (!serialized) continue;
            const ElementKey key{file_index, serialized->id(), serialized->guid()};
            breps_[key] = serialized->geometry().brep_data();
            continue;
        }
        auto* triangulation = dynamic_cast<ifcopenshell::geom::triangulation_element*>(element.get());
        if (!triangulation) continue;
        element.release();
        std::shared_ptr<ifcopenshell::geom::triangulation_element> owned(triangulation);

        ElementKey key{file_index, owned->id(), owned->guid()};
        auto mesh = make_mesh(std::move(owned));

        if (variant == Variant::MeshLocal) {
            ElementBoxes boxes;
            boxes.aabb = geometry::aabb_of(mesh->world_verts);
            boxes.obb = geometry::obb_of(mesh->world_verts);
            boxes.uncertainty = 0.0;
            boxes_[key] = boxes;
        }
        meshes_[v][key] = std::move(mesh);
    } while (iterator.next());
}

void IfcSource::prepare(const std::vector<ElementKey>& keys, Variant variant) {
    std::lock_guard<std::mutex> lock(mutex_);
    const int v = static_cast<int>(variant);
    std::map<uint32_t, std::vector<int>> pending;
    for (const auto& key : keys) {
        if (!covers(key) || converted_[v].count(key)) continue;
        converted_[v].insert(key);
        pending[key.file_index].push_back(key.entity_id);
    }
    for (auto& [file_index, ids] : pending) convert(file_index, ids, variant);
}

std::optional<ElementBoxes> IfcSource::boxes(const ElementKey& key) {
    prepare({key});
    std::lock_guard<std::mutex> lock(mutex_);
    auto it = boxes_.find(key);
    if (it == boxes_.end()) return std::nullopt;
    return it->second;
}

std::shared_ptr<const Mesh> IfcSource::mesh(const ElementKey& key) { return mesh(key, Variant::MeshLocal); }

std::shared_ptr<const Mesh> IfcSource::mesh(const ElementKey& key, Variant variant) {
    if (variant == Variant::BrepWorld) return nullptr;
    prepare({key}, variant);
    std::lock_guard<std::mutex> lock(mutex_);
    const auto& cache = meshes_[static_cast<int>(variant)];
    auto it = cache.find(key);
    if (it == cache.end()) return nullptr;
    return it->second;
}

std::optional<TopoDS_Shape> IfcSource::brep(const ElementKey& key) {
    prepare({key}, Variant::BrepWorld);
    std::string data;
    {
        std::lock_guard<std::mutex> lock(mutex_);
        auto it = breps_.find(key);
        if (it == breps_.end()) return std::nullopt;
        data = it->second;
    }
    // As ifcopenshell.geom.occ_utils.create_shape_from_serialization
    // (breptools.ReadFromString).
    TopoDS_Shape shape;
    BRep_Builder builder;
    std::istringstream in(data);
    BRepTools::Read(shape, in, builder);
    if (shape.IsNull()) return std::nullopt;
    return shape;
}

// ---------------------------------------------------------------- ray trees

namespace {

class IfcRayTreeImpl final : public RayTree {
public:
    std::unique_ptr<ifcopenshell::geom::tree> tree;
    std::vector<std::unique_ptr<ifcopenshell::geom::native_element>> elements;  // kept alive with the tree

    size_t hits(const Point3& origin, const Point3& direction, double length) const override {
        return tree->select_ray(origin, direction, length).size();
    }
};

}  // namespace

std::unique_ptr<RayTree> IfcSource::build_ray_tree(const std::vector<ElementKey>& keys) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto out = std::make_unique<IfcRayTreeImpl>();
    out->tree = ifcopenshell::geom::trees::construct("opencascade.brep");  // clash_utils.RAY_TREE_BACKEND
    if (!out->tree) throw ConfigError("IfcOpenShell tree backend not available: opencascade.brep");
    std::map<uint32_t, std::set<int>> by_file;
    for (const auto& k : keys)
        if (covers(k)) by_file[k.file_index].insert(k.entity_id);
    for (const auto& [file_index, ids] : by_file) {
        FileEntry& entry = *files_[file_index];
        // add_elements_to_ray_tree: USE_PYTHON_OPENCASCADE settings, get_native()
        ifcopenshell::geom::settings settings;
        settings.get<ifcopenshell::geom::settings::UseWorldCoords>().value = true;
        settings.get<ifcopenshell::geom::settings::IteratorOutput>().value = ifcopenshell::geom::settings::SERIALIZED;
        auto kernel = ifcopenshell::geom::kernels::construct(entry.file.get(), "opencascade", settings);
        ifcopenshell::geom::instance_id_filter include(true, false, ids);
        std::vector<ifcopenshell::geom::filter_function> filters{include};
        int threads = options_.iterator_threads;
        if (threads <= 0) threads = static_cast<int>(std::max(1u, std::thread::hardware_concurrency()));
        ifcopenshell::geom::iterator iterator(std::move(kernel), settings, entry.file.get(), filters, threads);
        if (!iterator.initialize()) continue;
        do {
            auto native = iterator.get_native();
            if (!native) continue;
            out->tree->add_element(native.get());
            out->elements.push_back(std::move(native));
        } while (iterator.next());
    }
    return out;
}

// ---------------------------------------------------------------- IFC queries

express::entity IfcSource::entity(const ElementKey& key) {
    if (key.file_index >= files_.size()) return {};
    try {
        express::base b = files_[key.file_index]->file->instance_by_id(key.entity_id);
        return b ? b.as<express::entity>() : express::entity();
    } catch (const std::exception&) {
        return {};
    }
}

std::string IfcSource::ifc_class(const ElementKey& key) {
    auto e = entity(key);
    return e ? e.declaration().name() : std::string();
}

namespace {

bool has_attribute(const express::entity& e, const char* name) {
    const auto* decl = e.declaration().as_entity();
    if (!decl) return false;
    try {
        decl->attribute_index(name);
        return true;
    } catch (const std::exception&) {
        return false;
    }
}

std::optional<std::string> string_attribute(const express::entity& e, const char* name) {
    if (!has_attribute(e, name)) return std::nullopt;
    auto value = e.get(name);
    if (value.isNull()) return std::nullopt;
    const std::string s = static_cast<std::string>(value);
    if (s.empty()) return std::nullopt;
    return s;
}

express::entity entity_attribute(const express::entity& e, const char* name) {
    if (!has_attribute(e, name)) return {};
    auto value = e.get(name);
    if (value.isNull()) return {};
    express::base b = static_cast<express::base>(value);
    return b ? b.as<express::entity>() : express::entity();
}

std::vector<express::entity> entity_list_attribute(const express::entity& e, const char* name) {
    std::vector<express::entity> out;
    if (!has_attribute(e, name)) return out;
    auto value = e.get(name);
    if (value.isNull()) return out;
    for (const auto& b : static_cast<std::vector<express::base>>(value)) {
        if (b) out.push_back(b.as<express::entity>());
    }
    return out;
}

std::vector<express::entity> inverse(const express::entity& e, const char* name) {
    try {
        return e.get_inverse(name);
    } catch (const std::exception&) {
        return {};
    }
}

// ifcopenshell.util.element.get_material (should_inherit=True)
express::entity material_of(const express::entity& element, bool inherit) {
    for (const auto& rel : inverse(element, "HasAssociations")) {
        if (rel.declaration().is("IfcRelAssociatesMaterial")) return entity_attribute(rel, "RelatingMaterial");
    }
    if (!inherit) return {};
    // ifcopenshell.util.element.get_type: IsTypedBy (IFC4) or IsDefinedBy (IFC2X3)
    express::entity type;
    for (const auto& rel : inverse(element, "IsTypedBy")) {
        type = entity_attribute(rel, "RelatingType");
        if (type) break;
    }
    if (!type) {
        for (const auto& rel : inverse(element, "IsDefinedBy")) {
            if (rel.declaration().is("IfcRelDefinesByType")) {
                type = entity_attribute(rel, "RelatingType");
                if (type) break;
            }
        }
    }
    if (type && !(type == element) && !inverse(type, "HasAssociations").empty()) return material_of(type, false);
    return {};
}

}  // namespace

std::vector<std::string> IfcSource::material_names(const ElementKey& key) {
    std::lock_guard<std::mutex> lock(mutex_);
    std::vector<std::string> names;
    auto element = entity(key);
    if (!element) return names;
    express::entity material;
    try {
        material = material_of(element, true);
    } catch (const std::exception&) {
        return names;
    }
    if (!material) return names;
    if (material.declaration().is("IfcMaterial")) {
        if (auto n = string_attribute(material, "Name")) names.push_back(*n);
        return names;
    }
    if (material.declaration().is("IfcMaterialLayerSetUsage")) material = entity_attribute(material, "ForLayerSet");
    if (material && material.declaration().is("IfcMaterialLayerSet")) {
        for (const auto& layer : entity_list_attribute(material, "MaterialLayers")) {
            auto m = entity_attribute(layer, "Material");
            if (m) {
                if (auto n = string_attribute(m, "Name")) names.push_back(*n);
            }
        }
        return names;
    }
    if (material && material.declaration().is("IfcMaterialConstituentSet")) {
        for (const auto& c : entity_list_attribute(material, "MaterialConstituents")) {
            auto m = entity_attribute(c, "Material");
            if (m) {
                if (auto n = string_attribute(m, "Name")) names.push_back(*n);
            }
        }
        return names;
    }
    if (material) {
        if (auto n = string_attribute(material, "Name")) names.push_back(*n);
    }
    return names;
}

namespace {

using M4 = std::array<double, 16>;  // row-major

M4 identity4() { return {1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1}; }

M4 matmul(const M4& a, const M4& b) {
    M4 c{};
    for (int i = 0; i < 4; ++i)
        for (int j = 0; j < 4; ++j) {
            double s = 0.0;
            for (int k = 0; k < 4; ++k) s += a[4 * i + k] * b[4 * k + j];
            c[4 * i + j] = s;
        }
    return c;
}

std::array<double, 3> ratios(const express::entity& direction, std::array<double, 3> fallback) {
    if (!direction) return fallback;
    const auto values = static_cast<std::vector<double>>(direction.get("DirectionRatios"));
    std::array<double, 3> out{0.0, 0.0, 0.0};
    for (size_t i = 0; i < values.size() && i < 3; ++i) out[i] = values[i];
    return out;
}

// ifcopenshell.util.placement.a2p
M4 a2p(std::array<double, 3> o, std::array<double, 3> z, std::array<double, 3> x) {
    auto nrm = [](std::array<double, 3> v) {
        const double n = std::sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2]);
        return std::array<double, 3>{v[0] / n, v[1] / n, v[2] / n};
    };
    x = nrm(x);
    z = nrm(z);
    std::array<double, 3> y{z[1] * x[2] - z[2] * x[1], z[2] * x[0] - z[0] * x[2], z[0] * x[1] - z[1] * x[0]};
    y = nrm(y);
    // r rows = x, y, z, o; returned transposed: columns = x, y, z, o
    return {x[0], y[0], z[0], o[0], x[1], y[1], z[1], o[1], x[2], y[2], z[2], o[2], 0, 0, 0, 1};
}

M4 axis2placement(const express::entity& p) {
    const std::string cls = p.declaration().name();
    std::array<double, 3> o{0, 0, 0}, z{0, 0, 1}, x{1, 0, 0};
    express::entity location = entity_attribute(p, "Location");
    std::vector<double> coords;
    if (location && has_attribute(location, "Coordinates"))
        coords = static_cast<std::vector<double>>(location.get("Coordinates"));
    for (size_t i = 0; i < coords.size() && i < 3; ++i) o[i] = coords[i];
    if (cls == "IfcAxis2Placement3D" || cls == "IfcAxis2PlacementLinear") {
        z = ratios(entity_attribute(p, "Axis"), {0, 0, 1});
        x = ratios(entity_attribute(p, "RefDirection"), {1, 0, 0});
    } else if (cls == "IfcAxis2Placement2D") {
        x = ratios(entity_attribute(p, "RefDirection"), {1, 0, 0});
    } else if (cls == "IfcAxis1Placement") {
        z = ratios(entity_attribute(p, "Axis"), {0, 0, 1});
    }
    return a2p(o, z, x);
}

M4 local_placement_of(const express::entity& placement) {
    if (!placement) return identity4();
    if (!placement.declaration().is("IfcLocalPlacement")) return identity4();
    const express::entity rel = entity_attribute(placement, "PlacementRelTo");
    const M4 parent = rel ? local_placement_of(rel) : identity4();
    const express::entity relative = entity_attribute(placement, "RelativePlacement");
    return relative ? matmul(parent, axis2placement(relative)) : parent;
}

}  // namespace

std::array<double, 16> IfcSource::local_placement(const ElementKey& key) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto e = entity(key);
    if (!e) return identity4();
    try {
        return local_placement_of(entity_attribute(e, "ObjectPlacement"));
    } catch (const std::exception&) {
        return identity4();
    }
}

std::optional<std::string> IfcSource::door_operation_type(const ElementKey& key) {
    std::lock_guard<std::mutex> lock(mutex_);
    auto door = entity(key);
    if (!door) return std::nullopt;
    std::optional<std::string> operation;
    try {
        for (const auto& rel : inverse(door, "IsTypedBy")) {
            auto type = entity_attribute(rel, "RelatingType");
            if (type && type.declaration().is("IfcDoorType") && has_attribute(type, "OperationType")) {
                auto value = type.get("OperationType");
                if (!value.isNull()) {
                    const auto s = static_cast<std::string>(value);
                    if (!s.empty()) operation = s;  // the last one wins, as in Python
                }
            }
        }
        if (!operation) {
            for (const auto& rel : inverse(door, "IsDefinedBy")) {
                if (!rel.declaration().is("IfcRelDefinesByProperties")) continue;
                auto props = entity_attribute(rel, "RelatingPropertyDefinition");
                // IfcDoorPanelProperties has no OperationType attribute (the
                // Python code raises there): nothing to read.
                if (props && props.declaration().is("IfcDoorPanelProperties") && has_attribute(props, "OperationType")) {
                    auto value = props.get("OperationType");
                    if (!value.isNull()) operation = static_cast<std::string>(value);
                }
            }
        }
    } catch (const std::exception&) {
    }
    return operation;
}

}  // namespace ifcclash
