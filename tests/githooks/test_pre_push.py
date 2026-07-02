"""Tests for .githooks/pre-push.

v1.72.0: the tutorial-docs version gate AND the whats-new freshness gate were
retired with the docs site. The hook's one remaining job is the methodology
quick check. These tests run the REAL hook against a fixture repo.
"""

import os
import subprocess
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_PATH = KIT_ROOT / ".githooks" / "pre-push"


def _setup_fixture(tmpdir: Path, methodology_exit: int = 0) -> dict:
    """Init a repo on main with the real hook copied in and a stub
    methodology test exiting with the given code."""
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "Test",
        "GIT_AUTHOR_EMAIL": "test@example.com",
        "GIT_COMMITTER_NAME": "Test",
        "GIT_COMMITTER_EMAIL": "test@example.com",
    }

    subprocess.run(["git", "init", str(tmpdir)], check=True, capture_output=True, env=env)
    subprocess.run(
        ["git", "-C", str(tmpdir), "symbolic-ref", "HEAD", "refs/heads/main"],
        check=True, capture_output=True, env=env,
    )

    # The hook derives PROJECT_ROOT from its own location, so it must be
    # copied into the fixture repo (not invoked from the kit tree).
    hooks_dir = tmpdir / ".githooks"
    hooks_dir.mkdir()
    hook_copy = hooks_dir / "pre-push"
    hook_copy.write_bytes(HOOK_PATH.read_bytes())
    hook_copy.chmod(0o755)

    exec_dir = tmpdir / "execution"
    exec_dir.mkdir()
    (exec_dir / "test_methodology.py").write_text(
        f"import sys\nsys.exit({methodology_exit})\n"
    )

    subprocess.run(["git", "-C", str(tmpdir), "add", "-A"], check=True, capture_output=True, env=env)
    subprocess.run(
        ["git", "-C", str(tmpdir), "commit", "-m", "initial"],
        check=True, capture_output=True, env=env,
    )

    return env


def _run_hook(tmpdir: Path, env: dict, stdin: str = "") -> subprocess.CompletedProcess:
    """Invoke the fixture's pre-push hook.

    stdin mimics git's pre-push ref lines:
    "<local_ref> <local_sha> <remote_ref> <remote_sha>"
    """
    return subprocess.run(
        ["bash", str(tmpdir / ".githooks" / "pre-push")],
        cwd=tmpdir, env=env, capture_output=True, text=True, input=stdin,
    )


def test_branch_push_passes_without_docs(tmp_path):
    """v1.72.0 regression: the retired tutorial-docs gate must not fire.

    Pre-v1.72.0 this fixture (a tag behind the docs stamp) blocked pushes
    from main. With the docs site gone the hook must pass straight through
    to the methodology check.
    """
    env = _setup_fixture(tmp_path)
    subprocess.run(
        ["git", "-C", str(tmp_path), "tag", "v0.1.0"],
        check=True, capture_output=True, env=env,
    )

    result = _run_hook(
        tmp_path, env,
        stdin="refs/heads/main aaa refs/heads/main bbb\n",
    )

    assert result.returncode == 0, (
        f"Branch push was blocked.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "Tutorial docs version mismatch" not in (result.stdout + result.stderr)


def test_tag_push_passes_without_whats_new(tmp_path):
    """v1.72.0 regression: the retired whats-new freshness gate must not fire.

    Pre-v1.72.0, pushing a release tag without a matching whats-new.html
    section blocked. whats-new.html no longer exists; release-tag pushes
    must pass (CHANGELOG.md is the release record, checked at commit time
    by commit-msg).
    """
    env = _setup_fixture(tmp_path)

    result = _run_hook(
        tmp_path, env,
        stdin="refs/tags/v0.2.0 aaa refs/tags/v0.2.0 0000\n",
    )

    assert result.returncode == 0, (
        f"Tag push was blocked.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "Whats-new freshness check failed" not in (result.stdout + result.stderr)


def test_methodology_failure_blocks_push(tmp_path):
    """The one remaining gate: a failing methodology quick check blocks."""
    env = _setup_fixture(tmp_path, methodology_exit=1)

    result = _run_hook(
        tmp_path, env,
        stdin="refs/heads/main aaa refs/heads/main bbb\n",
    )

    # Note: the hook's `set -e` exits on the failing python call before the
    # "Pre-push blocked" message line is reached — the nonzero exit code is
    # the blocking mechanism, so that's what we assert.
    assert result.returncode != 0, "Failing methodology check must block the push"
