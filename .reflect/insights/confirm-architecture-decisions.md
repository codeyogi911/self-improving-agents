---
schema_version: "1.0"
id: confirm-architecture-decisions
title: Confirm architecture decisions with user before implementing
confidence: HIGH
created: 2026-04-02
last_seen: 2026-04-03
times_seen: 2
sessions: [3f10d4ade5ea, 56cd9d49]
category: best-practice
relevance_type: architectural
contradicts: null
contradicted_by: null
baked: true
baked_to: CLAUDE.md
---

# Confirm architecture decisions with user before implementing

## Pattern
Changes that affect core architecture (learning mechanism, data flow, required dependencies) should be confirmed with the user before implementation. Session 56cd9d49 demonstrated this well — the auto/manual config was proposed, user confirmed, then default was changed per user preference.

## Actionable Rule
For changes that affect core architecture (learning mechanism, data flow, required dependencies), confirm the design decision (optional vs required, additive vs replacement) with the user before implementing.

## Evidence Trail
- **2026-04-02 (3f10d4ade5ea)**: First /reflect run identified this as a best practice
- **2026-04-03 (56cd9d49)**: Confirmed in practice — proposed manual default, user said auto, adjusted

## Promotion History
- 2026-04-02: Created at MEDIUM (observed pattern)
- 2026-04-02: Promoted to HIGH (baked into CLAUDE.md)
