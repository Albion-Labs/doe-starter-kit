Remove a sibling git worktree after its feature work is shipped (PR merged) or abandoned (branch deleted unmerged).

Usage: `/worktree-remove <feature-slug-or-path>` — accepts either the feature slug (e.g. `framework-migration` → resolves to `<project-parent>/<project>-framework-migration/`) or an absolute / relative path to the worktree directory.

## Pre-flight

1. **Argument resolution.** Resolve the argument to a worktree path:
   - If it looks like a path (contains `/`, starts with `.` or `~`), expand and resolve to an absolute path.
   - Otherwise treat as a feature slug: compute `<dirname of trunk>/<basename of trunk>-<slug>` (mirror of /worktree-create's path logic). The trunk path is `git rev-parse --show-toplevel` if running from the trunk; otherwise parse `git worktree list --porcelain` for the worktree whose branch matches `git symbolic-ref refs/remotes/origin/HEAD --short`.
   - If neither resolution maps to an existing worktree, list the available worktrees from `git worktree list` and ask the user which one.

2. **Worktree-existence check.** The resolved path must appear as a record in `git worktree list --porcelain`. If it does not, STOP and surface the available worktrees so the user can pick a real one.

3. **Trunk refusal.** The trunk worktree (the worktree whose `branch refs/heads/<default>` line matches the repo default per `git symbolic-ref refs/remotes/origin/HEAD`) is structural — it holds the default branch and is the canonical entry point for kit operations. If the argument resolves to the trunk, STOP and refuse: "Cannot remove the trunk worktree — it holds the project's default branch." Suggest the user pick a sibling worktree instead.

4. **Locked-worktree check (v1.63.0+, spike Goal 4 finding).** Parse the resolved worktree's record from `git worktree list --porcelain`. If it has a `locked` flag, STOP and surface the lock reason in the error message:

   ```
   Worktree at <path> is locked: <reason from the locked line>.
   Run `git worktree unlock <path>` if removal is intended, then re-run /worktree-remove.
   ```

   Worktree locks exist so accidental removal is harder; the user must explicitly unlock first. The lock reason is whatever string follows the `locked` flag in `git worktree list --porcelain`; it may be empty if `git worktree lock` was run without `--reason`.

5. **Cleanliness check.** Run `git -C <worktree-path> status --porcelain`. If the output is non-empty, surface the uncommitted change summary (path + status code per line, capped at the first 10 lines) and ask: "Worktree has N uncommitted change(s). Remove anyway? [y/n]" — proceed only on explicit `y`. The user keeps the option to bail and commit / push the work first.

6. **Unmerged-branch check.** Read the worktree's branch from the porcelain record. Compare against `git branch --merged <default-branch>` to see if the branch is already merged into the default. If the branch is NOT in the merged list, warn: "Branch `<feature/x>` has not been merged into `<default>`. Remove the worktree anyway? [y/n]" — proceed only on explicit `y`. This catches abandoned-feature cases and gives the user a chance to merge / cherry-pick / archive first.

## Remove

1. Run the canonical command:
   ```bash
   git worktree remove "<resolved-path>"
   ```
   This deletes the working directory contents and removes the worktree admin record. The branch itself remains in the repo's branch list.

2. Offer branch cleanup as a follow-up step:
   - If the branch was merged into the default (step 6 found it in `--merged`): ask "Also delete the merged branch `feature/<slug>`? [y/n]". On `y`, run `git branch -d feature/<slug>` (the safe form, which preserves any branch with un-merged commits even though we asked).
   - If the branch was unmerged but the user already confirmed removal in step 6: ask "Also delete the unmerged branch `feature/<slug>`? [y/n]". On `y`, run `git branch -D feature/<slug>` (the force form). Frame this as a separate decision from the worktree removal so the user can keep the branch around for later cherry-picks.

## Post-remove

Confirm by re-running `git worktree list --porcelain` and showing the user the remaining worktrees. The trunk should still be present; the removed sibling should be gone.

## Edge cases

- **Worktree directory missing on disk.** If the user manually deleted the directory (`rm -rf <path>`) but the git admin record persists, `git worktree remove` fails with "<path> is not a worktree". Run `git worktree prune` with the user's confirmation — `prune` is the surgical tool for sweeping stale admin records, and it is the correct fit when the working directory is already gone.
- **Worktree containing a stash.** Worktrees do not have per-worktree stashes (`git stash` writes to the shared `.git/refs/stash`), so `/worktree-remove` does not need a stash check. Surface a reminder in the cleanliness step if any `git stash list` entries exist that look related (the user can inspect via `git stash list`).
- **Cwd inside the worktree being removed.** `git worktree remove` fails if the current working directory is inside the worktree being removed. Pre-flight should detect this via `git rev-parse --show-toplevel` and tell the user to `cd` to the trunk path first. /worktree-remove ideally runs from the trunk worktree itself.
- **Force flag.** `--force` stays unexposed by /worktree-remove. Users who genuinely need to force-remove (e.g. a hopelessly stuck submodule worktree) can run `git worktree remove --force <path>` directly; the slash command keeps the safer path as the default.

## What /worktree-remove deliberately does NOT do

- It leaves the user's commit / push / merge of any outstanding feature work to the user — the cleanliness and unmerged-branch warnings exist so the user can choose to bail out and finish properly.
- It leaves remote branch cleanup (`git push origin --delete feature/<slug>`) to the user — remote-branch deletion is a separate operational decision (PR auto-delete-branch handles this on merge; abandoned branches are intentional artifacts).
- It does not run `git gc` or any repo-wide cleanup. Worktree admin records are tiny; pruning happens via `git worktree prune` only when needed.
