End-of-day report aggregating all sessions into a single visual HTML page. Answers "what did I do today?" — or for any past date.

This is a read-only summary command. Do NOT modify any files or start/stop sessions.

## Arguments

Parse the user's arguments (if any) after `/eod`:
- No arguments → report for today
- A date argument (e.g. `/eod 2026-03-18`, `/eod 18/03/26`, `/eod yesterday`) → report for that date. Parse flexibly: YYYY-MM-DD, DD/MM/YY, or relative words (yesterday, last Monday, etc.). Convert to YYYY-MM-DD for filtering.

## Step 1: Data Gathering

Collect all of the following before building the report. Use `TARGET_DATE` (today or the date argument) for all filtering:

1. **Sessions for the target date** — First try local: read `.claude/stats.json` and filter `recentSessions` where `date` matches TARGET_DATE. If TARGET_DATE is not today and local data has no matching sessions, pull from the Gist via `gist_sync`:
```bash
python3 ~/.claude/scripts/gist_sync.py --read <project-slug>
```
Parse the returned JSON and filter `.sessions[]` where `.date` matches TARGET_DATE. Use the `.wrapJson` from each matching session entry for metrics. If `gist_sync.py` is not found or fails, fall back to local data only with a note: "No session data found for {date}. Historical data requires Gist sync (/wrap pushes sessions to the Gist)."

For today only: check if `.tmp/.session-start` exists — if it does, there is one active unwrapped session (compute its duration from the timestamp to now).

2. **Today's commits** — Run `git log --oneline --since="$(date +%Y-%m-%d)T00:00:00"` to get all commits from today. Also run `git diff --shortstat` for the range to get total lines/files.

3. **Steps completed today** — Read `tasks/todo.md` and count `[x]` items with timestamps containing today's date (DD/MM/YY format).

4. **Features completed today** — Check `tasks/todo.md` ## Done for features with completion timestamps matching today.

5. **Current position** — Read `STATE.md` for active feature, blockers, current version.

6. **Checks** — Run `python3 execution/audit_claims.py --hook --json` and parse the results. Check DOE kit sync status.

7. **Streak** — From stats.json `streak.current`.

## Step 2: Compose the EOD JSON

Build a JSON object with this schema:

```json
{
  "projectName": "PROJECT_DIR_NAME_UPPERCASED",
  "date": "DD/MM/YY",
  "streak": N,
  "summary": "One plain English sentence addressing the user: 'Today you did X and achieved Y.'",
  "breakdowns": [
    {"heading": "Area of work", "bullets": ["What was done", "Another thing done"]},
    {"heading": "Another area", "bullets": ["What changed"]}
  ],
  "vibe": {"emoji": "EMOJI", "text": "Day vibe description"},
  "metrics": {
    "sessions": N,
    "totalDuration": "Xh Ym",
    "avgSession": "Xh Ym",
    "commits": N,
    "linesAdded": N,
    "linesRemoved": N,
    "filesTouched": N,
    "stepsCompleted": N,
    "featuresCompleted": N,
    "agentsSpawned": N
  },
  "sessionTimeline": [
    {"number": 76, "start": "HH:MM", "duration": "Xh Ym", "summary": "What this session did", "pct": N}
  ],
  "commitBreakdown": [
    {"name": "Feature/task name", "count": N, "pct": N}
  ],
  "decisions": [
    {"title": "Short title", "problem": "What the problem was", "solution": "What was decided"}
  ],
  "learnings": [
    {"title": "Short title", "problem": "What was discovered", "solution": "What changed"}
  ],
  "checks": {
    "audit": {"pass": N, "warn": N, "fail": N, "details": ["detail if warn/fail"]},
    "doeKit": {"version": "vX.Y.Z", "synced": true|false}
  },
  "nextUp": "What to do next -- pull from todo.md"
}
```

### Field guidance:

**summary**: One plain English sentence addressing the user -- "Today you did X and achieved Y." No jargon.

**breakdowns**: Group the day's work into 2-4 subheadings, each with 1-3 bullet points. Keep bullets top-level and plain English -- what was achieved, not implementation details. Think "Built the EOD report" not "Created eod_html.py with render_summary function".

**vibe**: Pick the best match for the day:
- All planning, no code → `{"emoji": "📐", "text": "Architect mode"}`
- Lots of code shipped (500+ lines) → `{"emoji": "🏭", "text": "Factory floor"}`
- Multiple features completed → `{"emoji": "🏃", "text": "Sprint day"}`
- Mostly config/docs changes → `{"emoji": "🧹", "text": "Housekeeping day"}`
- Mixed planning + building → `{"emoji": "🔨", "text": "Builder's day"}`
- Single focused feature all day → `{"emoji": "🎯", "text": "Deep work"}`
- Lots of failures + fixes → `{"emoji": "⚔️", "text": "Trench warfare"}`

**sessionTimeline**: One entry per session today. `start` is the session start time (from stats or git log). `pct` is what percentage of total day time this session represents. For sessions without a summary in stats.json, derive one from their commit messages.

**commitBreakdown**: Group all today's commits by feature/task (match against todo.md feature names). Each entry shows the feature name, commit count, and what percentage of today's total commits it represents. Ungrouped commits go in "Housekeeping" or "Other".

**decisions**: Aggregate from today's sessions. Pull from learnings.md commits today, or from what you know happened. Use Problem/Solution format.

**learnings**: Same — aggregate from today. Use Discovery/Change format.

**checks**: Run the audit and capture results. Same format as /wrap.

## Step 3: Generate and open

Run:
```bash
python3 ~/.claude/scripts/eod_html.py --json '<the JSON string>' --output .tmp/eod.html
```

Then open in the browser:
```bash
open .tmp/eod.html
```

Print a one-line summary to the terminal: `EOD report opened in browser. [N] sessions, [X] commits, [duration] total.`

## Important Rules

- This is READ-ONLY. Do not modify any files. Do not wrap the current session. Do not update stats.json.
- Pull all numbers from git commands and stats.json. Never estimate.
- The `summary` is one plain English sentence addressing the user. The `breakdowns` array groups work into subheadings with bullets.
- Decisions and learnings use Problem/Solution and Discovery/Change format — same as /wrap.
- Works correctly with 1 session or 10 sessions in a day.
- If no sessions exist for the target date and no git data is available, show: "No session data for {date}. Run /wrap during sessions to populate the Gist for retroactive reports."
- For today: if no sessions exist, still show the report with data from git log.
