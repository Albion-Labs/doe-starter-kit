# tasks/todo.md — The Task Tracker

This is where work gets tracked. Every feature you build is broken into numbered steps, and every step has a contract that defines exactly what "done" means. Claude checks this file at the start of every session to know what to work on next.

Think of it as a very precise to-do list where each item comes with built-in acceptance criteria.

## Structure

The file has three sections:

### Current

The one feature actively being built. Only one feature lives here at a time. It has a heading with the feature name, a type tag (`[APP]` for user-facing changes, `[INFRA]` for tooling), and a version range. Below that are numbered steps.

### Queue

Approved features waiting their turn. These have descriptions and often link to a plan file, but they don't move to Current until the active feature is done.

### Awaiting Sign-off

Features that are code-complete — all steps are built, all `[auto]` criteria pass — but still have unchecked `[manual]` items. Features land here when Claude finishes the last step and all automated checks pass, but manual items (visual layout, interaction quality, print rendering) still need you to test and confirm. Once you verify all manual items, the feature moves to Done.

### Done

Completed features, kept for audit and reference. Only the last few are kept here — older ones move to an archive file.

## Step Format

Each step is a numbered item with a checkbox, a description, and a version tag:

```markdown
1. [x] Settings panel — add party and role config → v0.5.0 *(completed 14:30 10/03/26)*
2. [ ] Data layer — scoring algorithm for all records → v0.5.1
3. [ ] UI — table with filters and sort → v0.5.2
```

- `[x]` means done, `[ ]` means pending
- The version tag (`→ v0.5.1`) tells Claude what version number to use when committing
- Completed steps get a timestamp

## Contracts

Every step has a Contract block — a list of criteria that must pass before the step can be marked done. This is what makes DOE different from a regular to-do list: you define "done" before you start building.

There are two types of criteria:

### [auto] — Machine-Verified

These are checked automatically by running a command or inspecting a file. Each one uses a `Verify:` pattern that Claude can execute:

```markdown
Contract:
- [ ] [auto] Scoring function exists. Verify: file: src/js/scoring.js contains computeScore
- [ ] [auto] Build succeeds. Verify: run: python3 execution/build.py
- [ ] [auto] Config page exists. Verify: file: src/pages/config.html exists
- [ ] [auto] Has search input. Verify: html: src/pages/search.html has input.search-box
```

The four `Verify:` pattern types are:

| Pattern | What it does | Example |
|---------|-------------|---------|
| `run: <command>` | Runs a shell command, passes if exit code is 0 | `run: python3 execution/build.py` |
| `file: <path> exists` | Checks that a file exists | `file: src/pages/dashboard.html exists` |
| `file: <path> contains <text>` | Checks that a file contains a specific string | `file: src/js/app.js contains initDashboard` |
| `html: <path> has <selector>` | Parses HTML and checks for a CSS selector | `html: index.html has .nav-menu` |

### [manual] — Human-Verified

These are things only a person can check — visual layout, interaction feel, whether something "looks right." They don't have a `Verify:` pattern because they need human eyes:

```markdown
- [ ] [manual] Dashboard cards are evenly spaced and responsive at 375px, 768px,
  and 1440px widths. Sort pills change the card order instantly.
```

Manual criteria are batched and presented to you at the end of a feature (not after every step), so you can test everything at once rather than being interrupted constantly.

## A Realistic Example

Here is what a feature looks like in todo.md with three steps — one done, one in progress, one pending:

```markdown
## Current

### Recipe Search — Filter and Find Recipes [APP] (v0.5.x)

Add search and filtering to the recipe list page. Plan: `.claude/plans/recipe-search.md`.

1. [x] Data layer — index recipes by ingredient and category → v0.5.0 *(completed 10:15 08/03/26)*
   Contract:
   - [x] [auto] Index function exists. Verify: file: src/js/recipes.js contains buildIndex
   - [x] [auto] Categories extracted. Verify: file: src/js/recipes.js contains categoryMap
   - [x] [auto] Build succeeds. Verify: run: python3 execution/build.py

2. [ ] Search UI — search bar, filter pills, results table → v0.5.1
   Contract:
   - [ ] [auto] Search input rendered. Verify: file: src/js/recipes.js contains recipe-search
   - [ ] [auto] Filter pills for categories. Verify: file: src/js/recipes.js contains filter-pill
   - [ ] [auto] Results update on input. Verify: file: src/js/recipes.js contains filterResults
   - [ ] [auto] Build succeeds. Verify: run: python3 execution/build.py
   - [ ] [manual] Search returns relevant results. Filter pills narrow the list.
     Clearing search restores full list. Responsive on mobile.

3. [ ] Housekeeping — changelog, version bump, roadmap → v0.5.2
   Contract:
   - [ ] [auto] Version bumped. Verify: file: src/pages/nav.html contains v0.5
   - [ ] [auto] Changelog entry. Verify: file: src/pages/changelog.html contains Recipe Search
   - [ ] [auto] Build succeeds. Verify: run: python3 execution/build.py

4. [ ] Retro
   Contract:
   - [ ] [auto] Retro level recorded. Verify: file: tasks/todo.md contains [quick: or [full:
```

## How Claude Uses It

1. At session start, Claude reads `## Current` to find the active feature and its next unchecked step.
2. Before starting work, Claude validates the step's contract — confirming the `Verify:` patterns are executable.
3. After completing the work, Claude runs each `[auto]` criterion and marks it `[x]` as it passes.
4. When all `[auto]` criteria pass, Claude marks the step `[x]`, commits, and moves to the next step.
5. When the last step's `[auto]` criteria pass, the feature moves to `## Awaiting Sign-off` immediately. `[manual]` criteria are presented for you to test.
6. Once you verify all `[manual]` items, the feature moves to `## Done`.

## When You'd Edit It

- **Adding a new feature to the Queue** — describe it and link to a plan if one exists.
- **Adjusting a contract** — if you realise a criterion is wrong or missing before Claude starts the step.
- **Moving features between sections** — promoting from Queue to Current when ready.

You generally don't need to mark steps done manually — Claude handles that as it works.

## Where It Lives

`tasks/todo.md` in your project directory.

## Related Files

- [CLAUDE.md](claude-md.md) — contains the rules Claude follows when working through tasks
- [STATE.md](state-md.md) — points to the currently active step
- [ROADMAP.md](roadmap-md.md) — the big picture; features flow from roadmap into todo.md
- [execution/verify.py](execution-scripts.md) — the engine that runs `Verify:` patterns
