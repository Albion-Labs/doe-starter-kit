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
v2.0 plan in flight (.claude/plans/doe-v2-lean-proof-of-life.md), paused for the liveness-audit tangent (.claude/plans/audit-2026-06-11-liveness-findings.md). Batch A shipped (v1.71.3, PR #112) + hotfix v1.71.4 (PR #113: review-gate event-cwd fallback, ~/.claude/hooks mirror). Next: PR B (vacuous checkers) on fix/v1.71.5-vacuous-checkers — v1.71.5, the .4 slot is taken — then PR C (corpses + distribution), then resume v2.0 PR 2 (gate dispatcher + telemetry spine, implements #78; the remaining #107 worktree-artifact sub-case lands there).

## Blockers & Edge Cases
<!-- Known issues, workarounds, things to watch for. Remove when resolved. -->
Background-job sessions execute all guardrail hooks from ~/.claude/hooks (their CLAUDE_PROJECT_DIR=$HOME resolves the registered paths there). Those copies refresh only on FULL setup.sh runs (v1.71.4 mirror step); --tools-only deliberately skips hooks. Consumer projects' vendored hooks still lag until /pull-doe.

## Last Session
<!-- 1-2 sentence summary of what happened last session. Overwritten each session. -->
Liveness-audit batch A: all 10 PR-A findings fixed and released as v1.71.3 (block_secrets Edit/MultiEdit gap closed red-first via corpus F16/F17; setup.sh workflow leak manifest-scoped; pre-retro gate passing for the first time since v1.49.1). Follow-up v1.71.4 killed the recurring "Could not determine git state" PR-creation false block (event-cwd fallback, corpus F18 red-first via its benign twin) and mirrors kit project hooks into ~/.claude/hooks so background sessions stop running stale guardrails. Both deployed machine-wide.
