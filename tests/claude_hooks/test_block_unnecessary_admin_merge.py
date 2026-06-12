"""Tests for .claude/hooks/block_unnecessary_admin_merge.py (liveness audit C7).

Two edges fixed in v1.71.6, both exercised here red-first:

1. The trigger regex used `[^\\n;]*` between `gh pr merge` and `--admin`,
   which spans `&&` / `|` into UNRELATED chained statements — a command like
   `gh pr merge 7 --merge && echo 'no --admin needed'` was intercepted even
   though the merge itself carried no --admin flag.

2. The hook's `gh` subprocess queries inherited the hook process cwd. When
   the intercepted command is `cd /other/repo && gh pr merge --admin`, the
   query ran against the WRONG repo. The hook must honour the event's `cwd`
   and a leading `cd <dir> &&` prefix.

All gh calls are hermetic: a stub `gh` on PATH records its cwd and returns
canned JSON, so no network and no dependence on real PR state.
"""
import json
import os
import stat
import subprocess
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[2]  # repo root: tests this checkout, not a hardcoded ~/doe-starter-kit (worktree/CI-safe)
HOOK = KIT / ".claude" / "hooks" / "block_unnecessary_admin_merge.py"

GH_STUB = """#!/bin/bash
# Test stub for gh: record invocation cwd, return canned answers.
echo "$PWD" >> "$GH_CWD_LOG"
if [ "$1" = "pr" ] && [ "$2" = "view" ]; then
  case "$*" in
    *"--json number"*) echo "7"; exit 0 ;;
    *) echo "$GH_VIEW_JSON"; exit 0 ;;
  esac
fi
if [ "$1" = "api" ]; then
  echo "ci-check: failure"
  exit 0
fi
exit 0
"""

CLEAN_JSON = json.dumps(
    {"state": "OPEN", "mergeStateStatus": "CLEAN", "headRefOid": "abc123"}
)


@pytest.fixture
def gh_env(tmp_path):
    """PATH-prepended stub gh + cwd log file. Returns (env, log_path)."""
    bin_dir = tmp_path / "stub-bin"
    bin_dir.mkdir()
    gh = bin_dir / "gh"
    gh.write_text(GH_STUB)
    gh.chmod(gh.stat().st_mode | stat.S_IEXEC)
    log = tmp_path / "gh-cwd.log"
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}:{env['PATH']}"
    env["GH_CWD_LOG"] = str(log)
    env["GH_VIEW_JSON"] = CLEAN_JSON
    env.pop("BYPASS_BLOCK", None)
    return env, log


def _run(payload, env, cwd="/tmp"):
    result = subprocess.run(
        ["python3", str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    out = result.stdout.strip()
    return json.loads(out) if out else None


# --- Edge 1: trigger must not span statement separators ---

def test_admin_in_unrelated_chained_statement_passes_through(gh_env):
    """`--admin` appearing after && in a DIFFERENT statement must not trip
    the hook (and must not trigger any gh query at all)."""
    env, log = gh_env
    decision = _run(
        {"tool_input": {"command":
            "gh pr merge 7 --merge && echo 'no --admin needed here'"}},
        env,
    )
    assert decision is None, f"hook intercepted an admin-free merge: {decision}"
    assert not log.exists(), "hook queried gh for a command it should ignore"


def test_admin_after_pipe_passes_through(gh_env):
    env, log = gh_env
    decision = _run(
        {"tool_input": {"command":
            "gh pr merge 7 --merge | grep -v -- --admin"}},
        env,
    )
    assert decision is None
    assert not log.exists()


def test_real_admin_flag_still_intercepted(gh_env):
    """Sanity: --admin in the SAME statement is still caught (CLEAN -> block)."""
    env, _ = gh_env
    decision = _run(
        {"tool_input": {"command": "gh pr merge 7 --admin --merge"}},
        env,
    )
    assert decision is not None and decision["decision"] == "block"
    assert "CLEAN" in decision["reason"]


# --- Edge 2: gh queries must run in the command's target repo ---

def test_cd_prefix_routes_gh_query_to_target_dir(gh_env, tmp_path):
    """`cd X && gh pr merge --admin` must query gh from X, not from the
    hook process cwd."""
    env, log = gh_env
    target = tmp_path / "other-repo"
    target.mkdir()
    _run(
        {"tool_input": {"command": f"cd {target} && gh pr merge 7 --admin"}},
        env,
    )
    recorded = log.read_text().strip().splitlines()
    assert recorded, "stub gh never invoked"
    assert all(Path(line).resolve() == target.resolve() for line in recorded), (
        f"gh queried from {recorded}, expected {target}"
    )


def test_event_cwd_routes_gh_query(gh_env, tmp_path):
    """Without a cd prefix, the event's cwd field is the query directory."""
    env, log = gh_env
    repo = tmp_path / "event-repo"
    repo.mkdir()
    _run(
        {"cwd": str(repo),
         "tool_input": {"command": "gh pr merge 7 --admin"}},
        env,
    )
    recorded = log.read_text().strip().splitlines()
    assert recorded, "stub gh never invoked"
    assert all(Path(line).resolve() == repo.resolve() for line in recorded)


def test_relative_cd_resolves_against_event_cwd(gh_env, tmp_path):
    env, log = gh_env
    base = tmp_path / "base"
    sub = base / "sub"
    sub.mkdir(parents=True)
    _run(
        {"cwd": str(base),
         "tool_input": {"command": "cd sub && gh pr merge 7 --admin"}},
        env,
    )
    recorded = log.read_text().strip().splitlines()
    assert recorded, "stub gh never invoked"
    assert all(Path(line).resolve() == sub.resolve() for line in recorded)


# --- Decision-matrix sanity (hermetic via stub) ---

def test_unknown_state_blocks(gh_env):
    env, _ = gh_env
    env["GH_VIEW_JSON"] = json.dumps(
        {"state": "OPEN", "mergeStateStatus": "UNKNOWN", "headRefOid": "abc"}
    )
    decision = _run(
        {"tool_input": {"command": "gh pr merge 7 --admin"}}, env
    )
    assert decision["decision"] == "block"
    assert "TRANSIENT" in decision["reason"]


def test_blocked_state_surfaces_failing_checks(gh_env):
    env, _ = gh_env
    env["GH_VIEW_JSON"] = json.dumps(
        {"state": "OPEN", "mergeStateStatus": "BLOCKED", "headRefOid": "abc"}
    )
    decision = _run(
        {"tool_input": {"command": "gh pr merge 7 --admin"}}, env
    )
    assert decision["decision"] == "block"
    assert "ci-check: failure" in decision["reason"]


def test_merged_pr_passes_through(gh_env):
    env, _ = gh_env
    env["GH_VIEW_JSON"] = json.dumps(
        {"state": "MERGED", "mergeStateStatus": "UNKNOWN", "headRefOid": "abc"}
    )
    decision = _run(
        {"tool_input": {"command": "gh pr merge 7 --admin"}}, env
    )
    assert decision is None
