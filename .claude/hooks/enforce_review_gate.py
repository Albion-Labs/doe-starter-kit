"""Hook: Block gh pr create unless adversarial review passed for current HEAD.

Checks for a review artifact at .tmp/review-passed-<branch>.json written by
execution/record_review_result.py. The artifact must exist and its reviewed_sha
must match the current HEAD -- stale reviews (commits added after review) are
rejected.

Skip: SKIP_REVIEW_GATE=1
"""
import json
import os
import subprocess
import sys
from pathlib import Path


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
