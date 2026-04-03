# Reflect Roadmap

**`git` answers "what changed." `reflect` answers "why."**

Git tells you what happened: diffs, commits, blame. But it can't tell you why a
decision was made, why an approach was abandoned, or why a file exists the way it
does. That context lives in session transcripts, PR threads, and people's heads —
it doesn't travel with the code.

Reflect puts the "why" in the repo. Structured, versioned, readable by any agent
or human. The same way `git log` is the reflex for "what happened here?",
`reflect why` should be the reflex for "why is it this way?"

---

## Current State

- A Claude Code skill that reads Entire CLI session transcripts
- Writes structured markdown evidence to `.reflect/`
- Auto-wires `context.md` into `CLAUDE.md` for session briefings
- SessionStart hook keeps context fresh

**What works:** The analysis engine and evidence format are solid.
**What's missing:** It only works in Claude Code, only captures from Entire CLI,
and requires manual invocation.

---

## Design Principles

1. **Files are the interface.** `.reflect/` is plain markdown. Any tool that can
   read files gets the knowledge. No server, no protocol, no runtime dependency.
2. **One writer at a time.** The CLI is the single entry point for writes —
   enforces idempotency, locking, and deduplication in one place.
3. **Evidence has provenance.** Every record knows where it came from (session
   transcript, commit, PR, manual entry) and how much to trust it.
4. **Instruction files are the delivery mechanism.** Every AI tool reads a
   project instructions file. Wire `context.md` into all of them — that's the
   universal read path.
5. **Entire is the premium path, not a gate.** Full transcript analysis is the
   richest evidence source, but reflect works without it.

---

## Phase 1: Universal Read Path

**Goal:** Any AI coding tool gets the briefing automatically.

Right now, context.md is wired into `CLAUDE.md` only. Extend to every
instruction file format:

| File | Tool |
|------|------|
| `CLAUDE.md` | Claude Code (already done) |
| `.cursor/rules/*.mdc` | Cursor |
| `.github/copilot-instructions.md` | GitHub Copilot |
| `.windsurfrules` | Windsurf |
| `.clinerules` | Cline |

The skill already auto-wires CLAUDE.md on first run. Do the same for whichever
instruction files exist in the project. This is the highest-leverage change:
small effort, every tool benefits immediately.

**Also:** Make context.md self-contained enough that even tools with no special
integration get value from a human pasting it into their context window.

---

## Phase 2: `reflect` CLI

**Goal:** `reflect` becomes a command any agent (or human) can run, like `git`.

The skill stays as the Claude Code entry point. But the core logic moves into a
standalone CLI that any agent can invoke via bash:

```
reflect why src/auth/middleware.ts    # decision trail with receipts
reflect brief auth                   # task-focused context
reflect search "database migration"  # grep across evidence
reflect context                      # regenerate briefing
reflect status                       # evidence store stats
reflect record decision "..."        # write a decision (with provenance)
reflect record insight "..."         # write an insight (with provenance)
reflect analyze                      # full session analysis (needs Entire)
```

Every AI agent has bash access. No protocol adapter needed.

**Write consistency model:** All writes go through the CLI. The CLI validates
input, assigns content-addressable IDs (hash of source + timestamp),
deduplicates, and enforces the schema. Concurrency rules:

- **Local writes** (hooks, skill, manual): a lockfile serializes access. In
  practice these are sequential — you commit, the hook fires, later you run
  reflect.
- **Remote writes** (GitHub Actions, CI): never push directly to `.reflect/`.
  Open a PR instead, so the human reviews what enters the evidence store.
- **ID generation**: deterministic from source content + timestamp, so the same
  evidence written twice produces the same ID and is deduplicated.

**The skill becomes a thin wrapper** that calls the CLI under the hood, adding
the conversational UX (summary output, bake-in prompts, session-start hooks).

---

## Phase 3: Passive Evidence Capture

**Goal:** The "why" accumulates without the developer doing anything special.

### Git hooks (no Entire required)

A `post-commit` hook that extracts structured evidence from commits:

- AI-generated commits tend to be descriptive — parse intent, files, approach
- Conventional commits (`feat:`, `fix:`, `refactor:`) carry signal
- Merge commits from PRs carry the PR body as context

This makes reflect useful from day one in any repo, without Entire.

### Entire CLI (premium path)

Full transcript analysis remains the richest source — it captures the reasoning
process, not just the outcome. But it's an enhancer, not a prerequisite.

### Provenance model

Every evidence record carries:

| Field | Purpose |
|-------|---------|
| `source` | Where it came from: `entire-session`, `git-commit`, `pr-merge`, `manual` |
| `trust` | `verified` (human-confirmed), `inferred` (agent-extracted), `raw` (unreviewed) |
| `author` | Who or what wrote it |

**Trust boundary — evidence store vs instruction files:**

- **`context.md`** (the briefing) can include all trust levels. It's regenerated
  every session and is a read-only overlay — not an instruction file. Inferred
  evidence is surfaced with its provenance so the agent knows the source.
- **Instruction files** (`CLAUDE.md`, `.cursorrules`, etc.) are the high-trust
  zone. Bake-in **always requires human approval** — no auto-bake regardless of
  how many times a pattern is seen. Only `verified` evidence (from Entire
  transcript analysis with a human in the loop) is eligible for bake-in.
- **Inferred evidence** (from commits, PRs) is queryable via `reflect why`,
  `reflect search`, `reflect brief` — but never promoted to instruction files.

This prevents the prompt injection vector where repeated bad commit messages
could auto-promote into agent instructions. The evidence store is open to all
sources; instruction files are human-gated, verified-only.

---

## Phase 4: Zero-Effort Learning Loop

**Goal:** Developer does nothing. Memory accumulates and stays fresh.

1. **SessionStart hook** (exists) → regenerates context.md from evidence
2. **Post-commit hook** (Phase 3) → captures decisions from commits
3. **Scheduled analysis** → periodic full `/reflect` via cron for repos with Entire
4. **Bake-in nudges** → when verified insights hit HIGH confidence, the skill
   surfaces them and asks the human to approve bake-in. Never automatic.

The only manual action: approving bake-ins when prompted. The evidence
accumulates passively; the promotion to instruction files stays human-gated.

---

## Phase 5: Team Workflows

**Goal:** The "why" is shared, not just local.

1. **GitHub Action on PR merge** — parses PR description + review comments,
   writes decision/session records. Team discussions become project memory.
2. **PR review bot** — comments on PRs with relevant decisions for changed files.
   "FYI: decision #0003 explains why this file uses the adapter pattern."
3. **Onboarding briefing** — `reflect onboard` generates a comprehensive
   "here's everything you need to know" for someone new to the repo.

**Scope boundary:** All evidence stays within its repo. No cross-repo leakage.
If org-level patterns are needed later, they get their own explicit opt-in
mechanism with namespace isolation.

---

## Priority Matrix

| Priority | Item | Effort | Impact |
|----------|------|--------|--------|
| **P0** | Multi-tool instruction file wiring | Small | Every AI tool gets the briefing |
| **P0** | `reflect` CLI | Medium | Universal write/query interface |
| **P1** | Git hook passive capture | Small | Works without Entire |
| **P1** | Provenance + trust model in SPEC.md | Small | Prevents evidence poisoning |
| **P2** | GitHub Action for PR merge | Medium | Team-level evidence capture |
| **P2** | Bake-in nudges (human-gated) | Small | Surfaces insights for approval |
| **P3** | PR review bot | Medium | Surfaces "why" in code review |
| **P3** | Onboarding briefing | Small | New contributor experience |

---

## The Analogy

```
git log       → what happened
git blame     → who changed this line
git bisect    → which commit broke it

reflect why   → why is it this way
reflect brief → what do I need to know for this task
reflect what-failed → what went wrong before
```

Git is infrastructure you never think about — it just works, captures everything,
and answers questions when you ask. Reflect should be the same for the "why."
