"""Context providers — inject context for the maker LLM.

Supports two benchmark modes:
  1. v3 vs v4: compare old structured artifacts against new harness (external repo)
  2. with-reflect vs without-reflect: measure whether reflect helps at all (self-bench)
"""

import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from ..config import Task


class ContextProvider(ABC):
    @abstractmethod
    def get_context(self, task: Task) -> str:
        """Return context string to prepend to the maker's prompt."""


class V3ContextProvider(ContextProvider):
    """Reads pre-computed v3 .reflect/ artifacts (sessions, decisions, insights)."""

    def __init__(self, reflect_dir: str):
        self.reflect_dir = Path(reflect_dir)

    def get_context(self, task: Task) -> str:
        parts = []

        # 1. Read compiled context.md
        context_md = self.reflect_dir / "context.md"
        if context_md.exists():
            parts.append("## Compiled Context Briefing\n")
            parts.append(context_md.read_text())

        # 2. Read matching sessions
        sessions_dir = self.reflect_dir / "sessions"
        if sessions_dir.exists():
            matching = self._find_matching_files(sessions_dir, task)
            if matching:
                parts.append("\n## Relevant Sessions\n")
                for f in matching[:5]:
                    parts.append(f"### {f.stem}\n")
                    parts.append(f.read_text()[:2000])
                    parts.append("")

        # 3. Read matching decisions
        decisions_dir = self.reflect_dir / "decisions"
        if decisions_dir.exists():
            matching = self._find_matching_files(decisions_dir, task)
            if matching:
                parts.append("\n## Relevant Decisions\n")
                for f in matching[:5]:
                    parts.append(f"### {f.stem}\n")
                    parts.append(f.read_text()[:2000])
                    parts.append("")

        # 4. Read matching insights
        insights_dir = self.reflect_dir / "insights"
        if insights_dir.exists():
            matching = self._find_matching_files(insights_dir, task)
            if matching:
                parts.append("\n## Relevant Insights\n")
                for f in matching[:3]:
                    parts.append(f"### {f.stem}\n")
                    parts.append(f.read_text()[:1500])
                    parts.append("")

        if not parts:
            return "(No v3 context available)"

        return "\n".join(parts)

    def _find_matching_files(self, directory: Path, task: Task) -> list[Path]:
        """Find files in a directory whose content matches task tags/files/title."""
        search_terms = set()
        search_terms.update(t.lower() for t in task.tags)
        search_terms.update(f.split("/")[-1].lower() for f in task.relevant_files)
        # Add significant words from the title
        for word in task.title.lower().split():
            if len(word) > 3:
                search_terms.add(word)

        matching = []
        for f in sorted(directory.glob("*.md")):
            content = f.read_text().lower()
            score = sum(1 for term in search_terms if term in content)
            if score > 0:
                matching.append((score, f))

        # Sort by relevance score descending
        matching.sort(key=lambda x: x[0], reverse=True)
        return [f for _, f in matching]


class V4ContextProvider(ContextProvider):
    """Invokes the v4 reflect CLI to get context on demand."""

    def __init__(self, target_repo: str, reflect_bin: str = "python3"):
        self.target_repo = target_repo
        self.reflect_bin = reflect_bin
        # Find the reflect script relative to this repo
        self.reflect_script = str(Path(__file__).parent.parent.parent / "reflect")

    def get_context(self, task: Task) -> str:
        parts = []

        # 1. Run reflect context
        context_output = self._run_reflect(["context"])
        if context_output:
            # Read the generated context.md
            context_md = Path(self.target_repo) / ".reflect" / "context.md"
            if context_md.exists():
                parts.append("## Context Briefing (v4 harness)\n")
                parts.append(context_md.read_text())

        # 2. For each relevant file, run reflect why
        for filepath in task.relevant_files[:3]:
            why_output = self._run_reflect(["why", filepath])
            if why_output:
                parts.append(f"\n## Evidence for: {filepath}\n")
                parts.append(why_output[:3000])

        # 3. Search by tags/title keywords
        search_terms = list(task.tags[:2])
        if not search_terms:
            # Extract a keyword from the title
            words = [w for w in task.title.lower().split() if len(w) > 4]
            search_terms = words[:1]

        for term in search_terms:
            search_output = self._run_reflect(["search", term])
            if search_output:
                parts.append(f"\n## Search: '{term}'\n")
                parts.append(search_output[:2000])

        if not parts:
            return "(No v4 context available)"

        return "\n".join(parts)

    def _run_reflect(self, args: list[str]) -> str:
        """Run the reflect CLI in the target repo."""
        cmd = [self.reflect_bin, self.reflect_script] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                cwd=self.target_repo,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""


# ---------------------------------------------------------------------------
# Self-benchmark providers: with-reflect vs without-reflect
# ---------------------------------------------------------------------------

class WithoutReflectProvider(ContextProvider):
    """Baseline — only CLAUDE.md and code structure, no reflect context.

    Simulates a Claude Code session where reflect is NOT installed.
    The maker gets the project's CLAUDE.md (minus the @.reflect/context.md
    reference) plus a basic directory listing. No git log — that would
    give the baseline an unfair advantage on history-dependent tasks.
    """

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)

    def get_context(self, task: Task) -> str:
        parts = []

        # 1. CLAUDE.md (strip the @.reflect/context.md line)
        claude_md = self.repo_path / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text()
            lines = [
                ln for ln in content.splitlines()
                if "@.reflect/context.md" not in ln
            ]
            parts.append("## Project Instructions (CLAUDE.md)\n")
            parts.append("\n".join(lines))

        # 2. Directory tree (first 2 levels, like a new dev would see)
        tree = self._get_tree()
        if tree:
            parts.append("\n## Repository Structure\n")
            parts.append(tree)

        if not parts:
            return "(No project context available)"

        return "\n".join(parts)

    def _get_tree(self) -> str:
        try:
            result = subprocess.run(
                ["find", ".", "-maxdepth", "2", "-not", "-path", "./.git/*",
                 "-not", "-path", "./.git", "-not", "-name", "__pycache__",
                 "-not", "-path", "./__pycache__/*"],
                capture_output=True, text=True, timeout=5,
                cwd=self.repo_path,
            )
            return result.stdout.strip()[:2000] if result.returncode == 0 else ""
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""


class WithReflectProvider(ContextProvider):
    """Full reflect context — context.md + targeted why/search queries.

    Simulates a Claude Code session where reflect IS installed and active.
    """

    def __init__(self, repo_path: str, reflect_bin: str = "python3"):
        self.repo_path = Path(repo_path)
        self.reflect_bin = reflect_bin
        self.reflect_script = str(Path(__file__).parent.parent.parent / "reflect")

    def get_context(self, task: Task) -> str:
        parts = []

        # 1. CLAUDE.md (strip @.reflect/context.md — we inline it below)
        claude_md = self.repo_path / "CLAUDE.md"
        if claude_md.exists():
            content = claude_md.read_text()
            lines = [
                ln for ln in content.splitlines()
                if "@.reflect/context.md" not in ln
            ]
            parts.append("## Project Instructions (CLAUDE.md)\n")
            parts.append("\n".join(lines))

        # 2. Run reflect context → read the generated context.md
        self._run_reflect(["context"])
        context_md = self.repo_path / ".reflect" / "context.md"
        if context_md.exists():
            content = context_md.read_text()
            if content.strip():
                parts.append("\n## Reflect Context Briefing\n")
                parts.append(content)

        # 3. reflect why for relevant files
        for filepath in task.relevant_files[:3]:
            why_output = self._run_reflect(["why", filepath])
            if why_output:
                parts.append(f"\n## Reflect Evidence: {filepath}\n")
                parts.append(why_output[:3000])

        # 4. reflect search by task tags
        search_terms = list(task.tags[:2])
        if not search_terms:
            words = [w for w in task.title.lower().split() if len(w) > 4]
            search_terms = words[:1]

        for term in search_terms:
            search_output = self._run_reflect(["search", term])
            if search_output:
                parts.append(f"\n## Reflect Search: '{term}'\n")
                parts.append(search_output[:2000])

        if not parts:
            return "(No context available)"

        return "\n".join(parts)

    def _run_reflect(self, args: list[str]) -> str:
        cmd = [self.reflect_bin, self.reflect_script] + args
        try:
            result = subprocess.run(
                cmd,
                capture_output=True, text=True, timeout=30,
                cwd=str(self.repo_path),
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return ""
