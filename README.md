# Self-Improving Agents

**A Claude Code skill that gives your project agents that learn from every build cycle.**

Invoke `/self-improving-agents` in any project and get a full agentic harness — an orchestrator that decomposes goals into tasks, a builder that writes code, a verifier that catches bugs before they ship, a tester that validates user flows, and a researcher that investigates before building. After each cycle, agents record what went wrong and what to do differently — and those learnings persist across sessions.

## Why This Exists

Claude Code is powerful, but complex projects need more than a single prompt. You need:

- **Structured loops** — build, verify, test, retry until quality gates pass
- **Separation of concerns** — the code writer shouldn't review its own work
- **Memory across sessions** — don't rediscover the same issues every time
- **Human escalation** — agents should ask when stuck, not guess

This skill sets up all of that in one command.

## How It Works

```
ANALYZE → PLAN → [RESEARCH? → BUILD → VERIFY → TEST → REFLECT]* → DONE
                                                       ↓ (3 fails)
                                                    ESCALATE → human
```

1. **Orchestrator** decomposes your goal into ordered tasks
2. Each task cycles through BUILD → VERIFY (two-gate review) → TEST
3. Failed tasks retry up to 3 times, then escalate to you with context and options
4. After each cycle, agents append learnings to their own files
5. Open gaps and task progress persist across sessions

## Install

### Option 1: Symlink (recommended for development)

```bash
git clone https://github.com/shashwatjain/self-improving-agents.git
mkdir -p ~/.claude/skills/self-improving-agents
ln -sf "$(pwd)/self-improving-agents/SKILL.md" ~/.claude/skills/self-improving-agents/SKILL.md
ln -sf "$(pwd)/self-improving-agents/templates" ~/.claude/skills/self-improving-agents/templates
```

### Option 2: Copy

```bash
git clone https://github.com/shashwatjain/self-improving-agents.git
mkdir -p ~/.claude/skills/self-improving-agents
cp self-improving-agents/SKILL.md ~/.claude/skills/self-improving-agents/SKILL.md
cp -r self-improving-agents/templates ~/.claude/skills/self-improving-agents/templates
```

## Usage

Once installed, open any project in Claude Code and run:

```
/self-improving-agents
```

Or with a goal:

```
/self-improving-agents build a REST API for user management
```

After scaffolding, use the harness:

```
Use the orchestrator to build [your goal]
Use the orchestrator to continue
```

Check state between sessions:

```
Read .claude/gaps.md
Read .claude/progress.md
```

## What Gets Created

```
your-project/
└── .claude/
    ├── agents/
    │   ├── orchestrator.md    — Coordinates build loops, dispatches agents
    │   ├── builder.md         — Writes code, runs tests
    │   ├── verifier.md        — Two-gate code review (spec + quality)
    │   ├── e2e-tester.md      — End-to-end testing, failure classification
    │   └── researcher.md      — Pre-build investigation
    ├── gaps.md                — Cross-session blocker and decision tracker
    └── progress.md            — Task completion and session log
```

## Agents

| Agent | What It Does |
|---|---|
| **Orchestrator** | Reads learnings and state, decomposes goals into tasks, drives the build loop state machine, escalates when stuck |
| **Builder** | Studies existing patterns before coding, writes tests first when possible, flags new dependencies, stays within scope |
| **Verifier** | Gate 1: spec compliance (missing/extra/wrong). Gate 2: code quality (security, edge cases, tests). Never approves CRITICAL issues |
| **E2E Tester** | Detects existing test infrastructure, writes targeted tests, classifies failures as app bug vs test bug vs environment |
| **Researcher** | Investigates codebases and docs before building. Cites sources. Reduces ambiguity that would waste build cycles |

## Self-Improvement: Two-Tier System

Most "learning" systems just append notes to a file. That's tier 1. The real power is **tier 2: bake-in** — where validated learnings get rewritten into the agent's core instructions, then removed from the learnings list.

### Tier 1: Capture

After each build cycle, agents append structured learnings:

```markdown
### 2026-04-01 — auth middleware refactor
- OBSERVATION: Unit tests passed but e2e failed because session cookie wasn't set
- INSIGHT: Auth changes need both unit and e2e coverage — they touch the full request lifecycle
- ACTION: When modifying auth, always add an e2e test for the full login→action→logout flow
- STATUS: raw
```

### Tier 2: Bake-In

After each build loop completes, the orchestrator runs an **EVOLVE** phase:

1. Reviews all learnings across agent files
2. Identifies candidates: confirmed across 2+ sessions, or caused significant rework
3. **Rewrites the agent's core instructions** to incorporate the insight
4. Removes the learning entry — it's now part of the agent's DNA

For example, if the builder keeps learning "run full auth tests after middleware changes", the EVOLVE phase edits `builder.md`'s Process section to add that as a permanent step. The learning disappears because the agent now does it automatically.

Each agent file has two sections at the bottom:
- **Project-Specific Rules** — baked-in learnings that are now permanent instructions
- **Learnings** — raw observations waiting to be validated

You can also trigger evolution manually: `"Evolve the agents"` or `"Bake in the learnings"`.

### Why This Matters

- **Context efficiency** — agents don't re-read a growing list of notes every run
- **Genuine improvement** — the agent's actual behavior changes, not just its reading list
- **Compounding returns** — each session makes the next one faster and more reliable

## Key Design Decisions

- **Idempotent scaffolding** — Re-running preserves existing learnings, gaps, and progress
- **Two-tier self-improvement** — Learnings captured raw, then baked into agent DNA when validated
- **Two-gate verification** — Spec compliance before code quality (don't optimize wrong code)
- **Escalation over guessing** — 3 failures → ask the human with context and options
- **Research-first** — Dedicated research step prevents building on assumptions
- **Project-adaptive** — Detects your stack and customizes agent behavior

## Contributing

Contributions welcome! The main files to edit:

- `SKILL.md` — The skill workflow (what happens when you invoke `/self-improving-agents`)
- `templates/*.md` — The agent prompt templates that get scaffolded into projects
- `README.md` — This file

To test changes locally, symlink and invoke in a test project.

## License

MIT
