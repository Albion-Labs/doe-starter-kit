"""Hook: Force a confirmation step before any PR merge.

Claude CAN merge PRs, but the hook forces a two-step flow:
1. First attempt hits the block -- Claude must stop and ask the user
2. User confirms -- Claude reruns with ALLOW_MERGE=1

This means Claude can never merge as a silent side-effect of a larger
task. The block forces the conversation to happen.
"""
import json
import os
import re
import sys


def main():
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "")

    # v1.71.3: match an actual invocation at a statement position (start of
    # command or after a separator), optionally preceded by env-var
    # assignments -- backport of enforce_review_gate's v1.71.1 fix. The
    # previous bare substring match also fired on the PHRASE inside quoted
    # text (PR bodies, echo'd cards, heredoc documentation), gating commands
    # that merge nothing.
    invocations = list(re.finditer(
        r'(?:^|[\n;&|])\s*((?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*)gh\s+pr\s+merge\b',
        command,
    ))
    if not invocations:
        sys.exit(0)

    # Confirmation flag: the env var, or an inline assignment in the
    # invocation's own env-prefix (group 1) -- NOT a bare substring mention,
    # which would count a quoted "ALLOW_MERGE=1" in a PR body or card as
    # user confirmation. Every merge invocation in the command needs it.
    if os.environ.get("ALLOW_MERGE") == "1" or all(
        re.search(r'\bALLOW_MERGE=1\s', m.group(1)) for m in invocations
    ):
        sys.exit(0)

    print(json.dumps({
        "decision": "block",
        "reason": (
            "GUARDRAIL: PR merge requires user confirmation. "
            "Show a bordered card with PR details (number, title, branch, "
            "checks) and ask the user: 'Shall I merge this?' "
            "Only proceed with ALLOW_MERGE=1 after they confirm."
        ),
    }))


if __name__ == "__main__":
    main()
