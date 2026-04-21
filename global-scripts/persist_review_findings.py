"""Persist subagent review findings as proof-of-work for the review gate.

Called by Finder/Adversarial/Referee agents as their mandatory final action.
record_review_result.py checks these files exist before recording a PASS.
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# Worktree-safe: always write to main project root's .tmp/ regardless of cwd.
# Adversarial runs with isolation: worktree, so cwd would otherwise be the
# worktree path, causing the downstream review gate to miss the artifact.
_SCRIPTS_DIR = Path.home() / ".claude" / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))
try:
    from doe_utils import resolve_project_root
except ImportError:
    def resolve_project_root():
        return Path.cwd(), Path.cwd()


def main():
    if len(sys.argv) < 3:
        print(
            "Usage: python3 execution/persist_review_findings.py "
            "<role> <findings_summary>"
        )
        sys.exit(1)

    role = sys.argv[1].lower()
    if role not in ("finder", "adversarial", "referee"):
        print(f"Invalid role: {role}. Must be finder, adversarial, or referee.")
        sys.exit(1)

    findings = sys.argv[2]

    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], text=True
    ).strip()
    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()

    main_root, _ = resolve_project_root()
    artifact = main_root / ".tmp" / f"review-{role}-{branch}.json"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps({
        "role": role,
        "branch": branch,
        "reviewed_sha": sha,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "findings_summary": findings,
    }, indent=2) + "\n")
    print(f"{role.title()} findings persisted for {branch} @ {sha[:8]}")


if __name__ == "__main__":
    main()
