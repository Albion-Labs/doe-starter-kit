# ROADMAP.md — The Big Picture

ROADMAP.md is your product planning file. It's where ideas are captured, prioritised, and tracked from first thought to shipped feature. While [tasks/todo.md](todo-md.md) tracks the detailed steps of whatever you're building right now, ROADMAP.md shows the full picture — everything you might build, everything you've shipped, and what's next.

## How It's Organised

The file has sections arranged from most concrete (top) to most speculative (bottom):

### Up Next

Features that are planned and ready to build. Each has a description, a status tag, and usually a link to a plan file. When the current feature in todo.md finishes, the next one gets pulled from here.

### Suggested Next

Claude's recommendation for what to build next, based on the current state of the project. Two or three items maximum. This gets updated when the project state changes significantly (a feature ships, new data arrives, user feedback changes priorities).

### Must Plan

Important features that will be built but need scoping first. These might have blockers ("need legal sign-off first"), prerequisites ("requires the database backend"), or just haven't been designed yet. They're commitments, not ideas — they just need more thinking before they become actionable.

### Ideas

Casual captures. Anything you might want to build someday. No commitment, no order, no pressure. The point is to not lose good ideas. Some will eventually move up to Must Plan or Up Next. Most will stay here or quietly get removed.

### Claude Suggested Ideas

Ideas that Claude pitches while working on other things. When Claude notices a gap, a natural extension, or a data source that would add value, it adds a brief pitch here. You can promote these to Ideas or Must Plan if they're interesting, or ignore them.

### Parked

Features that were considered but aren't being pursued right now. Keeps them visible without cluttering the active sections.

### Complete

Shipped features, newest first. One-line summaries with version numbers and dates. This is the project's shipping history.

## How Features Flow

The typical journey of a feature:

```
Ideas → Must Plan → Up Next → Current (in todo.md) → Complete
```

1. An idea gets captured in Ideas (by you or Claude)
2. When it's important enough, it moves to Must Plan
3. After scoping (writing a plan, defining steps), it moves to Up Next with a PLANNED tag
4. When it's time to build, it moves to `## Current` in todo.md
5. When all steps are done, it moves to Complete in ROADMAP.md

Not every feature follows this exact path. Simple features might jump straight from Ideas to Up Next. Complex ones might sit in Must Plan for weeks while prerequisites are sorted out.

## Status Tags

Every entry in Up Next and Must Plan has a status tag:

| Tag | Meaning |
|-----|---------|
| `SCOPED` | Has a brief or description but no implementation steps yet |
| `PLANNED` | Has steps and contracts — ready to build |
| `IN PROGRESS` | Currently being built (in todo.md ## Current) |
| `COMPLETE` | Shipped and done |

## Timestamps

Every entry gets a timestamp showing when it was added or last changed:

```markdown
*(pitched 03/03/26)* — for ideas
*(added 05/03/26)* — for planned features
*(scoped 10/03/26)* — when a plan was written
*(completed 09/03/26)* — for shipped features
```

## A Realistic Example

```markdown
## Up Next

### Live Weather Alerts [APP] — PLANNED
Real-time severe weather warnings per region. API integration with Met Office.
3 steps. Plan: `.claude/plans/weather-alerts.md`. *(scoped 15/03/26)*

### Admin Dashboard [INFRA] — SCOPED
Usage analytics and system health monitoring. Needs design before steps can be
written. *(added 12/03/26)*

## Must Plan

### Mobile App Wrapper
PWA scaffold for mobile access. Blocked on: responsive redesign must finish first.
*(pitched 08/03/26)*

## Ideas

### Dark Mode Toggle
User-requested. Low effort, nice-to-have. *(pitched 10/03/26)*

### CSV Export for All Tables
Let users download any data table as CSV. *(pitched 05/03/26)*

## Complete

### Recipe Search [APP] (v0.5.2) — COMPLETE
Search bar, category filters, and result sorting for the recipe list page.
*(completed 14/03/26)*

### User Profiles [APP] (v0.4.0) — COMPLETE
Profile pages with preferences, saved recipes, and cooking history.
*(completed 10/03/26)*
```

## When You'd Edit It

- **Capturing a new idea** — add it to Ideas with a timestamp
- **Prioritising** — move something from Ideas to Must Plan or Up Next
- **After scoping** — update a Must Plan entry with a PLANNED tag and link to the plan file
- **Reviewing progress** — Claude updates the Complete section automatically after shipping a feature, but you might want to adjust wording or add context

## Where It Lives

`ROADMAP.md` in the root of your project directory.

## Related Files

- [tasks/todo.md](todo-md.md) — where features go when they're actively being built
- [STATE.md](state-md.md) — tracks which roadmap feature is currently in progress
- [CLAUDE.md](claude-md.md) — contains the rules for how features flow between these files
