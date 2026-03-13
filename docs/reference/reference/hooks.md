# Hooks — Automatic Guardrails

Hooks are scripts that run automatically at specific moments — before Claude edits a file, after Claude runs a command, or when you make a git commit. They enforce rules without anyone needing to remember the rules.

Think of them as security cameras. They're always watching, always enforcing. You don't notice them until they catch something.

## Two Systems, One Purpose

DOE uses two separate hook systems. They work differently but serve the same goal: preventing mistakes automatically.

### Claude Code Hooks

These run every time Claude uses a tool (reads a file, writes a file, runs a command). They're configured in `.claude/settings.json` and live in `.claude/hooks/`.

There are two types:

**PreToolUse hooks** run *before* Claude does something. They can block the action entirely:

| Hook | What It Catches |
|------|----------------|
| `protect_directives.py` | Blocks edits to existing files in `directives/`. Claude can create new directives, but it cannot modify existing ones without your explicit permission. |
| `block_secrets_in_code.py` | Scans file content for patterns that look like API keys, tokens, or passwords. Blocks the write if something suspicious is found. The only exception is `.env` — secrets belong there. |
| `block_dangerous_commands.py` | Blocks shell commands that could cause serious damage: `rm -rf /`, `DROP TABLE`, fork bombs, disk formatting commands. |

**PostToolUse hooks** run *after* Claude does something. They don't block — they observe and respond:

| Hook | What It Does |
|------|-------------|
| `copy_plan_to_project.py` | If Claude writes a plan to the global `~/.claude/plans/` directory (which plan mode sometimes does by default), this hook automatically copies it to the project's `.claude/plans/` directory where it belongs. |

### Git Hooks

These run during git operations (committing, pushing). They're configured by running `git config core.hooksPath .githooks` and live in `.githooks/`.

| Hook | When It Runs | What It Does |
|------|-------------|-------------|
| `pre-commit` | Before a commit is saved | Runs the claim audit (`audit_claims.py`) to check project health. Warns about `console.log` in JavaScript files, TODOs without references, and hardcoded localhost URLs. Also runs contract verification to make sure the current step's criteria are checked off. |
| `commit-msg` | After you write a commit message | Strips AI co-authorship trailers (like "Co-authored-by: Claude") from commit messages. This keeps the git history clean — the project's rule is no AI attribution in commits. |

## Configuration

Claude Code hooks are configured in `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "write|create|edit",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/protect_directives.py",
            "description": "Block unilateral writes to directives/"
          },
          {
            "type": "command",
            "command": "python3 .claude/hooks/block_secrets_in_code.py",
            "description": "Block secrets outside .env"
          }
        ]
      },
      {
        "matcher": "bash",
        "hooks": [
          {
            "type": "command",
            "command": "python3 .claude/hooks/block_dangerous_commands.py",
            "description": "Block destructive commands"
          }
        ]
      }
    ]
  }
}
```

The `matcher` field controls when a hook fires:
- `"write|create|edit"` — fires when Claude tries to create or modify a file
- `"bash"` — fires when Claude tries to run a shell command

Each hook receives the tool call details via standard input (as JSON), inspects it, and responds with either `{"decision": "allow"}` or `{"decision": "block", "reason": "..."}`.

## When They Fire

Claude Code hooks run on every single tool call. Most of the time, they allow the action and you never notice them. You only see a hook when it blocks something — and when it does, it tells you exactly what it caught and why.

For example, if Claude accidentally tries to write an API key into a JavaScript file:

```
GUARDRAIL: Potential secret detected in src/js/api-client.js.
Secrets must only be stored in .env.
```

Git hooks run during git operations. The pre-commit hook runs every time you (or Claude) make a commit. The commit-msg hook runs after the commit message is written.

## What to Do When Blocked

When a hook blocks an action, it tells you:
1. **What was caught** — the specific file, command, or content that triggered the block
2. **Why it was blocked** — which rule was violated
3. **What to do instead** — where the content should go, or how to get permission

The fix is usually straightforward:
- Secret detected? Move it to `.env` and reference it with `os.getenv()`
- Directive edit blocked? Tell Claude you approve the edit, and it will ask the hook to allow it
- Dangerous command blocked? Rethink the approach — there's almost always a safer way
- Contract check failed? Mark the criteria as done or fix the failing verification

Do not try to bypass hooks. They exist because real problems happened without them. If a hook is consistently blocking legitimate work, that's a sign the hook's rules need updating — not that the hook should be disabled.

## Creating Your Own Hooks

A hook is a Python script that reads JSON from standard input and prints JSON to standard output. Here's the minimal structure:

```python
"""Hook: Describe what this hook checks."""
import json, sys

def main():
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})

    # Your check logic here
    if something_is_wrong(tool_input):
        print(json.dumps({
            "decision": "block",
            "reason": "Explain what was caught and how to fix it."
        }))
    else:
        print(json.dumps({"decision": "allow"}))

if __name__ == "__main__":
    main()
```

After writing the hook, add it to `.claude/settings.json` with an appropriate matcher.

## Where They Live

- Claude Code hooks: `.claude/hooks/` (configured in `.claude/settings.json`)
- Git hooks: `.githooks/` (activated with `git config core.hooksPath .githooks`)

There is also a global settings file at `~/.claude/settings.json` for hooks that should apply to all projects.

## Related Files

- [CLAUDE.md](claude-md.md) — contains the Guardrails that hooks enforce
- [execution/audit_claims.py](execution-scripts.md) — the health check script run by the pre-commit hook
- [execution/check_contract.py](execution-scripts.md) — the contract validator run by the pre-commit hook
