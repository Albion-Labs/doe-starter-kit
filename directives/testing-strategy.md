# Directive: Testing Strategy

## Goal
Define what, when, and how to test in this project -- so verification is consistent, fast, and never skipped.

## When to Use
- Setting up testing for a new project or configuring test tools
- Writing contract criteria for a new task
- Deciding whether a change needs [auto] or [manual] verification
- Debugging a verification failure

## Project Type
<!-- Fill in your project type from tests/config.json (e.g. html-app, python-cli, api-service) -->

## What to Test

### [auto] Criteria (deterministic, machine-verified)
Use these for anything a script can check reliably:
- **File existence:** `Verify: file: <path> exists`
- **File content:** `Verify: file: <path> contains <string>`
- **Script execution:** `Verify: run: <shell command>` (exit code 0 = pass)
- **HTML structure:** `Verify: html: <path> has <CSS selector>` (requires BeautifulSoup)

Rules:
- Every task in todo.md must have at least one `[auto]` criterion
- Prefer `file: ... contains` over `run: grep` -- it's faster and more readable
- `run:` commands must complete within the timeout set in tests/config.json (default 30s)
- Keep commands simple -- one check per criterion, no chained pipes when avoidable

### [manual] Criteria (human-verified)
Use these for things that require visual judgment or interaction:
- UI rendering, layout, and responsiveness
- Data accuracy that requires domain knowledge
- User flows that involve clicking, scrolling, or navigation
- Accessibility checks (screen reader, keyboard nav)

Rules:
- `[APP]` tasks must have at least one `[manual]` criterion
- `[INFRA]` tasks can be fully `[auto]`
- Write manual criteria as yes/no questions

## What NOT to Test
- Third-party API availability (flaky, not our fault)
- Exact pixel rendering (varies by browser/OS)
- Performance benchmarks (too environment-dependent for contracts)
- File sizes or line counts (brittle, break on unrelated changes)

## Verification Flow

### Solo mode (single terminal)
1. Write task + contract in todo.md
2. Implement the feature
3. Run `/agent-verify` (or verify manually)
4. All `[auto]` pass + all `[manual]` confirmed -> mark step done
5. If `[auto]` fails: fix and re-verify (up to 3 attempts)

### Informal parallel (multiple terminals, manual coordination)
Same as solo mode per-terminal. Each terminal works on a different step. The user coordinates which steps run where. No shared wave infrastructure — just run `/agent-verify` in each terminal independently. Watch for shared-file contention on STATE.md, learnings.md, and todo.md.

### Formal parallel (wave/DAG dispatch)
1. `/agent-launch` validates contracts at pre-flight
2. Agent implements the feature
3. `--complete` runs `execution/verify.py` automatically
4. `--merge` runs regression checks (pre/post comparison)

## Build Step
<!-- If your project has a build step, tests/config.json buildCommand runs before verification -->

## Pattern Reference

| Pattern | Example | Checks |
|---------|---------|--------|
| `file: <path> exists` | `file: src/config.py exists` | File exists on disk |
| `file: <path> contains <str>` | `file: CLAUDE.md contains testing trigger` | Substring in file |
| `run: <cmd>` | `run: python3 execution/verify.py --self-test` | Exit code 0 |
| `html: <path> has <sel>` | `html: index.html has .main-content` | CSS selector match |

## Three-Level Verification

When writing `[auto]` contract criteria, aim for depth -- not just existence. Three levels of verification catch progressively more bugs:

### Level 1: Exists
The file or function is physically present.
```
Verify: file: src/feature.js exists
```
**Catches:** missing files, typos in filenames, forgotten creation.
**Misses:** stubs, placeholder code, dead functions.

### Level 2: Substantive
The implementation contains real logic, not stubs or placeholders.
```
Verify: file: src/feature.js contains calculateScore
Verify: run: ! grep -q 'return null' src/feature.js
```
**Catches:** stub implementations (`return null`, `// TODO`), empty function bodies, placeholder text.
**Misses:** code that exists but is never called.

### Level 3: Wired
The implementation is actually imported, called, and used by the rest of the application.
```
Verify: run: grep -rq 'calculateScore' src/
Verify: run: grep -rq 'featureInit' src/app.js
```
**Catches:** orphan code, dead functions, modules that exist but are never loaded.
**Misses:** logic correctness (use `/code-trace` for that).

### When to use each level
- **Quick tasks (1-2 files):** Level 1 is usually enough -- the contract criteria themselves describe the behaviour.
- **Data-layer steps (algorithms, scoring, derivation):** Use Level 2 to verify substantive implementation, then run `/code-trace` for logic correctness.
- **Integration steps (cross-module wiring):** Use Level 3 to verify the module is actually connected to the rest of the app.
- **All [APP] features:** The `[manual]` criteria naturally cover "is it wired?" since the tester sees the UI working.

### Contract Verify: strings are design-phase guesses

When a plan is written, `Verify:` patterns reference class names, function names, and id attributes that don't exist yet -- they're the author's guess at what the implementation will use. By Step N, the actual code may use slightly different names (e.g. plan said `section-group`, code uses `el-section`; plan said `_dimensionBrief('x')`, function takes dimension IDs like `'y'`).

Before marking a step `[x]`:
1. Re-read the contract's `Verify:` patterns
2. Check each `contains` string and CSS selector against the actual implementation
3. If there's a mismatch, fix the contract (not the code) -- the contract is a promise to a future reader and should describe what's true

This applies doubly to manual test instructions: function names, parameter types, and valid inputs in manual steps must reflect the shipped implementation, not the plan. Otherwise the human tester hits errors that weren't real bugs.

Quick fix, not a process problem. Do it reflexively at each step's verify-and-mark moment.

### Post-Step Testing Protocol

After completing each step, Claude runs the appropriate quality checks based on the step type:

| Step type | What runs automatically | Signpost |
|-----------|------------------------|----------|
| Data-layer (algorithms, scoring, derivation) | `/code-trace` on the new module | "This is a data-layer step -- running code trace" |
| UI (pages, components, layouts) | Playwright browser tests | "Running browser tests for affected pages" |
| Integration (cross-module wiring) | `/code-trace --integration` | "Running integration trace across modules" |
| Any step | Regression suite (if wired) | "Regression: N/N passed" |
| Final step | Full sweep: regression + health check | "Running final verification sweep" |

Claude announces what testing will happen at the start of each step and reports results after completion. The user never has to remember what to run.

## Playwright MCP: Converting [manual] to [auto] Criteria

When the Playwright MCP server is available (`mcp__plugin_playwright_playwright__*` tools), many criteria labelled `[manual]` can be converted to `[auto]` with `Verify: run:` patterns that drive a browser. This reduces the manual testing burden at feature completion.

### When to Convert

Convert a `[manual]` criterion to `[auto]` when it checks something a browser can verify deterministically:
- **Element existence:** "Button X appears on the page" -> DOM snapshot + selector check
- **Content rendering:** "Card shows data" -> navigate + text content check
- **Navigation flow:** "Clicking X navigates to Y" -> click + URL assertion
- **Responsive layout:** "Layout stacks on mobile" -> resize viewport + check element position
- **Error states:** "Error message appears on invalid input" -> fill form + check error element

### When to Keep [manual]

Keep `[manual]` for criteria that require human judgment:
- **Visual quality:** "Layout looks clean and professional" -- subjective
- **Interaction feel:** "Scrolling is smooth" -- timing-dependent
- **Content accuracy:** "The analysis is fair and balanced" -- domain judgment
- **Accessibility feel:** "Screen reader experience is coherent" -- holistic UX

### Process

When starting a feature with `[manual]` visual/UI criteria:
1. Review each `[manual]` criterion against the conversion rules above
2. For each convertible criterion, write a `Verify: run:` pattern using Playwright
3. Update the contract in todo.md (change `[manual]` to `[auto]`, add `Verify:` pattern)
4. Keep only genuinely subjective criteria as `[manual]`

This reduces the manual sign-off burden and catches regressions automatically.

## Edge Cases
- `html:` pattern requires `beautifulsoup4` -- if not installed, criterion returns SKIP (not FAIL)
- `run:` commands inherit the project root as cwd
- `file:` paths are relative to project root unless absolute
- If `tests/config.json` is missing, verify.py uses defaults (30s timeout, no build step)

## Maintenance

This section governs ongoing changes to code that already has test coverage -- the freshness loop that keeps a passing suite from rotting into a hollow one. Loaded by the manifest trigger "Testing setup / strategy / Modifying tested code", so it fires on edits, not only on initial setup.

### When you modify tested code, tests are required (not optional)

Tested surfaces in this kit:
- `execution/*.py` -- `doe_init.py`, `verify.py`, `test_methodology.py`, `audit_claims.py`, `health_check.py`, generators
- `.githooks/*` -- `pre-commit`, `pre-push`, `commit-msg`, `post-commit`
- Any source file that has a sibling test under `tests/`

For these surfaces, every commit that changes behaviour must either:

1. **Update an existing test** -- if your change adjusts the contract of a function that already has coverage, update the assertions in the matching test file. Don't delete the test "because it's broken now" -- the test was the spec.
2. **Add a new test** -- if your change introduces a new code path, prompt, branch, or flag, add a test that exercises it. The pre-commit warning hook will flag tested-file changes that ship without staged tests, but the warning is a nudge, not a substitute for thinking.

If a change is genuinely test-irrelevant (a comment fix, a docstring tweak, a rename with no behavioural impact), say so in the commit body and move on. The default is "tests come with the change."

### Reviewing `[manual]` contracts when new auto tools ship

When a new auto tool ships (e.g. Playwright MCP, a new linter, a new methodology scenario), don't build an auto-promotion engine -- review existing `[manual]` contracts by hand and promote the ones the new tool can verify. Replace each promotable item's free-text description with a `Verify: run:` (or `Verify: html:`, `Verify: file:`) pattern that drives the new tool deterministically.

The signpost: a new auto tool that overlaps with criteria currently sitting under `[manual]` should trigger a one-pass sweep of open contracts, not a generic "convert everything" script. Keep the genuinely subjective items (visual quality, interaction feel, content judgment) as `[manual]`. See "Playwright MCP: Converting [manual] to [auto] Criteria" above for the conversion checklist.

### Doc freshness counterpart

Code changes that ship without doc updates rot the tutorial. Pre-commit warns when `global-commands/*.md` change without `docs/tutorial/commands.html`, or `.githooks/*` change without `docs/tutorial/hooks.md`. Same rule as tests: the warning is a nudge, the change still ships, but `kit-development.md` expects the doc to land in the same PR where reasonable.

## Verification
- [ ] This directive exists and is referenced from CLAUDE.md triggers
- [ ] tests/config.json exists alongside this directive
- [ ] Pattern examples above match the patterns defined in todo.md format rules
