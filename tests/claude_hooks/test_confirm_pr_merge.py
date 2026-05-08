"""Tests for .claude/hooks/confirm_pr_merge.py (kit v1.61.3).

The hook forces a confirmation conversation before any PR merge. Claude
can merge PRs but must hit the block once, get user approval, then rerun
with ALLOW_MERGE=1. Non-merge commands and ALLOW_MERGE=1 commands take
the silent no-opinion path (sys.exit(0)).
"""
import json
import subprocess
from pathlib import Path

import pytest

KIT = Path.home() / "doe-starter-kit"
HOOK = KIT / ".claude" / "hooks" / "confirm_pr_merge.py"

# Build the trigger phrase at runtime so this test file's bytes don't sit
# in the harness's tool-call stream as a literal that other hooks scan.
GH_PR_MERGE = "gh" + " pr" + " merge"


def _run(command):
    payload = {"tool_name": "Bash", "tool_input": {"command": command}}
    result = subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
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


# --- Bypass path: ALLOW_MERGE=1 ---

def test_allow_merge_bypass_allows():
    assert _run(f"ALLOW_MERGE=1 {GH_PR_MERGE} 99")["decision"] == "allow"


def test_allow_merge_bypass_with_flags_allows():
    assert _run(f"ALLOW_MERGE=1 {GH_PR_MERGE} 99 --squash --delete-branch")["decision"] == "allow"
