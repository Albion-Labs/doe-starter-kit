# DOE Proof Kit — Tasks

**Mission:** Prove DOE catches real defects (deterministically) and improves real-world outcomes (honestly), in a way a company could sell — a scorecard that stands alone for a sales call now and feeds HQ later.

**Decisions (resolved):** subsystem inside `~/doe-starter-kit` (`proof/`); fully synthetic, project-agnostic fixture; developed on `feature/proof-kit` (worktree-isolated), landed via PR. Data contract locked at schemaVersion 1.0, additive-only. Full design in `SPEC.md`.

**Status:** PK-0, PK-1, PK-2 COMPLETE — the call-ready set. PK-3+ remain.

---

## Current

*(empty — PK-3 promotes here on go)*

---

## Queue

### PK-3 — Real-project metrics extractor  *(Thing 2: prove it on real projects)*
Read git history -> change-failure-rate, rework-rate, lead-time -> same-schema JSON. Honest economics.
- [ ] Build `proof/metrics.py --repo <path>` -> `out/metrics.json`
- [ ] CFR + rework (rework moves first) + lead-time guardrail
- [ ] Economics module with NIST/Boehm-sourced constants
Contract:
- [auto] Verify: run: `python3 proof/metrics.py --repo fixtures/with-history --json` -- exit 0
- [auto] Verify: run: `python3 schema/validate.py out/metrics.json` -- exit 0
- [auto] Verify: run: `! grep -rEi "100x|IBM Systems Sciences" proof/economics/` -- exit 0 (no folklore)
- [manual] Metrics match hand-computed values on the known fixture.

### PK-4 — CI regression + growing corpus
- [ ] `.github/workflows/proof.yml` runs the harness on push
- [ ] Append-only corpus integrity check
- [ ] History time-series accumulation in scorecard
Contract:
- [auto] Verify: file: `.github/workflows/proof.yml` exists
- [auto] Verify: run: `python3 proof/run.py --self-test` -- exit 0 (CI gate)
- [manual] A deliberately-introduced escaped defect can be promoted into the corpus in one step.

### PK-5 — Self-pruning ablation  *(prove DOE cuts its own theatre)*
- [ ] Build `proof/ablation.py` -> per-ceremony marginal catch report
- [ ] Emit `ablation` block into scorecard
Contract:
- [auto] Verify: run: `python3 proof/ablation.py --json` -- exit 0
- [manual] Report credibly separates load-bearing gates from ceremony.

### PK-6 — HQ integration  *(DEFERRED — blocked on HQ existing)*
HQ reads the PK-0 schema across projects. Listed only to fix the interface boundary.

---

## Done

### PK-0 — Pin the data contract  *(commit e7ca1fa)*
- [x] `schema/scorecard.schema.json` (v1.0, additive-only)
- [x] 2 valid examples + dependency-free `schema/validate.py`
- Verified: examples validate, negative-control broken scorecard correctly rejected.

### PK-1 — Fault-injection harness  *(commit 12e1722)*
- [x] Synthetic fixture + 7-fault corpus (F01-F07), trigger strings stored split
- [x] `run.py` invokes the REAL unmodified kit gates, scores catch-rate
- [x] Control pass (0/7) + provenance (gate sha256 + kit commit)
- Verified: 6/6 covered classes caught; F07 honest miss; `--self-test` PASS.

### PK-2 — Standalone HTML scorecard
- [x] `render.py` json -> self-contained themed HTML
- [x] `README.md` reproduction guide + `sample/` reference card
- Verified: renders, has `[data-catch-rate]`, zero external refs.

---

## Sequencing
PK-0 -> PK-1 -> PK-2 (done, call-ready) -> PK-3 -> PK-4 -> PK-5. PK-6 deferred.
