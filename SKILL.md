---
name: reflect
description: >
  Analyze Claude Code session transcripts captured by Entire CLI. Extracts
  patterns (retry loops, research gaps, what worked, what took too long),
  produces structured reflections, and optionally bakes validated insights
  into your CLAUDE.md or agent files. Use when: user asks to analyze sessions,
  reflect on past work, review what happened, improve agents from transcripts,
  mine session history, or check what went wrong. Also trigger on "reflect",
  "session analysis", "what went wrong", "what can I improve".
allowed-tools: Read, Edit, Bash, Glob, Grep
metadata:
  author: shashwatjain
  version: '1.0'
---

# Reflect — Session Transcript Analysis

You analyze session transcripts captured by Entire CLI, extract patterns,
and produce structured reflections. You work with whatever the user already
has — CLAUDE.md, agent files, or nothing at all.

If $ARGUMENTS is provided, use it to scope the analysis (e.g., "last 3 sessions",
"and bake", a specific session ID). If empty, analyze the last 5 sessions.

---

## Step 1: Prerequisites

1. Check if Entire CLI is installed:
   ```bash
   which entire || test -f ~/.local/bin/entire
   ```
   If NOT found → tell the user: "Entire CLI is required for session analysis.
   Install it from https://entire.io" and stop.

2. Run `entire status` to check for session history.
   If no sessions exist → report "No session history available yet. Run some
   sessions first, then come back to reflect." and stop.

---

## Step 2: Gather Session Data

1. Run `entire status` for a session overview (current position, session count).

2. Run `entire explain` to get session and commit details. This is your primary
   analysis tool — it shows what happened in each session.

3. Parse $ARGUMENTS for scope:
   - "last N sessions" or "last N" → limit to N most recent
   - A session ID → analyze only that session
   - "and bake" → auto-proceed to bake-in after analysis (skip confirmation)
   - No scope specified → default to last 5 sessions
   - Cap at 10 sessions per run to keep context manageable

---

## Step 3: Pattern Extraction

Parse the session data looking for these patterns:

### Problems

- **Retry loops** — same file edited 3+ times in a session (thrashing)
- **Research-then-fail** — investigation happened but the build still failed
  (research was insufficient or ignored)
- **Verification ping-pong** — rejected, fixed, rejected again (unclear spec
  or persistent bad pattern)
- **Long tool chains** — many sequential Bash/Read/Grep calls with no Write
  (exploration without progress)
- **Token-heavy sessions** — high token count relative to files changed
  (efficiency problem)
- **Compaction frequency** — frequent context compression events suggest
  agents are consuming too much context

### Successes

- **Clean first-pass completions** — tasks that succeeded on the first try
  (what made them work?)
- **Effective research** — research phase that prevented build failures
- **Fast iterations** — short build-verify cycles that converged quickly

### Opportunities

- **Escalation resolutions** — how the human resolved an escalation (gold
  for future automation)
- **Time sinks** — tasks that took disproportionate effort relative to their
  complexity
- **Repeated manual steps** — things the human had to do repeatedly that
  could be automated

---

## Step 4: Cross-Reference & Confidence

1. Read `.claude/reflections.md` if it exists — check for recurring patterns
   from prior runs. If a MEDIUM confidence pattern from a prior reflection
   appears again, upgrade it to HIGH.

2. Read `CLAUDE.md` if it exists — check for insights already captured.
   Don't duplicate what's already known.

3. Run `ls .claude/agents/ 2>/dev/null` — if agent files exist, read their
   `## Project-Specific Rules` sections to check for overlap.

4. Assign confidence to each insight:
   - **HIGH** — pattern seen across 2+ sessions, or caused significant rework
     (>3 retries), or confirmed by prior MEDIUM reflection
   - **MEDIUM** — seen in one session but significant (caused failure or
     major time sink)
   - **LOW** — minor or uncertain pattern

---

## Step 5: Write Reflection

Read the reflection format template from `templates/reflection-format.md`
(located in the same directory as this SKILL.md file).

Write the reflection to `.claude/reflections.md`:
- If the file exists, insert the new reflection at the top (after the header)
- If the file doesn't exist, create it with a header and the first reflection
- Keep the file to a reasonable size — if it exceeds 50 entries, summarize
  the oldest entries into a `## Historical Patterns` section at the bottom

Display a summary to the user showing:
- Sessions analyzed (count and IDs)
- Key patterns found (top 3-5)
- HIGH confidence insights with recommended actions

---

## Step 6: Bake Insights (Optional)

If $ARGUMENTS contains "and bake", or the user confirms when asked:

For each HIGH confidence insight:

1. **Determine the target file:**
   - If the insight maps to a specific agent and `.claude/agents/{agent}.md`
     exists → target that agent file
   - If the insight is project-wide or no agents exist → target `CLAUDE.md`
   - Never create new agent files — only append to existing ones

2. **Bake into the target:**
   - For agent files: append to the `## Project-Specific Rules` section
     (create the section if it doesn't exist)
   - For CLAUDE.md: append to a `## Session Insights` section
     (create the section if it doesn't exist)
   - Write the insight as a clear, actionable instruction — not a note
   - Check that a substantially similar insight isn't already baked in

3. **Log what was baked** in the reflection entry (mark insights as BAKED)

If $ARGUMENTS does NOT contain "and bake":
- Show HIGH confidence insights and ask: "Would you like to bake these
  insights into your project files?"
- If yes → proceed with bake-in
- If no → done, insights are saved in reflections.md for future reference

---

## Rules

- NEVER read `.entire/metadata/` directly — always use Entire CLI commands
- Cite session IDs for every pattern so findings are traceable
- Focus on actionable insights, not statistics for statistics' sake
- If no meaningful patterns emerge, say so — don't fabricate insights
- Don't duplicate insights already in CLAUDE.md or agent Project-Specific Rules
- Keep reflections.md entries concise — quality over quantity
