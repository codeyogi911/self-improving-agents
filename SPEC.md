# `.reflect/` Specification

**Version**: 2.0.0

This document specifies the `.reflect/` directory format — a minimal,
repo-owned interface for AI coding agent memory.

---

## 1. Design Principles

1. **Zero storage**: `.reflect/` does not duplicate evidence. It reads from
   Entire CLI and git on demand.
2. **Replaceable harness**: Context generation is a script, not a schema.
   Different repos can have different harnesses.
3. **Plug and play**: `reflect init` in any git repo. No external dependencies
   required (Entire CLI is optional enrichment).
4. **Human-reviewable**: All files are plain text. The harness is readable code.
5. **Agent-agnostic**: `context.md` is plain Markdown, readable by any tool.

---

## 2. Directory Layout

```
.reflect/
├── harness             # Executable script that generates context.md (REQUIRED)
├── context.md          # Generated briefing for agent consumption (GENERATED)
├── config.yaml         # Optional configuration
├── .last_run           # Freshness state (GENERATED, gitignored)
└── notes/              # Manual annotations (optional)
    └── <slug>.md
```

---

## 3. Harness Contract

The harness is an executable file at `.reflect/harness`. Any language.

**Interface**:
```
.reflect/harness [--max-lines N] [--format md|json]

stdin:  none
stdout: generated context (Markdown or JSON)
exit:   0 on success, non-zero on failure
```

**Reads from** (at runtime, not from stored files):
- Entire CLI commands (`entire explain`, `entire status`)
- Git commands (`git log`, `git diff`, `git blame`)
- `.reflect/notes/*.md`

**Writes**:
- Context to stdout
- `.reflect/.last_run` state file (for freshness tracking)

The harness is committed to git. It ships with a sensible default. Repos
replace it to customize context generation — this is the part that can be
optimized, A/B tested, or auto-evolved.

---

## 4. Two Read Paths

### Passive (pre-session briefing)
`reflect context` runs the harness and writes `context.md`. This is the
pre-computed briefing that gets wired into instruction files (CLAUDE.md,
.cursorrules, etc.).

### Active (live query)
`reflect why <topic>` and `reflect search <query>` bypass the harness.
They fetch raw evidence from Entire + git and dump it to stdout. The agent
reasons over raw evidence — no line budget, no filtering.

---

## 5. Configuration

**Location**: `.reflect/config.yaml` (optional)

```yaml
max_lines: 150            # Line budget for context.md
session_start: auto       # "auto" regenerates on session start; "manual" reminds
```

---

## 6. Freshness Tracking

**Location**: `.reflect/.last_run` (generated, gitignored)

```json
{
  "last_checkpoint": "<entire-checkpoint-id>",
  "last_git_sha": "<short-sha>",
  "timestamp": "<ISO-8601>"
}
```

The session-start hook compares this against current state to decide whether
to regenerate context.md.

---

## 7. Git Conventions

**Commit**: `.reflect/harness`, `.reflect/config.yaml`, `.reflect/notes/`
**Gitignore**: `.reflect/context.md`, `.reflect/.last_run`

---

## 8. Security

- Never store credentials, API keys, or secrets in notes or context output.
- The harness should not log sensitive data from session transcripts.
- Notes are human-authored — review before committing.

---

## Changelog

### 2.0.0 (2026-04-03)
- Complete architecture redesign: zero storage, replaceable harness.
- Removed: artifact schemas, freshness decay model, confidence levels,
  contradiction handling, trace index, file knowledge maps.
- Added: harness contract, two read paths, freshness tracking.
- Evidence is read on demand from Entire CLI + git, not stored in `.reflect/`.
