# DOE Proof Kit — Tasks

**Mission:** Prove DOE catches real defects (deterministically) and improves real-world outcomes (honestly), in a way a company could sell.

**Decisions (resolved):** subsystem inside `~/doe-starter-kit` (`proof/`); fully synthetic, project-agnostic fixture; developed on `feature/proof-kit` (worktree-isolated), landed via PR. Data contract locked at schemaVersion 1.0, additive-only. Full design in `SPEC.md`.

**Status:** PK-0 through PK-5 COMPLETE. Only PK-6 (HQ integration) deferred.

---

## Current
*(empty)*

## Queue

### PK-6 — HQ integration  *(DEFERRED — blocked on HQ existing)*
HQ reads the PK-0 schema across projects. Listed only to fix the interface boundary.

---

## Done

### PK-0 — Data contract  *(e7ca1fa)*
Schema v1.0 (additive-only) + dependency-free validator + 2 examples. Negative-control broken scorecard correctly rejected.

### PK-1 — Fault-injection harness  *(12e1722)*
Synthetic fixture + 7-fault corpus; `run.py` invokes the REAL unmodified kit gates; 6/6 covered classes caught, F07 honest miss (86%), control 0/7.

### PK-2 — HTML scorecard + reproduction  *(1c41d62)*
`render.py` self-contained themed card; `README.md` reproduction/audit guide; provenance (gate sha256 + kit commit); `sample/` reference card.

### PK-3 — Real-project metrics  *(f8846c1)*
`metrics.py` git-proxy DORA (CFR, rework, lead-time, deploy-freq) + sourced economics (NIST/Boehm, no folklore). Self-test: CFR 0.25 / rework 0.375.

### PK-4 — CI gate + corpus integrity  *(59bdb13)*
`corpus_check.py` append-only integrity; `.github/workflows/proof.yml` re-runs the whole benchmark on every proof/ change.

### PK-5 — Self-pruning ablation
`ablation.py` marginal-catch per gate; all 3 gates load-bearing, 0 candidate-to-cut. Ceremony-level ablation flagged as future work.

---

## Sequencing
PK-0 -> PK-1 -> PK-2 -> PK-3 -> PK-4 -> PK-5 done. PK-6 deferred (needs HQ).
