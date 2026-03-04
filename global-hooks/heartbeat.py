"""PostToolUse hook: update session heartbeat every 2 minutes during active waves.

Runs after every tool use. Uses a temp file to track last heartbeat time
so we only shell out to multi_agent.py when >2 minutes have elapsed.
Only active when a wave is running and this session is registered.
"""
import json
import os
import sys
import subprocess
import time
from pathlib import Path

PROJECT_ROOT = Path.cwd()
SESSIONS_FILE = PROJECT_ROOT / ".tmp" / "waves" / "sessions.json"
HEARTBEAT_INTERVAL = 30  # seconds


def main():
    # Accept and discard stdin (hook protocol requires it)
    json.load(sys.stdin)

    # Quick exit: no wave active
    if not SESSIONS_FILE.exists():
        print(json.dumps({}))
        return

    # Check elapsed time via temp file (avoids reading sessions.json on every call)
    pid = os.getpid()
    marker = PROJECT_ROOT / ".tmp" / f".last-heartbeat-{pid}"

    now = time.time()
    if marker.exists():
        try:
            last = float(marker.read_text().strip())
            if now - last < HEARTBEAT_INTERVAL:
                print(json.dumps({}))
                return
        except (ValueError, OSError):
            pass

    # Time to heartbeat — write marker and fire the update
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(str(now))

    subprocess.run(
        ["python3", str(Path.home() / ".claude" / "scripts" / "multi_agent.py"), "--heartbeat"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    print(json.dumps({}))


if __name__ == "__main__":
    main()
