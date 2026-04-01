"""Record adversarial review result for PR gate enforcement.

Called by /review after verdict. Writes a pass artifact that
enforce_review_gate.py checks before allowing gh pr create.

Requires Finder subagent findings as proof-of-work -- refuses to
record PASS/PASS_WITH_NOTES unless .tmp/review-finder-{branch}.json
exists, has the correct SHA, and was written within the last 30 min.
"""
import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

STALE_MINUTES = 30


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python3 execution/record_review_result.py "
            "<PASS|PASS_WITH_NOTES|FAIL>"
        )
        sys.exit(1)

    verdict = sys.argv[1].upper().replace(" ", "_")
    if verdict not in ("PASS", "PASS_WITH_NOTES", "FAIL"):
        print(f"Invalid verdict: {verdict}. Must be PASS, PASS_WITH_NOTES, or FAIL.")
        sys.exit(1)

    branch = subprocess.check_output(
        ["git", "branch", "--show-current"], text=True
    ).strip()
    head_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], text=True
    ).strip()

    artifact = Path(".tmp") / f"review-passed-{branch}.json"

    if verdict == "FAIL":
        artifact.unlink(missing_ok=True)
        print("Review FAIL recorded. Fix issues and re-run /review.")
        return

    # --- Proof-of-work: require Finder subagent findings ---
    finder_file = Path(".tmp") / f"review-finder-{branch}.json"

    if not finder_file.exists():
        print(
            "ERROR: No Finder findings found at "
            f".tmp/review-finder-{branch}.json\n"
            "The Finder subagent must run and persist findings before "
            "a PASS verdict can be recorded. Run /review with subagents."
        )
        sys.exit(1)

    try:
        finder_data = json.loads(finder_file.read_text())
    except json.JSONDecodeError:
        print("ERROR: Finder findings file is corrupted. Re-run /review.")
        sys.exit(1)

    # SHA must match current HEAD
    finder_sha = finder_data.get("reviewed_sha", "")
    if finder_sha != head_sha:
        print(
            f"ERROR: Finder findings are stale "
            f"(reviewed {finder_sha[:8]}, HEAD is {head_sha[:8]}). "
            "Re-run /review."
        )
        sys.exit(1)

    # Timestamp must be within STALE_MINUTES
    try:
        ts = datetime.fromisoformat(finder_data["timestamp"])
        age = datetime.now(timezone.utc) - ts
        if age > timedelta(minutes=STALE_MINUTES):
            mins = int(age.total_seconds() // 60)
            print(
                f"ERROR: Finder findings are {mins} minutes old "
                f"(limit: {STALE_MINUTES}). Re-run /review."
            )
            sys.exit(1)
    except (KeyError, ValueError):
        print("ERROR: Finder findings have no valid timestamp. Re-run /review.")
        sys.exit(1)

    # --- Proof-of-work passed, record verdict ---
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(json.dumps({
        "branch": branch,
        "reviewed_sha": head_sha,
        "verdict": verdict,
        "finder_findings": finder_data.get("findings_summary", ""),
    }, indent=2) + "\n")
    print(f"Review {verdict} recorded for {branch} @ {head_sha[:8]}")


if __name__ == "__main__":
    main()
