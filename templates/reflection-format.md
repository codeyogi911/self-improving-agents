# Reflection Format Template

Use this format when writing reflections to `.claude/reflections.md`.

---

```markdown
## YYYY-MM-DD

### Sessions Analyzed
- `[session-id]`: [one-line summary of what happened]

### What Worked Well
- **[pattern name]**: [evidence from session — what happened and why it worked]

### Issues Found
- **[pattern name]** (severity: HIGH | MEDIUM | LOW): [what happened, which
  session, impact — e.g., "3 retries", "20min time sink"]

### Insights
- **TARGET**: [CLAUDE.md or .claude/agents/{agent}.md]
  **CONFIDENCE**: HIGH | MEDIUM | LOW
  **INSIGHT**: [what this means for the project]
  **ACTION**: [specific, actionable change to bake in]
  **STATUS**: PENDING | BAKED

### Metrics
- Sessions analyzed: [N]
- Patterns found: [N] ([N] HIGH, [N] MEDIUM, [N] LOW)
- Insights baked: [N] / [total HIGH]
```
