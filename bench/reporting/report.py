"""Report generation — markdown comparison report from benchmark summary."""

from ..config import BenchmarkConfig


def generate_report(summary: dict, config: BenchmarkConfig) -> str:
    labels = summary.get("labels", ["v3", "v4"])
    la, lb = labels[0], labels[1]

    lines = []
    lines.append(f"# Reflect Benchmark: {la} vs {lb}")
    lines.append(f"<!-- Run: {config.run_id} | Model: {config.maker_model} | Max rounds: {config.max_rounds} -->")
    lines.append("")

    a_stats = summary.get(la, {})
    b_stats = summary.get(lb, {})
    wins = summary.get("wins", {})

    # Summary table
    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | {la} | {lb} | Delta | Winner |")
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
        a_val = a_stats.get(key, 0)
        b_val = b_stats.get(key, 0)
        delta = b_val - a_val
        delta_str = f"+{delta:.2f}" if delta > 0 else f"{delta:.2f}"

        if higher_is_better:
            winner = lb if b_val > a_val else la if a_val > b_val else "tie"
        else:
            winner = lb if b_val < a_val else la if a_val < b_val else "tie"

        lines.append(f"| {label} | {a_val} | {b_val} | {delta_str} | **{winner}** |")

    lines.append("")
    lines.append(f"**Win/Loss/Tie**: {la}={wins.get(la, 0)} / {lb}={wins.get(lb, 0)} / tie={wins.get('tie', 0)}")
    lines.append("")

    # By task type
    a_types = summary.get(f"{la}_by_type", {})
    b_types = summary.get(f"{lb}_by_type", {})
    all_types = sorted(set(list(a_types.keys()) + list(b_types.keys())))

    if all_types:
        lines.append("## By Task Type")
        lines.append("")
        lines.append(f"| Type | {la} score | {lb} score | {la} rounds | {lb} rounds |")
        lines.append("|------|----------|----------|-----------|-----------|")

        for t in all_types:
            at = a_types.get(t, {})
            bt = b_types.get(t, {})
            lines.append(
                f"| {t} | {at.get('mean_score', '-')} | {bt.get('mean_score', '-')} "
                f"| {at.get('mean_rounds', '-')} | {bt.get('mean_rounds', '-')} |"
            )
        lines.append("")

    # Per-task detail
    per_task = summary.get("per_task", [])
    if per_task:
        lines.append("## Per-Task Detail")
        lines.append("")
        lines.append(f"| Task | {la} score | {lb} score | {la} rounds | {lb} rounds | {la} conv | {lb} conv | GT {la} | GT {lb} | Winner |")
        lines.append("|------|----------|----------|-----------|-----------|---------|---------|-------|-------|--------|")

        for t in per_task:
            lines.append(
                f"| {t['task_id']} "
                f"| {t.get(f'{la}_score', '-')} | {t.get(f'{lb}_score', '-')} "
                f"| {t.get(f'{la}_rounds', '-')} | {t.get(f'{lb}_rounds', '-')} "
                f"| {'Y' if t.get(f'{la}_converged') else 'N'} | {'Y' if t.get(f'{lb}_converged') else 'N'} "
                f"| {t.get(f'{la}_gt_coverage', '-')} | {t.get(f'{lb}_gt_coverage', '-')} "
                f"| **{t['winner']}** |"
            )
        lines.append("")

    # Context sizes
    if per_task:
        lines.append("## Context Sizes")
        lines.append("")
        lines.append(f"| Task | {la} chars | {lb} chars | Ratio |")
        lines.append("|------|----------|----------|-------|")
        for t in per_task:
            ac = t.get(f"{la}_context_chars", 0)
            bc = t.get(f"{lb}_context_chars", 0)
            ratio = f"{bc / ac:.1f}x" if ac > 0 else "n/a"
            lines.append(f"| {t['task_id']} | {ac:,} | {bc:,} | {ratio} |")
        lines.append("")

    # Cost breakdown
    if per_task:
        lines.append("## Cost Breakdown")
        lines.append("")
        a_total = sum(t.get(f"{la}_cost", 0) for t in per_task)
        b_total = sum(t.get(f"{lb}_cost", 0) for t in per_task)
        lines.append(f"- **{la} total**: ${a_total:.4f}")
        lines.append(f"- **{lb} total**: ${b_total:.4f}")
        lines.append(f"- **Combined**: ${a_total + b_total:.4f}")
        lines.append("")

    return "\n".join(lines)
