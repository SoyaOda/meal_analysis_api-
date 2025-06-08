#!/usr/bin/env python3
"""
栄養データベース構築スクリプト v2.0

name/food_name/titleとdescriptionを分離した改善版
段階的検索戦略に対応
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

class NutritionDBBuilderV2:
    def __init__(self, raw_data_path: str, output_path: str):
        self.raw_data_path = Path(raw_data_path)
        self.output_path = Path(output_path)
        self.output_path.mkdir(exist_ok=True)
        
        # 統計情報
        self.stats = {
            "recipe": {"processed": 0, "errors": 0},
            "food": {"processed": 0, "errors": 0},
            "branded": {"processed": 0, "errors": 0}
        }
        
        # 構築されたデータベース
        self.db_items = []
    
    def extract_serving_size_grams(self, serving_size: str) -> Optional[float]:
        """servingSizeから数値を抽出してfloatに変換"""
        try:
            if isinstance(serving_size, str) and serving_size.endswith(" grams"):
                number_part = serving_size.replace(" grams", "").strip()
                return float(number_part)
            else:
                # 数値のみの場合や、他の形式の場合の処理
                # 数値部分を正規表現で抽出
                match = re.search(r'(\d+(?:\.\d+)?)', str(serving_size))
                if match:
                    return float(match.group(1))
        except (ValueError, AttributeError):
            return None
        return None
    
    def find_grams_amount(self, units: List[Dict]) -> Optional[float]:
        """unitsやunit_weightsからgramsに対応するamountを取得"""
        for unit in units:
            if unit.get("description") == "grams":
                return unit.get("amount")
        return None
    
    def process_recipe_item(self, data: Dict) -> Optional[Dict]:
        """レシピデータを統一フォーマットに変換（改善版）"""
        try:
            # 必須フィールドの確認
            if not all(key in data for key in ["id", "title", "nutrients"]):
                return None
            
            nutrients = data["nutrients"]
            required_nutrients = ["calories", "proteinContent", "fatContent", "carbohydrateContent", "servingSize"]
            if not all(key in nutrients for key in required_nutrients):
                return None
            
            # servingSizeの処理
            weight = self.extract_serving_size_grams(nutrients["servingSize"])
            if weight is None:
                return None
            
            # 🎯 改善版: nameとdescriptionを分離
            return {
                "db_type": "dish",
                "id": int(data["id"]),
                "food_name": data["title"],  # 主要検索対象
                "description": None,  # recipeにはdescriptionがない場合が多い
                "nutrition": {
                    "calories": float(nutrients["calories"]),
                    "protein_g": float(nutrients["proteinContent"]),
                    "fat_total_g": float(nutrients["fatContent"]),
                    "carbohydrate_by_difference_g": float(nutrients["carbohydrateContent"])
                },
                "weight": weight
            }
            
        except (KeyError, ValueError, TypeError) as e:
            return None
    
    def process_food_item(self, data: Dict) -> Optional[Dict]:
        """食材データを統一フォーマットに変換（改善版）"""
        try:
            # 必須フィールドの確認
            if not all(key in data for key in ["id", "name", "description", "nutrition", "units"]):
                return None
            
            nutrition = data["nutrition"]
            required_nutrients = ["calories", "proteinContent", "fatContent", "carbohydrateContent"]
            if not all(key in nutrition for key in required_nutrients):
                return None
            
            # gramsのunit検索
            weight = self.find_grams_amount(data["units"])
            if weight is None:
                return None
            
            # 🎯 改善版: nameとdescriptionを分離
            return {
                "db_type": "ingredient",
                "id": int(data["id"]),
                "food_name": data["name"],  # 主要検索対象（例: "Potato"）
                "description": data["description"],  # 補助情報（例: "Flesh and skin, raw"）
                "nutrition": {
                    "calories": float(nutrition["calories"]),
                    "protein_g": float(nutrition["proteinContent"]),
                    "fat_total_g": float(nutrition["fatContent"]),
                    "carbohydrate_by_difference_g": float(nutrition["carbohydrateContent"])
                },
                "weight": weight
            }
            
        except (KeyError, ValueError, TypeError) as e:
            return None
    
    def process_branded_item(self, data: Dict) -> Optional[Dict]:
        """ブランド食品データを統一フォーマットに変換（改善版）"""
        try:
            # データ構造の確認
            if "data" not in data:
                return None
            
            item_data = data["data"]
            
            # 必須フィールドの確認
            if not all(key in item_data for key in ["id", "food_name", "description", "unit_weights"]):
                return None
            
            # カロリーの取得
            calories = None
            if "calories" in item_data:
                calories = item_data["calories"]
            elif "serving_calories" in item_data:
                calories = item_data["serving_calories"]
            
            if calories is None:
                return None
            
            # プロテインの取得
            protein = None
            if "proteins" in item_data:
                protein = item_data["proteins"]
            elif "serving_proteins" in item_data:
                protein = item_data["serving_proteins"]
            
            if protein is None:
                return None
            
            # 脂質の取得
            fat = None
            if "fats" in item_data:
                fat = item_data["fats"]
            elif "serving_fats" in item_data:
                fat = item_data["serving_fats"]
            
            if fat is None:
                return None
            
            # 炭水化物の取得
            carbs = None
            if "carbs" in item_data:
                carbs = item_data["carbs"]
            elif "serving_carbs" in item_data:
                carbs = item_data["serving_carbs"]
            
            if carbs is None:
                return None
            
            # gramsのunit_weight検索
            weight = self.find_grams_amount(item_data["unit_weights"])
            if weight is None:
                return None
            
            # 🎯 改善版: food_nameとdescriptionを分離
            return {
                "db_type": "branded",
                "id": int(item_data["id"]),
                "food_name": item_data["food_name"],  # 主要検索対象
                "description": item_data["description"],  # 補助情報
                "nutrition": {
                    "calories": float(calories),
                    "protein_g": float(protein),
                    "fat_total_g": float(fat),
                    "carbohydrate_by_difference_g": float(carbs)
                },
                "weight": weight
            }
            
        except (KeyError, ValueError, TypeError) as e:
            return None
    
    def process_category(self, category: str):
        """指定されたカテゴリのデータを処理"""
        print(f"\n🔄 Processing {category} data...")
        category_path = self.raw_data_path / category
        
        if not category_path.exists():
            print(f"❌ Category directory not found: {category_path}")
            return
        
        processed_count = 0
        error_count = 0
        
        # IDディレクトリを巡回
        for id_dir in category_path.iterdir():
            if not id_dir.is_dir():
                continue
            
            processed_dir = id_dir / "processed"
            if not processed_dir.exists():
                continue
            
            # processedディレクトリ内のJSONファイルを確認
            json_files = list(processed_dir.glob("*.json"))
            if not json_files:
                continue
            
            # 最新のJSONファイルを使用
            json_file = max(json_files, key=lambda x: x.stat().st_mtime)
            
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # カテゴリ別の処理
                processed_item = None
                if category == "recipe":
                    processed_item = self.process_recipe_item(data)
                elif category == "food":
                    processed_item = self.process_food_item(data)
                elif category == "branded":
                    processed_item = self.process_branded_item(data)
                
                if processed_item:
                    self.db_items.append(processed_item)
                    processed_count += 1
                    if processed_count % 100 == 0:
                        print(f"   ✅ Processed {processed_count} items...")
                else:
                    error_count += 1
                    
            except Exception as e:
                error_count += 1
                if error_count <= 5:  # 最初の5つのエラーのみ表示
                    print(f"   ❌ Error processing {id_dir.name}: {str(e)}")
        
        # 統計更新
        self.stats[category]["processed"] = processed_count
        self.stats[category]["errors"] = error_count
        
        print(f"   📊 {category}: {processed_count} processed, {error_count} errors")
    
    def save_database(self):
        """データベースをファイルに保存"""
        print(f"\n💾 Saving database to {self.output_path}...")
        
        # 各カテゴリ別のファイル保存
        db_by_type = {
            "dish": [],
            "ingredient": [],
            "branded": []
        }
        
        for item in self.db_items:
            db_by_type[item["db_type"]].append(item)
        
        # カテゴリ別ファイル保存
        for db_type, items in db_by_type.items():
            if items:
                file_path = self.output_path / f"{db_type}_db_v2.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(items, f, indent=2, ensure_ascii=False)
                print(f"   ✅ Saved {len(items)} {db_type} items to {file_path}")
        
        # 統合データベースファイル保存
        unified_db_path = self.output_path / "unified_nutrition_db_v2.json"
        with open(unified_db_path, 'w', encoding='utf-8') as f:
            json.dump(self.db_items, f, indent=2, ensure_ascii=False)
        print(f"   ✅ Saved {len(self.db_items)} total items to {unified_db_path}")
    
    def print_summary(self):
        """構築サマリーを表示"""
        print(f"\n📊 Database Build Summary:")
        print("="*50)
        
        total_processed = sum(cat["processed"] for cat in self.stats.values())
        total_errors = sum(cat["errors"] for cat in self.stats.values())
        
        for category, stats in self.stats.items():
            print(f"{category:>10}: {stats['processed']:,} processed, {stats['errors']:,} errors")
        
        print("-"*50)
        print(f"{'Total':>10}: {total_processed:,} processed, {total_errors:,} errors")
        print(f"{'Success Rate':>10}: {(total_processed/(total_processed+total_errors)*100):.1f}%")
        
        # データタイプ別の内訳
        print(f"\n📊 Database Type Breakdown:")
        db_by_type = {"dish": 0, "ingredient": 0, "branded": 0}
        for item in self.db_items:
            db_by_type[item["db_type"]] += 1
        
        for db_type, count in db_by_type.items():
            print(f"{db_type:>10}: {count:,} items")
    
    def build(self):
        """データベース構築を実行"""
        print("🏗 Building improved nutrition database v2.0...")
        print("🎯 Key improvement: Separated food_name and description fields for better search")
        
        # 各カテゴリを処理
        for category in ["recipe", "food", "branded"]:
            self.process_category(category)
        
        # データベース保存
        self.save_database()
        
        # サマリー表示
        self.print_summary()
        
        print("\n✅ Database build completed!")

def main():
    """メイン実行関数"""
    builder = NutritionDBBuilderV2(
        raw_data_path="raw_nutrition_data",
        output_path="nutrition_db_v2"
    )
    builder.build()

if __name__ == "__main__":
    main() 