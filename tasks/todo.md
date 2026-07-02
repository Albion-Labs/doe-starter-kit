# Active Task List
<!--
FORMAT RULES (Claude: follow these when updating this file)
- This file tracks immediate work only. Long-term roadmap lives elsewhere.
- Sections: ## Current (one active feature), ## Queue (approved, not started), ## Awaiting Sign-off (code complete, manual contracts pending user test), ## Done (all contracts verified, keep for audit)
- Each feature gets a heading, short description, and numbered steps
- Each feature heading includes a type tag: [APP] for changes users see, [INFRA] for tooling/workflow/dev improvements. Example: ### Election History [APP] (v0.9.x). Data work that produces user-visible output is [APP]. Data work that only improves dev workflow is [INFRA].
- Complex features (3+ steps): link to the full design in .claude/plans/ — e.g. "Plan: .claude/plans/feature-name.md"
- Steps are numbered. Step 1 maps to patch 0, step 2 to patch 1, etc (step number = patch + 1). Each new feature starts a new minor version at patch 0 (v0.X.0, v0.X.1, etc.). Feature headings show (vX.Y.x) while in progress, then update to the final patch version when complete.
- Each step shows its version tag after the description: "→ v0.X.Y". Step 1 = v0.X.0, step 2 = v0.X.1, etc. Example: 1. [x] First step — description → v0.X.0 *(completed HH:MM DD/MM/YY)*
- Each step must be scoped to one shippable patch — one commit, one push, one changelog entry. If a step is too big to commit as a single unit, break it down further. If a step is trivial housekeeping, combine it with the previous step.
- When completing a step: N. [x] Step name → v0.X.Y *(completed HH:MM DD/MM/YY)* — then bump the version everywhere it appears (version badges, config files, filenames), rename any versioned deliverable files to match the new version number (even if their content didn't change — the filename must always match the project version), update the changelog, and commit.
- When the final step of a feature completes, run the retro in the same commit: (1) Update version references. (2) Update changelog. (3) Update ROADMAP.md: move the feature from Up Next to Complete (with date and one-line summary), update any status tags (IN PROGRESS → COMPLETE), and refresh Suggested Next if it references the completed feature. (4) Update feature heading from (vX.Y.x) to (vX.Y.N). (5) Run brief retro: what worked, what was slow, what to do differently. Add learnings to learnings.md or ~/.claude/CLAUDE.md, tagged with source. If the process recurs, create a directive + trigger. Check the Progressive Disclosure triggers section in CLAUDE.md — are there any recurring patterns from this feature that should have a trigger but don't? (6) Move the feature to `## Awaiting Sign-off` -- this is the default destination for every completed feature. Features cannot enter `## Done` with unchecked `[manual]` criteria. The only exception: if all `[manual]` criteria happen to already be `[x]` (e.g. from a mid-feature checkpoint), move directly to `## Done`. Present the manual test checklist immediately -- do not wait for session wrap.
- Keep ## Done trimmed to last 3 completed features. Move older ones to tasks/archive.md with all steps and timestamps preserved. Newest at top of archive.
- Don't duplicate the product roadmap here. Reference it: "See ROADMAP.md"
- Progress tracking happens HERE, not in .claude/plans/. Plans are reference docs.
- **Task contracts** are mandatory for every step. Every task added to todo.md gets a `Contract:` block with at least one `[auto]` criterion. No exceptions.
  Format:
  N. [ ] Step name -> vX.Y.Z
    Contract:
    - [ ] [auto] Description. Verify: [executable pattern]
    - [ ] [manual] Description of what the human should check
    Agent cannot mark the step done until all contract items pass /agent-verify.
  **`[auto]` criteria** must use one of these executable Verify: patterns:
    - `Verify: run: <shell command>` -- execute, check exit code 0
    - `Verify: file: <path> exists` -- check file existence
    - `Verify: file: <path> contains <string>` -- check file content for substring
    - `Verify: html: <path> has <selector>` -- parse HTML, check CSS selector (requires BeautifulSoup)
    Anything not matching a pattern is flagged invalid during /agent-launch pre-flight.
  **`[manual]` criteria** describe what the human should check visually/behaviourally. No Verify: method. Prefer converting to `[auto]` where possible — only keep `[manual]` for things that genuinely need human eyes (visual layout, interaction feel, print rendering). `[manual]` criteria are batched and presented to the user at feature completion (or mid-feature for 5+ step features), not per-step.
  **Rules:** Every task must have at least one `[auto]` criterion. `[APP]` tasks must also have at least one `[manual]` criterion. `[INFRA]` tasks can be fully `[auto]`.
  System-generated side effects (stats.json, learnings, wave infrastructure) are NOT tasks and don't get contracts.
- This format can be changed — just update these rules and Claude will follow the new convention.
-->

## Current

### Wave-stack removal — retire the old multi-agent/DAG subsystem [INFRA] (v1.73.x)
v2.0 plan PR 5 (WS1 Phase 4), cuts-first order. The wave stack (multi_agent.py,
dispatch_dag.py, heartbeat/context_monitor hooks, /agent-launch + /agent-status,
serial-dispatch-protocol, multi-agent-coordination plan) is superseded by Claude
Code's native subagents + workflows. Delete it + every reference. Traps (from the
reference map): `global-scripts/doe_utils.py` STAYS (imported by /review scripts
record_review_result.py + persist_review_findings.py); `docs/reference/commands/multi-agent.md`
is a live file. Also drops the dag_validation + status_protocol_compliance methodology
scenarios (they test the dead subsystem). Plan: .claude/plans/doe-v2-lean-proof-of-life.md (WS1 Phase 4).

1. [x] Delete wave stack + strip all references -> v1.73.0 *(completed 18:48 02/07/26)*
  Contract:
  - [x] [auto] All wave files deleted. Verify: run: for f in global-scripts/multi_agent.py global-scripts/dispatch_dag.py global-hooks/heartbeat.py global-hooks/context_monitor.py global-commands/agent-launch.md global-commands/agent-status.md .claude/plans/multi-agent-coordination.md docs/reference/commands/multi-agent.md tests/claude_hooks/test_global_hooks_no_opinion.py directives/serial-dispatch-protocol.md; do test ! -e "$f" || { echo "STILL PRESENT: $f"; exit 1; }; done
  - [x] [auto] doe_utils.py STAYS (the trap — /review scripts import it). Verify: run: test -f global-scripts/doe_utils.py
  - [x] [auto] No live references to deleted wave files in operational code (explanatory retirement comments excluded). Verify: run: ! grep -rn "multi_agent\|dispatch_dag\|agent-launch\|agent-status\|serial-dispatch-protocol\|multi-agent-coordination\|heartbeat\|context_monitor" --include="*.py" --include="*.json" --include="*.sh" execution/ global-scripts/ .claude/settings.json manifest.json setup.sh | grep -vE ':[0-9]+: *#'
  - [x] [auto] dag_validation + status_protocol_compliance scenarios gone. Verify: run: ! grep -rn "dag_validation\|status_protocol_compliance\|scenario_dag_validation\|check_dag_validation" execution/test_methodology.py execution/audit_claims.py
  - [x] [auto] Methodology + pytest suites green (pytest scoped as usual; the 11 tests/claude_hooks failures are the pre-existing Python-3.9 `type|None` artifact, identical on main; CI runs 3.11). Verify: run: python3 execution/test_methodology.py --quick && /usr/bin/python3 -m pytest tests/githooks tests/execution -q
  - [x] [manual] Skimmed subagent-protocol.md + agent-verify.md — solo/worktree phrasing reads cleanly, no orphaned wave references.

## Queue

<!-- Approved features waiting to start. Brief description + link to plan if one exists. -->

## Awaiting Sign-off

### Docs site removal — tutorial + whats-new retired [INFRA] (v1.72.0)
v2.0 lean cut, docs-first order (decision 2026-07-02, supersedes plan decision #6 "convert"):
the kit is internal-only, the tutorial's external audience no longer exists, and
`docs/reference/` (markdown) already covers the content. Step 1 deleted the 18 tutorial
pages + stamping machinery; step 2 (same session, William's call) removed `whats-new.html`
and its generator too — CHANGELOG.md + GitHub Releases are the release record.
Git history (`v1.71.8`) is the archive. Plan: .claude/plans/doe-v2-lean-proof-of-life.md (WS2, decision revised).

1. [x] Delete tutorial pages + stamp machinery; make whats-new standalone -> v1.72.0 *(completed 11:25 02/07/26)*
  Contract:
  - [x] [auto] Tutorial pages gone, whats-new survives. Verify: run: test ! -f docs/tutorial/index.html && test ! -f execution/stamp_tutorial_version.py && test -f docs/tutorial/whats-new.html
  - [x] [auto] No live references to the stamp script in operational code (audit_sync.py's KIT_ONLY legacy-suppression entry is the deliberate exception — it keeps stale consumer copies from being flagged). Verify: run: ! grep -rn "stamp_tutorial_version" --include="*.py" --include="*.yml" --include="*.sh" --exclude=audit_sync.py execution/ .githooks/ .github/ global-commands/
  - [x] [auto] whats-new regenerates cleanly with no links to deleted pages. Verify: run: python3 execution/generate_whats_new.py && ! grep -qE 'href="(index|getting-started|key-concepts|commands|workflows|multi-agent|faq|glossary|context|daily-flow|first-session|new-project|pr-workflow|testing|tips-and-mistakes|troubleshooting|migration-guide|ide-setup)\.html' docs/tutorial/whats-new.html
  - [x] [auto] Methodology + pytest suites green (pytest scoped to the suites this PR touches; tests/claude_hooks needs Python 3.10+, runs in CI). Verify: run: python3 execution/test_methodology.py --quick && /usr/bin/python3 -m pytest tests/githooks tests/execution -q
  - [x] [manual] Obsoleted by step 2 — whats-new.html was removed before merge, nothing left to render-check.

2. [x] Remove whats-new + generator; retire the remaining docs gates -> v1.72.0 *(completed 11:59 02/07/26)*
  Contract:
  - [x] [auto] docs/tutorial gone entirely; generator and its test gone. Verify: run: test ! -d docs/tutorial && test ! -f execution/generate_whats_new.py && test ! -f tests/execution/test_generate_whats_new.py
  - [x] [auto] No whats-new references left in operational code (hooks, CI, commands, execution, router) — explanatory retirement comments excluded. Verify: run: ! grep -rn "whats.new\|whats_new" execution/ .githooks/ .github/ global-commands/ global-scripts/ CLAUDE.md | grep -vE ':[0-9]+: *#'
  - [x] [auto] Methodology + pytest suites green (pytest scoped to the suites this PR touches; tests/claude_hooks needs Python 3.10+, runs in CI). Verify: run: python3 execution/test_methodology.py --quick && /usr/bin/python3 -m pytest tests/githooks tests/execution -q

## Done

### Proof fault net — full guardrail-hook coverage [INFRA] (v1.71.0)
PR 1 of the v2.0 plan (.claude/plans/doe-v2-lean-proof-of-life.md ## Implementation map). Every blocking hook gets at least one must-catch fault + a benign twin in proof/corpus, and the proof job runs on every kit PR so a silently-dead gate turns CI red.

1. [x] Harness: deterministic hook invocation (kit-anchored cwd, escape-valve + GIT_* env scrub, git-fixture support, gh-shim + neutral-cwd fixtures) -> v1.71.0 *(completed 01:41 11/06/26)*
  Contract:
  - [x] [auto] Existing corpus still green under new harness. Verify: run: python3 proof/run.py --self-test
2. [x] Corpus: F08-F15 faults + benign twins covering protect_directives (both branches), guard_kit_writes (rm + force-push), confirm_pr_merge, block_unnecessary_admin_merge (fail-closed arm), enforce_review_gate (feature-branch gate + fail-closed arm) -> v1.71.0 *(completed 01:41 11/06/26)*
  Contract:
  - [x] [auto] Corpus well-formed. Verify: run: python3 proof/corpus_check.py
  - [x] [auto] All covered faults caught, zero measured false positives. Verify: run: python3 proof/run.py --self-test
3. [x] CI: proof job runs on every push to main and every PR (path scoping removed) -> v1.71.0 *(completed 01:41 11/06/26)*
  Contract:
  - [x] [auto] Workflow no longer path-scoped. Verify: file: .github/workflows/proof.yml contains pull_request:
4. [x] Docs + release: proof README + TODO counts, CHANGELOG v1.71.0 entry, whats-new regenerated -> v1.71.0 *(completed 01:41 11/06/26)*
  Contract:
  - [x] [auto] Changelog entry present. Verify: file: CHANGELOG.md contains ## v1.71.0
