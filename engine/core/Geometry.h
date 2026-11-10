// IfcClash_Plus engine — the geometry data shared by sources, provider and rules.
// Metres everywhere (SPEC "Unités"): the conversion happens when the IFC is read.
#pragma once

#include <Bnd_Box.hxx>
#include <Bnd_OBB.hxx>

#include <array>
#include <memory>
#include <vector>

namespace ifcclash {

// The geometry variants the Python rules ask IfcOpenShell for, each with
// the ifcopenshell.geom.settings() defaults plus:
enum class Variant {
    MeshLocal = 0,  // triangulation in the element frame (no flag)
    MeshWorld = 1,  // triangulation, USE_WORLD_COORDS
    BrepWorld = 2,  // OCC B-Rep, USE_PYTHON_OPENCASCADE (= SERIALIZED + world coords)
    // The triangles of the _triang rules (engine/triang), world
    // coordinates: the .ifcview triangles (no IFC conversion) or the IFC
    // triangulation (MeshWorld), per SessionOptions::triangle_source. Served
    // by the GeometryProvider, never asked to a source directly.
    Triangles = 3,
};
// The variants an IFC source converts (Triangles excluded).
inline constexpr int kVariantCount = 3;

// The raw bounding volumes of one element, computed once per Session.
struct ElementBoxes {
    Bnd_Box aabb;
    Bnd_OBB obb;
    // 0 for the IFC; quantisation + deflection for a .ifcview (step 6).
    // The broad and mid volumes are inflated by it: a box coming from an
    // approximate source may keep too many pairs, never lose one.
    double uncertainty = 0.0;
};

// A triangulated element.
struct Mesh {
    // Vertices in the element's local frame, exactly as produced by the
    // geometry iterator (flat x, y, z). Kept for the measures that the
    // Python engine computes in that frame (volume).
    std::vector<double> local_verts;
    // Triangles, three vertex indices each.
    std::vector<int> faces;
    // Local -> world placement, column-major 4x4 (Eigen layout).
    std::array<double, 16> placement{1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1};
    // Vertices in world coordinates (flat x, y, z).
    std::vector<double> world_verts;

    // Opaque handle on the native element of the source that produced the
    // mesh (an IfcOpenShell triangulation_element for the IfcSource). It lets
    // the IFC-specific narrow tests (IfcClashTree) reuse the exact data the
    // Python engine feeds to its clash tree. Null for other sources.
    std::shared_ptr<const void> native;

    size_t vertex_count() const { return world_verts.size() / 3; }
    size_t triangle_count() const { return faces.size() / 3; }
};

}  // namespace ifcclash
