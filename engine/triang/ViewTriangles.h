// IfcClash_Plus engine — the triangles of a .ifcview (the _triang rules).
//
// A .ifcview (BonsaiViewer cache, IfcOpenShell src/ifcviewer format v19)
// stores instanced meshes: per mesh, its vertices in local coordinates,
// quantized on 16 bits against the mesh's local AABB (12 bytes per vertex),
// and its triangles (LOD0, mesh-local indices); per instance, the mesh and
// the element it belongs to, with its placement. The geometry is split in
// zstd-compressed chunks: a chunk holds the vertices of a contiguous range
// of meshes, then their LOD0 indices, then their LOD1 indices.
//
// decode_elements reads the chunks the requested elements need (and only
// them), decodes their meshes and places every instance: one world mesh per
// element. No IFC is read.
//
// Precision: a position is min + q/65535 * (max - min), so within
// (max - min) / 131070 of the tessellated surface (0.08 mm for a 10 m mesh),
// on top of the tessellation deflection of the producer.
#pragma once

#include "../core/Geometry.h"
#include "../sources/ifcview/third_party/IfcViewFormat.h"

#include <array>
#include <cstddef>
#include <cstdint>
#include <filesystem>
#include <memory>
#include <vector>

namespace ifcclash::triang {

// One instance of an element: its mesh and its placement (local -> world,
// column-major 4x4, the .ifcview placement_transformation).
struct ViewInstance {
    uint32_t mesh_id = 0;
    std::array<double, 16> placement{};
};

// What decoding needs of one .ifcview (kept by IfcViewSource).
struct ViewGeometry {
    std::filesystem::path path;
    uint64_t geometry_section_offset = 0;  // absolute file offset of the chunks
    std::vector<MeshInfo> meshes;
    std::vector<IfcViewChunk> chunks;
};

// The world mesh of each element (the instances of elements[i], placed),
// chunks decoded on up to `threads` threads. Out[i] is nullptr when the
// element has no triangle. Throws ConfigError when a needed chunk cannot be
// read or decompressed (a corrupted .ifcview).
std::vector<std::shared_ptr<const Mesh>> decode_elements(const ViewGeometry& view,
                                                         const std::vector<const std::vector<ViewInstance>*>& elements,
                                                         unsigned threads);

}  // namespace ifcclash::triang
