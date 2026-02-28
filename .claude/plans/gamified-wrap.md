# Gamified Session Wrap-Up System

## Context

The `/wrap` command produces a gamified session summary with scoring, badges, streaks, genre-themed title cards, and persistent stats tracking. The wrap command is a **prompt** (not executable code), so all logic is instructions for Claude to follow using git data + a stats file.

## Features

1. **Adaptive Title Card** — genre picked by session characteristics (Star Wars crawl, noir, heist, fantasy, haiku, horror, war, sports, action). Big sessions get a full Star Wars opening crawl.

2. **20 Achievement Badges** — earned from real git data, rendered as bordered ASCII cards. Only earned badges shown.

3. **Scoring System** — base score from commits, lines, files, steps, learnings, recoveries. Multiplied by daily streak bonus. NEW HIGH SCORE celebration when beaten.

4. **Daily Streak with Slow Ramp** — 1.0x to 3.0x over 21 days. Continues if last session was yesterday, resets if 2+ days gap.

5. **Last 10 Days Leaderboard** — always 10 rows, gaps shown as `--`.

6. **Diff of the Day** — most interesting change + witty one-liner.

7. **Mood/Vibe Rating** — based on failure ratio and session shape.

8. **Persistent Stats** (`.claude/stats.json`) — lifetime totals, streak tracking, high scores, badge counts, last 20 sessions.

9. **Claude Chat Sync Prompt** — copy-paste prompt to sync Claude Chat with Claude Code changes. Uses verification tests to prove comprehension.

## Key Files

| File | Purpose |
|---|---|
| `.claude/commands/wrap.md` | The full gamified wrap prompt |
| `.claude/stats.json` | Persistent stats across sessions |
| `.claude/claude-chat-sync-prompt.md` | Template for syncing Claude Chat |

## Design Decisions

- Prompt-only approach (no execution script) — Claude reads git data and stats.json inline
- Streak multiplier uses slow ramp (1.0x→3.0x over 21 days) — rewards long-term consistency
- stats.json validated before write — if corrupted, back up to `.bak` and reinitialise
- Housekeeping (STATE.md, todo.md, learnings) runs first as Step 1 before any gamification
