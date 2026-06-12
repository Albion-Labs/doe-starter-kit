"""Hook: Block gh pr create on feature branches unless adversarial review
passed for current HEAD and all steps in ## Current are complete.

Only applies to feature/* branches. Housekeeping, wrap, and other non-feature
branches pass through freely -- process improvements shouldn't be blocked by
incomplete feature work.

Cross-project guard (v1.61.4): if the Bash command starts with
`cd <path> &&` and the path resolves outside the hook's project tree, the
gate passes through. This handles cross-project `gh pr create` from one
project's harness targeting a different repo (e.g. a consumer project editing the kit) --
the hook's release-readiness checks don't apply to a different project.

Checks (feature/* branches only):
1. All steps in tasks/todo.md ## Current must be [x]. Prevents mid-feature PRs
   which create merge/rebase overhead. PRs are created at retro only.
2. Review artifact at .tmp/review-passed-<branch>.json (written by
   execution/record_review_result.py). Must exist and reviewed_sha must match
   current HEAD -- stale reviews are rejected.

Bypass (human-only): export SKIP_REVIEW_GATE=1 in the shell before
launching the session. The hook reads the env var only -- an inline
`SKIP_REVIEW_GATE=1 gh pr create` assignment never reaches the hook
(hooks are siblings of the Bash tool, not children), and
block_dangerous_commands blocks the AI from writing that assignment
anyway (ASSIGNMENT list, v1.60.1).

v1.71.1 (issue #107): branch is resolved before (and independently of)
HEAD, so unborn-HEAD repos and worktrees on non-feature branches pass
through instead of tripping the fail-closed arm; the trigger matches an
actual `gh pr create` invocation at a statement position rather than the
phrase anywhere in the command string.

v1.71.4 (issue #107 class, pinned by proof corpus fault F18): git state
resolves from the first candidate that has any -- $CLAUDE_PROJECT_DIR,
then the event's cwd (the shell the command actually runs in). Sessions
whose project dir is not a git repo at all (background jobs anchor it to
$HOME; cross-repo sessions point it elsewhere) previously took the
fail-closed arm on EVERY `gh pr create`, including fix/* and
housekeeping/* branches the gate does not gate. The fail-closed block
for genuinely unreadable git state (no candidate resolves) is retained
and pinned by proof corpus fault F15.
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def _resolve_root_and_branch(event):
    """Return (root, branch) from the first candidate with readable git
    state: $CLAUDE_PROJECT_DIR, then the event's cwd. (None, None) when
    nothing resolves -- the caller fail-closes. $CLAUDE_PROJECT_DIR stays
    first so every existing anchoring behaviour (v1.62.2/v1.63.0) is
    unchanged whenever it IS a repo; the event cwd is strictly a fallback.
    Process cwd is used only when neither is present (legacy fallback) --
    falling back to it when $CLAUDE_PROJECT_DIR is set but unreadable
    would let an unrelated checkout answer for the project (F15).
    """
    candidates = []
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if project_dir:
        candidates.append(Path(project_dir))
    event_cwd = event.get("cwd")
    if event_cwd:
        candidates.append(Path(event_cwd))
    if not candidates:
        candidates.append(Path.cwd())
    for root in candidates:
        try:
            branch = subprocess.check_output(
                ["git", "-C", str(root), "branch", "--show-current"],
                text=True, stderr=subprocess.DEVNULL,
            ).strip()
            return root, branch
        except (subprocess.CalledProcessError, OSError):
            continue
    return None, None


def check_steps_complete(root: Path):
    """Return (ok, message). ok=True if all steps complete or no steps exist."""
    todo_path = root / "tasks" / "todo.md"
    if not todo_path.exists():
        return True, ""

    lines = todo_path.read_text().splitlines()
    in_current = False
    total = 0
    done = 0

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("## Current"):
            in_current = True
            continue
        if in_current and stripped.startswith("## "):
            break
        if in_current and re.match(r"\d+[a-d]?\.\s+\[", stripped):
            total += 1
            if re.match(r"\d+[a-d]?\.\s+\[x\]", stripped):
                done += 1

    if total == 0:
        return True, ""
    if done < total:
        return False, f"{done}/{total} steps complete -- finish all steps before creating PR"
    return True, ""


def main():
    event = json.load(sys.stdin)
    tool_input = event.get("tool_input", {})
    command = tool_input.get("command", "")

    # v1.71.1: match an actual invocation at a statement position (start of
    # command or after a separator), optionally preceded by env-var
    # assignments. The previous substring match also fired on the PHRASE
    # appearing inside quoted text -- PR bodies, issue comments, heredoc
    # documentation -- gating commands that create no PR at all.
    if not re.search(
        r'(?:^|[\n;&|])\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*gh\s+pr\s+create\b',
        command,
    ):
        sys.exit(0)

    if os.environ.get("SKIP_REVIEW_GATE") == "1":
        sys.exit(0)

    # Cross-project guard: if the command starts with `cd <path> &&` and the
    # target resolves outside this hook's cwd, the gate doesn't apply.
    cd_match = re.match(r'^\s*cd\s+(\S+)\s*&&', command)
    if cd_match:
        target = os.path.expanduser(cd_match.group(1).strip("'\""))
        if os.path.isdir(target):
            target_real = os.path.realpath(target)
            cwd_real = os.path.realpath(os.getcwd())
            if target_real != cwd_real and not target_real.startswith(cwd_real + os.sep):
                sys.exit(0)

    # v1.71.1 (issue #107): resolve the BRANCH first, on its own.
    # `git branch --show-current` succeeds on unborn-HEAD repos (zero
    # commits) and in worktrees (.git is a file), where `rev-parse HEAD`
    # does not.
    # v1.71.4: resolution falls back from $CLAUDE_PROJECT_DIR to the
    # event's cwd (see _resolve_root_and_branch); fail-closed only when
    # NO candidate has readable git state (F15).
    root, branch = _resolve_root_and_branch(event)
    if root is None:
        print(json.dumps({
            "decision": "block",
            "reason": (
                "GUARDRAIL: Could not determine git state. "
                "Blocking PR creation as a precaution. "
                "Bypass (human-only): export SKIP_REVIEW_GATE=1 "
                "in the shell before launching the session."
            ),
        }))
        return
    project_root = str(root)

    # Only gate feature branches. Housekeeping/wrap/fix/other branches --
    # and detached HEAD (empty string) -- pass freely, with no need for a
    # resolvable HEAD commit.
    if not branch.startswith("feature/"):
        sys.exit(0)

    # feature/* only: HEAD is required to verify review freshness.
    try:
        head_sha = subprocess.check_output(
            ["git", "-C", project_root, "rev-parse", "HEAD"],
            text=True, stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, OSError):
        print(json.dumps({
            "decision": "block",
            "reason": (
                "GUARDRAIL: feature branch has no commits -- cannot verify "
                "a review against HEAD. Commit the work, run /review, then "
                "create the PR. Bypass (human-only): export SKIP_REVIEW_GATE=1 "
                "in the shell before launching the session."
            ),
        }))
        return

    # Gate 1: All steps must be complete (no mid-feature PRs)
    steps_ok, steps_msg = check_steps_complete(root)
    if not steps_ok:
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"GUARDRAIL: {steps_msg}. "
                "No mid-feature PRs -- PRs are created at retro only. "
                "Bypass (human-only): export SKIP_REVIEW_GATE=1 "
                "in the shell before launching the session."
            ),
        }))
        return

    # Gate 2: Adversarial review must have passed for current HEAD.
    # Artifact path is anchored to the SAME resolved root as the git state
    # so reader and writer can never disagree -- a stale-looking "no
    # artifact" block under shell drift is the same false-fail class as
    # the silent false-pass v1.63.0 fixes.
    artifact = root / ".tmp" / f"review-passed-{branch}.json"

    if not artifact.exists():
        print(json.dumps({
            "decision": "block",
            "reason": (
                "GUARDRAIL: Adversarial review required before creating PR. "
                "Run /review first. Bypass (human-only): export SKIP_REVIEW_GATE=1 "
                "in the shell before launching the session."
            ),
        }))
        return

    try:
        data = json.loads(artifact.read_text())
        reviewed_sha = data.get("reviewed_sha", "")
    except (json.JSONDecodeError, KeyError):
        print(json.dumps({
            "decision": "block",
            "reason": (
                "GUARDRAIL: Review artifact is corrupted. "
                "Re-run /review. Bypass (human-only): export SKIP_REVIEW_GATE=1 "
                "in the shell before launching the session."
            ),
        }))
        return

    if reviewed_sha != head_sha:
        print(json.dumps({
            "decision": "block",
            "reason": (
                f"GUARDRAIL: Review is stale (reviewed {reviewed_sha[:8]}, "
                f"HEAD is {head_sha[:8]}). Re-run /review. "
                "Bypass (human-only): export SKIP_REVIEW_GATE=1 "
                "in the shell before launching the session."
            ),
        }))
        return

    sys.exit(0)


if __name__ == "__main__":
    main()
