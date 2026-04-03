# Multi-Agent Coordination Protocol (Branch + PR Model)

Wave-based parallel development using feature branches and pull requests. Each agent works on its own feature branch, creates a PR at completion, and merges via the standard PR workflow.

## Branch Model

- **Main branch (`main`):** Always stable. Protected with required CI status checks. No direct commits.
- **Feature branches (`feature/<task-slug>`):** One per agent task. Created from `main` at wave launch. All commits happen here.
- **Merge flow:** Feature branch → Pull Request → CI passes → Merge to main.

## Wave Lifecycle

### 1. Planning (Coordinator terminal)

Define 2-4 independent tasks in `tasks/todo.md`. Each task must:
- Have a `Contract:` block with `[auto]` criteria
- Own specific files (no overlap between tasks)
- Be achievable in one session

### 2. Launch

Each agent terminal runs `/crack-on` which:
- Creates a feature branch from `main` (`git checkout -b feature/<task-slug>`)
- Pushes the branch (`git push -u origin feature/<task-slug>`)
- Picks up the assigned task

Agents work independently on their feature branches. No shared file conflicts because each task owns distinct files.

### 3. Build (Per agent)

Each agent:
- Commits per step on their feature branch
- Pushes each commit immediately
- Runs `/agent-verify` to check `[auto]` criteria per step
- Does NOT edit shared files (`todo.md`, `CLAUDE.md`, `learnings.md`, `STATE.md`)

### 4. Complete (Per agent)

When all steps pass:
- Run `--complete` to verify all contract criteria
- Create a pull request: `gh pr create --base main --head feature/<task-slug>`
- CI runs automatically on the PR
- Agent reports completion to coordinator

### 5. Merge (Coordinator terminal)

The coordinator merges PRs sequentially:
1. Review each PR (CI must be green)
2. Merge first PR to main
3. Update remaining PRs to rebase on new main if needed
4. Merge next PR
5. After all PRs merged, update shared files (`todo.md` step markers, `STATE.md`, `learnings.md`)
6. Commit shared file updates on main

### 6. Cleanup

- Delete merged feature branches: `git branch -d feature/<task-slug>`
- Delete remote branches: `git push origin --delete feature/<task-slug>`
- Clean up any wave state files in `.tmp/waves/`

## Worktrees and Branches Are Layers, Not Alternatives

The original protocol framed worktrees vs branch+PR as an either/or choice. They solve different problems and should be combined:

| Layer | Purpose | When needed |
|-------|---------|-------------|
| **Worktrees** | Local filesystem isolation -- each terminal gets its own directory with its own branch checked out | Any time 2+ terminals work on different branches simultaneously (you cannot checkout two branches in one directory) |
| **Branches** | Remote tracking -- each feature has its own ref that can be pushed, rebased, compared | Always (single or parallel) |
| **PRs** | Merge workflow -- CI gating, code review, GitHub conflict detection | Always (replaced direct-to-main commits) |

The DAG executor (`dispatch_dag.py`) already combines all three: creates worktrees for local isolation, branches for tracking, and PRs for merge. Informal parallel should do the same.

What the old model lacked was CI gating and PR-based merge -- not worktrees. Worktrees remain the correct local isolation mechanism for all parallel modes.

## Compatibility

This protocol works with:
- Raw terminal multiplexing (multiple VS Code terminals)
- Agentastic, Conductor, cmux (external orchestrators)
- Claude Code's built-in `multi_agent.py` (auto-detects main/master)

The `multi_agent.py` script's `--merge` command now uses the default branch (auto-detected) and supports both the legacy worktree model and the new branch + PR model.

## Serial Dispatch (Alternative to Parallel Waves)

For complex features where steps are interdependent (shared files, output dependencies), use serial dispatch instead of parallel waves. The coordinator dispatches one implementer at a time, with review gates between steps.

**When to use serial dispatch vs parallel waves:**
- **Serial:** 3+ interdependent steps, shared files, integration concerns. Coordinator → implementer → reviewer chain.
- **Parallel:** 2+ truly independent tasks, no shared files. Standard wave model above.
- **Solo:** Single-step tasks, quick fixes. No dispatch needed.

See `directives/serial-dispatch-protocol.md` for the full workflow, decision tree, model selection guide, and re-dispatch limits.

## Guardrails

- Wave agents MUST NOT edit shared files on main (`todo.md`, `CLAUDE.md`, `learnings.md`, `STATE.md`)
- Each task's `owns` list defines which files the agent can modify
- CI checks on PRs prevent broken code from reaching main
- Feature branches are deleted after merge — no branch accumulation
