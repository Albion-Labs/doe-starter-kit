# Security Test Fixtures

This directory contains **deliberately vulnerable files** used to test that
pre-commit hooks and Claude Code hooks correctly detect and block insecure
patterns before they reach version control.

## How it works

Each `bad-*` file contains a single known-bad pattern (XSS, eval injection,
hardcoded secrets, shell injection). The `run-security-tests.sh` script
stages each file via `git add` and verifies the pre-commit hook **blocks**
the commit.

Each `good-*` file contains only safe patterns. The test runner verifies
these are **allowed** through without false positives.

## Files

| File | Pattern | Expected |
|------|---------|----------|
| `bad-innerhtml.js` | `element.innerHTML = userInput` | BLOCKED |
| `bad-eval.js` | `eval(userInput)` | BLOCKED |
| `bad-secret.js` | Hardcoded API key (`sk_test_...`) | BLOCKED |
| `bad-shell.py` | `subprocess.call(cmd, shell=True)` | BLOCKED |
| `bad-dangerouslysetinnerhtml.jsx` | `dangerouslySetInnerHTML` | BLOCKED |
| `good-textcontent.js` | `element.textContent = userInput` | ALLOWED |

## Running

```bash
./run-security-tests.sh
```

The script exits 0 if all assertions pass, non-zero if any test fails.

## Important

These files are **intentionally insecure**. Do not copy their patterns into
production code. They exist solely as test inputs for the security hook
pipeline.
