// Alignement of Rules.py: the elements that do not belong to an aligned
// group of at least min_group members are flagged, with their offset to the
// fitted line / plane. A set rule: the verdict of an element depends on all
// the others.
//
// Order: the Python engine takes the elements in the order its multi-thread
// IfcOpenShell iterator yields them, which changes from one run to the next
// (and the grouping seeds depend on it). The C++ engine takes them in the
// selection order: deterministic.
#include "AllRules.h"

#include "../geometry/Obb.h"

#include <Eigen/Dense>

#include <cmath>
#include <set>

namespace ifcclash {

namespace {

const double kVerticalCosine = std::cos(45.0 * M_PI / 180.0);
constexpr double kFootprintElongation = 2.0;
const double kParallelCosine = std::cos(15.0 * M_PI / 180.0);  // ALIGNMENT_PARALLEL_COSINE
const double kPlaneCosine = std::cos(75.0 * M_PI / 180.0);     // ALIGNMENT_PLANE_COSINE
const double kLevelCosine = std::cos(1.0 * M_PI / 180.0);      // ALIGNMENT_LEVEL_COSINE
constexpr double kCoincidence = 1e-9;                           // ALIGNMENT_COINCIDENCE

using Vec = std::vector<double>;  // 2D or 3D

// numpy 1-D forms (OpenBLAS ddot: fused chain)
double dot(const Vec& a, const Vec& b) {
    double r = a[0] * b[0];
    for (size_t i = 1; i < a.size(); ++i) r = std::fma(a[i], b[i], r);
    return r;
}
double norm(const Vec& a) { return std::sqrt(dot(a, a)); }
Vec sub(const Vec& a, const Vec& b) {
    Vec r(a.size());
    for (size_t i = 0; i < a.size(); ++i) r[i] = a[i] - b[i];
    return r;
}
Vec add(const Vec& a, const Vec& b) {
    Vec r(a.size());
    for (size_t i = 0; i < a.size(); ++i) r[i] = a[i] + b[i];
    return r;
}
Vec mul(const Vec& a, double k) {
    Vec r(a.size());
    for (size_t i = 0; i < a.size(); ++i) r[i] = a[i] * k;
    return r;
}
Vec div(const Vec& a, double k) {
    Vec r(a.size());
    for (size_t i = 0; i < a.size(); ++i) r[i] = a[i] / k;
    return r;
}
Vec cross(const Vec& a, const Vec& b) {
    return {a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]};
}

double point_line_distance(const Vec& p, const Vec& origin, Vec direction) {
    direction = div(direction, norm(direction));
    const Vec diff = sub(p, origin);
    return norm(sub(diff, mul(direction, dot(diff, direction))));
}

double point_plane_distance(const Vec& p, const Vec& origin, Vec normal) {
    normal = div(normal, norm(normal));
    return std::abs(dot(sub(p, origin), normal));
}

// The centroid and the covariance eigen-decomposition of least_squares_*.
struct Fit {
    Vec centroid;
    Eigen::VectorXd values;   // ascending
    Eigen::MatrixXd vectors;  // columns
};

Fit fit(const std::vector<Vec>& pts) {
    const size_t k = pts[0].size();
    Fit f;
    f.centroid.assign(k, 0.0);
    for (const auto& p : pts)
        for (size_t i = 0; i < k; ++i) f.centroid[i] += p[i];
    for (auto& c : f.centroid) c /= static_cast<double>(pts.size());
    Eigen::MatrixXd cov = Eigen::MatrixXd::Zero(k, k);
    for (const auto& p : pts) {
        const Vec c = sub(p, f.centroid);
        for (size_t i = 0; i < k; ++i)
            for (size_t j = 0; j < k; ++j) cov(i, j) += c[i] * c[j];
    }
    Eigen::SelfAdjointEigenSolver<Eigen::MatrixXd> solver(cov);
    f.values = solver.eigenvalues();
    f.vectors = solver.eigenvectors();
    return f;
}

std::pair<Vec, Vec> least_squares_line(const std::vector<Vec>& pts) {
    const Fit f = fit(pts);
    const size_t k = f.centroid.size();
    Vec d(k);
    for (size_t i = 0; i < k; ++i) d[i] = f.vectors(i, k - 1);
    if (norm(d) < 1e-12) {
        Vec x(k, 0.0);
        x[0] = 1.0;
        return {f.centroid, x};
    }
    return {f.centroid, div(d, norm(d))};
}

std::pair<Vec, Vec> least_squares_plane(const std::vector<Vec>& pts) {
    const Fit f = fit(pts);
    Vec normal{f.vectors(0, 0), f.vectors(1, 0), f.vectors(2, 0)};
    if (f.values(1) < 1e-12) {
        const Vec line{f.vectors(0, 2), f.vectors(1, 2), f.vectors(2, 2)};
        Vec helper{1.0, 0.0, 0.0};
        if (std::abs(dot(line, helper)) > 0.9) helper = {0.0, 1.0, 0.0};
        normal = cross(line, helper);
    }
    if (norm(normal) < 1e-12) return {f.centroid, {0.0, 0.0, 1.0}};
    return {f.centroid, div(normal, norm(normal))};
}

using Group = std::vector<int>;

// clash_utils.plan_alignment_groups
std::set<Group> plan_groups(const std::vector<Vec>& pts, const std::vector<std::optional<Vec>>& dirs, double tolerance) {
    std::set<Group> groups;
    const int count = static_cast<int>(pts.size());
    if (count < 2) return groups;
    auto members_of = [&](const Vec& origin, const Vec& direction) {
        Group members;
        for (int i = 0; i < count; ++i) {
            if (point_line_distance(pts[i], origin, direction) > tolerance) continue;
            if (dirs[i] && std::abs(dot(*dirs[i], direction)) < kParallelCosine) continue;
            members.push_back(i);
        }
        return members;
    };
    for (int i = 0; i < count; ++i)
        for (int j = i + 1; j < count; ++j) {
            std::optional<Vec> direction;
            if (dirs[i] && dirs[j]) {
                if (!(std::abs(dot(*dirs[i], *dirs[j])) < kParallelCosine)) direction = dirs[i];
            } else if (dirs[i]) {
                direction = dirs[i];
            } else if (dirs[j]) {
                direction = dirs[j];
            } else {
                const Vec v = sub(pts[j], pts[i]);
                const double n = norm(v);
                if (!(n < kCoincidence)) direction = div(v, n);
            }
            if (!direction) continue;
            const Vec origin = div(add(pts[i], pts[j]), 2.0);
            if (point_line_distance(pts[i], origin, *direction) >= tolerance ||
                point_line_distance(pts[j], origin, *direction) >= tolerance)
                continue;
            auto m = members_of(origin, *direction);
            if (m.size() >= 2) groups.insert(m);
        }
    std::vector<bool> clustered(count, false);
    for (int i = 0; i < count; ++i) {
        if (clustered[i]) continue;
        Group cluster{i};
        for (int j = i + 1; j < count; ++j) {
            if (!clustered[j] && norm(sub(pts[j], pts[i])) < kCoincidence) {
                clustered[j] = true;
                cluster.push_back(j);
            }
        }
        if (cluster.size() >= 2) groups.insert(cluster);
    }
    return groups;
}

using Segment = std::pair<Vec, Vec>;

double segment_max_line_distance(const Segment& s, const Vec& origin, const Vec& direction) {
    return std::max(point_line_distance(s.first, origin, direction), point_line_distance(s.second, origin, direction));
}

// clash_utils.collinear_alignment_groups
std::set<Group> collinear_groups(const std::vector<Segment>& ends, const std::vector<Vec>& dirs, double tolerance) {
    std::set<Group> groups;
    const int count = static_cast<int>(ends.size());
    if (count < 2) return groups;
    auto members_of = [&](const Vec& origin, const Vec& direction) {
        Group members;
        for (int i = 0; i < count; ++i) {
            if (segment_max_line_distance(ends[i], origin, direction) > tolerance) continue;
            if (std::abs(dot(dirs[i], direction)) < kParallelCosine) continue;
            members.push_back(i);
        }
        return members;
    };
    for (int i = 0; i < count; ++i)
        for (int j = i + 1; j < count; ++j) {
            if (std::abs(dot(dirs[i], dirs[j])) < kParallelCosine) continue;
            const Vec& direction = dirs[i];
            const std::vector<Vec> seed{ends[i].first, ends[i].second, ends[j].first, ends[j].second};
            Vec origin(3, 0.0);
            for (const auto& p : seed) origin = add(origin, p);
            origin = div(origin, 4.0);
            double worst = 0.0;
            for (const auto& p : seed) worst = std::max(worst, point_line_distance(p, origin, direction));
            if (worst >= tolerance) continue;
            auto m = members_of(origin, direction);
            if (m.size() >= 2) groups.insert(m);
        }
    return groups;
}

// clash_utils.coplanar_alignment_groups
std::set<Group> coplanar_groups(const std::vector<Segment>& ends, std::vector<Vec> dirs, double tolerance) {
    std::set<Group> groups;
    const int count = static_cast<int>(ends.size());
    if (count < 2) return groups;
    for (auto& d : dirs) d = div(d, norm(d));
    std::vector<Vec> centers;
    for (const auto& e : ends) centers.push_back(div(add(e.first, e.second), 2.0));
    auto line_members = [&](const Vec& origin, const Vec& direction) {
        Group members;
        for (int i = 0; i < count; ++i) {
            if (segment_max_line_distance(ends[i], origin, direction) > tolerance) continue;
            if (std::abs(dot(dirs[i], direction)) < kParallelCosine) continue;
            members.push_back(i);
        }
        return members;
    };
    auto plane_members = [&](const Vec& origin, const Vec& normal) {
        Group members;
        for (int i = 0; i < count; ++i) {
            const double d = std::max(std::abs(dot(sub(ends[i].first, origin), normal)),
                                      std::abs(dot(sub(ends[i].second, origin), normal)));
            if (d > tolerance) continue;
            if (std::abs(dot(dirs[i], normal)) > kPlaneCosine) continue;
            members.push_back(i);
        }
        return members;
    };
    for (int i = 0; i < count; ++i)
        for (int j = i + 1; j < count; ++j) {
            if (std::abs(dot(dirs[i], dirs[j])) < kParallelCosine) continue;
            const Vec& direction = dirs[i];
            const Vec connect = sub(centers[j], centers[i]);
            const Vec perpendicular = sub(connect, mul(direction, dot(connect, direction)));
            Group m;
            if (norm(perpendicular) <= tolerance) {
                const std::vector<Vec> seed{ends[i].first, ends[i].second, ends[j].first, ends[j].second};
                const auto [origin, fitted] = least_squares_line(seed);
                double worst = 0.0;
                for (const auto& p : seed) worst = std::max(worst, point_line_distance(p, origin, fitted));
                if (worst >= tolerance) continue;
                m = line_members(origin, fitted);
            } else {
                Vec normal = cross(direction, perpendicular);
                normal = div(normal, norm(normal));
                if (std::abs(normal[2]) < kLevelCosine) continue;
                m = plane_members(div(add(centers[i], centers[j]), 2.0), normal);
            }
            if (m.size() >= 2) groups.insert(m);
        }
    return groups;
}

struct AxisObject {
    Vec center;
    Vec main_axis;
    double half_main = 0.0;
    Vec largest_axis;
};

struct AlignementParams {
    std::optional<std::string> axis;  // None / "" = auto, "Vertical", "Horizontal"
    std::string alignment_type = "Plane";
    std::optional<double> tolerance;
    int min_group = 3;
};

class Alignement final : public SetRule<AlignementParams> {
public:
    Variant base_variant() const override { return Variant::BrepWorld; }
    std::vector<Variant> narrow_variants() const override { return {}; }

    void setup() override {
        const auto& p = params();
        if (p.axis && !p.axis->empty() && *p.axis != "Vertical" && *p.axis != "Horizontal")
            throw ConfigError("axis must be None, 'Vertical' or 'Horizontal'");
        if (p.alignment_type != "Line" && p.alignment_type != "Plane")
            throw ConfigError("alignment_type must be 'Line' or 'Plane'");
        if (!p.tolerance) throw ConfigError("tolerance is mandatory and must be a number (in meter)");
        if (*p.tolerance < 0) throw ConfigError("tolerance must be positive");
        if (p.min_group < 1) throw ConfigError("min_group must be an integer >= 1");
    }

    std::vector<Verdict> narrow_set(const std::vector<ElementGeometry>& elements) const override {
        std::vector<Verdict> out(elements.size());
        std::vector<AxisObject> objects;
        std::vector<size_t> where;
        for (size_t e = 0; e < elements.size(); ++e) {
            const auto brep = elements[e].meshed_brep();  // OBB kept in the Session
            if (!brep) continue;
            objects.push_back(axis_object(brep->obb));
            where.push_back(e);
        }
        if (objects.empty()) return out;
        const double tol = *params().tolerance;

        // _compute_offsets
        std::string orientation = params().axis && !params().axis->empty() ? *params().axis : detect(objects);
        std::vector<double> offsets;
        std::vector<Segment> segments;
        for (const auto& o : objects)
            segments.push_back({sub(o.center, mul(o.main_axis, o.half_main)), add(o.center, mul(o.main_axis, o.half_main))});
        if (orientation == "Vertical") {
            std::vector<Vec> plan;
            for (const auto& o : objects) plan.push_back({o.center[0], o.center[1]});
            const auto [origin, direction] = least_squares_line(plan);
            for (const auto& p : plan) offsets.push_back(point_line_distance(p, origin, direction));
        } else {
            std::vector<Vec> endpoints;
            for (const auto& s : segments) {
                endpoints.push_back(s.first);
                endpoints.push_back(s.second);
            }
            if (params().alignment_type == "Plane") {
                const auto [origin, normal] = least_squares_plane(endpoints);
                for (const auto& s : segments)
                    offsets.push_back(std::max(point_plane_distance(s.first, origin, normal),
                                               point_plane_distance(s.second, origin, normal)));
            } else {
                const auto [origin, direction] = least_squares_line(endpoints);
                for (const auto& s : segments) offsets.push_back(segment_max_line_distance(s, origin, direction));
            }
        }

        // _compute_groups
        std::set<Group> groups;
        if (orientation == "Vertical") {
            std::vector<Vec> pts;
            std::vector<std::optional<Vec>> dirs;
            for (const auto& o : objects) {
                pts.push_back({o.center[0], o.center[1]});
                if (std::abs(o.main_axis[2]) >= kVerticalCosine) {
                    dirs.push_back(std::nullopt);
                } else {
                    const Vec plan{o.main_axis[0], o.main_axis[1]};
                    dirs.push_back(div(plan, norm(plan)));
                }
            }
            groups = plan_groups(pts, dirs, tol);
        } else {
            std::vector<Vec> dirs;
            for (const auto& o : objects) dirs.push_back(o.main_axis);
            groups = params().alignment_type == "Plane" ? coplanar_groups(segments, dirs, tol)
                                                        : collinear_groups(segments, dirs, tol);
        }

        // _clash_flags
        if (params().min_group <= 1) return out;
        std::set<int> passing;
        for (const auto& g : groups)
            if (static_cast<int>(g.size()) >= params().min_group) passing.insert(g.begin(), g.end());
        for (size_t i = 0; i < objects.size(); ++i) {
            if (passing.count(static_cast<int>(i))) continue;
            Verdict& v = out[where[i]];
            v.status = true;
            v.measures.set(Measure::Offset, offsets[i]);
        }
        return out;
    }

private:
    // Alignement._collect_axis_data
    static AxisObject axis_object(const Bnd_OBB& obb) {
        const gp_XYZ c = obb.Center();
        const gp_XYZ d[3] = {obb.XDirection(), obb.YDirection(), obb.ZDirection()};
        const Vec dirs[3] = {{d[0].X(), d[0].Y(), d[0].Z()}, {d[1].X(), d[1].Y(), d[1].Z()}, {d[2].X(), d[2].Y(), d[2].Z()}};
        const double half[3] = {obb.XHSize(), obb.YHSize(), obb.ZHSize()};
        std::vector<int> horizontal;
        for (int i = 0; i < 3; ++i)
            if (std::abs(dirs[i][2]) < kVerticalCosine) horizontal.push_back(i);
        std::stable_sort(horizontal.begin(), horizontal.end(), [&](int a, int b) { return half[a] > half[b]; });
        int largest = 0;
        for (int i = 1; i < 3; ++i)
            if (half[i] > half[largest]) largest = i;
        const int main = horizontal.size() >= 2 && half[horizontal[0]] >= kFootprintElongation * half[horizontal[1]]
                             ? horizontal[0]
                             : largest;
        return {{c.X(), c.Y(), c.Z()}, dirs[main], half[main], dirs[largest]};
    }

    static std::string detect(const std::vector<AxisObject>& objects) {
        int votes = 0;
        for (const auto& o : objects)
            if (std::abs(o.largest_axis[2]) >= kVerticalCosine) ++votes;
        return votes >= static_cast<int>(objects.size()) - votes ? "Vertical" : "Horizontal";
    }
};

}  // namespace

RuleSpec spec_alignement() {
    return RuleSpec::set<Alignement>(
        "Alignement", "Alignement", {Slot::Source},
        "Flags the elements that are not part of an aligned group of at least min_group elements.",
        {param(&AlignementParams::axis, "axis").doc("Axis (empty = auto)").values({"", "Vertical", "Horizontal"}),
         param(&AlignementParams::alignment_type, "alignment_type").doc("Alignment type").values({"Line", "Plane"}),
         param(&AlignementParams::tolerance, "tolerance").doc("Tolerance").unit(Unit::Metre),
         param(&AlignementParams::min_group, "min_group").doc("Minimum group size")});
}

}  // namespace ifcclash
