#!/usr/bin/env python3
"""Pooled paired rotation analysis across evaluation sets.

複数の評価セット（frozen-50 / NVReal-104 / N5k-100 / JFB-100 など）の
run summary（`evals/runs/<ts>/summary.json` の `per_image_calorie_errors`）から、
candidate vs baseline の per-image paired delta（candidate_abs_err − baseline_abs_err）
をセット横断で単純連結（= set重みは画像数比例）し、

- per-set: ΔMAE(pt) + paired BCa 95% CI + sign-flip permutation p値
- pooled: ΔMAE + BCa 95% CI + permutation p値
- 方向一貫性: 各setのΔ符号と全set同方向か

を計算して採用判定ヒントを出す。

過去の教訓（E1 v18, lesson 20260606_e1_v18_identity_separation_*）:
pooled ΔMAE が有意に負（−6.21pt CI[−12,−1]）でも、set間でΔ符号が flip
（+0.46 / −1.69 / −14.26）していれば SET-SPECIFIC であり一般化しない。
pooled 有意性と方向一貫性の両方を必ず見ること。

注意:
- 同一画像indexでもrun（セット）が違えば別サンプルとして扱う。
- pairing は両candidateが成功した共通画像のみ（`per_image_calorie_errors` は
  成功画像のみ保持しているため、キーの共通部分 = 共通成功画像）。
- delta の順序は candidate 側の評価順（dictの挿入順）を保持するため、
  同一 seed なら run_pdca_batch_eval が summary に保存した paired CI を再現する。

Usage:
    PYTHONPATH=<repo_root> python -m \
        apps.freeform_usda_meal_analysis_api.scripts.pool_paired_rotation \
        --runs evals/runs/<ts1> evals/runs/<ts2> ... \
        --candidate v18 --baseline-candidate v13 \
        --labels frozen-50 NVReal-104 ...
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, NoReturn, Optional, Tuple

from .run_pdca_batch_eval import (
    DEFAULT_BOOTSTRAP_RESAMPLES,
    DEFAULT_BOOTSTRAP_SEED,
    PROJECT_ROOT,
    bootstrap_mean_ci,
    sign_flip_pvalue,
)

DEFAULT_OUTPUT_ROOT = (
    PROJECT_ROOT / "apps" / "freeform_usda_meal_analysis_api" / "evals" / "runs"
)
OUTPUT_DIR_PREFIX = "pooled_"
OUTPUT_BASENAME = "pooled_summary"
ROUND_DIGITS = 4
# permutation p値の seed は run_pdca_batch_eval と同じく CI seed + 1（独立ストリーム）
PVALUE_SEED_OFFSET = 1

VERDICT_POOLED_WIN = "POOLED WIN (direction-consistent)"
VERDICT_SET_SPECIFIC = "SET-SPECIFIC (caution: not generalizing)"
VERDICT_NO_WIN = "NO WIN"

DIRECTION_IMPROVE = "improve(-)"
DIRECTION_REGRESS = "regress(+)"
DIRECTION_FLAT = "flat(0)"


def fail(message: str) -> NoReturn:
    """Fallbackせず明確なエラーで停止する。"""
    raise SystemExit(f"ERROR: {message}")


def resolve_summary_path(raw: str) -> Path:
    """run dir または summary.json パスを summary.json の絶対パスに解決する。"""
    path = Path(raw)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    if path.is_dir():
        path = path / "summary.json"
    if not path.exists():
        fail(f"run '{raw}': summary.json が見つからない（解決先: {path}）")
    return path


def load_run_summary(path: Path) -> Dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        fail(f"{path}: JSONパースに失敗: {exc}")
    if not isinstance(data, dict) or not isinstance(data.get("results"), list):
        fail(
            f"{path}: 'results' 配列がない"
            "（run_pdca_batch_eval / merge_pdca_runs が生成した summary.json か確認）"
        )
    return data


def find_candidate_entry(
    summary: Dict[str, Any], candidate_name: str, path: Path
) -> Dict[str, Any]:
    """run summary 内の candidate エントリを name で一意に特定する。"""
    results: List[Dict[str, Any]] = summary["results"]
    matches = [r for r in results if r.get("summary", {}).get("name") == candidate_name]
    if not matches:
        available = sorted(str(r.get("summary", {}).get("name")) for r in results)
        fail(
            f"{path}: candidate '{candidate_name}' が見つからない"
            f"（このrunの candidates: {available}）"
        )
    if len(matches) > 1:
        fail(
            f"{path}: candidate '{candidate_name}' が {len(matches)} 件あり"
            "一意に特定できない"
        )
    return matches[0]


def extract_per_image_errors(
    entry: Dict[str, Any], candidate_name: str, path: Path
) -> Dict[str, float]:
    """candidate エントリから per-image abs%誤差 dict（成功画像のみ）を取り出す。"""
    errors = entry.get("per_image_calorie_errors")
    if errors is None:
        fail(
            f"{path}: candidate '{candidate_name}' に per_image_calorie_errors がない"
            "（古い形式のrun。run_pdca_batch_eval を再実行して summary を作り直すか、"
            "このrunを --runs から除外する）"
        )
    if not isinstance(errors, dict) or not errors:
        fail(
            f"{path}: candidate '{candidate_name}' の per_image_calorie_errors が"
            "空または不正（成功画像が1件もない）"
        )
    return {str(image): float(err) for image, err in errors.items()}


def paired_deltas_from_errors(
    candidate_errors: Dict[str, float], baseline_errors: Dict[str, float]
) -> Tuple[List[float], List[str]]:
    """共通成功画像の per-image paired delta（candidate − baseline）。

    candidate 側の評価順（dict挿入順）を保持する。これにより同一 seed で
    run_pdca_batch_eval が保存した paired BCa CI と一致する。
    """
    images = [img for img in candidate_errors if img in baseline_errors]
    deltas = [candidate_errors[img] - baseline_errors[img] for img in images]
    return deltas, images


def candidate_side_metrics(entry: Dict[str, Any]) -> Dict[str, Optional[float]]:
    """summary から片側（candidate or baseline）の表示用メトリクスを抽出する。

    signed bias（decomposed.signed_mean_error_percent）は summary にあれば載せる
    （任意項目。無い場合は None）。
    """
    summ: Dict[str, Any] = entry["summary"]
    decomposed = summ.get("decomposed") or {}
    return {
        "calorie_mae_percent": summ.get("calorie_mae_percent"),
        "signed_mean_error_percent": decomposed.get("signed_mean_error_percent"),
        "avg_latency_sec": summ.get("avg_latency_sec"),
        "avg_cost_usd": summ.get("avg_cost_usd"),
        "success_count": summ.get("success_count"),
        "failure_count": summ.get("failure_count"),
    }


def mean(values: List[float]) -> float:
    return sum(values) / len(values)


def delta_direction(mean_delta: float) -> str:
    if mean_delta < 0.0:
        return DIRECTION_IMPROVE
    if mean_delta > 0.0:
        return DIRECTION_REGRESS
    return DIRECTION_FLAT


def classify_verdict(
    pooled_ci_high: float, set_mean_deltas: List[float]
) -> Tuple[str, List[str]]:
    """判定ヒント。pooled CI と方向一貫性の組み合わせで分類する。

    - pooled CI 全体 < 0 かつ 全setのΔ < 0 → POOLED WIN (direction-consistent)
    - pooled CI 全体 < 0 だが set間で符号 flip → SET-SPECIFIC（一般化しない疑い）
    - それ以外 → NO WIN
    """
    pooled_ci_negative = pooled_ci_high < 0.0
    all_negative = all(d < 0.0 for d in set_mean_deltas)
    signs = ", ".join(f"{d:+.2f}" for d in set_mean_deltas)
    if pooled_ci_negative and all_negative:
        return VERDICT_POOLED_WIN, [
            "pooled BCa 95% CI 全体が 0 未満",
            f"全setでΔMAEが負（{signs}）= 方向一貫",
        ]
    if pooled_ci_negative:
        return VERDICT_SET_SPECIFIC, [
            f"pooled BCa 95% CI 全体は 0 未満だが、set間でΔ符号が flip（{signs}）",
            "特定セットの分布に固有の効果の疑い。一般化しない可能性が高い"
            "（教訓: E1 v18 は pooled −6.21pt でも REJECT）",
        ]
    return VERDICT_NO_WIN, [
        f"pooled BCa 95% CI が 0 を跨ぐか正側（ci_high={pooled_ci_high:+.4f}）",
    ]


def format_optional(value: Optional[float], fmt: str) -> str:
    return format(value, fmt) if value is not None else "-"


def format_pair(
    baseline_value: Optional[float], candidate_value: Optional[float], fmt: str
) -> str:
    return (
        f"{format_optional(baseline_value, fmt)} → "
        f"{format_optional(candidate_value, fmt)}"
    )


def build_markdown(payload: Dict[str, Any]) -> str:
    lines: List[str] = []
    lines.append(
        f"# Pooled paired rotation: {payload['candidate']} vs "
        f"{payload['baseline_candidate']} (baseline)"
    )
    lines.append("")
    lines.append(f"- generated_at: {payload['generated_at']}")
    lines.append(
        f"- bootstrap: BCa, {payload['bootstrap_resamples']} resamples, "
        f"seed {payload['bootstrap_seed']} "
        f"(permutation seed {payload['bootstrap_seed'] + PVALUE_SEED_OFFSET})"
    )
    lines.append(
        "- 重み付け: **set重み=画像数比例**（per-image delta の単純連結。"
        "セット均等重みではない）"
    )
    lines.append(
        "- 同一画像indexでもrun（セット）が違えば別サンプルとして扱う。"
        "pairing は両candidate共通の成功画像のみ。"
    )
    lines.append("")
    lines.append(
        "| set | run | n_paired | baseline MAE% | candidate MAE% | ΔMAE(pt) "
        "| paired 95% BCa CI | p(sign-flip) | signed bias b→c | "
        "latency b→c (s) | cost b→c ($) |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for s in payload["sets"]:
        ci = s["paired"]["ci"]
        base = s["baseline"]
        cand = s["candidate"]
        lines.append(
            f"| {s['label']} "
            f"| {Path(s['run']).parent.name} "
            f"| {s['n_paired']} "
            f"| {format_optional(base['calorie_mae_percent'], '.2f')} "
            f"| {format_optional(cand['calorie_mae_percent'], '.2f')} "
            f"| {s['paired']['delta_mae_point']:+.2f} "
            f"| [{ci['ci_low']:+.2f}, {ci['ci_high']:+.2f}] "
            f"| {s['paired']['sign_flip_pvalue']} "
            f"| {format_pair(base['signed_mean_error_percent'], cand['signed_mean_error_percent'], '+.2f')} "
            f"| {format_pair(base['avg_latency_sec'], cand['avg_latency_sec'], '.2f')} "
            f"| {format_pair(base['avg_cost_usd'], cand['avg_cost_usd'], '.6f')} |"
        )
    pooled = payload["pooled"]
    pooled_ci = pooled["ci"]
    lines.append(
        f"| **POOLED** | — | {pooled['n']} "
        f"| {pooled['baseline_mae_on_paired']:.2f} "
        f"| {pooled['candidate_mae_on_paired']:.2f} "
        f"| **{pooled['delta_mae_point']:+.2f}** "
        f"| [{pooled_ci['ci_low']:+.2f}, {pooled_ci['ci_high']:+.2f}] "
        f"| {pooled['sign_flip_pvalue']} | — | — | — |"
    )
    lines.append("")
    lines.append("## Direction consistency")
    direction = payload["direction_consistency"]
    per_set = ", ".join(
        f"{s['label']}: {s['paired']['direction']}" for s in payload["sets"]
    )
    lines.append(f"- per-set Δ direction: {per_set}")
    lines.append(f"- all_same_direction: {direction['all_same_direction']}")
    lines.append("")
    lines.append("## Verdict")
    lines.append(f"**{payload['verdict']['verdict']}**")
    for reason in payload["verdict"]["reasons"]:
        lines.append(f"- {reason}")
    lines.append("")
    return "\n".join(lines)


def resolve_output_paths(output_arg: Optional[str]) -> Tuple[Path, Path]:
    """--output から (json_path, md_path) を決める。

    - 未指定: evals/runs/pooled_<YYYYMMDD_HHMMSS>/pooled_summary.{json,md}
    - *.json 指定: そのパスにJSON、同stemの .md を併置
    - それ以外: ディレクトリとみなし pooled_summary.{json,md} を生成
    """
    if output_arg is None:
        out_dir = DEFAULT_OUTPUT_ROOT / (
            OUTPUT_DIR_PREFIX + datetime.now().strftime("%Y%m%d_%H%M%S")
        )
        return out_dir / f"{OUTPUT_BASENAME}.json", out_dir / f"{OUTPUT_BASENAME}.md"
    path = Path(output_arg)
    if not path.is_absolute():
        path = (PROJECT_ROOT / path).resolve()
    if path.suffix == ".json":
        return path, path.with_suffix(".md")
    return path / f"{OUTPUT_BASENAME}.json", path / f"{OUTPUT_BASENAME}.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "クロスデータセット pooled paired 解析: 複数runの summary.json の "
            "per_image_calorie_errors から candidate vs baseline の paired delta を"
            "プールし、pooled ΔMAE + BCa 95% CI + permutation p値 + 方向一貫性で"
            "採用判定ヒントを出す。"
        )
    )
    parser.add_argument(
        "--runs",
        nargs="+",
        required=True,
        help=(
            "各評価セットの run dir または summary.json パス（1run = 1セット）。"
            "相対パスはrepo rootからの解決"
        ),
    )
    parser.add_argument(
        "--candidate",
        required=True,
        help="評価対象 candidate の name（全runに存在すること）",
    )
    parser.add_argument(
        "--baseline-candidate",
        required=True,
        help="比較基準 candidate の name（全runに存在すること）",
    )
    parser.add_argument(
        "--labels",
        nargs="+",
        default=None,
        help="各runの表示名（--runs と同数）。未指定は run dir 名",
    )
    parser.add_argument(
        "--bootstrap-resamples",
        type=int,
        default=DEFAULT_BOOTSTRAP_RESAMPLES,
        help="BCa bootstrap / permutation の resample 数",
    )
    parser.add_argument(
        "--bootstrap-seed",
        type=int,
        default=DEFAULT_BOOTSTRAP_SEED,
        help="決定的 resampling の seed（permutation は seed+1）",
    )
    parser.add_argument(
        "--output",
        default=None,
        help=(
            "出力先（*.json パス or ディレクトリ）。"
            "未指定は evals/runs/pooled_<ts>/pooled_summary.{json,md}"
        ),
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    candidate_name: str = args.candidate
    baseline_name: str = args.baseline_candidate
    if candidate_name == baseline_name:
        fail("--candidate と --baseline-candidate が同一")

    run_args: List[str] = args.runs
    labels: Optional[List[str]] = args.labels
    if labels is not None and len(labels) != len(run_args):
        fail(
            f"--labels の数（{len(labels)}）が --runs の数（{len(run_args)}）と"
            "一致しない"
        )

    resamples = int(args.bootstrap_resamples)
    if resamples <= 0:
        fail(f"--bootstrap-resamples は正の整数が必要（指定値: {resamples}）")
    seed = int(args.bootstrap_seed)

    set_payloads: List[Dict[str, Any]] = []
    pooled_deltas: List[float] = []
    pooled_candidate_errors: List[float] = []
    pooled_baseline_errors: List[float] = []
    set_mean_deltas: List[float] = []

    for i, run_arg in enumerate(run_args):
        summary_path = resolve_summary_path(run_arg)
        run_summary = load_run_summary(summary_path)
        label = labels[i] if labels is not None else summary_path.parent.name

        candidate_entry = find_candidate_entry(
            run_summary, candidate_name, summary_path
        )
        baseline_entry = find_candidate_entry(run_summary, baseline_name, summary_path)
        candidate_errors = extract_per_image_errors(
            candidate_entry, candidate_name, summary_path
        )
        baseline_errors = extract_per_image_errors(
            baseline_entry, baseline_name, summary_path
        )

        deltas, common_images = paired_deltas_from_errors(
            candidate_errors, baseline_errors
        )
        if not deltas:
            fail(
                f"{summary_path}: '{candidate_name}' と '{baseline_name}' の"
                "共通成功画像が0件で paired delta を作れない"
            )

        set_ci = bootstrap_mean_ci(deltas, n_resamples=resamples, seed=seed)
        if set_ci is None:
            fail(f"{summary_path}: paired delta の BCa CI 計算に失敗（n=0）")
        set_p = sign_flip_pvalue(
            deltas, n_resamples=resamples, seed=seed + PVALUE_SEED_OFFSET
        )

        mean_delta = mean(deltas)
        set_mean_deltas.append(mean_delta)
        pooled_deltas.extend(deltas)
        pooled_candidate_errors.extend(candidate_errors[img] for img in common_images)
        pooled_baseline_errors.extend(baseline_errors[img] for img in common_images)

        set_payloads.append(
            {
                "label": label,
                "run": str(summary_path),
                "n_paired": len(deltas),
                "n_candidate_success": len(candidate_errors),
                "n_baseline_success": len(baseline_errors),
                "baseline": candidate_side_metrics(baseline_entry),
                "candidate": candidate_side_metrics(candidate_entry),
                "paired": {
                    "delta_mae_point": round(mean_delta, ROUND_DIGITS),
                    "baseline_mae_on_paired": round(
                        mean([baseline_errors[img] for img in common_images]),
                        ROUND_DIGITS,
                    ),
                    "candidate_mae_on_paired": round(
                        mean([candidate_errors[img] for img in common_images]),
                        ROUND_DIGITS,
                    ),
                    "ci": set_ci,
                    "sign_flip_pvalue": set_p,
                    "direction": delta_direction(mean_delta),
                },
            }
        )

    pooled_ci = bootstrap_mean_ci(pooled_deltas, n_resamples=resamples, seed=seed)
    if pooled_ci is None:
        fail("pooled delta の BCa CI 計算に失敗（n=0）")
    pooled_p = sign_flip_pvalue(
        pooled_deltas, n_resamples=resamples, seed=seed + PVALUE_SEED_OFFSET
    )
    pooled_mean = mean(pooled_deltas)

    directions = [s["paired"]["direction"] for s in set_payloads]
    all_same_direction = len(set(directions)) == 1 and directions[0] != DIRECTION_FLAT
    verdict, reasons = classify_verdict(float(pooled_ci["ci_high"]), set_mean_deltas)

    payload: Dict[str, Any] = {
        "generated_at": datetime.now().isoformat(),
        "tool": "pool_paired_rotation",
        "candidate": candidate_name,
        "baseline_candidate": baseline_name,
        "bootstrap_resamples": resamples,
        "bootstrap_seed": seed,
        "weighting": (
            "per-image concatenation (set weight proportional to paired image count)"
        ),
        "sets": set_payloads,
        "pooled": {
            "n": len(pooled_deltas),
            "delta_mae_point": round(pooled_mean, ROUND_DIGITS),
            "baseline_mae_on_paired": round(mean(pooled_baseline_errors), ROUND_DIGITS),
            "candidate_mae_on_paired": round(
                mean(pooled_candidate_errors), ROUND_DIGITS
            ),
            "ci": pooled_ci,
            "sign_flip_pvalue": pooled_p,
        },
        "direction_consistency": {
            "set_directions": directions,
            "set_mean_deltas": [round(d, ROUND_DIGITS) for d in set_mean_deltas],
            "all_same_direction": all_same_direction,
        },
        "verdict": {"verdict": verdict, "reasons": reasons},
    }

    json_path, md_path = resolve_output_paths(args.output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_text = build_markdown(payload)
    md_path.write_text(md_text, encoding="utf-8")

    print(md_text)
    print(f"Saved pooled summary: {json_path}")
    print(f"Saved pooled markdown: {md_path}")


if __name__ == "__main__":
    main()
