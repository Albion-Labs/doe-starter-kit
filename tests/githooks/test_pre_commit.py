"""Tests for .githooks/pre-commit main-branch protection.

Covers the v1.56.0 first-commit-on-main exception: the initial commit on
a fresh repo (no HEAD yet) must be allowed through; every commit after
that is still blocked.
"""

import os
import subprocess
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_PATH = KIT_ROOT / ".githooks" / "pre-commit"


def _make_env() -> dict:
    """Env with all downstream hook stages skipped and git identity set."""
    return {
        **os.environ,
        "SKIP_ESLINT": "1",
        "SKIP_XSS_CHECK": "1",
        "SKIP_SIGNOFF_CHECK": "1",
        "SKIP_TODO_LINT": "1",
        "SKIP_QUALITY_GATE": "1",
        "SKIP_RETRO_GATE": "1",
        "SKIP_PENDING_PR_CHECK": "1",
        "SKIP_CONTRACT_CHECK": "1",
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }


def _init_repo(tmpdir: Path) -> None:
    """Init a fresh repo on main, install the real pre-commit hook, stub audit_claims."""
    subprocess.run(["git", "init", str(tmpdir)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(tmpdir), "symbolic-ref", "HEAD", "refs/heads/main"],
        check=True, capture_output=True,
    )

    hooks_dir = tmpdir / ".githooks"
    hooks_dir.mkdir()
    hook_dest = hooks_dir / "pre-commit"
    hook_dest.write_bytes(HOOK_PATH.read_bytes())
    hook_dest.chmod(0o755)

    exec_dir = tmpdir / "execution"
    exec_dir.mkdir()
    (exec_dir / "audit_claims.py").write_text("import sys\nsys.exit(0)\n")

    subprocess.run(
        ["git", "-C", str(tmpdir), "config", "core.hooksPath", ".githooks"],
        check=True, capture_output=True,
    )


def test_first_commit_allowed(tmp_path):
    """Fresh repo on main with no HEAD: initial commit must be allowed."""
    _init_repo(tmp_path)

    result = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "--allow-empty", "-m", "Initial commit"],
        env=_make_env(), capture_output=True, text=True,
    )

    assert result.returncode == 0, (
        f"First commit on main was blocked.\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )


def test_second_commit_blocked(tmp_path):
    """After HEAD exists, direct commits on main must still be blocked."""
    _init_repo(tmp_path)
    env = _make_env()

    first = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "--allow-empty", "-m", "Initial commit"],
        env=env, capture_output=True, text=True,
    )
    assert first.returncode == 0, f"First commit setup failed: {first.stderr}"

    second = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "--allow-empty", "-m", "Second commit"],
        env=env, capture_output=True, text=True,
    )

    assert second.returncode != 0, "Second direct commit on main was not blocked"
    assert "Main branch protection" in second.stderr, (
        f"Expected 'Main branch protection' in stderr, got:\n{second.stderr}"
    )


# ── v1.58.0: Test freshness check ────────────────────────────────────────


def _init_repo_on_feature_branch(tmpdir: Path) -> None:
    """Init repo, commit once on main, switch to a feature branch.

    Lets later commits run the full hook chain without tripping main-branch
    protection (which only allows the first commit on main)."""
    _init_repo(tmpdir)
    subprocess.run(
        ["git", "-C", str(tmpdir), "commit", "--allow-empty", "-m", "Initial commit"],
        env=_make_env(), check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmpdir), "checkout", "-b", "feature/freshness-test"],
        check=True, capture_output=True,
    )


def test_test_freshness_warn(tmp_path):
    """Staging execution/doe_init.py without its test emits a stderr warning
    but commit still succeeds (warning-only, exit 0)."""
    _init_repo_on_feature_branch(tmp_path)

    src = tmp_path / "execution" / "doe_init.py"
    src.write_text("# tested change\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "execution/doe_init.py"],
        check=True, capture_output=True,
    )

    result = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "feat(init): adjust tested code"],
        env=_make_env(), capture_output=True, text=True,
    )

    assert result.returncode == 0, (
        f"Freshness check must not block (warning-only).\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "Tested file staged without" in result.stderr, (
        f"Expected freshness warning in stderr, got:\n{result.stderr}"
    )
    assert "tests/execution/test_doe_init.py" in result.stderr, (
        "Warning must name the missing test path so the fix is obvious"
    )


def test_test_freshness_silent_when_test_staged(tmp_path):
    """Staging the source AND its test together emits no warning."""
    _init_repo_on_feature_branch(tmp_path)

    src = tmp_path / "execution" / "doe_init.py"
    src.write_text("# tested change\n")
    test = tmp_path / "tests" / "execution" / "test_doe_init.py"
    test.parent.mkdir(parents=True)
    test.write_text("# updated test\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add",
         "execution/doe_init.py", "tests/execution/test_doe_init.py"],
        check=True, capture_output=True,
    )

    result = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "feat(init): paired change"],
        env=_make_env(), capture_output=True, text=True,
    )

    assert result.returncode == 0, f"Commit failed: {result.stderr}"
    assert "Tested file staged without" not in result.stderr, (
        f"Expected silence when test was staged, got:\n{result.stderr}"
    )


def test_test_freshness_silent_for_unrelated(tmp_path):
    """Staging an unrelated file (no test mapping) emits no warning."""
    _init_repo_on_feature_branch(tmp_path)

    readme = tmp_path / "README.md"
    readme.write_text("# unrelated change\n")
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "README.md"],
        check=True, capture_output=True,
    )

    result = subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "docs: tweak readme"],
        env=_make_env(), capture_output=True, text=True,
    )

    assert result.returncode == 0, f"Commit failed: {result.stderr}"
    assert "Tested file staged without" not in result.stderr, (
        f"Expected silence for unrelated file, got:\n{result.stderr}"
    )
