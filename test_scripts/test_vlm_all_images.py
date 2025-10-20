#!/usr/bin/env python3
"""
test_vlm_all_images.py

test_imagesディレクトリ内の全ての画像に対してVLM（Vision Language Model）を呼び出し、
結果をJSON形式で保存するテストスクリプト。

Usage:
    PYTHONPATH=/Users/odasoya/meal_analysis_api_2 python test_scripts/test_vlm_all_images.py [--model MODEL_ID]
    
Arguments:
    --model MODEL_ID  VLMモデルID (デフォルト: 設定ファイルから取得)
"""

import os
import sys
import json
import asyncio
import argparse
from pathlib import Path
from datetime import datetime
import mimetypes

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared.services.deepinfra_service import DeepInfraService
from shared.config import get_settings


# サポートする画像形式
SUPPORTED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}


def generate_vlm_prompt(food_names_list: str) -> str:
    """
    VLMに送信するプロンプトを生成（食品名リストを埋め込み）
    
    Args:
        food_names_list: 食品名リストの文字列
    
    Returns:
        str: 完全なプロンプト
    """
    return f"""You are an **expert food analyst and nutritionist** for a US-based diet management application. Analyze ONE meal image and return a **single JSON object** only.

Your primary goal is to **identify every visually separate food item** (each is a `dish`) and assign the most accurate `analysis_method` while **copying food names exactly** from the provided **EXACT_FOOD_LIST (CORE)**.

---

## Primary Rule

- **Do NOT merge** different items into one dish. If a plate shows pizza + salad + soda → return **three** dishes.

- **VISIBLE INGREDIENTS ONLY**: Include only what you can clearly see. Never add hidden items (e.g., don't add chicken to a salad unless visible). When uncertain, choose a simpler valid base or omit the invisible item.

---

## Method Choice (use this priority to reduce over-decomposition)

1) **USE_AS_IS** — Standard single item or standard dish with no visible customization.
   - Output: `base_food.item_name` = exact match from EXACT_FOOD_LIST; `ingredients` = `[]`.

2) **HYBRID_DECOMPOSITION** — A standard base plus **visible add-ons** (toppings/extras).
   - Output: `base_food.item_name` = base from EXACT_FOOD_LIST; `ingredients` = **only extras**.

3) **DECOMPOSE_TO_INGREDIENTS** — Fully custom assembly; all constituents are visible; no suitable standard base.
   - Output: `base_food.item_name = null`, `base_food.weight_g = 0`; list **all** visible parts.

> If uncertain within a cuisine cluster, prefer an **NFS** item from the list rather than inventing names.

---

## HYBRID duplicate rule (critical)

When you pick a HYBRID base (e.g., `"Pasta with tomato-based sauce and cheese"`), **do not** add ingredients that the base already implies (e.g., `"Cheese, ..."` / `"Tomatoes, ..."`), **unless** there are clearly visible **extra** toppings beyond the base.

---

## Multiple Identical Units

If the **same** item appears multiple times (e.g., two tacos), you may **either**:
- output separate dishes, **or**
- output **one** dish with an **optional** field `"unit_count": <integer>` and make `weight_g` the **total** across units.

Keep the approach consistent within one image.

---

## Weight Estimation & Cooking State

- Report all weights in **grams**. Use plate/bowl scaling (typical dinner plate 25–28 cm) and volume cues.
- If rice/pasta/noodles/legumes **look cooked**, choose cooked entries (e.g., `"Rice, white, cooked, no added fat"`). Use "dry/uncooked" only if the image shows a dry product.

---

## Name Validation (must pass before output)

For every `base_food.item_name` and `ingredients[].ingredient_name`, **verify** the string exists **verbatim** in the EXACT_FOOD_LIST you received in this run.
If not found, **replace** it with the nearest valid **NFS/NS** fallback from the list or **omit** it. **Never** invent new names.

---

## Output Format (JSON only)

Return **one** JSON object with this structure. If a value is unknown, use `null`. Do **not** include explanations or comments.

{{
  "dishes": [
    {{
      "dish_name": "Example Dish 1",
      "unit_count": 1,
      "confidence": 0.95,
      "analysis_method": "HYBRID_DECOMPOSITION",
      "base_food": {{
        "item_name": "[Base dish from EXACT_FOOD_LIST]",
        "weight_g": 280
      }},
      "ingredients": [
        {{ "ingredient_name": "[Additional ingredient 1 from EXACT_FOOD_LIST]", "weight_g": 30 }},
        {{ "ingredient_name": "[Additional ingredient 2 from EXACT_FOOD_LIST]", "weight_g": 20 }}
      ]
    }},
    {{
      "dish_name": "Example Dish 2",
      "unit_count": 1,
      "confidence": 0.98,
      "analysis_method": "DECOMPOSE_TO_INGREDIENTS",
      "base_food": {{ "item_name": null, "weight_g": 0 }},
      "ingredients": [
        {{ "ingredient_name": "[Ingredient 1 from EXACT_FOOD_LIST]", "weight_g": 100 }},
        {{ "ingredient_name": "[Ingredient 2 from EXACT_FOOD_LIST]", "weight_g": 50 }},
        {{ "ingredient_name": "[Ingredient 3 from EXACT_FOOD_LIST]", "weight_g": 40 }}
      ]
    }},
    {{
      "dish_name": "Example Dish 3",
      "unit_count": 1,
      "confidence": 1.0,
      "analysis_method": "USE_AS_IS",
      "base_food": {{ "item_name": "[Single food item from EXACT_FOOD_LIST]", "weight_g": 180 }},
      "ingredients": []
    }}
  ]
}}

---

## FINAL PRE-FLIGHT CHECK (run mentally before returning JSON)

1) Every name appears **verbatim** in EXACT_FOOD_LIST.
2) HYBRID lists **only extras** not already in the base.
3) Weights reflect **cooked vs raw** states that match the image.
4) `unit_count` is used consistently (or omitted); total weights are correct.
5) No dish merges across different foods; no invisible items added.

---

## EXACT_FOOD_LIST (CORE)

You will receive a **CORE** list (below). Prefer CORE items. If an adequate match does not exist in CORE, choose the **closest NFS/NS** item within CORE; do **not** invent names.

{food_names_list}

---

**END OF PROMPT**"""


async def process_single_image(
    image_path: Path,
    deepinfra_service: DeepInfraService,
    prompt: str,
    temperature: float = 0.0,
    seed: int = 123456
) -> dict:
    """
    単一の画像を処理し、VLMの結果を返す
    
    Args:
        image_path: 画像ファイルのパス
        deepinfra_service: DeepInfraServiceインスタンス
        prompt: VLMに送信するプロンプト
        temperature: AI推論のランダム性制御 (0.0-1.0)
        seed: 再現性のためのシード値
    
    Returns:
        dict: 処理結果（画像ファイル名、VLMレスポンス、エラー情報など）
    """
    print(f"\n{'='*80}")
    print(f"処理中: {image_path.name}")
    print(f"{'='*80}")
    
    result = {
        "image_file": image_path.name,
        "image_path": str(image_path),
        "timestamp": datetime.now().isoformat(),
        "success": False,
        "vlm_response": None,
        "error": None
    }
    
    try:
        # 画像ファイルを読み込み
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # MIMEタイプを取得
        mime_type, _ = mimetypes.guess_type(str(image_path))
        if not mime_type:
            mime_type = "image/jpeg"  # デフォルト
        
        result["mime_type"] = mime_type
        result["image_size_bytes"] = len(image_bytes)
        
        print(f"画像サイズ: {len(image_bytes):,} bytes")
        print(f"MIMEタイプ: {mime_type}")
        print(f"Temperature: {temperature}, Seed: {seed}")
        
        # VLMを呼び出し
        print(f"\nVLM呼び出し中...")
        raw_response = await deepinfra_service.analyze_image(
            image_bytes=image_bytes,
            image_mime_type=mime_type,
            prompt=prompt,
            temperature=temperature,
            seed=seed
        )
        
        # JSONパース
        vlm_response = json.loads(raw_response)
        result["vlm_response"] = vlm_response
        result["success"] = True
        
        # 結果のサマリーを表示
        print(f"\n✅ 成功!")
        if "dishes" in vlm_response:
            dishes_count = len(vlm_response["dishes"])
            print(f"検出された料理数: {dishes_count}")
            for idx, dish in enumerate(vlm_response["dishes"], 1):
                dish_name = dish.get("dish_name", "N/A")
                confidence = dish.get("confidence", 0)
                ingredients_count = len(dish.get("ingredients", []))
                analysis_method = dish.get("analysis_method", "N/A")
                print(f"  {idx}. {dish_name} (confidence: {confidence:.2f}, "
                      f"ingredients: {ingredients_count}, method: {analysis_method})")
        
    except Exception as e:
        result["error"] = str(e)
        result["success"] = False
        print(f"\n❌ エラー: {e}")
    
    return result


async def main():
    """メイン処理"""
    # コマンドライン引数を解析
    parser = argparse.ArgumentParser(
        description="test_imagesディレクトリ内の全画像でVLMを呼び出し、結果をJSON形式で保存"
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="使用するVLMモデルID (例: google/gemma-3-27b-it, meta-llama/Llama-3.2-90B-Vision-Instruct)"
    )
    args = parser.parse_args()
    print(f"\n{'#'*80}")
    print(f"# VLM全画像テストスクリプト")
    print(f"{'#'*80}\n")
    
    # test_imagesディレクトリのパス
    test_images_dir = project_root / "test_images"
    
    if not test_images_dir.exists():
        print(f"❌ エラー: {test_images_dir} が存在しません")
        sys.exit(1)
    
    # 画像ファイルを取得
    image_files = []
    for ext in SUPPORTED_IMAGE_EXTENSIONS:
        image_files.extend(test_images_dir.glob(f"*{ext}"))
        image_files.extend(test_images_dir.glob(f"*{ext.upper()}"))
    
    # ファイル名でソート
    image_files = sorted(set(image_files))
    
    if not image_files:
        print(f"⚠️  警告: {test_images_dir} に画像ファイルが見つかりませんでした")
        print(f"サポートされている拡張子: {', '.join(SUPPORTED_IMAGE_EXTENSIONS)}")
        sys.exit(0)
    
    print(f"検出された画像ファイル: {len(image_files)}件")
    for idx, img_file in enumerate(image_files, 1):
        print(f"  {idx}. {img_file.name}")
    
    # DeepInfraServiceを初期化
    print(f"\nDeepInfraServiceを初期化中...")
    settings = get_settings()
    
    # コマンドライン引数からモデルIDを取得（指定がない場合は設定ファイルから）
    model_id = args.model if args.model else settings.DEEPINFRA_MODEL_ID
    
    deepinfra_service = DeepInfraService(
        model_id=model_id
    )
    print(f"モデル: {deepinfra_service.model_id}")
    
    # USDA用のプロンプトを生成（exclude_uncooked=False）
    print(f"\nプロンプトを生成中...")
    # food_names_list.txtを読み込み
    food_names_list_path = project_root / "test_scripts" / "food_names_list" / "food_names_list.txt"
    
    if not food_names_list_path.exists():
        print(f"❌ エラー: {food_names_list_path} が存在しません")
        sys.exit(1)
    
    with open(food_names_list_path, 'r', encoding='utf-8') as f:
        food_names_list = f.read()
    
    print(f"食品名リスト読み込み完了: {len(food_names_list):,} 文字")
    
    prompt = generate_vlm_prompt(food_names_list)
    print(f"プロンプト長: {len(prompt):,} 文字")
    
    # 各画像を処理
    results = []
    for idx, image_path in enumerate(image_files, 1):
        print(f"\n進捗: {idx}/{len(image_files)}")
        result = await process_single_image(
            image_path=image_path,
            deepinfra_service=deepinfra_service,
            prompt=prompt,
            temperature=0.0,
            seed=123456
        )
        results.append(result)
    
    # 結果を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = project_root / "test_scripts" / "output"
    output_dir.mkdir(exist_ok=True)
    
    # モデル名をファイル名に含める（スラッシュやコロンを_に置換）
    model_name_safe = deepinfra_service.model_id.replace("/", "_").replace(":", "_")
    output_file = output_dir / f"vlm_test_results_{model_name_safe}_{timestamp}.json"
    
    print(f"\n{'='*80}")
    print(f"結果を保存中...")
    print(f"{'='*80}")
    
    summary = {
        "test_metadata": {
            "timestamp": datetime.now().isoformat(),
            "total_images": len(image_files),
            "successful": sum(1 for r in results if r["success"]),
            "failed": sum(1 for r in results if not r["success"]),
            "model_id": deepinfra_service.model_id,
            "temperature": 0.0,
            "seed": 123456,
            "prompt_length": len(prompt)
        },
        "results": results
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 結果を保存しました: {output_file}")
    print(f"\n{'='*80}")
    print(f"サマリー:")
    print(f"  総画像数: {summary['test_metadata']['total_images']}")
    print(f"  成功: {summary['test_metadata']['successful']}")
    print(f"  失敗: {summary['test_metadata']['failed']}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    asyncio.run(main())
