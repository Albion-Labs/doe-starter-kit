"""Hook: Block --admin PR merges that don't need admin override.

Recurring AI failure mode: query `gh pr view` shortly after PR creation,
see `mergeStateStatus: UNKNOWN` (GitHub still computing checks), conclude
"PR is blocked," reach for `gh pr merge --admin` reflexively. The block
was transient. Admin override was unnecessary.

This hook intercepts `gh pr merge --admin` before it runs and verifies
whether the override is actually needed by querying the real merge state.

Decision matrix:
* CLEAN -> BLOCK. Admin not needed; drop --admin and retry.
* UNKNOWN -> BLOCK. State still computing; wait 30-60s then re-query.
* BLOCKED -> Surface failing checks. Require BYPASS_BLOCK=1 to proceed.
* DIRTY (conflicts) / BEHIND -> Pass through. gh will refuse below.
* API error -> BLOCK (fail-closed).

BYPASS_BLOCK is in block_dangerous_commands ASSIGNMENT_DANGEROUS so the
AI cannot autonomously set it. Human must export it for legitimate
admin-override scenarios (CI broken for unrelated reasons, urgent ship).
"""
import json
import os
import re
import subprocess
import sys


def _emit_block(reason: str) -> None:
    print(json.dumps({"decision": "block", "reason": reason}))


def _exec_cwd(command: str, event_cwd):
    """Directory the gh queries should run in. gh resolves {owner}/{repo}
    from the cwd's git remote, so inheriting the hook process cwd queries
    the WRONG repo when the intercepted command targets another one. Use
    the event's `cwd`, adjusted for a single leading `cd <dir> &&` / `;`
    prefix on the command itself."""
    base = event_cwd or None
    m = re.match(
        r"""\s*cd\s+(?:"([^"]+)"|'([^']+)'|([^\s;&|]+))\s*(?:&&|;)""",
        command,
    )
    if m:
        target = next(g for g in m.groups() if g)
        target = os.path.expanduser(target)
        if not os.path.isabs(target) and base:
            target = os.path.join(base, target)
        if os.path.isdir(target):
            return target
    return base


def _query_pr_state(pr_number: str, cwd=None):
    """Returns (state, mergeStateStatus, headRefOid, err)."""
    try:
        result = subprocess.run(
            ["gh", "pr", "view", pr_number, "--json", "state,mergeStateStatus,headRefOid"],
            capture_output=True, text=True, timeout=15, cwd=cwd,
        )
        if result.returncode != 0:
            return None, None, None, result.stderr.strip()
        data = json.loads(result.stdout)
        return (
            data.get("state", ""),
            data.get("mergeStateStatus", ""),
            data.get("headRefOid", ""),
            None,
        )
    except Exception as e:
        return None, None, None, str(e)


def _failing_checks(sha: str, cwd=None) -> str:
    """Returns a human-readable summary of non-passing checks on the SHA."""
    try:
        result = subprocess.run(
            [
                "gh", "api", f"repos/{{owner}}/{{repo}}/commits/{sha}/check-runs",
                "--jq",
                '.check_runs[] | select(.conclusion != "success" and .conclusion != "skipped" and .conclusion != null) | "\\(.name): \\(.conclusion)"',
            ],
            capture_output=True, text=True, timeout=15, cwd=cwd,
        )
        out = result.stdout.strip()
        return out or "(no failing check-runs reported -- may be required reviews or unresolved conversations)"
    except Exception:
        return "(could not query check-runs)"


def main() -> None:
    try:
        event = json.load(sys.stdin)
    except Exception:
        sys.exit(0)

    command = event.get("tool_input", {}).get("command", "") or ""

    # Only intercept `gh pr merge ... --admin` -- require --admin to appear
    # AFTER `gh pr merge` in the same STATEMENT (no newline, `;`, `&` or
    # `|` between them). Catches real flag usage while skipping false
    # positives where --admin appears earlier in echo'd documentation
    # cards, heredoc bodies, or unrelated chained commands.
    # [v1.65.1 hotfix: prior naive substring match tripped on heredoc body
    # containing the literal token "--admin" in a confirmation card.]
    # [v1.71.6: the matcher excluded only newline/`;`, so it spanned `&&`
    # and `|` into unrelated chained statements -- `gh pr merge 7 --merge
    # && echo '--admin'` was intercepted despite an admin-free merge.]
    if not re.search(r'gh pr merge[^\n;&|]*--admin\b', command):
        sys.exit(0)

    # Bypass mechanism (env or inline). AI cannot set this autonomously
    # because BYPASS_BLOCK is in block_dangerous_commands ASSIGNMENT_DANGEROUS.
    if os.environ.get("BYPASS_BLOCK") == "1" or re.search(r'(?:^|[\s;&|])BYPASS_BLOCK\s*=\s*1', command):
        sys.exit(0)

    # gh queries must run where the command would run, not where the hook
    # process happens to live (v1.71.6: `cd X && gh pr merge --admin`
    # previously queried the hook cwd's repo).
    exec_cwd = _exec_cwd(command, event.get("cwd"))

    # Resolve PR number: explicit `gh pr merge <N>` or current-branch fallback.
    m = re.search(r'gh pr merge\s+(\d+)', command)
    if m:
        pr_number = m.group(1)
    else:
        try:
            result = subprocess.run(
                ["gh", "pr", "view", "--json", "number", "-q", ".number"],
                capture_output=True, text=True, timeout=10, cwd=exec_cwd,
            )
            pr_number = result.stdout.strip()
            if not pr_number:
                _emit_block(
                    "GUARDRAIL: --admin merge requested but no PR number found and "
                    "current branch has no open PR. Re-run with explicit number: "
                    "`gh pr merge N --admin`."
                )
                return
        except Exception as e:
            _emit_block(
                f"GUARDRAIL: Could not resolve PR number ({e}). "
                "Re-run with explicit number: `gh pr merge N --admin`."
            )
            return

    # Query the authoritative state.
    pr_state, mss, sha, err = _query_pr_state(pr_number, cwd=exec_cwd)
    if pr_state is None:
        _emit_block(
            f"GUARDRAIL: Could not query PR #{pr_number} state ({err}). "
            "Fail-closed: investigate before --admin merging."
        )
        return

    # Closed/merged PRs report UNKNOWN mergeStateStatus -- pass through so
    # gh surfaces the real error (PR closed / already merged).
    if pr_state != "OPEN":
        sys.exit(0)

    if mss == "CLEAN":
        _emit_block(
            f"GUARDRAIL: PR #{pr_number} is CLEAN -- --admin override is NOT "
            f"needed. Drop the --admin flag and retry with a normal merge:\n"
            f"  ALLOW_MERGE=1 gh pr merge {pr_number} --merge\n"
            f"This is the recurring AI mistake the hook exists to catch."
        )
        return

    if mss == "UNKNOWN":
        _emit_block(
            f"GUARDRAIL: PR #{pr_number} mergeStateStatus is UNKNOWN -- GitHub "
            f"is likely still computing checks (this is a TRANSIENT state, not "
            f"a permanent block). Wait 30-60s, then re-query with:\n"
            f"  gh pr view {pr_number} --json mergeStateStatus\n"
            f"before deciding whether --admin is needed."
        )
        return

    if mss == "BLOCKED":
        failing = _failing_checks(sha, cwd=exec_cwd) if sha else "(no SHA available)"
        _emit_block(
            f"GUARDRAIL: PR #{pr_number} is BLOCKED. Non-passing items:\n"
            f"{failing}\n\n"
            f"Verify --admin is the right tool (e.g., unrelated CI breakage, "
            f"urgent ship). If so, the HUMAN must export BYPASS_BLOCK=1 in "
            f"the shell BEFORE launching the session (an inline "
            f"BYPASS_BLOCK=1 assignment is itself blocked by "
            f"block_dangerous_commands), then re-run:\n"
            f"  ALLOW_MERGE=1 gh pr merge {pr_number} --admin --merge"
        )
        return

    # DIRTY (conflicts), BEHIND, HAS_HOOKS, etc. -- not classes the hook can
    # decide on. Pass through; gh will surface the real reason if it refuses.
    sys.exit(0)


if __name__ == "__main__":
    main()
