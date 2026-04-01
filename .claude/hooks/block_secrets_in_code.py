"""Hook: Block writes that contain potential API keys or secrets."""
import json, re, sys

SECRET_PATTERNS = [
    r'(?:sk|pk|api|key|secret|token|password|auth)[-_]?[a-zA-Z0-9]{20,}',
    r'(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}',
    r'xox[bpors]-[A-Za-z0-9-]+',
    r'AKIA[0-9A-Z]{16}',
    r'-----BEGIN\s+(RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
    r'://[^/\s]*:.*@',  # credential-bearing URLs (user:pass@host)
    r'sbp_[a-zA-Z0-9]{20,}',  # Supabase service role keys
    r'eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}',  # JWT tokens
]

# Only exact .env is exempt. .env.local, .env.production etc are NOT.
EXEMPT_PATHS = ['.env']
BLOCKED_ENV_VARIANTS = ['.env.local', '.env.production', '.env.staging', '.env.development']

def main():
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    content = tool_input.get("content", "") or tool_input.get("file_text", "")
    path = tool_input.get("file_path", "") or tool_input.get("path", "")
    basename = path.rsplit("/", 1)[-1] if "/" in path else path
    if basename in EXEMPT_PATHS:
        print(json.dumps({"decision": "allow"}))
        return
    if basename in BLOCKED_ENV_VARIANTS or (basename.startswith(".env.") and basename not in EXEMPT_PATHS):
        print(json.dumps({
            "decision": "block",
            "reason": f"GUARDRAIL: {basename} must not be committed. Only .env is allowed (and must be in .gitignore)."
        }))
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
