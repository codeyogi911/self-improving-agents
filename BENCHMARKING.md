# Harness Benchmarking Plan

How do you know if one harness is better than another? This document defines the evaluation framework.

---

## The Core Problem

Meta-Harness had clean benchmarks with scalar scores (classification accuracy, pass rate). Real repos don't have that. "Did the context help the agent?" is noisy, delayed, and subjective.

We need proxy metrics that are **measurable now** from data we already have (Entire sessions + git history).

---

## Evaluation Method: Hindsight Scoring

Use historical sessions as ground truth. For each past session:

1. **Generate context** using the harness, pretending it's the start of that session (only evidence available *before* the session counts)
2. **Compare against what actually happened** in the session
3. **Score** how well the context predicted what mattered

This is offline evaluation — no live sessions needed. Every Entire checkpoint is a test case.

### What "mattered" in a session (extractable from Entire transcripts)

| Signal | How to extract | What it tells us |
|--------|---------------|-----------------|
| Files touched | `entire explain --checkpoint <id> --full` → Files section | Did the context mention these files? |
| Errors encountered | Grep transcript for error messages, failed commands | Did the context warn about known issues? |
| Retries / thrashing | Count edits to same file, repeated commands | Was context missing that could have prevented this? |
| Intent | User's first prompt | Did the context relate to what the user wanted to do? |
| Outcome | Session result (success/partial/failure) | Correlation: better context → better outcomes? |

---

## Metrics

### 1. File Coverage Score

**What**: Of the files the agent touched in a session, what fraction were mentioned in the context?

```
file_coverage = |files_in_context ∩ files_touched| / |files_touched|
```

**Why**: If the context mentions files the agent ends up working on, it's relevant. If it's all about unrelated files, it's noise.

**Extraction**: Parse `Files:` section from `entire explain --checkpoint <id> --full`. Parse generated context for file paths and commit messages mentioning files.

### 2. Error Anticipation Score

**What**: Of the errors that occurred in a session, were any related to patterns/warnings in the context?

```
error_anticipation = |errors_warned_about| / |total_errors|
```

**Why**: The highest-value context is "watch out for X" when X actually happens.

**Extraction**: Grep transcript for error patterns (stack traces, "Error:", "failed", non-zero exit codes). Check if context contained related warnings.

### 3. Token Efficiency

**What**: How much of the context budget was used by entries that turned out to be relevant?

```
token_efficiency = relevant_tokens / total_context_tokens
```

**Why**: Context window is finite. Wasting it on irrelevant information displaces useful information.

**Extraction**: Classify each context section as relevant (mentioned files/topics that appeared in session) or irrelevant. Count tokens.

### 4. Session Outcome Correlation

**What**: Do sessions with better context scores have better outcomes?

**Why**: The ultimate question. But noisy — many factors affect session outcome beyond context.

**Extraction**: Group sessions by context quality (high/low on metrics 1-3), compare outcome rates (success/partial/failure). Need enough sessions for statistical significance.

### 5. Retry Reduction (aspirational)

**What**: For sessions where the agent retried/thrashed, would the context have prevented it?

**Why**: Direct measure of "context would have saved time."

**Extraction**: Identify retry sequences in transcripts (same file edited 3+ times, same command retried). Check if the pattern that caused retries was addressable by context.

---

## Test Harness Runner

A script that automates evaluation:

```python
# bench/runner.py (future)

for checkpoint in get_all_checkpoints():
    # 1. Get evidence available BEFORE this session
    prior_evidence = get_evidence_before(checkpoint.timestamp)
    
    # 2. Run the harness with only prior evidence
    context = run_harness(harness_path, evidence=prior_evidence)
    
    # 3. Get what actually happened in the session
    transcript = get_transcript(checkpoint.id)
    files_touched = extract_files(transcript)
    errors = extract_errors(transcript)
    
    # 4. Score
    scores.append({
        "checkpoint": checkpoint.id,
        "file_coverage": compute_file_coverage(context, files_touched),
        "error_anticipation": compute_error_anticipation(context, errors),
        "token_efficiency": compute_token_efficiency(context, files_touched),
    })

# 5. Aggregate
print(f"Mean file coverage: {mean(s['file_coverage'] for s in scores):.2f}")
print(f"Mean error anticipation: {mean(s['error_anticipation'] for s in scores):.2f}")
print(f"Mean token efficiency: {mean(s['token_efficiency'] for s in scores):.2f}")
```

### Challenge: Time-Gating Evidence

The harness reads from `entire explain` and `git log` in real-time — it doesn't know "only use evidence before timestamp X." For benchmarking, we need:

- Option A: Mock the evidence sources (pass pre-filtered data to the harness)
- Option B: Add `--before <timestamp>` flag to the harness contract
- Option C: Create snapshot evidence directories per test case

**Recommendation**: Option B — add `--before` as an optional harness flag. The default harness filters `entire explain` and `git log` results by date. Custom harnesses can ignore it.

---

## Baseline Harnesses to Compare

| Harness | Description | Expected behavior |
|---------|-------------|-------------------|
| `default` | Recency-ranked, ships with reflect | Baseline — decent file coverage, no error anticipation |
| `null` | Outputs empty context | Lower bound — proves context helps at all |
| `kitchen-sink` | Dumps everything within budget | Tests whether more = better (usually not) |
| `topic-focused` | Clusters evidence by topic, picks most relevant cluster | Tests whether focus beats breadth |
| `error-weighted` | Ranks error-containing sessions higher | Tests whether error anticipation improves |

---

## Data Requirements

| Metric | Minimum sessions | Why |
|--------|-----------------|-----|
| File coverage | 10 | Need variety of file patterns |
| Error anticipation | 10 with errors | Need sessions that had failures |
| Token efficiency | 10 | Need enough to measure waste |
| Outcome correlation | 30+ | Need statistical power for comparison |

This repo currently has **13 checkpoints** — enough for file coverage and error anticipation, marginal for outcome correlation. Benchmarking improves as more sessions accumulate across repos.

---

## Running a Benchmark

```bash
# Future CLI command
reflect bench --harness harness/default.py
reflect bench --harness harness/default.py --harness harness/error-weighted.py --compare
```

Output:
```
Harness: default.py
  File coverage:      0.42 (10 sessions)
  Error anticipation: 0.15 (6 sessions with errors)
  Token efficiency:   0.61

Harness: error-weighted.py  
  File coverage:      0.38 (10 sessions)
  Error anticipation: 0.45 (6 sessions with errors)  ← +200%
  Token efficiency:   0.55

Winner: error-weighted.py (better error anticipation, slight file coverage tradeoff)
```

---

## The Meta-Harness Loop

Once benchmarking exists, the optimization path is:

1. Run benchmark on current harness → get scores
2. Give scores + harness code + raw sessions to a proposer agent
3. Agent rewrites the harness to improve scores
4. Run benchmark on new harness → compare
5. Keep the winner, repeat

This is exactly the Meta-Harness paper's loop, applied to reflect. The benchmarking framework is the prerequisite.

---

## Implementation Priority

| Step | Effort | Prerequisite |
|------|--------|-------------|
| File coverage scorer | Small | Just needs transcript parser |
| Error extraction from transcripts | Small | Regex patterns |
| `--before` flag on harness | Small | Filter by date |
| `reflect bench` CLI command | Medium | Scorer + runner |
| Null/kitchen-sink baseline harnesses | Small | Just harness variants |
| Outcome correlation analysis | Medium | Needs 30+ sessions |
| Automated proposer loop | Large | Needs benchmarking + proposer agent |
