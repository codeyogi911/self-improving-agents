"""CLI entry point for the benchmark harness."""

import argparse
import json
import sys
from pathlib import Path

from .config import BenchmarkConfig
from .tasks.registry import load_tasks


def cmd_run(args):
    """Run the v3-vs-v4 benchmark (external repo)."""
    config = BenchmarkConfig(
        target_repo=args.target_repo,
        v3_reflect_dir=args.v3_reflect,
        maker_model=args.model,
        checker_model=args.model,
        max_rounds=args.max_rounds,
        tasks_file=args.tasks,
        dry_run=args.dry_run,
    )

    # Load and validate tasks
    tasks = load_tasks(config.tasks_file)
    print(f"Loaded {len(tasks)} tasks from {config.tasks_file}")

    # Create results directory
    results_dir = Path("bench/results") / config.run_id
    results_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir = results_dir / "tasks"
    tasks_dir.mkdir(exist_ok=True)

    # Freeze config
    with open(results_dir / "run_config.json", "w") as f:
        json.dump({**config.to_dict(), "mode": "v3-vs-v4"}, f, indent=2)
    print(f"Results directory: {results_dir}")

    if config.dry_run:
        from .context.provider import V3ContextProvider, V4ContextProvider
        v3 = V3ContextProvider(config.v3_reflect_dir)
        v4 = V4ContextProvider(config.target_repo)
        print("\n--- Dry Run: Context Sizes ---")
        for task in tasks:
            v3_ctx = v3.get_context(task)
            v4_ctx = v4.get_context(task)
            print(f"  {task.id}: v3={len(v3_ctx)} chars, v4={len(v4_ctx)} chars")
        print("\nDry run complete. No API calls made.")
        return 0

    # Import here to avoid requiring anthropic for dry runs
    from .context.provider import V3ContextProvider, V4ContextProvider
    from .loop.runner import LoopRunner
    from .metrics.collector import MetricsCollector
    from .reporting.report import generate_report

    v3_provider = V3ContextProvider(config.v3_reflect_dir)
    v4_provider = V4ContextProvider(config.target_repo)
    runner = LoopRunner(config)
    collector = MetricsCollector(label_a="v3", label_b="v4")

    for task in tasks:
        print(f"\n{'='*60}")
        print(f"Task: {task.id} — {task.title}")
        print(f"{'='*60}")

        # Run with v3 context
        print(f"\n  [v3] Running...")
        v3_result = runner.run_task(task, v3_provider, "v3")
        collector.add(v3_result)
        with open(tasks_dir / f"{task.id}_v3.json", "w") as f:
            json.dump(v3_result.to_dict(), f, indent=2)
        v3_score = v3_result.final_score.weighted_score if v3_result.final_score else 0
        print(f"  [v3] {'Converged' if v3_result.converged else 'Did not converge'} in {v3_result.num_rounds} rounds (score: {v3_score:.1f})")

        # Run with v4 context
        print(f"\n  [v4] Running...")
        v4_result = runner.run_task(task, v4_provider, "v4")
        collector.add(v4_result)
        with open(tasks_dir / f"{task.id}_v4.json", "w") as f:
            json.dump(v4_result.to_dict(), f, indent=2)
        v4_score = v4_result.final_score.weighted_score if v4_result.final_score else 0
        print(f"  [v4] {'Converged' if v4_result.converged else 'Did not converge'} in {v4_result.num_rounds} rounds (score: {v4_score:.1f})")

    # Generate summary and report
    summary = collector.summary()
    with open(results_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    report = generate_report(summary, config)
    with open(results_dir / "report.md", "w") as f:
        f.write(report)

    print(f"\n{'='*60}")
    print(f"Benchmark complete. Results: {results_dir}")
    print(f"  summary.json — machine-readable metrics")
    print(f"  report.md    — human-readable comparison")
    return 0


def cmd_self_bench(args):
    """Run the self-benchmark: with-reflect vs without-reflect on this repo."""
    repo_path = args.repo or str(Path(__file__).parent.parent)
    max_rounds = 1 if args.quick else args.max_rounds

    config = BenchmarkConfig(
        target_repo=repo_path,
        v3_reflect_dir="",  # not used for self-bench
        maker_model=args.model,
        checker_model=args.model,
        max_rounds=max_rounds,
        tasks_file=args.tasks,
        dry_run=args.dry_run,
    )

    tasks = load_tasks(config.tasks_file)
    total_tasks = len(tasks)
    mode_str = "QUICK (1 round)" if args.quick else f"FULL (up to {max_rounds} rounds)"
    print(f"Self-benchmark: {total_tasks} tasks, {mode_str}, model={args.model}")

    label_a = "without-reflect"
    label_b = "with-reflect"

    results_dir = Path("bench/results") / f"self-{config.run_id}"
    results_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir = results_dir / "tasks"
    tasks_dir.mkdir(exist_ok=True)

    with open(results_dir / "run_config.json", "w") as f:
        json.dump({**config.to_dict(), "mode": "self-bench", "labels": [label_a, label_b], "quick": args.quick}, f, indent=2)
    print(f"Results: {results_dir}")

    from .context.provider import WithoutReflectProvider, WithReflectProvider

    without_provider = WithoutReflectProvider(repo_path)
    with_provider = WithReflectProvider(repo_path)

    if config.dry_run:
        print(f"\n--- Dry Run: Context Sizes ---")
        for task in tasks:
            without_ctx = without_provider.get_context(task)
            with_ctx = with_provider.get_context(task)
            print(f"  {task.id}: without={len(without_ctx):,} chars, with={len(with_ctx):,} chars")
        print(f"\nDry run complete. No API calls made.")
        return 0

    from .loop.runner import LoopRunner
    from .metrics.collector import MetricsCollector
    from .reporting.report import generate_report

    runner = LoopRunner(config)
    collector = MetricsCollector(label_a=label_a, label_b=label_b)

    # Running scoreboard
    a_scores = []
    b_scores = []

    for i, task in enumerate(tasks, 1):
        print(f"\n{'='*60}")
        print(f"[{i}/{total_tasks}] {task.id} — {task.title}")
        print(f"{'='*60}")

        # Run WITHOUT reflect
        print(f"\n  [{label_a}]")
        without_result = runner.run_task(task, without_provider, label_a)
        collector.add(without_result)
        with open(tasks_dir / f"{task.id}_without.json", "w") as f:
            json.dump(without_result.to_dict(), f, indent=2)

        ws_a = without_result.final_score.weighted_score if without_result.final_score else 0
        err_a = f" ({without_result.error_rounds} errors)" if without_result.error_rounds else ""
        print(
            f"  -> {'PASS' if without_result.converged else 'FAIL'} "
            f"score={ws_a:.1f} rounds={without_result.num_rounds}{err_a}"
        )
        a_scores.append(ws_a)

        # Run WITH reflect
        print(f"\n  [{label_b}]")
        with_result = runner.run_task(task, with_provider, label_b)
        collector.add(with_result)
        with open(tasks_dir / f"{task.id}_with.json", "w") as f:
            json.dump(with_result.to_dict(), f, indent=2)

        ws_b = with_result.final_score.weighted_score if with_result.final_score else 0
        err_b = f" ({with_result.error_rounds} errors)" if with_result.error_rounds else ""
        print(
            f"  -> {'PASS' if with_result.converged else 'FAIL'} "
            f"score={ws_b:.1f} rounds={with_result.num_rounds}{err_b}"
        )
        b_scores.append(ws_b)

        # Running scoreboard
        avg_a = sum(a_scores) / len(a_scores)
        avg_b = sum(b_scores) / len(b_scores)
        delta = avg_b - avg_a
        leader = label_b if delta > 0 else label_a if delta < 0 else "tied"
        print(f"\n  Scoreboard ({i}/{total_tasks}): without={avg_a:.2f} | with={avg_b:.2f} | delta={delta:+.2f} ({leader})")

    # Generate summary and report
    summary = collector.summary()
    with open(results_dir / "summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    report = generate_report(summary, config)
    with open(results_dir / "report.md", "w") as f:
        f.write(report)

    print(f"\n{'='*60}")
    print(f"BENCHMARK COMPLETE")
    print(f"{'='*60}")
    print(report)
    return 0


def cmd_report(args):
    """Regenerate report from existing results."""
    from .metrics.collector import MetricsCollector
    from .reporting.report import generate_report

    results_dir = Path("bench/results") / args.run_id
    if not results_dir.exists():
        print(f"Run not found: {results_dir}", file=sys.stderr)
        return 1

    with open(results_dir / "run_config.json") as f:
        config_dict = json.load(f)

    # Extract non-config keys before constructing BenchmarkConfig
    config_dict.pop("mode", None)
    config_dict.pop("labels", None)
    config_dict.pop("quick", None)

    config = BenchmarkConfig(**{k: v for k, v in config_dict.items() if k != "run_id"}, run_id=args.run_id)

    with open(results_dir / "summary.json") as f:
        summary = json.load(f)

    report = generate_report(summary, config)
    with open(results_dir / "report.md", "w") as f:
        f.write(report)
    print(report)
    return 0


def cmd_list_runs(args):
    """List available benchmark runs."""
    results_dir = Path("bench/results")
    if not results_dir.exists():
        print("No benchmark runs found.")
        return 0

    runs = sorted(results_dir.iterdir())
    if not runs:
        print("No benchmark runs found.")
        return 0

    print(f"{'Run ID':<30} {'Mode':<15} {'Tasks':<8} {'Has Report'}")
    print("-" * 70)
    for run_dir in runs:
        if not run_dir.is_dir():
            continue

        # Detect mode from config
        mode = "unknown"
        config_file = run_dir / "run_config.json"
        if config_file.exists():
            try:
                with open(config_file) as f:
                    cfg = json.load(f)
                mode = cfg.get("mode", "v3-vs-v4")
            except json.JSONDecodeError:
                pass

        tasks_dir = run_dir / "tasks"
        task_count = len(list(tasks_dir.glob("*.json"))) // 2 if tasks_dir.exists() else 0
        has_report = "yes" if (run_dir / "report.md").exists() else "no"
        print(f"{run_dir.name:<30} {mode:<15} {task_count:<8} {has_report}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="bench",
        description="Benchmark reflect context quality via maker-checker loop",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # run (v3-vs-v4, external repo)
    p_run = sub.add_parser("run", help="Run v3-vs-v4 benchmark on external repo")
    p_run.add_argument("--target-repo", required=True, help="Path to the target repository")
    p_run.add_argument("--v3-reflect", required=True, help="Path to v3 .reflect/ directory")
    p_run.add_argument("--tasks", default="bench/tasks/tasks.json", help="Path to tasks JSON file")
    p_run.add_argument("--model", default="claude-sonnet-4-6", help="Claude model for maker and checker")
    p_run.add_argument("--max-rounds", type=int, default=5, help="Max maker-checker iterations")
    p_run.add_argument("--dry-run", action="store_true", help="Validate config and show context sizes without API calls")
    p_run.set_defaults(func=cmd_run)

    # self-bench (with-reflect vs without-reflect, this repo)
    p_self = sub.add_parser("self-bench", help="Run with-reflect vs without-reflect benchmark on this repo")
    p_self.add_argument("--repo", default=None, help="Path to repo (default: this repo)")
    p_self.add_argument("--tasks", default="bench/tasks/self_tasks.json", help="Path to self-benchmark tasks JSON")
    p_self.add_argument("--model", default="claude-sonnet-4-6", help="Claude model for maker and checker")
    p_self.add_argument("--max-rounds", type=int, default=3, help="Max maker-checker iterations")
    p_self.add_argument("--quick", action="store_true", help="Single-shot mode: 1 round only (fast, cheap)")
    p_self.add_argument("--dry-run", action="store_true", help="Validate config and show context sizes without API calls")
    p_self.set_defaults(func=cmd_self_bench)

    # report
    p_report = sub.add_parser("report", help="Regenerate report from existing run")
    p_report.add_argument("--run-id", required=True, help="Run ID to regenerate report for")
    p_report.set_defaults(func=cmd_report)

    # list-runs
    p_list = sub.add_parser("list-runs", help="List available benchmark runs")
    p_list.set_defaults(func=cmd_list_runs)

    args = parser.parse_args()
    sys.exit(args.func(args) or 0)
