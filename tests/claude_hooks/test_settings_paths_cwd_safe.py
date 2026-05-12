"""Regression test for kit .claude/settings.json hook command path resolution
(kit v1.62.2).

Bug: prior to v1.62.2, every hook command in the kit's settings.json template
used a relative path of the form `python3 .claude/hooks/<name>.py`. Claude
Code's persistent shell preserves cwd across tool calls, so any legitimate
`cd` (e.g. to spin up a dev server) caused the hook to resolve against the
wrong directory. Python exited with errno 2 (file-not-found), the hook
exited non-zero, and Claude Code interpreted that as the hook BLOCKING the
tool. Net effect: a single `cd` bricked every subsequent Edit/Write/Bash
tool call in the session.

Fix: every hook command now uses `$CLAUDE_PROJECT_DIR` (injected by Claude
Code into hook environments and pointing at the project root regardless of
shell cwd).

This test asserts two things:
1. STATIC -- no settings.json hook command uses a relative `.claude/hooks/`
   path string.
2. DYNAMIC -- every hook command resolves to its script file when invoked
   from a different cwd, with `CLAUDE_PROJECT_DIR` exported. The hook may
   exit 0 or with a controlled non-zero (block/warn) status, but must never
   fail with "can't open file" / errno 2.

The dynamic check uses a minimal JSON payload that no hook acts on, so the
only failure mode under test is path resolution itself -- not hook logic.
"""
import json
import os
import re
import subprocess
from pathlib import Path

KIT = Path.home() / "doe-starter-kit"
SETTINGS = KIT / ".claude" / "settings.json"


def _iter_hook_commands(settings_path):
    data = json.loads(settings_path.read_text())
    for stage, entries in data.get("hooks", {}).items():
        for entry in entries:
            matcher = entry.get("matcher", "")
            for hook in entry.get("hooks", []):
                cmd = hook.get("command", "")
                if cmd:
                    yield stage, matcher, cmd


def test_no_relative_hook_paths_in_settings():
    """No hook command references a bare `.claude/hooks/` relative path."""
    offenders = []
    for stage, matcher, cmd in _iter_hook_commands(SETTINGS):
        # Look for a literal relative `.claude/hooks/` segment that is NOT
        # preceded by `$CLAUDE_PROJECT_DIR/`. The bug pattern is: a path
        # token starting with `.claude/hooks/` (no leading slash, no env-var
        # prefix).
        if re.search(r"(?<![/\w])\.claude/hooks/", cmd):
            offenders.append(f"{stage}:{matcher}: {cmd}")
    assert not offenders, (
        "Relative `.claude/hooks/` paths in settings.json are not cwd-safe. "
        "A single `cd` in the agent shell bricks the session. Use "
        '`"$CLAUDE_PROJECT_DIR/.claude/hooks/<name>.py"` instead.\n  '
        + "\n  ".join(offenders)
    )


def test_every_hook_uses_claude_project_dir():
    """Every hook command that targets .claude/hooks/ uses $CLAUDE_PROJECT_DIR."""
    bad = []
    for stage, matcher, cmd in _iter_hook_commands(SETTINGS):
        if ".claude/hooks/" in cmd and "$CLAUDE_PROJECT_DIR" not in cmd:
            bad.append(f"{stage}:{matcher}: {cmd}")
    assert not bad, "Hook command targets .claude/hooks/ without $CLAUDE_PROJECT_DIR:\n  " + "\n  ".join(bad)


def test_hooks_resolve_when_cwd_changes(tmp_path):
    """Every settings.json hook command resolves correctly when invoked from
    a foreign cwd. Simulates the real-world failure mode: agent does `cd`,
    then a tool call fires the hook.
    """
    minimal_payload = json.dumps({
        "tool_name": "Read",
        "tool_input": {"file_path": str(tmp_path / "nothing.txt")},
    })

    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(KIT)}
    foreign_cwd = "/tmp"

    failures = []
    for stage, matcher, cmd in _iter_hook_commands(SETTINGS):
        result = subprocess.run(
            cmd,
            shell=True,  # nosec -- intentional: we need shell expansion of $CLAUDE_PROJECT_DIR to mimic Claude Code's hook invocation. Command strings come from settings.json (trusted config), not user input.
            input=minimal_payload,
            capture_output=True,
            text=True,
            env=env,
            cwd=foreign_cwd,
            timeout=10,
        )
        # The diagnostic failure mode from the original bug. errno 2 surfaces
        # as "can't open file" on stderr from python's startup loader, and
        # the process exits with code 2.
        if "can't open file" in result.stderr or "No such file or directory" in result.stderr and "python3" in result.stderr:
            failures.append(
                f"{stage}:{matcher}: {cmd}\n"
                f"  returncode={result.returncode}\n"
                f"  stderr={result.stderr.strip()[:200]}"
            )

    assert not failures, (
        "Hook command failed path resolution from a foreign cwd. This is the "
        "exact bug v1.62.2 fixed -- a single `cd` in the agent shell breaks "
        "the session.\n\n" + "\n\n".join(failures)
    )


def test_claude_project_dir_required_at_runtime(tmp_path):
    """When $CLAUDE_PROJECT_DIR is missing, hooks fail loudly rather than
    silently -- this is the conscious tradeoff in v1.62.2: trust the env
    var unconditionally rather than fall back to `$PWD` (which would silently
    re-introduce the original bug).
    """
    # Pick the first PreToolUse hook command as a probe.
    probe = None
    for stage, matcher, cmd in _iter_hook_commands(SETTINGS):
        if stage == "PreToolUse":
            probe = cmd
            break
    assert probe is not None, "no PreToolUse hooks found"

    env = {k: v for k, v in os.environ.items() if k != "CLAUDE_PROJECT_DIR"}
    result = subprocess.run(
        probe,
        shell=True,  # nosec -- intentional: see test_hooks_resolve_when_cwd_changes for rationale.
        input='{"tool_name":"Read","tool_input":{"file_path":"/tmp/x"}}',
        capture_output=True,
        text=True,
        env=env,
        cwd="/tmp",
        timeout=10,
    )
    # With CLAUDE_PROJECT_DIR unset, the expansion produces `python3 "/.claude/..."`
    # which python will fail to open. We do NOT want a silent fallback. A loud
    # failure here is the correct, designed behaviour.
    assert result.returncode != 0, (
        "Hook command succeeded with CLAUDE_PROJECT_DIR unset. v1.62.2 trades "
        "robustness-via-fallback for fail-loud detection -- a silent fallback "
        "to $PWD would re-introduce the original cwd bug."
    )
