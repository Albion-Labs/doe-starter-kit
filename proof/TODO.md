# DOE Proof Kit — Tasks

**Mission:** Prove DOE catches real defects (deterministically) and improves real-world outcomes (honestly), in a way a company could sell — a scorecard that stands alone for a sales call now and feeds HQ later.

**Scope guard — what this is NOT:** not building HQ; not a marketing deck; not a causal-proof claim (no one can make one). We build the *engine + data contract + standalone scorecard*. HQ consumes the output later.

**Decisions (resolved):** subsystem **inside `~/doe-starter-kit`** (`proof/` + future `/doe-prove`); **fully synthetic, project-agnostic** fixture (no real project referenced anywhere); developed on a **kit feature branch (`feature/proof-kit`), landed via PR** (never direct-to-main). Data contract locked at **schemaVersion 1.0, additive-only** (new fields never bump the version; renames/removals do). Full design in `SPEC.md`.

**Status:** PK-0 COMPLETE (this session). PK-1 next.

---

## Current

*(empty — PK-1 promotes here on go)*

---

## Queue

### PK-1 — Fault-injection harness  *(Thing 1: prove the framework — the call artifact)*
Fixture + labelled fault corpus + injector/runner + scorer -> catch-rate JSON.
- [ ] Build synthetic fixture project (clean, build passes, baseline green)
- [ ] Encode fault corpus F01-F08 (SPEC section 3) as reversible mutations + manifest
- [ ] Build `proof/run.py`: for each fault -> inject -> run gate -> record caught/missed -> revert
- [ ] Add control pass (gates off) to establish the ~0 baseline
- [ ] Emit `out/scorecard.json` conforming to PK-0 schema

Contract:
- [auto] Verify: run: `python3 proof/run.py --self-test` -- exit 0
- [auto] Verify: run: `python3 schema/validate.py out/scorecard.json` -- exit 0
- [auto] Verify: run: `python3 proof/run.py --assert-catch-rate 1.0` -- exit 0 (all seeded faults caught)
- [auto] Verify: run: `python3 proof/run.py --assert-control 0.0` -- exit 0 (gates-off catches nothing -> proves the delta)
- [auto] Verify: file: `proof/corpus/manifest.json` exists
- [manual] Fault corpus is representative of defects a non-engineer would actually ship.

### PK-2 — Standalone HTML scorecard  *(Surface 1: what you open on the call)*
Render `scorecard.json` -> self-contained themed HTML (reuse `/wrap` card aesthetic).
- [ ] Build `proof/render.py` (json -> single self-contained html)
- [ ] Apply Palantir/Raycast/arcade-leaning theme
- [ ] Show: catch-rate vs control, per-gate breakdown, "untested = unproven" honesty row

Contract:
- [auto] Verify: run: `python3 proof/render.py out/scorecard.json out/scorecard.html` -- exit 0
- [auto] Verify: html: `out/scorecard.html` has `[data-catch-rate]`
- [auto] Verify: run: `! grep -E "https?://" out/scorecard.html` -- exit 0 (self-contained, no external deps)
- [manual] Visually on-brand and credible to show a skeptical non-engineer.

### PK-3 — Real-project metrics extractor  *(Thing 2: prove it on real projects)*
Read git history -> change-failure-rate, rework-rate, lead-time -> same-schema JSON. Honest economics.
- [ ] Build `proof/metrics.py --repo <path>` -> `out/metrics.json`
- [ ] Implement CFR + rework (rework moves first) + lead-time guardrail
- [ ] Economics module with NIST/Boehm-sourced constants

Contract:
- [auto] Verify: run: `python3 proof/metrics.py --repo fixtures/with-history --json` -- exit 0
- [auto] Verify: run: `python3 schema/validate.py out/metrics.json` -- exit 0
- [auto] Verify: run: `! grep -rEi "100x|IBM Systems Sciences" proof/economics/` -- exit 0 (no folklore)
- [manual] Metrics match hand-computed values on the known fixture.

### PK-4 — CI regression + growing corpus  *(make it falsifiable over time)*
Wire catch-rate into CI; each escaped defect appends to the corpus; track history.
- [ ] `.github/workflows/proof.yml` runs the harness on push
- [ ] Append-only corpus integrity check
- [ ] History time-series accumulation in scorecard

Contract:
- [auto] Verify: file: `.github/workflows/proof.yml` exists
- [auto] Verify: run: `python3 proof/corpus_check.py` -- exit 0 (append-only integrity holds)
- [auto] Verify: run: `python3 proof/run.py --append-history && python3 schema/validate.py out/scorecard.json` -- exit 0
- [manual] A deliberately-introduced escaped defect can be promoted into the corpus in one step.

### PK-5 — Self-pruning ablation  *(prove DOE cuts its own theatre)*
Gates-only vs full-ceremony arm -> marginal catch per ceremony -> flag zero-catch ceremonies.
- [ ] Build `proof/ablation.py` -> per-ceremony marginal catch report
- [ ] Emit `ablation` block into scorecard
- [ ] Document any ceremony flagged "candidate-to-cut"

Contract:
- [auto] Verify: run: `python3 proof/ablation.py --json` -- exit 0
- [auto] Verify: run: `python3 schema/validate.py out/scorecard.json` -- exit 0 (ablation block present & valid)
- [manual] Report credibly separates load-bearing gates from ceremony, and we act on at least one finding.

### PK-6 — HQ integration  *(DEFERRED — blocked on HQ existing)*
Not in this workstream. HQ reads the PK-0 schema across projects. Listed only to fix the interface boundary.

---

## Done

### PK-0 — Pin the data contract  *(the hinge)*
The JSON schema every scorecard conforms to and that HQ will also build against. Locked at v1.0, additive-only.
- [x] Write `schema/scorecard.schema.json` (from SPEC section 4)
- [x] Add 2 valid examples under `schema/examples/`
- [x] Add a dependency-free validator script `schema/validate.py`

Contract:
- [auto] Verify: file: `schema/scorecard.schema.json` exists
- [auto] Verify: run: `python3 schema/validate.py schema/examples/` -- exit 0 (examples validate)
- [auto] Verify: file: `schema/scorecard.schema.json` contains `catchRate`
- [auto] Verify: file: `schema/scorecard.schema.json` contains `reworkRate`
- [manual] Schema covers catch-rate, DORA, economics, ablation, history — acceptable as the HQ interface.

---

## Sequencing

PK-0 (done) -> PK-1 + PK-2 (the call-ready artifact) -> PK-3 -> PK-4 -> PK-5. PK-6 deferred.
**Minimum for the call:** PK-0, PK-1, PK-2.
