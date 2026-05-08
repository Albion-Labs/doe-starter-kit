"""Tests for .claude/hooks/enforce_review_gate.py (kit v1.61.3).

The hook gates `gh pr create` on feature/* branches: all steps in
tasks/todo.md ## Current must be [x] AND a fresh adversarial-review
artifact must exist. Non-feature branches and non-pr-create commands
take the silent no-opinion path (sys.exit(0)). SKIP_REVIEW_GATE=1
bypasses the whole hook.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

KIT = Path.home() / "doe-starter-kit"
HOOK = KIT / ".claude" / "hooks" / "enforce_review_gate.py"

# Runtime-built trigger to keep this file's bytes out of any literal scan.
GH_PR_CREATE = "gh" + " pr" + " create"


def _run(command, cwd=None, env_extra=None):
    env = os.environ.copy()
    env.pop("SKIP_REVIEW_GATE", None)
    if env_extra:
        env.update(env_extra)
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    result = subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else "/tmp",
        env=env,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout.strip()
    if not out:
        return {"decision": "allow"}
    decoded = json.loads(out)
    assert decoded.get("decision") != "allow", (
        "regression: hook emitted legacy {'decision': 'allow'} JSON. "
        "PreToolUse no-opinion path must use sys.exit(0); 'allow' is not a "
        "valid root-level decision value (only approve/block are accepted)."
    )
    return decoded


def _init_repo(tmp_path, branch):
    """Initialise a tmp git repo on the named branch with one commit."""
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", branch], cwd=tmp_path, check=True)
    (tmp_path / "README.md").write_text("test")
    subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t.test", "-c", "user.name=Test", "commit", "-q", "-m", "init"],
        cwd=tmp_path, check=True,
    )
    return tmp_path


# --- Silent no-opinion: command not gated ---

def test_non_pr_create_command_allows():
    assert _run("ls -la")["decision"] == "allow"


def test_gh_pr_view_allows():
    assert _run("gh pr view 99")["decision"] == "allow"


def test_gh_pr_merge_allows():
    """Only `gh pr create` is gated by THIS hook (merge is a different hook)."""
    assert _run("gh pr merge 99")["decision"] == "allow"


# --- Bypass path ---

def test_skip_review_gate_bypass_allows():
    assert _run(
        f"{GH_PR_CREATE} --title foo",
        env_extra={"SKIP_REVIEW_GATE": "1"},
    )["decision"] == "allow"


# --- Branch-scoped: non-feature branches pass through ---

def test_main_branch_pr_create_allows(tmp_path):
    repo = _init_repo(tmp_path, "main")
    assert _run(f"{GH_PR_CREATE} --title foo", cwd=repo)["decision"] == "allow"


def test_housekeeping_branch_pr_create_allows(tmp_path):
    repo = _init_repo(tmp_path, "housekeeping/cleanup")
    assert _run(f"{GH_PR_CREATE} --title foo", cwd=repo)["decision"] == "allow"


def test_fix_branch_pr_create_allows(tmp_path):
    """fix/* branches (e.g. patch releases) are not gated -- only feature/*."""
    repo = _init_repo(tmp_path, "fix/v1.0.1-typo")
    assert _run(f"{GH_PR_CREATE} --title foo", cwd=repo)["decision"] == "allow"


# --- Branch-scoped: feature branches without artifact block ---

def test_feature_branch_without_review_artifact_blocks(tmp_path):
    repo = _init_repo(tmp_path, "feature/new-thing-v1.0.0")
    decision = _run(f"{GH_PR_CREATE} --title foo", cwd=repo)
    assert decision["decision"] == "block"
    assert "review" in decision["reason"].lower() or "step" in decision["reason"].lower()


def test_feature_branch_with_incomplete_steps_blocks(tmp_path):
    repo = _init_repo(tmp_path, "feature/new-thing-v1.0.0")
    todo = repo / "tasks"
    todo.mkdir()
    (todo / "todo.md").write_text(
        "## Current\n\n"
        "1. [x] Done step\n"
        "2. [ ] Incomplete step\n"
    )
    decision = _run(f"{GH_PR_CREATE} --title foo", cwd=repo)
    assert decision["decision"] == "block"
    # Steps gate fires before review-artifact gate, so reason mentions steps.
    assert "step" in decision["reason"].lower()
