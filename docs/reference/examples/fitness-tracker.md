# Example: Fitness Tracker

**Starting point:** "I have a rough idea"

This walkthrough follows someone building a workout tracker with charts. They've thought about what they want and have bullet points — but no detailed spec. It shows how DOE handles multi-session projects where each session builds on the last.

---

## The idea

> "Track daily workouts — type, duration, notes. Show weekly and monthly charts so I can see trends. Set goals and track streaks."

This is more concrete than a vague "I want a fitness app." There are clear nouns (workouts, charts, goals, streaks) and clear actions (track, show, set). But it's still a list of wishes, not a buildable plan.

## How you'd start

You give Claude the bullet points directly. Since the idea is already reasonably clear, you don't need `/scope` — Claude has enough to build a plan.

Claude creates a plan file in `.claude/plans/fitness-tracker.md` with roughly six steps:

1. Data model — workout structure (type, duration, date, notes), goal structure (target, timeframe)
2. Storage layer — save and retrieve workouts, stored locally
3. Workout input form — log a new workout with type, duration, and optional notes
4. Workout history — list of past workouts, sorted by date
5. Charts and progress — weekly/monthly bar charts showing duration over time
6. Goals and streaks — set a weekly goal, track current streak of consecutive days

Notice how the plan separates the data layer (steps 1-2) from the user-facing pages (steps 3-6). This is a core DOE principle: execution scripts handle data storage and retrieval, page scripts handle what the user sees. If you later decide to change how workouts are stored (say, moving from local files to a database), only the storage layer changes — the charts and forms stay untouched.

## What a session looks like

This project spans three sessions. Here's what each one looks like.

### Session 1: Foundation

You run `/stand-up`. Since it's the first session, there's no history — just the plan. Claude starts on steps 1 and 2: defining the workout data model and building the storage logic.

The contract for step 2 might look like:

```
2. [ ] Storage layer
   Contract:
   - [ ] [auto] Can save a workout. Verify: run: node tests/storage.test.js
   - [ ] [auto] Can retrieve workouts by date range. Verify: run: node tests/query.test.js
   - [ ] [auto] Handles empty state gracefully. Verify: run: node tests/empty-state.test.js
```

Claude builds the storage layer and runs the tests. The date range query test fails — it's returning workouts from outside the requested range because of an off-by-one error in the date comparison. Claude reads the test output, identifies that the comparison is using `<` instead of `<=` for the end date, fixes it, and re-runs. All three tests pass.

Both steps get committed separately — one commit for the data model, one for the storage layer. You run `/wrap`. Claude logs that the data foundation is complete, notes that step 3 is next, and records one decision: "Workouts stored as JSON in localStorage, keyed by date."

### Session 2: Input and history

You run `/stand-up`. Claude shows a kick-off card:

> Session 1 completed: data model and storage layer. All contracts passed. Next: workout input form (step 3).

Claude builds the input form and the workout history list. During testing, it discovers that workout dates are stored in UTC but displayed in local time — so a workout logged at 11pm on Monday shows up under Tuesday. Claude fixes the date handling, logs the issue to `learnings.md`:

> Workout dates: store in ISO 8601 with timezone offset, not bare UTC. Displaying UTC dates in local context causes off-by-one day errors.

Both steps pass their contracts. You run `/wrap`.

### Session 3: Charts and goals

You run `/stand-up`. This time, the kick-off card shows something extra:

> Session 2 completed: input form and history. Note from learnings: date timezone handling was fixed — dates now stored with timezone offset. Next: charts (step 5).

Claude knows about the date bug from Session 2 because it was logged. When it builds the chart logic, it uses the timezone-aware dates correctly from the start — no repeat of the same mistake.

The chart step has a contract like:

```
5. [ ] Charts and progress
   Contract:
   - [ ] [auto] Chart renders with test data. Verify: run: node tests/chart-render.test.js
   - [ ] [auto] Weekly and monthly views both work. Verify: run: node tests/chart-views.test.js
   - [ ] [manual] Charts are readable — bars are labelled, axes make sense
```

Claude builds the charts, runs the automated checks, then moves on to goals and streaks. At the end, it presents the manual test checklist for the whole feature: check the form layout, check the chart readability, check the streak counter display. You test, everything looks good, and the feature is complete.

## What DOE gives you

This walkthrough shows four DOE concepts across multiple sessions:

**Planning separated data from UI.** The storage layer and the chart display are independent. When the date bug was found, Claude fixed it in one place (the storage layer) without rewriting the input form or the history list. This separation is what DOE means by "deterministic code handles execution" — the storage script works the same way every time, regardless of what page is calling it.

**Contracts verified the chart renders with real data.** The chart test didn't just check that chart code exists — it verified that the chart actually renders when given workout data. This catches the common AI mistake of writing a chart function that looks correct but crashes with real inputs.

**`/wrap` captured the date bug, and future sessions used that knowledge.** Session 2 discovered a problem and logged it. Session 3 automatically avoided the same problem because Claude read `learnings.md` at stand-up. This is project memory in action — the project gets smarter over time.

**Each session started exactly where the last one left off.** No re-explaining what you're building. No "actually, we already did that." The stand-up reads STATE.md and todo.md, so Claude arrives already briefed. Three sessions felt like one continuous conversation.

---

This is DOE with a medium-sized project: multiple sessions, each building on the last, with memory that carries bugs, decisions, and context forward automatically. The fitness tracker isn't complex, but the multi-session pattern is the same one you'd use for a much larger build.
