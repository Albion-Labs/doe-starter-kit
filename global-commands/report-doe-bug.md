Report a bug in the DOE framework. This command acts as a triage-first system: it gathers context, checks if the issue is already fixed, detects user error, searches for duplicates, and only files a GitHub Issue if it's a genuine new bug.

## Phase 1: Gather

**User's account:** Ask the user to describe what went wrong. If $ARGUMENTS was provided, use that as the initial description. Otherwise ask: "What were you trying to do, and what went wrong?"

**Claude's reconstruction:** From the current conversation context, reconstruct:
- What command or script was being used when the issue occurred
- What error messages or unexpected behaviour appeared
- What was attempted to fix it (if anything)
- The sequence of events leading to the problem

If there's no relevant conversation context (user is reporting from memory), note that and rely more heavily on the user's account.

**Environment capture:** Run the execution script to gather system info:

```bash
python3 execution/doe_bug_report.py --environment
```

Parse the JSON output and note the DOE version, OS, Node, Python.

**Severity:** Ask the user: "How much did this block you? (a) Completely blocked -- couldn't continue, (b) Found a workaround but it was painful, (c) Minor annoyance / cosmetic issue"

Map to labels: a = `severity:blocking`, b = `severity:workaround`, c = `severity:cosmetic`.

**Reproducibility:** Ask: "Does this happen every time you try, or was it a one-off?"

## Phase 2: Gate — Version Check

Run the version check:

```bash
python3 execution/doe_bug_report.py --version-check
```

Parse the JSON output. If `is_behind` is true:
- Read the `changelog_entries` to see if any mention keywords related to the user's bug
- If a fix is found: tell the user "This looks like it was fixed in vX.Y.Z. Run `/pull-doe` to update your DOE kit." Show the relevant changelog entry. **Stop here — do not file an issue.**
- If no relevant fix found in the changelog: continue to Phase 3 (the user may be behind but this is a different bug)

If `is_behind` is false or there's an error fetching the upstream version: continue to Phase 3.

## Phase 3: Gate — User Error Detection

This is a judgment call. Based on the user's description and Claude's reconstruction, assess whether this is:
- **A DOE framework bug** — something in the DOE kit itself is broken (a command, hook, script, or directive behaves incorrectly)
- **A usage mistake** — the user is using DOE correctly but misunderstands a feature, or their project code has an issue

Signs of user error: the error is in their project code (not in `execution/`, `global-commands/`, `.githooks/`, or `.claude/hooks/`), they're using a command with wrong arguments, their project config is missing required fields.

Signs of a framework bug: a DOE command crashes or produces wrong output, a hook blocks valid actions, an execution script fails on valid input, documentation is wrong or misleading.

If you assess this as user error:
1. Explain what went wrong and how to fix it
2. Scan tutorials for relevant documentation:

```bash
python3 execution/doe_bug_report.py --scan-tutorials "<relevant keywords>"
```

3. Present the top tutorial matches: "For more on this, check the DOE tutorial: [page] > [section]"
4. **Stop here — do not file an issue.**

If uncertain, err on the side of filing — false positives are better than lost bug reports.

## Phase 4: Gate — Duplicate Search

Search for existing issues that might match:

```bash
python3 execution/doe_bug_report.py --search-duplicates "<keywords from the bug description>"
```

If matches are found:
- Present each match to the user: "This looks similar to issue #N: [title]. Is this the same problem?"
- If the user confirms it's the same: offer to add their context as a comment using `--add-comment`
- If the user says it's different: continue to Phase 5

If no matches or search fails: continue to Phase 5.

## Phase 5: Draft, Sanitise, and File

**Assemble the draft issue:**

Title: A concise summary of the bug (under 80 chars). Format: "[component] brief description" — e.g. "[/snagging] crashes when no manual items exist" or "[health_check.py] returns invalid JSON on empty project"

Body: Use this structure:
```
## Summary
[2-3 sentence description combining user's account and Claude's reconstruction]

## Environment
| Field | Value |
|-------|-------|
| DOE Kit Version | [from --environment] |
| OS | [os + version] |
| Node | [version] |
| Python | [version] |
| Shell | [shell] |

## Steps to Reproduce
[Numbered list of steps to reproduce the issue]

## Expected vs Actual
**Expected:** [what should have happened]
**Actual:** [what actually happened]

## Claude's Analysis
[Claude's reconstruction of what went wrong technically — which component failed and why]

## User's Description
[The user's own words about the problem — verbatim or lightly edited for clarity]

## Severity
[blocking / workaround / cosmetic]

## Reproducibility
[every time / intermittent / one-off]

---
*Filed via `/report-doe-bug` from DOE Kit [version]*
```

**Sanitise the draft:**

```bash
python3 execution/doe_bug_report.py --sanitise "<full draft body>"
```

This strips API keys, secrets, absolute paths, and email addresses. Review the sanitised output — if it removed something that was actually needed for the bug report (e.g. a path that's part of the error), add it back in generic form (e.g. `~/project/src/file.js` instead of the absolute path).

**Present to user:** Show the full draft issue (title + sanitised body + labels) and ask: "Does this look right? I can edit it, or you can tell me what to change. Say 'file it' to submit."

**File or fallback:**

If the user approves:

```bash
python3 execution/doe_bug_report.py --file-issue "<title>" "<sanitised body>" "bug,user-reported,<version>,<severity>"
```

Parse the result:
- If `filed` is true: "Bug report filed: [issue_url]. You'll get updates via GitHub notifications."
- If `fallback_file` is set: "Couldn't reach GitHub. Your bug report has been saved to [fallback_file]. You can file it manually at https://github.com/williamporter/doe-starter-kit/issues/new or email it to the maintainer."

## Behavioural Rules

- **Sanitise aggressively.** The upstream repo is public. Never include API keys, .env values, project-specific source code, or identifiable paths. When in doubt, redact.
- **Neutral tone.** Don't blame the user or the framework. Present facts.
- **Don't file unless all gates pass.** The goal is quality over quantity — one well-documented bug report is worth ten vague ones.
- **Respect the user's time.** Move through phases efficiently. Don't ask unnecessary questions. If the conversation already contains the answers, use them.
- **Be transparent about limitations.** If you can't determine whether something is a framework bug or user error, say so and let the user decide.
