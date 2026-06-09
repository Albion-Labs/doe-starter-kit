"""Hook: Block dangerous bash commands.

Two classes of dangerous patterns:

* SUBSTRING -- matched as a case-insensitive substring of the command.
  Right for invariant tokens that should never appear in any context
  (e.g. `rm -rf /`, `DROP TABLE`, fork bombs).

* ASSIGNMENT -- env-var names that grant privileged bypasses. Matched only
  when the command actually ASSIGNS the variable (followed by `=`),
  not when it merely mentions the name. This avoids false positives on
  documentation, grep, test commands, or quoted strings that reference
  the bypass flag without setting it.
"""
import json
import re
import sys

SUBSTRING_DANGEROUS = [
    "DROP TABLE", "DROP DATABASE", "TRUNCATE",
    "DISABLE ROW LEVEL SECURITY",
    "supabase db reset",
    "emptyBucket",
    ":(){ :|:& };:", "fork bomb",
    "> /dev/sda", "mkfs.", "dd if=",
]
# NOTE: `.delete()` / `deleteMany()` were removed from the substring list — as bare
# substrings they blocked ordinary ORM calls, tests, and `grep ".delete()"`. They are
# accident-prevention, not a security boundary; the false-positive cost outweighed the
# benefit. Recursive-force `rm` is handled by _is_dangerous_rm below (flag-order- and
# whitespace-insensitive) rather than fixed substrings like "rm -rf /".

# Recursive-force rm targeting one of these (after stripping quotes) is blocked.
_DANGEROUS_RM_TARGETS = {"/", "~", ".", "/*", "~/*", "*"}


def _is_dangerous_rm(command):
    """True if the command runs `rm` recursively AND forcefully against a
    catastrophic target (/, ~, ., *), regardless of flag order, spacing, or
    quoting. Catches `rm -rf /`, `rm -fr /`, `rm -r -f /`, `rm  -rf  "/"`, etc.
    A specific path like `rm -rf ./build` is NOT flagged.
    """
    for m in re.finditer(r'(?:^|[\s;&|(])rm\s+([^;&|\n]*)', command):
        recursive = force = False
        targets = []
        for tok in m.group(1).split():
            if tok.startswith("--"):
                recursive = recursive or tok == "--recursive"
                force = force or tok == "--force"
            elif tok.startswith("-"):
                chars = tok[1:].lower()
                recursive = recursive or "r" in chars
                force = force or "f" in chars
            else:
                targets.append(tok.strip("'\""))
        if recursive and force and any(t in _DANGEROUS_RM_TARGETS for t in targets):
            return True
    return False

# Privileged bypass env vars. The AI must not autonomously set these; the
# human gets to approve. Substring-mentioning the names (in docs, grep,
# error messages, test cases) is fine -- only assignment is dangerous.
ASSIGNMENT_DANGEROUS = [
    "SKIP_REVIEW_GATE",     # Adversarial-review bypass
    "SKIP_CONTRACT_CHECK",  # Contract-check bypass
    "SKIP_SIGNOFF_CHECK",   # Sign-off check bypass
    "BYPASS_BLOCK",         # block_unnecessary_admin_merge bypass (must be human-set)
]


def main():
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "") or ""
    lowered = command.lower()

    if _is_dangerous_rm(command):
        print(json.dumps({
            "decision": "block",
            "reason": "GUARDRAIL: Blocked recursive-force rm against a catastrophic target (/, ~, ., *).",
        }))
        return

    for pattern in SUBSTRING_DANGEROUS:
        if pattern.lower() in lowered:
            print(json.dumps({
                "decision": "block",
                "reason": f"GUARDRAIL: Blocked dangerous command containing '{pattern}'.",
            }))
            return

    for var in ASSIGNMENT_DANGEROUS:
        # Match as `VAR=` (possibly preceded by `export `, possibly with
        # surrounding whitespace). Reject only assignments, not mentions.
        for m in re.finditer(rf'(?:^|[\s;&|])(?:export\s+)?{re.escape(var)}\s*=', command):
            # Heuristic quote-context check: skip the match if it sits inside
            # a quoted string (echo / printf / sed / grep arguments commonly
            # mention the var name without setting it). Counts unescaped
            # quotes preceding the match position; odd count => inside a
            # quoted region. Imperfect for nested or here-doc cases, but
            # covers the dominant false-positive class.
            before = command[:m.start()]
            single_q = before.count("'") - before.count("\\'")
            double_q = before.count('"') - before.count('\\"')
            if single_q % 2 == 1 or double_q % 2 == 1:
                continue
            print(json.dumps({
                "decision": "block",
                "reason": (
                    f"GUARDRAIL: Setting {var} bypasses a review gate. "
                    f"This must be set by the human, not the AI. Ask the user to run the command "
                    f"with the env var, or have them approve via a different channel."
                ),
            }))
            return

    sys.exit(0)


if __name__ == "__main__":
    main()
