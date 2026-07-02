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
v2.0 plan in flight (.claude/plans/doe-v2-lean-proof-of-life.md), **cuts-first order (decision 2026-07-02)**: docs site → wave stack → structural merges, then PR 2 (gate dispatcher + telemetry spine #78 + specimen-13 pytest-in-CI). Liveness audit fully shipped (v1.71.3–.6). Docs-site removal (v1.72.0, plan WS2 revised convert→delete, ~30.7k lines) is code-complete on chore/v2.0-docs-site-removal awaiting PR merge + manual whats-new render check. Next: wave-stack deletion + command pruning (plan PR 5, in todo Queue). Note: plan's ~42k target is really ~60k pre-cull; PR 2's "fixes #107" line is stale (#107 closed via PR #110/#113).

## Blockers & Edge Cases
<!-- Known issues, workarounds, things to watch for. Remove when resolved. -->
Background-job sessions execute all guardrail hooks from ~/.claude/hooks (their CLAUDE_PROJECT_DIR=$HOME resolves the registered paths there). Those copies refresh only on FULL setup.sh runs (v1.71.4 mirror step); --tools-only deliberately skips hooks. Consumer projects' vendored hooks still lag until /pull-doe — after v1.71.5, their health checks may newly WARN on mismatched projectType and verify.py exits 1 on [auto] criteria without Verify: patterns; both are new signal, not regressions.

## Last Session
<!-- 1-2 sentence summary of what happened last session. Overwritten each session. -->
Plan-vs-reality review (plan holds; Phase 0 already done, PR 1 half-done, big cuts untouched), then the first big cut: tutorial site retired as v1.72.0 — 18 pages + kit-version.js + stamp_tutorial_version.py + the pre-push docs gate + four pre-commit doc-freshness mappings deleted (~30.7k lines); whats-new.html survives standalone (CHANGELOG-first versioning); --scan-tutorials repointed at docs/reference markdown; pre-push tests rewritten (old ones exercised the real kit's files via PROJECT_ROOT — fixture now copies the hook in).
