---
schema_version: "1.0"
id: keep-descriptions-aligned
title: Keep repo descriptions aligned across all surfaces
confidence: MEDIUM
created: 2026-04-03
last_seen: 2026-04-03
times_seen: 2
sessions: [e179abd8fa28, 56cd9d49]
category: anti-pattern
relevance_type: temporal
contradicts: null
contradicted_by: null
baked: false
baked_to: null
---

# Keep repo descriptions aligned across all surfaces

## Pattern
The GitHub repo description drifted from the README/CLAUDE.md/SKILL.md descriptions. Session e179abd8 refined docs for clarity, but the GitHub description wasn't updated until session 56cd9d49 caught the inconsistency. Multiple description surfaces (GitHub, README tagline, CLAUDE.md, SKILL.md frontmatter) need to stay in sync.

## Actionable Rule
When updating the project description or positioning, check all surfaces: GitHub repo description, README tagline, CLAUDE.md project section, and SKILL.md frontmatter description.

## Evidence Trail
- **2026-04-02 (e179abd8fa28)**: Refined CLAUDE.md and README descriptions but didn't update GitHub
- **2026-04-03 (56cd9d49)**: Caught stale GitHub description, aligned all surfaces

## Promotion History
- 2026-04-03: Created at MEDIUM (caused inconsistency across 2 sessions)
