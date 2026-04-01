# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A Claude Code skill that scaffolds a self-improving agentic harness into any project. The main deliverables are `SKILL.md` and the `templates/` directory.

## Structure

- `SKILL.md` — the skill definition file (frontmatter + workflow steps, keep under 500 lines)
- `templates/` — agent prompt templates that get written into target projects
  - `orchestrator.md`, `builder.md`, `verifier.md`, `e2e-tester.md`, `researcher.md`
  - `gaps.md`, `progress.md` — state file templates
- `README.md` — installation and usage docs
- `CLAUDE.md` — this file

## Development

- Edit `SKILL.md` to change the scaffolding workflow
- Edit `templates/*.md` to change agent behavior
- Test locally by symlinking both SKILL.md and templates/:
  ```bash
  mkdir -p ~/.claude/skills/self-improving-agents
  ln -sf $(pwd)/SKILL.md ~/.claude/skills/self-improving-agents/SKILL.md
  ln -sf $(pwd)/templates ~/.claude/skills/self-improving-agents/templates
  ```
- Invoke with `/self-improving-agents` in any project to test
- The skill reads templates at runtime, so changes to templates/ take effect immediately when symlinked

## Self-Improving Agent Harness

Agents in `.claude/agents/`: orchestrator, builder, verifier, e2e-tester, researcher.
State: `.claude/gaps.md` (blockers/decisions), `.claude/progress.md` (task tracking).

### Usage
- Start: "Use the orchestrator to build [goal]"
- Continue: "Use the orchestrator to continue"
- Bake learnings into agents: "Evolve the agents"
- Check gaps: "Read .claude/gaps.md"

### How It Works
1. Orchestrator decomposes goal into tasks
2. Each task: RESEARCH? → BUILD → VERIFY → TEST with retry
3. 3 failures → escalate to you
4. After each cycle, agents capture raw learnings
5. EVOLVE phase bakes validated learnings into agent core instructions
6. Gaps and progress persist across sessions
