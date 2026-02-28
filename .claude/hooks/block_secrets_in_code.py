"""Hook: Block writes that contain potential API keys or secrets."""
import json, re, sys

SECRET_PATTERNS = [
    r'(?:sk|pk|api|key|secret|token|password|auth)[-_]?[a-zA-Z0-9]{20,}',
    r'(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}',
    r'xox[bpors]-[A-Za-z0-9-]+',
    r'AKIA[0-9A-Z]{16}',
]

def main():
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    content = tool_input.get("content", "") or tool_input.get("file_text", "")
    path = tool_input.get("file_path", "") or tool_input.get("path", "")
    if path.endswith(".env"):
        print(json.dumps({"decision": "allow"}))
        return
    for pattern in SECRET_PATTERNS:
        if re.search(pattern, content):
            print(json.dumps({
                "decision": "block",
                "reason": f"GUARDRAIL: Potential secret detected in {path}. Secrets must only be stored in .env."
            }))
            return
    print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
