#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MyNetDiaryデータを統合データベース形式に変換するスクリプト
"""

import os
import json
from pathlib import Path

def calculate_per_100g_nutrition(nutrition, weight_g):
    """
    100gあたりの栄養値を計算する
    """
    if weight_g == 0:
        return {
            "calories": 0.0,
            "protein": 0.0,
            "fat": 0.0,
            "carbs": 0.0
        }
    
    factor = 100.0 / weight_g
    
    return {
        "calories": nutrition["calories"] * factor,
        "protein": nutrition["protein"] * factor,
        "fat": nutrition["fat"] * factor,
        "carbs": nutrition["carbs"] * factor
    }

def process_json_files(json_data_dir):
    """
    json_dataディレクトリ内の全JSONファイルを処理
    Enhanced版：カテゴリーとserving情報も含める
    """
    unified_data = []
    current_id = 10000000000  # 11桁の開始ID
    
    json_data_path = Path(json_data_dir)
    
    # 各サブディレクトリを処理
    for subdir in sorted(json_data_path.iterdir()):
        if not subdir.is_dir():
            continue
            
        print(f"処理中: {subdir.name}")
        
        # サブディレクトリ内のJSONファイルを処理
        for json_file in sorted(subdir.glob('*.json')):
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 必要なデータが存在するかチェック
                if not data.get('name') or data.get('weight_g', 0) == 0:
                    print(f"  スキップ: {json_file.name} (名前または重量が不正)")
                    continue
                
                # 100gあたりの栄養値を計算
                per_100g_nutrition = calculate_per_100g_nutrition(
                    data['nutrition'], 
                    data['weight_g']
                )
                
                # 統合フォーマットに変換（Enhanced版）
                unified_entry = {
                    "data_type": "unified",
                    "id": current_id,
                    "search_name": data['name'],
                    "description": None,
                    "nutrition": per_100g_nutrition,
                    "source": "MyNetDiary",
                    # 新しいフィールド
                    "category": data.get('category', ''),
                    "serving": {
                        "unit": data.get('serving', {}).get('unit', ''),
                        "grams": data.get('serving', {}).get('grams', 0.0)
                    }
                }
                
                unified_data.append(unified_entry)
                current_id += 1
                
                if len(unified_data) % 100 == 0:
                    print(f"  処理済み: {len(unified_data)}件")
                    
            except Exception as e:
                print(f"  エラー: {json_file.name} - {str(e)}")
    
    return unified_data

def main():
    """
    メイン処理
    Enhanced版：カテゴリーとserving情報を含む統合DB作成
    """
    input_directory = "json_data"
    output_file = "mynetdiary_db_v2.json"
    
    print("MyNetDiary統合データベースv2を作成しています...")
    print(f"入力ディレクトリ: {input_directory}")
    print(f"出力ファイル: {output_file}")
    print("Enhanced版: カテゴリーとserving情報を含む")
    
    # JSONファイルを処理
    unified_data = process_json_files(input_directory)
    
    print(f"\n統合データベース作成完了!")
    print(f"総エントリ数: {len(unified_data)}")
    
    # 統合データベースを保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(unified_data, f, ensure_ascii=False, indent=2)
    
    print(f"ファイルが保存されました: {output_file}")
    
    # サンプルデータを表示（Enhanced版）
    if unified_data:
        print(f"\nサンプルエントリ（Enhanced版）:")
        for i, entry in enumerate(unified_data[:3]):
            print(f"{i+1}. ID: {entry['id']}")
            print(f"   名前: {entry['search_name']}")
            print(f"   カテゴリー: {entry.get('category', 'N/A')}")
            
            serving = entry.get('serving', {})
            if serving.get('unit') and serving.get('grams'):
                print(f"   Serving: {serving['unit']} ({serving['grams']}g)")
            else:
                print(f"   Serving: N/A")
                
            print(f"   100gあたり - カロリー: {entry['nutrition']['calories']:.1f}, "
                  f"プロテイン: {entry['nutrition']['protein']:.1f}g, "
                  f"脂肪: {entry['nutrition']['fat']:.1f}g, "
                  f"炭水化物: {entry['nutrition']['carbs']:.1f}g")
            print()
    
    # 統計情報
    categories = set()
    serving_units = set()
    for entry in unified_data:
        if entry.get('category'):
            categories.add(entry['category'])
        serving = entry.get('serving', {})
        if serving.get('unit'):
            serving_units.add(serving['unit'])
    
    print(f"📊 統計情報:")
    print(f"   カテゴリー数: {len(categories)}")
    print(f"   Serving単位数: {len(serving_units)}")
    
    if categories:
        print(f"   カテゴリー一覧: {sorted(categories)}")
    if serving_units:
        print(f"   Serving単位一覧: {sorted(serving_units)}")

if __name__ == "__main__":
    main() 