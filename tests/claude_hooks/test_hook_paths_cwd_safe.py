"""Regression test for internal relative paths in hook scripts (kit v1.63.0).

Companion to test_settings_paths_cwd_safe.py (v1.62.2):
- v1.62.2 fixed the INVOCATION path: `python3 $CLAUDE_PROJECT_DIR/.claude/hooks/X.py`
  in settings.json so the hook script is always findable regardless of shell cwd.
- v1.63.0 fixes INTERNAL paths inside hook scripts: `Path("tasks/todo.md")`,
  `Path(".tmp")/...` previously resolved against the subprocess cwd (= shell
  cwd at fire time), which silently false-passed when the agent shell drifted
  to a subdir. The failure mode was the dangerous class: check_steps_complete
  returns (True, "") when the file isn't found, so the PR gate goes quiet
  exactly when it should block.

Anchor: $CLAUDE_PROJECT_DIR. When the env var is unset the hooks fall back to
cwd (so existing tests that did not set it continue to pass), but when it IS
set the env var wins regardless of cwd.

Tests below construct a fake project tree under $CLAUDE_PROJECT_DIR, chdir to
a foreign cwd, and assert the hook still finds the project files.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

# Resolve the kit root from this test file's location so the test runs
# against the LOCAL checkout (worktree or main) -- pre-merge worktree
# verification is the primary use case for this test. Other kit tests use a
# hardcoded Path.home()/"doe-starter-kit" because they pre-date the
# worktree convention; this test is born after it.
KIT = Path(__file__).resolve().parents[2]
CHECK_HOOK = KIT / ".claude" / "hooks" / "check_completed_feature.py"
REVIEW_HOOK = KIT / ".claude" / "hooks" / "enforce_review_gate.py"

GH_PR_CREATE = "gh" + " pr" + " create"


def _make_fake_project(root: Path, todo_body: str) -> Path:
    """Initialise a tmp git repo with a tasks/todo.md and one commit."""
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "checkout", "-q", "-b", "feature/test-branch"], cwd=root, check=True)
    (root / "tasks").mkdir()
    (root / "tasks" / "todo.md").write_text(todo_body)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)
    subprocess.run(
        ["git", "-c", "user.email=t@t.test", "-c", "user.name=Test", "commit", "-q", "-m", "init"],
        cwd=root, check=True,
    )
    return root


def _run_review_hook(command, project_dir, cwd, env_extra=None):
    """Invoke enforce_review_gate.py with the given Bash command + cwd + env."""
    env = os.environ.copy()
    env.pop("SKIP_REVIEW_GATE", None)
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    if env_extra:
        env.update(env_extra)
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    result = subprocess.run(
        ["python3", str(REVIEW_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout.strip()
    if not out:
        return {"decision": "allow"}
    return json.loads(out)


def _run_check_hook(file_path, project_dir, cwd):
    """Invoke check_completed_feature.py with a fake Edit payload."""
    env = os.environ.copy()
    env["CLAUDE_PROJECT_DIR"] = str(project_dir)
    payload = {
        "tool_name": "Edit",
        "tool_input": {"file_path": file_path},
    }
    result = subprocess.run(
        ["python3", str(CHECK_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd),
        env=env,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    return result.stderr  # warnings emit to stderr


# --- enforce_review_gate: tasks/todo.md path resolution ---

def test_enforce_review_gate_finds_todo_under_project_dir_from_foreign_cwd(tmp_path):
    """check_steps_complete must find tasks/todo.md under $CLAUDE_PROJECT_DIR
    even when the subprocess cwd is unrelated. This is the false-pass class
    the v1.63.0 fix targets: pre-fix, Path("tasks/todo.md") looked under cwd
    and returned (True, "") on missing file -- silently passing the gate.
    """
    project = tmp_path / "project"
    project.mkdir()
    todo = (
        "## Current\n\n"
        "### Test feature\n\n"
        "1. [ ] First step\n"  # uncompleted -- gate must block
    )
    _make_fake_project(project, todo)

    # Run hook with cwd=/tmp (foreign). Pre-fix: hook would not find todo.md
    # because Path("tasks/todo.md") resolved to /tmp/tasks/todo.md. Returns
    # (True, "") -> gate passes -> PR creation allowed. Post-fix: hook anchors
    # to $CLAUDE_PROJECT_DIR, finds the file, sees uncompleted step, blocks.
    decision = _run_review_hook(GH_PR_CREATE, project_dir=project, cwd="/tmp")
    assert decision.get("decision") == "block", (
        "Hook should have found tasks/todo.md under $CLAUDE_PROJECT_DIR and "
        "blocked because step 1 is incomplete. Pre-v1.63.0 fix this returned "
        "allow because Path('tasks/todo.md') resolved against the foreign cwd."
    )
    assert "1/" in decision.get("reason", "") or "0/" in decision.get("reason", "")


def test_enforce_review_gate_passes_when_all_steps_complete_from_foreign_cwd(tmp_path):
    """Symmetric to the previous test: when all steps are [x], the gate should
    NOT block on Gate 1 (steps). It will still block on Gate 2 (missing review
    artifact) -- that's the next test's concern.
    """
    project = tmp_path / "project"
    project.mkdir()
    todo = (
        "## Current\n\n"
        "### Test feature\n\n"
        "1. [x] Done step\n"
    )
    _make_fake_project(project, todo)

    decision = _run_review_hook(GH_PR_CREATE, project_dir=project, cwd="/tmp")
    # All steps complete, so Gate 1 passes; Gate 2 (review artifact) blocks.
    assert decision.get("decision") == "block"
    assert "review" in decision.get("reason", "").lower()


# --- enforce_review_gate: .tmp/review-passed-<branch>.json path resolution ---

def test_enforce_review_gate_finds_review_artifact_under_project_dir(tmp_path):
    """The review-passed artifact must be looked up under $CLAUDE_PROJECT_DIR/.tmp
    not cwd/.tmp. Pre-v1.63.0 fix, a valid review artifact in the project's
    .tmp/ would be invisible to the hook after the agent shell drifted, and
    the gate would block with a misleading 'review required' error.
    """
    project = tmp_path / "project"
    project.mkdir()
    todo = (
        "## Current\n\n"
        "### Test feature\n\n"
        "1. [x] Done step\n"
    )
    _make_fake_project(project, todo)

    # Get HEAD sha to write a fresh artifact
    head_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=project, text=True
    ).strip()

    artifact_dir = project / ".tmp"
    artifact_dir.mkdir()
    artifact = artifact_dir / "review-passed-feature/test-branch.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps({"reviewed_sha": head_sha}))

    decision = _run_review_hook(GH_PR_CREATE, project_dir=project, cwd="/tmp")
    assert decision.get("decision") == "allow", (
        f"Hook should have found the review artifact under $CLAUDE_PROJECT_DIR/.tmp "
        f"and allowed the PR creation. Got: {decision}"
    )


# --- check_completed_feature: tasks/todo.md path resolution ---

def test_check_completed_feature_finds_todo_under_project_dir_from_foreign_cwd(tmp_path):
    """When a feature is fully complete in ## Current, the hook must warn --
    even when the subprocess cwd is unrelated to the project. Pre-fix,
    Path("tasks/todo.md") resolved against cwd and the warning silently
    disappeared.
    """
    project = tmp_path / "project"
    project.mkdir()
    todo = (
        "## Current\n\n"
        "### Test feature\n\n"
        "1. [x] Done step one\n"
        "2. [x] Done step two\n"
        "\n"
        "## Done\n"
    )
    _make_fake_project(project, todo)

    # Pass an Edit tool payload pointing at todo.md; subprocess cwd is /tmp.
    fake_todo_path = str(project / "tasks" / "todo.md")
    stderr = _run_check_hook(fake_todo_path, project_dir=project, cwd="/tmp")
    assert "Feature complete" in stderr, (
        f"Hook should have emitted the completion warning to stderr. "
        f"Got stderr: {stderr!r}"
    )
    assert "Test feature" in stderr


def test_check_completed_feature_silent_when_feature_incomplete(tmp_path):
    """Negative case: when steps are incomplete, the hook should NOT emit a
    warning. Verifies the path resolution change doesn't cause spurious
    warnings.
    """
    project = tmp_path / "project"
    project.mkdir()
    todo = (
        "## Current\n\n"
        "### Test feature\n\n"
        "1. [x] Done step\n"
        "2. [ ] Pending step\n"
    )
    _make_fake_project(project, todo)

    fake_todo_path = str(project / "tasks" / "todo.md")
    stderr = _run_check_hook(fake_todo_path, project_dir=project, cwd="/tmp")
    assert "Feature complete" not in stderr, (
        f"Hook should have stayed silent (feature incomplete). Got: {stderr!r}"
    )


# --- Static guard: hook source code has no bare relative paths ---

def test_check_completed_feature_uses_claude_project_dir():
    """Static check: the source code of check_completed_feature.py references
    CLAUDE_PROJECT_DIR for its path anchor. Future edits that drop this
    reference will trip this test before they ship.
    """
    src = CHECK_HOOK.read_text()
    assert "CLAUDE_PROJECT_DIR" in src, (
        "check_completed_feature.py must reference CLAUDE_PROJECT_DIR for "
        "cwd-safe path resolution. Pre-v1.63.0 the hook used a bare "
        "Path('tasks/todo.md') and silently no-op'd under shell drift."
    )


def test_enforce_review_gate_anchors_paths_to_resolved_root():
    """Static check: enforce_review_gate.py anchors tasks/todo.md and the
    .tmp review artifact to the resolved project root, never bare cwd.
    v1.71.4 replaced the _project_root() helper with
    _resolve_root_and_branch() (CLAUDE_PROJECT_DIR first, event cwd
    fallback); both consumers must route through its returned root.
    """
    src = REVIEW_HOOK.read_text()
    assert "CLAUDE_PROJECT_DIR" in src, (
        "enforce_review_gate.py must reference CLAUDE_PROJECT_DIR"
    )
    assert "_resolve_root_and_branch(event)" in src, (
        "git state must come from the shared resolver"
    )
    assert "check_steps_complete(root)" in src, (
        "tasks/todo.md must be read from the resolved root, not cwd"
    )
    assert 'root / ".tmp"' in src, (
        "the review artifact must be read from the resolved root, not cwd"
    )
    assert 'Path(".tmp")' not in src and 'Path("tasks")' not in src, (
        "no cwd-relative paths allowed in the gate"
    )
