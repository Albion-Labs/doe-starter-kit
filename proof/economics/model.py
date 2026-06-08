"""Sourced, conservative remediation-cost model for the DOE Proof Kit.

We translate "a defect caught before merge" into money saved using only
defensible, named sources -- and we deliberately reject the unsourced
cost-curve folklore (the oft-repeated hundred-fold lifecycle multiplier that
traces back to an internal training slide with no published study behind it).

Anchors:
  - NIST 2002, "The Economic Impacts of Inadequate Infrastructure for Software
    Testing": software defects cost the US economy roughly $59.5B per year.
  - Boehm & Basili 2001, "Software Defect Reduction Top 10 List": for small,
    non-critical systems the fix-cost ratio is about 5 to 1 (not the inflated
    figure). We use this modest 5:1 ratio.
"""

PRE_MERGE_FIX_COST_GBP = 15.0      # conservative: a few minutes of dev time at review
POST_MERGE_FIX_RATIO = 5.0         # Boehm-Basili small-system ratio (5:1)

MODEL = "defects_caught x pre_merge_cost x (5:1 Boehm-Basili ratio - 1), conservative"
SOURCES = ["NIST 2002 (~$59.5B/yr US macro)", "Boehm-Basili 2001 (5:1 small-system fix ratio)"]


def pounds_saved(defects_caught_pre_merge):
    n = int(defects_caught_pre_merge or 0)
    if n <= 0:
        return 0.0
    avoided_per_defect = PRE_MERGE_FIX_COST_GBP * (POST_MERGE_FIX_RATIO - 1.0)
    return round(n * avoided_per_defect, 2)
