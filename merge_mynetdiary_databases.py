#!/usr/bin/env python3
"""
MyNetDiary データベースマージスクリプト

新しい名前分離データ（final_mynetdiary_conversion_FIXED_20250627_173611.json）と
元の栄養データ（mynetdiary_db.json）を結合して、
完全なMyNetDiaryデータベースを作成する
"""

import json
import os
from typing import Dict, List, Any


def load_original_database() -> Dict[str, Dict[str, Any]]:
    """元のMyNetDiaryデータベースを読み込み、original_nameをキーとした辞書を作成"""
    print("Loading original MyNetDiary database...")
    
    with open('db/mynetdiary_db.json', 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # search_nameをキーとした辞書を作成
    original_dict = {}
    for item in original_data:
        search_name = item.get('search_name', '')
        if search_name:
            original_dict[search_name] = item
    
    print(f"✅ Loaded {len(original_dict)} items from original database")
    return original_dict


def load_name_separated_database() -> List[Dict[str, Any]]:
    """新しい名前分離データベースを読み込み"""
    print("Loading name-separated MyNetDiary database...")
    
    with open('db/mynetdiary_final_fixed.json', 'r', encoding='utf-8') as f:
        separated_data = json.load(f)
    
    print(f"✅ Loaded {len(separated_data)} items from name-separated database")
    return separated_data


def merge_databases(original_dict: Dict[str, Dict[str, Any]], 
                   separated_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """データベースをマージ"""
    print("Merging databases...")
    
    merged_data = []
    matched_count = 0
    unmatched_count = 0
    
    for separated_item in separated_data:
        original_name = separated_item.get('original_name', '')
        
        # 元のデータベースから対応するアイテムを検索
        if original_name in original_dict:
            original_item = original_dict[original_name]
            
            # 新しいフォーマットでアイテムを作成
            merged_item = {
                "data_type": "unified_fixed",
                "id": original_item.get('id', 0),
                "search_name": separated_item.get('search_name', ''),
                "description": separated_item.get('description', ''),
                "original_name": original_name,
                "nutrition": original_item.get('nutrition', {}),
                "source": "MyNetDiary_Fixed",
                "processing_method": separated_item.get('processing_method', ''),
                "attempts": separated_item.get('attempts', 1)
            }
            
            # 温度情報があれば追加
            if 'temperature' in separated_item:
                merged_item['temperature'] = separated_item['temperature']
            
            # reasoning情報があれば追加
            if 'reasoning' in separated_item:
                merged_item['reasoning'] = separated_item['reasoning']
            
            merged_data.append(merged_item)
            matched_count += 1
        else:
            print(f"⚠️ No match found for: {original_name}")
            unmatched_count += 1
    
    print(f"✅ Merged {matched_count} items successfully")
    if unmatched_count > 0:
        print(f"⚠️ {unmatched_count} items could not be matched")
    
    return merged_data


def save_merged_database(merged_data: List[Dict[str, Any]]) -> None:
    """マージしたデータベースを保存"""
    output_file = 'db/mynetdiary_final_complete.json'
    
    print(f"Saving merged database to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Saved {len(merged_data)} items to {output_file}")


def main():
    """メイン処理"""
    print("=== MyNetDiary Database Merger ===")
    
    # 元のデータベースを読み込み
    original_dict = load_original_database()
    
    # 名前分離データベースを読み込み
    separated_data = load_name_separated_database()
    
    # データベースをマージ
    merged_data = merge_databases(original_dict, separated_data)
    
    # マージしたデータベースを保存
    save_merged_database(merged_data)
    
    # 統計情報を表示
    print("\n=== Merge Statistics ===")
    print(f"Original database items: {len(original_dict)}")
    print(f"Separated database items: {len(separated_data)}")
    print(f"Merged database items: {len(merged_data)}")
    print(f"Match rate: {len(merged_data)/len(separated_data)*100:.1f}%")
    
    # サンプルアイテムを表示
    print("\n=== Sample Merged Items ===")
    for i, item in enumerate(merged_data[:3]):
        print(f"\n{i+1}. {item['search_name']}")
        print(f"   Description: {item['description']}")
        print(f"   Original: {item['original_name']}")
        print(f"   Nutrition: Calories={item['nutrition'].get('calories', 0):.1f}, "
              f"Protein={item['nutrition'].get('protein', 0):.1f}g, "
              f"Fat={item['nutrition'].get('fat', 0):.1f}g, "
              f"Carbs={item['nutrition'].get('carbs', 0):.1f}g")
    
    print("\n✅ Database merge completed successfully!")


if __name__ == "__main__":
    main() 