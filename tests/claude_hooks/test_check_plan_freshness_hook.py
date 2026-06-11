"""Tests for .claude/hooks/check_plan_freshness_hook.py (v1.71.2).

The hook fires on Read of .claude/plans/*.md, anchors the freshness
subprocess to $CLAUDE_PROJECT_DIR (script path AND cwd), and surfaces the
checker's stdout when it exits non-zero. Regression net for the never-alive
casing bug (compared against lowercase "read") and the unanchored-subprocess
bug (relative script path, no cwd=).
"""
import json
import os
import subprocess
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
HOOK = KIT / ".claude" / "hooks" / "check_plan_freshness_hook.py"

STUB_STALE = "import sys\nprint('PLAN STALE: fixture says so')\nsys.exit(1)\n"
STUB_FRESH = "import sys\nsys.exit(0)\n"


def _project(tmp_path, checker_body=STUB_STALE, with_plan=True):
    """Fixture project: .claude/plans/p.md + a stub execution/check_plan_freshness.py."""
    (tmp_path / ".claude" / "plans").mkdir(parents=True)
    (tmp_path / "execution").mkdir()
    if with_plan:
        (tmp_path / ".claude" / "plans" / "p.md").write_text("# plan")
    if checker_body is not None:
        (tmp_path / "execution" / "check_plan_freshness.py").write_text(checker_body)
    return tmp_path


def _run(tool_name, path, project_root, cwd=None):
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_root)
    payload = {"tool_name": tool_name, "tool_input": {"file_path": path}}
    result = subprocess.run(
        ["python3", str(HOOK)], input=json.dumps(payload),
        capture_output=True, text=True, env=env,
        cwd=str(cwd) if cwd else "/tmp",
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_read_of_stale_plan_surfaces_warning(tmp_path):
    """The core path that never worked pre-v1.71.2: a real 'Read' event."""
    root = _project(tmp_path)
    out = _run("Read", str(root / ".claude" / "plans" / "p.md"), root)
    assert "PLAN STALE" in out


def test_fresh_plan_is_silent(tmp_path):
    root = _project(tmp_path, checker_body=STUB_FRESH)
    assert _run("Read", str(root / ".claude" / "plans" / "p.md"), root) == ""


def test_non_read_tool_is_silent(tmp_path):
    root = _project(tmp_path)
    assert _run("Write", str(root / ".claude" / "plans" / "p.md"), root) == ""


def test_non_plan_path_is_silent(tmp_path):
    root = _project(tmp_path)
    assert _run("Read", str(root / "README.md"), root) == ""


def test_relative_plan_path_resolves_against_project_root(tmp_path):
    """Relative paths must anchor to $CLAUDE_PROJECT_DIR, not the shell cwd
    (hook runs with cwd=/tmp here -- pre-fix this silently no-opped)."""
    root = _project(tmp_path)
    out = _run("Read", ".claude/plans/p.md", root, cwd="/tmp")
    assert "PLAN STALE" in out


def test_missing_checker_script_is_silent(tmp_path):
    """Projects without the freshness script (or drifted cwd pre-fix) must
    not error or emit noise."""
    root = _project(tmp_path, checker_body=None)
    assert _run("Read", str(root / ".claude" / "plans" / "p.md"), root) == ""


def test_no_legacy_empty_json_emitted(tmp_path):
    """v1.61.3 convention: no-opinion is silent exit 0, never '{}'."""
    root = _project(tmp_path)
    out = _run("Write", str(root / ".claude" / "plans" / "p.md"), root)
    assert out != "{}"
