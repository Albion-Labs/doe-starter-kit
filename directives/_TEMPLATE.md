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

---

### Optional: Anti-patterns bullet
When a rule in this directive has a recognisable failure mode worth showing, add a bold-labelled bullet inside the relevant section (Process, Edge Cases, wherever it fits). Use when the directive is corrective and the failure modes are easy to spot at a glance. Skip when the directive is descriptive (a routine or process). Existing directives are not required to retrofit.

Format:
- **Anti-patterns:** concrete failure modes this directive prevents.
  - Before: <one-line example of the failure mode>
  - After: <one-line example of the correction>
