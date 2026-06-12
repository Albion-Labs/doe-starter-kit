"""Registration-liveness checks for .claude/settings.json (kit v1.71.3).

Liveness-audit finding A8: guard_kit_writes.py was registered under the
Edit|Write|MultiEdit matcher while the hook acts only on Bash events —
a guaranteed no-op python spawn on every file edit, with a description
claiming a file-edit guard that was retired in v1.60.0.
"""
import json
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
SETTINGS = KIT / ".claude" / "settings.json"


def _registrations(script_name):
    """(stage, matcher) pairs where script_name is registered."""
    data = json.loads(SETTINGS.read_text())
    found = []
    for stage, entries in data.get("hooks", {}).items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                if script_name in hook.get("command", ""):
                    found.append((stage, entry.get("matcher", "")))
    return found


def test_guard_kit_writes_registered_only_for_bash():
    regs = _registrations("guard_kit_writes.py")
    assert regs == [("PreToolUse", "Bash")], (
        f"guard_kit_writes acts only on Bash events; registrations: {regs}"
    )


def test_registered_hook_scripts_exist():
    """Every command registered in settings.json must point at a script
    that exists in this checkout — a registration for a missing file is a
    silent no-op on every matched tool call."""
    data = json.loads(SETTINGS.read_text())
    for stage, entries in data.get("hooks", {}).items():
        for entry in entries:
            for hook in entry.get("hooks", []):
                cmd = hook.get("command", "")
                if "$CLAUDE_PROJECT_DIR/" not in cmd:
                    continue
                rel = cmd.split("$CLAUDE_PROJECT_DIR/", 1)[1].split('"')[0]
                assert (KIT / rel).is_file(), f"{stage}: registered script missing: {rel}"
