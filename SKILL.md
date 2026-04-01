---
name: self-improving-agents
description: >
  Scaffold a self-improving agentic harness into any project. Creates
  orchestrator, builder, verifier, e2e-tester, and researcher agents with
  iterative build loops, two-gate verification, gap tracking, and cross-session
  learning. Use when: user asks to set up self-improving agents, create an agent
  harness, add build loops, scaffold agent infrastructure, wants agents that
  learn from mistakes, or wants an iterative build-verify-test workflow.
  Also trigger when user mentions "build loop", "agent harness", "self-improving",
  or wants to add structured agent coordination to their project.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, Agent, WebSearch, WebFetch
metadata:
  author: shashwatjain
  version: '3.0'
---

# Self-Improving Agents Harness

You are scaffolding a self-improving agentic harness into the user's project.
The harness runs iterative build loops — agents build, verify, test, and
improve, learning from each cycle and getting better across sessions.

If $ARGUMENTS is provided, use it as the initial goal.
If empty, scaffold in generic mode and ask the user for their goal afterward.

---

## Step 1: Analyze Target Project

1. Read `CLAUDE.md` if it exists — understand project conventions
2. Detect stack by checking for: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Gemfile`, `pom.xml`, `Makefile`
   - Identify: language, framework, test runner, package manager, linter/formatter
3. Scan directory structure with `ls` and `Glob` to understand project layout
4. Check `.claude/` directory for existing state:
   - If agent files exist with `## Learnings` content → **extract and preserve all learnings**
   - If `gaps.md` exists → **do NOT overwrite** (cross-session state)
   - If `progress.md` exists → **do NOT overwrite** (cross-session state)
5. Check for e2e test setup (Playwright, Cypress, Selenium, etc.)

**Note your findings** (you'll use these to customize agent files in Step 3):
- Language: __ | Framework: __ | Test runner: __ | Pkg manager: __
- E2E framework: __ or "none" | Linter: __ or "none"
- Existing learnings to preserve: yes/no

If you can't detect a value, leave it as "none" — the agent templates work
without project-specific customization, it just makes them more effective.

---

## Step 2: Create Directory Structure

```bash
mkdir -p .claude/agents
```

---

## Step 3: Write Agent Files

Read each template from the skill's `templates/` directory, customize for this
project, and write to `.claude/agents/`.

The skill's templates directory is located at the same path as this SKILL.md
file, under `templates/`. Read each template file listed below.

### For each agent file:

1. Read the template from `templates/{agent}.md`
2. If an existing `.claude/agents/{agent}.md` has `## Learnings` content,
   extract those entries — they represent hard-won knowledge from prior runs
3. Write the template content to `.claude/agents/{agent}.md`
4. If learnings were extracted in step 2, append them under `## Learnings`

### Agent files to create:

| Template | Target | Purpose |
|----------|--------|---------|
| `templates/orchestrator.md` | `.claude/agents/orchestrator.md` | Coordinates build loops, dispatches to other agents |
| `templates/builder.md` | `.claude/agents/builder.md` | Writes code, runs tests, reports changes |
| `templates/verifier.md` | `.claude/agents/verifier.md` | Two-gate review: spec compliance then code quality |
| `templates/e2e-tester.md` | `.claude/agents/e2e-tester.md` | End-to-end testing, failure classification |
| `templates/researcher.md` | `.claude/agents/researcher.md` | Pre-build investigation of APIs, patterns, docs |

### Project-specific customization

After writing each agent file, apply these customizations if the project
analysis detected specific tools. Skip if values are "none".

- In **builder.md**, under "Process" step 3, add a line like:
  `This project uses Jest — run tests with \`npm test\` or \`npx jest\`.`
  And under step 5: `Run ESLint: \`npx eslint .\` before reporting.`
  (Replace with the actual detected tools and commands.)

- In **e2e-tester.md**, under "Detect existing infrastructure", add:
  `This project has Playwright configured — check for existing tests in \`tests/\` or \`e2e/\`.`
  (Replace with the actual detected framework and test directory.)

---

## Step 4: Write State Files

### `.claude/gaps.md`

**Skip if `.claude/gaps.md` already exists** — it contains cross-session state.

Read `templates/gaps.md` and write to `.claude/gaps.md`.

### `.claude/progress.md`

**Skip if `.claude/progress.md` already exists** — it contains cross-session state.

Read `templates/progress.md` and write to `.claude/progress.md`.

---

## Step 5: Update CLAUDE.md

Append the following section to CLAUDE.md. Create the file if it doesn't exist.
**If a "Self-Improving Agent Harness" section already exists, update it rather
than duplicating it.**

```markdown

## Self-Improving Agent Harness

Agents in `.claude/agents/`: orchestrator, builder, verifier, e2e-tester, researcher.
State files: `.claude/gaps.md` (blockers/decisions), `.claude/progress.md` (task tracking).

### Usage
- Start a build loop: "Use the orchestrator to build [goal]"
- Continue where you left off: "Use the orchestrator to continue"
- Bake learnings into agents: "Evolve the agents"
- Check open blockers: "Read .claude/gaps.md"
- Check progress: "Read .claude/progress.md"

### How It Works
1. Orchestrator reads agent learnings + state files, then decomposes goal into tasks
2. Each task cycles: RESEARCH? → BUILD → VERIFY → TEST with up to 3 retries
3. After 3 failures on a task, the orchestrator escalates to you with options
4. After each cycle, agents capture raw learnings in ## Learnings sections
5. After each build loop, the EVOLVE phase bakes validated learnings into agent instructions
6. Gaps and progress persist across sessions — the harness picks up where it left off
```

---

## Step 6: Report to User

1. List every file created or updated with a one-line description
2. Show usage examples:
   - `Use the orchestrator to build [goal]`
   - `Use the orchestrator to continue`
   - `Evolve the agents` (bake validated learnings into agent instructions)
   - `Read .claude/gaps.md`
3. If $ARGUMENTS was provided: "Ready to start the first build loop with goal: **$ARGUMENTS**?"
4. If $ARGUMENTS was empty: "What would you like the agents to build?"
