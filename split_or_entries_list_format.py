#!/usr/bin/env python3
"""
MyNetDiary JSONファイルの「or」エントリ分割スクリプト（リスト形式版）

search_nameに「or」が含まれるエントリをリスト形式に変換して、
検索時に各項目を独立評価し最高スコアを採用できるようにする。

例:
"Chickpeas or garbanzo beans" → ["Chickpeas", "garbanzo beans"]
"""

import json
import time
import re
from typing import List, Dict, Any, Union

def clean_food_name(name: str) -> str:
    """食品名をクリーンアップ"""
    # 前後の空白を除去
    name = name.strip()
    
    # 複数の空白を単一の空白に変換
    name = re.sub(r'\s+', ' ', name)
    
    # 不要な記号を除去（必要に応じて調整）
    name = name.replace('  ', ' ')
    
    return name

def convert_or_entries_to_list(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """「or」を含むエントリをリスト形式に変換"""
    
    new_data = []
    or_entries_processed = 0
    total_list_entries = 0
    
    for item in data:
        search_name = item.get('search_name', '')
        
        # 「or」が含まれていない場合はそのまま追加（文字列のまま）
        if ' or ' not in search_name.lower():
            new_data.append(item)
            continue
        
        # 「or」で分割
        parts = re.split(r'\s+or\s+', search_name, flags=re.IGNORECASE)
        
        if len(parts) <= 1:
            # 分割できない場合はそのまま追加
            new_data.append(item)
            continue
        
        or_entries_processed += 1
        
        # 分割された部分をリスト形式で保存
        cleaned_parts = []
        for part in parts:
            cleaned_part = clean_food_name(part)
            if cleaned_part:
                cleaned_parts.append(cleaned_part)
        
        if cleaned_parts:
            # 新しいエントリを作成（search_nameをリスト形式に）
            new_entry = item.copy()
            new_entry['search_name'] = cleaned_parts  # リスト形式
            
            # 元の情報を保持するためのメタデータを追加
            new_entry['original_search_name'] = search_name
            new_entry['search_name_type'] = 'list'
            new_entry['alternative_names_count'] = len(cleaned_parts)
            
            new_data.append(new_entry)
            total_list_entries += 1
            
            print(f"変換: '{search_name}' → {cleaned_parts}")
        else:
            # クリーンアップ後に何も残らない場合は元のまま
            new_data.append(item)
    
    print(f"\n📊 変換結果:")
    print(f"   🔄 変換されたエントリ: {or_entries_processed}")
    print(f"   📝 リスト形式エントリ: {total_list_entries}")
    print(f"   📦 総エントリ数: {len(new_data)}")
    
    return new_data

def validate_conversion_results(original_data: List[Dict[str, Any]], new_data: List[Dict[str, Any]]):
    """変換結果を検証"""
    
    print(f"\n🔍 検証結果:")
    
    # リスト形式エントリのチェック
    list_entries = [item for item in new_data if isinstance(item.get('search_name'), list)]
    string_entries = [item for item in new_data if isinstance(item.get('search_name'), str)]
    
    print(f"   📝 リスト形式エントリ: {len(list_entries)}")
    print(f"   📄 文字列形式エントリ: {len(string_entries)}")
    
    # 残存「or」エントリの確認
    remaining_or_entries = []
    for item in new_data:
        search_name = item.get('search_name', '')
        if isinstance(search_name, str) and ' or ' in search_name.lower():
            remaining_or_entries.append(item)
    
    print(f"   🔄 残存「or」エントリ: {len(remaining_or_entries)}")
    
    if remaining_or_entries:
        print("   ⚠️ 以下のエントリがまだ変換されていません:")
        for entry in remaining_or_entries[:5]:
            print(f"      - {entry['search_name']}")
    
    # リスト形式エントリの例を表示
    if list_entries:
        print("   📝 リスト形式の例:")
        for i, entry in enumerate(list_entries[:5]):
            print(f"      {i+1}. {entry['search_name']} (原名: {entry.get('original_search_name', 'N/A')})")

def analyze_search_name_distribution(data: List[Dict[str, Any]]):
    """search_nameの分布を分析"""
    
    list_count = 0
    string_count = 0
    max_alternatives = 0
    alternative_counts = {}
    
    for item in data:
        search_name = item.get('search_name', '')
        if isinstance(search_name, list):
            list_count += 1
            alt_count = len(search_name)
            max_alternatives = max(max_alternatives, alt_count)
            alternative_counts[alt_count] = alternative_counts.get(alt_count, 0) + 1
        else:
            string_count += 1
    
    print(f"\n📈 search_name分布分析:")
    print(f"   📄 文字列形式: {string_count}")
    print(f"   📝 リスト形式: {list_count}")
    print(f"   🔢 最大代替名数: {max_alternatives}")
    
    if alternative_counts:
        print(f"   📊 代替名数別分布:")
        for count, freq in sorted(alternative_counts.items()):
            print(f"      {count}個: {freq}エントリ")

def main():
    """メイン処理"""
    
    print("🚀 MyNetDiary 「or」エントリリスト形式変換スクリプト")
    print("=" * 65)
    
    # データ読み込み
    print("📂 データを読み込み中...")
    with open('db/mynetdiary_converted_tool_calls.json', 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    print(f"✅ {len(original_data)} エントリを読み込み完了")
    
    # 「or」エントリをリスト形式に変換
    print(f"\n🔄 「or」エントリをリスト形式に変換中...")
    new_data = convert_or_entries_to_list(original_data)
    
    # 結果を検証
    validate_conversion_results(original_data, new_data)
    
    # search_name分布を分析
    analyze_search_name_distribution(new_data)
    
    # 新しいファイルに保存
    output_file = 'db/mynetdiary_converted_tool_calls_list.json'
    print(f"\n💾 結果を保存中: {output_file}")
    
    # タイムスタンプを追加
    for item in new_data:
        if 'conversion_timestamp' not in item:
            item['conversion_timestamp'] = time.time()
        if 'search_name_type' in item:
            item['list_conversion_timestamp'] = time.time()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 完了! {len(new_data)} エントリが保存されました")
    
    # サマリー表示
    print(f"\n📊 最終サマリー:")
    print(f"   📁 入力ファイル: db/mynetdiary_converted_tool_calls.json")
    print(f"   📁 出力ファイル: {output_file}")
    print(f"   📦 エントリ数: {len(original_data)} → {len(new_data)} (変化なし)")
    print(f"   🎯 検索精度向上: 「or」エントリがリスト形式になり、独立評価が可能")
    print(f"   🔍 アルゴリズム: 各代替名を独立評価し、最高スコアを採用")

if __name__ == "__main__":
    main() 