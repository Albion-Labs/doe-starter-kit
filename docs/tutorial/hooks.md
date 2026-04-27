# Git hooks

The DOE kit ships three git hooks under `.githooks/` that run automatically on every commit and push. They're activated when a project runs `git config core.hooksPath .githooks` (the wizard does this for you on first setup).

## pre-commit

Fires on `git commit`. Runs a series of fast structural checks; any failure blocks the commit.

- **Main-branch protection.** Direct commits to `main` or `master` are blocked. Exception: the first-ever commit on a fresh repo (no `HEAD` yet) is allowed through, so `bash setup.sh && git commit` works without workarounds. Skip with `SKIP_MAIN_PROTECTION=1`.
- **Audit sweep.** Runs `python3 execution/audit_claims.py --hook` to catch staleness in tracked docs. Blocks on any FAIL finding.
- **Step-mark + version-tag enforcement.** If a commit references a step number or version tag, `tasks/todo.md` must be staged. Skip with `SKIP_STEP_MARK_CHECK=1`.
- **Pending-PR sync, contract verification, quality-gate checkpoints.** Bigger checks that fire when the relevant files are staged.
- **Test freshness** (added in v1.58.0). Warns when a tested source file (`execution/doe_init.py`, `.githooks/pre-commit`, `.githooks/commit-msg`) is staged without its sibling test under `tests/`. Warning-only — the commit still goes through. The directive `directives/testing-strategy.md` ## Maintenance is the source of truth that says tests are required; this hook is the forgetful-human nudge. Skip with `SKIP_TEST_FRESHNESS=1`.
- **Doc freshness** (added in v1.58.0). Warns when source files ship without their tutorial-doc counterpart: `global-commands/*.md` paired with `docs/tutorial/commands.html`, `.githooks/*` paired with `docs/tutorial/hooks.md`. Warning-only. Skip with `SKIP_DOC_FRESHNESS=1`.

Skip the entire pre-commit hook with `git commit --no-verify`. Avoid this except in genuine emergencies — most failures are caught for a reason.

## commit-msg

Fires after `git commit` accepts a message. Runs in this order:

- **Co-author trailer strip.** Removes `Co-Authored-By: Claude` and `Co-Authored-By: Anthropic` lines automatically. The kit policy is no AI co-author trailers in commits.
- **Conventional Commits validation** (added in v1.57.0). Subject must match `<type>[(scope)][!]: <description>` with type in `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `style`. Allowlisted prefixes (`Merge`, `Revert`, `Initial commit`, `fixup!`, `squash!`, legacy `vX.Y.Z:`) bypass validation. Mode is controlled by the `DOE_COMMIT_HOOK_MODE` env var: default `warn` prints a stderr warning and lets the commit through; set `block` to make non-compliance a hard error. Full spec in `directives/git-conventions.md`.
- **Changelog enforcement.** If the commit message contains a version tag like `(v1.57.0)`, `changelog.html` must be staged. Skip with `SKIP_CHANGELOG_CHECK=1`.
- **Step-marking enforcement.** Same as the pre-commit version but checked again after the message is finalised.

## pre-push

Fires on `git push`. Two checks:

- **Tutorial docs version gate.** On `main` or `master` only: docs must match the latest tag. Prevents shipping a release without the tutorial docs being stamped to the same version. Skip with `git push --no-verify`. Branch-aware as of v1.56.0 — feature branches that bump docs ahead of their release tag (the normal pre-merge state) push cleanly.
- **Methodology --quick checks.** Fast structural validations across the kit (cross-reference consistency, directive schema, todo.md format). Catches issues before CI does.

## When hooks fire too aggressively

If a hook is blocking a commit you genuinely need to make:

1. **Read the error.** Each hook prints the env var to skip it and a one-line description of what went wrong. The skip path is documented per-hook.
2. **Use the targeted skip, not `--no-verify`.** `SKIP_MAIN_PROTECTION=1 git commit ...` skips just main-branch protection; the audit, CC, and step-mark checks still run. `--no-verify` bypasses everything.
3. **Fix the root cause if you keep skipping.** A hook firing repeatedly for the same reason is signal. The kit's hooks are designed to stay fast (<1s per commit) and stay relevant; persistent skips usually mean the hook needs improving, not the rule needs avoiding.

## Hook design rule

DOE pre-commit hooks must stay fast (under ~1s on a clean repo). Slow checks belong in slash commands like `/agent-verify` or `/doe-health`, where the user is willing to wait. See `directives/kit-development.md` for the full design rule and the rationale.
