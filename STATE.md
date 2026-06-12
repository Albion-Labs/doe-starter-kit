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
v2.0 plan in flight (.claude/plans/doe-v2-lean-proof-of-life.md), paused for the liveness-audit tangent (.claude/plans/audit-2026-06-11-liveness-findings.md — now tracked, with per-item resolutions). Batches A (v1.71.3) and B (v1.71.5) shipped + hotfix v1.71.4. Next: PR C (template corpses + distribution wiring, chore branch, pre-approved deletions: hook-templates/ all three files, global-hooks/pre-commit; leave heartbeat/context_monitor for Phase 4). Then resume v2.0 PR 2 (gate dispatcher + telemetry spine, implements #78; remaining #107 worktree-artifact sub-case lands there).

## Blockers & Edge Cases
<!-- Known issues, workarounds, things to watch for. Remove when resolved. -->
Background-job sessions execute all guardrail hooks from ~/.claude/hooks (their CLAUDE_PROJECT_DIR=$HOME resolves the registered paths there). Those copies refresh only on FULL setup.sh runs (v1.71.4 mirror step); --tools-only deliberately skips hooks. Consumer projects' vendored hooks still lag until /pull-doe — after v1.71.5, their health checks may newly WARN on mismatched projectType and verify.py exits 1 on [auto] criteria without Verify: patterns; both are new signal, not regressions.

## Last Session
<!-- 1-2 sentence summary of what happened last session. Overwritten each session. -->
Liveness-audit batch B shipped as v1.71.5 (PR #115): all ten vacuous-checker findings fixed with disclosure-plus-WARN-at-zero (health_check scan coverage, the three ROADMAP parsers sighted with release tags as shipped-evidence, verify.py loud-fails malformed contracts, proof harness refuses empty corpus / garbage repo paths). Headline specimen: the 358-check doe-init integration suite — run by nothing — had silently broken on doe_init's interactive commit prompt; fixed and wired into CI. Housekeeping PR #114 merged.
