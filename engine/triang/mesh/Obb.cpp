#include "Obb.h"

#include <TColgp_Array1OfPnt.hxx>
#include <gp_Pnt.hxx>

namespace ifcclash::triang {

Bnd_OBB optimal_obb(const std::vector<double>& xyz) {
    Bnd_OBB obb;
    const int n = static_cast<int>(xyz.size() / 3);
    if (n == 0) return obb;
    TColgp_Array1OfPnt points(1, n);
    for (int i = 0; i < n; ++i) points.SetValue(i + 1, gp_Pnt(xyz[3 * i], xyz[3 * i + 1], xyz[3 * i + 2]));
    obb.ReBuild(points, nullptr, true);
    return obb;
}

}  // namespace ifcclash::triang
