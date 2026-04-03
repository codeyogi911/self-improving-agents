"""Loop runner — orchestrates the maker-checker iteration cycle."""

from ..config import BenchmarkConfig, Round, Task, TaskResult
from ..context.provider import ContextProvider
from .checker import CheckerAgent
from .maker import MakerAgent


class LoopRunner:
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.maker = MakerAgent(config)
        self.checker = CheckerAgent(config)

    def run_task(
        self, task: Task, context_provider: ContextProvider, version: str
    ) -> TaskResult:
        """Run the full maker-checker loop for a single task."""
        context = context_provider.get_context(task)
        context_size = len(context)

        rounds = []
        feedback = None
        previous = None

        for round_num in range(1, self.config.max_rounds + 1):
            # Maker attempt
            maker_resp = self.maker.attempt(task, context, feedback, previous)
            print(f"    Round {round_num}: maker done ({maker_resp.usage.total} tokens, ${maker_resp.cost_usd:.4f})")

            # Checker evaluation
            checker_resp = self.checker.evaluate(task, maker_resp.output)
            ws = checker_resp.scores.weighted_score
            print(
                f"    Round {round_num}: checker verdict={checker_resp.verdict} "
                f"score={ws:.1f} "
                f"(C={checker_resp.scores.correctness} "
                f"Co={checker_resp.scores.completeness} "
                f"E={checker_resp.scores.evidence_grounding} "
                f"Q={checker_resp.scores.code_quality})"
            )

            rounds.append(Round(
                round_num=round_num,
                maker_output=maker_resp.output,
                checker_verdict=checker_resp.verdict,
                checker_scores=checker_resp.scores,
                checker_feedback=checker_resp.feedback,
                checker_rationale=checker_resp.rationale,
                ground_truth_hits=checker_resp.ground_truth_hits,
                ground_truth_misses=checker_resp.ground_truth_misses,
                maker_usage=maker_resp.usage,
                checker_usage=checker_resp.usage,
                maker_cost_usd=maker_resp.cost_usd,
                checker_cost_usd=checker_resp.cost_usd,
            ))

            if checker_resp.verdict == "accept":
                break

            feedback = checker_resp.feedback
            previous = maker_resp.output

        return TaskResult(
            task_id=task.id,
            version=version,
            rounds=rounds,
            context_size_chars=context_size,
        )
