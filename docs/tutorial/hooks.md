# Git hooks

The DOE kit ships three git hooks under `.githooks/` that run automatically on every commit and push. They're activated when a project runs `git config core.hooksPath .githooks` (the wizard does this for you on first setup).

## Kit-write model: PR-only (v1.60.0)

As of v1.60.0, the kit-write discipline is committed to a PR-only model. The canonical gate for kit changes is the kit's own `.githooks/pre-commit` 'no direct-to-main' hook plus PR review. The `.claude/hooks/guard_kit_writes.py` PreToolUse hook is now a defence-in-depth layer that blocks only **irreversible** Bash operations — recursive removal of kit paths (`rm -r*`) and force-push to kit main (`git push --force` mentioning the kit OR from inside the kit cwd). It does **not** gate ordinary edits, redirects, or `cd kit && git commit`.

The parallel `.claude/hooks/protect_directives.py` hook also tightened in v1.60.0: the overbroad `python3 -c "...directives/..."` Bash pattern was retired (it matched any Python one-liner that referenced the directives token, including read-only). The eight unambiguous Bash write patterns (`>`, `>>`, `tee`, `sed -i`, `awk -i inplace`, `rm`, `mv`, `cp`) and the existence-aware file-path branch are unchanged.

Cross-project AI sessions can now edit the kit working tree without a PreToolUse block. The detection points for unintended drift are:

1. `/sync-doe` Step 0.5 (mandatory pre-flight): refuses to apply a sync if `git status --porcelain` in the kit returns non-empty.
2. `KIT DIRTY` row in `/crack-on`, `/stand-up`, and `/wrap`: surfaces uncommitted kit working-tree changes at session boundaries.

Last-resort override for the destructive Bash patterns: `SKIP_KIT_GUARD=1`. Set only when an operator genuinely needs a destructive action (emergency rollback). The flag file `.tmp/.sync-doe-active` from v1.59.x is no longer read; `/sync-doe` may still touch it for backwards compatibility with v1.59.x clients.

Empirical basis: 8 minor releases (v1.51 - v1.58) shipped with `guard_kit_writes` matchers in lowercase form that never fired on real Tool calls. During that window, multiple consuming projects pulled the kit and edited working trees freely with zero corruption incidents documented. v1.59.0 fixed the matchers; the dominant effect was a long false-positive tail. v1.60.0 commits to the PR-only model PR review was already enforcing.

The companion `block_dangerous_commands` hook splits its match logic in v1.60.1: substring patterns (`rm -rf /`, `DROP TABLE`, fork bombs, `dd if=`, etc.) keep substring-match semantics; env-var bypass names (`SKIP_REVIEW_GATE`, `SKIP_CONTRACT_CHECK`, `SKIP_SIGNOFF_CHECK`) match only on actual assignment (`VAR=`), with a quote-context heuristic that skips the match when it sits inside a quoted string. Reading docs, running `grep`, or echoing the flag name no longer trip a false-positive block.

## pre-commit

Fires on `git commit`. Runs a series of fast structural checks; any failure blocks the commit.

- **Main-branch protection.** Direct commits to `main` or `master` are blocked. Exception: the first-ever commit on a fresh repo (no `HEAD` yet) is allowed through, so `bash setup.sh && git commit` works without workarounds. Skip with `SKIP_MAIN_PROTECTION=1`.
- **Audit sweep.** Runs `python3 execution/audit_claims.py --hook` to catch staleness in tracked docs. Blocks on any FAIL finding.
- **Step-mark + version-tag enforcement.** If a commit references a step number or version tag, `tasks/todo.md` must be staged. Skip with `SKIP_STEP_MARK_CHECK=1`.
- **Pending-PR sync, contract verification, quality-gate checkpoints.** Bigger checks that fire when the relevant files are staged.
- **Test freshness** (added in v1.58.0). Warns when a tested source file (`execution/doe_init.py`, `.githooks/pre-commit`, `.githooks/commit-msg`) is staged without its sibling test under `tests/`. Warning-only — the commit still goes through. The directive `directives/testing-strategy.md` ## Maintenance is the source of truth that says tests are required; this hook is the forgetful-human nudge. Skip with `SKIP_TEST_FRESHNESS=1`.
- **Doc freshness** (added in v1.58.0, extended in v1.60.1). Warns when source files ship without their tutorial-doc counterpart. Mappings: `global-commands/*.md` -> `commands.html`, `.githooks/*` -> `hooks.md`, `.claude/hooks/*.py` -> `hooks.md` (v1.60.1), `migrations/*.md` -> `migration-guide.html` (v1.60.1), `CHANGELOG.md` -> `whats-new.html` (v1.60.1). Warning-only. Skip with `SKIP_DOC_FRESHNESS=1`.

Skip the entire pre-commit hook with `git commit --no-verify`. Avoid this except in genuine emergencies — most failures are caught for a reason.

## commit-msg

Fires after `git commit` accepts a message. Runs in this order:

- **Co-author trailer strip.** Removes `Co-Authored-By: Claude` and `Co-Authored-By: Anthropic` lines automatically. The kit policy is no AI co-author trailers in commits.
- **Conventional Commits validation** (added in v1.57.0). Subject must match `<type>[(scope)][!]: <description>` with type in `feat`, `fix`, `chore`, `docs`, `refactor`, `test`, `perf`, `build`, `ci`, `style`. Allowlisted prefixes (`Merge`, `Revert`, `Initial commit`, `fixup!`, `squash!`, legacy `vX.Y.Z:`) bypass validation. Mode is controlled by the `DOE_COMMIT_HOOK_MODE` env var: default `warn` prints a stderr warning and lets the commit through; set `block` to make non-compliance a hard error. Full spec in `directives/git-conventions.md`.
- **Changelog enforcement.** If the commit message contains a version tag like `(v1.57.0)`, `whats-new.html` must be staged. Skip with `SKIP_CHANGELOG_CHECK=1`.
- **Step-marking enforcement.** Same as the pre-commit version but checked again after the message is finalised.

## pre-push

Fires on `git push`. Two checks:

- **Tutorial docs version gate.** On `main` or `master` only: docs must match the latest tag. Prevents shipping a release without the tutorial docs being stamped to the same version. Skip with `git push --no-verify`. Branch-aware as of v1.56.0 — feature branches that bump docs ahead of their release tag (the normal pre-merge state) push cleanly.
- **Whats-new freshness on tag pushes** (added in v1.60.1). When pushing a tag matching `v*.*.*`, fail-fast unless `docs/tutorial/whats-new.html` contains a matching release section (or `CHANGELOG.md` has a corresponding `## vX.Y.Z` heading). Skip with `SKIP_WHATSNEW_CHECK=1 git push origin <tag>`. Catches the failure where release tags went out without `python3 execution/generate_whats_new.py` having been run.
- **Methodology --quick checks.** Fast structural validations across the kit (cross-reference consistency, directive schema, todo.md format). Catches issues before CI does.

## When hooks fire too aggressively

If a hook is blocking a commit you genuinely need to make:

1. **Read the error.** Each hook prints the env var to skip it and a one-line description of what went wrong. The skip path is documented per-hook.
2. **Use the targeted skip, not `--no-verify`.** `SKIP_MAIN_PROTECTION=1 git commit ...` skips just main-branch protection; the audit, CC, and step-mark checks still run. `--no-verify` bypasses everything.
3. **Fix the root cause if you keep skipping.** A hook firing repeatedly for the same reason is signal. The kit's hooks are designed to stay fast (<1s per commit) and stay relevant; persistent skips usually mean the hook needs improving, not the rule needs avoiding.

## Hook design rule

DOE pre-commit hooks must stay fast (under ~1s on a clean repo). Slow checks belong in slash commands like `/agent-verify` or `/doe-health`, where the user is willing to wait. See `directives/kit-development.md` for the full design rule and the rationale.
