"""Tests for the worktree-convention hint surfaced by `card_done` in
execution/doe_init.py (kit v1.63.0 Step 5).

The hint is universal across solo / team / regulated modes — first-time
users discover the parallel-session pattern at init time so they reach
for `/worktree-create` when they start running multiple Claude Code
sessions on the same project. The convention itself lives in
directives/parallel-worktrees.md (shipped at v1.61.5).
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "execution"))

import doe_init  # noqa: E402
from doe_init import card_done  # noqa: E402


def _base_config(**overrides):
    """Minimal config that satisfies card_done's lookups."""
    base = {
        "framework": "next",
        "is_empty": False,
        "collaboration_mode": "solo",
        "kit_dir": "~/doe-starter-kit",
    }
    base.update(overrides)
    return base


def test_card_done_mentions_worktree_hint_solo_mode(tmp_path, capsys):
    """Solo mode: the worktree hint appears in the done card."""
    card_done(
        kit_version="1.63.0",
        project_dir=str(tmp_path),
        config=_base_config(collaboration_mode="solo"),
        file_count=42,
    )
    out = capsys.readouterr().out
    assert "worktree" in out.lower(), (
        "card_done must surface the worktree convention hint so first-time "
        "users discover /worktree-create before they need it."
    )
    assert "parallel session" in out.lower(), (
        "Hint must include the 'parallel session' framing so users connect "
        "the convention to the situation it solves."
    )


def test_card_done_mentions_worktree_hint_team_mode(tmp_path, capsys):
    """Team mode: same hint surfaces; it is universal across modes."""
    card_done(
        kit_version="1.63.0",
        project_dir=str(tmp_path),
        config=_base_config(collaboration_mode="team"),
        file_count=42,
    )
    out = capsys.readouterr().out
    assert "worktree" in out.lower()
    assert "parallel session" in out.lower()


def test_card_done_hint_references_slash_command(tmp_path, capsys):
    """The hint points users at /worktree-create -- the actionable command,
    not just an abstract convention. The directive reference is the
    follow-on for users who want the full pattern.
    """
    card_done(
        kit_version="1.63.0",
        project_dir=str(tmp_path),
        config=_base_config(),
        file_count=42,
    )
    out = capsys.readouterr().out
    assert "/worktree-create" in out, (
        "Hint must reference the actual slash command so users have a "
        "direct command to run, not just an abstract concept."
    )
    assert "parallel-worktrees.md" in out, (
        "Hint must reference the convention directive for users who want "
        "the full context behind the slash command."
    )


def test_card_done_hint_independent_of_is_empty(tmp_path, capsys):
    """is_empty=True (fresh project getting framework init command) vs
    is_empty=False (existing project) -- both surface the worktree hint.
    """
    for is_empty in (True, False):
        card_done(
            kit_version="1.63.0",
            project_dir=str(tmp_path),
            config=_base_config(is_empty=is_empty),
            file_count=42,
        )
        out = capsys.readouterr().out
        assert "worktree" in out.lower(), (
            f"is_empty={is_empty}: worktree hint must surface regardless of "
            f"whether the project is fresh or existing."
        )
