"""reflect search — grep across all evidence sources."""

import sys
from .sources import has_entire, has_git, get_entire_checkpoints, run


def cmd_search(args):
    """Grep across all evidence sources for a query."""
    query = " ".join(args.query)
    if not query:
        print("Usage: reflect search <query>", file=sys.stderr)
        return 1

    found = 0
    query_lower = query.lower()

    # Search Entire intents
    if has_entire():
        checkpoints = get_entire_checkpoints()
        matches = []
        for cp in checkpoints:
            searchable = cp["intent"]
            for c in cp["commits"]:
                searchable += " " + c["message"]
            if query_lower in searchable.lower():
                matches.append(cp)

        if matches:
            print(f"## Entire Sessions ({len(matches)} matches)\n")
            for cp in matches[:10]:
                commits_str = ""
                if cp["commits"]:
                    commits_str = f" → {cp['commits'][0]['message'][:60]}"
                print(f"- [{cp['id'][:12]}] ({cp['date']}) {cp['intent'][:100]}{commits_str}")
            print()
            found += len(matches)

    # Search git log
    if has_git():
        git_output = run(["git", "log", "--oneline", "-20", f"--grep={query}", "-i"])
        if git_output:
            lines = git_output.split("\n")
            print(f"## Git Commits ({len(lines)} matches)\n")
            for line in lines[:10]:
                print(f"- {line}")
            print()
            found += len(lines)

    if found == 0:
        print(f"No matches for '{query}'.")
        return 1

    print(f"---\n{found} total matches across all sources.")
    return 0
