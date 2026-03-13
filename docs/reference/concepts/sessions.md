# Sessions

## What a Session Is

A session is one conversation with Claude Code. It starts when you open Claude Code (or begin a new conversation) and ends when you close it or run `/wrap`. Everything in between — every question you ask, every file Claude edits, every command it runs — is one session.

Think of it like a meeting. You arrive, do focused work, and before you leave you write up notes so the next meeting can pick up where this one left off.

## The Session Lifecycle

Every session has four phases, though not all of them are required every time.

### 1. Start — Orient and Plan

**Commands:** `/stand-up` or `/crack-on`

When you begin a session, Claude reads your project's current state. It checks:

- **STATE.md** — What happened in the last session? Are there any blockers? What was the plan?
- **todo.md** — What tasks are in progress? What's next on the list?
- **learnings.md** — Have any recent discoveries or gotchas been logged?

Then it shows you where things stand and proposes a plan for this session. You might agree, adjust the plan, or say "actually, I need to do something different today."

`/stand-up` gives you the full briefing and waits for your approval before doing anything. `/crack-on` is for resuming after an interruption — when context was lost (you had to `/clear`, came back after a break, started a new conversation) and you want Claude to refamiliarise itself with the current task and immediately start building without ceremony or sign-off.

### 2. Work — Build and Review

This is the bulk of the session. You tell Claude what to do, it builds, you review. The cycle repeats as many times as needed.

After each completed piece of work, Claude commits the changes to git. This is like auto-saving a game after each level — if something goes wrong later, you can roll back to any previous save point without losing everything.

Each commit is atomic: one task, one commit, one clear message describing what changed. This makes the project history easy to read and easy to undo if needed.

### 3. Check — Mid-Session Status

**Command:** `/sitrep`

This is optional but useful during longer sessions. `/sitrep` gives you a snapshot: what's been done so far, what's still in progress, and what's coming next. It's a way to step back and make sure the session is still on track.

You might use this after Claude has completed a few tasks and you want to confirm everything looks right before moving on.

### 4. End — Save and Close

**Command:** `/wrap`

This is the most important phase. When you run `/wrap`, Claude:

- **Updates STATE.md** — Records what happened this session, where the project stands now, and any decisions that were made. This is the bridge to your next session.
- **Records learnings** — If anything failed, was discovered, or worked in a surprising way, it gets logged to `learnings.md` so the project remembers.
- **Calculates session stats** — How many tasks completed, how many commits, how long the session ran.

After `/wrap`, the project has everything it needs for Claude to pick up where you left off next time — even if "next time" is next week.

## Why Sessions Matter

Without session structure, you lose context. You come back tomorrow, open Claude Code, and it has no idea what happened yesterday. You end up re-explaining your project setup, reminding Claude about decisions you already made, and redoing work that was already done.

With sessions, STATE.md bridges the gap. Claude reads it at the start of every session and immediately knows: what the project does, what was done recently, what's in progress, and what's blocked. The conversation itself is gone — but the important information survives.

## What Persists Between Sessions

**Survives (on disk):**
- **STATE.md** — Short-term memory. What happened recently, current blockers, next steps.
- **learnings.md** — Long-term memory. Patterns, gotchas, things that went wrong and how they were fixed.
- **todo.md** — The task list. What's done, what's in progress, what's planned.
- **All committed code** — Every file Claude created or edited, saved in git history.
- **Directives and execution scripts** — The project's instructions and tools.

**Does not survive:**
- **The conversation itself** — Once you close Claude Code, the back-and-forth dialogue is gone. That's why `/wrap` captures the important parts into files before you close.
- **Uncommitted changes** — If Claude edited a file but didn't commit it, and you close the session, those changes are still in the files but not in git history. Always wrap before ending.

## Multiple Sessions in a Day

You might have three or four sessions in a single day, each focused on a different task. That's normal and encouraged — short, focused sessions work better than marathon ones.

At the end of the day, `/eod` (end of day) gives you a summary across all of that day's sessions: what was accomplished, what's still in progress, what's planned for tomorrow.

For the bigger picture — across days and across projects — `/hq` shows a high-level overview of where everything stands.

## Tips

- **Keep sessions focused.** One task per session works best. If you finish a task and want to start something unrelated, consider running `/wrap` and starting fresh. Mixing unrelated tasks in one session muddies the context.
- **Always wrap before ending.** It takes 30 seconds and saves you 10 minutes of re-orientation next time.
- **Use `/clear` if things get confused.** Sometimes a long session accumulates too much context and Claude starts making odd decisions. `/clear` resets the conversation but keeps all your files and project state intact. It's like closing and reopening a document — you don't lose anything, you just get a clean view.
- **Don't worry about session length.** Some sessions are 10 minutes (quick fix), some are two hours (building a feature). The structure works the same either way.
