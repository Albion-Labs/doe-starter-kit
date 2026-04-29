# Universal Learnings

Cross-project patterns that apply to any codebase. Auto-loaded by Claude Code at every session start.

## Grammar

These learnings are written in positive "When X, do Y" form. The grammar matters: prohibition-style rules have a documented failure mode where the model re-activates the forbidden concept and fills the un-named gap with training-baked defaults (arxiv 2503.22395, "Pink Elephants in Your CLAUDE.md"). Positive specs name the action; binary YES/NO sub-criteria make compliance auditable.

When you add a new learning, write the rule as the action you want, with the verifiable check inline. The Canary section below is the leading indicator: if you find yourself violating any canary rule, treat it as a signal that context has drifted -- re-read the directive triggers relevant to the current task before continuing.

## Canary

- **British English throughout.** Use colour, behaviour, organisation, optimise, recognise. Verify: `! grep -rE '\b(color|behavior|organize|optimize|recognize)\b' directives/` returns no matches.
- **Cite directives by file path when applying them.** Write "per `directives/X.md`" so the reader can navigate to the source.
- **Bordered output uses Unicode box-drawing characters** (`┌─┐├─┤└─┘│`); content inside borders stays ASCII (no emojis, no `·`, no `…`) so terminal monospace alignment holds.

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

## Output

- Assemble multi-section formatted output (wrap-ups, reports, dashboards) as a single block, generated in one script and printed in one tool call. [retro: universal]
- After generating formatted output (wrap-ups, dashboards) via a Bash/Python script, echo the full output as text in your response. Tool output alone is invisible to the user; the user expects the output as your actual reply. [retro: universal]

## DOE Starter Kit

- During feature work, make changes in the project repo first; run `/sync-doe` once at feature end to push them to the kit. The sync procedure handles tutorial footer stamping, changelog, tagging, pushing, AND creating the GitHub release. Direct commits to the kit skip all of these -- the tag may exist locally but no release appears on GitHub. [retro: universal]

## Verification

- After creating or editing files, verify with `ls`/`cat`/`grep` before reporting success. Verify even "obvious" edits. [retro: universal]
-->
