# Directive: Delivery Rules

## Goal
Ensure quality, compliance, and completeness when shipping features -- verification, retros, guardrails, and governance.

Tradeoff: Delivery discipline costs retro time at the end of every feature in exchange for shipping work that holds up under reviewer scrutiny and stakeholder questions. Apply on every feature retro and PR. Skip when: the change is a single-line hotfix that bypass-flags the relevant gate (e.g., `SKIP_REVIEW_GATE=1`) with the bypass reason in the commit body.

## When to Use
Loaded when delivering: retros, PR creation, sign-off, wrap, version bumps, merging, or any pre-ship activity.

## Verify Before Delivering

Verify before delivering: run the script, test the output, confirm it matches the spec. After file edits, `ls`/`cat` to confirm. Neutral prompts only -- no sycophantic self-evaluation.

## Pre-Commit Checks

Check STATE.md, learnings.md, and governed docs before every commit. Update if position/decisions/domain changed. Skip if none apply.

## Pitch Spontaneously

Pitch spontaneously: if you notice a genuine improvement, pitch it briefly. One sentence what, one sentence why. User says "add it" (-> Ideas in ROADMAP.md) or "this is important" (-> Must Plan).

## Pre-Retro Quality Gate

Before starting the retro step on any feature (regardless of size):

1. Run `python3 execution/test_methodology.py --scenario cross_reference_consistency --scenario directive_schema --scenario agent_definition_integrity`
2. If the feature modified shared infrastructure (directives, CLAUDE.md routing, agents, execution scripts): spawn Finder agent to review all files modified during the feature (`git diff --name-only main...HEAD`). The Finder should focus on cross-file consistency and documentation-implementation drift, not individual code correctness.
3. Fix findings before proceeding to retro. Log significant findings to learnings.md.

This gate is the universal safety net. Even if the mid-feature checkpoint in `building-rules.md` was skipped or the feature had fewer than 5 steps, the pre-retro gate catches accumulated drift before it ships.

## Retro Discipline

Retro discipline: every feature gets a mandatory retro as its final step. Includes PR creation via `gh pr create`.

- **Quick** (default): `[x] Retro [quick: nothing to log]` or `[quick: logged to learnings.md]`
- **Full** (escalate when: failure, approach change, workaround, repeatable pattern, time exceeded, prevented past failure): `[x] Retro [full: logged to learnings.md + prevention added]`
- Wave agents defer: `[quick: deferred to merge]` or `[full: deferred to merge]`
- **Refresh** (always present, third bracketed field): `[refresh: <next-feature-id> <one-line finding>]` for substantive updates, `[refresh: <next-feature-id> no-op]` when the scan confirms no change is needed. The field documents that Step 7 (Plan refresh) ran and what it produced. Skip the field only when there is genuinely no `## Current` or `## Queue` to scan.

### Retro Procedure
1. Rename HTML to final patch version, update nav badge
2. Update changelog -- add final entry to grouped card
3. Update ROADMAP.md: move feature from Up Next to Complete
4. If [APP] feature, add to showcase entries array
5. Update feature heading from (vX.Y.x) to (vX.Y.N)
6. Run brief retro: what worked, what was slow, what to do differently. Causal discipline: write 'coincided with' or 'was followed by' rather than 'caused' or 'drove' unless the causal link is verified.
7. **Plan refresh.** Scan `## Current` + `## Queue` in `tasks/todo.md` for staleness against the just-shipped change. Triggers any of: new directive grammar (e.g. positive-form requirements), new workflow gates (PR-only, freshness, dirty-tree), new directives added, retired hooks/patterns/scripts. Update affected steps or contracts in place. Record the result inline as a third bracketed field on the retro line: `[refresh: <next-feature-id> <one-line finding>]` for substantive updates, `[refresh: <next-feature-id> no-op]` when the scan confirms no change is needed. Include the next feature even when nothing changed -- the no-op log is the audit trail. The same scan also runs at Queue -> Current promotion, so the next author starts fresh against current reality. Examples:
   - `[x] Retro [quick: nothing to log] [refresh: v1.62.0 Step 3 reframed for positive-form grammar]`
   - `[x] Retro [full: logged to learnings.md + prevention added] [refresh: v1.61.0 no-op]`
8. Promote lasting contracts to `tests/invariants.txt`. Auto-promote: any `[auto]` contract whose `Verify:` pattern references files in `CLAUDE.md`, `directives/`, `.claude/agents/`, `execution/`, `.github/workflows/`, `.githooks/`, `SYSTEM-MAP.md`, `CUSTOMIZATION.md`, or `tests/`. Skip version-specific patterns (containing `vX.Y.Z` or HTML filenames). If the feature intentionally changed something an existing invariant tests, update that invariant to reflect the new state.
9. Run `/review` -- adversarial review of the full feature diff. This records a review artifact that the PR creation hook checks. If the review FAILs, fix issues and re-run before proceeding.
10. PR creation: `gh pr create` from feature branch to main (blocked by `enforce_review_gate.py` hook unless step 9 passed for current HEAD)
11. Move the whole block to ## Done

### Match merge patterns before authoring

Before running `gh pr create` (step 10 of the retro procedure), read 5-10 recently merged PRs to match the project's tone, structure, and review expectations. The recent merged corpus is the strongest signal of what reviewers accept; documented conventions are the second-best signal.

Run: `gh pr list --state merged --limit 10 --json number,title --jq '.[] | "#\(.number) \(.title)"'` then read 2-3 in full with `gh pr view <N>`. Look for: subject-line conventions, body structure (Summary / Why / Test plan), test-plan depth, screenshot expectations, contract-tagging style.

The check is cheap: 5 minutes of reading saves a round-trip review cycle. New repos with fewer than 5 merged PRs use the documented PR template instead.

Source: Junghwan Na harness pipeline article -- recent merged PRs are the production-grade prompt for the next PR.

## IMPORTANT: Guardrails

- **Directive changes go through `/sync-doe` with user approval.** Propose; the user merges. New directives also add a trigger to CLAUDE.md Progressive Disclosure.
- **Secrets live in `.env` only.** Code reads them via the documented loader; nothing else (commit messages, comments, logs) holds a live secret.
- Deliverables go to cloud services (Google Sheets, Slides, etc.) where the user can access them directly.
- Clean up `.tmp/` after tasks complete. Intermediate files are disposable.
- **Kit edits go through branches and PRs.** The kit's `.githooks/pre-commit` 'no direct-to-main' hook plus PR review are the canonical gate; the `guard_kit_writes` PreToolUse hook backs that up by blocking only irreversible Bash operations (recursive removal, force-push to kit main). For project-originated changes, `/sync-doe` is the translation tooling that strips project content, opens a kit branch, and opens the PR.
- **Destructive git operations require explicit user approval.** Force-push, revert, branch delete: show the diff and ask before acting.
- **When a hook blocks an action, fix the underlying issue and report back with evidence.** Show what was flagged, what changed, and the verification (re-run, grep, test pass).
- **Wave agents edit only files in their `Owns:` declaration.** Shared files (`todo.md`, `CLAUDE.md`, `learnings.md`, `STATE.md`) are written by the coordinator after `--merge`.

## Performance Budget

The performance budget when shipping to production:
- LCP (Largest Contentful Paint): < 2.5s
- JavaScript bundle: < 300KB (compressed)
- Lighthouse Performance: >= 80
- No render-blocking resources on critical path

Run `npx lighthouse <url> --output=json` or Playwright Lighthouse integration to verify.

## Feature Flag Guidance

Use a feature flag for gradual rollout or toggling without deploying:
- Use Vercel Flags + Edge Config when on the Vercel platform
- Feature flags are especially critical for a political tool where broken features have real consequences
- Add as a step in the deployment plan, not a separate feature
- Default: flag off in production, on in preview

## Staging & Environments

Vercel's model is preview-per-PR, not persistent staging. Each PR gets a unique preview URL for testing. For stakeholders who need a bookmarkable URL to check weekly, use a `staging` Git branch with auto-deploy or a promoted preview. Clarify needs before scoping.

## Delivery-Phase Triggers

These triggers apply during delivery (absorbed from the original CLAUDE.md trigger table):
- Version bump or release -> check `tasks/todo.md` ## Done for the version bump pattern
- Reviewing changes before commit -> suggest `/diff-review`
- Running `/wrap` -> run `python3 execution/health_check.py`, include in wrap summary
- Feature's final code step with unchecked [manual] items -> read `directives/manual-testing.md`, run `python3 execution/generate_test_checklist.py`
- Syncing DOE or updating framework version -> run `python3 execution/scan_docs.py` after sync
- Returning after absence -> suggest `/project-recap`

## Common Delivery Commands
```bash
python3 execution/build.py              # Rebuild monolith HTML from src/
python3 execution/verify.py             # Run contract verification
python3 execution/health_check.py       # Health check (--quick --json)
python3 execution/audit_claims.py       # Audit governed docs (--hook --json)
gh pr create                            # Create PR from feature branch
gh pr list --state open                 # List open PRs
```
