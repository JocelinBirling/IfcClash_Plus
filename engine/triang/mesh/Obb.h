// IfcClash_Plus engine — oriented boxes of triangulated elements
// (engine/triang/mesh).
#pragma once

#include <Bnd_OBB.hxx>

#include <vector>

namespace ifcclash::triang {

// The tightest oriented box of a point set (OCCT Bnd_OBB::ReBuild, optimal
// mode: the method of BRepBndLib::AddOBB on a triangulation).
Bnd_OBB optimal_obb(const std::vector<double>& xyz);

}  // namespace ifcclash::triang
