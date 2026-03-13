# Starting a New Project

This guide walks you through creating a new project with DOE from absolute zero. By the end, you'll have a working project with version control, session tracking, and an AI collaborator ready to build.

---

## 1. Create a project folder

Open your terminal and create a folder for your project:

```bash
mkdir my-project
```

`mkdir` stands for "make directory" — a directory is just a folder. This is where all your project files will live. Pick a short, descriptive name with no spaces (use hyphens instead).

## 2. Initialise git

```bash
cd my-project
git init
```

Git is a version control system — think of it as an unlimited undo system for your entire project. Every time you save a "commit," git takes a snapshot of all your files. You can go back to any snapshot at any time. `git init` creates this save system inside your project folder.

## 3. Copy DOE starter kit files

Copy the DOE starter kit files into your project folder. The key files are:

- **`CLAUDE.md`** — Instructions that tell Claude how to work on your project. This is the single most important file — it defines your project's rules, directory structure, and working patterns.
- **`.claude/`** — Hooks and commands that automate common tasks (stand-ups, wrap-ups, audits).
- **`.githooks/`** — Git hooks that enforce quality checks automatically when you commit.
- **`tasks/todo.md`** — Where your task queue lives. Claude tracks what's planned, what's in progress, and what's done.
- **`ROADMAP.md`** — The big picture: features planned, in progress, and complete.
- **`STATE.md`** — Session memory. Where you left off, what's blocked, what decisions were made recently.
- **`learnings.md`** — Institutional memory. Things that went wrong and how to avoid them next time.

See [Configuration](../configuration.md) for detailed explanations of each file and how to customise them.

## 4. Open Claude Code

Navigate into your project folder and launch Claude Code:

```bash
cd my-project
claude
```

Claude Code reads your `CLAUDE.md` file automatically when it starts, so it already knows your project's rules and structure.

## 5. Run setup

If you haven't already, run the starter kit setup script:

```bash
bash setup.sh
```

This configures git hooks, creates the directory structure, and sets up the command shortcuts. You only need to do this once per project.

## 6. First stand-up

Run the stand-up command to initialise your first session:

```
/stand-up
```

Since this is a brand-new project, the stand-up will be brief — there's no history yet. But from now on, every session starts this way. It reads STATE.md, checks todo.md, and gives you a kick-off card summarising where things are.

## 7. Tell Claude what you're building

Describe your idea in plain English. You don't need to know how to code — just explain what you want the end result to be. For example:

> "I'm building a website that tracks local council spending. It should show a table of expenses by department, with a chart showing trends over time. The data comes from a CSV file I'll download monthly."

Be specific about what you want, who it's for, and what the output should look like. The more concrete you are, the better the plan will be.

## 8. Claude creates the plan

Based on your description, Claude will:

- Write a plan to `.claude/plans/` with detailed steps, technical approach, and the order of work
- Add steps to `tasks/todo.md` under the Queue section, each with a contract (testable criteria that define "done")
- Add the feature to `ROADMAP.md` so you can track it at a glance

Review the plan. If something doesn't look right, say so — Claude will adjust. This is your chance to steer before any code gets written.

## 9. Start building

You have two options:

- **Describe what you want** — Tell Claude what to build in your own words, or say "go" to start the next planned step
- **`/crack-on`** — For resuming after an interruption (context loss, `/clear`, came back after a break). Claude refamiliarises itself and starts building immediately without ceremony

Either way, Claude builds in small steps. Each step gets verified against its contract and committed (saved) to git. If something goes wrong, you can always go back.

## 10. Wrap up

When you're done for now:

```
/wrap
```

This saves your session state: what you accomplished, where you stopped, and any blockers. The next time you run `/stand-up`, all of this context comes back automatically.

---

## What just happened

You've set up a complete development environment in about ten minutes:

- **Git** is tracking every change, so nothing is ever lost
- **CLAUDE.md** tells Claude your project's rules, so it works consistently
- **todo.md** and **ROADMAP.md** track your plan, so you always know what's next
- **STATE.md** remembers where you left off between sessions
- **Stand-up and wrap** bookend every session, so context carries over automatically

From here, every session follows the same rhythm: stand-up, build, wrap. The system handles the rest — version tracking, state management, quality checks, and institutional memory all happen in the background.
