"""reflect note — add a manual note to .reflect/notes/."""

import re
import sys
from pathlib import Path


def cmd_note(args):
    """Add a manual note to .reflect/notes/."""
    title = " ".join(args.title)
    if not title:
        print("Usage: reflect note <title>", file=sys.stderr)
        return 1

    reflect_dir = Path(".reflect")
    notes_dir = reflect_dir / "notes"

    if not reflect_dir.exists():
        print("No .reflect/ directory. Run `reflect init` first.", file=sys.stderr)
        return 1

    notes_dir.mkdir(exist_ok=True)

    # Generate slug from title
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    note_path = notes_dir / f"{slug}.md"

    # Read content from stdin if available, otherwise create empty note
    if not sys.stdin.isatty():
        content = sys.stdin.read().strip()
    else:
        content = f"# {title}\n\n"

    if note_path.exists():
        # Append to existing note
        existing = note_path.read_text()
        note_path.write_text(existing.rstrip() + "\n\n" + content + "\n")
        print(f"Appended to {note_path}")
    else:
        note_path.write_text(content + "\n")
        print(f"Created {note_path}")

    return 0
