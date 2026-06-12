"""No-opinion output convention for global-hooks/ (liveness audit C7).

The kit convention for a hook with nothing to say is SILENT sys.exit(0) —
no stdout at all. heartbeat.py and context_monitor.py carried the legacy
`print(json.dumps({}))` form, which emits a bare `{}` to stdout on every
tool call. `{}` is not a recognised hook response and is noise at best;
the convention is enforced here for every remaining global hook.

Hermetic: runs each hook in a tmp dir with a .git marker so
doe_utils.resolve_project_root anchors there; PYTHONPATH points at the
kit's own global-scripts/ so the doe_utils import works on machines (and
CI) without an installed ~/.claude/scripts/.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[2]  # repo root: tests this checkout, not a hardcoded ~/doe-starter-kit (worktree/CI-safe)
GLOBAL_HOOKS = KIT / "global-hooks"
GLOBAL_SCRIPTS = KIT / "global-scripts"


def _run(hook_name, cwd, payload=None):
    env = os.environ.copy()
    # doe_utils fallback for environments without ~/.claude/scripts (CI)
    env["PYTHONPATH"] = str(GLOBAL_SCRIPTS)
    result = subprocess.run(
        ["python3", str(GLOBAL_HOOKS / hook_name)],
        input=json.dumps(payload if payload is not None else {"tool_input": {}}),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
    )
    return result


@pytest.fixture
def project_dir(tmp_path):
    (tmp_path / ".git").mkdir()  # resolve_project_root anchors on .git
    return tmp_path


def test_heartbeat_no_wave_is_silent(project_dir):
    """No active wave -> nothing to say -> empty stdout, exit 0."""
    result = _run("heartbeat.py", project_dir)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", (
        f"legacy no-opinion output on stdout: {result.stdout!r}"
    )


def test_context_monitor_below_threshold_is_silent(project_dir):
    """Below the 60% warn threshold -> nothing to say -> empty stdout."""
    result = _run(
        "context_monitor.py",
        project_dir,
        payload={"tool_input": {"file_path": "x.md"}, "tool_response": "ok"},
    )
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "", (
        f"legacy no-opinion output on stdout: {result.stdout!r}"
    )
