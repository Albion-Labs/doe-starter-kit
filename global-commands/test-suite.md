Run the project's accumulated test suite and report results.

Tests are stored in `tests/suite.json` -- criteria that passed verification get added automatically. This command re-runs them all to catch regressions.

## Step 1: Load suite

Read `tests/suite.json`. If it doesn't exist or is empty, show:
```
No test suite found. Tests accumulate automatically when /agent-verify passes.
```
And stop.

## Step 2: Run all criteria

For each test in the suite, run its `verify` pattern through verify.py:

```
python3 -c "
import json, sys; sys.path.insert(0, '.')
from execution.verify import run_criterion, run_build_step

# Build first
build = run_build_step()
if build and build['status'] == 'FAIL':
    print(f'Build failed: {build[\"detail\"]}')
    sys.exit(1)

suite = json.load(open('tests/suite.json'))
results = []
for test in suite:
    r = run_criterion(test['verify'])
    r['id'] = test['id']
    r['text'] = test['text']
    results.append(r)
print(json.dumps(results, indent=2))
"
```

## Step 3: Show results

Display a bordered results card:

```
+--------------------------------------------------+
|  TEST SUITE -- N tests                            |
+--------------------------------------------------+
|  [PASS] file: src/data/geo.js exists              |
|  [PASS] run: python3 execution/build.py           |
|  [FAIL] file: CHANGELOG.md contains v0.16.0       |
|         does not contain 'v0.16.0'                 |
|  [SKIP] html: index.html has .map-container       |
|         beautifulsoup4 not installed               |
+--------------------------------------------------+
|  Result: N/M passed, K failed, J skipped          |
|  Last full pass: [date or "never"]                |
+--------------------------------------------------+
```

Use simple ASCII borders. No emojis inside the box.

## Step 4: Update suite metadata

For each test in suite.json, update:
- `lastRun`: current ISO timestamp
- `lastStatus`: PASS/FAIL/SKIP
- `passCount`: increment if PASS
- `failCount`: increment if FAIL

Write the updated suite.json back.

## Step 5: Handle failures

If any tests failed:
- Show the failures prominently
- Suggest: "Run /agent-verify to investigate and fix failures"
- Do NOT auto-fix -- this is a reporting command

## Options

If the user says `/test-suite --prune`:
- Remove tests that have failed 3+ consecutive times (likely stale)
- Show what was pruned

If the user says `/test-suite --add '<verify pattern>'`:
- Add a new test manually to suite.json
- Assign it the next sequential ID
- Run it immediately and report result

## suite.json schema

```json
[
  {
    "id": "test-001",
    "text": "Human-readable description",
    "verify": "file: src/data/geo.js exists",
    "source": "v0.16.2-step3",
    "addedAt": "2026-03-05T14:00:00Z",
    "lastRun": "2026-03-05T14:30:00Z",
    "lastStatus": "PASS",
    "passCount": 5,
    "failCount": 0
  }
]
```

## Important notes

- SKIP counts as neutral (not pass, not fail) -- don't increment either counter
- Suite grows automatically from /agent-verify; manual additions via --add
- This is read-only except for metadata updates and --prune/--add
