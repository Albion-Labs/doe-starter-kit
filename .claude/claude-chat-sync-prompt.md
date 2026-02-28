# Claude Chat Sync Prompt

Copy everything below the line and paste it into Claude Chat when starting a new project.

---

I have a project starter pack — a set of template files that define how I work with Claude Code. I need you to help me set up a new project using these templates.

## What the system is

**DOE Architecture** (Directive → Orchestration → Execution): Markdown SOPs define goals, Claude orchestrates, deterministic Python scripts execute. No inline execution when a script exists.

**9 Operating Rules** covering: plan before building, ask don't assume, check before spending, verify before delivering, explain simply, commit per task, delegate to subagents, check STATE.md + learnings.md + governed docs before commits, pitch improvements spontaneously.

**Self-Annealing**: Every failure feeds back into learnings files so the system handles that edge case next time.

**Break Glass Recovery**: 4-step procedure (STOP → Assess → Show → Ask) for when things go wrong. Non-technical user friendly.

**Progressive Disclosure**: Triggers that tell Claude where to look before starting common tasks. Points to learnings sections until proper directives are written.

**Version-Aware Planning**: Each step gets a version tag at planning time (step 1 = v0.X.0, step 2 = v0.X.1). Steps scoped to one committable unit.

**Documentation Governance**: Governed documents have YAML front-matter (Version, Last updated, Applies to, Updated by). Directive defines registry, versioning rules, and staleness detection.

**Claim Audit System**: `execution/audit_claims.py` runs 5 universal checks (front-matter, staleness, task format, roadmap consistency, orphan claims). Pre-commit hook runs fast checks. `/audit` and `/quick-audit` slash commands. Extensible with project-specific checks via `@register()` decorator.

## Template files included

| File | Purpose |
|------|---------|
| `CLAUDE.md` | Operating rules, guardrails, code hygiene, break glass, triggers |
| `STATE.md` | Session memory — current position, blockers, last session |
| `ROADMAP.md` | What to build — Up Next, Ideas, Parked, Complete |
| `todo.md` | Active task tracking — Current, Queue, Done (last 3) |
| `learnings.md` | Institutional memory — patterns, decisions, mistakes |
| `archive.md` | Completed features with full step detail |
| `settings.json` | Hook configuration for guardrails |
| `audit_claims.py` | Automated claim audit script (5 universal checks) |
| `documentation-governance.md` | Directive — governed doc registry + front-matter rules |
| `claim-auditing.md` | Directive — when/how to audit claims |
| `pre-commit` | Git hook — fast audit before every commit |
| `pitch.md` | `/pitch` slash command — generate product ideas |
| `wrap.md` | `/wrap` slash command — end-of-session routine with stats |
| Slash commands | Global (`~/.claude/commands/`): `/stand-up`, `/crack-on`, `/eli5`, `/roast`, `/shower-thought`, `/audit`, `/quick-audit`, `/wrap`, `/pitch` |

## What I need

When I describe a new project, help me:
1. Adapt CLAUDE.md for the project (update triggers, add project-specific rules)
2. Set up the directory structure (`directives/`, `execution/`, `tasks/`, `.claude/`, `.tmp/`)
3. Initialise STATE.md with the starting position
4. Create the initial ROADMAP.md with planned features
5. Set up git with hooks from settings.json + `.githooks/` (`git config core.hooksPath .githooks`)
6. Register governed documents in `directives/documentation-governance.md`
7. Add project-specific checks to `audit_claims.py` under a new `@register("yourproject")` section
8. Run first commit to establish baseline

Note: Slash commands are global — they live in `~/.claude/commands/` and work across all DOE projects. If they're not installed yet, copy them from the `global-commands/` folder in the starter kit to `~/.claude/commands/`.

The templates are attached. Use them as the starting point — don't reinvent the structure.
