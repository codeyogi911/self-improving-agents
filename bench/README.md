# Reflect Benchmark: v3 vs v4

Measures whether v4's raw-evidence-on-demand approach helps an LLM converge
faster on coding tasks compared to v3's pre-computed summaries.

## How it works

```
                          tasks.json
                              |
                     16 tasks (4 types)
                              |
                   +----------+----------+
                   |                     |
              v3 context            v4 context
          (pre-computed)         (on-demand CLI)
                   |                     |
                   v                     v
          +----------------+    +----------------+
          |                |    |                |
          |  .reflect/     |    |  reflect why   |
          |  sessions/     |    |  reflect ctx   |
          |  decisions/    |    |  reflect search|
          |  insights/     |    |                |
          +-------+--------+    +-------+--------+
                  |                     |
                  +----------+----------+
                             |
                     +-------v-------+
                     |    MAKER      |
                     |  claude CLI   |
                     | (Sonnet 4)    |
                     +-------+-------+
                             |
                        task output
                             |
                     +-------v-------+
                     |   CHECKER     |
                     |  claude CLI   |
                     | (Sonnet 4)    |
                     +-------+-------+
                             |
                    accept?--+--revise?
                      |             |
                   record      feedback
                   result      to maker
                      |             |
                      v             +-----> loop (max 5 rounds)
                             |
                     +-------v-------+
                     |   METRICS     |
                     | rounds, score |
                     | cost, GT cov  |
                     +-------+-------+
                             |
                     +-------v-------+
                     |    REPORT     |
                     | summary.json  |
                     | report.md     |
                     +---------------+
```

## The maker-checker loop

Each task runs through an iterative refinement cycle:

```
Round 1:  Maker attempts  -->  Checker scores  -->  accept (done)
                                                    or
                                                    revise + feedback
                                                        |
Round 2:  Maker revises   -->  Checker scores  -->  accept (done)
                                                    or
                                                    revise + feedback
                                                        |
  ...                                              (up to 5 rounds)
```

**Primary metric**: rounds to convergence (fewer = better context).
The hypothesis: better context helps the maker get it right sooner.

## Checker rubric

The checker scores each response on 4 dimensions:

```
+------------------------+--------+----------------------------------+
| Dimension              | Weight | Scale                            |
+------------------------+--------+----------------------------------+
| Correctness            |  0.30  | 5=accurate ... 1=wrong           |
| Completeness           |  0.25  | 5=thorough ... 1=barely touched  |
| Evidence Grounding     |  0.25  | 5=all cited ... 1=fabricated     |
| Code/Reasoning Quality |  0.20  | 5=production ... 1=broken        |
+------------------------+--------+----------------------------------+

Accept when:  weighted_score >= 4.0  AND  no dimension < 3
```

The checker does NOT see the project context -- only the maker's output
and ground-truth signal keywords. This prevents echo-chamber bias.

## Task types

```
+---------------------------+-------+------------------------------------------+
| Type                      | Count | Example                                  |
+---------------------------+-------+------------------------------------------+
| why_query                 |   4   | Why were XSUAA roles separated?          |
| code_modification         |   4   | Add error code to LoansetService         |
| debugging                 |   4   | Diagnose XSUAA deploy validation failure |
| architectural_reasoning   |   4   | Evaluate migrating JS handler to TS      |
+---------------------------+-------+------------------------------------------+
```

Each task carries `ground_truth_signals` -- verifiable keywords the checker
uses as objective anchors (e.g., `"ROLE_LOANSET"`, `"scanbotsdk"`, `"SELECT.one"`).

## Context comparison

v3 and v4 provide very different context for the same task:

```
              v3 (structured)                v4 (raw evidence)
         +----------------------+       +----------------------+
         | context.md (curated) |       | context.md (harness) |
         | sessions/*.md        |       | reflect why <file>   |
         | decisions/*.md       |       | reflect search <kw>  |
         | insights/*.md        |       |                      |
         +----------------------+       +----------------------+
               ~10-18K chars                  ~2-7K chars
```

v3 provides more volume (pre-computed artifacts).
v4 provides targeted evidence (fetched on demand).

## File structure

```
bench/
  cli.py               CLI: run, report, list-runs
  config.py            BenchmarkConfig + Task/Round/TaskResult dataclasses
  compare.py           Legacy static heuristic scorer (predecessor)
  tasks/
    registry.py        Load + validate task definitions
    tasks.json         16 curated tasks with ground_truth_signals
  context/
    provider.py        V3ContextProvider (reads artifacts)
                       V4ContextProvider (invokes reflect CLI)
  loop/
    maker.py           Calls claude CLI with context + task prompt
    checker.py         Calls claude CLI with rubric, returns JSON scores
    runner.py          Orchestrates maker -> checker -> revise loop
  metrics/
    collector.py       Per-task + aggregate stats, win/loss/tie
  reporting/
    report.py          Generates report.md + summary.json
  results/             (gitignored)
    <run-id>/
      run_config.json  Frozen config for reproducibility
      tasks/           Per-task JSON (all rounds preserved)
      summary.json     Aggregate metrics
      report.md        Human-readable comparison
```

## Usage

```bash
# Dry run -- validate tasks, show context sizes, no API calls
python3 -m bench run \
  --target-repo /path/to/mymediset_cloud \
  --v3-reflect /path/to/mymediset_cloud/.reflect \
  --dry-run

# Full benchmark
python3 -m bench run \
  --target-repo /path/to/mymediset_cloud \
  --v3-reflect /path/to/mymediset_cloud/.reflect \
  --max-rounds 5

# Regenerate report from a previous run
python3 -m bench report --run-id 2026-04-03_1712

# List all runs
python3 -m bench list-runs
```

## Output

The report compares v3 and v4 across all tasks:

```
| Metric                  | v3   | v4   | Delta  | Winner |
|-------------------------|------|------|--------|--------|
| Convergence rate        | 0.75 | 0.88 | +0.13  | v4     |
| Mean rounds             | 2.8  | 1.9  | -0.9   | v4     |
| Mean weighted score     | 3.9  | 4.2  | +0.3   | v4     |
| Mean evidence grounding | 3.1  | 3.8  | +0.7   | v4     |
| Total cost (USD)        | 1.20 | 0.85 | -0.35  | v4     |
```

*(Example values -- actual results depend on the run.)*

## Design decisions

**Why claude CLI, not the API SDK?**
Runs on existing Claude Code auth -- no API key management needed.

**Why the checker has no context?**
If the checker saw the same context, it would grade based on whether the
maker echoed the context, not whether the claims were correct.
Ground-truth signals serve as the objective anchor instead.

**Why iterative refinement?**
A single-shot score doesn't capture how recoverable a bad start is.
Measuring rounds-to-convergence reveals whether context helps the
agent self-correct faster with reviewer feedback.

**Why same model for maker and checker?**
Eliminates model capability as a confound. We are measuring
context quality, not model quality.
