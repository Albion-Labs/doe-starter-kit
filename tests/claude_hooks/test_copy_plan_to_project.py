"""Tests for .claude/hooks/copy_plan_to_project.py (v1.71.2).

Regression net for the never-alive casing bug: the hook compared tool_name
against lowercase ("write", "edit") while real events carry "Write"/"Edit"/
"MultiEdit", so no plan was ever auto-copied.
"""
import json
import os
import shutil
import subprocess
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
HOOK_SRC = KIT / ".claude" / "hooks" / "copy_plan_to_project.py"


def _fixture(tmp_path):
    """Project fixture with the hook installed (PROJECT_PLANS derives from the
    hook file's own location) and an isolated HOME."""
    proj = tmp_path / "proj"
    (proj / ".claude" / "hooks").mkdir(parents=True)
    shutil.copy2(HOOK_SRC, proj / ".claude" / "hooks" / "copy_plan_to_project.py")
    home = tmp_path / "home"
    (home / ".claude" / "plans").mkdir(parents=True)
    return proj, home


def _run(proj, home, tool_name, path):
    env = os.environ.copy()
    env["HOME"] = str(home)
    payload = {"tool_name": tool_name, "tool_input": {"file_path": str(path)}}
    result = subprocess.run(
        ["python3", str(proj / ".claude" / "hooks" / "copy_plan_to_project.py")],
        input=json.dumps(payload), capture_output=True, text=True, env=env, cwd="/tmp",
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def test_write_of_home_plan_copies_to_project(tmp_path):
    """The path that never worked pre-v1.71.2: a real 'Write' event."""
    proj, home = _fixture(tmp_path)
    plan = home / ".claude" / "plans" / "feature-x.md"
    plan.write_text("# plan")
    out = _run(proj, home, "Write", plan)
    assert (proj / ".claude" / "plans" / "feature-x.md").exists()
    assert "Auto-copied" in out


def test_edit_and_multiedit_also_fire(tmp_path):
    proj, home = _fixture(tmp_path)
    for i, tool in enumerate(("Edit", "MultiEdit")):
        plan = home / ".claude" / "plans" / f"p{i}.md"
        plan.write_text("# plan")
        _run(proj, home, tool, plan)
        assert (proj / ".claude" / "plans" / f"p{i}.md").exists()


def test_non_plan_path_is_silent_noop(tmp_path):
    proj, home = _fixture(tmp_path)
    out = _run(proj, home, "Write", home / "notes.md")
    assert out == ""
    assert not (proj / ".claude" / "plans" / "notes.md").exists()


def test_read_does_not_copy(tmp_path):
    proj, home = _fixture(tmp_path)
    plan = home / ".claude" / "plans" / "feature-y.md"
    plan.write_text("# plan")
    out = _run(proj, home, "Read", plan)
    assert out == ""
    assert not (proj / ".claude" / "plans" / "feature-y.md").exists()
