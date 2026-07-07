#!/usr/bin/env python3
"""Self-check for the repo's "development OS" (`ssot/DEVELOPMENT_OS.md`).

Runs a fixed set of checks (branch-pointer consistency, lessons INDEX
freshness, negative_results.json integrity, dataset presence, tracked
config, trunk divergence, docs INDEX coverage, app plans existence) and
reports PASS/WARN/FAIL for each. Exits 1 if any check FAILs.

Fixes are propose-then-ratify (`ssot/DEVELOPMENT_OS.md` §9): this script
never edits repo files, it only reports and suggests remediation commands.

Usage:
    python3 scripts/os_audit.py
    python3 scripts/os_audit.py --repo-root /path/to/repo
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

MAIN_DIVERGENCE_WARN_THRESHOLD = 50
GIT_CHECKOUT_PATTERN = re.compile(r"git checkout\s+([^\s&`]+)")
NEGATIVE_RESULTS_REQUIRED_FIELDS = (
    "id",
    "scope",
    "claim",
    "verdict",
    "evidence",
    "reopen_when",
)
BUILD_LESSONS_INDEX_MODULE = (
    "apps.freeform_usda_meal_analysis_api.scripts.build_lessons_index"
)
FREEFORM_PLANS_RELATIVE_PATH = "apps/freeform_usda_meal_analysis_api/plans/current.md"
BARCODE_PLANS_RELATIVE_PATH = "apps/barcode_api/plans/current.md"
NEGATIVE_RESULTS_RELATIVE_PATH = (
    "apps/freeform_usda_meal_analysis_api/evals/knowledge/negative_results.json"
)
VERIFY_DATASETS_RELATIVE_PATH = "scripts/verify_datasets.py"
SETTINGS_JSON_RELATIVE_PATH = ".claude/settings.json"
DOCS_INDEX_RELATIVE_PATH = "docs/INDEX.md"
GIT_TIMEOUT_SECONDS = 30
SUBPROCESS_TIMEOUT_SECONDS = 120


class Status(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class CheckResult:
    label: str
    name: str
    status: Status
    message: str


def _run(cmd: list[str], cwd: Path, timeout: int) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def check_branch_pointer(repo_root: Path) -> CheckResult:
    label, name = "a", "branch pointer consistency"
    current_md = repo_root / FREEFORM_PLANS_RELATIVE_PATH
    if not current_md.is_file():
        return CheckResult(
            label,
            name,
            Status.WARN,
            f"{FREEFORM_PLANS_RELATIVE_PATH} not found; cannot verify branch pointer",
        )

    text = current_md.read_text(encoding="utf-8")
    matches = GIT_CHECKOUT_PATTERN.findall(text)
    if not matches:
        return CheckResult(
            label,
            name,
            Status.WARN,
            f"no 'git checkout <branch>' pattern found in {FREEFORM_PLANS_RELATIVE_PATH}",
        )

    pointed_branch = matches[0]
    result = _run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=repo_root,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        return CheckResult(
            label,
            name,
            Status.WARN,
            f"could not determine current branch: {result.stderr.strip()}",
        )

    actual_branch = result.stdout.strip()
    if pointed_branch == actual_branch:
        return CheckResult(
            label,
            name,
            Status.PASS,
            f"{FREEFORM_PLANS_RELATIVE_PATH} points at '{pointed_branch}', matches HEAD",
        )

    return CheckResult(
        label,
        name,
        Status.WARN,
        (
            f"{FREEFORM_PLANS_RELATIVE_PATH} says 'git checkout {pointed_branch}' but HEAD is '{actual_branch}'. "
            f"Fix: update the checkout line in {FREEFORM_PLANS_RELATIVE_PATH} to '{actual_branch}', "
            f"or checkout '{pointed_branch}' if that is the intended branch."
        ),
    )


def check_lessons_index_freshness(repo_root: Path) -> CheckResult:
    label, name = "b", "lessons INDEX freshness"
    result = _run(
        [sys.executable, "-m", BUILD_LESSONS_INDEX_MODULE, "--check"],
        cwd=repo_root,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )
    output = (result.stdout + result.stderr).strip()
    regen_hint = f"Regenerate with: python -m {BUILD_LESSONS_INDEX_MODULE}"
    if result.returncode == 0:
        return CheckResult(
            label, name, Status.PASS, output or "lessons INDEX.md is up to date"
        )
    return CheckResult(
        label, name, Status.FAIL, f"{output}\n{regen_hint}" if output else regen_hint
    )


def check_negative_results(repo_root: Path) -> CheckResult:
    label, name = "c", "negative_results.json integrity"
    path = repo_root / NEGATIVE_RESULTS_RELATIVE_PATH
    if not path.is_file():
        return CheckResult(
            label,
            name,
            Status.WARN,
            f"{NEGATIVE_RESULTS_RELATIVE_PATH} not found (expected while a separate lane is authoring it)",
        )

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return CheckResult(
            label,
            name,
            Status.FAIL,
            f"{NEGATIVE_RESULTS_RELATIVE_PATH} is not valid JSON: {exc}",
        )

    entries = data.get("entries") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        return CheckResult(
            label,
            name,
            Status.FAIL,
            f"{NEGATIVE_RESULTS_RELATIVE_PATH} must have a top-level 'entries' list",
        )

    field_violations: list[str] = []
    evidence_violations: list[str] = []
    for index, entry in enumerate(entries):
        entry_id = (
            entry.get("id", f"<index {index}>")
            if isinstance(entry, dict)
            else f"<index {index}>"
        )
        if not isinstance(entry, dict):
            field_violations.append(f"entry {index} is not an object")
            continue
        missing = [f for f in NEGATIVE_RESULTS_REQUIRED_FIELDS if not entry.get(f)]
        if missing:
            field_violations.append(f"{entry_id}: missing/empty field(s) {missing}")
            continue

        evidence = entry["evidence"]
        evidence_paths = evidence if isinstance(evidence, list) else [evidence]
        for evidence_path in evidence_paths:
            if not (repo_root / str(evidence_path)).exists():
                evidence_violations.append(
                    f"{entry_id}: evidence path not found: {evidence_path}"
                )

    if field_violations or evidence_violations:
        lines = [f"{NEGATIVE_RESULTS_RELATIVE_PATH} has violation(s):"]
        lines.extend(f"  - {v}" for v in field_violations + evidence_violations)
        return CheckResult(label, name, Status.FAIL, "\n".join(lines))

    return CheckResult(
        label,
        name,
        Status.PASS,
        f"{len(entries)} entries validated, all required fields present, all evidence paths exist",
    )


def check_datasets(repo_root: Path) -> CheckResult:
    label, name = "d", "dataset presence (verify_datasets.py)"
    script_path = repo_root / VERIFY_DATASETS_RELATIVE_PATH
    if not script_path.is_file():
        return CheckResult(
            label, name, Status.FAIL, f"{VERIFY_DATASETS_RELATIVE_PATH} not found"
        )

    result = _run(
        [sys.executable, str(script_path)],
        cwd=repo_root,
        timeout=SUBPROCESS_TIMEOUT_SECONDS,
    )
    output = (result.stdout + result.stderr).strip()
    status = Status.PASS if result.returncode == 0 else Status.FAIL
    return CheckResult(label, name, status, output)


def check_settings_json_tracked(repo_root: Path) -> CheckResult:
    label, name = "e", ".claude/settings.json tracked by git"
    result = _run(
        ["git", "ls-files", SETTINGS_JSON_RELATIVE_PATH],
        cwd=repo_root,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    if result.stdout.strip():
        return CheckResult(
            label, name, Status.PASS, f"{SETTINGS_JSON_RELATIVE_PATH} is tracked"
        )
    return CheckResult(
        label,
        name,
        Status.FAIL,
        f"{SETTINGS_JSON_RELATIVE_PATH} is NOT tracked by git (git ls-files returned nothing)",
    )


def check_main_divergence(repo_root: Path) -> CheckResult:
    label, name = "f", "divergence from main"
    result = _run(
        ["git", "rev-list", "--count", "main..HEAD"],
        cwd=repo_root,
        timeout=GIT_TIMEOUT_SECONDS,
    )
    if result.returncode != 0:
        return CheckResult(
            label,
            name,
            Status.WARN,
            f"could not compute main..HEAD divergence: {result.stderr.strip()}",
        )

    count = int(result.stdout.strip())
    if count > MAIN_DIVERGENCE_WARN_THRESHOLD:
        return CheckResult(
            label,
            name,
            Status.WARN,
            f"HEAD is {count} commits ahead of main (> {MAIN_DIVERGENCE_WARN_THRESHOLD}); consider integrating into main (DEVELOPMENT_OS.md §11-1)",
        )
    return CheckResult(
        label,
        name,
        Status.PASS,
        f"HEAD is {count} commits ahead of main (<= {MAIN_DIVERGENCE_WARN_THRESHOLD})",
    )


def check_docs_index_coverage(repo_root: Path) -> CheckResult:
    label, name = "g", "root docs INDEX coverage"
    docs_dir = repo_root / "docs"
    index_path = repo_root / DOCS_INDEX_RELATIVE_PATH

    direct_md_files = sorted(
        p.name for p in docs_dir.glob("*.md") if p.is_file() and p.name != "INDEX.md"
    )
    if not index_path.is_file():
        return CheckResult(
            label,
            name,
            Status.WARN,
            f"{DOCS_INDEX_RELATIVE_PATH} not found (expected while a separate lane is authoring it)",
        )

    index_text = index_path.read_text(encoding="utf-8")
    missing = [name_ for name_ in direct_md_files if name_ not in index_text]
    if missing:
        return CheckResult(
            label,
            name,
            Status.WARN,
            f"docs/*.md not listed in {DOCS_INDEX_RELATIVE_PATH}: {missing}",
        )

    return CheckResult(
        label,
        name,
        Status.PASS,
        f"all {len(direct_md_files)} docs/*.md files are listed in {DOCS_INDEX_RELATIVE_PATH}",
    )


def check_app_plans_exist(repo_root: Path) -> CheckResult:
    label, name = "h", "app plans/current.md existence"
    required_paths = (FREEFORM_PLANS_RELATIVE_PATH, BARCODE_PLANS_RELATIVE_PATH)
    missing = [p for p in required_paths if not (repo_root / p).is_file()]
    if missing:
        return CheckResult(
            label, name, Status.FAIL, f"missing plans/current.md: {missing}"
        )
    return CheckResult(label, name, Status.PASS, f"present: {list(required_paths)}")


def run_all_checks(repo_root: Path) -> list[CheckResult]:
    return [
        check_branch_pointer(repo_root),
        check_lessons_index_freshness(repo_root),
        check_negative_results(repo_root),
        check_datasets(repo_root),
        check_settings_json_tracked(repo_root),
        check_main_divergence(repo_root),
        check_docs_index_coverage(repo_root),
        check_app_plans_exist(repo_root),
    ]


def render_report(results: list[CheckResult]) -> str:
    lines = ["os-audit — development OS self-check", "=" * 80]
    for result in results:
        lines.append(f"[{result.label}] {result.status.value:<4} {result.name}")
        for message_line in result.message.splitlines():
            lines.append(f"      {message_line}")
    lines.append("=" * 80)

    pass_count = sum(1 for r in results if r.status == Status.PASS)
    warn_count = sum(1 for r in results if r.status == Status.WARN)
    fail_count = sum(1 for r in results if r.status == Status.FAIL)
    lines.append(f"Summary: PASS={pass_count} WARN={warn_count} FAIL={fail_count}")
    lines.append(
        "Fixes are propose-then-ratify: the agent proposes, the user ratifies before applying (ssot/DEVELOPMENT_OS.md §9)."
    )
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root (default: parent of this script's directory)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = run_all_checks(args.repo_root)
    print(render_report(results))
    return 1 if any(r.status == Status.FAIL for r in results) else 0


if __name__ == "__main__":
    sys.exit(main())
