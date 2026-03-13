# Quality & Verification Commands

These commands help you check that things are correct — from individual task contracts to project-wide health. Think of them as your testing and inspection toolkit.

---

## /audit

**What it does:** Runs a battery of automated checks across your entire project and reports what's healthy and what needs attention.

**When to use it:** Before commits, before releases, or whenever you want a confidence check that the project is in good shape. Good habit to run periodically.

**What it checks:**

- **Governed doc freshness** — Are documents like `data-governance.md` and `legal-framework.md` up to date, or have they gone stale?
- **Task format** — Do all tasks in `todo.md` have proper contracts with testable criteria?
- **Roadmap consistency** — Do the status tags in `ROADMAP.md` match reality?
- **Git status** — Are there uncommitted changes, untracked files, or other loose ends?
- **Framework integrity** — Are all the DOE components (directives, execution scripts, hooks) present and correctly configured?

**What to expect:** A checklist with PASS, WARN, or FAIL for each category:

```
┌─ Audit ─────────────────────────────────────┐
│ Governed docs freshness    PASS              │
│ Task format & contracts    PASS              │
│ Roadmap consistency        WARN — 1 stale    │
│ Git status                 PASS              │
│ Framework integrity        PASS              │
│                                              │
│ Result: 4 PASS, 1 WARN, 0 FAIL              │
└──────────────────────────────────────────────┘
```

Warnings are things to look at when you have a moment. Failures should be fixed before proceeding.

---

## /fact-check

**What it does:** Reads a document and checks whether its claims match the actual codebase. If it finds inaccuracies, it corrects them in place.

**When to use it:** After major refactors or changes that might have made documentation stale. Also useful before sharing documentation externally — you don't want to claim a feature works one way when the code says otherwise.

**How it works:** Claude reads the target document, identifies factual claims (function names, file paths, behaviour descriptions, data formats), then checks each one against the codebase. Claims that don't match reality get flagged and corrected.

**What to expect:** A report showing what was checked and what was fixed:

```
Checking STATE.md...
  ✓ "Current feature: Targeting Page v2" — matches todo.md
  ✗ "8 of 10 steps complete" — actual: 9 of 10. Fixed.
  ✓ "No blockers" — matches STATE.md
  2 claims checked, 1 corrected
```

The corrections happen directly in the file. Review the changes before committing if you want to verify them.

---

## /review

**What it does:** Performs an adversarial code review. It's looking for problems, not compliments.

**When to use it:** Before shipping a feature, before merging a branch, or when you want a critical second opinion on recent changes. Especially valuable for code you wrote quickly or late at night.

**What it checks:**

- **Bugs** — Logic errors, off-by-one mistakes, unhandled edge cases
- **Security issues** — Exposed credentials, injection vulnerabilities, unsafe data handling
- **Performance problems** — Unnecessary loops, redundant API calls, missing caching
- **Style issues** — Inconsistent naming, unclear variable names, missing comments where needed

**What to expect:** A direct, honest assessment. This is deliberately not polite — the goal is to catch problems before users do:

```
ISSUES FOUND:

1. BUG (high): filter_regions() doesn't handle empty input.
   Line 45 of execution/filters.py — if `regions` is an empty
   list, the SQL query returns all rows instead of none.
   Fix: Add early return for empty input.

2. STYLE (low): Variable `x` in build_card() is unclear.
   Line 112 of execution/cards.py — rename to `card_index`
   or similar.

No security or performance issues found.
```

Think of it as a code review from a colleague who cares about quality but doesn't care about your feelings.

---

## /agent-verify

**What it does:** Runs all the `Verify:` patterns from the current task's contract and reports which pass and which fail.

**When to use it:** During and after building a task, to confirm the work meets its contract. This is the command that actually executes the testable criteria you defined.

**How it works:** Every task in `todo.md` has a contract with criteria marked `[auto]` (machine-checkable) and `[manual]` (needs human eyes). Each `[auto]` criterion has a `Verify:` pattern — a specific check like "run this script" or "confirm this file contains this string." `/agent-verify` runs all of them.

**Verify pattern types:**

| Pattern | What it does | Example |
|---------|-------------|---------|
| `run:` | Executes a command, checks exit code | `run: python3 execution/test_filters.py` |
| `file: ... exists` | Checks a file exists | `file: src/data/regions.json exists` |
| `file: ... contains` | Checks a file contains specific text | `file: src/index.html contains "region-filter"` |
| `html: ... has` | Checks an HTML file for an element | `html: src/index.html has div.filter-panel` |

**What to expect:**

```
Verifying: Add region filter dropdown
  [auto] run: python3 execution/test_filters.py    ✓ PASS
  [auto] file: src/data/regions.json exists         ✓ PASS
  [auto] html: src/index.html has select.region     ✓ PASS
  [manual] Dropdown appears below search bar        — skip (needs human)

  Result: 3/3 auto checks passed
```

If any check fails, you'll see the error output so you can diagnose what went wrong.

---

## /test-suite

**What it does:** Runs the project's accumulated test suite and reports the results.

**When to use it:** Before committing, after refactoring, or whenever you want to check that existing functionality still works. This catches regressions — things that used to work but broke because of a recent change.

**How it works:** Executes all test scripts that have been added to the project over time. Each passing task's `Verify:` patterns often get promoted into permanent tests, so the test suite grows as the project grows.

**What to expect:**

```
Running test suite...
  test_data_integrity        ✓ PASS
  test_filters               ✓ PASS
  test_card_generation       ✓ PASS
  test_build                 ✗ FAIL — missing closing tag in output

  Result: 3/4 passed, 1 failed
```

A failing test tells you exactly what broke, so you can fix it before the problem reaches users.

---

## /codemap

**What it does:** Generates a structured index of the project — files, functions, and how they relate to each other. Writes the result to `.claude/codemap.md`.

**When to use it:** When joining a new project for the first time, or after significant structural changes (new files, renamed modules, reorganised directories). The codemap helps Claude understand the codebase faster in future sessions.

**How it works:** Scans the project's files, reads their contents, and builds a map of:

- What each file does (one-line summary)
- Key functions and their signatures
- Which files depend on which other files
- Entry points and data flow

**What to expect:** A markdown file at `.claude/codemap.md` that reads like a table of contents for your codebase:

```markdown
## execution/
- build.py — Assembles monolith HTML from src/ files
  - build_page() → reads templates, injects data, writes output
  - calls: load_data(), render_cards()
- filters.py — Region and category filtering logic
  - filter_regions(data, selected) → filtered dataset
  - used by: build.py, test_filters.py
```

This file is for Claude's reference, but it's human-readable too. Useful for onboarding or for understanding unfamiliar parts of the project.
