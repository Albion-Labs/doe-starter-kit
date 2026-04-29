"""Hook: Block direct writes to ~/doe-starter-kit. Use /sync-doe instead.

Covers Write/Edit tools (file_path check) AND Bash commands that write to
or commit in the kit directory (command string check). The only allowed path
to kit main is /sync-doe, which sets a flag file to bypass this guard.
"""
import json, os, re, sys, pathlib

FLAG_FILE = pathlib.Path(__file__).parent.parent.parent / ".tmp" / ".sync-doe-active"
KIT_DIR = os.path.expanduser("~/doe-starter-kit")
BLOCK_MSG = (
    "GUARDRAIL: Direct writes to ~/doe-starter-kit are blocked. "
    "Make changes in the project repo first, then use /sync-doe to push them to the kit. "
    "Override with SKIP_KIT_GUARD=1 (you must tag/release manually)."
)

# Bash patterns that indicate writing to kit. Redirect (`>`, `>>`) and tee
# patterns require the kit path to follow the operator with no whitespace or
# Bash word-boundary chars in between -- otherwise heredoc bodies, JSON
# payloads, or downstream string mentions of the kit path on the same line
# trip a false positive (e.g. `cat > /tmp/foo.json <<EOF { "p": "~/doe-...
# starter-kit" } EOF`). cp/mv stay broad because their first kit-path
# argument is the destination -- broadness there is the safe default.
# cd-and-then-write keeps its `&& git commit|sed|tee|>` suffix gate.
KIT_BASH_PATTERNS = [
    r'cp\s.*doe-starter-kit',
    r'mv\s.*doe-starter-kit',
    r'cd\s.*doe-starter-kit.*&&.*(?:git\s+(?:commit|add|tag|push)|sed|tee|>)',
    r'>\|?\s*[\'"]?[^\s\'"|;&<>]*doe-starter-kit',  # > path (and >| noclobber-override)
    r'>>\s*[\'"]?[^\s\'"|;&<>]*doe-starter-kit',    # >> path
    r'\btee\s+(?:-a\s+)?[^\s|;&]*doe-starter-kit',  # tee [-a] path
]

def main():
    # Skip valves
    if os.environ.get("SKIP_KIT_GUARD") == "1":
        print(json.dumps({"decision": "allow"}))
        return
    if FLAG_FILE.exists():
        print(json.dumps({"decision": "allow"}))
        return
    # Cwd-aware early-return: when working from inside the kit (e.g. on a
    # kit feature branch), the file-level guard is performative -- the kit's
    # `.githooks/pre-commit` 'no direct-to-main' hook plus PR review are the
    # canonical gate. From outside the kit (cwd in monty/cortex/etc.) the
    # guard's full behaviour is preserved.
    try:
        cwd = os.path.realpath(os.getcwd())
    except (FileNotFoundError, OSError):
        cwd = ""
    if cwd and (cwd == KIT_DIR or cwd.startswith(KIT_DIR + os.sep)):
        print(json.dumps({"decision": "allow"}))
        return

    event = json.load(sys.stdin)
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # Check Write/Edit tools via file path
    path = tool_input.get("file_path", "") or tool_input.get("path", "")
    if path and (path.startswith(KIT_DIR) or "/doe-starter-kit/" in path):
        print(json.dumps({"decision": "block", "reason": BLOCK_MSG}))
        return

    # Check Bash commands for kit write patterns. Tool name is case-sensitive
    # ("Bash") -- the lowercase form does not match Claude Code's actual Tool
    # name string.
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        for pattern in KIT_BASH_PATTERNS:
            if re.search(pattern, command):
                print(json.dumps({"decision": "block", "reason": BLOCK_MSG}))
                return

    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
