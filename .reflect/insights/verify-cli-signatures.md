---
schema_version: "1.0"
id: verify-cli-signatures
title: Always verify CLI command signatures before documenting
confidence: HIGH
created: 2026-04-02
last_seen: 2026-04-02
times_seen: 2
sessions: [3f10d4ade5ea, 073406f183b0]
category: anti-pattern
relevance_type: architectural
contradicts: null
contradicted_by: null
baked: true
baked_to: CLAUDE.md
---

# Always verify CLI command signatures before documenting

## Pattern
Across multiple sessions, CLI install/usage commands were written assuming flag syntax without verifying against `--help` or docs. Session 073406f1 caught wrong Entire CLI install instructions that had been assumed rather than verified.

## Actionable Rule
When writing code that shells out to external CLIs or APIs, verify available commands/endpoints with `--help` or reference docs before implementation — don't assume command signatures.

## Evidence Trail
- **2026-04-02 (3f10d4ade5ea)**: First /reflect run identified this pattern from earlier sessions
- **2026-04-02 (073406f183b0)**: User caught incorrect Entire CLI install instructions — commands were assumed

## Promotion History
- 2026-04-02: Created at MEDIUM (caused incorrect documentation)
- 2026-04-02: Promoted to HIGH (seen in 2 sessions, baked into CLAUDE.md)
