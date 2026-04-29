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
   Only include subsections that have entries.
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

### Step 10: Commit, tag, and push

**Run each of these as a SEPARATE Bash tool call** -- one command per call so each exit code propagates independently. Bash pipelines return the last command's exit code: `git commit ... | tail -5 && git tag` fires the tag even when commit was blocked by a hook (`tail` exits 0). Separate calls keep each exit code visible. When chaining is unavoidable, prefix with `set -o pipefail`.

```bash
cd ~/doe-starter-kit
python3 ~/doe-starter-kit/execution/generate_whats_new.py
python3 ~/doe-starter-kit/execution/stamp_tutorial_version.py v[X.Y.Z]
git add -A
git diff --staged --stat
# Show diff, wait for sign-off
SKIP_MAIN_PROTECTION=1 SKIP_STEP_MARK_CHECK=1 git commit -m "chore(release): v[X.Y.Z] — sync from [project] ([what changed])"
git tag v[X.Y.Z]
SKIP_MAIN_PROTECTION=1 git push
git push origin v[X.Y.Z]
```

Both env vars on the commit are required:
- `SKIP_MAIN_PROTECTION=1` — the kit repo's `.githooks/pre-commit` and `.githooks/pre-push` refuse direct-to-main by default. Kit sync is the one procedure where direct-to-main is expected.
- `SKIP_STEP_MARK_CHECK=1` — the commit message contains a version tag `(vX.Y.Z)` which triggers the step-mark enforcement hook. Kit release commits don't correspond to a todo.md step, so the check doesn't apply.

The `.tmp/.sync-doe-active` bypass file covers the kit-write-guard hook but does **not** disable either of these checks; the env vars are still needed.

Then create a GitHub release:
```bash
gh release create v[X.Y.Z] --title "v[X.Y.Z] — [short description]" --notes "[changelog entry content]"
```

If the stash was used in Step 6, drop it after successful push:
```bash
git stash drop
```

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
