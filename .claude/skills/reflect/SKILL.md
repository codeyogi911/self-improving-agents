---
name: reflect
description: >
  Answers questions about project history, past decisions, and how things
  evolved. Use this skill whenever the user asks "why" about code, files,
  architecture, or decisions — e.g., "why was this file deleted", "why did
  we switch to X", "what happened with Y", "who changed Z and why". Also
  use for retrospectives, post-mortems, understanding past sessions, learning
  from recent work, onboarding context ("what do I need to know about this
  repo"), and any question that is best answered by consulting git history
  or past AI session transcripts. Even if the user doesn't say "reflect" or
  "history" explicitly, if the answer lives in the past — use this skill.
  Commands: /reflect, /reflect search <query>, /reflect status,
  /reflect sessions [session_id], /reflect timeline, /reflect improve.
allowed-tools: Read, Bash, Glob, Grep
hooks:
  SessionStart:
    - hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
metadata:
  author: shashwatjain
  version: '5.1'
---

# Reflect — Repo-Owned Memory

You help users query and manage repo-owned memory for AI coding agents.
Reflect reads raw evidence from Entire CLI sessions and git history on demand
— no intermediate storage. A declarative `format.yaml` controls what sections
appear in the context briefing; a Claude subagent synthesizes high-quality
briefings with references. Live queries dump raw evidence for you to reason over.

Parse $ARGUMENTS to determine which command to run:

1. `search <query>` → go to **Command: Search**
2. `status` → go to **Command: Status**
3. `context` → go to **Command: Context**
4. `sessions [session_id]` → go to **Command: Sessions**
5. `timeline` → go to **Command: Timeline**
6. `improve` → go to **Command: Improve**
7. Everything else (including no arguments) → go to **Command: Context**

---

## Command: Context (default)

Regenerate the context briefing:

```bash
reflect context
```

This gathers evidence from Entire CLI + git, passes it through the subagent
with the format config, validates output (citations, line budget), and writes
`context.md`. Falls back to deterministic rendering if Claude CLI is unavailable.

Report the result to the user: "Context briefing updated."

If the **SessionStart hook** output contains `REFLECT_AUTO_RUN`, run this
command automatically without user prompting. This keeps the briefing fresh.

---

## Command: Search

**Usage**: `/reflect search <query>`

```bash
reflect search <query>
```

Display the results to the user with source labels.

---

## Command: Status

**Usage**: `/reflect status`

```bash
reflect status
```

Display the output. If no evidence sources are found, suggest next steps.

---

## Command: Sessions

**Usage**: `/reflect sessions [session_id]`

```bash
reflect sessions
reflect sessions <session_id>
```

Use this after `reflect search` or `reflect timeline` when you need to move
from broad evidence into a specific Entire session. Without an ID, list recent
sessions. With an ID or prefix, inspect one session in detail.

---

## Command: Timeline

**Usage**: `/reflect timeline [--days N]`

```bash
reflect timeline
reflect timeline --days 14
```

Use this for time-bounded questions such as "what changed this week" or "what
happened before the revert". It groups recent sessions and checkpoints by date
so you can quickly identify the right period before drilling deeper.

---

## Command: Improve

**Usage**: `/reflect improve`

Analyzes context quality and proposes format.yaml changes. This is the self-improvement loop.

```bash
reflect improve
```

Read the full output. It contains:

1. **Context Quality Issues** — missing citations, truncation, empty sections
2. **Evidence Gaps** — signals in sessions that didn't make it into context
3. **Current format.yaml** — the section config to edit

Based on the analysis:

1. Propose specific edits to `.reflect/format.yaml` — add/remove/rename sections,
   adjust max_bullets, change recency windows
2. Show the user the diff and explain why each change helps
3. After approval, apply the edits and re-run `reflect context` to verify
4. Run `reflect improve` again to confirm the issues are resolved

**This is the core learning loop**: the format controls what gets synthesized,
the improve command evaluates quality against real evidence, and the user
tunes sections to match what their project actually needs.

---

## Deep History: Timeline, Sessions, Entire, Git

Use this short evidence ladder when the answer needs more than the current
briefing:

1. Start with `.reflect/context.md` as the briefing. It is the fastest way to
   get the current narrative and references.
2. Run `reflect status` if you are not sure whether Entire-backed evidence is
   available in this repo.
3. Run `reflect search <query>` for breadth across aggregated evidence when
   you are still locating the right topic, checkpoint, or session.
4. Run `reflect timeline` for time-bounded questions, especially when the user
   cares about a recent window or the order of events.
5. Run `reflect sessions` after search or timeline when you need to navigate by
   session, inspect one session, or pick the right ID before going deeper.
6. Run `entire explain --checkpoint <id>` or `entire explain --commit <sha>`
   once you already have an ID and need transcript-level depth.
7. Use `git log` and `git show` as supplements for commit metadata and diffs.
   Git is useful context, but weak on its own for reconstructing agent
   reasoning or backtracking.

This ladder is also the default workflow for the **Keeper** agent.

---

## Digging Deeper

`context.md` is a briefing — a starting point, not the full story. When an entry
is relevant to your current task, spawn the **Keeper** agent to investigate.
Keeper should read this skill first so it inherits the same command semantics,
then follow the evidence ladder above: start from `context.md`, use
`reflect search`, `reflect timeline`, or `reflect sessions` to locate the right
evidence, and only then drill into raw checkpoints with `entire explain` and
cross-check with git as needed. Keeper returns a sourced narrative.

Spawn Keeper when:

- A context.md entry relates to what you're about to change
- You need to trace a decision across multiple sessions
- You want to understand what was tried vs what landed
- An entry about pitfalls or reverted work is a STOP signal — let Keeper
  verify the constraint before you proceed

---

## Rules

- NEVER read `.entire/metadata/` directly — use `reflect` CLI or `entire` CLI
- To customize context, edit `.reflect/format.yaml` — add project-specific sections
- `.reflect/context.md` is generated — never edit it manually
- NEVER include secrets, API keys, or credentials in output
- **Pitfall/mistake entries are blocking**: if context.md lists a past mistake or revert
  for the area you're about to change, read the linked evidence BEFORE writing code
