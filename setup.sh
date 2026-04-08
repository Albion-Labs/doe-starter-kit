#!/bin/bash
# DOE Starter Kit — one-command setup
# For new/non-DOE projects: runs the init wizard (doe_init.py)
# For existing DOE projects: installs global commands, hooks, scripts, and settings.
# Safe to run repeatedly (updates in place, never overwrites user config).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMMANDS_SRC="$SCRIPT_DIR/global-commands"
COMMANDS_DST="$HOME/.claude/commands"
HOOKS_SRC="$SCRIPT_DIR/global-hooks"
HOOKS_DST="$HOME/.claude/hooks"
SCRIPTS_SRC="$SCRIPT_DIR/global-scripts"
SCRIPTS_DST="$HOME/.claude/scripts"
SETTINGS_FILE="$HOME/.claude/settings.json"

# Get kit version from latest git tag (fall back to "unknown")
KIT_VERSION=$(cd "$SCRIPT_DIR" && git describe --tags --abbrev=0 2>/dev/null || echo "unknown")
TODAY=$(date +%d/%m/%y)

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
    fname=$(basename "$f")
    # Skip README.md — it's the GitHub directory readme, not a command
    if [ "$fname" = "README.md" ]; then
        continue
    fi
    cp -f "$f" "$COMMANDS_DST/$fname"
    COMMAND_COUNT=$((COMMAND_COUNT + 1))
done

# 2. Install global hooks
mkdir -p "$HOOKS_DST"
HOOK_COUNT=0
for f in "$HOOKS_SRC"/*.py; do
    [ -f "$f" ] || continue
    cp -f "$f" "$HOOKS_DST/$(basename "$f")"
    HOOK_COUNT=$((HOOK_COUNT + 1))
done

# 2b. Install project hooks (if in a DOE project)
PROJECT_HOOK_COUNT=0
if [ -f "CLAUDE.md" ] && [ -d "$SCRIPT_DIR/.claude/hooks" ]; then
    mkdir -p .claude/hooks
    for f in "$SCRIPT_DIR"/.claude/hooks/*.py; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
        # Always update from kit (kit is authoritative for DOE hooks)
        cp -f "$f" ".claude/hooks/$fname"
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
        cp -f "$f" ".claude/agents/$fname"
        PROJECT_AGENT_COUNT=$((PROJECT_AGENT_COUNT + 1))
    done
fi

# 3. Install global scripts
mkdir -p "$SCRIPTS_DST"
SCRIPT_COUNT=0
for f in "$SCRIPTS_SRC"/*.py; do
    [ -f "$f" ] || continue
    cp -f "$f" "$SCRIPTS_DST/$(basename "$f")"
    SCRIPT_COUNT=$((SCRIPT_COUNT + 1))
done

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
post_hooks = hooks.get('PostToolUse', [])

GLOBAL_HOOKS = [
    {
        'hooks': [
            {'type': 'command', 'command': 'python3 ~/.claude/hooks/heartbeat.py',
             'description': 'Update session heartbeat during active waves'},
            {'type': 'command', 'command': 'python3 ~/.claude/hooks/context_monitor.py',
             'description': 'Warn at 60% context usage, stop at 80%'},
        ]
    }
]

global_cmds = {h['command'] for entry in GLOBAL_HOOKS for h in entry.get('hooks', [])}
existing_cmds = {h.get('command', '') for entry in post_hooks for h in entry.get('hooks', [])}

if not global_cmds.issubset(existing_cmds):
    cleaned = [e for e in post_hooks if not any(h.get('command', '') in global_cmds for h in e.get('hooks', []))]
    cleaned.extend(GLOBAL_HOOKS)
    hooks['PostToolUse'] = cleaned
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
QS_SCRIPTS="run_test_suite.py health_check.py verify_tests.py generate_test_checklist.py audit_claims.py"
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

# 8. Copy CI workflow (only if not already present)
CI_COUNT=0
if [ -d "$SCRIPT_DIR/.github/workflows" ]; then
    for f in "$SCRIPT_DIR"/.github/workflows/*.yml; do
        [ -f "$f" ] || continue
        fname=$(basename "$f")
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

# 10. Set DOE Role in project STATE.md
STATE_FILE="STATE.md"
if [ -f "$STATE_FILE" ] && grep -q "DOE Role:" "$STATE_FILE"; then
    echo ""
    echo "Are you a DOE contributor? (Most users: no)"
    echo "  n = Consumer — you build projects using DOE (default)"
    echo "  y = Creator  — you contribute improvements back to the starter kit"
    printf "Choice [n]: "
    read -r DOE_ROLE_CHOICE
    if [ "$DOE_ROLE_CHOICE" = "y" ] || [ "$DOE_ROLE_CHOICE" = "Y" ]; then
        # Cross-platform sed -i (macOS needs '', Linux doesn't)
        if sed --version 2>/dev/null | grep -q GNU; then
            sed -i 's/\*\*DOE Role:\*\* consumer/**DOE Role:** creator/' "$STATE_FILE"
        else
            sed -i '' 's/\*\*DOE Role:\*\* consumer/**DOE Role:** creator/' "$STATE_FILE"
        fi
        echo "✓ DOE Role set to creator"
    else
        echo "✓ DOE Role set to consumer"
    fi
fi

# 11. Summary
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
