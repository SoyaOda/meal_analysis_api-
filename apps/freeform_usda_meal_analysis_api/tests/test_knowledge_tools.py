"""Tests for the knowledge-governance tools:
build_lessons_index / check_prior_art / negative_results.json schema.
"""

import json
import os
from pathlib import Path

import pytest

from apps.freeform_usda_meal_analysis_api.scripts import build_lessons_index as bli
from apps.freeform_usda_meal_analysis_api.scripts import check_prior_art as cpa

APP_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = APP_ROOT.parents[1]

NEGATIVE_RESULTS_PATH = APP_ROOT / "evals" / "knowledge" / "negative_results.json"
REQUIRED_NEGATIVE_RESULT_FIELDS = {
    "id",
    "scope",
    "claim",
    "verdict",
    "evidence",
    "reopen_when",
    "recorded_at",
}
VALID_VERDICTS = {"REJECTED", "CEILING", "HOLD", "VOID"}
VALID_SCOPES = {
    "prompt",
    "schema",
    "retrieval",
    "model",
    "sc",
    "uncertainty",
    "calibration",
    "data",
    "ensemble",
}


def _write_lesson(dir_path: Path, filename: str, body: str) -> Path:
    path = dir_path / filename
    path.write_text(body, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# build_lessons_index
# ---------------------------------------------------------------------------


def test_build_entries_parses_valid_lessons(tmp_path) -> None:
    good1 = _write_lesson(
        tmp_path, "20260101_first_finding.md", "# First finding\nbody text\n"
    )
    good2 = _write_lesson(
        tmp_path, "20260202_second_finding.md", "# Second finding\nbody text\n"
    )
    entries = bli.build_entries([good1, good2])
    by_name = {entry.filename: entry for entry in entries}
    assert by_name["20260101_first_finding.md"].date == "2026-01-01"
    assert by_name["20260101_first_finding.md"].title == "First finding"
    assert by_name["20260202_second_finding.md"].date == "2026-02-02"


def test_build_entries_rejects_bad_filename(tmp_path) -> None:
    bad = _write_lesson(tmp_path, "not_a_valid_name.md", "# Some finding\n")
    with pytest.raises(bli.BuildLessonsIndexError):
        bli.build_entries([bad])


def test_build_entries_rejects_missing_h1(tmp_path) -> None:
    bad = _write_lesson(
        tmp_path, "20260101_missing_h1.md", "no heading here\nmore text\n"
    )
    with pytest.raises(bli.BuildLessonsIndexError):
        bli.build_entries([bad])


def test_build_entries_reports_all_violations_at_once(tmp_path) -> None:
    bad_name = _write_lesson(tmp_path, "bad_name.md", "# has a finding\n")
    bad_h1 = _write_lesson(tmp_path, "20260101_no_h1.md", "no heading\n")
    with pytest.raises(bli.BuildLessonsIndexError) as exc_info:
        bli.build_entries([bad_name, bad_h1])
    message = str(exc_info.value)
    assert "bad_name.md" in message
    assert "20260101_no_h1.md" in message


def test_build_index_markdown_orders_by_date_desc_and_counts_total() -> None:
    entries = [
        bli.LessonEntry(date="2026-01-01", filename="20260101_a.md", title="A finding"),
        bli.LessonEntry(date="2026-03-03", filename="20260303_b.md", title="B finding"),
    ]
    markdown = bli.build_index_markdown(entries)
    lines = markdown.splitlines()
    newer_index = lines.index(
        "| 2026-03-03 | [20260303_b.md](20260303_b.md) | B finding |"
    )
    older_index = lines.index(
        "| 2026-01-01 | [20260101_a.md](20260101_a.md) | A finding |"
    )
    assert newer_index < older_index
    assert "Total: 2 lessons." in markdown


def test_check_freshness_detects_missing_and_stale(tmp_path, monkeypatch) -> None:
    lessons_dir = tmp_path / "lessons"
    lessons_dir.mkdir()
    index_path = lessons_dir / "INDEX.md"
    monkeypatch.setattr(bli, "LESSONS_DIR", lessons_dir)
    monkeypatch.setattr(bli, "INDEX_PATH", index_path)

    lesson = _write_lesson(lessons_dir, "20260101_alpha.md", "# Alpha finding\n")
    entries = bli.build_entries([lesson])

    # INDEX.md does not exist yet -> every lesson is reported missing
    missing, newer = bli.check_freshness(entries)
    assert missing == ["20260101_alpha.md"]
    assert newer == []

    # write INDEX.md -> up to date
    index_path.write_text(bli.build_index_markdown(entries), encoding="utf-8")
    missing, newer = bli.check_freshness(entries)
    assert missing == []
    assert newer == []

    # lesson edited after INDEX.md was generated -> stale
    future_mtime = index_path.stat().st_mtime + 5
    os.utime(lesson, (future_mtime, future_mtime))
    missing, newer = bli.check_freshness(entries)
    assert missing == []
    assert newer == ["20260101_alpha.md"]


# ---------------------------------------------------------------------------
# check_prior_art
# ---------------------------------------------------------------------------


def test_matches_or_semantics() -> None:
    assert cpa._matches("foo bar", ["foo"], require_all=False) is True
    assert cpa._matches("foo bar", ["baz"], require_all=False) is False
    assert cpa._matches("foo bar", ["foo", "baz"], require_all=False) is True


def test_matches_and_semantics() -> None:
    assert cpa._matches("foo bar", ["foo", "baz"], require_all=True) is False
    assert cpa._matches("foo bar baz", ["foo", "baz"], require_all=True) is True


def test_search_negative_results_or_and_and(tmp_path, monkeypatch) -> None:
    registry = {
        "entries": [
            {
                "id": "x1",
                "scope": "prompt",
                "claim": "alpha claim text",
                "verdict": "REJECTED",
                "reopen_when": "never",
            },
            {
                "id": "x2",
                "scope": "model",
                "claim": "beta claim text",
                "verdict": "HOLD",
                "reopen_when": "later",
            },
        ]
    }
    path = tmp_path / "negative_results.json"
    path.write_text(json.dumps(registry), encoding="utf-8")
    monkeypatch.setattr(cpa, "NEGATIVE_RESULTS_PATH", path)

    or_hits = cpa.search_negative_results(["alpha", "beta"], require_all=False)
    assert {hit.path for hit in or_hits} == {
        "negative_results.json#x1",
        "negative_results.json#x2",
    }

    and_hits = cpa.search_negative_results(["alpha", "beta"], require_all=True)
    assert and_hits == []

    single_hit = cpa.search_negative_results(["alpha"], require_all=False)
    assert len(single_hit) == 1
    assert single_hit[0].path == "negative_results.json#x1"


def test_search_docs_matches_filename_and_h1(tmp_path, monkeypatch) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "20260101_alpha_topic.md").write_text(
        "# Alpha topic write-up\nbody\n", encoding="utf-8"
    )
    (docs_dir / "unrelated.md").write_text(
        "# Something else entirely\n", encoding="utf-8"
    )
    monkeypatch.setattr(cpa, "DOCS_DIR", docs_dir)

    hits = cpa.search_docs(["alpha"], require_all=False)
    assert len(hits) == 1
    assert hits[0].path == "docs/20260101_alpha_topic.md"


# ---------------------------------------------------------------------------
# negative_results.json schema
# ---------------------------------------------------------------------------


def test_negative_results_registry_schema_is_valid() -> None:
    payload = json.loads(NEGATIVE_RESULTS_PATH.read_text(encoding="utf-8"))
    entries = payload.get("entries")
    assert isinstance(entries, list) and entries

    seen_ids: set[str] = set()
    for entry in entries:
        missing_fields = REQUIRED_NEGATIVE_RESULT_FIELDS - entry.keys()
        assert not missing_fields, f"{entry.get('id')} missing fields: {missing_fields}"

        entry_id = entry["id"]
        assert entry_id not in seen_ids, f"duplicate negative_results id: {entry_id}"
        seen_ids.add(entry_id)

        assert entry["verdict"] in VALID_VERDICTS, (
            f"{entry_id} has an unrecognized verdict: {entry['verdict']!r}"
        )
        assert entry["scope"] in VALID_SCOPES, (
            f"{entry_id} has an unrecognized scope: {entry['scope']!r}"
        )
        assert isinstance(entry["evidence"], list) and entry["evidence"], (
            f"{entry_id} evidence must be a non-empty list"
        )


def test_negative_results_evidence_paths_exist_on_disk() -> None:
    payload = json.loads(NEGATIVE_RESULTS_PATH.read_text(encoding="utf-8"))
    for entry in payload["entries"]:
        for evidence_path in entry["evidence"]:
            resolved = REPO_ROOT / evidence_path
            assert resolved.is_file(), (
                f"{entry['id']} evidence path does not exist: {evidence_path}"
            )
