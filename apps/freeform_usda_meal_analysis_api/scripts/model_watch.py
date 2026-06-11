#!/usr/bin/env python3
"""Watch OpenRouter for new VLM candidates and gate them for PDCA screening.

sync_openrouter_candidates.py の上位スクリプト。次を行う:
1. OpenRouter カタログ全件取得 + image/reasoning フィルタ
2. 現行 baseline からの per-image コスト試算（k1 / k3）と予算ゲート
3. 既テストレジストリ (evals/knowledge/tested_models.json) との突合
4. 前回スナップショットとの差分 (new_since_last)
5. スナップショット JSON + 人間用 Markdown レポート出力
6. (オプション) スクリーニング用 eval config 生成 / model_pricing.json 追記
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.request import urlopen

OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"
HTTP_TIMEOUT_SEC = 30

APP_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = APP_ROOT / "evals" / "knowledge" / "tested_models.json"
DEFAULT_PRICING_PATH = APP_ROOT / "config" / "model_pricing.json"
DEFAULT_BASELINE_PATH = APP_ROOT / "evals" / "baselines" / "current_baseline.json"
DEFAULT_OUTPUT_DIR = APP_ROOT / "evals" / "catalog"

# emit-config に埋め込む repo 相対パス（評価スクリプトは repo root から実行されるため）
BASELINE_FILE_REPO_RELATIVE = (
    "apps/freeform_usda_meal_analysis_api/evals/baselines/current_baseline.json"
)

# per-image コスト内訳の実測シェア。
# 根拠: smoke run 20260611_164346 の flash (in $0.5 / out $3.0 per 1M tokens) 実測 usage 合計
# in 9,503 tokens / out(+reasoning) 11,682 tokens → cost $0.00475 : $0.03505 = 0.119 : 0.881。
# 出力トークンの冗長さはモデル依存のため、これはスクリーニング用の粗い試算
# （正式な予算ゲートは eval の実測 avg_cost_usd）。
INPUT_COST_SHARE = 0.12
OUTPUT_COST_SHARE = 0.88

# self-consistency K=3 運用（本番採用構成）でのコスト試算倍率
SELF_CONSISTENCY_K = 3

DEFAULT_MAX_COST_MULTIPLIER = 10.0
DEFAULT_CONFIG_TOP_N = 8

# 予算ゲート判定ラベル
BUDGET_FITS_K3 = "fits_k3"
BUDGET_FITS_K1 = "fits_k1"
BUDGET_OVER = "over_budget"

TEST_STATUS_TESTED = "tested"
TEST_STATUS_UNTESTED = "untested"

VALID_VERDICTS = frozenset(
    {"adopted", "rejected", "withdrawn", "no_clean_win", "replaced", "untested_blocked"}
)
VALID_SLOTS = frozenset({"vlm", "embedding", "reranker"})
VLM_SLOT = "vlm"

# 除外パターン: :free 版 / openrouter 自身のルータ / エイリアス(~) / -latest エイリアス
DEFAULT_EXCLUDE_PATTERNS: Tuple[str, ...] = (
    r":free$",
    r"^openrouter/",
    r"^~",
    r"-latest",
)

SNAPSHOT_GLOB = "model_watch_*.json"
SNAPSHOT_PREFIX = "model_watch_"

PRICE_ROUND_DECIMALS = 6
COST_ROUND_DECIMALS = 6
FACTOR_ROUND_DECIMALS = 4
BUDGET_ROUND_DECIMALS = 4

MD_OVER_BUDGET_EXCERPT_ROWS = 5

PAIRED_BASELINE_CANDIDATE_NAME = "v13_floor20_flash"
SCREENING_RERANKER_TOP_N = 5
SCREENING_DEFAULTS: Dict[str, object] = {
    "reasoning_effort": "medium",
    "temperature": 0.3,
    "seed": 1,
    "max_tokens": 12288,
    "use_vlm_cache": False,
    "concurrency": 3,
}


class ModelWatchError(RuntimeError):
    """想定外データ・設定不備を明示的に止めるためのエラー。"""


@dataclass
class EvaluatedModel:
    """フィルタ通過後の候補モデル1件分の評価結果。"""

    model_id: str
    raw_model_id: str
    name: str
    prompt_price_per_million_usd: float
    completion_price_per_million_usd: float
    context_length: Optional[int]
    supports_reasoning_control: bool
    cost_factor_vs_baseline: float
    est_cost_per_image_k1_usd: float
    est_cost_per_image_k3_usd: float
    budget_status: str
    test_status: str
    verdict: Optional[str]
    tested_date: Optional[str]
    evidence: Optional[str]
    new_since_last: bool


def parse_price_per_million(value: object) -> Optional[float]:
    """OpenRouter の per-token 価格文字列を USD/1M tokens に変換する。"""
    if value is None:
        return None
    try:
        parsed = float(str(value)) * 1_000_000
    except (TypeError, ValueError):
        return None
    if parsed < 0:
        return None
    return parsed


def has_image_input(model: Dict[str, Any]) -> bool:
    arch = model.get("architecture") or {}
    input_modalities = arch.get("input_modalities") or []
    return "image" in input_modalities


def supports_reasoning_control(model: Dict[str, Any]) -> bool:
    supported = set(model.get("supported_parameters") or [])
    return "reasoning" in supported or "include_reasoning" in supported


def load_openrouter_models() -> List[Dict[str, Any]]:
    with urlopen(OPENROUTER_MODELS_URL, timeout=HTTP_TIMEOUT_SEC) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    models = payload.get("data")
    if not isinstance(models, list) or not models:
        raise ModelWatchError(
            f"OpenRouter API のレスポンスに data 配列がありません: {OPENROUTER_MODELS_URL}"
        )
    return models


def load_json_file(path: Path, description: str) -> Dict[str, Any]:
    if not path.is_file():
        raise ModelWatchError(f"{description} が見つかりません: {path}")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ModelWatchError(
            f"{description} が JSON として不正です: {path} ({exc})"
        ) from exc
    if not isinstance(loaded, dict):
        raise ModelWatchError(
            f"{description} のトップレベルが object ではありません: {path}"
        )
    return loaded


def load_registry_vlm_entries(registry_path: Path) -> Dict[str, Dict[str, str]]:
    """tested_models.json を検証付きで読み、vlm スロットを model_id → entry で返す。"""
    registry = load_json_file(registry_path, "tested_models registry")
    raw_models = registry.get("models")
    if not isinstance(raw_models, list) or not raw_models:
        raise ModelWatchError(f"registry に models 配列がありません: {registry_path}")

    vlm_entries: Dict[str, Dict[str, str]] = {}
    for index, entry in enumerate(raw_models):
        if not isinstance(entry, dict):
            raise ModelWatchError(
                f"registry models[{index}] が object ではありません: {registry_path}"
            )
        for required_key in ("model_id", "slot", "verdict", "date", "evidence"):
            if (
                not isinstance(entry.get(required_key), str)
                or not entry[required_key].strip()
            ):
                raise ModelWatchError(
                    f"registry models[{index}] の {required_key} が不正です"
                    f"（非空文字列が必要）: {registry_path}"
                )
        slot = entry["slot"]
        verdict = entry["verdict"]
        if slot not in VALID_SLOTS:
            raise ModelWatchError(
                f"registry models[{index}] slot={slot!r} は未定義です（許容: {sorted(VALID_SLOTS)}）"
            )
        if verdict not in VALID_VERDICTS:
            raise ModelWatchError(
                f"registry models[{index}] verdict={verdict!r} は未定義です（許容: {sorted(VALID_VERDICTS)}）"
            )
        if slot != VLM_SLOT:
            continue
        model_id = entry["model_id"]
        if model_id in vlm_entries:
            raise ModelWatchError(
                f"registry に vlm model_id が重複しています: {model_id}"
            )
        vlm_entries[model_id] = entry
    if not vlm_entries:
        raise ModelWatchError(
            f"registry に vlm スロットのエントリがありません: {registry_path}"
        )
    return vlm_entries


def load_baseline(baseline_path: Path) -> Tuple[str, float]:
    """current_baseline.json から (model_id, avg_cost_usd) を返す。"""
    baseline = load_json_file(baseline_path, "current baseline")
    model_id = baseline.get("model_id")
    if not isinstance(model_id, str) or not model_id:
        raise ModelWatchError(f"baseline に model_id がありません: {baseline_path}")
    summary = baseline.get("summary")
    if not isinstance(summary, dict):
        raise ModelWatchError(f"baseline に summary がありません: {baseline_path}")
    avg_cost = summary.get("avg_cost_usd")
    if not isinstance(avg_cost, (int, float)) or avg_cost <= 0:
        raise ModelWatchError(
            f"baseline summary.avg_cost_usd が正の数ではありません: {avg_cost!r} ({baseline_path})"
        )
    return model_id, float(avg_cost)


def load_baseline_prices(
    pricing_doc: Dict[str, Any], baseline_model_id: str, pricing_path: Path
) -> Tuple[float, float]:
    """model_pricing.json から baseline モデルの (input, output) 価格 USD/1M を返す。"""
    models = pricing_doc.get("models")
    if not isinstance(models, dict):
        raise ModelWatchError(f"pricing file に models がありません: {pricing_path}")
    entry = models.get(baseline_model_id)
    if not isinstance(entry, dict):
        raise ModelWatchError(
            f"pricing file に baseline モデル {baseline_model_id} のエントリがありません"
            f"（default へのフォールバックは行いません）: {pricing_path}"
        )
    input_price = entry.get("input_price_per_million")
    output_price = entry.get("output_price_per_million")
    if not isinstance(input_price, (int, float)) or input_price <= 0:
        raise ModelWatchError(
            f"baseline input_price_per_million が不正です: {input_price!r}"
        )
    if not isinstance(output_price, (int, float)) or output_price <= 0:
        raise ModelWatchError(
            f"baseline output_price_per_million が不正です: {output_price!r}"
        )
    return float(input_price), float(output_price)


def find_previous_snapshot(output_dir: Path, current_filename: str) -> Optional[Path]:
    """出力ディレクトリ内の最新 model_watch_*.json（今回生成分を除く）を返す。"""
    if not output_dir.is_dir():
        return None
    snapshots = sorted(
        path for path in output_dir.glob(SNAPSHOT_GLOB) if path.name != current_filename
    )
    if not snapshots:
        return None
    return snapshots[-1]


def load_previous_model_ids(snapshot_path: Path) -> frozenset:
    snapshot = load_json_file(snapshot_path, "前回スナップショット")
    candidates = snapshot.get("candidates")
    if not isinstance(candidates, list):
        raise ModelWatchError(
            f"前回スナップショットに candidates 配列がありません: {snapshot_path}"
        )
    model_ids = []
    for item in candidates:
        if not isinstance(item, dict) or not isinstance(item.get("model_id"), str):
            raise ModelWatchError(
                f"前回スナップショットの candidates が不正です: {snapshot_path}"
            )
        model_ids.append(item["model_id"])
    return frozenset(model_ids)


def cost_factor_vs_baseline(
    prompt_price: float,
    completion_price: float,
    baseline_input_price: float,
    baseline_output_price: float,
) -> float:
    """baseline モデル比のコスト係数（input/output シェア加重）。"""
    return (prompt_price / baseline_input_price) * INPUT_COST_SHARE + (
        completion_price / baseline_output_price
    ) * OUTPUT_COST_SHARE


def classify_budget(est_k1: float, est_k3: float, budget_limit: float) -> str:
    if est_k3 <= budget_limit:
        return BUDGET_FITS_K3
    if est_k1 <= budget_limit:
        return BUDGET_FITS_K1
    return BUDGET_OVER


def slugify_model_id(raw_model_id: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", raw_model_id.lower()).strip("_")
    if not slug:
        raise ModelWatchError(f"candidate 名を生成できません: {raw_model_id!r}")
    return slug


def evaluate_models(
    models: List[Dict[str, Any]],
    registry_vlm: Dict[str, Dict[str, str]],
    baseline_cost_usd: float,
    baseline_input_price: float,
    baseline_output_price: float,
    budget_limit: float,
    require_reasoning: bool,
    exclude_patterns: Tuple[str, ...],
    previous_model_ids: Optional[frozenset],
) -> Tuple[List[EvaluatedModel], List[str]]:
    """フィルタ + コスト試算 + 突合 + 差分。戻り値: (評価済み候補, 価格情報なしでスキップしたID)。"""
    evaluated: List[EvaluatedModel] = []
    skipped_no_pricing: List[str] = []

    for model in models:
        raw_id = str(model.get("id", ""))
        if not raw_id:
            raise ModelWatchError(f"OpenRouter モデルに id がありません: {model!r}")
        if any(re.search(pattern, raw_id) for pattern in exclude_patterns):
            continue
        if not has_image_input(model):
            continue
        has_reasoning = supports_reasoning_control(model)
        if require_reasoning and not has_reasoning:
            continue

        pricing = model.get("pricing") or {}
        prompt_price = parse_price_per_million(pricing.get("prompt"))
        completion_price = parse_price_per_million(pricing.get("completion"))
        if prompt_price is None or completion_price is None:
            # 価格未公開(BYOK等)はコスト試算不能のため候補から除外し、件数を明示的に記録する
            skipped_no_pricing.append(raw_id)
            continue

        model_id = f"openrouter:{raw_id}"
        factor = cost_factor_vs_baseline(
            prompt_price, completion_price, baseline_input_price, baseline_output_price
        )
        est_k1 = baseline_cost_usd * factor
        est_k3 = est_k1 * SELF_CONSISTENCY_K

        registry_entry = registry_vlm.get(model_id)
        new_since_last = (
            previous_model_ids is not None and model_id not in previous_model_ids
        )

        evaluated.append(
            EvaluatedModel(
                model_id=model_id,
                raw_model_id=raw_id,
                name=str(model.get("name") or raw_id),
                prompt_price_per_million_usd=round(prompt_price, PRICE_ROUND_DECIMALS),
                completion_price_per_million_usd=round(
                    completion_price, PRICE_ROUND_DECIMALS
                ),
                context_length=model.get("context_length"),
                supports_reasoning_control=has_reasoning,
                cost_factor_vs_baseline=round(factor, FACTOR_ROUND_DECIMALS),
                est_cost_per_image_k1_usd=round(est_k1, COST_ROUND_DECIMALS),
                est_cost_per_image_k3_usd=round(est_k3, COST_ROUND_DECIMALS),
                budget_status=classify_budget(est_k1, est_k3, budget_limit),
                test_status=TEST_STATUS_TESTED
                if registry_entry
                else TEST_STATUS_UNTESTED,
                verdict=registry_entry["verdict"] if registry_entry else None,
                tested_date=registry_entry["date"] if registry_entry else None,
                evidence=registry_entry["evidence"] if registry_entry else None,
                new_since_last=new_since_last,
            )
        )

    evaluated.sort(key=lambda item: (item.est_cost_per_image_k1_usd, item.model_id))
    return evaluated, skipped_no_pricing


def select_untested_in_budget(evaluated: List[EvaluatedModel]) -> List[EvaluatedModel]:
    return [
        item
        for item in evaluated
        if item.test_status == TEST_STATUS_UNTESTED
        and item.budget_status in (BUDGET_FITS_K3, BUDGET_FITS_K1)
    ]


def build_markdown_report(
    date_str: str,
    total_models_received: int,
    baseline_model_id: str,
    baseline_cost_usd: float,
    baseline_input_price: float,
    baseline_output_price: float,
    max_cost_multiplier: float,
    budget_limit: float,
    registry_path: Path,
    registry_vlm: Dict[str, Dict[str, str]],
    previous_snapshot: Optional[Path],
    evaluated: List[EvaluatedModel],
    skipped_no_pricing: List[str],
) -> str:
    untested_in_budget = select_untested_in_budget(evaluated)
    tested = [item for item in evaluated if item.test_status == TEST_STATUS_TESTED]
    over_budget = [item for item in evaluated if item.budget_status == BUDGET_OVER]
    catalog_model_ids = {item.model_id for item in evaluated}
    registry_only = [
        model_id
        for model_id in sorted(registry_vlm)
        if model_id not in catalog_model_ids
    ]

    lines: List[str] = []
    lines.append(f"# Model Watch Report — {date_str}")
    lines.append("")
    lines.append(
        f"- Source: {OPENROUTER_MODELS_URL}（取得 {total_models_received} モデル）"
    )
    lines.append(
        f"- Baseline: `{baseline_model_id}` avg ${baseline_cost_usd:.6f}/image"
        f"（in ${baseline_input_price}/1M, out ${baseline_output_price}/1M）"
    )
    lines.append(
        f"- 予算ゲート: baseline × {max_cost_multiplier} = ${budget_limit:.6f}/image"
        f"（k3 = k1 × {SELF_CONSISTENCY_K} で判定）"
    )
    lines.append(
        f"- コスト試算: factor = (in/base_in)×{INPUT_COST_SHARE} + (out/base_out)×{OUTPUT_COST_SHARE}"
    )
    previous_label = (
        previous_snapshot.name
        if previous_snapshot
        else "なし（初回実行・new判定は省略）"
    )
    lines.append(f"- 前回スナップショット: {previous_label}")
    lines.append(f"- Registry: {registry_path}（vlm {len(registry_vlm)} 件）")
    lines.append(f"- 価格未公開でスキップ: {len(skipped_no_pricing)} 件")
    lines.append("")

    lines.append(f"## Untested × 予算内（est k1 昇順, {len(untested_in_budget)} 件）")
    lines.append("")
    if untested_in_budget:
        lines.append(
            "| model_id | est k1 $/img | est k3 $/img | factor | in $/1M | out $/1M | budget | new |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for item in untested_in_budget:
            new_mark = "NEW" if item.new_since_last else ""
            lines.append(
                f"| `{item.model_id}` | {item.est_cost_per_image_k1_usd:.6f} "
                f"| {item.est_cost_per_image_k3_usd:.6f} | {item.cost_factor_vs_baseline:.4f} "
                f"| {item.prompt_price_per_million_usd} | {item.completion_price_per_million_usd} "
                f"| {item.budget_status} | {new_mark} |"
            )
    else:
        lines.append("該当なし。")
    lines.append("")

    lines.append(f"## Tested（registry 突合, {len(tested)} 件）")
    lines.append("")
    if tested:
        lines.append("| model_id | verdict | date | evidence |")
        lines.append("|---|---|---|---|")
        for item in tested:
            lines.append(
                f"| `{item.model_id}` | {item.verdict} | {item.tested_date} | {item.evidence} |"
            )
    else:
        lines.append("該当なし。")
    lines.append("")

    lines.append(
        f"## Over budget（{len(over_budget)} 件, 安い順抜粋 {MD_OVER_BUDGET_EXCERPT_ROWS} 件）"
    )
    lines.append("")
    if over_budget:
        lines.append("| model_id | est k1 $/img | in $/1M | out $/1M |")
        lines.append("|---|---|---|---|")
        for item in over_budget[:MD_OVER_BUDGET_EXCERPT_ROWS]:
            lines.append(
                f"| `{item.model_id}` | {item.est_cost_per_image_k1_usd:.6f} "
                f"| {item.prompt_price_per_million_usd} | {item.completion_price_per_million_usd} |"
            )
    else:
        lines.append("該当なし。")
    lines.append("")

    lines.append(f"## Registry にあるが現カタログに無い vlm（{len(registry_only)} 件）")
    lines.append("")
    if registry_only:
        for model_id in registry_only:
            entry = registry_vlm[model_id]
            lines.append(f"- `{model_id}` — {entry['verdict']} ({entry['date']})")
    else:
        lines.append("該当なし。")
    lines.append("")
    return "\n".join(lines)


def read_prompt_file(prompt_path: Path) -> str:
    if not prompt_path.is_file():
        raise ModelWatchError(f"--prompt-file が見つかりません: {prompt_path}")
    prompt_text = prompt_path.read_text(encoding="utf-8")
    if not prompt_text.strip():
        raise ModelWatchError(f"--prompt-file が空です: {prompt_path}")
    return prompt_text


def build_screening_config(
    date_str: str,
    untested_in_budget: List[EvaluatedModel],
    config_top_n: int,
    prompt_text: str,
    baseline_model_id: str,
    baseline_cost_usd: float,
    max_cost_multiplier: float,
) -> Dict[str, Any]:
    if config_top_n <= 0:
        raise ModelWatchError(f"--config-top-n は正の整数が必要です: {config_top_n}")
    if not untested_in_budget:
        raise ModelWatchError(
            "untested×予算内のモデルが0件のため、スクリーニングconfigを生成できません"
        )

    selected = untested_in_budget[:config_top_n]
    # k3 運用前提の予算: baseline×multiplier は k3 合計の上限なので、per-call 上限はその 1/K
    per_image_budget = round(
        baseline_cost_usd * max_cost_multiplier / SELF_CONSISTENCY_K,
        BUDGET_ROUND_DECIMALS,
    )

    candidates: List[Dict[str, object]] = [
        {
            "name": PAIRED_BASELINE_CANDIDATE_NAME,
            "vlm_model_id": baseline_model_id,
            "prompt_text": prompt_text,
            "reranker_top_n": SCREENING_RERANKER_TOP_N,
        }
    ]
    for item in selected:
        candidates.append(
            {
                "name": slugify_model_id(item.raw_model_id),
                "vlm_model_id": item.model_id,
                "prompt_text": prompt_text,
                "reranker_top_n": SCREENING_RERANKER_TOP_N,
            }
        )

    model_list = ", ".join(item.model_id for item in selected)
    return {
        "description": (
            f"model_watch 自動生成スクリーニング config ({date_str}): "
            f"untested×予算内の安い順 top {len(selected)} を {PAIRED_BASELINE_CANDIDATE_NAME} と paired 比較。"
            f"候補: {model_list}。採用判定は full50 + Ground truth総カロリー比較が別途必須。"
        ),
        "defaults": dict(SCREENING_DEFAULTS),
        "baseline_file": BASELINE_FILE_REPO_RELATIVE,
        "paired_baseline_candidate": PAIRED_BASELINE_CANDIDATE_NAME,
        "budget": {"max_avg_cost_usd_per_image": per_image_budget},
        "candidates": candidates,
    }


def update_pricing_file(
    pricing_path: Path,
    pricing_doc: Dict[str, Any],
    untested_in_budget: List[EvaluatedModel],
    date_str: str,
) -> List[str]:
    """untested×予算内のうち pricing file に無いモデルを OpenRouter 価格で追記する。"""
    models = pricing_doc.get("models")
    if not isinstance(models, dict):
        raise ModelWatchError(f"pricing file に models がありません: {pricing_path}")

    # 既存キーは "openrouter:vendor/model" / "vendor/model" が混在するため両形式で重複判定する
    existing_normalized = set()
    for key in models:
        normalized = key.lower()
        if normalized.startswith("openrouter:"):
            normalized = normalized[len("openrouter:") :]
        existing_normalized.add(normalized)

    added_ids: List[str] = []
    for item in untested_in_budget:
        if item.raw_model_id.lower() in existing_normalized:
            continue
        models[item.model_id] = {
            "name": f"{item.name} (via OpenRouter)",
            "input_price_per_million": item.prompt_price_per_million_usd,
            "output_price_per_million": item.completion_price_per_million_usd,
            "vision_supported": True,
            "provider": "openrouter",
            "source": "OpenRouter models API",
            "_source": "openrouter_api",
            "_added": date_str,
        }
        added_ids.append(item.model_id)

    if added_ids:
        pricing_path.write_text(
            json.dumps(pricing_doc, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    return added_ids


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Watch OpenRouter for new VLM models, gate by budget, cross-check tested registry"
    )
    parser.add_argument(
        "--registry",
        type=str,
        default=str(DEFAULT_REGISTRY_PATH),
        help="tested_models.json のパス",
    )
    parser.add_argument(
        "--pricing-file",
        type=str,
        default=str(DEFAULT_PRICING_PATH),
        help="model_pricing.json のパス（--update-pricing の書き込み先にもなる）",
    )
    parser.add_argument(
        "--baseline-file",
        type=str,
        default=str(DEFAULT_BASELINE_PATH),
        help="current_baseline.json のパス",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help="スナップショット JSON / Markdown の出力ディレクトリ",
    )
    parser.add_argument(
        "--max-cost-multiplier",
        type=float,
        default=DEFAULT_MAX_COST_MULTIPLIER,
        help="予算ゲート: baseline avg_cost_usd × この倍率を per-image 上限とする",
    )
    parser.add_argument(
        "--include-non-reasoning",
        action="store_true",
        help="reasoning 制御非対応モデルも候補に含める",
    )
    parser.add_argument(
        "--emit-config",
        type=str,
        default=None,
        help="untested×予算内 top-N でスクリーニング用 eval config JSON を生成するパス",
    )
    parser.add_argument(
        "--config-top-n",
        type=int,
        default=DEFAULT_CONFIG_TOP_N,
        help="--emit-config に含める untested×予算内モデル数（est cost 昇順）",
    )
    parser.add_argument(
        "--prompt-file",
        type=str,
        default=None,
        help="--emit-config の prompt_text に使うテキストファイル（--emit-config 時は必須）",
    )
    parser.add_argument(
        "--update-pricing",
        action="store_true",
        help="untested×予算内モデルのうち pricing file に無いものを OpenRouter 価格で追記",
    )
    return parser


def main() -> int:
    parser = build_arg_parser()
    args = parser.parse_args()

    if args.emit_config and not args.prompt_file:
        parser.error("--emit-config を使う場合は --prompt-file が必須です")

    registry_path = Path(args.registry)
    pricing_path = Path(args.pricing_file)
    baseline_path = Path(args.baseline_file)
    output_dir = Path(args.output_dir)
    if args.max_cost_multiplier <= 0:
        parser.error(
            f"--max-cost-multiplier は正の数が必要です: {args.max_cost_multiplier}"
        )

    # emit-config の prompt はネットワークアクセス前に検証する（失敗を早く出す）
    prompt_text: Optional[str] = None
    if args.emit_config:
        prompt_text = read_prompt_file(Path(args.prompt_file))

    registry_vlm = load_registry_vlm_entries(registry_path)
    baseline_model_id, baseline_cost_usd = load_baseline(baseline_path)
    pricing_doc = load_json_file(pricing_path, "model pricing file")
    baseline_input_price, baseline_output_price = load_baseline_prices(
        pricing_doc, baseline_model_id, pricing_path
    )
    budget_limit = baseline_cost_usd * args.max_cost_multiplier

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    snapshot_filename = f"{SNAPSHOT_PREFIX}{now.strftime('%Y%m%d')}.json"
    previous_snapshot = find_previous_snapshot(output_dir, snapshot_filename)
    previous_model_ids = (
        load_previous_model_ids(previous_snapshot) if previous_snapshot else None
    )

    models = load_openrouter_models()
    evaluated, skipped_no_pricing = evaluate_models(
        models=models,
        registry_vlm=registry_vlm,
        baseline_cost_usd=baseline_cost_usd,
        baseline_input_price=baseline_input_price,
        baseline_output_price=baseline_output_price,
        budget_limit=budget_limit,
        require_reasoning=not args.include_non_reasoning,
        exclude_patterns=DEFAULT_EXCLUDE_PATTERNS,
        previous_model_ids=previous_model_ids,
    )

    untested_in_budget = select_untested_in_budget(evaluated)
    tested = [item for item in evaluated if item.test_status == TEST_STATUS_TESTED]
    over_budget = [item for item in evaluated if item.budget_status == BUDGET_OVER]
    new_models = [item for item in evaluated if item.new_since_last]

    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = output_dir / snapshot_filename
    report_path = output_dir / f"{SNAPSHOT_PREFIX}{now.strftime('%Y%m%d')}.md"

    snapshot = {
        "generated_at_utc": now.isoformat(),
        "source": OPENROUTER_MODELS_URL,
        "baseline": {
            "model_id": baseline_model_id,
            "avg_cost_usd_per_image": baseline_cost_usd,
            "input_price_per_million_usd": baseline_input_price,
            "output_price_per_million_usd": baseline_output_price,
            "baseline_file": str(baseline_path),
        },
        "cost_model": {
            "input_cost_share": INPUT_COST_SHARE,
            "output_cost_share": OUTPUT_COST_SHARE,
            "self_consistency_k": SELF_CONSISTENCY_K,
            "max_cost_multiplier": args.max_cost_multiplier,
            "budget_limit_usd_per_image": round(budget_limit, COST_ROUND_DECIMALS),
        },
        "filters": {
            "require_image": True,
            "require_reasoning": not args.include_non_reasoning,
            "exclude_patterns": list(DEFAULT_EXCLUDE_PATTERNS),
        },
        "registry_file": str(registry_path),
        "previous_snapshot": str(previous_snapshot) if previous_snapshot else None,
        "total_models_received": len(models),
        "skipped_no_pricing_count": len(skipped_no_pricing),
        "skipped_no_pricing_ids": sorted(skipped_no_pricing),
        "counts": {
            "evaluated": len(evaluated),
            "untested_in_budget": len(untested_in_budget),
            "tested": len(tested),
            "over_budget": len(over_budget),
            "new_since_last": len(new_models),
        },
        "candidates": [asdict(item) for item in evaluated],
    }
    snapshot_path.write_text(
        json.dumps(snapshot, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    report = build_markdown_report(
        date_str=date_str,
        total_models_received=len(models),
        baseline_model_id=baseline_model_id,
        baseline_cost_usd=baseline_cost_usd,
        baseline_input_price=baseline_input_price,
        baseline_output_price=baseline_output_price,
        max_cost_multiplier=args.max_cost_multiplier,
        budget_limit=budget_limit,
        registry_path=registry_path,
        registry_vlm=registry_vlm,
        previous_snapshot=previous_snapshot,
        evaluated=evaluated,
        skipped_no_pricing=skipped_no_pricing,
    )
    report_path.write_text(report, encoding="utf-8")

    print(f"Snapshot: {snapshot_path}")
    print(f"Report:   {report_path}")
    print(
        f"Models received: {len(models)} / evaluated: {len(evaluated)} "
        f"(skipped_no_pricing: {len(skipped_no_pricing)})"
    )
    print(
        f"untested_in_budget: {len(untested_in_budget)} / tested: {len(tested)} "
        f"/ over_budget: {len(over_budget)} / new_since_last: {len(new_models)}"
    )

    if args.emit_config:
        if prompt_text is None:
            raise ModelWatchError("prompt_text が未ロードです（内部状態エラー）")
        config = build_screening_config(
            date_str=date_str,
            untested_in_budget=untested_in_budget,
            config_top_n=args.config_top_n,
            prompt_text=prompt_text,
            baseline_model_id=baseline_model_id,
            baseline_cost_usd=baseline_cost_usd,
            max_cost_multiplier=args.max_cost_multiplier,
        )
        config_path = Path(args.emit_config)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        config_path.write_text(
            json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(
            f"Screening config: {config_path} (candidates: {len(config['candidates'])})"
        )

    if args.update_pricing:
        added_ids = update_pricing_file(
            pricing_path=pricing_path,
            pricing_doc=pricing_doc,
            untested_in_budget=untested_in_budget,
            date_str=date_str,
        )
        if added_ids:
            print(f"Pricing updated: {pricing_path} (+{len(added_ids)} models)")
            for model_id in added_ids:
                print(f"  + {model_id}")
        else:
            print(f"Pricing unchanged: 追記対象なし ({pricing_path})")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ModelWatchError as exc:
        raise SystemExit(f"ERROR: {exc}")
