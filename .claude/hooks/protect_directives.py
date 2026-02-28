"""Hook: Block edits to existing directives/ files. New directives allowed (e.g. during retros)."""
import json, sys

def main():
    event = json.load(sys.stdin)
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})
    path = tool_input.get("file_path", "") or tool_input.get("path", "")
    if "directives/" in path and tool_name in ("write", "edit"):
        print(json.dumps({
            "decision": "block",
            "reason": "GUARDRAIL: Cannot edit existing directives without explicit permission. Show proposed changes to the user and get approval first."
        }))
    else:
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
