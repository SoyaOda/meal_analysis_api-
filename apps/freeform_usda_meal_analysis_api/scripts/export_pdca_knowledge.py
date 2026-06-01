#!/usr/bin/env python3
"""Export structured PDCA knowledge rows from eval run summaries."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def iter_run_dirs(runs_root: Path) -> List[Path]:
    dirs = [p for p in runs_root.iterdir() if p.is_dir()]
    return sorted(dirs, key=lambda p: p.name)


def build_rows(summary_payload: Dict[str, Any], run_id: str) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    base = {
        "run_id": run_id,
        "generated_at": summary_payload.get("generated_at"),
        "api_url": summary_payload.get("api_url"),
        "image_count": summary_payload.get("image_count"),
        "requested_image_count": summary_payload.get("requested_image_count"),
        "required_image_count": summary_payload.get("required_image_count"),
        "missing_indices": summary_payload.get("missing_indices", []),
        "baseline_file": summary_payload.get("baseline_file"),
    }
    for result in summary_payload.get("results", []):
        summary = result.get("summary", {})
        decision = result.get("decision", {})
        row = {
            **base,
            "candidate": result.get("candidate", {}),
            "summary": summary,
            "baseline_delta": result.get("baseline_delta", {}),
            "decision": decision.get("decision"),
            "decision_reasons": decision.get("reasons", []),
            "factor_tags": {
                "model_id": summary.get("vlm_model_id"),
                "prompt_path": summary.get("prompt_path"),
                "prompt_sha256": (result.get("candidate", {}) or {}).get(
                    "prompt_sha256"
                ),
                "reasoning_effort": (result.get("candidate", {}) or {}).get(
                    "reasoning_effort"
                ),
                "temperature": (result.get("candidate", {}) or {}).get("temperature"),
                "seed": (result.get("candidate", {}) or {}).get("seed"),
                "max_tokens": (result.get("candidate", {}) or {}).get("max_tokens"),
                "stage1_top_k": (result.get("candidate", {}) or {}).get("stage1_top_k"),
                "use_vlm_cache": (result.get("candidate", {}) or {}).get(
                    "use_vlm_cache"
                ),
            },
        }
        rows.append(row)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export structured PDCA knowledge rows"
    )
    parser.add_argument(
        "--runs-root",
        default="apps/freeform_usda_meal_analysis_api/evals/runs",
        help="Directory containing run folders",
    )
    parser.add_argument(
        "--output",
        default="apps/freeform_usda_meal_analysis_api/evals/knowledge/experiment_log.jsonl",
        help="Output JSONL path",
    )
    args = parser.parse_args()

    runs_root = Path(args.runs_root).resolve()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rows: List[Dict[str, Any]] = []
    for run_dir in iter_run_dirs(runs_root):
        summary_path = run_dir / "summary.json"
        if not summary_path.exists():
            continue
        summary_payload = load_json(summary_path)
        rows.extend(build_rows(summary_payload, run_dir.name))

    with output_path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"rows={len(rows)}")
    print(f"output={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
