# Directive: Building Rules

## Goal
Enforce code quality, branch discipline, and collaboration patterns during implementation.

Tradeoff: Branch and code-hygiene rules cost a few seconds per commit; they preserve revertability and reviewer trust. Apply on every feature commit. Skip when: the commit is a tooling fixup that bypass-flags the relevant gate (e.g., `SKIP_STEP_MARK_CHECK=1`) and the bypass reason is in the commit body.

## When to Use
Loaded when building, coding, or implementing features. Also loaded on first session for a brand new project.

## Branch & Commit Discipline

Work on feature branches, commit per step. `/crack-on` creates `feature/<name>` from main.
- Commit after every completed step. Push immediately. One commit per step keeps each change independently revertable.
- **Mark the step [x] in todo.md before committing step work.** The commit-msg hook blocks commits that reference "Step N" or contain a version tag `(vX.Y.Z)` unless `tasks/todo.md` is staged. This is deterministic — you cannot commit step work without updating progress. Skip: `SKIP_STEP_MARK_CHECK=1`.
- **Use Conventional Commits format.** Subjects follow `<type>[(scope)][!]: <description>` — see `directives/git-conventions.md` for the full spec, the allowlist for legacy/automated patterns (`Merge `, `Revert "`, `Initial commit`, `fixup!`, `squash!`, legacy `vX.Y.Z:`), and the `DOE_COMMIT_HOOK_MODE` env var (default `warn`, switch to `block` once the team is fully on CC). The commit-msg hook validates every subject in warn mode by default during the v1.57.0 -> v1.58.x transition.
- Commit on feature branches; merge to main via PR. Commit messages omit "Co-authored-by" trailers (the commit-msg hook strips them).
- At retro: `gh pr create` with PR template auto-filled from contracts. CI must pass before merge.
- **No mid-feature PRs.** Push to the feature branch to save work between sessions -- the branch is on GitHub, nothing is lost. PRs are created at retro only (the final step). Mid-feature PRs create merge/rebase overhead with no benefit. If a session ends mid-feature, wrap commits directly to the feature branch.

## Subagent Protocol

Delegate to subagents to preserve context. Spawn when: 3+ files, doc research, 50+ lines, or verbose output. Pass only needed files. Stay in main thread for direct edits and back-and-forth.

- Model selection: Opus for judgment/architecture, Sonnet for implementation, Haiku for lookups
- **Status protocol:** Must report DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED
  - See `directives/subagent-protocol.md` for format. No ad-hoc "I'm done" -- require the report

## Parallelise by Default

2+ independent tasks -> parallel subagents. Commit one at a time per branch discipline. For interdependent steps, use serial dispatch -- see `directives/serial-dispatch-protocol.md`.

## Code Hygiene

- **Check before creating.** Check if a similar file exists and edit it. New variants (`filename-new`, `_v2`, `-copy`) require explicit user approval.
- **Surgical edits only.** Edit only the lines that change. Wholesale rewrites require user approval first -- say so and wait.
- **Pre-refactor cleanup.** Before any structural refactor on a file >300 LOC, first commit a dead-code removal pass (unused imports, dead props, orphaned exports). Separate commit -- cleanup and logic changes must be distinct in the diff.
- **Reuse before writing.** Check `execution/` and project files for existing logic before writing new. Flag duplication.
  - **Three layers of knowledge.** Pick the right layer for the task.
    - Layer 1 (tried-and-true: Postgres, Linux, bash, the standard library) is the default -- battle-tested for decades, well-known failure modes, abundant docs.
    - Layer 2 (new-and-popular: Tailwind, Next.js, the framework of the moment) earns its place when it closes a Layer 1 gap; name the gap before promoting to Layer 2.
    - Layer 3 (first-principles: TCP, HTTP, Unix pipes, file descriptors) is the substrate every layer above stands on -- understanding it lets you debug across abstractions.
    - Layer 2 mania (reaching for the latest framework when Layer 1 covers the case) is the most common search-failure mode. Source: gstack ETHOS.
- **One task, one session.** When the conversation drifts, recommend `/clear` -- keep context scoped to the active task.
- **Refactor is not rewrite.** Refactor preserves behaviour. Behaviour changes are tracked as feature work -- say so explicitly when a refactor will alter observable behaviour.
- **No orphan files.** If you replace a file, delete the old one.
- **Plans go in `.claude/plans/`.** Project plans live in the project repo; `~/.claude/plans/` is the personal sandbox and stays out of project commits.
- **Visual docs go in `docs/`.** Project diagrams live in the project repo; `~/.agent/diagrams/` is the personal sandbox.
- **Files in designated directories.** Follow the directory structure in CLAUDE.md. New directories or root-level files require explicit approval.
- **Rename safety protocol.** When renaming or changing a function/type/variable signature, run separate searches for: direct calls, type references, string literals containing the name, dynamic imports, re-exports, barrel files, test mocks. Never assume a single grep caught everything.

## Build Discipline: Mini-Plans & Evidence Gates

For multi-step build work inside a single session, use the inline mini-plan format. For the trigger to start work at all, use the evidence gates.

### Mini-plan format

When a step contains 2+ sub-actions, write the mini-plan inline before starting:

```
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Each line names one sub-action and the binary check that confirms it landed. The mini-plan is the smallest useful pre-write before the work begins; the verify lines become the test you loop against.

Same format as Goal-Driven Execution in `universal-claude-md-template.md`; replicated here as the build-time application of that principle.

Source: Doodlestein -- inline plan format that ties each action to its own check.

### Evidence gates

A handful of build-phase actions require a piece of evidence before the action begins. Generalise the rule: no evidence -> no action.

- **No reproduction -> no fix.** Before fixing a bug, write the test that reproduces it. The test is the evidence the bug exists; the test passing is the evidence the fix landed.
- **No contract -> no merge.** Before merging step work, the step's `[auto]` contract must pass. The contract is the evidence the step is done.
- **No hotspot list -> no perf change.** Before changing code in the name of performance, profile and produce a ranked hotspot list. The hotspots are the evidence the change targets the right code.

The pattern generalises: name the evidence the action depends on, and produce that evidence before acting. Action without evidence is speculation; action with evidence is iteration.

Source: Doodlestein -- "no reproduction -> no fix" / "no contract -> no merge" / "no hotspot list -> no perf change" as the same evidence-gate principle in three domains.

## Search & Tool-Use Discipline

- **Search truncation awareness.** When grep/search results look suspiciously small, re-run with narrower scope (single directory, stricter glob). State explicitly when truncation is suspected rather than working from incomplete results.

## File Ownership in Parallel Work

When working alongside other agents (wave mode or DAG executor), respect the owns list:
- Only edit files listed in your step's `Owns:` metadata
- CLAUDE.md, STATE.md, todo.md, learnings.md are shared files -- off-limits to all parallel agents
- If you need a file you don't own, report `NEEDS_CONTEXT` (subagent status protocol)
- Pre-commit hooks enforce ownership mechanically in DAG mode

### DAG Push Mode
In DAG parallel mode (formal parallel), individual steps do NOT push to the feature branch. Instead:
1. Each agent works in its own worktree on a sub-branch
2. After all steps in a wave complete and pass contracts
3. The executor performs the wave merge into the feature branch
4. Integration contracts run on the merged result
5. Feature branch pushes to remote after integration passes

## Explain Technical Decisions
When making technical choices during building, explain simply. No jargon without context. If recommending a library, framework, or pattern, explain why in terms the user can evaluate.

## Quality Gate

Contracts verify each step in isolation. They don't catch cross-step drift -- where step 3's documentation claim becomes false after step 5 changes the implementation, or where two directives describe the same concept with no cross-reference. This gate catches consistency issues between steps.

### Mid-feature checkpoint (5+ step features)

After every 4th completed step, before picking up the next:

1. Run `python3 execution/test_methodology.py --scenario cross_reference_consistency --scenario directive_schema --scenario agent_definition_integrity`
2. Assess blast radius using `directives/adversarial-review/README.md` matrix:
   - **High** (feature modified directives, agents, execution scripts, or CLAUDE.md routing): spawn Finder agent to scan all files modified during the feature for semantic drift
   - **Medium** (single feature, no shared interfaces): methodology checks only
   - **Low** (docs, comments, config): no mid-feature gate needed
3. Fix findings before continuing. 3 fix attempts then escalate to user.

The methodology checks catch structural issues (broken references, invalid schemas, invariant drift). The Finder agent catches semantic issues (documentation claims that contradict implementation, duplicated concepts without cross-references, descriptions in one file that conflict with the state of another).

### Invariant failures during builds
If `invariant_regression` reports drift during a build:
- If your step **intentionally changed** what the invariant tests (e.g. restructuring CLAUDE.md) -> update `tests/invariants.txt` to reflect the new state in the same commit
- If your step **shouldn't have affected** what the invariant tests -> fix the code, not the invariant

### What the Finder should receive

When spawning the Finder for a mid-feature gate, pass it:
- The list of files modified since the feature branch was created (`git diff --name-only main...HEAD`)
- The current step number and total steps
- Instruction to focus on cross-file consistency, not individual code correctness

## Build-Phase Triggers
These triggers apply during building (absorbed from the original CLAUDE.md trigger table):
- Creating a new execution script -> check `execution/` for reusable patterns, review `learnings.md` ## Execution Script Gotchas
- Completing a data-layer step -> run `/code-trace`. Announce: "Data-layer step -- running code trace."
- Completing a UI step -> run `npx playwright test` on affected pages. Announce: "Running browser tests."
- Completing an integration step -> run `/code-trace --integration`
- Checking implementation vs plan -> suggest `/plan-review`

## Structured JSON Logging
For any backend or API code, use structured JSON logging rather than unstructured print/console.log. This enables log aggregation, search, and alerting in production. Format: `{"level": "info", "message": "...", "context": {...}}`.

## Data Integrity Testing
When building features that process or display data, add data integrity checks:
- Validate data codes (e.g. category IDs exist in lookup tables)
- Check numeric sums (e.g. percentages sum to ~100%)
- Verify no NaN/null in required numeric fields
- Check no orphan codes (references to entities that don't exist)

Template: `~/doe-starter-kit/tests/data/test_data_integrity_template.py`
