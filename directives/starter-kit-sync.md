# Directive: DOE Starter Kit Sync

## Goal
Keep the universal DOE Claude Code Starter Kit repository in sync with improvements made during project work. When a project improves the DOE system itself (new directives, better rules, new commands, workflow refinements), those improvements should flow back to the starter kit — stripped of all project-specific content.

Tradeoff: Sync ceremony costs a CHANGELOG entry, version bump, tag, and release per push in exchange for keeping the kit's history honest -- every project that pulls from the kit gets a clean version landing line. Apply when an [INFRA] feature changed kit-syncable files (CLAUDE.md rules, directives, commands, hooks, audit checks). Skip when: the feature is project-only (CLAUDE.md project sections, project-specific hooks, project content).

## When to Use
- After completing an [INFRA] feature that changed DOE files (CLAUDE.md, todo.md format rules, directives, commands, hooks, audit script)
- After a retro identifies a new universal learning that was added to learnings.md or ~/.claude/CLAUDE.md
- After creating a new directive or command that would benefit other projects
- When explicitly asked to sync

## How to Sync

`/sync-doe` is the project-to-kit translation tooling: it diffs, strips project-specific content, applies surgically, and opens the kit PR. It is not the canonical gate -- that role is held by the kit's `.githooks/pre-commit` 'no direct-to-main' hook plus PR review (see `directives/kit-development.md` ## Kit-write model: PR-only). `/sync-doe` automates the project-side translation step so syncs land cleanly.

### Step 0: Run sync audit (mandatory pre-flight)
Before comparing individual files, run the automated audit to catch universal files that might be missing from the kit:
```bash
python3 execution/audit_sync.py
```
This compares all syncable directories and flags:
- **MISSING FROM KIT** — universal files that should be synced
- **NEEDS STRIPPING** — universal structure with project-specific content (strip before sync)
- **DIVERGED** — files in both repos that differ (examine each)
- **KIT ONLY** — files in kit that the project doesn't have (may need pulling)

**Decision rule for "universal vs project-specific":** A file is universal if the SCRIPT is generic, even if the DATA it processes is project-specific. Examples: `run_snagging.py` reads todo.md (project data) but the script itself works for any DOE project. `build_session_archive.py` is structurally universal but contains hardcoded feature names — it needs stripping. `build.py` is always project-specific. When in doubt, flag it for the user -- the universal/project-specific call is theirs to make.

Review the audit output before proceeding. If MISSING FROM KIT has items, include them in this sync.

### Step 0.5: Verify kit working tree is clean (mandatory pre-flight)

`/sync-doe` translates from project to kit. If the kit working tree has uncommitted changes that did not come from this session, surface them in the Analysis Box and require user acknowledgement before applying anything.

```bash
cd ~/doe-starter-kit && git status --porcelain
```

If the output is non-empty, the sync MUST stop and surface every dirty path with its diff. The user decides whether the changes are intended (continue) or accidental (revert + retry). This is the canonical detection point for the v1.60.0 model's residual exposure: cross-project AI edits to the kit working tree that go silent until the next sync (since `guard_kit_writes` no longer blocks them at PreToolUse time).

### Step 0.7: Detect pending release (resume mode)

`/sync-doe` is a two-phase command: **Phase 1** (Steps 1-10) opens a PR with the editorial changes (translated diff, CHANGELOG, version bump). **Phase 2** (Step 11) does the post-merge release machinery (tutorial stamp, tag, GitHub release) on main. State between phases lives at `~/doe-starter-kit/.tmp/.sync-doe-pending-release.json`.

At the start of every `/sync-doe` invocation (after Step 0.5), check for the state file:

```bash
STATE=~/doe-starter-kit/.tmp/.sync-doe-pending-release.json
if [ -f "$STATE" ]; then
    PR_NUMBER=$(python3 -c "import json; print(json.load(open('$STATE'))['prNumber'])")
    PR_STATE=$(gh pr view $PR_NUMBER --repo Albion-Labs/doe-starter-kit --json state --jq .state 2>/dev/null)
    echo "Pending release detected: PR #$PR_NUMBER (state: $PR_STATE)"
fi
```

Branch on the PR state:

| `gh pr view` state | Action |
|---|---|
| `MERGED` | Skip Steps 1-10 (no new sync). Jump to **Step 11** with the version + project context from the state file. |
| `OPEN` | Tell the user: "PR #N still open: \<URL\>. Merge it on GitHub then re-run `/sync-doe` to release." Stop. Do not start a new Phase 1 — the kit can only have one pending release at a time. |
| `CLOSED` (without merge) | Tell the user: "PR #N was closed without merging. Discard pending state and start a fresh sync? \[y/n\]". On `y`: `rm "$STATE"` and continue normally to Step 1. On `n`: stop. |

If no state file exists, this is a fresh sync — continue to Step 1.

**Conversational shortcut**: from any Claude Code session (the same one that opened the PR, or a different project's session days later), replying with a merge confirmation (e.g., "merged", "yes", "done") routes here just as `/sync-doe` re-invocation does. The state file lives in the kit, accessible from any project. Claude verifies the PR state via `gh` and proceeds to Step 11 if `MERGED`.

### Step 1: Add the starter kit directory
```
/add-dir ~/doe-starter-kit
```

### Step 2: Pull latest from GitHub
Before comparing anything, make sure the local starter kit is up to date. Another project may have synced improvements since you last pulled.
```bash
cd ~/doe-starter-kit && git pull
```
When there are local uncommitted changes, pause and ask the user how to handle them before proceeding.

### Step 3: Check all layers
Compare files across ALL layers — not just two. Every sync must check:

**Layer A — DOE Kit** (`~/doe-starter-kit/global-commands/`, `~/doe-starter-kit/.githooks/`, etc.)
**Layer B — Installed Global** (`~/.claude/commands/`)
**Layer C — Local Project** (`.claude/commands/`, `.githooks/`, `.claude/hooks/`, etc.)

For each syncable file, diff A↔B and A↔C. Report which layers are ahead, behind, or in sync. This catches edits made at any layer (e.g. editing an installed command without syncing back to kit).

Files to compare:
- CLAUDE.md (rules, triggers, directory structure)
- tasks/todo.md (format rules only — not task content)
- directives/*.md (universal ones only)
- execution/audit_claims.py (universal checks only)
- ~/.claude/commands/*.md (global commands — Layer B)
- ~/doe-starter-kit/global-commands/*.md (global commands — Layer A)
- .claude/commands/*.md (local commands — Layer C, if any exist beyond README)
- .githooks/* (hook scripts)
- .claude/hooks/*.py (guardrail hooks)
- SYSTEM-MAP.md (structure documentation)
- .claude/claude-chat-sync-prompt.md

**Commands README check:** Check `~/doe-starter-kit/global-commands/README.md` (the kit's authoritative command index — projects no longer carry their own copy). For every command file that differs across layers, re-read its content and compare against the README description. If the command's behaviour or features changed meaningfully (new card rows, new modes, renamed sections), update the README description. If the change is purely internal (wording tweaks, border fixes, reordering), leave the README as-is. Present README updates alongside other diffs for approval.

If all syncable files are identical across all layers, say "Starter kit is up to date — nothing to sync" and stop.

### Step 4: Three-way comparison
For each file that differs, show THREE things:
1. **What the starter kit currently has** (this may include improvements from other projects)
2. **What this project has** (may include project-specific customizations)
3. **The diff between them**

This prevents silently overwriting improvements synced from other projects. If the starter kit has content that this project doesn't, flag it explicitly:
> "The starter kit has [X] that this project doesn't — this was likely synced from another project. I'll preserve it."

IMPORTANT: Merge improvements additively -- add new rules, update changed rules, and keep existing starter-kit content that the current project doesn't have. Wholesale replacement is reserved for files the kit doesn't yet have.

### Step 5: Strip project-specific content
Before copying anything to the starter kit, remove ALL project-specific references:
- Project names (e.g. "Monty", "Broker Platform")
- Project-specific file paths (e.g. monty-app-v0.12.3.html)
- Project-specific data (constituency names, API endpoints)
- Project-specific audit checks (only `@register("universal")` checks go to starter kit)
- Project-specific directives (only universal SOPs go to starter kit)
- Project-specific governed documents in the registry (only learnings.md stays)

Replace with generic equivalents:
- "Monty" → "[project name]" or remove entirely
- Specific HTML filenames → "your-app.html"
- Project-specific examples → generic examples

### Step 6: Create safety backup
Before writing any changes, create a backup branch so changes can be rolled back:
```bash
cd ~/doe-starter-kit
git stash push -m "Pre-sync backup from [project name] $(date +%Y-%m-%d_%H:%M)"
```
If there's nothing to stash (working tree clean), that's fine — git log is the safety net.

### Step 7: Apply changes
Merge stripped improvements into the starter kit directory. For files that exist in both:
- Apply changes surgically (add/update specific sections, don't replace whole files)
- Preserve any starter-kit-only content (e.g. setup instructions, template comments, improvements from other projects)
- After applying, run `git diff --stat` and `git diff` in the kit repo
- Present the diff summary in a bordered box for approval before proceeding. **Generate programmatically** — compute W from content, use `.ljust(W)` padding, Unicode box-drawing borders. Content inside borders must be ASCII-only.

```
┌──────────────────────────────────────────────────────────────────────┐
│  DIFF SUMMARY                                          N files changed│
├──────────────────────────────────────────────────────────────────────┤
│  1. [file] ([+N/-N]) -- [what changed]                              │
│  2. [file] (NEW) -- [what it is]                                    │
│                                                                     │
│  Net: [summary, e.g. "CLAUDE.md 117 -> 83 lines"]                  │
└──────────────────────────────────────────────────────────────────────┘
```

Wait for explicit user approval before proceeding to Step 8.

### Step 8: Verify
```bash
# Zero project-specific references
grep -ri "monty\|broker\|pleasantly" ~/doe-starter-kit/ --include="*.md" --include="*.py" --include="*.json"

# Audit script has only universal checks
grep '@register(' ~/doe-starter-kit/execution/audit_claims.py

# Extension point comment exists
grep 'yourproject' ~/doe-starter-kit/execution/audit_claims.py

# Commands are project-agnostic
grep -ri "monty\|broker" ~/.claude/commands/

# README consistency: every command file in kit has a matching README entry
for f in ~/doe-starter-kit/global-commands/*.md; do
  base=$(basename "$f" .md)
  [ "$base" = "README" ] && continue
  grep -q "/$base" ~/doe-starter-kit/global-commands/README.md || echo "MISSING README ENTRY: $base"
done
```

### Step 9: Update CHANGELOG.md and version
Before committing, update `CHANGELOG.md`:
1. Read the current version from the latest `## [vX.Y.Z]` heading in CHANGELOG.md
2. Determine the new version:
   - **Patch** (v1.0.1): bug fixes, wording improvements, small tweaks
   - **Minor** (v1.1.0): new commands, new directives, new hooks, new features
   - **Major** (v2.0.0): breaking changes to CLAUDE.md rules or directory structure
3. Add a new `## [vX.Y.Z] — YYYY-MM-DD` section at the top (below the header) with subsections:
   - `### Added` — new files, commands, features
   - `### Changed` — modified behaviour, updated wording
   - `### Fixed` — bug fixes, compatibility fixes
   - `### Removed` — deleted files or features
   Only include subsections that have entries. Add the `<!-- hero -->` ... `<!-- /hero -->` block above the subsections (1-3 sentence "do I care?" answer); add the optional `<!-- background -->` ... `<!-- /background -->` block when postmortem prose is load-bearing and does not fit in bullets. See `directives/kit-development.md` ## CHANGELOG structure for the contract.
4. Present the changelog entry in a bordered box for approval. **Generate programmatically** — compute W from content, use `.ljust(W)` padding, Unicode box-drawing borders. Content inside borders must be ASCII-only. Structure: header row with "CHANGELOG" left-aligned and version + date right-aligned, separator, 2-line plain English summary, then ADDED/CHANGED/FIXED/REMOVED sections with bulleted items. Wait for explicit approval before proceeding.

### Step 9.5: Author a migration manifest (when the release rewrites prompts or rules)

When the release changes phrasing in CLAUDE.md, directives, or templates that downstream projects may have copied verbatim — or changes the **behaviour** of a hook, permission rule, or matcher — author a migration manifest at `migrations/v<version>.md`. The manifest is consumed by `/pull-doe` pre-flight (Step 4.5 of `directives/starter-kit-pull.md`) so projects pulling the release see exactly which of their files reference retired phrases or workflows.

**Manifest format:**

```
# Migration Manifest — kit vX.Y.Z

**Pull impact summary.** <one paragraph: scope of phrase rewrites, scope
of behavioural changes, what the pre-flight greps for>.

## Format

OLD: "<exact phrase removed from the file>"
NEW: "<phrase that replaced it>"
WHY: <one-line reason — usually positive form name, or load-bearing -> decoration deletion>

## Tier 1 — universal templates + Core Behaviours

### CLAUDE.md (kit's own — also the project-CLAUDE.md template)

OLD: "<old phrase>"
NEW: "<new phrase>"
WHY: <one-line reason>

(repeat per phrase, then per file under Tier 1)

## Tier 2 — directives/

(per-directive blocks; same OLD/NEW/WHY shape; one block per file is
expected even if the file had no rewrites -- mark such files "(No
load-bearing rewrites this pass.)" so the audit trail is complete)

## Tier 3 — kit's learnings.md + remaining files

(per-file blocks)

## Behavioural changes

### <subject> -- <one-line summary>

Scope: <where the change lives -- `.claude/settings.json`, hook script, etc.>
Old behaviour: <what happened before>
New behaviour: <what happens now>
Pull-impact for projects on v<previous>: <what they will newly observe>
Pull-impact grep: `<command for /pull-doe to run against the project>`

(repeat per behavioural change)

## Customised-directive check

Run from the project root before pulling:

```bash
PINNED_TAG=$(grep -oE 'kit v?[0-9]+\.[0-9]+\.[0-9]+' STATE.md | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')
KIT_DIR=~/doe-starter-kit
for f in directives/*.md; do
    diff -q "$f" "$KIT_DIR/$f" 2>/dev/null \
        || echo "PROJECT-CUSTOMISED (3-way merge needed): $f"
done
```
```

**Authoring rules:**
- One manifest per release (`migrations/v1.59.0.md`, `migrations/v1.60.0.md`).
- `OLD:` / `NEW:` lines start at column 0 so the pre-flight grep can extract them line-by-line.
- Long multi-line OLD/NEW phrases get summarised in the OLD: line (truncated to ~200 chars with `\n` escapes) so the line stays greppable; the full text can live in a fenced block underneath when needed.
- `Pull-impact grep:` for behavioural changes is the exact command the pre-flight will run -- write it so a project can paste it as-is.
- "Files with no load-bearing rewrites" still get a stub heading so the audit trail covers every file the audit examined.

**When NOT to author a manifest:**
- The release adds new files only (no phrase changes to existing files, no behavioural changes to hooks/matchers/permissions).
- The release is a pure bug-fix patch (e.g. fixing a typo in a directive that doesn't change meaning).

In those cases, note "No migration manifest needed (additive release)" in the CHANGELOG hero so the absence is documented.

### Step 10: Open the PR (Phase 1)

After Steps 1–9.5 prepare the kit-side changes (translated diff, CHANGELOG entry, version bump in version files, migration manifest if applicable), commit them on a feature branch in the kit and open a PR. **No tutorial stamp, no tag, no GitHub release in Phase 1** — those happen in Step 11 after the PR merges.

The branch + PR is the editorial review surface. The maintainer reviews the diff, the CHANGELOG entry, and the version bump on GitHub before any of it lands on main.

**Run each of these as a SEPARATE Bash tool call** so exit codes propagate independently. Bash pipelines return the last command's exit code: chaining `git commit ... && git push` after a pipe-trimmed prior command fires the push even when commit was blocked by a hook. Separate calls keep each exit code visible. When chaining is unavoidable, prefix with `set -o pipefail`.

**Sanitize the branch name** before using it (project names with spaces, slashes, or special characters break `git checkout -b`):

```bash
PROJECT_SLUG=$(echo "$PROJECT_NAME" | tr '[:upper:] /' '[:lower:]--' | tr -cd 'a-z0-9-')
BRANCH="sync-from-${PROJECT_SLUG}-$(date +%Y-%m-%d-%H%M)"
```

Branch, commit, push:

```bash
cd ~/doe-starter-kit
git checkout -b "$BRANCH"
git add -A
git diff --staged --stat
# Show diff, wait for user sign-off before committing
git commit -m "sync: from ${PROJECT_NAME} — [one-line summary of what changed]"
git push -u origin "$BRANCH"
```

The Phase 1 commit message does NOT contain a version tag (`vX.Y.Z`) — it's a `sync:` prefix, which the kit's `commit-msg` step-mark hook does not match against. **No `SKIP_STEP_MARK_CHECK=1` needed in Phase 1.** (Phase 2's stamp commit DOES have a version tag and DOES need the bypass — see Step 11.)

Open the PR. The body is a heredoc with **single-quoted delimiter** (`<<'PRBODY'`) so `$VARS` are NOT expanded by Bash — Claude substitutes the placeholders before invoking:

```bash
gh pr create \
  --repo Albion-Labs/doe-starter-kit \
  --title "sync: from ${PROJECT_NAME} — [one-line summary]" \
  --body "$(cat <<'PRBODY'
[CHANGELOG entry content rendered as the PR body, plus a "Files changed" summary table]

## Phase 2 (post-merge)

After this PR merges, run `/sync-doe` from any project (or reply "merged" in the same session) to trigger Phase 2: tutorial stamp + tag v[X.Y.Z] + GitHub release.
PRBODY
)"
```

Capture the PR number and URL — `gh pr create` prints the URL on stdout:

```bash
PR_URL=$(gh pr view --repo Albion-Labs/doe-starter-kit --json url --jq .url)
PR_NUMBER=$(echo "$PR_URL" | grep -oE '[0-9]+$')
```

(`gh pr view` with no argument resolves to the current branch's PR, which we just created. Robust against PR-list pagination and works even if `gh pr create`'s stdout was captured elsewhere.)

Write the state file using a pure-Bash heredoc — no Python, no env-export ceremony, variables interpolate inline because the heredoc delimiter is **un-quoted**:

```bash
mkdir -p ~/doe-starter-kit/.tmp
cat > ~/doe-starter-kit/.tmp/.sync-doe-pending-release.json <<EOF
{
  "version": "$NEW_VERSION",
  "prNumber": $PR_NUMBER,
  "prUrl": "$PR_URL",
  "branch": "$BRANCH",
  "project": "$PROJECT_NAME",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "phase": "awaiting-merge"
}
EOF
```

Switch back to main locally so the kit working tree is in a clean state for any subsequent operations:

```bash
git checkout main
```

Tell the user:

> "PR #N opened: \<URL\>. Review and merge it on GitHub. Reply 'merged' (or run `/sync-doe` again later) to release."

**Phase 1 ends here.** The state file persists. Phase 2 runs when the user confirms the PR merged (Step 11). The Step 6 stash (if any) is dropped in Phase 2 after the release succeeds — keeping it in place during the open-PR window means a buyer-remorse "abandon" path can `git stash pop` to restore the pre-sync state.

### Step 11: Release after merge (Phase 2)

Phase 2 runs only after the PR opened in Step 10 has merged on `origin/main`. Step 0.7 (resume detection) routes here when the state file is present and `gh pr view` reports the PR as `MERGED`. In the conversational case (same session, user replies "merged"), the same routing applies — verify the PR state via `gh` before running, then proceed.

**Pre-flight: verify PR merged.** Check `gh` exit code first — a transient `gh` failure (auth, rate limit, network) must not be conflated with "PR not merged":

```bash
STATE=~/doe-starter-kit/.tmp/.sync-doe-pending-release.json
PR_NUMBER=$(python3 -c "import json; print(json.load(open('$STATE'))['prNumber'])")
VERSION=$(python3 -c "import json; print(json.load(open('$STATE'))['version'])")

# Verify gh succeeds first; only then trust the state value
PR_STATE=$(gh pr view "$PR_NUMBER" --repo Albion-Labs/doe-starter-kit --json state --jq .state) \
  || { echo "gh pr view failed; cannot verify PR state. Aborting Phase 2."; exit 1; }

[ "$PR_STATE" = "MERGED" ] \
  || { echo "PR #$PR_NUMBER state is '$PR_STATE' (not MERGED). Aborting Phase 2."; exit 1; }
```

**Run each command as a SEPARATE Bash tool call** — same exit-code rationale as Step 10.

**Pull the merged main:**

```bash
cd ~/doe-starter-kit
git checkout main
git pull origin main
# main now has the merged PR (translated content + CHANGELOG entry + version bump in version files).
# Tutorial docs are still stamped to the PREVIOUS version — Phase 2 fixes that.
```

**Idempotency check** — Phase 2 may be resumed after a partial failure (e.g., `gh release create` flaked after the tag was pushed). Detect prior progress and skip already-done steps:

```bash
TAG_EXISTS=$(git rev-parse "$VERSION" 2>/dev/null && echo 1 || echo 0)
RELEASE_EXISTS=$(gh release view "$VERSION" --repo Albion-Labs/doe-starter-kit >/dev/null 2>&1 && echo 1 || echo 0)
echo "Tag exists: $TAG_EXISTS · Release exists: $RELEASE_EXISTS"
```

**Stamp + commit (skip if tag already exists — the stamp commit was already made on a previous attempt):**

```bash
if [ "$TAG_EXISTS" = "0" ]; then
  python3 ~/doe-starter-kit/execution/generate_whats_new.py
  python3 ~/doe-starter-kit/execution/stamp_tutorial_version.py "$VERSION"
  git add -A
  git diff --staged --stat
  # Show diff, wait for user sign-off
  SKIP_MAIN_PROTECTION=1 SKIP_STEP_MARK_CHECK=1 git commit -m "chore(stamp): $VERSION"
fi
```

Both env vars on the stamp commit are required:
- `SKIP_MAIN_PROTECTION=1` — the kit repo's `.githooks/pre-commit` refuses direct-to-main by default. **The post-merge tutorial stamp is the one operation where direct-to-main is expected** — the editorial work went through the PR in Phase 1. The bypass scope is narrower than the pre-Phase-2 design (stamp commit only, not the full release content).
- `SKIP_STEP_MARK_CHECK=1` — the commit message contains a version tag `(vX.Y.Z)` which triggers the step-mark hook.

**Tag, push tag, push commit (in that order — see universal learning on the pre-push tutorial-docs-version gate):**

```bash
if [ "$TAG_EXISTS" = "0" ]; then
  git tag "$VERSION"
  git push origin "$VERSION"          # tag first — tag-only pushes don't trip the docs-version gate
  SKIP_MAIN_PROTECTION=1 git push     # commit — pre-push gate sees tag=$VERSION, docs=$VERSION, passes
fi
```

The order matters: pushing the commit before pushing the tag means the gate compares stamped docs to the OLD tag and refuses the push. The fix-up cost (force-push, manual unstuck) is large; the prevention cost (one extra Bash call in the right order) is zero.

**Create the GitHub release (skip if already exists):**

```bash
if [ "$RELEASE_EXISTS" = "0" ]; then
  gh release create "$VERSION" \
    --repo Albion-Labs/doe-starter-kit \
    --title "$VERSION — [short description]" \
    --notes "[CHANGELOG entry content, copied from the PR body]"
fi
```

**Drop the safety stash from Step 6** (if used) — release succeeded, no rollback needed:

```bash
git stash list | grep -q "Pre-sync backup" && git stash drop
```

**Clean up the state file:**

```bash
rm ~/doe-starter-kit/.tmp/.sync-doe-pending-release.json
```

**Tell the user:**

> "Released $VERSION."

Note: Phase 2 does NOT update the originating project's `STATE.md` — `/sync-doe` may run from a different cwd than the project that opened the PR (the state file lives in the kit, not the project), and stamping STATE.md in the wrong project would be silently misleading. Each project picks up the new kit version on its next `/pull-doe`, which updates STATE.md as part of its own procedure.

## What NOT to sync
- Task content (todo.md items, archive.md history)
- STATE.md session content
- stats.json data
- Project-specific learnings (only universal patterns)
- Project-specific directives
- Project-specific audit checks
- .env files
- .tmp/ contents

## Edge Cases
- If a format rule was added to todo.md, sync the rule itself but not the tasks
- If a new trigger was added to CLAUDE.md, check if it references project-specific directives — if so, genericize the directive path
- If a new command references project-specific files, either genericize it or don't sync it
- If audit_claims.py gained new universal checks, sync those but leave the extension point comment intact
- If the starter kit has content this project doesn't have, ALWAYS preserve it — it came from another project's sync
- When git pull in Step 2 reveals conflicts, surface the conflict to the user before any merge action -- conflicts are the user's call to resolve

## Post-Sync Checklist
- [ ] Tutorial footers auto-stamped by `stamp_tutorial_version.py` (verify in diff)
- [ ] Check if tutorial docs need updating for framework changes:

| If this changed... | Check this tutorial page |
|---|---|
| `setup.sh` | `getting-started.html` (install flow, terminal mockups) |
| `wrap.md` or `wrap_stats.py` or `wrap_html.py` | `commands.html` (command description), `daily-flow.html` (session end section) |
| New/removed command in `global-commands/` | `commands.html` (add/remove entry), sidebar in all pages if navigation changed |
| `.githooks/` or `check_contract.py` | `tips-and-mistakes.html` (hooks section) |
| `STATE.md` template | `key-concepts.html` (state management), `getting-started.html` (initial setup) |
| `CLAUDE.md` operating rules | `key-concepts.html` (DOE architecture), `workflows.html` (feature lifecycle) |
| Multi-agent scripts | `multi-agent.html` (terminal mockups, worked example) |

Only update if the change is user-facing. Internal refactors don't need doc updates.
