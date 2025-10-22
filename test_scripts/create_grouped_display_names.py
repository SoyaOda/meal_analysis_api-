#!/usr/bin/env python
"""
display_nameをアルファベット順でグループ化したリストも作成
"""

import json
from pathlib import Path
from collections import defaultdict

mappings_file = Path(__file__).parent / "mappings" / "mappings.json"
grouped_output_file = Path(__file__).parent / "mappings" / "display_names_grouped.txt"

def create_grouped_list():
    """アルファベット別にグループ化"""
    
    # mappings.jsonを読み込み
    with open(mappings_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    mappings = data.get('mappings', {})
    
    # アルファベット別にグループ化
    grouped = defaultdict(list)
    
    for key, value in mappings.items():
        display_name = value.get('display_name', key)
        first_letter = display_name[0].upper() if display_name else '#'
        if not first_letter.isalpha():
            first_letter = '#'  # 数字や記号は#グループ
        grouped[first_letter].append(display_name)
    
    # 各グループをソート
    for letter in grouped:
        grouped[letter].sort()
    
    # ファイルに保存
    with open(grouped_output_file, 'w', encoding='utf-8') as f:
        f.write("# Display Names Grouped by First Letter\n")
        f.write(f"# Total: {sum(len(items) for items in grouped.values())} items\n")
        f.write("# " + "="*50 + "\n\n")
        
        # アルファベット順に出力
        for letter in sorted(grouped.keys()):
            items = grouped[letter]
            f.write(f"\n## {letter} ({len(items)} items)\n")
            f.write("-" * 30 + "\n")
            for item in items:
                f.write(f"  • {item}\n")
    
    print(f"✅ グループ化リストを保存: {grouped_output_file}")
    
    # 統計表示
    print("\n📊 アルファベット別分布:")
    for letter in sorted(grouped.keys()):
        count = len(grouped[letter])
        bar = "█" * (count // 2)
        print(f"  {letter}: {count:3d} {bar}")
    
    return grouped

if __name__ == "__main__":
    create_grouped_list()
