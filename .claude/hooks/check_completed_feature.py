#!/usr/bin/env python3
"""PostToolUse hook: warn when all steps in ## Current are complete.

Fires after Write/Edit. Checks if tasks/todo.md has a feature in
## Current where every step is [x]. If so, prints a warning that
the feature should be moved to ## Done or ## Awaiting Sign-off.

This catches the gap where lint_todo.py (pre-commit) never fires
because todo.md changes haven't been committed yet.
"""

import json
import re
import sys

STEP_DONE_RE = re.compile(r"^\s*\d+[a-d]?\.\s+\[x\]\s+")
STEP_ANY_RE = re.compile(r"^\s*\d+[a-d]?\.\s+\[[ x]\]\s+")
FEATURE_RE = re.compile(r"^###\s+(.*)")
SECTION_RE = re.compile(r"^##\s+(\S+)")
MANUAL_UNCHECKED_RE = re.compile(r"^\s+-\s+\[ \]\s+\[manual\]")


def check():
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return

    tool = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})

    # Only check after edits to todo.md
    file_path = tool_input.get("file_path", "")
    if "todo.md" not in file_path:
        return

    # Find and read the actual todo.md
    from pathlib import Path
    candidates = [
        Path("tasks/todo.md"),
        Path(file_path),
    ]
    todo_path = None
    for p in candidates:
        if p.exists():
            todo_path = p
            break
    if not todo_path:
        return

    text = todo_path.read_text(encoding="utf-8")
    lines = text.splitlines()

    in_current = False
    feature_name = None
    feature_line = 0
    step_done = 0
    step_total = 0
    has_unchecked_manual = False

    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        sm = SECTION_RE.match(stripped)
        if sm:
            # Flush previous feature if in Current
            if in_current and feature_name and step_total > 0 and step_done == step_total:
                dest = "Awaiting Sign-off" if has_unchecked_manual else "Done"
                print(
                    f"\n!! Feature complete but still in ## Current: "
                    f"'{feature_name[:50]}' ({step_done}/{step_total} steps done). "
                    f"Move to ## {dest} now.\n",
                    file=sys.stderr,
                )
            in_current = sm.group(1) == "Current"
            feature_name = None
            step_done = 0
            step_total = 0
            has_unchecked_manual = False
            continue

        if not in_current:
            continue

        fm = FEATURE_RE.match(stripped)
        if fm:
            # Flush previous feature
            if feature_name and step_total > 0 and step_done == step_total:
                dest = "Awaiting Sign-off" if has_unchecked_manual else "Done"
                print(
                    f"\n!! Feature complete but still in ## Current: "
                    f"'{feature_name[:50]}' ({step_done}/{step_total} steps done). "
                    f"Move to ## {dest} now.\n",
                    file=sys.stderr,
                )
            feature_name = fm.group(1)
            feature_line = i
            step_done = 0
            step_total = 0
            has_unchecked_manual = False
            continue

        if STEP_ANY_RE.match(line):
            step_total += 1
            if STEP_DONE_RE.match(line):
                step_done += 1

        if MANUAL_UNCHECKED_RE.match(line):
            has_unchecked_manual = True

    # Flush last feature
    if in_current and feature_name and step_total > 0 and step_done == step_total:
        dest = "Awaiting Sign-off" if has_unchecked_manual else "Done"
        print(
            f"\n!! Feature complete but still in ## Current: "
            f"'{feature_name[:50]}' ({step_done}/{step_total} steps done). "
            f"Move to ## {dest} now.\n",
            file=sys.stderr,
        )


if __name__ == "__main__":
    check()
