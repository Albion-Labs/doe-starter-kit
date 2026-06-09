#!/usr/bin/env python3
"""Generate a session wrap-up HTML page from JSON data.

Usage:
    python3 ~/.claude/scripts/wrap_html.py --json '{"title": "...", ...}' --output .tmp/wrap.html
    echo '{"title": "..."}' | python3 ~/.claude/scripts/wrap_html.py
"""

import argparse
import json
import os
import re
import sys

from html_builder import (
    page_scaffold, esc, badge, badge_row, metric_grid, card, icon,
    timeline as builder_timeline, timeline_legend, data_table, raw,
    dl_item, pill, check_row, next_card, page_footer, page_header,
    section, section_header, collapsible_js, DOE_COLORS,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _parse_dur_mins(dur_str):
    """Parse a duration string like '15m' or '1h 30m' into total minutes."""
    mins = 0
    h_match = re.search(r'(\d+)h', dur_str)
    m_match = re.search(r'(\d+)m', dur_str)
    if h_match:
        mins += int(h_match.group(1)) * 60
    if m_match:
        mins += int(m_match.group(1))
    return mins


def _parse_hhmm(time_str):
    """Parse HH:MM string into total minutes since midnight."""
    parts = time_str.strip().split(":")
    if len(parts) == 2:
        try:
            return int(parts[0]) * 60 + int(parts[1])
        except ValueError:
            pass
    return None


def _collapsible_card(title, body, *, meta_html='', collapsed=False, icon_name=''):
    """Collapsible card with a HugeIcons-style glyph + title + optional meta.

    No coloured left-edge stripe — Chalk & Flint signals via icon/badge, never a
    coloured card border (see feedback_no_left_border_accent).
    """
    cls = 'card card-collapsible'
    if collapsed:
        cls += ' collapsed'

    ico = (
        f'<span class="ico" style="color:var(--text-faint);display:flex;">'
        f'{icon(icon_name)}</span>'
    ) if icon_name else ''
    inner = f'{ico}<span class="card-title">{esc(title)}</span>'
    if meta_html:
        inner += f' {meta_html}'
    title_html = (
        f'<div style="display: flex; align-items: center; gap: 8px;">{inner}</div>'
    )

    return (
        f'<div class="{cls}">'
        f'<div class="card-header">'
        f'{title_html}'
        f'<span class="card-chevron">&#9660;</span>'
        f'</div>'
        f'<div class="card-collapse-body"><div class="card-body">{body}</div></div>'
        f'</div>'
    )


# ── Render Functions ───────────────────────────────────────────────────────────

def render_header(data):
    """Page header: label, title, badge row."""
    project = data.get("projectName", "")
    title = data.get("title", "")
    footer = data.get("footer", {})

    dim = f'/ {title}' if title else ''
    header = page_header('Session Report', project, dim_title=dim)

    badges = []
    session = footer.get("session", "")
    if session:
        badges.append(badge(f'#{session}', 'accent'))

    streak = footer.get("streak", "")
    if streak:
        badges.append(badge(f'{streak}-day streak', 'pass'))

    lifetime = footer.get("lifetimeCommits", "")
    if lifetime:
        badges.append(badge(f'{lifetime} lifetime commits', 'dim'))

    platform = data.get("platform", "")
    if platform:
        name = {'darwin': 'macOS', 'win32': 'PC', 'linux': 'Linux'}.get(
            platform.lower(), platform)
        badges.append(badge(name, 'dim'))

    model = data.get("model", "")
    if model:
        m = model.lower()
        if 'opus' in m:
            name = 'Opus'
        elif 'sonnet' in m:
            name = 'Sonnet'
        elif 'haiku' in m:
            name = 'Haiku'
        else:
            name = model
        badges.append(badge(name, 'info'))

    tag = data.get("tag", "")
    if tag:
        variant_map = {
            'BUILD': 'pass', 'PLAN': 'info', 'DEBUG': 'dim',
            'HOUSEKEEPING': 'dim', 'RESEARCH': 'accent',
        }
        badges.append(badge(tag.upper(), variant_map.get(tag.upper(), 'dim')))

    return header + '\n' + badge_row(*badges) if badges else header


def render_metrics(data):
    """Twelve-tile stat grid — 3 bands of 4 (cadence -> output -> outcomes).

    A session wrap reports one session; cadence tiles derive from that session's
    own metrics, outcome tiles from the decision/learning arrays and a verifiable
    PRs-merged count (no self-reported numbers).
    """
    m = data.get("metrics", {})
    if not m:
        return ""

    today = data.get("todaySessions", [])
    sessions = len(today) if today else 1
    duration = m.get("sessionDuration", "") or "N/A"
    avg = duration if sessions <= 1 else "N/A"
    added = m.get("linesAdded", 0)
    removed = m.get("linesRemoved", 0)
    decisions = data.get("decisions", [])
    learnings = data.get("learnings", [])
    d_count = len(decisions) if isinstance(decisions, list) else 0
    l_count = len(learnings) if isinstance(learnings, list) else 0
    features = m.get("featuresShipped", m.get("featuresCompleted", 0))
    prs = m.get("prsMerged", 0)

    tiles = [
        # Band 1 — cadence
        (str(sessions), 'Sessions'),
        (str(duration), 'Total Time'),
        (str(avg), 'Avg Session'),
        (str(m.get("commits", 0)), 'Commits'),
        # Band 2 — output
        (f'+{added}', 'Lines Added', 'acc'),
        (f'−{removed}', 'Lines Removed', 'faint'),
        (str(m.get("filesTouched", 0)), 'Files Touched'),
        (str(m.get("stepsCompleted", 0)), 'Steps Done'),
        # Band 3 — outcomes & knowledge
        (str(features), 'Features Shipped'),
        (str(d_count), 'Decisions'),
        (str(l_count), 'Learnings'),
        (str(prs), 'PRs Merged', 'acc' if prs else None),
    ]

    return metric_grid(tiles, columns=4)


def render_summary(data):
    """Collapsible Summary card with breakdowns."""
    summary = data.get("summary", "")
    breakdowns = data.get("breakdowns", [])

    # Backward compat: old-style narrative array
    if not summary and not breakdowns:
        lines = data.get("narrative", [])
        if not lines:
            return ""
        summary = " ".join(lines)

    parts = []
    if summary:
        parts.append(
            f'<p style="margin-bottom: 16px; color: var(--text);">{esc(summary)}</p>')

    color_map = {
        'build': '--accent', 'review': '--text-dim',
        'housekeeping': '--text-dim', 'debug': '--text-dim',
        'research': '--status-live',
    }

    for b in breakdowns:
        heading = b.get("heading", "")
        bullets = b.get("bullets", [])
        color_var = color_map.get(heading.lower(), '--text')
        inner = '<br>'.join(esc(item) for item in bullets)
        parts.append(
            f'<div style="margin-bottom: 14px;">'
            f'<div style="font-weight: 600; font-size: 14px; margin-bottom: 4px;">'
            f'<span style="color: var({color_var});">{esc(heading)}</span>'
            f'</div>'
            f'<div style="padding-left: 14px; font-size: 14px; color: var(--text-dim);">'
            f'{inner}</div></div>'
        )

    body = '\n'.join(parts)

    # Vibe inline in header (right-aligned, like old wrap)
    vibe = data.get("vibe")
    meta = ''
    if vibe:
        emoji = vibe.get("emoji", "")
        text = esc(vibe.get("text", ""))
        vibe_str = f'{emoji} {text}'.strip() if emoji else text
        meta = (
            f'<span style="margin-left: auto; font-family: var(--mono); '
            f'font-size: 12px; color: var(--text-dim); letter-spacing: 0.04em;">'
            f'Vibe: {vibe_str}</span>'
        )

    return _collapsible_card('Summary', body, meta_html=meta, icon_name='summary')


def render_timeline_section(data):
    """Collapsible Timeline card."""
    items = data.get("timeline", [])
    if not items:
        return ""

    # Compute durations from timestamps
    parsed_times = [_parse_hhmm(item.get("time", "")) for item in items]
    session_dur_str = data.get("metrics", {}).get("sessionDuration", "")
    total_mins = _parse_dur_mins(session_dur_str) if session_dur_str else 0

    computed_durs = []
    for i in range(len(items)):
        if parsed_times[i] is None:
            computed_durs.append(0)
            continue
        if i + 1 < len(items) and parsed_times[i + 1] is not None:
            gap = parsed_times[i + 1] - parsed_times[i]
            if gap < 0:
                gap += 24 * 60
            computed_durs.append(gap)
        elif total_mins > 0 and parsed_times[0] is not None:
            elapsed = sum(computed_durs)
            computed_durs.append(max(0, total_mins - elapsed))
        else:
            computed_durs.append(0)

    if total_mins == 0:
        total_mins = sum(computed_durs)

    # Build timeline items for builder component
    color_map = {'start': None, 'major': 'green', 'fix': 'amber'}
    tl_items = []
    for i, item in enumerate(items):
        t = item.get("time", "")
        desc = item.get("desc", "")
        item_type = item.get("type", "")
        color = color_map.get(item_type)

        mins = computed_durs[i]
        dur = ""
        if mins > 0 and item_type != "start":
            dur_str = f"{mins}m" if mins < 60 else f"{mins // 60}h {mins % 60}m"
            pct = round(mins / total_mins * 100) if total_mins > 0 else 0
            dur = f"{dur_str} ({pct}%)" if pct > 0 else dur_str

        entry = {'time': t, 'text': desc}
        if color:
            entry['color'] = color
        if dur:
            entry['duration'] = dur
        tl_items.append(entry)

    tl_html = builder_timeline(tl_items)

    # Legend
    legend = timeline_legend([
        (DOE_COLORS['accent'], 'Session start'),
        (DOE_COLORS['green'], 'Major change'),
        (DOE_COLORS['amber'], 'Fix'),
        (DOE_COLORS['text_dim'], 'Normal'),
    ])

    # Total duration
    total_html = ''
    if session_dur_str:
        total_html = (
            f'<div style="margin-top: 12px; text-align: right;">'
            f'<span style="font-family: var(--mono); font-size: 13px; '
            f'font-weight: 600;">Total: {esc(session_dur_str)}</span></div>'
        )

    body = tl_html + legend + total_html
    meta = f'<span class="card-meta">{esc(session_dur_str)}</span>' if session_dur_str else ''

    return _collapsible_card('Timeline', body, meta_html=meta, icon_name='clock')


def render_commits(data):
    """Collapsible Commits card with grouped table or flat list."""
    m = data.get("metrics", {})
    commit_log = m.get("commitLog", [])
    if not commit_log:
        return ""

    groups = data.get("commitGroups")
    total_commits = len(commit_log)

    if groups:
        # Grouped: show each group with its commits
        commit_map = {c.get("hash", ""): c for c in commit_log}
        sections = []
        for group in groups:
            name = group.get("name", "Other")
            hashes = group.get("commits", [])
            count = len(hashes)

            rows = []
            for h in hashes:
                c = commit_map.get(h, {})
                msg = esc(c.get("message", ""))
                ctype = c.get("type", "normal")
                msg_style = ' style="color: var(--text-dim); font-style: italic;"' if ctype in ("test", "fix") else ''
                rows.append(
                    f'<div style="display: flex; align-items: baseline; gap: 10px; '
                    f'padding: 4px 0; font-size: 13px;">'
                    f'<span style="font-family: var(--mono); font-size: 12px; '
                    f'color: var(--accent); flex-shrink: 0;">{esc(h)}</span>'
                    f'<span{msg_style}>{msg}</span>'
                    f'</div>'
                )
            sections.append(
                f'<div style="margin-bottom: 16px;">'
                f'<div style="font-size: 13px; font-weight: 600; margin-bottom: 6px; '
                f'display: flex; align-items: center; gap: 8px;">'
                f'{esc(name)} <span style="color: var(--text-dim); font-weight: 400;">({count})</span>'
                f'</div>'
                f'{"".join(rows)}'
                f'</div>'
            )
        body = ''.join(sections)
        meta = f'<span class="card-meta">{esc(str(total_commits))} commits in {len(groups)} groups</span>'
    else:
        # Flat list
        items = []
        for c in commit_log:
            h = esc(c.get("hash", ""))
            msg = esc(c.get("message", ""))
            ctype = c.get("type", "normal")
            msg_style = ' style="color: var(--text-dim); font-style: italic;"' if ctype in ("test", "fix") else ''
            items.append(
                f'<div style="display: flex; align-items: baseline; gap: 10px; '
                f'padding: 6px 0; border-bottom: 1px solid var(--border); font-size: 14px;">'
                f'<span style="font-family: var(--mono); font-size: 12px; '
                f'color: var(--accent); flex-shrink: 0;">{h}</span>'
                f'<span{msg_style}>{msg}</span>'
                f'</div>'
            )
        body = ''.join(items)
        meta = f'<span class="card-meta">{esc(str(total_commits))} commits</span>'

    return _collapsible_card('Commits', body, meta_html=meta, icon_name='commit')


def render_decisions_learnings(data):
    """Collapsible Decisions + Learnings card (collapsed by default)."""
    decisions = data.get("decisions", [])
    learnings = data.get("learnings", [])
    if isinstance(decisions, str):
        decisions = []
    if isinstance(learnings, str):
        learnings = []
    if not decisions and not learnings:
        return ""

    parts = []
    for d in decisions:
        if isinstance(d, dict):
            title_text = d.get("title", "")
            problem = d.get("problem", "")
            solution = d.get("solution", "")
            context = d.get("context", "")
            rows = []
            if problem:
                rows.append(('Problem', esc(problem)))
            if solution:
                rows.append(('Solution', esc(solution)))
            if context and not problem:
                rows.append(('Context', esc(context)))
            parts.append(dl_item(title_text, rows, pills=[('decision', 'accent')]))
        else:
            parts.append(dl_item(str(d), [], pills=[('decision', 'accent')]))

    for l in learnings:
        if isinstance(l, dict):
            title_text = l.get("title", "")
            problem = l.get("problem", "")
            solution = l.get("solution", "")
            context = l.get("context", "")
            rows = []
            if problem:
                rows.append(('Discovery', esc(problem)))
            if solution:
                rows.append(('Change', esc(solution)))
            if context and not problem:
                rows.append(('Context', esc(context)))
            parts.append(dl_item(title_text, rows, pills=[('learning', 'neutral')]))
        else:
            parts.append(dl_item(str(l), [], pills=[('learning', 'neutral')]))

    body = ''.join(parts)
    d_count = len(decisions)
    l_count = len(learnings)
    counts = []
    if d_count:
        counts.append(f'{d_count} decision{"s" if d_count != 1 else ""}')
    if l_count:
        counts.append(f'{l_count} learning{"s" if l_count != 1 else ""}')
    meta = f'<span class="card-meta">{", ".join(counts)}</span>'

    return _collapsible_card('Decisions + Learnings', body, meta_html=meta,
                             collapsed=True, icon_name='decision')


def render_checks(data):
    """System Checks section — bordered blue card with check rows."""
    checks = data.get("checks")
    if not checks:
        return ""

    audit = checks.get("audit", {})
    doe = checks.get("doeKit", {})
    rows = []

    # Audit rows
    p = audit.get("pass", 0)
    w = audit.get("warn", 0)
    f = audit.get("fail", 0)
    if p or w or f:
        # Status badge
        if f > 0:
            status_badge = f'<span class="checks-badge checks-badge-fail">FAIL {f}</span>'
        elif w > 0:
            status_badge = f'<span class="checks-badge checks-badge-warn">WARN {w}</span>'
        else:
            status_badge = f'<span class="checks-badge checks-badge-pass">PASS {p}</span>'
        rows.append(
            f'<div class="checks-row">{status_badge} '
            f'<span class="checks-label">Claim Audit</span></div>'
        )
        for detail in audit.get("details", []):
            rows.append(
                f'<div class="checks-row checks-detail">{esc(detail)}</div>'
            )

    # DOE Kit row
    version = doe.get("version", "")
    synced = doe.get("synced", True)
    if version:
        if synced:
            rows.append(
                f'<div class="checks-row">'
                f'<span class="checks-badge checks-badge-pass">SYNCED</span> '
                f'<span class="checks-label">DOE Kit</span> '
                f'<span class="checks-value">{esc(version)}</span></div>'
            )
        else:
            u_count = doe.get("userCount", 0)
            c_count = doe.get("creatorCount", 0)
            uc_parts = []
            if u_count:
                uc_parts.append(f'{u_count}u')
            if c_count:
                uc_parts.append(f'{c_count}c')
            uc_label = f' ({" ".join(uc_parts)})' if uc_parts else ''
            rows.append(
                f'<div class="checks-row">'
                f'<span class="checks-badge checks-badge-warn">{esc(version)}*</span> '
                f'<span class="checks-label">DOE Kit</span> '
                f'<span class="checks-value">not synced{esc(uc_label)}</span></div>'
            )

    if not rows:
        return ""

    # Section header with icon
    header_badges = ''
    if w > 0:
        header_badges += f' <span class="checks-badge checks-badge-warn">{w} WARN</span>'
    if f > 0:
        header_badges += f' <span class="checks-badge checks-badge-fail">{f} FAIL</span>'

    inner = '\n'.join(rows)
    return (
        f'<div class="section">'
        f'<div class="section-title" style="margin-bottom: 10px; '
        f'display: flex; align-items: center; gap: 8px;">'
        f'<span style="color: var(--text-faint); display: flex;">{icon("shield")}</span> '
        f'System Checks{header_badges}</div>'
        f'<div class="checks-card">\n{inner}\n</div>'
        f'</div>'
    )


def render_today_sessions(data):
    """Collapsible Today's Sessions card (collapsed by default)."""
    sessions = data.get("todaySessions", [])
    if not sessions:
        return ""

    rows = []
    for s in sessions:
        num = esc(s.get("number", ""))
        dur = esc(s.get("duration", ""))
        summary = esc(s.get("summary", ""))
        time_range = esc(s.get("timeRange", ""))
        commits = s.get("commits", "")

        commits_html = (
            f'<span class="session-row-commits">{esc(str(commits))} commits</span>'
            if commits else ''
        )
        rows.append(
            f'<div class="session-row">'
            f'<span class="session-row-time">{time_range if time_range else f"#{num}"}</span>'
            f'<span class="session-row-duration">{dur}</span>'
            f'<span class="session-row-summary">{summary}</span>'
            f'{commits_html}'
            f'</div>'
        )

    body = ''.join(rows)
    meta = badge(f'{len(sessions)} sessions', 'dim')

    return _collapsible_card("Today's Sessions", body, meta_html=meta,
                             collapsed=True, icon_name='sessions')


def render_awaiting_signoff(data):
    """Awaiting Sign-off section — amber-bordered expandable details cards."""
    items = data.get("awaitingSignOff", [])
    if not items:
        return ""

    cards = []
    for item in items:
        feature = esc(item.get("feature", ""))
        summary = esc(item.get("summary", ""))
        count = item.get("manualItems", 0)
        groups = item.get("groups", [])

        # Build grouped checklist with checkbox squares
        groups_html = ""
        if groups:
            group_parts = []
            for g in groups:
                name = esc(g.get("name", ""))
                gitems = g.get("items", [])
                items_html = '\n'.join(
                    f'<li class="so-item">{esc(i)}</li>' for i in gitems
                )
                group_parts.append(
                    f'<div class="so-group">'
                    f'<div class="so-group-name">{name}'
                    f'<span class="so-group-count">{len(gitems)}</span></div>'
                    f'<ul class="so-checklist">\n{items_html}\n</ul>'
                    f'</div>'
                )
            groups_html = '\n'.join(group_parts)

        summary_html = f'<div class="so-summary">{summary}</div>' if summary else ''

        cards.append(
            f'<details class="so-card">\n'
            f'  <summary class="so-card-header">\n'
            f'    <span class="so-feature">{feature}</span>\n'
            f'    <span class="so-count">{count} items</span>\n'
            f'  </summary>\n'
            f'  {summary_html}\n'
            f'{groups_html}\n'
            f'</details>'
        )

    inner = '\n'.join(cards)
    total_features = len(items)
    total_items = sum(i.get("manualItems", 0) for i in items)

    return (
        f'<div class="section">'
        f'<div class="section-title" style="margin-bottom: 10px; '
        f'display: flex; align-items: center; gap: 8px;">'
        f'<span style="color: var(--text-faint); display: flex;">{icon("check")}</span> '
        f'Awaiting Sign-off '
        f'<span class="so-header-badge">'
        f'{total_features} features &middot; {total_items} manual items</span>'
        f'</div>\n'
        f'{inner}\n'
        f'</div>'
    )


def render_next_up(data):
    """Next Up section with highlighted card."""
    text = data.get("nextUp", "")
    if not text:
        return ""
    return (
        f'<div class="section">'
        f'<p class="section-subtitle" style="margin-bottom: 8px;">Next Up</p>'
        + next_card('Next', esc(text))
        + '</div>'
    )


# ── CSS ────────────────────────────────────────────────────────────────────────

WRAP_CSS = r"""
/* Wrap-specific CSS (base CSS provided by html_builder via page_scaffold) */
  .container { max-width: 800px; }

  /* ── Today's Sessions ── */
  .session-row {
    display: flex; align-items: center; gap: 12px;
    padding: 8px 0; border-bottom: 1px solid var(--border); font-size: 14px;
  }
  .session-row:last-child { border-bottom: none; }
  .session-row-time {
    font-family: var(--mono);
    font-size: 13px; color: var(--text-dim); flex: 0 0 120px;
  }
  .session-row-duration {
    font-family: var(--mono);
    font-size: 13px; font-weight: 600; flex: 0 0 60px;
  }
  .session-row-summary { flex: 1; }
  .session-row-commits {
    font-family: var(--mono);
    font-size: 13px; color: var(--text-dim); flex: 0 0 90px; text-align: right;
  }

  /* ── System Checks (blue bordered card) ── */
  .checks-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 8px; padding: 1rem 1.2rem;
  }
  .checks-row {
    display: flex; align-items: center; gap: 0.8rem;
    padding: 0.3rem 0; font-size: 0.85rem;
  }
  .checks-detail {
    padding-left: 4.5rem; font-size: 0.8rem; color: var(--text-dim);
  }
  .checks-badge {
    font-family: var(--mono);
    font-size: 0.75rem; font-weight: 600;
    padding: 0.15rem 0.5rem; border-radius: 4px;
    flex-shrink: 0;
  }
  .checks-badge-pass { color: var(--green); background: var(--green-dim); }
  .checks-badge-warn { color: var(--text-dim); background: var(--surface-sunk); }
  .checks-badge-fail { color: var(--rose); background: var(--rose-dim); }
  .checks-label { color: var(--text-dim); }
  .checks-value { color: var(--text); }

  /* ── Awaiting Sign-off (amber bordered expandable cards) ── */
  .so-card {
    background: var(--surface); border: 1px solid var(--text-dim);
    border-radius: 8px; margin-bottom: 0.8rem;
  }
  .so-card:last-child { margin-bottom: 0; }
  .so-card-header {
    display: flex; justify-content: space-between; align-items: center;
    padding: 1rem 1.2rem; cursor: pointer; list-style: none;
  }
  .so-card-header::-webkit-details-marker { display: none; }
  .so-card-header::before {
    content: '\25B6'; font-size: 0.6rem; color: var(--text-dim);
    margin-right: 0.6rem; transition: transform 0.2s;
  }
  .so-card[open] > .so-card-header::before { transform: rotate(90deg); }
  .so-feature {
    font-family: var(--mono);
    font-size: 0.85rem; font-weight: 600; color: var(--text); flex: 1;
  }
  .so-count {
    font-family: var(--mono);
    font-size: 0.7rem; color: var(--text-dim); background: var(--surface-sunk);
    padding: 0.15rem 0.5rem; border-radius: 4px; flex-shrink: 0;
  }
  .so-summary {
    font-size: 0.8rem; color: var(--text-dim); line-height: 1.5;
    padding: 0 1.2rem 0.8rem; border-bottom: 1px solid var(--border);
  }
  .so-group { padding: 0.6rem 1.2rem; }
  .so-group:last-child { padding-bottom: 1rem; }
  .so-group-name {
    font-family: var(--mono);
    font-size: 0.7rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.05em; color: var(--text-dim); margin-bottom: 0.3rem;
    display: flex; align-items: center; gap: 0.4rem;
  }
  .so-group-count {
    font-size: 0.6rem; font-weight: 400; color: var(--text-dim);
    background: var(--surface-sunk); padding: 0.05rem 0.35rem; border-radius: 3px;
  }
  .so-checklist { list-style: none; padding: 0; margin: 0; }
  .so-item {
    font-size: 0.8rem; color: var(--text-dim); line-height: 1.6;
    padding: 0.15rem 0 0.15rem 1.2rem; position: relative;
  }
  .so-item::before {
    content: '\25A1'; position: absolute; left: 0;
    color: var(--text-dim); font-size: 0.7rem;
  }
  .so-header-badge {
    font-family: var(--mono);
    font-size: 0.7rem; color: var(--text-dim); margin-left: 8px;
  }
"""


# ── Assembly ───────────────────────────────────────────────────────────────────

def build_html(data):
    """Build the complete HTML string from the data dict."""
    episode = esc(data.get("episode", ""))
    title = esc(data.get("title", ""))

    sections = [
        render_header(data),
        render_metrics(data),
        render_summary(data),
        render_timeline_section(data),
        render_commits(data),
        render_decisions_learnings(data),
        render_checks(data),
        render_today_sessions(data),
        render_awaiting_signoff(data),
        render_next_up(data),
        '<div class="page-footer">Built with <strong>DOE</strong> &mdash; Directive, Orchestration, Execution</div>',
    ]
    body = '<div class="container">\n' + "\n".join(s for s in sections if s) + '\n</div>'

    return page_scaffold(
        f'Session {episode} \u2014 {title}',
        body,
        css=WRAP_CSS,
        js=collapsible_js(),
        theme_toggle=True,
    )


def main():
    parser = argparse.ArgumentParser(description="Generate session wrap-up HTML")
    parser.add_argument("--json", dest="json_str", help="JSON data as a string argument")
    parser.add_argument("--theme", choices=["light", "dark"], default="dark",
                        help="Color theme (legacy, auto-detected now)")
    parser.add_argument("--output", default=".tmp/wrap.html",
                        help="Output HTML file path (default: .tmp/wrap.html)")
    args = parser.parse_args()

    if args.json_str:
        data = json.loads(args.json_str)
    else:
        data = json.load(sys.stdin)

    html_out = build_html(data)

    out_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_out)

    print(out_path)


if __name__ == "__main__":
    main()
