#!/usr/bin/env python3
"""Print the basenames of distributable CI workflows, one per line.

Source of truth is manifest.json's per-layer "github" lists -- the same
lists doe_init.py installs from. setup.sh consumes this instead of
blind-copying .github/workflows/*.yml: kit-internal workflows
(auto-release.yml would tag/release consumer repos; proof.yml goes red
in any project without proof/) must never reach consumer projects.

Usage: list_distributable_workflows.py [path/to/manifest.json]
"""
import json
import sys
from pathlib import Path


def distributable_workflows(manifest_path):
    """Workflow basenames named in any layer's "github" list, deduped,
    manifest order preserved."""
    data = json.loads(Path(manifest_path).read_text())
    names = []
    for layer in data.get("layers", {}).values():
        for entry in layer.get("github", []):
            if entry.startswith("workflows/"):
                name = entry.split("/", 1)[1]
                if name not in names:
                    names.append(name)
    return names


def main():
    default = Path(__file__).resolve().parents[1] / "manifest.json"
    manifest = sys.argv[1] if len(sys.argv) > 1 else str(default)
    for name in distributable_workflows(manifest):
        print(name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
