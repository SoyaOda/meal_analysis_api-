#!/usr/bin/env python3
"""
1,152食材用データ後処理スクリプト

生データからノイズを除去し、APIで使用可能な
クリーンなフォーマットに変換して出力する
"""

import json
import os
import re
from datetime import datetime
from typing import Dict, List, Any, Set, Tuple, Optional
from pathlib import Path


class FoodDataProcessor:
    """食材データ後処理クラス"""

    def __init__(self):
        """初期化"""
        self.base_dir = Path('.')
        self.catalog_dir = self.base_dir / 'food_catalog_data'
        self.data_dir = self.base_dir / 'data'
        self.output_dir = self.base_dir / 'processed_data'
        
        # 除外対象の食材
        self.excluded_foods = {
            "Sea salt non-iodized, tsp 0cals",
            "Olives kalamata pitted, olives 9cals"
        }
        
        # 処理結果格納用
        self.processed_foods = []

    def load_catalog_foods(self) -> List[Dict[str, Any]]:
        """カタログから食材リストを読み込み"""
        print("📁 カタログ食材読み込み中...")

        all_foods = []
        catalog_files = [f for f in os.listdir(self.catalog_dir) if f.endswith('.json')]

        for file_name in catalog_files:
            file_path = os.path.join(self.catalog_dir, file_name)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                category_data = data.get("category_data", {})
                foods = category_data.get("foods", [])

                for food in foods:
                    food_name = food.get("food_name", "").strip()
                    if food_name:
                        normalized_name = re.sub(r'\n', ' ', food_name).strip()

                        # 除外食材チェック
                        if normalized_name not in self.excluded_foods:
                            food["normalized_name"] = normalized_name
                            all_foods.append(food)

            except Exception as e:
                print(f"  ❌ {file_name}読み込みエラー: {e}")

        print(f"✅ 有効食材: {len(all_foods)}個読み込み完了")
        self.catalog_foods = all_foods
        return all_foods

    def load_raw_data(self) -> Dict[str, Any]:
        """生データを読み込み（複数エントリーから最新成功データを選択）"""
        print("📁 生データ読み込み中...")

        latest_file = self.find_latest_collection_file()
        if not latest_file:
            print("❌ 収集済みデータファイルが見つかりません")
            return {}

        print(f"📄 対象ファイル: {os.path.basename(latest_file)}")

        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            collection_results = data.get("collection_results", [])
            print(f"📊 総エントリー数: {len(collection_results)}")

            # 食材名をキーとした辞書を作成（複数エントリーから最適選択）
            raw_dict = {}
            food_entry_counts = {}
            
            for i, result in enumerate(collection_results):
                food_name = result.get("food_name", "").strip()
                normalized_name = re.sub(r'\n', ' ', food_name).strip()

                # 除外食材チェック
                if normalized_name in self.excluded_foods:
                    continue

                # エントリーカウント追跡
                if normalized_name not in food_entry_counts:
                    food_entry_counts[normalized_name] = 0
                food_entry_counts[normalized_name] += 1

                # データ収集成功判定
                data_success = result.get("data_collection_success", False)
                overall_success = result.get("overall_success", False)
                
                # 既存エントリーがある場合の選択ロジック
                if normalized_name in raw_dict:
                    existing = raw_dict[normalized_name]
                    existing_success = existing.get("data_collection_success", False)
                    existing_overall = existing.get("overall_success", False)
                    
                    # 優先順位: 1) 両方成功 > 2) データ収集のみ成功 > 3) 失敗
                    current_priority = self._get_success_priority(data_success, overall_success)
                    existing_priority = self._get_success_priority(existing_success, existing_overall)
                    
                    # より高い優先度、または同じ優先度で後のエントリー（より新しい）を選択
                    if current_priority > existing_priority or (current_priority == existing_priority and i > existing.get("_entry_index", -1)):
                        result["_entry_index"] = i
                        raw_dict[normalized_name] = result
                else:
                    result["_entry_index"] = i
                    raw_dict[normalized_name] = result

            # 複数エントリー統計
            multiple_entries = {name: count for name, count in food_entry_counts.items() if count > 1}
            if multiple_entries:
                print(f"📋 複数エントリー食材: {len(multiple_entries)}個")
                for name, count in sorted(multiple_entries.items(), key=lambda x: x[1], reverse=True)[:5]:
                    selected = raw_dict[name]
                    success_status = "✅成功" if selected.get("data_collection_success", False) else "❌失敗"
                    print(f"  - {name}: {count}エントリー → {success_status}")

            print(f"✅ 生データ: {len(raw_dict)}個読み込み完了")
            self.raw_data = raw_dict
            return raw_dict

        except Exception as e:
            print(f"❌ 生データ読み込みエラー: {e}")
            return {}

    def _get_success_priority(self, data_success: bool, overall_success: bool) -> int:
        """成功状態の優先度を計算"""
        if data_success and overall_success:
            return 3  # 最高優先度
        elif data_success:
            return 2  # 中優先度
        else:
            return 1  # 最低優先度

    def find_latest_collection_file(self):
        """最新の収集済みデータファイルを検索（完全版を優先）"""
        pattern = "comprehensive_food_collection_*.json"
        files = list(self.data_dir.glob(pattern))
        
        if not files:
            print("❌ 収集済みデータファイルが見つかりません")
            return None
        
        # 完全版ファイル（intermediateを含まない）を優先
        complete_files = [f for f in files if 'intermediate' not in f.name]
        
        if complete_files:
            # 完全版ファイルがある場合は最新のものを返す
            latest_file = max(complete_files, key=lambda f: f.stat().st_mtime)
            return latest_file
        else:
            # 完全版がない場合は中間ファイルの最新を返す
            latest_file = max(files, key=lambda f: f.stat().st_mtime)
            return latest_file

    def clean_nutrition_data(self, raw_nutrition_data: List[str]) -> List[Dict[str, Any]]:
        """栄養素データのクリーニング"""
        if not raw_nutrition_data:
            return []

        # 有効な栄養素パターン
        nutrition_patterns = [
            (r"(Total Fat)\s+(\d+\.?\d*)g", "total_fat", "g"),
            (r"(Saturated Fat)\s+(\d+\.?\d*)g", "saturated_fat", "g"),
            (r"(Trans Fat)\s+(\d+\.?\d*)g", "trans_fat", "g"),
            (r"(Monounsaturated Fat)\s+(\d+\.?\d*)g", "monounsaturated_fat", "g"),
            (r"(Polyunsaturated Fat)\s+(\d+\.?\d*)g", "polyunsaturated_fat", "g"),
            (r"(Cholesterol)\s+(\d+\.?\d*)mg", "cholesterol", "mg"),
            (r"(Sodium)\s+(\d+\.?\d*)mg", "sodium", "mg"),
            (r"(Total Carbs)\s+(\d+\.?\d*)g", "total_carbs", "g"),
            (r"(Net Carbs)\s+(\d+\.?\d*)g", "net_carbs", "g"),
            (r"(Dietary Fiber)\s+(\d+\.?\d*)g", "dietary_fiber", "g"),
            (r"(Total Sugars)\s+(\d+\.?\d*)g", "total_sugars", "g"),
            (r"(Protein)\s+(\d+\.?\d*)g", "protein", "g"),
            (r"(Calories)\s+(\d+\.?\d*)cals", "calories", "kcal"),
            (r"(Vitamin A)\s+(\d+\.?\d*)(mg|mcg)", "vitamin_a", None),
            (r"(Vitamin C)\s+(\d+\.?\d*)mg", "vitamin_c", "mg"),
            (r"(Calcium)\s+(\d+\.?\d*)mg", "calcium", "mg"),
            (r"(Iron)\s+(\d+\.?\d*)mg", "iron", "mg"),
            (r"(Potassium)\s+(\d+\.?\d*)mg", "potassium", "mg"),
            (r"(Alcohol)\s+(\d+\.?\d*)g", "alcohol", "g"),
            (r"(Caffeine)\s+(\d+\.?\d*)mg", "caffeine", "mg")
        ]

        cleaned_nutrients = []

        for item in raw_nutrition_data:
            if not isinstance(item, str):
                continue

            for pattern, key, default_unit in nutrition_patterns:
                match = re.search(pattern, item, re.IGNORECASE)
                if match:
                    name = match.group(1)
                    value = float(match.group(2))

                    # 単位の決定
                    if default_unit is None and len(match.groups()) > 2:
                        unit = match.group(3)
                    else:
                        unit = default_unit

                    cleaned_nutrients.append({
                        "name": name,
                        "key": key,
                        "value": value,
                        "unit": unit,
                        "raw_text": item.strip()
                    })
                    break

        return cleaned_nutrients

    def clean_serving_data(self, raw_serving_data):
        """サービングデータのクリーニング（改善版：完全な形式のみを使用）"""
        if not raw_serving_data:
            return []
        
        # raw_serving_dataから実際のリストを取得
        if isinstance(raw_serving_data, dict):
            actual_raw_data = raw_serving_data.get('raw_serving_data', [])
        elif isinstance(raw_serving_data, list):
            actual_raw_data = raw_serving_data
        else:
            return []
        
        if not actual_raw_data:
            return []
        
        # 完全な形式の行のみを抽出: "unit XXcals / Xg"
        # パターン1: 数値プレフィックス付き (例: "3 oz 155cals / 85 g")
        # パターン2: 通常の形式 (例: "gram 2cals / 1 g")
        # パターン3: 複雑な記述 (例: "ear, small (...) 63cals / 73 g")
        
        pattern1 = r'^(\d+(?:\.\d+)?)\s+([\w\s\.\-\(\)"/,]+?)\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s*cals?\s*/\s*(\d+(?:\.\d+)?)\s*g\s*$'
        pattern2 = r'^([\w\s\.\-\(\)"/,]+?)\s+(\d+(?:,\d{3})*(?:\.\d+)?)\s*cals?\s*/\s*(\d+(?:\.\d+)?)\s*g\s*$'
        
        valid_servings = []
        processed_units = set()
        
        for line in actual_raw_data:
            if not isinstance(line, str):
                continue
            
            line_stripped = line.strip()
            
            # パターン1: 数値プレフィックス付き
            match1 = re.match(pattern1, line_stripped, re.IGNORECASE)
            if match1:
                quantity = match1.group(1)
                unit = match1.group(2).strip()
                calories_str = match1.group(3).replace(',', '')
                grams = float(match1.group(4))
                calories = float(calories_str)
                
                # 数値プレフィックス付きunitとして保存
                full_unit = f"{quantity} {unit}"
                unit_clean = self._clean_unit_name(full_unit)
                
                if unit_clean and len(unit_clean) <= 50:
                    unit_key = unit_clean.lower()
                    if unit_key not in processed_units:
                        processed_units.add(unit_key)
                        
                        valid_servings.append({
                            "unit": unit_clean,
                            "calories_per_unit": round(calories, 1),
                            "grams_per_unit": round(grams, 1),
                            "conversion_factor": round(grams, 1),
                            "calories_per_gram": round(calories / grams, 4) if grams > 0 else 0,
                            "display_text": f"{unit_clean} ({round(grams, 1)}g) = {round(calories, 1)} kcal",
                            "source": "complete_line_with_quantity"
                        })
                continue
            
            # パターン2: 通常の形式または複雑な記述
            match2 = re.match(pattern2, line_stripped, re.IGNORECASE)
            if match2:
                unit = match2.group(1).strip()
                calories_str = match2.group(2).replace(',', '')
                grams = float(match2.group(3))
                calories = float(calories_str)
                
                unit_clean = self._clean_unit_name(unit)
                
                if unit_clean and len(unit_clean) <= 50:
                    unit_key = unit_clean.lower()
                    if unit_key not in processed_units:
                        processed_units.add(unit_key)
                        
                        valid_servings.append({
                            "unit": unit_clean,
                            "calories_per_unit": round(calories, 1),
                            "grams_per_unit": round(grams, 1),
                            "conversion_factor": round(grams, 1),
                            "calories_per_gram": round(calories / grams, 4) if grams > 0 else 0,
                            "display_text": f"1 {unit_clean} ({round(grams, 1)}g) = {round(calories, 1)} kcal",
                            "source": "complete_line"
                        })
        
        # ソート（gramを最初に、その後はアルファベット順）
        def serving_sort_key(s):
            unit = s["unit"].lower()
            if unit == "gram":
                return "0_gram"
            return f"1_{unit}"
        
        valid_servings.sort(key=serving_sort_key)

        return valid_servings
    
    def _clean_unit_name(self, unit_text):
        """単位名をクリーニングして標準化（特殊なunitもそのまま保存）"""
        if not unit_text or not isinstance(unit_text, str):
            return None
        
        unit_lower = unit_text.lower().strip()
        
        # calsプレフィックスを削除
        unit_lower = re.sub(r'^cals\s+', '', unit_lower)
        
        # 数値プレフィックスを持つunitの場合
        # 例: "3 oz", "0.5 fillet", "ear, small (5-1/2" to 6-1/2" long)"
        numeric_prefix_match = re.match(r'^(\d+(?:\.\d+)?)\s+(.+)$', unit_lower)
        
        if numeric_prefix_match:
            # 数値部分と単位部分を分離
            quantity = numeric_prefix_match.group(1)
            unit_part = numeric_prefix_match.group(2).strip()
            
            # 単位部分を標準化（標準的なunitの場合）
            standardized_unit = self._standardize_unit(unit_part)
            
            # 数値 + 標準化された単位を返す
            return f"{quantity} {standardized_unit}"
        
        # 数値プレフィックスがない場合は、単位のみを標準化
        standardized = self._standardize_unit(unit_lower)
        return standardized
    
    def _standardize_unit(self, unit_text):
        """単位部分のみを標準化するヘルパー関数（完全一致のみ標準化）"""
        if not unit_text:
            return None
        
        unit_lower = unit_text.lower().strip()
        
        # 標準的な単位パターン（重要: 長いパターンを先に配置!）
        # 注意: これらは完全一致の場合のみ適用される
        standard_units = {
            'fl oz': 'fl oz',
            'fluid ounce': 'fl oz',
            'tablespoon': 'tablespoon',
            'tbsp': 'tablespoon',
            'tbs': 'tablespoon',
            'teaspoon': 'teaspoon',
            'tsp': 'teaspoon',
            'ounce': 'oz',
            'oz': 'oz',
            'gram': 'gram',
            'g': 'gram',
            'cup': 'cup',
            'cups': 'cup',
            'pound': 'lb',
            'lb': 'lb',
            'lbs': 'lb',
            'ml': 'ml',
            'milliliter': 'ml',
            'liter': 'liter',
            'l': 'liter',
            'serving': 'serving',
            'servings': 'serving',
            'piece': 'piece',
            'pieces': 'piece',
            'slice': 'slice',
            'slices': 'slice',
            'each': 'each'
        }
        
        # 完全一致チェック（標準的なunitのみ正規化）
        if unit_lower in standard_units:
            return standard_units[unit_lower]
        
        # 完全一致しない場合は、特殊なunit形式として全体を保存
        # 例: "slice, large", "can (10.75 oz)", "ear, small (5-1/2\" to 6-1/2\" long)"
        # 最大50文字まで、かつ英数字と特定の記号のみ許可
        if len(unit_lower) <= 50 and re.match(r'^[\w\s\.\-\(\)"/,]+$', unit_lower):
            return unit_lower
        
        # それ以外はNone
        return None

    def _is_valid_serving_text(self, text: str) -> bool:
        """
        Servingテキストが有効な食材データか判定（HTML/CSS/JSゴミを除外）

        Args:
            text: 検証するテキスト

        Returns:
            bool: 有効な場合True、ゴミデータの場合False
        """
        if not text or not isinstance(text, str):
            return False

        text_lower = text.lower().strip()

        # 必須条件: "cals"と"g"を含む（正しいservingデータの特徴）
        if 'cals' not in text_lower or 'g' not in text_lower:
            return False

        # 除外パターン: HTML/CSS/JavaScript
        invalid_patterns = [
            'var ', 'function', 'const ', 'let ', 'return',  # JavaScript
            '.mui', '.jss', 'class=', 'id=',  # CSS/HTML
            '{', '}', '<', '>',  # HTML/CSS構文
            'px', 'em', 'rem', 'flex', 'display:',  # CSSプロパティ
            'padding:', 'margin:', 'background',  # CSSプロパティ
            'overflow:', 'position:', 'z-index',  # CSSプロパティ
            'isadmin', 'mobilelinking', 'plateai'  # 変数名
        ]

        for pattern in invalid_patterns:
            if pattern in text_lower:
                return False

        return True

    def extract_essential_nutrition(self, food_name, nutrition_data, serving_data):
        """必須栄養項目を抽出（確定的アルゴリズム）"""
        essential = {
            "calories": None,
            "serving_size": None,
            "macros": {
                "total_fat": None,
                "total_carbs": None,
                "protein": None
            },
            "serving_info": {
                "unit": None,
                "grams": None
            }
        }
        
        # 1. 食材名からカロリー値を抽出
        # パターン: "Arrowroot flour, cup\n457cals" -> 457
        calories_match = re.search(r'(\d+(?:\.\d+)?)\s*cals?', food_name.replace('\n', ' '))
        if calories_match:
            essential["calories"] = {
                "value": float(calories_match.group(1)),
                "unit": "kcal",
                "source": "food_name"
            }
        
        # 2. 食材名からServing単位を抽出
        # パターン: "Arrowroot flour, cup\n457cals" -> "cup"
        # 改行を含む場合があるので正規化
        clean_name = food_name.replace('\n', ' ').strip()
        # "食材名, 単位 数値cals" のパターンを想定
        serving_pattern = r',\s*([a-zA-Z\s/]+?)\s+\d+(?:\.\d+)?\s*cals?'
        serving_match = re.search(serving_pattern, clean_name)
        if serving_match:
            serving_unit = serving_match.group(1).strip()
            essential["serving_info"]["unit"] = serving_unit
        
        # 3. Serving Dataから詳細なServing Size情報を抽出
        # パターン: "cup 457cals / 128 g" -> unit="cup", calories=457, grams=128
        if serving_data and "raw_serving_data" in serving_data:
            # 有効なservingデータを収集
            valid_servings = []

            for item in serving_data["raw_serving_data"]:
                # バリデーション：HTML/CSS/JSゴミを除外
                if not self._is_valid_serving_text(item):
                    continue

                # "unit Xcals / Y g" パターンを探す
                serving_pattern = r'^([a-zA-Z\s/]+?)\s+(\d+(?:\.\d+)?)\s*cals?\s*/\s*(\d+(?:\.\d+)?)\s*g$'
                match = re.match(serving_pattern, item.strip())
                if match:
                    unit = match.group(1).strip()
                    calories = float(match.group(2))
                    grams = float(match.group(3))

                    valid_servings.append({
                        "unit": unit,
                        "calories": calories,
                        "grams": grams,
                        "raw_text": item
                    })

            # 有効なservingから最適なものを選択
            if valid_servings:
                # 優先順位1: 食材名の単位と一致するもの
                target_unit = essential["serving_info"]["unit"]
                matched_serving = None

                if target_unit:
                    for serving in valid_servings:
                        if serving["unit"].lower() == target_unit.lower():
                            matched_serving = serving
                            break

                # 優先順位2: 一致しない場合は最初の有効なservingを使用
                if not matched_serving:
                    matched_serving = valid_servings[0]

                # serving_sizeを設定
                essential["serving_info"]["grams"] = matched_serving["grams"]
                essential["serving_size"] = {
                    "value": 1.0,
                    "unit": matched_serving["unit"],
                    "grams": matched_serving["grams"],
                    "calories": matched_serving["calories"],
                    "raw_text": matched_serving["raw_text"]
                }
                # カロリー情報も更新（より正確）
                essential["calories"] = {
                    "value": matched_serving["calories"],
                    "unit": "kcal",
                    "source": "serving_data"
                }
        
        # 4. 栄養データから基本マクロ栄養素を抽出
        if nutrition_data and "detailed_nutrients" in nutrition_data:
            nutrients = nutrition_data["detailed_nutrients"]
            if "raw_nutrition_data" in nutrients:
                raw_data = nutrients["raw_nutrition_data"]
                
                # パターン: ["Total Fat 0.1g", "Total Fat", "0.1g", ...]
                for i, item in enumerate(raw_data):
                    if isinstance(item, str):
                        # "Total Fat 0.1g" パターン
                        fat_match = re.match(r'^Total Fat\s+(\d+(?:\.\d+)?)\s*(g|mg)$', item.strip())
                        if fat_match:
                            essential["macros"]["total_fat"] = {
                                "value": float(fat_match.group(1)),
                                "unit": fat_match.group(2),
                                "raw_text": item
                            }
                            continue
                        
                        # "Total Carbs 113g" パターン
                        carbs_match = re.match(r'^Total Carbs?\s+(\d+(?:\.\d+)?)\s*(g|mg)$', item.strip())
                        if carbs_match:
                            essential["macros"]["total_carbs"] = {
                                "value": float(carbs_match.group(1)),
                                "unit": carbs_match.group(2),
                                "raw_text": item
                            }
                            continue
                        
                        # "Protein 0g" パターン
                        protein_match = re.match(r'^Protein\s+(\d+(?:\.\d+)?)\s*(g|mg)$', item.strip())
                        if protein_match:
                            essential["macros"]["protein"] = {
                                "value": float(protein_match.group(1)),
                                "unit": protein_match.group(2),
                                "raw_text": item
                            }
                            continue
        
        # 5. カロリー情報の追加確認（栄養データから）
        if not essential["calories"] and nutrition_data and "detailed_nutrients" in nutrition_data:
            nutrients = nutrition_data["detailed_nutrients"]
            if "raw_nutrition_data" in nutrients:
                for item in nutrients["raw_nutrition_data"]:
                    if isinstance(item, str):
                        # "Calories 457" や "Energy 457kcal" パターン
                        cal_match = re.match(r'^(?:Calories?|Energy)\s+(\d+(?:\.\d+)?)\s*(?:kcal|cal)?$', item.strip())
                        if cal_match:
                            essential["calories"] = {
                                "value": float(cal_match.group(1)),
                                "unit": "kcal",
                                "source": "nutrition_data",
                                "raw_text": item
                            }
                            break
        
        return essential

    def process_single_food(self, catalog_food: Dict[str, Any], raw_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """単一食材の処理"""
        food_name = catalog_food["normalized_name"]
        category = catalog_food.get("category", "Unknown")

        # データ存在チェック
        if not raw_result.get("data_collection_success", False):
            return None

        comprehensive_data = raw_result.get("comprehensive_data", {})
        if not comprehensive_data:
            return None

        # 栄養素データ処理
        nutrition_data = comprehensive_data.get("nutrition_data", {})
        detailed_nutrients = nutrition_data.get("detailed_nutrients", {})
        raw_nutrition = detailed_nutrients.get("raw_nutrition_data", [])

        cleaned_nutrition = self.clean_nutrition_data(raw_nutrition)

        # サービングデータ処理
        serving_options = comprehensive_data.get("serving_options", {})
        raw_serving = serving_options.get("raw_serving_data", [])

        cleaned_serving = self.clean_serving_data(raw_serving)

        # 基本品質チェック（栄養素2個以上、サービング2個以上）
        if len(cleaned_nutrition) < 2 or len(cleaned_serving) < 2:
            return None

        # 必須栄養項目を抽出
        essential_nutrition = self.extract_essential_nutrition(
            food_name, 
            {"detailed_nutrients": detailed_nutrients}, 
            {"raw_serving_data": raw_serving}
        )

        # 処理済み食材データ構築
        processed_food = {
            "food_id": f"food_{len(self.processed_foods) + 1:04d}",
            "food_name": food_name,
            "category": category,
            "essential_nutrition": essential_nutrition,  # 必須栄養項目追加
            "nutrition_facts": {
                "nutrients": cleaned_nutrition,
                "total_nutrients": len(cleaned_nutrition)
            },
            "serving_options": {
                "servings": cleaned_serving,
                "total_servings": len(cleaned_serving)
            },
            "metadata": {
                "processed_at": datetime.now().isoformat(),
                "original_collection_success": raw_result.get("data_collection_success", False),
                "raw_nutrition_count": len(raw_nutrition),
                "raw_serving_count": len(raw_serving),
                "essential_extraction_success": {
                    "calories": essential_nutrition["calories"] is not None,
                    "serving_size": essential_nutrition["serving_size"] is not None,
                    "total_fat": essential_nutrition["macros"]["total_fat"] is not None,
                    "total_carbs": essential_nutrition["macros"]["total_carbs"] is not None,
                    "protein": essential_nutrition["macros"]["protein"] is not None
                }
            }
        }

        return processed_food

    def process_all_foods(self) -> List[Dict[str, Any]]:
        """全食材を処理"""
        print("🔄 1,152食材の後処理実行中...")

        if not self.catalog_foods or not self.raw_data:
            print("❌ カタログまたは生データが読み込まれていません")
            return []

        processed_count = 0
        skipped_count = 0

        for catalog_food in self.catalog_foods:
            food_name = catalog_food["normalized_name"]
            raw_result = self.raw_data.get(food_name)

            if not raw_result:
                skipped_count += 1
                continue

            processed_food = self.process_single_food(catalog_food, raw_result)

            if processed_food:
                self.processed_foods.append(processed_food)
                processed_count += 1
            else:
                skipped_count += 1

        print(f"✅ 処理完了: {processed_count}個成功, {skipped_count}個スキップ")
        return self.processed_foods

    
    def analyze_failed_foods(self, catalog_foods, raw_data_dict):
        """失敗した食材の詳細分析"""
        failed_analysis = {
            "total_failed": 0,
            "failure_reasons": {
                "no_data_collection_success": [],
                "no_comprehensive_data": [],
                "insufficient_nutrition": [],
                "insufficient_serving": [],
                "serving_parsing_failed": [],
                "nutrition_parsing_failed": []
            },
            "detailed_failures": []
        }
        
        print("\n🔍 失敗食材の詳細分析開始...")
        
        for catalog_food in catalog_foods:
            food_name = catalog_food["normalized_name"]
            
            # 対応する生データを検索
            raw_result = raw_data_dict.get(food_name)
            
            if not raw_result:
                failed_analysis["failure_reasons"]["no_data_collection_success"].append(food_name)
                failed_analysis["detailed_failures"].append({
                    "food_name": food_name,
                    "reason": "no_raw_data_found",
                    "details": "対応する生データが見つからない"
                })
                continue
            
            # データ収集成功チェック
            if not raw_result.get("data_collection_success", False):
                failed_analysis["failure_reasons"]["no_data_collection_success"].append(food_name)
                failed_analysis["detailed_failures"].append({
                    "food_name": food_name,
                    "reason": "data_collection_failed",
                    "details": f"navigation_success: {raw_result.get('navigation_success')}, data_collection_success: {raw_result.get('data_collection_success')}"
                })
                continue
            
            comprehensive_data = raw_result.get("comprehensive_data", {})
            if not comprehensive_data:
                failed_analysis["failure_reasons"]["no_comprehensive_data"].append(food_name)
                failed_analysis["detailed_failures"].append({
                    "food_name": food_name,
                    "reason": "no_comprehensive_data",
                    "details": "comprehensive_dataが空"
                })
                continue
            
            # 栄養データ分析
            nutrition_data = comprehensive_data.get("nutrition_data", {})
            detailed_nutrients = nutrition_data.get("detailed_nutrients", {})
            raw_nutrition = detailed_nutrients.get("raw_nutrition_data", [])
            
            try:
                cleaned_nutrition = self.clean_nutrition_data(raw_nutrition)
            except Exception as e:
                failed_analysis["failure_reasons"]["nutrition_parsing_failed"].append(food_name)
                failed_analysis["detailed_failures"].append({
                    "food_name": food_name,
                    "reason": "nutrition_parsing_error",
                    "details": f"栄養データ解析エラー: {str(e)}, raw_count: {len(raw_nutrition)}"
                })
                continue
            
            # サービングデータ分析
            serving_options = comprehensive_data.get("serving_options", {})
            raw_serving = serving_options.get("raw_serving_data", [])
            
            try:
                cleaned_serving = self.clean_serving_data(raw_serving)
            except Exception as e:
                failed_analysis["failure_reasons"]["serving_parsing_failed"].append(food_name)
                failed_analysis["detailed_failures"].append({
                    "food_name": food_name,
                    "reason": "serving_parsing_error",
                    "details": f"サービングデータ解析エラー: {str(e)}, raw_count: {len(raw_serving)}"
                })
                continue
            
            # 品質チェック
            if len(cleaned_nutrition) < 2:
                failed_analysis["failure_reasons"]["insufficient_nutrition"].append(food_name)
                failed_analysis["detailed_failures"].append({
                    "food_name": food_name,
                    "reason": "insufficient_nutrition",
                    "details": f"栄養素数不足: {len(cleaned_nutrition)}個 (必要: 2個以上), raw_count: {len(raw_nutrition)}",
                    "sample_raw_nutrition": raw_nutrition[:10] if raw_nutrition else []  # サンプルデータ
                })
                continue
            
            if len(cleaned_serving) < 2:
                failed_analysis["failure_reasons"]["insufficient_serving"].append(food_name)
                failed_analysis["detailed_failures"].append({
                    "food_name": food_name,
                    "reason": "insufficient_serving",
                    "details": f"サービング数不足: {len(cleaned_serving)}個 (必要: 2個以上), raw_count: {len(raw_serving)}",
                    "sample_raw_serving": raw_serving[:10] if raw_serving else []  # サンプルデータ
                })
                continue
        
        # 統計計算
        failed_analysis["total_failed"] = sum(len(reasons) for reasons in failed_analysis["failure_reasons"].values())
        
        return failed_analysis

    def generate_summary_stats(self) -> Dict[str, Any]:
        """サマリー統計を生成"""
        if not self.processed_foods:
            return {}

        # カテゴリ別統計
        category_stats = {}

        for food in self.processed_foods:
            category = food["category"]

            if category not in category_stats:
                category_stats[category] = {
                    "count": 0,
                    "avg_nutrition": 0,
                    "avg_serving": 0
                }

            category_stats[category]["count"] += 1
            category_stats[category]["avg_nutrition"] += food["nutrition_facts"]["total_nutrients"]
            category_stats[category]["avg_serving"] += food["serving_options"]["total_servings"]

        # 平均値計算
        for category in category_stats:
            count = category_stats[category]["count"]
            category_stats[category]["avg_nutrition"] /= count
            category_stats[category]["avg_serving"] /= count

        return {
            "total_processed_foods": len(self.processed_foods),
            "category_breakdown": category_stats,
            "processing_timestamp": datetime.now().isoformat()
        }

    def save_processed_data(self) -> Tuple[str, str]:
        """処理済みデータを保存"""
        os.makedirs(self.output_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # メインデータファイル
        main_file = os.path.join(self.output_dir, f"processed_foods_{timestamp}.json")
        main_data = {
            "metadata": {
                "version": "1.0",
                "processed_at": datetime.now().isoformat(),
                "total_foods": len(self.processed_foods),
                "excluded_foods": list(self.excluded_foods),
                "processing_notes": "Cleaned and formatted nutrition and serving data"
            },
            "foods": self.processed_foods
        }

        with open(main_file, 'w', encoding='utf-8') as f:
            json.dump(main_data, f, ensure_ascii=False, indent=2)

        # サマリーファイル
        summary_file = os.path.join(self.output_dir, f"processing_summary_{timestamp}.json")
        summary_data = self.generate_summary_stats()

        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)

        return main_file, summary_file

    def generate_report(self) -> str:
        """処理レポートを生成"""
        if not self.processed_foods:
            return "処理が実行されていません"

        summary = self.generate_summary_stats()

        report = []
        report.append("=" * 80)
        report.append("🍽️ 食材データ後処理レポート")
        report.append("=" * 80)
        report.append(f"📅 処理実行日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"📊 処理済み食材数: {summary['total_processed_foods']:,}個")
        report.append(f"❌ 除外食材: {len(self.excluded_foods)}個")
        report.append("")

        # カテゴリ別詳細
        report.append("📂 カテゴリ別処理結果")
        report.append("-" * 60)

        category_breakdown = summary.get("category_breakdown", {})
        sorted_categories = sorted(category_breakdown.items(),
                                 key=lambda x: x[1]["count"], reverse=True)

        for category, stats in sorted_categories:
            report.append(f"📁 {category}")
            report.append(f"   📊 食材数: {stats['count']}個")
            report.append(f"   🥗 平均栄養素: {stats['avg_nutrition']:.1f}個")
            report.append(f"   🍽️ 平均サービング: {stats['avg_serving']:.1f}個")
            report.append("")

        # 除外された食材
        if self.excluded_foods:
            report.append("❌ 除外食材")
            report.append("-" * 60)
            for food in self.excluded_foods:
                report.append(f"   • {food}")
            report.append("")

        # サンプルデータ表示
        if self.processed_foods:
            sample_food = self.processed_foods[0]
            report.append("📋 サンプルデータ構造")
            report.append("-" * 60)
            report.append(f"食材名: {sample_food['food_name']}")
            report.append(f"栄養素数: {sample_food['nutrition_facts']['total_nutrients']}個")
            report.append(f"サービング数: {sample_food['serving_options']['total_servings']}個")
            report.append("")

        report.append("🎯 処理完了: APIで使用可能なクリーンなデータが生成されました")
        report.append("=" * 80)

        return "\n".join(report)


def main():
    """メイン処理"""
    print("🍽️ 食材データ後処理システム")
    print("=" * 60)
    
    processor = FoodDataProcessor()
    
    # カタログ食材の読み込み
    print("📁 カタログ食材読み込み中...")
    catalog_foods = processor.load_catalog_foods()
    print(f"✅ 有効食材: {len(catalog_foods)}個読み込み完了")
    
    # 生データの読み込み
    print("📁 生データ読み込み中...")
    raw_data = processor.load_raw_data()
    print(f"✅ 生データ: {len(raw_data)}個読み込み完了")
    
    # 失敗分析の実行
    print("\n🔍 失敗食材の分析実行中...")
    failed_analysis = processor.analyze_failed_foods(catalog_foods, raw_data)
    
    # 失敗分析結果の出力
    print(f"\n📊 失敗分析結果:")
    print(f"総失敗数: {failed_analysis['total_failed']}個")
    print("\n失敗理由別統計:")
    for reason, foods in failed_analysis["failure_reasons"].items():
        if foods:
            print(f"  {reason}: {len(foods)}個")
    
    # 詳細失敗リストの保存
    failure_report_path = processor.output_dir / f"failure_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(failure_report_path, 'w', encoding='utf-8') as f:
        json.dump(failed_analysis, f, ensure_ascii=False, indent=2)
    print(f"📄 詳細失敗分析: {failure_report_path}")
    
    # 成功した食材のみで処理続行
    print(f"\n🔄 {len(catalog_foods)}食材の後処理実行中...")
    processed_foods = processor.process_all_foods()
    
    # サマリー統計の生成
    summary_stats = processor.generate_summary_stats()
    
    # データ保存（引数なしで呼び出し）
    main_file, summary_file = processor.save_processed_data()
    
    print(f"✅ 処理完了: {len(processed_foods)}個成功, {failed_analysis['total_failed']}個スキップ")
    print(f"\n💾 処理済みデータ保存完了:")
    print(f"   📄 メインデータ: {os.path.basename(main_file)}")
    print(f"   📄 サマリー: {os.path.basename(summary_file)}")
    
    # レポート生成（引数なしで呼び出し）
    report = processor.generate_report()
    print("\n" + report)


if __name__ == "__main__":
    main()