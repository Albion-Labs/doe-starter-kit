#!/bin/bash
# DOE Starter Kit — one-command setup
# Installs global commands, activates hooks, writes version receipt.
# Safe to run repeatedly (updates in place, never overwrites user config).

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMMANDS_SRC="$SCRIPT_DIR/global-commands"
COMMANDS_DST="$HOME/.claude/commands"
VERSION_FILE="$HOME/.claude/.doe-kit-version"

# Get kit version from latest git tag (fall back to "unknown")
KIT_VERSION=$(cd "$SCRIPT_DIR" && git describe --tags --abbrev=0 2>/dev/null || echo "unknown")
TODAY=$(date +%d/%m/%y)

# 1. Install commands
mkdir -p "$COMMANDS_DST"
COMMAND_COUNT=0
for f in "$COMMANDS_SRC"/*.md; do
    fname=$(basename "$f")
    # Skip README.md — it's the GitHub directory readme, not a command
    if [ "$fname" = "README.md" ]; then
        continue
    fi
    cp "$f" "$COMMANDS_DST/$fname"
    COMMAND_COUNT=$((COMMAND_COUNT + 1))
done

# 2. Copy universal CLAUDE.md template (only if user doesn't have one)
CLAUDE_MD="$HOME/.claude/CLAUDE.md"
if [ ! -f "$CLAUDE_MD" ]; then
    if [ -f "$SCRIPT_DIR/universal-claude-md-template.md" ]; then
        cp "$SCRIPT_DIR/universal-claude-md-template.md" "$CLAUDE_MD"
        echo "✓ Universal CLAUDE.md installed to ~/.claude/CLAUDE.md"
    fi
else
    echo "✓ ~/.claude/CLAUDE.md already exists (not overwritten)"
fi

# 3. Activate git hooks (only if in a git repo)
if [ -d "$SCRIPT_DIR/.git" ] || git -C "$SCRIPT_DIR" rev-parse --git-dir > /dev/null 2>&1; then
    git -C "$SCRIPT_DIR" config core.hooksPath .githooks 2>/dev/null
    echo "✓ Git hooks activated"
fi

# 4. Write version receipt
mkdir -p "$(dirname "$VERSION_FILE")"
cat > "$VERSION_FILE" << EOF
version=$KIT_VERSION
installed=$TODAY
EOF

# 5. Summary
echo "✓ $COMMAND_COUNT commands installed to ~/.claude/commands/"
echo "✓ DOE Kit $KIT_VERSION installed ($TODAY)"
echo ""
echo "Ready — run claude and type /stand-up"
