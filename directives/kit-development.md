# Directive: Kit Development

## Goal
The conventions specific to contributing changes back to the DOE Starter Kit itself — versioning model, branch naming, CHANGELOG structure, release mechanics, CC self-dogfood, the tests-included-by-default expectation, and the hook-design rule. These are kit-only rules; they don't apply to projects that consume the kit.

## When to Use
- Working in `~/doe-starter-kit` directly
- Running `/sync-doe` to push monty-side improvements back to the kit
- Reviewing or merging a kit PR
- Designing a new kit feature that will ship across multiple steps

## Versioning model: one release per PR

The kit uses a single shared release version per PR — **all steps of a feature ship together in one minor or patch release**, not one patch per step (which is monty's per-step-versioning model). For example, v1.57.0's seven steps all land in `v1.57.0`; there is no `v1.57.1` for Step 1, `v1.57.2` for Step 2, etc.

**Patch vs minor vs major:**
- **Patch (`vX.Y.Z+1`)** — bug fixes only. Spec deviations corrected, no new behaviour.
- **Minor (`vX.Y+1.0`)** — new features, new directives, new commands, new hook stages. The default for kit feature work.
- **Major (`vX+1.0.0`)** — breaking changes to CLAUDE.md rules or directory structure. Rare; needs explicit user discussion.

## Branch naming

Feature branches follow `feature/<short-name>-vX.Y.Z`, where the version matches the release the work targets:

- `feature/bootstrap-polish-v1.56.0`
- `feature/conventional-commits-phase1-v1.57.0`

Patch fix branches use `fix/vX.Y.Z-<short-name>`:

- `fix/v1.56.1-spec-deviations`

Housekeeping (no feature, no release-bump): `housekeeping/<short-name>` (no version).

## CHANGELOG structure

Every release adds a section to `CHANGELOG.md` at the top, above the previous release. The structure:

```markdown
## v1.57.0 (YYYY-MM-DD)
<!-- hero -->
One paragraph (no line breaks within) summarising the release for a human reading the GitHub release page or the tutorial. Sentences only -- no bullets here.
<!-- /hero -->

### Added
- **path/to/file** — what was added and why.

### Changed
- **path/to/file** — what changed and why.

### Fixed
- **path/to/file** — what was broken and how it's fixed now.
```

The `<!-- hero -->` ... `<!-- /hero -->` block is what `gh release create` uses for release notes (extract via `sed -n '/^## v1\.57\.0/,/^## v1\.56/p'`). Keep it scannable; one paragraph, complete sentences. The `### Added` / `### Changed` / `### Fixed` sections are for the diligent reader who wants the per-file detail.

## Release mechanics

Releases are **manual** after PR merge. The kit doesn't auto-release because the human merging is also the human deciding "yes, this is shippable as vX.Y.Z."

After PR merge:

```bash
cd ~/doe-starter-kit
git checkout main && git pull
git tag vX.Y.Z
git push origin vX.Y.Z
gh release create vX.Y.Z --title "vX.Y.Z — <short-name>" \
  --notes "$(sed -n '/^## vX\.Y\.Z/,/^## vX\.Y\./p' CHANGELOG.md | sed '$d')"
```

The release notes come from the CHANGELOG hero + sections of the release being shipped. Don't hand-write release notes; the CHANGELOG is the source of truth.

## CC self-dogfood

Every commit on a kit branch must use Conventional Commits format (see `git-conventions.md`). The retro contract for v1.57.0+ explicitly checks this:

```bash
test $(git log --format=%s main..HEAD | grep -cvE "^(Merge |Revert |(feat|fix|chore|docs|refactor|test|perf|build|ci|style)(\(.+\))?!?: )") -eq 0
```

A non-zero count fails the contract, blocking the retro step until the offending commit is amended or fixed up. The `commit-msg` hook in warn mode will flag non-CC commits as you go; treating those warnings as errors during kit work avoids retro-time surprises.

## Tests included by default

Kit features that touch executable code or hook scripts MUST ship with tests in the same PR:

- Changes to `execution/*.py` -> matching tests in `tests/execution/`
- Changes to `.githooks/*` -> tests in `tests/githooks/` driving subprocess invocations of the real hook
- Changes to `templates/_base/claude_sections/*.md` that affect generated CLAUDE.md content -> tests in `tests/execution/test_doe_init.py` asserting the generated text

The kit's pytest suite is the regression net. Skipping tests "for speed" creates the silent-regression gap that v1.58.0's freshness-warning hook is designed to catch — but tests are required even before that hook lands. See `testing-strategy.md` for how to structure new tests, what fixtures exist, and how to drive subprocess-style hook tests.

## Hook design rule: fast checks only

Pre-commit hooks run on every commit. They MUST stay fast — under 1s in the typical case. If a check needs to run pytest, fetch from a network, or analyse a large file, it doesn't belong in the pre-commit hook; it belongs in a slash command (e.g. `/agent-verify`, `/doe-health`) or a CI job.

Concrete rule: if a check would add more than ~200ms to commit latency on a clean repo, push it to a slash command and have the hook print a one-line reminder ("run `/doe-health` before pushing"). The hook stays a fast structural check; the slow but valuable work happens at a moment when the user is willing to wait.

## See also

- `git-conventions.md` — the Conventional Commits 1.0 spec and the kit's allowlist that the commit-msg hook enforces
- `testing-strategy.md` — how to structure tests for kit-surface code and what coverage is expected
- `starter-kit-sync.md` — pushing monty-side improvements back to the kit (`/sync-doe`)
- `starter-kit-pull.md` — pulling kit updates into a project
