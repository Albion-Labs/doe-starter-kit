"""Tests for .githooks/pre-push tutorial-docs version gate.

Covers the v1.56.0 branch-awareness fix: the docs-vs-tag gate should
enforce on main/master only. Feature branches that stamp docs ahead of
their release tag (PR bumps docs, tag cut post-merge) must push cleanly.
"""

import os
import subprocess
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_PATH = KIT_ROOT / ".githooks" / "pre-push"


def _setup_fixture(tmpdir: Path, branch: str) -> dict:
    """Init a repo with: a v0.1.0 tag, docs stamped to v0.2.0 (mismatch),
    a stub methodology test, and HEAD on the requested branch."""
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

    # docs stamped to v0.2.0 (the "about to ship" state)
    docs = tmpdir / "docs" / "tutorial"
    docs.mkdir(parents=True)
    (docs / "index.html").write_text("<html>v0.2.0</html>\n")

    # stamp_tutorial_version.py needs to exist (gate precondition) but is never invoked here
    exec_dir = tmpdir / "execution"
    exec_dir.mkdir()
    (exec_dir / "stamp_tutorial_version.py").write_text("import sys\nsys.exit(0)\n")
    # Methodology test must exit 0 so the hook reaches its final `exit 0`
    (exec_dir / "test_methodology.py").write_text("import sys\nsys.exit(0)\n")

    # Initial commit + tag v0.1.0 (one minor BEHIND docs)
    subprocess.run(["git", "-C", str(tmpdir), "add", "-A"], check=True, capture_output=True, env=env)
    subprocess.run(
        ["git", "-C", str(tmpdir), "commit", "-m", "initial"],
        check=True, capture_output=True, env=env,
    )
    subprocess.run(
        ["git", "-C", str(tmpdir), "tag", "v0.1.0"],
        check=True, capture_output=True, env=env,
    )

    if branch != "main":
        subprocess.run(
            ["git", "-C", str(tmpdir), "checkout", "-b", branch],
            check=True, capture_output=True, env=env,
        )

    return env


def _run_hook(tmpdir: Path, env: dict) -> subprocess.CompletedProcess:
    """Invoke the real pre-push hook against tmpdir."""
    return subprocess.run(
        ["bash", str(HOOK_PATH)],
        cwd=tmpdir, env=env, capture_output=True, text=True,
    )


def test_docs_gate_blocks_on_main(tmp_path):
    """Docs stamped ahead of tag: pushing from main must be blocked."""
    env = _setup_fixture(tmp_path, branch="main")

    result = _run_hook(tmp_path, env)

    assert result.returncode != 0, "Docs gate must block a main-branch push with mismatched docs"
    assert "Tutorial docs version mismatch" in result.stdout + result.stderr


def test_docs_gate_skipped_on_feature_branch(tmp_path):
    """Same mismatch, feature branch: docs gate must skip, hook must pass."""
    env = _setup_fixture(tmp_path, branch="feature/test-branch")

    result = _run_hook(tmp_path, env)

    assert result.returncode == 0, (
        f"Feature-branch push was blocked (expected skip).\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
    assert "Tutorial docs version mismatch" not in (result.stdout + result.stderr)
