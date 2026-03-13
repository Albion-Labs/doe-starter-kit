# State Management

## The Memory Problem

When you close Claude Code, the conversation disappears. Every new session starts completely fresh — Claude doesn't remember what you built yesterday, what broke last week, or what you decided to do next.

Without a memory system, you'd have to re-explain your entire project at the start of every session. "We're building a political data dashboard. The election results import is done but the demographic overlay is half-finished. Last time we hit a bug with Scottish constituency names not matching — we fixed it by normalising to ONS codes. Oh, and the API has a rate limit of 100 requests per minute, so don't hammer it."

That gets old fast. And you'll forget things. And Claude will make the same mistakes again because nobody told it not to.

DOE solves this with a layered memory system — four files, each serving a different purpose, each checked automatically at the right time.

## The Four Memory Files

### STATE.md — Short-Term Memory

**What it is:** A snapshot of where things stand right now.

STATE.md captures what's happening in the current moment: what feature you're working on, what happened in the last session, what's blocked, what to try next. Claude updates this automatically when you end a session with `/wrap`.

Think of it as a sticky note on your monitor that says: "Picked up here. The import script works but the date parsing is wrong for Scottish data. Try converting to ISO format before the merge step."

A typical STATE.md looks like this:

```markdown
## Current Position
Working on: Demographic overlay for constituency map
Last session: Fixed Scottish constituency name matching (ONS codes)
Next step: Wire up the overlay toggle in the UI

## Blockers
- Census API returns UTF-8 BOM — need to strip before parsing

## Recent Decisions
- Using ONS constituency codes as the join key (not names — too inconsistent)
```

It's short, concrete, and focused on what Claude needs to know *right now* to pick up where you left off.

### learnings.md — Long-Term Memory

**What it is:** Patterns discovered over the life of the project. Things that went wrong, how they were fixed, and how to avoid them next time.

While STATE.md is "what's happening now," learnings.md is "what we've learned along the way." It's the project's institutional memory — the accumulated wisdom from every bug, every API quirk, every decision that took longer than it should have.

When Claude encounters a situation similar to something that's gone wrong before, it checks learnings.md first. If there's a relevant pattern, it follows the known-good approach instead of discovering the problem again from scratch.

Entries range from one-liners to structured breakdowns:

```markdown
- Nomis API returns CSV with UTF-8 BOM — always strip with .lstrip('\ufeff'). [retro: census import]
- Scottish constituency data uses different column names than England/Wales.
  Map 'constituency_name' → 'pcon_name' before merging. [retro: demographic overlay]
```

The key constraint: learnings.md stays concise. It's capped at around 50 lines. Only the most useful, most frequently relevant patterns survive. If a learning becomes irrelevant (the API changed, the bug was fixed upstream), it gets removed. This isn't a diary — it's a distilled reference.

### tasks/todo.md — Work Tracker

**What it is:** The active task list. What's being built, what's waiting, and what's finished.

todo.md is where work gets planned and tracked. It has three sections:

- **Current** — What's actively being worked on right now
- **Queue** — Approved tasks waiting their turn
- **Done** — Completed work (kept for reference and version history)

Each task has numbered steps with contracts — testable criteria that define "done" for each step. Here's what an entry looks like:

```markdown
## Current

### Demographic overlay for constituency map
1. [x] Import Census constituency-level data
   - Contract: [auto] Verify: run: python3 execution/import_census.py --validate
   - Contract: [auto] Verify: file: src/data/census_constituencies.json exists
2. [ ] Build overlay toggle component
   - Contract: [auto] Verify: file: src/components/overlay-toggle.js exists
   - Contract: [manual] Toggle switches between election results and demographics smoothly
3. [ ] Wire up colour scale for demographic values
   - Contract: [auto] Verify: run: python3 execution/test_colour_scale.py
```

The `[x]` marks show progress. The contracts make it unambiguous whether each step is actually done — no "I think that works" — there's a concrete check.

This is where you track *how* something is being built. For *what* should be built, that's the next file.

### ROADMAP.md — Big Picture

**What it is:** Product-level planning. The bird's-eye view of where the project is going.

While todo.md tracks the steps to build a specific feature, ROADMAP.md tracks which features matter and in what order. Ideas flow through stages:

- **Ideas** — Interesting possibilities. No commitment, just captured so they don't get lost.
- **Must Plan** — Important enough to design properly before building. Needs a plan in `.claude/plans/` before work starts.
- **Up Next** — Planned and ready to go. Will move to Current when the current work is done.
- **Current** — Actively being built. Has a matching entry in todo.md with steps and contracts.
- **Complete** — Shipped and done.

ROADMAP.md answers "what should we build and in what order?" todo.md answers "how are we building the thing we're building right now?" They work together but serve different purposes.

## How Memory Flows

Here's what happens across a typical session:

**Session start:**
Claude reads STATE.md, learnings.md, and todo.md automatically (they're referenced in CLAUDE.md, which loads every session). Within seconds, Claude knows: what you're working on, what's been tried, what to watch out for, and what step comes next.

**During the session:**
You work. Claude writes code, runs scripts, fixes bugs, commits progress. If it discovers something worth remembering (an API quirk, a platform-specific gotcha), it notes it for later.

**Session end (`/wrap`):**
Claude updates the memory files:
- **STATE.md** gets rewritten with what happened this session, where things stand now, and what to do next
- **learnings.md** gets any new patterns added (if something failed and the fix is worth recording)
- **todo.md** gets completed steps marked `[x]` and any new tasks added

**Next session:**
The cycle repeats. Claude reads the updated files and picks up exactly where you left off.

## What Happens If You Skip /wrap

The code itself is safe — Claude commits work as it goes (every completed task gets its own commit). Your progress is saved in git regardless.

But STATE.md won't be updated. Next session, Claude has to piece together what happened by reading the git log and scanning the code. It can do this — it's not a disaster — but it's slower and less reliable than having a clean summary waiting.

It's like leaving work without writing yourself a note about where you stopped. You'll figure it out tomorrow morning, but you'll waste ten minutes doing it. Multiply that across dozens of sessions and it adds up.

Always `/wrap` when you're done for the day.

## CLAUDE.md — The Rules

CLAUDE.md is different from the four memory files. It's not memory — it's the project's instruction manual.

CLAUDE.md is loaded automatically at the start of every session. It contains:

- **Operating rules** — How Claude should behave (plan before building, ask don't assume, verify before delivering)
- **Guardrails** — What Claude must never do (overwrite directives, store secrets in code, force-push without permission)
- **Directory structure** — Where files go and why
- **Triggers** — Patterns that tell Claude when to load specific directives (e.g. "if importing external data, read the data import directive first")

This file rarely changes. When it does, it's usually to add a new trigger or tighten a guardrail based on something that went wrong. Think of it as the project's constitution — it sets the rules that everything else operates within.

The memory files (STATE.md, learnings.md, todo.md, ROADMAP.md) change constantly. CLAUDE.md provides the stable foundation they all sit on.
