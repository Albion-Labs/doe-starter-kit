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

KIT = Path(__file__).resolve().parents[2]  # repo root: tests this checkout, not a hardcoded ~/doe-starter-kit (worktree/CI-safe)
HOOK = KIT / ".claude" / "hooks" / "enforce_review_gate.py"

# Runtime-built trigger to keep this file's bytes out of any literal scan.
GH_PR_CREATE = "gh" + " pr" + " create"


def _run(command, cwd=None, env_extra=None):
    env = os.environ.copy()
    env.pop("SKIP_REVIEW_GATE", None)
    env.pop("CLAUDE_PROJECT_DIR", None)
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


# --- Cross-project guard (v1.61.4): inline `cd <other>` exempts ---

def test_cross_project_cd_outside_cwd_allows(tmp_path):
    """gh pr create preceded by `cd <other-dir>` (cross-project work) should
    pass through silently -- the gate's release-readiness checks don't apply
    when the actual repo being PR'd lives elsewhere."""
    inside = tmp_path / "inside"
    outside = tmp_path / "outside"
    inside.mkdir()
    outside.mkdir()
    decision = _run(
        f"cd {outside} && {GH_PR_CREATE} --title foo",
        cwd=inside,
    )
    assert decision["decision"] == "allow"


def test_cross_project_cd_with_tilde_expansion_allows(tmp_path):
    """The cd-detect block expands ~ before comparing paths."""
    inside = tmp_path / "inside"
    inside.mkdir()
    # ~/. expands to home; if that's outside tmp_path/inside it's cross-project
    decision = _run(
        f"cd ~/ && {GH_PR_CREATE} --title foo",
        cwd=inside,
    )
    assert decision["decision"] == "allow"


def test_inline_cd_to_subdir_still_gates(tmp_path):
    """cd to a subdir inside the hook's cwd should NOT exempt -- only
    targets resolving outside the cwd tree are cross-project."""
    repo = _init_repo(tmp_path, "feature/new-thing-v1.0.0")
    subdir = repo / "subdir"
    subdir.mkdir()
    decision = _run(f"cd {subdir} && {GH_PR_CREATE} --title foo", cwd=repo)
    # Subdir is inside repo -> not cross-project -> gate continues. No review
    # artifact present, so the artifact gate fires.
    assert decision["decision"] == "block"


# --- v1.71.1 (issue #107): unborn HEAD, worktrees, statement-position match ---

def _init_unborn_repo(tmp_path, branch):
    """git repo on the named branch with ZERO commits (unborn HEAD).
    `git branch --show-current` succeeds here; `rev-parse HEAD` does not."""
    subprocess.run(["git", "init", "-q", "-b", branch], cwd=tmp_path, check=True)
    return tmp_path


def test_unborn_head_nonfeature_branch_allows(tmp_path):
    """A zero-commit repo on a non-feature branch (e.g. a home-directory DOE
    project) must NOT fail-closed-block PR creation targeting other repos."""
    repo = _init_unborn_repo(tmp_path, "main")
    assert _run(f"{GH_PR_CREATE} --title foo", cwd=repo)["decision"] == "allow"


def test_unborn_head_feature_branch_blocks(tmp_path):
    """feature/* with no commits: review can't be verified against HEAD."""
    repo = _init_unborn_repo(tmp_path, "feature/empty-v0.0.0")
    decision = _run(f"{GH_PR_CREATE} --title foo", cwd=repo)
    assert decision["decision"] == "block"
    assert "no commits" in decision["reason"].lower()


def test_non_git_dir_still_fails_closed(tmp_path):
    """F15 contract: unreadable git state blocks (never silently passes)."""
    plain = tmp_path / "not-a-repo"
    plain.mkdir()
    decision = _run(f"{GH_PR_CREATE} --title foo", cwd=plain)
    assert decision["decision"] == "block"
    assert "git state" in decision["reason"].lower()


def test_worktree_nonfeature_branch_allows(tmp_path):
    """Linked worktree (.git is a file) on a non-feature branch passes."""
    (tmp_path / "main-co").mkdir()
    repo = _init_repo(tmp_path / "main-co", "main")
    wt = tmp_path / "wt"
    subprocess.run(["git", "worktree", "add", "-q", str(wt), "-b", "fix/wt-test"],
                   cwd=repo, check=True)
    assert _run(f"{GH_PR_CREATE} --title foo", cwd=wt)["decision"] == "allow"


def test_worktree_feature_branch_without_artifact_blocks(tmp_path):
    """Worktree on feature/*: gate applies normally (review reason, NOT the
    misleading could-not-determine-git-state block)."""
    (tmp_path / "main-co").mkdir()
    repo = _init_repo(tmp_path / "main-co", "main")
    wt = tmp_path / "wt"
    subprocess.run(["git", "worktree", "add", "-q", str(wt), "-b", "feature/wt-v0.0.0"],
                   cwd=repo, check=True)
    decision = _run(f"{GH_PR_CREATE} --title foo", cwd=wt)
    assert decision["decision"] == "block"
    assert "git state" not in decision["reason"].lower()
    assert "review" in decision["reason"].lower()


def test_phrase_inside_quoted_body_allows(tmp_path):
    """The PHRASE inside quoted text (issue comments, PR bodies, docs) is not
    an invocation and must not engage the gate."""
    repo = _init_repo(tmp_path, "feature/new-thing-v1.0.0")
    cmd = f'gh issue comment 9 --body "before you {GH_PR_CREATE}, run /review"'
    assert _run(cmd, cwd=repo)["decision"] == "allow"


def test_invocation_after_chained_command_still_gates(tmp_path):
    """A statement-position invocation after && is still gated (no under-match)."""
    repo = _init_repo(tmp_path, "feature/new-thing-v1.0.0")
    decision = _run(f"pytest -q && {GH_PR_CREATE} --fill", cwd=repo)
    assert decision["decision"] == "block"


def test_invocation_with_env_prefix_still_gates(tmp_path):
    """VAR=val prefixes don't hide the invocation."""
    repo = _init_repo(tmp_path, "feature/new-thing-v1.0.0")
    decision = _run(f"GH_PAGER=cat {GH_PR_CREATE} --fill", cwd=repo)
    assert decision["decision"] == "block"
