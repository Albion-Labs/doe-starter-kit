# DOE v2.0 — Lean Core + Proof-of-Life

**Status:** PLANNED, decisions resolved · **Source:** Fable full-kit review 2026-06-10, decisions 2026-06-11 · **Owner:** William
**Drop this file at:** `~/doe-starter-kit/.claude/plans/doe-v2-lean-proof-of-life.md`

## North star

DOE v1 proved the premise: probabilistic AI + deterministic guardrails. DOE v2 fixes the part v1 got wrong: the guardrails themselves became probabilistic — they exist, but whether they fire is unverified. v2 has two moves:

1. **Lean:** delete everything Claude Code now does natively, everything with zero callers, and everything serving an audience that no longer exists. Target: ~88k tracked lines → ~42k.
2. **Proof-of-life:** every surviving control (hook, scenario, directive, command) must demonstrably fire — proven by fault injection in CI and a liveness ledger — or it gets culled. The kit becomes empirical about itself.

Positioning: **Claude Code owns the harness layer** (commands→skills, subagents, workflows, memory, worktrees, code review, scheduling). **DOE owns the accountability layer**: contracts (`verify.py`), claim auditing, deterministic project state (STATE/todo ritual), cross-project ops (HQ), and gates that prove they work (`proof/`). Anything Anthropic ships natively, we delete within one release.

## Decisions — RESOLVED 2026-06-11 (do not re-litigate)

| # | Decision | Outcome |
|---|---|---|
| 1 | Wave stack (~3,950 lines) | **DELETE.** Git history is the archive. |
| 2 | Flutter/Go/Rust templates + `.maestro/` | **KEEP.** Revisit at first `/cull` with usage data. |
| 3 | Political layer | **KEEP.** Revisit at first `/cull`. |
| 4 | `/eod` + `eod_html.py` | **KEEP.** The liveness ledger will answer this empirically at first `/cull`. |
| 5 | doe_init TUI | **KEEP.** Living polish; doctrine targets dead controls, not enjoyment. |
| 6 | Docs site | **KEEP the site, generate it, prune during conversion** (one pass; no deferred editorial pass). |
| 7 | Plugin packaging | **DEFER to v2.1.** Package the lean surface once. Pull forward only if the setup.sh merge footgun bites again. |

---

## Workstream 1 — The Cut

### Phase 0: pure wins, no judgement calls (1 session, 1 PR)
- [ ] Unregister `heartbeat.py` + `context_monitor.py` from `~/.claude/settings.json` (PostToolUse `*` block — 2 python spawns on every tool call for a dead wave system + a natively-superseded context monitor).
- [ ] Delete orphans: `execution/stamp_kit_version.py` (zero refs), `execution/logger.py` (zero importers), `execution/verify_tests.py` (never executed), `execution/scan_docs.py` (requires `docs/docs-manifest.json`, which has never existed in git history) + remove its instruction at `directives/delivery-rules.md:111`, `tests/security/` (zero consumers), `proof/live/index.html` (verify unreferenced first).
- [ ] `git worktree remove .claude/worktrees/v2-roadmap-doc` (4.5MB stale copy polluting greps).
- [ ] Resolve the release contradiction: delete `starter-kit-sync.md` Step 11 manual-release walkthrough (~110 lines) — `auto-release.yml` owns releases since v1.65.0 and the manual sequence would race the workflow with opposite tag ordering. Leave a one-line pointer to `kit-development.md` ## Release mechanics.
- [ ] Fix `global-commands/commands.md` hardcoded "24 expected commands" → derive from directory.
- [ ] Adopt `~/.claude/scripts/gist_sync.py` into `global-scripts/` (unversioned dependency of `/wrap` and `/eod`).
- [ ] Move `execution/bootstrap_invariants.py` → `migrations/`; move `execution/test_doe_init.py` → `tests/execution/test_doe_init_integration.py` (same-basename trap).

### Phase 4: wave deletion + command pruning (after sensors are live)
- [ ] Delete wave stack: `global-scripts/multi_agent.py`, `global-scripts/dispatch_dag.py`, `global-hooks/heartbeat.py`, `global-commands/agent-launch.md`, `global-commands/agent-status.md`; strip wave branches from `agent-verify.md` (keep solo mode) and `context_monitor.py` (or delete the monitor outright — natively superseded); delete `global-scripts/doe_utils.py` if no remaining importer. Delete `docs` wave content (`multi-agent.html` dies in the docs conversion anyway). Strip the `dispatch_dag` prompt from `crack-on.md`; retire `serial-dispatch-protocol.md` wave references during the directive merge.
- [ ] Merge `stand-up.md` into `crack-on.md` (kick-off mode) + `sitrep.md` (status mode).
- [ ] Trim `report-doe-bug.md` 328→~50 lines; `request-doe-feature.md` 81→~15 (internal-only — you file issues against yourself).
- [ ] Delete `codemap.md` + `project-recap.md` (superseded by auto-memory + `/context`).
- [ ] Delete `worktree-create.md`/`worktree-remove.md`; keep the sibling-naming convention as a 10-line note in `context-management.md`.

### Phase 4b: structural merges
- [ ] Extract shared `execution/doe_checks.py`: the 8 checks duplicated line-for-line between `test_methodology.py` and `audit_claims.py` (~400 lines, kills divergence risk).
- [ ] Merge `doe_bug_report.py` + `doe_feature_request.py` around a shared gh-issue core (`_run`/`sanitise` byte-identical).
- [ ] `execution/_lib.py`: one `find_project_root()` + ANSI/box helpers (4 drifting copies today).
- [ ] Directive consolidation (~1,000 lines): merge serial-dispatch + subagent-protocol → `dispatch.md`; fold chrome-verification → testing-strategy; single breach-timeline copy across data-safety/incident-response; delete `documentation-governance.md`, `integrations.md`, `framework-evolution.md`, `parallel-worktrees.md`; strip self-referential "this directive exists" verification checklists; resolve the perf-budget contradiction (testing-strategy vs delivery-rules); remove political residue from universal directives (delivery-rules L96) — the political *layer* stays, residue in universal files goes.
- [ ] Archive CHANGELOG pre-v1.50 → `CHANGELOG-archive.md` (verify `generate_whats_new.py` + migration greps only read recent sections); archive `migrations/v1.59–v1.60` once every project's `.doe-version` ≥ v1.62 (check first).
- [ ] Generate framework `claude_section.md` from `scaffold.json` at init time (6 files, one drift class).
- [ ] Move shipped test templates `tests/` → `templates/tests/`, and `playwright.config.js` under `templates/` (stops kit CI detecting itself as a Playwright project).

---

## Workstream 2 — Docs site: keep it, generate it, prune in the same pass

**Decision: site stays, same look/URL structure, generated from markdown, content pruned during conversion (Option A — one pass).** Today: 19 hand-written pages, 34,349 lines, 60.5% duplicated boilerplate, 19 drifted CSS copies + a 20th inside `generate_whats_new.py`, zero pages documenting `doe init`.

### Architecture
```
docs-src/                 # single human-facing content source (markdown + front-matter)
docs/tutorial/assets/     # site.css (ONE stylesheet, ~1,200 lines) + site.js (ONE copy)
docs/nav.json             # sidebar defined once
execution/build_docs.py   # ~400-600 lines: markdown → HTML via one template
```
- Template extracted from `generate_whats_new.py`; that script then imports the shared module (−600 lines, kills the 20th copy).
- Version stamped at build time, build wired into `auto-release.yml` → delete `stamp_tutorial_version.py` and the stamp-20-files release tax; pre-push docs gate becomes "build is current".
- Where a page explains a directive (self-annealing, testing, workflows), render the directive itself — prose Claude enforces ≡ prose you read.
- Hooks documented in ONE markdown source → one generated page (currently 4 copies, 2 contradictory).

### Content map (prune-during-conversion)
- **Dies:** `ide-setup.html`; terminal lessons in `getting-started.html`; git-basics half of glossary; marketing hero on `index.html` (→ plain hub); `multi-agent.html` (false after wave deletion); FAQ dissolved into relevant pages.
- **Merges:** `getting-started` + `new-project` + `first-session` → one "Start a project" page rebuilt around `doe init`; `troubleshooting` + `tips-and-mistakes` → one recovery page.
- **Survives updated:** commands (generated from `global-commands/` frontmatter so it can't drift), key-concepts, daily-flow, workflows, testing, context, pr-workflow, DOE glossary, whats-new (untouched).
- Target: ~10–12 pages, every one accurate, internal tone matching `introduction.md`.

**Verification:** screenshot-diff surviving pages against the live site for theme/layout fidelity; content accuracy via `/fact-check` against the kit.

**Net:** ~34.3k → ~8–10k lines, drift structurally impossible.

---

## Workstream 3 — Proof-of-life (the v2 doctrine)

**Rule: a control that cannot prove it fired does not exist.** Three failure classes, each with a sensor:

| Failure class | v1 example | Sensor |
|---|---|---|
| Never-alive (shipped broken) | `scan_docs.py` (manifest never existed); `guard_kit_writes` dead 8 releases (matcher casing) | **Fault injection in CI** |
| Silently superseded (native parity) | `context_monitor`, wave stack, worktree commands | **Absorption review in the cull** |
| Never-loaded (nothing reads it) | `documentation-governance.md` (cites Rule 8/9 of 7); `framework-evolution.md` | **Liveness ledger** |

### 3a. Single gate dispatcher + liveness ledger (Phase 1 — ship sensors EARLY)
Replace per-event hook registrations with **one `doe_gate.py` dispatcher** running all applicable checks in-process:
- 1 python spawn per tool call instead of 4–7 — the latency win lands here.
- Every evaluation appends JSONL to `~/.claude/doe-telemetry/gate-fires.jsonl` (`{ts, hook, tool, decision, project}`). Track **evaluated** (proves wiring) separately from **blocked** (proves value) — guardrails should rarely block, so liveness ≠ block-count.
- Directive reads logged via the `check_plan_freshness_hook.py` Read-hook pattern extended to `directives/`; `/wrap` rolls "directives loaded" into `stats.json`.
- Scoping note: the dispatcher invalidates parts of `tests/claude_hooks/` (1,519 lines test hooks individually) — decide wrap-vs-absorb in the scoping pass.

### 3b. Promote `proof/` from sales artifact to CI liveness gate (Phase 2)
`proof/run.py` already injects a fault corpus, runs the REAL hooks, and measures false positives against benign twins. Changes:
- Extend the corpus so **every blocking hook and every `test_methodology` scenario has ≥1 fault it must catch + 1 benign twin it must pass** (currently 3 gates covered).
- Run on every kit PR in `doe-ci.yml`. The `guard_kit_writes` 8-release death becomes a day-one red X.
- **TDD for guardrails:** any PR adding a hook/scenario must add its corpus fault FIRST (red), then the control (green). Enforce via `kit-development.md` + a pre-commit check that new hook files have a corpus entry.

### 3c. The Cull — subtraction gets a ritual (Phase 6)
Addition has a ritual (retro), a trigger (incident), and a reward (badge); subtraction has none — that's why the ratchet turns one way.
- **`/cull`** (quarterly or every 25 sessions, ≤10 min): reads the ledger, presents bottom-N controls (zero evaluations / zero loads / native-parity candidates) with evidence. Keep/kill each; deletion is the default. **Standing agenda items: `/eod` usage, Flutter/Go/Rust templates, political layer** (kept on 2026-06-11 pending data).
- **Sunset front-matter:** every new directive/hook gets `review-by:`; a methodology scenario warns when overdue.
- **Caps (one-in-one-out)** in `test_methodology.py`: ≤N hooks per event, ≤N directives, project CLAUDE.md ≤150 lines (invariant 3 — currently violated AND unenforced).
- **Gamify subtraction:** `/wrap` badges for culls and net-negative-LOC sessions; HQ shows kit liveness %.

### 3d. `scenario_liveness` in test_methodology
Fails on: (a) execution scripts with zero operational callers, (b) directives with no CLAUDE.md trigger, (c) registered hooks with no corpus fault, (d) controls past `review-by`. The kit currently verifies existence; this verifies usage.

---

## Workstream 4 — Plugin distribution (v2.1, DEFERRED)

Not in v2.0 scope. When taken: package the global layer (commands/hooks/scripts/agents) as a private versioned plugin; retire setup.sh's copy + settings-merge (and the exact-command-string dedup footgun class); delete `check_tools_version.py` (version awareness becomes native). Project layer stays repo-installed via `doe init`. Trigger to pull forward: the merge footgun biting again.

---

## Sequencing

| Phase | What | Why this order |
|---|---|---|
| 0 | Cut Phase 0 + unregister dead hooks | 1 session, pure wins, immediate latency relief |
| 1 | Gate dispatcher + liveness ledger (3a) | Sensors EARLY — the cull needs weeks of accrued data |
| 2 | proof/ → full-coverage CI gate (3b) | Catches never-alive before further refactors |
| 3 | Docs generator + prune-during-conversion (WS2) | Biggest LOC win; independent |
| 4 | Wave deletion + command pruning + structural merges (WS1) | Decisions made, sensors running |
| 5 | — (plugin deferred to v2.1) | |
| 6 | First `/cull` with ≥30 days of ledger + instate caps/sunsets (3c–d) | Closes the loop; v2.0 ships here |

**Net effect:** ~88k → ~42k tracked lines; 6–9 python spawns per Bash call → 1–2; three drift classes (CSS copies, duplicated checks, triple-maintained prose) eliminated structurally; every surviving control CI-fault-proven or ledger-visible; kept-on-faith items (`/eod`, Flutter/Go, political layer) face data at the first cull.
