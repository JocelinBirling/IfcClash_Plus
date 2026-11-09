#include "Obb.h"

#include <BRepBndLib.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <BRepPrimAPI_MakeBox.hxx>
#include <gp_Ax2.hxx>
#include <Bnd_Box.hxx>

#include <algorithm>
#include <cmath>
#include <vector>

namespace ifcclash::geometry {

Bnd_OBB obb_of_shape(const TopoDS_Shape& shape) {
    BRepMesh_IncrementalMesh mesh(shape, 0.01, false, 0.5);
    mesh.Perform();
    Bnd_OBB obb;
    BRepBndLib::AddOBB(shape, obb, true, true, true);
    // Custom_OBB(center, gp_Dir(x), gp_Dir(y), gp_Dir(z), hx, hy, hz)
    return Bnd_OBB(gp_Pnt(obb.Center()), gp_Dir(obb.XDirection()), gp_Dir(obb.YDirection()),
                   gp_Dir(obb.ZDirection()), obb.XHSize(), obb.YHSize(), obb.ZHSize());
}

std::array<gp_XYZ, 8> obb_corners(const Bnd_OBB& obb) {
    const gp_XYZ c = obb.Center();
    const gp_XYZ x = obb.XDirection(), y = obb.YDirection(), z = obb.ZDirection();
    const double hx = obb.XHSize(), hy = obb.YHSize(), hz = obb.ZHSize();
    std::array<gp_XYZ, 8> out;
    int n = 0;
    for (double sx : {-1.0, 1.0})
        for (double sy : {-1.0, 1.0})
            for (double sz : {-1.0, 1.0})
                out[n++] = gp_XYZ(c.X() + sx * x.X() * hx + sy * y.X() * hy + sz * z.X() * hz,
                                  c.Y() + sx * x.Y() * hx + sy * y.Y() * hy + sz * z.Y() * hz,
                                  c.Z() + sx * x.Z() * hx + sy * y.Z() * hy + sz * z.Z() * hz);
    return out;
}

std::pair<gp_Dir, gp_Dir> two_main_directions(const Bnd_OBB& obb, const std::string& wide_or_narrow,
                                              bool only_check_xy) {
    struct Dim {
        char name;
        double size;
    };
    const double sx = obb.XHSize() * 2, sy = obb.YHSize() * 2, sz = obb.ZHSize() * 2;
    std::vector<Dim> dims{{'X', sx}, {'Y', sy}, {'Z', sz}};
    if (only_check_xy) {
        const gp_Dir z_abs(0, 0, 1);
        const double tol = 0.1;
        const gp_Dir zd(obb.ZDirection()), xd(obb.XDirection()), yd(obb.YDirection());
        if (z_abs.IsParallel(zd, tol)) {
            dims = {{'X', sx}, {'Y', sy}};
        } else if (z_abs.IsParallel(xd, tol)) {
            dims = {{'Y', sy}, {'Z', sz}};
        } else if (z_abs.IsParallel(yd, tol)) {
            dims = {{'X', sx}, {'Z', sz}};
        } else {
            // Tilted object: keep the biggest axis and the most horizontal
            // of the two others (first max / first min, as Python's max/min).
            struct Axis {
                char name;
                double size;
                gp_Dir dir;
            };
            std::vector<Axis> axes{{'X', sx, xd}, {'Y', sy, yd}, {'Z', sz, zd}};
            size_t biggest = 0;
            for (size_t i = 1; i < 3; ++i)
                if (axes[i].size > axes[biggest].size) biggest = i;
            std::vector<size_t> rest;
            for (size_t i = 0; i < 3; ++i)
                if (i != biggest) rest.push_back(i);
            size_t horizontal = rest[0];
            for (size_t i : rest)
                if (std::abs(axes[i].dir.Dot(z_abs)) < std::abs(axes[horizontal].dir.Dot(z_abs))) horizontal = i;
            dims = {{axes[biggest].name, axes[biggest].size}, {axes[horizontal].name, axes[horizontal].size}};
        }
    }
    const bool reverse = wide_or_narrow == "Narrow";
    std::stable_sort(dims.begin(), dims.end(),
                     [reverse](const Dim& a, const Dim& b) { return reverse ? a.size > b.size : a.size < b.size; });
    const char first = dims.front().name;
    const gp_XYZ d = first == 'X' ? obb.XDirection() : first == 'Y' ? obb.YDirection() : obb.ZDirection();
    return {gp_Dir(d), gp_Dir(d.Reversed())};
}

ObbData obb_data(const Bnd_OBB& obb, const std::optional<std::string>& label) {
    auto p = [](const gp_XYZ& v) { return Point3{v.X(), v.Y(), v.Z()}; };
    ObbData data;
    data.center = p(obb.Center());
    data.axes = {p(obb.XDirection()), p(obb.YDirection()), p(obb.ZDirection())};
    data.half_sizes = {obb.XHSize(), obb.YHSize(), obb.ZHSize()};
    data.label = label;
    return data;
}

Bnd_OBB make_obb(const gp_Pnt& center, const gp_Dir& x, const gp_Dir& y, const gp_Dir& z, double hx, double hy,
                 double hz) {
    return Bnd_OBB(center, x, y, z, hx, hy, hz);
}

Bnd_OBB detach_by_extrude(const Bnd_OBB& obb, const ObbChange& change_in, bool top) {
    const gp_Dir world(0, 0, top ? 1 : -1);
    const gp_XYZ c = obb.Center();
    gp_Dir dirs[3] = {gp_Dir(obb.XDirection()), gp_Dir(obb.YDirection()), gp_Dir(obb.ZDirection())};
    const double hs[3] = {obb.XHSize(), obb.YHSize(), obb.ZHSize()};
    int up = -1;
    double best = 0.0;
    for (int i = 0; i < 3; ++i) {
        const double dot = world.Dot(dirs[i]);
        if (up < 0 || std::abs(dot) > std::abs(best)) {
            best = dot;
            up = i;
        }
    }
    gp_Dir up_dir = dirs[up];
    const double up_h = hs[up];
    double change = change_in.value;
    if (change_in.percent) change = change_in.value * up_h * 2;
    if (best < 0) up_dir = up_dir.Reversed();
    const gp_Pnt top_center(c.X() + up_dir.X() * up_h + up_dir.X() * (change / 2),
                            c.Y() + up_dir.Y() * up_h + up_dir.Y() * (change / 2),
                            c.Z() + up_dir.Z() * up_h + up_dir.Z() * (change / 2));
    gp_Dir new_dirs[3] = {dirs[0], dirs[1], dirs[2]};
    double new_hs[3] = {hs[0], hs[1], hs[2]};
    new_dirs[up] = up_dir;
    new_hs[up] = change / 2;
    return make_obb(top_center, new_dirs[0], new_dirs[1], new_dirs[2], new_hs[0], new_hs[1], new_hs[2]);
}

Bnd_OBB extend_vertically(const Bnd_OBB& obb, const ObbChange& change_in, bool up) {
    const gp_XYZ c = obb.Center();
    const gp_Dir x(obb.XDirection()), y(obb.YDirection()), z(obb.ZDirection());
    const double hx = obb.XHSize(), hy = obb.YHSize(), hz = obb.ZHSize();
    const gp_Dir w(0, 0, up ? 1 : -1);
    const double px = std::abs(w.Dot(x)), py = std::abs(w.Dot(y)), pz = std::abs(w.Dot(z));
    const double height = px * hx * 2 + py * hy * 2 + pz * hz * 2;
    const double change = change_in.percent ? height * change_in.value : change_in.value;
    const gp_Pnt center(c.X() + w.X() * change / 2, c.Y() + w.Y() * change / 2, c.Z() + w.Z() * change / 2);
    return make_obb(center, x, y, z, hx + px * change / 2, hy + py * change / 2, hz + pz * change / 2);
}

void expand_sides(Bnd_OBB& obb, const ObbChange& change) {
    const double hx = obb.XHSize(), hy = obb.YHSize(), hz = obb.ZHSize();
    double nx, ny;
    if (change.percent) {
        nx = hx + (hx * change.value) / 2;
        ny = hy + (hy * change.value) / 2;
    } else {
        nx = hz + change.value / 2;
        ny = hz + change.value / 2;
    }
    obb.SetXComponent(gp_Dir(obb.XDirection()), nx);
    obb.SetYComponent(gp_Dir(obb.YDirection()), ny);
}

Bnd_OBB detach_side_by_extrude(const Bnd_OBB& obb, const gp_Dir& d, double distance) {
    const gp_XYZ c = obb.Center();
    const gp_Dir x(obb.XDirection()), y(obb.YDirection()), z(obb.ZDirection());
    const double hx = obb.XHSize(), hy = obb.YHSize(), hz = obb.ZHSize();
    const double px = std::abs(d.Dot(x)), py = std::abs(d.Dot(y)), pz = std::abs(d.Dot(z));
    const double size = hx * px + hy * py + hz * pz;
    const gp_Pnt center(c.X() + d.X() * (size + distance / 2), c.Y() + d.Y() * (size + distance / 2),
                        c.Z() + d.Z() * (size + distance / 2));
    double nx = hx, ny = hy, nz = hz;
    if (px > py && px > pz) nx = distance / 2;
    else if (py > px && py > pz) ny = distance / 2;
    else nz = distance / 2;
    return make_obb(center, x, y, z, nx, ny, nz);
}

TopoDS_Shape obb_solid(const Bnd_OBB& obb) {
    const gp_XYZ c = obb.Center();
    double ax = obb.XHSize(), ay = obb.YHSize(), az = obb.ZHSize();
    gp_XYZ xd = obb.XDirection(), yd = obb.YDirection();
    const gp_XYZ zd = obb.ZDirection();
    if (gp_Dir(xd).Crossed(gp_Dir(yd)).Dot(gp_Dir(zd)) < 0) {
        std::swap(xd, yd);
        std::swap(ax, ay);
    }
    const gp_Pnt corner(c.X() - ax * xd.X() - ay * yd.X() - az * zd.X(), c.Y() - ax * xd.Y() - ay * yd.Y() - az * zd.Y(),
                        c.Z() - ax * xd.Z() - ay * yd.Z() - az * zd.Z());
    const gp_Ax2 frame(corner, gp_Dir(zd), gp_Dir(xd));
    return BRepPrimAPI_MakeBox(frame, 2 * ax, 2 * ay, 2 * az).Shape();
}

Bnd_Box obb_aabb(const Bnd_OBB& obb) {
    Bnd_Box box;
    for (const auto& p : obb_corners(obb)) box.Add(gp_Pnt(p));
    return box;
}

gp_Pnt shape_center(const TopoDS_Shape& shape) {
    Bnd_Box box;
    BRepBndLib::Add(shape, box);
    const gp_Pnt a = box.CornerMin(), b = box.CornerMax();
    return gp_Pnt((a.X() + b.X()) / 2.0, (a.Y() + b.Y()) / 2.0, (a.Z() + b.Z()) / 2.0);
}

}  // namespace ifcclash::geometry
