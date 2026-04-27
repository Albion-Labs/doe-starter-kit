"""Tests for execution/doe_init.py post-install polish helpers.

Covers v1.56.0 Parts A (auto-commit), B (.env bootstrap), and D (branch
normalisation), plus v1.56.1 spec-deviation fixes (kit version stamping
in commit, .gitignore safety check, fill-values hint) — all run inside
setup_ci_git_collaboration() before core.hooksPath is activated.
"""

import inspect
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "execution"))

import doe_init
from doe_init import (
    generate_claude_md,
    maybe_auto_commit,
    maybe_bootstrap_env,
    maybe_normalise_branch,
)


# ── Part B: maybe_bootstrap_env ─────────────────────────────────────────

def test_env_bootstrap_creates(tmp_path, capsys):
    """Fresh dir with .env.example + .gitignore (.env excluded) + accept=True
    -> .env is copied and the fill-values hint is printed (v1.56.1)."""
    (tmp_path / ".env.example").write_text("FOO=bar\n")
    (tmp_path / ".gitignore").write_text(".env\n")

    created = maybe_bootstrap_env(tmp_path, accept=True)

    assert created is True
    assert (tmp_path / ".env").exists()
    assert (tmp_path / ".env").read_text() == "FOO=bar\n"
    out = capsys.readouterr().out
    assert "fill in values" in out, "Confirmation must include fill-values hint"


def test_env_bootstrap_preserves_existing(tmp_path, capsys):
    """Existing .env is preserved, not overwritten, even with accept=True.
    Reaches the existing-file check before the .gitignore safety check."""
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


# ── v1.56.1: .gitignore safety check (issue #16 deviation) ──────────────

def test_env_bootstrap_skips_when_gitignore_missing(tmp_path, capsys):
    """No .gitignore at all -> skip with warning. Never create ungitignored secrets."""
    (tmp_path / ".env.example").write_text("FOO=bar\n")
    # Deliberately no .gitignore created

    created = maybe_bootstrap_env(tmp_path, accept=True)

    assert created is False
    assert not (tmp_path / ".env").exists()
    out = capsys.readouterr().out
    assert ".gitignore" in out and ("missing" in out.lower() or "skip" in out.lower())


def test_env_bootstrap_skips_when_gitignore_lacks_env_entry(tmp_path, capsys):
    """`.gitignore` exists but no `.env` rule -> skip with warning."""
    (tmp_path / ".env.example").write_text("FOO=bar\n")
    (tmp_path / ".gitignore").write_text("node_modules/\n*.log\n")  # no .env rule

    created = maybe_bootstrap_env(tmp_path, accept=True)

    assert created is False
    assert not (tmp_path / ".env").exists()
    out = capsys.readouterr().out
    assert "doesn't exclude .env" in out or "doesn't exclude `.env`" in out or "exclude .env" in out


def test_env_bootstrap_proceeds_when_gitignore_excludes_env(tmp_path):
    """Standard kit `.gitignore` (with `.env` line) -> proceed normally."""
    (tmp_path / ".env.example").write_text("FOO=bar\n")
    (tmp_path / ".gitignore").write_text(".env\n.env.local\n")

    created = maybe_bootstrap_env(tmp_path, accept=True)

    assert created is True
    assert (tmp_path / ".env").exists()


def test_env_bootstrap_proceeds_when_gitignore_uses_glob(tmp_path):
    """`.env*` glob in `.gitignore` -> accepted (covers `.env`, `.env.local`, etc)."""
    (tmp_path / ".env.example").write_text("FOO=bar\n")
    (tmp_path / ".gitignore").write_text(".env*\n")

    created = maybe_bootstrap_env(tmp_path, accept=True)

    assert created is True
    assert (tmp_path / ".env").exists()


def test_env_bootstrap_treats_negation_as_no_match(tmp_path):
    """A `!.env` negation rule must NOT count as exclusion. Edge case for the parser."""
    (tmp_path / ".env.example").write_text("FOO=bar\n")
    (tmp_path / ".gitignore").write_text("!.env\n")

    created = maybe_bootstrap_env(tmp_path, accept=True)

    assert created is False, "Negation rule re-includes .env; safety check must skip"


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

    # Match the call site by function name alone — kwargs (like kit_version=...)
    # may have been added without changing the structural invariant.
    hooks_activation = '"core.hooksPath", ".githooks"'
    auto_call = "maybe_auto_commit("

    assert auto_call in src, "setup_ci_git_collaboration must call maybe_auto_commit(...)"
    assert hooks_activation in src, "setup_ci_git_collaboration must run `git config core.hooksPath .githooks`"

    auto_idx = src.index(auto_call)
    hooks_idx = src.index(hooks_activation)
    assert auto_idx < hooks_idx, (
        "maybe_auto_commit must be called BEFORE core.hooksPath is activated "
        "so the initial commit does not trigger pre-commit hooks."
    )


# ── v1.56.1: kit version stamping (issue #15 deviation) ─────────────────

def test_auto_commit_includes_kit_version_when_provided(tmp_path, monkeypatch):
    """kit_version='1.56.1' -> commit subject contains `(kit v1.56.1)`."""
    _init_isolated_repo(tmp_path, monkeypatch)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test User"],
        check=True, capture_output=True,
    )
    (tmp_path / "file.txt").write_text("hi\n")

    sha = maybe_auto_commit(tmp_path, accept=True, kit_version="1.56.1")

    assert sha is not None
    log = subprocess.run(
        ["git", "-C", str(tmp_path), "log", "-1", "--format=%s"],
        capture_output=True, text=True, check=True,
    )
    assert log.stdout.strip() == "chore: initial DOE scaffolding (kit v1.56.1)"


def test_auto_commit_omits_kit_version_when_not_provided(tmp_path, monkeypatch):
    """Backwards compat: kit_version=None -> commit subject is the unadorned form."""
    _init_isolated_repo(tmp_path, monkeypatch)
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.email", "test@example.com"],
        check=True, capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(tmp_path), "config", "user.name", "Test User"],
        check=True, capture_output=True,
    )
    (tmp_path / "file.txt").write_text("hi\n")

    sha = maybe_auto_commit(tmp_path, accept=True)

    assert sha is not None
    log = subprocess.run(
        ["git", "-C", str(tmp_path), "log", "-1", "--format=%s"],
        capture_output=True, text=True, check=True,
    )
    assert log.stdout.strip() == "chore: initial DOE scaffolding"


def test_setup_passes_kit_version_to_auto_commit():
    """Source-level invariant: setup_ci_git_collaboration must pass kit_version
    to maybe_auto_commit so the wizard's commit is stamped with the kit release."""
    src = inspect.getsource(doe_init.setup_ci_git_collaboration)
    assert "kit_version=" in src and "get_kit_version(kit_dir)" in src, (
        "setup_ci_git_collaboration must call maybe_auto_commit with "
        "kit_version=get_kit_version(kit_dir)"
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

    # Match by function name alone; kwargs may be added without changing the order.
    normalise_call = "maybe_normalise_branch("
    auto_call = "maybe_auto_commit("

    assert normalise_call in src, "setup_ci_git_collaboration must call maybe_normalise_branch"
    assert auto_call in src
    assert src.index(normalise_call) < src.index(auto_call), (
        "maybe_normalise_branch must run before maybe_auto_commit so the "
        "scaffolding commit lands on main, not master."
    )


# ── v1.57.0: Git Conventions section in generated CLAUDE.md ─────────────

def test_claude_md_has_git_conventions():
    """Generated CLAUDE.md must include the Git Conventions section -- list of
    Conventional Commits types, the DOE_COMMIT_HOOK_MODE env var, and a
    reference to directives/git-conventions.md."""
    kit_dir = PROJECT_ROOT
    config = {
        "project_type": "static_site",
        "project_type_custom": "",
        "framework": "static",
        "framework_custom": "",
        "collaboration_mode": "solo",
        "has_database": False,
        "has_personal_data": False,
        "platform_targets": [],
    }

    md = generate_claude_md(config, kit_dir)

    assert "Git Conventions" in md, "generated CLAUDE.md missing the Git Conventions header"
    assert "Conventional Commits" in md, "generated CLAUDE.md missing Conventional Commits reference"
    assert "DOE_COMMIT_HOOK_MODE" in md, "generated CLAUDE.md missing the DOE_COMMIT_HOOK_MODE env var"
    assert "directives/git-conventions.md" in md, (
        "generated CLAUDE.md must point readers at the full directive"
    )
    # Sanity: every type prefix is mentioned
    for t in ("feat", "fix", "chore", "docs", "refactor", "test", "perf", "build", "ci", "style"):
        assert t in md, f"Git Conventions section missing type {t!r}"
