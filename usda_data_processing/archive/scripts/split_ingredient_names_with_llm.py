#!/usr/bin/env python3
"""
USDA FNDDS食材名をLLMで分割（MyNetDiaryと同じルール）

処理対象:
- Raw Ingredients（基本食材）
- Prepared Ingredients（調理済み食材）

分割ルール:
1. search_name: コア食材名（検索用）
2. description: 修飾語・調理方法・状態など

LLM: DeepInfra google/gemma-3-27b-it
"""

import asyncio
import json
import os
from pathlib import Path
from openai import AsyncOpenAI
from typing import Dict, List, Optional
from datetime import datetime
import time


# 調理キーワード（generate_usda_food_database.pyと同じ）
COOKING_KEYWORDS = [
    'cooked', 'toasted', 'baked', 'broiled', 'fried', 'roasted',
    'boiled', 'steamed', 'grilled', 'poached', 'sauteed', 'braised', 'stewed',
    'smoked', 'cured', 'dried', 'pickled'
]


def load_survey_data(file_path: str) -> List[Dict]:
    """surveyDownload.jsonを読み込み"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get('SurveyFoods', [])


def is_cooked_ingredient(description: str) -> bool:
    """調理済み食材かどうかを判定"""
    desc_lower = description.lower()
    return any(keyword in desc_lower for keyword in COOKING_KEYWORDS)


def extract_ingredients(foods: List[Dict]) -> tuple[List[Dict], List[Dict]]:
    """
    raw_ingredientsとprepared_ingredientsを抽出

    Returns:
        (raw_ingredients, prepared_ingredients)
    """
    raw_ingredients = []
    prepared_ingredients = []

    for food in foods:
        input_foods_count = len(food.get('inputFoods', []))

        # inputFoods == 1のみ（単一食材）
        if input_foods_count == 1:
            food_name = food.get('description', '')

            if is_cooked_ingredient(food_name):
                prepared_ingredients.append(food)
            else:
                raw_ingredients.append(food)

    return raw_ingredients, prepared_ingredients


def create_splitting_prompt(recent_results: List[Dict] = None) -> str:
    """
    食品名分割用のプロンプトを生成

    Args:
        recent_results: 直近の処理結果（文脈として提供）
    """
    # 文脈セクションの構築
    context_section = ""
    if recent_results and len(recent_results) > 0:
        context_section = "\n\nRECENT PROCESSING CONTEXT (for consistency):\n"
        context_section += "Below are the most recent ingredient name splits. Use these as reference to maintain consistency:\n\n"

        for i, result in enumerate(recent_results[-10:], 1):  # 最新10件
            # json.dumps()の結果を先に変数に格納（f-stringの中括弧衝突を回避）
            search_name_json = json.dumps(result['search_name'], ensure_ascii=False)
            context_section += f"{i}. \"{result['original_name']}\"\n"
            context_section += f"   → search_name: {search_name_json}\n"
            context_section += f"   → description: \"{result['description']}\"\n\n"

        context_section += "CONSISTENCY RULES:\n"
        context_section += "- If the current ingredient is SIMILAR to any recent ones (e.g., same food with different modifiers),\n"
        context_section += "  use the SAME search_name format and capitalization\n"
        context_section += "- Example: If you recently processed \"Black beans boiled\" → search_name: \"Black beans\",\n"
        context_section += "  then \"Black beans canned\" should also use search_name: \"Black beans\" (same capitalization)\n\n"

    return f"""You are a food name parsing AI specialized in splitting food ingredient names into search-optimized components.
{context_section}
YOUR TASK:
Split the given food ingredient name into two parts:
1. **search_name**: The core ingredient name(s) for searching
2. **description**: Modifiers like cooking method, preparation state, additions, etc.

CRITICAL RULES:

1. **"or" HANDLING - TWO PATTERNS:**

   **Pattern A: Alternative Names (Synonyms) → LIST format**
   When "or" separates alternative names of the SAME ingredient, create a LIST of search_names.

   Examples:
   - "Chickpeas or garbanzo beans boiled without salt"
     → search_name: ["Chickpeas", "garbanzo beans"]
     → description: "boiled, without salt"

   - "Cannellini or white kidney beans canned"
     → search_name: ["Cannellini", "white kidney beans"]
     → description: "canned"

   **Pattern B: Modifier Options → STRING format**
   When "or" separates MODIFIERS (cooking methods, states), keep search_name as STRING and include all options in description.

   Examples:
   - "Beans baked canned plain or vegetarian"
     → search_name: "beans"
     → description: "baked, canned, plain, vegetarian"

   - "Coffee prepared without milk or sugar"
     → search_name: "coffee"
     → description: "prepared, without milk, without sugar"

2. **MODIFIER SEPARATION:**
   Extract cooking methods, preparation states, additives, and conditions into description.

   Examples:
   - "Black beans boiled without salt"
     → search_name: "Black beans"
     → description: "boiled, without salt"

   - "Almonds roasted salted"
     → search_name: "Almonds"
     → description: "roasted, salted"

3. **NO MODIFIERS:**
   If the ingredient has no modifiers, set description to "None" (the string "None", not null).

   Examples:
   - "Hummus"
     → search_name: "hummus"
     → description: "None"

   - "Romano cheese"
     → search_name: "Romano cheese"
     → description: "None"

4. **DESCRIPTION FORMAT:**
   - Use comma-separated format: "modifier1, modifier2, modifier3"
   - Keep it clean and concise
   - Convert "without X or Y" to "without X, without Y"

RESPONSE FORMAT:
You MUST respond with ONLY a valid JSON object. No explanations, no markdown, just JSON.

{{
  "search_name": "string" OR ["string1", "string2"],
  "description": "string"
}}

IMPORTANT:
- search_name can be either a string OR a list of strings (for alternative names)
- description is ALWAYS a string (use "None" if no modifiers)
- Your response MUST be valid JSON only"""


async def split_ingredient_name(
    ingredient_name: str,
    api_key: str,
    client: AsyncOpenAI,
    recent_results: List[Dict] = None,
    max_retries: int = 3
) -> Optional[Dict]:
    """
    LLMを使って食材名を分割

    Args:
        ingredient_name: 元の食材名
        api_key: DeepInfra APIキー
        client: AsyncOpenAIクライアント
        recent_results: 直近の処理結果（一貫性のため）
        max_retries: 最大リトライ回数

    Returns:
        {
            "search_name": str or list,
            "description": str
        }
    """
    system_prompt = create_splitting_prompt(recent_results)
    user_prompt = f"Split this food ingredient name:\n\n{ingredient_name}"

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model="google/gemma-3-27b-it",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=500
            )

            response_text = response.choices[0].message.content.strip()

            # マークダウンコードブロックを削除
            if response_text.startswith('```json'):
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif response_text.startswith('```'):
                response_text = response_text.split('```')[1].split('```')[0].strip()

            # JSONをパース
            result = json.loads(response_text)

            # バリデーション
            if 'search_name' not in result or 'description' not in result:
                print(f"⚠️  無効な応答フォーマット (試行 {attempt + 1}/{max_retries}): {ingredient_name}")
                continue

            return result

        except json.JSONDecodeError as e:
            print(f"⚠️  JSON解析エラー (試行 {attempt + 1}/{max_retries}): {ingredient_name}")
            print(f"   エラー: {e}")
            print(f"   レスポンス: {response_text[:200]}...")

            if attempt == max_retries - 1:
                return None

            await asyncio.sleep(1)  # リトライ前に待機

        except Exception as e:
            print(f"⚠️  API呼び出しエラー (試行 {attempt + 1}/{max_retries}): {ingredient_name}")
            print(f"   エラー: {e}")

            if attempt == max_retries - 1:
                return None

            await asyncio.sleep(2)  # エラー後は長めに待機

    return None


def load_checkpoint(checkpoint_path: Path) -> List[Dict]:
    """チェックポイントから中間結果を読み込み"""
    if checkpoint_path.exists():
        with open(checkpoint_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_checkpoint(results: List[Dict], checkpoint_path: Path):
    """チェックポイントに中間結果を保存"""
    with open(checkpoint_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


async def process_ingredients_batch(
    ingredients: List[Dict],
    api_key: str,
    checkpoint_path: Path,
    batch_size: int = 10,
    delay_between_batches: float = 1.0
) -> List[Dict]:
    """
    食材リストをバッチ処理（直近10件の文脈を保持 + チェックポイント機能）

    Args:
        ingredients: 食材リスト
        api_key: DeepInfra APIキー
        checkpoint_path: チェックポイントファイルパス
        batch_size: バッチサイズ
        delay_between_batches: バッチ間の待機時間（秒）

    Returns:
        分割結果リスト
    """
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://api.deepinfra.com/v1/openai"
    )

    # チェックポイントから既存の結果を読み込み
    results = load_checkpoint(checkpoint_path)
    processed_food_codes = {r['foodCode'] for r in results}

    # 未処理の食材のみをフィルタリング
    remaining_ingredients = [
        food for food in ingredients
        if food.get('foodCode') not in processed_food_codes
    ]

    total = len(ingredients)
    already_processed = len(results)
    remaining = len(remaining_ingredients)

    if already_processed > 0:
        print(f"\n🔄 処理再開: チェックポイントから{already_processed}件の結果を読み込みました")

    print(f"\n🔄 処理開始:")
    print(f"   総食材数: {total}件")
    print(f"   処理済み: {already_processed}件")
    print(f"   残り: {remaining}件")
    print(f"   バッチサイズ: {batch_size}")
    print(f"   バッチ間待機: {delay_between_batches}秒")
    print(f"   文脈保持: 直近10件の処理結果を参照")
    print(f"   チェックポイント: {checkpoint_path.name}\n")

    if remaining == 0:
        print("✅ すべての食材が処理済みです")
        return results

    try:
        for i in range(0, remaining, batch_size):
            batch = remaining_ingredients[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (remaining + batch_size - 1) // batch_size
            current_position = already_processed + i + 1

            print(f"📦 バッチ {batch_num}/{total_batches} 処理中 ({current_position}-{min(current_position + len(batch) - 1, total)}/{total})...")

            # バッチ内の食材を逐次処理（直近の文脈を保持するため）
            for food in batch:
                ingredient_name = food.get('description', '')

                # 直近10件の結果を文脈として渡す
                recent_context = results[-10:] if len(results) >= 10 else results

                split_result = await split_ingredient_name(
                    ingredient_name,
                    api_key,
                    client,
                    recent_results=recent_context,
                    max_retries=1  # リトライ回数を1に削減（エラー時は即座に終了）
                )

                if split_result:
                    result = {
                        'foodCode': food.get('foodCode'),
                        'fdcId': food.get('fdcId'),
                        'original_name': food.get('description'),
                        'search_name': split_result['search_name'],
                        'description': split_result['description'],
                        'inputFoods': food.get('inputFoods', []),
                        'foodNutrients': food.get('foodNutrients', []),
                        'wweiaFoodCategory': food.get('wweiaFoodCategory', {}),
                        'processing_method': 'gemma_3_27b_name_splitting_with_context',
                        'conversion_timestamp': time.time()
                    }
                    results.append(result)
                else:
                    # 処理失敗時は即座に終了
                    print(f"\n❌ 処理失敗: {food.get('description')}")
                    print(f"❌ エラーが発生したため処理を中断します")
                    print(f"💾 チェックポイント保存中...")
                    save_checkpoint(results, checkpoint_path)
                    print(f"✅ チェックポイント保存完了: {len(results)}件")
                    print(f"\n再実行すると、続きから処理を再開できます")
                    return results

            # バッチ完了後、チェックポイントを保存
            save_checkpoint(results, checkpoint_path)
            print(f"   💾 チェックポイント保存: {len(results)}件")

            # バッチ間で待機（API制限対策）
            if i + batch_size < remaining:
                await asyncio.sleep(delay_between_batches)

    except Exception as e:
        # 予期しないエラー発生時
        print(f"\n❌ 予期しないエラー: {e}")
        print(f"💾 チェックポイント保存中...")
        save_checkpoint(results, checkpoint_path)
        print(f"✅ チェックポイント保存完了: {len(results)}件")
        print(f"\n再実行すると、続きから処理を再開できます")
        raise

    print(f"\n✅ 処理完了: {len(results)}/{total}件成功")
    return results


def save_results(
    raw_results: List[Dict],
    prepared_results: List[Dict],
    output_dir: Path
):
    """結果を保存"""

    # Raw Ingredients
    raw_output = output_dir / "usda_raw_ingredients_split.json"
    with open(raw_output, 'w', encoding='utf-8') as f:
        json.dump(raw_results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Raw Ingredients保存: {raw_output}")
    print(f"   件数: {len(raw_results)}件")
    print(f"   サイズ: {raw_output.stat().st_size / 1024:.1f} KB")

    # Prepared Ingredients
    prepared_output = output_dir / "usda_prepared_ingredients_split.json"
    with open(prepared_output, 'w', encoding='utf-8') as f:
        json.dump(prepared_results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Prepared Ingredients保存: {prepared_output}")
    print(f"   件数: {len(prepared_results)}件")
    print(f"   サイズ: {prepared_output.stat().st_size / 1024:.1f} KB")


def print_sample_results(results: List[Dict], title: str, num_samples: int = 5):
    """サンプル結果を表示"""
    print(f"\n{'='*80}")
    print(f"📊 {title} - サンプル結果（最初の{num_samples}件）")
    print(f"{'='*80}\n")

    for i, result in enumerate(results[:num_samples], 1):
        print(f"{i}. original_name: {result['original_name']}")
        print(f"   search_name: {result['search_name']}")
        print(f"   description: {result['description']}")
        print()


async def main():
    """メイン実行"""

    # API設定
    api_key = os.getenv('DEEPINFRA_API_KEY')
    if not api_key:
        print("❌ DEEPINFRA_API_KEYが設定されていません")
        print("   export DEEPINFRA_API_KEY=your_api_key")
        return

    # パス設定
    base_dir = Path("/Users/odasoya/meal_analysis_api_2")
    survey_json_path = base_dir / "usda_database" / "surveyDownload.json"
    output_dir = base_dir / "usda_data_processing" / "output"

    # 出力ディレクトリ作成
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*80)
    print("🤖 USDA食材名分割処理（LLMベース）")
    print("="*80)
    print(f"📂 入力: {survey_json_path}")
    print(f"📂 出力: {output_dir}")
    print(f"🤖 モデル: google/gemma-3-27b-it (DeepInfra)")
    print()

    # データ読み込み
    print("🔄 surveyDownload.json読み込み中...")
    foods = load_survey_data(str(survey_json_path))
    print(f"✅ 総食品数: {len(foods)}件")

    # 食材抽出
    print("\n🔍 食材抽出中...")
    raw_ingredients, prepared_ingredients = extract_ingredients(foods)

    print(f"✅ 抽出完了:")
    print(f"   Raw Ingredients: {len(raw_ingredients)}件")
    print(f"   Prepared Ingredients: {len(prepared_ingredients)}件")

    # ユーザー確認
    print(f"\n⚠️  処理対象: 合計 {len(raw_ingredients) + len(prepared_ingredients)}件")
    print(f"   推定時間: 約{((len(raw_ingredients) + len(prepared_ingredients)) / 10 * 1.5):.0f}秒")

    response = input("\n処理を開始しますか？ (y/n): ")
    if response.lower() != 'y':
        print("❌ 処理をキャンセルしました")
        return

    # チェックポイントファイルパス
    raw_checkpoint = output_dir / "usda_raw_ingredients_split_checkpoint.json"
    prepared_checkpoint = output_dir / "usda_prepared_ingredients_split_checkpoint.json"

    # Raw Ingredients処理
    print("\n" + "="*80)
    print("📝 Raw Ingredients処理中...")
    print("="*80)

    try:
        raw_results = await process_ingredients_batch(
            raw_ingredients,
            api_key=api_key,
            checkpoint_path=raw_checkpoint,
            batch_size=10,
            delay_between_batches=1.0
        )
    except Exception as e:
        print(f"\n❌ Raw Ingredients処理中にエラーが発生しました: {e}")
        print(f"再実行すると、チェックポイントから処理を再開できます")
        return

    # Prepared Ingredients処理
    print("\n" + "="*80)
    print("📝 Prepared Ingredients処理中...")
    print("="*80)

    try:
        prepared_results = await process_ingredients_batch(
            prepared_ingredients,
            api_key=api_key,
            checkpoint_path=prepared_checkpoint,
            batch_size=10,
            delay_between_batches=1.0
        )
    except Exception as e:
        print(f"\n❌ Prepared Ingredients処理中にエラーが発生しました: {e}")
        print(f"再実行すると、チェックポイントから処理を再開できます")
        return

    # 結果保存（最終版）
    print("\n" + "="*80)
    print("💾 最終結果保存中...")
    print("="*80)

    save_results(raw_results, prepared_results, output_dir)

    # チェックポイントファイルを削除（処理完了）
    if raw_checkpoint.exists():
        raw_checkpoint.unlink()
        print(f"🗑️  チェックポイント削除: {raw_checkpoint.name}")

    if prepared_checkpoint.exists():
        prepared_checkpoint.unlink()
        print(f"🗑️  チェックポイント削除: {prepared_checkpoint.name}")

    # サンプル結果表示
    if raw_results:
        print_sample_results(raw_results, "Raw Ingredients", 5)

    if prepared_results:
        print_sample_results(prepared_results, "Prepared Ingredients", 5)

    # サマリー
    print("\n" + "="*80)
    print("🎉 処理完了！")
    print("="*80)
    print(f"\n✅ Raw Ingredients: {len(raw_results)}/{len(raw_ingredients)}件")
    print(f"✅ Prepared Ingredients: {len(prepared_results)}/{len(prepared_ingredients)}件")
    print(f"\n合計成功: {len(raw_results) + len(prepared_results)}件")
    print(f"合計失敗: {(len(raw_ingredients) + len(prepared_ingredients)) - (len(raw_results) + len(prepared_results))}件")

    if len(raw_results) + len(prepared_results) > 0:
        success_rate = (len(raw_results) + len(prepared_results)) / (len(raw_ingredients) + len(prepared_ingredients)) * 100
        print(f"成功率: {success_rate:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
