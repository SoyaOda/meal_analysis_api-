#!/usr/bin/env python3
"""Run repeated PDCA evals and aggregate candidate stability metrics."""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_AGG_ROOT = (
    PROJECT_ROOT / "apps" / "freeform_usda_meal_analysis_api" / "evals" / "repeat_runs"
)
RUN_PATH_PATTERN = re.compile(r"^Saved run:\s*(.+)$", re.MULTILINE)


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_saved_run_dir(stdout_text: str) -> Optional[Path]:
    match = RUN_PATH_PATTERN.search(stdout_text)
    if not match:
        return None
    return Path(match.group(1).strip())


def add_optional_flag(cmd: List[str], name: str, value: Optional[bool]) -> None:
    if value is None:
        return
    cmd.append(f"--{name}" if value else f"--no-{name}")


def run_single_eval(
    *,
    config: Path,
    api_url: str,
    limit: int,
    start_index: int,
    end_index: Optional[int],
    image_index_file: Optional[Path],
    required_image_count: int,
    timeout_sec: int,
    max_retries: int,
    retry_backoff_sec: float,
    concurrency: Optional[int],
    use_vlm_cache: Optional[bool],
    allow_missing_images: Optional[bool],
    allow_prompt_leakage: Optional[bool],
    baseline_file: Optional[Path],
    output_root: Optional[Path],
) -> Path:
    cmd = [
        sys.executable,
        "-m",
        "apps.freeform_usda_meal_analysis_api.scripts.run_pdca_batch_eval",
        "--config",
        str(config),
        "--api-url",
        api_url,
        "--limit",
        str(limit),
        "--start-index",
        str(start_index),
        "--required-image-count",
        str(required_image_count),
        "--timeout-sec",
        str(timeout_sec),
        "--max-retries",
        str(max_retries),
        "--retry-backoff-sec",
        str(retry_backoff_sec),
    ]

    if end_index is not None:
        cmd.extend(["--end-index", str(end_index)])
    if image_index_file is not None:
        cmd.extend(["--image-index-file", str(image_index_file)])
    if concurrency is not None:
        cmd.extend(["--concurrency", str(concurrency)])
    if baseline_file is not None:
        cmd.extend(["--baseline-file", str(baseline_file)])
    if output_root is not None:
        cmd.extend(["--output-root", str(output_root)])

    add_optional_flag(cmd, "use-vlm-cache", use_vlm_cache)
    add_optional_flag(cmd, "allow-missing-images", allow_missing_images)
    add_optional_flag(cmd, "allow-prompt-leakage", allow_prompt_leakage)

    completed = subprocess.run(
        cmd,
        cwd=str(PROJECT_ROOT),
        text=True,
        capture_output=True,
        check=False,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            "run_pdca_batch_eval failed:\n"
            f"cmd={' '.join(cmd)}\n"
            f"stdout:\n{completed.stdout}\n"
            f"stderr:\n{completed.stderr}"
        )

    run_dir = parse_saved_run_dir(completed.stdout)
    if run_dir is None:
        raise RuntimeError(
            "Could not parse run directory from run_pdca_batch_eval output.\n"
            f"stdout:\n{completed.stdout}"
        )

    return run_dir


def safe_mean(values: List[float]) -> Optional[float]:
    if not values:
        return None
    return float(statistics.mean(values))


def safe_stdev(values: List[float]) -> float:
    if len(values) <= 1:
        return 0.0
    return float(statistics.stdev(values))


def stability_verdict(
    row: Dict[str, Any],
    *,
    baseline_mae: Optional[float],
    max_mae_std: float,
    max_high30_std: float,
) -> Dict[str, Any]:
    """Code-enforced stability gate over repeated runs.

    A candidate is 'stable' only when every run fully succeeded/covered, the
    run-to-run std of MAE and high30 are within bounds, and (when a baseline is
    given) the mean MAE beats the baseline. Previously these thresholds were
    applied only by hand in lesson notes.
    """
    reasons: List[str] = []
    if row["success_run_count"] < row["run_count"]:
        reasons.append(
            f"only {row['success_run_count']}/{row['run_count']} runs fully succeeded/covered"
        )
    if row["mae_std"] > max_mae_std:
        reasons.append(f"mae_std {row['mae_std']} > {max_mae_std}")
    if row["high30_std"] > max_high30_std:
        reasons.append(f"high30_std {row['high30_std']} > {max_high30_std}")
    if baseline_mae is not None and row["mae_mean"] > baseline_mae:
        reasons.append(
            f"mae_mean {row['mae_mean']} does not beat baseline {round(baseline_mae, 4)}"
        )
    if reasons:
        return {"decision": "hold", "reasons": reasons}
    note = "mae_std/high30_std within bounds"
    if baseline_mae is not None:
        note += " and mae_mean beats baseline"
    return {"decision": "stable", "reasons": [note]}


def build_markdown_summary(path: Path, payload: Dict[str, Any]) -> None:
    lines: List[str] = []
    lines.append("# PDCA Repeated Eval Summary")
    lines.append("")
    lines.append(f"- generated_at: {payload['generated_at']}")
    lines.append(f"- config_path: {payload['config_path']}")
    lines.append(f"- api_url: {payload['api_url']}")
    lines.append(f"- repeats: {payload['repeats']}")
    lines.append(f"- run_dirs_count: {len(payload['run_dirs'])}")
    lines.append("")
    lines.append(
        "| candidate | runs | mae_mean | mae_std | high30_mean | high30_std | all_success_runs | stability |"
    )
    lines.append("|---|---:|---:|---:|---:|---:|---:|---|")

    for row in payload["candidates"]:
        stability = (row.get("stability") or {}).get("decision", "n/a")
        lines.append(
            "| {name} | {runs} | {mae_mean:.4f} | {mae_std:.4f} | {high_mean:.4f} | {high_std:.4f} | {ok}/{runs} | {stability} |".format(
                name=row["name"],
                runs=row["run_count"],
                mae_mean=row["mae_mean"],
                mae_std=row["mae_std"],
                high_mean=row["high30_mean"],
                high_std=row["high30_std"],
                ok=row["success_run_count"],
                stability=stability,
            )
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repeated PDCA evals")
    parser.add_argument("--config", required=True, help="Path to eval config JSON")
    parser.add_argument("--api-url", default="http://localhost:8006")
    parser.add_argument("--repeats", type=int, default=2)
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--start-index", type=int, default=1)
    parser.add_argument("--end-index", type=int, default=None)
    parser.add_argument("--image-index-file", default=None)
    parser.add_argument("--required-image-count", type=int, default=50)
    parser.add_argument("--timeout-sec", type=int, default=300)
    parser.add_argument("--max-retries", type=int, default=2)
    parser.add_argument("--retry-backoff-sec", type=float, default=1.5)
    parser.add_argument("--concurrency", type=int, default=None)
    parser.add_argument(
        "--use-vlm-cache",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--allow-missing-images",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument(
        "--allow-prompt-leakage",
        action=argparse.BooleanOptionalAction,
        default=None,
    )
    parser.add_argument("--baseline-file", default=None)
    parser.add_argument(
        "--max-mae-std",
        type=float,
        default=1.0,
        help="Max allowed run-to-run mae_std for a 'stable' verdict",
    )
    parser.add_argument(
        "--max-high30-std",
        type=float,
        default=2.0,
        help="Max allowed run-to-run high30_std for a 'stable' verdict",
    )
    parser.add_argument(
        "--inner-output-root",
        default=None,
        help="Optional output root passed to each inner run_pdca_batch_eval",
    )
    parser.add_argument("--output-root", default=str(DEFAULT_AGG_ROOT))
    args = parser.parse_args()

    if args.repeats < 1:
        raise ValueError("repeats must be >= 1")

    config_path = resolve_path(args.config)
    image_index_file = (
        resolve_path(args.image_index_file) if args.image_index_file else None
    )
    baseline_file = resolve_path(args.baseline_file) if args.baseline_file else None
    inner_output_root = (
        resolve_path(args.inner_output_root) if args.inner_output_root else None
    )

    run_dirs: List[Path] = []
    run_payloads: List[Dict[str, Any]] = []

    for i in range(args.repeats):
        print(f"[repeat {i + 1}/{args.repeats}] starting...")
        run_dir = run_single_eval(
            config=config_path,
            api_url=args.api_url,
            limit=args.limit,
            start_index=args.start_index,
            end_index=args.end_index,
            image_index_file=image_index_file,
            required_image_count=args.required_image_count,
            timeout_sec=args.timeout_sec,
            max_retries=args.max_retries,
            retry_backoff_sec=args.retry_backoff_sec,
            concurrency=args.concurrency,
            use_vlm_cache=args.use_vlm_cache,
            allow_missing_images=args.allow_missing_images,
            allow_prompt_leakage=args.allow_prompt_leakage,
            baseline_file=baseline_file,
            output_root=inner_output_root,
        )
        run_dirs.append(run_dir)
        run_payloads.append(load_json(run_dir / "raw_results.json"))
        print(f"[repeat {i + 1}/{args.repeats}] done: {run_dir}")

    candidate_runs: Dict[str, Dict[str, Any]] = {}
    for payload in run_payloads:
        for result in payload.get("results", []):
            name = result.get("summary", {}).get("name")
            if not name:
                continue
            entry = candidate_runs.setdefault(
                name,
                {
                    "name": name,
                    "candidate": result.get("candidate", {}),
                    "summaries": [],
                },
            )
            entry["summaries"].append(result.get("summary", {}))

    candidate_rows: List[Dict[str, Any]] = []
    for name, entry in candidate_runs.items():
        summaries = entry["summaries"]
        maes = [float(s.get("calorie_mae_percent", 0.0)) for s in summaries]
        high30 = [float(s.get("high_error_rate_30_percent", 0.0)) for s in summaries]
        latencies = [float(s.get("avg_latency_sec", 0.0)) for s in summaries]
        costs = [
            float(s.get("avg_cost_usd"))
            for s in summaries
            if s.get("avg_cost_usd") is not None
        ]
        success_runs = [
            s
            for s in summaries
            if bool(s.get("all_success", False))
            and bool(s.get("coverage_complete", False))
        ]
        row = {
            "name": name,
            "candidate": entry.get("candidate", {}),
            "run_count": len(summaries),
            "success_run_count": len(success_runs),
            "mae_mean": round(safe_mean(maes) or 0.0, 4),
            "mae_std": round(safe_stdev(maes), 4),
            "high30_mean": round(safe_mean(high30) or 0.0, 4),
            "high30_std": round(safe_stdev(high30), 4),
            "latency_mean": round(safe_mean(latencies) or 0.0, 4),
            "cost_mean": round(safe_mean(costs) or 0.0, 6) if costs else None,
            "raw_summaries": summaries,
        }
        candidate_rows.append(row)

    candidate_rows.sort(key=lambda r: (r["mae_mean"], r["high30_mean"]))

    baseline_mae: Optional[float] = None
    if baseline_file is not None and baseline_file.exists():
        baseline_summary = load_json(baseline_file).get("summary") or {}
        baseline_mae_value = baseline_summary.get("calorie_mae_percent")
        if baseline_mae_value is not None:
            baseline_mae = float(baseline_mae_value)

    for row in candidate_rows:
        row["stability"] = stability_verdict(
            row,
            baseline_mae=baseline_mae,
            max_mae_std=args.max_mae_std,
            max_high30_std=args.max_high30_std,
        )

    agg_dir = Path(args.output_root).resolve() / datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )
    agg_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "config_path": str(config_path),
        "api_url": args.api_url,
        "repeats": args.repeats,
        "run_dirs": [str(p) for p in run_dirs],
        "candidates": candidate_rows,
    }

    raw_path = agg_dir / "repeated_raw.json"
    summary_path = agg_dir / "repeated_summary.json"
    md_path = agg_dir / "repeated_summary.md"

    raw_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary_payload = {
        "generated_at": payload["generated_at"],
        "config_path": payload["config_path"],
        "api_url": payload["api_url"],
        "repeats": payload["repeats"],
        "run_dirs": payload["run_dirs"],
        "candidates": [
            {
                "name": c["name"],
                "run_count": c["run_count"],
                "success_run_count": c["success_run_count"],
                "mae_mean": c["mae_mean"],
                "mae_std": c["mae_std"],
                "high30_mean": c["high30_mean"],
                "high30_std": c["high30_std"],
                "latency_mean": c["latency_mean"],
                "cost_mean": c["cost_mean"],
                "stability": c.get("stability"),
                "candidate": c["candidate"],
            }
            for c in candidate_rows
        ],
    }
    summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    build_markdown_summary(md_path, summary_payload)

    print(f"Saved repeated aggregate: {agg_dir}")
    print(f"- raw: {raw_path}")
    print(f"- summary: {summary_path}")
    print(f"- markdown: {md_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
