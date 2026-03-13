# Self-Annealing

## What It Means

Self-annealing is DOE's system for learning from failure. When something goes wrong, the framework doesn't just fix the immediate problem — it records what happened, why it happened, and how to prevent it next time. Over time, the project builds up immunity to its own failure patterns.

The name comes from metallurgy. Annealing is the process of heating metal and cooling it slowly to remove internal stresses and weaknesses. Each cycle makes the metal stronger and more resilient. DOE does the same thing with software projects — each failure, properly recorded, makes the system less likely to fail that way again.

> **In Plain English:** Imagine you're cooking and you burn the garlic because the heat was too high. You could just make a new batch. Or you could write "medium heat for garlic, not high" on a sticky note on the recipe. Next time, you check the note. The more you cook, the more notes you have, and the fewer mistakes you make. Self-annealing is DOE's version of those sticky notes — except Claude writes them automatically.

## How It Works in Practice

The cycle has five steps:

**1. Something fails.**
A script throws an error. A test doesn't pass. A file ends up in the wrong directory. The build breaks. An API returns unexpected data. Failures are normal — especially early in a project when patterns haven't been established yet.

**2. Claude diagnoses the root cause.**
This is the critical step. Claude doesn't just read the error message and try a quick fix. It traces back to *why* the failure happened. There's a difference between "the script crashed" (what happened) and "the script crashed because the API returns dates in DD/MM/YYYY format but the parser expects YYYY-MM-DD" (why it happened). The root cause is what gets recorded.

**3. Claude fixes the immediate problem.**
The script gets patched. The test gets updated. The file gets moved. Whatever broke gets unbroken. This is the quick fix — necessary, but not sufficient on its own.

**4. Claude records the pattern.**
This is what makes self-annealing different from just "fixing bugs." The pattern gets written down so it never has to be discovered again. Where it gets recorded depends on what kind of learning it is:

- **Project-specific** (references this project's setup, its APIs, its file structure) — goes in `learnings.md` in the project root. Example: "Our Census API returns a UTF-8 BOM character at the start of CSV responses — strip it before parsing."
- **Universal** (any project could hit this, regardless of what it's building) — goes in `~/.claude/CLAUDE.md`, the global learnings file that loads for every project. Example: "macOS `sed -i` requires an empty backup extension: `sed -i '' '...'`."

**5. Next time, Claude checks before acting.**
When a similar situation comes up — importing CSV data, using `sed` on macOS, calling the same API — Claude reads the relevant learnings before writing code. The pattern is already known. The mistake doesn't repeat.

## Two Levels of Recording

Not every failure deserves the same treatment. DOE uses two levels:

### Routine Failures

Small things. A flag that needed quoting. A path that was wrong. An API parameter that changed. These get a one-line entry in learnings.md with a source tag:

```
- macOS sed requires empty backup arg: sed -i '' '...'. [retro: data-pipeline]
- Nomis API pagination starts at 0, not 1. [retro: census-import]
- zsh glob fails with 'no matches found' when empty — guard with nullglob. [retro: build-script]
```

Short, searchable, and immediately useful when Claude encounters the same situation.

### Significant Failures

These are failures that cost more than 30 minutes of work, broke something important, or happened more than once. They get a structured entry with four parts:

```markdown
### Scottish data column mismatch
**What happened:** Demographic merge produced empty results for all Scottish constituencies.
**Root cause:** Scottish CSV uses 'constituency_name' while England/Wales uses 'pcon_name'.
  The merge script assumed a single column name across all nations.
**Fix applied:** Added column name mapping in import_census.py — normalises to 'pcon_name'
  before merge.
**Prevention added:** import_census.py now validates that the join column exists in both
  datasets before attempting the merge. Fails with a clear error message if not.
```

The structured format forces thoroughness. It's not enough to say "fixed the Scottish data bug." The root cause and prevention are what stop it from happening again — either in the same form or a similar one.

## Why This Matters

A fresh DOE project has no learnings. Claude starts with its general training and the rules in CLAUDE.md, but it doesn't know anything specific about your project's quirks. Early sessions will have more failures as patterns get discovered.

But each failure, properly recorded, makes the next session more reliable. After 20 sessions, learnings.md contains the most common gotchas. After 50 sessions, Claude navigates the project's problem space with real expertise — not because it's gotten smarter, but because the collective knowledge of every past session is available to it.

A project with 100 sessions of learnings behind it is dramatically more reliable than a fresh one. The failure rate drops because the patterns are already known. Edge cases that would trip up a new developer — or a new Claude session — are documented and handled.

This is the compounding effect of self-annealing: the system literally gets stronger the more you use it.

## The Human Role

Self-annealing isn't fully automatic. You have a part to play:

**Add learnings yourself.** If you notice Claude keeps getting something wrong — maybe it forgets a convention, or mishandles a particular file format — tell it directly. "Record this in learnings: always use double quotes for JSON keys in our config files." Claude will add it, and the pattern sticks.

**Review learnings periodically.** Open `learnings.md` every few weeks and scan it. Some learnings become irrelevant over time — an API changes, a library gets updated, a workaround is no longer needed. Remove stale entries to keep the file focused. A bloated learnings file is harder to scan and slower to load.

**Correct bad learnings.** Occasionally Claude records a pattern that's wrong, or too specific, or misses the real root cause. If you spot one, fix it or ask Claude to fix it. A wrong learning is worse than no learning — it actively sends Claude in the wrong direction.

The best projects have a clean, curated learnings.md where every entry earns its place. Think of it as tending a garden — regular pruning keeps it healthy.
