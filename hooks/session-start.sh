#!/usr/bin/env bash
# /reflect SessionStart hook — checks for new sessions since last reflect
# Non-blocking: always exits 0.
# Behavior depends on .reflect/config.yaml session_start setting:
#   "auto"   → prints a trigger line that tells the agent to run /reflect
#   "manual" → prints a reminder (default)

set -euo pipefail

# Skip if .reflect/ doesn't exist (user hasn't run /reflect yet)
if [ ! -d ".reflect" ]; then
  exit 0
fi

# Skip if entire CLI isn't available
if ! command -v entire &>/dev/null && [ ! -f ~/.local/bin/entire ]; then
  exit 0
fi

# Read session_start mode from config (default: manual)
MODE="auto"
if [ -f ".reflect/config.yaml" ]; then
  # Extract session_start value — POSIX-compatible, no yq/grep -P dependency
  # Handles inline comments (e.g., "session_start: manual # note")
  CONFIGURED=$(sed -n 's/^session_start:[[:space:]]*\([a-z]*\).*/\1/p' .reflect/config.yaml 2>/dev/null || true)
  if [ "$CONFIGURED" = "manual" ]; then
    MODE="manual"
  fi
fi

# Find the most recent session file in .reflect/sessions/
LAST_SESSION_FILE=$(ls -t .reflect/sessions/*.md 2>/dev/null | head -1)

if [ -z "$LAST_SESSION_FILE" ]; then
  # No sessions analyzed yet — check if there are any Entire sessions at all
  if entire status 2>/dev/null | grep -q "session"; then
    if [ "$MODE" = "auto" ]; then
      echo "Reflect: Sessions available but none analyzed yet. Running /reflect automatically."
      echo "REFLECT_AUTO_RUN"
    else
      echo "Reflect: Sessions available but none analyzed yet. Run /reflect to capture insights."
    fi
  fi
  exit 0
fi

# Get the modification time of the last analyzed session
LAST_REFLECT_TIME=$(stat -c %Y "$LAST_SESSION_FILE" 2>/dev/null || stat -f %m "$LAST_SESSION_FILE" 2>/dev/null)

if [ -z "$LAST_REFLECT_TIME" ]; then
  exit 0
fi

# Check Entire for sessions newer than our last analysis
ENTIRE_OUTPUT=$(entire status 2>/dev/null || true)

if [ -z "$ENTIRE_OUTPUT" ]; then
  exit 0
fi

# Extract the most recent session date from entire status
LATEST_ENTIRE=$(echo "$ENTIRE_OUTPUT" | grep -oP '\d{4}-\d{2}-\d{2}' | sort -r | head -1)
LAST_REFLECT_DATE=$(date -d "@$LAST_REFLECT_TIME" +%Y-%m-%d 2>/dev/null || date -r "$LAST_REFLECT_TIME" +%Y-%m-%d 2>/dev/null)

if [ -n "$LATEST_ENTIRE" ] && [ -n "$LAST_REFLECT_DATE" ]; then
  if [[ "$LATEST_ENTIRE" > "$LAST_REFLECT_DATE" ]]; then
    if [ "$MODE" = "auto" ]; then
      echo "Reflect: New sessions detected since last /reflect (last analyzed: $LAST_REFLECT_DATE). Running analysis automatically."
      echo "REFLECT_AUTO_RUN"
    else
      echo "Reflect: New sessions detected since last /reflect (last analyzed: $LAST_REFLECT_DATE). Run /reflect to capture recent insights."
    fi
  fi
fi

exit 0
