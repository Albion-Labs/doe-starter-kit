## Git Conventions

Commit subjects follow Conventional Commits 1.0:

```
<type>[(scope)][!]: <description>
```

**Types:** `feat` (new feature), `fix` (bug fix), `chore` (housekeeping/releases), `docs` (documentation), `refactor` (code change without behaviour change), `test` (tests), `perf` (performance), `build` (build system), `ci` (CI config), `style` (formatting only).

Add `!` after type/scope for breaking changes (`feat!: ...`). Combine with scope freely (`fix(auth)!: ...`).

**Allowlist** (commits that bypass validation): `Merge `, `Revert "`, `Initial commit`, `fixup!`, `squash!`, and the legacy `vX.Y.Z:` release format.

**Mode:** the `.githooks/commit-msg` hook validates every subject. Default `DOE_COMMIT_HOOK_MODE=warn` prints a warning and lets the commit through. Set `DOE_COMMIT_HOOK_MODE=block` once the team is fully on Conventional Commits to make non-compliance a hard error.

**Examples:**
- `feat(wizard): add reset button`
- `fix(auth): expire stale sessions`
- `chore(release): v1.57.0`
- `docs(directives): add git-conventions`

See `directives/git-conventions.md` for the full spec, the rationale behind each allowlist entry, and DOE-grounded worked examples.
