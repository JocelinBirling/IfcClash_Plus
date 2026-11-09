#include "ViewTriangles.h"

#include "../core/Errors.h"
#include "../sources/ifcview/third_party/IfcViewReader.h"

#include <algorithm>
#include <atomic>
#include <cstdio>
#include <cstring>
#include <exception>
#include <mutex>
#include <string>
#include <thread>
#include <unordered_map>

namespace ifcclash::triang {

namespace {

// The decoded mesh of the .ifcview, in its local frame.
struct LocalMesh {
    std::vector<double> verts;  // x, y, z
    std::vector<int> faces;     // mesh-local indices, three per triangle
};

class File {
public:
    explicit File(const std::filesystem::path& path) : f_(std::fopen(path.string().c_str(), "rb")) {}
    ~File() {
        if (f_) std::fclose(f_);
    }
    File(const File&) = delete;
    File& operator=(const File&) = delete;

    // One zstd frame at the absolute offset `off`: `comp` bytes on disk,
    // `raw` bytes once decompressed into dst.
    bool frame(uint64_t off, uint64_t comp, uint64_t raw, uint8_t* dst) {
        if (raw == 0) return comp == 0;
        if (!f_ || fseeko(f_, static_cast<off_t>(off), SEEK_SET) != 0) return false;
        buffer_.resize(static_cast<size_t>(comp));
        if (comp && std::fread(buffer_.data(), 1, buffer_.size(), f_) != buffer_.size()) return false;
        return decompressIfcViewFrame(buffer_.data(), buffer_.size(), dst, static_cast<size_t>(raw));
    }

private:
    FILE* f_;
    std::vector<uint8_t> buffer_;
};

// The vertices and LOD0 triangles of one mesh, from its chunk-local slices
// (IfcOpenShell ViewportCore: positions dequantized against the local
// AABB, indices checked against the vertex count).
// The vertices sharing a quantized position are welded: the viewer splits
// them per face (one normal each), which opens a closed solid as far as
// the indices go, and the clash tree only measures penetrations on closed
// (manifold) meshes.
void decode_mesh(const MeshInfo& info, const uint8_t* vbytes, const uint32_t* indices, LocalMesh& out) {
    std::unordered_map<uint64_t, int> welded;
    std::vector<int> remap(info.vertex_count);
    out.verts.clear();
    out.verts.reserve(size_t(info.vertex_count) * 3);
    for (uint32_t v = 0; v < info.vertex_count; ++v) {
        const uint8_t* p = vbytes + size_t(v) * INSTANCED_VERTEX_STRIDE_BYTES + INSTANCED_VERTEX_POS_OFFSET;
        uint16_t q[3];
        std::memcpy(q, p, sizeof q);
        const uint64_t key = (uint64_t(q[0]) << 32) | (uint64_t(q[1]) << 16) | uint64_t(q[2]);
        auto [it, fresh] = welded.emplace(key, static_cast<int>(out.verts.size() / 3));
        remap[v] = it->second;
        if (!fresh) continue;
        for (int k = 0; k < 3; ++k) {
            const double lo = info.local_aabb_min[k];
            const double hi = info.local_aabb_max[k];
            out.verts.push_back(lo + (double(q[k]) / 65535.0) * (hi - lo));
        }
    }
    out.faces.clear();
    out.faces.reserve(info.index_count);
    for (uint32_t i = 0; i + 2 < info.index_count; i += 3) {
        const uint32_t a = indices[i], b = indices[i + 1], c = indices[i + 2];
        if (a >= info.vertex_count || b >= info.vertex_count || c >= info.vertex_count) continue;
        const int ra = remap[a], rb = remap[b], rc = remap[c];
        if (ra == rb || rb == rc || ra == rc) continue;  // collapsed by the quantization
        out.faces.insert(out.faces.end(), {ra, rb, rc});
    }
}

}  // namespace

std::vector<std::shared_ptr<const Mesh>> decode_elements(const ViewGeometry& view,
                                                         const std::vector<const std::vector<ViewInstance>*>& elements,
                                                         unsigned threads) {
    std::vector<std::shared_ptr<const Mesh>> out(elements.size());

    // ---- The meshes and chunks the elements need
    std::vector<char> needed(view.meshes.size(), 0);
    for (const auto* instances : elements) {
        if (!instances) continue;
        for (const auto& inst : *instances) {
            if (inst.mesh_id < needed.size()) needed[inst.mesh_id] = 1;
        }
    }
    std::vector<size_t> chunk_ids;
    for (size_t c = 0; c < view.chunks.size(); ++c) {
        const auto& chunk = view.chunks[c];
        const size_t end = std::min<size_t>(size_t(chunk.first_mesh) + chunk.mesh_count, needed.size());
        for (size_t m = chunk.first_mesh; m < end; ++m) {
            if (needed[m]) {
                chunk_ids.push_back(c);
                break;
            }
        }
    }

    // ---- Decode the chunks (one file handle per thread)
    std::vector<LocalMesh> local(view.meshes.size());
    std::atomic<size_t> next{0};
    std::atomic<bool> failed{false};
    auto work = [&]() {
        File file(view.path);
        std::vector<uint8_t> vbytes;
        std::vector<uint32_t> indices;
        for (;;) {
            const size_t k = next.fetch_add(1);
            if (k >= chunk_ids.size() || failed.load()) return;
            const IfcViewChunk& c = view.chunks[chunk_ids[k]];
            vbytes.assign(size_t(c.v_raw_size), 0);
            indices.assign(size_t(c.i_raw_size / sizeof(uint32_t)), 0);
            const uint64_t base = view.geometry_section_offset;
            if (!file.frame(base + c.v_comp_off, c.v_comp_size, c.v_raw_size, vbytes.data()) ||
                !file.frame(base + c.i_comp_off, c.i_comp_size, c.i_raw_size,
                            reinterpret_cast<uint8_t*>(indices.data()))) {
                failed.store(true);
                return;
            }
            uint64_t base_vertex = 0, first_index = 0;
            const size_t end = std::min<size_t>(size_t(c.first_mesh) + c.mesh_count, view.meshes.size());
            for (size_t m = c.first_mesh; m < end; ++m) {
                const MeshInfo& info = view.meshes[m];
                const uint64_t v_end = (base_vertex + info.vertex_count) * INSTANCED_VERTEX_STRIDE_BYTES;
                const uint64_t i_end = first_index + info.index_count;
                if (v_end > vbytes.size() || i_end > indices.size()) {
                    failed.store(true);
                    return;
                }
                if (needed[m]) {
                    decode_mesh(info, vbytes.data() + base_vertex * INSTANCED_VERTEX_STRIDE_BYTES,
                                indices.data() + first_index, local[m]);
                }
                base_vertex += info.vertex_count;
                first_index += info.index_count;
            }
        }
    };
    const size_t workers = std::max<size_t>(1, std::min<size_t>(threads, chunk_ids.size()));
    std::vector<std::thread> pool;
    for (size_t w = 1; w < workers; ++w) pool.emplace_back(work);
    work();
    for (auto& t : pool) t.join();
    if (failed.load()) {
        throw ConfigError(view.path.filename().string() + ": a geometry chunk cannot be read or decompressed");
    }

    // ---- Place the instances: one world mesh per element
    for (size_t e = 0; e < elements.size(); ++e) {
        if (!elements[e]) continue;
        auto mesh = std::make_shared<Mesh>();
        for (const auto& inst : *elements[e]) {
            if (inst.mesh_id >= local.size()) continue;
            const LocalMesh& lm = local[inst.mesh_id];
            if (lm.faces.empty()) continue;
            const int offset = static_cast<int>(mesh->world_verts.size() / 3);
            const auto& m = inst.placement;
            for (size_t v = 0; v + 2 < lm.verts.size(); v += 3) {
                const double x = lm.verts[v], y = lm.verts[v + 1], z = lm.verts[v + 2];
                for (int r = 0; r < 3; ++r)
                    mesh->world_verts.push_back(m[r] * x + m[4 + r] * y + m[8 + r] * z + m[12 + r]);
            }
            for (int f : lm.faces) mesh->faces.push_back(f + offset);
        }
        if (!mesh->faces.empty()) out[e] = std::move(mesh);
    }
    return out;
}

}  // namespace ifcclash::triang
