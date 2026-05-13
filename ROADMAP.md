# Product Roadmap

A living notepad for what to build. Sections flow from most concrete to most speculative. When you're ready to build something, tell Claude to plan it.

<!--
Claude: section rules
- ## Up Next: Planned and scoped. Has todo.md steps or a plan file. Pull from here when Current is empty.
- ## Suggested Next: Claude's strategic recommendation based on project state. 2-3 items max. Update when project state changes significantly (feature ships, new data, user feedback). If empty, promote from Ideas or pitch new ones.
- ## Must Plan: Important items that need scoping before they can be built. Blockers, prerequisites, compliance. Not ideas — these WILL be built, just not yet planned.
- ## Ideas: Casual captures. No commitment, no order. Just don't lose them.
- ## Claude Suggested Ideas: AI-pitched additions based on the codebase and product direction. Refresh periodically. User can promote to Ideas, Must Plan, or Up Next.
- ## Parked: Considered but not pursuing right now.
- ## Complete: Shipped, newest first.
- Every entry gets a *(pitched/added DD/MM/YY)* or *(added HH:MM DD/MM/YY)* timestamp.
- Status tags: PLANNED, IN PROGRESS, COMPLETE. Used on Up Next and Must Plan entries.
- When pitching (Rule 9): add to Ideas with timestamp. If the user says "this is important" or "note for later", add to Must Plan instead.
-->

## Up Next
<!-- Planned and scoped. Has todo.md steps or a plan file. Pull from here when Current is empty. -->

## Suggested Next
<!-- Claude's strategic recommendation based on where the project is now. 2-3 items, updated when project state changes. -->

## Must Plan
<!-- Important items that WILL be built but need scoping first. Blockers, prerequisites, compliance. Not ideas — these are commitments waiting for a plan. -->

## Ideas
<!-- Anything you might want to build. No commitment, no order. Just capture it. -->

## Claude Suggested Ideas
<!-- AI-pitched additions based on the codebase and product direction. Refreshed periodically. Promote to Ideas or Must Plan if interesting. -->

## Parked
<!-- Things you considered but aren't pursuing right now. Keeps them out of the way without losing them. -->

## Complete
<!-- Shipped features, newest first. One-line summary each, tagged [APP] or [INFRA]. For step-by-step detail, see tasks/archive.md. -->

- **Worktree auto-detection + parallel-session protocols (v1.63.0)** [INFRA] — Operationalises the v1.61.5 convention end-to-end: `/stand-up` reads `git worktree list --porcelain` and shows a WORKTREES row with branch summary, detached-worktree hints, and the honest-scope footnote (worktrees fix BRANCH-level races, not FILE-level edit conflicts). `/wrap` Step 0a detects branch drift via `.tmp/.session-start-branch` (captured by `/crack-on` at kick-off) and auto-switches to the trunk worktree for bookkeeping commits. `/sync-doe` + `/pull-doe` gain a trunk-worktree pre-flight via `git symbolic-ref refs/remotes/origin/HEAD` (resilient across main / master defaults). Two new slash commands `/worktree-create` and `/worktree-remove` operationalise the convention with safety gates -- locked worktrees stay locked until explicit `git worktree unlock`, trunk worktrees stay non-removable. Init wizard surfaces the convention at scaffolding time. Step 0 spike (`monty/.tmp/worktree-spike.md`) caught three pre-existing relative-path landmines in hook scripts (silent false-pass under shell cwd drift); fixes bundled into Step 2 rather than a separate v1.62.3 patch. Suite 199 -> 203 tests. *(shipped 12/05/26)*
- **Hook commands cwd-safe ($CLAUDE_PROJECT_DIR, v1.62.2)** [INFRA] — Safety-critical fix: every PreToolUse / PostToolUse hook command in `.claude/settings.json` now uses `python3 "$CLAUDE_PROJECT_DIR/.claude/hooks/X.py"` instead of the relative `python3 .claude/hooks/X.py` form. Pre-fix, any legitimate `cd` in the agent shell caused subsequent hook invocations to fail errno-2 and brick every Edit/Write/Bash tool call in the session. 18 commands updated across settings.json + hook-templates/universal.json + docs/reference/reference/hooks.md. 4 regression tests in tests/claude_hooks/test_settings_paths_cwd_safe.py. No `$PWD` fallback -- fail-loud on missing env-var beats silent re-introduction. Documented project-side migration one-liner in `### Pull impact` since setup.sh hook-merge deduplicates by exact command-string match. *(shipped 12/05/26)*
- **Worktree convention for parallel sessions (v1.61.5)** [INFRA] — New `directives/parallel-worktrees.md` codifies the convention for multiple Claude sessions on the same project: `<project>/` lives on `main`, long-lived feature branches get sibling `<project>-<feature>/` worktrees. Each session gets its own working directory and HEAD; one session's `git checkout` cannot silently move another session's HEAD onto the wrong branch. Universal CLAUDE.md template gains `## Parallel Sessions` section as a positive-form rule with Tradeoff: line. Honest scope: worktrees fix the BRANCH-level race, not the FILE-level race for shared docs. Convention-statement only -- auto-detection layer queued separately as v1.62.0. Source: a consumer project's session retro. *(shipped 08/05/26)*
- **Hook misfire fixes -- commit-msg path + cross-project guard (v1.61.4)** [INFRA] — `.githooks/commit-msg` changelog-enforcement check switched from the long-removed `changelog.html` to `whats-new.html` (eliminates false positive that required `SKIP_CHANGELOG_CHECK=1` for legitimate version-tagged commits). `.claude/hooks/enforce_review_gate.py` gains a cross-project guard: when a Bash command starts with `cd <other-dir> &&` resolving outside the hook's cwd tree, the hook exits silently rather than gating the wrong project's release-readiness state. Three new tests cover the cross-project guard. *(shipped 08/05/26)*
- **Hook output validation -- silent no-opinion (v1.61.3)** [INFRA] — All six guardrail hooks (block_dangerous_commands, block_secrets_in_code, confirm_pr_merge, enforce_review_gate, guard_kit_writes, protect_directives) had their no-opinion paths emitting invalid `{"decision": "allow"}` JSON, triggering "Hook JSON output validation failed" warnings on every Bash/Edit/Write/MultiEdit call (~80 wasted tokens per Bash). Replaced with `sys.exit(0)` -- the canonical silent no-opinion signal. Block paths unchanged. Behaviour-neutral, just stops the noise. *(shipped 08/05/26)*
- **Pink Elephant diff-bounded canonical pattern (v1.61.2)** [INFRA] — Documents the canonical Pink Elephant compliance check in `directives/testing-strategy.md` ## Pattern Reference: rev-parse precondition (closes silent-pass mode on missing `origin/main` ref), two-grep additions filter (`grep "^+" | grep -v "^+++ "` keeps markdown `+` bullets in scope), and word-boundary prohibition scan. Replaces the brittle `grep -A N` form that captured pre-existing surrounding content. Old form named in-place as Before/After anti-pattern via the v1.61.1 convention. Closes kit issue #42. *(shipped 08/05/26)*
- **Directive enrichments (v1.61.1)** [INFRA] — Three additive enrichments: Three Layers of Knowledge sub-block (Layer 1 tried-and-true / Layer 2 new-and-popular / Layer 3 first-principles, names Layer 2 mania) under "Reuse before writing" in `building-rules.md`; optional Anti-patterns bullet convention as meta-block in `_TEMPLATE.md`; one-line rationale linking the trace test in Surgical Changes to its human-in-loop purpose. Pure additive — no procedure or hook changes. Sources: gstack ETHOS.md (Garry Tan / YC, MIT) and Willison's "merchants of complexity" framing. *(shipped 06/05/26)*
- **Karpathy integration (v1.61.0)** [INFRA] — Added Andrej Karpathy's four engineering principles (Think Before Coding / Simplicity First / Surgical Changes / Goal-Driven Execution) to the universal CLAUDE.md template in positive form, with three companion directive enrichments: intent-test + transform table + skill-prep (planning-rules.md); mini-plan format + evidence-gate generalisation (building-rules.md); merge-pattern matching (delivery-rules.md). Pure additive — no procedure or hook changes. Karpathy attribution to forrestchang/andrej-karpathy-skills (MIT). *(shipped 05/05/26)*
- **Pink Elephant rewrite (v1.59.0)** [INFRA] — Converted load-bearing negation rules across CLAUDE.md, the universal template, and 35 directives to positive "When X, do Y" form per the Pink Elephant article (arxiv 2503.22395) and IFEval/InFoBench evidence. Added `Tradeoff:` lines to 25 of 26 flat directives. Fixed PreToolUse and PostToolUse matcher casing in `.claude/settings.json` (kit hooks were silently non-functional since their introduction; case-sensitive Tool name strings now match real tool calls). Extended `protect_directives.py` and `block_secrets_in_code.py` to the `Bash` matcher so redirected writes (`cat >`, `tee`, `sed -i`) covering `directives/` files or carrying secret-shaped values are caught. Authored `migrations/v1.59.0.md` with 135 OLD/NEW/WHY phrase pairs across 31 files plus four behavioural-change records, consumed by a new `/pull-doe` pre-flight phase that warns projects about retired phrases before they pull. *(shipped 29/04/26)*
