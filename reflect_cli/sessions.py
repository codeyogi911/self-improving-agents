"""reflect sessions — list and inspect sessions via Entire CLI."""

import sys
from datetime import datetime
from .sources import has_entire, get_entire_sessions, get_session_info


def _format_duration(started_at, ended_at):
    """Compute human-readable duration from ISO timestamps."""
    try:
        start = datetime.fromisoformat(started_at)
        end = datetime.fromisoformat(ended_at)
        delta = end - start
        total_secs = int(delta.total_seconds())
        if total_secs < 60:
            return f"{total_secs}s"
        if total_secs < 3600:
            return f"{total_secs // 60}m"
        hours = total_secs // 3600
        mins = (total_secs % 3600) // 60
        return f"{hours}h {mins}m" if mins else f"{hours}h"
    except (ValueError, TypeError):
        return "?"


def _format_tokens(total):
    """Format token count with K/M suffix."""
    if total >= 1_000_000:
        return f"{total / 1_000_000:.1f}M"
    if total >= 1_000:
        return f"{total / 1_000:.1f}k"
    return str(total)


def _cache_hit_pct(tokens):
    """Compute cache-hit percentage from token breakdown."""
    total = tokens.get("total", 0)
    cache_read = tokens.get("cache_read", 0)
    if total <= 0:
        return 0
    return round(cache_read / total * 100)


def _show_list(limit):
    """List recent sessions with computed fields."""
    sessions = get_entire_sessions()
    if not sessions:
        print("No sessions found. Is Entire CLI configured?")
        return 1

    shown = 0
    print(f"## Sessions\n")
    for s in sessions:
        if shown >= limit:
            break
        info = get_session_info(s["session_id"], filter_project=True)
        if not info:
            continue
        shown += 1

        status = info.get("status", "?")
        tokens = info.get("tokens", {})
        total_tok = tokens.get("total", 0)
        cache_pct = _cache_hit_pct(tokens)
        files = info.get("files_touched", [])
        turns = info.get("turns", 0)

        duration = "active"
        if info.get("ended_at"):
            duration = _format_duration(info["started_at"], info["ended_at"])

        # Date
        try:
            dt = datetime.fromisoformat(info["started_at"])
            date_str = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, KeyError):
            date_str = "?"

        prompt = s.get("prompt_snippet", "")[:60]
        agent = info.get("agent", "?")

        status_icon = "*" if status == "active" else "-"
        print(f"{status_icon} {date_str}  {agent}  [{status}]  \"{prompt}\"")
        print(f"  Tokens: {_format_tokens(total_tok)} (cache: {cache_pct}%)  "
              f"Duration: {duration}  Turns: {turns}  Files: {len(files)}")
    print()
    return 0


def _show_detail(session_id):
    """Show full detail for a single session."""
    info = get_session_info(session_id)
    if not info:
        # Try prefix match
        sessions = get_entire_sessions()
        for s in sessions:
            if s["session_id"].startswith(session_id):
                info = get_session_info(s["session_id"])
                break
    if not info:
        print(f"Session not found: {session_id}", file=sys.stderr)
        return 1

    tokens = info.get("tokens", {})
    files = info.get("files_touched", [])

    print(f"## Session {info['session_id']}\n")
    print(f"Agent: {info.get('agent', '?')}")
    print(f"Status: {info.get('status', '?')}")

    try:
        dt = datetime.fromisoformat(info["started_at"])
        print(f"Started: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
    except (ValueError, KeyError):
        pass

    if info.get("ended_at"):
        duration = _format_duration(info["started_at"], info["ended_at"])
        print(f"Duration: {duration}")

    print(f"Turns: {info.get('turns', 0)}")
    print(f"Checkpoints: {info.get('checkpoints', 0)}")

    # Token breakdown
    total = tokens.get("total", 0)
    print(f"\nTokens: {_format_tokens(total)} total")
    print(f"  Input: {_format_tokens(tokens.get('input', 0))}")
    print(f"  Cache read: {_format_tokens(tokens.get('cache_read', 0))} ({_cache_hit_pct(tokens)}%)")
    print(f"  Cache write: {_format_tokens(tokens.get('cache_write', 0))}")
    print(f"  Output: {_format_tokens(tokens.get('output', 0))}")

    if files:
        print(f"\nFiles touched ({len(files)}):")
        for f in files:
            print(f"  - {f}")

    prompt = info.get("last_prompt", "")
    if prompt:
        print(f"\nLast prompt: {prompt[:200]}")

    print()
    return 0


def cmd_sessions(args):
    """List or inspect sessions tracked by Entire CLI."""
    if not has_entire():
        print("reflect sessions requires Entire CLI. Install from https://entire.dev", file=sys.stderr)
        return 1

    session_id = getattr(args, "session_id", None)
    limit = getattr(args, "limit", 15)

    if session_id:
        return _show_detail(session_id)
    return _show_list(limit)
