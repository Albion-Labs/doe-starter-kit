# Infrastructure & Maintenance Commands

These commands handle the plumbing — keeping the framework updated, checking what's installed, and managing the connection between your project and the DOE Starter Kit it was built from.

---

## /pull-doe

**What it does:** Pulls the latest updates from the DOE Starter Kit into your project.

**When to use it:** When the starter kit has been updated (new commands, bug fixes, improved hooks) and you want those improvements in your project.

**How it works:**

1. Checks the current starter kit version your project is using.
2. Checks the latest version available.
3. Shows you what changed between versions (a changelog).
4. Applies the updates safely, without overwriting your project-specific customisations.

**What to expect:**

```
Current version: v1.29.0
Latest version: v1.30.1

Changes in v1.30.1:
  - New: /codemap command for project indexing
  - Fixed: /wrap streak calculation off-by-one
  - Improved: Pre-commit hook now checks for trailing whitespace

Apply update? (y/n)
```

The update is non-destructive. If you've customised a file that the update also changes, you'll be shown the conflict and asked how to resolve it.

---

## /sync-doe

**What it does:** Pushes universal DOE improvements from your project back to the starter kit — the reverse direction of `/pull-doe`.

**When to use it:** When you've made a genuinely universal improvement (a new command, a fixed hook, a better directive) while working in a project and want it to land in the kit so every other project can pull it.

**How it works:** It's a two-phase command. Phase 1 diffs the syncable files between your project and `~/doe-starter-kit`, strips out all project-specific content (names, paths, data, examples), bumps the version, updates the changelog, and opens a PR against `Albion-Labs/doe-starter-kit` for review. Phase 2 runs after that PR merges and does the release machinery on `main` — stamps the tutorial docs, tags the version, and cuts the GitHub release.

**What to expect:** Before anything is written, it presents an analysis box summarising which file diffs are universal vs project-specific and a recommendation. Nothing is committed without your sign-off. Once approved, it opens the PR and stops; re-run `/sync-doe` (or reply "merged") after merging to trigger the release.

Use `/pull-doe` to pull kit updates the other way — into your project.

---

## /commands

**What it does:** Shows all available slash commands, their status, and version information.

**When to use it:** When you want to see what commands are available, check if something is installed correctly, or troubleshoot a missing command.

**How it works:** Scans the `.claude/commands/` directory and checks each command file against expected conventions: does it exist, is it properly formatted, is it the latest version?

**What to expect:**

```
┌─ Commands ──────────────────────────────────┐
│ Session                                      │
│   /stand-up       ✓ installed                │
│   /crack-on       ✓ installed                │
│   /sitrep         ✓ installed                │
│   /wrap           ✓ installed                │
│   /eod            ✓ installed                │
│                                              │
│ Quality                                      │
│   /audit          ✓ installed                │
│   /fact-check     ✓ installed                │
│   /review         ✓ installed                │
│   /agent-verify   ✓ installed                │
│   /test-suite     ✓ installed                │
│   /codemap        ✓ installed                │
│                                              │
│ Visual                                       │
│   /project-recap  ✓ installed                │
│   /diff-review    ✓ installed                │
│   ...                                        │
│                                              │
│ Framework: DOE Starter Kit v1.30.1           │
│ All commands operational.                    │
└──────────────────────────────────────────────┘
```

If a command is missing or broken, the output will tell you what's wrong and how to fix it (usually a `/pull-doe` will resolve it).

---

## /hq

**What it does:** Shows a project dashboard — a bird's-eye view of session history, feature timelines, and metrics across your projects and over time.

**When to use it:** When you want the big picture. How many sessions have you run? What features have you shipped? What's your commit velocity? This is the "zoom all the way out" view.

**What to expect:**

```
┌─ HQ Dashboard ──────────────────────────────┐
│                                              │
│ Project: my-project                          │
│ Sessions: 117 total, 12-day streak           │
│ Features shipped: 14                         │
│ Current: Targeting Page v2 (90%)             │
│                                              │
│ This week:                                   │
│   Mon ████████ 4 sessions, 12 commits        │
│   Tue ██████   3 sessions, 8 commits         │
│   Wed ████     2 sessions, 5 commits         │
│                                              │
│ Recent features:                             │
│   Targeting Page v2    ██████████░ 90%        │
│   Home Page Rebuild    ████████████ Done      │
│   Data Pipeline v3     ████████████ Done      │
│                                              │
│ All-time: 117 sessions, 847 commits          │
│           +34,291 / -12,847 lines            │
└──────────────────────────────────────────────┘
```

This is a read-only, feel-good command. It doesn't change anything — it just shows you what you've built. Useful for motivation, for reporting to others, or for spotting trends (are sessions getting shorter? are you shipping more per session?).

---

## /report-doe-bug

**What it does:** Reports a bug in the DOE framework itself — a command, hook, script, or directive that behaves incorrectly.

**When to use it:** When something in the kit (not your own project code) is broken or misbehaving and you want it tracked and fixed.

**How it works:** It's triage-first. It gathers context (your account plus a reconstruction from the conversation), captures the environment, then runs a series of gates: a version check (is this already fixed in a newer kit version?), a user-error check (is this actually a usage mistake rather than a framework bug?), and a duplicate search against existing issues. Only if all gates pass does it draft, sanitise, and file a GitHub issue on `Albion-Labs/doe-starter-kit`.

**What to expect:** A short back-and-forth — project type, severity, reproducibility — followed by bordered cards for the environment, each gate result, and a draft issue. Output is sanitised aggressively (keys, secrets, paths, emails stripped) because the repo is shared. Nothing is filed without your approval.

---

## /request-doe-feature

**What it does:** Files a feature request for the DOE starter kit as a GitHub issue.

**When to use it:** When you want a new capability in the kit — a command, a directive, a hook, a docs improvement — and want it captured for the maintainers.

**How it works:** A short conversational flow: what you'd like (the spark), the current workaround (the pain), and what using it would look like (the picture). It then silently scans for overlapping existing features and duplicate issues, categorises the request for labelling, and sanitises your input before drafting.

**What to expect:** A bordered draft box summarising the problem, current workaround, desired outcome, and any overlap detected, with suggested labels. On your approval it files the issue on `Albion-Labs/doe-starter-kit`; if GitHub is unreachable it falls back to a local file and tells you where it saved.

---

## When to Use These Commands

| Situation | Command |
|-----------|---------|
| "Is my framework up to date?" | `/pull-doe` |
| "Push my kit improvement back to the kit" | `/sync-doe` |
| "What commands do I have?" | `/commands` |
| "Show me the big picture" | `/hq` |
| "Something in the kit is broken" | `/report-doe-bug` |
| "I want a new kit feature" | `/request-doe-feature` |

These are maintenance commands — you won't use them every session. `/commands` is useful when getting started. `/pull-doe` is worth running every week or two, and `/sync-doe` when you've made a universal improvement worth sharing back. `/report-doe-bug` and `/request-doe-feature` are for when the kit itself needs fixing or extending. `/hq` whenever you want perspective.
