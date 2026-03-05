# Directive: DOE Starter Kit Pull

## Goal
Safely pull DOE starter kit updates INTO a project. The reverse of `/sync-doe` (which pushes project improvements out to the kit). Version-aware diffing ensures only new changes are applied, and project-specific content is never overwritten.

## When to Use
- When the kit has been updated (new commands, directives, hooks, CLAUDE.md rules) and a project needs those improvements
- After another project synced improvements to the kit via `/sync-doe`
- When a new kit version is released on GitHub
- When explicitly asked to pull kit updates

## Inputs
- Access to `~/doe-starter-kit` (the local clone of the starter kit repo)
- The project's `.doe-kit-version` file (if it exists) — records last-synced kit version
- The kit's current version (from `git describe --tags`)

## Process

### Step 1: Ensure kit is accessible
If `~/doe-starter-kit` is not available in the current session:
```
/add-dir ~/doe-starter-kit
```

### Step 2: Pull latest kit from GitHub
Before comparing anything, make sure the local kit is up to date.
```bash
cd ~/doe-starter-kit && git pull
```
If there are local uncommitted changes, stop and ask the user how to handle them before proceeding.

### Step 3: Read versions
Read the project's last-synced version:
```bash
cat .doe-kit-version 2>/dev/null || echo "NOT FOUND"
```
Read the kit's current version:
```bash
cd ~/doe-starter-kit && git describe --tags --abbrev=0
```

### Step 4: Compare versions
- **Versions match** → "Already up to date — project is on kit vX.Y.Z" → show UP TO DATE result box → stop.
- **Kit is newer** → continue to Step 5.
- **Kit is older than project's recorded version** → warn: "Kit version vX.Y.Z is older than project's recorded vX.Y.Z. This is unusual — the project may have been manually updated. Proceed with caution?" Wait for confirmation.
- **`.doe-kit-version` not found** → this is the project's first pull. Warn: "No .doe-kit-version found — treating as first pull. Will show all changes for review." Be extra cautious — show everything, apply nothing without approval.

### Step 5: Show what changed
Show the kit CHANGELOG entries between the project's version and the current kit version:
```bash
cd ~/doe-starter-kit && git log <old-version>..<new-version> --oneline
```
Also read the CHANGELOG.md and extract entries between the two versions. Present these so the user understands what's incoming.

If this is a **major version bump** (e.g. v1.x.x → v2.x.x), warn explicitly:
> "This is a major version bump which may include breaking changes to CLAUDE.md rules or directory structure. Review each change carefully before approving."

### Step 6: Global installs
Run the kit's setup script to update globally-installed files (commands, hooks, scripts):
```bash
cd ~/doe-starter-kit && bash setup.sh
```
This updates:
- `~/.claude/commands/*.md` (global slash commands)
- `~/.claude/hooks/*.py` (guardrail hooks)
- `~/.claude/scripts/*.py` (utility scripts)
- `~/.claude/settings.json` (PostToolUse hook registrations)
- `~/.claude/.doe-kit-version` (global version receipt)

### Step 7: Project hooks and settings
Compare the kit's hook/settings templates against the project's versions:
- `.claude/hooks/*.py` — diff each file
- `.claude/settings.json` — diff PreToolUse entries
- `.githooks/*` — diff hook scripts

For each file that differs:
1. Show the diff
2. Identify what's new in the kit vs what's project-specific
3. Propose the update — add new kit content, preserve project-specific additions

IMPORTANT: Projects may have added their own hooks or settings entries. Never remove project-specific additions — only add/update kit-provided content.

### Step 8: CLAUDE.md
This is the most sensitive file — it contains both universal DOE rules and project-specific customizations.

```bash
cd ~/doe-starter-kit && git diff <old-version>..<new-version> -- CLAUDE.md
```

Show what changed in the kit's CLAUDE.md between versions. Then compare against the project's CLAUDE.md and propose surgical edits:

- **New rules** → propose adding them in the correct section
- **Changed rules** → show old vs new wording, propose update
- **New triggers** → propose adding to Progressive Disclosure
- **New guardrails** → propose adding to Guardrails section

Flag and SKIP anything that would conflict with project-specific content:
- Project-specific triggers (e.g. "Building a UI card → check learnings.md ## UI Patterns")
- Project-specific guardrails (e.g. "YOU MUST NOT edit ~/doe-starter-kit directly")
- Project-specific directory structure entries
- Project-specific governed document references

Present all proposed CLAUDE.md changes in a single diff view before applying.

### Step 9: Templates (learnings.md, todo.md)
Compare format rules only — never touch content.

- **learnings.md** — if the kit added new section headings or format rules in the template, propose adding them to the project's learnings.md. Never modify existing learnings content.
- **todo.md** — if the kit changed format rules (e.g. new step format, new status tags), propose the rule change. Never modify existing tasks.

### Step 10: Directives
List directives in both the kit and the project:
```bash
ls ~/doe-starter-kit/directives/*.md
ls directives/*.md
```

For each kit directive:
- **Exists in both** → diff them. If the kit version is newer, propose updating the project's copy. Preserve any project-specific additions.
- **Kit-only (new)** → propose adding it to the project. These are universal SOPs.
- **Project-only** → leave untouched. These are project-specific.

### Step 11: Execution scripts
Compare `execution/audit_claims.py` between kit and project:
- If the kit added new `@register("universal")` checks, propose adding them to the project's copy
- Never touch `@register("project-specific")` checks — these are project customizations
- Preserve the extension point comment if present

### Step 12: Show full summary and get approval
Present the Analysis Box (as defined in the /pull-doe command) with all proposed changes categorized. Wait for explicit user approval before applying anything.

### Step 13: Apply approved changes
Apply only the changes the user approved. For each file:
- Make surgical edits (add/update specific sections)
- Never replace files wholesale
- After applying, show a brief confirmation of what was changed

### Step 14: Update project version
Write the kit's current version to the project's version file:
```bash
echo "vX.Y.Z" > .doe-kit-version
```

### Step 15: Commit
```bash
git add -A
git commit -m "Pull DOE kit vX.Y.Z — [summary of what changed]"
```
If a remote is configured, push after committing.

## Outputs
- Updated project files matching the latest kit version
- `.doe-kit-version` updated to the new version
- A commit recording the pull with a clear message

## Edge Cases
- **Kit version older than project's recorded version** → warn, ask for confirmation before proceeding
- **`.doe-kit-version` doesn't exist** → first pull, be extra cautious, show everything
- **Major version bump** → warn about breaking changes, require explicit confirmation
- **Merge conflicts in CLAUDE.md** → show both versions side-by-side, let the user decide which to keep
- **Project has diverged significantly** → show the full comparison of each file category before proposing anything
- **Kit has files the project doesn't** → propose adding them (they're new kit features)
- **Project has custom hooks not in the kit** → leave them untouched
- **setup.sh fails** → show the error, try to continue with manual file-by-file comparison
- **Git pull fails (network, conflicts)** → show BLOCKED result box with the error

## Verification
- [ ] All approved changes applied correctly (spot-check key files)
- [ ] `.doe-kit-version` matches kit's current version
- [ ] Project-specific CLAUDE.md content preserved (triggers, guardrails, directory entries)
- [ ] Project-specific hooks and settings preserved
- [ ] Project-specific directives untouched
- [ ] Project-specific audit checks preserved
- [ ] No kit template content leaked into project content sections (learnings, tasks)
- [ ] Commit message clearly states what was pulled and from which version
