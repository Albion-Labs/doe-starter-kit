# Changelog

All notable changes to the DOE Claude Code Starter Kit.

Format: `## [vX.Y.Z] — YYYY-MM-DD` with sections for Added, Changed, Fixed, Removed.
Versioning: patch for small fixes, minor for new features/commands/directives, major for breaking changes to CLAUDE.md rules or directory structure.

---

## [v1.2.1] — 2026-03-01

### Changed
- `/sync-doe` now shows a bordered result summary box at the end of every sync — `✅ SYNCED`, `⏭️ NO CHANGES`, `❌ REJECTED`, or `⚠️ BLOCKED` with explanation and kit version

---

## [v1.2.0] — 2026-03-01

### Added
- **CLAUDE.md Rule 10: Parallelise by default** — automatically spawn sub-agents for independent tasks, flag sequential dependencies, commit one-at-a-time per Rule 6
- **CLAUDE.md Guardrail: Protect starter kit** — blocks direct edits to `~/doe-starter-kit`; all changes must go through `/sync-doe`

### Changed
- Renamed `/sync-kit` to `/sync-doe` across all files — command name, file (`sync-doe.md`), and 40+ references in 10 files. Better describes syncing DOE framework improvements.

---

## [v1.1.1] — 2026-02-28

### Added
- `/wrap` footer now shows DOE Kit version and sync status as the last line before closing

---

## [v1.1.0] — 2026-02-28

### Added
- **DOE Kit awareness** — `/stand-up`, `/crack-on`, `/sitrep`, and `/wrap` now check `~/doe-starter-kit` if it exists
- `/stand-up` and `/crack-on` show kit version + pending change count at session start
- `/sitrep` shows `DOE KIT` row with version and sync status
- `/wrap` nudges `/sync-doe` when DOE files have changed since last sync
- All four commands recommend `/sync-doe` when pending changes are detected

---

## [v1.0.0] — 2026-02-28

Initial release. 40 files across 8 directories.

### Added
- **CLAUDE.md** — 9 operating rules, guardrails, progressive disclosure triggers, directory structure
- **STATE.md** — Session memory template
- **ROADMAP.md** — Product roadmap template
- **SYSTEM-MAP.md** — Complete file-by-file documentation and relationship map
- **CUSTOMIZATION.md** — Guide for adapting the kit to new projects
- **Directives** — `_TEMPLATE.md`, `documentation-governance.md`, `claim-auditing.md`, `starter-kit-sync.md`
- **Execution** — `audit_claims.py` with universal checks and project extension point
- **11 slash commands** — `/stand-up`, `/crack-on`, `/wrap` (gamified), `/sitrep`, `/sync-doe`, `/pitch`, `/audit`, `/quick-audit`, `/roast`, `/eli5`, `/shower-thought`
- **Guardrail hooks** — `block_dangerous_commands.py`, `block_secrets_in_code.py`, `protect_directives.py`
- **Git hooks** — `commit-msg` (strip AI co-author trailers), `pre-commit` (fast audit)
- **Session timer** — `/stand-up` and `/crack-on` start clock, `/sitrep` and `/wrap` report duration
- **Gamification** — Scoring, badges, streaks, leaderboard, themed wrap-up cards
- **README.md** — Quick start guide and feature overview

### Fixed
- `commit-msg` hook uses macOS-compatible `sed -i ''` syntax
- `/sitrep` STATUS field has clearer instruction wording
- `/wrap` score table has separate high score / non-high score templates with `d[streak]` multiplier format

### Changed
- `/sync-doe` includes up-to-date check — stops early if nothing to sync
- Sync directive includes safety guardrails: pull-before-compare, three-way diff, additive merging, git stash backup
