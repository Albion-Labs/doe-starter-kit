"""Hook: Block destructive Bash operations against ~/doe-starter-kit.

The kit follows a PR-only write model: kit changes go through a feature
branch and PR, gated by `.githooks/pre-commit` ('no direct-to-main') plus
human review. The file-level guard that previously blocked any Edit/Write
on a kit path was retired in v1.60.0 -- 8 minor releases (v1.51-v1.58)
shipped with that guard silently non-functional (lowercase Tool-name
matchers), zero corruption incidents documented; once the matchers were
fixed in v1.59.0, the guard's main effect was a long tail of false
positives on legitimate Bash commands whose source bytes happened to
contain a kit-path token (heredoc bodies, JSON payloads, `python3 -c`
quoted code, `cd kit && git describe`).

This hook now does one thing only: block irreversible Bash operations
against the kit -- recursive removal of kit directories, force-push to
kit main. PR review is the canonical gate for everything else.

Last-resort override: SKIP_KIT_GUARD=1.
"""
import json
import os
import re
import sys

KIT_DIR = os.path.expanduser("~/doe-starter-kit")
BLOCK_MSG = (
    "GUARDRAIL: Destructive operation against ~/doe-starter-kit blocked. "
    "Recursive removal and force-push to kit main are gated. "
    "Override with SKIP_KIT_GUARD=1 only if this is intentional."
)

# Destructive Bash patterns. The redirect / tee / cd-and-commit / cp / mv
# patterns from earlier kit versions were retired in v1.60.0 because their
# false-positive rate (heredoc bodies, JSON payloads, downstream string
# mentions on the same command line) outweighed the marginal safety they
# offered over PR review. Edits to kit working-tree files now flow freely;
# only irreversible operations are gated here.
KIT_DESTRUCTIVE_PATTERNS = [
    # Recursive removal of a kit path: `rm -rf ~/doe-starter-kit`,
    # `rm -fr ~/doe-starter-kit/directives`, etc. The `-r` or `-R` flag
    # makes this irrecoverable for the working tree.
    r'\brm\s+(?:-[a-zA-Z]*[rR][a-zA-Z]*\s+|--recursive\s+)[^|;&]*doe-starter-kit',
    # Force-push that mentions the kit path explicitly. Catches both
    # `--force` / `--force-with-lease` and `-f`.
    r'\bgit\s+push\s+(?:--force(?:-with-lease)?|-f)\b[^|;&]*doe-starter-kit',
]


def main():
    # Single escape valve. Set when an operator genuinely needs to perform
    # a destructive action (e.g. emergency rollback).
    if os.environ.get("SKIP_KIT_GUARD") == "1":
        print(json.dumps({"decision": "allow"}))
        return

    event = json.load(sys.stdin)
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    if tool_name == "Bash":
        command = tool_input.get("command", "") or ""
        # Force-push from inside the kit dir doesn't need to mention the
        # kit path explicitly. Catch that case too.
        cwd_inside = _cwd_inside_kit()
        if cwd_inside and re.search(
            r'\bgit\s+push\s+(?:--force(?:-with-lease)?|-f)\b',
            command,
        ):
            print(json.dumps({"decision": "block", "reason": BLOCK_MSG}))
            return
        for pattern in KIT_DESTRUCTIVE_PATTERNS:
            if re.search(pattern, command):
                print(json.dumps({"decision": "block", "reason": BLOCK_MSG}))
                return

    print(json.dumps({"decision": "allow"}))


def _cwd_inside_kit():
    try:
        cwd = os.path.realpath(os.getcwd())
    except (FileNotFoundError, OSError):
        return False
    return cwd == KIT_DIR or cwd.startswith(KIT_DIR + os.sep)


if __name__ == "__main__":
    main()
