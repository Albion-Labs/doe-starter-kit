#!/usr/bin/env python3
"""Audit project DOE files against the starter kit.

Compares syncable directories and flags universal files that exist in
the project but not in the kit. Runs as a pre-flight check before
/sync-doe to prevent accidental omissions.

Usage:
  python3 execution/audit_sync.py              # summary
  python3 execution/audit_sync.py --verbose    # show file-level detail
  python3 execution/audit_sync.py --json       # machine-readable output
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

# Project-specific patterns -- files containing these are NOT universal
PROJECT_PATTERNS = re.compile(
    r"\b(monty|constituency|constituencies|pcon\d{2}|pulse|broker|pleasantly"
    r"|restore.britain|albion.labs|election|mp[_\s]interest|census"
    r"|council.control|swing.model|voting.record|canvass|briefing.pack"
    r"|candidate.vett|scenario.builder|ward.level)\b",
    re.IGNORECASE,
)

# Files that are always project-specific by nature (skip without scanning)
ALWAYS_PROJECT_SPECIFIC = {
    "build.py",
    "test_build.py",
    "lighthouse.sh",
    "curated_votes.json",
}

# Files that need stripping before sync (universal structure, project content)
NEEDS_STRIPPING = {
    "build_session_archive.py",
}

# Kit-only files (exist in kit, not expected in project) or files that moved
# from execution/ to global-scripts/ (still in project execution/ from old setup)
KIT_ONLY = {
    "stamp_tutorial_version.py",
    "wrap_html.py",
    "eod_html.py",
    "dispatch_dag.py",
    "run_snagging.py",
    "record_review_result.py",
    "persist_review_findings.py",
}

# Directories to compare: (project_path, kit_path, description)
KIT_ROOT = Path.home() / "doe-starter-kit"


def get_sync_pairs(project_root):
    """Return list of (project_dir, kit_dir, label) to compare."""
    p = Path(project_root)
    k = KIT_ROOT
    pairs = [
        (p / "execution", k / "execution", "execution/", True),
        (p / ".githooks", k / ".githooks", ".githooks/", True),
        (p / ".claude" / "hooks", k / ".claude" / "hooks", ".claude/hooks/", True),
        (p / ".claude" / "agents", k / ".claude" / "agents", ".claude/agents/", True),
        (p / ".claude" / "commands", k / "global-commands", "commands/", False),
        (p / "directives", k / "directives", "directives/", True),
        (p / "tests" / "execution", k / "tests" / "execution", "tests/execution/", True),
    ]
    # check_kit_only=False for commands: global commands install to ~/.claude/commands/,
    # not the project's .claude/commands/. Kit-only commands are expected.
    return pairs


def list_files(directory):
    """List all files in a directory (non-recursive for flat dirs, recursive for nested)."""
    if not directory.exists():
        return set()
    files = set()
    for f in directory.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            files.add(str(f.relative_to(directory)))
    return files


def has_project_references(filepath):
    """Check if a file contains project-specific references."""
    try:
        text = Path(filepath).read_text(encoding="utf-8", errors="ignore")
        return bool(PROJECT_PATTERNS.search(text))
    except Exception:
        return False


def files_differ(path_a, path_b):
    """Check if two files have different content."""
    try:
        return path_a.read_bytes() != path_b.read_bytes()
    except Exception:
        return True


def audit(project_root, verbose=False):
    """Run the full sync audit. Returns findings dict."""
    if not KIT_ROOT.exists():
        return {"error": "Kit not found at ~/doe-starter-kit"}

    pairs = get_sync_pairs(project_root)
    findings = {
        "missing_from_kit": [],  # universal files in project, not in kit
        "needs_stripping": [],   # universal structure but has project content
        "project_specific": [],  # correctly not in kit
        "kit_only": [],          # in kit, not in project
        "diverged": [],          # in both, content differs
        "in_sync": [],           # in both, identical
    }

    for proj_dir, kit_dir, label, check_kit_only in pairs:
        proj_files = list_files(proj_dir)
        kit_files = list_files(kit_dir)

        # Files only in project
        for f in sorted(proj_files - kit_files):
            filepath = proj_dir / f
            name = filepath.name

            if name in ALWAYS_PROJECT_SPECIFIC:
                findings["project_specific"].append(f"{label}{f}")
                continue

            if name in KIT_ONLY:
                continue

            if name in NEEDS_STRIPPING:
                findings["needs_stripping"].append(f"{label}{f}")
                continue

            if has_project_references(filepath):
                findings["project_specific"].append(f"{label}{f}")
            else:
                findings["missing_from_kit"].append(f"{label}{f}")

        # Files only in kit
        if check_kit_only:
            for f in sorted(kit_files - proj_files):
                name = Path(f).name
                if name not in KIT_ONLY:
                    findings["kit_only"].append(f"{label}{f}")

        # Files in both
        for f in sorted(proj_files & kit_files):
            proj_path = proj_dir / f
            kit_path = kit_dir / f
            if files_differ(proj_path, kit_path):
                findings["diverged"].append(f"{label}{f}")
            else:
                findings["in_sync"].append(f"{label}{f}")

    return findings


def print_summary(findings):
    """Print a human-readable summary."""
    missing = findings.get("missing_from_kit", [])
    diverged = findings.get("diverged", [])
    kit_only = findings.get("kit_only", [])
    project_specific = findings.get("project_specific", [])
    in_sync = findings.get("in_sync", [])

    needs_strip = findings.get("needs_stripping", [])
    total_issues = len(missing) + len(needs_strip) + len(diverged) + len(kit_only)

    if total_issues == 0:
        print("All DOE files in sync. Nothing to do.")
        return

    print()
    print(f"{'=' * 50}")
    print(f"  SYNC AUDIT — {total_issues} item(s) need attention")
    print(f"{'=' * 50}")

    if missing:
        print(f"\n  MISSING FROM KIT ({len(missing)} universal files):")
        for f in missing:
            print(f"    + {f}")

    if needs_strip:
        print(f"\n  NEEDS STRIPPING ({len(needs_strip)} universal structure, project content):")
        for f in needs_strip:
            print(f"    * {f}")

    if diverged:
        print(f"\n  DIVERGED ({len(diverged)} files differ):")
        for f in diverged:
            print(f"    ~ {f}")

    if kit_only:
        print(f"\n  KIT ONLY ({len(kit_only)} files not in project):")
        for f in kit_only:
            print(f"    ? {f}")

    print(f"\n  In sync: {len(in_sync)} | Project-specific: {len(project_specific)}")
    print()


def self_test():
    """Create temp fixtures and verify classification logic."""
    import shutil
    import tempfile

    tmpdir = Path(tempfile.mkdtemp(prefix="audit_sync_test_"))
    proj = tmpdir / "project"
    kit = tmpdir / "kit"

    try:
        # Set up minimal directory structures
        for d in ["execution", ".githooks", "directives", "tests/execution"]:
            (proj / d).mkdir(parents=True, exist_ok=True)
            (kit / d).mkdir(parents=True, exist_ok=True)

        # 1. Universal file in project, not in kit -> MISSING
        (proj / "execution" / "universal_tool.py").write_text("# Generic DOE tool\nimport sys\n")

        # 2. Project-specific file (has project reference) -> PROJECT_SPECIFIC
        (proj / "execution" / "import_data.py").write_text("# Import project-specific data\n")

        # 3. Always-project-specific file -> PROJECT_SPECIFIC
        (proj / "execution" / "build.py").write_text("# Project build\n")

        # 4. Needs-stripping file -> NEEDS_STRIPPING
        (proj / "execution" / "build_session_archive.py").write_text("# Has project refs\n")

        # 5. File in both, identical -> IN_SYNC
        (proj / "execution" / "shared.py").write_text("# Shared tool\n")
        (kit / "execution" / "shared.py").write_text("# Shared tool\n")

        # 6. File in both, different -> DIVERGED
        (proj / "execution" / "diverged.py").write_text("# Version A\n")
        (kit / "execution" / "diverged.py").write_text("# Version B\n")

        # 7. File only in kit -> KIT_ONLY
        (kit / "directives" / "kit_only.md").write_text("# Kit directive\n")

        # 8. Kit-only file (stamp_tutorial_version.py) -> ignored
        (kit / "execution" / "stamp_tutorial_version.py").write_text("# Kit only\n")

        # Override KIT_ROOT for test
        global KIT_ROOT
        original_root = KIT_ROOT
        KIT_ROOT = kit

        findings = audit(proj)

        KIT_ROOT = original_root

        # Assertions
        errors = []

        if "execution/universal_tool.py" not in findings["missing_from_kit"]:
            errors.append("FAIL: universal_tool.py should be MISSING FROM KIT")

        proj_specific = findings["project_specific"]
        if not any("build.py" in f for f in proj_specific):
            errors.append("FAIL: build.py should be PROJECT_SPECIFIC (always list)")

        if not any("build_session_archive.py" in f for f in findings["needs_stripping"]):
            errors.append("FAIL: build_session_archive.py should be NEEDS_STRIPPING")

        if not any("shared.py" in f for f in findings["in_sync"]):
            errors.append("FAIL: shared.py should be IN_SYNC")

        if not any("diverged.py" in f for f in findings["diverged"]):
            errors.append("FAIL: diverged.py should be DIVERGED")

        if not any("kit_only.md" in f for f in findings["kit_only"]):
            errors.append("FAIL: kit_only.md should be KIT_ONLY")

        # stamp_tutorial_version.py should NOT appear anywhere
        all_files = []
        for v in findings.values():
            if isinstance(v, list):
                all_files.extend(v)
        if any("stamp_tutorial_version.py" in f for f in all_files):
            errors.append("FAIL: stamp_tutorial_version.py should be ignored (KIT_ONLY list)")

        if errors:
            for e in errors:
                print(f"  {e}")
            print(f"\n  {len(errors)} test(s) FAILED")
            return False
        else:
            print("  All self-test assertions passed.")
            return True

    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def main():
    parser = argparse.ArgumentParser(description="Audit project DOE files against kit")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all categories")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--self-test", action="store_true", help="Run self-test with fixtures")
    parser.add_argument("--project", default=".", help="Project root (default: cwd)")
    args = parser.parse_args()

    if args.self_test:
        ok = self_test()
        sys.exit(0 if ok else 1)

    project_root = Path(args.project).resolve()

    if not KIT_ROOT.exists():
        print("Error: ~/doe-starter-kit not found")
        sys.exit(1)

    findings = audit(project_root)

    if "error" in findings:
        print(f"Error: {findings['error']}")
        sys.exit(1)

    if args.json:
        print(json.dumps(findings, indent=2))
    else:
        print_summary(findings)

    # Exit 1 if there are items needing attention
    missing = findings.get("missing_from_kit", [])
    if missing:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
