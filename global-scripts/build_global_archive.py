#!/usr/bin/env python3
"""Generate a global portfolio dashboard HTML page from project registry and stats.

Usage:
    python3 ~/.claude/scripts/build_global_archive.py [--registry PATH] [--output PATH]
"""

import argparse
import html
import json
import os
import re
import sys
from datetime import datetime, timedelta


def esc(text):
    """HTML-escape a string."""
    return html.escape(str(text))


# ── Color Palette ──
# Each entry: (css_var_dark, css_var_light, css_var_name)
PALETTE = [
    ("#4ade80", "#16a34a", "green"),
    ("#67e8f9", "#0891b2", "cyan"),
    ("#fbbf24", "#d97706", "amber"),
    ("#f87171", "#dc2626", "red"),
    ("#6c63ff", "#5046e5", "accent"),
]


def get_project_color(idx):
    """Return (dark_hex, light_hex, var_name) for a project index."""
    if idx < len(PALETTE):
        return PALETTE[idx]
    return PALETTE[4]  # accent for overflow


def format_number(n):
    """Format a number with k suffix for thousands."""
    if n >= 10000:
        return f"{n / 1000:.1f}k"
    if n >= 1000:
        return f"{n / 1000:.1f}k"
    return str(n)


def parse_date(s):
    """Parse YYYY-MM-DD string to datetime.date."""
    return datetime.strptime(s, "%Y-%m-%d").date()


def format_date_short(d):
    """Format date as '10 Mar'."""
    return d.strftime("%-d %b")


def format_dow(d):
    """Format date as 'Mon', 'Tue', etc."""
    return d.strftime("%a")


def get_week_start(d):
    """Get the Monday of the week containing date d (ISO weeks: Mon-Sun)."""
    return d - timedelta(days=d.weekday())


def days_between(d1, d2):
    """Days from d1 to d2 (can be negative)."""
    return (d2 - d1).days


def load_projects(registry_path):
    """Load project registry and stats for each project.

    Returns list of dicts with registry info + stats data.
    """
    if not os.path.isfile(registry_path):
        return None  # registry missing

    with open(registry_path, "r", encoding="utf-8") as f:
        registry = json.load(f)

    projects = []
    for entry in registry.get("projects", []):
        path = entry.get("path", "")
        name = entry.get("displayName", entry.get("name", os.path.basename(path)))
        archive_path = entry.get("archivePath", "")

        stats_path = os.path.join(path, ".claude", "stats.json")
        stats = None
        if os.path.isfile(stats_path):
            try:
                with open(stats_path, "r", encoding="utf-8") as sf:
                    stats = json.load(sf)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Could not load stats for {name}: {e}", file=sys.stderr)
        elif not os.path.isdir(path):
            print(f"Warning: Project path does not exist: {path}", file=sys.stderr)
            continue
        else:
            print(f"Warning: No stats.json found for {name} at {stats_path}", file=sys.stderr)

        projects.append({
            "name": name,
            "path": path,
            "archivePath": archive_path,
            "lastUpdated": entry.get("lastUpdated", ""),
            "stats": stats,
        })

    return projects


def compute_global_stats(projects):
    """Compute aggregated lifetime stats across all projects."""
    total_sessions = 0
    total_commits = 0
    total_lines_added = 0
    total_lines_removed = 0
    active_projects = 0
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=7)

    for p in projects:
        s = p.get("stats")
        if not s:
            continue
        lt = s.get("lifetime", {})
        total_sessions += lt.get("totalSessions", 0)
        total_commits += lt.get("totalCommits", 0)
        total_lines_added += lt.get("totalLinesAdded", 0)
        total_lines_removed += lt.get("totalLinesRemoved", 0)

        # Check if active in last 7 days
        recent = s.get("recentSessions", [])
        for sess in recent:
            d = sess.get("date", "")
            if d:
                try:
                    sd = parse_date(d)
                    if sd >= seven_days_ago:
                        active_projects += 1
                        break
                except ValueError:
                    pass

    net_code = total_lines_added - total_lines_removed
    return {
        "totalSessions": total_sessions,
        "totalCommits": total_commits,
        "totalLinesAdded": total_lines_added,
        "netCode": net_code,
        "activeProjects": active_projects,
    }


def compute_all_day_sessions(projects):
    """Build a dict: date_str -> list of {project_name, project_idx, session_data}.

    Also returns (earliest_date, latest_date) across all sessions.
    """
    day_map = {}
    earliest = None
    latest = None

    for idx, p in enumerate(projects):
        s = p.get("stats")
        if not s:
            continue
        for sess in s.get("recentSessions", []):
            d = sess.get("date", "")
            if not d:
                continue
            try:
                sd = parse_date(d)
            except ValueError:
                continue
            if earliest is None or sd < earliest:
                earliest = sd
            if latest is None or sd > latest:
                latest = sd

            if d not in day_map:
                day_map[d] = []
            day_map[d].append({
                "project_name": p["name"],
                "project_idx": idx,
                "session": sess,
            })

    # Also check lifetime.firstSessionDate for earliest
    for idx, p in enumerate(projects):
        s = p.get("stats")
        if not s:
            continue
        fsd = s.get("lifetime", {}).get("firstSessionDate", "")
        if fsd:
            try:
                d = parse_date(fsd)
                if earliest is None or d < earliest:
                    earliest = d
            except ValueError:
                pass

    return day_map, earliest, latest


def compute_weeks(day_map, earliest, latest):
    """Compute list of weeks from earliest to latest.

    Returns list of week dicts, each containing:
    - start: Monday date
    - end: Sunday date
    - days: list of 7 day dicts (Mon-Sun), each with:
      - date: date object
      - sessions: list of session entries from day_map
    """
    if earliest is None or latest is None:
        return []

    weeks = []
    ws = get_week_start(earliest)
    while ws <= latest:
        week = {"start": ws, "end": ws + timedelta(days=6), "days": []}
        for i in range(7):
            d = ws + timedelta(days=i)
            d_str = d.strftime("%Y-%m-%d")
            sessions = day_map.get(d_str, [])
            week["days"].append({
                "date": d,
                "sessions": sessions,
            })
        weeks.append(week)
        ws += timedelta(days=7)

    return weeks


def compute_week_stats(week, prev_week=None):
    """Compute aggregate stats for a week."""
    total_sessions = 0
    total_commits = 0
    total_lines_added = 0
    active_projects = set()

    for day in week["days"]:
        for entry in day["sessions"]:
            total_sessions += 1
            s = entry["session"]
            total_commits += s.get("commits", 0)
            total_lines_added += s.get("linesAdded", 0)
            active_projects.add(entry["project_name"])

    # Deltas vs previous week
    delta_sessions = None
    delta_commits = None
    delta_lines = None
    if prev_week:
        ps = sum(len(d["sessions"]) for d in prev_week["days"])
        pc = sum(e["session"].get("commits", 0) for d in prev_week["days"] for e in d["sessions"])
        pl = sum(e["session"].get("linesAdded", 0) for d in prev_week["days"] for e in d["sessions"])
        delta_sessions = total_sessions - ps
        delta_commits = total_commits - pc
        delta_lines = total_lines_added - pl

    # Best of
    most_active = None
    max_proj_sessions = 0
    proj_counts = {}
    for day in week["days"]:
        for entry in day["sessions"]:
            pn = entry["project_name"]
            proj_counts[pn] = proj_counts.get(pn, 0) + 1
    for pn, count in proj_counts.items():
        if count > max_proj_sessions:
            max_proj_sessions = count
            most_active = pn

    biggest_day = None
    biggest_day_sessions = 0
    biggest_day_projects = set()
    for day in week["days"]:
        if len(day["sessions"]) > biggest_day_sessions:
            biggest_day_sessions = len(day["sessions"])
            biggest_day = day["date"]
            biggest_day_projects = set(e["project_name"] for e in day["sessions"])

    return {
        "total_sessions": total_sessions,
        "total_commits": total_commits,
        "total_lines_added": total_lines_added,
        "active_projects": sorted(active_projects),
        "delta_sessions": delta_sessions,
        "delta_commits": delta_commits,
        "delta_lines": delta_lines,
        "most_active": most_active,
        "most_active_count": max_proj_sessions,
        "biggest_day": biggest_day,
        "biggest_day_sessions": biggest_day_sessions,
        "biggest_day_projects": biggest_day_projects,
    }


def compute_project_status(project, today):
    """Determine ACTIVE/IDLE/DORMANT status for a project."""
    s = project.get("stats")
    if not s:
        return "dormant", "No data"

    last_date_str = s.get("streak", {}).get("lastSessionDate", "")
    if not last_date_str:
        recent = s.get("recentSessions", [])
        if recent:
            last_date_str = recent[0].get("date", "")
    if not last_date_str:
        return "dormant", "No sessions"

    try:
        last_date = parse_date(last_date_str)
    except ValueError:
        return "dormant", "Unknown"

    days_ago = (today - last_date).days

    if days_ago <= 0:
        return "active", "last active today"
    elif days_ago == 1:
        return "active", "last active yesterday"
    elif days_ago <= 3:
        return "active", f"last active {days_ago} days ago"
    elif days_ago <= 14:
        return "idle", f"last active {days_ago} days ago"
    else:
        return "dormant", f"last active {days_ago} days ago"


def extract_version(sessions):
    """Extract version from the most recent session summary."""
    for s in sessions[:5]:
        summary = s.get("summary", "")
        match = re.search(r'v(\d+\.\d+(?:\.\d+)?)', summary)
        if match:
            return f"v{match.group(1)}"
    return None


def extract_feature(sessions):
    """Extract current feature from the most recent session summary."""
    if not sessions:
        return None
    summary = sessions[0].get("summary", "")
    # Look for patterns like "Built X", "Shipped X", "Completed X", "Started X"
    # Or feature names before version numbers
    # Try to find the key activity
    for pattern in [
        r'(?:Built|Shipped|Completed|Started|Added|Designed|Created)\s+(.+?)(?:\s*[-—]\s*|\s*\(|\s*v\d|\.\s|$)',
        r'^(.+?)(?:\s*[-—]\s*|\s*:)',
    ]:
        match = re.search(pattern, summary)
        if match:
            feat = match.group(1).strip()
            if len(feat) > 60:
                feat = feat[:57] + "..."
            return feat
    # Fallback: first sentence
    first = summary.split(".")[0] if summary else None
    if first and len(first) > 60:
        first = first[:57] + "..."
    return first


def count_active_days(sessions):
    """Count unique dates in sessions list."""
    dates = set()
    for s in sessions:
        d = s.get("date", "")
        if d:
            dates.add(d)
    return len(dates)


# ── HTML Building ──

CSS = r"""  @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;500;600;700&family=Inter:wght@300;400;500;600;700&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --bg: #0a0a0f;
    --surface: #12121a;
    --surface2: #1a1a26;
    --border: #2a2a3a;
    --text: #e0e0e8;
    --text-dim: #8888a0;
    --accent: #6c63ff;
    --accent-glow: rgba(108, 99, 255, 0.15);
    --green: #4ade80;
    --green-dim: rgba(74, 222, 128, 0.1);
    --amber: #fbbf24;
    --amber-dim: rgba(251, 191, 36, 0.1);
    --red: #f87171;
    --cyan: #67e8f9;
  }

  body.light {
    --bg: #f0efe9;
    --surface: #f8f7f3;
    --surface2: #eae9e3;
    --border: #d5d4cc;
    --text: #1a1a2e;
    --text-dim: #6b6b80;
    --accent: #5046e5;
    --accent-glow: rgba(80, 70, 229, 0.08);
    --green: #16a34a;
    --green-dim: rgba(22, 163, 74, 0.08);
    --amber: #d97706;
    --amber-dim: rgba(217, 119, 6, 0.08);
    --red: #dc2626;
    --cyan: #0891b2;
  }

  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', -apple-system, sans-serif;
    line-height: 1.6;
    min-height: 100vh;
    padding: 2rem;
  }

  .container { max-width: 900px; margin: 0 auto; }

  /* ── Page Header ── */
  .page-header {
    text-align: center;
    padding: 2.5rem 2rem 2rem;
    border: 1px solid var(--border);
    border-radius: 12px;
    background: linear-gradient(135deg, var(--surface) 0%, var(--bg) 100%);
    position: relative;
    overflow: hidden;
    margin-bottom: 2rem;
  }
  .page-header::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(ellipse at center, var(--accent-glow) 0%, transparent 70%);
    pointer-events: none;
  }
  .page-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: var(--text);
    position: relative;
    margin-bottom: 0.3rem;
  }
  .page-subtitle {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    color: var(--accent);
    letter-spacing: 0.1em;
    position: relative;
  }

  /* ── Lifetime Stats Bar ── */
  .lifetime-bar {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1rem;
    margin-bottom: 2rem;
  }
  .lifetime-stat {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 0.8rem;
    text-align: center;
  }
  .lifetime-value {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--text);
  }
  .lifetime-label {
    font-size: 0.65rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-dim);
    margin-top: 0.15rem;
  }

  /* ── Time Allocation Bar ── */
  .allocation-section {
    margin-bottom: 2rem;
  }
  .allocation-section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 0.6rem;
  }
  .allocation-bar-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.2rem;
  }
  .allocation-bar {
    display: flex;
    height: 24px;
    border-radius: 6px;
    overflow: hidden;
    margin-bottom: 0.8rem;
  }
  .allocation-segment {
    height: 100%;
    transition: opacity 0.15s;
    cursor: default;
    position: relative;
  }
  .allocation-segment:hover {
    opacity: 0.85;
  }
  .allocation-segment:first-child {
    border-radius: 6px 0 0 6px;
  }
  .allocation-segment:last-child {
    border-radius: 0 6px 6px 0;
  }
  .allocation-labels {
    display: flex;
    gap: 1.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-dim);
  }
  .alloc-label {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }
  .alloc-dot {
    width: 8px;
    height: 8px;
    border-radius: 2px;
  }
  .alloc-name { color: var(--text); font-weight: 500; }
  .alloc-count { color: var(--text-dim); }
  .alloc-pct { color: var(--text-dim); font-size: 0.6rem; }

  /* ── Week View ── */
  .week-section {
    margin-bottom: 2rem;
  }
  .week-nav {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
  }
  .week-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    font-weight: 600;
    color: var(--text);
    letter-spacing: 0.05em;
  }
  .week-label-sub {
    font-size: 0.75rem;
    font-weight: 400;
    color: var(--text-dim);
    margin-left: 0.6rem;
  }
  .week-arrows {
    display: flex;
    gap: 0.4rem;
  }
  .week-arrow {
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text-dim);
    cursor: pointer;
    font-size: 0.8rem;
    transition: all 0.15s;
  }
  .week-arrow:hover { border-color: var(--accent); color: var(--text); }
  .week-arrow.disabled { opacity: 0.3; pointer-events: none; }

  /* Week summary card */
  .week-summary {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    margin-bottom: 1rem;
  }
  .week-summary-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 0.6rem;
  }
  .week-summary-text {
    font-size: 0.9rem;
    color: var(--text);
    line-height: 1.6;
    margin-bottom: 0.8rem;
  }
  .week-summary-metrics {
    display: flex;
    gap: 1.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--text-dim);
    padding-top: 0.6rem;
    border-top: 1px solid var(--border);
    flex-wrap: wrap;
  }
  .week-summary-metrics .wsm-val { color: var(--text); font-weight: 600; }
  .week-summary-metrics .wsm-green { color: var(--green); }
  .wsm-delta {
    font-size: 0.65rem;
    font-weight: 600;
    padding: 0 0.3rem;
    border-radius: 3px;
    margin-left: 0.2rem;
  }
  .wsm-delta.up { color: var(--green); background: var(--green-dim); }
  .wsm-delta.down { color: var(--red); background: rgba(248, 113, 113, 0.1); }
  .week-best-of {
    display: flex;
    gap: 1.5rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-dim);
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px dashed var(--border);
    flex-wrap: wrap;
  }
  .best-item {
    display: flex;
    align-items: center;
    gap: 0.3rem;
  }
  .best-label { color: var(--amber); font-weight: 600; font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.05em; }
  .best-val { color: var(--text); }

  /* Day strip -- 7 columns */
  .week-strip {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 6px;
    margin-bottom: 1rem;
  }
  .week-day {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 10px;
    display: flex;
    flex-direction: column;
    min-height: 160px;
    cursor: default;
    transition: all 0.15s;
    position: relative;
  }
  .week-day.has-sessions { cursor: pointer; }
  .week-day.has-sessions:hover {
    border-color: var(--accent);
    background: var(--surface2);
  }
  .week-day.today { border-color: var(--accent); }
  .week-day.selected {
    border-color: var(--accent);
    background: var(--accent-glow);
    box-shadow: 0 0 12px rgba(108, 99, 255, 0.15);
  }
  .week-day.rest-day {
    opacity: 0.4;
  }

  .wd-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
  }
  .wd-dow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-dim);
  }
  .week-day.has-sessions .wd-dow { color: var(--text); }
  .wd-date {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: var(--text-dim);
  }
  .week-day.today .wd-date { color: var(--accent); font-weight: 600; }

  .wd-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: var(--accent);
    background: var(--accent-glow);
    padding: 1px 5px;
    border-radius: 3px;
    margin-bottom: 6px;
    display: inline-block;
    align-self: flex-start;
  }

  .wd-metrics {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: var(--text-dim);
    display: flex;
    gap: 6px;
    margin-bottom: 6px;
  }
  .wd-metrics .wdm-a { color: var(--green); }

  /* Project dots */
  .wd-projects {
    display: flex;
    gap: 4px;
    margin-bottom: 6px;
  }
  .wd-project-dot {
    width: 18px;
    height: 18px;
    border-radius: 4px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.5rem;
    font-weight: 700;
    color: var(--bg);
  }
  body.light .wd-project-dot { color: #fff; }

  /* Mini stacked bar */
  .wd-mini-bar {
    display: flex;
    height: 4px;
    border-radius: 2px;
    overflow: hidden;
    margin-top: auto;
  }
  .wd-mini-segment {
    height: 100%;
  }

  .wd-rest {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-dim);
    margin: auto 0;
    text-align: center;
  }

  /* ── Project Swimlane ── */
  .swimlane-section {
    margin-bottom: 2rem;
  }
  .swimlane-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 0.6rem;
  }
  .swimlane {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    position: relative;
  }
  .sl-dow-row {
    display: grid;
    grid-template-columns: 140px repeat(7, 1fr);
    gap: 0;
    margin-bottom: 4px;
  }
  .sl-dow-spacer { }
  .sl-dow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.55rem;
    color: var(--text-dim);
    text-align: center;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-left: 1px solid var(--border);
  }
  .swimlane-grid {
    display: grid;
    grid-template-columns: 140px repeat(7, 1fr);
    gap: 0;
    align-items: center;
  }
  .sl-project-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--text);
    font-weight: 500;
    padding-right: 8px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .sl-cell {
    height: 28px;
    position: relative;
    border-left: 1px solid var(--border);
  }
  .sl-bar {
    position: absolute;
    top: 4px;
    bottom: 4px;
    left: 4px;
    border-radius: 3px;
    opacity: 0.8;
  }

  /* ── Timeline Scrubber ── */
  .scrubber-section {
    margin-bottom: 2rem;
    position: sticky;
    top: 0;
    z-index: 100;
    background: var(--bg);
    padding: 0.8rem 0;
    border-bottom: 1px solid var(--border);
  }
  .scrubber-track {
    position: relative;
    height: 36px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 6px;
    overflow: hidden;
    cursor: pointer;
  }
  .scrubber-bar {
    position: absolute;
    bottom: 0;
    width: 5px;
    border-radius: 2px 2px 0 0;
    opacity: 0.6;
  }
  .scrubber-bar.active {
    opacity: 1;
  }
  .scrubber-viewport {
    position: absolute;
    top: 0;
    height: 100%;
    background: rgba(108, 99, 255, 0.08);
    border-left: 2px solid var(--accent);
    border-right: 2px solid var(--accent);
    cursor: grab;
    transition: left 0.15s ease;
  }
  .scrubber-viewport:hover {
    background: rgba(108, 99, 255, 0.12);
  }
  .scrubber-labels {
    display: flex;
    justify-content: space-between;
    margin-top: 0.3rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    color: var(--text-dim);
  }

  /* ── Section Label ── */
  .section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 1rem;
  }

  /* ── Project Cards ── */
  .project-cards-section {
    margin-bottom: 2rem;
  }
  .project-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.6rem;
    cursor: pointer;
    transition: all 0.15s;
    position: relative;
    overflow: hidden;
  }
  .project-card:hover {
    border-color: var(--accent);
    background: var(--surface2);
  }
  .project-card .card-chevron {
    position: absolute;
    right: 1.2rem;
    top: 1rem;
    color: var(--text-dim);
    font-size: 0.7rem;
    transition: transform 0.2s, opacity 0.15s;
    opacity: 0.4;
  }
  .project-card:hover .card-chevron { opacity: 1; }
  .project-card.expanded .card-chevron { transform: rotate(90deg); opacity: 1; }

  .project-top {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 0.5rem;
    flex-wrap: wrap;
  }
  .project-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 1rem;
    font-weight: 700;
    color: var(--text);
  }
  .status-badge {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    padding: 0.1rem 0.5rem;
    border-radius: 3px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .status-badge.active { color: var(--green); background: var(--green-dim); }
  .status-badge.idle { color: var(--amber); background: var(--amber-dim); }
  .status-badge.dormant { color: var(--red); background: rgba(248, 113, 113, 0.1); }
  .project-last-active {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-dim);
    margin-left: auto;
    padding-right: 2rem;
  }

  .project-desc {
    font-size: 0.85rem;
    color: var(--text-dim);
    line-height: 1.5;
    margin-bottom: 0.6rem;
    padding-right: 2rem;
  }

  .project-metrics {
    display: flex;
    gap: 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-dim);
    margin-bottom: 0.6rem;
    flex-wrap: wrap;
  }
  .pm-val { color: var(--text); font-weight: 500; }
  .pm-green { color: var(--green); }

  .project-feature-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.4rem;
    flex-wrap: wrap;
  }
  .project-feature-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-dim);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  .project-feature-name {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    color: var(--text);
    font-weight: 500;
  }

  /* Progress bar */
  .progress-bar-container {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 0.4rem;
  }
  .progress-bar {
    flex: 1;
    display: flex;
    gap: 2px;
    max-width: 200px;
  }
  .progress-step {
    flex: 1;
    height: 4px;
    border-radius: 2px;
    background: var(--border);
  }
  .progress-step.done { background: var(--green); }
  .progress-step.wip { background: var(--amber); }
  .progress-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-dim);
  }

  .project-version {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-dim);
  }
  .project-version .pv-ver { color: var(--accent); font-weight: 600; }
  .project-version .pv-count { color: var(--text-dim); margin-left: 0.6rem; }

  /* Expandable detail */
  .project-detail {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease, padding 0.3s ease;
    border-top: 0px solid var(--border);
    margin-top: 0;
  }
  .project-card.expanded .project-detail {
    max-height: 500px;
    border-top: 1px solid var(--border);
    margin-top: 0.8rem;
    padding-top: 0.8rem;
  }

  .recent-activity-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.6rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-dim);
    margin-bottom: 0.4rem;
  }
  .recent-session {
    font-size: 0.8rem;
    color: var(--text);
    padding: 0.2rem 0;
    line-height: 1.5;
  }
  .recent-session .rs-num {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--accent);
    font-weight: 600;
  }
  .recent-session .rs-date {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    color: var(--text-dim);
    margin-left: 0.3rem;
  }

  .view-archive-btn {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--accent);
    background: var(--accent-glow);
    border: 1px solid var(--accent);
    padding: 0.4rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s;
    text-decoration: none;
    margin-top: 0.6rem;
  }
  .view-archive-btn:hover {
    background: var(--accent);
    color: var(--bg);
  }

  /* ── Footer ── */
  .archive-footer {
    border-top: 1px solid var(--border);
    padding-top: 1.5rem;
    margin-top: 2rem;
    text-align: center;
    font-size: 0.8rem;
    color: var(--text-dim);
  }
  .archive-footer strong { color: var(--accent); font-weight: 600; }
  .archive-footer .footer-line {
    margin-bottom: 0.3rem;
  }
  .archive-footer .footer-shortcut {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-dim);
    opacity: 0.5;
    margin-top: 0.5rem;
  }

  /* ── Theme Toggle ── */
  .theme-toggle {
    position: fixed;
    top: 1rem;
    right: 1rem;
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text-dim);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
    z-index: 200;
    transition: all 0.2s;
  }
  .theme-toggle:hover { border-color: var(--accent); color: var(--text); }

  /* ── Keyboard Help Modal ── */
  .kb-help {
    display: none;
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.6);
    z-index: 300;
    align-items: center;
    justify-content: center;
  }
  .kb-help.visible { display: flex; }
  .kb-help-panel {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.5rem 2rem;
    max-width: 400px;
    width: 90%;
  }
  .kb-help-title {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--text);
    margin-bottom: 1rem;
    text-transform: uppercase;
    letter-spacing: 0.1em;
  }
  .kb-row {
    display: flex;
    justify-content: space-between;
    padding: 0.3rem 0;
    font-size: 0.8rem;
  }
  .kb-key {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    color: var(--accent);
    background: var(--accent-glow);
    padding: 0.1rem 0.5rem;
    border-radius: 3px;
    font-weight: 600;
  }
  .kb-desc { color: var(--text-dim); }

  /* Keyboard nav focus ring */
  .project-card.kb-focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 2px var(--accent-glow);
  }

  /* ── Mobile ── */
  @media (max-width: 700px) {
    .lifetime-bar { grid-template-columns: repeat(3, 1fr); }
    .week-strip { grid-template-columns: repeat(4, 1fr); }
    .allocation-labels { flex-wrap: wrap; }
    .project-metrics { gap: 0.6rem; }
    .sl-dow-row, .swimlane-grid { grid-template-columns: 100px repeat(7, 1fr); }
    .week-best-of { flex-direction: column; gap: 0.3rem; }
    .project-top { flex-direction: column; align-items: flex-start; gap: 0.4rem; }
    .project-last-active { margin-left: 0; }
  }"""


JS = r"""  // ── Theme ──
  (function() {
    const hour = new Date().getHours();
    if (hour >= 6 && hour < 18) document.body.classList.add('light');
  })();

  document.getElementById('theme-toggle').addEventListener('click', function() {
    document.body.classList.toggle('light');
    this.textContent = document.body.classList.contains('light') ? '\u2600' : '\u263E';
  });

  // ── Toggle Card ──
  function toggleCard(card) {
    card.classList.toggle('expanded');
  }

  // ── Day Selection ──
  function selectDay(el) {
    document.querySelectorAll('.week-day').forEach(d => d.classList.remove('selected'));
    el.classList.toggle('selected');
  }

  // ── Week Navigation ──
  var currentWeekIdx = CURRENT_WEEK_IDX;
  var totalWeeks = TOTAL_WEEKS;
  var weekData = WEEK_DATA_JSON;

  function renderWeek(idx) {
    if (idx < 0 || idx >= totalWeeks) return;
    currentWeekIdx = idx;
    var w = weekData[idx];
    document.getElementById('week-label').innerHTML = w.label;
    document.getElementById('week-strip').innerHTML = w.stripHtml;
    document.getElementById('week-summary-content').innerHTML = w.summaryHtml;
    document.getElementById('swimlane-content').innerHTML = w.swimlaneHtml;

    // Update arrow states
    var prev = document.getElementById('prev-week');
    var next = document.getElementById('next-week');
    if (idx <= 0) prev.classList.add('disabled'); else prev.classList.remove('disabled');
    if (idx >= totalWeeks - 1) next.classList.add('disabled'); else next.classList.remove('disabled');

    // Update scrubber viewport
    updateScrubberViewport(idx);
  }

  function updateScrubberViewport(idx) {
    var vp = document.getElementById('scrubber-viewport');
    if (!vp || totalWeeks <= 0) return;
    var pct = 100 / totalWeeks;
    vp.style.left = (idx * pct) + '%';
    vp.style.width = pct + '%';
  }

  document.getElementById('prev-week').addEventListener('click', function() {
    renderWeek(currentWeekIdx - 1);
  });
  document.getElementById('next-week').addEventListener('click', function() {
    renderWeek(currentWeekIdx + 1);
  });

  // ── Scrubber click ──
  document.getElementById('scrubber-track').addEventListener('click', function(e) {
    var rect = this.getBoundingClientRect();
    var pct = (e.clientX - rect.left) / rect.width;
    var idx = Math.floor(pct * totalWeeks);
    idx = Math.max(0, Math.min(idx, totalWeeks - 1));
    renderWeek(idx);
  });

  // ── Keyboard Navigation ──
  var focusedCardIdx = -1;
  var cards = function() { return document.querySelectorAll('.project-card'); };

  function focusCard(idx) {
    var all = cards();
    all.forEach(function(c) { c.classList.remove('kb-focus'); });
    if (idx >= 0 && idx < all.length) {
      focusedCardIdx = idx;
      all[idx].classList.add('kb-focus');
      all[idx].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }

  document.addEventListener('keydown', function(e) {
    var help = document.getElementById('kb-help');

    // ? = toggle help
    if (e.key === '?') {
      e.preventDefault();
      help.classList.toggle('visible');
      return;
    }
    // Esc = close help
    if (e.key === 'Escape') {
      help.classList.remove('visible');
      return;
    }
    // T = toggle theme
    if (e.key === 't' || e.key === 'T') {
      if (help.classList.contains('visible')) return;
      document.getElementById('theme-toggle').click();
      return;
    }

    // Arrow left/right = week nav
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      renderWeek(currentWeekIdx - 1);
      return;
    }
    if (e.key === 'ArrowRight') {
      e.preventDefault();
      renderWeek(currentWeekIdx + 1);
      return;
    }

    // Arrow up/down = project cards
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      var max = cards().length - 1;
      focusCard(Math.min(focusedCardIdx + 1, max));
      return;
    }
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      focusCard(Math.max(focusedCardIdx - 1, 0));
      return;
    }

    // Enter = expand/collapse focused card
    if (e.key === 'Enter') {
      e.preventDefault();
      var all = cards();
      if (focusedCardIdx >= 0 && focusedCardIdx < all.length) {
        toggleCard(all[focusedCardIdx]);
      }
      return;
    }
  });

  // Init scrubber viewport
  updateScrubberViewport(currentWeekIdx);"""


def render_error_page(message):
    """Render an error page when the registry is missing or empty."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Global Session Archive</title>
<style>
{CSS}
</style>
</head>
<body>
<div class="container">
  <div class="page-header">
    <div class="page-title">Global Archive</div>
    <div class="page-subtitle">{esc(message)}</div>
  </div>
  <div class="archive-footer">
    <div class="footer-line">Built with <strong>DOE</strong> &mdash; Directive, Orchestration, Execution</div>
  </div>
</div>
</body>
</html>
"""


def render_page_header(global_stats, num_projects, total_days):
    """Render the page header section."""
    ps = "project" if num_projects == 1 else "projects"
    ds = "day" if total_days == 1 else "days"
    return f"""  <div class="page-header">
    <div class="page-title">Global Archive</div>
    <div class="page-subtitle">{num_projects} {ps} &mdash; {global_stats['totalSessions']} sessions across {total_days} {ds}</div>
  </div>"""


def render_lifetime_bar(global_stats):
    """Render the global lifetime stats bar."""
    return f"""  <div class="lifetime-bar">
    <div class="lifetime-stat">
      <div class="lifetime-value">{esc(format_number(global_stats['totalSessions']))}</div>
      <div class="lifetime-label">Total Sessions</div>
    </div>
    <div class="lifetime-stat">
      <div class="lifetime-value">{esc(format_number(global_stats['totalCommits']))}</div>
      <div class="lifetime-label">Total Commits</div>
    </div>
    <div class="lifetime-stat">
      <div class="lifetime-value" style="color: var(--green)">{esc(format_number(global_stats['totalLinesAdded']))}</div>
      <div class="lifetime-label">Lines Added</div>
    </div>
    <div class="lifetime-stat">
      <div class="lifetime-value">{esc(format_number(global_stats['netCode']))}</div>
      <div class="lifetime-label">Net Code</div>
    </div>
    <div class="lifetime-stat">
      <div class="lifetime-value">{esc(str(global_stats['activeProjects']))}</div>
      <div class="lifetime-label">Active Projects</div>
    </div>
  </div>"""


def render_allocation_bar(projects):
    """Render the time allocation stacked bar."""
    total = 0
    project_sessions = []
    for idx, p in enumerate(projects):
        s = p.get("stats")
        count = s.get("lifetime", {}).get("totalSessions", 0) if s else 0
        total += count
        project_sessions.append((p["name"], count, idx))

    if total == 0:
        total = 1  # avoid division by zero

    # Segments
    segments = []
    labels = []
    for name, count, idx in project_sessions:
        pct = round(count / total * 100)
        if pct == 0 and count > 0:
            pct = 1
        dark, light, var_name = get_project_color(idx)
        segments.append(
            f'        <div class="allocation-segment" style="width: {pct}%; '
            f'background: var(--{var_name});" title="{esc(name)}: {pct}%"></div>'
        )
        labels.append(
            f'        <span class="alloc-label">\n'
            f'          <span class="alloc-dot" style="background: var(--{var_name});"></span>\n'
            f'          <span class="alloc-name">{esc(name)}</span>\n'
            f'          <span class="alloc-count">{count} sessions</span>\n'
            f'          <span class="alloc-pct">{pct}%</span>\n'
            f'        </span>'
        )

    segments_html = "\n".join(segments)
    labels_html = "\n".join(labels)

    return f"""  <div class="allocation-section">
    <div class="allocation-section-label">Time Allocation</div>
    <div class="allocation-bar-container">
      <div class="allocation-bar">
{segments_html}
      </div>
      <div class="allocation-labels">
{labels_html}
      </div>
    </div>
  </div>"""


def render_week_strip_html(week, projects, today):
    """Render the 7-day strip for a week. Returns HTML string."""
    parts = []
    for day_info in week["days"]:
        d = day_info["date"]
        sessions = day_info["sessions"]
        dow = format_dow(d)
        date_str = format_date_short(d)
        is_today = d == today

        if not sessions:
            # Rest day
            today_cls = " today" if is_today else ""
            parts.append(
                f'      <div class="week-day rest-day{today_cls}" data-day="{d.isoformat()}">\n'
                f'        <div class="wd-header">\n'
                f'          <span class="wd-dow">{esc(dow)}</span>\n'
                f'          <span class="wd-date">{esc(date_str)}</span>\n'
                f'        </div>\n'
                f'        <div class="wd-rest">--</div>\n'
                f'      </div>'
            )
        else:
            today_cls = " today" if is_today else ""
            total_sessions = len(sessions)
            total_lines = sum(s["session"].get("linesAdded", 0) for s in sessions)
            lines_str = f"+{format_number(total_lines)}"

            # Project dots
            seen_projects = {}
            for entry in sessions:
                pi = entry["project_idx"]
                pn = entry["project_name"]
                if pi not in seen_projects:
                    seen_projects[pi] = pn

            dots = []
            for pi, pn in sorted(seen_projects.items()):
                _, _, var_name = get_project_color(pi)
                initial = pn[0].upper()
                dots.append(
                    f'          <span class="wd-project-dot" style="background: var(--{var_name});" '
                    f'title="{esc(pn)}">{esc(initial)}</span>'
                )
            dots_html = "\n".join(dots)

            # Mini stacked bar
            proj_session_counts = {}
            for entry in sessions:
                pi = entry["project_idx"]
                proj_session_counts[pi] = proj_session_counts.get(pi, 0) + 1

            mini_segments = []
            for pi in sorted(proj_session_counts.keys()):
                count = proj_session_counts[pi]
                pct = round(count / total_sessions * 100)
                if pct == 0:
                    pct = 1
                _, _, var_name = get_project_color(pi)
                mini_segments.append(
                    f'          <div class="wd-mini-segment" style="width: {pct}%; '
                    f'background: var(--{var_name});"></div>'
                )
            mini_html = "\n".join(mini_segments)

            sess_label = "session" if total_sessions == 1 else "sessions"
            parts.append(
                f'      <div class="week-day has-sessions{today_cls}" data-day="{d.isoformat()}" onclick="selectDay(this)">\n'
                f'        <div class="wd-header">\n'
                f'          <span class="wd-dow">{esc(dow)}</span>\n'
                f'          <span class="wd-date">{esc(date_str)}</span>\n'
                f'        </div>\n'
                f'        <div class="wd-projects">\n{dots_html}\n'
                f'        </div>\n'
                f'        <div class="wd-badge">{total_sessions} {sess_label}</div>\n'
                f'        <div class="wd-metrics">\n'
                f'          <span class="wdm-a">{esc(lines_str)}</span>\n'
                f'        </div>\n'
                f'        <div class="wd-mini-bar">\n{mini_html}\n'
                f'        </div>\n'
                f'      </div>'
            )

    return "\n\n".join(parts)


def render_week_summary_html(ws, week):
    """Render the week summary card content (inner HTML)."""
    # Determine if current week
    today = datetime.now().date()
    week_end = week["end"]
    is_current = week["start"] <= today <= week_end

    title = "This Week" if is_current else f"Week of {format_date_short(week['start'])}"

    # Narrative
    active_names = ws["active_projects"]
    if len(active_names) == 0:
        narrative = "No sessions this week."
    elif len(active_names) == 1:
        narrative = f"Focused on {active_names[0]}."
    else:
        narrative = f"Active across {', '.join(active_names[:-1])} and {active_names[-1]}."

    # Metrics row
    metrics_parts = []
    sess_str = f'<span class="wsm-val">{ws["total_sessions"]}</span> sessions'
    if ws["delta_sessions"] is not None and ws["delta_sessions"] != 0:
        d = ws["delta_sessions"]
        cls = "up" if d > 0 else "down"
        sign = "+" if d > 0 else ""
        sess_str += f' <span class="wsm-delta {cls}">{sign}{d}</span>'
    metrics_parts.append(f"<span>{sess_str}</span>")

    commit_str = f'<span class="wsm-val">{ws["total_commits"]}</span> commits'
    if ws["delta_commits"] is not None and ws["delta_commits"] != 0:
        d = ws["delta_commits"]
        cls = "up" if d > 0 else "down"
        sign = "+" if d > 0 else ""
        commit_str += f' <span class="wsm-delta {cls}">{sign}{d}</span>'
    metrics_parts.append(f"<span>{commit_str}</span>")

    lines_str = f'+{format_number(ws["total_lines_added"])} lines'
    if ws["delta_lines"] is not None and ws["delta_lines"] != 0:
        d = ws["delta_lines"]
        cls = "up" if d > 0 else "down"
        sign = "+" if d > 0 else ""
        lines_str += f' <span class="wsm-delta {cls}">{sign}{format_number(d)}</span>'
    metrics_parts.append(f'<span class="wsm-green">{lines_str}</span>')

    metrics_html = "\n        ".join(metrics_parts)

    # Best of
    best_parts = []
    if ws["most_active"]:
        best_parts.append(
            f'<span class="best-item"><span class="best-label">Most active</span> '
            f'<span class="best-val">{esc(ws["most_active"])} ({ws["most_active_count"]} sessions)</span></span>'
        )
    if ws["biggest_day"] and ws["biggest_day_sessions"] > 0:
        bd = ws["biggest_day"]
        n_proj = len(ws["biggest_day_projects"])
        proj_label = "project" if n_proj == 1 else "projects"
        best_parts.append(
            f'<span class="best-item"><span class="best-label">Biggest day</span> '
            f'<span class="best-val">{format_dow(bd)} {format_date_short(bd)} &mdash; '
            f'{ws["biggest_day_sessions"]} sessions across {n_proj} {proj_label}</span></span>'
        )
    best_html = "\n        ".join(best_parts)

    result = f"""      <div class="week-summary-title">{esc(title)}</div>
      <div class="week-summary-text">{narrative}</div>
      <div class="week-summary-metrics">
        {metrics_html}
      </div>"""

    if best_parts:
        result += f"""
      <div class="week-best-of">
        {best_html}
      </div>"""

    return result


def render_swimlane_html(week, projects):
    """Render the project swimlane for a given week."""
    # DOW header row
    dow_labels = []
    for day_info in week["days"]:
        dow_labels.append(f'        <div class="sl-dow">{format_dow(day_info["date"])}</div>')
    dow_html = "\n".join(dow_labels)

    # Find max sessions on any single day for any project (for bar width scaling)
    max_sessions = 1
    for day_info in week["days"]:
        proj_counts = {}
        for entry in day_info["sessions"]:
            pi = entry["project_idx"]
            proj_counts[pi] = proj_counts.get(pi, 0) + 1
        for c in proj_counts.values():
            if c > max_sessions:
                max_sessions = c

    # One row per project
    rows = []
    for idx, p in enumerate(projects):
        _, _, var_name = get_project_color(idx)
        cells = []
        for day_info in week["days"]:
            # Count sessions for this project on this day
            count = sum(1 for e in day_info["sessions"] if e["project_idx"] == idx)
            if count == 0:
                cells.append('        <div class="sl-cell"></div>')
            else:
                # Scale bar width: proportional to count vs max
                width_pct = count / max_sessions
                opacity = max(0.5, min(1.0, 0.4 + width_pct * 0.6))
                right = max(4, int((1 - width_pct) * 80))
                sess_label = "session" if count == 1 else "sessions"
                cells.append(
                    f'        <div class="sl-cell"><div class="sl-bar" style="background: var(--{var_name}); '
                    f'left: 4px; right: {right}%; opacity: {opacity:.1f};" '
                    f'title="{count} {sess_label}"></div></div>'
                )
        cells_html = "\n".join(cells)
        rows.append(
            f'      <div class="swimlane-grid">\n'
            f'        <div class="sl-project-name">{esc(p["name"])}</div>\n'
            f'{cells_html}\n'
            f'      </div>'
        )

    rows_html = "\n".join(rows)

    return f"""      <div class="sl-dow-row">
        <div class="sl-dow-spacer"></div>
{dow_html}
      </div>
{rows_html}"""


def render_scrubber(day_map, earliest, latest, projects, weeks, current_week_idx):
    """Render the timeline scrubber section."""
    if earliest is None or latest is None:
        return ""

    total_days = (latest - earliest).days + 1
    if total_days <= 0:
        return ""

    # Build bars
    bars = []
    max_sessions_day = 1
    for d_offset in range(total_days):
        d = earliest + timedelta(days=d_offset)
        d_str = d.strftime("%Y-%m-%d")
        entries = day_map.get(d_str, [])
        if len(entries) > max_sessions_day:
            max_sessions_day = len(entries)

    for d_offset in range(total_days):
        d = earliest + timedelta(days=d_offset)
        d_str = d.strftime("%Y-%m-%d")
        entries = day_map.get(d_str, [])
        if not entries:
            continue

        left_pct = (d_offset / total_days) * 100
        total_here = len(entries)
        height_pct = max(10, int((total_here / max_sessions_day) * 90))

        # Find dominant project (most sessions that day)
        proj_counts = {}
        for e in entries:
            pi = e["project_idx"]
            proj_counts[pi] = proj_counts.get(pi, 0) + 1

        # Stack segments for this day
        cum_bottom = 0
        for pi in sorted(proj_counts.keys()):
            count = proj_counts[pi]
            seg_height_pct = int((count / total_here) * height_pct)
            if seg_height_pct < 3:
                seg_height_pct = 3
            _, _, var_name = get_project_color(pi)
            is_today = (d == datetime.now().date())
            active_cls = " active" if is_today else ""
            if cum_bottom == 0:
                bars.append(
                    f'      <div class="scrubber-bar{active_cls}" style="left: {left_pct:.1f}%; '
                    f'height: {seg_height_pct}%; background: var(--{var_name});"></div>'
                )
            else:
                bars.append(
                    f'      <div class="scrubber-bar{active_cls}" style="left: {left_pct:.1f}%; '
                    f'height: {seg_height_pct}%; bottom: {cum_bottom}%; background: var(--{var_name});"></div>'
                )
            cum_bottom += seg_height_pct

    bars_html = "\n".join(bars)

    # Viewport position
    vp_width = max(5, 100 / max(1, len(weeks)))
    vp_left = current_week_idx * vp_width

    # Labels
    label_dates = [earliest]
    mid = earliest + timedelta(days=total_days // 3)
    mid2 = earliest + timedelta(days=2 * total_days // 3)
    label_dates.append(mid)
    label_dates.append(mid2)
    label_dates.append(latest)

    labels = [f'      <span>{format_date_short(d)}</span>' for d in label_dates]
    labels_html = "\n".join(labels)

    return f"""  <div class="scrubber-section">
    <div class="scrubber-track" id="scrubber-track">
{bars_html}
      <div class="scrubber-viewport" id="scrubber-viewport" style="left: {vp_left:.1f}%; width: {vp_width:.1f}%;"></div>
    </div>
    <div class="scrubber-labels">
{labels_html}
    </div>
  </div>"""


def render_project_card(project, idx, projects, today, first_expanded=False):
    """Render a single project card."""
    name = project["name"]
    s = project.get("stats")
    status, last_active_text = compute_project_status(project, today)
    _, _, var_name = get_project_color(idx)

    expanded_cls = " expanded" if first_expanded and idx == 0 else ""
    card_id = f"card-{name.replace(' ', '-').lower()}"

    # Metrics
    sessions = s.get("lifetime", {}).get("totalSessions", 0) if s else 0
    commits = s.get("lifetime", {}).get("totalCommits", 0) if s else 0
    lines_added = s.get("lifetime", {}).get("totalLinesAdded", 0) if s else 0
    streak = s.get("streak", {}).get("current", 0) if s else 0
    recent = s.get("recentSessions", []) if s else []
    active_days = count_active_days(recent)

    # Feature and version from recent sessions
    feature = extract_feature(recent) if recent else None
    version = extract_version(recent) if recent else None

    feature_html = ""
    if feature:
        feature_html = (
            f'    <div class="project-feature-row">\n'
            f'      <span class="project-feature-label">Current:</span>\n'
            f'      <span class="project-feature-name">{esc(feature)}</span>\n'
            f'    </div>'
        )

    version_html = ""
    if version:
        version_html = (
            f'    <div class="project-version">\n'
            f'      <span class="pv-ver">{esc(version)}</span>\n'
            f'    </div>'
        )

    # Recent sessions (last 3)
    recent_html_parts = []
    for i, sess in enumerate(recent[:3]):
        sess_num = sessions - i
        d = sess.get("date", "")
        summary = sess.get("summary", "")
        if summary and len(summary) > 100:
            summary = summary[:97] + "..."
        try:
            sd = parse_date(d)
            date_fmt = f"{format_dow(sd)} {format_date_short(sd)}"
        except (ValueError, TypeError):
            date_fmt = d
        recent_html_parts.append(
            f'      <div class="recent-session">\n'
            f'        <span class="rs-num">#{sess_num}</span> '
            f'<span class="rs-date">{esc(date_fmt)}</span> &mdash; {esc(summary)}\n'
            f'      </div>'
        )
    recent_items_html = "\n".join(recent_html_parts) if recent_html_parts else (
        '      <div class="recent-session" style="color: var(--text-dim);">No recent session data</div>'
    )

    # Archive button
    archive_path = project.get("archivePath", "")
    archive_btn = ""
    if archive_path:
        archive_btn = (
            f'      <a class="view-archive-btn" href="{esc(archive_path)}" '
            f'onclick="event.stopPropagation()">View Project Archive &rarr;</a>'
        )

    no_recent_note = ""
    if not recent:
        no_recent_note = '    <div class="project-desc" style="font-style: italic;">No recent session data available.</div>\n'

    return f"""    <div class="project-card{expanded_cls}" id="{esc(card_id)}" onclick="toggleCard(this)">
      <span class="card-chevron">&#9656;</span>
      <div class="project-top">
        <span class="project-name">{esc(name)}</span>
        <span class="status-badge {status}">{status.title()}</span>
        <span class="project-last-active">{esc(last_active_text)}</span>
      </div>
{no_recent_note}      <div class="project-metrics">
        <span><span class="pm-val">{sessions}</span> sessions</span>
        <span><span class="pm-val">{commits}</span> commits</span>
        <span class="pm-green">+{format_number(lines_added)} lines</span>
        <span><span class="pm-val">{active_days}</span> days active</span>
        <span>Streak: <span class="pm-val">{streak}</span></span>
      </div>
{feature_html}
{version_html}

      <div class="project-detail">
        <div class="recent-activity-label">Recent Activity</div>
{recent_items_html}
{archive_btn}
      </div>
    </div>"""


def render_footer(num_projects, registry_path):
    """Render the footer."""
    ps = "project" if num_projects == 1 else "projects"
    return f"""  <div class="archive-footer">
    <div class="footer-line">Built with <strong>DOE</strong> &mdash; Directive, Orchestration, Execution</div>
    <div class="footer-line">Aggregated from <strong>{esc(registry_path)}</strong> &mdash; {num_projects} {ps}</div>
    <div class="footer-shortcut">Press ? for keyboard shortcuts</div>
  </div>"""


def build_html(projects, registry_path):
    """Build the complete HTML page."""
    today = datetime.now().date()
    global_stats = compute_global_stats(projects)
    day_map, earliest, latest = compute_all_day_sessions(projects)

    # Count total active days
    total_days = len(set(day_map.keys()))

    weeks = compute_weeks(day_map, earliest, latest)

    # Find the week containing today (or the last week)
    current_week_idx = len(weeks) - 1
    for i, w in enumerate(weeks):
        if w["start"] <= today <= w["end"]:
            current_week_idx = i
            break

    # Pre-render week data for JS navigation
    week_data_js = []
    for i, week in enumerate(weeks):
        prev_week = weeks[i - 1] if i > 0 else None
        ws = compute_week_stats(week, prev_week)

        # Week label
        start_str = format_date_short(week["start"])
        end_str = format_date_short(week["end"])
        year = week["end"].strftime("%Y")
        label = f'{start_str} &ndash; {end_str} {year} <span class="week-label-sub">Week {i + 1} of {len(weeks)}</span>'

        # Strip HTML
        strip_html = render_week_strip_html(week, projects, today)
        # Summary HTML
        summary_html = render_week_summary_html(ws, week)
        # Swimlane HTML
        swimlane_html = render_swimlane_html(week, projects)

        week_data_js.append({
            "label": label,
            "stripHtml": strip_html,
            "summaryHtml": summary_html,
            "swimlaneHtml": swimlane_html,
        })

    # Escape week data for embedding in JS
    week_data_json = json.dumps(week_data_js, ensure_ascii=False)

    # Render current week for initial display
    current_week = weeks[current_week_idx] if weeks else None
    prev_week = weeks[current_week_idx - 1] if current_week_idx > 0 and weeks else None
    current_ws = compute_week_stats(current_week, prev_week) if current_week else None

    # Week nav label
    if current_week:
        start_str = format_date_short(current_week["start"])
        end_str = format_date_short(current_week["end"])
        year = current_week["end"].strftime("%Y")
        week_label = (
            f'{start_str} &ndash; {end_str} {year} '
            f'<span class="week-label-sub">Week {current_week_idx + 1} of {len(weeks)}</span>'
        )
    else:
        week_label = "No data"

    # Initial strip HTML
    initial_strip = render_week_strip_html(current_week, projects, today) if current_week else ""
    initial_summary = render_week_summary_html(current_ws, current_week) if current_ws else ""
    initial_swimlane = render_swimlane_html(current_week, projects) if current_week else ""

    # Arrow states
    prev_disabled = ' disabled' if current_week_idx <= 0 else ''
    next_disabled = ' disabled' if current_week_idx >= len(weeks) - 1 else ''

    # Project cards
    project_cards = []
    for idx, p in enumerate(projects):
        card = render_project_card(p, idx, projects, today, first_expanded=True)
        project_cards.append(card)
    project_cards_html = "\n\n".join(project_cards)

    # Build JS with week data
    js_rendered = JS.replace("CURRENT_WEEK_IDX", str(current_week_idx))
    js_rendered = js_rendered.replace("TOTAL_WEEKS", str(len(weeks)))
    js_rendered = js_rendered.replace("WEEK_DATA_JSON", week_data_json)

    # Sections
    page_header = render_page_header(global_stats, len(projects), total_days)
    lifetime_bar = render_lifetime_bar(global_stats)
    allocation = render_allocation_bar(projects)

    week_section = f"""  <div class="week-section">
    <div class="week-nav">
      <div class="week-arrows">
        <div class="week-arrow{prev_disabled}" id="prev-week">&larr;</div>
      </div>
      <div class="week-label" id="week-label">
        {week_label}
      </div>
      <div class="week-arrows">
        <div class="week-arrow{next_disabled}" id="next-week">&rarr;</div>
      </div>
    </div>

    <div class="week-summary" id="week-summary-content">
{initial_summary}
    </div>

    <div class="week-strip" id="week-strip">
{initial_strip}
    </div>
  </div>"""

    swimlane_section = f"""  <div class="swimlane-section">
    <div class="swimlane-label">Project Activity</div>
    <div class="swimlane" id="swimlane-content">
{initial_swimlane}
    </div>
  </div>"""

    scrubber = render_scrubber(day_map, earliest, latest, projects, weeks, current_week_idx)

    project_cards_section = f"""  <div class="project-cards-section">
    <div class="section-label">Projects</div>

{project_cards_html}
  </div>"""

    footer = render_footer(len(projects), registry_path)

    # Keyboard help modal
    kb_help = """<div class="kb-help" id="kb-help">
  <div class="kb-help-panel">
    <div class="kb-help-title">Keyboard Shortcuts</div>
    <div class="kb-row"><span class="kb-key">&larr; &rarr;</span> <span class="kb-desc">Navigate weeks</span></div>
    <div class="kb-row"><span class="kb-key">&uarr; &darr;</span> <span class="kb-desc">Navigate project cards</span></div>
    <div class="kb-row"><span class="kb-key">Enter</span> <span class="kb-desc">Expand / collapse card</span></div>
    <div class="kb-row"><span class="kb-key">T</span> <span class="kb-desc">Toggle theme</span></div>
    <div class="kb-row"><span class="kb-key">?</span> <span class="kb-desc">Show / hide this help</span></div>
    <div class="kb-row"><span class="kb-key">Esc</span> <span class="kb-desc">Close</span></div>
  </div>
</div>"""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Global Session Archive</title>
<style>
{CSS}
</style>
</head>
<body>
<button class="theme-toggle" id="theme-toggle" title="Toggle light/dark mode">&#9790;</button>

{kb_help}

<div class="container">

{page_header}

{lifetime_bar}

{allocation}

{week_section}

{swimlane_section}

{scrubber}

{project_cards_section}

{footer}

</div>

<script>
{js_rendered}
</script>
</body>
</html>
"""


def main():
    parser = argparse.ArgumentParser(description="Generate global portfolio dashboard HTML")
    parser.add_argument(
        "--registry",
        default=os.path.expanduser("~/.claude/project-registry.json"),
        help="Path to project registry JSON (default: ~/.claude/project-registry.json)",
    )
    parser.add_argument(
        "--output",
        default=os.path.expanduser("~/.claude/docs/global-archive.html"),
        help="Output HTML file path (default: ~/.claude/docs/global-archive.html)",
    )
    args = parser.parse_args()

    registry_path = os.path.abspath(args.registry)
    output_path = os.path.abspath(args.output)

    projects = load_projects(registry_path)

    if projects is None:
        # Registry missing
        html_out = render_error_page("No projects registered. Run /archive in a project first.")
    elif len(projects) == 0:
        html_out = render_error_page("Registry is empty. No valid projects found.")
    else:
        html_out = build_html(projects, registry_path)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(output_path)


if __name__ == "__main__":
    main()
