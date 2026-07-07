#!/usr/bin/env python3
"""Verify local presence of dataset assets registered in `ssot/datasets.json`.

Machine-verifiable counterpart to the human SSOT `ssot/DATASETS.md`. Used by
`scripts/os_audit.py` and by fresh-machine setup flows (`/os-audit`,
`docs/MACHINE_MIGRATION.md`).

Each asset in `ssot/datasets.json` is one of:
  - `kind: "file"`      -> the `path` must exist as a regular file.
  - `kind: "image_dir"` -> the `path` must exist as a directory and contain
    at least `min_count` files matching `glob` (searched recursively, since
    several registered sets store their files under a nested `images/`
    subdirectory rather than directly under `path`).

No fallback: a malformed `datasets.json` (missing keys, unknown `kind`) is a
hard error, never silently skipped.

Usage:
    python3 scripts/verify_datasets.py
    python3 scripts/verify_datasets.py --lenient   # exit 0 even if required assets are missing
    python3 scripts/verify_datasets.py --repo-root /path/to/repo
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

DEFAULT_DATASETS_JSON_RELATIVE_PATH = "ssot/datasets.json"
KIND_FILE = "file"
KIND_IMAGE_DIR = "image_dir"
KNOWN_KINDS = frozenset({KIND_FILE, KIND_IMAGE_DIR})


class DatasetRegistryError(RuntimeError):
    """Raised for a malformed datasets.json (no silent skip)."""


class AssetStatus(str, Enum):
    OK = "OK"
    MISSING = "MISSING"
    SHORT = "SHORT"


@dataclass
class AssetResult:
    asset_id: str
    kind: str
    status: AssetStatus
    detail: str
    required_for: list[str]
    note: str


def _require_keys(entry: dict, keys: tuple[str, ...], context: str) -> None:
    missing = [key for key in keys if key not in entry]
    if missing:
        raise DatasetRegistryError(
            f"datasets.json asset {context!r} is missing required key(s): {missing}"
        )


def load_registry(datasets_json_path: Path) -> list[dict]:
    if not datasets_json_path.is_file():
        raise DatasetRegistryError(f"datasets.json not found: {datasets_json_path}")
    try:
        raw = json.loads(datasets_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise DatasetRegistryError(
            f"failed to parse {datasets_json_path}: {exc}"
        ) from exc

    if "assets" not in raw or not isinstance(raw["assets"], list):
        raise DatasetRegistryError(
            f"{datasets_json_path} must have a top-level 'assets' list"
        )
    return raw["assets"]


def evaluate_asset(entry: dict, repo_root: Path) -> AssetResult:
    _require_keys(
        entry, ("id", "path", "kind", "required_for"), entry.get("id", "<unknown>")
    )
    asset_id = entry["id"]
    kind = entry["kind"]
    required_for = entry["required_for"]
    note = entry.get("note", "")

    if kind not in KNOWN_KINDS:
        raise DatasetRegistryError(
            f"asset {asset_id!r} has unknown kind {kind!r} (expected one of {sorted(KNOWN_KINDS)})"
        )
    if not isinstance(required_for, list):
        raise DatasetRegistryError(f"asset {asset_id!r} 'required_for' must be a list")

    target = repo_root / entry["path"]

    if kind == KIND_FILE:
        if target.is_file():
            return AssetResult(
                asset_id, kind, AssetStatus.OK, f"exists ({target})", required_for, note
            )
        return AssetResult(
            asset_id,
            kind,
            AssetStatus.MISSING,
            f"not found ({target})",
            required_for,
            note,
        )

    # kind == KIND_IMAGE_DIR
    _require_keys(entry, ("min_count", "glob"), asset_id)
    min_count = entry["min_count"]
    glob_pattern = entry["glob"]
    if not isinstance(min_count, int):
        raise DatasetRegistryError(f"asset {asset_id!r} 'min_count' must be an int")

    if not target.is_dir():
        return AssetResult(
            asset_id,
            kind,
            AssetStatus.MISSING,
            f"directory not found ({target})",
            required_for,
            note,
        )

    count = sum(1 for _ in target.rglob(glob_pattern))
    if count >= min_count:
        return AssetResult(
            asset_id,
            kind,
            AssetStatus.OK,
            f"{count} files matching '{glob_pattern}' (>= {min_count})",
            required_for,
            note,
        )
    return AssetResult(
        asset_id,
        kind,
        AssetStatus.SHORT,
        f"{count} files matching '{glob_pattern}' (< {min_count})",
        required_for,
        note,
    )


def render_report(results: list[AssetResult]) -> str:
    header = f"{'id':<28} {'kind':<11} {'status':<8} {'required_for':<28} detail"
    separator = "-" * len(header)
    lines = ["Dataset verification (ssot/datasets.json)", separator, header, separator]
    for result in results:
        required_for_str = (
            ",".join(result.required_for) if result.required_for else "(none)"
        )
        lines.append(
            f"{result.asset_id:<28} {result.kind:<11} {result.status.value:<8} {required_for_str:<28} {result.detail}"
        )
    lines.append(separator)

    ok_count = sum(1 for r in results if r.status == AssetStatus.OK)
    missing_count = sum(1 for r in results if r.status == AssetStatus.MISSING)
    short_count = sum(1 for r in results if r.status == AssetStatus.SHORT)
    lines.append(
        f"Summary: {len(results)} assets checked | OK={ok_count} MISSING={missing_count} SHORT={short_count}"
    )

    required_broken = [
        r for r in results if r.required_for and r.status != AssetStatus.OK
    ]
    if required_broken:
        broken_ids = ", ".join(
            f"{r.asset_id}({r.status.value})" for r in required_broken
        )
        lines.append(f"Required-and-broken: {broken_ids}")
    else:
        lines.append("Required-and-broken: none")

    optional_broken = [
        r for r in results if not r.required_for and r.status != AssetStatus.OK
    ]
    if optional_broken:
        optional_ids = ", ".join(
            f"{r.asset_id}({r.status.value})" for r in optional_broken
        )
        lines.append(f"WARN (optional, no required_for): {optional_ids}")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Repository root to resolve asset paths against (default: parent of this script's directory)",
    )
    parser.add_argument(
        "--lenient",
        action="store_true",
        help="Always exit 0 even if required assets are MISSING/SHORT (for fresh-machine setup flows)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root: Path = args.repo_root
    datasets_json_path = repo_root / DEFAULT_DATASETS_JSON_RELATIVE_PATH

    assets = load_registry(datasets_json_path)
    results = [evaluate_asset(entry, repo_root) for entry in assets]

    print(render_report(results))

    if args.lenient:
        return 0

    required_broken = any(
        r.required_for and r.status != AssetStatus.OK for r in results
    )
    return 1 if required_broken else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except DatasetRegistryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(2)
