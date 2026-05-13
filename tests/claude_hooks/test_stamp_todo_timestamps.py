"""Tests for .claude/hooks/stamp_todo_timestamps.py (kit v1.64.0).

Covers the PostToolUse JSON-on-stdin path, the --pre-commit CLI path, and
the pure process() function. The hook must stamp [x] step lines that lack
a timestamp, leave already-stamped lines alone (idempotent), and ignore
contract criteria (dash-prefixed -- not numbered).
"""
import importlib.util
import json
import os
import subprocess
from datetime import datetime
from pathlib import Path

import pytest

KIT = Path.home() / "doe-starter-kit"
HOOK = KIT / ".claude" / "hooks" / "stamp_todo_timestamps.py"


def _load_hook_module():
    """Import the hook script as a module so we can test process() directly."""
    spec = importlib.util.spec_from_file_location("stamp_todo_timestamps", HOOK)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _run_hook(payload, env=None):
    """Invoke the hook via subprocess with a JSON event on stdin."""
    base_env = os.environ.copy()
    if env:
        base_env.update(env)
    result = subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd="/tmp",
        env=base_env,
    )
    assert result.returncode == 0, result.stderr
    return result


# ─── Pure process() tests (regex behaviour, idempotence) ──────────────────

def test_process_stamps_numbered_step():
    mod = _load_hook_module()
    now = datetime(2026, 5, 13, 14, 30)
    text = "1. [x] First step → v0.1.0"
    out, n = mod.process(text, now)
    assert n == 1
    assert out == "1. [x] First step → v0.1.0 *(completed 14:30 13/05/26)*"


def test_process_idempotent_on_stamped_line():
    mod = _load_hook_module()
    now = datetime(2026, 5, 13, 14, 30)
    text = "1. [x] First step → v0.1.0 *(completed 09:15 12/05/26)*"
    out, n = mod.process(text, now)
    assert n == 0
    assert out == text


def test_process_idempotent_date_only_stamp():
    """Older stamps may be date-only (HH:MM omitted). Don't double-stamp."""
    mod = _load_hook_module()
    now = datetime(2026, 5, 13, 14, 30)
    text = "1. [x] First step *(completed 12/05/26)*"
    out, n = mod.process(text, now)
    assert n == 0


def test_process_skips_contract_criteria():
    """Dash-prefixed lines (- [x] [auto] foo) are contract criteria, not steps."""
    mod = _load_hook_module()
    now = datetime(2026, 5, 13, 14, 30)
    text = "  - [x] [auto] Verify build passes"
    out, n = mod.process(text, now)
    assert n == 0
    assert out == text


def test_process_skips_unchecked():
    mod = _load_hook_module()
    now = datetime(2026, 5, 13, 14, 30)
    text = "1. [ ] Not done yet"
    out, n = mod.process(text, now)
    assert n == 0


def test_process_stamps_indented_unnumbered():
    """Audit regex matches `  [x] foo` (indented, no number). Mirror it."""
    mod = _load_hook_module()
    now = datetime(2026, 5, 13, 14, 30)
    text = "  [x] Bare bullet step"
    out, n = mod.process(text, now)
    assert n == 1
    assert "*(completed 14:30 13/05/26)*" in out


def test_process_stamps_retro_step():
    """Retro is exempt from VERSION tag, NOT from timestamp."""
    mod = _load_hook_module()
    now = datetime(2026, 5, 13, 14, 30)
    text = "5. [x] Retro [quick: logged to learnings.md]"
    out, n = mod.process(text, now)
    assert n == 1


def test_process_handles_multiple_lines():
    mod = _load_hook_module()
    now = datetime(2026, 5, 13, 14, 30)
    text = "\n".join([
        "1. [x] First → v0.1.0 *(completed 09:00 12/05/26)*",
        "2. [x] Second → v0.1.1",
        "3. [ ] Third",
        "  - [x] [auto] contract item",
    ])
    out, n = mod.process(text, now)
    assert n == 1, "only line 2 should get stamped"
    lines = out.split("\n")
    assert "*(completed 14:30 13/05/26)*" in lines[1]
    assert lines[0].endswith("*(completed 09:00 12/05/26)*"), "line 1 untouched"
    assert lines[2] == "3. [ ] Third"
    assert lines[3] == "  - [x] [auto] contract item"


def test_process_preserves_trailing_text_intact():
    """rstrip then append -- trailing spaces lost, content preserved."""
    mod = _load_hook_module()
    now = datetime(2026, 5, 13, 14, 30)
    text = "1. [x] Step name → v1.2.3   "
    out, n = mod.process(text, now)
    assert n == 1
    assert out == "1. [x] Step name → v1.2.3 *(completed 14:30 13/05/26)*"


# ─── PostToolUse subprocess tests (JSON-on-stdin path) ────────────────────

def test_posttooluse_stamps_real_file(tmp_path):
    todo = tmp_path / "tasks" / "todo.md"
    todo.parent.mkdir()
    todo.write_text("1. [x] Build feature → v0.1.0\n")

    _run_hook(
        {"tool_name": "Edit", "tool_input": {"file_path": str(todo)}},
        env={"CLAUDE_PROJECT_DIR": str(tmp_path)},
    )

    out = todo.read_text()
    assert "*(completed " in out
    assert "v0.1.0" in out


def test_posttooluse_idempotent_repeated_fire(tmp_path):
    """Hook can fire many times per session; stamping must converge."""
    todo = tmp_path / "tasks" / "todo.md"
    todo.parent.mkdir()
    todo.write_text("1. [x] Build feature → v0.1.0\n")

    for _ in range(3):
        _run_hook(
            {"tool_name": "Edit", "tool_input": {"file_path": str(todo)}},
            env={"CLAUDE_PROJECT_DIR": str(tmp_path)},
        )

    out = todo.read_text()
    # Exactly one timestamp, not three.
    assert out.count("*(completed ") == 1


def test_posttooluse_ignores_non_todo_files(tmp_path):
    other = tmp_path / "STATE.md"
    other.write_text("1. [x] Build feature → v0.1.0\n")

    _run_hook(
        {"tool_name": "Edit", "tool_input": {"file_path": str(other)}},
        env={"CLAUDE_PROJECT_DIR": str(tmp_path)},
    )

    assert "*(completed " not in other.read_text()


def test_posttooluse_silent_on_bad_json():
    """Bad JSON in must not crash the hook (PostToolUse never blocks)."""
    result = subprocess.run(
        ["python3", str(HOOK)],
        input="this is not json",
        capture_output=True,
        text=True,
        cwd="/tmp",
    )
    assert result.returncode == 0


def test_posttooluse_resolves_via_claude_project_dir(tmp_path):
    """Path in event may be stale; CLAUDE_PROJECT_DIR is the source of truth."""
    real_todo = tmp_path / "tasks" / "todo.md"
    real_todo.parent.mkdir()
    real_todo.write_text("1. [x] Resolved via env var\n")

    _run_hook(
        {
            "tool_name": "Edit",
            "tool_input": {"file_path": "/nonexistent/tasks/todo.md"},
        },
        env={"CLAUDE_PROJECT_DIR": str(tmp_path)},
    )

    assert "*(completed " in real_todo.read_text()


# ─── Pre-commit CLI path (--pre-commit FILE) ──────────────────────────────

def test_pre_commit_mode_stamps_file(tmp_path):
    todo = tmp_path / "todo.md"
    todo.write_text("1. [x] direct edit no Claude\n")

    result = subprocess.run(
        ["python3", str(HOOK), "--pre-commit", str(todo)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0

    out = todo.read_text()
    assert "*(completed " in out


def test_pre_commit_mode_idempotent(tmp_path):
    todo = tmp_path / "todo.md"
    todo.write_text("1. [x] step → v0.1.0 *(completed 09:00 01/01/26)*\n")

    subprocess.run(
        ["python3", str(HOOK), "--pre-commit", str(todo)],
        capture_output=True, text=True, check=True,
    )

    assert todo.read_text().count("*(completed ") == 1


def test_pre_commit_mode_missing_file_is_silent(tmp_path):
    """Pre-commit may pass a path that no longer exists (race). No crash."""
    result = subprocess.run(
        ["python3", str(HOOK), "--pre-commit", str(tmp_path / "missing.md")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
