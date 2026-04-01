#!/usr/bin/env python3
"""Stamp DOE kit tutorial pages with the current version.

Usage:
  python3 execution/stamp_kit_version.py <version>
  python3 execution/stamp_kit_version.py v1.51.2

Called by /sync-doe before tagging. Also validates that every tutorial
HTML file has at least one version reference (catches new pages added
without the stamp).
"""

import re
import sys
from pathlib import Path

KIT_DOCS = Path.home() / "doe-starter-kit" / "docs" / "tutorial"

# Only match version stamps in known locations: sidebar-version span, hero-badge div, site-footer
# This avoids clobbering example version numbers in tutorial content
STAMP_PATTERNS = [
    re.compile(r'(sidebar-version">)v\d+\.\d+\.\d+'),
    re.compile(r'(DOE Starter Kit )v\d+\.\d+\.\d+'),
]
# For validation: any file with these markers should have a version
HAS_STAMP = re.compile(r'sidebar-version|DOE Starter Kit v\d+\.\d+\.\d+')


def stamp(version):
    if not KIT_DOCS.exists():
        print(f"ERROR: {KIT_DOCS} not found")
        return False

    html_files = sorted(KIT_DOCS.glob("*.html"))
    if not html_files:
        print("ERROR: No HTML files found in tutorial directory")
        return False

    updated = 0
    missing = []

    for f in html_files:
        content = f.read_text(encoding="utf-8")

        if not HAS_STAMP.search(content):
            missing.append(f.name)
            continue

        new_content = content
        for pattern in STAMP_PATTERNS:
            new_content = pattern.sub(lambda m: m.group(1) + version, new_content)

        if new_content != content:
            f.write_text(new_content, encoding="utf-8")
            updated += 1

    if missing:
        print(f"ERROR: {len(missing)} tutorial page(s) have no version stamp:")
        for name in missing:
            print(f"  {name}")
        return False

    print(f"Stamped {updated} files with {version} ({len(html_files)} total)")
    return True


def main():
    if len(sys.argv) < 2:
        print("Usage: stamp_kit_version.py <version>")
        print("Example: stamp_kit_version.py v1.51.2")
        sys.exit(1)

    version = sys.argv[1]
    if not re.match(r"v\d+\.\d+\.\d+", version):
        print(f"ERROR: '{version}' is not a valid version (expected vX.Y.Z)")
        sys.exit(1)

    if stamp(version):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
