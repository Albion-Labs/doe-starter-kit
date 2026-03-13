# directives/ — Standard Operating Procedures

Directives are instruction documents for specific types of tasks. They're written in plain English (markdown), and they tell Claude exactly how to handle a particular kind of work — what to do, in what order, what tools to use, and what to check when done.

Think of them as recipes. Instead of saying "make a cake," you hand Claude a recipe that says "preheat to 180, mix these ingredients, bake for 25 minutes, check with a skewer." The result is consistent and repeatable.

## How They Work

You don't need to tell Claude which directive to read. CLAUDE.md contains a Progressive Disclosure section with triggers — rules like "when importing external data, read the data import directive first." Claude matches the current task to a trigger and loads the right directive automatically.

For example, if you say "import the weather data from the Met Office API," Claude matches that to the "importing external data" trigger, reads the relevant directive, and follows its steps.

This matters because directives can be detailed — sometimes a full page of instructions. Loading all of them into every session would waste Claude's context window. Progressive Disclosure means Claude only reads what it needs for the current task.

## Built-In Directives

A DOE project comes with several directives out of the box:

| Directive | What It Covers |
|-----------|---------------|
| `documentation-governance.md` | Rules for keeping project documentation accurate and versioned |
| `claim-auditing.md` | How to verify that claims in the codebase are still true |
| `break-glass.md` | Emergency procedures when something goes seriously wrong |
| `architectural-invariants.md` | Structural rules that must never be violated during refactoring |
| `testing-strategy.md` | How to set up and run tests |
| `starter-kit-sync.md` | How to sync improvements back to the DOE starter kit |
| `best-practices/` | Language-specific coding standards (Python, JavaScript, etc.) |

## Creating Your Own

Every directive follows the same structure, defined in `_TEMPLATE.md`:

```markdown
# Directive: Weather Data Import

## Goal
Import daily weather forecasts from the Met Office API and store them as JSON.

## When to Use
When importing, refreshing, or backfilling weather data.

## Inputs
- Met Office API key (stored in .env as MET_OFFICE_KEY)
- Date range to import

## Process
1. Run `python3 execution/import_weather.py --start YYYY-MM-DD --end YYYY-MM-DD`
2. Script fetches daily forecasts, handles pagination, writes to src/data/weather.json
3. If the API returns a rate limit error, wait 60 seconds and retry (max 3 retries)
4. After import completes, run `python3 execution/build.py` to rebuild the app

## Outputs
- `src/data/weather.json` — one entry per day per region
- Console summary showing records imported, skipped, and any errors

## Edge Cases
- API returns 429 (rate limit): script handles automatically with backoff
- Missing data for a date: logs a warning, continues with next date
- API key expired: script exits with clear error message pointing to .env

## Verification
- [ ] Output file exists and contains expected date range
- [ ] No errors in execution logs
- [ ] Build succeeds after import
- [ ] Spot-check 3 random dates against the API directly
```

To add a trigger so Claude reads this directive automatically, add a line to the Progressive Disclosure section in CLAUDE.md:

```markdown
- Importing or refreshing weather data → read `directives/weather-data-import.md`
```

## The Key Principle

Directives describe **what** to do. Execution scripts (in `execution/`) do the actual work. A directive might say "run the import script with these parameters," but the directive itself doesn't contain any code. This separation means:

- You can read a directive and understand the process without reading Python
- The script runs the same way every time, regardless of what Claude's reasoning is doing
- You can update the process (directive) without touching the code (script), and vice versa

## When You'd Create One

Create a directive when:
- A task has more than 3 steps that must happen in order
- Multiple sessions might need to perform the same task
- The task has edge cases that are easy to forget
- Getting the task wrong has consequences (data loss, compliance issues, billing)

Don't create a directive for:
- Simple one-off tasks ("add a button to the settings page")
- Tasks that are already well-covered by an existing directive
- Anything that changes too frequently to be worth documenting

## Important: Directives Are Protected

A CLAUDE.md guardrail prevents Claude from editing existing directives without your explicit permission. This is enforced by a [hook](hooks.md) that blocks writes to the `directives/` directory. This exists because directives are living SOPs (Standard Operating Procedures) — changing one without review could silently break a process.

Claude can create new directives freely. It just can't modify existing ones without asking first.

## Where They Live

`directives/` in the root of your project directory. The template is at `directives/_TEMPLATE.md`.

## Related Files

- [CLAUDE.md](claude-md.md) — contains the Progressive Disclosure triggers that point to directives
- [execution/](execution-scripts.md) — the scripts that directives reference
- [Hooks](hooks.md) — the `protect_directives.py` hook that guards existing directives
