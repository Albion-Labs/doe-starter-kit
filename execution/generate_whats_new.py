#!/usr/bin/env python3
"""Generate docs/tutorial/whats-new.html from CHANGELOG.md.

Usage:
    python3 execution/generate_whats_new.py            # Generate the page
    python3 execution/generate_whats_new.py --preview   # Generate and open in browser
"""

import html
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
KIT_ROOT = SCRIPT_DIR.parent
CHANGELOG = KIT_ROOT / "CHANGELOG.md"
OUTPUT = KIT_ROOT / "docs" / "tutorial" / "whats-new.html"

MONTHS = {
    1: "January", 2: "February", 3: "March", 4: "April",
    5: "May", 6: "June", 7: "July", 8: "August",
    9: "September", 10: "October", 11: "November", 12: "December",
}

# Number of latest releases to show expanded
EXPANDED_COUNT = 5


def get_kit_version():
    """Get the current kit version from the top CHANGELOG entry, or git tag.

    CHANGELOG is primary: auto-release regenerates this page BEFORE the new
    tag exists, so the latest git tag is stale-by-one at exactly that moment.
    The top CHANGELOG heading is what the release workflow itself treats as
    the version being released.
    """
    if CHANGELOG.exists():
        for line in CHANGELOG.read_text(encoding="utf-8").split("\n"):
            m = re.match(r"^##\s+\[?(v[\d.]+)\]?", line)
            if m:
                return m.group(1)
    # Fallback: latest git tag
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, cwd=str(KIT_ROOT),
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except FileNotFoundError:
        pass
    return "v0.0.0"


def parse_changelog(text):
    """Parse CHANGELOG.md into a list of version entries."""
    entries = []
    # Match both formats: ## v1.54.0 (2026-04-07) and ## [v1.2.0] — 2026-03-01
    heading_re = re.compile(
        r"^##\s+\[?(v[\d.]+)\]?\s*(?:—|\()\s*(\d{4}-\d{2}-\d{2})\)?\s*$"
    )

    lines = text.split("\n")
    i = 0
    while i < len(lines):
        m = heading_re.match(lines[i])
        if m:
            version = m.group(1)
            date_str = m.group(2)
            i += 1

            # Check for hero block
            hero = None
            if i < len(lines) and lines[i].strip() == "<!-- hero -->":
                i += 1
                hero_lines = []
                while i < len(lines) and lines[i].strip() != "<!-- /hero -->":
                    hero_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    i += 1  # skip <!-- /hero -->
                hero = " ".join(l.strip() for l in hero_lines if l.strip())

            # Skip blank lines between hero and background blocks
            while i < len(lines) and lines[i].strip() == "":
                i += 1

            # Check for optional background block (postmortem prose that
            # would otherwise bloat the hero). Renders as <h4>Background</h4>
            # + <p class="release-background"> below the hero.
            background = None
            if i < len(lines) and lines[i].strip() == "<!-- background -->":
                i += 1
                bg_lines = []
                while i < len(lines) and lines[i].strip() != "<!-- /background -->":
                    bg_lines.append(lines[i])
                    i += 1
                if i < len(lines):
                    i += 1  # skip <!-- /background -->
                background = " ".join(l.strip() for l in bg_lines if l.strip())

            # Collect subsections until next ## heading
            subsections = []
            current_sub = None
            while i < len(lines) and not heading_re.match(lines[i]):
                sub_m = re.match(r"^###\s+(.+)$", lines[i])
                if sub_m:
                    current_sub = sub_m.group(1).strip()
                    subsections.append((current_sub, []))
                elif current_sub and lines[i].startswith("- "):
                    subsections[-1][1].append(lines[i][2:].strip())
                elif current_sub and lines[i].startswith("  ") and subsections[-1][1]:
                    # Continuation line
                    subsections[-1][1][-1] += " " + lines[i].strip()
                i += 1

            entries.append({
                "version": version,
                "date": date_str,
                "hero": hero,
                "background": background,
                "subsections": subsections,
            })
        else:
            i += 1

    return entries


def format_date(date_str):
    """Convert 2026-04-07 to 7 April 2026."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{dt.day} {MONTHS[dt.month]} {dt.year}"


def month_key(date_str):
    """Return 'April 2026' from '2026-04-07'."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{MONTHS[dt.month]} {dt.year}"


def md_to_html(text):
    """Convert minimal markdown to HTML."""
    escaped = html.escape(text)
    # Bold
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    # Inline code
    escaped = re.sub(r"`(.+?)`", r"<code>\1</code>", escaped)
    # Em dash: -- surrounded by spaces
    escaped = escaped.replace(" -- ", " &mdash; ")
    # Em dash at start of text
    escaped = re.sub(r"^-- ", "&mdash; ", escaped)
    # [APP] and [INFRA] tags -> badges
    escaped = re.sub(
        r"\[APP\]",
        '<span class="tag app">APP</span>',
        escaped,
    )
    escaped = re.sub(
        r"\[INFRA\]",
        '<span class="tag infra">INFRA</span>',
        escaped,
    )
    return escaped


def version_to_id(version):
    """Convert v1.49.0 to v1-49-0 for use as HTML id."""
    return version.replace(".", "-")


def subsection_class(name):
    """Return CSS class for subsection heading colour."""
    n = name.lower()
    if n == "changed":
        return ' class="changed"'
    elif n == "fixed":
        return ' class="fixed"'
    elif n in ("removed", "deprecated"):
        return ' class="removed"'
    elif n == "documentation":
        return ' class="changed"'
    return ""


def render_entry(entry):
    """Render a single version entry as HTML."""
    vid = version_to_id(entry["version"])
    date_fmt = format_date(entry["date"])
    v = html.escape(entry["version"])
    # Count total items across all subsections
    total_items = sum(len(items) for _, items in entry["subsections"])
    is_compact = total_items <= 3 and not entry["hero"]
    css_class = "release release-compact" if is_compact else "release"
    parts = []
    parts.append(f'        <div class="{css_class}" id="{vid}">')
    parts.append(f'          <div class="release-header">')
    parts.append(f'            <span class="version-badge">{v}</span>')
    parts.append(f'            <span class="release-date">{date_fmt}</span>')
    parts.append(f"          </div>")

    if entry["hero"]:
        parts.append(f'          <h4 class="summary">Summary</h4>')
        parts.append(f'          <p class="release-hero">{md_to_html(entry["hero"])}</p>')
    if entry.get("background"):
        parts.append(f'          <h4 class="background">Background</h4>')
        parts.append(f'          <p class="release-background">{md_to_html(entry["background"])}</p>')

    for sub_name, items in entry["subsections"]:
        if not items:
            continue
        cls = subsection_class(sub_name)
        parts.append(f"          <h4{cls}>{html.escape(sub_name)}</h4>")
        parts.append(f"          <ul>")
        for item in items:
            parts.append(f"            <li>{md_to_html(item)}</li>")
        parts.append(f"          </ul>")

    parts.append(f"        </div>")
    return "\n".join(parts)


def render_entries(entries):
    """Render all entries, with expand/collapse for older ones."""
    if not entries:
        return "        <p>No releases found.</p>"

    parts = []

    # Latest N expanded
    expanded = entries[:EXPANDED_COUNT]
    older = entries[EXPANDED_COUNT:]

    for e in expanded:
        parts.append(render_entry(e))

    # Group older by month (preserving order)
    if older:
        month_groups = []
        for e in older:
            mk = month_key(e["date"])
            if month_groups and month_groups[-1][0] == mk:
                month_groups[-1][1].append(e)
            else:
                month_groups.append((mk, [e]))

        for mk, month_entries in month_groups:
            count = len(month_entries)
            parts.append(f'        <details class="month-group">')
            parts.append(f"          <summary>{html.escape(mk)} ({count} release{'s' if count != 1 else ''})</summary>")
            for e in month_entries:
                parts.append(render_entry(e))
            parts.append(f"        </details>")

    return "\n\n".join(parts)


def generate_page(entries):
    """Generate the full HTML page."""
    content = render_entries(entries)
    kit_version = get_kit_version()
    total = len(entries)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <title>What's New &mdash; DOE Starter Kit</title>
  <link id="favicon" rel="icon" type="image/png" href="favicon-light.png">
  <link rel="apple-touch-icon" href="apple-touch-icon.png">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg-body: #FFFFFF;
      --bg-sidebar: #F7F7F5;
      --bg-card: #FFFFFF;
      --bg-card-hover: #F5F5F3;
      --bg-code: #14171A;
      --bg-callout-info: #F4F5F3;
      --bg-callout-tip: #EAF3EC;
      --bg-callout-warn: #F7F0E0;
      --border: #E6E5E1;
      --border-light: #F0EFEC;
      --text-primary: #16181C;
      --text-secondary: #5C6066;
      --text-muted: #8E9095;
      --text-sidebar: #5C6066;
      --text-sidebar-active: #16181C;
      --accent: #216E48;
      --accent-light: #E7F1EB;
      --accent-green: #2E8B57;
      --accent-amber: #9A6B12;
      --accent-blue: #5C6066;
      --accent-rose: #B23A22;
      --sidebar-w: 260px;
      --content-max: 720px;
      --toc-w: 220px;
      --radius: 8px;
      --radius-lg: 12px;
      --shadow-card: 0 1px 2px rgba(20,23,26,0.04), 0 1px 2px rgba(20,23,26,0.06);
      --shadow-card-hover: 0 4px 14px rgba(20,23,26,0.10);
      --font: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
      --font-mono: 'JetBrains Mono', 'SF Mono', ui-monospace, monospace;
    }}

    [data-theme="dark"] {{
      --bg-body: #14171A;
      --bg-sidebar: #15191C;
      --bg-card: #1B2024;
      --bg-card-hover: #20262B;
      --bg-code: #0F1214;
      --bg-callout-info: #1B2024;
      --bg-callout-tip: #15211A;
      --bg-callout-warn: #241F14;
      --border: #2A3138;
      --border-light: #1F252A;
      --text-primary: #E9ECE8;
      --text-secondary: #8B9590;
      --text-muted: #5E6872;
      --text-sidebar: #8B9590;
      --text-sidebar-active: #E9ECE8;
      --accent: #41A56E;
      --accent-light: #1E2A23;
      --accent-green: #4FB97E;
      --accent-amber: #D9A441;
      --accent-blue: #8B9590;
      --accent-rose: #E0654E;
      --shadow-card: 0 1px 2px rgba(0,0,0,0.3);
      --shadow-card-hover: 0 6px 18px rgba(0,0,0,0.45);
    }}

    html {{ scroll-behavior: smooth; }}

    body {{
      font-family: var(--font);
      font-size: 15px;
      line-height: 1.7;
      color: var(--text-primary);
      background: var(--bg-body);
      -webkit-font-smoothing: antialiased;
      transition: background 0.2s, color 0.2s;
    }}

    /* -- Layout -- */
    .layout {{
      display: flex;
      min-height: 100vh;
    }}

    /* -- Sidebar -- */
    .sidebar {{
      position: fixed;
      top: 0;
      left: 0;
      width: var(--sidebar-w);
      height: 100vh;
      background: var(--bg-sidebar);
      border-right: 1px solid var(--border);
      overflow-y: auto;
      z-index: 100;
      display: flex;
      flex-direction: column;
      transition: transform 0.25s ease, background 0.2s, border-color 0.2s;
    }}

    .sidebar-brand {{
      display: block;
      padding: 20px 16px 16px;
      font-size: 14px;
      font-weight: 700;
      color: var(--text-primary);
      text-decoration: none;
      border-bottom: 1px solid var(--border);
      letter-spacing: -0.01em;
      transition: color 0.15s;
      flex-shrink: 0;
    }}
    .sidebar-brand:hover {{ color: var(--accent); }}
    .sidebar-version {{ font-weight: 400; font-size: 11px; color: var(--text-muted); margin-left: 4px; }}

    .sidebar-nav {{
      flex: 1;
      padding: 16px 10px 24px;
      overflow-y: auto;
    }}

    .sidebar-section {{ margin-bottom: 20px; }}

    .sidebar-section-title {{
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--text-muted);
      padding: 0 4px;
      margin-bottom: 6px;
    }}

    .sidebar-link {{
      display: block;
      padding: 5px 8px;
      border-radius: 6px;
      font-size: 13px;
      color: var(--text-sidebar);
      text-decoration: none;
      line-height: 1.4;
      transition: background 0.1s, color 0.1s;
    }}
    .sidebar-link:hover {{
      background: var(--border-light);
      color: var(--text-sidebar-active);
    }}
    .sidebar-link.active {{
      background: var(--accent-light);
      color: var(--accent);
      font-weight: 500;
    }}
    .sidebar-link.nested {{
      padding-left: 20px;
      font-size: 12.5px;
    }}

    /* -- Hamburger (mobile) -- */
    .hamburger {{
      display: none;
      position: fixed;
      top: 14px;
      left: 14px;
      z-index: 200;
      width: 36px;
      height: 36px;
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      cursor: pointer;
      align-items: center;
      justify-content: center;
      flex-direction: column;
      gap: 5px;
      padding: 0;
      transition: background 0.2s;
    }}
    .hamburger span {{
      display: block;
      width: 18px;
      height: 2px;
      background: var(--text-primary);
      border-radius: 2px;
    }}

    /* -- Dark mode button -- */
    /* -- Theme Toggle (sun/moon sliding pill) -- */
    .theme-toggle {{
      position: fixed;
      top: 14px;
      right: 14px;
      z-index: 200;
      display: inline-flex;
      align-items: center;
      width: 62px;
      height: 30px;
      padding: 0;
      border: 1px solid var(--border);
      border-radius: 999px;
      background: var(--bg-card-hover);
      cursor: pointer;
      box-shadow: var(--shadow-card);
      -webkit-tap-highlight-color: transparent;
    }}
    .theme-toggle .tt-thumb {{
      position: absolute;
      top: 2px;
      left: 2px;
      width: 24px;
      height: 24px;
      border-radius: 50%;
      background: var(--accent);
      transition: transform .34s cubic-bezier(.34,1.18,.5,1);
    }}
    .theme-toggle .tt-ic {{
      position: relative;
      z-index: 1;
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      height: 100%;
    }}
    .theme-toggle .tt-ic svg {{ width: 14px; height: 14px; transition: transform .34s cubic-bezier(.34,1.18,.5,1); }}
    .theme-toggle .tt-sun svg {{ color: #fff; }}
    .theme-toggle .tt-moon svg {{ color: var(--text-muted); }}
    [data-theme="dark"] .theme-toggle .tt-thumb {{ transform: translateX(32px); }}
    [data-theme="dark"] .theme-toggle .tt-moon svg {{ color: #fff; }}
    [data-theme="dark"] .theme-toggle .tt-sun svg {{ color: var(--text-muted); transform: rotate(-35deg); }}

    /* -- Sidebar overlay (mobile) -- */
    .sidebar-overlay {{
      display: none;
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,0.4);
      z-index: 99;
    }}
    .sidebar-overlay.visible {{ display: block; }}

    /* -- Content area -- */
    .content-area {{
      margin-left: var(--sidebar-w);
      flex: 1;
      display: flex;
      justify-content: center;
      padding: 40px 48px;
      min-width: 0;
    }}

    .content {{
      max-width: var(--content-max);
      width: 100%;
    }}

    /* -- Typography -- */
    .content h1 {{
      font-size: 32px;
      font-weight: 700;
      line-height: 1.2;
      margin-bottom: 8px;
      letter-spacing: -0.02em;
      color: var(--text-primary);
    }}

    .content h2 {{
      font-size: 22px;
      font-weight: 600;
      margin-top: 48px;
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--border);
      letter-spacing: -0.01em;
      color: var(--text-primary);
    }}

    .content h3 {{
      font-size: 17px;
      font-weight: 600;
      margin-top: 32px;
      margin-bottom: 12px;
      color: var(--text-primary);
    }}

    .content p {{
      color: var(--text-secondary);
      margin-bottom: 16px;
    }}

    .content ul, .content ol {{
      color: var(--text-secondary);
      margin-bottom: 16px;
      padding-left: 20px;
    }}
    .content li {{ margin-bottom: 6px; }}

    .content a {{
      color: var(--accent);
      text-decoration: underline;
    }}
    .content a:hover {{ text-decoration: underline; }}

    .content code {{
      font-family: var(--font-mono);
      font-size: 13px;
      background: var(--bg-sidebar);
      padding: 2px 6px;
      border-radius: 4px;
      border: 1px solid var(--border);
    }}

    /* -- Cards -- */
    .card-grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;
      margin-bottom: 24px;
    }}
    .card-grid.cols-3 {{ grid-template-columns: 1fr 1fr 1fr; }}

    .m-card {{
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 20px;
      background: var(--bg-card);
      transition: all 0.15s;
      text-decoration: none;
      color: inherit;
      display: block;
    }}
    .m-card:hover {{
      border-color: var(--accent);
      box-shadow: var(--shadow-card-hover);
      transform: translateY(-1px);
      text-decoration: none;
    }}

    .card-icon {{
      width: 36px;
      height: 36px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      margin-bottom: 12px;
    }}
    .card-icon.indigo {{ background: var(--accent-light); color: var(--accent); }}
    .card-icon.green  {{ background: #ECFDF5; color: var(--accent-green); }}
    .card-icon.amber  {{ background: #FEF3C7; color: var(--accent-amber); }}
    .card-icon.blue   {{ background: #DBEAFE; color: var(--accent-blue); }}
    .card-icon.rose   {{ background: #FFE4E6; color: var(--accent-rose); }}

    [data-theme="dark"] .card-icon.indigo {{ background: #312E81; }}
    [data-theme="dark"] .card-icon.green  {{ background: #064E3B; }}
    [data-theme="dark"] .card-icon.amber  {{ background: #78350F; }}
    [data-theme="dark"] .card-icon.blue   {{ background: #1E3A5F; }}
    [data-theme="dark"] .card-icon.rose   {{ background: #4C0519; }}

    .m-card h4 {{
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 4px;
      color: var(--text-primary);
    }}
    .m-card p {{
      font-size: 13px;
      color: var(--text-muted);
      margin: 0;
      line-height: 1.5;
    }}

    /* -- Terminal -- */
    .terminal {{
      background: #0F172A;
      border-radius: var(--radius-lg);
      overflow: hidden;
      margin: 24px 0;
      box-shadow: 0 8px 32px rgba(0,0,0,0.15);
    }}
    .terminal-header {{
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 12px 16px;
      background: #1E293B;
    }}
    .terminal-dot {{ width: 12px; height: 12px; border-radius: 50%; }}
    .terminal-dot.red    {{ background: #EF4444; }}
    .terminal-dot.yellow {{ background: #F59E0B; }}
    .terminal-dot.green  {{ background: #22C55E; }}
    .terminal-title {{
      margin-left: 8px;
      font-size: 12px;
      color: #64748B;
      font-family: var(--font-mono);
    }}
    .terminal pre {{
      padding: 20px;
      font-family: var(--font-mono);
      font-size: 13px;
      line-height: 1.7;
      color: #CBD5E1;
      overflow-x: auto;
      margin: 0;
    }}
    .t-comment {{ color: #64748B; }}
    .t-prompt  {{ color: #F59E0B; }}
    .t-cmd     {{ color: #6EE7B7; }}

    /* -- Callout -- */
    .callout {{
      border-radius: var(--radius);
      padding: 14px 16px;
      margin-bottom: 20px;
      font-size: 14px;
      display: flex;
      gap: 10px;
      line-height: 1.5;
    }}
    .callout-icon {{ font-size: 16px; flex-shrink: 0; margin-top: 1px; }}
    .callout.tip {{
      background: var(--bg-callout-tip);
      border: 1px solid #BBF7D0;
      color: #166534;
    }}
    [data-theme="dark"] .callout.tip {{ border-color: #064E3B; color: #6EE7B7; }}
    .callout strong {{ font-weight: 600; }}
    .callout a {{ color: inherit; font-weight: 500; }}
    .callout .callout-body {{ color: inherit; }}

    /* -- Steps -- */
    .steps {{
      margin: 24px 0;
      padding: 0;
      list-style: none;
    }}
    .step {{
      position: relative;
      padding-left: 48px;
      padding-bottom: 24px;
      border-left: 2px solid var(--border);
      margin-left: 14px;
    }}
    .step:last-child {{ border-left: 2px solid transparent; padding-bottom: 0; }}
    .step-number {{
      position: absolute;
      left: -15px;
      top: 0;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: var(--accent);
      color: #fff;
      font-size: 13px;
      font-weight: 600;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .step h4 {{
      font-size: 15px;
      font-weight: 600;
      margin-bottom: 4px;
      color: var(--text-primary);
    }}
    .step p {{
      font-size: 14px;
      color: var(--text-secondary);
      margin: 0 0 8px;
    }}
    .step code {{
      font-family: var(--font-mono);
      font-size: 12px;
      background: var(--bg-sidebar);
      padding: 1px 5px;
      border-radius: 3px;
      border: 1px solid var(--border);
    }}
    .step a {{ color: var(--accent); }}

    /* -- Code block -- */
    .code-block {{
      background: var(--bg-code);
      border-radius: var(--radius);
      padding: 16px 20px;
      margin: 12px 0 16px;
      overflow-x: auto;
    }}
    .code-block pre {{
      margin: 0;
      font-family: var(--font-mono);
      font-size: 13px;
      line-height: 1.6;
      color: #CBD5E1;
    }}

    /* -- Plain English box -- */
    .plain-english {{
      background: linear-gradient(135deg, var(--accent-light), var(--bg-card));
      border: 1px solid var(--accent);
      border-radius: var(--radius-lg);
      padding: 20px 24px;
      margin: 24px 0;
    }}
    .plain-english h4 {{
      font-size: 13px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      color: var(--accent);
      margin-bottom: 8px;
    }}
    .plain-english p {{
      color: var(--text-secondary);
      font-size: 14px;
      margin: 0;
    }}

    /* -- Diagram container -- */
    .diagram {{
      background: var(--bg-card);
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      padding: 20px 16px 12px;
      margin: 24px 0;
      text-align: center;
      box-shadow: var(--shadow-card);
      overflow-x: auto;
    }}
    .diagram svg {{
      width: 100%;
      height: auto;
    }}

    /* -- Pagination -- */
    .pagination {{
      display: flex;
      gap: 16px;
      margin-top: 48px;
      padding-top: 24px;
      border-top: 1px solid var(--border);
    }}
    .pagination a {{
      flex: 1;
      display: block;
      padding: 16px;
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      text-decoration: none;
      color: inherit;
      transition: all 0.15s;
    }}
    .pagination a:hover {{
      border-color: var(--accent);
      box-shadow: var(--shadow-card);
      text-decoration: none;
    }}
    .pg-label {{
      font-size: 11px;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-bottom: 4px;
    }}
    .pg-title {{
      font-size: 14px;
      font-weight: 500;
      color: var(--accent);
    }}
    .pagination .next {{ text-align: right; }}

    /* -- Footer -- */
    .site-footer {{
      margin-top: 48px;
      padding-top: 24px;
      border-top: 1px solid var(--border);
      font-size: 12px;
      color: var(--text-muted);
      text-align: center;
    }}

    /* -- Responsive -- */
    @media (max-width: 900px) {{
      .sidebar {{ transform: translateX(calc(-1 * var(--sidebar-w))); }}
      .sidebar.open {{ transform: translateX(0); }}
      .content-area {{ margin-left: 0; padding: 24px 20px; padding-top: 60px; }}
      .hamburger {{ display: flex; }}
    }}

    @media (max-width: 600px) {{
      .card-grid {{ grid-template-columns: 1fr; }}
      .card-grid.cols-3 {{ grid-template-columns: 1fr; }}
    }}

    @media (min-width: 601px) and (max-width: 900px) {{
      .card-grid.cols-3 {{ grid-template-columns: 1fr 1fr; }}
    }}

    /* -- Right-side TOC -- */
    .toc {{
      width: var(--toc-w);
      min-width: var(--toc-w);
      position: fixed;
      right: 24px;
      top: 120px;
      font-size: 12px;
    }}
    .toc-title {{
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--text-muted);
      margin-bottom: 10px;
    }}
    .toc-link {{
      display: block;
      padding: 3px 0 3px 12px;
      color: var(--text-muted);
      text-decoration: none;
      border-left: 2px solid var(--border);
      transition: all 0.1s;
    }}
    .toc-link:hover {{
      color: var(--text-secondary);
      border-color: var(--text-muted);
    }}
    .toc-link.active {{
      color: var(--accent);
      border-color: var(--accent);
      font-weight: 500;
    }}


    /* -- Release-specific styles -- */
    .version-badge {{
      display: inline-block;
      font-family: var(--font-mono);
      font-size: 15px;
      font-weight: 700;
      background: var(--accent-light);
      color: var(--accent);
      padding: 5px 14px;
      border-radius: 20px;
      letter-spacing: -0.01em;
    }}
    .release-date {{
      font-size: 13px;
      color: var(--text-muted);
      margin-left: 12px;
    }}
    .release-hero {{
      font-size: 14px;
      color: var(--text-secondary);
      line-height: 1.65;
      margin: 10px 0 14px;
      padding: 14px 18px;
      background: linear-gradient(135deg, var(--accent-light), var(--bg-card));
      border-left: 3px solid var(--accent);
      border-radius: 0 var(--radius) var(--radius) 0;
    }}
    /* Summary label sits tight on the hero paragraph below it. */
    .release h4.summary + .release-hero {{ margin-top: 0; }}
    .release-background {{
      font-size: 14px;
      color: var(--text-muted);
      line-height: 1.65;
      margin: 0 0 14px;
      padding: 14px 18px;
      background: var(--bg-card-hover);
      border-left: 3px solid var(--text-muted);
      border-radius: 0 var(--radius) var(--radius) 0;
    }}
    .release {{
      margin-bottom: 20px;
      padding-bottom: 20px;
      border-bottom: 1px solid var(--border);
    }}
    .release-header {{
      display: flex;
      align-items: center;
      margin-bottom: 8px;
    }}
    .release h4 {{
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      color: var(--accent-green);
      margin: 10px 0 4px;
    }}
    .release h4.summary {{ color: var(--accent); }}
    .release h4.background {{ color: var(--text-muted); }}
    .release h4.changed {{ color: var(--accent-blue); }}
    .release h4.fixed {{ color: var(--accent-amber); }}
    .release h4.removed {{ color: var(--accent-rose); }}
    .release h4.docs {{ color: var(--text-muted); }}
    .release ul {{
      margin: 0 0 4px 18px;
      padding: 0;
    }}
    .release li {{
      font-size: 13px;
      color: var(--text-secondary);
      margin-bottom: 2px;
      line-height: 1.55;
    }}
    .release li strong {{
      color: var(--text-primary);
      font-size: 13px;
    }}
    /* Description after the bold title is de-emphasised */
    .release li {{
      color: var(--text-muted);
    }}
    .release li strong {{
      color: var(--text-primary);
    }}
    .release li code {{
      font-size: 11px;
      padding: 1px 4px;
      color: var(--text-muted);
      background: var(--border-light);
      border-color: transparent;
    }}
    [data-theme="dark"] .release li code {{
      background: var(--bg-code);
      border-color: transparent;
    }}
    /* Patch releases (few items) get compact treatment */
    .release-compact {{
      margin-bottom: 12px;
      padding-bottom: 12px;
    }}
    .release-compact .release-header {{
      margin-bottom: 4px;
    }}
    .release-compact h4 {{
      margin: 6px 0 2px;
    }}
    .release-compact .version-badge {{
      font-size: 13px;
      padding: 3px 10px;
    }}

    /* -- Tag badges -- */
    .tag {{
      display: inline-block;
      font-size: 10px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      padding: 2px 6px;
      border-radius: 10px;
      vertical-align: middle;
      margin-right: 4px;
    }}
    .tag.app {{
      background: #DBEAFE;
      color: #1D4ED8;
    }}
    .tag.infra {{
      background: #FEF3C7;
      color: #92400E;
    }}
    [data-theme="dark"] .tag.app {{
      background: #1E3A5F;
      color: #93C5FD;
    }}
    [data-theme="dark"] .tag.infra {{
      background: #78350F;
      color: #FDE68A;
    }}

    /* -- Month groups (collapsed) -- */
    .month-group {{
      margin-bottom: 16px;
      border: 1px solid var(--border);
      border-radius: var(--radius-lg);
      overflow: hidden;
    }}
    .month-group summary {{
      padding: 14px 20px;
      font-size: 15px;
      font-weight: 600;
      color: var(--text-primary);
      cursor: pointer;
      background: var(--bg-sidebar);
      transition: background 0.1s;
      list-style: none;
    }}
    .month-group summary::-webkit-details-marker {{ display: none; }}
    .month-group summary::before {{
      content: "\\25B6";
      display: inline-block;
      margin-right: 10px;
      font-size: 11px;
      color: var(--text-muted);
      transition: transform 0.2s;
    }}
    .month-group[open] summary::before {{ transform: rotate(90deg); }}
    .month-group summary:hover {{ background: var(--bg-card-hover); }}
    .month-group .release {{
      margin: 0;
      padding: 14px 20px;
      border-bottom: 1px solid var(--border);
    }}
    .month-group .release:last-child {{ border-bottom: none; }}
    .month-group .release-compact {{
      padding: 10px 20px;
    }}
  
    /* ALBION-DOC-THEME v2 */
    /* ── typography → Albion scale (Inter, tight tracking) ── */
    body {{ letter-spacing: -0.15px; }}
    .content {{ line-height: 1.65; }}
    .content h1 {{ font-size: 30px; font-weight: 700; letter-spacing: -0.6px; }}
    .content h2 {{ font-size: 19px; font-weight: 700; letter-spacing: -0.4px; margin-top: 38px; }}
    .content h3 {{ font-size: 15px; font-weight: 650; letter-spacing: -0.2px; margin-top: 26px; }}
    .content p, .content li {{ color: var(--text-secondary); }}
    .content a {{ color: var(--accent); font-weight: 500; }}
    .content code {{
      font-family: var(--font-mono); font-size: 12.5px; color: var(--text-primary);
      background: var(--bg-card-hover); border: 1px solid var(--border-light);
      border-radius: 6px; padding: 1.5px 6px;
    }}

    /* ── sidebar → Albion left-rail ── */
    .sidebar {{ background: var(--bg-body); border-right: 1px solid var(--border-light); }}
    .sidebar-brand {{ font-weight: 700; font-size: 15px; letter-spacing: -0.2px; }}
    .sidebar-section {{ margin-bottom: 16px; }}
    .sidebar-section-title {{
      font-size: 11px; font-weight: 500; letter-spacing: 0.02em;
      color: var(--text-muted); text-transform: none; padding: 14px 10px 6px;
    }}
    .sidebar-link {{
      padding: 7px 10px; border-radius: 8px; font-size: 13.5px; font-weight: 500;
      color: var(--text-sidebar); border-left: none !important;
      transition: background .12s, color .12s;
    }}
    .sidebar-link:hover {{ background: var(--bg-card-hover); color: var(--text-primary); }}
    .sidebar-link.active {{
      background: var(--bg-card-hover) !important; color: var(--text-primary) !important;
      font-weight: 600; border-left: none !important; box-shadow: none !important;
    }}
    .sidebar-link.nested {{ font-size: 12.5px; padding-left: 24px; color: var(--text-muted); }}

    /* ── content cards → Albion .fcard ── */
    .card-grid {{ gap: 14px; }}
    .m-card {{
      background: var(--bg-card); border: 1px solid var(--border); border-radius: 12px;
      box-shadow: none; transition: border-color .15s, transform .15s, box-shadow .15s;
    }}
    .m-card:hover {{ border-color: var(--accent); transform: translateY(-2px); box-shadow: var(--shadow-card-hover); }}
    .m-card h4 {{ font-weight: 600; letter-spacing: -0.01em; }}
    .m-card p {{ color: var(--text-secondary); }}
    .card-icon {{
      border-radius: 8px;
      background: var(--accent-light) !important; color: var(--accent) !important;
    }}
    .card-icon.indigo, .card-icon.green, .card-icon.amber, .card-icon.blue, .card-icon.rose {{
      background: var(--accent-light) !important; color: var(--accent) !important;
    }}

    /* ── callouts → Albion restraint (surface + border + tinted icon, no fills) ── */
    .callout {{
      background: var(--bg-card) !important; border: 1px solid var(--border) !important;
      border-radius: 10px; padding: 14px 16px; gap: 12px;
    }}
    .callout .callout-body {{ color: var(--text-secondary) !important; }}
    .callout .callout-body strong, .callout strong {{ color: var(--text-primary) !important; }}
    .callout.tip {{ border-color: color-mix(in srgb, var(--accent) 26%, var(--border)) !important; }}
    .callout.tip .callout-icon {{ color: var(--accent) !important; }}
    .callout.info .callout-icon {{ color: var(--text-muted) !important; }}
    .callout.warn {{ border-color: color-mix(in srgb, var(--accent-amber) 40%, var(--border)) !important; }}
    .callout.warn .callout-icon {{ color: var(--accent-amber) !important; }}

    /* ── steps → Albion accent circle, neutral connector ── */
    .step {{ border-left: 2px solid var(--border-light); }}
    .step-number {{ background: var(--accent); color: #fff; border-radius: 50%; box-shadow: none; }}
    .step h4 {{ font-weight: 600; }}
    .step p {{ color: var(--text-secondary); }}

    /* ── hero → Albion editorial (left-aligned, like .pagehead) ── */
    .hero {{ text-align: left; padding: 6px 0 30px; }}
    .hero h1 {{ margin-left: 0; margin-right: 0; }}
    .hero .subtitle {{ text-align: left; margin: 14px 0 0; max-width: 640px; }}

    /* ── badges / chips → Albion mono chip ── */
    .cmd-badge, .version-badge, .hero-badge, .layer-badge {{
      font-family: var(--font-mono); font-size: 11px; font-weight: 600; letter-spacing: 0.02em;
      border-radius: 6px; padding: 2px 8px;
      background: var(--accent-light); color: var(--accent); border: none;
    }}
    .risk-badge, .impact-badge {{
      font-size: 10px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;
      border-radius: 6px; padding: 3px 7px;
    }}

    /* ── tabs → Albion pill group ── */
    .env-tabs, .content-tabs {{
      background: var(--bg-card); border: 1px solid var(--border); border-radius: 9px; padding: 3px; gap: 0;
    }}
    .env-tab-btn, .content-tab-btn {{
      border-radius: 6px; font-size: 12.5px; font-weight: 500; color: var(--text-muted); border: none;
    }}
    .env-tab-btn.active, .content-tab-btn.active {{
      background: var(--bg-card-hover); color: var(--text-primary);
      box-shadow: inset 0 0 0 1px var(--border-light); border: none;
    }}

    /* ── on-this-page TOC → Albion label ── */
    .toc-title {{ font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--text-muted); font-weight: 600; }}
    .toc-link {{ font-size: 12.5px; color: var(--text-muted); }}
    .toc-link:hover {{ color: var(--text-primary); }}
    .toc-link.active {{ color: var(--accent); border-color: var(--accent); font-weight: 500; }}

    /* ── code-block / mockup containers → Albion radius (interiors untouched) ── */
    pre, .code-block, .terminal, .vscode-mockup, .terminal-window, .code-window {{
      border-radius: 12px;
    }}

    /* ── tables → Albion hairline rows ── */
    .content table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
    .content th {{
      text-align: left; font-size: 11px; letter-spacing: 0.04em; text-transform: uppercase;
      color: var(--text-muted); font-weight: 600; padding: 9px 12px; border-bottom: 1px solid var(--border);
    }}
    .content td {{ padding: 10px 12px; border-bottom: 1px solid var(--border-light); color: var(--text-secondary); vertical-align: top; }}

    /* ── glossary search / filter → Albion input + pill ── */
    .search-bar {{ background: var(--bg-card); border: 1px solid var(--border); border-radius: 9px; }}
    .search-input {{ color: var(--text-primary); }}
    .filter-pill {{
      background: var(--bg-card); border: 1px solid var(--border); border-radius: 8px;
      font-size: 12px; color: var(--text-muted); padding: 6px 12px;
    }}
    .filter-pill.active {{ background: var(--bg-card-hover); color: var(--text-primary); box-shadow: inset 0 0 0 1px var(--border-light); }}

    /* ── straggler fixes: kill left-edge stripes, neutralise categorical badges ── */
    .doe-callout {{ border-left: 1px solid var(--border) !important; }}
    .release-hero {{
      border: none !important;
      border-left: 4px solid var(--accent) !important;
      background: linear-gradient(135deg, var(--accent-light), var(--bg-card)) !important;
      border-radius: 0 var(--radius) var(--radius) 0 !important;
    }}
    .release-background {{
      border: none !important;
      border-left: 4px solid var(--accent-amber) !important;
      background: var(--bg-callout-warn) !important;
      border-radius: 0 var(--radius) var(--radius) 0 !important;
    }}
    .release h4.summary {{ color: var(--accent) !important; }}
    .release h4.background {{ color: var(--accent-amber) !important; }}
    .layer-badge.universal, .layer-badge.public, .layer-badge.data, .layer-badge.regulated,
    [data-theme="dark"] .layer-badge.universal, [data-theme="dark"] .layer-badge.public,
    [data-theme="dark"] .layer-badge.data, [data-theme="dark"] .layer-badge.regulated {{
      background: var(--bg-card-hover) !important; color: var(--text-secondary) !important;
    }}
    .badge-read, [data-theme="dark"] .badge-read {{
      background: var(--bg-card-hover) !important; color: var(--text-secondary) !important;
    }}

    /* ── only show the right-hand TOC when there's room (was overlapping
          the glossary filter-pills / wide content at ~1280px) ── */
    @media (max-width: 1340px) {{ .toc {{ display: none !important; }} }}
  </style>
</head>
<body>

  <!-- Mobile hamburger -->
  <button class="hamburger" id="hamburger" aria-label="Open menu">
    <span></span><span></span><span></span>
  </button>

  <!-- Dark mode toggle -->
  <button class="theme-toggle" id="themeBtn" aria-label="Toggle dark mode"><span class="tt-thumb"></span><span class="tt-ic tt-sun"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3.6"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.1 5.1l1.4 1.4M17.5 17.5l1.4 1.4M18.9 5.1l-1.4 1.4M6.5 17.5l-1.4 1.4"/></svg></span><span class="tt-ic tt-moon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M20.5 14.5A8.5 8.5 0 1 1 9.5 3.5a6.6 6.6 0 0 0 11 11Z"/></svg></span></button>

  <!-- Sidebar overlay -->
  <div class="sidebar-overlay" id="sidebarOverlay"></div>

  <div class="layout">

    <!-- Sidebar -->
    <!-- The tutorial site was retired in v1.72.0 (kit is internal-only; docs/reference/
         holds the markdown docs). This page is the sole survivor, so the sidebar is
         just the brand + changelog. -->
    <nav class="sidebar" id="sidebar">
      <a class="sidebar-brand" href="whats-new.html">DOE Starter Kit <span class="sidebar-version">{kit_version}</span></a>
      <div class="sidebar-nav">

        <div class="sidebar-section">
          <div class="sidebar-section-title">What's New</div>
          <a class="sidebar-link active" href="whats-new.html">Changelog</a>
        </div>

      </div>
    </nav>

    <!-- Main Content -->
    <div class="content-area">
      <div class="content">

        <h1>What's New</h1>
        <p style="font-size: 17px; color: var(--text-secondary); margin-bottom: 32px;">Every release of the DOE Starter Kit, newest first.</p>

{content}

        <footer class="site-footer">DOE Starter Kit {kit_version}</footer>

      </div><!-- /content -->
    </div><!-- /content-area -->

  </div><!-- /layout -->

  <script>
    // Dark mode
    (function () {{
      var btn  = document.getElementById('themeBtn');
      var html = document.documentElement;

      function applyTheme(dark) {{
        var fav = document.getElementById('favicon');
        if (fav) fav.href = dark ? 'favicon-dark.png' : 'favicon-light.png';
        if (dark) {{
          html.setAttribute('data-theme', 'dark');
        }} else {{
          html.removeAttribute('data-theme');
        }}
      }}

      var stored = localStorage.getItem('doe-docs-theme');
      applyTheme(stored === 'dark');

      btn.addEventListener('click', function () {{
        var isDark = html.getAttribute('data-theme') === 'dark';
        localStorage.setItem('doe-docs-theme', isDark ? 'light' : 'dark');
        applyTheme(!isDark);
      }});
    }})();

    // Mobile sidebar
    (function () {{
      var hamburger = document.getElementById('hamburger');
      var sidebar   = document.getElementById('sidebar');
      var overlay   = document.getElementById('sidebarOverlay');

      function open()  {{ sidebar.classList.add('open');    overlay.classList.add('visible'); }}
      function close() {{ sidebar.classList.remove('open'); overlay.classList.remove('visible'); }}

      hamburger.addEventListener('click', function () {{
        sidebar.classList.contains('open') ? close() : open();
      }});
      overlay.addEventListener('click', close);
    }})();
  </script>

</body>
</html>"""


def main():
    if not CHANGELOG.exists():
        print(f"Error: {CHANGELOG} not found", file=sys.stderr)
        sys.exit(1)

    text = CHANGELOG.read_text(encoding="utf-8")
    entries = parse_changelog(text)

    if not entries:
        print("Error: no version entries found in CHANGELOG.md", file=sys.stderr)
        sys.exit(1)

    page_html = generate_page(entries)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(page_html, encoding="utf-8")

    print(f"Generated {OUTPUT} ({len(entries)} releases)")

    if "--preview" in sys.argv:
        if sys.platform == "darwin":
            subprocess.run(["open", str(OUTPUT)])
        elif sys.platform == "linux":
            subprocess.run(["xdg-open", str(OUTPUT)])
        else:
            print(f"Open {OUTPUT} in your browser")


if __name__ == "__main__":
    main()
