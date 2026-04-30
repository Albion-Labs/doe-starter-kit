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
    "rm -rf /", "rm -rf ~", "rm -rf .",
    "DROP TABLE", "DROP DATABASE", "TRUNCATE",
    "DISABLE ROW LEVEL SECURITY",
    "supabase db reset",
    "deleteMany()", ".delete()",
    "emptyBucket",
    ":(){ :|:& };:", "fork bomb",
    "> /dev/sda", "mkfs.", "dd if=",
]

# Privileged bypass env vars. The AI must not autonomously set these; the
# human gets to approve. Substring-mentioning the names (in docs, grep,
# error messages, test cases) is fine -- only assignment is dangerous.
ASSIGNMENT_DANGEROUS = [
    "SKIP_REVIEW_GATE",     # Adversarial-review bypass
    "SKIP_CONTRACT_CHECK",  # Contract-check bypass
    "SKIP_SIGNOFF_CHECK",   # Sign-off check bypass
]


def main():
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "") or ""
    lowered = command.lower()

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

    print(json.dumps({"decision": "allow"}))


if __name__ == "__main__":
    main()
