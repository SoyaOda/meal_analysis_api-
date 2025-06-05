#!/usr/bin/env python3
"""
栄養データベース構築前の整合性確認スクリプト

各カテゴリ（recipe, food, branded）のJSONファイルで
必要な項目が全て存在するかを確認する。
"""

import json
import os
from pathlib import Path
import re

def check_recipe_data(data):
    """レシピデータの必要項目確認"""
    errors = []
    warnings = []
    
    # 必須項目の存在確認
    if "id" not in data:
        errors.append("Missing 'id' field")
    
    if "title" not in data:
        errors.append("Missing 'title' field")
    
    if "nutrients" not in data:
        errors.append("Missing 'nutrients' field")
        return errors, warnings
    
    nutrients = data["nutrients"]
    
    # 栄養素の確認
    required_nutrients = ["calories", "proteinContent", "fatContent", "carbohydrateContent"]
    for nutrient in required_nutrients:
        if nutrient not in nutrients:
            errors.append(f"Missing nutrients.{nutrient}")
    
    # servingSizeの確認
    if "servingSize" not in nutrients:
        errors.append("Missing nutrients.servingSize")
    else:
        serving_size = nutrients["servingSize"]
        if not isinstance(serving_size, str):
            errors.append("nutrients.servingSize is not a string")
        elif not serving_size.endswith(" grams"):
            warnings.append(f"nutrients.servingSize format unexpected: {serving_size}")
        else:
            # 数値部分の抽出確認
            number_part = serving_size.replace(" grams", "")
            try:
                float(number_part)
            except ValueError:
                errors.append(f"Cannot extract numeric value from servingSize: {serving_size}")
    
    return errors, warnings

def check_food_data(data):
    """食材データの必要項目確認"""
    errors = []
    warnings = []
    
    # 必須項目の存在確認
    if "id" not in data:
        errors.append("Missing 'id' field")
    
    if "name" not in data:
        errors.append("Missing 'name' field")
    
    if "description" not in data:
        errors.append("Missing 'description' field")
    
    if "nutrition" not in data:
        errors.append("Missing 'nutrition' field")
        return errors, warnings
    
    nutrition = data["nutrition"]
    
    # 栄養素の確認
    required_nutrients = ["calories", "proteinContent", "fatContent", "carbohydrateContent"]
    for nutrient in required_nutrients:
        if nutrient not in nutrition:
            errors.append(f"Missing nutrition.{nutrient}")
    
    # unitsの確認
    if "units" not in data:
        errors.append("Missing 'units' field")
        return errors, warnings
    
    units = data["units"]
    if not isinstance(units, list):
        errors.append("'units' is not a list")
        return errors, warnings
    
    # gramsのunitを探す
    grams_unit = None
    for unit in units:
        if unit.get("description") == "grams":
            grams_unit = unit
            break
    
    if grams_unit is None:
        errors.append("No unit with description='grams' found")
    else:
        if "amount" not in grams_unit:
            errors.append("grams unit missing 'amount' field")
    
    return errors, warnings

def check_branded_data(data):
    """ブランド食品データの必要項目確認"""
    errors = []
    warnings = []
    
    # データ構造の確認（brandedは'data'フィールドでラップされている）
    if "data" not in data:
        errors.append("Missing 'data' field")
        return errors, warnings
    
    item_data = data["data"]
    
    # 必須項目の存在確認
    if "id" not in item_data:
        errors.append("Missing data.id field")
    
    if "food_name" not in item_data:
        errors.append("Missing data.food_name field")
    
    if "description" not in item_data:
        errors.append("Missing data.description field")
    
    if "nutrition" not in item_data:
        errors.append("Missing data.nutrition field")
        return errors, warnings
    
    nutrition = item_data["nutrition"]
    
    # 栄養素の確認（brandedでは直接フィールドとして存在）
    # caloriesはデータルートにあることが多い
    calories_found = False
    if "calories" in item_data:
        calories_found = True
    elif "serving_calories" in item_data:
        calories_found = True
        warnings.append("Using serving_calories instead of calories")
    
    if not calories_found:
        errors.append("Missing calories information")
    
    # その他の栄養素確認（brandedでは名前が異なる）
    protein_found = False
    if "proteins" in item_data:
        protein_found = True
    elif "serving_proteins" in item_data:
        protein_found = True
        warnings.append("Using serving_proteins instead of proteins")
    
    if not protein_found:
        errors.append("Missing protein information")
    
    fat_found = False
    if "fats" in item_data:
        fat_found = True
    elif "serving_fats" in item_data:
        fat_found = True
        warnings.append("Using serving_fats instead of fats")
    
    if not fat_found:
        errors.append("Missing fat information")
    
    carb_found = False
    if "carbs" in item_data:
        carb_found = True
    elif "serving_carbs" in item_data:
        carb_found = True
        warnings.append("Using serving_carbs instead of carbs")
    
    if not carb_found:
        errors.append("Missing carb information")
    
    # unit_weightsの確認
    if "unit_weights" not in item_data:
        errors.append("Missing data.unit_weights field")
        return errors, warnings
    
    unit_weights = item_data["unit_weights"]
    if not isinstance(unit_weights, list):
        errors.append("'unit_weights' is not a list")
        return errors, warnings
    
    # gramsのunit_weightを探す
    grams_weight = None
    for weight in unit_weights:
        if weight.get("description") == "grams":
            grams_weight = weight
            break
    
    if grams_weight is None:
        errors.append("No unit_weight with description='grams' found")
    else:
        if "amount" not in grams_weight:
            errors.append("grams unit_weight missing 'amount' field")
    
    return errors, warnings

def scan_directory(base_path, category):
    """指定されたカテゴリのディレクトリをスキャンして整合性を確認"""
    category_path = Path(base_path) / category
    
    if not category_path.exists():
        print(f"❌ Category directory not found: {category_path}")
        return
    
    print(f"\n🔍 Checking {category} data...")
    print("=" * 50)
    
    total_files = 0
    valid_files = 0
    error_files = 0
    warning_files = 0
    
    # IDディレクトリを巡回
    for id_dir in category_path.iterdir():
        if not id_dir.is_dir():
            continue
        
        processed_dir = id_dir / "processed"
        if not processed_dir.exists():
            print(f"⚠️ No processed directory in {id_dir.name}")
            continue
        
        # processedディレクトリ内のJSONファイルを確認
        json_files = list(processed_dir.glob("*.json"))
        if not json_files:
            print(f"⚠️ No JSON files in {processed_dir}")
            continue
        
        # 最新のJSONファイルを使用
        json_file = max(json_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            total_files += 1
            
            # カテゴリ別の確認
            if category == "recipe":
                errors, warnings = check_recipe_data(data)
            elif category == "food":
                errors, warnings = check_food_data(data)
            elif category == "branded":
                errors, warnings = check_branded_data(data)
            else:
                print(f"❌ Unknown category: {category}")
                continue
            
            # 結果の判定
            if errors:
                error_files += 1
                print(f"❌ {id_dir.name}: {len(errors)} errors")
                for error in errors:
                    print(f"   - {error}")
            elif warnings:
                warning_files += 1
                print(f"⚠️ {id_dir.name}: {len(warnings)} warnings")
                for warning in warnings:
                    print(f"   - {warning}")
            else:
                valid_files += 1
                print(f"✅ {id_dir.name}: OK")
                
        except Exception as e:
            error_files += 1
            print(f"❌ {id_dir.name}: File read error - {str(e)}")
    
    # サマリー表示
    print(f"\n📊 {category} Summary:")
    print(f"   Total files: {total_files}")
    print(f"   ✅ Valid: {valid_files}")
    print(f"   ⚠️ Warnings: {warning_files}")
    print(f"   ❌ Errors: {error_files}")
    
    if total_files > 0:
        success_rate = (valid_files + warning_files) / total_files * 100
        print(f"   📈 Success rate: {success_rate:.1f}%")

def main():
    """メイン実行関数"""
    base_path = "../raw_nutrition_data"
    
    print("🔍 栄養データベース整合性確認スクリプト")
    print("=" * 60)
    
    categories = ["recipe", "food", "branded"]
    
    for category in categories:
        scan_directory(base_path, category)
    
    print("\n✅ 整合性確認完了")

if __name__ == "__main__":
    main() 