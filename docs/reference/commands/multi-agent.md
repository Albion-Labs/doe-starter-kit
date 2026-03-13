# Multi-Agent Commands

These commands let you run multiple Claude Code sessions in parallel, each working on a different task. This is an advanced workflow — most users won't need it initially, but it becomes valuable once you have several independent tasks to build.

---

## The Concept: Waves

Normally, Claude Code works on one task at a time in a single terminal. A **wave** runs multiple tasks simultaneously across multiple terminals.

Think of it like building a house. Normally, one builder works on one room at a time. In a wave, you have multiple builders working on different rooms at the same time — the electrician is wiring the kitchen while the plumber works on the bathroom. At the end, you walk through and check everything works together.

Here's how it works technically:

1. You identify tasks in `todo.md` that don't depend on each other (they don't edit the same files or need each other's output).
2. Each task gets assigned to its own terminal, working on an isolated copy of the code (a git worktree — a separate checkout of the same repository).
3. Each terminal builds its task independently: reading the contract, implementing, verifying, committing.
4. When all terminals finish, the results are merged back into the main branch one at a time.

The key constraint is **independence**. Two tasks that edit the same file can't run in parallel — they'd create merge conflicts. The system checks for this before launching.

---

## /agent-launch

**What it does:** Sets up a wave — scans your tasks, finds ones that can run in parallel, validates their contracts, and assigns each to a terminal.

**When to use it:** When you have 2 or more independent tasks ready to build. The time savings are significant: three 20-minute tasks take 20 minutes in a wave instead of 60 minutes sequentially.

**How it works:**

1. Reads `todo.md` and identifies incomplete tasks.
2. Checks which tasks are independent (no shared files, no output dependencies).
3. Validates that each task has a proper contract with testable criteria.
4. Creates a git worktree for each task (an isolated copy of the code).
5. Tells you which terminals to open and what command to run in each.

**What to expect:**

```
Wave scan complete. 3 tasks can run in parallel:

Terminal 1: "Add region filter dropdown"
  → cd /path/to/worktree-1
  → Run: /crack-on

Terminal 2: "Update data governance doc"
  → cd /path/to/worktree-2
  → Run: /crack-on

Terminal 3: "Add export button to cards"
  → cd /path/to/worktree-3
  → Run: /crack-on

Sequential (shares files with Task 1):
  - "Add filter reset button"

Open 3 terminals and run the commands above.
Use /agent-status to monitor progress.
```

You then open the specified number of terminals, navigate to each worktree, and start Claude Code in each one. Each session works independently.

**Important constraints during a wave:**

- Wave agents must not edit shared files (`todo.md`, `CLAUDE.md`, `learnings.md`, `STATE.md`). These are updated after merging.
- Each agent only works on its assigned task and only touches files in its `owns` list.
- Merging happens from the coordinator terminal (the one that ran `/agent-launch`) after all agents finish.

---

## /agent-status

**What it does:** Shows a dashboard of the current wave — which terminals are active, what each is working on, and how far along they are.

**When to use it:** During an active wave, from the coordinator terminal (the one that ran `/agent-launch`). Check in periodically to see how things are going.

**What to expect:**

```
┌─ Wave Status ───────────────────────────────┐
│ Wave started: 14:32                          │
│                                              │
│ Terminal 1: Region filter dropdown           │
│   Status: Building (step 2/3)                │
│   Last commit: a3f8c21 (2 min ago)           │
│                                              │
│ Terminal 2: Data governance doc              │
│   Status: Complete ✓                         │
│   Commits: 1                                 │
│                                              │
│ Terminal 3: Export button                    │
│   Status: Verifying                          │
│   Last commit: b7e2d44 (5 min ago)           │
│                                              │
│ Merge order: T2 → T1 → T3                   │
│ Ready to merge: T2                           │
└──────────────────────────────────────────────┘
```

The merge order is determined automatically to minimise conflicts. Tasks that touch fewer files merge first.

---

## When to Use Waves vs Sequential Work

**Use waves when:**
- You have 2+ tasks that don't share files
- Each task has a clear contract
- You want to save wall-clock time

**Use sequential work when:**
- Tasks depend on each other (Task B needs Task A's output)
- Tasks edit the same files
- You're exploring or prototyping (unclear scope)
- You only have one task to do

Waves add coordination overhead, so they're not worth it for a single quick task. They shine when you have a batch of independent work — like building several UI components, writing multiple execution scripts, or updating several documents.
