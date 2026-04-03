"""Report generation — markdown comparison report from benchmark summary."""

from ..config import BenchmarkConfig


def generate_report(summary: dict, config: BenchmarkConfig) -> str:
    lines = []
    lines.append(f"# Reflect Benchmark: v3 vs v4")
    lines.append(f"<!-- Run: {config.run_id} | Model: {config.maker_model} | Max rounds: {config.max_rounds} -->")
    lines.append("")

    v3 = summary.get("v3", {})
    v4 = summary.get("v4", {})
    wins = summary.get("wins", {})

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | v3 | v4 | Delta | Winner |")
    lines.append("|--------|-----|-----|-------|--------|")

    metrics = [
        ("Convergence rate", "convergence_rate", True),
        ("Mean rounds", "mean_rounds", False),  # lower is better
        ("Mean weighted score", "mean_weighted_score", True),
        ("Mean evidence grounding", "mean_evidence_grounding", True),
        ("Mean GT coverage", "mean_ground_truth_coverage", True),
        ("Total cost (USD)", "total_cost_usd", False),
    ]

    for label, key, higher_is_better in metrics:
        v3_val = v3.get(key, 0)
        v4_val = v4.get(key, 0)
        delta = v4_val - v3_val
        delta_str = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"

        if higher_is_better:
            winner = "v4" if v4_val > v3_val else "v3" if v3_val > v4_val else "tie"
        else:
            winner = "v4" if v4_val < v3_val else "v3" if v3_val < v4_val else "tie"

        lines.append(f"| {label} | {v3_val} | {v4_val} | {delta_str} | **{winner}** |")

    lines.append("")
    lines.append(f"**Win/Loss/Tie**: v3={wins.get('v3', 0)} / v4={wins.get('v4', 0)} / tie={wins.get('tie', 0)}")
    lines.append("")

    # By task type
    v3_types = summary.get("v3_by_type", {})
    v4_types = summary.get("v4_by_type", {})
    all_types = sorted(set(list(v3_types.keys()) + list(v4_types.keys())))

    if all_types:
        lines.append("## By Task Type")
        lines.append("")
        lines.append("| Type | v3 score | v4 score | v3 rounds | v4 rounds |")
        lines.append("|------|----------|----------|-----------|-----------|")

        for t in all_types:
            v3t = v3_types.get(t, {})
            v4t = v4_types.get(t, {})
            lines.append(
                f"| {t} | {v3t.get('mean_score', '-')} | {v4t.get('mean_score', '-')} "
                f"| {v3t.get('mean_rounds', '-')} | {v4t.get('mean_rounds', '-')} |"
            )
        lines.append("")

    # Per-task detail
    per_task = summary.get("per_task", [])
    if per_task:
        lines.append("## Per-Task Detail")
        lines.append("")
        lines.append("| Task | v3 score | v4 score | v3 rounds | v4 rounds | v3 conv | v4 conv | GT v3 | GT v4 | Winner |")
        lines.append("|------|----------|----------|-----------|-----------|---------|---------|-------|-------|--------|")

        for t in per_task:
            lines.append(
                f"| {t['task_id']} "
                f"| {t['v3_score']} | {t['v4_score']} "
                f"| {t['v3_rounds']} | {t['v4_rounds']} "
                f"| {'Y' if t['v3_converged'] else 'N'} | {'Y' if t['v4_converged'] else 'N'} "
                f"| {t['v3_gt_coverage']} | {t['v4_gt_coverage']} "
                f"| **{t['winner']}** |"
            )
        lines.append("")

    # Context sizes
    if per_task:
        lines.append("## Context Sizes")
        lines.append("")
        lines.append("| Task | v3 chars | v4 chars | Ratio |")
        lines.append("|------|----------|----------|-------|")
        for t in per_task:
            v3c = t["v3_context_chars"]
            v4c = t["v4_context_chars"]
            ratio = f"{v4c / v3c:.1f}x" if v3c > 0 else "n/a"
            lines.append(f"| {t['task_id']} | {v3c:,} | {v4c:,} | {ratio} |")
        lines.append("")

    # Cost breakdown
    if per_task:
        lines.append("## Cost Breakdown")
        lines.append("")
        v3_total = sum(t["v3_cost"] for t in per_task)
        v4_total = sum(t["v4_cost"] for t in per_task)
        lines.append(f"- **v3 total**: ${v3_total:.4f}")
        lines.append(f"- **v4 total**: ${v4_total:.4f}")
        lines.append(f"- **Combined**: ${v3_total + v4_total:.4f}")
        lines.append("")

    return "\n".join(lines)
