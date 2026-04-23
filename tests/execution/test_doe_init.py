"""Tests for execution/doe_init.py post-install polish helpers.

Covers v1.56.0 Parts A (auto-commit) and B (.env bootstrap) — both run
inside setup_ci_git_collaboration() before core.hooksPath is activated.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "execution"))

import doe_init
from doe_init import maybe_bootstrap_env


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
