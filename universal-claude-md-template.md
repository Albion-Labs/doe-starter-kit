# Universal CLAUDE.md

Cross-project patterns and engineering defaults that apply to any codebase. Auto-loaded by Claude Code at every session start. Three layers: **Canary** (red flags signalling context drift), **Core Behaviours** (engineering defaults that apply to every session), and **Learnings** (specific patterns and gotchas captured retroactively).

## Grammar

These rules are written in positive "When X, do Y" form. The grammar matters: prohibition-style rules have a documented failure mode where the model re-activates the forbidden concept and fills the un-named gap with training-baked defaults (arxiv 2503.22395, "Pink Elephants in Your CLAUDE.md"). Positive specs name the action; binary YES/NO sub-criteria make compliance auditable.

When you add a new learning, write the rule as the action you want, with the verifiable check inline. The Canary section below is the leading indicator: if you find yourself violating any canary rule, treat it as a signal that context has drifted -- re-read the directive triggers relevant to the current task before continuing.

## Canary

- **British English throughout.** Use colour, behaviour, organisation, optimise, recognise. Verify: `! grep -rE '\b(color|behavior|organize|optimize|recognize)\b' directives/` returns no matches.
- **Cite directives by file path when applying them.** Write "per `directives/X.md`" so the reader can navigate to the source.
- **Bordered output uses Unicode box-drawing characters** (`┌─┐├─┤└─┘│`); content inside borders stays ASCII (no emojis, no `·`, no `…`) so terminal monospace alignment holds.

## Core Behaviours

Four engineering defaults credited to Andrej Karpathy via forrestchang/andrej-karpathy-skills (MIT). Written in positive form per the Grammar section above.

**Tradeoff:** these defaults bias toward caution over speed. For trivial tasks, use judgement.

### Think Before Coding

**State assumptions, surface confusion, surface tradeoffs.**

Before implementing:
- Name your assumptions explicitly. Ask when uncertain.
- When multiple interpretations exist, present them and ask which one fits.
- When a simpler approach exists, name it. Push back when warranted.
- When something is unclear, pause, name what is confusing, and ask.

### Simplicity First

**Minimum code that solves the problem. Build only what was asked.**

- Build only what was asked. Defer features beyond the request.
- Reserve abstractions for the second use.
- Add flexibility only when the user requests it.
- Handle errors that can actually occur; trust internal guarantees.
- If you write 200 lines and 50 would do, rewrite it.

Ask yourself: would a senior engineer say this is overcomplicated? If yes, simplify.

### Surgical Changes

**Touch only what the request requires. Clean up your own changes only.**

When editing existing code:
- Leave adjacent code, comments, and formatting alone.
- Refactor only what the request requires.
- Match the existing style; consistency beats personal preference.
- When you notice unrelated dead code, mention it; leave deletion to a separate request.

When your changes create orphans:
- Remove imports, variables, and functions that your changes orphaned.
- Leave pre-existing dead code in place unless asked.

The test: every changed line should trace directly to the user's request. This keeps human reviewers in the loop: small, traceable diffs are checkable at a glance.

### Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" -> "Write tests for invalid inputs, then make them pass."
- "Fix the bug" -> "Write a test that reproduces it, then make it pass."
- "Refactor X" -> "Ensure tests pass before and after."

For multi-step tasks, state a brief plan inline:

```
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") force constant clarification.

These behaviours are working if: fewer unnecessary changes in diffs, fewer rewrites from overcomplication, and clarifying questions arrive before implementation rather than after mistakes.

<!--
Claude: short bullet points under descriptive ## headings. One learning per line.
Max 30 lines of content. When full, replace the least useful before adding new.
Only truly universal patterns here -- project-specific learnings go in that project's learnings.md.
Tag source: e.g. "[retro: feature-name vX.Y.Z]"

## Python Execution

- When caching large API downloads to disk, delete stale caches before re-running with different parameters (e.g. changed page size). A partial cache from a previous run silently produces incomplete results. [retro: universal]
- macOS system Python 3.9 has an old OpenSSL that fails TLS 1.3 sites (`TLSV1_ALERT_PROTOCOL_VERSION`). Use `subprocess` + `curl` for downloads from sites requiring modern TLS. [retro: universal]

## Shell & Platform

- macOS `sed -i` requires an empty backup extension: `sed -i '' '...'`. Linux uses `sed -i '...'` with no argument. Git hooks and shell scripts must account for this or they fail silently on one platform. [retro: universal]
- Bordered output uses text-only labels; emojis render double-width in terminal monospace fonts and break border alignment. Emojis are fine in standalone or unbounded contexts. [retro: universal]
- zsh `for f in glob-*` fails with `no matches found` when no files match (bash silently skips). Guard with `(setopt nullglob 2>/dev/null; for f in ...)` or `ls glob-* 2>/dev/null`. [retro: universal]
- Use a fixed file name for cross-call state in Claude Code Bash tool calls; `$$` is the subshell PID and differs between calls. Worktrees handle multi-session isolation. [retro: universal]
- Bash pipelines return the LAST command's exit code. `cmd | tail -N && side_effect` fires the side effect even when `cmd` failed -- `tail` exits 0, so `&&` proceeds. Before chaining a destructive command (`&& git tag`, `&& git push`, `&& rm`) after a pipe-trimmed output, split into separate Bash tool calls so exit codes propagate, or prefix with `set -o pipefail`. `pipefail` is OFF by default in zsh and bash. [retro: universal]

## Dev Servers

- Before starting any dev server (Next.js, Vite, Webpack, etc.), kill existing instances on the same or adjacent ports. Stale servers compete for CPU/memory during on-demand compilation, causing unvisited routes to hang while cached pages work fine. macOS: `pkill -f "next dev"` or `lsof -ti:3000 | xargs kill`. Windows: `taskkill //f //im node.exe`. [retro: universal]

## Hooks & Session Files

- Hooks that write per-invocation files (e.g. per-PID tracking) accumulate hundreds of orphans per session. Use a single fixed-name file and overwrite each invocation; hooks need the latest state, not history. [retro: universal]

## Parallel Sessions

- For multiple Claude sessions on the same project, use a separate `git worktree` per long-lived branch. Each session gets its own working directory and HEAD; one session's branch switch cannot silently move another session's HEAD. Convention: `<project>/` lives on `main`; feature work happens in sibling `<project>-<feature>/` worktrees, removed when the feature merges. See `directives/parallel-worktrees.md` for setup, scope, and cleanup. Tradeoff: build artefacts (`node_modules/`, `.next/`, etc.) duplicate per worktree; shared docs (STATE.md, todo.md, learnings.md, CLAUDE.md) still need "edit from one terminal at a time" coordination since all worktrees write to the same git history. [retro: parallel-session branch race silently moved wrap commits onto a long-lived feature branch]

## Output

- Assemble multi-section formatted output (wrap-ups, reports, dashboards) as a single block, generated in one script and printed in one tool call. [retro: universal]
- After generating formatted output (wrap-ups, dashboards) via a Bash/Python script, echo the full output as text in your response. Tool output alone is invisible to the user; the user expects the output as your actual reply. [retro: universal]

## DOE Starter Kit

- **Kit changes flow through PRs** (v1.60.0+ PR-only model). The kit's `.githooks/pre-commit` 'no direct-to-main' hook plus human PR review are the canonical write gate. Two ways to land a kit change, both PR-based: (1) **Manual PR** for a one-off fix or improvement — branch in the kit, commit, push, `gh pr create`, review, merge, same as any other repo. (2) **`/sync-doe`** for bundling many project-originated kit changes into a versioned release — translates project-side improvements, opens a kit PR with the diff + CHANGELOG entry + version bump (Phase 1), then after merge runs the post-merge release machinery (Phase 2: tutorial stamp + tag + GitHub release) on main with a narrowly-scoped `SKIP_MAIN_PROTECTION=1` for the stamp commit only. Pick the manual PR for a one-line bug fix; pick `/sync-doe` when you have multiple project-originated changes ready to release. If you discover a kit bug while working in a project repo, keep the local patch (so the project keeps working) and open a kit PR with the same fix; the project-side patch can be removed after `/pull-doe` syncs the merged version back. See `directives/kit-development.md` ## Kit-write model: PR-only. [retro: universal]

## Verification

- After creating or editing files, verify with `ls`/`cat`/`grep` before reporting success. Verify even "obvious" edits. [retro: universal]
-->
