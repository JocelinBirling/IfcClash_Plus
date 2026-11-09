// IfcClash_Plus engine — the floating-point forms of the numpy operations the
// Python rules use on 3-vectors.
//
// numpy delegates `@` / np.dot / np.linalg.norm on 1-D vectors and the
// matrix-vector product to OpenBLAS, whose kernels use fused multiply-adds in
// a fixed order; a plain a0*b0 + a1*b1 + a2*b2 differs in the last bit in
// about a third of the cases. On boundary cases (a vertex exactly on an edge,
// a strict 0 < u < 1 test) that bit decides the verdict, so the C++ engine
// reproduces the exact forms measured on the reference environment
// (numpy 2 / OpenBLAS, x86-64). They are kernel-dependent: on another BLAS
// build the Python engine itself may round differently.
#pragma once

#include <array>
#include <cmath>

namespace ifcclash::geometry::np {

using V3 = std::array<double, 3>;

// a @ b, np.dot(a, b) for two 1-D vectors (OpenBLAS ddot)
inline double dot(const V3& a, const V3& b) { return std::fma(a[2], b[2], std::fma(a[1], b[1], a[0] * b[0])); }
// np.linalg.norm(a) for a 1-D vector
inline double norm(const V3& a) { return std::sqrt(dot(a, a)); }
// one row of M @ d, M of shape (n, 3) (OpenBLAS dgemv)
inline double matvec(const V3& row, const V3& d) { return std::fma(row[2], d[2], std::fma(row[0], d[0], row[1] * d[1])); }
// one row of np.linalg.norm(M, axis=1) (add.reduce, no FMA)
inline double row_norm(const V3& r) { return std::sqrt((r[0] * r[0] + r[1] * r[1]) + r[2] * r[2]); }
// one row of np.einsum("ij,ij->i", A, B)
inline double einsum_rowdot(const V3& a, const V3& b) { return (a[0] * b[0] + a[2] * b[2]) + a[1] * b[1]; }
// np.cross (no FMA)
inline V3 cross(const V3& a, const V3& b) {
    return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
}
inline V3 sub(const V3& a, const V3& b) { return {a[0] - b[0], a[1] - b[1], a[2] - b[2]}; }
inline V3 div(const V3& a, double k) { return {a[0] / k, a[1] / k, a[2] / k}; }
// x / np.linalg.norm(x) for a 1-D vector
inline V3 unit(const V3& a) { return div(a, norm(a)); }

}  // namespace ifcclash::geometry::np
