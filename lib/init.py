"""reflect init — create .reflect/ with default harness."""

import shutil
import sys
from pathlib import Path


def cmd_init(args):
    """Initialize .reflect/ directory with default harness and config."""
    reflect_dir = Path(".reflect")

    if reflect_dir.exists() and (reflect_dir / "harness").exists():
        print(".reflect/ already initialized.", file=sys.stderr)
        return 0

    reflect_dir.mkdir(exist_ok=True)
    (reflect_dir / "notes").mkdir(exist_ok=True)

    # Copy default harness
    harness_src = Path(__file__).parent.parent / "harness" / "default.py"
    harness_dst = reflect_dir / "harness"
    if harness_src.exists():
        shutil.copy2(harness_src, harness_dst)
        harness_dst.chmod(0o755)
    else:
        print(f"Warning: default harness not found at {harness_src}", file=sys.stderr)

    # Write default config
    config = reflect_dir / "config.yaml"
    if not config.exists():
        config.write_text(
            "# reflect configuration\n"
            "max_lines: 150\n"
            "session_start: auto\n"
        )

    # Auto-wire @.reflect/context.md into CLAUDE.md if present
    claude_md = Path("CLAUDE.md")
    context_ref = "@.reflect/context.md"
    if claude_md.exists():
        claude_content = claude_md.read_text()
        if context_ref not in claude_content:
            with open(claude_md, "a") as f:
                f.write(f"\n{context_ref}\n")
            print("Added @.reflect/context.md reference to CLAUDE.md")
    else:
        claude_md.write_text(f"# CLAUDE.md\n\n{context_ref}\n")
        print("Created CLAUDE.md with @.reflect/context.md reference")

    # Suggest .gitignore
    gitignore = Path(".gitignore")
    if gitignore.exists():
        content = gitignore.read_text()
        if ".reflect/context.md" not in content:
            print("Tip: Add .reflect/context.md and .reflect/.last_run to .gitignore")
    else:
        print("Tip: Add .reflect/context.md and .reflect/.last_run to .gitignore")

    print("Initialized .reflect/ with default harness.")
    print("Run `reflect context` to generate your first context briefing.")
    return 0
