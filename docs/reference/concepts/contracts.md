# Contracts

## What a Contract Is

A contract is a checklist attached to every task that Claude must complete before it can say "done." Each item on the checklist is a specific, testable criterion — not vague ("looks good") but concrete ("the file exists and contains this function").

Here's what a contract looks like in practice:

```
1. [ ] Add search to recipe list
   Contract:
   - [ ] [auto] Search input exists. Verify: file: src/recipes.js contains search-input
   - [ ] [auto] Search filters results. Verify: run: node tests/search.test.js
   - [ ] [manual] Search feels responsive, results update as you type
```

Each line is one criterion. Each criterion has a type (`[auto]` or `[manual]`) and — for auto criteria — a verification command that actually runs and checks the work.

## Why Contracts Exist

> **In Plain English:** AI is confident. Sometimes too confident. Claude will tell you something works when it doesn't. Not because it's lying — it genuinely believes what it's saying. Contracts fix this by requiring proof: automated checks that actually run and verify the work. It's like requiring a builder to pass a building inspection before you sign off, rather than just taking their word that the wiring is safe.

Without contracts, the workflow is: Claude builds something, says "done!", and you trust it. Sometimes that trust is warranted. Sometimes you discover three days later that the feature is broken in a way Claude never noticed.

With contracts, Claude can't mark a task complete until every automated check passes. It has to prove the work is correct, not just assert it.

## The Two Types

### [auto] — Verified Automatically

Auto criteria are checked by running a command or inspecting a file. Claude runs these itself after completing the work. If any check fails, it fixes the code and re-checks — up to three attempts before flagging the problem to you.

The `Verify:` patterns look like this:

| Pattern | What it checks | Example |
|---|---|---|
| `file: ... exists` | Does this file exist? | `Verify: file: src/app.js exists` |
| `file: ... contains` | Does this file contain specific text? | `Verify: file: src/app.js contains searchFunction` |
| `run: ...` | Does this command complete successfully? | `Verify: run: python3 tests/test_app.py` |
| `html: ... has` | Does this HTML file contain a specific element? | `Verify: html: index.html has .search-bar` |

These are the backbone of the contract system. A task with well-written auto criteria catches most bugs before they ship.

### [manual] — Verified by You

Some things can't be checked by a script. Does the layout look right? Does the interaction feel smooth? Is the print formatting readable? These need human eyes.

Manual criteria are collected and presented to you in a batch at the end of a feature — not after every individual step. This means Claude keeps building without stopping to ask "does this look okay?" every few minutes. You test once at the end, report what passed and what didn't, and any failures get fixed.

## How Contracts Work in Practice

Let's walk through the recipe search example from above:

```
1. [ ] Add search to recipe list
   Contract:
   - [ ] [auto] Search input exists. Verify: file: src/recipes.js contains search-input
   - [ ] [auto] Search filters results. Verify: run: node tests/search.test.js
   - [ ] [manual] Search feels responsive, results update as you type
```

**Claude builds the search feature.** It adds a search input to the recipe list page, writes the filtering logic, and creates a test file.

**Claude runs the first auto check:** `file: src/recipes.js contains search-input`. It reads the file, finds the text — check passes.

**Claude runs the second auto check:** `run: node tests/search.test.js`. The test runs and... fails. The filtering function has a bug where it matches against the recipe ID instead of the recipe name.

**Claude fixes and re-checks.** It updates the filtering logic, runs the test again. This time it passes.

**Claude marks the step done.** Both auto criteria pass, so the step is marked `[x]` in `todo.md`. Claude moves on to the next task.

**Feature moves to Awaiting Sign-off.** When the last step's auto criteria pass, the feature moves to the `## Awaiting Sign-off` section in todo.md — not straight to Done. It stays there until all manual items are verified. The SIGN-OFF row in `/stand-up` and `/sitrep` cards reminds you how many manual items are still pending.

**You test the manual criteria.** Claude presents a checklist: "Please test that the search feels responsive and results update as you type." You try it, confirm it works (or report what's wrong), and the feature moves to Done.

## The Rules

Every task must follow these rules:

- **At least one [auto] criterion.** No task can be purely manual. There must always be something that can be verified by running a command.
- **User-facing features need [manual] criteria too.** If the task is tagged `[APP]` (meaning it affects what users see), it must include at least one manual criterion for visual or interaction quality.
- **Infrastructure tasks can be fully automated.** Tasks tagged `[INFRA]` (internal tooling, scripts, configuration) can have only `[auto]` criteria if there's nothing visual to check.
- **Criteria must be specific.** "Works correctly" is not a valid criterion. "The function returns a sorted list of 650 items" is.
- **Verify patterns must be executable.** Every `[auto]` criterion needs a `Verify:` command that can actually run. `Verify: it looks right` is not executable. `Verify: run: python3 -c "assert len(data) == 650"` is.

## Why This Matters

Contracts serve two purposes:

**They catch bugs before they ship.** An auto criterion that runs a test will catch a broken function immediately — not three days later when you're trying to demo the project.

**They create a paper trail.** You can look back through `todo.md` and see exactly what was verified for each completed step. If something breaks later, you know what was tested and can narrow down where the new bug was introduced. This is especially valuable when a project grows and you can't personally remember every decision that was made.

Contracts add a small amount of overhead to planning each task. In exchange, they prevent the much larger overhead of debugging mysterious failures, re-doing work that "seemed fine," and losing trust in what Claude tells you.
