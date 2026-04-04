"""reflect why — search + entire explain detail + cross-session synthesis."""

import io
import shutil
import sys
from .sources import (
    has_entire, has_git, get_entire_checkpoints,
    get_checkpoint_for_commit, get_session_info, run
)


def _query_words(query):
    """Split query into lowercase words for flexible matching."""
    return [w for w in query.lower().split() if len(w) >= 2]


def _matches_text(words, text, require_all=True):
    if not words:
        return False
    text_lower = text.lower()
    if require_all:
        return all(w in text_lower for w in words)
    return any(w in text_lower for w in words)


def _is_reflect_session(cp):
    """Filter out sessions spawned by reflect why itself."""
    intent = cp["intent"].lower()
    if intent.startswith("## question"):
        return True
    for c in cp["commits"]:
        msg = c["message"].lower()
        if msg.startswith("## question") or "evidence (untrusted raw data)" in msg:
            return True
    return False


# ── Step 1: Search — find relevant checkpoint IDs ──────────────────────


def _search_checkpoints(words, query):
    """Find checkpoint IDs relevant to query. Returns deduplicated list of IDs."""
    checkpoint_ids = []
    seen = set()

    def _add(cp_id):
        if cp_id and cp_id not in seen:
            seen.add(cp_id)
            checkpoint_ids.append(cp_id)

    # 1a: keyword match over entire explain --short listing
    if has_entire():
        checkpoints = [cp for cp in get_entire_checkpoints() if not _is_reflect_session(cp)]
        for cp in checkpoints:
            searchable = cp["intent"].lower()
            for c in cp["commits"]:
                searchable += " " + c["message"].lower()
            if _matches_text(words, searchable):
                _add(cp["id"])

        # Relax to OR if too few
        if len(checkpoint_ids) < 2 and len(words) > 1:
            for cp in checkpoints:
                searchable = cp["intent"].lower()
                for c in cp["commits"]:
                    searchable += " " + c["message"].lower()
                if _matches_text(words, searchable, require_all=False):
                    _add(cp["id"])

    # 1b: git log --grep → commit SHAs → entire explain --commit → checkpoint IDs
    if has_git() and has_entire():
        for word in words:
            git_shas = run(["git", "log", "--all", "-20",
                            "--format=%h", f"--grep={word}", "-i"])
            if git_shas:
                for sha in git_shas.strip().split("\n"):
                    sha = sha.strip()
                    if not sha:
                        continue
                    # Filter out reflect-why commits
                    msg = run(["git", "log", "-1", "--format=%s", sha])
                    if msg and ("## Question" in msg or "Evidence (untrusted" in msg):
                        continue
                    cp = get_checkpoint_for_commit(sha)
                    if cp:
                        _add(cp["id"])

    # 1c: file path search
    if has_git() and has_entire() and ("/" in query or "." in query):
        git_shas = run(["git", "log", "--all", "-10", "--format=%h", "--", query])
        if git_shas:
            for sha in git_shas.strip().split("\n"):
                sha = sha.strip()
                if sha:
                    cp = get_checkpoint_for_commit(sha)
                    if cp:
                        _add(cp["id"])

    return checkpoint_ids[:8]  # cap to avoid excessive entire explain calls


# ── Step 2: Enrich — pull full detail from entire explain ───────────────


def _get_checkpoint_detail(checkpoint_id):
    """Get full structured output from entire explain --checkpoint."""
    raw = run(
        ["entire", "explain", "--checkpoint", checkpoint_id, "--no-pager"],
        timeout=15,
    )
    if not raw:
        return None

    # Parse into sections
    detail = {"raw": raw, "id": checkpoint_id}
    for line in raw.split("\n"):
        if line.startswith("Intent:"):
            detail["intent"] = line.split(":", 1)[1].strip()
        elif line.startswith("Outcome:"):
            detail["outcome"] = line.split(":", 1)[1].strip()
        elif line.startswith("Created:"):
            detail["date"] = line.split(":", 1)[1].strip()[:10]
        elif line.startswith("Session:"):
            detail["session_id"] = line.split(":", 1)[1].strip()
        elif line.startswith("Tokens:"):
            try:
                detail["tokens"] = int(line.split(":", 1)[1].strip())
            except ValueError:
                pass

    # Extract everything from Intent: through Files: (the structured meat)
    lines = raw.split("\n")
    start = end = None
    for i, line in enumerate(lines):
        if line.startswith("Intent:") and start is None:
            start = i
        if line.startswith("Files:") or line.startswith("Transcript (checkpoint scope):"):
            end = i
            break
    if start is not None:
        end = end or len(lines)
        detail["structured"] = "\n".join(lines[start:end]).strip()

    return detail


def _enrich_checkpoints(checkpoint_ids):
    """Pull entire explain detail + session info for each checkpoint ID."""
    details = []
    session_cache = {}
    for cp_id in checkpoint_ids:
        detail = _get_checkpoint_detail(cp_id)
        if detail and detail.get("structured"):
            # Enrich with session-level metadata
            sid = detail.get("session_id")
            if sid:
                if sid not in session_cache:
                    session_cache[sid] = get_session_info(sid)
                detail["_session_info"] = session_cache.get(sid)
            details.append(detail)
    return details


# ── Step 3: Build evidence document ────────────────────────────────────


def _build_evidence(query, words, details):
    """Combine enriched checkpoint details + git context into evidence."""
    buf = io.StringIO()

    # Checkpoint details (the core — from entire explain)
    if details:
        buf.write(f"## Sessions ({len(details)} relevant)\n\n")
        for d in details:
            buf.write(f"### Checkpoint {d['id'][:12]}")
            if d.get("date"):
                buf.write(f" ({d['date']})")
            buf.write("\n")
            # Session context line
            si = d.get("_session_info")
            if si:
                tokens = si.get("tokens", {})
                total_tok = tokens.get("total", 0)
                files = si.get("files_touched", [])
                turns = si.get("turns", 0)
                tok_str = f"{total_tok / 1000:.1f}k" if total_tok >= 1000 else str(total_tok)
                buf.write(f"Session: {si.get('agent', '?')} · {turns} turns · "
                          f"{tok_str} tokens · {len(files)} files\n")
            buf.write(d["structured"])
            buf.write("\n\n")

    # Git commit details for file-path queries (diff stat)
    if has_git() and ("/" in query or "." in query):
        git_log = run(["git", "log", "--all", "-10", "--follow",
                        "--format=%h %ad %s", "--date=short", "--", query])
        if git_log:
            buf.write(f"## File History: {query}\n\n")
            for line in git_log.strip().split("\n")[:8]:
                buf.write(f"- {line}\n")
            buf.write("\n")

    return buf.getvalue()


# ── Entry point ─────────────────────────────────────────────────────────


def cmd_why(args):
    """Answer questions about project history using entire explain + synthesis."""
    query = " ".join(args.query)
    if not query:
        print("Usage: reflect why <file-or-topic>", file=sys.stderr)
        return 1

    words = _query_words(query)
    raw_mode = getattr(args, "raw", False)
    verbose = getattr(args, "verbose", False)

    if not has_entire():
        print("reflect why requires Entire CLI. Install from https://entire.dev", file=sys.stderr)
        return 1

    # Step 1: Search
    if verbose:
        print("  [search] finding relevant checkpoints...", file=sys.stderr)
    checkpoint_ids = _search_checkpoints(words, query)

    if not checkpoint_ids:
        print(f"No sessions found matching '{query}'.")
        return 1

    if verbose:
        print(f"  [search] found {len(checkpoint_ids)} checkpoints", file=sys.stderr)

    # Step 2: Enrich via entire explain
    if verbose:
        print("  [enrich] pulling detail from entire explain...", file=sys.stderr)
    details = _enrich_checkpoints(checkpoint_ids[:5])  # top 5

    if not details:
        print(f"No detailed evidence found for '{query}'.")
        return 1

    # Step 3: Build evidence
    evidence = _build_evidence(query, words, details)

    # Raw mode: dump evidence
    if raw_mode:
        print(evidence)
        return 0

    # Step 4: Synthesize via LLM
    if not shutil.which("claude"):
        print("Note: claude CLI not found, showing raw evidence.\n", file=sys.stderr)
        print(evidence)
        return 0

    from .synthesize import synthesize

    result = synthesize(query, evidence, verbose=verbose)

    if result is None:
        print("Synthesis failed, showing raw evidence.\n", file=sys.stderr)
        print(evidence)
        return 0

    answer, confidence, sources = result
    print(answer)
    print()
    if sources:
        print(f"Sources: {', '.join(sources)}")
    print(f"Confidence: {confidence}")

    if verbose:
        print(f"\n--- Raw Evidence ---\n", file=sys.stderr)
        print(evidence, file=sys.stderr)

    return 0
