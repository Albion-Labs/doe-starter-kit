# Your First Session

This guide walks you through a complete DOE session — from opening the terminal to wrapping up with all your progress saved. By the end, you'll understand the rhythm that every session follows.

## Starting your first session

Open your terminal and navigate to your project folder. You do this with the `cd` command, which stands for "change directory" — it's how you move between folders in the terminal.

```
cd ~/my-project
```

The `~` symbol means your home folder (like `/Users/yourname` on Mac or `C:\Users\yourname` on Windows). If your project is on your Desktop, you'd type `cd ~/Desktop/my-project`.

Now start Claude Code:

```
claude
```

You'll see Claude Code's prompt appear. Run the stand-up command:

```
/stand-up
```

## What the stand-up card shows

The stand-up card is a snapshot of where your project stands. Think of it as a morning briefing. It shows:

- **Feature** — what you're currently building (or "No active feature" if you're starting fresh)
- **Progress** — how far through the current work you are, shown as completed steps out of total steps
- **Plan** — the specific steps in the current task, with checkmarks next to anything that's already done
- **Blockers** — anything that's preventing progress (questions that need answering, decisions that need making)
- **Last session** — a brief summary of what happened last time, so you have context

On your very first session, most of this will be empty — and that's fine. The card becomes more useful as your project grows and sessions accumulate.

## Telling Claude what to build

You don't need to write code or use special syntax. Just type what you want in plain English. Be specific about what you want the end result to look like.

For example:

```
I want to build a recipe book app where I can add recipes with a title,
ingredients list, and method. I want to search recipes by name or ingredient,
and mark my favourites so I can find them quickly.
```

The more detail you give, the better the result. But you don't need to know technical details — Claude figures out the implementation. Focus on describing what you want as a user.

Other good starting prompts:

- "Build me a personal budget tracker where I can log expenses, categorise them, and see monthly totals"
- "I need a simple website for my photography portfolio with a gallery page and a contact form"
- "Create a tool that reads a CSV file of student grades and produces a summary report"

## What happens next

Once you describe what you want, Claude follows a structured process:

1. **Reads CLAUDE.md** — your project's instruction manual. This tells Claude the rules: where to put files, how to work, what not to do. You set these rules once and Claude follows them every session.

2. **Creates a plan** — Claude breaks your request into steps, each with clear success criteria. It writes this plan to `tasks/todo.md` so there's a record.

3. **Asks for approval** — Claude shows you the plan before building anything. This is your chance to adjust scope, reorder priorities, or ask questions. Nothing gets built until you say go.

4. **Builds step by step** — Claude works through the plan one step at a time. After each step, it verifies the work against the success criteria.

5. **Commits after each step** — every completed step gets saved as a Git commit. This is your safety net. If step 5 breaks something, you can go back to the state after step 4 without losing anything. Each commit is like a save point in a game — clearly labelled so you know exactly what it contains.

You can talk to Claude throughout this process. Ask questions, change direction, or tell it to skip something. It's a conversation, not a one-way instruction.

## Checking progress

At any point during the session, you can run:

```
/sitrep
```

This shows you a situation report — a quick view of where things stand. It includes:

- Which step you're on
- What's been completed
- What's coming next
- Whether there are any blockers or issues

This is particularly useful in longer sessions where you've been building for a while and want to get your bearings.

## Ending your session

When you're done for the day (or just need a break), run:

```
/wrap
```

The wrap command does several important things:

- **Saves your current position** — updates STATE.md so the next session knows exactly where you left off
- **Records session stats** — how long you worked, how many commits were made, what was accomplished
- **Summarises the session** — creates a brief record of what happened

This matters because Claude Code doesn't automatically remember previous sessions. Without the wrap-up, your next session would start cold — Claude wouldn't know what was built, what was tried, or what's left to do. The wrap command bridges that gap.

When you come back (whether that's in an hour, a day, or a month), your next `/stand-up` will show everything the wrap saved. Claude picks up right where you left off.

## What you just did

In this first session, you:

1. **Started up** with `/stand-up` to get oriented
2. **Described what you wanted** in plain English
3. **Reviewed Claude's plan** before any building started
4. **Watched Claude build** step by step, with each step committed as a save point
5. **Checked progress** with `/sitrep` whenever you needed a status update
6. **Wrapped up** with `/wrap` to save your position and session memory

This is the rhythm every session follows: stand-up, build, wrap. The more sessions you run, the richer your project's memory becomes — and the more effectively Claude can build on previous work.

Your project now has its first commits, a task tracker with progress recorded, and session memory that will carry forward. Next time you start a session, Claude will know everything that happened today.

Next step: [Configuration](configuration.md) — understanding the files that control how DOE works in your project.
