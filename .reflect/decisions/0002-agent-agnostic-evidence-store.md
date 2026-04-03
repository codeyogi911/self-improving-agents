---
schema_version: "1.0"
id: "0002"
title: Agent-agnostic evidence store format
date: 2026-04-02
status: accepted
sessions: [14431d424b86, 3f10d4ade5ea]
files: [SPEC.md, README.md]
superseded_by: null
confidence: HIGH
last_validated: 2026-04-03
---

# Decision: Agent-agnostic evidence store format

## Context
The /reflect skill started as Claude Code-specific. As the project matured, the question arose whether `.reflect/` should be tied to Claude Code or designed for any AI coding agent.

## Options Considered
1. **Agent-agnostic format** — plain Markdown + YAML frontmatter, readable by any tool (CHOSEN)
2. **Claude-specific format** — tighter integration but vendor lock-in
3. **JSON/structured format** — machine-friendly but not human-reviewable

## Decision
Use an agent-agnostic format (plain Markdown with YAML frontmatter) documented in SPEC.md. This makes `.reflect/` portable across Claude Code, Cursor, and any future agent. The spec is independent of the skill — any compliant tool can read/write to the store.

## Consequences
- Any AI coding tool can consume the evidence store
- Human-reviewable in PRs and git diffs
- Slightly more complex to parse than structured JSON
- SPEC.md serves as the contract for interoperability
