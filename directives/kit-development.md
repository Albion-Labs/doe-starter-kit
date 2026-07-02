# Directive: Kit Development

## Goal
The conventions specific to contributing changes back to the DOE Starter Kit itself — versioning model, branch naming, CHANGELOG structure, release mechanics, CC self-dogfood, the tests-included-by-default expectation, and the hook-design rule. These rules apply to kit work only; projects that consume the kit are governed by their own CLAUDE.md.

Tradeoff: Kit-dev rules add a pytest run and CHANGELOG edit to every kit feature in exchange for safe upgrades for every project that pulls the kit. Apply on every PR against `~/doe-starter-kit`. Skip when: the work is a project-only edit (CLAUDE.md, project directives) with no kit sync planned.

## When to Use
- Working in `~/doe-starter-kit` directly
- Running `/sync-doe` to push project-side improvements back to the kit
- Reviewing or merging a kit PR
- Designing a new kit feature that will ship across multiple steps

## Kit-write model: PR-only

Kit changes flow through a feature branch and PR. The canonical gate is the kit's `.githooks/pre-commit` 'no direct-to-main' hook (active when `git config core.hooksPath .githooks` has been run on the clone) plus human PR review. The `guard_kit_writes` PreToolUse hook is a defence-in-depth layer that blocks only irreversible operations -- recursive removal of kit paths and force-push to kit main; it does not gate ordinary edits.

Empirical basis: 8 minor kit releases (v1.51 - v1.58) shipped with `guard_kit_writes` matchers in lowercase form that never fired on real Tool calls. During that window, multiple consuming projects pulled the kit and edited kit working trees freely. Zero corruption incidents documented. v1.59.0 fixed the matchers; the dominant effect was a long tail of false positives on legitimate Bash commands whose source bytes happened to contain a kit-path token (heredoc bodies, JSON payloads, `python3 -c` quoted code, `cd kit && git describe`). v1.60.0 retired the file-edit branch and the redirect/tee/cd-and-commit Bash patterns; PR review is the canonical gate.

Last-resort override for the destructive Bash patterns: `SKIP_KIT_GUARD=1`. Set only when an operator genuinely needs to perform a destructive action (emergency rollback). The flag file `.tmp/.sync-doe-active` from v1.59.x is no longer read by the hook; `/sync-doe` may still touch it for backwards compatibility with v1.59.x clients.

Cross-project exposure: in v1.60.0, an AI working in a consuming project can edit the kit working tree directly. The dominant detection point is the `/sync-doe` Step 0.5 dirty-tree pre-flight, which surfaces any uncommitted kit changes for user acknowledgement before applying a sync. See `directives/starter-kit-sync.md` ## Step 0.5.

## Roles: by context and repo permission, not a self-declared flag

There is no "consumer vs creator" identity. Every person using the kit is BOTH a consumer of it inside their project repos AND a contributor the moment they hit a kit gap and fix it — role is a function of what you are doing in the moment, not a setting on your machine. The old `**DOE Role:**` line in `STATE.md` (and the `setup.sh` prompt that wrote it) was removed in v1.66.0: it gated nothing in code — no hook or command ever read it, and even the `/wrap` messaging it claimed to control was never conditional on it.

Who can release is governed at the repo layer, where it belongs and is actually enforced:
- `.github/CODEOWNERS` requires owner review on security-critical paths (`.githooks`, `.github/workflows`, `CLAUDE.md`).
- Branch protection + the `.githooks/pre-commit` 'no-direct-to-main' hook force every change through a PR.
- `auto-release.yml` (v1.65.0+) means merge == release; only merged PRs ship.

Anyone may open a `/sync-doe` PR; merging it is gated by the above. The four loops every project uses, flagless: **Use** (no gate) → **Improve** (local patch → `/sync-doe` PR → review → merge → auto-release) → **Update** (`/pull-doe`) → **Idea** (`/report-doe-bug` / `/request-doe-feature` → kit issues).

## Local divergence: staging area, not end state

A project's vendored kit files differing from the kit is fine ONLY as one of two declared things: (1) an in-flight patch awaiting backport via `/sync-doe`, or (2) a deliberate project-specific override recorded in the project's `.doe-overrides` manifest (per-clone, gitignored; `.doe-overrides.example` is the template). Everything else that differs is **drift** — silent forks that erode the kit's whole reason to exist (one methodology across projects). `execution/audit_sync.py` reports un-declared diverged files as `diverged` (drift) and declared ones as `declared_overrides` (suppressed); `/wrap` surfaces the drift count each session so it never accumulates invisibly.

## Versioning model: one release per PR

The kit uses a single shared release version per PR — **all steps of a feature ship together in one minor or patch release**, not one patch per step (which is a per-step-versioning model some projects use). For example, v1.57.0's seven steps all land in `v1.57.0`; there is no `v1.57.1` for Step 1, `v1.57.2` for Step 2, etc.

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
One paragraph (no line breaks within) answering "do I care about this release?" in 1-3 sentences. Names the headline change and who needs it. Specific implementation prose goes in the bullet sections below; the hero stays scannable.
<!-- /hero -->

<!-- background -->
(Optional.) Postmortem prose for releases where the why-context is load-bearing: how the bug was caught, why the design decision went the way it did, what failure mode this prevents. Skip the block entirely for small patches that do not need it.
<!-- /background -->

### Added
- **path/to/file** — what was added and why.

### Changed
- **path/to/file** — what changed and why.

### Fixed
- **path/to/file** — what was broken and how it's fixed now.
```

The `<!-- hero -->` ... `<!-- /hero -->` block is the lead — it answers "do I care?" in 1-3 sentences. The optional `<!-- background -->` ... `<!-- /background -->` block carries postmortem prose for releases where the why-context is load-bearing (e.g. v1.62.2's "every install was broken by a single cd" mechanism). Most patch releases skip the background block. Both blocks are extracted by `gh release create` as release notes (HTML comment markers strip cleanly under GitHub's markdown renderer; prose flows naturally). The page renderer in `execution/generate_whats_new.py` emits `<h4>Summary</h4>` above the hero and `<h4>Background</h4>` above the background when present.

The `### Added` / `### Changed` / `### Fixed` sections are for the diligent reader who wants the per-file detail. **The hero is not a re-prose of these bullets** — if the hero is duplicating bullet content, push the duplication into the bullets and tighten the hero.

Anti-pattern: a hero that exceeds 3 sentences usually contains either (a) postmortem prose that belongs in `<!-- background -->`, or (b) bullet-level detail that belongs in `### Added` / `### Fixed`. v1.62.2 and v1.63.0 are examples of heroes that pre-date this contract — the new contract applies forward only; historical entries are not retroactively rewritten.

## Content hygiene

Kit content (CHANGELOG.md, docs/tutorial/, directives/, ROADMAP.md, kit PR descriptions, GitHub release notes) is downstream-visible. Two rules.

**Never name specific consumer projects.** The kit is a product; consumer projects (the ones running `/pull-doe`) are not. Naming a consumer project in kit content leaks the user's project list into a shared artefact and creates an awkward asymmetry where some projects are "famous" and others aren't. Refer to consumer projects generically: "consumer projects", "projects using the kit", "a project", "a consuming project". Provenance attribution (e.g. "source: <project> session N retro") goes in the kit PR's commit messages or local notes, not the kit's CHANGELOG. This rule applies to ALL kit-visible content, including pre-existing entries when they get touched.

**Never include empty sections.** A `### Removed` heading followed by "Nothing removed" (or any equivalent "Nothing to report") is bloat — it signals diligence that wasn't required and adds a row of noise to the whats-new page. Omit the section entirely if there's nothing to put in it. Same applies to `### Changed` / `### Fixed` when not applicable. The four-section structure in ## CHANGELOG structure is a menu, not a contract; pick the sections that have content.

## Release mechanics

Releases are **automatic** as of v1.65.0. The `auto-release` GitHub Action (`.github/workflows/auto-release.yml`) fires on every push to `main` -- PR merge, direct push, or any other route -- and runs the full release ceremony whenever the top `## vX.Y.Z` heading in `CHANGELOG.md` has no matching tag. Merge = release.

### What the workflow does

On every push to main:

1. Extract the top `## vX.Y.Z` heading (pre-release tags like `vX.Y.Z-rc.1` excluded by regex)
2. If `git rev-parse refs/tags/vX.Y.Z` succeeds, no-op and exit
3. Otherwise: regen `whats-new.html`, run `stamp_tutorial_version.py`, commit `chore(stamp): vX.Y.Z`, **push commit**, **tag locally**, **push tag**, `gh release create` with notes from the CHANGELOG entry

The workflow uses **commit-first / tag-second** ordering. This is the safe order for partial-failure recovery: if the tag push fails, the commit is already on origin and re-runs detect it (skip the redundant commit, tag the existing HEAD, push tag) -- recoverable. Tag-first would risk leaving an orphaned tag pointing to a SHA the runner had locally but never pushed; re-runs would see the tag and no-op, leaving the kit in a broken state.

The manual fallback (below) uses the OPPOSITE order -- tag-first -- because the local pre-push tutorial-docs-version gate fires when pushing the branch and requires the tag to already match. GH Actions runners don't activate `.githooks/`, so the gate doesn't apply there and the workflow picks the safer ordering.

The workflow is **idempotent**: every step is gated on state checks. Re-runs after partial failure detect what already happened and skip. Trigger a re-run via `workflow_dispatch` from the Actions UI.

**On failure**, the workflow opens an issue labelled `release-automation` + `needs-triage` describing where it stopped and what to do.

**Concurrency** is pinned: only one auto-release runs at a time (`concurrency.group: auto-release`, `cancel-in-progress: false`).

### Why automatic

The kit's prior "manual ceremony" rule depended on human memory at exactly the moment of context-switching after a PR merge -- when attention naturally migrates back to the project that prompted the kit work. v1.64.1 surfaced the gap: a 1-line gitignore patch merged cleanly, then the human pivoted to project work and only completed the release after explicit prompting. The original rationale ("the human merging is also the human deciding shippability") assumed merge != release-ready, but the kit's "one release per PR" model means merge IS release-ready by construction. The deferred-tag flexibility paid for nothing while drift accumulated.

### When to bypass automation

No skip flag by design. To merge a version-bumping PR without auto-releasing:

1. Disable the workflow via Actions UI (`Actions -> auto-release -> ... -> Disable workflow`)
2. Merge the PR
3. When ready, run the manual fallback (below) to create the tag
4. Re-enable the workflow (next push sees tag-already-exists, no-ops)

Don't add a skip flag to the workflow file -- every flag is a foot-gun.

### Manual fallback (if automation is broken)

```bash
cd ~/doe-starter-kit
git checkout main && git pull
python3 execution/generate_whats_new.py
git add docs/tutorial/whats-new.html
SKIP_MAIN_PROTECTION=1 git commit -m "chore(release): regen whats-new for vX.Y.Z"
git tag vX.Y.Z
git push origin vX.Y.Z         # tag first -- whats-new gate passes (section just regenerated)
git push                       # branch push

awk -v v="vX.Y.Z" '
  in_section && /^## v[0-9]+\.[0-9]+\.[0-9]+/ { exit }
  $0 ~ "^## " v "($| )" { in_section=1 }
  in_section { print }
' CHANGELOG.md > /tmp/release-notes.md

gh release create vX.Y.Z --title "vX.Y.Z" --notes-file /tmp/release-notes.md
```

`SKIP_MAIN_PROTECTION=1` goes on the **commit** (the kit's pre-commit hook does the no-direct-to-main check). `SKIP_WHATSNEW_CHECK=1` on pre-push exists from v1.60.1 for genuine emergencies where regeneration itself fails.

The CHANGELOG is the source of truth -- both the workflow and the manual fallback lift release notes from it.

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
- `starter-kit-sync.md` — pushing project-side improvements back to the kit (`/sync-doe`)
- `starter-kit-pull.md` — pulling kit updates into a project
