#!/usr/bin/env python3
"""Build a reproducible PDCA session snapshot for agent handoff."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.error import URLError, HTTPError
from urllib.request import urlopen


APP_ROOT = Path(__file__).resolve().parents[1]
EVALS_ROOT = APP_ROOT / "evals"
BASELINE_PATH = EVALS_ROOT / "baselines" / "current_baseline.json"
LESSONS_ROOT = EVALS_ROOT / "lessons"
REPEAT_RUNS_ROOT = EVALS_ROOT / "repeat_runs"


@dataclass
class RemoteConfigSummary:
    api_url: str
    updated_at: Optional[str]
    updated_by: Optional[str]
    vlm_model_id: Optional[str]
    vlm_prompt_file: Optional[str]
    vlm_prompt_text_len: int
    vlm_temperature: Optional[float]
    vlm_max_tokens: Optional[int]
    vlm_reasoning_effort: Optional[str]
    stage1_top_k: Optional[int]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def extract_markdown_field(lines: list[str], prefix: str) -> str:
    prefix_lower = prefix.lower()
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith(prefix_lower):
            return stripped[len(prefix) :].strip() or "-"
    return "-"


def summarize_lesson(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    title = next((line.strip() for line in lines if line.strip().startswith("#")), path.name)
    date = extract_markdown_field(lines, "- Date:")
    decision = extract_markdown_field(lines, "- Decision:")
    promoted_prompt = extract_markdown_field(lines, "- Promoted prompt:")
    return {
        "file": str(path.relative_to(APP_ROOT)),
        "title": title,
        "date": date,
        "decision": decision,
        "promoted_prompt": promoted_prompt,
    }


def fetch_remote_config(api_url: str, timeout_sec: int) -> tuple[Optional[RemoteConfigSummary], Optional[str]]:
    endpoint = f"{api_url.rstrip('/')}/admin/api/config?refresh=true"
    try:
        with urlopen(endpoint, timeout=timeout_sec) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        return None, f"HTTPError: {exc.code} {exc.reason}"
    except URLError as exc:
        return None, f"URLError: {exc.reason}"
    except Exception as exc:  # pragma: no cover - defensive branch
        return None, f"{type(exc).__name__}: {exc}"

    config = payload.get("config", {}) if isinstance(payload, dict) else {}
    vlm = config.get("vlm", {}) if isinstance(config, dict) else {}
    search = config.get("search", {}) if isinstance(config, dict) else {}

    prompt_text = vlm.get("prompt_text")
    prompt_text_len = len(prompt_text) if isinstance(prompt_text, str) else 0

    summary = RemoteConfigSummary(
        api_url=api_url,
        updated_at=config.get("updated_at"),
        updated_by=config.get("updated_by"),
        vlm_model_id=vlm.get("model_id"),
        vlm_prompt_file=vlm.get("prompt_file"),
        vlm_prompt_text_len=prompt_text_len,
        vlm_temperature=vlm.get("temperature"),
        vlm_max_tokens=vlm.get("max_tokens"),
        vlm_reasoning_effort=vlm.get("reasoning_effort"),
        stage1_top_k=search.get("stage1_top_k"),
    )
    return summary, None


def build_markdown(
    baseline_payload: dict[str, Any],
    latest_lessons: list[dict[str, str]],
    latest_repeat_summaries: list[str],
    remote_summary: Optional[RemoteConfigSummary],
    remote_error: Optional[str],
    lessons_limit: int,
    repeat_limit: int,
) -> str:
    now_utc = datetime.now(timezone.utc).isoformat()
    summary = baseline_payload.get("summary", {})
    lines: list[str] = [
        "# PDCA Session Bootstrap Snapshot",
        "",
        f"- generated_at_utc: {now_utc}",
        "- scope: apps/freeform_usda_meal_analysis_api",
        "",
        "## Must Read (in order)",
        "1. `apps/freeform_usda_meal_analysis_api/AGENTS.md`",
        "2. `apps/freeform_usda_meal_analysis_api/CLAUDE.md`",
        "3. `apps/freeform_usda_meal_analysis_api/docs/PDCA_SESSION_START_CHECKLIST.md`",
        "4. `apps/freeform_usda_meal_analysis_api/evals/baselines/current_baseline.json`",
        f"5. latest {lessons_limit} lessons listed below",
        "",
        "## Current Baseline",
        "- file: `apps/freeform_usda_meal_analysis_api/evals/baselines/current_baseline.json`",
        f"- candidate: `{summary.get('name', '-')}`",
        f"- model: `{summary.get('vlm_model_id', '-')}`",
        f"- calorie_mae_percent: `{summary.get('calorie_mae_percent', '-')}`",
        f"- high_error_rate_30_percent: `{summary.get('high_error_rate_30_percent', '-')}`",
        f"- avg_latency_sec: `{summary.get('avg_latency_sec', '-')}`",
        f"- avg_cost_usd: `{summary.get('avg_cost_usd', '-')}`",
        f"- source_run: `{baseline_payload.get('source_run', '-')}`",
        f"- note: `{baseline_payload.get('notes', '-')}`",
        "",
        f"## Latest Lessons (top {lessons_limit})",
    ]

    if latest_lessons:
        for lesson in latest_lessons:
            lines.extend(
                [
                    f"- file: `{lesson['file']}`",
                    f"  - title: {lesson['title']}",
                    f"  - {lesson['date']}",
                    f"  - {lesson['decision']}",
                    f"  - {lesson['promoted_prompt']}",
                ]
            )
    else:
        lines.append("- no lesson files found")

    lines.extend(
        [
            "",
            f"## Latest Repeat Summaries (top {repeat_limit})",
        ]
    )
    if latest_repeat_summaries:
        for item in latest_repeat_summaries:
            lines.append(f"- `{item}`")
    else:
        lines.append("- no repeat summary found")

    lines.extend(
        [
            "",
            "## Remote Config Check",
        ]
    )
    if remote_summary:
        lines.extend(
            [
                f"- api_url: `{remote_summary.api_url}`",
                f"- updated_at: `{remote_summary.updated_at}`",
                f"- updated_by: `{remote_summary.updated_by}`",
                f"- vlm_model_id: `{remote_summary.vlm_model_id}`",
                f"- vlm_prompt_file: `{remote_summary.vlm_prompt_file}`",
                f"- vlm_prompt_text_len: `{remote_summary.vlm_prompt_text_len}`",
                f"- vlm_temperature: `{remote_summary.vlm_temperature}`",
                f"- vlm_max_tokens: `{remote_summary.vlm_max_tokens}`",
                f"- vlm_reasoning_effort: `{remote_summary.vlm_reasoning_effort}`",
                f"- search.stage1_top_k: `{remote_summary.stage1_top_k}`",
            ]
        )
        if remote_summary.vlm_prompt_text_len > 0:
            lines.append("- warning: Prompt Text Override is active (Prompt File is ignored).")
    else:
        lines.append(f"- skipped/failed: {remote_error or 'not requested'}")

    lines.extend(
        [
            "",
            "## Guardrails",
            "- Never promote from dev-only split results. Promotion requires full50 coverage.",
            "- Keep `use_vlm_cache=false` for evaluation runs.",
            "- Never include `test_foodXX`/ground-truth hints in prompts.",
            "- Admin panel `Local` tab uses current origin (relative path), not guaranteed localhost.",
        ]
    )
    return "\n".join(lines) + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate PDCA session bootstrap snapshot for reproducible handoff"
    )
    parser.add_argument(
        "--lessons-limit",
        type=int,
        default=5,
        help="How many latest lessons to include",
    )
    parser.add_argument(
        "--repeat-limit",
        type=int,
        default=3,
        help="How many latest repeat summaries to include",
    )
    parser.add_argument(
        "--api-url",
        default=None,
        help="Optional API URL for /admin/api/config refresh check",
    )
    parser.add_argument(
        "--timeout-sec",
        type=int,
        default=15,
        help="HTTP timeout for remote config check",
    )
    parser.add_argument(
        "--output",
        default=str(EVALS_ROOT / "knowledge" / "session_bootstrap_latest.md"),
        help="Output markdown path",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if not BASELINE_PATH.exists():
        raise FileNotFoundError(f"baseline not found: {BASELINE_PATH}")
    baseline_payload = load_json(BASELINE_PATH)

    lesson_paths = sorted(
        [p for p in LESSONS_ROOT.glob("*.md") if p.name.lower() != "readme.md"],
        key=lambda p: p.name,
        reverse=True,
    )
    latest_lessons = [summarize_lesson(p) for p in lesson_paths[: args.lessons_limit]]

    repeat_paths = sorted(
        REPEAT_RUNS_ROOT.glob("*/repeated_summary.md"),
        key=lambda p: p.parent.name,
        reverse=True,
    )
    latest_repeat_summaries = [
        str(path.relative_to(APP_ROOT)) for path in repeat_paths[: args.repeat_limit]
    ]

    remote_summary: Optional[RemoteConfigSummary] = None
    remote_error: Optional[str] = None
    if args.api_url:
        remote_summary, remote_error = fetch_remote_config(args.api_url, args.timeout_sec)

    markdown = build_markdown(
        baseline_payload=baseline_payload,
        latest_lessons=latest_lessons,
        latest_repeat_summaries=latest_repeat_summaries,
        remote_summary=remote_summary,
        remote_error=remote_error,
        lessons_limit=args.lessons_limit,
        repeat_limit=args.repeat_limit,
    )

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"wrote: {output_path}")
    if remote_error:
        print(f"remote_config_check: {remote_error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
