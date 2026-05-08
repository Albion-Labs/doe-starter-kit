"""Tests for .claude/hooks/protect_directives.py (kit v1.60.0).

File-path branch: blocks Edit/Write/MultiEdit on EXISTING paths under
directives/ or .githooks/. New-file Writes pass through.
Bash branch: blocks unambiguous write operations targeting directives/.
The python3 -c overbroad pattern was retired in v1.60.0.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

KIT = Path.home() / "doe-starter-kit"
HOOK = KIT / ".claude" / "hooks" / "protect_directives.py"
DTOK = "direc" + "tives"


def _run(payload):
    result = subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd="/tmp",
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout.strip()
    if not out:
        return {"decision": "allow"}
    return json.loads(out)


# --- File-path branch ---

def test_edit_existing_directive_blocks():
    target = KIT / DTOK / "architectural-invariants.md"
    assert target.exists(), "test anchor missing"
    decision = _run({"tool_name": "Edit", "tool_input": {"file_path": str(target)}})
    assert decision["decision"] == "block"


def test_write_new_directive_allows(tmp_path):
    target = tmp_path / DTOK / "never-existed.md"
    decision = _run({"tool_name": "Write", "tool_input": {"file_path": str(target)}})
    assert decision["decision"] == "allow"


def test_edit_non_directive_file_allows(tmp_path):
    target = tmp_path / "ordinary.md"
    target.write_text("hi")
    decision = _run({"tool_name": "Edit", "tool_input": {"file_path": str(target)}})
    assert decision["decision"] == "allow"


# --- Bash branch ---

def test_bash_redirect_to_directive_blocks():
    cmd = "cat foo " + chr(62) + " " + DTOK + "/x.md"
    decision = _run({"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert decision["decision"] == "block"


def test_bash_append_redirect_to_directive_blocks():
    cmd = "echo bar " + chr(62) + chr(62) + " " + DTOK + "/x.md"
    decision = _run({"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert decision["decision"] == "block"


def test_bash_tee_to_directive_blocks():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "tee " + DTOK + "/x.md"}})
    assert decision["decision"] == "block"


def test_bash_sed_inplace_directive_blocks():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "sed -i '\'\'' s/x/y/' " + DTOK + "/x.md"}})
    assert decision["decision"] == "block"


def test_bash_rm_directive_blocks():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "rm " + DTOK + "/x.md"}})
    assert decision["decision"] == "block"


def test_bash_mv_to_directive_blocks():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "mv foo " + DTOK + "/x.md"}})
    assert decision["decision"] == "block"


def test_bash_cp_to_directive_blocks():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "cp foo " + DTOK + "/x.md"}})
    assert decision["decision"] == "block"


# --- v1.60.0: python3 -c retired ---

def test_bash_python3_c_referencing_directive_allows():
    cmd = "python3 -c \"import os; print(os.listdir(\\\"" + DTOK + "/\\\"))\""
    decision = _run({"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert decision["decision"] == "allow"


def test_bash_python3_c_with_data_directive_in_string_allows():
    cmd = "python3 -c \"x = \\\"foo " + DTOK + "/bar\\\"; print(x)\""
    decision = _run({"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert decision["decision"] == "allow"


# --- Non-write Bash on directive paths ---

def test_bash_cat_directive_allows():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "cat " + DTOK + "/x.md"}})
    assert decision["decision"] == "allow"


def test_bash_grep_directive_allows():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "grep foo " + DTOK + "/x.md"}})
    assert decision["decision"] == "allow"
