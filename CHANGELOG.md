# Changelog

All notable changes to the DOE Claude Code Starter Kit.

Format: `## [vX.Y.Z] — YYYY-MM-DD` with sections for Added, Changed, Fixed, Removed.
Versioning: patch for small fixes, minor for new features/commands/directives, major for breaking changes to CLAUDE.md rules or directory structure.

---

## [v1.16.0] — 2026-03-05

Restructured ROADMAP.md with new sections for better project planning visibility.

### Added
- **ROADMAP.md** — 4 new sections: Suggested Next (Claude's strategic recommendation), Must Plan (important items needing scoping), Claude Suggested Ideas (AI-pitched additions), plus HTML comment block with section rules for Claude
- **ROADMAP.md** — every entry now requires a `*(pitched/added DD/MM/YY)*` timestamp

### Changed
- **CLAUDE.md Rule 9** — pitch routing now specifies Ideas (casual) vs Must Plan (important) sections
- **ROADMAP.md** — description updated from "living notepad" to "sections flow from most concrete to most speculative"

---

## [v1.15.1] — 2026-03-05

Remove Last 10 Days leaderboard from /wrap.

### Removed
- **`/wrap` Part 8 (Last 10 Days Leaderboard)** -- entire section, template, rules, and `result.leaderboard` reference
- Leaderboard mention from README.md /wrap description

---

## [v1.15.0] — 2026-03-05

Card format cleanup and smart CLAUDE.md diffing across all DOE Kit-aware commands.

### Changed
- **`/stand-up` kick-off card** — removed BLOCKERS and LEARNINGS rows, PROJECT right-aligned on header row, added last-session SUMMARY above PLAN
- **`/stand-up` status card** — removed BLOCKERS and DECISIONS rows
- **`/eod` card** — removed Blockers from POSITION AT EOD section
- **DOE Kit sync check** (`/stand-up`, `/crack-on`, `/sitrep`, `/wrap`) — smart CLAUDE.md diff: only flags universal section changes (Operating Rules, Guardrails, Code Hygiene, Self-Annealing), ignores project-specific sections (Directory Structure, triggers)
- **`/crack-on`** — genericized project-specific example in header rule
- **README.md** — updated `/stand-up` description and DOE Kit awareness paragraph

---

## [v1.14.6] — 2026-03-05

New `/agent-start` command and simplified `/agent-launch` instructions.

### Added
- **`/agent-start` command** — claims a wave task, cd's into the worktree, shows the assignment, and starts working. Replaces manual `python3 multi_agent.py --claim` + `cd` workflow.

### Changed
- **`/agent-launch` instructions** — "go" output now shows `/agent-start` instead of manual python3 commands. Cleaner onboarding for new terminals.

---

## [v1.14.5] — 2026-03-05

Docs update: command count and wrap system checks heading.

### Fixed
- **Command count** — README claimed 15/22 commands; actual count is 27. Updated both READMEs with missing commands: `/agent-launch`, `/codemap`, `/doe-health`, `/review`, `/pull-doe`
- **Wrap system checks heading** — Added `🔍 SYSTEM CHECKS` section heading before the bordered audit/DOE Kit box

---

## [v1.14.4] — 2026-03-05

Round 4 fix: session ID resolution for all commands.

### Fixed
- **CRITICAL: --complete/--fail/--abandon session resolution** — `--parent-pid` now auto-reads `.session-id-{pid}` file and sets `_session_override` in `main()`, so ALL commands resolve the correct session ID. Previously only `--claim` and hooks could find the session.
- **agent-launch instructions** — ALL multi_agent.py commands now include `--parent-pid $PPID` (claim, complete, fail, abandon)

---

## [v1.14.3] — 2026-03-05

Round 3 fix: per-terminal isolation via Claude Code PID.

### Fixed
- **CRITICAL: Session ID isolation (take 3)** — per-terminal files using Claude Code PID (`os.getppid()` in hooks, `$PPID` in Bash). Each terminal gets `.session-id-{pid}`, `.last-heartbeat-{pid}`, `.context-usage-{pid}.json`, `.context-warned-{pid}`. Solves the two-directory problem: hooks stay in project root, coordination files stay in project root, but each terminal's markers are isolated.
- **Wave completion cleanup** — glob-based cleanup of all PID-specific marker files (`*.session-id-*`, etc.)
- **agent-launch draft wave** — wave file written to `.draft-wave.json` (dotfile) until user approves, then moved to `wave-{N}.json`. Prevents orphaned wave files if session crashes before approval.
- **Wave file filtering** — `find_active_wave`/`find_latest_wave` now skip dotfiles (draft waves)
- **agent-launch instructions** — claim command now includes `--parent-pid $PPID` and explicit cd-to-worktree step

### Added
- **`--parent-pid` CLI arg** — passes Claude Code PID to `--claim` for session-id file naming

---

## [v1.14.2] — 2026-03-05

Round 2 adversarial review fixes + new `/agent-launch` command.

### Fixed
- **Reclaim log accuracy** — captures task-to-session mapping before modifying claims, so log entries attribute the correct stale session to each task
- **Context monitor glob** — matches all wave file names (not just `wave-*.json`), so budget detection works with custom waveIds like `comparison-filter`

### Added
- **`/agent-launch` command** — reads todo.md Queue, builds wave file, runs preview, launches on approval
- **Failed task retry docs** — documented that failed tasks are intentionally retryable (not terminal state)

---

## [v1.14.1] — 2026-03-05

Should-fix multi-agent bugs from adversarial review.

### Fixed
- **Reclaim** — preserves worktree branch (`delete_branch=False`) so new session can continue partial work
- **Wave sort** — `find_active_wave`/`find_latest_wave` use numeric index extraction instead of string sort (fixes wave-10 sorting before wave-2)
- **Validation dedup** — `cmd_validate` now delegates to `_analyze_wave` internally, eliminating ~100 lines of duplicated logic

### Added
- **`--fail` subcommand** — marks a task as failed with optional `--reason`, keeps worktree+branch for debugging, logs failure event

---

## [v1.14.0] — 2026-03-05

Critical multi-agent bug fixes from adversarial review.

### Fixed
- **Heartbeat hook** — uses fixed marker file (not per-PID) and reads session ID from `.tmp/.session-id` written by `--claim`
- **Context monitor** — corrected field names (`claimedTask`/`taskId` instead of `currentTask`/`id`), reads session ID from file instead of PID matching
- **Merge command** — auto-detects default branch (`master`/`main`) instead of hardcoding `master`

### Added
- `--claim` now writes `.tmp/.session-id` for hooks to read consistent session identity

---

## [v1.13.10] — 2026-03-05

Visual-explainer Progressive Disclosure triggers.

### Added
- 3 new triggers in CLAUDE.md: suggest `/diff-review` before commits, `/project-recap` after absence, `/plan-review` for alignment checks

---

## [v1.13.9] — 2026-03-05

Hook templates and pre-commit audit sweep.

### Added
- `hook-templates/javascript.json` — Claude Code hook template: warns on `console.log` and non-strict equality (`==`/`!=`) in JS/TS files
- `hook-templates/python.json` — Claude Code hook template: warns on bare exception catching and `shell=True` in subprocess calls
- `hook-templates/universal.json` — reference doc for hooks already included in the kit
- Pre-commit audit sweep — warnings (non-blocking) for `console.log` in JS/TS, bare `TODO` without reference, hardcoded localhost URLs
- Hook Templates section in CUSTOMIZATION.md — explains activation process

---

## [v1.13.8] — 2026-03-05

/doe-health diagnostic command.

### Added
- `/doe-health` command — 8-point integrity check (required files, CLAUDE.md line count, Progressive Disclosure targets, commands, hooks, git hooks, STATE.md freshness, kit version). Report only, never modifies.

---

## [v1.13.7] — 2026-03-05

/codemap command and /wrap structural change detection.

### Added
- `/codemap` command — generates `.claude/codemap.md` with project structure, key files, data flow, and active patterns
- `/wrap` step 8 — detects new/moved/deleted files and prompts to run /codemap

---

## [v1.13.6] — 2026-03-05

Self-annealing enhancement — root cause analysis and structured format for significant failures.

### Changed
- **Self-Annealing** section in CLAUDE.md — added "diagnose WHY" step, two-tier format (routine one-liners vs structured significant failures)
- **learnings.md** template — added structured failure format with What/Root cause/Fix/Prevention fields

---

## [v1.13.5] — 2026-03-05

Language best practices directives — prevention-over-detection guides for common agent failure modes.

### Added
- `directives/best-practices/javascript.md` — strict equality, async error handling, XSS prevention, cleanup patterns
- `directives/best-practices/python.md` — specific exceptions, mutable defaults, pathlib, injection prevention
- `directives/best-practices/html-css.md` — accessibility, semantic HTML, CSS custom properties, no inline styles
- `directives/best-practices/react.md` — dependency arrays, state immutability, derived state, cleanup effects

---

## [v1.13.4] — 2026-03-05

Architectural invariants directive — non-negotiable truths that survive any refactor.

### Added
- `directives/architectural-invariants.md` — 10 invariants covering DOE architecture, session integrity, safety, and extensibility. Includes escalation process when changes would violate an invariant.
- Progressive Disclosure trigger for architectural changes

---

## [v1.13.3] — 2026-03-05

/review command — adversarial code review via subagent.

### Added
- `/review` command — reads git diff, checks security/correctness/dead code/breaking changes/contract compliance, outputs PASS/PASS WITH NOTES/FAIL with structured findings. Advisory only, never modifies files.

---

## [v1.13.2] — 2026-03-05

Task contracts — testable completion criteria for non-trivial todo.md steps.

### Added
- **Task contract format** in todo.md format rules — `Contract:` block with verifiable criteria. Prevents premature "done" marking on complex steps.

---

## [v1.13.1] — 2026-03-05

CLAUDE.md enrichments — identity reframe, research separation, sycophancy-aware verification, subagent context savings, and best practices trigger.

### Changed
- **Who We Are** — reframed from role-specific ("non-technical founder") to generic ("human defines intent, Claude builds")
- **Rule 2** — added research/implementation separation guidance for significant research tasks (3+ approaches)
- **Rule 4** — added sycophancy-aware evaluation: use neutral verification prompts, not leading questions
- **Rule 7** — added concrete context savings numbers (15k tokens → 500-token summary = 30x saving)

### Added
- Progressive Disclosure trigger: read language best practices directives before writing code

---

## [v1.13.0] — 2026-03-05

Added /pull-doe — the reverse of /sync-doe. Pulls kit updates into a project with version-aware diffing, file categorization, and safe merging.

### Added
- `/pull-doe` command — reverse sync (kit → project) with version-aware diffing, analysis box, and result summary
- `directives/starter-kit-pull.md` — 15-step pull procedure with file categorization (global installs, hooks, CLAUDE.md, templates, directives, execution scripts)
- Progressive Disclosure trigger for starter-kit-pull directive

### Changed
- `/sync-doe` — added cross-reference to `/pull-doe` for reverse direction

---

## [v1.12.7] — 2026-03-05

Upgraded /crack-on to bordered card format matching stand-up, sitrep, and other commands.

### Changed
- `/crack-on`: full bordered card with project in header, feature, progress bar, DOE Kit status, picking-up step with plain English summary, and model row
- `/crack-on`: removed separate model check paragraph — now integrated into card

---

## [v1.12.6] — 2026-03-05

Bordered card alignment fix and bidirectional DOE sync detection across all 8 global command files.

### Changed
- All bordered commands: explicit `line()` helper pattern in BORDER rules — prevents header misalignment
- All bordered commands: mandate "never construct `f"│{...}│"` manually" in generation rules
- 5 commands: bidirectional sync detection (inbound tag comparison + outbound file diff, not just file diff)
- Files: commands, crack-on, eod, sitrep, stand-up, sync-doe, vitals, wrap

---

## [v1.12.5] — 2026-03-05

Model allocation rules — plans and subagents must specify which model and thinking level to use.

### Changed
- Rule 1: plans must include recommended model + thinking level per step
- Rule 7: subagents must use deliberate model selection (Opus/Sonnet/Haiku)
- `/sitrep`: DOE KIT diff wording fix ("check" vs "count")

---

## [v1.12.4] — 2026-03-04

Standardised DOE sync status format across all 6 global commands. Compact notation replaces verbose text.

### Changed
- DOE sync status: compact `*` format across `/commands`, `/crack-on`, `/sitrep`, `/stand-up`, `/vitals`, `/wrap`
- Synced state: bare version (no tick, no "synced" text)
- Unsynced state: `vX.Y.Z *` (asterisk suffix)
- `/stand-up` WARNINGS: omit section when all PASS (was showing "None ✓")

---

## [v1.12.3] — 2026-03-04

Compressed CLAUDE.md from 117 to 83 lines by moving Break Glass to a directive and tightening 3 rules. Overhauled /sitrep.

### Added
- `directives/break-glass.md` — emergency recovery procedure (extracted from CLAUDE.md)
- Progressive Disclosure trigger for break-glass directive
- `/sitrep` COMPLETED section — cumulative session work log
- `/sitrep` push status indicator (pushed/committed)
- `/sitrep` DOE version in header row

### Changed
- CLAUDE.md compressed: Rule 1 (planning), Rule 8 (pre-commit checks), hook response format (117 → 83 lines)
- `/sitrep` reordered: ACTIVE shown first, DONE second, PENDING renamed to UP NEXT (capped at 5)
- `/sitrep` box auto-stretches to fit content instead of truncating
- `directives/starter-kit-sync.md` — Steps 7 and 9 now require bordered boxes (diff summary + changelog) for approval

### Removed
- Break Glass section from CLAUDE.md (moved to directive)
- `/sitrep` BLOCKERS, QUEUE, and DOE KIT rows (DOE version moved to header)

## [v1.12.2] — 2026-03-04

### Added
- **`/sync-doe` analysis box** — new required Analysis Box section showing a bordered diff summary with header (version right-aligned), context summary, numbered file list, verdict, and recommendation. Displayed before proposing changes so the user can approve or reject from a clear overview.

---

## [v1.12.1] — 2026-03-04

### Added
- **Universal learnings template** — added 3 Shell & Platform entries (emoji box-drawing, zsh nullglob, `$$` subshell PID), new Hooks & Session Files section (orphan file prevention), new Output section (single-block assembly, re-present script output as text). Template now has 6 sections and 11 learnings.

---

## [v1.12.0] — 2026-03-04

### Changed
- **`/commands` reference** — updated from 15 to 22 commands. Added `/fact-check` to Quality section. Added new Visual section with 6 commands: `/project-recap`, `/diff-review`, `/plan-review`, `/generate-visual-plan`, `/generate-web-diagram`, `/generate-slides`.

---

## [v1.11.8] — 2026-03-04

### Fixed
- **`/sync-doe` result box** — replaced hardcoded box width with dynamic computation (`W = max(len(line)) + 4`). Long summary lines no longer break the right border.

---

## [v1.11.7] — 2026-03-04

### Changed
- **`/wrap` layout** — moved NEXT UP section to render after the footer (was between Decisions and Numbers). Renumbered parts 6-9.

---

## [v1.11.6] — 2026-03-04

### Fixed
- **Session timer** — replaced per-PID `.session-start-$$` with single `.tmp/.session-start` file across 6 commands (`/stand-up`, `/crack-on`, `/sitrep`, `/wrap`, `/eod`, `/commands`). `$$` returned a different subshell PID per Bash tool call, making the timer unreliable. Worktrees handle multi-session isolation, so per-PID files were unnecessary.

---

## [v1.11.5] — 2026-03-04

### Changed
- **Box-drawing rules** — clarified in 5 global commands (`/audit`, `/sitrep`, `/stand-up`, `/sync-doe`, `/wrap`): explicitly use Unicode box-drawing characters (`┌─┐`, `├─┤`, `└─┘`, `│`) for borders, ASCII-only for content inside borders

---

## [v1.11.4] — 2026-03-04

### Changed
- **Commands README** — updated from 15 to 22 commands, added Visual category (`/project-recap`, `/diff-review`, `/plan-review`, `/generate-visual-plan`, `/generate-web-diagram`, `/generate-slides`), added `/fact-check` to Quality, reorganised table layout

---

## [v1.11.3] — 2026-03-04

### Changed
- **`/audit` result box** — output now ends with a programmatic bordered result box (matching `/sync-doe` and `/wrap` style) showing PASS/WARN/FAIL counts and key stats

---

## [v1.11.2] — 2026-03-04

### Added
- **`/wrap` agents stat** — new "agents spawned" metric in The Numbers section, counted from Agent tool calls in the session

### Changed
- **`/wrap` session time label** — shortened from "total session time" to "session time"
- **`/wrap` system checks box** — replaced hand-padded example boxes with programmatic generation instruction (collect lines, find max length, `.ljust()`)

### Removed
- **`/wrap` One-Stat Highlight** — removed Part 9 (redundant with The Numbers). Parts renumbered from 11 to 10.

---

## [v1.11.1] — 2026-03-04

### Changed
- **`/wrap` title card** — project name now uses spaced-out uppercase text (e.g. `M O N T Y`) centered in the box, generated from the current directory name. Narrative lines render as plain paragraphs below the code fence (no indentation).
- **`/wrap` output** — removed haiku section. Parts renumbered from 12 to 11. Narrative sections (vibe, journey, commits, decisions, next up) now appear before data tables (numbers, timeline, leaderboard).

---

## [v1.11.0] — 2026-03-04

### Added
- **7 new universal commands:** `diff-review.md` (visual HTML diff review), `fact-check.md` (verify doc accuracy against codebase), `generate-slides.md` (magazine-quality HTML slide decks), `generate-visual-plan.md` (visual HTML implementation plans), `generate-web-diagram.md` (standalone HTML diagrams), `plan-review.md` (visual HTML plan review), `project-recap.md` (visual HTML project recap).

---

## [v1.10.2] — 2026-03-04

### Changed
- **`sync-doe.md` result box templates** — moved status emojis above the box as standalone signal lines (e.g. `✅ SYNCED` before the bordered box). Emojis stay visible for quick-glance scanning without breaking box-drawing alignment.

---

## [v1.10.1] — 2026-03-04

### Fixed
- **`sync-doe.md` result box templates** — removed emojis from inside bordered boxes (they render double-width, breaking alignment). Added programmatic box generation rule and ASCII-only constraint matching other commands.

---

## [v1.10.0] — 2026-03-04

### Changed
- **Per-PID session timers for multi-terminal safety.** Session clock files changed from `.tmp/.session-start` to `.tmp/.session-start-$$` (shell PID). Each terminal gets an independent timer. Stale PID files are pruned on `/crack-on`, `/stand-up`, and `/wrap` via `kill -0` checks. `/eod` scans all PID files to detect multiple active sessions. Updated all 6 command files: `crack-on.md`, `stand-up.md`, `sitrep.md`, `wrap.md`, `eod.md`, `commands.md`.
- **Progress bar border exception** in `stand-up.md` — `█` and `░` characters now explicitly permitted inside bordered boxes (they render at fixed width in terminals).

---

## [v1.9.4] — 2026-03-04

### Added
- **Code Hygiene rule: plans go in the project.** New CLAUDE.md rule requiring plans to be written to the project's `.claude/plans/` directory with descriptive filenames, not to `~/.claude/plans/`. Prevents plan files from landing in the global directory where they're invisible to the project.

---

## [v1.9.3] — 2026-03-04

### Fixed
- **`wrap_stats.py` step counting** — `count_steps_completed_today()` counted all `[x]` steps with today's date, inflating `stepsCompleted` across multiple sessions on the same day. Replaced with `count_steps_completed_since()` which parses the `HH:MM DD/MM/YY` timestamp and only counts steps completed after the session start time.

---

## [v1.9.2] — 2026-03-04

### Fixed
- **`context_monitor.py` file accumulation** — replaced per-PID tracker files (`.context-{pid}.json`) with a single `.context-usage.json` that gets overwritten each tool call. Prevents hundreds of orphan files accumulating in `.tmp/` per session. Same fix applied to warn marker (`.context-warned-{pid}` → `.context-warned`).

---

## [v1.9.1] — 2026-03-04

### Added
- **`copy_plan_to_project.py` hook** — PostToolUse hook that auto-copies plans written to `~/.claude/plans/` into the current project's `.claude/plans/` directory. Fires after `write|edit` tool calls targeting `~/.claude/plans/*.md`.
- **PostToolUse section in `settings.json`** — registers the plan-copy hook

---

## [v1.9.0] — 2026-03-04

### Changed
- **Multi-agent system moved to global install** — no more per-project copies. `multi_agent.py` → `~/.claude/scripts/`, `heartbeat.py` + `context_monitor.py` → `~/.claude/hooks/`, `/hq` → `~/.claude/commands/`. Install once, works across all projects.
- **`setup.sh` extended** — 3 new install sections: hooks to `~/.claude/hooks/`, scripts to `~/.claude/scripts/`, merges PostToolUse into `~/.claude/settings.json`
- **Path refactor** — all multi-agent Python files use `Path.cwd()` instead of `Path(__file__)` for global execution
- **`--project-root` override** — `multi_agent.py` accepts `--project-root DIR` to specify the project directory explicitly
- **Template `.claude/settings.json` now PreToolUse-only** — PostToolUse hooks are merged into the global settings by `setup.sh`

---

## [v1.8.0] — 2026-03-04

### Added
- **Multi-agent coordination system** — `execution/multi_agent.py` for running 2-4 parallel Claude Code sessions. Wave management, task claiming, session registry, heartbeats, merge protocol, cost tracking. All state in `.tmp/waves/`.
- **`/hq` command** — `.claude/commands/hq.md` project-level dashboard. Shows wave status, terminal liveness, task progress, cost estimates, merge order. Modes: no_wave (help), active (live dashboard).
- **Heartbeat hook** — `.claude/hooks/heartbeat.py` PostToolUse hook updating session liveness every 30s during active waves. Stale sessions (>2 min) are detectable and reclaimable.
- **Context monitor hook** — `.claude/hooks/context_monitor.py` PostToolUse hook tracking estimated context usage. Warns at 60%, stops at 80% for graceful handoff. Model-aware budgets during waves (haiku: 30k, sonnet: 80k, opus: 200k).
- **Active wave audit check** — `check_active_wave` in `audit_claims.py` warns when a wave is active and results may be incomplete until merge. Runs in fast/hook mode.
- **PostToolUse hooks in settings.json** — heartbeat and context monitor fire after every tool use

---

## [v1.7.4] — 2026-03-03

### Removed
- **`/wrap`** — removed fortune cookie line from session footer. Adds noise without value.

---

## [v1.7.3] — 2026-03-03

### Changed
- **`/stand-up` (status mode)** — reordered card: PHASE GOAL now appears above PROGRESS for better readability. Added NEXT STEP line showing the first uncompleted step from todo.md, so the immediate task is always visible at a glance.

---

## [v1.7.2] — 2026-03-03

### Fixed
- **`execution/audit_claims.py`** — skip version tag WARN for `[INFRA]` tasks. Infrastructure features don't bump app version, so their todo steps never have version tags. `parse_completed_tasks()` now tracks heading context and `check_task_format()` skips the check for `[INFRA]` sections.

---

## [v1.7.0] — 2026-03-02

### Changed
- **`/wrap`** — lightweight rewrite. Removed scoring/badges/genre system. One dramatic narrative (no genre selection), added session haiku, one-stat highlight, fortune cookie footer. Leaderboard now shows commits/lines instead of scores. Vibe check determined inline instead of by script.
- **`/roast`** — removed score trend and badge pattern analysis bullets (stats.json no longer has these fields)
- **`/stand-up`** — removed "score trends" FOCUS bullet
- **`/eod`** — removed SCORE line from card, simplified session list to title + duration (no scores/badges)
- **`/commands`** — updated `/wrap` and `/roast` descriptions to reflect lightweight wrap

### Removed
- Scoring formula, badge definitions, genre selection, multiplier system, high score tracking from `/wrap`
- `execution/wrap_stats.py` scoring logic (978 → ~150 lines, now metrics + streak only)

---

## [v1.6.0] — 2026-03-02

### Added
- **`/eod`** — new end-of-day report command. Aggregates all sessions, commits, features, and position into one bordered summary. Shows day stats, session list, semantic "What Got Done" grouping, position at EOD, and day vibe.
- **`execution/wrap_stats.py`** — new deterministic scoring script (978 lines). Handles all session scoring computation: git metrics, streak, multiplier, raw/final score, badge evaluation (with once-per-day dedup), high score check, leaderboard consolidation. Outputs JSON for the `/wrap` prompt to render.

### Changed
- **`/stand-up`** — added WARNINGS section (surfaces audit WARN/FAIL findings in kick-off card with detail lines and "Fix now?" suggestions) and FOCUS section (2-3 coaching bullets from `stats.json` analysis: infra/product ratio, stale WARNs, commits/session trends, steps completed, time-of-day patterns, score trends)
- **`/vitals`** — added mandatory audit detail lines rule: WARN/FAIL items must each be shown on indented detail lines, using `--json` flag for reliable parsing
- **`/roast`** — added "And you..." developer habit analysis section: roasts session timing, infra/product ratio, score trends, badge patterns, commits/session, steps throughput, and streak from `stats.json`
- **`/wrap`** — rewrote to delegate all scoring computation to `execution/wrap_stats.py`. Steps 2+3 replaced with single script call. Display sections now reference `result.*` JSON fields. Prompt reduced from ~22K to ~17K chars.

---

## [v1.5.0] — 2026-03-02

### Changed
- **`/stand-up`** — rewritten as context-aware dual-mode command. Detects `.tmp/.session-start`: **kick-off mode** (no session) starts clock, reads project state, shows bordered card with plan, waits for sign-off. **Status mode** (session active) shows bordered daily status card with progress, momentum, activity since last milestone, blockers, pending decisions, and queue. Read-only in status mode.
- **`/commands`** — updated `/stand-up` description for dual-mode, updated smart filter section
- **Reference docs** — updated stand-up descriptions across README, SYSTEM-MAP, CUSTOMIZATION, and global-commands/README
- **CUSTOMIZATION** — corrected command count from 11 to 13 (added `/vitals`, `/commands` to list)

---

## [v1.4.0] — 2026-03-02

### Added
- **`/vitals`** — new workspace health check command: git status, quick audit, DOE Kit sync, STATE.md alignment, stale temp files. Bordered output with ✓/⚠️ per check.

### Changed
- **`/wrap`** — added quick audit to Step 1 housekeeping; replaced plain footer with bordered "System Checks" section showing audit results and DOE Kit sync status together
- **`/commands`** — updated to 13 commands, added `/vitals` under Quality category
- **README** — command count 12 → 13, added `/vitals` to Quality row in table
- **SYSTEM-MAP** — added vitals.md to file table, command reference, and directory tree

---

## [v1.3.0] — 2026-03-02

### Added
- **`setup.sh`** — one-command installer: copies commands to `~/.claude/commands/`, copies universal CLAUDE.md template (if none exists), activates git hooks, writes version receipt to `~/.claude/.doe-kit-version`
- **`/commands`** — new slash command replacing `/README`. Shows full command reference by category, checks installation status (missing commands), and checks GitHub for kit updates
- **Slash Commands section in README** — category table with smart filter explanation, links to `/commands` for full reference
- **Manual setup fallback** — collapsible details block in Quick Start for users who prefer not to use the script

### Changed
- Quick Start simplified from 6 steps to 3 (clone → `./setup.sh` → `/stand-up`)
- `global-commands/README.md` is now a short GitHub directory readme (no longer doubles as a command)
- Command count updated from 11 → 12 across README and command reference

### Removed
- `/README` command — replaced by `/commands`

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
