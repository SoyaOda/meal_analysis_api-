#!/usr/bin/env python3
"""Build a reproducible PDCA session snapshot for agent handoff."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

from .build_lessons_index import (
    EXCLUDED_FILENAMES,
    BuildLessonsIndexError,
    build_entries,
    build_index_markdown,
    check_freshness,
    discover_lesson_files,
)
from .build_lessons_index import INDEX_PATH as LESSONS_INDEX_PATH


APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parents[1]
EVALS_ROOT = APP_ROOT / "evals"
BASELINE_PATH = EVALS_ROOT / "baselines" / "current_baseline.json"
LESSONS_ROOT = EVALS_ROOT / "lessons"
REPEAT_RUNS_ROOT = EVALS_ROOT / "repeat_runs"
NEGATIVE_RESULTS_PATH = EVALS_ROOT / "knowledge" / "negative_results.json"
CURRENT_PLAN_PATH = APP_ROOT / "plans" / "current.md"

GIT_HEAD_TIMEOUT_SEC = 10


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


@dataclass
class NegativeRegistrySummary:
    total: int
    verdict_counts: dict[str, int]
    entry_ids: list[str]


@dataclass
class LessonsIndexStatus:
    lesson_count: int
    status: str  # "up_to_date" | "regenerated"
    missing_before: list[str]
    newer_before: list[str]


@dataclass
class BranchConsistencyCheck:
    current_branch: Optional[str]
    plan_branch: Optional[str]
    warning: Optional[str]


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
    title = next(
        (line.strip() for line in lines if line.strip().startswith("#")), path.name
    )
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


def fetch_remote_config(
    api_url: str, timeout_sec: int
) -> tuple[Optional[RemoteConfigSummary], Optional[str]]:
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


def build_negative_registry_summary(
    negative_results_path: Path,
) -> NegativeRegistrySummary:
    if not negative_results_path.is_file():
        raise FileNotFoundError(
            f"negative results registry not found: {negative_results_path}"
        )
    payload = load_json(negative_results_path)
    entries = payload.get("entries", [])
    verdict_counts: dict[str, int] = {}
    entry_ids: list[str] = []
    for entry in entries:
        verdict = entry.get("verdict", "UNKNOWN")
        verdict_counts[verdict] = verdict_counts.get(verdict, 0) + 1
        entry_ids.append(entry.get("id", "?"))
    return NegativeRegistrySummary(
        total=len(entries), verdict_counts=verdict_counts, entry_ids=entry_ids
    )


def refresh_lessons_index_if_stale() -> LessonsIndexStatus:
    """Verify evals/lessons/INDEX.md freshness and auto-regenerate it if stale."""
    lesson_files = discover_lesson_files()
    entries = build_entries(lesson_files)
    missing, newer = check_freshness(entries)
    if not missing and not newer:
        return LessonsIndexStatus(
            lesson_count=len(entries),
            status="up_to_date",
            missing_before=[],
            newer_before=[],
        )
    markdown = build_index_markdown(entries)
    LESSONS_INDEX_PATH.write_text(markdown, encoding="utf-8")
    return LessonsIndexStatus(
        lesson_count=len(entries),
        status="regenerated",
        missing_before=missing,
        newer_before=newer,
    )


def check_branch_consistency() -> BranchConsistencyCheck:
    """Compare the current git branch against the resume branch in plans/current.md."""
    current_branch: Optional[str] = None
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=GIT_HEAD_TIMEOUT_SEC,
            check=False,
        )
        if result.returncode == 0:
            current_branch = result.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        current_branch = None

    plan_branch: Optional[str] = None
    if CURRENT_PLAN_PATH.is_file():
        match = re.search(
            r"git checkout ([^\s&`]+)", CURRENT_PLAN_PATH.read_text(encoding="utf-8")
        )
        if match:
            plan_branch = match.group(1)

    warning: Optional[str] = None
    if current_branch and plan_branch and current_branch != plan_branch:
        warning = (
            f"WARNING: current branch `{current_branch}` does not match the "
            f"plans/current.md resume branch `{plan_branch}`."
        )
    return BranchConsistencyCheck(
        current_branch=current_branch, plan_branch=plan_branch, warning=warning
    )


def build_markdown(
    baseline_payload: dict[str, Any],
    latest_lessons: list[dict[str, str]],
    latest_repeat_summaries: list[str],
    remote_summary: Optional[RemoteConfigSummary],
    remote_error: Optional[str],
    lessons_limit: int,
    repeat_limit: int,
    negative_registry: NegativeRegistrySummary,
    lessons_index_status: LessonsIndexStatus,
    branch_check: BranchConsistencyCheck,
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
            "## Negative Registry Summary",
            "- file: `apps/freeform_usda_meal_analysis_api/evals/knowledge/negative_results.json`",
            f"- total entries: {negative_registry.total}",
        ]
    )
    if negative_registry.verdict_counts:
        for verdict in sorted(negative_registry.verdict_counts):
            lines.append(f"  - {verdict}: {negative_registry.verdict_counts[verdict]}")
    lines.append(f"- entry ids: {', '.join(negative_registry.entry_ids) or '-'}")
    lines.append(
        '- **before starting a new experiment, run `check_prior_art --query "<lever keyword>"` '
        "(read-before-write, required)**"
    )

    lines.extend(
        [
            "",
            "## Lessons Index Freshness",
            "- file: `apps/freeform_usda_meal_analysis_api/evals/lessons/INDEX.md`",
            f"- lesson count: {lessons_index_status.lesson_count}",
        ]
    )
    if lessons_index_status.status == "up_to_date":
        lines.append("- status: up to date")
    else:
        lines.append("- status: **regenerated** (was stale, auto-rebuilt this run)")
        if lessons_index_status.missing_before:
            lines.append(
                f"  - previously not listed: {', '.join(lessons_index_status.missing_before)}"
            )
        if lessons_index_status.newer_before:
            lines.append(
                f"  - previously newer than INDEX.md: {', '.join(lessons_index_status.newer_before)}"
            )

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
            lines.append(
                "- warning: Prompt Text Override is active (Prompt File is ignored)."
            )
    else:
        lines.append(f"- skipped/failed: {remote_error or 'not requested'}")

    lines.extend(
        [
            "",
            "## Branch Consistency",
            f"- current branch: `{branch_check.current_branch or '-'}`",
            f"- plans/current.md resume branch: `{branch_check.plan_branch or '-'}`",
        ]
    )
    if branch_check.warning:
        lines.append(f"- {branch_check.warning}")
    else:
        lines.append("- OK: branches match (or one side is unavailable to compare).")

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
        [
            p
            for p in LESSONS_ROOT.glob("*.md")
            if p.name.lower() not in EXCLUDED_FILENAMES
        ],
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
        remote_summary, remote_error = fetch_remote_config(
            args.api_url, args.timeout_sec
        )

    negative_registry = build_negative_registry_summary(NEGATIVE_RESULTS_PATH)

    try:
        lessons_index_status = refresh_lessons_index_if_stale()
    except BuildLessonsIndexError as exc:
        raise BuildLessonsIndexError(
            f"cannot refresh lessons INDEX during bootstrap: {exc}"
        ) from exc

    branch_check = check_branch_consistency()

    markdown = build_markdown(
        baseline_payload=baseline_payload,
        latest_lessons=latest_lessons,
        latest_repeat_summaries=latest_repeat_summaries,
        remote_summary=remote_summary,
        remote_error=remote_error,
        lessons_limit=args.lessons_limit,
        repeat_limit=args.repeat_limit,
        negative_registry=negative_registry,
        lessons_index_status=lessons_index_status,
        branch_check=branch_check,
    )

    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"wrote: {output_path}")
    if remote_error:
        print(f"remote_config_check: {remote_error}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildLessonsIndexError as exc:
        raise SystemExit(f"ERROR: {exc}")
