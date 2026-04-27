# Project Learnings

Cross-cutting patterns and institutional memory for this project. Check this file at session start. Updated automatically via Self-Annealing (failure recovery) and feature retros (post-completion review).

<!--
Claude: add learnings to the most relevant section. If no section fits, create a new ## heading.
Max 50 lines of content. When full, remove the least useful before adding new.

Routine learnings: one line, specific, actionable. Tag source: e.g. "[retro: feature-name vX.Y.Z]"
  Example: - macOS sed -i requires '' backup extension. [retro: doe-hooks v1.2.0]

Significant failures (cost >30 min, broke production, or recurred): use structured format:
  ### Learning: [title]
  **What happened:** [description]
  **Root cause:** [WHY -- context pollution? Ambiguous spec? Missing constraint?]
  **Fix applied:** [what changed]
  **Prevention:** [rule/hook/directive added, or "none needed -- one-off"]
  [source tag]
-->

## Process & Workflow
<!-- How to work effectively in this project. Planning, sequencing, context management. -->

## API & Integration Patterns
<!-- External service behaviours, rate limits, auth quirks, data formats. -->

## Execution Script Gotchas
<!-- Bugs, edge cases, and workarounds discovered in execution/ scripts. -->

## Architecture Decisions
<!-- Stack choices, trade-offs, and why things are built the way they are. -->

## Decisions
<!-- Technical and process decisions. Format: "Decision — reason. [source]" -->

## UI Patterns
<!-- Reusable patterns for the app. -->

## Common Mistakes
<!-- Recurring errors to watch for. Failure-driven learnings from Self-Annealing. -->

## Considered & Rejected
<!-- Patterns evaluated and deliberately not adopted. Records the *why* so future sessions don't relitigate. -->

- Considered and deferred indefinitely (research session 215, Apr 2026): Skills-standard hybrid migration (DOE value is orchestration, not per-directive content; portable Skills don't carry the orchestration layer; two-system overhead exceeds theoretical portability gain), disposable-worktree validation in /review (no problem we have; existing hooks already gate at commit/push), auto-fix mode for /review findings (contradicts Surgical Changes principle -- AI silently changing things is the opposite of "every changed line traces to the user's request"), structured contract format with linter (`/agent-launch` already validates Verify: patterns -- speculative for the one drift instance we've had), kit-as-submodule for DOE-using projects (UX cost > benefit; setup.sh "just works" model is the right primitive for non-technical users), DOE Lite single-file curl-installable distribution (decision is "no, unless tooling ecosystem forces us"; viral surface is a marketing question not engineering, and competing with the full kit at the install gate would dilute adoption). See the 5 v2.0 GH issues that survived the cull (Kit-bloat audit, Persistent memory layer, Cross-project asset sharing, Performance engineering directive, Output evals).
