"""Hook: Block gh pr create on feature branches unless adversarial review
passed for current HEAD and all steps in ## Current are complete.

Only applies to feature/* branches. Housekeeping, wrap, and other non-feature
branches pass through freely -- process improvements shouldn't be blocked by
incomplete feature work.

Cross-project guard (v1.61.4): if the Bash command starts with
`cd <path> &&` and the path resolves outside the hook's project tree, the
gate passes through. This handles cross-project `gh pr create` from one
project's harness targeting a different repo (e.g. a consumer project editing the kit) --
the hook's release-readiness checks don't apply to a different project.

Checks (feature/* branches only):
1. All steps in tasks/todo.md ## Current must be [x]. Prevents mid-feature PRs
   which create merge/rebase overhead. PRs are created at retro only.
2. Review artifact at .tmp/review-passed-<branch>.json (written by
   execution/record_review_result.py). Must exist and reviewed_sha must match
   current HEAD -- stale reviews are rejected.

Skip: SKIP_REVIEW_GATE=1
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    """Return the project root anchored to $CLAUDE_PROJECT_DIR. v1.63.0
    hardening: relative paths inside this hook resolve against the agent
    shell's cwd, which silently false-passes (gate goes quiet) when the
    shell has drifted to a subdir. Pair with v1.62.2 which fixed the
    invocation-side path. Fall back to cwd only if the env var is unset --
    a loud failure beats a silent regression.
    """
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        return Path(project_dir)
    return Path.cwd()


def check_steps_complete():
    """Return (ok, message). ok=True if all steps complete or no steps exist."""
    todo_path = _project_root() / "tasks" / "todo.md"
    if not todo_path.exists():
        return True, ""

    lines = todo_path.read_text().splitlines()
    in_current = False
    total = 0
    done = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Current"):
            in_current = True
            continue
        if in_current and stripped.startswith("## "):
            break
        if in_current and re.match(r"\d+[a-d]?\.\s+\[", stripped):
            total += 1
            if re.match(r"\d+[a-d]?\.\s+\[x\]", stripped):
                done += 1

    if total == 0:
        return True, ""
    if done < total:
        return False, f"{done}/{total} steps complete -- finish all steps before creating PR"
    return True, ""


def main():
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "")

    if "gh pr create" not in command:
        sys.exit(0)

    if os.environ.get("SKIP_REVIEW_GATE") == "1":
        sys.exit(0)

    # Cross-project guard: if the command starts with `cd <path> &&` and the
    # target resolves outside this hook's cwd, the gate doesn't apply.
    cd_match = re.match(r'^\s*cd\s+(\S+)\s*&&', command)
    if cd_match:
        target = os.path.expanduser(cd_match.group(1).strip("'\""))
        if os.path.isdir(target):
            target_real = os.path.realpath(target)
            cwd_real = os.path.realpath(os.getcwd())
            if target_real != cwd_real and not target_real.startswith(cwd_real + os.sep):
                sys.exit(0)

    try:
        # Anchor git invocations to $CLAUDE_PROJECT_DIR so the hook stays
        # cwd-safe (v1.63.0). Pre-fix, these inherited the agent shell's
        # cwd; a subdir cd would still find the project's .git/ via
        # upward search, but a foreign cwd (or a directory outside the
        # project tree) would fail to find git state and the hook would
        # block with a misleading "could not determine git state" error.
        project_root = str(_project_root())
        branch = subprocess.check_output(
            ["git", "-C", project_root, "branch", "--show-current"], text=True
        ).strip()
        head_sha = subprocess.check_output(
            ["git", "-C", project_root, "rev-parse", "HEAD"], text=True
        ).strip()
    except subprocess.CalledProcessError:
        print(json.dumps({
            "decision": "block",
            "reason": (
                "GUARDRAIL: Could not determine git state. "
                "Blocking PR creation as a precaution. "
                "Skip: SKIP_REVIEW_GATE=1"
            ),
        }))
        return

    # Only gate feature branches. Housekeeping/wrap/other branches pass freely.
    is_feature_branch = branch.startswith("feature/")

    if not is_feature_branch:
        sys.exit(0)

    # Gate 1: All steps must be complete (no mid-feature PRs)
    steps_ok, steps_msg = check_steps_complete()
    if not steps_ok:
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"GUARDRAIL: {steps_msg}. "
                "No mid-feature PRs -- PRs are created at retro only. "
                "Skip: SKIP_REVIEW_GATE=1"
            ),
        }))
        return

    # Gate 2: Adversarial review must have passed for current HEAD.
    # Artifact path is anchored to $CLAUDE_PROJECT_DIR so the gate stays
    # cwd-safe -- a stale-looking "no artifact" block under shell drift
    # is the same false-fail class as the silent false-pass v1.63.0 fixes.
    artifact = _project_root() / ".tmp" / f"review-passed-{branch}.json"

    if not artifact.exists():
        print(json.dumps({
            "decision": "block",
            "reason": (
                "GUARDRAIL: Adversarial review required before creating PR. "
                "Run /review first. Skip: SKIP_REVIEW_GATE=1"
            ),
        }))
        return

    try:
        data = json.loads(artifact.read_text())
        reviewed_sha = data.get("reviewed_sha", "")
    except (json.JSONDecodeError, KeyError):
        print(json.dumps({
            "decision": "block",
            "reason": (
                "GUARDRAIL: Review artifact is corrupted. "
                "Re-run /review. Skip: SKIP_REVIEW_GATE=1"
            ),
        }))
        return

    if reviewed_sha != head_sha:
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"GUARDRAIL: Review is stale (reviewed {reviewed_sha[:8]}, "
                f"HEAD is {head_sha[:8]}). Re-run /review. "
                "Skip: SKIP_REVIEW_GATE=1"
            ),
        }))
        return

    sys.exit(0)


if __name__ == "__main__":
    main()
