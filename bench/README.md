# Reflect Benchmark

Two benchmark modes measuring context quality via a maker-checker loop.

## Modes

### 1. Self-Benchmark: with-reflect vs without-reflect

Measures whether reflect actually helps an LLM work on this repo.
Uses 12 tasks derived from real development pitfalls in reflect's own history.

```
  without-reflect                with-reflect
  +------------------+           +------------------+
  | CLAUDE.md        |           | CLAUDE.md        |
  | (no reflect ref) |           | + context.md     |
  | dir listing      |           | + reflect why    |
  | git log (10)     |           | + reflect search |
  +--------+---------+           +--------+---------+
           |                              |
           +----------+-------------------+
                      |
              +-------v-------+
              |    MAKER      |
              |  claude CLI   |
              +-------+-------+
                      |
              +-------v-------+
              |   CHECKER     |
              | (no context)  |
              +-------+-------+
                      |
             accept?--+--revise?
               |             |
            record       feedback → loop (max 5)
```

**Hypothesis**: With reflect, the maker gets it right sooner because it has
access to session history, decision rationale, and pitfall warnings that
aren't visible from code alone.

### 2. v3 vs v4 Benchmark

Compares v3's pre-computed artifacts against v4's on-demand harness.
Uses 16 tasks from an external SAP CAP project. See [original docs](#v3-vs-v4-details) below.

## Quick Start

```bash
# Self-benchmark: dry run (no API calls, just check context sizes)
python3 -m bench self-bench --dry-run

# Self-benchmark: full run
python3 -m bench self-bench

# Self-benchmark: with specific model
python3 -m bench self-bench --model claude-sonnet-4-6

# List all runs
python3 -m bench list-runs

# Regenerate report from previous run
python3 -m bench report --run-id self-2026-04-03_1930
```

## Self-Benchmark Task Types

```
+---------------------------+-------+------------------------------------------+
| Type                      | Count | Example                                  |
+---------------------------+-------+------------------------------------------+
| why_query                 |   4   | Why list-based subprocess, not shell=True|
| code_modification         |   2   | Add a new CLI command to reflect         |
| debugging                 |   3   | Diagnose benchmark maker OS arg limits   |
| architectural_reasoning   |   3   | Evaluate LLM summarization in harness    |
+---------------------------+-------+------------------------------------------+
```

Each task has `ground_truth_signals` — verifiable keywords the checker uses
as objective anchors. These are derived from actual commit messages, PR
descriptions, and development session transcripts.

## The Maker-Checker Loop

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

## Checker Rubric

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

The checker does NOT see the project context — only the maker's output
and ground-truth signal keywords. This prevents echo-chamber bias.

## Output

The report compares the two conditions across all tasks:

```
| Metric                  | without-reflect | with-reflect | Delta  | Winner       |
|-------------------------|-----------------|--------------|--------|--------------|
| Convergence rate        | 0.58            | 0.83         | +0.25  | with-reflect |
| Mean rounds             | 3.2             | 1.8          | -1.4   | with-reflect |
| Mean weighted score     | 3.5             | 4.3          | +0.8   | with-reflect |
| Mean evidence grounding | 2.8             | 4.1          | +1.3   | with-reflect |
| Total cost (USD)        | 1.40            | 0.90         | -0.50  | with-reflect |
```

*(Example values — actual results depend on the run.)*

## File Structure

```
bench/
  cli.py               CLI: run, self-bench, report, list-runs
  config.py            BenchmarkConfig + Task/Round/TaskResult dataclasses
  compare.py           Legacy static heuristic scorer
  tasks/
    registry.py        Load + validate task definitions
    tasks.json         16 tasks for v3-vs-v4 (external repo)
    self_tasks.json    12 tasks for self-bench (this repo)
  context/
    provider.py        V3/V4 + WithReflect/WithoutReflect providers
  loop/
    maker.py           Calls claude CLI with context + task prompt
    checker.py         Calls claude CLI with rubric, returns JSON scores
    runner.py          Orchestrates maker -> checker -> revise loop
  metrics/
    collector.py       Per-task + aggregate stats, generic labels
  reporting/
    report.py          Generates report.md + summary.json
  results/             (gitignored)
    <run-id>/          v3-vs-v4 runs
    self-<run-id>/     self-bench runs
```

## Design Decisions

**Why claude CLI, not the API SDK?**
Runs on existing Claude Code auth — no API key management needed.

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

**Why self-benchmark on this repo?**
The reflect repo has rich session history (via Entire CLI) and well-documented
pitfalls from its own development. Using it as the benchmark target means the
ground truth is verifiable from the actual git history and transcripts.

---

<a id="v3-vs-v4-details"></a>
## v3 vs v4 Benchmark (Original)

```bash
# Dry run
python3 -m bench run \
  --target-repo /path/to/mymediset_cloud \
  --v3-reflect /path/to/mymediset_cloud/.reflect \
  --dry-run

# Full benchmark
python3 -m bench run \
  --target-repo /path/to/mymediset_cloud \
  --v3-reflect /path/to/mymediset_cloud/.reflect \
  --max-rounds 5
```
