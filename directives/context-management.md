# Directive: Context Management

## Goal
Maximise agent effectiveness by treating context as the scarcest resource. Every irrelevant token degrades performance.

Tradeoff: Context discipline costs upfront recovery time after compaction or `/clear` in exchange for predictable rule compliance and faster reasoning. Apply on every session that spans more than one feature or hits compaction. Skip when: the session is a single-step lookup that fits in one prompt.

## When to Use
Loaded when working in parallel, managing context limits, recovering from compaction, or scaling from solo to multi-terminal work.

## Core Principle
Every terminal is an independent pipeline: load context -> build -> verify contracts -> commit -> next step. Scale by opening more terminals, not by cramming more into one. Solo mode does this through discipline; parallel worktrees (`directives/parallel-worktrees.md`) do it across terminals.

## Post-Compaction Recovery

After context compaction, the thin router (CLAUDE.md) is all the agent retains. Without explicit recovery, the agent proceeds with degraded memory of rules it once read.

**Recovery procedure:**
1. Treat ALL directives as unloaded -- re-read each one before acting on its rules
2. Identify which triggers in CLAUDE.md apply to your current task
3. Re-read those directives before your next action
4. In parallel worktrees: also re-read your step assignment and `Owns:` list from todo.md
5. Check STATE.md for current position and any blockers

**Why this matters:** A compacted agent that skips recovery may violate guardrails it previously loaded, miss triggers it previously knew about, or duplicate work already completed. The 1% rule (CLAUDE.md) applies with extra force after compaction -- if there's any chance a directive applies, load it.

## Neutral Prompt Discipline

Use Neutral Prompts when evaluating your own work. State what you did, state what you verified, state what remains -- let the verification results speak. Self-congratulation ("this looks great!") is a signal that the verification step was skipped.

Bad: "I've successfully implemented a beautiful solution."
Good: "Created the API route. Contract criteria 1-3 pass. Criterion 4 untested -- requires running server."

## Solo

Standard single-terminal work. Context discipline matters most here because you carry the full conversation history.

**Session blocking:** For large features (5+ steps), plan which steps to tackle per session. A fresh `/clear` between groups of steps prevents context degradation. If you notice yourself re-reading the same files or making mistakes on things you previously knew, the context is too polluted -- recommend `/clear`.

**One task, one session:** Recommend `/clear` when the user pivots to an unrelated topic. Unrelated context is dead weight -- a fresh session keeps reasoning crisp.

**Progressive Disclosure:** Only load directives when triggered. Reading all directives "just in case" defeats the purpose of the thin router. Trust the trigger table.

## Informal Parallel

2-3 terminals on independent tasks. Each terminal is its own independent pipeline -- no coordination protocol needed.

**Shared-file awareness:** The only coordination rule: shared files (STATE.md, learnings.md, todo.md, CLAUDE.md) are edited from one terminal at a time. Check whether another terminal might be mid-edit before writing.

**No step ownership needed:** Informal parallel is for genuinely independent tasks (e.g. one terminal builds a feature, another researches a bug). If tasks touch overlapping files, upgrade to Formal Parallel.

## Formal Parallel

Run genuinely parallel steps in separate git worktrees, one per step (see `directives/parallel-worktrees.md`). Each worktree is its own independent pipeline on its own branch. Discipline, not automation, keeps them from colliding:

- Each terminal edits only the files its step owns; declare them in the step's `Owns:` metadata in todo.md.
- Shared files (CLAUDE.md, STATE.md, todo.md, learnings.md) are edited from one terminal at a time.
- Merge each branch back once its step passes all contract criteria, then run any integration contracts on the merged result before starting dependents.

**The independent pipeline principle:** Each terminal gets a fresh session with minimal context -- the step contract, the `Owns:` list, relevant plan sections, and the directives its task triggers. No cross-terminal state sharing. Maximum context quality, minimum pollution.
