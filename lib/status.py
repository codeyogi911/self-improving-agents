"""reflect status — show available evidence sources."""

import json
import sys
from pathlib import Path
from .sources import has_entire, has_git, run


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

    # Notes
    notes_dir = reflect_dir / "notes"
    if notes_dir.exists():
        note_count = len(list(notes_dir.glob("*.md")))
        print(f"- **Notes**: {note_count} files")
    else:
        print("- **Notes**: none")

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

    return 0


def _is_default_harness(harness_path):
    """Check if the harness is the default one."""
    try:
        content = harness_path.read_text()
        return "Default reflect harness" in content
    except OSError:
        return False
