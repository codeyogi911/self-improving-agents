"""Maker agent — performs coding tasks with injected context via claude CLI."""

import json
import subprocess
from dataclasses import dataclass
from typing import Optional

from ..config import BenchmarkConfig, Task, TokenUsage

MAKER_SYSTEM_PROMPT = """\
You are an expert software engineer working on a project. You have been given \
project context from a memory system that captures session history, decisions, \
and architectural knowledge.

Use this context to inform your response. When you reference specific decisions, \
sessions, or history, cite the source (commit SHA, session ID, file path, or \
artifact name). If the context does not contain relevant information for the \
task, say so explicitly rather than fabricating history.

Be thorough but concise. Provide concrete, actionable answers."""


@dataclass
class MakerResponse:
    output: str
    usage: TokenUsage
    cost_usd: float = 0.0
    is_error: bool = False


class MakerAgent:
    def __init__(self, config: BenchmarkConfig):
        self.config = config

    def attempt(
        self,
        task: Task,
        context: str,
        feedback: Optional[str] = None,
        previous_attempt: Optional[str] = None,
    ) -> MakerResponse:
        """Make one attempt at the task via claude CLI."""
        user_parts = []

        user_parts.append("## Project Context\n")
        user_parts.append(context)
        user_parts.append("\n## Task\n")
        user_parts.append(task.prompt)

        if previous_attempt and feedback:
            user_parts.append("\n## Your Previous Attempt\n")
            user_parts.append(previous_attempt)
            user_parts.append("\n## Reviewer Feedback\n")
            user_parts.append(feedback)
            user_parts.append("\nPlease revise your response addressing the feedback above.")

        prompt = "\n".join(user_parts)
        return _call_claude(prompt, MAKER_SYSTEM_PROMPT, self.config.maker_model, self.config.max_maker_tokens)


def _call_claude(prompt: str, system_prompt: str, model: str, max_tokens: int, retries: int = 1) -> MakerResponse:
    """Call claude CLI in print mode, piping prompt via stdin. Retries on transient errors."""
    cmd = [
        "claude", "-p",
        "--model", model,
        "--output-format", "json",
        "--max-turns", "1",
        "--tools", "",
        "--system-prompt", system_prompt,
    ]

    for attempt in range(1 + retries):
        try:
            result = subprocess.run(
                cmd,
                input=prompt,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            if attempt < retries:
                print(f"      [maker] timeout, retrying ({attempt+1}/{retries})...")
                continue
            return MakerResponse(output="[ERROR: timeout after 300s]", usage=TokenUsage(), is_error=True)

        # Claude CLI returns JSON even on errors — always try to parse stdout
        try:
            data = json.loads(result.stdout)
        except (json.JSONDecodeError, TypeError):
            if attempt < retries:
                print(f"      [maker] JSON parse error, retrying ({attempt+1}/{retries})...")
                continue
            err = f"[ERROR: CLI rc={result.returncode}: {result.stderr[:200]} | stdout: {(result.stdout or '')[:200]}]"
            return MakerResponse(output=err, usage=TokenUsage(), is_error=True)

        # Check if the CLI reported an error in JSON
        if data.get("is_error"):
            if attempt < retries:
                print(f"      [maker] CLI error, retrying ({attempt+1}/{retries})...")
                continue
            return MakerResponse(
                output=f"[ERROR: {data.get('result', 'unknown')}]",
                usage=TokenUsage(),
                is_error=True,
            )

        # Success
        output = data.get("result", "")
        cost = data.get("total_cost_usd", 0.0)

        usage = TokenUsage()
        model_usage = data.get("modelUsage", {})
        for model_key, mu in model_usage.items():
            usage.input_tokens += mu.get("inputTokens", 0) + mu.get("cacheReadInputTokens", 0)
            usage.output_tokens += mu.get("outputTokens", 0)

        return MakerResponse(output=output, usage=usage, cost_usd=cost)

    # Should not reach here, but just in case
    return MakerResponse(output="[ERROR: all retries exhausted]", usage=TokenUsage(), is_error=True)
