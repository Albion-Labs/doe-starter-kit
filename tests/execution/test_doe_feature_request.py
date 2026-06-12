"""Tests for execution/doe_feature_request.py --scan-existing (kit v1.71.3).

Liveness-audit finding A6: duplicate detection globbed kit/commands/,
a directory that has never existed (real dirs: global-commands/ and
.claude/commands/). glob on a missing dir returns silently empty, so
the scan had never matched a command since it shipped.
"""
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(KIT / "execution"))

import doe_feature_request  # noqa: E402


def _scan(monkeypatch, kit_path, description):
    monkeypatch.setattr(doe_feature_request, "DOE_KIT_PATH", kit_path)
    return doe_feature_request.scan_existing(description)


def test_scan_matches_global_command(monkeypatch, tmp_path):
    (tmp_path / "global-commands").mkdir()
    (tmp_path / "global-commands" / "wrap.md").write_text(
        "End-of-session wrap: retro, learnings, archive."
    )
    result = _scan(monkeypatch, tmp_path, "session wrap retro")
    matched = [m["file"] for m in result["matches"]]
    assert "global-commands/wrap.md" in matched, (
        f"command docs must be reachable by the duplicate scan; got {matched}"
    )


def test_scan_matches_project_command(monkeypatch, tmp_path):
    cmd_dir = tmp_path / ".claude" / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "review.md").write_text("Adversarial review of the codebase.")
    result = _scan(monkeypatch, tmp_path, "adversarial review")
    matched = [m["file"] for m in result["matches"]]
    assert ".claude/commands/review.md" in matched


def test_scan_against_real_kit_reaches_commands(monkeypatch):
    """On the actual kit checkout, a description lifted from a real command
    doc must surface at least one command file — pins the directory names
    to reality, not just to fixtures."""
    result = _scan(monkeypatch, KIT, "feature request kit")
    assert result["doe_kit_exists"]
    assert any(
        m["file"].startswith(("global-commands/", ".claude/commands/"))
        for m in result["matches"]
    ), f"no command files matched: {[m['file'] for m in result['matches']][:10]}"
