"""Hook: Block gh pr create on feature branches unless adversarial review
passed for current HEAD and all steps in ## Current are complete.

Only applies to feature/* branches. Housekeeping, wrap, and other non-feature
branches pass through freely -- process improvements shouldn't be blocked by
incomplete feature work.

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


def check_steps_complete():
    """Return (ok, message). ok=True if all steps complete or no steps exist."""
    todo_path = Path("tasks/todo.md")
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
        print(json.dumps({"decision": "allow"}))
        return

    if os.environ.get("SKIP_REVIEW_GATE") == "1":
        print(json.dumps({"decision": "allow"}))
        return

    try:
        branch = subprocess.check_output(
            ["git", "branch", "--show-current"], text=True
        ).strip()
        head_sha = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True
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
        print(json.dumps({"decision": "allow"}))
        return

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

    # Gate 2: Adversarial review must have passed for current HEAD
    artifact = Path(".tmp") / f"review-passed-{branch}.json"

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

    print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
