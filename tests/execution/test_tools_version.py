"""Tests for global-scripts/check_tools_version.py — the global-tools staleness check.

The check must be silent when current and never raise; these tests pin the version
comparison (numeric, not lexical), the stamp parsing, and the silent-on-anything-odd
behaviour.
"""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "global-scripts"))

import check_tools_version as c


# ── parse_version ────────────────────────────────────────────
def test_parse_version_forms():
    assert c.parse_version("v1.67.0") == (1, 67, 0)
    assert c.parse_version("1.2.3") == (1, 2, 3)
    assert c.parse_version("v1.67.0-3-gabc123") == (1, 67, 0)  # ahead-of-tag describe


def test_parse_version_rejects_junk():
    for bad in (None, "", "unknown", "v1.2", "garbage"):
        assert c.parse_version(bad) is None


# ── is_behind ────────────────────────────────────────────────
def test_is_behind_true_only_when_strictly_newer():
    assert c.is_behind("v1.66.0", "v1.67.0") is True
    assert c.is_behind("v1.67.0", "v1.67.0") is False
    assert c.is_behind("v1.68.0", "v1.67.0") is False


def test_is_behind_is_numeric_not_lexical():
    # 1.9.0 < 1.10.0 numerically (would be wrong if compared as strings)
    assert c.is_behind("v1.9.0", "v1.10.0") is True
    assert c.is_behind("v1.10.0", "v1.9.0") is False


def test_is_behind_safe_on_unparseable():
    assert c.is_behind(None, "v1.0.0") is False
    assert c.is_behind("v1.0.0", "nonsense") is False


# ── read_stamp ───────────────────────────────────────────────
def test_read_stamp_roundtrip(tmp_path):
    p = tmp_path / "stamp.json"
    p.write_text(json.dumps({"version": "v1.67.0", "kit_path": "/x"}))
    assert c.read_stamp(str(p)) == {"version": "v1.67.0", "kit_path": "/x"}


def test_read_stamp_missing_or_malformed(tmp_path):
    assert c.read_stamp(str(tmp_path / "nope.json")) is None
    bad = tmp_path / "bad.json"
    bad.write_text("{ not json")
    assert c.read_stamp(str(bad)) is None


# ── staleness_line (the surfaced behaviour) ──────────────────
def _stamp(tmp_path, version, kit_path="/kit"):
    p = tmp_path / ".doe-tools-version"
    p.write_text(json.dumps({"version": version, "kit_path": kit_path}))
    return str(p)


def test_staleness_line_nudges_when_behind(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "STAMP_PATH", _stamp(tmp_path, "v1.66.0"))
    monkeypatch.setattr(c, "kit_latest_version", lambda kp: "v1.67.0")
    line = c.staleness_line()
    assert line.startswith("[DOE]")
    assert "v1.66.0" in line and "v1.67.0" in line
    assert "setup.sh --tools-only" in line


def test_staleness_line_silent_when_current(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "STAMP_PATH", _stamp(tmp_path, "v1.67.0"))
    monkeypatch.setattr(c, "kit_latest_version", lambda kp: "v1.67.0")
    assert c.staleness_line() == ""


def test_staleness_line_silent_without_stamp(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "STAMP_PATH", str(tmp_path / "absent.json"))
    assert c.staleness_line() == ""


def test_staleness_line_silent_when_kit_unavailable(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "STAMP_PATH", _stamp(tmp_path, "v1.0.0", kit_path="/nope"))
    monkeypatch.setattr(c, "kit_latest_version", lambda kp: None)
    assert c.staleness_line() == ""


def test_nudge_message_is_actionable():
    msg = c.nudge_message("v1.66.0", "v1.67.0", "/home/me/doe-starter-kit")
    assert "/home/me/doe-starter-kit/setup.sh --tools-only" in msg
