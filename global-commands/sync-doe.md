First, check if ~/doe-starter-kit is accessible. If not, run: /add-dir ~/doe-starter-kit

Then read directives/starter-kit-sync.md and follow it precisely. `/sync-doe` is a **two-phase** command:

- **Phase 1** opens a PR with the editorial changes (translated diff, CHANGELOG entry, version bump).
- **Phase 2** runs after the PR merges and does the release machinery (tutorial stamp, tag, GitHub release) on main.

State between phases lives in `~/doe-starter-kit/.tmp/.sync-doe-pending-release.json`.

## Pre-flight (every invocation)

1. **Step 0** — Run `python3 execution/audit_sync.py` to surface universal files missing from the kit
2. **Step 0.5** — `cd ~/doe-starter-kit && git status --porcelain` — if dirty, surface paths and stop
3. **Step 0.7 — Detect pending release.** If `~/doe-starter-kit/.tmp/.sync-doe-pending-release.json` exists, branch on PR state:
   - PR `MERGED` → skip Phase 1, jump straight to **Step 11 (Phase 2)** with version + project from the state file
   - PR `OPEN` → say "PR #N still open: <URL>. Merge it and re-run `/sync-doe` to release." and stop
   - PR `CLOSED` (without merge) → ask user "Discard pending state and start fresh? [y/n]"; on `y`, `rm` the state file and continue to Step 1; on `n`, stop

Conversational shortcut: if the user has just opened a PR in this same session and replies with "merged" / "yes" / "done", verify via `gh pr view` and proceed directly to Step 11.

## Phase 1 — open the PR (Steps 1-10)

For a fresh sync (no state file):

1. Pull latest from GitHub first — another project may have synced since your last pull
2. Diff all syncable files between this project and ~/doe-starter-kit. If nothing has changed, say "Starter kit is up to date — nothing to sync" and stop.
3. Three-way comparison: show what the starter kit has, what this project has, and the diff. Flag any starter kit content that this project doesn't have (it came from another project — preserve it).
4. For files that differ, identify which changes are universal DOE improvements vs project-specific content
5. Strip ALL project-specific content (names, paths, data, examples) and replace with generic equivalents
6. Create a safety backup (`git stash`) before writing anything
7. Apply changes surgically — merge improvements in, never replace whole files
8. Show me the exact edits before applying — wait for my approval
9. Verify: `grep` for project-specific references — must return zero results
10. Update CHANGELOG.md with what changed, bump the version (patch/minor/major). Author a migration manifest at `migrations/v[X.Y.Z].md` if the release rewrites prompts/rules or changes hook/permission behaviour (see directive Step 9.5).
11. **Open the PR (Phase 1 commit + push):**
    - Branch: `cd ~/doe-starter-kit && git checkout -b sync-from-[project]-[YYYY-MM-DD-HHMM]`
    - Commit: `SKIP_STEP_MARK_CHECK=1 git commit -m "sync: from [project] — [summary]"`
    - Push: `git push -u origin sync-from-[project]-[YYYY-MM-DD-HHMM]`
    - PR: `gh pr create --repo Albion-Labs/doe-starter-kit --title "sync: from [project] — [summary]" --body-file <body>`
    - Write state file: `~/doe-starter-kit/.tmp/.sync-doe-pending-release.json` with `{version, prNumber, prUrl, branch, project, timestamp, phase: "awaiting-merge"}`
    - `git checkout main` (clean working tree)
    - Show user: "PR #N opened: <URL>. Review and merge it on GitHub. Reply 'merged' (or re-run `/sync-doe`) to release."
    - **STOP here.** No tag, no stamp, no release in Phase 1.

## Phase 2 — release after merge (Step 11, gated on PR state)

Routed here from Step 0.7 when the state file is present and `gh pr view` reports `MERGED`.

12. **Verify PR merged**, pull main, stamp + commit + tag + push + release:
    - `cd ~/doe-starter-kit && git checkout main && git pull origin main`
    - `python3 execution/generate_whats_new.py`
    - `python3 execution/stamp_tutorial_version.py v[X.Y.Z]`
    - `SKIP_MAIN_PROTECTION=1 SKIP_STEP_MARK_CHECK=1 git commit -am "chore(stamp): v[X.Y.Z]"`
    - `git tag v[X.Y.Z]`
    - `git push origin v[X.Y.Z]` (tag first — pre-push docs-version gate gotcha; see directive)
    - `SKIP_MAIN_PROTECTION=1 git push` (then commit — gate now sees matching tag + docs)
    - `gh release create v[X.Y.Z] --repo Albion-Labs/doe-starter-kit --title "..." --notes "..."`
    - `rm ~/doe-starter-kit/.tmp/.sync-doe-pending-release.json`
    - Update STATE.md's "DOE Starter Kit" line to the new version
    - Show user: "Released v[X.Y.Z]."

`SKIP_MAIN_PROTECTION=1` is required only on the **post-merge stamp commit**, not the editorial PR (which goes through normal review). The bypass scope is narrower than the pre-Phase-2 design.

To pull kit updates INTO this project (reverse direction), use `/pull-doe`.

Rules:
- NEVER replace a file wholesale. Merge additively — add new content, update changed content, preserve existing starter kit content.
- If the starter kit has something this project doesn't, keep it. It came from another project.
- Only sync universal DOE improvements. Never sync project-specific tasks, data, plans, or domain content.
- If unsure whether something is universal or project-specific, ask me.
- Show diffs before writing. Don't commit without my sign-off.
- If `directives/starter-kit-sync.md` doesn't exist, tell me — the starter kit may not be set up yet.
- Version bumps: patch for fixes/tweaks, minor for new commands/directives/features, major for breaking CLAUDE.md or structure changes.
- **Only one pending release at a time.** If the state file exists with an unmerged PR, do not start a new sync — Phase 2 must complete first.

## Analysis Box (REQUIRED before Phase 1 changes)

After diffing all syncable files, present the analysis in a bordered box BEFORE proposing any changes. This is the decision-support summary the user reads to approve or reject. **Generate programmatically** — compute W from content, define a `line(content)` helper: `f"│  {content}".ljust(W + 1) + "│"`. ALL rows including headers MUST use this helper — never construct `f"│{...}│"` manually. For headers with right-aligned text: build the inner content string first (e.g. `f"{left}{right:>{W - 2 - len(left)}}"`) then pass through `line()`. Unicode box-drawing borders. Content inside borders must be ASCII-only.

Structure:
- **Header row:** "UPDATES TO DOE" left-aligned, current kit version (from `git describe --tags` in `~/doe-starter-kit`) right-aligned, with `├─┤` separator below
- **Summary:** 2-3 lines of context about what was compared and the state of the diffs
- **Numbered list:** One entry per file that differs, with a short explanation of whether the diff is universal or project-specific
- **VERDICT:** 1-2 lines — are there universal changes worth syncing?
- **RECOMMENDATION:** 1-2 lines — merge, skip, or ask for clarification

```
┌──────────────────────────────────────────────────────────────────────┐
│  UPDATES TO DOE                                             vX.Y.Z  │
├──────────────────────────────────────────────────────────────────────┤
│  [2-3 line summary of what was compared]                            │
│                                                                     │
│  1. [file] -- [universal/project-specific] ([detail])               │
│  2. [file] -- [universal/project-specific] ([detail])               │
│                                                                     │
│  VERDICT                                                            │
│                                                                     │
│  [Assessment of whether changes are worth syncing]                  │
│                                                                     │
│  RECOMMENDATION                                                     │
│                                                                     │
│  [Merge / skip / ask user about specific items]                     │
└──────────────────────────────────────────────────────────────────────┘
```

If the user approves, proceed with Phase 1. If not, skip to the Result Summary.

## Result Summary (REQUIRED at end of every invocation)

After completing all steps — or when stopping early — ALWAYS end with this bordered result box. Pick the matching status. **Generate boxes programmatically** per the rules in the Analysis Box section.

**Phase 1 complete — PR opened, awaiting merge:**
```
🟡 PR OPENED
┌──────────────────────────────────────────────────────┐
│  SYNC RESULT                                         │
├──────────────────────────────────────────────────────┤
│  PR #N opened: <URL>                                 │
│  Reply 'merged' (or re-run /sync-doe) to release.    │
│  Kit: vX.Y.Z (unchanged until Phase 2)              │
└──────────────────────────────────────────────────────┘
```

**Phase 2 complete — released from a pending state:**
```
✅ RELEASED
┌──────────────────────────────────────────────────────┐
│  SYNC RESULT                                         │
├──────────────────────────────────────────────────────┤
│  [1-2 line summary of what was released]             │
│  Kit: vX.Y.Z -> vX.Y.Z                              │
└──────────────────────────────────────────────────────┘
```

**Pending PR not yet merged (resume mode hit OPEN):**
```
🟡 AWAITING MERGE
┌──────────────────────────────────────────────────────┐
│  SYNC RESULT                                         │
├──────────────────────────────────────────────────────┤
│  PR #N still open: <URL>                             │
│  Merge it on GitHub then re-run /sync-doe.          │
│  Kit: vX.Y.Z (unchanged)                            │
└──────────────────────────────────────────────────────┘
```

**Pending PR closed without merge:**
```
❌ PR CLOSED
┌──────────────────────────────────────────────────────┐
│  SYNC RESULT                                         │
├──────────────────────────────────────────────────────┤
│  PR #N closed without merging.                       │
│  State discarded; ready for fresh sync.              │
│  Kit: vX.Y.Z (unchanged)                            │
└──────────────────────────────────────────────────────┘
```

**Nothing to sync:**
```
⏭️  NO CHANGES
┌──────────────────────────────────────────────────────┐
│  SYNC RESULT                                         │
├──────────────────────────────────────────────────────┤
│  [1-2 line explanation]                              │
│  Kit: vX.Y.Z (unchanged)                            │
└──────────────────────────────────────────────────────┘
```

**User declined proposed changes:**
```
❌ REJECTED
┌──────────────────────────────────────────────────────┐
│  SYNC RESULT                                         │
├──────────────────────────────────────────────────────┤
│  [What was proposed and why it was declined]         │
│  Kit: vX.Y.Z (unchanged)                            │
└──────────────────────────────────────────────────────┘
```

**Blocked by an issue:**
```
⚠️  BLOCKED
┌──────────────────────────────────────────────────────┐
│  SYNC RESULT                                         │
├──────────────────────────────────────────────────────┤
│  [What went wrong -- e.g. conflicts, missing dir]   │
│  Kit: vX.Y.Z (unchanged)                            │
└──────────────────────────────────────────────────────┘
```

Adapt box width to fit the longest content line. Pad all lines so the right border aligns.
