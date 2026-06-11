# Project State

Session memory that persists across `/clear`. Claude updates this file during sessions; the user rarely edits it directly.

<!--
Claude: update this file when any of the following happen:
- A blocker or edge case is discovered
- An approach changes (decisions themselves go in learnings.md ## Decisions)
- A session ends or the user runs /clear
- An assumption is corrected

Keep each section short. Replace stale info, don't accumulate. This file should reflect CURRENT state, not history.
Keep each section short. Replace stale info, don't accumulate. Max ~30 lines of content.
-->

## Current Position
<!-- What feature/step is in progress. Updated at session start and end. -->
v2.0 plan in flight (.claude/plans/doe-v2-lean-proof-of-life.md). Phase 0 shipped (v1.70.0). PR 1 (proof fault net, v1.71.0) on feature/proof-fault-net-v1.71.0 — code complete, PR pending. Next: PR 2 (gate dispatcher + telemetry spine, implements #78, fixes #107).

## Blockers & Edge Cases
<!-- Known issues, workarounds, things to watch for. Remove when resolved. -->

## Last Session
<!-- 1-2 sentence summary of what happened last session. Overwritten each session. -->
Full-kit review → v2.0 Lean + Proof-of-Life plan (merged, #108). Phase 0 lean cuts shipped + auto-released as v1.70.0. Open-issue backlog reconciled into the plan (#25/#17 closed, #78/#24/#28/#35 absorbed). Proof fault net built: corpus 7→15 faults, all blocking hooks covered, CI unscoped.
