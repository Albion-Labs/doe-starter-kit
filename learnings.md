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

- `grep -A N` Pink Elephant contracts (`! grep -A N <heading> file | grep -iE '\b(don't|never|avoid)\b'`) capture pre-existing content within N lines of the new heading. The fixed line-count buffer extends past the new content into surrounding existing bullets, falsely failing the new feature's contract on words used legitimately elsewhere in the same file. Fix in contract design: bound the check to the new content's structural unit (consecutive lines with same indentation, delimiter-bounded scope, or a content-end marker). In-flight workaround: expand single-line new content into a multi-line block until the pre-existing content sits outside the buffer. [retro: kit v1.61.1 Step 1]

## Considered & Rejected
<!-- Patterns evaluated and deliberately set aside. Records the *why* so future sessions can act on the prior decision rather than re-running the analysis. -->

- Considered and deferred indefinitely (research session 215, Apr 2026): Skills-standard hybrid migration (DOE's value is orchestration, not per-directive content; portable Skills omit the orchestration layer; two-system overhead exceeds the theoretical portability gain), disposable-worktree validation in /review (existing hooks already gate at commit/push -- no validation gap to close), auto-fix mode for /review findings (contradicts the Surgical Changes principle -- silent AI edits violate "every changed line traces to the user's request"), structured contract format with linter (`/agent-launch` already validates Verify: patterns -- speculative for the one drift instance we have), kit-as-submodule for DOE-using projects (UX cost > benefit; setup.sh "just works" model is the right primitive for non-technical users), DOE Lite single-file curl-installable distribution (decision is "stay with the full kit unless tooling ecosystem forces a change"; viral surface is a marketing question, not engineering, and competing with the full kit at the install gate would dilute adoption). See the 5 v2.0 GH issues that survived the cull (Kit-bloat audit, Persistent memory layer, Cross-project asset sharing, Performance engineering directive, Output evals).
