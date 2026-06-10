Before ending this session, complete all steps in order.

## Step 0a: Worktree handling (v1.63.0+)

Run `git worktree list --porcelain` and count records (lines starting with `worktree `).

**Single-worktree project (1 record):** Skip this whole step; the convention's drift surface doesn't exist when there's nothing to drift between.

**Multi-worktree project (2+ records):**

1. **Branch drift check.** Read `.tmp/.session-start-branch` (written by `/crack-on` at session kick-off; see `/crack-on` for the exact mechanism). Compare against the current branch (`git branch --show-current`). If they differ, this is **branch drift** — somewhere mid-session your HEAD moved to a branch you didn't start on. This is the exact race the worktree convention is designed to surface. Report:
   - The branch you started on
   - The branch you're on now
   - Which worktree path each lives in (parsed from `git worktree list --porcelain`)

   Do not silently continue. Ask the user whether to wrap on the current branch (drift accepted), switch back to the session-start branch, or investigate the divergence first. If `.tmp/.session-start-branch` does not exist (pre-v1.63.0 session, or a session started via `/stand-up` kick-off only — its session-start-branch write was added at v1.63.0), skip the drift check and note the gap.

2. **Trunk-worktree switch for wrap commits.** Identify the **trunk worktree** — the worktree whose branch matches the repo's default branch, parsed via `git symbolic-ref refs/remotes/origin/HEAD` (works for repos with `main` or legacy `master` as default). Wrap-only bookkeeping commits (STATE.md update, stats.json snapshot, session JSON under `docs/wraps/`) belong in the trunk worktree so `main` always reflects the latest session's bookkeeping — even when feature work is not yet merged.

   Sequence when currently in a non-trunk (sibling) worktree:
   - Commit any actual feature work first (uncommitted edits to feature files in the sibling worktree), pushing to the feature branch per the existing Step 0 rules below.
   - Then `cd <trunk-worktree-path>` and run the bookkeeping portion of /wrap (Steps 1-end) from the trunk worktree.

   Sequence when currently in the trunk worktree: proceed as today — no switch needed.

   Honest scope reminder: the trunk-worktree switch fixes the **branch-level** race (wrap commits land on main, anchored at the trunk worktree). The remaining **file-level** race surfaces when two parallel sessions both edit STATE.md at the same time — the second wrap commit hits a merge conflict at push. Shared docs (STATE.md, todo.md, learnings.md, CLAUDE.md) still need single-terminal coordination at the file level even when the branch is locked down.

## Step 0: Branch handling

Run `git branch --show-current` to check the current branch.

**On main:** Skip to Step 1.

**On a feature branch:**
1. Check if the branch's PR has been merged: `gh pr list --state merged --head $(git branch --show-current) --json number,title 2>/dev/null`
2. If the PR is merged: switch to main, pull latest, and delete the local feature branch:
   ```bash
   git checkout main && git pull && git branch -d <feature-branch-name>
   ```
3. If the PR is NOT merged but the feature is complete (all steps `[x]` in todo.md): warn "Feature complete but PR not yet merged. Run `/snagging` to verify, then merge before wrapping."
4. If mid-feature (incomplete steps remain): stay on the feature branch. Wrap data (STATE.md, stats.json) commits directly to the feature branch -- no separate housekeeping branch, no PR. This is normal: mid-feature sessions just push to the branch. The PR is created at retro (the final step), not before.

## Step 1: Housekeeping

1. **Update STATE.md** — Write the current position, any decisions made, blockers found, and a 1-2 sentence summary under Last Session.
2. **Update tasks/todo.md** — Make sure all completed steps have timestamps. Move any completed features to Done if needed.
3. **Check for learnings** — If anything failed and was fixed, or a useful pattern was discovered, log it to learnings.md or ~/.claude/CLAUDE.md.
4. **Commit and push** — Make sure all work is committed and pushed. Run `git status` to check for uncommitted changes, commit them if any, then `git push` to sync with remote. No uncommitted or unpushed changes should remain.
4b. **Check pull request state** — Run `gh pr list --state open --json number,title 2>/dev/null` to check for open PRs. Record the branch name and open PR count for the checks section. Do NOT suggest creating a PR if mid-feature -- PRs are created at retro only.
5. **Clean up session timer** — Run `rm -f .tmp/.session-start` to delete the session timer file.
6. **DOE Kit sync check** — If `~/doe-starter-kit` exists:
   - **Version check:** Run `cd ~/doe-starter-kit && git describe --tags --abbrev=0` to get the kit version. Compare against STATE.md's "DOE Starter Kit" version. If kit is newer, flag `* pull` for `/pull-doe`. If versions match, record as `synced`.
   - **Kit dirty-tree check (v1.60.0+):** Run `cd ~/doe-starter-kit && git status --porcelain 2>/dev/null` to check for uncommitted changes in the kit working tree. If non-empty, show in the wrap output: `Kit working tree dirty: N path(s) -- path1, path2, ...` (truncate to first 3 paths + `+M more` if N > 3). The dirty state could be intentional (active kit feature branch) or accidental (cross-project edits that the v1.60.0 PR-only model no longer blocks at PreToolUse time). Advisory only -- the user decides whether to investigate. Record count in doeKit data (e.g. `"dirtyPaths": 3`). This is the end-of-session detection point for the v1.60.0 model's residual exposure.
   - **Session-specific syncable file check:** Identify files committed THIS session (since `.tmp/.session-start` or the first session commit) that are kit-syncable: `.githooks/*`, `.claude/hooks/*.py`, `~/.claude/commands/*.md`. If any were modified this session, show a one-line reminder in the wrap output: `Kit-syncable files modified this session: [list]. Run /sync-doe?` This only fires when you actually touched syncable files, not for pre-existing customisations.
   - **Sync gap + drift check:** Run `python3 execution/audit_sync.py --json 2>/dev/null` and read three counts. (a) `missing_from_kit` > 0 → `Sync gap: N universal file(s) not in kit. Run /sync-doe.` (b) `diverged` > 0 → **only warn if the version check above recorded `synced`** (i.e. the project is on the current kit version). When the project is BEHIND (`* pull` flagged), `diverged` is dominated by pull-lag, not real forks — suppress the drift warning and let the pull prompt stand. When synced, show `Kit drift: N file(s) differ from the kit and are not declared. Sync back via /sync-doe, or declare intentional forks in .doe-overrides.` (c) `declared_overrides` is informational only — do not warn on it. Record counts in doeKit data (e.g. `"syncGap": 3, "drift": 2, "overrides": 1`); when suppressed because behind, record `"drift": null` or omit. If the script doesn't exist or fails, skip silently. These checks (inbound version/pull + outbound sync/drift) run for EVERY project — there is no consumer/creator distinction; release authority lives in the kit repo's CODEOWNERS + branch protection, not a per-project flag.
   - **Global tools freshness (v1.68.0+):** Run `python3 ~/.claude/scripts/check_tools_version.py`. The script is silent when your installed global tools are current; if it prints a line, surface that line verbatim in the wrap output. It means the global tools (`~/.claude/scripts`, `~/.claude/commands`) the kit installed on this machine are behind the latest kit release — the line includes the one-command fix (`bash <kit>/setup.sh --tools-only`). If the script is absent (older install) or prints nothing, skip silently. This is the end-of-session half of the same check the SessionStart hook runs at the start.
   - Record result for the System Checks section (e.g. `"doeKit": {"version": "v1.36.1", "synced": true}` or `"doeKit": {"version": "v1.36.1", "synced": false, "action": "pull"}`).
7. **Health check** — Run `python3 execution/health_check.py --quick` (universal checks only). Record pass/warn/fail counts. If the test suite has entries (`tests/suite.json` is non-empty), also run `python3 execution/verify.py --regression` and record results. Include both in the System Checks section (e.g. `"health": {"pass": 5, "warn": 1, "fail": 0}, "regression": {"total": 23, "passed": 23, "failed": 0}`).
8. **Quick audit** — Run `python3 execution/audit_claims.py --hook` (fast checks only). Record the PASS/WARN/FAIL counts for the System Checks section. If any FAIL items exist, fix them before proceeding. WARN items can be noted and left for the next session.
9. **Structural change check** — Run `git diff --name-status HEAD~$(git rev-list --count HEAD --since="$(cat .tmp/.session-start 2>/dev/null || echo '1 hour ago')") 2>/dev/null` to detect new/moved/deleted files this session. If structural changes are found (files added, renamed, or deleted — not just modified), ask: "Structural changes detected — run /codemap to update the project index?" Only run `/codemap` if the user says yes.

## Step 2: Compute Session Stats

Find the first commit of this session: look at `git log --oneline` and identify where your work started (after the last "Update session stats" or "wrap" commit, or use the session start time from `.tmp/.session-start`).

Read `.tmp/.session-start` for the session start ISO timestamp. If it doesn't exist, omit `--session-start` from the `wrap_stats.py` invocation and set `sessionDuration` to `"N/A"` in the wrap JSON. Do NOT substitute the first commit time as a proxy session-start and do NOT add explanatory prose to `sessionDuration` (e.g. "session timer not started -- duration based on first commit") -- the field reads as `"N/A"` so the renderer shows a clean N/A in the Duration metric card.

Run the stats script:
```bash
python3 execution/wrap_stats.py \
  --since <first-session-commit-hash> \
  --session-start <ISO-timestamp-from-.tmp/.session-start> \
  --todo tasks/todo.md \
  --stats .claude/stats.json
```

This script gathers git metrics, computes streak, updates stats.json (v2), and outputs JSON to stdout.

Parse the JSON output. The key fields:

```
result.metrics      → commits, linesAdded, linesRemoved, filesTouched,
                      stepsCompleted, sessionDuration, prsMerged, commitLog
result.streak       → current streak day count
result.stats        → the full updated stats.json
```

After composing your session summary (a plain English sentence of what was done), update stats.json to add it to the most recent session entry before committing:

```bash
python3 -c "
import json
with open('.claude/stats.json') as f: data = json.load(f)
if data.get('recentSessions'):
    data['recentSessions'][0]['summary'] = '<YOUR_SUMMARY_HERE>'
    with open('.claude/stats.json', 'w') as f: json.dump(data, f, indent=2)
"
```

Do this BEFORE committing stats.json.

Commit stats.json with message: "Update session stats" and push.

Register this project in the global project registry (for `/archive-global`).
**Worktree-aware:** a DOE worktree lives at `<project>/.claude/worktrees/<name>`. Attribute the session to the **parent project**, not the worktree, so worktree work rolls up under one project in the dashboard instead of fragmenting into a separate `<name>` entry. (Combined with Step 0a's trunk-worktree switch, which already routes wrap bookkeeping to the trunk, this keeps the registry correct even when that switch is skipped.)
```bash
python3 -c "
import json
from pathlib import Path
from datetime import datetime
reg = Path.home() / '.claude' / 'project-registry.json'
data = json.loads(reg.read_text()) if reg.exists() else {'projects': []}
root = str(Path.cwd().resolve())
marker = '/.claude/worktrees/'
if marker in root:
    root = root.split(marker)[0]  # roll a worktree session up to its parent project
existing = next((p for p in data['projects'] if p.get('path') == root), {})
data['projects'] = [p for p in data['projects'] if p.get('path') != root]
existing.update({'path': root, 'name': Path(root).name, 'lastUpdated': datetime.now().strftime('%Y-%m-%d')})
data['projects'].append(existing)
reg.write_text(json.dumps(data, indent=2))
"
```

## Step 3: Generate HTML Wrap-Up

Build the wrap-up as an HTML page using `~/.claude/scripts/wrap_html.py`. This renders beautifully in the browser instead of fighting terminal formatting.

### 3a: Compose the wrap-up data

Using the stats JSON from Step 2, compose a JSON object with this schema. You must write the content (title, summary, breakdowns, vibe) yourself based on what happened this session:

```json
{
  "projectName": "PROJECT_DIR_NAME_UPPERCASED",
  "episode": result.stats.lifetime.totalSessions,
  "title": "Short Descriptive Title",
  "summary": "One plain English sentence summarising the session. What happened, in a way anyone would understand.",
  "breakdowns": [
    {"heading": "Area of work", "bullets": ["What was done", "Another thing done"]},
    {"heading": "Another area", "bullets": ["What changed"]}
  ],
  "vibe": {"emoji": "EMOJI", "text": "Vibe description"},
  "metrics": {
    "commits": N,
    "linesAdded": N,
    "linesRemoved": N,
    "filesTouched": N,
    "stepsCompleted": N,
    "sessionDuration": "Xh Ym",
    "prsMerged": N,
    "commitLog": [
      {"hash": "abc1234", "time": "HH:MM", "message": "Commit message", "type": "normal|fix|test"}
    ]
  },
  "commitGroups": [
    {"name": "Feature/task name", "commits": ["hash1", "hash2"]},
    {"name": "Housekeeping", "commits": ["hash3"]}
  ],
  "todaySessions": [
    {"number": 76, "duration": "1h 9m", "summary": "Plain English what was done"}
  ],
  "timeline": [
    {"time": "HH:MM", "desc": "Session started", "dur": "", "type": "start"},
    {"time": "HH:MM", "desc": "What happened", "dur": "Nm", "type": "normal|major|fix"}
  ],
  "decisions": [
    {"title": "Short decision title", "problem": "What the problem was", "solution": "What was decided and why"}
  ],
  "learnings": [
    {"title": "Short learning title", "problem": "What went wrong or was discovered", "solution": "What changed as a result"}
  ],
  "checks": {
    "audit": {"pass": N, "warn": N, "fail": N, "details": ["detail string if warn/fail"]},
    "doeKit": {"version": "vX.Y.Z", "synced": true|false},
    "pullRequests": {"open": N, "merged": N, "branch": "current-branch-name"}
  },
  "awaitingSignOff": [
    {
      "feature": "Feature Name [APP] (vX.Y.Z)",
      "summary": "One-line description of what needs testing",
      "manualItems": N,
      "groups": [
        {"name": "Group Name", "items": ["Manual check description", "..."]},
        {"name": "Another Group", "items": ["..."]}
      ]
    }
  ],
  "footer": {
    "session": N,
    "streak": N,
    "lifetimeCommits": N
  },
  "nextUp": "What to do next session -- pull from todo.md"
}
```

**awaitingSignOff**: Parse `## Awaiting Sign-off` in todo.md. For each feature heading (`###`), collect all unchecked `[ ] [manual]` lines. Also check `## Current` for unchecked `[manual]` items on completed steps (steps marked `[x]` but with `[ ] [manual]` items). Group related items by theme (e.g. "Modal & Navigation", "Responsive", "Data Validation") -- use your judgment to create 2-5 groups per feature based on what the checks are testing. Each entry has: `feature` (heading text), `summary` (one-line description of what needs testing overall), `manualItems` (total count), `checklistPath` (path to the test checklist HTML if `docs/{feature-slug}-manual-tests.html` exists, otherwise null), and `groups` (array of `{name, items}` where items are the check descriptions stripped of `- [ ] [manual]` prefix). Cards render as collapsible -- the summary and count are always visible, groups expand on click. When `checklistPath` is non-null, show a "Open test checklist" link pointing to the file. If the section is empty or has no features, use an empty array `[]` -- the renderer omits the section.

**commitGroups**: Group commits by feature or task. Use feature names from todo.md where possible. Commits that don't belong to a feature go in "Housekeeping" or "Other". Every commit in commitLog must appear in exactly one group.

**todaySessions**: Pull from stats.json recentSessions, filtering to today's date. Each entry needs a `number`, `duration`, and `summary` field. For the CURRENT session, write the summary yourself based on what you did. For previous sessions today that lack a summary, derive one from their commit messages in git log.

**decisions**: Each decision uses `title` (short label), `problem` (what was going wrong), and `solution` (what was decided and why). Renders as Problem:/Solution: under the title. Example: `{"title": "Batch manual verification at feature end", "problem": "Per-step manual approval was blocking autonomous building and killing throughput", "solution": "Accumulate manual checks and present as a single checklist at feature completion. Auto-verified steps proceed without waiting."}`

**learnings**: Each learning uses `title` (short label), `problem` (what went wrong or was discovered), and `solution` (what changed as a result). Renders as Discovery:/Change: under the title. Example: `{"title": "Contract patterns are planning-time guesses", "problem": "Wrote contains pcon= in the contract but actual code used pcon: with a colon — the = only appeared at runtime via buildHash()", "solution": "Now verify contract Verify: patterns match actual code before marking done. Quick fix, not a process problem."}`

### 3b: Vibe selection

Pick the vibe based on what happened:
- Smooth session, no failures, 5+ commits: `{"emoji": "😎", "text": "Smooth sailing"}`
- Clean but small session: `{"emoji": "😌", "text": "Clean & quiet"}`
- Had failures but recovered: `{"emoji": "💪", "text": "Hard-fought win"}`
- Had failures, messy: `{"emoji": "🫠", "text": "We got there eventually"}`
- Single quick fix: `{"emoji": "🩹", "text": "Quick patch"}`
- Massive output (1000+ lines): `{"emoji": "🏭", "text": "Factory floor"}`
- Mostly docs/config changes: `{"emoji": "🧹", "text": "Housekeeping"}`

### 3c: Timeline construction

Build the timeline from `result.metrics.commitLog`:
- First entry: session start time from `.tmp/.session-start`, type "start"
- Each commit: local time, short description (truncate long messages), duration since previous event, type:
  - "major" for feature additions, new files, significant changes
  - "fix" for bug fixes, corrections
  - "normal" for everything else (housekeeping, docs, state updates)
- Group rapid commits (< 1 min apart) into a single timeline entry
- For each timeline entry with a duration, the renderer will automatically calculate and display what percentage of total session time it represents. Include the total session duration in metrics.sessionDuration.

### 3d: Commit classification

For each commit in commitLog, set the type by reading its Conventional Commits prefix (see `directives/git-conventions.md`):
- "test" if the subject starts with `test:` or `test(...)`
- "fix" if the subject starts with `fix:` or `fix(...)` (also `fix!:` / `fix(...)!:` for breaking fixes)
- "feat" if the subject starts with `feat:` or `feat(...)` (also `feat!:` / `feat(...)!:`)
- "chore" if the subject starts with `chore:` or `chore(...)` — covers releases (`chore(release): vX.Y.Z`), dependency bumps, internal cleanup
- "docs" if the subject starts with `docs:` or `docs(...)`
- "normal" for everything else (legacy `vX.Y.Z:` releases, allowlisted Merge/Revert commits, anything pre-Conventional-Commits)

Fallback: if the prefix is unrecognised but the subject literally starts with "Fix " (capital F), classify as "fix" — this preserves classification for legacy commits before the kit adopted Conventional Commits in v1.57.0.

### 3e: Generate and open

Determine the theme based on the current time: run `date +%H` to get the current hour (0-23). If the hour is >= 6 AND < 18, use `--theme light`. Otherwise use `--theme dark` (the default).

Run:
```bash
python3 ~/.claude/scripts/wrap_html.py --json '<the JSON string>' --theme <light|dark> --output .tmp/wrap.html
```

Then save the JSON data permanently for HQ and open the HTML in the browser:
```bash
mkdir -p docs/wraps
python3 -c "import json; open('docs/wraps/session-<SESSION_NUMBER>.json', 'w').write(json.dumps(<THE_JSON_OBJECT>, indent=2))"
open .tmp/wrap.html
```

The `docs/wraps/session-N.json` file is what gets committed. The HTML is generated on demand (by `build_session_archive.py` regenerating it from JSON). The `.tmp/wrap.html` copy is disposable. Commit this file with message "Save session N wrap data" and push.

### 3f: Gist sync (push session to cloud)

After saving the local JSON and committing, push the session data to the Gist for cross-machine access. This is a best-effort step — if it fails, the local wrap still succeeds.

```bash
python3 ~/.claude/scripts/gist_sync.py --push \
  --slug <PROJECT_DIR_NAME_LOWERCASED> \
  --meta '<json with name, path, lifetime, recentSessions from stats.json>' \
  --session '<the full wrap JSON object>'
```

Build the `--meta` JSON from stats.json: `{"name": "<project>", "path": "<cwd>", "lifetime": <stats.lifetime>, "recentSessions": <stats.recentSessions>}`.

**Graceful fallback:** If `gist_sync.py` is not found, or if the push fails (non-zero exit), print a warning: `Gist sync: skipped (reason)` and continue. Never let a Gist failure block the wrap.

Print a one-line summary to the terminal: `Session [N] wrap-up opened in browser. [X] commits, [Y] steps, [duration].`

Then check for open PRs: `gh pr list --state open --json number,title,headRefName 2>/dev/null`. If any exist, print a reminder below the summary: `Open PRs: #N [title] (M manual items pending)` for each. Pull manual item counts from the `awaitingSignOff` data already computed. **Conflict detection:** If 2+ PRs are open, check for file overlaps: run `gh pr view N --json files --jq '.files[].path'` for each PR. If any files appear in multiple PRs, add a warning: `Conflict risk: [overlapping files] -- merge [ready PR] first, then rebase the other`. **Branch staleness:** If on a feature branch, run `git rev-list --count HEAD..origin/main`. If > 0, add: `Branch is N commits behind main -- rebase before merging`. This ensures PRs don't go stale and merge order is clear.

## Important Rules

- Pull ALL numbers from the wrap_stats.py JSON output. Never estimate or make up stats.
- The `summary` is one plain English sentence -- what happened this session in a way anyone would understand. No jargon, no drama.
- The `breakdowns` array groups the session's work into small subheadings (2-4 groups), each with 1-3 bullet points. Name specific features, files, and outcomes. Keep bullets short and scannable.
- Title, summary, and breakdowns MUST reference actual features, real files, and real problems from this session.
- If stats.json doesn't exist yet, this is session 1.
- Commit stats.json BEFORE generating the wrap-up so the push includes it.
- The `decisions` array should list decisions written to STATE.md this session, or `["None this session"]`.
- The `learnings` array should list learnings written to learnings.md or ~/.claude/CLAUDE.md, or `["None this session"]`.
- For `prsMerged`, count PRs merged during this session — a verifiable number, e.g. from the commit log's merge refs or `gh pr list --state merged --search "merged:>=<session-start>"`. Use `0` if none. (Do not self-report a count nothing can verify.)
