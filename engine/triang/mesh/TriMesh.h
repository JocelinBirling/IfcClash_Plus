// IfcClash_Plus engine — a world triangle mesh made usable by the _triang
// rules (engine/triang/mesh): welded, consistently wound, with the data of
// each triangle and a BVH on demand.
//
// The triangulations met in IFC files are often open (the IFC triangulation
// of Duplex Mechanical: 32 closed elements out of 524) and often wound
// inwards (Revit MEP). A TriMesh never trusts the input winding:
//  - the vertices sharing a position are welded (exact equality);
//  - the triangles collapsed by the weld are dropped;
//  - the winding is made consistent across shared edges, component by
//    component, then turned outwards (positive signed volume about the
//    component centroid);
//  - `closed` tells whether every edge is shared by exactly two triangles
//    of opposite directions: only then are the volume and the inside test
//    exact.
#pragma once

#include "../../core/Geometry.h"
#include "../kernels/TriangleTests.h"
#include "../spatial/BoxTree.h"

#include <Bnd_Box.hxx>

#include <memory>
#include <mutex>
#include <vector>

namespace ifcclash::triang {

class TriMesh {
public:
    // From a world mesh (Mesh::world_verts / faces).
    explicit TriMesh(const Mesh& mesh);
    TriMesh(std::vector<double> verts, std::vector<int> faces);

    const std::vector<double>& verts() const { return verts_; }  // flat x, y, z
    const std::vector<int>& faces() const { return faces_; }     // 3 per triangle, consistent winding
    size_t vertex_count() const { return verts_.size() / 3; }
    size_t triangle_count() const { return faces_.size() / 3; }

    P3 vertex(int i) const { return {verts_[3 * size_t(i)], verts_[3 * size_t(i) + 1], verts_[3 * size_t(i) + 2]}; }
    // The three corners of triangle t.
    void corners(size_t t, P3& a, P3& b, P3& c) const {
        a = vertex(faces_[3 * t]);
        b = vertex(faces_[3 * t + 1]);
        c = vertex(faces_[3 * t + 2]);
    }
    const P3& normal(size_t t) const { return normals_[t]; }  // unit, after the winding repair
    double area(size_t t) const { return areas_[t]; }
    const Bnd_Box& box(size_t t) const { return boxes_[t]; }
    const Bnd_Box& bounds() const { return bounds_; }

    double total_area() const { return total_area_; }
    // Every edge shared by exactly two triangles of opposite directions.
    bool closed() const { return closed_; }
    // Number of connected components (by shared edges).
    int components() const { return components_; }
    // Signed volume after the winding repair (exact for a closed mesh,
    // indicative otherwise).
    double volume() const { return volume_; }

    // The BVH of the triangle boxes, built on first use (thread-safe).
    const BoxTree& tree() const;

private:
    // raw_faces: the vertex indices of each kept triangle before the weld
    // (the topology of the source), or empty.
    void build(const std::vector<int>& raw_faces = {});
    bool inside_by_parity(const P3& p) const;

    std::vector<double> verts_;
    std::vector<int> faces_;
    std::vector<P3> normals_;
    std::vector<double> areas_;
    std::vector<Bnd_Box> boxes_;
    Bnd_Box bounds_;
    double total_area_ = 0.0;
    double volume_ = 0.0;
    bool closed_ = false;
    int components_ = 0;
    mutable std::once_flag tree_once_;
    mutable std::unique_ptr<BoxTree> tree_;
};

}  // namespace ifcclash::triang
