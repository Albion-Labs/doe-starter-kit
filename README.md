# DOE Claude Code Starter Kit

A structured framework for AI-assisted development using Claude Code. **Directive → Orchestration → Execution.**

## What This Is

Albion-Labs' **internal operating harness** for AI-assisted development with Claude Code — shared with and maintained by the team, not a public starter kit. Used across Albion-Labs projects: `doe init` asks what you're building and installs only what applies (Next.js, Vite, Python, Go, Flutter, and static HTML).

## Quick Start

**New project:**
```bash
git clone https://github.com/Albion-Labs/doe-starter-kit.git ~/doe-starter-kit
mkdir my-project && cd my-project
bash ~/doe-starter-kit/setup.sh
```

The `doe init` wizard runs automatically: detects your framework, asks about collaboration mode and data handling, then scaffolds CLAUDE.md, directives, CI, hooks, and execution scripts tailored to your stack.

**Existing project (add DOE):**
```bash
cd my-existing-project
bash ~/doe-starter-kit/setup.sh
```

The wizard detects your existing code (package.json, go.mod, etc.), infers the framework, and adds DOE files alongside your code. Existing **project** files are never overwritten. Note: shared global tooling installed to `~/.claude/` (commands, hooks, scripts) **can be replaced** with the kit's versions — back up any custom global files before running setup. (Safe backup-before-overwrite is in progress.)

**After setup:** Start Claude Code and type `/stand-up`.

<details>
<summary>Manual setup (if you prefer not to use the script)</summary>

1. Copy `global-commands/*.md` (except README.md) to `~/.claude/commands/`
2. Copy `global-hooks/*.py` to `~/.claude/hooks/`
3. Copy `global-scripts/*.py` to `~/.claude/scripts/`
4. Copy `universal-claude-md-template.md` to `~/.claude/CLAUDE.md` (if you don't have one)
5. Merge PostToolUse hooks from `global-hooks/` into `~/.claude/settings.json`
6. Run `git config core.hooksPath .githooks` to activate git hooks
7. Start Claude Code — it reads CLAUDE.md automatically

</details>

## What's Included

**Framework**

- **CLAUDE.md** — 7 operating rules, progressive disclosure triggers, guardrails
- **STATE.md** — Session memory (blockers, current position)
- **36 directives** — SOPs for planning, building, delivery, security, testing, architecture, and more
- **25 execution scripts** — Verification, auditing, scoring, test orchestration, and quality gates
- **Audit system** — Automated false-positive detection with pre-commit hook
- **Multi-agent coordination** — Wave management, task claiming, heartbeats, merge protocol for parallel Claude Code sessions (`/agent-status` dashboard). Installs globally to `~/.claude/scripts/` and `~/.claude/hooks/`.
- **33 slash commands** — session lifecycle, quality checks, visual tools, multi-agent, utilities, and infrastructure (see below)
- **Session timer** — `/stand-up` (in kick-off mode) and `/crack-on` start a clock, `/sitrep` and `/wrap` report elapsed time
- **Gamification** — Session scoring, badges, streaks, leaderboard, themed wrap-up cards
- **Git hooks** — Pre-commit claim audit, commit message cleanup, pre-push methodology check
- **7 guardrail hooks** — block secrets, protect directives, block dangerous commands, guard kit writes, enforce review gate, confirm PR merge, block unnecessary admin-merge. These are **accident-prevention** (catching a careless paste), **not a security boundary** — they are string-matched denylists that a determined actor can phrase around.
- **4 custom agents** — Finder, Adversarial, Referee, ReadOnly for adversarial code review
- **Context monitoring** — Warns at 60% context usage, stops at 80% for graceful handoff

**Documentation (55 files)**

- **20 HTML tutorial pages** (`docs/tutorial/`) — Mintlify-style visual guides covering installation, first session, key concepts, commands, daily workflow, feature lifecycle, example apps, tips, and glossary
- **33 markdown reference docs** (`docs/reference/`) — searchable reference for every command, concept, workflow, file format, and example app

**Guides**

- **CUSTOMIZATION.md** — What to keep, what to customize, what to clear for your project
- **SYSTEM-MAP.md** — Complete file-by-file documentation and relationship map

## Slash Commands

33 commands in `global-commands/`. Install with `./setup.sh` or copy manually. Run `/commands` inside Claude Code for the full reference and installation health check.

| Category | Commands | Purpose |
|----------|----------|---------|
| **Session Lifecycle** | `/stand-up`, `/crack-on`, `/sitrep`, `/wrap`, `/eod` | Dual-mode stand-up, track progress, gamified wrap-up, end-of-day report |
| **Quality** | `/audit`, `/fact-check`, `/review`, `/codemap` | Comprehensive audit, accuracy checking, adversarial review, project index |
| **Visual** | `/project-recap`, `/diff-review`, `/plan-review`, `/generate-visual-plan`, `/generate-web-diagram`, `/generate-slides` | HTML visual explainers, diagrams, slide decks |
| **Multi-Agent** | `/agent-status`, `/agent-launch` | Wave dashboard, automated wave builder + task claiming |
| **Utility** | `/pitch`, `/roast` | Feature ideas, code roasts |
| **Infrastructure** | `/sync-doe`, `/pull-doe`, `/commands` | Sync DOE improvements, pull kit updates, installation health check |

**Smart filter:** The lifecycle commands check for DOE Kit sync opportunities. When comparing CLAUDE.md, they distinguish universal changes (Operating Rules, Guardrails, etc.) from project-specific additions (Directory Structure, triggers) — so you only get nudged when there's something genuinely worth syncing.

## Syncing Improvements From Projects

When you improve the DOE system during project work (new rules, better directives, new commands), sync improvements back here:

```bash
# From your project directory in Claude Code:
/add-dir ~/doe-starter-kit
# Then say:
# "Sync DOE improvements to the starter kit — read directives/starter-kit-sync.md first"
```

The sync directive handles stripping project-specific content, verifying the result, updating the changelog, bumping the version, and creating a GitHub release.

## Customizing for Your Project

See **CUSTOMIZATION.md** for the full guide. Short version:

1. Keep all operating rules and commands as-is
2. Edit CLAUDE.md triggers for your project's domain
3. Edit documentation-governance.md with your governed docs
4. Clear task/session content, keep structure
5. Add project-specific audit checks to `audit_claims.py`

## Versioning

The starter kit uses semantic versioning with GitHub releases. Every `/sync-doe` run that pushes changes will bump the version, update CHANGELOG.md, tag the commit, and create a release. See CHANGELOG.md for the full history.

## File Count

Around 305 files across 49 directories. The structured counts above (directives, scripts, commands, docs, hooks, agents) are enforced against the tree by `test_methodology.py` (scenario `readme_claims_match_disk`), so they can't silently drift. See SYSTEM-MAP.md for the complete map.
