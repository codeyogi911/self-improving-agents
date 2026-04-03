#!/usr/bin/env python3
"""Default reflect harness — closed-loop context generation.

Reads Entire CLI transcripts + git history + notes on demand.
Extracts signals (corrections, decisions, hot files, open threads)
from session transcripts and generates semantic context — not git log.

Zero intermediate storage. Entire is the memory; this is the lens.
"""

import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Subprocess helper
# ---------------------------------------------------------------------------

def run(cmd, timeout=30):
    """Run a command and return stdout, or empty string on failure."""
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return result.stdout.strip() if result.returncode == 0 else ""
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""

# ---------------------------------------------------------------------------
# Evidence source readers
# ---------------------------------------------------------------------------

def has_entire():
    return shutil.which("entire") is not None

def has_git():
    return bool(run(["git", "rev-parse", "--is-inside-work-tree"]))

def get_entire_checkpoints():
    """Get all checkpoints from Entire CLI."""
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
            commits = []
            dates = []
            i += 1
            while i < len(lines) and lines[i].startswith("  "):
                commit_match = re.match(
                    r"^\s+(\d{2}-\d{2})\s+(\d{2}:\d{2})?\s*\(([a-f0-9]+)\)\s+(.*)",
                    lines[i],
                )
                if commit_match:
                    dates.append(commit_match.group(1))
                    commits.append({
                        "sha": commit_match.group(3),
                        "message": commit_match.group(4).strip(),
                    })
                i += 1
            checkpoints.append({
                "id": cp_id,
                "intent": intent[:200],
                "date": dates[0] if dates else "",
                "commits": commits,
            })
        else:
            i += 1
    return checkpoints

def get_entire_transcript(checkpoint_id, max_lines=200):
    """Get full transcript for a checkpoint, truncated."""
    raw = run(
        ["entire", "explain", "--checkpoint", checkpoint_id, "--full", "--no-pager"],
        timeout=15,
    )
    if not raw:
        return ""
    lines = raw.split("\n")
    return "\n".join(lines[:max_lines])

def get_notes(notes_dir):
    """Read manual notes from .reflect/notes/."""
    notes = []
    if not notes_dir.exists():
        return notes
    for f in sorted(notes_dir.glob("*.md")):
        content = f.read_text().strip()
        if content:
            notes.append({"name": f.stem, "content": content})
    return notes

# ---------------------------------------------------------------------------
# Signal extraction
# ---------------------------------------------------------------------------

CORRECTION_PREFIXES = [
    "no,", "no ", "don't", "stop", "wait,", "actually,", "actually ",
    "that's wrong", "that's not", "not what i", "i said", "i meant",
    "undo", "revert", "go back", "wrong", "incorrect",
]

FILE_PATH_RE = re.compile(
    r'(?:Read|Edit|Write|Created|Modified|Glob|Grep)\s+[`"]?'
    r'([A-Za-z0-9_./-]+\.[a-z]{1,10})'
)
BARE_PATH_RE = re.compile(
    r'(?:^|\s)([a-zA-Z0-9_]+(?:/[a-zA-Z0-9_.]+)+\.[a-z]{1,10})'
)


def extract_signals(transcript, checkpoint):
    """Extract corrections, hot files, and open-thread flag from a transcript."""
    corrections = []
    file_mentions = Counter()
    last_assistant_line = ""

    for line in transcript.split("\n"):
        # Track assistant context for pairing with corrections
        if line.startswith("[Assistant]"):
            last_assistant_line = line.split("] ", 1)[-1][:120]
            continue

        # Detect corrections in user messages
        if line.startswith("[User]"):
            user_text = line.split("] ", 1)[-1]
            if len(user_text) >= 10:
                lower = user_text.lower().strip()
                if any(lower.startswith(p) for p in CORRECTION_PREFIXES):
                    corrections.append({
                        "date": checkpoint.get("date", ""),
                        "user_said": user_text[:150],
                        "context": last_assistant_line,
                        "session_id": checkpoint["id"][:12],
                    })

        # Detect file paths in tool calls and content
        for match in FILE_PATH_RE.finditer(line):
            path = match.group(1)
            if not path.startswith(".") and "/" in path:
                file_mentions[path] += 1
        for match in BARE_PATH_RE.finditer(line):
            path = match.group(1)
            if not path.startswith("."):
                file_mentions[path] += 1

    is_open_thread = bool(checkpoint.get("intent")) and not checkpoint.get("commits")

    return {
        "corrections": corrections,
        "file_mentions": file_mentions,
        "is_open_thread": is_open_thread,
    }

# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------

def build_warnings(all_corrections, max_lines=10):
    """Build Warnings section from corrections across all sessions."""
    if not all_corrections:
        return []
    lines = ["## Warnings"]
    # Deduplicate by user_said prefix (first 60 chars)
    seen = set()
    for c in all_corrections:
        key = c["user_said"][:60].lower()
        if key in seen:
            continue
        seen.add(key)
        text = c["user_said"]
        if len(text) > 100:
            text = text[:100] + "..."
        lines.append(f"- **{text}** — {c['date']} (session {c['session_id']})")
        if len(lines) >= max_lines:
            break
    lines.append("")
    return lines


QUESTION_PREFIXES = [
    "question", "help me", "how ", "what ", "why ", "can ",
    "i want", "let's", "please", "could you", "tell me",
]


def _is_noisy_decision(intent, commit_msg):
    """Filter decisions that are user prompts or echo the intent."""
    lower_intent = intent.lower().strip()
    # User questions/requests are not decisions
    if any(lower_intent.startswith(p) for p in QUESTION_PREFIXES):
        return True
    # Commit message just echoes the intent — no signal
    intent_words = set(lower_intent.split())
    commit_words = set(commit_msg.lower().split())
    if intent_words and commit_words:
        overlap = len(intent_words & commit_words) / len(intent_words | commit_words)
        if overlap > 0.6:
            return True
    return False


def build_decisions(checkpoints, max_lines=15):
    """Build Key Decisions section from intent+commit pairs."""
    decisions = []
    for cp in checkpoints:
        if cp.get("commits") and cp.get("intent"):
            for commit in cp["commits"][:2]:
                if _is_noisy_decision(cp["intent"], commit["message"]):
                    continue
                decisions.append({
                    "date": cp["date"],
                    "intent": cp["intent"][:80],
                    "commit": commit["message"][:80],
                })
    if not decisions:
        return []
    lines = ["## Key Decisions"]
    for d in decisions[:max_lines - 1]:
        lines.append(f"- {d['date']}: {d['intent']} → `{d['commit']}`")
    lines.append("")
    return lines


def build_hot_areas(all_file_mentions, total_sessions, max_lines=8):
    """Build Hot Areas section from file mention frequency."""
    if not all_file_mentions:
        return []
    # Sort by count descending, only show files mentioned in 2+ sessions
    ranked = [(path, count) for path, count in all_file_mentions.most_common(20)
              if count >= 2]
    if not ranked:
        return []
    lines = ["## Hot Areas"]
    for path, count in ranked[:max_lines - 1]:
        lines.append(f"- `{path}` — touched in {count} of {total_sessions} sessions")
    lines.append("")
    return lines


def build_open_threads(checkpoints, max_lines=8):
    """Build Open Threads section — sessions with intent but no commits.

    Prune threads whose intent words overlap >50% with a later decision.
    """
    # Collect committed intents for pruning
    committed_words = set()
    for cp in checkpoints:
        if cp.get("commits") and cp.get("intent"):
            committed_words.update(_tokenize(cp["intent"]))

    threads = []
    for cp in checkpoints:
        if cp.get("intent") and not cp.get("commits"):
            intent_words = _tokenize(cp["intent"])
            if not intent_words:
                continue
            overlap = len(intent_words & committed_words) / len(intent_words)
            if overlap < 0.5:
                threads.append(cp)

    if not threads:
        return []
    lines = ["## Open Threads"]
    for cp in threads[:max_lines - 1]:
        lines.append(f"- {cp['intent'][:100]} ({cp['date']}, no commits)")
    lines.append("")
    return lines


STOPWORDS = frozenset(
    "a an the is are was were be been being have has had do does did will would "
    "shall should may might can could of in to for on with at by from as into "
    "through during before after above below between out off over under again "
    "further then once here there when where why how all each every both few "
    "more most other some such no nor not only own same so than too very and "
    "but or if while about against it its this that these those i me my we our "
    "you your he him his she her they them their what which who whom".split()
)


def _tokenize(text):
    """Lowercase word tokenization with stopword removal."""
    words = set(re.findall(r'[a-z][a-z0-9_]+', text.lower()))
    return words - STOPWORDS


GENERIC_VERBS = frozenset(
    "add get set run use fix new update check make create delete remove "
    "change move copy find show help explore look try start".split()
)


def build_focus(checkpoints, max_lines=4):
    """Build Current Focus — keyword summary of recent session intents."""
    if not checkpoints:
        return []
    # Count topic words across recent intents
    topic_counts = Counter()
    for cp in checkpoints[:5]:
        if cp.get("intent"):
            topic_counts.update(_tokenize(cp["intent"]))
    # Filter out generic verbs and short words — keep domain-specific terms
    top_topics = [
        word for word, _ in topic_counts.most_common(15)
        if len(word) > 3 and word not in GENERIC_VERBS
    ]
    if not top_topics:
        return []
    lines = ["## Current Focus"]
    lines.append(f"Recent work touches: {', '.join(top_topics[:6])}.")
    lines.append("")
    return lines


def build_notes(notes_dir, max_lines=15):
    """Build Notes section from .reflect/notes/."""
    notes = get_notes(notes_dir)
    if not notes:
        return []
    lines = ["## Notes"]
    remaining = max_lines - 1
    for note in notes:
        if remaining <= 0:
            break
        lines.append(f"### {note['name']}")
        remaining -= 1
        content_lines = note["content"].split("\n")
        for cl in content_lines[:min(8, remaining)]:
            lines.append(cl)
            remaining -= 1
        if len(content_lines) > 8:
            lines.append(f"_...({len(content_lines) - 8} more lines)_")
            remaining -= 1
    lines.append("")
    return lines

# ---------------------------------------------------------------------------
# Freshness state (unchanged from v4)
# ---------------------------------------------------------------------------

def get_last_run(reflect_dir):
    last_run = reflect_dir / ".last_run"
    if not last_run.exists():
        return None
    try:
        return json.loads(last_run.read_text())
    except (json.JSONDecodeError, OSError):
        return None

def write_last_run(reflect_dir, checkpoint_id, git_sha):
    last_run = reflect_dir / ".last_run"
    state = {
        "last_checkpoint": checkpoint_id,
        "last_git_sha": git_sha,
        "timestamp": datetime.now().isoformat(),
    }
    last_run.write_text(json.dumps(state))

# ---------------------------------------------------------------------------
# Main context generation
# ---------------------------------------------------------------------------

def generate_context(max_lines=150):
    """Generate semantic context from Entire transcripts + git + notes."""
    reflect_dir = Path(".reflect")
    latest_checkpoint_id = None
    latest_git_sha = None

    # --- Fetch evidence ---
    checkpoints = []
    if has_entire():
        checkpoints = get_entire_checkpoints()[:10]
        if checkpoints:
            latest_checkpoint_id = checkpoints[0]["id"]

    if has_git():
        git_sha = run(["git", "rev-parse", "--short", "HEAD"])
        if git_sha:
            latest_git_sha = git_sha

    # --- Extract signals from transcripts ---
    all_corrections = []
    all_file_mentions = Counter()
    total_sessions = len(checkpoints)

    for cp in checkpoints:
        transcript = get_entire_transcript(cp["id"], max_lines=200)
        if transcript:
            signals = extract_signals(transcript, cp)
            all_corrections.extend(signals["corrections"])
            all_file_mentions.update(signals["file_mentions"])

    # --- Assemble context with priority-based line budget ---
    sections = []

    # Header
    header_count = f"{total_sessions} sessions analyzed" if total_sessions else "no sessions"
    sections.append("# Project Context")
    sections.append(
        f"<!-- GENERATED by reflect harness — do not edit, regenerate with: reflect context -->"
    )
    sections.append(f"<!-- Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | {header_count} -->")
    sections.append("")

    # Priority order: warnings > open threads > decisions > hot areas > focus > notes
    section_builders = [
        lambda: build_warnings(all_corrections),
        lambda: build_open_threads(checkpoints),
        lambda: build_decisions(checkpoints),
        lambda: build_hot_areas(all_file_mentions, total_sessions),
        lambda: build_focus(checkpoints),
        lambda: build_notes(reflect_dir / "notes"),
    ]

    used_lines = 4  # header
    for builder in section_builders:
        section = builder()
        if section and used_lines + len(section) <= max_lines:
            sections.extend(section)
            used_lines += len(section)

    # No evidence at all
    if used_lines <= 4:
        sections.append(
            "_No evidence sources found. Install Entire CLI for session capture, "
            "or make some git commits._"
        )
        sections.append("")

    output = "\n".join(sections)

    # Update freshness state
    if reflect_dir.exists():
        write_last_run(reflect_dir, latest_checkpoint_id, latest_git_sha)

    return output


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Default reflect harness")
    parser.add_argument("--max-lines", type=int, default=150, help="Line budget for output")
    parser.add_argument("--format", choices=["md", "json"], default="md", help="Output format")
    args = parser.parse_args()

    context = generate_context(max_lines=args.max_lines)

    if args.format == "json":
        print(json.dumps({"context": context}))
    else:
        print(context)


if __name__ == "__main__":
    main()
