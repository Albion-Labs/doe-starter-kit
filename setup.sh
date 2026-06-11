#!/bin/bash
# DOE Starter Kit — one-command setup
# For new/non-DOE projects: runs the init wizard (doe_init.py)
# For existing DOE projects: installs global commands, hooks, scripts, and settings.
# Safe to run repeatedly. Project files are never overwritten. Global tooling in
# ~/.claude/ IS updated in place — but any existing global file that differs is
# first backed up to ~/.claude/.doe-backups/<timestamp>/ so nothing is lost.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMMANDS_SRC="$SCRIPT_DIR/global-commands"
COMMANDS_DST="$HOME/.claude/commands"
HOOKS_SRC="$SCRIPT_DIR/global-hooks"
HOOKS_DST="$HOME/.claude/hooks"
SCRIPTS_SRC="$SCRIPT_DIR/global-scripts"
SCRIPTS_DST="$HOME/.claude/scripts"
SETTINGS_FILE="$HOME/.claude/settings.json"
TOOLS_STAMP="$HOME/.claude/.doe-tools-version"

# Flags. --tools-only (alias --scripts-only) re-installs ONLY the global tools
# (scripts + commands) + the version stamp, skipping hooks/settings/project files.
# It's the fast, safe updater the freshness nudge points at (no hook-merge churn).
TOOLS_ONLY=0
for arg in "$@"; do
    case "$arg" in
        --tools-only|--scripts-only) TOOLS_ONLY=1 ;;
    esac
done

# Get kit version from latest git tag (fall back to "unknown")
KIT_VERSION=$(cd "$SCRIPT_DIR" && git describe --tags --abbrev=0 2>/dev/null || echo "unknown")
TODAY=$(date +%d/%m/%y)

# --- Safe overwrite of global tooling ---
# Global files in ~/.claude/ are shared across every project, so a user may have
# their own command/hook/script with the same name. Before replacing one, preserve
# the existing copy under a timestamped backup dir (created lazily, once per run).
BACKUP_DIR="$HOME/.claude/.doe-backups/$(date +%Y%m%d-%H%M%S)"
BACKUP_COUNT=0

# backup_then_copy SRC DST SUBDIR
# Copies SRC -> DST. If DST already exists and differs from SRC, the existing DST
# is first copied to BACKUP_DIR/SUBDIR/ so a user's customised file is never lost.
backup_then_copy() {
    src="$1"; dst="$2"; subdir="$3"
    if [ -f "$dst" ] && ! cmp -s "$src" "$dst"; then
        mkdir -p "$BACKUP_DIR/$subdir"
        cp -p "$dst" "$BACKUP_DIR/$subdir/"
        BACKUP_COUNT=$((BACKUP_COUNT + 1))
    fi
    cp -f "$src" "$dst"
}

# write_tools_stamp — record what kit version produced the installed global tools,
# and where the kit checkout lives, so the freshness check can compare without a
# network call. Read by global-scripts/check_tools_version.py.
write_tools_stamp() {
    python3 - "$KIT_VERSION" "$SCRIPT_DIR" "$TODAY" "$TOOLS_STAMP" <<'PYEOF'
import json, os, sys
version, kit_path, installed, stamp = sys.argv[1:5]
os.makedirs(os.path.dirname(stamp), exist_ok=True)
with open(stamp, "w", encoding="utf-8") as f:
    json.dump({"version": version, "kit_path": kit_path, "installed": installed},
              f, indent=2)
    f.write("\n")
PYEOF
}

# --- Tools-only fast path ---
# Re-install just the global tools (commands + scripts) and refresh the stamp,
# then exit before touching hooks/settings/project files. This is what the
# staleness nudge tells you to run after a kit release.
if [ "$TOOLS_ONLY" = "1" ]; then
    mkdir -p "$COMMANDS_DST" "$SCRIPTS_DST"
    c=0; s=0
    for f in "$COMMANDS_SRC"/*.md; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        [ "$fname" = "README.md" ] && continue
        backup_then_copy "$f" "$COMMANDS_DST/$fname" commands
        c=$((c + 1))
    done
    for f in "$SCRIPTS_SRC"/*.py; do
        [ -f "$f" ] || continue
        backup_then_copy "$f" "$SCRIPTS_DST/$(basename "$f")" scripts
        s=$((s + 1))
    done
    write_tools_stamp
    if [ "$BACKUP_COUNT" -gt 0 ]; then
        echo "ℹ  Backed up $BACKUP_COUNT customised file(s) to $BACKUP_DIR"
    fi
    echo "✓ $c commands + $s scripts updated to DOE Kit $KIT_VERSION (tools-only; hooks/settings unchanged)"
    exit 0
fi

# --- Wizard delegation ---
# If this is a new or non-DOE project, run the init wizard instead of blind-copy setup.
if [ ! -f "CLAUDE.md" ] || [ ! -d "directives" ]; then
    if [ -f "$SCRIPT_DIR/execution/doe_init.py" ]; then
        python3 "$SCRIPT_DIR/execution/doe_init.py" --kit-dir "$SCRIPT_DIR" "$@"
        # After wizard completes, fall through to install global tooling below
    fi
fi

# --- Global tooling installation ---
# Always runs: installs commands, hooks, scripts to ~/.claude/ (global, not per-project).

# 1. Install commands
mkdir -p "$COMMANDS_DST"
COMMAND_COUNT=0
for f in "$COMMANDS_SRC"/*.md; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    # Skip README.md — it's the GitHub directory readme, not a command
    if [ "$fname" = "README.md" ]; then
        continue
    fi
    backup_then_copy "$f" "$COMMANDS_DST/$fname" commands
    COMMAND_COUNT=$((COMMAND_COUNT + 1))
done

# 2. Install global hooks
mkdir -p "$HOOKS_DST"
HOOK_COUNT=0
for f in "$HOOKS_SRC"/*.py; do
    [ -f "$f" ] || continue
    backup_then_copy "$f" "$HOOKS_DST/$(basename "$f")" hooks
    HOOK_COUNT=$((HOOK_COUNT + 1))
done

# 2b. Install project hooks (if in a DOE project)
PROJECT_HOOK_COUNT=0
if [ -f "CLAUDE.md" ] && [ -d "$SCRIPT_DIR/.claude/hooks" ]; then
    mkdir -p .claude/hooks
    for f in "$SCRIPT_DIR"/.claude/hooks/*.py; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        # Always update from kit (kit is authoritative for DOE hooks).
        # Guard against self-copy when setup.sh is run on the kit itself
        # (`cp` returns non-zero on byte-identical files, crashing under
        # `set -e`). The `-ef` test compares inodes; cp is skipped only
        # when source and dest are literally the same file.
        [ "$f" -ef ".claude/hooks/$fname" ] || cp -f "$f" ".claude/hooks/$fname"
        PROJECT_HOOK_COUNT=$((PROJECT_HOOK_COUNT + 1))
    done
fi

# 2c. Install project plans (if in a DOE project, only missing files)
PROJECT_PLAN_COUNT=0
if [ -f "CLAUDE.md" ] && [ -d "$SCRIPT_DIR/.claude/plans" ]; then
    mkdir -p .claude/plans
    for f in "$SCRIPT_DIR"/.claude/plans/*.md; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        if [ ! -f ".claude/plans/$fname" ]; then
            cp "$f" ".claude/plans/$fname"
            PROJECT_PLAN_COUNT=$((PROJECT_PLAN_COUNT + 1))
        fi
    done
fi

# 2d. Install project agents (if in a DOE project)
PROJECT_AGENT_COUNT=0
if [ -f "CLAUDE.md" ] && [ -d "$SCRIPT_DIR/.claude/agents" ]; then
    mkdir -p .claude/agents
    for f in "$SCRIPT_DIR"/.claude/agents/*.md; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        # Self-copy guard (see Section 2b for rationale).
        [ "$f" -ef ".claude/agents/$fname" ] || cp -f "$f" ".claude/agents/$fname"
        PROJECT_AGENT_COUNT=$((PROJECT_AGENT_COUNT + 1))
    done
fi

# 3. Install global scripts
mkdir -p "$SCRIPTS_DST"
SCRIPT_COUNT=0
for f in "$SCRIPTS_SRC"/*.py; do
    [ -f "$f" ] || continue
    backup_then_copy "$f" "$SCRIPTS_DST/$(basename "$f")" scripts
    SCRIPT_COUNT=$((SCRIPT_COUNT + 1))
done

# Tell the user if we preserved any of their existing global files.
if [ "$BACKUP_COUNT" -gt 0 ]; then
    echo "ℹ  Backed up $BACKUP_COUNT existing global file(s) you had customised to:"
    echo "   $BACKUP_DIR"
fi

# 4a. Merge global hooks into ~/.claude/settings.json
python3 -c "
import json
from pathlib import Path

settings_path = Path('$SETTINGS_FILE')
settings = {}
if settings_path.exists():
    try:
        settings = json.loads(settings_path.read_text())
    except json.JSONDecodeError:
        pass

hooks = settings.setdefault('hooks', {})

# Desired global hooks, keyed by event. Dedup is by exact command string, so
# re-running setup is idempotent and adding a NEW command never duplicates an
# existing one.
WANTED = {
    'SessionStart': [
        {'matcher': 'startup', 'hooks': [
            {'type': 'command', 'command': 'python3 ~/.claude/scripts/check_tools_version.py',
             'description': 'Nudge when DOE global tools are behind the kit'},
        ]}
    ],
}

changed = False
for event, wanted_entries in WANTED.items():
    existing = hooks.get(event, [])
    wanted_cmds = {h['command'] for e in wanted_entries for h in e['hooks']}
    existing_cmds = {h.get('command', '') for e in existing for h in e.get('hooks', [])}
    if not wanted_cmds.issubset(existing_cmds):
        cleaned = [e for e in existing if not any(h.get('command', '') in wanted_cmds for h in e.get('hooks', []))]
        cleaned.extend(wanted_entries)
        hooks[event] = cleaned
        changed = True

if changed:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(settings, indent=2) + '\n')
    print('  ✓ Global hooks merged into ~/.claude/settings.json')
else:
    print('  ✓ Global hooks already present in ~/.claude/settings.json')
"

# 4b. Merge project hooks into PROJECT/.claude/settings.json (if in a DOE project)
if [ -f "CLAUDE.md" ] && [ -f "$SCRIPT_DIR/.claude/settings.json" ]; then
    python3 -c "
import json
from pathlib import Path

kit_settings = json.loads(Path('$SCRIPT_DIR/.claude/settings.json').read_text())
project_path = Path('.claude/settings.json')
project = {}
if project_path.exists():
    try:
        project = json.loads(project_path.read_text())
    except json.JSONDecodeError:
        pass

# For each hook type (PreToolUse, PostToolUse), merge kit entries
# Strategy: collect all unique commands from both kit and project
kit_hooks = kit_settings.get('hooks', {})
proj_hooks = project.setdefault('hooks', {})
changed = False

for hook_type in ('PreToolUse', 'PostToolUse'):
    kit_entries = kit_hooks.get(hook_type, [])
    proj_entries = proj_hooks.get(hook_type, [])

    # Collect all commands already in project
    existing_cmds = set()
    for entry in proj_entries:
        for h in entry.get('hooks', []):
            existing_cmds.add(h.get('command', ''))

    # Add any kit commands that are missing from project
    for kit_entry in kit_entries:
        new_hooks = []
        for h in kit_entry.get('hooks', []):
            if h.get('command', '') not in existing_cmds:
                new_hooks.append(h)
                existing_cmds.add(h['command'])
        if new_hooks:
            # Find matching matcher entry or create new one
            matcher = kit_entry.get('matcher', '')
            matched_entry = None
            for pe in proj_entries:
                if pe.get('matcher', '') == matcher:
                    matched_entry = pe
                    break
            if matched_entry:
                matched_entry['hooks'].extend(new_hooks)
            else:
                proj_entries.append({'matcher': matcher, 'hooks': new_hooks})
            changed = True

    proj_hooks[hook_type] = proj_entries

# Preserve other settings (plugins, etc)
for k, v in kit_settings.items():
    if k != 'hooks' and k not in project:
        project[k] = v

if changed:
    project_path.parent.mkdir(parents=True, exist_ok=True)
    project_path.write_text(json.dumps(project, indent=2) + '\n')
    print('  ✓ Project hooks merged into .claude/settings.json')
else:
    print('  ✓ Project hooks already up to date in .claude/settings.json')
"
fi

# 5. Copy universal CLAUDE.md template (only if user doesn't have one)
CLAUDE_MD="$HOME/.claude/CLAUDE.md"
if [ ! -f "$CLAUDE_MD" ]; then
    if [ -f "$SCRIPT_DIR/universal-claude-md-template.md" ]; then
        cp "$SCRIPT_DIR/universal-claude-md-template.md" "$CLAUDE_MD"
        echo "✓ Universal CLAUDE.md installed to ~/.claude/CLAUDE.md"
    fi
else
    echo "✓ ~/.claude/CLAUDE.md already exists (not overwritten)"
fi

# 6. Activate git hooks (only if cwd is a git repo)
if git rev-parse --git-dir > /dev/null 2>&1; then
    git config core.hooksPath .githooks 2>/dev/null
    echo "✓ Git hooks activated"
fi

# 7. Copy Quality Stack files (only if not already present in project)
# Execution scripts for test orchestration, health checks, and verification
QS_SCRIPTS="run_test_suite.py health_check.py generate_test_checklist.py audit_claims.py audit_sync.py"
QS_SCRIPT_COUNT=0
if [ -d "$SCRIPT_DIR/execution" ]; then
    for script in $QS_SCRIPTS; do
        if [ -f "$SCRIPT_DIR/execution/$script" ] && [ ! -f "execution/$script" ]; then
            mkdir -p execution
            cp "$SCRIPT_DIR/execution/$script" "execution/$script"
            QS_SCRIPT_COUNT=$((QS_SCRIPT_COUNT + 1))
        fi
    done
fi

# Test infrastructure: config, helpers, specs, baselines, playwright config
if [ -d "$SCRIPT_DIR/tests" ]; then
    # tests/config.json — only if missing (preserves project customisations)
    if [ -f "$SCRIPT_DIR/tests/config.json" ] && [ ! -f "tests/config.json" ]; then
        mkdir -p tests
        cp "$SCRIPT_DIR/tests/config.json" "tests/config.json"
        QS_SCRIPT_COUNT=$((QS_SCRIPT_COUNT + 1))
    fi
    # tests/helpers.js
    if [ -f "$SCRIPT_DIR/tests/helpers.js" ] && [ ! -f "tests/helpers.js" ]; then
        mkdir -p tests
        cp "$SCRIPT_DIR/tests/helpers.js" "tests/helpers.js"
        QS_SCRIPT_COUNT=$((QS_SCRIPT_COUNT + 1))
    fi
    # tests/*.spec.js — template specs
    for f in "$SCRIPT_DIR"/tests/*.spec.js; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        if [ ! -f "tests/$fname" ]; then
            mkdir -p tests
            cp "$f" "tests/$fname"
            QS_SCRIPT_COUNT=$((QS_SCRIPT_COUNT + 1))
        fi
    done
    # tests/baselines/
    if [ -d "$SCRIPT_DIR/tests/baselines" ] && [ ! -d "tests/baselines" ]; then
        mkdir -p tests/baselines
        cp "$SCRIPT_DIR"/tests/baselines/* tests/baselines/ 2>/dev/null
        QS_SCRIPT_COUNT=$((QS_SCRIPT_COUNT + 1))
    fi
fi

# playwright.config.js
if [ -f "$SCRIPT_DIR/playwright.config.js" ] && [ ! -f "playwright.config.js" ]; then
    cp "$SCRIPT_DIR/playwright.config.js" "playwright.config.js"
    QS_SCRIPT_COUNT=$((QS_SCRIPT_COUNT + 1))
fi

if [ "$QS_SCRIPT_COUNT" -gt 0 ]; then
    echo "✓ $QS_SCRIPT_COUNT Quality Stack files installed"
else
    echo "✓ Quality Stack files already present (not overwritten)"
fi

# 8. Copy CI workflows (only if not already present) — scoped to the
# manifest's "github" lists, mirroring doe_init.py. Blind-copying
# .github/workflows/*.yml leaked kit-internal workflows into consumer
# projects (auto-release.yml would tag/release them; proof.yml goes red
# in any project without proof/).
CI_COUNT=0
if [ -d "$SCRIPT_DIR/.github/workflows" ]; then
    for fname in $(python3 "$SCRIPT_DIR/execution/list_distributable_workflows.py" "$SCRIPT_DIR/manifest.json" 2>/dev/null); do
        f="$SCRIPT_DIR/.github/workflows/$fname"
        [ -f "$f" ] || continue
        if [ ! -f ".github/workflows/$fname" ]; then
            mkdir -p .github/workflows
            cp "$f" ".github/workflows/$fname"
            CI_COUNT=$((CI_COUNT + 1))
        fi
    done
fi
if [ "$CI_COUNT" -gt 0 ]; then
    echo "✓ $CI_COUNT CI workflow(s) installed to .github/workflows/"
else
    echo "✓ CI workflows already present (not overwritten)"
fi

# 9. Copy PR template (only if not already present)
if [ -f "$SCRIPT_DIR/.github/pull_request_template.md" ] && [ ! -f ".github/pull_request_template.md" ]; then
    mkdir -p .github
    cp "$SCRIPT_DIR/.github/pull_request_template.md" ".github/pull_request_template.md"
    echo "✓ PR template installed to .github/"
fi

# 10. Stamp the installed tools version (powers the staleness nudge) + summary
write_tools_stamp

echo ""
echo "✓ $COMMAND_COUNT commands installed to ~/.claude/commands/"
echo "✓ $HOOK_COUNT global hooks installed to ~/.claude/hooks/"
echo "✓ $SCRIPT_COUNT scripts installed to ~/.claude/scripts/"
if [ "$PROJECT_HOOK_COUNT" -gt 0 ]; then
    echo "✓ $PROJECT_HOOK_COUNT project hooks installed to .claude/hooks/"
fi
if [ "$PROJECT_PLAN_COUNT" -gt 0 ]; then
    echo "✓ $PROJECT_PLAN_COUNT plan files installed to .claude/plans/"
fi
if [ "$PROJECT_AGENT_COUNT" -gt 0 ]; then
    echo "✓ $PROJECT_AGENT_COUNT agent definitions installed to .claude/agents/"
fi
echo "✓ DOE Kit $KIT_VERSION installed ($TODAY)"
echo ""
echo "Ready — run claude and type /stand-up"
