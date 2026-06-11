"""PostToolUse hook: Run plan freshness check when .claude/plans/*.md files are read.

Fires on Read of a plan file. Checks version conflicts, dead file references,
CLAUDE.md drift, and plan age, surfacing warnings inline.

v1.71.2 (never-alive fix): the original compared tool_name against lowercase
"read" -- real events carry "Read" -- so the hook exited early on every
invocation since it shipped. Same casing class as the v1.59.0 matcher fix.
Also hardened per v1.62.2/v1.63.0: the freshness subprocess is anchored to
$CLAUDE_PROJECT_DIR (script path AND cwd) instead of a relative path that
silently broke under shell drift, and the no-opinion path is a silent
sys.exit(0) per the v1.61.3 convention.
"""
import json
import os
import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        return Path(project_dir)
    return Path.cwd()


def main():
    event = json.load(sys.stdin)
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    path = tool_input.get("file_path", "")

    # Only trigger on Read of .claude/plans/*.md files
    if tool_name != "Read" or ".claude/plans/" not in path or not path.endswith(".md"):
        sys.exit(0)

    root = _project_root()
    plan_path = Path(path)
    if not plan_path.is_absolute():
        plan_path = root / plan_path
    if not plan_path.exists():
        sys.exit(0)

    checker = root / "execution" / "check_plan_freshness.py"
    if not checker.exists():
        sys.exit(0)

    try:
        result = subprocess.run(
            [sys.executable, str(checker), str(plan_path)],
            capture_output=True, text=True, timeout=10, cwd=str(root),
        )
    except (OSError, subprocess.SubprocessError):
        sys.exit(0)

    output = (result.stdout or "").strip()
    if result.returncode != 0 and output:
        print(output)
    sys.exit(0)


if __name__ == "__main__":
    main()
