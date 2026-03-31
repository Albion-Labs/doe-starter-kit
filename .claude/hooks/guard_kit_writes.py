"""Hook: Block direct writes to ~/doe-starter-kit. Use /sync-doe instead."""
import json, os, sys, pathlib

FLAG_FILE = pathlib.Path(__file__).parent.parent.parent / ".tmp" / ".sync-doe-active"

def main():
    # Skip valves
    if os.environ.get("SKIP_KIT_GUARD") == "1":
        print(json.dumps({"decision": "allow"}))
        return
    if FLAG_FILE.exists():
        print(json.dumps({"decision": "allow"}))
        return

    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    path = tool_input.get("file_path", "") or tool_input.get("path", "")

    kit_dir = os.path.expanduser("~/doe-starter-kit")
    if path.startswith(kit_dir) or "/doe-starter-kit/" in path:
        print(json.dumps({
            "decision": "block",
            "reason": "GUARDRAIL: Direct writes to ~/doe-starter-kit are blocked. "
                       "Make changes in the project repo first, then use /sync-doe to push them to the kit. "
                       "Override with SKIP_KIT_GUARD=1 for kit-native work (you must tag/release manually)."
        }))
    else:
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
