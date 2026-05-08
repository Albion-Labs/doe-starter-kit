"""Hook: Block edits to existing directives/ files.

Covers Edit/Write/MultiEdit (file_path check) AND Bash commands that
redirect into or rewrite a file under directives/ (command string check).
New directives are still allowed (e.g., during retros) -- only edits to
existing files in directives/ (or .githooks/) trigger the guard via the
file_path branch. Existence is checked at hook time, so a Write that
creates a brand-new directive passes through.
The Bash branch is conservative: it blocks any redirected write or
in-place edit that mentions a directives/ path. New-vs-existing detection
on Bash arguments is a heuristic loss, so the Bash branch defaults to
block-all on directives/ paths.
"""
import json
import re
import sys
from pathlib import Path

WRITE_TOOLS = ("Write", "Edit", "MultiEdit")

# Bash patterns that write to or edit files under directives/. Each entry
# names an unambiguous write operation -- redirect, in-place edit, remove,
# move, copy. sed/awk in-place edits scan up to the next pipe/semicolon
# so macOS-style empty backup args (`sed -i ''`) don't slip through. The
# `>` redirect pattern allows an optional `|` immediately after the angle
# bracket so `>|` (noclobber-override) is also caught. mv/cp accept either
# whitespace OR `/` before `directives/` so `mv x ./directives/y.md` and
# absolute paths (`mv x /Users/foo/proj/directives/y.md`) are not bypasses.
#
# The `python3 -c "...directives/..."` pattern was retired in v1.60.0 --
# it matched ANY Python one-liner that referenced `directives/`, including
# read-only (`os.listdir`), data-only (JSON payloads in test scaffolding),
# and string-literal mentions. The false-positive rate during legitimate
# scripting work was high enough to make `python3 -c` near-unusable from
# Claude Code. The narrow bypass route it closed (a Python one-liner that
# `open()`s a directive in write mode) is theoretical; in practice writes
# go through Edit/Write/MultiEdit (file-path branch) or Bash redirects
# (covered above), and PR review is the canonical gate for kit work.
BASH_DIRECTIVE_PATTERNS = [
    r'>\|?\s*[\'"]?[^\s\'"|;&<>]*directives/',      # cat ... > directives/x.md (and >| variant)
    r'>>\s*[\'"]?[^\s\'"|;&<>]*directives/',        # echo ... >> directives/x.md
    r'\btee\s+(?:-a\s+)?[^\s|;&]*directives/',      # tee [-a] directives/x.md
    r'\bsed\s+-i\b[^|;&]*directives/',              # sed -i [args] directives/x.md
    r'\bawk\s+-i\s+inplace\b[^|;&]*directives/',    # awk -i inplace ... directives/x.md
    r'\brm\s+[^|;&]*directives/',                   # rm directives/x.md
    r'\bmv\s+[^|;&]*[\s/]directives/',              # mv X directives/x.md (incl. ./directives/)
    r'\bcp\s+[^|;&]*[\s/]directives/',              # cp X directives/x.md (incl. ./directives/)
]


def _block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))


def _allow():
    sys.exit(0)


def main():
    event = json.load(sys.stdin)
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # File-path branch: Edit/Write/MultiEdit on an EXISTING path under
    # directives/ or .githooks/. Writes that create a new file pass through
    # so retros can add fresh directives without ceremony; only edits to
    # already-tracked files trigger the guard.
    if tool_name in WRITE_TOOLS:
        path = tool_input.get("file_path", "") or tool_input.get("path", "")
        if (
            ("directives/" in path or ".githooks" in path)
            and Path(path).exists()
        ):
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
