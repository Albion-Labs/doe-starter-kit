#!/usr/bin/env python3
"""Gist-backed sync for HQ session data.

Stores session history in a private GitHub Gist so that /hq and /eod
can read it from any machine. One JSON file per project in the Gist.

Usage:
    python3 gist_sync.py --test          # Verify gh auth and Gist access
    python3 gist_sync.py --list          # List all projects in the Gist
    python3 gist_sync.py --read <slug>   # Read one project's data
    python3 gist_sync.py --push --slug <slug> --meta <json> --session <json>
"""

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

GIST_ID_FILE = Path.home() / ".claude" / "hq-gist-id"
SEED_FILENAME = "hq-index.json"


def gh_available():
    """Check if gh CLI is authenticated. Runs: gh auth status"""
    try:
        result = subprocess.run(
            ["gh", "auth", "status"],
            capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_gist_id():
    """Read Gist ID from the local file. Returns None if not set."""
    if GIST_ID_FILE.exists():
        gist_id = GIST_ID_FILE.read_text().strip()
        if gist_id:
            return gist_id
    return None


def create_gist():
    """Create a new private Gist and save the ID locally."""
    seed = json.dumps({"created": _now_iso(), "version": 1}, indent=2)
    # Write seed to a temp file for gh gist create
    tmp = Path("/tmp/hq-gist-seed.json")
    tmp.write_text(seed)
    try:
        result = subprocess.run(
            ["gh", "gist", "create", "--public=false", "--desc",
             "Claude Code HQ - Session History", str(tmp)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"Error creating Gist: {result.stderr.strip()}", file=sys.stderr)
            return None
        # gh gist create outputs the Gist URL
        url = result.stdout.strip()
        gist_id = url.rstrip("/").split("/")[-1]
        GIST_ID_FILE.parent.mkdir(parents=True, exist_ok=True)
        GIST_ID_FILE.write_text(gist_id)
        print(f"Created Gist: {url}")
        return gist_id
    finally:
        tmp.unlink(missing_ok=True)


def ensure_gist():
    """Get existing Gist ID or create a new one."""
    gist_id = get_gist_id()
    if gist_id:
        return gist_id
    return create_gist()


def read_project(gist_id, slug):
    """Read one project's JSON from the Gist. Returns dict or None."""
    filename = f"{slug}.json"
    result = subprocess.run(
        ["gh", "gist", "view", gist_id, "-f", filename],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        return None


def read_all_projects(gist_id):
    """Read all project files from the Gist. Returns dict of slug -> data."""
    result = subprocess.run(
        ["gh", "gist", "view", gist_id, "--raw"],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        print(f"Error reading Gist: {result.stderr.strip()}", file=sys.stderr)
        return {}

    # gh gist view --raw outputs all files. We need to list files first.
    files_result = subprocess.run(
        ["gh", "gist", "view", gist_id, "--json", "files",
         "--jq", ".files[].filename"],
        capture_output=True, text=True, timeout=30
    )
    if files_result.returncode != 0:
        return {}

    projects = {}
    for filename in files_result.stdout.strip().split("\n"):
        filename = filename.strip()
        if not filename or filename == SEED_FILENAME:
            continue
        if not filename.endswith(".json"):
            continue
        slug = filename.removesuffix(".json")
        data = read_project(gist_id, slug)
        if data:
            projects[slug] = data
    return projects


def append_session(gist_id, slug, project_meta, session_data):
    """Append a session to a project's Gist file with dedup.

    Args:
        gist_id: The Gist ID
        slug: Project slug (used as filename)
        project_meta: Dict with name, path, lastUpdated, lifetime, recentSessions
        session_data: The full session wrap JSON
    """
    filename = f"{slug}.json"

    # Read existing project data
    existing = read_project(gist_id, slug)
    if existing is None:
        existing = {
            "name": project_meta.get("name", slug),
            "path": project_meta.get("path", ""),
            "lastUpdated": _now_iso(),
            "sessions": []
        }

    # Dedup: check if session already exists by number
    session_number = session_data.get("footer", {}).get("session", 0)
    existing_numbers = {s.get("number") for s in existing.get("sessions", [])}
    if session_number in existing_numbers:
        print(f"Session {session_number} already exists for {slug}, skipping.")
        return True

    # Update project metadata
    existing["name"] = project_meta.get("name", existing.get("name", slug))
    existing["path"] = project_meta.get("path", existing.get("path", ""))
    existing["lastUpdated"] = _now_iso()
    if "lifetime" in project_meta:
        existing["lifetime"] = project_meta["lifetime"]
    if "recentSessions" in project_meta:
        existing["recentSessions"] = project_meta["recentSessions"]

    # Append session
    existing.setdefault("sessions", []).append({
        "number": session_number,
        "date": session_data.get("metrics", {}).get("date", _now_iso()[:10]),
        "wrapJson": session_data
    })

    # Write back to Gist
    tmp = Path(f"/tmp/hq-gist-{slug}.json")
    tmp.write_text(json.dumps(existing, indent=2))
    try:
        result = subprocess.run(
            ["gh", "gist", "edit", gist_id, "-a", str(tmp)],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            print(f"Error updating Gist: {result.stderr.strip()}", file=sys.stderr)
            return False
        print(f"Pushed session {session_number} for {slug}.")
        return True
    finally:
        tmp.unlink(missing_ok=True)


def _now_iso():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")


def cmd_test():
    """Test gh auth and Gist access."""
    if not gh_available():
        print("FAIL: gh CLI not authenticated. Run 'gh auth login'.")
        return False
    print("OK: gh CLI authenticated.")

    gist_id = get_gist_id()
    if gist_id:
        print(f"OK: Gist ID found: {gist_id}")
        # Verify Gist is accessible
        result = subprocess.run(
            ["gh", "gist", "view", gist_id, "--json", "id", "--jq", ".id"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            print("OK: Gist is accessible.")
        else:
            print(f"WARN: Gist {gist_id} not accessible: {result.stderr.strip()}")
    else:
        print("INFO: No Gist ID set. Will create on first push.")
    return True


def cmd_list(gist_id):
    """List all projects in the Gist."""
    projects = read_all_projects(gist_id)
    if not projects:
        print("No projects found in Gist.")
        return
    for slug, data in sorted(projects.items()):
        session_count = len(data.get("sessions", []))
        updated = data.get("lastUpdated", "unknown")
        print(f"  {slug}: {session_count} sessions (updated {updated})")


def cmd_read(gist_id, slug):
    """Read and display one project's data."""
    data = read_project(gist_id, slug)
    if data is None:
        print(f"Project '{slug}' not found in Gist.")
        return
    print(json.dumps(data, indent=2))


def cmd_push(gist_id, slug, meta_json, session_json):
    """Push a session to the Gist."""
    try:
        meta = json.loads(meta_json)
    except json.JSONDecodeError as e:
        print(f"Invalid meta JSON: {e}", file=sys.stderr)
        return False
    try:
        session = json.loads(session_json)
    except json.JSONDecodeError as e:
        print(f"Invalid session JSON: {e}", file=sys.stderr)
        return False
    return append_session(gist_id, slug, meta, session)


def main():
    parser = argparse.ArgumentParser(
        description="Gist-backed sync for HQ session data",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--test", action="store_true", help="Test gh auth and Gist access")
    group.add_argument("--list", action="store_true", help="List all projects in the Gist")
    group.add_argument("--read", metavar="SLUG", help="Read one project's data")
    group.add_argument("--push", action="store_true", help="Push a session to the Gist")

    parser.add_argument("--slug", help="Project slug (for --push)")
    parser.add_argument("--meta", help="Project metadata JSON (for --push)")
    parser.add_argument("--session", help="Session wrap JSON (for --push)")

    args = parser.parse_args()

    if args.test:
        success = cmd_test()
        sys.exit(0 if success else 1)

    if not gh_available():
        print("Error: gh CLI not authenticated. Run 'gh auth login'.", file=sys.stderr)
        sys.exit(1)

    if args.push:
        gist_id = ensure_gist()
        if not gist_id:
            print("Error: Could not create or find Gist.", file=sys.stderr)
            sys.exit(1)
        if not args.slug or not args.meta or not args.session:
            print("Error: --push requires --slug, --meta, and --session.", file=sys.stderr)
            sys.exit(1)
        success = cmd_push(gist_id, args.slug, args.meta, args.session)
        sys.exit(0 if success else 1)

    gist_id = get_gist_id()
    if not gist_id:
        print("No Gist configured. Run a /wrap first to create one.", file=sys.stderr)
        sys.exit(1)

    if args.list:
        cmd_list(gist_id)
    elif args.read:
        cmd_read(gist_id, args.read)


if __name__ == "__main__":
    main()
