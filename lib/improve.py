"""reflect improve — analyze harness effectiveness, propose changes.

Gathers evidence about what the harness produced vs what sessions actually
needed, then outputs a structured analysis the running LLM can act on.

reflect does not call LLMs — it prepares the evidence. The agent reasons.
"""

import os
import re
import sys
from pathlib import Path

# Import from the harness to reuse evidence readers
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from harness.default import (
    get_entire_checkpoints,
    get_entire_transcript,
    has_entire,
    has_git,
    run,
)


def analyze_context_quality(context_md):
    """Find issues in the generated context.md."""
    issues = []
    lines = context_md.strip().split("\n")

    for i, line in enumerate(lines):
        # Detect session intents leaking as decisions (user prompts, not real decisions)
        if line.startswith("- ") and "→" in line:
            # Check if the "decision" is actually just a user question/prompt
            parts = line.split("→")
            if len(parts) == 2:
                intent = parts[0].strip("- ").strip()
                commit_msg = parts[1].strip().strip("`")
                # User questions leaking as decisions
                if any(intent.lower().startswith(q) for q in [
                    "question", "help me", "how ", "what ", "why ", "can ",
                    "i want", "let's", "please",
                ]):
                    issues.append({
                        "type": "noise",
                        "line": i + 1,
                        "detail": f"User prompt leaked as decision: '{intent[:60]}...'",
                        "fix_hint": "Filter checkpoints where intent looks like a user question, not a task",
                    })
                # Commit message is just echoing the intent
                if _similarity(intent.lower(), commit_msg.lower()) > 0.6:
                    issues.append({
                        "type": "echo",
                        "line": i + 1,
                        "detail": f"Commit message echoes intent — no signal added",
                        "fix_hint": "Skip decisions where commit message ~= intent (no transformation happened)",
                    })
                # Truncation artifacts
                if commit_msg.endswith("...") or intent.endswith("..."):
                    issues.append({
                        "type": "truncation",
                        "line": i + 1,
                        "detail": "Truncated text in decision — reader can't act on it",
                        "fix_hint": "Summarize rather than truncate, or skip entries that don't fit",
                    })

        # Vague focus keywords
        if line.startswith("Recent work touches:"):
            words = line.split(":")[1].strip().rstrip(".").split(", ")
            vague = [w for w in words if len(w) <= 3 or w in [
                "add", "get", "set", "run", "use", "fix", "new", "update",
            ]]
            if len(vague) > len(words) // 2:
                issues.append({
                    "type": "vague_focus",
                    "line": i + 1,
                    "detail": f"Focus keywords too generic: {vague}",
                    "fix_hint": "Use bigrams or filter out action verbs from focus keywords",
                })

    return issues


def analyze_transcript_gaps(checkpoints):
    """Find things sessions needed that the harness didn't surface."""
    gaps = []

    for cp in checkpoints[:5]:
        transcript = get_entire_transcript(cp["id"], max_lines=300)
        if not transcript:
            continue

        lines = transcript.split("\n")
        user_lines = [l for l in lines if l.startswith("[User]")]
        assistant_lines = [l for l in lines if l.startswith("[Assistant]")]

        # Detect repeated explanations — user re-explaining the same thing
        explained_topics = []
        for ul in user_lines:
            text = ul.split("] ", 1)[-1].lower() if "] " in ul else ""
            if len(text) > 30:
                explained_topics.append(text[:80])

        # Detect the agent searching for context it should have had
        search_patterns = []
        for al in assistant_lines:
            text = al.split("] ", 1)[-1] if "] " in al else ""
            # Agent grepping for project info = context gap
            if any(kw in text.lower() for kw in [
                "let me search", "let me find", "let me look",
                "let me check", "searching for",
            ]):
                search_patterns.append(text[:100])

        if search_patterns:
            gaps.append({
                "session": cp["id"][:12],
                "intent": cp.get("intent", "")[:80],
                "type": "agent_searching",
                "detail": f"Agent spent time searching — harness could pre-surface this",
                "examples": search_patterns[:3],
            })

    return gaps


def _similarity(a, b):
    """Jaccard word similarity."""
    wa = set(a.split())
    wb = set(b.split())
    if not wa or not wb:
        return 0
    return len(wa & wb) / len(wa | wb)


def cmd_improve(args):
    """Output analysis + harness source for the running LLM to propose changes."""
    reflect_dir = Path(".reflect")
    harness_path = reflect_dir / "harness"
    context_file = reflect_dir / "context.md"

    if not reflect_dir.exists():
        print("No .reflect/ directory. Run `reflect init` first.", file=sys.stderr)
        return 1

    # --- Gather evidence ---
    sections = []
    sections.append("# Harness Improvement Analysis")
    sections.append("")

    # 1. Current context quality
    if context_file.exists():
        context_md = context_file.read_text()
        issues = analyze_context_quality(context_md)
        sections.append("## Context Quality Issues")
        if issues:
            for issue in issues:
                sections.append(f"- **{issue['type']}** (line {issue['line']}): {issue['detail']}")
                sections.append(f"  Fix: {issue['fix_hint']}")
        else:
            sections.append("- No issues detected in current context.md")
        sections.append("")

        sections.append("## Current context.md")
        sections.append("```markdown")
        sections.append(context_md.strip())
        sections.append("```")
        sections.append("")

    # 2. Transcript gaps
    if has_entire():
        checkpoints = get_entire_checkpoints()[:6]
        gaps = analyze_transcript_gaps(checkpoints)
        sections.append("## Evidence Gaps")
        if gaps:
            for gap in gaps:
                sections.append(f"- **{gap['type']}** (session {gap['session']}): {gap['detail']}")
                for ex in gap.get("examples", []):
                    sections.append(f"  - `{ex[:80]}`")
        else:
            sections.append("- No obvious gaps detected")
        sections.append("")

    # 3. Harness source (so the LLM can propose changes)
    harness_source = None
    if harness_path.exists():
        # Resolve symlink to get actual harness source
        real_path = harness_path.resolve()
        harness_source = real_path.read_text()
        sections.append(f"## Current Harness Source ({real_path})")
        sections.append("```python")
        sections.append(harness_source.strip())
        sections.append("```")
        sections.append("")

    # 4. Improvement prompt for the LLM
    sections.append("## Suggested Action")
    sections.append("")
    sections.append("Based on the issues above, propose specific edits to the harness source.")
    sections.append("Focus on changes that:")
    sections.append("1. Reduce noise (filter out non-decisions, vague keywords)")
    sections.append("2. Fill gaps (surface information the agent had to search for)")
    sections.append("3. Are minimal — change the least code for the most impact")
    sections.append("")
    sections.append("The harness is a Python script. Edit it directly.")

    print("\n".join(sections))
    return 0
