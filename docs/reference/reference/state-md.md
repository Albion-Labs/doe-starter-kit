# STATE.md — Session Memory

When you close Claude Code or run `/clear`, the conversation is gone. Claude has no memory of what you discussed. STATE.md solves this problem — it's a small file that persists between sessions, giving Claude just enough context to pick up where it left off.

Think of it as a sticky note on Claude's desk that survives between shifts.

## What It Contains

STATE.md has three sections:

### Current Position

What you're working on right now. The active feature, the current step, the project version. This is the first thing Claude reads when a session starts, so it knows immediately what's in progress.

### Blockers & Edge Cases

Known problems, workarounds, and things to watch out for. These stay here until they're resolved. If Claude hit a bug in the last session that it couldn't fix, it records it here so the next session doesn't repeat the same investigation.

### Last Session

A one or two sentence summary of what happened in the most recent session. This gets overwritten every session — it's not a history log, just "what did we do last time?"

## A Realistic Example

Here is what a real STATE.md looks like mid-project:

```markdown
# Project State

Session memory that persists across sessions. Claude updates this file
automatically; you rarely need to edit it manually.

## Current Position

**Active feature:** User Dashboard [APP] (v0.5.x) — Steps 1-2 complete, Step 3 next
**Current app version:** v0.5.2 (`my-app-v0.5.2.html`)

## Blockers & Edge Cases

- Weather API rate limit is 60 requests/minute — batch calls in groups of 50
  with a 1-second delay between batches.
- Safari renders the chart tooltips behind the modal overlay. No fix yet —
  tracked as a known issue.

## Last Session

Built the activity feed component and integrated it with the dashboard layout.
Chart rendering works but tooltip z-index needs fixing on Safari.
```

## Who Updates It

Claude updates STATE.md automatically during sessions — typically when wrapping up a session using the `/wrap` command, or when a significant state change happens (a blocker is discovered, an approach changes, a step completes).

You rarely need to edit it manually. The main reason you would is to correct something Claude got wrong, or to add a blocker you discovered outside of Claude Code (e.g., you found a bug while testing in the browser).

## How Claude Uses It

At the start of every session, Claude reads STATE.md (along with CLAUDE.md and learnings.md). This gives it three things:

1. **What to work on** — the active feature and step
2. **What to avoid** — known blockers and edge cases
3. **What just happened** — context from the last session

Without STATE.md, every session would start from zero. Claude would have to ask "what are we working on?" and you'd have to re-explain the current state. STATE.md eliminates that friction.

## Rules for STATE.md

- **Replace, don't accumulate.** This file reflects current state, not history. Old blockers get removed when resolved. The Last Session summary gets overwritten, not appended.
- **Keep it short.** Maximum around 30 lines of content. If it's getting longer, something should be moved to learnings.md (for permanent patterns) or removed (if it's no longer relevant).
- **Current state only.** Decisions and their reasoning go in learnings.md. STATE.md just tracks where things are right now.

## Where It Lives

`STATE.md` sits at the root of your project directory, next to CLAUDE.md.

## Related Files

- [CLAUDE.md](claude-md.md) — the rules that tell Claude to check STATE.md at session start
- [tasks/todo.md](todo-md.md) — the detailed task tracker (STATE.md points to the active step)
- [learnings.md](learnings-md.md) — where permanent knowledge goes (STATE.md is temporary)
