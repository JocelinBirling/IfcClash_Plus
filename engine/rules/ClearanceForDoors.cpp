// ClearanceForDoors of Rules.py: the clearance zones swept by the door
// leaves (arc or rectangle, per the door operation type), and the deepest
// target vertex inside a zone.
#include "AllRules.h"

#include "../geometry/Faces.h"
#include "../sources/IfcQueries.h"

#include <BRepBndLib.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_MakePolygon.hxx>
#include <BRepBuilderAPI_MakeVertex.hxx>
#include <BRepClass3d_SolidClassifier.hxx>
#include <BRepExtrema_DistShapeShape.hxx>
#include <BRepPrimAPI_MakePrism.hxx>
#include <BRep_Builder.hxx>
#include <TopExp_Explorer.hxx>
#include <TopoDS_Compound.hxx>
#include <gp_Pnt.hxx>
#include <gp_Vec.hxx>

#include <algorithm>
#include <cctype>
#include <cmath>
#include <set>

namespace ifcclash {

namespace {

using V3 = std::array<double, 3>;
V3 add(const V3& a, const V3& b) { return {a[0] + b[0], a[1] + b[1], a[2] + b[2]}; }
V3 mul(const V3& a, double k) { return {a[0] * k, a[1] * k, a[2] * k}; }
gp_Pnt pnt(const V3& p) { return gp_Pnt(p[0], p[1], p[2]); }

struct DoorOperation {
    std::string mechanism = "unknown";
    int leaves = 1;
    std::vector<std::string> hinges;
};

// clash_utils.parse_door_operation
DoorOperation parse_door_operation(const std::optional<std::string>& type) {
    if (!type || type->empty()) return {};
    std::string n;
    for (char c : *type)
        if (c != ' ' && c != '_') n += static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    if (n.find("sliding") != std::string::npos) return {"sliding", 1, {}};
    if (n.find("double") != std::string::npos) return {"swing", 2, {"left", "right"}};
    if (n.find("swingleft") != std::string::npos) return {"swing", 1, {"left"}};
    if (n.find("swingright") != std::string::npos) return {"swing", 1, {"right"}};
    return {};
}

TopoDS_Shape prism(BRepBuilderAPI_MakePolygon& polygon, const V3& z, double height) {
    polygon.Close();
    BRepBuilderAPI_MakeFace face(polygon.Wire());
    return BRepPrimAPI_MakePrism(face.Face(), gp_Vec(z[0] * height, z[1] * height, z[2] * height)).Shape();
}

// clash_utils.make_box_zone
TopoDS_Shape box_zone(const V3& o, const V3& x, const V3& y, const V3& z, double w, double d, double h, double sign) {
    const V3 dd = mul(y, sign);
    auto corner = [&](double u, double v) { return pnt(add(add(o, mul(x, w * u)), mul(dd, d * v))); };
    BRepBuilderAPI_MakePolygon polygon;
    polygon.Add(corner(0.0, 0.0));
    polygon.Add(corner(1.0, 0.0));
    polygon.Add(corner(1.0, 1.0));
    polygon.Add(corner(0.0, 1.0));
    return prism(polygon, z, h);
}

// clash_utils.make_arc_zone
TopoDS_Shape arc_zone(const V3& hinge, const V3& x, const V3& y, const V3& z, double r, double h, int segments = 16) {
    BRepBuilderAPI_MakePolygon polygon;
    polygon.Add(pnt(hinge));
    polygon.Add(gp_Pnt(hinge[0] + x[0] * r, hinge[1] + x[1] * r, hinge[2] + x[2] * r));
    for (int i = 1; i <= segments; ++i) {
        const double angle = M_PI / 2.0 * i / segments;
        const V3 dir = add(mul(x, std::cos(angle)), mul(y, std::sin(angle)));
        polygon.Add(gp_Pnt(hinge[0] + dir[0] * r, hinge[1] + dir[1] * r, hinge[2] + dir[2] * r));
    }
    return prism(polygon, z, h);
}

// clash_utils.max_penetration_depth
double max_penetration_depth(const TopoDS_Shape& zone, const std::vector<double>& points) {
    BRep_Builder builder;
    TopoDS_Compound boundary;
    builder.MakeCompound(boundary);
    for (TopExp_Explorer ex(zone, TopAbs_FACE); ex.More(); ex.Next()) builder.Add(boundary, ex.Current());
    BRepClass3d_SolidClassifier classifier(zone);
    double depth = 0.0;
    for (size_t i = 0; i + 2 < points.size(); i += 3) {
        const gp_Pnt p(points[i], points[i + 1], points[i + 2]);
        classifier.Perform(p, 1e-7);
        if (classifier.State() == TopAbs_IN) {
            BRepExtrema_DistShapeShape tool;
            tool.LoadS1(BRepBuilderAPI_MakeVertex(p).Vertex());
            tool.LoadS2(boundary);
            tool.Perform();
            depth = std::max(depth, tool.Value());
        }
    }
    return depth;
}

struct DoorParams {
    std::string zone_shape = "Arc";
    std::string sides = "Swing";
    std::optional<int> leaves;
    std::optional<double> width, depth, height;
    double tolerance = 0.001;
};

struct DoorZone {
    std::string side, leaf_type;
    double width, depth, height;
    TopoDS_Shape solid;
};

struct DoorData {  // sources
    std::vector<DoorZone> zones;
};

struct TargetData {
    TopoDS_Shape occ;
    std::vector<double> verts;
};

class ClearanceForDoors final : public PairRule<DoorParams> {
public:
    // Doors: their local triangulation (dimensions); targets: B-Rep and
    // world triangulation.
    std::vector<Variant> data_variants() const override { return {Variant::BrepWorld, Variant::MeshWorld}; }
    std::vector<Variant> narrow_variants() const override { return {}; }
    bool needs_element_data() const override { return true; }
    bool skip_self() const override { return false; }  // Python: no self check

    void setup() override {
        const auto& p = params();
        if (p.zone_shape != "Arc" && p.zone_shape != "Rectangle") throw ConfigError("zone_shape must be 'Arc' or 'Rectangle'");
        if (p.sides != "Swing" && p.sides != "Both" && p.sides != "Front" && p.sides != "Back")
            throw ConfigError("sides must be 'Swing', 'Both', 'Front' or 'Back'");
        if (p.leaves && *p.leaves < 1) throw ConfigError("leaves must be None or an integer >= 1");
        for (const auto& [name, value] : {std::make_pair("width", p.width), std::make_pair("depth", p.depth),
                                          std::make_pair("height", p.height)})
            if (value && *value <= 0) throw ConfigError(std::string(name) + " must be None or a positive number");
        if (p.tolerance < 0) throw ConfigError("tolerance must be a positive number");
    }

    std::shared_ptr<const void> element_data(const ElementGeometry& e, Role role) const override {
        if (role == Role::Target) {
            auto occ = e.brep();
            auto mesh = e.mesh(Variant::MeshWorld);
            if (!occ || !mesh) return nullptr;
            auto data = std::make_shared<TargetData>();
            data->occ = *occ;
            data->verts = mesh->local_verts;
            return data;
        }
        auto* q = e.provider().ifc_queries();
        const auto mesh = e.mesh();
        if (!q || !mesh || mesh->local_verts.empty()) return nullptr;
        return std::make_shared<DoorData>(DoorData{zones(*q, e.key, *mesh)});
    }

    Bnd_Box broad_volume(const ElementGeometry& e, Role role) const override {
        Bnd_Box box;
        if (role == Role::Target) {
            BRepBndLib::Add(e.as<TargetData>().occ, box);
            const auto& v = e.as<TargetData>().verts;
            for (size_t i = 0; i + 2 < v.size(); i += 3) box.Add(gp_Pnt(v[i], v[i + 1], v[i + 2]));
        } else {
            for (const auto& z : e.as<DoorData>().zones) BRepBndLib::Add(z.solid, box);
        }
        return geometry::inflate(box, 1e-6);
    }

    Verdict narrow_test(const ElementGeometry& source, const ElementGeometry& target) const override {
        const auto& t = target.as<TargetData>();
        const DoorZone* worst_zone = nullptr;
        double worst = 0.0;
        for (const auto& zone : source.as<DoorData>().zones) {
            BRepExtrema_DistShapeShape tool;
            tool.LoadS1(t.occ);
            tool.LoadS2(zone.solid);
            tool.Perform();
            if (tool.Value() > 0) continue;
            const double depth = max_penetration_depth(zone.solid, t.verts);
            if (depth > params().tolerance && (!worst_zone || depth > worst)) {
                worst = depth;
                worst_zone = &zone;
            }
        }
        Verdict v;
        if (!worst_zone) return v;
        v.status = true;
        v.measures.set(Measure::PenetrationDepth, worst);
        v.zone = ZoneBlock{worst_zone->side, worst_zone->leaf_type, worst_zone->width, worst_zone->depth,
                           worst_zone->height};
        return v;
    }

private:
    // ClearanceForDoors._build_zones
    std::vector<DoorZone> zones(IfcQueries& q, const ElementKey& door, const Mesh& mesh) const {
        const auto& p = params();
        const auto m = q.local_placement(door);
        const V3 origin{m[3], m[7], m[11]}, x{m[0], m[4], m[8]}, y{m[1], m[5], m[9]}, z{m[2], m[6], m[10]};
        V3 lo{1e300, 1e300, 1e300}, hi{-1e300, -1e300, -1e300};
        for (size_t i = 0; i + 2 < mesh.local_verts.size(); i += 3)
            for (int k = 0; k < 3; ++k) {
                lo[k] = std::min(lo[k], mesh.local_verts[i + k]);
                hi[k] = std::max(hi[k], mesh.local_verts[i + k]);
            }
        const double width = hi[0] - lo[0], door_height = hi[2] - lo[2];
        const auto type = q.door_operation_type(door);
        const DoorOperation op = parse_door_operation(type);
        const std::string leaf_type = (type && !type->empty()) ? *type : op.mechanism;
        const int leaves = p.leaves ? *p.leaves : op.leaves;
        const double leaf_width = leaves > 0 ? width / leaves : width;
        const double zw = p.width ? *p.width : leaf_width;
        const double zd = p.depth ? *p.depth : leaf_width;
        const double zh = p.height ? *p.height : std::max(door_height, 0.0);

        std::vector<DoorZone> out;
        auto rect = [&](double sign, const char* side) {
            out.push_back({side, leaf_type, zw, zd, zh, box_zone(origin, x, y, z, zw, zd, zh, sign)});
        };
        auto arc = [&](const V3& hinge) { out.push_back({"Front", leaf_type, zw, zw, zh, arc_zone(hinge, x, y, z, zw, zh)}); };
        const std::string& sides = p.sides;
        if (op.mechanism == "sliding") {
            if (sides == "Swing" || sides == "Both") {
                rect(1.0, "Front");
                rect(-1.0, "Back");
            } else if (sides == "Front") {
                rect(1.0, "Front");
            } else {
                rect(-1.0, "Back");
            }
            return out;
        }
        if (op.mechanism == "swing" && p.zone_shape == "Arc") {
            for (const auto& hinge_side : op.hinges) {
                const V3 hinge = hinge_side == "left" ? origin : add(origin, mul(x, width));
                if (sides == "Swing" || sides == "Both" || sides == "Front") arc(hinge);
                if (sides == "Both" || sides == "Back") rect(-1.0, "Back");
            }
            return out;
        }
        if (op.mechanism == "swing" && p.zone_shape == "Rectangle") {
            for (size_t i = 0; i < op.hinges.size(); ++i) {
                if (sides == "Swing" || sides == "Both" || sides == "Front") rect(1.0, "Front");
                if (sides == "Both" || sides == "Back") rect(-1.0, "Back");
            }
            std::vector<DoorZone> dedup;
            std::set<std::pair<std::string, double>> seen;
            for (auto& zone : out) {
                const double w = std::round(zone.width * 1e9) / 1e9;
                if (!seen.insert({zone.side, w}).second) continue;
                dedup.push_back(std::move(zone));
            }
            return dedup;
        }
        rect(1.0, "Front");
        rect(-1.0, "Back");
        return out;
    }
};

}  // namespace

RuleSpec spec_clearance_for_doors() {
    return RuleSpec::pair<ClearanceForDoors>(
        "ClearanceForDoors", "Clearance For Doors", {Slot::Source, Slot::Target},
        "Flags the targets entering the clearance zone swept by the door leaves.",
        {param(&DoorParams::zone_shape, "zone_shape").doc("Zone shape").values({"Arc", "Rectangle"}),
         param(&DoorParams::sides, "sides").doc("Door sides").values({"Swing", "Both", "Front", "Back"}),
         param(&DoorParams::leaves, "leaves").doc("Number of leaves (None = from the door type)"),
         param(&DoorParams::width, "width").doc("Zone width").unit(Unit::Metre),
         param(&DoorParams::depth, "depth").doc("Zone depth").unit(Unit::Metre),
         param(&DoorParams::height, "height").doc("Zone height").unit(Unit::Metre),
         param(&DoorParams::tolerance, "tolerance").doc("Tolerance").unit(Unit::Metre)});
}

}  // namespace ifcclash
