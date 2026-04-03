---
schema_version: "1.0"
id: "0001"
title: Default session_start to auto
date: 2026-04-03
status: accepted
sessions: [56cd9d49]
files: [hooks/session-start.sh, SPEC.md, SKILL.md, README.md]
superseded_by: null
confidence: HIGH
last_validated: 2026-04-03
---

# Decision: Default session_start to auto

## Context
The session-start hook detects new Entire sessions but originally only printed a reminder, requiring the developer to manually run `/reflect`. This added friction and meant context could go stale between sessions.

## Options Considered
1. **Auto (run /reflect automatically)** — zero friction, always-fresh context (CHOSEN)
2. **Manual (remind only)** — user stays in control of when analysis runs, but context drifts

## Decision
Default to `auto` so every new session starts with fresh context without manual intervention. Users who prefer control can set `session_start: manual` in `.reflect/config.yaml`. The cost of an automatic analysis is acceptable — it's a one-time delay at session start that pays for itself in context quality.

## Consequences
- Sessions always start with up-to-date context briefing
- Slightly slower session start when new sessions exist
- Users can opt out via config
