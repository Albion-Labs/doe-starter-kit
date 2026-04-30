# Directive: Kit Development

## Goal
The conventions specific to contributing changes back to the DOE Starter Kit itself — versioning model, branch naming, CHANGELOG structure, release mechanics, CC self-dogfood, the tests-included-by-default expectation, and the hook-design rule. These rules apply to kit work only; projects that consume the kit are governed by their own CLAUDE.md.

Tradeoff: Kit-dev rules add a pytest run and CHANGELOG edit to every kit feature in exchange for safe upgrades for every project that pulls the kit. Apply on every PR against `~/doe-starter-kit`. Skip when: the work is a project-only edit (CLAUDE.md, project directives) with no kit sync planned.

## When to Use
- Working in `~/doe-starter-kit` directly
- Running `/sync-doe` to push monty-side improvements back to the kit
- Reviewing or merging a kit PR
- Designing a new kit feature that will ship across multiple steps

## Kit-write model: PR-only

Kit changes flow through a feature branch and PR. The canonical gate is the kit's `.githooks/pre-commit` 'no direct-to-main' hook (active when `git config core.hooksPath .githooks` has been run on the clone) plus human PR review. The `guard_kit_writes` PreToolUse hook is a defence-in-depth layer that blocks only irreversible operations -- recursive removal of kit paths and force-push to kit main; it does not gate ordinary edits.

Empirical basis: 8 minor kit releases (v1.51 - v1.58) shipped with `guard_kit_writes` matchers in lowercase form that never fired on real Tool calls. During that window, multiple consuming projects pulled the kit and edited kit working trees freely. Zero corruption incidents documented. v1.59.0 fixed the matchers; the dominant effect was a long tail of false positives on legitimate Bash commands whose source bytes happened to contain a kit-path token (heredoc bodies, JSON payloads, `python3 -c` quoted code, `cd kit && git describe`). v1.60.0 retired the file-edit branch and the redirect/tee/cd-and-commit Bash patterns; PR review is the canonical gate.

Last-resort override for the destructive Bash patterns: `SKIP_KIT_GUARD=1`. Set only when an operator genuinely needs to perform a destructive action (emergency rollback). The flag file `.tmp/.sync-doe-active` from v1.59.x is no longer read by the hook; `/sync-doe` may still touch it for backwards compatibility with v1.59.x clients.

Cross-project exposure: in v1.60.0, an AI working in a consuming project (monty, cortex, etc.) can edit the kit working tree directly. The dominant detection point is the `/sync-doe` Step 0.5 dirty-tree pre-flight, which surfaces any uncommitted kit changes for user acknowledgement before applying a sync. See `directives/starter-kit-sync.md` ## Step 0.5.

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
# Regenerate whats-new.html so the deployed docs reflect the new CHANGELOG entry.
python3 execution/generate_whats_new.py
git add docs/tutorial/whats-new.html
git commit -m "docs(tutorial): regen whats-new for vX.Y.Z"
git push
git tag vX.Y.Z
git push origin vX.Y.Z
gh release create vX.Y.Z --title "vX.Y.Z — <short-name>" \
  --notes "$(sed -n '/^## vX\.Y\.Z/,/^## vX\.Y\./p' CHANGELOG.md | sed '$d')"
```

The `generate_whats_new.py` step is enforced by the pre-push hook on tag push (added in v1.60.1): pushing `vX.Y.Z` fails if `docs/tutorial/whats-new.html` has no matching section. Skip with `SKIP_WHATSNEW_CHECK=1` for emergency releases.

The release notes come from the CHANGELOG hero + sections of the release being shipped. The CHANGELOG is the source of truth -- write the entry there first; `gh release create` lifts it.

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
