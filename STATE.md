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
v2.0 plan in flight (.claude/plans/doe-v2-lean-proof-of-life.md), **cuts-first order (decision 2026-07-02)**: docs site → wave stack → structural merges, then PR 2 (gate dispatcher + telemetry spine #78 + specimen-13 pytest-in-CI). Operating principle: less-code/DRY, not an arbitrary LOC target. Liveness audit fully shipped (v1.71.3–.6). Docs-site removal shipped as v1.72.0 (PR #120 merged). Wave-stack removal (v1.73.0, ~4.6k net lines — multi_agent/dispatch_dag/heartbeat/context_monitor/agent-launch/agent-status/serial-dispatch + 2 dead methodology scenarios) code-complete on chore/v2.0-wave-stack-removal, awaiting PR. Manual worktree-parallel kept (parallel-worktrees.md + /worktree-* stay). Next cut: structural merges (plan PR 6 — shared doe_checks.py, _lib.py, directive consolidation). Note: plan's ~42k target is really ~60k pre-cull; PR 2's "fixes #107" line is stale (#107 closed via PR #110/#113).

## Blockers & Edge Cases
<!-- Known issues, workarounds, things to watch for. Remove when resolved. -->
Background-job sessions execute all guardrail hooks from ~/.claude/hooks (their CLAUDE_PROJECT_DIR=$HOME resolves the registered paths there). Those copies refresh only on FULL setup.sh runs (v1.71.4 mirror step); --tools-only deliberately skips hooks. Consumer projects' vendored hooks still lag until /pull-doe — after v1.71.5, their health checks may newly WARN on mismatched projectType and verify.py exits 1 on [auto] criteria without Verify: patterns; both are new signal, not regressions.

## Last Session
<!-- 1-2 sentence summary of what happened last session. Overwritten each session. -->
Wave-stack removal (v1.73.0): deleted the multi-agent/DAG subsystem (multi_agent.py, dispatch_dag.py, heartbeat/context_monitor hooks, /agent-launch + /agent-status, serial-dispatch-protocol, multi-agent-coordination plan) + 2 dead methodology scenarios + dead code in verify.py/audit_claims.py; reframed 9 directives around manual worktrees (kept parallel-worktrees.md). ~4.6k net lines. Reference-map agent up front caught two traps: doe_utils.py stays (imported by /review scripts), and docs/reference/commands/multi-agent.md was a live file. quality_gate.py's PRE_RETRO_SCENARIOS still named dag_validation — caught by its own pinning test mid-PR.
