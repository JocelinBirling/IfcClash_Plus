#include "Faces.h"

#include <BRepAdaptor_Surface.hxx>
#include <BRepBndLib.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_MakePolygon.hxx>
#include <BRepExtrema_DistShapeShape.hxx>
#include <BRepGProp.hxx>
#include <BRepIntCurveSurface_Inter.hxx>
#include <GeomAdaptor_Curve.hxx>
#include <Geom_Line.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <BRep_Tool.hxx>
#include <Bnd_Box.hxx>
#include <GProp_GProps.hxx>
#include <Poly_Triangulation.hxx>
#include <TopExp_Explorer.hxx>
#include <TopLoc_Location.hxx>
#include <TopoDS.hxx>
#include <gp_Lin.hxx>
#include <gp_Vec.hxx>

#include <algorithm>
#include <limits>
#include <stdexcept>

namespace ifcclash::geometry {

std::optional<gp_Dir> face_normal(const TopoDS_Face& face) {
    BRepAdaptor_Surface surface(face);
    const double u = (surface.FirstUParameter() + surface.LastUParameter()) / 2.0;
    const double v = (surface.FirstVParameter() + surface.LastVParameter()) / 2.0;
    gp_Pnt p;
    gp_Vec du, dv;
    surface.D1(u, v, p, du, dv);
    const gp_Vec n = du.Crossed(dv);
    if (n.Magnitude() < 1e-10) return std::nullopt;
    gp_Dir dir(n);
    if (face.Orientation() == TopAbs_REVERSED) dir.Reverse();
    return dir;
}

double face_area(const TopoDS_Face& face) {
    GProp_GProps props;
    BRepGProp::SurfaceProperties(face, props);
    return props.Mass();
}

std::vector<Triangle3> face_triangles(const TopoDS_Face& face, double linear_deflection) {
    BRepMesh_IncrementalMesh(face, linear_deflection, false, 0.5, true);
    TopLoc_Location location;
    const Handle(Poly_Triangulation) triangulation = BRep_Tool::Triangulation(face, location);
    std::vector<Triangle3> out;
    if (triangulation.IsNull()) return out;
    for (int i = 1; i <= triangulation->NbTriangles(); ++i) {
        int n[3];
        triangulation->Triangle(i).Get(n[0], n[1], n[2]);
        Triangle3 t;
        for (int k = 0; k < 3; ++k) {
            const gp_Pnt p = triangulation->Node(n[k]);
            t[k] = {p.X(), p.Y(), p.Z()};
        }
        out.push_back(t);
    }
    return out;
}

FaceData extrem_face_data(const TopoDS_Face& face) {
    FaceData data;
    if (const auto n = face_normal(face)) data.normal = {n->X(), n->Y(), n->Z()};
    data.area = face_area(face);
    data.triangles = face_triangles(face);
    return data;
}

namespace {

// clash_utils.create_view_plane(shape, direction, distance, size_factor)
TopoDS_Face view_plane(const TopoDS_Shape& shape, const gp_Dir& direction, double distance, double size_factor) {
    Bnd_Box box;
    BRepBndLib::Add(shape, box);
    const gp_Pnt lo = box.CornerMin(), hi = box.CornerMax();
    const gp_Pnt center((lo.X() + hi.X()) / 2.0, (lo.Y() + hi.Y()) / 2.0, (lo.Z() + hi.Z()) / 2.0);
    const double max_dim = std::max({hi.X() - lo.X(), hi.Y() - lo.Y(), hi.Z() - lo.Z()});
    const double plane_size = max_dim * size_factor;
    gp_Vec offset(direction.X(), direction.Y(), direction.Z());
    offset.Multiply(-distance);
    const gp_Pnt pc(center.X() + offset.X(), center.Y() + offset.Y(), center.Z() + offset.Z());

    const gp_Vec d(direction.X(), direction.Y(), direction.Z());
    gp_Vec bx = std::abs(d.X()) < 0.5 ? gp_Vec(1, 0, 0) : gp_Vec(0, 1, 0);
    const double dot_x = bx.Dot(d);
    const double d2 = d.Dot(d);
    if (d2 > 1e-10) {
        const double f = dot_x / d2;
        bx.Subtract(gp_Vec(d.X() * f, d.Y() * f, d.Z() * f));
    }
    const double bxm = bx.Magnitude();
    if (bxm > 1e-10) bx.Divide(bxm);
    gp_Vec by = d.Crossed(bx);
    const double bym = by.Magnitude();
    if (bym > 1e-10) by.Divide(bym);

    const double h = plane_size / 2.0;
    BRepBuilderAPI_MakePolygon polygon;
    // Python: c - bx*h - by*h (component-wise subtraction order kept by the
    // signs: (pc - bx*h) - by*h).
    polygon.Add(gp_Pnt(pc.X() - bx.X() * h - by.X() * h, pc.Y() - bx.Y() * h - by.Y() * h, pc.Z() - bx.Z() * h - by.Z() * h));
    polygon.Add(gp_Pnt(pc.X() + bx.X() * h - by.X() * h, pc.Y() + bx.Y() * h - by.Y() * h, pc.Z() + bx.Z() * h - by.Z() * h));
    polygon.Add(gp_Pnt(pc.X() + bx.X() * h + by.X() * h, pc.Y() + bx.Y() * h + by.Y() * h, pc.Z() + bx.Z() * h + by.Z() * h));
    polygon.Add(gp_Pnt(pc.X() - bx.X() * h + by.X() * h, pc.Y() - bx.Y() * h + by.Y() * h, pc.Z() - bx.Z() * h + by.Z() * h));
    polygon.Close();
    BRepBuilderAPI_MakeFace face(polygon.Wire());
    if (!face.IsDone()) throw std::runtime_error("Failed to create view plane");
    return face.Face();
}

// clash_utils.sample_points_on_face
std::vector<gp_Pnt> sample_points(const TopoDS_Face& face, int n) {
    BRepAdaptor_Surface surface(face);
    const double u0 = surface.FirstUParameter(), u1 = surface.LastUParameter();
    const double v0 = surface.FirstVParameter(), v1 = surface.LastVParameter();
    std::vector<gp_Pnt> out;
    out.reserve(static_cast<size_t>(n * n));
    for (int i = 0; i < n; ++i)
        for (int j = 0; j < n; ++j) {
            const double u = u0 + (u1 - u0) * (i + 0.5) / n;
            const double v = v0 + (v1 - v0) * (j + 0.5) / n;
            gp_Pnt p;
            surface.D0(u, v, p);
            out.push_back(p);
        }
    return out;
}

}  // namespace

std::vector<TopoDS_Face> visible_faces(const TopoDS_Shape& shape, const gp_Dir& view) {
    const gp_Dir direction = view.Reversed();  // "We need to invert it"
    const TopoDS_Face plane = view_plane(shape, direction, 100.0, 1.0);
    std::vector<TopoDS_Face> hit;  // insertion order of the Python dict
    // Init(shape, line, tol) is Load(shape, tol) + Init(curve): the shape
    // (its faces and their boxes) is loaded once for the 2 500 rays instead
    // of once per ray. Same faces, same order, same intersections.
    BRepIntCurveSurface_Inter inter;
    inter.Load(shape, 1e-7);
    for (const gp_Pnt& point : sample_points(plane, 50)) {
        const gp_Lin ray(point, direction);
        inter.Init(GeomAdaptor_Curve(new Geom_Line(ray)));
        std::optional<TopoDS_Face> first;
        double first_distance = std::numeric_limits<double>::infinity();
        while (inter.More()) {
            const double t = inter.W();
            if (t < 0) {
                inter.Next();
                continue;
            }
            const gp_Pnt loc = ray.Location();
            const gp_Dir dir = ray.Direction();
            const gp_Pnt hit_point(loc.X() + t * dir.X(), loc.Y() + t * dir.Y(), loc.Z() + t * dir.Z());
            const double distance = point.Distance(hit_point);
            if (distance < first_distance) {
                first_distance = distance;
                first = inter.Face();
            }
            inter.Next();
        }
        if (first) {
            const bool known = std::any_of(hit.begin(), hit.end(), [&](const TopoDS_Face& f) { return f.IsEqual(*first); });
            if (!known) hit.push_back(*first);
        }
    }
    return hit;
}

ExtremCheck check_extrem_face_distance(const std::vector<TopoDS_Face>& source_faces,
                                       const std::vector<TopoDS_Face>& target_faces, double tolerance,
                                       bool above) {
    ExtremCheck out;
    for (const auto& sf : source_faces) {
        for (const auto& tf : target_faces) {
            BRepExtrema_DistShapeShape dist;
            dist.LoadS1(sf);
            dist.LoadS2(tf);
            dist.Perform();
            const double distance = dist.Value();
            if (distance <= tolerance) {
                for (int i = 1; i <= dist.NbSolution(); ++i) {
                    const gp_Pnt ps = dist.PointOnShape1(i);
                    const gp_Pnt pt = dist.PointOnShape2(i);
                    if (above ? ps.Z() > pt.Z() : ps.Z() < pt.Z()) continue;
                    if (std::abs(ps.X() - pt.X()) < 1e-3 && std::abs(ps.Y() - pt.Y()) < 1e-3) {
                        out.side = ExtremCheck::Side::RightSide;
                        out.details = ExtremDetails{sf, tf, {ps.X(), ps.Y(), ps.Z()}, {pt.X(), pt.Y(), pt.Z()}, distance};
                        return out;
                    }
                    out.candidates.push_back({pt, sf, tf, distance});
                }
            }
        }
    }
    out.side = out.candidates.empty() ? ExtremCheck::Side::TooFar : ExtremCheck::Side::NeedMoreCheck;
    return out;
}

double shape_distance(const TopoDS_Shape& a, const TopoDS_Shape& b) {
    BRepExtrema_DistShapeShape dist;
    dist.LoadS1(a);
    dist.LoadS2(b);
    dist.Perform();
    return dist.Value();
}

}  // namespace ifcclash::geometry
