#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# CLI: symlink to ~/.local/bin (or /usr/local/bin)
BIN_DIR="${HOME}/.local/bin"
mkdir -p "$BIN_DIR"
ln -sf "$SCRIPT_DIR/reflect" "$BIN_DIR/reflect"

# Skill: Claude Code integration
SKILL_DIR="$HOME/.claude/skills/reflect"
mkdir -p "$SKILL_DIR"
ln -sf "$SCRIPT_DIR/SKILL.md" "$SKILL_DIR/SKILL.md"
ln -sf "$SCRIPT_DIR/hooks" "$SKILL_DIR/hooks"

echo "reflect CLI installed to $BIN_DIR/reflect"
echo "reflect skill installed to $SKILL_DIR"
echo ""
echo "Make sure $BIN_DIR is on your PATH."
echo "Run 'reflect init' in any git repo to get started."
