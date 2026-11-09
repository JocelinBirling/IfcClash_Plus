// IfcClash_Plus engine — one function per rule: its RuleSpec (rules/<Rule>.cpp).
#pragma once

#include "../registry/RuleSpec.h"

namespace ifcclash {

RuleSpec spec_volume();
RuleSpec spec_intersection();
RuleSpec spec_clearance();
RuleSpec spec_collision();

}  // namespace ifcclash
