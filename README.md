<p align="center">
  <h1 align="center">reflect</h1>
  <p align="center">
    <strong>git answers "what changed." reflect answers "why."</strong>
  </p>
  <p align="center">
    Repo-owned memory for AI coding agents.
  </p>
</p>

<p align="center">
  <a href="#how-it-works">How It Works</a> &middot;
  <a href="#install">Install</a> &middot;
  <a href="#commands">Commands</a> &middot;
  <a href="#the-harness">The Harness</a> &middot;
  <a href="SPEC.md">Spec</a>
</p>

---

## The Problem

AI agents have memory — but it's trapped.

Claude's memory lives in `~/.claude/projects/` on your laptop. Cursor's lives somewhere else. Switch machines, switch agents, onboard a teammate — **the memory doesn't travel.**

Decisions get made, approaches get abandoned, lessons get learned. Then the next session starts fresh and makes the same mistakes.

## The Solution

**Put the "why" in the repo.**

```
git log       →  what happened
git blame     →  who changed this line
git bisect    →  which commit broke it

reflect why   →  why is it this way
reflect search → find sessions about a topic
```

Reflect reads raw evidence from [Entire CLI](https://entire.io) session transcripts and git history — on demand, no data duplication. A replaceable harness script generates context briefings that any AI agent can read.

**Zero storage. Zero opinions. Just a script that reads what's already there.**

---

## How It Works

```
Evidence Sources (already exist)        reflect (the read path)
┌─────────────────────────┐            ┌──────────────────────┐
│  Entire CLI sessions    │───────────▶│                      │
│  (transcripts, intents) │            │   .reflect/harness   │
│                         │            │   (replaceable script │
│  Git history            │───────────▶│    that generates     │
│  (commits, diffs)       │            │    context.md)        │
│                         │            │                      │
│  Manual notes           │───────────▶│                      │
│  (.reflect/notes/)      │            └──────────┬───────────┘
└─────────────────────────┘                       │
                                           context.md
                                                  │
                                    ┌─────────────┼─────────────┐
                                    │             │             │
                              CLAUDE.md    .cursorrules    copilot-
                                                          instructions
```

1. **Evidence already exists** — Entire captures sessions, git captures commits
2. **Harness reads on demand** — no copying, no intermediate storage
3. **Context briefing generated** — filtered, prioritized summary
4. **Every AI tool gets it** — auto-wired into instruction files

---

## Install

```bash
git clone https://github.com/codeyogi911/reflect.git
cd reflect && ./install.sh
```

This installs:
- `reflect` CLI to `~/.local/bin/`
- `/reflect` skill for Claude Code to `~/.claude/skills/`

Then in any git repo:
```bash
reflect init      # creates .reflect/ with default harness
reflect context   # generates your first context briefing
```

---

## Commands

### Generate context briefing

```bash
reflect context                  # run harness, write context.md
```

### Query raw evidence

```bash
reflect why src/auth/middleware.ts    # raw session + git evidence about a file
reflect why "database migration"     # raw evidence about a topic
reflect search "JWT bug"             # grep across all sources
```

### Manage

```bash
reflect init                     # set up .reflect/ in current repo
reflect status                   # show available evidence sources
reflect note "why we chose postgres" # add a manual note
```

### Claude Code skill

```bash
/reflect                         # regenerate context
/reflect why auth middleware     # evidence + AI narrative
/reflect search JWT              # search all sources
/reflect status                  # evidence overview
```

---

## The Harness

The harness is the brain — a replaceable script at `.reflect/harness` that reads raw evidence and generates `context.md`.

### Default harness

The default reads from Entire CLI and git, ranks by recency, and produces a Markdown briefing. It's deliberately simple.

### Custom harness

Replace `.reflect/harness` with any script that follows the contract:

```
reads: Entire CLI + git + notes (on demand)
writes: context to stdout
flags: --max-lines, --format
```

Examples of what a custom harness could do:
- Use an LLM to summarize sessions before generating context
- Implement semantic search with embeddings
- Add confidence levels and decay (if you want that)
- Fetch from additional sources (Slack, Linear, CI logs)

The harness is committed to git — different repos evolve different harnesses.

### Why this matters

The [Meta-Harness paper](https://arxiv.org/abs/2603.28052) (Stanford/MIT, 2026) proved that the code determining what context an AI sees matters as much as the model itself. Hand-designed memory structures are inferior to letting agents search raw evidence. Reflect's architecture makes the context-generation logic a replaceable, optimizable program — not a static schema.

---

## Two Read Paths

| Path | Command | How it works |
|------|---------|-------------|
| **Passive** | `reflect context` | Runs harness → writes context.md (pre-session briefing) |
| **Active** | `reflect why <topic>` | Fetches raw evidence → dumps to stdout (agent reasons over it) |

The passive path is for pre-computed briefings. The active path gives the agent raw evidence — because [raw traces outperform summaries](https://arxiv.org/abs/2603.28052).

---

## `.reflect/` Directory

```
.reflect/
├── harness             # the replaceable context-generation script
├── context.md          # generated briefing (gitignored)
├── config.yaml         # optional settings
├── .last_run           # freshness state (gitignored)
└── notes/              # manual annotations
```

That's it. No sessions/, no decisions/, no insights/. Evidence lives in Entire and git — reflect reads it on demand.

See [`SPEC.md`](SPEC.md) for the full specification.

---

## FAQ

**Does this work without Entire CLI?**
Yes. Git history is always available. Entire adds richer session transcripts but is not required.

**Will it modify my code?**
No. It only writes to `.reflect/` and auto-wires `@.reflect/context.md` into `CLAUDE.md` on first run.

**What about `.reflect/` in git?**
Commit: `harness`, `config.yaml`, `notes/`. Gitignore: `context.md`, `.last_run`.

**Can I customize the context generation?**
Yes — replace `.reflect/harness` with your own script. It's just a program.

**What about secrets?**
Reflect never stores file contents or credentials. The harness should redact sensitive data from transcripts.

---

## Contributing

1. Fork the repo
2. Edit `harness/default.py` to change default context generation
3. Edit `lib/` to change CLI commands
4. Changes take effect immediately via symlinks
5. Submit a PR

## License

MIT
