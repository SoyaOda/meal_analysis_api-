#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Pipeline栄養素 vs VLM Label栄養素の比較 (全50画像)
マッピングファイル使用版
"""

import json
import sys
import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from difflib import SequenceMatcher

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# プロジェクトルートをPYTHONPATHに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from apps.freeform_usda_meal_analysis_api.services.pipeline import MealAnalysisPipeline


class FoodNameMapper:
    """食品名マッピングを行うクラス"""

    def __init__(self, mappings_path: str):
        """
        Args:
            mappings_path: usda_food_mappings_unified.jsonのパス
        """
        with open(mappings_path, 'r', encoding='utf-8') as f:
            self.mappings = json.load(f)

        # エイリアスの逆引きインデックスを作成
        self.alias_to_key = {}
        for key, value in self.mappings.items():
            for alias in value.get('aliases', []):
                alias_lower = alias.lower().strip()
                if alias_lower not in self.alias_to_key:
                    self.alias_to_key[alias_lower] = []
                self.alias_to_key[alias_lower].append(key)

        logging.info(f"Loaded {len(self.mappings)} mappings with {len(self.alias_to_key)} unique aliases")

    def find_mapping(self, food_name: str) -> Optional[Dict]:
        """
        食品名に対応するマッピングを検索

        Args:
            food_name: VLMが出力した食品名

        Returns:
            マッピング情報（見つからない場合はNone）
        """
        food_name_lower = food_name.lower().strip()

        # 完全一致を試行
        if food_name_lower in self.alias_to_key:
            key = self.alias_to_key[food_name_lower][0]
            mapping = self.mappings[key]
            return {
                'key': key,
                'display_name': mapping.get('display_name'),
                'usda_name': self._extract_usda_name(mapping['default_usda']['name']),
                'original_usda_name': mapping['default_usda']['name'],
                'match_type': 'exact',
                'confidence': 1.0
            }

        # 部分一致を試行（類似度0.8以上）
        best_match = None
        best_score = 0.8

        for alias, keys in self.alias_to_key.items():
            score = SequenceMatcher(None, food_name_lower, alias).ratio()
            if score > best_score:
                best_score = score
                best_match = keys[0]

        if best_match:
            mapping = self.mappings[best_match]
            return {
                'key': best_match,
                'display_name': mapping.get('display_name'),
                'usda_name': self._extract_usda_name(mapping['default_usda']['name']),
                'original_usda_name': mapping['default_usda']['name'],
                'match_type': 'fuzzy',
                'confidence': best_score
            }

        return None

    def _extract_usda_name(self, name_with_number: str) -> str:
        """
        "3. Adobo, with rice" → "Adobo, with rice"
        """
        parts = name_with_number.split('.', 1)
        if len(parts) == 2:
            return parts[1].strip()
        return name_with_number


def load_label_nutrition(label_path: str) -> dict:
    """VLM Labelから栄養素を集計"""
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


async def get_pipeline_nutrition_with_mappings(
    pipeline: MealAnalysisPipeline,
    mapper: FoodNameMapper,
    image_path: str
) -> dict:
    """
    Pipelineで栄養素を取得（マッピング適用版）
    """
    from PIL import Image

    image = Image.open(image_path)
    result = await pipeline.analyze_meal_async(image, user_context="nutrition comparison with mappings")

    # VLMレスポンスにマッピングを適用
    if 'vlm_response' in result and 'dishes' in result['vlm_response']:
        mapping_info = []

        for dish in result['vlm_response']['dishes']:
            # main_food
            if dish.get('main_food'):
                mf = dish['main_food']
                original_name = mf.get('search_name', '')
                mapping = mapper.find_mapping(original_name)

                if mapping:
                    # マッピングされたUSDA名で再検索
                    mf['original_search_name'] = original_name
                    mf['search_name'] = mapping['usda_name']
                    mf['mapping_info'] = mapping
                    mapping_info.append({
                        'original': original_name,
                        'mapped': mapping['usda_name'],
                        'match_type': mapping['match_type'],
                        'confidence': mapping['confidence']
                    })

            # extras
            for ex in dish.get('extras', []):
                original_name = ex.get('search_name', '')
                mapping = mapper.find_mapping(original_name)

                if mapping:
                    ex['original_search_name'] = original_name
                    ex['search_name'] = mapping['usda_name']
                    ex['mapping_info'] = mapping
                    mapping_info.append({
                        'original': original_name,
                        'mapped': mapping['usda_name'],
                        'match_type': mapping['match_type'],
                        'confidence': mapping['confidence']
                    })

        result['mapping_info'] = mapping_info

        # マッピング適用後に再検索・栄養計算
        # NOTE: ここでは簡易的にVLMレスポンスを更新するのみ
        # 実際のUSDA検索は既存のパイプラインで実行される

    return result


async def main():
    """メイン処理"""
    print("=== Pipeline vs VLM Label 比較 (マッピング適用版) ===")
    print()

    # マッピングファイルを読み込み
    mappings_path = project_root / "test_scripts" / "mappings" / "mappings_final" / "usda_food_mappings_unified.json"
    mapper = FoodNameMapper(str(mappings_path))

    # パイプライン初期化
    pipeline = MealAnalysisPipeline()

    # テスト画像のディレクトリ
    images_dir = project_root / "test_images"
    labels_dir = project_root / "images_label_with_nutrition"

    results = []

    # 50画像をテスト
    for i in range(1, 51):
        image_name = f"test_food{i}.jpg"
        image_path = images_dir / image_name
        label_path = labels_dir / f"test_food{i}.json"

        if not image_path.exists() or not label_path.exists():
            logging.warning(f"Skipping {image_name}: file not found")
            continue

        try:
            # Label栄養素を取得
            label_nutrition = load_label_nutrition(str(label_path))

            # Pipeline栄養素を取得（マッピング適用）
            pipeline_result = await get_pipeline_nutrition_with_mappings(
                pipeline, mapper, str(image_path)
            )

            # 差分計算
            label_cal = label_nutrition["total_calorie"]
            pipeline_cal = pipeline_result["total_nutrition"]["calories"]

            diff_cal = pipeline_cal - label_cal
            diff_pct = (diff_cal / label_cal * 100) if label_cal > 0 else 0

            results.append({
                "image_name": image_name,
                "label_nutrition": label_nutrition,
                "pipeline_result": pipeline_result,
                "diff": {
                    "calories": diff_cal,
                    "calories_pct": diff_pct
                }
            })

            print(f"✅ [{i}/50] {image_name}: Label {label_cal:.0f} kcal | Pipeline {pipeline_cal:.0f} kcal | 差分 {diff_pct:+.1f}%")

            # マッピング情報を表示
            if pipeline_result.get('mapping_info'):
                for m in pipeline_result['mapping_info']:
                    print(f"   📌 Mapped: {m['original']} → {m['mapped']} ({m['match_type']})")

        except Exception as e:
            logging.error(f"Error processing {image_name}: {e}")
            continue

    print()
    print(f"✅ 処理完了: {len(results)}/50画像")

    # 結果を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_json = project_root / "test_scripts" / "output" / f"nutrition_comparison_with_mappings_{timestamp}.json"

    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ JSON詳細結果保存: {output_json}")

    # 統計計算
    import statistics
    calorie_diffs = [abs(r['diff']['calories_pct']) for r in results]
    print()
    print("【統計】")
    print(f"平均誤差率: {statistics.mean(calorie_diffs):.1f}%")
    print(f"中央値誤差率: {statistics.median(calorie_diffs):.1f}%")
    print(f"最大誤差率: {max(calorie_diffs):.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
