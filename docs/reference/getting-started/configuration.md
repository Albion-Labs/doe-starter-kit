# Configuration

DOE works because of a set of files that give Claude Code structure, memory, and rules. This guide explains each one — what it does, where it lives, and when you might want to change it.

You don't need to memorise all of this upfront. Come back to this page when you need to understand or modify a specific file.

## CLAUDE.md — the project's instruction manual

**Location:** `CLAUDE.md` in your project root

This is the most important file in DOE. Claude Code reads it automatically at the start of every session, and it controls how Claude behaves in your project. Think of it as a set of standing orders — rules that apply to every session without you having to repeat them.

### Key sections

**Operating Rules** — how Claude should work. These include things like:

- Plan before building (don't start coding without a plan)
- Ask, don't assume (if something is unclear, ask rather than guess)
- Commit after every completed task (every piece of work gets its own save point)
- Verify before delivering (test the output before saying it's done)

**Guardrails** — what Claude must not do. These are safety rails that prevent common disasters:

- Never overwrite existing files without permission
- Never store secrets (like API keys) in code
- Never force-push or delete branches without approval
- Never skip verification steps

**Directory Structure** — where different types of files go. DOE has specific folders for specific purposes (directives, execution scripts, tasks, etc.). This section tells Claude which folder to use for what.

**Progressive Disclosure** — when Claude should read which instructions. Instead of loading every instruction for every task, DOE tells Claude to load specific directives based on what you're doing. Working with data imports? It loads the data import instructions. Building a UI? It loads the UI patterns. This keeps context focused and relevant.

### What to customise

**Safe to change:**

- Directory structure — if your project needs different folders, update this section
- Progressive disclosure triggers — add triggers for your project's specific workflows
- Project-specific rules — add rules that make sense for your domain

**Leave alone (unless you know why you're changing it):**

- Operating rules — these are battle-tested across many projects. They prevent real problems.
- Guardrails — these exist because someone learned the hard way. Weakening them invites the same mistakes.

## STATE.md — session memory

**Location:** `STATE.md` in your project root

STATE.md is Claude's short-term memory. It persists between sessions and gets updated automatically when you run `/wrap`. When you start a new session and run `/stand-up`, Claude reads this file to understand where things stand.

It typically contains:

- **Current position** — what feature is being built, which step you're on
- **Blockers** — anything preventing progress (decisions needed, questions unanswered)
- **Last session summary** — what happened in the previous session

You generally don't need to edit this file by hand — the `/wrap` and `/stand-up` commands manage it. But you can read it any time to see what Claude currently "knows" about the project state.

## tasks/todo.md — the task tracker

**Location:** `tasks/todo.md`

This is where features are broken into concrete steps with success criteria. It's the single source of truth for what's been done, what's in progress, and what's coming next.

### Sections

**Current** — the feature actively being built, with its steps listed. Each step has:

- A checkbox (`[ ]` not started, `[x]` completed)
- A description of what the step does
- A "Contract" block with testable criteria — specific conditions that must be true for the step to count as done

**Queue** — features that are planned but not yet started, in priority order.

**Done** — completed features, kept as a record of what was built and when.

### Example

```markdown
## Current

### Recipe Book — Core Features

- [x] Step 1: Set up project structure and data model
  Contract: `file: src/models/recipe.py exists`, `file: src/models/recipe.py contains class Recipe`
- [ ] Step 2: Build add-recipe form
  Contract: `html: index.html has form#add-recipe`, `run: python3 tests/test_add.py`
- [ ] Step 3: Implement search
  Contract: `run: python3 tests/test_search.py`

## Queue

- Favourite recipes feature
- Export to PDF

## Done

- Project initialisation (v0.1.0) — 2025-01-15
```

Claude updates this file as it works — checking off steps as they're completed, moving features from Queue to Current when you start them, and from Current to Done when they're finished.

## learnings.md — long-term memory

**Location:** `learnings.md` in your project root

This is the project's institutional memory. Every time something fails, produces an unexpected result, or requires a non-obvious solution, Claude logs it here. The next time a similar situation arises, Claude checks learnings.md first — so it doesn't repeat the same mistake.

Entries range from one-liners to structured post-mortems:

```markdown
- macOS sed requires '' as backup argument, unlike Linux. [retro: setup-script]

- **Search broke after adding pagination**
  What happened: Search returned empty results after step 4
  Root cause: Pagination reset the search index on each page load
  Fix: Moved index build to app startup, not page render
  Prevention: Added test for search-after-paginate scenario
```

You don't need to write these yourself — Claude adds them automatically when it discovers something worth remembering. But you can read them to understand the project's history of hard-won knowledge.

## ROADMAP.md — the big picture

**Location:** `ROADMAP.md` in your project root

While todo.md tracks individual steps, ROADMAP.md tracks features at the product level. It gives you a high-level view of where the project is going.

Features flow through stages:

- **Ideas** — things that might be worth building someday
- **Must Plan** — important ideas that need proper scoping before work starts
- **Up Next** — scoped and ready to build, waiting for the current work to finish
- **Current** — actively being built
- **Complete** — shipped and done

This is the file to look at when you want to answer "what's the plan for this project?" rather than "what's the next step?"

## directives/ — detailed instructions

**Location:** `directives/` folder

Directives are Standard Operating Procedures (SOPs) for specific tasks. They contain detailed, step-by-step instructions that Claude follows when performing particular types of work.

For example, there might be a directive for:

- Importing data from an API
- Running an audit of the codebase
- Syncing changes to a shared template
- Handling documentation updates

You don't need to read these to use DOE. Claude loads the right directive automatically based on what you're doing (this is the "Progressive Disclosure" system in CLAUDE.md). But if you want to understand or customise how Claude handles a specific workflow, the relevant directive is the place to look.

## execution/ — deterministic scripts

**Location:** `execution/` folder

This is where Python scripts live that do the actual mechanical work — data imports, file transformations, report generation, audits, and builds. The key principle: these scripts run the same way every time. There's no AI randomness involved.

This is the "Execution" in DOE. When Claude needs to import data from an API or generate a report, it doesn't do it inline (which could produce inconsistent results). Instead, it runs a script from this folder — a script that's been written, tested, and produces predictable output.

If you're building a project that imports data, transforms files, or generates outputs, your execution scripts will accumulate here. Each one is a reliable, repeatable tool that Claude (and you) can run at any time.

## .claude/ — Claude's workspace

**Location:** `.claude/` folder

This folder contains the internal machinery that makes DOE work:

- **hooks/** — automatic checks that run at specific moments (before commits, after tool use). These are guardrails that catch problems without you having to remember to check. For example, a hook might prevent you from accidentally committing an API key.
- **plans/** — feature designs written during the planning phase. When Claude breaks a big feature into steps, the detailed thinking goes here. Plans are reference documents — the actionable steps go in todo.md.
- **settings.json** — Claude Code configuration (allowed/denied tools, permissions).
- **commands/** — the slash commands (like `/stand-up` and `/wrap`) that you use during sessions. These are small scripts that Claude Code recognises and runs.
- **stats/** — session statistics (duration, commits, tokens used). The `/wrap` command writes here.

You rarely need to edit files in `.claude/` directly. The setup script configures everything, and the slash commands handle the day-to-day. But knowing what's in here helps if you ever want to customise a hook or understand why something triggered automatically.

## How these files work together

Here's how a typical session touches these files:

1. You run `/stand-up` — Claude reads **STATE.md** (where did we leave off?) and **tasks/todo.md** (what's the plan?)
2. You describe what to build — Claude reads **CLAUDE.md** (how should I work?) and checks **learnings.md** (any past mistakes to avoid?)
3. Claude plans the work — writes to **tasks/todo.md** and possibly **.claude/plans/**
4. Claude builds — runs scripts from **execution/**, follows rules from **directives/**, commits after each step
5. You run `/wrap` — Claude updates **STATE.md** with the current position and session summary

Each file has a specific job. Together, they give your project structure, memory, and discipline that persists across sessions — no matter how many days or weeks pass between them.
