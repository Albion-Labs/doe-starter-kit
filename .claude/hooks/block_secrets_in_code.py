"""Hook: Block writes that contain potential API keys or secrets.

Covers Edit/Write/MultiEdit (every written field: Write `content`/`file_text`,
Edit `new_string`, MultiEdit `edits[].new_string` — plus the file_path check)
AND Bash commands that redirect secret-shaped strings into a file
(`echo SECRET=… >> .env.local`, `cat > config <<EOF SECRET=… EOF`, etc.).
The only file allowed to hold secrets is the local `.env`; every other
`.env.*` variant is blocked outright. Bash redirections targeting any path
receive the same secret-pattern scan.
"""
import json
import re
import sys

SECRET_PATTERNS = [
    r'(?:sk|pk|api|key|secret|token|password|auth)[-_]?[a-zA-Z0-9]{20,}',
    r'(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}',
    r'xox[bpors]-[A-Za-z0-9-]+',
    r'AKIA[0-9A-Z]{16}',
    r'-----BEGIN\s+(RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
    r'://[^/\s]*:.*@',                       # credential-bearing URLs
    r'sbp_[a-zA-Z0-9]{20,}',                 # Supabase service role keys
    r'eyJ[a-zA-Z0-9_-]{20,}\.[a-zA-Z0-9_-]{20,}',  # JWT tokens
]
SECRET_RE = re.compile("|".join(f"(?:{p})" for p in SECRET_PATTERNS))

WRITE_TOOLS = ("Write", "Edit", "MultiEdit")

# Only exact .env is exempt. .env.local, .env.production etc are NOT.
EXEMPT_PATHS = ['.env']
BLOCKED_ENV_VARIANTS = ['.env.local', '.env.production', '.env.staging', '.env.development']

# Bash redirections that write to a file. Captures the command body so the
# secret scan runs against the bytes being written (the redirection target
# might be a variant `.env.X` or any other path).
BASH_REDIRECT_RE = re.compile(
    r'(?:'
    r'>\s*\S+'                  # > file
    r'|>>\s*\S+'                # >> file
    r'|tee\s+(?:-a\s+)?\S+'     # tee [-a] file
    r'|cat\s+>\s*\S+'           # cat > file
    r'|cat\s+>>\s*\S+'          # cat >> file
    r')'
)


def _block(reason):
    print(json.dumps({"decision": "block", "reason": reason}))


def _allow():
    sys.exit(0)


def _basename(path):
    return path.rsplit("/", 1)[-1] if "/" in path else path


def _written_content(tool_input):
    """Every byte the tool would write: Write's content/file_text, Edit's
    new_string, MultiEdit's edits[].new_string. old_string is deliberately
    excluded — it is existing file content, and scanning it would block the
    edit that REMOVES a secret from a file."""
    pieces = [
        tool_input.get("content", "") or "",
        tool_input.get("file_text", "") or "",
        tool_input.get("new_string", "") or "",
    ]
    edits = tool_input.get("edits")
    if isinstance(edits, list):
        for edit in edits:
            if isinstance(edit, dict):
                pieces.append(edit.get("new_string", "") or "")
    return "\n".join(p for p in pieces if p)


def _scan_blocked_env_variant(command):
    """Return the matched .env.* variant if the command writes to one."""
    for variant in BLOCKED_ENV_VARIANTS:
        if re.search(rf'(?:>|>>|tee\s+(?:-a\s+)?)\s*[\'"]?[^\s\'"]*{re.escape(variant)}\b', command):
            return variant
    # Generic .env.<word> check (catches new variants we haven't enumerated).
    m = re.search(r'(?:>|>>|tee\s+(?:-a\s+)?)\s*[\'"]?[^\s\'"]*(\.env\.[A-Za-z0-9_-]+)\b', command)
    if m:
        return m.group(1)
    return None


def main():
    event = json.load(sys.stdin)
    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # ── Edit/Write/MultiEdit branch ──────────────────────────────
    if tool_name in WRITE_TOOLS:
        content = _written_content(tool_input)
        path = tool_input.get("file_path", "") or tool_input.get("path", "") or ""
        basename = _basename(path)

        if basename in EXEMPT_PATHS:
            _allow()
            return
        if basename in BLOCKED_ENV_VARIANTS or (basename.startswith(".env.") and basename not in EXEMPT_PATHS):
            _block(
                f"GUARDRAIL: {basename} must not be committed. Only .env is "
                "allowed (and must be in .gitignore)."
            )
            return
        if SECRET_RE.search(content):
            _block(
                f"GUARDRAIL: Potential secret detected in {path}. Secrets "
                "live in .env only."
            )
            return
        _allow()
        return

    # ── Bash branch ──────────────────────────────────────────────
    if tool_name == "Bash":
        command = tool_input.get("command", "") or ""

        # Block writes to .env variants regardless of content.
        variant = _scan_blocked_env_variant(command)
        if variant:
            _block(
                f"GUARDRAIL: Bash command writes to {variant}. Only .env is "
                "allowed (and must be in .gitignore)."
            )
            return

        # Scan the command body for secret patterns when a redirection is
        # present. We restrict to redirection commands so general logging
        # (`echo SECRET=… # description`) without a file target is allowed.
        if BASH_REDIRECT_RE.search(command) and SECRET_RE.search(command):
            _block(
                "GUARDRAIL: Bash command writes a secret-shaped value to a "
                "file. Secrets live in .env only."
            )
            return
        _allow()
        return

    _allow()


if __name__ == "__main__":
    main()
