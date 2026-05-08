"""Tests for execution/wrap_stats.py."""

import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "execution"))

import wrap_stats
from wrap_stats import (
    compute_streak,
    compute_session_duration,
    load_stats,
    fresh_stats,
    migrate_v1_to_v2,
    auto_classify_tag,
    count_steps_completed_since,
)


# ── Git stat parsing: gather_git_metrics ─────────────────────

def test_gather_git_metrics_returns_expected_keys():
    """gather_git_metrics must return all expected keys even if git is unavailable."""
    # Pass a non-existent hash so we get zeros — the function must not crash
    metrics = wrap_stats.gather_git_metrics("HEAD")
    assert isinstance(metrics, dict)
    for key in ("commits", "linesAdded", "linesRemoved", "filesTouched", "commitLog"):
        assert key in metrics, f"Missing key: {key}"


# ── Streak calculation ────────────────────────────────────────

def test_compute_streak_first_session():
    """First-ever session (no lastSessionDate) should return streak of 1."""
    stats = fresh_stats()
    streak = compute_streak(stats, "2026-04-23")
    assert streak == 1


def test_compute_streak_consecutive_day():
    """Session on the day after last session should increment streak."""
    stats = fresh_stats()
    stats["streak"]["current"] = 5
    stats["streak"]["lastSessionDate"] = "2026-04-22"

    streak = compute_streak(stats, "2026-04-23")
    assert streak == 6


def test_compute_streak_same_day():
    """Session on same day as last session should keep streak unchanged."""
    stats = fresh_stats()
    stats["streak"]["current"] = 3
    stats["streak"]["lastSessionDate"] = "2026-04-23"

    streak = compute_streak(stats, "2026-04-23")
    assert streak == 3


def test_compute_streak_broken():
    """Session more than 1 day after last session should reset streak to 1."""
    stats = fresh_stats()
    stats["streak"]["current"] = 10
    stats["streak"]["lastSessionDate"] = "2000-01-01"  # long ago

    streak = compute_streak(stats, "2026-04-23")
    assert streak == 1


# ── Corrupt JSON recovery ─────────────────────────────────────

def test_load_stats_missing_file(tmp_path):
    """load_stats must return fresh stats when file is absent."""
    stats = load_stats(tmp_path / "nonexistent.json")
    expected = fresh_stats()
    assert stats["version"] == expected["version"]
    assert stats["lifetime"]["totalSessions"] == 0


def test_load_stats_corrupt_json(tmp_path):
    """load_stats must recover from corrupt JSON and return fresh stats."""
    bad = tmp_path / "stats.json"
    bad.write_text("{corrupt json", encoding="utf-8")

    stats = load_stats(bad)
    expected = fresh_stats()
    assert stats["version"] == expected["version"]
    assert stats["lifetime"]["totalSessions"] == 0


def test_load_stats_v1_migrated(tmp_path):
    """load_stats must migrate v1 stats to v2 schema."""
    v1_stats = {
        "version": 1,
        "lifetime": {"totalSessions": 5, "totalCommits": 20,
                     "totalLinesAdded": 100, "totalLinesRemoved": 50,
                     "firstSessionDate": "2024-01-01"},
        "streak": {"current": 3, "best": 3, "lastSessionDate": "2024-01-10"},
        "highScores": [{"date": "2024-01-05", "score": 99}],
        "badges": ["first-session"],
        "recentSessions": [],
    }
    path = tmp_path / "stats.json"
    path.write_text(json.dumps(v1_stats), encoding="utf-8")

    stats = load_stats(path)
    assert stats["version"] == 2
    assert "highScores" not in stats
    assert "badges" not in stats
    assert stats["lifetime"]["totalSessions"] == 5


# ── Auto-classification ───────────────────────────────────────

def test_auto_classify_build_tag():
    """Session with completed steps must classify as BUILD."""
    metrics = {"commits": 3, "linesAdded": 50, "linesRemoved": 10,
               "filesTouched": 5, "commitLog": []}
    tag = auto_classify_tag(metrics, steps=2)
    assert tag == "BUILD"


def test_auto_classify_research_tag():
    """Session with zero commits must classify as RESEARCH."""
    metrics = {"commits": 0, "linesAdded": 0, "linesRemoved": 0,
               "filesTouched": 0, "commitLog": []}
    tag = auto_classify_tag(metrics, steps=0)
    assert tag == "RESEARCH"


def test_auto_classify_debug_tag():
    """Session with 'fix' in commit message must classify as DEBUG."""
    metrics = {"commits": 1, "linesAdded": 5, "linesRemoved": 2,
               "filesTouched": 1,
               "commitLog": [{"time": "2024-01-01T00:00:00Z", "message": "fix broken login"}]}
    tag = auto_classify_tag(metrics, steps=0)
    assert tag == "DEBUG"


# ── Session duration ──────────────────────────────────────────

def test_compute_session_duration_zero_for_future():
    """Duration must not be negative (returns 0m if start is in the future)."""
    from datetime import datetime, timezone, timedelta
    future = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    result = compute_session_duration(future)
    # Should be "0m" since we clamp with max(0, ...)
    assert result == "0m"


def test_compute_session_duration_format():
    """Duration must be formatted as 'Xh Ym' or 'Ym'."""
    import re
    from datetime import datetime, timezone, timedelta
    past = (datetime.now(timezone.utc) - timedelta(minutes=75)).isoformat()
    result = compute_session_duration(past)
    assert re.match(r"1h \d+m", result), f"Expected '1h Nm' format, got: {result}"


# ── count_steps_completed_since ───────────────────────────────

def test_count_steps_completed_since_empty(tmp_path):
    """Returns 0 for a todo.md with no completed steps."""
    todo = tmp_path / "todo.md"
    todo.write_text("## Current\n\n1. [ ] pending\n", encoding="utf-8")
    count = count_steps_completed_since(todo, "2000-01-01T00:00:00")
    assert count == 0


def test_count_steps_completed_since_missing_file(tmp_path):
    """Returns 0 when todo.md does not exist."""
    count = count_steps_completed_since(tmp_path / "nonexistent.md", "2000-01-01T00:00:00")
    assert count == 0


# ── _merge_main_streak (regression: first-session null lastSessionDate) ──

class _FakeGitShowResult:
    """Mimics subprocess.run() result for `git show origin/main:<path>`."""

    def __init__(self, returncode=0, stdout="{}"):
        self.returncode = returncode
        self.stdout = stdout


def _stats_path_inside_kit() -> Path:
    """`_merge_main_streak` requires stats_path to live inside PROJECT_ROOT."""
    return wrap_stats.PROJECT_ROOT / ".claude" / "stats.json"


def test_merge_main_streak_handles_null_local_and_null_main(monkeypatch):
    """First-ever wrap regression: both local and origin/main stats.json have
    lastSessionDate=null. Comparison must not raise TypeError."""
    main_payload = {"streak": {"current": 0, "best": 0, "lastSessionDate": None}}
    fake = _FakeGitShowResult(returncode=0, stdout=json.dumps(main_payload))
    monkeypatch.setattr(wrap_stats.subprocess, "run", lambda *a, **kw: fake)

    data = {"streak": {"current": 0, "best": 0, "lastSessionDate": None}}
    result = wrap_stats._merge_main_streak(data, _stats_path_inside_kit())

    # No TypeError; nothing copied (main_last is empty after coercion)
    assert result is data
    assert result["streak"]["lastSessionDate"] is None


def test_merge_main_streak_copies_when_main_is_newer(monkeypatch):
    """When origin/main has a more recent lastSessionDate, it should be copied."""
    main_payload = {"streak": {"current": 7, "best": 7, "lastSessionDate": "2026-05-09"}}
    fake = _FakeGitShowResult(returncode=0, stdout=json.dumps(main_payload))
    monkeypatch.setattr(wrap_stats.subprocess, "run", lambda *a, **kw: fake)

    data = {"streak": {"current": 3, "best": 3, "lastSessionDate": "2026-05-08"}}
    result = wrap_stats._merge_main_streak(data, _stats_path_inside_kit())

    assert result["streak"]["lastSessionDate"] == "2026-05-09"
    assert result["streak"]["current"] == 7


def test_merge_main_streak_does_not_copy_when_local_is_newer(monkeypatch):
    """When local has a more recent lastSessionDate, do not copy main's older streak."""
    main_payload = {"streak": {"current": 1, "best": 1, "lastSessionDate": "2026-05-01"}}
    fake = _FakeGitShowResult(returncode=0, stdout=json.dumps(main_payload))
    monkeypatch.setattr(wrap_stats.subprocess, "run", lambda *a, **kw: fake)

    data = {"streak": {"current": 5, "best": 5, "lastSessionDate": "2026-05-08"}}
    result = wrap_stats._merge_main_streak(data, _stats_path_inside_kit())

    # Local stays — origin's older streak does not overwrite
    assert result["streak"]["lastSessionDate"] == "2026-05-08"
    assert result["streak"]["current"] == 5


def test_merge_main_streak_handles_null_main_with_dated_local(monkeypatch):
    """If main has null but local has a date, do not copy (main_last is empty)."""
    main_payload = {"streak": {"current": 0, "best": 0, "lastSessionDate": None}}
    fake = _FakeGitShowResult(returncode=0, stdout=json.dumps(main_payload))
    monkeypatch.setattr(wrap_stats.subprocess, "run", lambda *a, **kw: fake)

    data = {"streak": {"current": 4, "best": 4, "lastSessionDate": "2026-05-08"}}
    result = wrap_stats._merge_main_streak(data, _stats_path_inside_kit())

    assert result["streak"]["lastSessionDate"] == "2026-05-08"
    assert result["streak"]["current"] == 4


def test_merge_main_streak_returns_data_unchanged_on_git_failure(monkeypatch):
    """If `git show origin/main:<path>` fails (e.g., no remote), return data as-is."""
    fake = _FakeGitShowResult(returncode=128, stdout="")
    monkeypatch.setattr(wrap_stats.subprocess, "run", lambda *a, **kw: fake)

    data = {"streak": {"current": 4, "best": 4, "lastSessionDate": "2026-05-08"}}
    result = wrap_stats._merge_main_streak(data, _stats_path_inside_kit())

    assert result is data
    assert result["streak"]["lastSessionDate"] == "2026-05-08"


def test_merge_main_streak_handles_malformed_json(monkeypatch):
    """If origin/main's stats.json is malformed, swallow the error and return data."""
    fake = _FakeGitShowResult(returncode=0, stdout="{not json")
    monkeypatch.setattr(wrap_stats.subprocess, "run", lambda *a, **kw: fake)

    data = {"streak": {"current": 4, "best": 4, "lastSessionDate": "2026-05-08"}}
    result = wrap_stats._merge_main_streak(data, _stats_path_inside_kit())

    assert result is data
    assert result["streak"]["lastSessionDate"] == "2026-05-08"
