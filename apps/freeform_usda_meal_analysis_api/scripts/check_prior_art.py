#!/usr/bin/env python3
"""Read-before-write prior-art check for freeform_usda_meal_analysis_api.

Searches known-knowledge sources for keyword hits BEFORE starting a new
experiment or investigation, so past do-not-retry findings are not re-litigated
(see ssot/DEVELOPMENT_OS.md §5). Sources searched:

  (a) evals/knowledge/negative_results.json — id / claim / scope / reopen_when
  (b) evals/knowledge/tested_models.json    — model_id / verdict
  (c) evals/lessons/INDEX.md                — each table row
  (d) docs/*.md                             — filename + first H1 title

Usage:
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python -m \
        apps.freeform_usda_meal_analysis_api.scripts.check_prior_art \
        --query "self-consistency" "portion"

    # AND instead of OR across query words
    ... check_prior_art --query "calibration" "lab" --require-all

This is an information tool: it never fails on "no hits" and exits 0 unless
an actual I/O error occurs while reading a knowledge source.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
NEGATIVE_RESULTS_PATH = APP_ROOT / "evals" / "knowledge" / "negative_results.json"
TESTED_MODELS_PATH = APP_ROOT / "evals" / "knowledge" / "tested_models.json"
LESSONS_INDEX_PATH = APP_ROOT / "evals" / "lessons" / "INDEX.md"
DOCS_DIR = APP_ROOT / "docs"

PRIOR_ART_NOTE = (
    "Read the matching lesson(s) before proceeding, and follow "
    "ssot/DEVELOPMENT_OS.md §5 (do not re-litigate without new reopen_when evidence)."
)

SOURCE_NEGATIVE_RESULTS = "negative_results.json"
SOURCE_TESTED_MODELS = "tested_models.json"
SOURCE_LESSONS_INDEX = "evals/lessons/INDEX.md"
SOURCE_DOCS = "docs/*.md"

H1_PREFIX = "# "


class CheckPriorArtError(RuntimeError):
    """Raised for genuine I/O errors while reading a knowledge source."""


@dataclass
class Hit:
    source: str
    path: str
    summary: str


def _matches(text: str, query_words: list[str], require_all: bool) -> bool:
    lowered = text.lower()
    checks = [word.lower() in lowered for word in query_words]
    return all(checks) if require_all else any(checks)


def _load_json(path: Path, description: str) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except OSError as exc:
        raise CheckPriorArtError(f"{description} を読めません: {path} ({exc})") from exc
    except json.JSONDecodeError as exc:
        raise CheckPriorArtError(
            f"{description} が JSON として不正です: {path} ({exc})"
        ) from exc


def search_negative_results(query_words: list[str], require_all: bool) -> list[Hit]:
    payload = _load_json(NEGATIVE_RESULTS_PATH, "negative_results registry")
    hits: list[Hit] = []
    for entry in payload.get("entries", []):
        searchable = " ".join(
            str(entry.get(field, ""))
            for field in ("id", "scope", "claim", "reopen_when", "verdict")
        )
        if _matches(searchable, query_words, require_all):
            hits.append(
                Hit(
                    source=SOURCE_NEGATIVE_RESULTS,
                    path=f"{SOURCE_NEGATIVE_RESULTS}#{entry.get('id', '?')}",
                    summary=f"[{entry.get('verdict', '?')}] {entry.get('claim', '')}",
                )
            )
    return hits


def search_tested_models(query_words: list[str], require_all: bool) -> list[Hit]:
    payload = _load_json(TESTED_MODELS_PATH, "tested models registry")
    hits: list[Hit] = []
    for entry in payload.get("models", []):
        searchable = " ".join(
            str(entry.get(field, "")) for field in ("model_id", "verdict")
        )
        if _matches(searchable, query_words, require_all):
            hits.append(
                Hit(
                    source=SOURCE_TESTED_MODELS,
                    path=f"{SOURCE_TESTED_MODELS}#{entry.get('model_id', '?')}",
                    summary=f"[{entry.get('verdict', '?')}] {entry.get('notes', '') or entry.get('evidence', '')}",
                )
            )
    return hits


def search_lessons_index(query_words: list[str], require_all: bool) -> list[Hit]:
    if not LESSONS_INDEX_PATH.is_file():
        return []
    try:
        lines = LESSONS_INDEX_PATH.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise CheckPriorArtError(
            f"lessons INDEX.md を読めません: {LESSONS_INDEX_PATH} ({exc})"
        ) from exc

    hits: list[Hit] = []
    for line in lines:
        if not line.startswith("| "):
            continue
        if _matches(line, query_words, require_all):
            hits.append(
                Hit(
                    source=SOURCE_LESSONS_INDEX,
                    path=SOURCE_LESSONS_INDEX,
                    summary=line.strip(),
                )
            )
    return hits


def _extract_h1(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped.startswith(H1_PREFIX):
                return stripped[len(H1_PREFIX) :].strip()
    except OSError as exc:
        raise CheckPriorArtError(f"doc を読めません: {path} ({exc})") from exc
    return ""


def search_docs(query_words: list[str], require_all: bool) -> list[Hit]:
    if not DOCS_DIR.is_dir():
        return []
    hits: list[Hit] = []
    for path in sorted(DOCS_DIR.glob("*.md")):
        title = _extract_h1(path)
        searchable = f"{path.name} {title}"
        if _matches(searchable, query_words, require_all):
            hits.append(
                Hit(
                    source=SOURCE_DOCS,
                    path=f"docs/{path.name}",
                    summary=title,
                )
            )
    return hits


def print_hits(title: str, hits: list[Hit]) -> None:
    print(f"== {title} ({len(hits)} hits) ==")
    if not hits:
        print("  (no hits)")
        return
    for hit in hits:
        print(f"  - {hit.path}: {hit.summary}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Search negative_results.json / tested_models.json / lessons INDEX.md "
            "/ docs for prior-art keyword hits (read-before-write check)."
        )
    )
    parser.add_argument(
        "--query",
        nargs="+",
        required=True,
        help="One or more keywords (OR by default, use --require-all for AND)",
    )
    parser.add_argument(
        "--require-all",
        action="store_true",
        help="Require every --query word to match (AND) instead of any (OR)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    query_words: list[str] = args.query
    require_all: bool = args.require_all

    negative_hits = search_negative_results(query_words, require_all)
    tested_model_hits = search_tested_models(query_words, require_all)
    lessons_hits = search_lessons_index(query_words, require_all)
    docs_hits = search_docs(query_words, require_all)

    mode = "AND" if require_all else "OR"
    print(f"Query ({mode}): {query_words}")
    print()
    print_hits(SOURCE_NEGATIVE_RESULTS, negative_hits)
    print()
    print_hits(SOURCE_TESTED_MODELS, tested_model_hits)
    print()
    print_hits(SOURCE_LESSONS_INDEX, lessons_hits)
    print()
    print_hits(SOURCE_DOCS, docs_hits)
    print()

    total_hits = (
        len(negative_hits) + len(tested_model_hits) + len(lessons_hits) + len(docs_hits)
    )
    print(f"Total hits: {total_hits}")
    if total_hits > 0:
        print(PRIOR_ART_NOTE)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CheckPriorArtError as exc:
        raise SystemExit(f"ERROR: {exc}")
