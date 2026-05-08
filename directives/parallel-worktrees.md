# Directive: Parallel Worktrees for Multi-Session Work

## Goal
Use git worktrees to isolate branch checkouts when running multiple Claude Code sessions on the same project, so concurrent branch switches in one session cannot silently move another session's HEAD onto the wrong branch.

## When to Use
Load this when:
- Starting a second (or third) Claude session in the same project repo
- A long-lived feature branch is in flight and routine work (wraps, `/sync-doe`, `/pull-doe`, plan-refresh, kit mirrors) needs to happen on `main` independently
- A wrap or stand-up surfaces branch drift between session-start and current HEAD
- Setting up a new project that anticipates parallel sessions

Apply only when multiple Claude sessions run against the same project repo. Solo-session projects use one folder with one HEAD as today -- the convention is opt-in.

## Inputs
- A clean git repo with `main` (or the project's trunk branch) accessible
- The branch you want to isolate in a sidecar worktree

## Process

1. **Convention.** The folder you have always used for this project (`<project>/`) lives on `main`. Long-lived feature branches get sibling worktrees: `<project>-<feature>/`. Each Claude session works in its own worktree.

2. **Create a feature worktree.** When starting work on a long-lived branch:
   ```
   git worktree add ../<project>-<feature> <branch>
   ```
   The branch must exist (or pass `-b <new-branch>` to create it). The original `<project>/` stays on `main`; the new sibling holds the feature branch.

3. **Switch to the feature worktree** when working on that feature: `cd ../<project>-<feature>`. Run `git checkout` for the feature branch in the sidecar; the trunk worktree stays on `main` for the duration.

4. **Single-branch concurrency.** A branch can be checked out in only ONE worktree at a time. Git enforces this. Treat it as a feature: the worktree IS the branch's session ownership.

5. **Cleanup after merge.** When the feature ships:
   ```
   git worktree remove ../<project>-<feature>
   ```

## Outputs
- A sibling worktree directory pinned to the feature branch
- The trunk worktree (`<project>/`) continues to live on `main` regardless of what the feature work does
- Each Claude session works in a directory whose HEAD it owns alone

## Edge Cases

- **What worktrees do NOT fix:** all worktrees write to the same git history. `STATE.md`, `tasks/todo.md`, `learnings.md`, and `CLAUDE.md` are still shared files. Two worktrees both committing to one of these still race -- worktrees solve the BRANCH-level race (silent HEAD switch), not the FILE-level race. The "edit shared files from one terminal at a time" rule still applies.
- **Build artefacts duplicate.** Each worktree has its own `node_modules/`, `.next/`, `.tmp/`, build outputs, etc. Costs disk + a fresh install per worktree. Hooks (`.claude/settings.json`, `.githooks/*`) are shared via git.
- **Branch already checked out.** `git worktree add` for a branch that is checked out elsewhere fails with `'<branch>' is already checked out at '<path>'`. Either remove the other worktree first or pick a different branch.
- **Detached HEAD or no main branch.** Worktrees still work but the "trunk on main" convention assumes `main` exists. Substitute the project's actual trunk branch name where applicable.

- **Anti-patterns:** sharing one working tree across parallel Claude sessions.
  - Before: `cd ~/Project && claude` running in two terminals -- one session's `git checkout feature/X` silently moves the other session's HEAD; commits land on the wrong branch.
  - After: `git worktree add ../Project-feature-X feature/X` -- each session owns its own working tree; HEAD switches stay isolated.

## Verification
- [ ] `git worktree list` shows the expected worktree layout
- [ ] Each worktree's HEAD is on the intended branch
- [ ] Trunk worktree is on `main` (or the project's trunk branch); it has not been switched away
- [ ] No two worktrees attempt to check out the same branch
