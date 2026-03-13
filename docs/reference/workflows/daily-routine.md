# Your Daily Routine

DOE works best with a consistent rhythm. This page maps out what a typical day looks like — from your first session to your end-of-day review.

---

## First session of the day

1. **Open your terminal and navigate to your project:**
   ```bash
   cd my-project
   claude
   ```

2. **Run stand-up:**
   ```
   /stand-up
   ```
   Claude reads your STATE.md, checks todo.md, and presents a kick-off card. This card tells you:
   - Where you left off last session
   - What's planned for today
   - Any blockers or decisions that need attention

3. **Review the kick-off card.** Read it carefully — it often catches things you'd forget. If the plan looks right, approve it. If you want to change priorities or adjust the approach, say so now.

4. **Build.** Tell Claude what you want to work on in plain English, or just say "go" / "let's build step 2" to start on the next planned step. (If you've been interrupted mid-session and need to resume — context loss, `/clear`, came back after a break — run `/crack-on` instead, which skips the briefing and picks up where you left off immediately.)

5. **Wrap up when you're done:**
   ```
   /wrap
   ```
   This saves everything: what you accomplished, what's in progress, and where to pick up next time.

---

## Second and third sessions

The rhythm is always the same:

```
/stand-up → work → /wrap
```

Each session picks up exactly where the last one left off. The stand-up card reflects the latest state, including anything that changed in previous sessions that day.

**One task per session** is the guiding principle. If you finish a task and want to start something unrelated, run `/wrap` and then `/clear` before starting the new topic. This keeps each session focused and prevents context from getting muddled.

If you want a quick status check mid-session without the full stand-up ceremony, run:

```
/sitrep
```

This gives you a snapshot of where things are — current task, recent commits, any issues — without resetting the session.

---

## End of day

When you're done for the day, run:

```
/eod
```

This gives you a summary of everything that happened across all your sessions today:
- What shipped (completed tasks, commits made)
- What's in progress (started but not finished)
- What's blocked (waiting on something)

This is your "what I did today" summary. It's useful for your own records, and if you're working with others, you can share it directly.

---

## Weekly check-in

Once a week (or whenever you want the big picture), run:

```
/hq
```

This shows you the state of your project at a high level — across all features, not just today's work.

Use this time to:

- **Review ROADMAP.md** — Are features moving from "Up Next" to "In Progress" to "Complete"? Is anything stuck?
- **Check learnings.md** — Has anything new been learned this week? Are there patterns you should be aware of?
- **Reassess priorities** — Does the plan still make sense, or has something changed?

---

## Key habits

These are the habits that make the biggest difference:

**Always `/wrap` before ending a session.** This is the single most important habit. Without it, STATE.md won't reflect where you actually are, and the next stand-up will be working from stale information. If you forget, your code is safe (git has it), but you'll lose session context.

**One task per session.** Context pollution is real. When a conversation accumulates unrelated topics, Claude's responses get less focused. Keep each session about one thing.

**If something goes wrong, Claude records it automatically.** DOE has a self-annealing system: when something fails, Claude diagnoses the root cause, fixes it, and logs the learning so it doesn't happen again. You don't need to manage this — just know it's happening in the background.

**Check the stand-up card.** Don't skip past it. It often surfaces things you'd miss — a stale blocker, a forgotten decision, a task that's been sitting in the queue too long. Two minutes of reading saves twenty minutes of confusion.

**Trust the rhythm.** Stand-up, build, wrap. It feels like overhead the first few times, but it pays for itself quickly. The system gets smarter about your project with every session, and that only works if it has clean state to work from.
