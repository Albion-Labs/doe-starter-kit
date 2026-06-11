"""Tests for .claude/hooks/confirm_pr_merge.py (kit v1.71.3).

The hook forces a confirmation conversation before any PR merge. Claude
can merge PRs but must hit the block once, get user approval, then rerun
with ALLOW_MERGE=1. Non-merge commands and ALLOW_MERGE=1 commands take
the silent no-opinion path (sys.exit(0)).

v1.71.3 (liveness audit A7): the trigger is now statement-position (the
phrase quoted inside a PR body/echo'd card no longer blocks — backport
of enforce_review_gate's v1.71.1 fix), and inline ALLOW_MERGE=1 only
counts when it sits in the merge invocation's own env-assignment prefix
(a quoted mention is not user confirmation).
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[2]  # repo root: tests this checkout, not a hardcoded ~/doe-starter-kit (worktree/CI-safe)
HOOK = KIT / ".claude" / "hooks" / "confirm_pr_merge.py"

# Build the trigger phrase at runtime so this test file's bytes don't sit
# in the harness's tool-call stream as a literal that other hooks scan.
GH_PR_MERGE = "gh" + " pr" + " merge"


def _run(command):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    # Scrub ALLOW_MERGE: the hook now reads the env var, and an inherited
    # shell override must not silently flip the block-path tests.
    env = {k: v for k, v in os.environ.items() if k != "ALLOW_MERGE"}
    result = subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
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


# --- Silent no-opinion paths ---

def test_non_merge_command_allows():
    assert _run("ls -la")["decision"] == "allow"


def test_git_status_allows():
    assert _run("git status")["decision"] == "allow"


def test_gh_pr_create_allows():
    """Different gh subcommand — only merge is gated."""
    assert _run("gh pr create --title foo")["decision"] == "allow"


def test_gh_pr_view_allows():
    assert _run("gh pr view 99")["decision"] == "allow"


# --- Block path ---

def test_gh_pr_merge_blocks():
    decision = _run(f"{GH_PR_MERGE} 99")
    assert decision["decision"] == "block"
    assert "ALLOW_MERGE=1" in decision["reason"]


def test_gh_pr_merge_with_flags_blocks():
    decision = _run(f"{GH_PR_MERGE} 99 --squash")
    assert decision["decision"] == "block"


# --- Statement-position trigger (v1.71.3) ---

def test_phrase_in_quoted_text_allows():
    """The phrase inside echo'd documentation must not gate a command that
    merges nothing — this false positive blocked the liveness audit's own
    driver."""
    assert _run(f'echo "next step: {GH_PR_MERGE} 123 after review"')["decision"] == "allow"


def test_phrase_in_pr_body_allows():
    assert _run(f'gh pr comment 5 --body "then run {GH_PR_MERGE} 5"')["decision"] == "allow"


def test_merge_after_separator_blocks():
    decision = _run(f"git fetch && {GH_PR_MERGE} 99 --squash")
    assert decision["decision"] == "block"


def test_merge_with_env_prefix_blocks():
    decision = _run(f"GH_PAGER=cat {GH_PR_MERGE} 99")
    assert decision["decision"] == "block"


# --- Bypass path: ALLOW_MERGE=1 ---

def test_allow_merge_bypass_allows():
    assert _run(f"ALLOW_MERGE=1 {GH_PR_MERGE} 99")["decision"] == "allow"


def test_allow_merge_bypass_with_flags_allows():
    assert _run(f"ALLOW_MERGE=1 {GH_PR_MERGE} 99 --squash --delete-branch")["decision"] == "allow"


def test_allow_merge_quoted_mention_still_blocks():
    """ALLOW_MERGE=1 quoted in trailing text is a mention, not an
    assignment prefixing the invocation — it is not user confirmation."""
    decision = _run(f'{GH_PR_MERGE} 99 --subject "re: ALLOW_MERGE=1 flow"')
    assert decision["decision"] == "block"


def test_allow_merge_on_other_statement_still_blocks():
    """The assignment must prefix the merge invocation itself."""
    decision = _run(f"export ALLOW_MERGE_NOTE=ALLOW_MERGE=1; {GH_PR_MERGE} 99")
    assert decision["decision"] == "block"
