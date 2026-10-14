# Description

> **Status: Specification** — this rule is not implemented yet; this page describes the target behavior. The implementation should include the Blondel law (2 × riser height + going between 60 and 64 cm, or 60–65 cm depending on the standard) as a derived criterion.

This rule checks the geometric conformity of a stair (step height,
going, regularity, flight width) against standard stair metrics.

The steps are not selected as elements: the rule reconstructs them
from the geometry of the stair alone. The source objects are sliced
by altitude to detect the steps, the walking line is rebuilt from the
detected steps, and the measurements are taken step by step along it.

Although it analyzes a single object, this rule is more complex than
a plain measurement rule: it decomposes one object into functional
sub-objects (the steps) before measuring them. It stays a one object
rule: everything is derived from the source geometry, no target and
no context selection are involved.

Out of scope: the guardrail (main courante) height. It needs the
guardrail as a second object, so it is covered by a separate two
objects rule (stair + guardrail), not by StairQuality.

# Property

Source: The stairs to analyze (IfcStair, IfcStairFlight or any
element typed as a stair). The steps are reconstructed from this
geometry; they must not be selected.

Parameters:

- **Step height min / max**: the allowed range for the riser height
  of each step. A step outside the range is non conforming.
- **Going min** (giron): the minimum tread depth, measured along the
  walking line between two consecutive step noses.
- **Regularity tolerance**: all the steps of a flight must be
  identical within this tolerance (a flight is non conforming as
  soon as one step deviates from the others by more than the
  tolerance).
- **Flight width min**: the minimum clear walking width of the
  flight, measured across the reconstructed steps along the walking
  line.
- **Walking line offset**: the position of the walking line used for
  the measurements, as a distance from the inner edge of the flight
  (default: the center of the flight).

# Result

One ClashResult per stair and per non conforming criterion. A stair
failing both the step height and the going produces two results, one
per criterion, each carrying the measured values and the offending
steps.

This granularity keeps the result atomic: one result is one
verdictable fact, ready for the sorting phase and the BCF subjects
(see specification_BCF_Link.md).

# Example

- ERP conformity: step height between 16 and 18 cm, going of at least
  24 cm, all steps identical within 5 mm.
- Accessibility: the flight width between the handrails must stay
  above 1.40 m.
- In Select: output the non conforming stairs for architectural
  rework.
