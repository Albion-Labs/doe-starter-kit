#!/usr/bin/env python3
"""Nudge when the installed DOE global tools are behind the kit.

The kit's global tools (``~/.claude/scripts/*.py``, ``~/.claude/commands/*.md``)
are copies installed by ``setup.sh``. A kit release does NOT update them in place
— you have to re-run ``setup.sh``. Nothing tracked that, so stale tools (e.g. an
old ``/wrap`` format) could be used unknowingly.

This is the single freshness check both surfaces call:
  * the SessionStart hook (start of every session), and
  * the ``/wrap`` kit-status step (end of session).

It is SILENT when the tools are current, prints one actionable line when behind,
and never errors out — any problem (no stamp, kit moved, git missing) exits 0
with no output, so it can never block a session.

Signals (both local — no network):
  * "installed" version  -> the stamp ``~/.claude/.doe-tools-version`` that
    setup.sh writes at install time ({"version","kit_path","installed"}).
  * "latest" version     -> ``git -C <kit_path> describe --tags --abbrev=0``
    in the kit checkout the stamp points at. This catches the common case:
    you pulled the kit but didn't re-run setup.

Exit code is always 0. Stdout is the nudge (or empty).
"""

import json
import os
import re
import subprocess
import sys

STAMP_PATH = os.path.expanduser("~/.claude/.doe-tools-version")

_SEMVER = re.compile(r"v?(\d+)\.(\d+)\.(\d+)")


def parse_version(s):
    """Parse 'v1.67.0' (or '1.67.0', or 'v1.67.0-3-gabc') into a (major, minor,
    patch) tuple. Returns None if it doesn't look like a semver."""
    if not s:
        return None
    m = _SEMVER.search(str(s))
    if not m:
        return None
    return tuple(int(g) for g in m.groups())


def is_behind(installed, latest):
    """True only when both parse and latest is strictly newer than installed."""
    iv, lv = parse_version(installed), parse_version(latest)
    if iv is None or lv is None:
        return False
    return lv > iv


def read_stamp(path=None):
    """Return the install stamp dict, or None if absent/unreadable."""
    if path is None:
        path = STAMP_PATH
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except (OSError, ValueError):
        pass
    return None


def kit_latest_version(kit_path):
    """Latest tag in the kit checkout, or None if the path/git is unavailable."""
    if not kit_path or not os.path.isdir(kit_path):
        return None
    try:
        out = subprocess.run(
            ["git", "-C", kit_path, "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    return out.stdout.strip() or None


def nudge_message(installed, latest, kit_path):
    """The one-line nudge surfaced when the tools are behind."""
    setup = os.path.join(kit_path, "setup.sh") if kit_path else "setup.sh"
    return (
        f"[DOE] Global tools are behind the kit — installed {installed}, "
        f"kit has {latest}. Update: bash {setup} --tools-only"
    )


def staleness_line():
    """Return the nudge string if the tools are stale, else '' (current/unknown)."""
    stamp = read_stamp()
    if not stamp:
        return ""  # never stamped (pre-feature / not installed) — stay quiet
    installed = stamp.get("version")
    kit_path = stamp.get("kit_path")
    latest = kit_latest_version(kit_path)
    if latest and is_behind(installed, latest):
        return nudge_message(installed, latest, kit_path)
    return ""


def main():
    try:
        line = staleness_line()
    except Exception:
        # Defensive: a freshness check must never break a session.
        return
    if line:
        print(line)


if __name__ == "__main__":
    main()
    sys.exit(0)
