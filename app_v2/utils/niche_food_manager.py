#!/usr/bin/env python3
"""
Niche Food Manager

ニッチな食材マッピングファイルの管理ユーティリティ
"""

import json
import os
from typing import Dict, List, Any
from datetime import datetime

class NicheFoodManager:
    """ニッチな食材マッピングファイルの管理クラス"""
    
    def __init__(self):
        """マネージャーの初期化"""
        # JSONファイルのパスを設定
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.json_path = os.path.join(current_dir, '..', 'config', 'data', 'niche_food_mappings.json')
    
    def load_mappings(self) -> Dict[str, Any]:
        """マッピングファイルを読み込み"""
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # デフォルト構造を返す
            return {
                "dishes": {"no_exact_match_items": []},
                "ingredients": {"no_exact_match_items": []}
            }
    
    def save_mappings(self, mappings: Dict[str, Any]) -> bool:
        """マッピングファイルを保存"""
        try:
            # 美しくフォーマットされたJSONで保存
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(mappings, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"マッピングファイル保存エラー: {e}")
            return False
    
    def add_ingredient_mapping(self, original: str, fallback_list: List[str]) -> bool:
        """新しい食材マッピングを追加"""
        mappings = self.load_mappings()
        
        # 既存のマッピングをチェック
        existing_items = mappings["ingredients"]["no_exact_match_items"]
        for item in existing_items:
            if item["original"].lower() == original.lower():
                print(f"⚠️  '{original}' は既に登録されています")
                return False
        
        # 新しいマッピングを追加
        new_item = {
            "original": original.lower(),
            "fallback": fallback_list
        }
        mappings["ingredients"]["no_exact_match_items"].append(new_item)
        
        # ソート（アルファベット順）
        mappings["ingredients"]["no_exact_match_items"].sort(key=lambda x: x["original"])
        
        # 保存
        success = self.save_mappings(mappings)
        if success:
            print(f"✅ 新しい食材マッピングを追加: '{original}' → {fallback_list}")
        return success
    
    def add_dish_mapping(self, dish_name: str) -> bool:
        """料理マッピングを追加"""
        try:
            mappings = self.load_mappings()
            
            # 既存項目のチェック
            existing_dishes = mappings["dishes"]["no_exact_match_items"]
            
            if dish_name.lower() not in [dish.lower() for dish in existing_dishes]:
                # シンプルにリストに追加
                mappings["dishes"]["no_exact_match_items"].append(dish_name.lower())
                mappings["dishes"]["no_exact_match_items"].sort()
                
                return self.save_mappings(mappings)
            else:
                print(f"Dish '{dish_name}' already exists")
                return True
                
        except Exception as e:
            print(f"Error adding dish mapping: {e}")
            return False
    
    def remove_ingredient_mapping(self, original: str) -> bool:
        """食材マッピングを削除"""
        mappings = self.load_mappings()
        
        # 該当するアイテムを探して削除
        items = mappings["ingredients"]["no_exact_match_items"]
        original_count = len(items)
        mappings["ingredients"]["no_exact_match_items"] = [
            item for item in items 
            if item["original"].lower() != original.lower()
        ]
        
        if len(mappings["ingredients"]["no_exact_match_items"]) == original_count:
            print(f"⚠️  '{original}' は見つかりませんでした")
            return False
        
        # 保存
        success = self.save_mappings(mappings)
        if success:
            print(f"✅ 食材マッピングを削除: '{original}'")
        return success
    
    def list_all_mappings(self):
        """すべてのマッピングを表示"""
        mappings = self.load_mappings()
        
        print("📊 現在のニッチ食材マッピング:")
        print("\n🥗 Ingredients:")
        for item in mappings["ingredients"]["no_exact_match_items"]:
            fallback_str = ", ".join(item["fallback"])
            print(f"   • {item['original']} → {fallback_str}")
        
        print(f"\n🍽️  Dishes: {len(mappings['dishes']['no_exact_match_items'])} items")
        for dish in mappings["dishes"]["no_exact_match_items"]:
            print(f"   • {dish}")
        
        total_items = (len(mappings["ingredients"]["no_exact_match_items"]) + 
                      len(mappings["dishes"]["no_exact_match_items"]))
        print(f"\n📈 総アイテム数: {total_items}")

def main():
    """CLIインターフェース"""
    import sys
    
    manager = NicheFoodManager()
    
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python niche_food_manager.py list                                    # 全マッピング表示")
        print("  python niche_food_manager.py add_ingredient <original> <fallback1> [fallback2] ...")
        print("  python niche_food_manager.py add_dish <dish_name>")
        print("  python niche_food_manager.py remove_ingredient <original>")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        manager.list_all_mappings()
    elif command == "add_ingredient" and len(sys.argv) >= 4:
        original = sys.argv[2]
        fallbacks = sys.argv[3:]
        manager.add_ingredient_mapping(original, fallbacks)
    elif command == "add_dish" and len(sys.argv) >= 3:
        dish = sys.argv[2]
        manager.add_dish_mapping(dish)
    elif command == "remove_ingredient" and len(sys.argv) >= 3:
        original = sys.argv[2]
        manager.remove_ingredient_mapping(original)
    else:
        print("❌ 無効なコマンドまたは引数です")

if __name__ == "__main__":
    main() 