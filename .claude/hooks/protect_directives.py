"""Hook: Block edits to existing directives/ files.

Covers Edit/Write/MultiEdit (file_path check) AND Bash commands that
redirect into or rewrite a file under directives/ (command string check).
New directives are still allowed (e.g., during retros) -- only edits to
existing files in directives/ trigger the guard via the file_path branch.
The Bash branch is conservative: it blocks any redirected write or
in-place edit that mentions a directives/ path.
"""
import json
import re
import sys

WRITE_TOOLS = ("Write", "Edit", "MultiEdit")

# Bash patterns that write to or edit files under directives/. The patterns
# are deliberately broad — false positives are easier to override than missed
# bypasses. sed/awk in-place edits scan up to the next pipe/semicolon so
# macOS-style empty backup args (`sed -i ''`) don't slip through.
BASH_DIRECTIVE_PATTERNS = [
    r'>\s*[\'"]?[^\s\'"|;&<>]*directives/',         # cat ... > directives/x.md
    r'>>\s*[\'"]?[^\s\'"|;&<>]*directives/',        # echo ... >> directives/x.md
    r'\btee\s+(?:-a\s+)?[^\s|;&]*directives/',      # tee [-a] directives/x.md
    r'\bsed\s+-i\b[^|;&]*directives/',              # sed -i [args] directives/x.md
    r'\bawk\s+-i\s+inplace\b[^|;&]*directives/',    # awk -i inplace ... directives/x.md
    r'\brm\s+[^|;&]*directives/',                   # rm directives/x.md
    r'\bmv\s+[^|;&]*\sdirectives/',                 # mv X directives/x.md
    r'\bcp\s+[^|;&]*\sdirectives/',                 # cp X directives/x.md
    r'\bpython3?\s+-c\s+[\'"][^\'"]*directives/',   # python -c "...directives/..."
]


def _block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))


def _allow():
    print(json.dumps({"decision": "allow"}))


def main():
    event = json.load(sys.stdin)
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # File-path branch: Edit/Write/MultiEdit on a path under directives/ or .githooks/
    if tool_name in WRITE_TOOLS:
        path = tool_input.get("file_path", "") or tool_input.get("path", "")
        if "directives/" in path or ".githooks" in path:
            _block(
                "GUARDRAIL: Editing existing directives requires explicit "
                "permission. Show the proposed changes to the user and get "
                "approval first."
            )
            return
        _allow()
        return

    # Bash branch: scan the command string for redirected writes targeting
    # files under directives/. The matcher is conservative — false positives
    # are easier to override than missed bypasses.
    if tool_name == "Bash":
        command = tool_input.get("command", "") or ""
        for pattern in BASH_DIRECTIVE_PATTERNS:
            if re.search(pattern, command):
                _block(
                    "GUARDRAIL: Bash command writes to directives/. Use "
                    "Edit/Write tools for directive changes so the review "
                    "trail is preserved, and get user approval before "
                    "modifying existing directive files."
                )
                return
        _allow()
        return

    _allow()


if __name__ == "__main__":
    main()
