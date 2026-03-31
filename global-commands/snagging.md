Generate (or regenerate) the manual test checklist for the current feature, with automated test results when available.

## Step 1: Identify the target feature

If arguments were passed (e.g. `/snagging Pulse 2.0`), use that as the feature name.

Otherwise, read `tasks/todo.md` and `STATE.md` to identify the current in-progress feature and its unchecked `[manual]` items.

If no unchecked `[manual]` items exist for the current feature, check `## Awaiting Sign-off` in `tasks/todo.md` for features with pending manual items.

If nothing is found anywhere, report: "No manual tests pending." and stop.

## Pre-merge context

Snagging is the pre-merge verification gate. Before a feature branch PR can be merged to main, the snagging checklist must be completed. This includes automated checks (CI Result gate, project-specific checks, health check, contract verification via agent-verify) and manual visual checks.

## Step 1b: PR conflict and staleness check

Before running any tests, check for merge risks:

1. **Branch staleness:** Run `git rev-list --count HEAD..origin/main` to see how many commits main is ahead. If > 0, warn: "Branch is N commits behind main -- rebase before merging to avoid surprises." If > 10, escalate: "Branch is significantly behind main (N commits) -- rebase strongly recommended."

2. **PR conflict detection:** If 2+ PRs are open (`gh pr list --state open`), check for file overlaps between this PR and others: run `gh pr view N --json files --jq '.files[].path'` for each. If any files appear in multiple PRs, warn: "Merging this PR will create conflicts for PR #N on [overlapping files]. Merge this one first, then rebase #N -- or merge #N first if it's ready."

Show results in the snagging output. These are warnings, not blockers -- the user decides how to proceed.

## Step 2: Run automated test suite (if available)

**Portability guard:** Only run this step if `execution/run_test_suite.py` exists. If it doesn't exist, skip to Step 3.

**Auto-bootstrap:** Before running, verify Playwright is installed by checking if `node_modules/.bin/playwright` exists. If not, tell the user: "Quality Stack not bootstrapped -- installing dependencies..." and run `python3 execution/run_test_suite.py --bootstrap` automatically. If bootstrap succeeds, continue with the test suite. If it fails, log the error and skip to Step 3.

Tell the user: "Running automated tests (health check, contract verification) -- about 30-60 seconds."

```bash
python3 execution/run_test_suite.py
```

Use `timeout: 180000` on the Bash tool call (3 minutes max).

**APP_PATH mismatch handling:** If the results JSON (`.tmp/test-suite-results.json`) contains a warning about APP_PATH mismatch, update the `APP_PATH` constant in all 3 test files (`tests/app.spec.js`, `tests/accessibility.spec.js`, `tests/visual.spec.js`) to match the current version from STATE.md, then re-run the test suite.

**Mobile projects (Maestro):** If `projectType` in `tests/config.json` is `react-native`, `expo`, or `flutter`, the test suite runs Maestro flows instead of Playwright tests. Results appear under a `maestro_results` key in the results JSON, and the checklist generator will show "Maestro Flows" tiles instead of "Browser Tests".

## Step 3: Run automated code trace

**Always run this step** -- code trace is available in every DOE project and provides automated verification without any dependencies.

Tell the user: "Running code trace on feature files..."

Perform a code trace on the files relevant to the current feature's `[manual]` items. Read the source files referenced in the manual checks, identify the functions/modules involved, and check for:
- Logic errors or unreachable code paths
- Missing null/undefined guards on data the manual check depends on
- DOM elements referenced in manual checks that may not exist or have wrong IDs/classes
- Event handlers that may not be wired up correctly
- Data flow issues (function called but return value not used, stale closures, etc.)

Write findings to `.tmp/test-code-trace.json`:

```json
[{"title": "Brief issue title", "description": "What the code trace found", "file": "path/to/file.js", "line": 123, "severity": "High|Medium|Low", "found_by": "code-trace"}]
```

If no issues found, write an empty array `[]` to the file. This ensures the automated summary section still renders showing "Code Trace: Clean".

## Step 4: Run the generator

```bash
python3 execution/generate_test_checklist.py [--feature "Name"] [--bugs .tmp/test-bugs.json] [--test-results .tmp/test-suite-results.json] [--code-trace .tmp/test-code-trace.json]
```

Include `--feature` if targeting a named feature. Include `--bugs` only if `.tmp/test-bugs.json` exists (from a previous run, not from code trace). Include `--test-results` only if `.tmp/test-suite-results.json` exists (i.e., the test suite ran in Step 2). Include `--code-trace` only if `.tmp/test-code-trace.json` exists (from Step 3).

## Step 5: Chrome verification (if available)

**This step only runs when Chrome MCP tools are available** (user ran `/chrome` or started with `--chrome`). If Chrome is not enabled, skip to Step 6 and show: "Chrome not enabled -- run `/chrome` to auto-verify visual items, or proceed with manual checks."

Read `directives/chrome-verification.md` for the full protocol. In brief:

1. The app is already being served on port 8080 (from Step 2's orchestrator, or start `npx serve -l 8080` if Step 2 was skipped)
2. Navigate to the app URL
3. For each `[manual]` item in the checklist, determine if Chrome can verify it:
   - **DOM/content checks** (element exists, text matches, tab works): Navigate, click, read DOM. Mark `[auto-chrome]` if verified.
   - **Console checks** (no JS errors): Read console after page load. Mark `[auto-chrome]` if clean.
   - **Layout checks** (responsive, visual): Screenshot and describe what's visible. Mark `[auto-chrome]` if layout matches description.
   - **Subjective items** (looks polished, feels smooth, content clarity): Leave as `[manual]` for the user.
4. Record Chrome-verified items with evidence (what was checked, what was found)
5. Update the checklist: re-run the generator with Chrome results included, or note Chrome-verified items in the summary card

**Do not block on Chrome failures.** If a Chrome check fails (extension disconnects, page won't load), log the failure and leave the item as `[manual]`.

## Step 6: Report

Show a brief summary:

```
┌──────────────────────────────────────────────────┐
│  TEST CHECKLIST -- [Feature name]                │
├──────────────────────────────────────────────────┤
│  Manual checks:  N items (M remaining for user)  │
│  Auto-verified:  N tests (or "skipped")          │
│  Bugs surfaced:  N (or none)                     │
│  Checklist:      open in browser                 │
└──────────────────────────────────────────────────┘
```

Use Unicode box-drawing characters (`┌─┐`, `├─┤`, `└─┘`, `│`). No emojis inside the box.

**Chrome visual verification:** After the automated checks, prompt the user: "Run `/chrome` to open the app in Chrome for visual verification of [manual] items."

**If test suite results show failures or warnings, mention them before telling the user to work through the checklist.** For example: "2 test failures and a health check warning -- see the automated results section at the top of the checklist."

Then tell the user:

```
Work through the checklist, then paste the exported results back here.
I'll fix any failures and regenerate.
```

## Step 6: Handle paste-back results

Items prefixed `[auto]` in the exported results were machine-verified during this snagging run -- distinct from `[auto]` contract criteria in todo.md. Do not ask the user about `[auto]` items. Only act on `[ ]` failures and manual `[x]` passes.

## Baseline updates

If the user wants to accept the current state as the new baseline (e.g., after an intentional UI redesign or accepted performance regression), run:

```bash
python3 execution/run_test_suite.py --update-baselines
```

For specific baselines only:
- `--update-visual` -- visual regression screenshots
- `--update-lighthouse` -- Lighthouse performance score
- `--update-a11y` -- accessibility known violations

Each update command automatically re-runs the full suite and writes fresh results.

## Important notes

- If `execution/generate_test_checklist.py` doesn't exist, report the error and stop -- do not generate a checklist inline
- Arguments override auto-detection: `/snagging Feature Name` always targets that feature
- Clean up `.tmp/test-bugs.json` after the checklist is generated (it's ephemeral)
