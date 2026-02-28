"""Hook: Block dangerous bash commands."""
import json, sys

DANGEROUS = [
    "rm -rf /", "rm -rf ~", "rm -rf .",
    "DROP TABLE", "DROP DATABASE", "TRUNCATE",
    ":(){ :|:& };:", "fork bomb",
    "> /dev/sda", "mkfs.", "dd if=",
]

def main():
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "")
    for pattern in DANGEROUS:
        if pattern.lower() in command.lower():
            print(json.dumps({
                "decision": "block",
                "reason": f"GUARDRAIL: Blocked dangerous command containing '{pattern}'."
            }))
            return
    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
