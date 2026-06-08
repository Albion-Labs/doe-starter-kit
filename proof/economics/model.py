"""Sourced, conservative remediation-cost model for the DOE Proof Kit.

We translate "a defect caught before merge" into money saved using defensible,
named sources -- and we deliberately reject the unsourced cost-curve folklore
(the oft-repeated hundred-fold lifecycle multiplier that traces back to an
internal training slide with no published study behind it).

Honesty note: of the two constants below, ONE is sourced and ONE is an explicit
assumption -- we label which is which rather than dressing a guess as data.
  - POST_MERGE_FIX_RATIO (5:1)  -- SOURCED. Boehm & Basili 2001, "Software Defect
    Reduction Top 10 List": for small, non-critical systems the fix-cost ratio is
    about 5 to 1 (not the inflated figure).
  - PRE_MERGE_FIX_COST_GBP      -- ASSUMPTION, not from a source: roughly a few
    minutes of developer time to fix at review. Set low and conservative on
    purpose. Treat poundsSaved as illustrative, not audited.
Macro context (not used in the formula): NIST 2002 put US software-defect cost at
roughly $59.5B/year.
"""

PRE_MERGE_FIX_COST_GBP = 15.0      # ASSUMPTION (unsourced, conservative)
POST_MERGE_FIX_RATIO = 5.0         # SOURCED: Boehm-Basili small-system 5:1

MODEL = "defects_caught x pre_merge_cost(ASSUMED GBP15) x (Boehm-Basili 5:1 ratio - 1)"
SOURCES = [
    "Boehm-Basili 2001 (5:1 small-system fix ratio) -- SOURCED",
    "pre-merge fix cost GBP15 -- ASSUMPTION, not sourced",
    "NIST 2002 (~$59.5B/yr US macro) -- context only",
]


def pounds_saved(defects_caught_pre_merge):
    n = int(defects_caught_pre_merge or 0)
    if n <= 0:
        return 0.0
    avoided_per_defect = PRE_MERGE_FIX_COST_GBP * (POST_MERGE_FIX_RATIO - 1.0)
    return round(n * avoided_per_defect, 2)
