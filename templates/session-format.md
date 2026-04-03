# Session Summary Format Template

Use this format when writing session summaries to `.reflect/sessions/`.

Filename convention: `YYYY-MM-DD_<session-id>.md`

---

```markdown
---
schema_version: "1.1"
session_id: <session-id>
date: <ISO-8601 timestamp>
branch: <git branch>
commits: [<commit-hash>, ...]
files_touched: [<file-path>, ...]
duration_estimate: <Nmin>
token_efficiency: <low | moderate | high>
outcome: <success | partial | failure>
env_snapshot:                        # optional — starting conditions
  branch: <git branch at session start>
  recent_commits: <N>                # commits since last session
  dirty_files: <N>                   # uncommitted changes at start
---

# Session <session-id>: <one-line summary>

## Intent
<What the user was trying to accomplish — 1-2 sentences.>

## Outcome
<SUCCESS | PARTIAL | FAILURE>. <Brief description of end result.>

## Approach
1. <Step 1 — what was tried>
2. <Step 2>
3. ...

## Evidence (optional)
<!-- Curated raw fragments that support decisions/patterns above.
     Include: error messages, surprising tool outputs, retry sequences,
     commands that revealed environment state.
     Omit: routine successful operations. -->
- `<command or context>`: <raw output fragment or error message>

## Patterns Observed
- **<pattern-name>**: <description>

## Decisions Made
- DECISION_REF: <decision-id> (<brief description>)

## Key Context Captured
- `<file-path>`: <important fact learned about this file>
```

### Field Notes

- **token_efficiency**: `high` = few tokens per file changed, `moderate` = average, `low` = many retries/exploration
- **outcome**: `success` = task completed as intended, `partial` = partially done, `failure` = abandoned or reverted
- **commits**: empty list if no commits were made
- **env_snapshot**: optional; captures starting conditions so future sessions can reason about environment differences
- **Evidence**: optional section for raw diagnostic fragments — error messages, surprising outputs, retry sequences. Include 1-3 fragments per pattern identified. These enable causal reasoning over failures (why something failed, not just that it failed). Omit routine successful operations.
- **Patterns Observed**: use short pattern IDs like `retry-loop`, `clean-first-pass`, `research-then-fail`
- **Decisions Made**: only include if an architectural/design decision was made; link to the decision record ID
- **Key Context**: facts about specific files that future sessions should know
