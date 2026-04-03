# Migration Plan: Reflect v4 — Replaceable Harness, Zero Storage

## Context

The Meta-Harness paper (Stanford/MIT, 2026) proves that raw execution traces dramatically outperform LLM-generated summaries (56.7% vs 38.7%), and that hand-designed memory structures are inferior to letting agents search raw evidence. Our current reflect system does exactly what the paper warns against: it takes raw Entire transcripts and compresses them into predefined artifact types (sessions with YAML frontmatter, decisions with confidence levels, insights with categories/decay).

**Key insight: Entire already stores the raw evidence.** We don't need to copy it. The harness reads directly from Entire + git at context-generation time — no intermediate storage layer, no data duplication.

North star: **"memory system for the repo which is as plug and play as git itself"**

---

## New Architecture (Two Layers)

### Layer 1: Harness (replaceable script)
```
.reflect/
  harness             # executable script — reads evidence, writes context
  context.md          # output (generated, gitignored)
  config.yaml         # optional settings
  notes/              # manual annotations (optional)
    <slug>.md
```

That's the entire footprint. No evidence/, no sessions/, no decisions/, no insights/, no legacy/.

The harness reads directly from:
- **Entire CLI** (`entire explain`) — session transcripts, checkpoints, intents
- **Git** (`git log`, `git diff`, `git blame`) — commits, history, authorship
- **`.reflect/notes/`** — manual human annotations (if any)

Like `git log` reads from `.git/objects/` directly — you don't copy objects into a separate directory before querying them.

### Layer 2: CLI (plug and play)
```
reflect init                    # create .reflect/, install default harness
reflect context                 # run harness → write context.md (passive briefing)
reflect why <file-or-topic>     # fetch raw evidence matching query → stdout (active query)
reflect search <query>          # grep across Entire + git → stdout
reflect status                  # what evidence sources are available
reflect note "title"            # add a manual note to .reflect/notes/
```

No `reflect capture`. No adapters. No data copying. No migration. The harness fetches on demand.

### Two Distinct Read Paths

```
PASSIVE (pre-session briefing):
  reflect context → runs harness → writes context.md
  Harness controls what gets included, within a line budget.
  Optimizable, replaceable.

ACTIVE (live query):
  reflect why <topic> → fetches raw evidence → dumps to stdout
  reflect search <q>  → grep across sources → dumps matches
  No harness, no line budget. Raw evidence for the agent to reason over.
  The agent is the intelligence layer, not a script.
```

This distinction matters: the harness is for generating a *pre-computed briefing*. `why` and `search` are live queries where the agent needs raw evidence, not a filtered summary. Collapsing both into the harness would make `why` useless (just grep + line budget).

### Freshness Bookkeeping

```
.reflect/.last_run              # tiny state file
```

Contains: last Entire checkpoint ID, last git SHA, timestamp. The session-start hook compares this against current state — if changed, regenerate context.md. Avoids expensive full-rescan on every session start.

---

## How The Harness Works (Passive Read Path)

The harness generates `context.md` — the pre-session briefing. It runs before the agent starts working, not during.

### Interface Contract

```
.reflect/harness [flags]

Inputs:
  --max-lines <N>         Line budget for output (default: 150)
  --format <md|json>      Output format (default: md)

Reads from:
  - `entire explain` commands (if Entire is available)
  - `git log` / `git diff` (always available)
  - `.reflect/notes/*.md` (if any exist)

Writes to:
  - stdout (piped to .reflect/context.md by CLI)

Exit code: 0 on success, non-zero on failure
```

The CLI calls the harness. The harness produces context. That is the entire interface.

### Default Harness Behavior

Written in Python (stdlib only). What it does:

1. **Detect sources** — check if `entire` is on PATH, check git repo
2. **Fetch evidence on demand**:
   - `entire explain --short --search-all` → list all session intents
   - `entire explain --checkpoint <ID> --full` → full transcript (only for recent/relevant sessions)
   - `git log --oneline -20` → recent commits
3. **Rank by recency** — most recent first. No decay formula. Simple.
4. **Extract raw fragments** — intents, error messages, file paths, commit messages
5. **Generate context** — within line budget:
   - `## Recent Sessions` — last N sessions with intent and outcome
   - `## Recent Commits` — last N commits with messages
   - `## Notes` — manual notes (if any)
6. **Update `.reflect/.last_run`** — write current Entire checkpoint ID + git SHA for freshness tracking

What it does NOT do: confidence levels, categories, freshness decay, contradiction tracking, bake-in, file knowledge maps, data storage.

### Custom Harness Examples

A repo can replace `.reflect/harness` with anything:
- A script that uses an LLM to summarize sessions before generating context
- A script that implements the old decay/confidence model
- A script that runs embeddings for semantic search
- A script that fetches from additional sources (Slack, Linear, etc.)

The harness is code. It's versioned in git. It's replaceable. It's optimizable.

---

## How `why` and `search` Work (Active Read Path)

These are live queries. They bypass the harness entirely and give the agent raw evidence to reason over. No line budget, no filtering heuristics — just relevant raw data.

### `reflect why <file-or-topic>`

1. **Search Entire** — `entire explain --short --search-all`, find sessions mentioning the topic
2. **For matching sessions** — `entire explain --checkpoint <ID> --full` to get transcripts
3. **Search git** — `git log --all -- <file>` or `git log --grep=<topic>` for relevant commits
4. **Search notes** — grep `.reflect/notes/` for the topic
5. **Dump everything to stdout** — raw session transcripts, commit messages, notes. Ordered by recency.

The agent (Claude, Cursor, etc.) receives this raw evidence and reasons over it — constructing the "why" narrative itself. This is the Meta-Harness insight: the agent with raw trace access outperforms any pre-computed summary.

### `reflect search <query>`

1. Grep across all sources (Entire intents, git log, notes) for the query
2. Return matching fragments with source labels (session ID, commit SHA, note filename)
3. No ranking, no interpretation — just matches

---

## Config

```yaml
# .reflect/config.yaml (all optional)
max_lines: 150            # line budget for context.md
session_start: auto       # "auto" runs harness on session start; "manual" just reminds
```

No adapter config needed — the harness detects what's available at runtime.

---

## SKILL.md Rewrite

From 615 lines → ~120 lines. Becomes a thin conversational wrapper:

```
Parse $ARGUMENTS:
- `why <topic>` → `reflect why <topic>`, display output
- `search <query>` → `reflect search <query>`, display output
- `status` → `reflect status`, display output
- `context` → `reflect context`, confirm done
- Everything else → `reflect context`, show summary

Prerequisites: check `which reflect`, check `.reflect/` exists, suggest migrate if legacy detected.
```

**Removed**: All of Steps 2-5 (pattern extraction, decision extraction, cross-reference, write to knowledge store), entire Context command logic, bake workflow, template reading, validation gate.

**Preserved**: SessionStart hook, conversational UX, argument parsing.

---

## What Gets Deleted

| Item | Action |
|------|--------|
| `templates/session-format.md` | Delete |
| `templates/decision-format.md` | Delete |
| `templates/insight-format.md` | Delete |
| `templates/context-format.md` | Delete |
| `templates/file-knowledge-format.md` | Delete |
| `templates/` directory | Delete |
| `.reflect/` directory (current) | Delete entirely — clean slate |

No migration needed. No one uses the current v3 format yet. Just delete `.reflect/` and start fresh with `reflect init`.

---

## Phased Implementation

### Phase 1: Default Harness (proof of concept)
**Create**: `harness/default.py`
**Test**: Run it against this repo — it calls `entire explain` and `git log`, produces a context.md.
**Value**: Proves the on-demand-fetch architecture works. No CLI needed yet — just the script.

### Phase 2: CLI Skeleton
**Create**: `reflect` entry point, `lib/cli.py`, `lib/init.py`, `lib/context.py`, `lib/search.py`, `lib/why.py`
**Modify**: `install.sh` (add CLI to PATH)
**Test**: `reflect init && reflect context` on a fresh repo with git history.
**Value**: Working CLI, installable via `./install.sh`.

### Phase 3: Skill Rewrite
**Modify**: `SKILL.md` (rewrite to ~120 lines), `hooks/session-start.sh` (call `reflect context`)
**Test**: `/reflect` in Claude Code delegates to CLI.
**Value**: Skill works with new architecture.

### Phase 4: Docs + Cleanup
**Modify**: `SPEC.md` (rewrite to ~100 lines), `README.md`, `ROADMAP.md`, `evals/evals.json`
**Delete**: `templates/` directory, `.reflect/` (current v3 artifacts)
**Value**: Documentation matches reality. Clean slate.

---

## SPEC.md Rewrite (outline)

From 489 lines → ~100 lines. Defines:
- `.reflect/` directory layout (harness, context.md, config.yaml, notes/)
- Harness contract (interface, inputs, outputs, exit codes)
- Config format
- Git conventions (what to commit, what to gitignore)
- Security (no secrets in notes or context)

Removes everything else: artifact schemas, freshness model, confidence levels, contradiction handling, context section contracts, schema versioning.

---

## Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Entire not installed → no session evidence | Git history is always available. Harness degrades gracefully to git-only context. |
| Harness is slow (calling `entire explain` each time) | `.last_run` state file tracks last checkpoint ID + git SHA. Session-start hook skips regeneration if nothing changed. |
| Default harness too simple | Can still be smart at read-time (count patterns, regex for errors, rank by recency). Key: heuristics in replaceable code, not baked spec. |
| No trust/provenance layer | Deferred to team workflows phase. For single-dev, recency handles contradictions naturally. Trust boundaries needed when adding multi-source adapters. |
| Losing bake-in workflow | Users manually promote to CLAUDE.md, or a custom harness implements it. Not blocked. |
| Entire CLI output format changes | Harness is a script — update it. No rigid schema to break. |
| `why` dumps too much raw evidence | Agent has context limits and handles selective reading. Future: add `--limit` flag. |

---

## Verification Plan

1. **Harness standalone**: `python3 harness/default.py` on this repo → produces usable context from Entire + git
2. **Git-only mode**: On a repo without Entire → harness produces context from git history alone
3. **Fresh init**: `reflect init` on new repo → .reflect/ created with harness + config
4. **Context generation**: `reflect context` → runs harness, writes context.md, updates .last_run
5. **Why (active query)**: `reflect why SKILL.md` → dumps raw session transcripts and git history about SKILL.md to stdout (bypasses harness)
6. **Search**: `reflect search "meta harness"` → grep matches from Entire intents + git log + notes
7. **Custom harness**: Replace .reflect/harness with `echo "custom"` → `reflect context` produces "custom" (does not affect `why`/`search`)
8. **Freshness tracking**: Run `reflect context` twice — second run skips regeneration because .last_run matches current state
9. **Skill integration**: `/reflect` in Claude Code → delegates to CLI
10. **Session hook**: New session → hook checks .last_run vs current state → regenerates only if changed

---

## Critical Files

| File | Current | After |
|------|---------|-------|
| `SKILL.md` | 615 lines, 8 commands, full analysis pipeline | ~120 lines, thin wrapper around CLI |
| `SPEC.md` | 489 lines, 4 artifact schemas, decay model | ~100 lines, harness contract + directory layout |
| `templates/` | 5 template files | Deleted |
| `hooks/session-start.sh` | 77 lines, checks Entire | Updated to call `reflect context` |
| `install.sh` | 14 lines, symlinks skill | Extended to also install CLI to PATH |
| `README.md` | 330 lines | Updated (commands, harness, no storage layer) |
| `ROADMAP.md` | 214 lines | Rewritten (new phases) |
| **New**: `reflect` | — | CLI entry point (Python) |
| **New**: `lib/` | — | CLI modules (cli, init, context, search, why) |
| **New**: `harness/default.py` | — | Default harness script |

---

## What This Means

The old reflect: **capture → interpret → store → retrieve → present** (5 steps, opinionated at every stage)
The new reflect: **fetch → present** (2 steps, opinions only in the replaceable harness)

Entire owns the write path. Git owns the history. Reflect owns one thing: **the harness that turns raw evidence into the right context for right now.** That harness is a replaceable program — the part the Meta-Harness paper says matters most.

Zero storage. Zero migration. Zero opinions baked into the spec. Just a script that reads what's already there.
