---
name: reflect
description: >
  Repo-owned memory for AI coding agents. Reads raw evidence from Entire CLI
  sessions and git history on demand via a replaceable harness. Generates
  context briefings, answers "why" queries with raw evidence, and searches
  across all sources. Commands: /reflect (regenerate context), /reflect why
  <file-or-topic>, /reflect search <query>, /reflect status.
  Trigger on "reflect", "why did we", "what happened", "session history",
  "what do I need to know".
allowed-tools: Read, Bash, Glob, Grep
hooks:
  SessionStart:
    - hooks:
        - type: command
          command: "${CLAUDE_PLUGIN_ROOT}/hooks/session-start.sh"
metadata:
  author: shashwatjain
  version: '4.0'
---

# Reflect — Repo-Owned Memory

You help users query and manage repo-owned memory for AI coding agents.
Reflect reads raw evidence from Entire CLI sessions and git history on demand
— no intermediate storage, no interpretation layer. A replaceable harness
script generates context briefings; live queries dump raw evidence for you
to reason over.

Parse $ARGUMENTS to determine which command to run:

1. `why <file-or-topic>` → go to **Command: Why**
2. `search <query>` → go to **Command: Search**
3. `status` → go to **Command: Status**
4. `context` → go to **Command: Context**
5. `note <title>` → go to **Command: Note**
6. Everything else (including no arguments) → go to **Command: Context**

---

## Step 0: Prerequisites

1. Check if `reflect` CLI is installed:
   ```bash
   which reflect
   ```
   If NOT found → tell the user:
   > "The reflect CLI is not installed. Run the installer from the reflect repo:
   > ```bash
   > cd <path-to-reflect-repo> && ./install.sh
   > ```"
   and stop.

2. Check if `.reflect/` exists in the project root:
   ```bash
   test -d .reflect
   ```
   If NOT found → run `reflect init` to set it up.

3. **Auto-wire context loading**: If `CLAUDE.md` exists and does not contain
   `@.reflect/context.md`, append that line. This ensures the context briefing
   is loaded in every future session. Do this silently.

---

## Command: Context (default)

Run the harness to regenerate the context briefing:

```bash
reflect context
```

Report the result to the user: "Context briefing updated."

If the **SessionStart hook** output contains `REFLECT_AUTO_RUN`, run this
command automatically without user prompting. This keeps the briefing fresh.

---

## Command: Why

**Usage**: `/reflect why <file-or-topic>`

This is a live query — it dumps raw evidence for you to reason over.

```bash
reflect why <file-or-topic>
```

Read the output and present it as a structured narrative:
- What sessions touched this file/topic and what happened
- What decisions were made and why
- What went wrong (if anything)
- What the user should know going forward

**You are the intelligence layer.** The CLI gives you raw evidence; you
construct the "why" story. This is the key design: raw traces outperform
pre-computed summaries (Meta-Harness, 2026).

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

## Command: Note

**Usage**: `/reflect note <title>`

```bash
echo "<content>" | reflect note <title>
```

Or interactively help the user write a note and pipe it in.

---

## Rules

- NEVER read `.entire/metadata/` directly — use `reflect` CLI or `entire` CLI
- When running `/reflect why`, read the raw output and synthesize a narrative
- The harness at `.reflect/harness` is replaceable — if the user wants to
  customize context generation, point them to that file
- `.reflect/context.md` is generated — never edit it manually
- NEVER include secrets, API keys, or credentials in notes or output
