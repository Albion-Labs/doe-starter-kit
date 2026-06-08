# DOE Proof Kit — Specification

**Status:** Draft for approval (2026-06-08). Nothing built yet.
**Owner:** Albion Labs.
**One-line:** A self-measurement system that proves — deterministically and honestly — that DOE catches real defects and improves real-world outcomes, producing a scorecard that stands alone for a sales call today and feeds HQ as a product surface tomorrow.

---

## 0. Why this exists (the honest frame)

Research finding that anchors everything: **nobody in the industry can cleanly prove a dev tool improves outcomes.** GitHub's "55% faster" was a greenfield toy task; the one rigorous RCT (METR 2025) found AI made *expert* devs 19% slower while they felt faster; the "bugs cost 100x more in production" stat is folklore with no traceable source.

So the goal is **not** "prove DOE makes everything better" — that bar is unclearable by anyone. The goal is:

1. Prove the **narrow, deterministic claim hard**: DOE's gates catch defined classes of defect, reproducibly. (This is the on-brand part — "deterministic" is in the name.)
2. Measure the **probabilistic outcome claims honestly**: change-failure-rate and rework-rate trending down on real projects, with velocity as a guardrail — labelled as directional, never overclaimed.
3. **Be more honest than the competition** — including pruning DOE's own ceremony where it catches nothing. Honesty is the moat.

Full research backing lives in the session history; key sources: METR RCT, DX Core 4 (DORA+SPACE+DevEx), mutation testing / SWE-bench Verified / chaos engineering (the "inject known faults, measure catch-rate" lineage), Fagan/Capers Jones (review efficacy is solid), NIST $59.5B (defensible macro cost), and the debunking of the IBM "100x" figure.

---

## 1. Two distinct things (do not conflate)

| | Thing 1 — Prove the **framework** | Thing 2 — Prove it on **real projects** |
|---|---|---|
| Question answered | "Does DOE catch real defect classes?" | "Is my project measurably sounder with DOE?" |
| Method | Fault injection against a fixture | Read git history → outcome metrics |
| Cadence | One-time-ish + CI on each kit release | Continuous, per project |
| Output | Catch-rate scorecard (the call artifact) | DORA/rework/£ scorecard (the product) |
| Feeds HQ? | No — standalone | **Yes** |

---

## 2. Architecture — three layers, one interface

**Layer A — Engine (backend, lives in / PRs to the DOE kit).**
Deterministic Python scripts, same pattern the kit already uses (`wrap_stats.py` → `stats.json`). Each emits structured JSON only. No UI, no styling.

**Layer B — Data contract (the hinge — Section 4).**
One JSON schema every scorecard conforms to. This is the interface between the engine and *all* surfaces. Pin it first; both this workstream and the HQ workstream build against it so they never diverge.

**Layer C — Surfaces (frontend).**
- *Now:* self-contained themed HTML scorecard (reuse `/wrap` card aesthetic). Zero infra. The call artifact.
- *Later:* **HQ** consumes the same JSON across all projects. Out of scope here — this kit makes HQ *substantive* (proof) instead of a prettier GitHub (ops). Building HQ's charts before this engine = the exact "trust me bro" demo we are avoiding.

---

## 3. Fault corpus design (Thing 1)

Each fault is a labelled, reversible mutation mapped to the DOE gate that should catch it. Mutation-testing logic: inject a known defect, confirm the gate fires; `caught ÷ injected` = catch-rate (the real metric — coverage is the vanity metric).

| ID | Defect class | Injected fault | Gate expected to fire |
|----|--------------|----------------|------------------------|
| F01 | Leaked secret | hard-coded API key in source | `block_secrets_in_code` |
| F02 | Left-in stub | `TODO`/`raise NotImplementedError` | health check / `audit_claims` |
| F03 | False claim | untrue statement in docs/site copy | `/fact-check` + claim audit |
| F04 | Broken build | syntax/type error | contract `[auto]` verify |
| F05 | Unmarked step | commit refs "Step N", todo.md not updated | commit-msg step-mark hook |
| F06 | Silent regression | break an earlier feature's behaviour | test-suite / invariants |
| F07 | Direct-to-main | commit straight to main | main-branch protection |
| F08 | Secret-shaped env write | redirect secret into tracked file | `block_secrets_in_code` (Bash branch) |

Corpus is **append-only with a manifest**: every defect that ever escapes a real project becomes a new permanent fault (the Braintrust/LangSmith "each escape becomes a regression test" pattern). Scored as a CI regression over time.

---

## 4. Data contract (PROPOSED — pin in Phase 0)

```jsonc
{
  "schemaVersion": "1.0",
  "kind": "framework-benchmark" | "project-metrics",
  "project":     { "id": "string", "name": "string", "repo": "string|null" },
  "generatedAt": "ISO-8601",

  // Thing 1 — deterministic catch-rate
  "catchRate": {
    "injected": 8,
    "caught":   8,
    "rate":     1.0,
    "byGate": [
      { "gate": "block_secrets_in_code", "defectClass": "leaked-secret",
        "injected": 1, "caught": 1 }
    ],
    "control": { "injected": 8, "caught": 0, "rate": 0.0 }   // gates-off baseline
  },

  // Thing 2 — real-world outcomes (DORA + rework)
  "dora": {
    "changeFailureRate":      0.04,
    "reworkRate":             0.11,   // moves first — defects shifted left
    "leadTimeHours":          6.2,    // guardrail: gate must not inflate this
    "deployFrequencyPerWeek": 9.0,
    "window": { "from": "ISO", "to": "ISO" }
  },

  // economics — DEFENSIBLE sources only, never the 100x folklore
  "economics": {
    "poundsSaved": 0.0,
    "model":   "string (named, sourced model)",
    "sources": ["NIST 2002 $59.5B", "Boehm-Basili 5:1 small-system"]
  },

  "defectsCaught": [
    { "id": "F01", "class": "leaked-secret", "gate": "block_secrets_in_code",
      "caughtAt": "ISO", "estimatedCostGBP": 0.0, "costBasis": "string" }
  ],

  // self-pruning ablation — which ceremony actually contributes
  "ablation": [
    { "ceremony": "review-gate", "marginalCatch": 2, "verdict": "load-bearing" },
    { "ceremony": "retro-step-X", "marginalCatch": 0, "verdict": "candidate-to-cut" }
  ],

  "history":    [ { "at": "ISO", "catchRate": 1.0, "changeFailureRate": 0.04, "reworkRate": 0.11 } ],
  "perception": { "dxiScore": null, "frictionFlag": false }   // optional, SPACE/DXI
}
```

---

## 5. Honesty guardrails (enforced as contracts, not promises)

- **No folklore:** economics module must not contain the "100x" figure or cite the non-existent "IBM Systems Sciences Institute." Enforced by a deterministic grep gate.
- **Label confidence:** any outcome number ships with N + method; framework-benchmark vs project-metrics never mixed in one claim.
- **Falsifiable:** each gate test is framed as a hypothesis the harness tries to *disprove*; an untested gate is reported as "unproven", not "passing".
- **Self-pruning:** the ablation arm (gates-only vs full ceremony) flags any ceremony with zero marginal catch as a candidate to cut. We attack DOE harder than the buyer can.

---

## 6. Decisions (resolved 2026-06-08)

1. **Location — RESOLVED:** a subsystem **inside `~/doe-starter-kit`** (e.g. `proof/` scripts + a `/doe-prove` command). Belongs to the framework, not any project.
2. **Fixture — RESOLVED:** a **fully synthetic, project-agnostic** mini-project. No reference to any real client or project anywhere in the kit — the proof system is agnostic of all projects.
3. **Workflow — RESOLVED:** developed on a **kit feature branch and landed via PR** — never committed directly to the kit's `main` (honors the kit-PR convention + `guard_kit_writes`). This is the reconciliation of "inside as a subsystem" (final home = the kit) with "don't build directly into the kit" (path = branch + PR, not direct-to-main).
4. **HQ interface — OPEN (being explained):** lock the §4 JSON shape now as `schemaVersion 1.0` so the HQ workstream reads a stable contract and nothing has to be re-done later.
