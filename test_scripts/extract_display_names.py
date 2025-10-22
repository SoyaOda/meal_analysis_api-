#!/usr/bin/env python
"""
mappings.jsonから全てのdisplay_nameを抽出してtxtファイルに保存
"""

import json
from pathlib import Path

mappings_file = Path(__file__).parent / "mappings" / "mappings.json"
output_file = Path(__file__).parent / "mappings" / "display_names_list.txt"

def extract_display_names():
    """display_nameを抽出"""
    
    # mappings.jsonを読み込み
    with open(mappings_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    mappings = data.get('mappings', {})
    
    # display_nameを収集
    display_names = []
    missing_display_names = []
    
    for key, value in mappings.items():
        if 'display_name' in value:
            display_names.append(value['display_name'])
        else:
            # display_nameがない場合はキーを使用
            display_names.append(key)
            missing_display_names.append(key)
    
    # ソート
    display_names.sort()
    
    return display_names, missing_display_names

def save_to_txt(display_names, missing_display_names):
    """テキストファイルに保存"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        # ヘッダー
        f.write("# Display Names List from mappings.json\n")
        f.write(f"# Total: {len(display_names)} items\n")
        f.write("# " + "="*50 + "\n\n")
        
        # display_nameリスト
        for i, name in enumerate(display_names, 1):
            f.write(f"{i}. {name}\n")
    
    print(f"✅ {len(display_names)} 個のdisplay_nameを保存しました")
    print(f"   ファイル: {output_file}")
    
    if missing_display_names:
        print(f"\n⚠️  {len(missing_display_names)} 個の項目にdisplay_nameがありませんでした")
        print(f"   （キー名を使用）")
    
    return output_file

def main():
    print("="*80)
    print("display_name抽出スクリプト")
    print("="*80)
    print()
    
    # display_nameを抽出
    print("📚 mappings.jsonからdisplay_nameを抽出中...")
    display_names, missing_display_names = extract_display_names()
    
    # ファイルに保存
    output_path = save_to_txt(display_names, missing_display_names)
    
    # 統計を表示
    print()
    print("📊 統計:")
    print(f"  総項目数: {len(display_names)}")
    
    # カテゴリ別の概算（名前パターンから推定）
    categories = {
        'Fruits': len([n for n in display_names if any(fruit in n.lower() for fruit in ['apple', 'banana', 'orange', 'grape', 'berry', 'mango', 'pear'])]),
        'Vegetables': len([n for n in display_names if any(veg in n.lower() for veg in ['carrot', 'broccoli', 'lettuce', 'tomato', 'potato', 'onion'])]),
        'Meat': len([n for n in display_names if any(meat in n.lower() for meat in ['beef', 'pork', 'chicken', 'turkey', 'bacon', 'sausage'])]),
        'Dairy': len([n for n in display_names if any(dairy in n.lower() for dairy in ['milk', 'cheese', 'yogurt', 'butter', 'cream'])]),
        'Beverages': len([n for n in display_names if any(drink in n.lower() for drink in ['juice', 'soda', 'tea', 'coffee', 'water', 'drink'])])
    }
    
    print("\n  推定カテゴリ分布:")
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        if count > 0:
            print(f"    {category}: {count} items")
    
    print()
    print("="*80)
    print("✅ 完了")
    print("="*80)

if __name__ == "__main__":
    main()
