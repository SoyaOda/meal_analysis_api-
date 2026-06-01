#!/usr/bin/env python3
"""Merge split PDCA run outputs into a single gated decision run."""

from __future__ import annotations

import argparse
import json
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .run_pdca_batch_eval import (
    PROJECT_ROOT,
    compare_to_baseline,
    gate_decision,
    load_baseline_summary,
    parse_image_index_from_name,
    safe_percentile,
    write_markdown_summary,
)


def resolve_path(path_str: str) -> Path:
    path = Path(path_str)
    if path.is_absolute():
        return path
    return (PROJECT_ROOT / path).resolve()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_raw_results_path(path: Path) -> Path:
    if path.is_dir():
        return path / "raw_results.json"
    return path


def summarize_candidate(
    candidate: Dict[str, Any],
    image_results: List[Dict[str, Any]],
    expected_image_count: int,
) -> Dict[str, Any]:
    success_rows = [r for r in image_results if r.get("success")]
    failure_rows = [r for r in image_results if not r.get("success")]
    calorie_errors = [
        float(r.get("calorie_abs_percent_error", 0.0)) for r in success_rows
    ]
    latencies = [float(r.get("latency_sec", 0.0)) for r in success_rows]
    costs = [
        float(r["cost_usd"]) for r in success_rows if r.get("cost_usd") is not None
    ]
    cache_hits = sum(
        1 for r in success_rows if (r.get("usage") or {}).get("cached") is True
    )

    evaluated_image_count = len(image_results)
    failure_count = len(failure_rows)
    return {
        "name": candidate["name"],
        "vlm_model_id": candidate["vlm_model_id"],
        "prompt_path": candidate.get("prompt_path"),
        "calorie_mae_percent": round(statistics.mean(calorie_errors), 4)
        if calorie_errors
        else 0.0,
        "calorie_p50_percent": round(safe_percentile(calorie_errors, 0.5), 4)
        if calorie_errors
        else 0.0,
        "calorie_p90_percent": round(safe_percentile(calorie_errors, 0.9), 4)
        if calorie_errors
        else 0.0,
        "high_error_rate_30_percent": round(
            (sum(1 for e in calorie_errors if e >= 30.0) / len(calorie_errors) * 100.0)
            if calorie_errors
            else 0.0,
            4,
        ),
        "avg_latency_sec": round(statistics.mean(latencies), 4) if latencies else 0.0,
        "avg_cost_usd": round(statistics.mean(costs), 6) if costs else None,
        "total_cost_usd": round(sum(costs), 6),
        "success_count": len(success_rows),
        "failure_count": failure_count,
        "cache_hit_rate_percent": round((cache_hits / len(success_rows) * 100.0), 4)
        if success_rows
        else 0.0,
        "evaluated_image_count": evaluated_image_count,
        "expected_image_count": expected_image_count,
        "coverage_complete": evaluated_image_count == expected_image_count,
        "all_success": failure_count == 0,
    }


def merge_payloads(payloads: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not payloads:
        raise ValueError("no payloads to merge")

    merged_candidates: Dict[str, Dict[str, Any]] = {}
    requested_indices: List[int] = []
    present_indices: List[int] = []
    missing_indices: List[int] = []

    for payload in payloads:
        payload_requested = payload.get("requested_indices") or []
        payload_present = payload.get("present_indices") or []
        payload_missing = payload.get("missing_indices") or []

        # Backward compatibility: older runs may not have index metadata.
        if not payload_requested or not payload_present:
            inferred_indices: List[int] = []
            for row in payload.get("results", []):
                for image_row in row.get("image_results", []):
                    idx = parse_image_index_from_name(image_row.get("image", ""))
                    if idx > 0:
                        inferred_indices.append(idx)
            inferred_unique = sorted(set(inferred_indices))
            if not payload_requested:
                payload_requested = inferred_unique
            if not payload_present:
                payload_present = inferred_unique

        requested_indices.extend(payload_requested)
        present_indices.extend(payload_present)
        missing_indices.extend(payload_missing)

        for row in payload.get("results", []):
            name = row["summary"]["name"]
            if name not in merged_candidates:
                merged_candidates[name] = {
                    "candidate": row.get("candidate", {}),
                    "image_results": {},
                }
            target = merged_candidates[name]["image_results"]
            for image_row in row.get("image_results", []):
                image_name = image_row["image"]
                if image_name in target:
                    raise RuntimeError(
                        f"duplicated image while merging: candidate={name}, image={image_name}"
                    )
                target[image_name] = image_row

    requested_unique = sorted(set(requested_indices))
    present_unique = sorted(set(present_indices))
    missing_unique = sorted(set(missing_indices))

    merged_rows: List[Dict[str, Any]] = []
    expected_image_count = (
        len(requested_unique) if requested_unique else len(present_unique)
    )
    for name, data in sorted(merged_candidates.items(), key=lambda x: x[0]):
        candidate = data["candidate"]
        image_results = sorted(
            data["image_results"].values(),
            key=lambda r: parse_image_index_from_name(r["image"]),
        )
        summary = summarize_candidate(
            candidate, image_results, expected_image_count=expected_image_count
        )
        merged_rows.append(
            {
                "candidate": candidate,
                "summary": summary,
                "image_results": image_results,
            }
        )

    return {
        "results": merged_rows,
        "requested_indices": requested_unique,
        "present_indices": present_unique,
        "missing_indices": missing_unique,
        "image_count": len(present_unique),
        "requested_image_count": len(requested_unique)
        if requested_unique
        else len(present_unique),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Merge split PDCA run outputs")
    parser.add_argument(
        "--runs",
        nargs="+",
        required=True,
        help="Run directories or raw_results.json files to merge",
    )
    parser.add_argument("--required-image-count", type=int, default=50)
    parser.add_argument("--baseline-file", default=None)
    parser.add_argument(
        "--output-root", default="apps/freeform_usda_meal_analysis_api/evals/runs"
    )
    parser.add_argument(
        "--write-baseline", default=None, help="Optional baseline output JSON path"
    )
    parser.add_argument(
        "--baseline-candidate", default=None, help="Candidate name for baseline write"
    )
    args = parser.parse_args()

    raw_paths = [resolve_raw_results_path(resolve_path(p)) for p in args.runs]
    payloads = [load_json(p) for p in raw_paths]
    merged = merge_payloads(payloads)

    baseline_file: Optional[Path]
    if args.baseline_file:
        baseline_file = resolve_path(args.baseline_file)
    else:
        baseline_hint = payloads[0].get("baseline_file")
        baseline_file = resolve_path(baseline_hint) if baseline_hint else None
    baseline_summary = load_baseline_summary(baseline_file)
    budget = payloads[0].get("budget") or {}

    for row in merged["results"]:
        row["baseline_delta"] = compare_to_baseline(row["summary"], baseline_summary)
        row["decision"] = gate_decision(
            row["summary"],
            baseline_summary,
            budget,
            required_image_count=args.required_image_count,
        )

    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = resolve_path(args.output_root) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    payload = {
        "generated_at": datetime.now().isoformat(),
        "api_url": payloads[0].get("api_url"),
        "config_path": payloads[0].get("config_path"),
        "baseline_file": str(baseline_file) if baseline_file else None,
        "baseline_summary": baseline_summary,
        "budget": budget,
        "image_count": merged["image_count"],
        "requested_image_count": merged["requested_image_count"],
        "required_image_count": args.required_image_count,
        "requested_indices": merged["requested_indices"],
        "present_indices": merged["present_indices"],
        "missing_indices": merged["missing_indices"],
        "merged_from_runs": [str(p.parent) for p in raw_paths],
        "results": merged["results"],
    }

    raw_path = run_dir / "raw_results.json"
    summary_path = run_dir / "summary.json"
    summary_md_path = run_dir / "summary.md"

    raw_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    summary_payload = {
        "generated_at": payload["generated_at"],
        "api_url": payload["api_url"],
        "image_count": payload["image_count"],
        "requested_image_count": payload["requested_image_count"],
        "required_image_count": payload["required_image_count"],
        "requested_indices": payload["requested_indices"],
        "present_indices": payload["present_indices"],
        "missing_indices": payload["missing_indices"],
        "baseline_file": payload["baseline_file"],
        "merged_from_runs": payload["merged_from_runs"],
        "results": [
            {
                "candidate": r["candidate"],
                "summary": r["summary"],
                "baseline_delta": r.get("baseline_delta", {}),
                "decision": r.get("decision", {}),
            }
            for r in merged["results"]
        ],
    }
    summary_path.write_text(
        json.dumps(summary_payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    write_markdown_summary(summary_md_path, summary_payload)

    print(f"Saved merged run: {run_dir}")
    print(f"- raw: {raw_path}")
    print(f"- summary: {summary_path}")
    print(f"- markdown: {summary_md_path}")

    if args.write_baseline:
        target = resolve_path(args.write_baseline)
        target.parent.mkdir(parents=True, exist_ok=True)
        promotable = [
            r
            for r in merged["results"]
            if r.get("decision", {}).get("decision") == "promote"
        ]

        chosen: Optional[Dict[str, Any]] = None
        if args.baseline_candidate:
            for row in promotable:
                if row["summary"]["name"] == args.baseline_candidate:
                    chosen = row
                    break
        else:
            ordered = sorted(
                promotable, key=lambda r: r["summary"]["calorie_mae_percent"]
            )
            chosen = ordered[0] if ordered else None

        if chosen is None:
            raise RuntimeError("No promotable candidate matched for baseline write")

        baseline_payload = {
            "generated_at": datetime.now().isoformat(),
            "source_run": str(run_dir),
            "summary": chosen["summary"],
        }
        target.write_text(
            json.dumps(baseline_payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"Baseline written: {target}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
