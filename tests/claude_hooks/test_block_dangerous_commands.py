"""Tests for .claude/hooks/block_dangerous_commands.py (kit v1.60.1).

The hook enforces two pattern classes:
- SUBSTRING: invariant tokens that should never appear in any context
- ASSIGNMENT: env-var bypasses; matched only when the var is actually
  ASSIGNED (`VAR=`), not when it's mentioned (grep, docs, test commands).

The substring vs assignment split was added in v1.60.1 to fix a
false-positive class where any Bash command mentioning `SKIP_REVIEW_GATE`
or similar (even just reading docs or running grep) would block.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

KIT = Path.home() / "doe-starter-kit"
HOOK = KIT / ".claude" / "hooks" / "block_dangerous_commands.py"


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
    return json.loads(out)


# --- SUBSTRING patterns: still block as before ---

def test_rm_rf_root_blocks():
    assert _run("rm -rf /")["decision"] == "block"


def test_rm_rf_home_blocks():
    assert _run("rm -rf ~")["decision"] == "block"


def test_rm_rf_dot_blocks():
    assert _run("rm -rf .")["decision"] == "block"


def test_drop_table_blocks():
    assert _run("psql -c 'DROP TABLE users'")["decision"] == "block"


def test_fork_bomb_blocks():
    assert _run(":(){ :|:& };:")["decision"] == "block"


def test_dd_to_disk_blocks():
    assert _run("dd if=/dev/zero of=/dev/sda")["decision"] == "block"


def test_supabase_db_reset_blocks():
    assert _run("supabase db reset")["decision"] == "block"


# --- ASSIGNMENT patterns: block only on actual assignment ---

# Use string concatenation to keep these literal tokens out of THIS test
# file's bytes-as-Bash-command surface (it's only relevant for hooks that
# scan command source bytes; pytest test bodies don't run as Bash, so this
# is purely defensive). The relevant strings are still present in the
# subprocess input -- which is what the hook actually scans.
SKIP_GATE = "SKIP_REVIEW" + "_GATE"
SKIP_CONTRACT = "SKIP_CONTRACT" + "_CHECK"
SKIP_SIGNOFF = "SKIP_SIGNOFF" + "_CHECK"


def test_skip_review_gate_assignment_blocks():
    assert _run(f"{SKIP_GATE}=1 gh pr create --title foo")["decision"] == "block"


def test_skip_review_gate_export_blocks():
    assert _run(f"export {SKIP_GATE}=1")["decision"] == "block"


def test_skip_contract_check_assignment_blocks():
    assert _run(f"{SKIP_CONTRACT}=1 some-command")["decision"] == "block"


def test_skip_signoff_check_assignment_blocks():
    assert _run(f"{SKIP_SIGNOFF}=1 some-command")["decision"] == "block"


def test_skip_review_gate_assignment_with_whitespace_blocks():
    assert _run(f"{SKIP_GATE} =1 cmd")["decision"] == "block"


def test_skip_review_gate_with_mid_command_assignment_blocks():
    """Catches `cmd1 ; SKIP_X=1 cmd2` and similar."""
    assert _run(f"foo; {SKIP_GATE}=1 bar")["decision"] == "block"


# --- ASSIGNMENT patterns: ALLOW when merely mentioned (the v1.60.1 fix) ---

def test_skip_review_gate_in_grep_allows():
    """Reading docs/code that mentions the bypass flag should not block."""
    assert _run(f"grep -rn '{SKIP_GATE}' .claude/hooks/")["decision"] == "allow"


def test_skip_review_gate_in_echo_allows():
    """Echoing the flag name (e.g. for documentation) should not block."""
    assert _run(f"echo 'Run with {SKIP_GATE}=1 to override'")["decision"] == "allow"


def test_skip_review_gate_in_quoted_string_allows():
    """A quoted string mentioning the flag in a different command should not block."""
    assert _run(f"some-cmd --note '{SKIP_GATE} is the bypass var'")["decision"] == "allow"


def test_skip_signoff_in_test_command_allows():
    """A test that asserts the hook blocks the assignment should not itself block."""
    assert _run(f"pytest tests/ -k '{SKIP_SIGNOFF}'")["decision"] == "allow"


# --- Benign commands ---

def test_plain_ls_allows():
    assert _run("ls -la")["decision"] == "allow"


def test_git_status_allows():
    assert _run("git status")["decision"] == "allow"


def test_python_script_allows():
    assert _run("python3 /tmp/script.py")["decision"] == "allow"
