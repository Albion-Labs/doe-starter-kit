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

> **REVISED 2026-07-02 — resolved by DELETION, shipped as v1.72.0.** Decision #6 ("convert")
> was made when the kit was heading toward a public audience; the kit is now internal-only and
> that audience no longer exists. The 18 tutorial pages + stamping machinery + docs gates were
> deleted (~36k lines — including `whats-new.html` + its generator, removed same day on
> William's call; CHANGELOG.md + GitHub Releases are the release record); markdown docs
> live in `docs/reference/`. Recovery: `git checkout v1.71.8 -- docs/tutorial`. Issue #35 is
> mooted; PRs 3–4 in the implementation map are superseded by the one deletion PR. The
> architecture below is retained for reference only (it's the "want docs again" path).

**Original decision (superseded): site stays, same look/URL structure, generated from markdown, content pruned during conversion (Option A — one pass).** Today: 19 hand-written pages, 34,349 lines, 60.5% duplicated boilerplate, 19 drifted CSS copies + a 20th inside `generate_whats_new.py`, zero pages documenting `doe init`.

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

---

## Workstream 5 — Senior Mode (build-time judgement) · target v2.1

The founding goal, stated plainly: a non-technical operator produces code a professional wouldn't be embarrassed by, by saying non-technical things and having the system do the right technical thing. v2.0's verification rails are the foundation (the AI's claims get checked); Senior Mode adds the judgement layer. Design constraint: **the model already has the senior's knowledge — the kit supplies the standing orders and the moments of application.** Policy, not essays. Every component must pass the proof-of-life bar (trigger + liveness evidence) before it counts as shipped.

- **5a. PRD engine (intent translation).** Rebuild `/scope` as structured elicitation: plain-English decision menus (recommended default first, trade-offs stated in operator terms), producing a lightweight PRD at `docs/prd/<feature>.md` -- problem, users, decisions + rationale in plain English, and **success criteria**. The success criteria compile into the existing contract system (todo.md `Verify:` lines), and the evidence pack (5d) closes the loop against the PRD at delivery: what was promised, what was proven. Add an **XY-problem duty** to planning-rules: before building the asked-for solution, confirm it solves the underlying problem; push back when it doesn't.
- **5b. Standing orders.** ONE directive (≤150 lines, policy form): when options exist choose the boring one; when scope is ambiguous choose the smaller one; when security trades against convenience choose security; no abstraction before the third use; model the data before the UI; vet every new dependency (maintenance, adoption, last release) before install; make it work → make it right → make it fast, in that order; flag each judgement call made on the operator's behalf.
- **5c. Production-readiness gates by project class.** `doe init` records the class (static site / app without user data / app with user data / app handling money). `delivery-rules` gains a class-keyed launch checklist; the dangerous classes gate shipping the way the DPIA already gates personal data. A senior's "you can't launch without X," encoded.
- **5d. Evidence packs.** Every feature delivery ends with an artifact a non-expert can read: tests green, security checks, screenshots of the working thing, and the plain-English decisions log from 5a. Generalises the `proof/` scorecard pattern from sales artifact to delivery norm.
- **5e. Risk tiers.** Every plan and PR states its blast radius in plain English — routine / careful / dangerous (touches auth, money, data deletion, or the public internet). Drives 5f.
- **5f. Second-opinion ritual.** Dangerous-tier changes require an independent fresh-context review before merge (native code review or cross-model review, result recorded). The builder never grades its own homework on the things that can really hurt.

## Workstream 6 — Steward Mode (run-time; the senior's other half) · target v2.2

The founding goal has a blind spot: it says "produce code," but most of a 20-year senior's value shows up AFTER shipping — monitoring, maintenance, security posture, cost control, recovery. For a non-technical operator this is the deepest unknown-unknown: shipped software rots silently. Claude Code's scheduled agents make this genuinely automatable now — this is where "senior dev on automode" becomes literal.

- **6a. Observability by default.** Init/deploy wires error monitoring (Sentry), an uptime check, and alerting for every deployed project. Rule: deployed without monitoring = not done. You should learn the site is broken from an alert, never from a user.
- **6b. Maintenance heartbeat.** A scheduled monthly fleet patrol (cloud agent) across all projects: dependency + security audit, certificate/domain expiry, billing anomaly review, backup-restore test, report delivered to HQ. The boring senior chores, on cron.
- **6c. Perimeter checklist.** Operator account hygiene, one-time + annual: 2FA on GitHub/Vercel/registrar/email (the registrar matters — domain hijack is game over), least-privilege API tokens, key rotation, billing alerts on every paid service.
- **6d. Data stewardship.** Staging-by-default for any project with a database; never test against production data; migrations must state their rollback; a backup that has never been restore-tested does not count as a backup.
- **6e. Incident runbook (plain English).** "The site is down": how it's detected, first 15 minutes of triage, how to roll back a deploy, where the status pages are. The non-GDPR sibling of incident-response.md.

## Revised sequencing

v2.0 = lean + proof-of-life → **v2.1 = Senior Mode** → **v2.2 = Steward Mode**. Order is deliberate: judgement and stewardship layers are only trustworthy on top of rails that provably fire. Plugin packaging (WS4) slots wherever convenient from v2.1 onward.

**One re-order inside v2.0: fault coverage (old Phase 2) now lands BEFORE the dispatcher refactor (old Phase 1).** Refactoring every guardrail hook without a fault net is the exact failure mode that killed `guard_kit_writes` for 8 releases. The corpus is the net, so it goes first — the plan's own TDD-for-guardrails doctrine, applied to building the plan.

## Implementation map (one PR per row, one session each unless noted)

### v2.0 — remaining (~6–8 sessions)
| # | Delivers |
|---|---|
| 1 | `proof/` corpus extended: every blocking hook + every methodology scenario gets ≥1 must-catch fault + a benign twin; proof runs in `doe-ci.yml` on every kit PR. Pure addition, low risk. |
| 2 | `doe_gate.py` dispatcher (one spawn per event instead of 4–7) + **session telemetry spine (implements #78's core)**: one local-first JSONL event stream, gate evaluations (evaluated vs blocked) + directive loads as first event types. **Fixes #107** (review-gate worktree bug) with regression test. `tests/claude_hooks/` rework. 1–2 sessions; protected by PR 1's fault net. |
| 3–4 | Docs generator: `build_docs.py` + single template/CSS extracted from `generate_whats_new.py`, 2 pilot pages verified by screenshot-diff; then full prune-during conversion, `nav.json`, `stamp_tutorial_version.py` deleted, build wired into `auto-release.yml`. 2–3 sessions. |
| 5 | Wave-stack deletion + command pruning (stand-up merge, report-doe-bug trim, codemap/project-recap/worktree-cmd removal). Mechanical; decisions already made. |
| 6 | Structural merges: shared `doe_checks.py`, bug/feature-request merge, `execution/_lib.py`, directive consolidation per the overlap map. 1–2 sessions. |
| 7 | `/cull` v1 + caps (one-in-one-out, CLAUDE.md ≤150 enforced) + `review-by:` sunsets + `scenario_liveness`. **Calendar-gated: ≥30 days of ledger data after PR 2 lands.** v2.0 ships here. |

### v2.1 — Senior Mode (~5–6 sessions)
| # | Delivers |
|---|---|
| 8 | Standing-orders directive + language-pack mechanism (#73) carrying anti-monolith content (#74): universal judgement layer plus per-language binding of best-practices at init. |
| 9–10 | PRD engine: `/scope` rebuild → `docs/prd/<feature>.md`; success criteria compile to todo.md contracts; XY-problem duty in planning-rules. The centrepiece — 2 sessions (design + build). |
| 11 | Project-class launch gates: `doe init` records class; class-keyed delivery checklist; hard gate for user-data/payments classes. Folds in the init backlog: transactional abort (#67), AGENTS.md mirror (#66), wizard prompt auto-derivation (#30). |
| 12 | Evidence packs: delivery artifact via `html_builder` (tests, checks, screenshots, decision log) — closes the loop against the PRD. |
| 13 | Risk tiers + second-opinion ritual: blast-radius declaration in plans/PRs; dangerous tier requires independent fresh-context review, recorded. |

### v2.2 — Steward Mode (~3–4 sessions)
| # | Delivers |
|---|---|
| 14 | Observability by default: init/deploy wires Sentry + uptime + alerting; "deployed without monitoring = not done" enters delivery-rules. |
| 15 | Maintenance heartbeat: scheduled fleet-patrol cloud agent (deps/security audit, cert + domain expiry, billing anomalies, backup-restore test) reporting to HQ. |
| 16 | Perimeter checklist + data stewardship + plain-English incident runbook (directives, init defaults, annual audit command). |

**Cadence:** at a few sessions a week, v2.0 completes in ~2 weeks, v2.1 in ~2 more, v2.2 in ~1–2 — call it 4–6 weeks to a kit that is lean, self-verifying, senior-opinionated, and on stewardship autopilot, with `/cull` firing on its own 30-day clock thereafter. Every PR follows the Phase 0 pattern: worktree, scoped contract first (planning-rules), tests in the same PR, CHANGELOG when releasable, merge = release.

---

## Outstanding-issue reconciliation (audited 2026-06-11)

The plan was drafted from the full-kit review; this section reconciles it against every open kit issue so the backlog and the plan are one thing.

### Absorbed into the plan (close via the implementing PR)
| Issue | Disposition |
|---|---|
| **#78 telemetry spine** (keystone for #24/#28/#65) | **PR 2 implements its core.** The liveness ledger IS the spine: one local-first JSONL event stream; gate evaluations + directive loads are the first event types, command usage next. Design PR 2's schema as #78's schema, not a parallel log. |
| **#107 review-gate worktree bug** | Fixed in PR 2 (`fixes #107`), with a worktree regression test. |
| **#35 auto doc sync** | Structurally solved by PRs 3–4 (docs generated from markdown inside `auto-release.yml` — freshness becomes impossible to lose). Close on PR 4 merge. |
| **#24 kit-bloat audit** | This plan IS #24 executed: the review + Phase 0 + PRs 5–6 do the cutting; PR 7's `/cull` delivers its literal acceptance criteria (per-directive load-rate, <20% = candidate). Close pointing here; measured load-rates land with PR 7. |
| **#28 output evals (binary YES/NO sub-criteria)** | Criteria *format* absorbed into the PRD engine (PRs 9–10): PRD success criteria are authored as binary sub-criteria that compile into contracts. The cross-session rolling pass-rate eval stays parked until the spine (PR 2) has months of data — its own stated trigger. |
| **#73 language packs + #74 anti-monolith content** | Slot into v2.1 PR 8: standing orders is the universal judgement layer; language packs are its per-language delivery mechanism (bind `best-practices/` + anti-monolith ceilings to detected framework at init). |
| **#67 init transactional abort, #66 AGENTS.md mirror, #30 wizard prompt auto-derivation** | All three fold into PR 11 (the init-touching PR): stage-to-.tmp atomic install, AGENTS.md mirror, derive ~4 of 7 wizard fields. |
| **#70 auto-/review on step completion** | Revisit at PR 13 (risk tiers): auto-review on *dangerous-tier* steps is the proof-of-life-compliant version of this (a hook with a reason to fire), and the dispatcher (PR 2) makes the event wiring cheap. |

### Obsoleted / recommend closing now (William to ratify)
| Issue | Why |
|---|---|
| **#25 persistent cross-session memory** | Native Claude Code auto-memory shipped after this was filed and provides the local-first layer; STATE.md/learnings.md remain the project-level state. Absorption doctrine: close as native-superseded. Revisit only if external-source ingestion (meetings/Slack) becomes a real need. |
| **#17 Conventional Commits adoption** | Substantially shipped in v1.56–v1.57 (commit-msg validation, git-conventions.md, CLAUDE.md section, CC self-dogfood). Residue: warn→block mode flip (one-line decision, take any time) and auto-changelog-from-commits — which now CONFLICTS with the hand-written hero contract in kit-development.md and should not be built. Close with residual note. |

### Parked with explicit triggers
| Issue | Trigger to revive |
|---|---|
| **#65 comparative DOE-value benchmark** | After v2.0 ships: the spine (PR 2) + extended `proof/` (PR 1) provide the substrate; the DOE-on/off comparative suite in a separate repo becomes Steward-era work and doubles as model-release regression detection. |
| **#69 Slack/CI playbook** | CONFLICT with lean doctrine: the plan deletes `integrations.md` (unused — its own Tradeoff line says skip for solo work) while #69 asks for more Slack docs. Park until any project actually wires Slack notifications — no reader, no docs. |
| **#27 performance directive** | Standing orders (PR 8) covers the 80% ("make it work → right → fast"); revive the full Doodlestein workflow only when a real perf incident triggers it. |
| **#26 cross-project asset registry** | Addressed by plugin packaging (WS4, v2.1+) — distribution is the registry. |
