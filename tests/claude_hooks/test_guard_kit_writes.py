"""Tests for .claude/hooks/guard_kit_writes.py (kit v1.60.0).

The hook now has one job: block irreversible Bash operations against the
kit (recursive removal, force-push to kit main). Edits and ordinary Bash
redirects are allowed; PR review is the canonical gate.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[2]  # repo root: tests this checkout, not a hardcoded ~/doe-starter-kit (worktree/CI-safe)
HOOK = KIT / ".claude" / "hooks" / "guard_kit_writes.py"


def _run(payload, cwd=None, env_extra=None):
    env = os.environ.copy()
    env.pop("SKIP_KIT_GUARD", None)
    if env_extra:
        env.update(env_extra)
    result = subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(cwd) if cwd else "/tmp",
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


# --- Edits + ordinary Bash redirects: ALLOW (file-edit branch retired) ---

def test_edit_kit_file_allows():
    decision = _run({"tool_name": "Edit", "tool_input": {"file_path": str(KIT / "x.md")}})
    assert decision["decision"] == "allow"


def test_write_kit_file_allows():
    decision = _run({"tool_name": "Write", "tool_input": {"file_path": str(KIT / "x.md")}})
    assert decision["decision"] == "allow"


def test_multiedit_kit_file_allows():
    decision = _run({"tool_name": "MultiEdit", "tool_input": {"file_path": str(KIT / "x.md")}})
    assert decision["decision"] == "allow"


def test_bash_redirect_to_kit_allows():
    cmd = "cat foo " + chr(62) + " " + str(KIT) + "/x.md"
    decision = _run({"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert decision["decision"] == "allow"


def test_bash_heredoc_with_kit_in_body_allows():
    cmd = (
        "cat " + chr(62) + " /tmp/foo.json "
        "<" + chr(60) + "EOF\n"
        "{\"path\": \"" + str(KIT) + "\"}\n"
        "EOF"
    )
    decision = _run({"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert decision["decision"] == "allow"


def test_bash_cp_to_kit_allows():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "cp foo " + str(KIT) + "/x.md"}})
    assert decision["decision"] == "allow"


def test_bash_cd_kit_then_git_commit_allows():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "cd " + str(KIT) + " && git commit -m foo"}})
    assert decision["decision"] == "allow"


def test_bash_python3_c_referencing_kit_allows():
    cmd = "python3 -c \"import os; print(os.listdir(\\\"" + str(KIT) + "\\\"))\""
    decision = _run({"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert decision["decision"] == "allow"


def test_bash_rm_non_recursive_kit_file_allows():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "rm " + str(KIT) + "/x.md"}})
    assert decision["decision"] == "allow"


# --- Destructive operations: BLOCK ---

def test_bash_rm_rf_kit_blocks():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "rm -rf " + str(KIT)}})
    assert decision["decision"] == "block"


def test_bash_rm_recursive_long_form_blocks():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "rm --recursive " + str(KIT) + "/foo"}})
    assert decision["decision"] == "block"


def test_bash_rm_capital_R_kit_blocks():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "rm -R " + str(KIT) + "/foo"}})
    assert decision["decision"] == "block"


def test_bash_force_push_mentioning_kit_blocks():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "git push --force " + str(KIT)}})
    assert decision["decision"] == "block"


def test_bash_force_push_short_form_mentioning_kit_blocks():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "git push -f " + str(KIT)}})
    assert decision["decision"] == "block"


def test_bash_force_push_from_kit_cwd_blocks():
    decision = _run(
        {"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}},
        cwd=KIT,
    )
    assert decision["decision"] == "block"


def test_bash_force_push_from_outside_kit_without_kit_mention_allows():
    decision = _run(
        {"tool_name": "Bash", "tool_input": {"command": "git push --force origin main"}},
        cwd="/tmp",
    )
    assert decision["decision"] == "allow"


# --- Escape valve ---

def test_skip_kit_guard_env_overrides_block():
    decision = _run(
        {"tool_name": "Bash", "tool_input": {"command": "rm -rf " + str(KIT)}},
        env_extra={"SKIP_KIT_GUARD": "1"},
    )
    assert decision["decision"] == "allow"


# --- Non-Bash, non-edit ---

def test_read_kit_file_allows():
    decision = _run({"tool_name": "Read", "tool_input": {"file_path": str(KIT / "x.md")}})
    assert decision["decision"] == "allow"
