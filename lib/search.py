"""reflect search — grep across all evidence sources."""

import sys
from .sources import has_entire, has_git, get_entire_checkpoints, run


def _search_tokens(query, phrase):
    """Return non-empty search tokens. Default: split on whitespace, OR-match each token."""
    raw = query.strip()
    if not raw:
        return []
    if phrase:
        return [raw]
    tokens = []
    for t in raw.split():
        if t:
            tokens.append(t)
    seen = set()
    out = []
    for t in tokens:
        k = t.lower()
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out


def cmd_search(args):
    """Grep across all evidence sources for a query."""
    query = " ".join(args.query)
    if not query.strip():
        print("Usage: reflect search <query>", file=sys.stderr)
        return 1

    phrase = getattr(args, "phrase", False)
    tokens = _search_tokens(query, phrase)
    if not tokens:
        print("No search terms after parsing query.", file=sys.stderr)
        return 1

    found = 0

    # Search Entire intents
    if has_entire():
        checkpoints = get_entire_checkpoints()
        matches = []
        for cp in checkpoints:
            searchable = cp["intent"]
            for c in cp["commits"]:
                searchable += " " + c["message"]
            hay = searchable.lower()
            if any(tok.lower() in hay for tok in tokens):
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

    # Search git log (multiple --grep = OR; -F = literal strings)
    if has_git():
        cmd = ["git", "log", "--oneline", "-20", "-i", "-F"]
        for tok in tokens:
            cmd.extend(["--grep", tok])
        git_output = run(cmd)
        if git_output:
            lines = git_output.split("\n")
            print(f"## Git Commits ({len(lines)} matches)\n")
            for line in lines[:10]:
                print(f"- {line}")
            print()
            found += len(lines)

    if found == 0:
        if len(tokens) == 1:
            print(f"No matches for {tokens[0]!r}.")
        else:
            print(
                f"No matches (OR across {len(tokens)} terms: "
                f"{', '.join(repr(t) for t in tokens)})."
            )
        return 0

    print(f"---\n{found} total matches across all sources.")
    return 0
