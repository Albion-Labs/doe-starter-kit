"""Tests for .githooks/pre-push gates.

v1.72.0: the tutorial-docs version gate was retired with the tutorial site.
What remains: the whats-new freshness gate on release-tag pushes, and the
methodology quick check. These tests run the REAL hook against a fixture repo.
"""

import os
import subprocess
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_PATH = KIT_ROOT / ".githooks" / "pre-push"


def _setup_fixture(tmpdir: Path, whats_new_tags=("v0.1.0",)) -> dict:
    """Init a repo on main with a whats-new.html carrying the given release
    sections and a stub methodology test that exits 0."""
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

    docs = tmpdir / "docs" / "tutorial"
    docs.mkdir(parents=True)
    sections = "".join(f"<h2>{t}</h2>\n" for t in whats_new_tags)
    (docs / "whats-new.html").write_text(f"<html>{sections}</html>\n")

    # Methodology test must exit 0 so the hook reaches its final `exit 0`
    exec_dir = tmpdir / "execution"
    exec_dir.mkdir()
    (exec_dir / "test_methodology.py").write_text("import sys\nsys.exit(0)\n")

    subprocess.run(["git", "-C", str(tmpdir), "add", "-A"], check=True, capture_output=True, env=env)
    subprocess.run(
        ["git", "-C", str(tmpdir), "commit", "-m", "initial"],
        check=True, capture_output=True, env=env,
    )

    return env


def _run_hook(tmpdir: Path, env: dict, stdin: str = "") -> subprocess.CompletedProcess:
    """Invoke the real pre-push hook against tmpdir.

    stdin mimics git's pre-push ref lines:
    "<local_ref> <local_sha> <remote_ref> <remote_sha>"
    """
    return subprocess.run(
        ["bash", str(tmpdir / ".githooks" / "pre-push")],
        cwd=tmpdir, env=env, capture_output=True, text=True, input=stdin,
    )


def test_branch_push_passes_without_tutorial_pages(tmp_path):
    """v1.72.0 regression: the retired tutorial-docs gate must not fire.

    Pre-v1.72.0 this fixture (docs stamped ahead of the tag) blocked pushes
    from main. With the tutorial site gone the hook must pass straight
    through to the methodology check.
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


def test_tag_push_blocked_when_whats_new_stale(tmp_path):
    """Pushing a release tag with no matching whats-new section must block."""
    env = _setup_fixture(tmp_path, whats_new_tags=("v0.1.0",))

    result = _run_hook(
        tmp_path, env,
        stdin="refs/tags/v0.2.0 aaa refs/tags/v0.2.0 0000\n",
    )

    assert result.returncode != 0, "Stale whats-new must block a release-tag push"
    assert "Whats-new freshness check failed" in (result.stdout + result.stderr)


def test_tag_push_passes_when_whats_new_current(tmp_path):
    """Pushing a release tag whose whats-new section exists must pass."""
    env = _setup_fixture(tmp_path, whats_new_tags=("v0.1.0", "v0.2.0"))

    result = _run_hook(
        tmp_path, env,
        stdin="refs/tags/v0.2.0 aaa refs/tags/v0.2.0 0000\n",
    )

    assert result.returncode == 0, (
        f"Current whats-new should pass.\nstdout: {result.stdout}\nstderr: {result.stderr}"
    )
