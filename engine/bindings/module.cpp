// IfcClash_Plus engine — pybind11 bindings: a thin layer on api/ only.
//
//   import _ifcclash_engine as engine
//   with engine.Session(ifc_paths=[...], geometry_cache="auto") as session:
//       result = session.run(rule_type="Clearance", params={"clearance": 0.05},
//                            selections={"source": [{"file_index": 0, "global_ids": [...]}],
//                                        "target": [...]},
//                            mode="verdicts")
//
// The GIL is released during run / evaluate_pairs; the progress callback
// takes it back.
#include "../api/Engine.h"
#include "../geometry/Faces.h"
#include "../geometry/MeshMeasures.h"
#include "../triang/surface/Visibility.h"
#include "../triang/kernels/TriangleTests.h"
#include "../triang/mesh/TriMesh.h"

#include <BRepTools.hxx>
#include <BRep_Builder.hxx>
#include <TopoDS_Shape.hxx>

#include <chrono>
#include <sstream>

#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/stl/filesystem.h>

#include <memory>

namespace py = pybind11;
using namespace ifcclash;

namespace {

py::object to_py(const Json& j) {
    switch (j.type()) {
        case Json::value_t::null: return py::none();
        case Json::value_t::boolean: return py::bool_(j.get<bool>());
        case Json::value_t::number_integer: return py::int_(j.get<long long>());
        case Json::value_t::number_unsigned: return py::int_(j.get<unsigned long long>());
        case Json::value_t::number_float: return py::float_(j.get<double>());
        case Json::value_t::string: return py::str(j.get<std::string>());
        case Json::value_t::array: {
            py::list out;
            for (const auto& item : j) out.append(to_py(item));
            return std::move(out);
        }
        case Json::value_t::object: {
            py::dict out;
            for (auto it = j.begin(); it != j.end(); ++it) out[py::str(it.key())] = to_py(it.value());
            return std::move(out);
        }
        default: return py::none();
    }
}

Json from_py(py::handle h) {
    if (h.is_none()) return nullptr;
    if (py::isinstance<py::bool_>(h)) return h.cast<bool>();
    if (py::isinstance<py::int_>(h)) return h.cast<long long>();
    if (py::isinstance<py::float_>(h)) return h.cast<double>();
    if (py::isinstance<py::str>(h)) return h.cast<std::string>();
    if (py::isinstance<py::dict>(h)) {
        Json out = Json::object();
        for (auto item : h.cast<py::dict>()) out[py::str(item.first).cast<std::string>()] = from_py(item.second);
        return out;
    }
    if (py::isinstance<py::list>(h) || py::isinstance<py::tuple>(h)) {
        Json out = Json::array();
        for (auto item : h) out.push_back(from_py(item));
        return out;
    }
    // numpy scalars and other numbers
    if (py::hasattr(h, "__float__")) return h.cast<double>();
    throw ConfigError("unsupported value in the parameters: " + py::repr(h).cast<std::string>());
}

std::vector<FileSelection> file_selections(py::handle slot) {
    std::vector<FileSelection> out;
    if (slot.is_none()) return out;
    for (auto item : slot) {
        auto d = item.cast<py::dict>();
        FileSelection f;
        f.file_index = d["file_index"].cast<uint32_t>();
        if (d.contains("global_ids")) f.global_ids = d["global_ids"].cast<std::vector<std::string>>();
        if (d.contains("entity_ids")) f.entity_ids = d["entity_ids"].cast<std::vector<int>>();
        out.push_back(std::move(f));
    }
    return out;
}

Selections selections_from(py::object selections) {
    Selections s;
    if (selections.is_none()) return s;
    auto d = selections.cast<py::dict>();
    for (auto item : d) {
        const auto key = py::str(item.first).cast<std::string>();
        if (key == "source") s.source = file_selections(item.second);
        else if (key == "target") s.target = file_selections(item.second);
        else if (key == "context") s.context = file_selections(item.second);
        else throw ConfigError("unknown selection slot '" + key + "' (expected source, target, context)");
    }
    return s;
}

ElementKey key_from(py::handle h) {
    auto d = h.cast<py::dict>();
    ElementKey k;
    k.file_index = d["file_index"].cast<uint32_t>();
    if (d.contains("entity_id")) k.entity_id = d["entity_id"].cast<int>();
    if (d.contains("global_id")) k.global_id = d["global_id"].cast<std::string>();
    return k;
}

RunRequest request_from(const std::string& rule_type, py::object params, py::object selections,
                        const std::string& mode, bool prefilter) {
    RunRequest r;
    r.rule_type = rule_type;
    r.params = params.is_none() ? Json::object() : from_py(params);
    r.selections = selections_from(selections);
    r.mode = run_mode_from_string(mode);
    r.prefilter = prefilter;
    return r;
}

py::dict result_to_py(const RunResult& result) {
    py::dict out = to_py(to_json(result));
    py::list display;
    for (const auto& item : result.display.items) {
        py::dict d;
        d["category"] = item.category;
        d["element"] = item.element ? to_py(to_json(*item.element)) : py::none();
        const py::ssize_t nv = static_cast<py::ssize_t>(item.vertices.size() / 3);
        py::array_t<double> vertices({nv, py::ssize_t(3)});
        std::copy(item.vertices.begin(), item.vertices.end(), vertices.mutable_data());
        const py::ssize_t width = item.category == "segment" ? 2 : 3;
        const py::ssize_t ni = static_cast<py::ssize_t>(item.indices.size()) / width;
        py::array_t<int32_t> indices({ni, width});
        std::copy(item.indices.begin(), item.indices.end(), indices.mutable_data());
        d["vertices"] = vertices;
        d["indices"] = indices;
        display.append(d);
    }
    out["display"] = display;
    return out;
}

class PyProgress final : public ProgressSink {
public:
    explicit PyProgress(py::object callback) : callback_(std::move(callback)) {}
    void report(std::string_view phase, size_t done, size_t total) override {
        if (callback_.is_none()) return;
        py::gil_scoped_acquire gil;
        callback_(std::string(phase), done, total);
    }

private:
    py::object callback_;
};

// The Python face of a Session: close() releases the parsed files and the
// cache at once (the context manager calls it).
class PySession {
public:
    PySession(std::vector<std::filesystem::path> paths, const std::string& geometry_cache,
              std::optional<std::filesystem::path> cache_dir, bool write_cache, int iterator_threads,
              std::vector<std::filesystem::path> ifcview_paths, const std::string& ifcview_freshness,
              double ifcview_linear_deflection, int rule_threads, const std::string& triangle_source) {
        SessionOptions options;
        options.geometry_cache = cache_policy_from_string(geometry_cache);
        options.cache_dir = std::move(cache_dir);
        options.ifcview_paths = std::move(ifcview_paths);
        options.ifcview_freshness = ifcview_freshness;
        options.ifcview_linear_deflection = ifcview_linear_deflection;
        options.write_cache = write_cache;
        options.iterator_threads = iterator_threads;
        options.rule_threads = rule_threads;
        options.triangle_source = triangle_source;
        py::gil_scoped_release release;
        session_ = std::make_unique<Session>(std::move(paths), options);
    }

    Session& session() {
        if (!session_) throw ConfigError("the session is closed");
        return *session_;
    }

    void close() { session_.reset(); }
    bool closed() const { return !session_; }

private:
    std::unique_ptr<Session> session_;
};


// ---- Benchmark entry points (scripts/benchmark_extreme_faces.py): one
// geometry function on one mesh or B-Rep, timed inside C++ (the numpy and
// BRep text conversions are excluded).
std::vector<double> flat_vertices(const py::array_t<double, py::array::c_style | py::array::forcecast>& a) {
    if (a.ndim() != 2 || a.shape(1) != 3) throw ConfigError("vertices must be an (n, 3) array");
    return {a.data(), a.data() + a.size()};
}
std::vector<int> flat_faces(const py::array_t<int, py::array::c_style | py::array::forcecast>& a) {
    if (a.ndim() != 2 || a.shape(1) != 3) throw ConfigError("faces must be an (m, 3) array");
    return {a.data(), a.data() + a.size()};
}
template <class F>
py::tuple timed(F&& f, int repeat) {
    using clock = std::chrono::steady_clock;
    repeat = std::max(1, repeat);
    decltype(f()) out;
    const auto t0 = clock::now();
    {
        py::gil_scoped_release release;
        for (int r = 0; r < repeat; ++r) out = f();
    }
    const double seconds = std::chrono::duration<double>(clock::now() - t0).count() / repeat;
    return py::make_tuple(out, seconds);
}

void bind_bench(py::module_& m) {
    auto b = m.def_submodule("bench", "Timed geometry functions, for the benchmarks.");
    b.def(
        "visible_triangles",
        [](py::array_t<double, py::array::c_style | py::array::forcecast> v,
           py::array_t<int, py::array::c_style | py::array::forcecast> f, double side, int repeat) {
            auto verts = flat_vertices(v);
            auto faces = flat_faces(f);
            return timed([&] { return triang::visible_triangles(verts, faces, side); }, repeat);
        },
        py::arg("vertices"), py::arg("faces"), py::arg("side"), py::arg("repeat") = 1,
        "triang::visible_triangles (sampled coverage, BVH): (triangle indices, seconds per call).");
    b.def(
        "visible_triangles_raster",
        [](py::array_t<double, py::array::c_style | py::array::forcecast> v,
           py::array_t<int, py::array::c_style | py::array::forcecast> f, double side, double cell, int max_side,
           int min_side, int repeat) {
            auto verts = flat_vertices(v);
            auto faces = flat_faces(f);
            triang::HeightMapOptions o;
            o.cell = cell;
            o.min_side = min_side;
            o.max_side = max_side;
            return timed([&] { return triang::visible_triangles_raster(verts, faces, side, o); }, repeat);
        },
        py::arg("vertices"), py::arg("faces"), py::arg("side"), py::arg("cell") = 0.01,
        py::arg("max_side") = 1024, py::arg("min_side") = 64, py::arg("repeat") = 1,
        "triang::visible_triangles_raster (height map): (triangle indices, seconds per call).");
    b.def(
        "visible_triangles_auto",
        [](py::array_t<double, py::array::c_style | py::array::forcecast> v,
           py::array_t<int, py::array::c_style | py::array::forcecast> f, double side, size_t from_triangles,
           int repeat) {
            auto verts = flat_vertices(v);
            auto faces = flat_faces(f);
            return timed([&] { return triang::visible_triangles_auto(verts, faces, side, from_triangles); },
                         repeat);
        },
        py::arg("vertices"), py::arg("faces"), py::arg("side"),
        py::arg("from_triangles") = triang::kHeightMapFromTriangles, py::arg("repeat") = 1,
        "triang::visible_triangles_auto (sampled under from_triangles triangles, height map from it): "
        "(triangle indices, seconds per call).");
    b.def(
        "tri_mesh",
        [](py::array_t<double, py::array::c_style | py::array::forcecast> v,
           py::array_t<int, py::array::c_style | py::array::forcecast> f) {
            const triang::TriMesh m(flat_vertices(v), flat_faces(f));
            py::array_t<double> verts({py::ssize_t(m.vertex_count()), py::ssize_t(3)});
            std::copy(m.verts().begin(), m.verts().end(), verts.mutable_data());
            py::array_t<int32_t> faces({py::ssize_t(m.triangle_count()), py::ssize_t(3)});
            std::copy(m.faces().begin(), m.faces().end(), faces.mutable_data());
            py::dict d;
            d["verts"] = verts;
            d["faces"] = faces;
            d["closed"] = m.closed();
            d["components"] = m.components();
            d["volume"] = m.volume();
            d["area"] = m.total_area();
            return d;
        },
        py::arg("vertices"), py::arg("faces"), "triang::TriMesh of a mesh: welded, repaired faces and facts.");
    b.def(
        "extreme_faces",
        [](py::array_t<double, py::array::c_style | py::array::forcecast> v,
           py::array_t<int, py::array::c_style | py::array::forcecast> f, std::array<double, 3> direction,
           int repeat) {
            auto verts = flat_vertices(v);
            auto faces = flat_faces(f);
            return timed(
                [&] {
                    geometry::Geos geos;
                    return geometry::extreme_faces(verts, faces, direction, geos);
                },
                repeat);
        },
        py::arg("vertices"), py::arg("faces"), py::arg("direction"), py::arg("repeat") = 1,
        "geometry::extreme_faces (port of clash_utils.get_extreme_faces): (triangle indices, seconds).");
    b.def(
        "visible_faces_brep",
        [](const std::string& brep, std::array<double, 3> direction, int repeat) {
            TopoDS_Shape shape;
            BRep_Builder builder;
            std::istringstream in(brep);
            BRepTools::Read(shape, in, builder);
            if (shape.IsNull()) throw ConfigError("the BRep text cannot be read");
            const gp_Dir dir(direction[0], direction[1], direction[2]);
            return timed([&] { return geometry::visible_faces(shape, dir).size(); }, repeat);
        },
        py::arg("brep"), py::arg("direction"), py::arg("repeat") = 1,
        "geometry::visible_faces (port of get_faces_visible_from_direction_with_plane, 50 x 50 rays on "
        "the B-Rep): (face count, seconds per call).");
}

}  // namespace

PYBIND11_MODULE(_ifcclash_engine, m) {
    m.doc() = "IfcClash_Plus C++ engine (libifcclash_engine)";
    m.attr("__version__") = kEngineVersion;
    m.attr("RESULT_SCHEMA_VERSION") = kResultSchemaVersion;

    static py::exception<ConfigError> config_error(m, "ConfigError", PyExc_ValueError);
    static py::exception<Cancelled> cancelled(m, "Cancelled", PyExc_RuntimeError);
    py::register_exception_translator([](std::exception_ptr p) {
        try {
            if (p) std::rethrow_exception(p);
        } catch (const ConfigError& e) {
            py::set_error(config_error, e.what());
        } catch (const Cancelled& e) {
            py::set_error(cancelled, e.what());
        }
    });

    py::class_<CancelToken>(m, "CancelToken")
        .def(py::init<>())
        .def("cancel", &CancelToken::cancel)
        .def_property_readonly("cancelled", &CancelToken::cancelled);

    py::class_<PySession>(m, "Session")
        .def(py::init<std::vector<std::filesystem::path>, const std::string&, std::optional<std::filesystem::path>,
                      bool, int, std::vector<std::filesystem::path>, const std::string&, double, int,
                      const std::string&>(),
             py::kw_only(), py::arg("ifc_paths"), py::arg("geometry_cache") = "auto",
             py::arg("cache_dir") = py::none(), py::arg("write_cache") = false, py::arg("iterator_threads") = 0,
             py::arg("ifcview_paths") = std::vector<std::filesystem::path>{},
             py::arg("ifcview_freshness") = "mtime", py::arg("ifcview_linear_deflection") = 0.01,
             py::arg("rule_threads") = 0, py::arg("triangle_source") = "auto")
        .def_property_readonly("diagnostics",
                               [](PySession& self) { return to_py(to_json(self.session().diagnostics())); })
        .def("__enter__", [](PySession& self) -> PySession& { return self; }, py::return_value_policy::reference)
        .def("__exit__", [](PySession& self, py::args) { self.close(); })
        .def("close", &PySession::close)
        .def(
            "triangles",
            [](PySession& self, uint32_t file_index, int entity_id) {
                auto [verts, faces] = self.session().triangles(file_index, entity_id);
                py::array_t<double> v({py::ssize_t(verts.size() / 3), py::ssize_t(3)});
                std::copy(verts.begin(), verts.end(), v.mutable_data());
                py::array_t<int32_t> f({py::ssize_t(faces.size() / 3), py::ssize_t(3)});
                std::copy(faces.begin(), faces.end(), f.mutable_data());
                return py::make_tuple(v, f);
            },
            py::arg("file_index"), py::arg("entity_id"),
            "Diagnostics: the world triangles of an element as the _triang rules read them (vertices (n, 3), "
            "faces (m, 3)).")
        .def_property_readonly("closed", &PySession::closed)
        .def_property_readonly("file_count", [](PySession& self) { return self.session().file_count(); })
        .def(
            "run",
            [](PySession& self, const std::string& rule_type, py::object params, py::object selections,
               const std::string& mode, py::object cancel, py::object progress, bool prefilter) {
                RunRequest request = request_from(rule_type, params, selections, mode, prefilter);
                CancelToken own;
                const CancelToken& token = cancel.is_none() ? own : *cancel.cast<CancelToken*>();
                PyProgress sink(progress);
                RunResult result;
                {
                    py::gil_scoped_release release;
                    result = self.session().run(request, token, sink);
                }
                return result_to_py(result);
            },
            py::kw_only(), py::arg("rule_type"), py::arg("params") = py::none(), py::arg("selections") = py::none(),
            py::arg("mode") = "verdicts", py::arg("cancel") = py::none(), py::arg("progress") = py::none(),
            py::arg("prefilter") = true)
        .def(
            "evaluate_pairs",
            [](PySession& self, const std::string& rule_type, py::object params, py::list pairs,
               const std::string& mode, bool prefilter) {
                RunRequest request = request_from(rule_type, params, py::none(), mode, prefilter);
                std::vector<KeyPair> keys;
                for (auto pair : pairs) {
                    auto t = pair.cast<py::tuple>();
                    keys.emplace_back(key_from(t[0]), key_from(t[1]));
                }
                RunResult result;
                {
                    py::gil_scoped_release release;
                    result = self.session().evaluate_pairs(request, keys);
                }
                return result_to_py(result);
            },
            py::kw_only(), py::arg("rule_type"), py::arg("params") = py::none(), py::arg("pairs"),
            py::arg("mode") = "verdicts", py::arg("prefilter") = true);

    m.def("catalogue_json", &catalogue_json, "The catalogue of the C++ rules, as JSON text.");
    bind_bench(m);
}
