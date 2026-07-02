# Project Configuration

## Who We Are
The human defines intent, constraints, and verification criteria. Claude recommends technical approach, explains trade-offs simply, then implements. The human steers — Claude builds.

## Architecture: DOE (Directive -> Orchestration -> Execution)
Probabilistic AI handles reasoning. Deterministic code handles execution. Non-negotiable.
- **Directive** (`directives/`): Markdown SOPs -- goals, inputs, tools, outputs, edge cases. Pure prose.
- **Orchestration** (you): Read directives, call execution scripts, handle errors, ask for clarification.
- **Execution** (`execution/`): Python scripts that do the work deterministically — no hidden randomness, no unconfirmed paid API calls. Credentials in `.env`. (Reads of git state/clock and explicit network calls are the I/O layer — keep them obvious.)
IMPORTANT: Check `execution/` first; reuse existing scripts whenever they cover the task.

## Core Behaviour
1. **Plan before building.** Check `tasks/todo.md` + `STATE.md`. -> `directives/planning-rules.md`
2. **Ask when ambiguous.** Match the question to the smallest decision that unblocks you. Separate research from implementation sessions.
3. **Check before spending.** Confirm with the user before running paid API calls.
4. **Verify before delivering.** Run it, test it, confirm it matches spec. -> `directives/delivery-rules.md`
5. **Explain simply.** Use plain language; introduce jargon after defining it. Frame trade-offs in terms the user can evaluate.
6. **One task, one session.** Feature branches, commit per step. -> `directives/building-rules.md`
7. **Shared-file awareness.** In parallel: check contention on STATE.md, learnings.md, todo.md, CLAUDE.md. -> `directives/context-management.md`

## Directory Structure
```
directives/    # SOPs -- read before starting any task
execution/     # Deterministic Python scripts
tasks/         # todo.md + plans
.claude/       # Hooks, settings, plans, commands, agents
.githooks/     # Git hooks (activate: git config core.hooksPath .githooks)
docs/          # Visual documents -- version-controlled
.tmp/          # Temporary files (disposable)
STATE.md  learnings.md  .env
```

## Common Commands
```bash
# Run DOE methodology tests
python3 execution/test_methodology.py

# Run health check (stubs, TODOs, empty functions)
python3 execution/health_check.py

# Run contract verification
python3 execution/verify.py

# Activate git hooks
git config core.hooksPath .githooks

# Create PR from feature branch
gh pr create --title "..." --body "..."
```
<!-- Add project-specific build/test/deploy commands here -->

## Gotchas
- **Warning:** `.env` files stay local; the pre-commit hook gates accidental commits, provided `git config core.hooksPath .githooks` has been run on this clone.
- **Caveat:** After context compaction, Claude loses all loaded directives. Re-read the triggers relevant to your current task after a `/clear` or long conversation.
- **Workaround:** If a pre-commit hook fails with "not executable", run `chmod +x .githooks/*` to fix permissions.
- **Kit-write model:** kit edits flow through branches and PRs. The `.githooks/pre-commit` 'no direct-to-main' hook plus PR review are the canonical gate; `guard_kit_writes` blocks only irreversible Bash operations (recursive removal, force-push to kit main). See `directives/kit-development.md` ## Kit-write model: PR-only.
- **Note:** `execution/` scripts avoid hidden nondeterminism — no `random`, no interactive `input()`, no unconfirmed paid API calls. Some read git state or the clock explicitly; that's the I/O layer, kept obvious. AI reasoning lives in orchestration (CLAUDE.md + directives). Enforced by the `execution_determinism` scenario in `execution/test_methodology.py` (new pure scripts can't silently add randomness/network; the genuine I/O scripts are allowlisted).
<!-- Add project-specific gotchas here as you discover them -->

## Context Rules
After context compaction, treat ALL directives as unloaded. Re-read triggers for your current task.
First session on a brand new project: load `directives/planning-rules.md` + `directives/building-rules.md`.
**1% rule:** If there is even a 1% chance a trigger applies, load it. See `directives/rationalisation-tables.md` ## 6.

## Triggers
- Planning/scoping -> `directives/planning-rules.md`
- Building/coding -> `directives/building-rules.md`
- Delivering (retro, PR, sign-off, wrap) -> `directives/delivery-rules.md`
- Parallel work / context management -> `directives/context-management.md`
- Self-annealing / learnings curation -> `directives/self-annealing.md`
- Platform evolution -> `directives/framework-evolution.md`
- Adversarial review / `/review` -> `directives/adversarial-review/`
- Subagent work -> `directives/subagent-protocol.md`
- About to skip a guardrail -> `directives/rationalisation-tables.md`
- Something went seriously wrong -> `directives/break-glass.md`
- Importing external data (API, CSV, download) -> `learnings.md` for known API behaviours
- Dataset or legal position change -> `directives/documentation-governance.md`
- Auditing claims -> `directives/claim-auditing.md`, run `/audit`
- DOE kit sync -> `directives/starter-kit-sync.md`
- Pulling DOE kit updates -> `directives/starter-kit-pull.md`
- Parallel sessions on same project (worktree setup, branch isolation) -> `directives/parallel-worktrees.md`
- Security-sensitive code (input, auth, rendering, headers) -> `directives/security-rules.md`
- Writing code -> `directives/best-practices/` for the language
- Refactoring / architecture -> `directives/architectural-invariants.md`
- Testing setup -> `directives/testing-strategy.md`
- Personal data features -> `directives/data-compliance.md` (DPIA is hard blocker)
- Political / electoral-campaign data -> `directives/political-data.md` (criminal liability; political layer)
- New functions / debugging -> `directives/best-practices/tdd-and-debugging.md`
- DOE feature request -> `/request-doe-feature`
- [APP] feature with visual output -> `directives/chrome-verification.md`
- Database / SQL / data protection -> `directives/data-safety.md`
- Security incident or breach -> `directives/incident-response.md`

<!-- Add project-specific triggers here as the system grows -->
