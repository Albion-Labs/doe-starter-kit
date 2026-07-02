# Directive: Planning Rules

## Goal
Ensure every feature is properly scoped, contracted, and sequenced before building begins.

Tradeoff: Planning rules cost upfront scoping time in exchange for catching scope drift, missing dependencies, and ambiguous contracts before they cost build time. Apply at session start and when starting any feature with 3+ steps. Skip when: the work is a one-step ad-hoc fix that has its Verify: criteria stated in conversation.

## When to Use
Loaded when planning, scoping, or starting a new feature. Also loaded on first session for a brand new project.

## Planning Process

### Name user intent in one sentence

Before any scoping, write the user intent as one declarative sentence: "The user wants X so they can Y." If the sentence comes out fuzzy ("the user wants to improve the dashboard"), the request is fuzzy -- pull a sharper version from the user before scoping. The intent sentence is the test the eventual plan answers; when you cannot write it, you cannot plan.

Source: octolane "Taste" framing -- naming what is being executed toward, before execution.

### Plan before building
Check `tasks/todo.md` and `STATE.md` at session start.

- **Complex features** (3+ steps): write design to `.claude/plans/`, add steps to `tasks/todo.md`
- **Simple tasks**: add directly to `tasks/todo.md`. Track progress only in todo.md -- plans are reference docs
- Each plan step includes a recommended model + thinking level (e.g. `Opus + high`, `Sonnet + medium`)
- **Ad-hoc work** (not in todo.md): state 1-3 `Verify:` criteria in conversation before starting. Confirm pass before committing. Mechanical changes just state what and why.

### Ask when ambiguous
Match the question to the smallest decision that unblocks you. Separate research from implementation sessions -- context pollution hurts both. When the user's meaning is unclear, clarify before spending tokens on the wrong path.

### Check before spending
If a script uses paid API calls or credits, confirm with the user before running.

### Plan freshness check
Plans written 10+ days before building accumulate staleness: version numbers taken by other features, file references renamed, CLAUDE.md structure changed, directive schemas evolved. Before starting Step 0 of a feature whose plan is more than 10 days old, run a freshness check:
- Compare file references in the plan against current paths (extract backticked paths and verify each exists)
- Check version ranges are still available (cross-check `ROADMAP.md ## Complete` and `tasks/todo.md ## Queue`)
- Verify structural assumptions (CLAUDE.md routing table, directive filenames, hook names, command filenames)

30 minutes of pre-build verification beats hours of mid-build debugging. Fix drift in the plan before committing Step 0.

### Dependency-aware planning
Think about what actually depends on what, not what order to build. Steps that share no files can run in parallel. Steps that write to the same files must be sequenced. The `Depends:` and `Owns:` metadata in todo.md captures this explicitly.

When writing step contracts, also identify integration contracts -- cross-step verifications that run after parallel steps merge. Example: "Step 1 creates the API route, Step 2 creates the UI. Integration contract: UI successfully calls the API."

### Explain technical decisions simply
No jargon without context. If you recommend a framework, tell the user why in terms they can evaluate (speed, cost, maintainability, ecosystem).

## Contract System

Every task added to todo.md gets a `Contract:` block with at least one `[auto]` criterion. No exceptions. See `directives/testing-strategy.md` for the full contract system (patterns, levels, verification flow).

### Transform vague requests into verifiable contracts

A vague request becomes a verifiable contract by naming the criterion that distinguishes done from not-done. The transform usually swaps a wish for a check:

| Vague request                | Verifiable contract                                                       |
| ---------------------------- | ------------------------------------------------------------------------- |
| "Add validation"             | `[auto]` Tests for invalid inputs return 400; valid inputs return 200      |
| "Improve performance"        | `[auto]` p95 latency for endpoint X drops from Yms to under Zms            |
| "Fix the bug"                | `[auto]` Reproduction test from issue #N passes                            |
| "Make the dashboard cleaner" | `[manual]` Visual review confirms agreed wireframe v2.1 layout shipped     |
| "Refactor module X"          | `[auto]` Existing tests pass before AND after; behaviour preserved (e.g. golden-file diff stays empty) |

The transform reveals scope: a vague request that resists transform is not yet ready to build. Surface the transform attempt to the user and ask which criterion fits.

Source: octolane "Taste" piece -- naming the verifiable bar before scoping.

### Verify: pattern types
`[auto]` criteria must use one of these executable patterns:
- `Verify: run: <shell command>` -- execute, check exit code 0
- `Verify: file: <path> exists` -- check file existence
- `Verify: file: <path> contains <string>` -- check file content
- `Verify: html: <path> has <selector>` -- parse HTML, check CSS selector

Anything not matching a pattern is flagged invalid during `/agent-verify` pre-flight.

### Manual vs auto criteria
Before marking a criterion `[manual]`, ask: could a machine determine pass/fail? If the answer involves checking a count, verifying a file exists, or comparing a value -- write it as `[auto]` with a `Verify:` pattern instead. Only keep `[manual]` for things that genuinely need human eyes: visual quality, content clarity, interaction feel, subjective judgment.

### Verification flow
- Run `Verify:` patterns after each step. Mark `[x]` as they pass. 3 fix attempts before escalating.
- Continue building autonomously. Manual approval batches at feature end (or at the mid-feature gate for 5+ step features).
- `[manual]` criteria are batched and presented at feature completion (or mid-feature for 5+ step features).
- When last step's `[auto]` pass: run retro, move to `## Awaiting Sign-off`, present manual checklist.

## Scale-Aware Session Planning

### Solo
One terminal, one feature. Standard context discipline. For large features (5+ steps), consider session blocking: plan which steps to tackle in one session to avoid context limit.

### Informal Parallel
2-3 terminals on independent tasks. Shared-file awareness: edit shared files (STATE.md, learnings.md, todo.md, CLAUDE.md) from one terminal at a time. Check before writing in multi-terminal mode.

### Formal Parallel
Separate git worktrees, one per step (see `directives/parallel-worktrees.md`). Step ownership via `Owns:` metadata; shared files edited from one terminal at a time. Merge each branch once its step passes contracts, then run integration contracts on the merged result.

## Session Preparation

### Skill-prep before main session

Before a session that will lean on a specific framework or pattern (e.g. Next.js App Router, Postgres migrations, Stripe webhooks), prepare a framework-specific skill or load the relevant directive in advance. The main session then opens with that context already paged in, instead of paying the load tax mid-flow.

Use cases:
- New framework on the project: load the official skill or write a project-local one before the first real feature.
- Recurring task with known steps (e.g. a deployment runbook, a release-candidate sweep): condense the steps into a project-local skill before the next session that needs it, so the main session loads the procedure pre-formed instead of reconstructing it.
- One-off but heavy (e.g. a complex migration): write a one-page skill outline first, then start the main session.

Source: Dhravya supermemory landing-page article -- prepare framework-specific skills before main session.

## Scoping Tools
- `/scope` -- interactive scoping partner for turning ideas into plans
- `/plan-review` -- check implementation against plan
- `/project-recap` -- rebuild mental model after absence
