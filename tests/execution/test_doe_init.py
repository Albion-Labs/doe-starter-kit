"""Tests for execution/doe_init.py post-install polish helpers.

Covers v1.56.0 Parts A (auto-commit), B (.env bootstrap), and D (branch
normalisation) — all run inside setup_ci_git_collaboration() before
core.hooksPath is activated.
"""

import inspect
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "execution"))

import doe_init
from doe_init import maybe_auto_commit, maybe_bootstrap_env, maybe_normalise_branch


# ── Part B: maybe_bootstrap_env ─────────────────────────────────────────

def test_env_bootstrap_creates(tmp_path):
    """Fresh dir with .env.example + accept=True -> .env is copied."""
    (tmp_path / ".env.example").write_text("FOO=bar\n")

    created = maybe_bootstrap_env(tmp_path, accept=True)

    assert created is True
    assert (tmp_path / ".env").exists()
    assert (tmp_path / ".env").read_text() == "FOO=bar\n"


def test_env_bootstrap_preserves_existing(tmp_path, capsys):
    """Existing .env is preserved, not overwritten, even with accept=True."""
    (tmp_path / ".env.example").write_text("FOO=new\n")
    (tmp_path / ".env").write_text("FOO=existing\n")

    created = maybe_bootstrap_env(tmp_path, accept=True)

    assert created is False
    assert (tmp_path / ".env").read_text() == "FOO=existing\n"
    captured = capsys.readouterr()
    assert "already exists" in captured.out or "not overwriting" in captured.out


def test_env_bootstrap_no_example(tmp_path):
    """Missing .env.example skips silently — no .env created, no error."""
    created = maybe_bootstrap_env(tmp_path, accept=True)

    assert created is False
    assert not (tmp_path / ".env").exists()


# ── Part A: maybe_auto_commit ───────────────────────────────────────────

def _init_isolated_repo(tmp_path, monkeypatch):
    """Init a git repo that ignores global config — HOME and GIT_CONFIG_GLOBAL."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    monkeypatch.delenv("GIT_AUTHOR_EMAIL", raising=False)
    monkeypatch.delenv("GIT_COMMITTER_EMAIL", raising=False)
    monkeypatch.delenv("GIT_AUTHOR_NAME", raising=False)
    monkeypatch.delenv("GIT_COMMITTER_NAME", raising=False)
    subprocess.run(
        ["git", "init", str(tmp_path)],
        check=True, capture_output=True,
    )


def test_auto_commit_skips_without_email(tmp_path, monkeypatch, capsys):
    """No user.email set -> warn, return None, no commit made."""
    _init_isolated_repo(tmp_path, monkeypatch)
    (tmp_path / "file.txt").write_text("hi\n")

    result = maybe_auto_commit(tmp_path, accept=True)

    assert result is None
    log = subprocess.run(
        ["git", "-C", str(tmp_path), "log", "--oneline"],
        capture_output=True, text=True,
    )
    assert log.stdout.strip() == "", "No commit should have been created"

    out = capsys.readouterr().out
    assert "user.email" in out


def test_auto_commit_before_hooks_activation():
    """Source-level invariant: maybe_auto_commit must be called before the
    `git config core.hooksPath` subprocess invocation in setup_ci_git_collaboration."""
    src = inspect.getsource(doe_init.setup_ci_git_collaboration)

    # The call site (not a docstring or comment mention) is uniquely identified by
    # the subprocess.run argv list.
    hooks_activation = '"core.hooksPath", ".githooks"'
    auto_call = "maybe_auto_commit(project_dir)"

    assert auto_call in src, "setup_ci_git_collaboration must call maybe_auto_commit(project_dir)"
    assert hooks_activation in src, "setup_ci_git_collaboration must run `git config core.hooksPath .githooks`"

    auto_idx = src.index(auto_call)
    hooks_idx = src.index(hooks_activation)
    assert auto_idx < hooks_idx, (
        "maybe_auto_commit must be called BEFORE core.hooksPath is activated "
        "so the initial commit does not trigger pre-commit hooks."
    )


# ── Part D: maybe_normalise_branch ──────────────────────────────────────

def _force_master(tmp_path):
    """Point HEAD at refs/heads/master regardless of init.defaultBranch."""
    subprocess.run(
        ["git", "-C", str(tmp_path), "symbolic-ref", "HEAD", "refs/heads/master"],
        check=True, capture_output=True,
    )


def _commit_dummy(tmp_path, monkeypatch):
    """Configure identity via env and commit one file. Caller supplies a clean state."""
    monkeypatch.setenv("GIT_AUTHOR_NAME", "T")
    monkeypatch.setenv("GIT_AUTHOR_EMAIL", "t@t.t")
    monkeypatch.setenv("GIT_COMMITTER_NAME", "T")
    monkeypatch.setenv("GIT_COMMITTER_EMAIL", "t@t.t")
    (tmp_path / "x.txt").write_text("hi\n")
    subprocess.run(["git", "-C", str(tmp_path), "add", "x.txt"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "commit", "-m", "init"],
        check=True, capture_output=True,
    )


def test_normalise_branch_unborn_master(tmp_path, monkeypatch):
    """Unborn HEAD on master -> symbolic-ref to refs/heads/main."""
    _init_isolated_repo(tmp_path, monkeypatch)
    _force_master(tmp_path)

    msg = maybe_normalise_branch(tmp_path)

    assert msg is not None
    assert "main" in msg
    head = subprocess.run(
        ["git", "-C", str(tmp_path), "symbolic-ref", "HEAD"],
        capture_output=True, text=True, check=True,
    )
    assert head.stdout.strip() == "refs/heads/main"


def test_normalise_branch_local_master_with_commits(tmp_path, monkeypatch):
    """Master with commits, no upstream -> renamed to main, commits preserved."""
    _init_isolated_repo(tmp_path, monkeypatch)
    _force_master(tmp_path)
    _commit_dummy(tmp_path, monkeypatch)

    msg = maybe_normalise_branch(tmp_path)

    assert msg == "Renamed master -> main"
    branch = subprocess.run(
        ["git", "-C", str(tmp_path), "branch", "--show-current"],
        capture_output=True, text=True, check=True,
    )
    assert branch.stdout.strip() == "main"
    log = subprocess.run(
        ["git", "-C", str(tmp_path), "log", "--oneline"],
        capture_output=True, text=True, check=True,
    )
    assert "init" in log.stdout


def test_normalise_branch_already_main(tmp_path, monkeypatch):
    """Branch already 'main' -> no-op, return None."""
    _init_isolated_repo(tmp_path, monkeypatch)
    subprocess.run(
        ["git", "-C", str(tmp_path), "symbolic-ref", "HEAD", "refs/heads/main"],
        check=True, capture_output=True,
    )

    msg = maybe_normalise_branch(tmp_path)

    assert msg is None


def test_normalise_branch_master_with_upstream_warns(tmp_path, monkeypatch):
    """Master with upstream tracking -> warn only, no rename (avoids remote side-effects)."""
    _init_isolated_repo(tmp_path, monkeypatch)
    _force_master(tmp_path)
    _commit_dummy(tmp_path, monkeypatch)

    # Synthesise an upstream by creating a remote-tracking ref + branch config.
    subprocess.run(
        ["git", "-C", str(tmp_path), "remote", "add", "origin", "/dev/null"],
        check=True, capture_output=True,
    )
    sha = subprocess.run(
        ["git", "-C", str(tmp_path), "rev-parse", "master"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    subprocess.run(
        ["git", "-C", str(tmp_path), "update-ref", "refs/remotes/origin/master", sha],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "branch.master.remote", "origin"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "branch.master.merge", "refs/heads/master"],
        check=True, capture_output=True,
    )

    msg = maybe_normalise_branch(tmp_path)

    assert msg is not None and "manually" in msg
    branch = subprocess.run(
        ["git", "-C", str(tmp_path), "branch", "--show-current"],
        capture_output=True, text=True, check=True,
    )
    assert branch.stdout.strip() == "master"


def test_normalise_branch_called_before_auto_commit():
    """Source-level invariant: maybe_normalise_branch must run before
    maybe_auto_commit so the scaffolding commit lands on `main`, not `master`."""
    src = inspect.getsource(doe_init.setup_ci_git_collaboration)

    normalise_call = "maybe_normalise_branch(project_dir)"
    auto_call = "maybe_auto_commit(project_dir)"

    assert normalise_call in src, "setup_ci_git_collaboration must call maybe_normalise_branch"
    assert auto_call in src
    assert src.index(normalise_call) < src.index(auto_call), (
        "maybe_normalise_branch must run before maybe_auto_commit so the "
        "scaffolding commit lands on main, not master."
    )
