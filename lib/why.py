"""reflect why — active query, dumps raw evidence to stdout."""

import sys
from .sources import (
    has_entire, has_git, get_entire_checkpoints,
    get_entire_transcript, get_notes, run
)
from pathlib import Path


def cmd_why(args):
    """Fetch raw evidence matching a query and dump to stdout."""
    query = " ".join(args.query)
    if not query:
        print("Usage: reflect why <file-or-topic>", file=sys.stderr)
        return 1

    found_anything = False

    # Search Entire sessions
    if has_entire():
        checkpoints = get_entire_checkpoints()
        query_lower = query.lower()
        matching = []
        for cp in checkpoints:
            # Match against intent and commit messages
            searchable = cp["intent"].lower()
            for c in cp["commits"]:
                searchable += " " + c["message"].lower()
            if query_lower in searchable:
                matching.append(cp)

        if matching:
            found_anything = True
            print(f"## Entire Sessions matching '{query}' ({len(matching)} found)\n")
            for cp in matching[:5]:
                print(f"### Session {cp['id'][:12]} ({cp['date']})")
                print(f"**Intent**: {cp['intent']}")
                if cp["commits"]:
                    for c in cp["commits"]:
                        print(f"**Commit**: `{c['sha']}` {c['message']}")
                print()

                # Get transcript for this session
                transcript = get_entire_transcript(cp["id"], max_lines=80)
                if transcript:
                    print("**Transcript (excerpt)**:")
                    print("```")
                    print(transcript)
                    print("```")
                    print()

    # Search git history
    if has_git():
        # Check if query looks like a file path
        if "/" in query or "." in query:
            git_output = run(["git", "log", "--oneline", "-20", "--format=%h %ad %s", "--date=short", "--", query])
        else:
            git_output = run(["git", "log", "--oneline", "-20", "--format=%h %ad %s", "--date=short", f"--grep={query}", "-i"])

        if git_output:
            found_anything = True
            print(f"## Git History matching '{query}'\n")
            for line in git_output.split("\n")[:15]:
                print(f"- {line}")
            print()

        # Also try git log for file paths
        if "/" in query or "." in query:
            blame = run(["git", "log", "--oneline", "-10", "--follow", "--", query])
            if blame:
                print(f"## File History: {query}\n")
                for line in blame.split("\n")[:10]:
                    print(f"- {line}")
                print()

    # Search notes
    notes_dir = Path(".reflect/notes")
    notes = get_notes(notes_dir)
    query_lower = query.lower()
    matching_notes = [n for n in notes if query_lower in n["content"].lower() or query_lower in n["name"].lower()]
    if matching_notes:
        found_anything = True
        print(f"## Notes matching '{query}'\n")
        for note in matching_notes:
            print(f"### {note['name']}")
            print(note["content"][:500])
            print()

    if not found_anything:
        print(f"No evidence found for '{query}'.")
        if not has_entire():
            print("Tip: Install Entire CLI for richer session evidence.")
        return 1

    return 0
