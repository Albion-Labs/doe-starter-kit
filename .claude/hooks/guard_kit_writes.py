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

# Bash patterns that indicate writing to kit
KIT_BASH_PATTERNS = [
    r'cp\s.*doe-starter-kit',
    r'mv\s.*doe-starter-kit',
    r'cd\s.*doe-starter-kit.*&&.*(?:git\s+(?:commit|add|tag|push)|sed|tee|>)',
    r'>\s*.*doe-starter-kit',
    r'tee\s.*doe-starter-kit',
]

def main():
    # Skip valves
    if os.environ.get("SKIP_KIT_GUARD") == "1":
        print(json.dumps({"decision": "allow"}))
        return
    if FLAG_FILE.exists():
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

    # Check Bash commands for kit write patterns
    if tool_name == "bash":
        command = tool_input.get("command", "")
        for pattern in KIT_BASH_PATTERNS:
            if re.search(pattern, command):
                print(json.dumps({"decision": "block", "reason": BLOCK_MSG}))
                return

    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
