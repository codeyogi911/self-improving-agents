"""Metrics collector — accumulates per-task and aggregate benchmark metrics."""

from statistics import mean, median

from ..config import TaskResult


class MetricsCollector:
    def __init__(self, label_a: str = "v3", label_b: str = "v4"):
        self.label_a = label_a
        self.label_b = label_b
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
            # Extract task type from task_id prefix (e.g., "why-001" -> "why")
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
        """Compare label_a vs label_b for each task."""
        a_map = {r.task_id: r for r in self._by_version(self.label_a)}
        b_map = {r.task_id: r for r in self._by_version(self.label_b)}

        comparisons = []
        for task_id in a_map:
            a = a_map[task_id]
            b = b_map.get(task_id)
            if not b:
                continue

            a_score = a.final_score.weighted_score if a.final_score else 0
            b_score = b.final_score.weighted_score if b.final_score else 0

            if b_score > a_score:
                winner = self.label_b
            elif a_score > b_score:
                winner = self.label_a
            else:
                winner = "tie"

            comparisons.append({
                "task_id": task_id,
                f"{self.label_a}_rounds": a.num_rounds,
                f"{self.label_b}_rounds": b.num_rounds,
                f"{self.label_a}_score": round(a_score, 2),
                f"{self.label_b}_score": round(b_score, 2),
                f"{self.label_a}_converged": a.converged,
                f"{self.label_b}_converged": b.converged,
                f"{self.label_a}_gt_coverage": round(a.ground_truth_coverage, 2),
                f"{self.label_b}_gt_coverage": round(b.ground_truth_coverage, 2),
                f"{self.label_a}_context_chars": a.context_size_chars,
                f"{self.label_b}_context_chars": b.context_size_chars,
                f"{self.label_a}_cost": round(a.total_cost, 4),
                f"{self.label_b}_cost": round(b.total_cost, 4),
                "winner": winner,
            })
        return comparisons

    def summary(self) -> dict:
        comparisons = self._per_task_comparison()
        wins = {self.label_a: 0, self.label_b: 0, "tie": 0}
        for c in comparisons:
            wins[c["winner"]] += 1

        return {
            "labels": [self.label_a, self.label_b],
            self.label_a: self._version_stats(self.label_a),
            self.label_b: self._version_stats(self.label_b),
            f"{self.label_a}_by_type": self._by_task_type(self.label_a),
            f"{self.label_b}_by_type": self._by_task_type(self.label_b),
            "per_task": comparisons,
            "wins": wins,
        }
