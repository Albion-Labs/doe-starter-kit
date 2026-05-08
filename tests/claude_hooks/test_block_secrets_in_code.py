"""Tests for .claude/hooks/block_secrets_in_code.py (kit v1.61.3).

Covers Edit/Write/MultiEdit (file_path + content scan) and Bash redirects
into .env variants or files containing secret-shaped strings. Only exact
.env is exempt; every .env.* variant is blocked outright. The hook's
no-opinion path is silent (sys.exit(0)); block paths emit
{"decision": "block", "reason": ...} JSON.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

KIT = Path.home() / "doe-starter-kit"
HOOK = KIT / ".claude" / "hooks" / "block_secrets_in_code.py"

# Build the secret-shaped sample at runtime so this test file's bytes don't
# themselves trip a future content-scanning hook running over the test tree.
SECRET_SAMPLE = "sk" + "_" + "a" * 32  # matches the sk/pk/api/key/... 20+ pattern


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
    decoded = json.loads(out)
    assert decoded.get("decision") != "allow", (
        "regression: hook emitted legacy {'decision': 'allow'} JSON. "
        "PreToolUse no-opinion path must use sys.exit(0); 'allow' is not a "
        "valid root-level decision value (only approve/block are accepted)."
    )
    return decoded


# --- Edit/Write/MultiEdit branch: file path checks ---

def test_edit_dot_env_allows():
    """Exact .env is the only exempt path."""
    decision = _run({"tool_name": "Edit", "tool_input": {"file_path": ".env", "content": "FOO=bar"}})
    assert decision["decision"] == "allow"


def test_edit_dot_env_local_blocks():
    decision = _run({"tool_name": "Edit", "tool_input": {"file_path": ".env.local", "content": "FOO=bar"}})
    assert decision["decision"] == "block"


def test_edit_dot_env_production_blocks():
    decision = _run({"tool_name": "Write", "tool_input": {"file_path": ".env.production", "content": "FOO=bar"}})
    assert decision["decision"] == "block"


def test_edit_dot_env_arbitrary_variant_blocks():
    """Generic .env.<word> check should catch new variants we haven't enumerated."""
    decision = _run({"tool_name": "Write", "tool_input": {"file_path": ".env.staging-eu", "content": "FOO=bar"}})
    assert decision["decision"] == "block"


# --- Edit/Write/MultiEdit branch: content scan ---

def test_edit_ordinary_file_with_secret_blocks():
    decision = _run({"tool_name": "Write", "tool_input": {"file_path": "src/config.ts", "content": f"export const API={SECRET_SAMPLE!r}"}})
    assert decision["decision"] == "block"


def test_edit_ordinary_file_without_secret_allows():
    decision = _run({"tool_name": "Edit", "tool_input": {"file_path": "src/config.ts", "content": "export const FOO = 'bar';"}})
    assert decision["decision"] == "allow"


def test_multiedit_ordinary_file_allows():
    decision = _run({"tool_name": "MultiEdit", "tool_input": {"file_path": "README.md", "content": "# Project"}})
    assert decision["decision"] == "allow"


# --- Bash branch ---

def test_bash_redirect_to_dot_env_local_blocks():
    cmd = "echo FOO=bar " + chr(62) + chr(62) + " .env.local"
    decision = _run({"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert decision["decision"] == "block"


def test_bash_redirect_with_secret_to_arbitrary_path_blocks():
    cmd = f"echo {SECRET_SAMPLE} " + chr(62) + chr(62) + " /tmp/leak.txt"
    decision = _run({"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert decision["decision"] == "block"


def test_bash_redirect_clean_string_allows():
    cmd = "echo hello " + chr(62) + " /tmp/log.txt"
    decision = _run({"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert decision["decision"] == "allow"


def test_bash_secret_in_command_without_redirection_allows():
    """Mentioning a secret-shaped value in a command (e.g. logging) is fine
    so long as no file redirection is present."""
    cmd = f"echo {SECRET_SAMPLE} # demo only"
    decision = _run({"tool_name": "Bash", "tool_input": {"command": cmd}})
    assert decision["decision"] == "allow"


def test_bash_plain_ls_allows():
    decision = _run({"tool_name": "Bash", "tool_input": {"command": "ls -la"}})
    assert decision["decision"] == "allow"


# --- Non-Bash, non-edit ---

def test_read_tool_allows():
    decision = _run({"tool_name": "Read", "tool_input": {"file_path": ".env"}})
    assert decision["decision"] == "allow"
