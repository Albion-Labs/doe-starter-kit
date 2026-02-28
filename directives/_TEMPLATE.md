# Directive: [Name]

## Goal
What this directive accomplishes in one sentence.

## When to Use
Trigger conditions — when should Claude load and follow this directive?

## Inputs
- What information/credentials/files are needed before starting

## Process
1. Step-by-step instructions
2. Reference execution scripts by name: `execution/script_name.py`
3. Include decision points: "If X, do Y. If Z, ask for clarification."

## Outputs
- What gets produced and where it goes (Google Sheet, file, API call, etc.)

## Edge Cases
- Known failure modes and how to handle them
- Rate limits, auth expiry, data format issues

## Verification
- [ ] Output matches expected format
- [ ] No errors in execution logs
- [ ] Credentials not exposed in output
- [ ] Results accessible where specified
