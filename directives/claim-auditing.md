# Directive: Claim Auditing

## Goal
Catch false positives — things claimed as done without proof — before they reach stakeholders.

## When to Use
- Before any external demo or stakeholder presentation
- Before marking a phase as COMPLETE in the roadmap
- When completing a feature (as part of the retro step)
- Anytime via `/audit` (full) or `/quick-audit` (fast checks only)
- Automatically on every commit (pre-commit hook runs fast checks)

## Inputs
- `execution/audit_claims.py` — the audit script
- Governed documents with front-matter (see `directives/documentation-governance.md` registry)
- Task tracker (`tasks/todo.md`, `tasks/archive.md`)
- Roadmap (`ROADMAP.md`)
- App state (`STATE.md`)

## Process
1. Run `python3 execution/audit_claims.py` for a full audit, or `--hook` for fast checks only.
2. Review findings: PASS (clean), WARN (advisory), FAIL (must fix before proceeding).
3. For each FAIL: fix the underlying issue, not the symptom. If a doc is stale, update the doc — don't just bump the version.
4. For each WARN: assess whether action is needed. WARNs don't block commits but may indicate drift.
5. If a FAIL was caught by the pre-commit hook, follow the hook feedback format (CLAUDE.md guardrail):
   ```
   Hook flagged: [what]
   Fixed: [what you did]
   Proof: [evidence]
   ```
6. If the audit revealed a systemic gap, add a learning to `learnings.md` so the system improves.

## Outputs
- Terminal report with PASS/WARN/FAIL per check
- `.tmp/last-audit.txt` — saved copy of last run
- JSON mode (`--json`) for machine consumption

## Edge Cases
- `learnings.md` may not have front-matter yet — this is a known WARN, not a FAIL
- Pre-versioning tasks may lack per-step version tags — these produce WARNs in orphan-claims
- Running outside a git repo skips commit-evidence checks gracefully
- Pre-commit hook runs fast checks only (<1 second) — slow checks are for manual/slash command use

## Verification
- [ ] `python3 execution/audit_claims.py` runs without errors
- [ ] `python3 execution/audit_claims.py --hook` completes in <1 second
- [ ] `python3 execution/audit_claims.py --json` produces valid JSON
- [ ] Pre-commit hook blocks commits when a FAIL is present
- [ ] `/audit` and `/quick-audit` slash commands produce expected output
