#!/usr/bin/env python3
"""Compare v3 (opinionated) vs v4 (raw) context quality.

For each historical session, scores both approaches on:
1. File coverage — did context mention files the agent touched?
2. Intent relevance — did context relate to what the user asked?
3. Actionability — does the context tell the agent what to DO?

Uses Entire CLI session transcripts as ground truth.
"""

import re
import subprocess
import sys


def run(cmd, timeout=30):
    if isinstance(cmd, str):
        import shlex
        cmd = shlex.split(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def get_checkpoints():
    """Get all checkpoints with metadata."""
    raw = run(["entire", "explain", "--short", "--search-all", "--no-pager"])
    if not raw:
        return []

    checkpoints = []
    lines = raw.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        match = re.match(r'^\[([a-f0-9-]+)\]\s+(?:\[temporary\]\s+)?"(.+)"', line)
        if match:
            cp_id = match.group(1)
            intent = match.group(2).rstrip('"').replace("\\n", " ")
            i += 1
            while i < len(lines) and lines[i].startswith("  "):
                i += 1
            checkpoints.append({"id": cp_id, "intent": intent[:200]})
        else:
            i += 1
    return checkpoints


def get_session_files(checkpoint_id):
    """Get files touched in a session."""
    raw = run(["entire", "explain", "--checkpoint", checkpoint_id, "--full", "--no-pager"], timeout=15)
    if not raw:
        return []
    files = []
    in_files = False
    for line in raw.split("\n"):
        if line.startswith("Files:"):
            in_files = True
            continue
        if in_files:
            if line.startswith("  - "):
                f = line.strip().lstrip("- ").strip()
                # Normalize to relative path
                f = f.split("/Repos/reflect/")[-1] if "/Repos/reflect/" in f else f
                files.append(f)
            elif not line.startswith("  "):
                break
    return files


def score_file_coverage(context, files_touched):
    """What fraction of touched files are mentioned in context?"""
    if not files_touched:
        return None  # Skip sessions with no file data
    context_lower = context.lower()
    mentioned = 0
    for f in files_touched:
        # Check various forms: full path, filename only, directory
        fname = f.split("/")[-1].lower()
        if fname in context_lower or f.lower() in context_lower:
            mentioned += 1
    return mentioned / len(files_touched)


def score_intent_relevance(context, intent):
    """Do any words from the intent appear in context?"""
    # Extract meaningful words from intent (skip common words)
    stop_words = {"the", "a", "an", "is", "to", "in", "for", "of", "and", "or", "we", "i", "it", "this", "that", "can", "how", "with", "also", "lets", "let"}
    intent_words = set()
    for w in re.findall(r'[a-zA-Z]+', intent.lower()):
        if len(w) > 2 and w not in stop_words:
            intent_words.add(w)

    if not intent_words:
        return None

    context_lower = context.lower()
    matched = sum(1 for w in intent_words if w in context_lower)
    return matched / len(intent_words)


def score_actionability(context):
    """How many actionable directives does the context contain?

    Actionable = imperative sentences, warnings, rules, decisions.
    Raw data (commit messages, session intents) = not actionable.
    """
    actionable_patterns = [
        r"always\s+\w+",        # "always verify..."
        r"never\s+\w+",         # "never include..."
        r"confirm\s+\w+",       # "confirm with user..."
        r"check\s+\w+",         # "check before..."
        r"watch out",           # warnings
        r"avoid\s+\w+",         # "avoid doing..."
        r"make sure",           # directives
        r"don't\s+\w+",        # negative directives
        r"chose\s+\w+.+over",  # decision rationale
        r"because\s+\w+",      # reasoning
    ]
    count = 0
    context_lower = context.lower()
    for pattern in actionable_patterns:
        count += len(re.findall(pattern, context_lower))
    return count


def main():
    # Get the old v3 context from git
    v3_context = run(["git", "show", "HEAD:.reflect/context.md"])
    if not v3_context:
        print("Could not retrieve old v3 context.md from git history.", file=sys.stderr)
        return 1

    # Get the new v4 context
    try:
        with open(".reflect/context.md") as f:
            v4_context = f.read()
    except FileNotFoundError:
        print("No .reflect/context.md found. Run `reflect context` first.", file=sys.stderr)
        return 1

    print("# Context Quality: v3 (opinionated) vs v4 (raw harness)")
    print()

    # Show contexts side by side (summary)
    v3_lines = len([l for l in v3_context.split("\n") if l.strip()])
    v4_lines = len([l for l in v4_context.split("\n") if l.strip()])
    print(f"| Metric | v3 (opinionated) | v4 (raw harness) |")
    print(f"|--------|-----------------|-----------------|")
    print(f"| Lines (non-empty) | {v3_lines} | {v4_lines} |")

    # Actionability
    v3_actionability = score_actionability(v3_context)
    v4_actionability = score_actionability(v4_context)
    print(f"| Actionable directives | {v3_actionability} | {v4_actionability} |")

    # Score against each historical session
    checkpoints = get_checkpoints()
    if not checkpoints:
        print("\nNo Entire checkpoints available for session-level comparison.")
        return 0

    v3_file_scores = []
    v4_file_scores = []
    v3_intent_scores = []
    v4_intent_scores = []

    print(f"\n## Per-Session Scores ({len(checkpoints)} sessions)\n")
    print(f"| Session | Intent (short) | v3 file cov | v4 file cov | v3 intent | v4 intent |")
    print(f"|---------|---------------|-------------|-------------|-----------|-----------|")

    for cp in checkpoints:
        files = get_session_files(cp["id"])
        intent_short = cp["intent"][:50]

        v3_fc = score_file_coverage(v3_context, files)
        v4_fc = score_file_coverage(v4_context, files)
        v3_ir = score_intent_relevance(v3_context, cp["intent"])
        v4_ir = score_intent_relevance(v4_context, cp["intent"])

        if v3_fc is not None:
            v3_file_scores.append(v3_fc)
            v4_file_scores.append(v4_fc)

        if v3_ir is not None:
            v3_intent_scores.append(v3_ir)
            v4_intent_scores.append(v4_ir)

        v3_fc_str = f"{v3_fc:.2f}" if v3_fc is not None else "n/a"
        v4_fc_str = f"{v4_fc:.2f}" if v4_fc is not None else "n/a"
        v3_ir_str = f"{v3_ir:.2f}" if v3_ir is not None else "n/a"
        v4_ir_str = f"{v4_ir:.2f}" if v4_ir is not None else "n/a"

        print(f"| `{cp['id'][:12]}` | {intent_short} | {v3_fc_str} | {v4_fc_str} | {v3_ir_str} | {v4_ir_str} |")

    # Aggregates
    if v3_file_scores:
        v3_fc_mean = sum(v3_file_scores) / len(v3_file_scores)
        v4_fc_mean = sum(v4_file_scores) / len(v4_file_scores)
    else:
        v3_fc_mean = v4_fc_mean = 0

    if v3_intent_scores:
        v3_ir_mean = sum(v3_intent_scores) / len(v3_intent_scores)
        v4_ir_mean = sum(v4_intent_scores) / len(v4_intent_scores)
    else:
        v3_ir_mean = v4_ir_mean = 0

    print(f"\n## Aggregate Scores\n")
    print(f"| Metric | v3 | v4 | Winner |")
    print(f"|--------|-----|-----|--------|")

    fc_winner = "v3" if v3_fc_mean > v4_fc_mean else "v4" if v4_fc_mean > v3_fc_mean else "tie"
    ir_winner = "v3" if v3_ir_mean > v4_ir_mean else "v4" if v4_ir_mean > v3_ir_mean else "tie"
    act_winner = "v3" if v3_actionability > v4_actionability else "v4" if v4_actionability > v3_actionability else "tie"

    print(f"| File coverage (mean) | {v3_fc_mean:.3f} | {v4_fc_mean:.3f} | **{fc_winner}** |")
    print(f"| Intent relevance (mean) | {v3_ir_mean:.3f} | {v4_ir_mean:.3f} | **{ir_winner}** |")
    print(f"| Actionable directives | {v3_actionability} | {v4_actionability} | **{act_winner}** |")

    print(f"\n## Analysis\n")
    if v3_actionability > v4_actionability:
        print("v3 is more actionable — it tells the agent what to DO (rules, decisions, warnings).")
        print("v4 is more informational — it shows what HAPPENED (sessions, commits).")
    print()
    if v4_fc_mean > v3_fc_mean:
        print("v4 has better file coverage — commit messages mention more files the agent will touch.")
    elif v3_fc_mean > v4_fc_mean:
        print("v3 has better file coverage — curated insights are more targeted than raw commit log.")
    print()
    print("Key insight: the default v4 harness is deliberately simple. These scores")
    print("establish the baseline. A smarter harness can combine v4's breadth with v3's actionability.")

    return 0


if __name__ == "__main__":
    sys.exit(main() or 0)
