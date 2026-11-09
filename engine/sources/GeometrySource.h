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

class GeometrySource {
public:
    virtual ~GeometrySource() = default;
    virtual std::string_view name() const = 0;
    virtual bool supports(Level) const = 0;
    virtual bool covers(const ElementKey&) const = 0;

    // Batch hint: the elements a run is about to ask for. A source that
    // converts geometry (IfcSource) converts them in one pass.
    virtual void prepare(const std::vector<ElementKey>& /*keys*/) {}

    // An element without computable geometry has no boxes / mesh:
    // std::nullopt / nullptr (never an exception).
    virtual std::optional<ElementBoxes> boxes(const ElementKey&) = 0;
    virtual std::shared_ptr<const Mesh> mesh(const ElementKey&) = 0;
    virtual std::optional<TopoDS_Shape> brep(const ElementKey&) { return std::nullopt; }

    // The exact triangle clash queries of IfcOpenShell (Intersection,
    // Clearance, Collision). Only a source holding IfcOpenShell elements
    // provides them.
    virtual TriangleClashService* triangle_clash() { return nullptr; }
};

}  // namespace ifcclash
