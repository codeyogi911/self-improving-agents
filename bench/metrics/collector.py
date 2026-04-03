"""Metrics collector — accumulates per-task and aggregate benchmark metrics."""

from statistics import mean, median

from ..config import TaskResult


class MetricsCollector:
    def __init__(self):
        self.results: list[TaskResult] = []

    def add(self, result: TaskResult):
        self.results.append(result)

    def _by_version(self, version: str) -> list[TaskResult]:
        return [r for r in self.results if r.version == version]

    def _version_stats(self, version: str) -> dict:
        results = self._by_version(version)
        if not results:
            return {}

        rounds = [r.num_rounds for r in results]
        scores = [r.final_score.weighted_score for r in results if r.final_score]
        gt_cov = [r.ground_truth_coverage for r in results]
        eg_scores = [r.final_score.evidence_grounding for r in results if r.final_score]
        costs = [r.total_cost for r in results]
        converged = sum(1 for r in results if r.converged)

        return {
            "num_tasks": len(results),
            "convergence_rate": round(converged / len(results), 2) if results else 0,
            "mean_rounds": round(mean(rounds), 2) if rounds else 0,
            "median_rounds": round(median(rounds), 2) if rounds else 0,
            "mean_weighted_score": round(mean(scores), 2) if scores else 0,
            "mean_evidence_grounding": round(mean(eg_scores), 2) if eg_scores else 0,
            "mean_ground_truth_coverage": round(mean(gt_cov), 2) if gt_cov else 0,
            "total_cost_usd": round(sum(costs), 4),
        }

    def _by_task_type(self, version: str) -> dict:
        results = self._by_version(version)
        by_type = {}
        for r in results:
            # Extract task type from task_id prefix (e.g., "why-001" -> "why_query")
            task_type = r.task_id.split("-")[0]
            by_type.setdefault(task_type, []).append(r)

        stats = {}
        for task_type, type_results in by_type.items():
            scores = [r.final_score.weighted_score for r in type_results if r.final_score]
            rounds = [r.num_rounds for r in type_results]
            stats[task_type] = {
                "mean_score": round(mean(scores), 2) if scores else 0,
                "mean_rounds": round(mean(rounds), 2) if rounds else 0,
                "count": len(type_results),
            }
        return stats

    def _per_task_comparison(self) -> list[dict]:
        """Compare v3 vs v4 for each task."""
        v3_map = {r.task_id: r for r in self._by_version("v3")}
        v4_map = {r.task_id: r for r in self._by_version("v4")}

        comparisons = []
        for task_id in v3_map:
            v3 = v3_map[task_id]
            v4 = v4_map.get(task_id)
            if not v4:
                continue

            v3_score = v3.final_score.weighted_score if v3.final_score else 0
            v4_score = v4.final_score.weighted_score if v4.final_score else 0

            if v4_score > v3_score:
                winner = "v4"
            elif v3_score > v4_score:
                winner = "v3"
            else:
                winner = "tie"

            comparisons.append({
                "task_id": task_id,
                "v3_rounds": v3.num_rounds,
                "v4_rounds": v4.num_rounds,
                "v3_score": round(v3_score, 2),
                "v4_score": round(v4_score, 2),
                "v3_converged": v3.converged,
                "v4_converged": v4.converged,
                "v3_gt_coverage": round(v3.ground_truth_coverage, 2),
                "v4_gt_coverage": round(v4.ground_truth_coverage, 2),
                "v3_context_chars": v3.context_size_chars,
                "v4_context_chars": v4.context_size_chars,
                "v3_cost": round(v3.total_cost, 4),
                "v4_cost": round(v4.total_cost, 4),
                "winner": winner,
            })
        return comparisons

    def summary(self) -> dict:
        comparisons = self._per_task_comparison()
        wins = {"v3": 0, "v4": 0, "tie": 0}
        for c in comparisons:
            wins[c["winner"]] += 1

        return {
            "v3": self._version_stats("v3"),
            "v4": self._version_stats("v4"),
            "v3_by_type": self._by_task_type("v3"),
            "v4_by_type": self._by_task_type("v4"),
            "per_task": comparisons,
            "wins": wins,
        }
