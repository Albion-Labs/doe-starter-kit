# Best Practices: Test-Driven Development & Systematic Debugging

## Goal
Prevent Claude from skipping tests or guessing at bug causes. Enforce disciplined TDD and evidence-based debugging.

## When to Use
- Writing new functions, modules, or features (TDD section)
- Fixing bugs, investigating failures, or diagnosing unexpected behaviour (Debugging section)
- Any time Claude claims "this is too simple to test" or "I'll add tests later" (check Rationalisation Table)

## Test-Driven Development

### The Cycle: Red → Green → Refactor

1. **Red:** Write a test that describes the desired behaviour. Run it. Watch it fail. If it passes without your code, the test is wrong.
2. **Green:** Write the minimum code to make the test pass. Nothing more.
3. **Refactor:** Clean up the implementation without changing behaviour. Tests must still pass.

One cycle per behaviour. Don't batch. Don't write three tests then implement all three — that's batch-and-pray, not TDD.

### What to Test

| Layer | Test with | Example |
|-------|-----------|---------|
| Pure functions | Unit test (assert input → output) | `computeSeatScore(data) → 73.2` |
| Data transforms | Snapshot test (known input → expected JSON) | `enrichRecord(raw) → enriched` |
| DOM rendering | Selector assertion (`html: ... has .class`) | Card renders with `.info-card` |
| API integration | Contract test (expected shape) | Response has `results[].id` |
| User flow | Playwright/Chrome (navigate, click, assert) | Search → click result → page loads |

### Rationalisation Table

Claude will find plausible reasons to skip tests. These are the common excuses and why they're wrong:

| Excuse | Why it's wrong | What to do instead |
|--------|---------------|-------------------|
| "This is too simple to test" | Simple code breaks when requirements change. The test documents intent. | Write a one-liner assertion. Simple code = simple test. |
| "I'll add tests later" | Later never comes. Untested code accumulates. | Write the test now. It takes 30 seconds for simple cases. |
| "The existing tests cover this" | Unless you can name the specific test, they don't. | Grep for the function name in tests. No match = no coverage. |
| "It's just a refactor, the tests still pass" | If no test exercises the refactored path, passing tests prove nothing. | Add a test that exercises the changed code path. |
| "This is a UI component, it can't be unit tested" | The logic can. Extract it. Test the logic. Visual goes to [manual]. | Separate rendering from logic. Test logic, screenshot UI. |
| "Testing this would require mocking half the system" | That's a design problem, not a testing problem. | Refactor to reduce coupling, then test the isolated unit. |
| "The contract criteria already verify this" | Contract criteria check existence and wiring. They don't check logic. | Contract = Level 1-3. TDD = logic correctness. Both needed. |

**Rule:** If you catch yourself using any of these excuses, stop and write the test. The excuse is the signal that a test is needed.

### When TDD Applies in DOE

TDD applies to **execution scripts** (`execution/`) and **data-layer code** (`src/js/`, `src/data/`). It does NOT apply to:
- Directive files (markdown — not executable)
- Configuration (JSON/YAML — validated by contract criteria)
- One-off data imports (run once, verify output, discard script)
- Prompt engineering (slash commands — tested by using them)

For [APP] features with UI:
- TDD the data layer (scoring, transforms, lookups)
- Contract-verify the DOM structure (selectors, element existence)
- [manual]-verify the visual result (layout, aesthetics, interaction feel)
- Chrome-verify where possible (navigate, screenshot, DOM state)

## Systematic Debugging

When something fails, follow these four phases in order. Do not skip phases.

### Phase 1: Investigate (gather evidence)

**Before forming any hypothesis:**
- Read the FULL error message. Not the first line — the full stack trace.
- Reproduce the failure. If you can't reproduce it, you can't verify a fix.
- Check what changed recently: `git log --oneline -10`, `git diff HEAD~1`.
- Check the environment: Node version, Python version, OS, dependencies.
- Read the relevant source code. Don't guess what a function does — read it.

**Output:** A factual summary of what fails, when, and what the error says. No theories yet.

### Phase 2: Pattern Analysis (what's common?)

- Is the failure consistent or intermittent?
- Does it fail in all environments or just one?
- Has this code ever worked? If yes, what changed since then?
- Are there similar failures elsewhere in the codebase? (grep for the error message)
- Does the failure correlate with specific inputs, timing, or state?

**Output:** Patterns or correlations that narrow the search space. Still no fix attempts.

### Phase 3: Hypothesis Testing (test each theory)

Form specific, falsifiable hypotheses. Test them one at a time.

**Format:**
```
Hypothesis: The build fails because X
Test: [specific command or check]
Result: [confirmed/rejected]
```

**Rules:**
- One hypothesis at a time. Don't change three things and see if it works.
- If a hypothesis is rejected, revert the test change before trying the next one.
- If three hypotheses fail, return to Phase 1 — you're missing evidence.
- Never say "I think the problem might be..." without immediately stating how to test that theory.

### Phase 4: Implementation (fix and prevent)

Only after confirming the root cause:

1. **Fix:** Change the minimum code to resolve the root cause. Not a workaround. Not a suppress.
2. **Verify:** Run the reproduction case. Confirm it passes.
3. **Regression:** Check that nothing else broke. Run existing tests.
4. **Prevent:** Can this class of bug be caught automatically? If yes, add a check (test, lint rule, contract criterion, or hook). If no, log to `learnings.md`.

### Debugging Anti-Patterns

| Anti-pattern | Why it fails | Do this instead |
|-------------|-------------|----------------|
| "Let me try this..." (random changes) | Masks the real cause, introduces new bugs | Follow Phase 1-3 before changing anything |
| Fixing the symptom | The root cause will resurface in a different form | Trace the error to its origin, not its manifestation |
| "Works on my machine" | Environment differences ARE the bug | Reproduce in a clean environment |
| Adding try/catch to suppress | Hides the error, doesn't fix it | Fix the throwing code, not the catching code |
| Reverting to a known-good state | You haven't learned what broke or why | Understand the failure BEFORE reverting |
| "The tests pass so it's fine" | If the tests don't cover the failure case, they prove nothing | Write a test that reproduces the failure first |

## Verification
- [ ] Directive exists at `directives/best-practices/tdd-and-debugging.md`
- [ ] CLAUDE.md triggers reference this directive
- [ ] Rationalisation table covers the 7 common excuses
- [ ] Debugging phases are numbered and sequential
