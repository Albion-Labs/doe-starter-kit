"""Tests for .githooks/commit-msg Conventional Commits validator (v1.57.0).

Drives the real commit-msg hook against a temp file containing a candidate
commit subject, asserting exit code and stderr in both warn and block modes.
"""

import os
import subprocess
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK_PATH = KIT_ROOT / ".githooks" / "commit-msg"


def _run_hook(subject: str, mode: str = "warn"):
    """Write `subject` to a temp commit-message file and run the hook against it.

    Returns subprocess.CompletedProcess with stdout/stderr/returncode.
    """
    msg_file = Path("/tmp") / f"doe-commit-msg-test-{os.getpid()}.txt"
    msg_file.write_text(subject + "\n")
    try:
        env = {**os.environ, "DOE_COMMIT_HOOK_MODE": mode}
        # Step-mark enforcement requires a git repo with staged tasks/todo.md
        # for messages mentioning "Step N" or "(vX.Y.Z)" -- bypass with the
        # skip vars so the test focuses on CC validation only.
        env["SKIP_STEP_MARK_CHECK"] = "1"
        env["SKIP_CHANGELOG_CHECK"] = "1"
        return subprocess.run(
            ["sh", str(HOOK_PATH), str(msg_file)],
            env=env, capture_output=True, text=True,
        )
    finally:
        msg_file.unlink(missing_ok=True)


# ── Compliant subject in warn mode ──────────────────────────────────────

def test_compliant():
    """A valid Conventional Commits subject must pass cleanly with no warning."""
    result = _run_hook("feat(wizard): add reset button", mode="warn")
    assert result.returncode == 0
    assert "Conventional Commits" not in result.stderr


# ── Warn mode behaviour ──────────────────────────────────────────────────

def test_warn_mode():
    """Non-compliant subject in warn mode -> warning to stderr, exit 0."""
    result = _run_hook("just some random message", mode="warn")
    assert result.returncode == 0, "warn mode must NOT block"
    assert "Conventional Commits" in result.stderr


# ── Block mode behaviour ─────────────────────────────────────────────────

def test_block_mode():
    """Non-compliant subject in block mode -> warning to stderr, exit 1."""
    result = _run_hook("just some random message", mode="block")
    assert result.returncode == 1, "block mode must block"
    assert "Conventional Commits" in result.stderr


# ── Allowlist: every entry bypasses validation in BOTH modes ─────────────

def test_allowlist():
    """All 6 allowlist patterns must pass cleanly in block mode (strictest)."""
    cases = [
        "Merge pull request #20 from Albion-Labs/feature/foo",
        'Revert "feat(wizard): broken thing"',
        "Initial commit",
        "fixup! feat(wizard): squash this in",
        "squash! feat(wizard): combine this",
        "v1.55.11: legacy release format from before v1.57.0",
    ]
    for subject in cases:
        result = _run_hook(subject, mode="block")
        assert result.returncode == 0, (
            f"Allowlisted subject was blocked in block mode.\n"
            f"  subject: {subject!r}\n"
            f"  stderr: {result.stderr}"
        )
        assert "Conventional Commits" not in result.stderr, (
            f"Allowlisted subject triggered the warning anyway.\n"
            f"  subject: {subject!r}"
        )
