Create a sibling git worktree for feature work, following the v1.63.0 worktree convention (the project's trunk worktree stays on the default branch; feature work lives in `<project>-<feature>/` siblings).

Usage: `/worktree-create <feature-slug>` — the feature slug becomes both the branch suffix and the sibling directory suffix. Example: `/worktree-create framework-migration` produces branch `feature/framework-migration` and worktree at `<project-parent>/<project>-framework-migration/`.

The slug is the only argument. Slug rules: lowercase, kebab-case, ASCII letters / digits / hyphens only, starts with a letter, no path separators, no leading or trailing hyphen.

## Pre-flight

1. **Argument check.** A feature-slug argument is required. If it is missing, ask: "Which feature is this worktree for? Provide a short kebab-case slug (e.g. `framework-migration`, `auth-overhaul`)." Validate against the slug rules above; if it fails, ask for a corrected one. Surface the regex used so the user understands the constraint: `^[a-z][a-z0-9-]*[a-z0-9]$` (or `^[a-z]$` for one-character slugs).

2. **Trunk-worktree check (v1.63.0+).** /worktree-create runs from the trunk worktree (the worktree whose branch matches the repo default). Verify:
   - Determine the default branch: `git symbolic-ref refs/remotes/origin/HEAD --short | sed 's|^origin/||'`. Resolves to `main` for current projects, `master` for legacy.
   - Compare against the current branch: `git branch --show-current`.
   - If they differ, STOP and surface: "/worktree-create runs from the trunk worktree. You appear to be on `<current-branch>` (sibling worktree?). cd to the trunk path and re-run." Parse `git worktree list --porcelain` to find and report the trunk path.

3. **Branch collision check.** Run `git branch --list "feature/<slug>"` and `git ls-remote --heads origin "feature/<slug>" 2>/dev/null`. If the branch already exists locally or on the remote, STOP and surface: "`feature/<slug>` already exists (local / remote / both). Use a different slug, or check out the existing branch in a worktree if one is appropriate."

4. **Worktree-path collision check.** Compute the target path: `<dirname of current worktree>/<basename of current worktree>-<slug>`. If the path already exists as a directory, STOP and report the conflicting path so the user can rename or remove it before retrying.

## Create

1. Compute paths and names:
   ```bash
   trunk_path=$(git rev-parse --show-toplevel)
   project_name=$(basename "$trunk_path")
   parent_dir=$(dirname "$trunk_path")
   sibling_path="$parent_dir/$project_name-<slug>"
   branch_name="feature/<slug>"
   ```

2. Create the branch and worktree in one operation:
   ```bash
   git worktree add "$sibling_path" -b "$branch_name"
   ```
   The new worktree starts at the trunk's current HEAD.

3. Confirm: `git worktree list --porcelain` shows the new sibling worktree record. The trunk path remains on the default branch unchanged.

## Post-create

Show the user a brief summary card with:
- The new worktree path (full absolute path)
- The branch name
- A hint on next steps: "Open a new terminal in `<sibling-path>` and start Claude Code from there. The sibling worktree holds the feature work; the trunk stays on the default branch so wrap commits and kit operations land cleanly."

**Honest scope reminder.** The sibling worktree gives BRANCH-level isolation between parallel sessions: two sessions on two worktrees keep their own HEADs. It is FILE-level coordination that still needs single-terminal discipline — shared docs (STATE.md, tasks/todo.md, learnings.md, CLAUDE.md) get committed via one terminal at a time so the second wrap commit lands without a merge conflict.

## Edge cases

- **Detached HEAD on trunk.** If the trunk is mid-rebase or in another detached state, STOP — ask the user to resolve the trunk state first. Worktrees branched from a detached HEAD inherit the detachment.
- **Uncommitted changes on trunk.** `git worktree add` works regardless of the trunk's working-tree state, but the new branch starts from the committed HEAD, not the dirty working tree. Mention the dirty state so the user knows their uncommitted edits stay in the trunk's working tree.
- **Bare repository.** If `git worktree list --porcelain` shows a `bare` flag at the main worktree (rare for DOE projects), the ergonomics differ slightly — `git worktree add` still works but the main worktree has no working tree of its own. Surface the bare flag in the post-create summary so the user understands the layout.
- **Path with spaces or special characters.** Quote `<sibling-path>` consistently in all commands. The slug constraints above eliminate spaces in the path, so the practical risk lives in the project-name basename — if the project itself has a space in its directory name, that already produces friction elsewhere.

## What /worktree-create deliberately does NOT do

- It leaves wrap bookkeeping (STATE.md, stats.json updates) to /wrap.
- It leaves session start (`.tmp/.session-start`, `.tmp/.session-start-branch`) to /crack-on running in the new sibling worktree.
- It does not push the new branch to origin — the first push happens at first commit per /crack-on conventions.
- It stays on the trunk worktree after creation; opening Claude Code in the new sibling is the user's next step.
