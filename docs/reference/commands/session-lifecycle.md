# Session Lifecycle Commands

These five commands form the daily rhythm of working with Claude Code in a DOE project. Think of them as clocking in, doing the work, checking progress, clocking out, and reviewing your day.

---

## /stand-up

**What it does:** Starts your session and shows you where things stand.

**When to use it:** At the beginning of every session. It's always your first command.

**How it works:** `/stand-up` has two modes, and it picks the right one automatically:

- **Kick-off mode** (no session is currently running): Starts the session clock, reads `STATE.md` and `todo.md`, and shows you a status card. The card includes current feature progress, any blockers from last time, a plan for what to work on, and coaching tips if relevant.
- **Status mode** (a session is already running): Shows the same status card but doesn't reset anything. Read-only — safe to run whenever.

**What to expect:** A bordered status card printed to your terminal. It typically looks like:

```
┌─ Stand-up ──────────────────────────────────┐
│ Feature: Targeting Page v2                   │
│ Progress: ████████░░░░ 6/10 steps            │
│                                              │
│ Last session: Fixed search debounce bug      │
│ Blockers: None                               │
│ Plan: Build region filter dropdown           │
│ Tip: Approve the plan, then start building    │
└──────────────────────────────────────────────┘
```

If any features are in Awaiting Sign-off, the card includes a **SIGN-OFF** row showing the count of features and how many manual items still need your testing.

You don't need to memorise what you were doing last time. The stand-up reads `STATE.md` and reconstructs your context automatically.

---

## /crack-on

**What it does:** Resumes interrupted work. Refamiliarises Claude with the current task and immediately starts building — no discussion, no plan approval, no ceremony.

**When to use it:** When you've been interrupted and want to pick up where you left off. Context was lost (you had to `/clear`, came back after a break, started a new conversation) and you just want Claude to resume building without a full briefing. Not for fresh sessions where you want to review the plan — use `/stand-up` for that.

**How it works:**

1. Starts the session clock, reads `CLAUDE.md`, `STATE.md`, `todo.md`, and `learnings.md`.
2. Runs a DOE kit check.
3. Finds the next incomplete step from `todo.md`.
4. Validates that the step has a proper contract (testable criteria that define "done").
5. Shows a compact bordered card summarising the current state.
6. Immediately starts building — no sign-off needed.
7. Builds one step, runs `[auto]` verification, commits, then stops and shows what was done.

If an auto-check fails, Claude attempts to fix the issue (up to 3 tries) before asking for help.

**How it differs from `/stand-up`:** `/stand-up` shows a full briefing card with a plan, focus coaching, and pipeline status, then waits for your approval before doing anything. `/crack-on` shows a compact card and starts building immediately. Use `/stand-up` at the start of a fresh session; use `/crack-on` to resume after an interruption.

**What to expect:** A compact status card followed immediately by Claude building the next step. No waiting for approval. The output ends with verification results and a commit hash. For tasks with `[manual]` criteria, Claude notes what you need to check but doesn't stop and wait.

**Example usage:**

```
You: /crack-on
Claude: [compact card showing current feature, progress, next step]
        Picking up: "Add region filter dropdown"
        Contract: [auto] run: python3 execution/test_filters.py
                  [manual] Dropdown appears below search bar
        Building...
        [runs tests]
        ✓ All auto criteria pass
        Committed: a3f8c21 Add region filter dropdown
        Manual check needed: Verify dropdown appears below search bar
```

---

## /sitrep

**What it does:** Shows a quick mid-session progress snapshot.

**When to use it:** Whenever you want to see where things stand without changing anything. Completely read-only and safe.

**How it works:** Reads the current feature's todo.md steps and shows which are done, which is current, and what's coming next. Think of it as a progress bar for your feature.

**What to expect:** A compact summary like:

```
┌─ Sitrep ────────────────────────────────────┐
│ Feature: Targeting Page v2                   │
│ Progress: ██████████░░ 8/10 steps            │
│                                              │
│ Done: Search, filters, region cards, map     │
│ Current: Performance optimisation            │
│ Next: Final visual polish                    │
│ Session: 47 min, 3 commits                   │
└──────────────────────────────────────────────┘
```

If any features are in Awaiting Sign-off, the card includes a **SIGN-OFF** row showing the count and pending manual items — a reminder to test them.

No side effects. Run it as often as you like.

---

## /wrap

**What it does:** Closes your session properly. Records what happened so the project remembers it next time.

**When to use it:** Before ending any session. Always. This is how continuity works — if you skip the wrap, the next session's `/stand-up` won't know what you did.

**How it works:**

1. Updates `STATE.md` with the current position (what was done, what's next, any blockers).
2. Records any new learnings discovered during the session to `learnings.md`.
3. Calculates session stats: number of commits, lines changed, duration, and your streak (consecutive days with sessions).
4. Generates a formatted summary of the session. If any features moved to Awaiting Sign-off during the session, the wrap output includes an `awaitingSignOff` section with collapsible grouped cards listing the manual test items that need your attention.

**What to expect:** A session summary card:

```
┌─ Wrap ──────────────────────────────────────┐
│ Session 117                                  │
│ Duration: 1h 23m                             │
│ Commits: 5                                   │
│ Lines: +342 / -89                            │
│ Streak: 12 days                              │
│                                              │
│ Completed:                                   │
│  • Region filter dropdown                    │
│  • Performance optimisation                  │
│  • Fixed map rendering on Safari             │
│                                              │
│ Next session: Final visual polish            │
└──────────────────────────────────────────────┘
```

Think of `/wrap` as saving your game. The state is written to files that persist between sessions, so you (or Claude) can pick up exactly where you left off.

---

## /eod

**What it does:** Generates an end-of-day report that aggregates everything you did today across all sessions.

**When to use it:** At the end of your working day, after your final `/wrap`. This gives you the full picture of your day's output.

**How it works:** Reads the git log and session records for the current day, then assembles a visual summary. If you ran three sessions today, it combines all three into one report.

**What to expect:** A day-level summary showing:

- **Timeline** of sessions (when each started and ended)
- **Commit breakdown** (what was built, in what order)
- **Metrics** (total commits, total lines changed, total time)
- **Feature progress** (where features started and ended the day)

This is useful for personal tracking, for updating teammates, or just for the satisfaction of seeing a productive day laid out clearly.

---

## Typical Daily Flow

A normal day looks like this:

```
/stand-up          ← Start session, see where you left off
                   ← Approve the plan, then tell Claude what to build
                     (or just say "go" to start the next step)
/sitrep            ← Quick progress check
                   ← Keep building — describe what you want
/wrap              ← Close the session

(break, come back later — context lost)

/crack-on          ← Resume where you left off, no ceremony
/wrap              ← Close the session
/eod               ← See everything you did today
```

You don't have to follow this exactly — these are tools, not rules. But `/stand-up` at the start and `/wrap` at the end are the two that matter most for keeping the project's memory intact. `/crack-on` is there for when you need to resume after an interruption without repeating the full stand-up.
