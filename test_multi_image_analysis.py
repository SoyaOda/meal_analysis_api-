#!/usr/bin/env python3
"""
Multi-Image Nutrition Analysis Test - food1-5 Batch Processing
food1.jpg から food5.jpg まで5つの画像を一括分析し、
見やすい形で結果を保存するテストスクリプト
"""

import asyncio
import os
import sys
import logging
import json
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app_v2.pipeline import MealAnalysisPipeline

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def setup_environment():
    """環境変数の設定"""
    os.environ.setdefault("GOOGLE_APPLICATION_CREDENTIALS", "/Users/odasoya/meal_analysis_api_2/service-account-key.json")
    os.environ.setdefault("GEMINI_PROJECT_ID", "recording-diet-ai-3e7cf")
    os.environ.setdefault("GEMINI_LOCATION", "us-central1")
    os.environ.setdefault("GEMINI_MODEL_NAME", "gemini-2.5-flash-preview-05-20")
    
    # Deep Infra設定
    os.environ.setdefault("DEEPINFRA_API_KEY", "l34kH6UDh9s2KfcRZn9ovJedHmb3CQlx")
    os.environ.setdefault("DEEPINFRA_MODEL_ID", "google/gemma-3-27b-it")
    os.environ.setdefault("DEEPINFRA_BASE_URL", "https://api.deepinfra.com/v1/openai")


def get_image_mime_type(file_path: str) -> str:
    """ファイル拡張子からMIMEタイプを推定"""
    ext = Path(file_path).suffix.lower()
    mime_types = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    return mime_types.get(ext, 'image/jpeg')


async def analyze_single_image(image_path: str, results_dir: str, image_index: int) -> Dict[str, Any]:
    """単一画像の分析を実行"""
    
    # 画像ファイルの存在確認
    if not os.path.exists(image_path):
        print(f"❌ エラー: 画像ファイルが見つかりません: {image_path}")
        return None
    
    # 画像データの読み込み
    with open(image_path, 'rb') as f:
        image_bytes = f.read()
    
    image_mime_type = get_image_mime_type(image_path)
    image_name = Path(image_path).stem
    
    print(f"\n{'='*80}")
    print(f"🍽️  画像 {image_index}/5: {image_name}")
    print(f"📁 分析対象: {image_path}")
    print(f"📊 画像サイズ: {len(image_bytes):,} bytes")
    print(f"🔍 MIMEタイプ: {image_mime_type}")
    print(f"{'='*80}")
    
    # 画像専用の結果ディレクトリを作成
    image_results_dir = f"{results_dir}/{image_name}"
    os.makedirs(image_results_dir, exist_ok=True)
    
    # パイプラインの初期化（ファジーマッチング検索を使用）
    pipeline = MealAnalysisPipeline(
        use_elasticsearch_search=True,
        use_fuzzy_matching=True  # 新しいファジーマッチングシステムを使用
    )
    
    try:
        print(f"🔄 {image_name} 分析開始...")
        analysis_start_time = time.time()
        
        result = await pipeline.execute_complete_analysis(
            image_bytes=image_bytes,
            image_mime_type=image_mime_type,
            save_detailed_logs=True,
            test_execution=True,
            test_results_dir=image_results_dir
        )
        
        analysis_end_time = time.time()
        analysis_time = analysis_end_time - analysis_start_time
        
        print(f"✅ {image_name} 分析完了！ ({analysis_time:.2f}秒)")
        
        # 基本結果の表示
        print_image_analysis_summary(result, image_name)
        
        # 結果にメタデータを追加
        result["image_metadata"] = {
            "image_name": image_name,
            "image_path": image_path,
            "image_size_bytes": len(image_bytes),
            "analysis_time_seconds": analysis_time,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        # 画像専用の詳細結果を保存
        await save_image_detailed_results(result, image_results_dir, image_name)
        
        return result
        
    except Exception as e:
        print(f"❌ {image_name} 分析エラー: {str(e)}")
        logger.error(f"Analysis failed for {image_name}: {str(e)}", exc_info=True)
        return {
            "error": str(e),
            "image_name": image_name,
            "image_path": image_path,
            "analysis_timestamp": datetime.now().isoformat()
        }


def print_image_analysis_summary(result: dict, image_name: str):
    """画像分析結果の基本サマリーを表示"""
    
    print(f"\n📋 {image_name} 分析結果サマリー")
    print(f"{'─'*60}")
    
    # Phase1結果
    phase1_result = result.get("phase1_result", {})
    dishes = phase1_result.get("dishes", [])
    
    print(f"🍽️  検出された料理: {len(dishes)}個")
    for i, dish in enumerate(dishes, 1):
        dish_name = dish.get("dish_name", "不明")
        confidence = dish.get("confidence", 0.0)
        ingredients = dish.get("ingredients", [])
        print(f"   {i}. {dish_name} (信頼度: {confidence:.2f}, 食材: {len(ingredients)}個)")
    
    # 栄養計算結果
    final_nutrition = result.get("final_nutrition_result", {})
    total_nutrition = final_nutrition.get("total_nutrition", {})
    
    if total_nutrition:
        calories = total_nutrition.get("calories", 0)
        protein = total_nutrition.get("protein", 0)
        fat = total_nutrition.get("fat", 0)
        carbs = total_nutrition.get("carbs", 0)
        
        print(f"\n🔢 栄養計算結果:")
        print(f"   📊 総カロリー: {calories:.1f} kcal")
        print(f"   🥩 タンパク質: {protein:.1f} g")
        print(f"   🧈 脂質: {fat:.1f} g")
        print(f"   🍞 炭水化物: {carbs:.1f} g")
    
    # 処理サマリー
    processing_summary = result.get("processing_summary", {})
    total_ingredients = processing_summary.get("total_ingredients", 0)
    match_rate = processing_summary.get("nutrition_search_match_rate", "不明")
    processing_time = processing_summary.get("processing_time_seconds", 0)
    
    print(f"\n⚡ 処理サマリー:")
    print(f"   🥕 総食材数: {total_ingredients}個")
    print(f"   🎯 マッチ率: {match_rate}")
    print(f"   ⏱️  処理時間: {processing_time:.2f}秒")


async def save_image_detailed_results(result: dict, image_results_dir: str, image_name: str):
    """画像の詳細結果を保存"""
    
    # 1. 完全な結果をJSONで保存
    complete_result_path = f"{image_results_dir}/complete_analysis_result.json"
    with open(complete_result_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    # 2. 栄養計算結果のサマリーをMarkdownで保存
    nutrition_summary_path = f"{image_results_dir}/nutrition_summary.md"
    await create_nutrition_summary_markdown(result, nutrition_summary_path, image_name)
    
    # 3. 料理別詳細をMarkdownで保存
    dish_details_path = f"{image_results_dir}/dish_details.md"
    await create_dish_details_markdown(result, dish_details_path, image_name)
    
    print(f"💾 {image_name} 詳細結果保存完了:")
    print(f"   📄 完全結果: {complete_result_path}")
    print(f"   📊 栄養サマリー: {nutrition_summary_path}")
    print(f"   🍽️  料理詳細: {dish_details_path}")


async def create_nutrition_summary_markdown(result: dict, file_path: str, image_name: str):
    """栄養計算結果のサマリーMarkdownを作成"""
    
    final_nutrition = result.get("final_nutrition_result", {})
    total_nutrition = final_nutrition.get("total_nutrition", {})
    dishes = final_nutrition.get("dishes", [])
    
    content = f"""# {image_name} 栄養分析サマリー

## 📊 食事全体の栄養情報

| 栄養素 | 値 |
|--------|-----|
| 🔥 カロリー | {total_nutrition.get('calories', 0):.1f} kcal |
| 🥩 タンパク質 | {total_nutrition.get('protein', 0):.1f} g |
| 🧈 脂質 | {total_nutrition.get('fat', 0):.1f} g |
| 🍞 炭水化物 | {total_nutrition.get('carbs', 0):.1f} g |
| 🌾 食物繊維 | {total_nutrition.get('fiber') or '不明'} g |
| 🍯 糖質 | {total_nutrition.get('sugar') or '不明'} g |
| 🧂 ナトリウム | {total_nutrition.get('sodium') or '不明'} mg |

## 🍽️ 料理別栄養情報

"""
    
    for i, dish in enumerate(dishes, 1):
        dish_name = dish.get("dish_name", "不明")
        dish_nutrition = dish.get("total_nutrition", {})
        ingredients = dish.get("ingredients", [])
        
        content += f"""### {i}. {dish_name}

**栄養情報:**
- 🔥 カロリー: {dish_nutrition.get('calories', 0):.1f} kcal
- 🥩 タンパク質: {dish_nutrition.get('protein', 0):.1f} g
- 🧈 脂質: {dish_nutrition.get('fat', 0):.1f} g
- 🍞 炭水化物: {dish_nutrition.get('carbs', 0):.1f} g

**含まれる食材:** {len(ingredients)}個

"""
        
        for ingredient in ingredients:
            ing_name = ingredient.get("ingredient_name", "不明")
            weight = ingredient.get("weight_g", 0)
            ing_nutrition = ingredient.get("calculated_nutrition", {})
            
            content += f"- **{ing_name}** ({weight}g): {ing_nutrition.get('calories', 0):.1f} kcal\n"
        
        content += "\n"
    
    # 分析メタデータ
    image_metadata = result.get("image_metadata", {})
    processing_summary = result.get("processing_summary", {})
    
    content += f"""## 📈 分析メタデータ

- **分析日時:** {image_metadata.get('analysis_timestamp', '不明')}
- **処理時間:** {image_metadata.get('analysis_time_seconds', 0):.2f}秒
- **総食材数:** {processing_summary.get('total_ingredients', 0)}個
- **マッチ率:** {processing_summary.get('nutrition_search_match_rate', '不明')}
- **画像サイズ:** {image_metadata.get('image_size_bytes', 0):,} bytes

---
*Generated by Multi-Image Nutrition Analysis System*
"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


async def create_dish_details_markdown(result: dict, file_path: str, image_name: str):
    """料理別詳細情報のMarkdownを作成"""
    
    phase1_result = result.get("phase1_result", {})
    dishes = phase1_result.get("dishes", [])
    final_nutrition = result.get("final_nutrition_result", {})
    nutrition_dishes = final_nutrition.get("dishes", [])
    
    content = f"""# {image_name} 料理詳細分析

## 🔍 検出された料理一覧

"""
    
    for i, (phase1_dish, nutrition_dish) in enumerate(zip(dishes, nutrition_dishes), 1):
        dish_name = phase1_dish.get("dish_name", "不明")
        confidence = phase1_dish.get("confidence", 0.0)
        ingredients = phase1_dish.get("ingredients", [])
        nutrition_ingredients = nutrition_dish.get("ingredients", [])
        
        content += f"""## {i}. {dish_name}

**基本情報:**
- 🎯 信頼度: {confidence:.2f}
- 🥕 食材数: {len(ingredients)}個
- ⚖️ 総重量: {sum(ing.get('weight_g', 0) for ing in ingredients)}g

### 📋 食材詳細

| 食材名 | 重量 | カロリー | タンパク質 | 脂質 | 炭水化物 | データソース |
|--------|------|----------|------------|------|----------|--------------|
"""
        
        for phase1_ing, nutrition_ing in zip(ingredients, nutrition_ingredients):
            ing_name = phase1_ing.get("ingredient_name", "不明")
            weight = phase1_ing.get("weight_g", 0)
            nutrition = nutrition_ing.get("calculated_nutrition", {})
            source_db = nutrition_ing.get("source_db", "不明")
            
            content += f"| {ing_name} | {weight}g | {nutrition.get('calories', 0):.1f} kcal | {nutrition.get('protein', 0):.1f}g | {nutrition.get('fat', 0):.1f}g | {nutrition.get('carbs', 0):.1f}g | {source_db} |\n"
        
        # 料理の栄養合計
        dish_nutrition = nutrition_dish.get("total_nutrition", {})
        content += f"""
### 🔢 料理合計栄養

- **🔥 総カロリー:** {dish_nutrition.get('calories', 0):.1f} kcal
- **🥩 総タンパク質:** {dish_nutrition.get('protein', 0):.1f} g
- **🧈 総脂質:** {dish_nutrition.get('fat', 0):.1f} g
- **🍞 総炭水化物:** {dish_nutrition.get('carbs', 0):.1f} g

---

"""
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)


async def create_comprehensive_summary(all_results: List[Dict[str, Any]], results_dir: str):
    """全画像の包括的サマリーを作成"""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    summary_path = f"{results_dir}/comprehensive_analysis_summary.md"
    
    # 成功した分析のみを抽出
    successful_results = [r for r in all_results if r and "error" not in r]
    failed_results = [r for r in all_results if r and "error" in r]
    
    content = f"""# 🍽️ Multi-Image Nutrition Analysis - 包括的サマリー

**分析日時:** {datetime.now().strftime("%Y年%m月%d日 %H:%M:%S")}  
**分析画像数:** {len(all_results)}枚  
**成功分析:** {len(successful_results)}枚  
**失敗分析:** {len(failed_results)}枚  

## 📊 全画像栄養サマリー

| 画像 | 料理数 | 食材数 | 総カロリー | タンパク質 | 脂質 | 炭水化物 | 処理時間 |
|------|--------|--------|------------|------------|------|----------|----------|
"""
    
    total_calories = 0
    total_protein = 0
    total_fat = 0
    total_carbs = 0
    total_processing_time = 0
    
    for result in successful_results:
        image_name = result.get("image_metadata", {}).get("image_name", "不明")
        processing_summary = result.get("processing_summary", {})
        final_nutrition = result.get("final_nutrition_result", {})
        total_nutrition = final_nutrition.get("total_nutrition", {})
        
        dishes_count = processing_summary.get("total_dishes", 0)
        ingredients_count = processing_summary.get("total_ingredients", 0)
        calories = total_nutrition.get("calories", 0)
        protein = total_nutrition.get("protein", 0)
        fat = total_nutrition.get("fat", 0)
        carbs = total_nutrition.get("carbs", 0)
        processing_time = result.get("image_metadata", {}).get("analysis_time_seconds", 0)
        
        content += f"| {image_name} | {dishes_count} | {ingredients_count} | {calories:.1f} kcal | {protein:.1f}g | {fat:.1f}g | {carbs:.1f}g | {processing_time:.1f}s |\n"
        
        total_calories += calories
        total_protein += protein
        total_fat += fat
        total_carbs += carbs
        total_processing_time += processing_time
    
    # 合計行
    content += f"| **合計** | - | - | **{total_calories:.1f} kcal** | **{total_protein:.1f}g** | **{total_fat:.1f}g** | **{total_carbs:.1f}g** | **{total_processing_time:.1f}s** |\n"
    
    # 平均値
    if successful_results:
        avg_calories = total_calories / len(successful_results)
        avg_protein = total_protein / len(successful_results)
        avg_fat = total_fat / len(successful_results)
        avg_carbs = total_carbs / len(successful_results)
        avg_processing_time = total_processing_time / len(successful_results)
        
        content += f"| **平均** | - | - | **{avg_calories:.1f} kcal** | **{avg_protein:.1f}g** | **{avg_fat:.1f}g** | **{avg_carbs:.1f}g** | **{avg_processing_time:.1f}s** |\n"
    
    content += f"""

## 🎯 分析統計

### 📈 栄養統計
- **総カロリー摂取量:** {total_calories:.1f} kcal
- **総タンパク質:** {total_protein:.1f} g
- **総脂質:** {total_fat:.1f} g
- **総炭水化物:** {total_carbs:.1f} g

### ⚡ パフォーマンス統計
- **総処理時間:** {total_processing_time:.1f}秒
- **平均処理時間:** {avg_processing_time:.1f}秒/画像
- **成功率:** {len(successful_results)/len(all_results)*100:.1f}%

## 🍽️ 画像別詳細

"""
    
    for i, result in enumerate(successful_results, 1):
        image_name = result.get("image_metadata", {}).get("image_name", "不明")
        phase1_result = result.get("phase1_result", {})
        dishes = phase1_result.get("dishes", [])
        
        content += f"""### {i}. {image_name}

**検出された料理:**
"""
        
        for j, dish in enumerate(dishes, 1):
            dish_name = dish.get("dish_name", "不明")
            confidence = dish.get("confidence", 0.0)
            ingredients = dish.get("ingredients", [])
            content += f"- {j}. {dish_name} (信頼度: {confidence:.2f}, 食材: {len(ingredients)}個)\n"
        
        content += "\n"
    
    # エラー情報
    if failed_results:
        content += f"""## ❌ 分析エラー

"""
        for result in failed_results:
            image_name = result.get("image_name", "不明")
            error = result.get("error", "不明なエラー")
            content += f"- **{image_name}:** {error}\n"
    
    content += f"""

---
*Generated by Multi-Image Nutrition Analysis System - {timestamp}*
"""
    
    with open(summary_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n📋 包括的サマリー保存完了: {summary_path}")
    return summary_path


async def analyze_all_food_images():
    """food1-5の全画像を分析"""
    
    # 環境設定
    setup_environment()
    
    # 結果保存用ディレクトリを作成
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = f"analysis_results/multi_image_analysis_{timestamp}"
    os.makedirs(results_dir, exist_ok=True)
    
    print(f"🚀 Multi-Image Nutrition Analysis 開始")
    print(f"📁 結果保存ディレクトリ: {results_dir}")
    print(f"🔧 検索方法: MyNetDiary専用検索 + 栄養計算")
    print(f"📊 対象画像: food1.jpg - food5.jpg (5枚)")
    
    # 画像パスのリスト
    image_paths = [
        "test_images/food1.jpg",
        "test_images/food2.jpg", 
        "test_images/food3.jpg",
        "test_images/food4.jpg",
        "test_images/food5.jpg"
    ]
    
    all_results = []
    total_start_time = time.time()
    
    # 各画像を順次分析
    for i, image_path in enumerate(image_paths, 1):
        try:
            result = await analyze_single_image(image_path, results_dir, i)
            all_results.append(result)
        except Exception as e:
            print(f"❌ 画像 {i} の分析でエラーが発生: {str(e)}")
            all_results.append({
                "error": str(e),
                "image_name": Path(image_path).stem,
                "image_path": image_path
            })
    
    total_end_time = time.time()
    total_processing_time = total_end_time - total_start_time
    
    # 包括的サマリーを作成
    summary_path = await create_comprehensive_summary(all_results, results_dir)
    
    # 最終結果の表示
    successful_results = [r for r in all_results if r and "error" not in r]
    failed_results = [r for r in all_results if r and "error" in r]
    
    print(f"\n{'='*80}")
    print(f"🎯 Multi-Image Nutrition Analysis 完了!")
    print(f"{'='*80}")
    print(f"📊 分析結果サマリー:")
    print(f"   ✅ 成功: {len(successful_results)}/{len(all_results)} 画像")
    print(f"   ❌ 失敗: {len(failed_results)}/{len(all_results)} 画像")
    print(f"   ⏱️  総処理時間: {total_processing_time:.2f}秒")
    print(f"   📁 結果保存先: {results_dir}")
    print(f"   📋 包括的サマリー: {summary_path}")
    
    if successful_results:
        total_calories = sum(r.get("final_nutrition_result", {}).get("total_nutrition", {}).get("calories", 0) for r in successful_results)
        print(f"   🔥 総カロリー: {total_calories:.1f} kcal")
    
    print(f"{'='*80}")
    
    return all_results, results_dir


def main():
    """メイン実行関数"""
    print("🍽️ Multi-Image Nutrition Analysis Test")
    print("food1.jpg から food5.jpg まで5つの画像を一括分析します")
    print()
    
    # 非同期実行
    asyncio.run(analyze_all_food_images())


if __name__ == "__main__":
    main() 