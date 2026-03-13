# execution/ — Deterministic Scripts

The `execution/` directory contains Python scripts that do the actual work in a DOE project — API calls, data imports, file transformations, audits, verification, and reports. These are the workhorses of the system.

## Why They're Separate from Claude

This is one of the core ideas in DOE: **probabilistic AI handles reasoning, deterministic code handles execution.**

Claude is great at deciding what to do — understanding your request, reading the current state, choosing the right approach. But Claude can hallucinate data, make inconsistent API calls, or produce slightly different results each time. For anything that needs to run the same way every time, you want a script.

The separation works like this:
- **Claude decides** which script to run and with what parameters
- **The script executes** the actual work identically every time
- **Claude verifies** the result matches what was expected

A data import that Claude runs inline might fetch 98% of the records one time and 100% the next. A script fetches 100% every time because the pagination logic is deterministic code, not probabilistic reasoning.

## Built-In Scripts

A DOE project includes several utility scripts:

| Script | What It Does |
|--------|-------------|
| `verify.py` | Runs `Verify:` patterns from contracts — the engine behind `[auto]` criteria |
| `check_contract.py` | Validates contract format before commits (used by the pre-commit hook) |
| `audit_claims.py` | Checks that claims in the codebase are still true (project health check) |
| `wrap_stats.py` | Computes session statistics for the `/wrap` command |
| `build.py` | Assembles source files into the final output (project-specific) |

## How Claude Uses Them

When Claude needs to perform an action that has an existing script, it runs the script rather than doing the work inline. For example:

- Instead of writing code to check if a file contains a string, Claude runs `verify.py`
- Instead of manually computing session statistics, Claude runs `wrap_stats.py`
- Instead of inlining an API call, Claude runs the relevant `import_*.py` script

This is enforced by a rule in CLAUDE.md: "Never do execution inline when a script exists. Check `execution/` first."

## Creating Your Own

When Claude needs to do something that no existing script covers — like importing data from a new API, or transforming a dataset into a different format — it creates a new script in `execution/`. Scripts follow a consistent pattern:

```python
#!/usr/bin/env python3
"""Import daily weather forecasts from the Met Office API.

Usage:
    python3 execution/import_weather.py --start 2026-01-01 --end 2026-03-01

Outputs:
    src/data/weather.json — one entry per day per region
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.request import Request, urlopen

# Load credentials from .env
API_KEY = os.getenv("MET_OFFICE_KEY", "")
if not API_KEY:
    print("Error: MET_OFFICE_KEY not set in .env", file=sys.stderr)
    sys.exit(1)

OUTPUT = Path("src/data/weather.json")


def fetch_forecasts(start_date, end_date):
    """Fetch daily forecasts, handling pagination and rate limits."""
    results = []
    # ... fetch logic with retry and backoff ...
    return results


def main():
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    args = parser.parse_args()

    data = fetch_forecasts(args.start, args.end)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, indent=2))
    print(f"Wrote {len(data)} records to {OUTPUT}")


if __name__ == "__main__":
    main()
```

Key patterns to notice:
- **Docstring at the top** explains what the script does and how to run it
- **Credentials from .env** — never hardcoded
- **Clear error messages** when prerequisites are missing
- **`if __name__ == "__main__"` guard** so the script can be both imported and run directly
- **Output goes to a defined location** (usually `src/data/`)

## The Key Principle

If a task involves any of these, it should be an execution script:

- **External API calls** — rate limits, pagination, retry logic
- **Data transformation** — parsing CSVs, merging datasets, computing statistics
- **File operations** — building output files, cleaning up temporary files
- **Verification** — checking that outputs match expected format

If a task is purely about reasoning (understanding a request, choosing an approach, writing a plan), that stays with Claude.

## When You'd Edit Them

- **Fixing a bug** — the script has an edge case it doesn't handle
- **Adding a parameter** — you need to import a different date range or region
- **Updating for API changes** — an external service changed its response format

Before editing, check [learnings.md](learnings-md.md) for known gotchas about the script. Before creating a new script, check if an existing one already does something similar — reuse before writing.

## Where They Live

`execution/` in the root of your project directory. All scripts are Python 3.

## Related Files

- [directives/](directives.md) — SOPs that reference execution scripts by name
- [tasks/todo.md](todo-md.md) — contracts that use `Verify: run:` to execute scripts
- [Hooks](hooks.md) — the pre-commit hook runs `audit_claims.py` and `check_contract.py` automatically
- [learnings.md](learnings-md.md) — the "Execution Script Gotchas" section tracks known issues
