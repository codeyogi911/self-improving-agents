# Dynamic Context Format Template

Use this format when generating `.reflect/context.md` — a compiled briefing of
current project context, optionally referenced from CLAUDE.md via
`@.reflect/context.md`. This is a generated overlay that supplements the
human-owned CLAUDE.md, never replaces it.

---

## Generation Rules

1. **Budget**: Maximum 150 lines (configurable in `.reflect/config.yaml`). Stay well under.
2. **Priority order**: HIGH-confidence fresh insights > accepted decisions > file knowledge > failure patterns
3. **Freshness threshold**: Include insights with freshness >= 0.3 in Active Rules. Insights below 0.3 are demoted to Archive References (max 5) rather than excluded entirely — this preserves discoverability for regression debugging and cross-session transfer.
4. **Freshness formula**: `freshness = 2^(-(days_since_last_seen / half_life_days))` where default `half_life_days = 60`
5. **Self-contained**: No references that require reading other files. Everything needed is inline.
6. **Full rewrite**: This file is regenerated from scratch each time — never appended to.
7. **Generated overlay, not source of truth**: This file is a computed view derived from typed records in `.reflect/`. It is NOT a human-authored instruction file. CLAUDE.md is the human-owned constitution — context.md MUST NEVER contradict, override, or weaken any rule in CLAUDE.md.
8. **Constitution precedence**: If an insight or pattern in context.md conflicts with a rule in CLAUDE.md, the CLAUDE.md rule wins unconditionally. The conflicting context.md entry should be dropped during generation rather than included with conflicting guidance.
9. **Human-readable staleness**: Every entry in Active Rules must include a staleness tier with a human-readable action cue. Active Rules only contains insights with freshness >= 0.3. Tiers:
   - **fresh** (freshness > 0.7): "confirmed N days ago" — no action cue needed
   - **aging** (freshness 0.3–0.7): "last confirmed N days ago — verify before relying on this"
   Insights below 0.3 do NOT appear in Active Rules — they go exclusively to Archive References (see below). This avoids mixing active guidance with stale entries.
   Human-readable cues empirically outperform raw dates because they trigger verification behavior rather than requiring mental arithmetic.

## Output Format

```markdown
# Dynamic Project Knowledge
<!-- GENERATED OVERLAY — this file is a computed view, not a source of truth -->
<!-- Regenerated from scratch by /reflect from typed records in .reflect/ -->
<!-- Human-authored rules in CLAUDE.md always take precedence over this file -->
<!-- Last updated: <ISO-8601 timestamp> -->
<!-- Source: <N> insights, <N> decisions, <N> file maps -->
<!-- Entries expire when their freshness score drops below the configured threshold -->

## Recent Failures
<!-- Sessions with outcome: partial or failure, plus anti-pattern/pitfall insights, last 3 -->
<!-- Surfaces what didn't work so agents avoid repeating it -->
- **<failure pattern or session outcome>** (<date>) — <one-line description with evidence pointer>

## Active Rules
<!-- HIGH confidence insights with freshness >= 0.3, sorted by freshness descending -->
<!-- Staleness tiers: fresh (>0.7), aging (0.3-0.7) — below 0.3 goes to Archive References -->
- <Actionable rule> (HIGH, 3x) — fresh, confirmed 2 days ago
- <Another rule> (MEDIUM, 2x) — aging, last confirmed 45 days ago — verify before relying on this

## Key Decisions
<!-- Accepted decisions, most recent first -->
- **<Decision title>**: <One-line summary of what was decided and why> (<YYYY-MM-DD>)

## File Notes
<!-- Knowledge for files changed in the last 5 sessions -->
- `<file-path>`: <Most important fact or pitfall>

## Watch Out
<!-- Recent failure patterns and pitfalls, if any -->
- <Failure pattern description> (seen <N>x)

## Archive References
<!-- Insights below freshness threshold (< 0.3) — demoted, not excluded -->
<!-- Max 5 entries, one-line each with file path for deep-dive -->
- <Old insight title> — `.reflect/insights/<slug>.md` (last seen <N> days ago)
```

### Section Rules

- **Recent Failures**: Include the last 3 items from: sessions with `outcome: partial` or `outcome: failure`, plus `anti-pattern`/`pitfall` insights from recent sessions. Sort by date descending. Each entry should include a one-line evidence pointer (error message, pattern name, or session ID). Max 3 entries.
- **Active Rules**: Include all HIGH-confidence insights above freshness threshold. If there are MEDIUM insights that were seen 2+ times, include those too. Max 15 rules.
- **Key Decisions**: Include all accepted decisions, sorted by date descending. Decisions do not decay — they remain valid until superseded. Cap at 10 entries for space, preferring more recent decisions when trimming.
- **File Notes**: Include file knowledge maps for files that appeared in the last 5 sessions. One line per file. Max 10 files.
- **Watch Out**: Include anti-pattern and pitfall insights not yet baked. Max 5 entries.
- **Archive References**: Include insights that have dropped below the freshness threshold (< 0.3) — demoted rather than excluded. One line each with the file path so agents can dig deeper if needed during regression debugging. Max 5 entries, sorted by `times_seen` descending (most-observed first).
- **Omit any section** that would be empty.
- If total content exceeds the line budget, trim from the bottom of each section (least important items first).
- **Nudge for unanalyzed sessions**: After generating the file, if Entire has sessions newer than the most recent `.reflect/sessions/*.md`, append: `<!-- N new sessions since last /reflect — run /reflect to capture new evidence -->`. This is a no-op for git (context.md is gitignored) but visible to agents loading the file.
