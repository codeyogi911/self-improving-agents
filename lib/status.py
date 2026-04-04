"""reflect status — show available evidence sources."""

import json
import sys
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from .sources import has_entire, has_git, run, get_entire_sessions, get_session_info


def cmd_status(args):
    """Show what evidence sources are available and their state."""
    reflect_dir = Path(".reflect")

    if not reflect_dir.exists():
        print("No .reflect/ directory. Run `reflect init` to get started.")
        return 1

    print("## Evidence Sources\n")

    # Entire CLI
    if has_entire():
        entire_raw = run(["entire", "status", "--no-pager"])
        entire_status = entire_raw.split("\n")[0] if entire_raw else ""
        from .sources import get_entire_checkpoints
        checkpoint_count = len(get_entire_checkpoints())
        print(f"- **Entire CLI**: available ({entire_status.strip()})")
        print(f"  Checkpoints: {checkpoint_count}")
    else:
        print("- **Entire CLI**: not installed")

    # Git
    if has_git():
        commit_count = run(["git", "rev-list", "--count", "HEAD"])
        last_commit = run(["git", "log", "-1", "--format=%h %ad %s", "--date=short"])
        print(f"- **Git**: {commit_count} commits")
        print(f"  Latest: {last_commit}")
    else:
        print("- **Git**: not a git repository")

    print()

    # Harness
    harness = reflect_dir / "harness"
    if harness.exists():
        print(f"**Harness**: {harness} (custom)" if not _is_default_harness(harness) else f"**Harness**: default")
    else:
        print("**Harness**: not installed")

    # Context freshness
    context = reflect_dir / "context.md"
    last_run = reflect_dir / ".last_run"
    if context.exists():
        import os
        from datetime import datetime
        mtime = datetime.fromtimestamp(os.path.getmtime(context))
        print(f"**Context**: last generated {mtime.strftime('%Y-%m-%d %H:%M')}")
    else:
        print("**Context**: not yet generated (run `reflect context`)")

    if last_run.exists():
        try:
            state = json.loads(last_run.read_text())
            print(f"**Last run**: checkpoint={state.get('last_checkpoint', 'none')}, git={state.get('last_git_sha', 'none')}")
        except (json.JSONDecodeError, OSError):
            pass

    # Token analytics from recent sessions
    if has_entire():
        _show_token_analytics()

    return 0


def _show_token_analytics(days=7, max_sessions=30):
    """Show token usage and hot areas from recent sessions."""
    sessions = get_entire_sessions()
    if not sessions:
        return

    cutoff = datetime.now().astimezone() - timedelta(days=days)
    total_tokens = 0
    total_cache_read = 0
    session_count = 0
    file_counter = Counter()

    for s in sessions[:max_sessions]:
        info = get_session_info(s["session_id"], filter_project=True)
        if not info:
            continue
        try:
            started = datetime.fromisoformat(info["started_at"])
            # Ensure both are tz-aware for comparison
            if started.tzinfo is None:
                started = started.astimezone()
            if started < cutoff:
                break  # sessions are ordered by recency
        except (ValueError, KeyError, TypeError):
            continue

        tokens = info.get("tokens", {})
        total_tokens += tokens.get("total", 0)
        total_cache_read += tokens.get("cache_read", 0)
        session_count += 1
        for f in info.get("files_touched", []):
            file_counter[f] += 1

    if session_count == 0:
        return

    cache_pct = round(total_cache_read / total_tokens * 100) if total_tokens > 0 else 0
    avg_tokens = total_tokens // session_count

    print(f"\n## Token Usage (last {days} days)\n")
    print(f"  Sessions: {session_count}")

    if total_tokens >= 1_000_000:
        print(f"  Total: {total_tokens / 1_000_000:.1f}M tokens")
    else:
        print(f"  Total: {total_tokens / 1_000:.1f}k tokens")

    print(f"  Cache hit rate: {cache_pct}%")

    if avg_tokens >= 1_000:
        print(f"  Avg session: {avg_tokens / 1_000:.1f}k tokens")
    else:
        print(f"  Avg session: {avg_tokens} tokens")

    # Hot areas: files touched across multiple sessions
    hot = [(f, c) for f, c in file_counter.most_common(8) if c >= 2]
    if hot:
        print(f"\n## Hot Areas (cross-session)\n")
        for filepath, count in hot:
            print(f"  {filepath} — {count} of {session_count} sessions")


def _is_default_harness(harness_path):
    """Check if the harness is the default one."""
    try:
        content = harness_path.read_text()
        return "Default reflect harness" in content
    except OSError:
        return False
