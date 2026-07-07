#!/usr/bin/env python3
"""Build evals/lessons/INDEX.md from the individual lesson files.

Each lesson file must follow the filename convention `YYYYMMDD_<slug>.md` and
start with a level-1 heading (`# ...`) that is used as the "finding" summary.

Usage:
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python -m \
        apps.freeform_usda_meal_analysis_api.scripts.build_lessons_index

    # verify INDEX.md is up to date without regenerating it
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python -m \
        apps.freeform_usda_meal_analysis_api.scripts.build_lessons_index --check

No fallback: a filename-convention violation or a missing H1 title stops the
script with a non-zero exit and the offending file list (never skipped silently).
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
LESSONS_DIR = APP_ROOT / "evals" / "lessons"
INDEX_PATH = LESSONS_DIR / "INDEX.md"

EXCLUDED_FILENAMES = frozenset({"readme.md", "index.md"})

FILENAME_DATE_LEN = 8
REGENERATE_COMMAND = (
    "PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python -m "
    "apps.freeform_usda_meal_analysis_api.scripts.build_lessons_index"
)
CHECK_COMMAND = f"{REGENERATE_COMMAND} --check"


class BuildLessonsIndexError(RuntimeError):
    """Raised for filename-convention or H1-title violations (no silent skip)."""


@dataclass
class LessonEntry:
    date: str  # YYYY-MM-DD
    filename: str
    title: str


def _parse_filename(path: Path) -> tuple[str, str] | None:
    """Return (date_prefix, slug) if `path` matches `YYYYMMDD_<slug>.md`, else None."""
    stem = path.name[: -len(".md")] if path.name.endswith(".md") else None
    if stem is None:
        return None
    if "_" not in stem:
        return None
    date_prefix, _, slug = stem.partition("_")
    if len(date_prefix) != FILENAME_DATE_LEN or not date_prefix.isdigit():
        return None
    if not slug:
        return None
    if not all(ch.isalnum() or ch == "_" for ch in slug):
        return None
    try:
        datetime.strptime(date_prefix, "%Y%m%d")
    except ValueError:
        return None
    return date_prefix, slug


def _extract_h1_title(path: Path) -> str | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
        if stripped == "#":
            return ""
    return None


def discover_lesson_files() -> list[Path]:
    if not LESSONS_DIR.is_dir():
        raise BuildLessonsIndexError(f"lessons directory not found: {LESSONS_DIR}")
    return sorted(
        p for p in LESSONS_DIR.glob("*.md") if p.name.lower() not in EXCLUDED_FILENAMES
    )


def build_entries(lesson_files: list[Path]) -> list[LessonEntry]:
    """Parse all lesson files. Raises BuildLessonsIndexError listing every violation."""
    filename_violations: list[str] = []
    missing_h1_violations: list[str] = []
    entries: list[LessonEntry] = []

    for path in lesson_files:
        parsed = _parse_filename(path)
        if parsed is None:
            filename_violations.append(path.name)
            continue
        date_prefix, _slug = parsed
        title = _extract_h1_title(path)
        if title is None:
            missing_h1_violations.append(path.name)
            continue
        date_str = f"{date_prefix[0:4]}-{date_prefix[4:6]}-{date_prefix[6:8]}"
        entries.append(LessonEntry(date=date_str, filename=path.name, title=title))

    if filename_violations or missing_h1_violations:
        message_lines = [
            "evals/lessons index build failed — no-fallback, fix these files:"
        ]
        if filename_violations:
            message_lines.append("  filename does not match `YYYYMMDD_<slug>.md`:")
            message_lines.extend(
                f"    - {name}" for name in sorted(filename_violations)
            )
        if missing_h1_violations:
            message_lines.append(
                "  missing level-1 heading (`# ...`) as first H1 line:"
            )
            message_lines.extend(
                f"    - {name}" for name in sorted(missing_h1_violations)
            )
        raise BuildLessonsIndexError("\n".join(message_lines))

    return entries


def _escape_table_cell(text: str) -> str:
    return text.replace("|", "\\|")


def build_index_markdown(entries: list[LessonEntry]) -> str:
    ordered = sorted(entries, key=lambda e: (e.date, e.filename), reverse=True)
    lines = [
        "<!-- AUTO-GENERATED FILE. DO NOT EDIT BY HAND.",
        "Regenerate with:",
        f"  {REGENERATE_COMMAND}",
        "Verify freshness with:",
        f"  {CHECK_COMMAND}",
        "-->",
        "",
        "# Lessons Index",
        "",
        "| date | lesson | finding |",
        "|---|---|---|",
    ]
    for entry in ordered:
        finding = _escape_table_cell(entry.title)
        lines.append(
            f"| {entry.date} | [{entry.filename}]({entry.filename}) | {finding} |"
        )
    lines.append("")
    lines.append(f"Total: {len(ordered)} lessons.")
    lines.append("")
    return "\n".join(lines)


def check_freshness(entries: list[LessonEntry]) -> tuple[list[str], list[str]]:
    """Compute (missing_from_index, newer_than_index) filenames without printing.

    `missing_from_index` is empty and `newer_than_index` is empty when INDEX.md
    is up to date. If INDEX.md does not exist, every entry is reported missing.
    """
    if not INDEX_PATH.is_file():
        return sorted(entry.filename for entry in entries), []

    index_text = INDEX_PATH.read_text(encoding="utf-8")
    index_mtime = INDEX_PATH.stat().st_mtime

    missing_from_index = sorted(
        entry.filename for entry in entries if entry.filename not in index_text
    )
    newer_than_index = sorted(
        entry.filename
        for entry in entries
        if (LESSONS_DIR / entry.filename).stat().st_mtime > index_mtime
    )
    return missing_from_index, newer_than_index


def run_check(entries: list[LessonEntry]) -> int:
    """Verify INDEX.md lists every current lesson and is not stale. Returns exit code."""
    if not INDEX_PATH.is_file():
        print(f"stale: {INDEX_PATH} does not exist. Run: {REGENERATE_COMMAND}")
        return 1

    missing_from_index, newer_than_index = check_freshness(entries)

    if not missing_from_index and not newer_than_index:
        print(f"up to date: {INDEX_PATH} ({len(entries)} lessons)")
        return 0

    print(f"stale: {INDEX_PATH} is out of date. Run: {REGENERATE_COMMAND}")
    if missing_from_index:
        print("  lessons not listed in INDEX.md:")
        for name in missing_from_index:
            print(f"    - {name}")
    if newer_than_index:
        print("  lessons newer than INDEX.md:")
        for name in newer_than_index:
            print(f"    - {name}")
    return 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build or verify evals/lessons/INDEX.md from lesson files"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify INDEX.md freshness without regenerating it",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    lesson_files = discover_lesson_files()
    entries = build_entries(lesson_files)

    if args.check:
        return run_check(entries)

    markdown = build_index_markdown(entries)
    INDEX_PATH.write_text(markdown, encoding="utf-8")
    print(f"wrote: {INDEX_PATH} ({len(entries)} lessons)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BuildLessonsIndexError as exc:
        raise SystemExit(f"ERROR: {exc}")
