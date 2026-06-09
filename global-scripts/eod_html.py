#!/usr/bin/env python3
"""Generate an end-of-day HTML report from JSON data.

Aggregates all sessions from a single day into one report.
Lives at: ~/.claude/scripts/eod_html.py (global script, installed from DOE kit)

Usage:
    python3 ~/.claude/scripts/eod_html.py --json '{"projectName": "...", ...}' --output .tmp/eod.html
    echo '{"projectName": "..."}' | python3 ~/.claude/scripts/eod_html.py
"""

import argparse
import json
import os
import sys
from datetime import datetime

from html_builder import (
    page_scaffold, esc, badge, metric_grid, data_table, raw, icon,
    dl_item, check_row, page_header, collapsible_js, bar_chart,
    allocation_bar, stats_bar,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

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
    """Page header: label, title, stats bar."""
    project = data.get("projectName", "")
    header = page_header('End of Day Report', project)

    # Stats bar
    date_str = data.get("date", "")
    streak = data.get("streak", 0)
    sessions_count = data.get("metrics", {}).get("sessions", 0)

    pretty_date = date_str
    try:
        dt = datetime.strptime(date_str, "%d/%m/%y")
        day = dt.day
        suffix = "th" if 11 <= day <= 13 else {1: "st", 2: "nd", 3: "rd"}.get(day % 10, "th")
        pretty_date = f"{dt.strftime('%A')} {day}{suffix} {dt.strftime('%B')}"
    except (ValueError, TypeError):
        pass

    time_now = datetime.now().strftime("%H:%M")

    bar_items = []
    if pretty_date:
        bar_items.append(f'{pretty_date} -- {time_now}')
    if sessions_count:
        bar_items.append(f'{sessions_count} sessions')
    if streak:
        bar_items.append(f'Streak: {streak} days')

    bar_html = stats_bar(bar_items) if bar_items else ''

    return header + '\n' + bar_html


def render_metrics(data):
    """Twelve-tile stat grid — 3 bands of 4 (cadence -> output -> outcomes)."""
    m = data.get("metrics", {})
    if not m:
        return ""

    added = m.get("linesAdded", 0)
    removed = m.get("linesRemoved", 0)
    decisions = data.get("decisions", [])
    learnings = data.get("learnings", [])
    d_count = len(decisions) if isinstance(decisions, list) else 0
    l_count = len(learnings) if isinstance(learnings, list) else 0
    prs = m.get("prsMerged", 0)

    tiles = [
        # Band 1 — cadence
        (str(m.get("sessions", 0)), 'Sessions'),
        (str(m.get("totalDuration", "") or "N/A"), 'Total Time'),
        (str(m.get("avgSession", "") or "N/A"), 'Avg Session'),
        (str(m.get("commits", 0)), 'Commits'),
        # Band 2 — output
        (f'+{added}', 'Lines Added', 'acc'),
        (f'−{removed}', 'Lines Removed', 'faint'),
        (str(m.get("filesTouched", 0)), 'Files Touched'),
        (str(m.get("stepsCompleted", 0)), 'Steps Done'),
        # Band 3 — outcomes & knowledge
        (str(m.get("featuresCompleted", 0)), 'Features Shipped'),
        (str(d_count), 'Decisions'),
        (str(l_count), 'Learnings'),
        (str(prs), 'PRs Merged', 'acc' if prs else None),
    ]
    return f'<div class="section">{metric_grid(tiles, columns=4)}</div>'


def render_summary(data):
    """Collapsible Summary card with session details and vibe."""
    summary_text = data.get("summary", "")
    breakdowns = data.get("breakdowns", [])
    session_timeline = data.get("sessionTimeline", [])

    # Backward compat: old-style list format
    if isinstance(summary_text, list):
        summary_text = " ".join(summary_text)
    if not summary_text and not breakdowns and not session_timeline:
        return ""

    parts = []
    if summary_text:
        parts.append(
            f'<p style="margin-bottom: 16px; color: var(--text);">{esc(summary_text)}</p>')

    # Session entries (wireframe pattern: session summaries in Summary card)
    if session_timeline:
        for item in session_timeline:
            num = item.get("number", "")
            duration = item.get("duration", "")
            sess_summary = item.get("summary", "")
            parts.append(
                f'<div style="margin-bottom: 10px;">'
                f'<strong style="color: var(--text);">Session {esc(str(num))}</strong> '
                f'<span class="card-meta">({esc(str(duration))})</span>'
                f'<div style="margin-top: 4px;">{esc(sess_summary)}</div>'
                f'</div>'
            )
    elif breakdowns:
        # Backward compat: old breakdown format
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

    # Vibe footer
    vibe = data.get("vibe")
    if vibe:
        emoji = vibe.get("emoji", "")
        text = esc(vibe.get("text", ""))
        vibe_str = f'{emoji} {text}'.strip() if emoji else text
        parts.append(
            f'<div style="margin-top: 16px; padding-top: 14px; border-top: 1px solid var(--border);">'
            f'<span style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.06em; '
            f'color: var(--text-dim); font-weight: 600;">Vibe</span>'
            f'<div style="margin-top: 4px; color: var(--text);">{vibe_str}</div>'
            f'</div>'
        )

    body = '\n'.join(parts)

    # Header badge from tag
    meta = ''
    tag = data.get("tag")
    if tag:
        variant_map = {
            'BUILD': 'pass', 'PLAN': 'info', 'DEBUG': 'dim',
            'HOUSEKEEPING': 'dim', 'RESEARCH': 'accent',
        }
        meta = badge(tag.upper(), variant_map.get(tag.upper(), 'dim'))

    return _collapsible_card('Summary', body, meta_html=meta, icon_name='summary')


def render_daily_timeline(data):
    """Collapsible Daily Timeline card with allocation bar and session table."""
    items = data.get("sessionTimeline", [])
    if not items:
        return ""

    total_dur = data.get("metrics", {}).get("totalDuration", "")

    # Allocation bar: aggregate by tag
    # Monochrome allocation (EOD is non-triage): the Albion green + muted greys,
    # no alert colours.
    tag_color_map = {
        'BUILD': 'var(--accent)', 'PLAN': 'var(--text-dim)',
        'DEBUG': 'var(--text-faint)', 'HOUSEKEEPING': 'var(--text-faint)',
        'RESEARCH': 'var(--status-live)',
    }
    tag_label_map = {
        'BUILD': 'Build', 'PLAN': 'Planning',
        'DEBUG': 'Debug', 'HOUSEKEEPING': 'Housekeeping',
        'RESEARCH': 'Research',
    }
    tag_pcts = {}
    tag_order = []
    for item in items:
        tag = (item.get("tag", "") or "BUILD").upper()
        if tag not in tag_pcts:
            tag_order.append(tag)
        tag_pcts[tag] = tag_pcts.get(tag, 0) + item.get("pct", 0)

    alloc_html = ''
    total_pct = sum(tag_pcts.values())
    if total_pct > 0:
        segments = []
        labels = []
        for tag in tag_order:
            pct = tag_pcts[tag]
            if pct > 0:
                color = tag_color_map.get(tag, 'var(--text-dim)')
                segments.append((pct, color))
                label = tag_label_map.get(tag, tag.title())
                labels.append(f'{label} {pct}%')

        label_spans = ''.join(f'<span>{esc(lbl)}</span>' for lbl in labels)
        alloc_html = (
            f'<div style="margin-bottom: 20px;">'
            f'<div style="font-size: 13px; margin-bottom: 6px; '
            f'color: var(--text-dim); font-weight: 500;">Time allocation</div>'
            f'{allocation_bar(segments)}'
            f'<div style="display: flex; gap: 14px; font-size: 13px; '
            f'color: var(--text-dim);">{label_spans}</div>'
            f'</div>'
        )

    # Session table
    headers = ['Session', 'Time', 'Focus', 'Share', 'Model', 'Tag']
    rows = []
    for item in items:
        num = item.get("number", "")
        start = item.get("start", "")
        duration = item.get("duration", "")
        sess_summary = item.get("summary", "")
        pct = item.get("pct", 0)
        model = item.get("model", "")
        tag = item.get("tag", "")

        time_display = start
        if start and duration:
            time_display = f'{start} ({duration})'
        elif duration:
            time_display = duration

        model_name = ""
        if model:
            m = model.lower()
            if "opus" in m:
                model_name = "Opus 4.6"
            elif "sonnet" in m:
                model_name = "Sonnet 4.6"
            elif "haiku" in m:
                model_name = "Haiku 4.5"
            else:
                model_name = model

        tag_html = ""
        if tag:
            variant_map = {
                'BUILD': 'pass', 'PLAN': 'accent', 'DEBUG': 'dim',
                'HOUSEKEEPING': 'dim', 'RESEARCH': 'info',
            }
            tag_html = badge(tag.upper(), variant_map.get(tag.upper(), 'dim'))

        rows.append([
            raw(f'<strong>{esc(str(num))}</strong>'),
            raw(f'<span class="mono">{esc(time_display)}</span>'),
            sess_summary,
            f'{pct}%' if pct else '',
            raw(f'<span style="font-size: 13px; color: var(--text-dim);">'
                f'{esc(model_name)}</span>'),
            raw(tag_html),
        ])

    table_html = data_table(headers, rows) if rows else ''

    # Total
    total_html = ''
    if total_dur:
        mono = "var(--mono)"
        total_html = (
            f'<div style="margin-top: 12px; text-align: right;">'
            f'<span style="font-family: {mono}; font-size: 13px; '
            f'font-weight: 600;">Total: {esc(total_dur)}</span></div>'
        )

    body = alloc_html + table_html + total_html
    count = len(items)
    meta = f'<span class="card-meta">{count} sessions, {esc(total_dur)} total</span>'

    return _collapsible_card('Daily Timeline', body, meta_html=meta, icon_name='clock')


def render_commit_breakdown(data):
    """Collapsible Commit Breakdown card with horizontal bars."""
    items = data.get("commitBreakdown", [])
    if not items:
        return ""

    total_commits = data.get("metrics", {}).get("commits", 0)
    max_count = max((item.get("count", 0) for item in items), default=1)

    # Monochrome bars: accent green alternating with a muted grey.
    colors = ['var(--accent)', 'var(--text-faint)']
    chart_rows = []
    for i, item in enumerate(items):
        name = item.get("name", "")
        count = item.get("count", 0)
        color = colors[i % len(colors)]
        chart_rows.append((name, count, max_count, color))

    body = bar_chart(chart_rows)
    meta = (
        f'<span class="card-meta">'
        f'{total_commits} commits in {len(items)} groups</span>'
    )

    return _collapsible_card('Commit Breakdown', body, meta_html=meta, icon_name='commit')


def render_decisions(data):
    """Collapsible Decisions card (collapsed by default)."""
    decisions = data.get("decisions", [])
    if isinstance(decisions, str):
        decisions = []
    if not decisions:
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

    body = ''.join(parts)
    count = len(decisions)
    meta = f'<span class="card-meta">{count} decision{"s" if count != 1 else ""}</span>'

    return _collapsible_card(
        'Decisions', body, meta_html=meta, collapsed=True, icon_name='decision')


def render_learnings(data):
    """Collapsible Learnings card (collapsed by default)."""
    learnings = data.get("learnings", [])
    if isinstance(learnings, str):
        learnings = []
    if not learnings:
        return ""

    parts = []
    for learning in learnings:
        if isinstance(learning, dict):
            title_text = learning.get("title", "")
            problem = learning.get("problem", "")
            solution = learning.get("solution", "")
            context = learning.get("context", "")
            rows = []
            if problem:
                rows.append(('Discovery', esc(problem)))
            if solution:
                rows.append(('Change', esc(solution)))
            if context and not problem:
                rows.append(('Context', esc(context)))
            parts.append(dl_item(title_text, rows, pills=[('learning', 'neutral')]))
        else:
            parts.append(dl_item(str(learning), [], pills=[('learning', 'neutral')]))

    body = ''.join(parts)
    count = len(learnings)
    meta = f'<span class="card-meta">{count} learning{"s" if count != 1 else ""}</span>'

    return _collapsible_card(
        'Learnings', body, meta_html=meta, collapsed=True, icon_name='learning')


def render_checks(data):
    """Collapsible System Checks card (collapsed by default)."""
    checks = data.get("checks")
    if not checks:
        return ""

    audit = checks.get("audit", {})
    doe = checks.get("doeKit", {})
    check_parts = []

    # Audit section
    p = audit.get("pass", 0)
    w = audit.get("warn", 0)
    f_count = audit.get("fail", 0)
    if p or w or f_count:
        audit_rows = [check_row(f'{p} criteria passing', 'pass')]
        for detail in audit.get("details", []):
            status = 'fail' if f_count > 0 else 'warn'
            audit_rows.append(check_row(esc(detail), status))
        if f_count == 0:
            audit_rows.append(check_row('0 failures', 'pass'))

        check_parts.append(
            f'<div style="margin-bottom: 16px;">'
            f'<div style="font-size: 13px; font-weight: 600; '
            f'margin-bottom: 8px; color: var(--text);">Audit</div>'
            f'{"".join(audit_rows)}'
            f'</div>'
        )

    # DOE Kit section
    version = doe.get("version", "")
    synced = doe.get("synced", True)
    if version:
        kit_rows = [check_row(f'Version: {esc(version)}', 'pass')]
        if synced:
            kit_rows.append(check_row('Synced', 'pass'))
        else:
            u_count = doe.get("userCount", 0)
            c_count = doe.get("creatorCount", 0)
            uc_parts = []
            if u_count:
                uc_parts.append(f'{u_count}u')
            if c_count:
                uc_parts.append(f'{c_count}c')
            uc_label = f' ({" ".join(uc_parts)})' if uc_parts else ''
            kit_rows.append(check_row(f'Not synced{esc(uc_label)}', 'warn'))

        u_display = doe.get("userCount", 0)
        c_display = doe.get("creatorCount", 0)
        if u_display or c_display:
            count_parts = []
            if u_display:
                count_parts.append(f'{u_display} pulls')
            if c_display:
                count_parts.append(f'{c_display} syncs')
            kit_rows.append(check_row(', '.join(count_parts), 'pass'))

        check_parts.append(
            f'<div>'
            f'<div style="font-size: 13px; font-weight: 600; '
            f'margin-bottom: 8px; color: var(--text);">DOE Kit</div>'
            f'{"".join(kit_rows)}'
            f'</div>'
        )

    if not check_parts:
        return ""

    body = ''.join(check_parts)

    # Header badges
    header_badges = []
    if p > 0:
        header_badges.append(badge(f'{p} PASS', 'pass'))
    if w > 0:
        header_badges.append(badge(f'{w} WARN', 'warn'))
    if f_count > 0:
        header_badges.append(badge(f'{f_count} FAIL', 'fail'))
    meta = ' '.join(header_badges)

    return _collapsible_card(
        'System Checks', body, meta_html=meta, collapsed=True, icon_name='shield')


def render_next_up(data):
    """Next Up card matching wireframe."""
    text = data.get("nextUp", "")
    if not text:
        return ""

    return (
        f'<div class="section">'
        f'<div class="card">'
        f'<div class="card-header">'
        f'<div style="display: flex; align-items: center; gap: 8px;">'
        f'<span class="card-title">Next Up</span>'
        f' {badge("QUEUED", "info")}'
        f'</div>'
        f'</div>'
        f'<div class="card-body">'
        f'<div style="color: var(--text);">{esc(text)}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


# ── EOD-specific CSS ──────────────────────────────────────────────────────────

EOD_CSS = r"""
/* EOD-specific CSS (base CSS provided by html_builder via page_scaffold) */
  .container { max-width: 800px; }
  .allocation-segment { opacity: 0.75; }
"""


# ── Assembly ───────────────────────────────────────────────────────────────────

def build_html(data):
    """Build the complete HTML string from the data dict."""
    project = esc(data.get("projectName", ""))
    date = esc(data.get("date", ""))

    sections = [
        render_header(data),
        render_metrics(data),
        render_summary(data),
        render_daily_timeline(data),
        render_commit_breakdown(data),
        render_decisions(data),
        render_learnings(data),
        render_checks(data),
        render_next_up(data),
        '<div class="page-footer">Built with <strong>DOE</strong>'
        ' &mdash; Directive, Orchestration, Execution</div>',
    ]
    body = (
        '<div class="container">\n'
        + "\n".join(s for s in sections if s)
        + '\n</div>'
    )

    return page_scaffold(
        f'{project} \u2014 EOD Report {date}',
        body,
        css=EOD_CSS,
        js=collapsible_js(),
        theme_toggle=True,
    )


def main():
    parser = argparse.ArgumentParser(description="Generate end-of-day HTML report")
    parser.add_argument("--json", dest="json_str",
                        help="JSON data as a string argument")
    parser.add_argument("--theme", choices=["light", "dark"], default="dark",
                        help="Color theme (legacy, auto-detected now)")
    parser.add_argument("--output", default=".tmp/eod.html",
                        help="Output HTML file path (default: .tmp/eod.html)")
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
