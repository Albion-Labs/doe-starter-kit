#!/usr/bin/env python3
"""Post session wrap summaries to Slack via incoming webhook.

Reads wrap JSON from stdin or --file, formats a Block Kit message,
and POSTs to the webhook URL from .env.

Usage:
    python3 execution/slack_notify.py --channel myproject \\
        --file docs/wraps/session-1.json \\
        --version v1.0.0 --kit-version v1.51.4 \\
        --tag BUILD --feature "My Feature"

Exit codes:
    0 = posted successfully
    1 = error (missing webhook, bad JSON, HTTP failure)
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

TAG_EMOJI = {
    "BUILD": "\U0001f3c1",       # chequered flag
    "PLAN": "\U0001f4d0",        # triangular ruler
    "DEBUG": "\U0001f41b",       # bug
    "HOUSEKEEPING": "\U0001f9f9", # broom
    "RESEARCH": "\U0001f50d",    # magnifying glass
}


def load_env():
    """Read .env file into a dict. Skips comments and blank lines."""
    env = {}
    if not ENV_FILE.exists():
        return env
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def get_webhook_url(channel):
    """Get webhook URL for the given channel name."""
    env = load_env()
    key = f"SLACK_WEBHOOK_URL_{channel.upper()}"
    url = env.get(key)
    if not url:
        print(f"Error: {key} not found in .env", file=sys.stderr)
        return None
    return url


def format_wrap_message(wrap_data, version=None, kit_version=None,
                        tag=None, feature=None):
    """Build a Slack Block Kit message from wrap JSON."""
    project = wrap_data.get("projectName", "Unknown")
    session = wrap_data.get("episode") or wrap_data.get("footer", {}).get("session", "?")
    title = wrap_data.get("title", "Session wrap")
    raw_summary = wrap_data.get("summary", "")

    # Split summary into bullets on sentence boundaries or conjunctions
    sentences = [s.strip() for s in raw_summary.split(". ") if s.strip()]
    if len(sentences) == 1 and " and " in raw_summary and len(raw_summary) > 80:
        # Single long sentence with "and" -- split into clauses
        sentences = [s.strip() for s in raw_summary.split(" and ") if s.strip()]
    if len(sentences) > 1:
        summary = "\n".join(
            f"\u2022 {s.rstrip('.').capitalize() if i > 0 and not s[0].isupper() else s.rstrip('.')}"
            for i, s in enumerate(sentences)
        )
    else:
        summary = raw_summary

    metrics = wrap_data.get("metrics", {})
    commits = metrics.get("commits", 0)
    lines_added = metrics.get("linesAdded", 0)
    lines_removed = metrics.get("linesRemoved", 0)
    steps = metrics.get("stepsCompleted", 0)
    duration = metrics.get("sessionDuration", "?")

    footer = wrap_data.get("footer", {})
    streak = footer.get("streak", 0)

    # Header + subheader
    tag_upper = (tag or "").upper()
    header_text = f"{project} \u00b7 Session {session}"

    # Context line: [TAG] Feature name (or Ad-hoc)
    feat_clean = (feature or "").strip().lower()
    if feat_clean and feat_clean != "none":
        feat_display = feature.strip()
    else:
        feat_display = "Ad-hoc"
    if tag_upper:
        context_line = f"[{tag_upper}] {feat_display}"
    else:
        context_line = feat_display

    # Single stats line: versions + metrics
    parts = []
    if version:
        parts.append(f"*App* {version}")
    if kit_version:
        parts.append(f"*Kit* {kit_version}")
    if commits:
        parts.append(f"*{commits}* commits")
    if lines_added or lines_removed:
        parts.append(f"*+{lines_added}/-{lines_removed}* lines")
    if steps:
        parts.append(f"*{steps}* steps")
    parts.append(f"*{duration}*")
    if streak > 1:
        parts.append(f"streak *{streak}*")
    footer_text = "  \u00b7  ".join(parts)

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header_text,
                "emoji": True,
            },
        },
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": context_line},
            ],
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*{title}*\n\n{summary}",
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": footer_text,
            },
        },
    ]

    return {"blocks": [b for b in blocks if b is not None]}


def post_to_slack(webhook_url, payload):
    """POST JSON payload to Slack webhook. Returns True on success."""
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except urllib.error.HTTPError as e:
        print(f"Slack API error: {e.code} {e.reason}", file=sys.stderr)
        return False
    except urllib.error.URLError as e:
        print(f"Network error: {e.reason}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Post wrap summary to Slack.")
    parser.add_argument(
        "--channel", required=True,
        help="Channel key matching SLACK_WEBHOOK_URL_<CHANNEL> in .env (e.g. myproject)",
    )
    parser.add_argument(
        "--file", default=None,
        help="Path to wrap JSON file. Reads from stdin if omitted.",
    )
    parser.add_argument(
        "--version", default=None,
        help="Current app version (e.g. v0.28.5)",
    )
    parser.add_argument(
        "--kit-version", default=None,
        help="Current DOE kit version (e.g. v1.51.3)",
    )
    parser.add_argument(
        "--tag", default=None,
        help="Session tag: BUILD, PLAN, DEBUG, HOUSEKEEPING, RESEARCH",
    )
    parser.add_argument(
        "--feature", default=None,
        help="Active feature name from todo.md (shown if different from title)",
    )
    args = parser.parse_args()

    webhook_url = get_webhook_url(args.channel)
    if not webhook_url:
        sys.exit(1)

    if args.file:
        try:
            wrap_data = json.loads(Path(args.file).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            print(f"Error reading {args.file}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        try:
            wrap_data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON on stdin: {e}", file=sys.stderr)
            sys.exit(1)

    payload = format_wrap_message(wrap_data, args.version, args.kit_version,
                                  args.tag, args.feature)
    if post_to_slack(webhook_url, payload):
        print(f"Posted session wrap to Slack ({args.channel}).")
    else:
        print(f"Warning: Failed to post to Slack ({args.channel}).", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
