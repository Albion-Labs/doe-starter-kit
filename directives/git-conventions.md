# Directive: Git Conventions

## Goal
A single source of truth for commit message formatting across DOE-Claude Code projects: the Conventional Commits 1.0 spec, the kit's allowlist for legacy/automated patterns, and the `DOE_COMMIT_HOOK_MODE` env var that controls how strictly the validator enforces the rules.

## When to Use
- Writing or editing a commit message in a DOE-bootstrapped project
- Designing a slash command or workflow that produces commits (e.g. `/wrap`, `/sync-doe`, `/agent-verify`)
- Triaging a `commit-msg` hook warning or block
- Onboarding a new contributor to a DOE project

## Format

Every commit subject must match Conventional Commits 1.0:

```
<type>[optional (scope)][!]: <description>
```

Examples that match: `feat: add reset button`, `fix(auth): expire stale sessions`, `chore(release): v1.57.0`, `refactor!: rename canonical paths`.

The body and footer are optional and not validated; only the subject line matters for the hook.

## Types (all 10 supported)

| Type | When to use |
|---|---|
| `feat` | A new user-visible feature or capability |
| `fix` | A bug fix |
| `chore` | Housekeeping — releases, dependency bumps, internal cleanup that isn't user-visible |
| `docs` | Documentation only |
| `refactor` | Code change that neither adds a feature nor fixes a bug |
| `test` | Adding or updating tests |
| `perf` | Performance improvement |
| `build` | Build system or external dependency changes |
| `ci` | CI configuration or pipeline changes |
| `style` | Formatting, whitespace, missing semicolons; no code change |

The `!` suffix marks a breaking change (e.g. `feat!: drop Node 18 support`). Combine with scope freely: `fix(api)!: ...`.

## Allowlist (commits that bypass validation)

Some commit subjects are deliberately not Conventional Commits and the hook lets them through unmolested:

1. `Merge ` — GitHub-generated merge commits (`Merge pull request #N from ...`)
2. `Revert "` — `git revert`-generated reverts
3. `Initial commit` — `git init`'s default first commit (rare; the wizard's `chore: initial DOE scaffolding` is preferred)
4. `fixup!` — `git commit --fixup` markers, intended to be squashed before merge
5. `squash!` — `git commit --squash` markers
6. legacy `vX.Y.Z:` — pre-Conventional-Commits release format (e.g. `v1.55.11: ...`). Allowed for backwards-compat with kit history before v1.57.0; new commits should use `chore(release): vX.Y.Z` instead

## Hook mode: `DOE_COMMIT_HOOK_MODE`

The `.githooks/commit-msg` hook validates every commit subject against the format above. Its strictness is controlled by an environment variable:

```bash
# Default: warn but never block
DOE_COMMIT_HOOK_MODE=warn

# Hard enforcement: non-compliant commits exit 1
DOE_COMMIT_HOOK_MODE=block
```

In `warn` mode (the default), a non-compliant message prints a one-line warning to stderr and the commit succeeds. This is the right default during the v1.57.0 -> v1.58.x transition window so existing workflows aren't broken by sudden enforcement.

In `block` mode, a non-compliant message exits 1 and the commit fails. Switch to `block` per-project via `.git/info/config` or globally via your shell profile once the team is fully on Conventional Commits.

To bypass the hook entirely for a single commit (e.g. an automated tool's output that you can't fix locally), use `git commit --no-verify`. This bypasses every commit-msg stage, not just the CC validator.

## Worked examples (DOE-grounded)

Releases — the dedicated form for kit/project version bumps:

```
chore(release): v1.57.0 -- Conventional Commits Phase 1
chore(release): v1.55.11 -- sync-procedure gotchas codified
```

Feature work — scope is the area of the codebase or the feature name:

```
feat(wizard): opt-in initial scaffolding commit prompt
feat(map): add filter highlight overlay
```

Bug fixes — scope is the bug surface:

```
fix(hook): allow first-ever commit on main for fresh repos
fix(census): handle missing 2011 LSOA codes
```

Docs / chores / tests:

```
docs(directives): add git-conventions
chore(deps): bump pytest to 9.0.3
test(githooks): cover commit-msg block mode
```

Body example (for context, not validated):

```
fix(hook): pre-push docs gate enforces on main only

The tutorial-docs version gate in pre-push was firing on every branch,
blocking legitimate feature-branch PRs that stamp docs ahead of their
release tag (the tag is cut AFTER PR merge, not before). Now the gate
only runs when CURRENT_BRANCH is main or master.
```

## Migration from legacy `vX.Y.Z:` format

Pre-v1.57.0 kit history used `vX.Y.Z: <description>` for release commits. The allowlist preserves these unchanged in `git log`. New commits should use `chore(release): vX.Y.Z`. Don't rewrite history to backfill — the `git log` is an honest record of how the convention evolved, and rewriting would invalidate every downstream clone.

## See also

- `kit-development.md` — kit versioning model, branch naming, release mechanics, and how this directive applies to kit contributors specifically
- `building-rules.md` — when to commit and how to scope work for one-step-one-commit
- `.githooks/commit-msg` — the hook that enforces this directive
