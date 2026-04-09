#!/usr/bin/env python3
"""Stamp tutorial HTML files with a new DOE Starter Kit version number.

Primary source of truth: docs/tutorial/kit-version.js (one file, all pages load it).
Fallback: also stamps hardcoded version strings in HTML for no-JS environments.
"""

import argparse
import re
import sys
from pathlib import Path


def stamp_version(version: str, root: Path) -> tuple[int, int]:
    """Replace version strings in kit-version.js and all tutorial HTML files.

    Returns (files_updated, total_replacements).
    """
    tutorial_dir = root / "docs" / "tutorial"
    if not tutorial_dir.exists():
        print(f"Error: tutorial directory not found: {tutorial_dir}", file=sys.stderr)
        sys.exit(1)

    files_updated = 0
    total_replacements = 0

    # ── Primary: update kit-version.js (single source of truth) ──
    version_js = tutorial_dir / "kit-version.js"
    if version_js.exists():
        original = version_js.read_text(encoding="utf-8")
        updated = re.sub(r"var VERSION = '[^']+';", f"var VERSION = '{version}';", original)
        if updated != original:
            version_js.write_text(updated, encoding="utf-8")
            files_updated += 1
            total_replacements += 1
    else:
        print(f"Warning: {version_js} not found — creating it", file=sys.stderr)
        version_js.write_text(
            f"// Single source of truth for DOE Starter Kit version across all tutorial pages.\n"
            f"// Updated by: python3 execution/stamp_tutorial_version.py vX.Y.Z\n"
            f"(function () {{\n"
            f"  var VERSION = '{version}';\n"
            f"  document.querySelectorAll('.sidebar-version').forEach(function (el) {{ el.textContent = VERSION; }});\n"
            f"  document.querySelectorAll('.hero-badge').forEach(function (el) {{\n"
            f"    el.textContent = el.textContent.replace(/v\\d+\\.\\d+\\.\\d+/, VERSION);\n"
            f"  }});\n"
            f"  document.querySelectorAll('.site-footer').forEach(function (el) {{\n"
            f"    el.textContent = el.textContent.replace(/v\\d+\\.\\d+\\.\\d+/, VERSION);\n"
            f"  }});\n"
            f"}})();\n",
            encoding="utf-8",
        )
        files_updated += 1
        total_replacements += 1

    # ── Fallback: stamp HTML files for no-JS environments ──
    html_files = list(tutorial_dir.glob("*.html"))
    if not html_files:
        print(f"Warning: no HTML files found in {tutorial_dir}")
        return files_updated, total_replacements

    patterns = [
        # Footer and hero badge: "DOE Starter Kit v1.2.3"
        (re.compile(r"DOE Starter Kit v\d+\.\d+\.\d+"), f"DOE Starter Kit {version}"),
        # Sidebar version badge: <span class="sidebar-version">v1.2.3</span>
        (re.compile(r'(sidebar-version">)v\d+\.\d+\.\d+'), rf"\g<1>{version}"),
        # Terminal mockup: "latest: v1.2.3"
        (re.compile(r"latest: v\d+\.\d+\.\d+"), f"latest: {version}"),
    ]

    for html_file in sorted(html_files):
        original = html_file.read_text(encoding="utf-8")
        updated = original
        file_replacements = 0

        for pattern, replacement in patterns:
            for m in pattern.finditer(updated):
                if m.group() != replacement:
                    file_replacements += 1
            updated = pattern.sub(replacement, updated)

        if file_replacements > 0:
            html_file.write_text(updated, encoding="utf-8")
            files_updated += 1
            total_replacements += file_replacements

    return files_updated, total_replacements


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Stamp tutorial HTML files with a new version number."
    )
    parser.add_argument("version", help="Version string, e.g. v1.37.0")
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="Override base directory (default: parent of this script's directory)",
    )
    args = parser.parse_args()

    # Validate version format
    if not re.fullmatch(r"v\d+\.\d+\.\d+", args.version):
        print(
            f"Error: version must match vX.Y.Z format, got: {args.version}",
            file=sys.stderr,
        )
        sys.exit(1)

    root = args.root if args.root is not None else Path(__file__).resolve().parent.parent

    files_updated, total_replacements = stamp_version(args.version, root)

    print(
        f"Done: {files_updated} file(s) updated, {total_replacements} replacement(s) made "
        f"({args.version})"
    )


if __name__ == "__main__":
    main()
