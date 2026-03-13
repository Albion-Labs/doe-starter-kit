# learnings.md — Long-Term Memory

STATE.md is Claude's short-term memory — it tracks where things are right now. learnings.md is Claude's long-term memory — it records patterns, mistakes, and decisions that should survive forever (or until they're no longer relevant).

Think of it as institutional knowledge. When Claude hits a bug in session 47 and figures out the fix, it writes that fix to learnings.md so it doesn't waste time rediscovering it in session 83.

## What It Contains

learnings.md is organised into sections by topic. The exact sections depend on your project, but common ones include:

- **Process & Workflow** — how to work effectively (planning patterns, sequencing, scope management)
- **API & Integration Patterns** — external service quirks (rate limits, auth, data formats)
- **Execution Script Gotchas** — bugs and edge cases in your scripts
- **Architecture Decisions** — why things are built the way they are
- **UI Patterns** — reusable patterns for the interface
- **Common Mistakes** — recurring errors to watch for

## Entry Formats

There are two formats, depending on severity.

### Routine Entries (One Line)

Most entries are a single line — specific, actionable, tagged with where the learning came from:

```markdown
## API & Integration Patterns

- Nomis API silently caps page size at 25,000 rows regardless of what you
  request. Always paginate at 25K. [retro: census-2011 v0.8.0]
- UK government CSVs from data.gov.uk often have UTF-8 BOM. Use
  encoding="utf-8-sig" when reading with Python's csv module. [retro: census v0.8.0]
```

```markdown
## Process & Workflow

- Building the changelog UI first (before steps that add entries) avoids
  rework — structure exists before content needs inserting. [retro: changelog v0.10.5]
```

The `[retro: ...]` tag tells you which feature or session produced the learning, so you can trace it back if you need more context.

### Significant Entries (Structured)

When something went seriously wrong — wasted more than 30 minutes, broke something, or happened more than once — it gets a structured write-up:

```markdown
### Learning: Wave merge lost contract checkmarks

**What happened:** During a parallel build, the housekeeping task merged first and
rewrote todo.md, stripping contract checkmarks before other tasks could record theirs.

**Root cause:** Merge ran all updates at the end instead of incrementally after
each task.

**Fix applied:** Changed merge to run todo.md updates after each task merge, not
once at the end.

**Prevention:** Added "incremental merge" to the wave coordination protocol.
[retro: wave-1 post-mortem]
```

## The 50-Line Rule

learnings.md has a soft cap of 50 lines of content. This forces curation — only the most useful patterns survive. When the file gets full:

- Remove entries for bugs that have been permanently fixed (the code already has the fix)
- Remove entries for patterns you've internalised (they're now in CLAUDE.md as rules)
- Remove entries for tools or APIs you no longer use
- Keep entries for things that could bite you again

The goal is signal, not volume. A 200-line learnings file is noise. A 40-line file where every line saves future time is gold.

## Who Updates It

**Claude** adds entries automatically in two situations:

1. **Self-Annealing** — when something fails and Claude diagnoses and fixes it, it logs the learning so the same failure doesn't happen twice.
2. **Feature retros** — at the end of every feature, Claude reviews what happened and logs any patterns worth remembering.

**You** can add entries manually too. If you discover something while testing in the browser, or learn a useful pattern from outside the project, add it directly. Just follow the format: one line, specific, tagged with a source.

## Classification: Project vs Universal

Not all learnings belong in the project file. Claude classifies each learning:

- **Project-specific** (references your project's names, configs, custom setup) goes in your project's `learnings.md`
- **Universal** (general pattern any project could hit) goes in `~/.claude/CLAUDE.md`, the global instruction file

For example: "Our API endpoint requires the `X-Custom-Auth` header" is project-specific. "macOS `sed -i` requires an empty backup extension" is universal.

## A Realistic Example

Here is what a learnings.md might look like in a small project:

```markdown
# Project Learnings

## Process & Workflow

- Build infrastructure (shared components, layout system) before content that
  uses it. Sequence matters. [retro: dashboard v0.3.0]
- Flag scope creep early. "Add a button" became 4 changes across 5 files.
  Pause and ask "do all of these now?" when scope grows. [retro: settings v0.4.0]

## API & Integration Patterns

- Weather API rate limit is 60 requests/minute. Use 0.5s delay between
  calls. [retro: weather-import v0.2.0]
- The recipes CSV from example.com has a UTF-8 BOM. Use encoding="utf-8-sig".
  [retro: data-import v0.1.0]

## Common Mistakes

- Don't rewrite the entire build script to fix a path issue — the build
  script works, the path was wrong. Surgical fixes only. [retro: build-fix v0.3.1]
```

## Where It Lives

`learnings.md` in the root of your project directory, next to CLAUDE.md and STATE.md.

## Related Files

- [CLAUDE.md](claude-md.md) — contains the Self-Annealing rules that produce learnings
- [STATE.md](state-md.md) — temporary state (learnings.md is permanent knowledge)
- [directives/](directives.md) — when a learning pattern recurs often enough, it may become a directive
