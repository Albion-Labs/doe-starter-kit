#!/usr/bin/env python3
"""PostToolUse hook: auto-stamp completion timestamps on [x] task lines.

When tasks/todo.md is edited and a step is marked [x] without a timestamp,
append *(completed HH:MM DD/MM/YY)* to the end of the line. Idempotent --
already-stamped lines are skipped.

Mirrors the regexes used by execution/audit_claims.py so what we stamp is
exactly what the CI audit (check_task_format) accepts, PLUS lettered
sub-steps (1a., 2b.) which lint_todo's step regexes (\\d+[a-d]?\\.) count
as steps. If audit or lint regexes change, this hook must update in
lockstep.

Closes the most common CI-failure class: [x] without timestamp -> FAIL.
Missing version tag is WARN-only in the audit and is intentionally NOT
addressed here (version is meaningful context for the human; timestamp
is mechanical).

Triggers on Edit / Write / MultiEdit. Stays silent on non-todo files and
on every tool call that doesn't change the stamp count.
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

# Superset of execution/audit_claims.py's _TASK_DONE_RE: the optional
# step prefix also accepts a letter suffix (1a.) to match lint_todo's
# \d+[a-d]?\. step convention. If those regexes change, this hook must
# update in lockstep.
_TASK_DONE_RE = re.compile(
    r"^[\s]*(?:\d+[a-d]?\.\s*)?\[x\]\s*(.+)",
    re.IGNORECASE,
)
_TIMESTAMP_RE = re.compile(
    r"\*\(completed\s+\d{2}:\d{2}\s+\d{2}/\d{2}/\d{2}\)\*"
)
_TIMESTAMP_DATE_ONLY_RE = re.compile(
    r"\*\(completed\s+\d{2}/\d{2}/\d{2}\)\*"
)


def _stamp(now: datetime) -> str:
    return now.strftime("*(completed %H:%M %d/%m/%y)*")


def process(text: str, now: datetime) -> tuple[str, int]:
    """Return (new_text, count_stamped). Idempotent."""
    out_lines = []
    stamped = 0
    for line in text.split("\n"):
        if _TASK_DONE_RE.match(line) and not (
            _TIMESTAMP_RE.search(line) or _TIMESTAMP_DATE_ONLY_RE.search(line)
        ):
            line = line.rstrip() + " " + _stamp(now)
            stamped += 1
        out_lines.append(line)
    return "\n".join(out_lines), stamped


def _resolve_todo_path(file_path: str) -> Path | None:
    """Anchor to $CLAUDE_PROJECT_DIR (v1.62.2 cwd-safety pattern)."""
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    candidates: list[Path] = []
    if project_dir:
        candidates.append(Path(project_dir) / "tasks" / "todo.md")
    if file_path:
        candidates.append(Path(file_path))
    for p in candidates:
        if p.exists():
            return p
    return None


def _stamp_file(path: Path) -> int:
    """Stamp the file in-place. Return count stamped (0 if no change)."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return 0
    new_text, stamped = process(text, datetime.now())
    if stamped == 0 or new_text == text:
        return 0
    try:
        path.write_text(new_text, encoding="utf-8")
    except OSError:
        return 0
    return stamped


def main():
    # Pre-commit safety-net mode: `--pre-commit <path>`. Stamps the file,
    # exits 0. Used by .githooks/pre-commit to catch direct human edits
    # that bypassed the PostToolUse hook (Claude wasn't involved).
    if len(sys.argv) >= 3 and sys.argv[1] == "--pre-commit":
        path = Path(sys.argv[2])
        if path.exists():
            stamped = _stamp_file(path)
            if stamped:
                print(
                    f"stamp_todo_timestamps: stamped {stamped} task "
                    f"line(s) in {path}",
                    file=sys.stderr,
                )
        return

    # PostToolUse mode: read JSON event from stdin.
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError, EOFError):
        return

    tool_input = event.get("tool_input", {})
    file_path = tool_input.get("file_path", "") or ""
    if "todo.md" not in file_path:
        return

    todo_path = _resolve_todo_path(file_path)
    if not todo_path:
        return

    stamped = _stamp_file(todo_path)
    if stamped:
        print(
            f"stamp_todo_timestamps: stamped {stamped} task line(s) "
            f"in {todo_path.name}",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
