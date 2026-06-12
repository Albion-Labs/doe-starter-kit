"""Tests for what setup.sh distributes to consumer projects (kit v1.71.3).

Two liveness-audit findings pinned here:
- A2: setup.sh blind-copied ALL .github/workflows/*.yml, leaking
  kit-internal workflows (auto-release.yml would tag/release consumer
  repos; proof.yml goes red in any project without proof/). The copy
  loop is now scoped to manifest.json's "github" lists via
  execution/list_distributable_workflows.py, mirroring doe_init.py.
- A5: audit_sync.py was referenced by /sync-doe Step 0 and /wrap's
  drift check but distributed by nothing — both silently no-opped in
  every consumer project.
"""
import json
import subprocess
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
HELPER = KIT / "execution" / "list_distributable_workflows.py"
MANIFEST = KIT / "manifest.json"
SETUP = KIT / "setup.sh"

sys.path.insert(0, str(KIT / "execution"))
from list_distributable_workflows import distributable_workflows  # noqa: E402

KIT_INTERNAL_WORKFLOWS = {"auto-release.yml", "proof.yml"}


# --- A2: workflow distribution scoped to the manifest ---

def test_kit_internal_workflows_not_distributable():
    names = distributable_workflows(MANIFEST)
    assert not KIT_INTERNAL_WORKFLOWS & set(names), (
        f"kit-internal workflows must never reach consumer projects: "
        f"{KIT_INTERNAL_WORKFLOWS & set(names)}"
    )


def test_distributable_workflows_exist_in_kit():
    names = distributable_workflows(MANIFEST)
    assert names, "manifest names no distributable workflows — distribution is dead"
    for name in names:
        assert (KIT / ".github" / "workflows" / name).is_file(), (
            f"manifest names {name} but the kit has no such workflow"
        )


def test_cli_output_matches_function():
    p = subprocess.run(
        [sys.executable, str(HELPER), str(MANIFEST)],
        capture_output=True, text=True, timeout=15,
    )
    assert p.returncode == 0, p.stderr
    assert p.stdout.split() == distributable_workflows(MANIFEST)


def test_dedupes_and_ignores_non_workflow_entries(tmp_path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"layers": {
        "a": {"github": ["workflows/ci.yml", "CODEOWNERS", "dependabot.yml"]},
        "b": {"github": ["workflows/ci.yml", "workflows/extra.yml"]},
        "c": {},
    }}))
    assert distributable_workflows(manifest) == ["ci.yml", "extra.yml"]


def test_setup_sh_uses_manifest_scoped_copy():
    text = SETUP.read_text()
    assert "list_distributable_workflows.py" in text, (
        "setup.sh must derive its workflow copy list from the manifest helper"
    )
    assert '"$SCRIPT_DIR"/.github/workflows/*.yml' not in text, (
        "regression: setup.sh blind-copies every workflow in the kit again"
    )


# --- A5: audit_sync.py distributed by both install paths ---

def test_audit_sync_in_manifest_universal_layer():
    data = json.loads(MANIFEST.read_text())
    assert "audit_sync.py" in data["layers"]["universal"]["execution"], (
        "/sync-doe Step 0 and /wrap's drift check need audit_sync.py in "
        "consumer projects; doe_init installs from this list"
    )


def test_audit_sync_in_setup_qs_scripts():
    for line in SETUP.read_text().splitlines():
        if line.startswith("QS_SCRIPTS="):
            assert "audit_sync.py" in line
            return
    raise AssertionError("QS_SCRIPTS line not found in setup.sh")


def test_audit_sync_exists_in_kit():
    assert (KIT / "execution" / "audit_sync.py").is_file()


# --- v1.71.4: project hooks mirrored into ~/.claude/hooks ---
# Background sessions anchor $CLAUDE_PROJECT_DIR to $HOME, so the global
# settings' "$CLAUDE_PROJECT_DIR/.claude/hooks/..." commands resolve to
# ~/.claude/hooks/*. Every guardrail such a session runs executes those
# copies; setup.sh must keep them fresh or they silently drift from the kit.

def test_setup_mirrors_project_hooks_to_global_hooks_dir():
    text = SETUP.read_text()
    assert 'backup_then_copy "$f" "$HOOKS_DST/$(basename "$f")" hooks' in text
    # The mirror loop must read from the kit's project-hooks dir.
    assert '"$SCRIPT_DIR"/.claude/hooks/*.py' in text, (
        "setup.sh must mirror the kit's .claude/hooks/*.py into ~/.claude/hooks "
        "(the copies background sessions actually execute)"
    )
    mirror_pos = text.find('"$SCRIPT_DIR"/.claude/hooks/*.py')
    tools_only_exit = text.find("tools-only; hooks/settings unchanged")
    assert mirror_pos > tools_only_exit, (
        "the mirror belongs on the full-run path; --tools-only deliberately "
        "leaves hooks untouched"
    )
