#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
API経由での栄養素 vs VLM Label栄養素の比較 (全50画像)
Markdownレポート生成

Usage:
    # デフォルトモデル (DeepInfra Qwen3-VL-30B-A3B-Thinking)
    python test_scripts/compare_all_50_nutrition_via_api.py

    # OpenRouter Qwen3-VL-235B
    python test_scripts/compare_all_50_nutrition_via_api.py \
      --model openrouter:qwen/qwen3-vl-235b-a22b-thinking

    # OpenRouter GPT-4o-mini
    python test_scripts/compare_all_50_nutrition_via_api.py \
      --model openrouter:openai/gpt-4o-mini

Arguments:
    --model MODEL_ID    VLMモデルID (デフォルト: Qwen/Qwen3-VL-30B-A3B-Thinking)
    --api-url URL       API URL (デフォルト: http://localhost:8006)
    --concurrent N      並行リクエスト数 (デフォルト: 5)
"""

import json
import sys
import asyncio
import logging
import aiohttp
from pathlib import Path
from datetime import datetime
from typing import List, Optional

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def load_label_nutrition(label_path: str) -> dict:
    """
    VLM Labelから栄養素を集計

    Args:
        label_path: images_label_with_nutrition/test_foodXX.json のパス

    Returns:
        {
            "total_calorie": float,
            "total_protein_g": float,
            "total_fat_g": float,
            "total_carbs_g": float,
            "items": [...]
        }
    """
    with open(label_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    total_calorie = 0.0
    total_protein_g = 0.0
    total_fat_g = 0.0
    total_carbs_g = 0.0
    items = []

    for dish in data.get("dishes", []):
        # main_food
        main_food = dish.get("main_food")
        if main_food:
            nutrition = main_food.get("nutrition", {})
            total_calorie += nutrition.get("calorie", 0)
            total_protein_g += nutrition.get("protein_g", 0)
            total_fat_g += nutrition.get("fat_g", 0)
            total_carbs_g += nutrition.get("carbs_g", 0)

            items.append({
                "type": "main_food",
                "search_name": main_food.get("search_name"),
                "weight_g": main_food.get("weight_g"),
                "nutrition": nutrition
            })

        # extras
        for extra in dish.get("extras", []):
            nutrition = extra.get("nutrition", {})
            total_calorie += nutrition.get("calorie", 0)
            total_protein_g += nutrition.get("protein_g", 0)
            total_fat_g += nutrition.get("fat_g", 0)
            total_carbs_g += nutrition.get("carbs_g", 0)

            items.append({
                "type": "extra",
                "search_name": extra.get("search_name"),
                "weight_g": extra.get("weight_g"),
                "nutrition": nutrition
            })

    return {
        "total_calorie": total_calorie,
        "total_protein_g": total_protein_g,
        "total_fat_g": total_fat_g,
        "total_carbs_g": total_carbs_g,
        "items": items
    }


async def get_api_nutrition(
    session: aiohttp.ClientSession,
    api_url: str,
    image_path: str,
    model_id: Optional[str] = None
) -> dict:
    """
    API経由で画像分析して栄養素を取得

    Args:
        session: aiohttp ClientSession
        api_url: API base URL (例: http://localhost:8006)
        image_path: 画像ファイルパス
        model_id: VLMモデルID (オプション)

    Returns:
        API分析結果

    Note:
        リトライはAPI側で実装されているため、このクライアント側ではリトライしません
    """
    endpoint = f"{api_url}/api/v1/meal-analyses/complete"

    # 画像ファイルを読み込み
    with open(image_path, 'rb') as f:
        image_data = f.read()

    try:
        # マルチパートフォームデータを構築
        data = aiohttp.FormData()
        data.add_field('image',
                      image_data,
                      filename=Path(image_path).name,
                      content_type='image/jpeg')

        # モデルIDを追加（指定されている場合）
        if model_id:
            data.add_field('model_id', model_id)

        # APIリクエスト（タイムアウト5分）
        timeout = aiohttp.ClientTimeout(total=300)
        async with session.post(endpoint, data=data, timeout=timeout) as response:
            if response.status != 200:
                error_text = await response.text()
                raise Exception(f"API Error {response.status}: {error_text}")

            result = await response.json()

            # レスポンスから栄養素を抽出
            total_nutrition = {
                "calories": 0.0,
                "protein_g": 0.0,
                "fat_g": 0.0,
                "carbs_g": 0.0
            }

            for dish in result.get("dishes", []):
                dish_nutrition = dish.get("total_nutrition", {})
                total_nutrition["calories"] += dish_nutrition.get("calories", 0)
                total_nutrition["protein_g"] += dish_nutrition.get("protein", 0)
                total_nutrition["fat_g"] += dish_nutrition.get("fat", 0)
                total_nutrition["carbs_g"] += dish_nutrition.get("carbs", 0)

            return {
                "total_nutrition": total_nutrition,
                "dishes": result.get("dishes", []),
                "analysis_id": result.get("analysis_id"),
                "processing_time": result.get("processing_time_seconds", 0),
                "usage": result.get("usage", {})  # usage情報を含める
            }

    except Exception as e:
        logger.error(f"API call failed: {str(e)}")
        raise


def calculate_diff(label: dict, api_result: dict) -> dict:
    """
    差分計算

    Args:
        label: label栄養素
        api_result: API栄養素 (total_nutrition)

    Returns:
        差分情報
    """
    api_calories = api_result.get('calories', 0)

    diff_cal = api_calories - label['total_calorie']
    diff_protein = api_result.get('protein_g', 0) - label['total_protein_g']
    diff_fat = api_result.get('fat_g', 0) - label['total_fat_g']
    diff_carbs = api_result.get('carbs_g', 0) - label['total_carbs_g']

    return {
        "calorie": {
            "diff": diff_cal,
            "percent": (diff_cal / label['total_calorie'] * 100) if label['total_calorie'] > 0 else 0
        },
        "protein_g": {
            "diff": diff_protein,
            "percent": (diff_protein / label['total_protein_g'] * 100) if label['total_protein_g'] > 0 else 0
        },
        "fat_g": {
            "diff": diff_fat,
            "percent": (diff_fat / label['total_fat_g'] * 100) if label['total_fat_g'] > 0 else 0
        },
        "carbs_g": {
            "diff": diff_carbs,
            "percent": (diff_carbs / label['total_carbs_g'] * 100) if label['total_carbs_g'] > 0 else 0
        }
    }


def generate_markdown_report(results: List[dict], output_path: str, model_id: str):
    """
    Markdownレポート生成

    Args:
        results: 比較結果リスト
        output_path: 出力ファイルパス
        model_id: 使用したVLMモデルID
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    md = []
    md.append("# API経由 栄養素比較レポート (Label vs VLM)")
    md.append(f"\n生成日時: {timestamp}")
    md.append(f"VLMモデル: `{model_id}`")
    md.append(f"対象画像数: {len(results)}\n")

    # 結果が空の場合
    if len(results) == 0:
        md.append("## エラー\n")
        md.append("処理に成功した画像がありません。\n")
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(md))
        print(f"⚠️  Markdownレポート生成: {output_path} (結果なし)")
        return

    # サマリー統計
    md.append("## サマリー\n")

    avg_cal_diff = sum(r['diff']['calorie']['percent'] for r in results) / len(results)
    avg_protein_diff = sum(r['diff']['protein_g']['percent'] for r in results) / len(results)
    avg_fat_diff = sum(r['diff']['fat_g']['percent'] for r in results) / len(results)
    avg_carbs_diff = sum(r['diff']['carbs_g']['percent'] for r in results) / len(results)

    md.append("### 平均差分（API - Label）\n")
    md.append("| 栄養素 | 平均差分 (%) |")
    md.append("|--------|--------------|")
    md.append(f"| カロリー | {avg_cal_diff:+.1f}% |")
    md.append(f"| タンパク質 | {avg_protein_diff:+.1f}% |")
    md.append(f"| 脂質 | {avg_fat_diff:+.1f}% |")
    md.append(f"| 炭水化物 | {avg_carbs_diff:+.1f}% |")
    md.append("")

    # Usage統計を追加
    md.append("### API Usage統計\n")

    # usage情報を集計
    total_prompt_tokens = 0
    total_completion_tokens = 0
    total_tokens = 0
    total_cost = 0.0
    usage_count = 0

    for r in results:
        usage = r.get('api_result', {}).get('usage', {})
        if usage:
            total_prompt_tokens += usage.get('prompt_tokens', 0)
            total_completion_tokens += usage.get('completion_tokens', 0)
            total_tokens += usage.get('total_tokens', 0)
            total_cost += usage.get('cost_usd', 0)
            usage_count += 1

    if usage_count > 0:
        avg_prompt_tokens = total_prompt_tokens / usage_count
        avg_completion_tokens = total_completion_tokens / usage_count
        avg_total_tokens = total_tokens / usage_count
        avg_cost = total_cost / usage_count

        md.append("| メトリクス | 平均 | 合計 |")
        md.append("|------------|------|------|")
        md.append(f"| Prompt Tokens | {avg_prompt_tokens:.0f} | {total_prompt_tokens} |")
        md.append(f"| Completion Tokens | {avg_completion_tokens:.0f} | {total_completion_tokens} |")
        md.append(f"| Total Tokens | {avg_total_tokens:.0f} | {total_tokens} |")
        if total_cost > 0:
            md.append(f"| Cost (USD) | ${avg_cost:.4f} | ${total_cost:.4f} |")
    else:
        md.append("Usage情報が取得できませんでした。\n")
    md.append("")

    # 詳細比較表
    md.append("## 詳細比較表\n")
    md.append("| 画像 | Label Cal | API Cal | 差分 | Label P | API P | 差分 | Label F | API F | 差分 | Label C | API C | 差分 |")
    md.append("|------|-----------|---------|------|---------|-------|------|---------|-------|------|---------|-------|------|")

    for r in results:
        label_nut = r['label_nutrition']
        api_nut = r['api_result']['total_nutrition']
        diff = r['diff']

        api_calories = api_nut.get('calories', 0)

        md.append(
            f"| {r['image_name']} | "
            f"{label_nut['total_calorie']:.0f} | "
            f"{api_calories:.0f} | "
            f"{diff['calorie']['percent']:+.1f}% | "
            f"{label_nut['total_protein_g']:.1f} | "
            f"{api_nut.get('protein_g', 0):.1f} | "
            f"{diff['protein_g']['percent']:+.1f}% | "
            f"{label_nut['total_fat_g']:.1f} | "
            f"{api_nut.get('fat_g', 0):.1f} | "
            f"{diff['fat_g']['percent']:+.1f}% | "
            f"{label_nut['total_carbs_g']:.1f} | "
            f"{api_nut.get('carbs_g', 0):.1f} | "
            f"{diff['carbs_g']['percent']:+.1f}% |"
        )

    md.append("")

    # 個別詳細
    md.append("## 個別詳細\n")

    for r in results:
        md.append(f"### {r['image_name']}\n")

        # Label
        md.append("**VLM Label栄養素**\n")
        md.append("| Type | Food | Weight | Cal | P | F | C |")
        md.append("|------|------|--------|-----|---|---|---|")

        for item in r['label_nutrition']['items']:
            nut = item['nutrition']
            md.append(
                f"| {item['type']} | {item['search_name']} | {item['weight_g']}g | "
                f"{nut.get('calorie', 0):.0f} | {nut.get('protein_g', 0):.1f}g | "
                f"{nut.get('fat_g', 0):.1f}g | {nut.get('carbs_g', 0):.1f}g |"
            )

        label_nut = r['label_nutrition']
        md.append(
            f"| **合計** | - | - | "
            f"**{label_nut['total_calorie']:.0f}** | **{label_nut['total_protein_g']:.1f}g** | "
            f"**{label_nut['total_fat_g']:.1f}g** | **{label_nut['total_carbs_g']:.1f}g** |"
        )
        md.append("")

        # API結果
        api_nut = r['api_result']['total_nutrition']
        api_calories = api_nut.get('calories') or api_nut.get('calorie', 0)

        md.append("**API栄養素**\n")
        md.append(
            f"合計: {api_calories:.0f} kcal, "
            f"P: {api_nut.get('protein_g', 0):.1f}g, "
            f"F: {api_nut.get('fat_g', 0):.1f}g, "
            f"C: {api_nut.get('carbs_g', 0):.1f}g\n"
        )

        # 差分
        diff = r['diff']
        md.append("**差分 (API - Label)**\n")
        md.append(
            f"- カロリー: {diff['calorie']['diff']:+.1f} kcal ({diff['calorie']['percent']:+.1f}%)\n"
            f"- タンパク質: {diff['protein_g']['diff']:+.1f}g ({diff['protein_g']['percent']:+.1f}%)\n"
            f"- 脂質: {diff['fat_g']['diff']:+.1f}g ({diff['fat_g']['percent']:+.1f}%)\n"
            f"- 炭水化物: {diff['carbs_g']['diff']:+.1f}g ({diff['carbs_g']['percent']:+.1f}%)\n"
        )

        md.append("---\n")

    # ファイル出力
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md))

    print(f"✅ Markdownレポート生成: {output_path}")


async def process_single_image(
    session: aiohttp.ClientSession,
    api_url: str,
    model_id: Optional[str],
    image_index: int,
    semaphore: asyncio.Semaphore
) -> dict:
    """
    1画像を処理（並行制御あり）

    Args:
        session: aiohttp ClientSession
        api_url: API base URL
        model_id: VLMモデルID
        image_index: 画像番号 (1-50)
        semaphore: 並行数制御用セマフォ

    Returns:
        処理結果辞書
    """
    async with semaphore:
        image_name = f"test_food{image_index}.jpg"
        image_path = f"test_images/images/{image_name}"
        label_path = f"test_images/images_label_with_nutrition/test_food{image_index:02d}.json"

        try:
            # Label読み込み
            label_nutrition = load_label_nutrition(label_path)

            # API実行
            api_result = await get_api_nutrition(session, api_url, image_path, model_id)

            # 差分計算
            diff = calculate_diff(label_nutrition, api_result['total_nutrition'])

            api_calories = api_result['total_nutrition'].get('calories') or \
                          api_result['total_nutrition'].get('calorie', 0)

            print(f"✅ [{image_index}/50] {image_name}: "
                  f"Label {label_nutrition['total_calorie']:.0f} kcal | "
                  f"API {api_calories:.0f} kcal | "
                  f"差分 {diff['calorie']['percent']:+.1f}%")

            return {
                "image_name": image_name,
                "label_nutrition": label_nutrition,
                "api_result": api_result,
                "diff": diff
            }

        except Exception as e:
            print(f"❌ [{image_index}/50] {image_name}: エラー - {e}")
            return None


async def main():
    # コマンドライン引数の解析
    import argparse
    parser = argparse.ArgumentParser(
        description="API経由での栄養素 vs VLM Label栄養素の比較 (全50画像)"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="VLMモデルID (例: openrouter:qwen/qwen3-vl-235b-a22b-thinking)"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:8006",
        help="API URL (デフォルト: http://localhost:8006)"
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=5,
        help="並行リクエスト数 (デフォルト: 5、OpenRouterの場合は2-3推奨)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="処理する画像数 (デフォルト: 50)"
    )
    args = parser.parse_args()

    print("=" * 80)
    print(f"API経由 栄養素比較 (Label vs VLM) - {args.limit}画像")
    print("=" * 80)
    print()
    print(f"API URL: {args.api_url}")
    print(f"VLMモデル: {args.model or 'デフォルト'}")
    print(f"並行リクエスト数: {args.concurrent}")
    print(f"処理画像数: {args.limit}")
    print()

    # 並行処理設定
    semaphore = asyncio.Semaphore(args.concurrent)

    print(f"🚀 並行処理開始（最大{args.concurrent}並行）")
    print()

    # aiohttp ClientSessionを作成
    async with aiohttp.ClientSession() as session:
        # 指定数の画像を並行処理
        tasks = [
            process_single_image(session, args.api_url, args.model, i, semaphore)
            for i in range(1, args.limit + 1)
        ]

        # 並行実行
        results_raw = await asyncio.gather(*tasks)

    # Noneを除外し、画像名でソート
    results = [r for r in results_raw if r is not None]
    results.sort(key=lambda x: x["image_name"])

    print()
    print(f"✅ 処理完了: {len(results)}/{args.limit}画像")
    print()

    # Markdownレポート生成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    model_suffix = args.model.replace('/', '_').replace(':', '_') if args.model else 'default'
    md_output = f"test_scripts/output/nutrition_comparison_api_{model_suffix}_{timestamp}.md"
    generate_markdown_report(results, md_output, args.model or "デフォルトモデル")

    # JSON詳細結果も保存
    json_output = f"test_scripts/output/nutrition_comparison_api_{model_suffix}_{timestamp}.json"
    with open(json_output, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"✅ JSON詳細結果保存: {json_output}")
    print()


if __name__ == "__main__":
    asyncio.run(main())
