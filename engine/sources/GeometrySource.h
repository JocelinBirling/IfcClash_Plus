// IfcClash_Plus engine — the interface of a geometry source (SPEC "Interface de source").
//
// The rules never know where the geometry comes from: they ask the
// GeometryProvider, which picks a source per level and per element.
#pragma once

#include "../core/ElementKey.h"
#include "../core/Geometry.h"

#include <TopoDS_Shape.hxx>

#include <memory>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace ifcclash {

enum class Level { Boxes, Mesh, BRep };

class TriangleClashService;  // IFC-specific narrow tests (sources/IfcClashTree.h)
class IfcQueries;            // IFC semantic queries (sources/IfcQueries.h)
class RayTreeService;        // IFC ray trees (sources/IfcRayTree.h)

class GeometrySource {
public:
    virtual ~GeometrySource() = default;
    virtual std::string_view name() const = 0;
    virtual bool supports(Level) const = 0;
    virtual bool covers(const ElementKey&) const = 0;

    // Batch hint: the elements a run is about to ask for. A source that
    // converts geometry (IfcSource) converts them in one pass.
    virtual void prepare(const std::vector<ElementKey>& /*keys*/, Variant /*variant*/ = Variant::MeshLocal) {}

    // An element without computable geometry has no boxes / mesh:
    // std::nullopt / nullptr (never an exception).
    virtual std::optional<ElementBoxes> boxes(const ElementKey&) = 0;
    virtual std::shared_ptr<const Mesh> mesh(const ElementKey&) = 0;
    // The other triangulation variants (MeshWorld).
    virtual std::shared_ptr<const Mesh> mesh(const ElementKey& key, Variant variant) {
        return variant == Variant::MeshLocal ? mesh(key) : nullptr;
    }
    // The B-Rep in world coordinates (Variant::BrepWorld), a FRESH shape at
    // every call: the rules mesh it (BRepMesh) as the Python engine does on
    // its own fresh shape, and must not see the triangulation of another.
    virtual std::optional<TopoDS_Shape> brep(const ElementKey&) { return std::nullopt; }

    // The exact triangle clash queries of IfcOpenShell (Intersection,
    // Clearance, Collision). Only a source holding IfcOpenShell elements
    // provides them.
    virtual TriangleClashService* triangle_clash() { return nullptr; }

    // ---- Variant::Triangles (engine/triang): a source that stores its own
    // tessellation (the .ifcview) gives the world triangles of the elements
    // it covers, decoded on `threads` threads; one mesh per key (nullptr:
    // not covered or no triangle).
    virtual bool accepts_file(uint32_t /*file_index*/) const { return false; }
    virtual std::vector<std::shared_ptr<const Mesh>> stored_meshes(const std::vector<ElementKey>& keys,
                                                                   unsigned /*threads*/) {
        return std::vector<std::shared_ptr<const Mesh>>(keys.size());
    }
    // The IfcOpenShell element (triangulation_element) of a mesh given in
    // world coordinates, for the clash tree: only the IFC source, which
    // holds the IFC products, can build it. nullptr otherwise.
    virtual std::shared_ptr<const void> triangulation_native(const ElementKey& /*key*/, const Mesh& /*world_mesh*/) {
        return nullptr;
    }
    virtual IfcQueries* ifc_queries() { return nullptr; }
    virtual RayTreeService* ray_trees() { return nullptr; }
};

}  // namespace ifcclash
