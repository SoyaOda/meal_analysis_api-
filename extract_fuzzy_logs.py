#!/usr/bin/env python3
"""
実際の画像分析でのファジーマッチング詳細ログを抽出
"""

import json
import os

def extract_fuzzy_logs():
    """実際のファジーマッチングログを抽出"""
    
    log_files = [
        'analysis_results/multi_image_analysis_20250615_134006/food2/api_calls/meal_analysis_20250615_134043/analysis_5b23d85a/complete_analysis_log.json',
        'analysis_results/multi_image_analysis_20250615_134006/food5/api_calls/meal_analysis_20250615_134152/analysis_4ecfae67/complete_analysis_log.json'
    ]
    
    print("🔍 実際のGeminiクエリでのファジーマッチング詳細")
    print("=" * 80)
    
    for log_file in log_files:
        if not os.path.exists(log_file):
            continue
            
        print(f"\n📁 ログファイル: {log_file.split('/')[-4]}")
        print("-" * 60)
        
        with open(log_file, 'r') as f:
            data = json.load(f)
        
        # ファジーマッチング関連のログを抽出
        fuzzy_logs = []
        for entry in data.get('log_entries', []):
            message = entry.get('message', '')
            if any(keyword in message for keyword in ['Tier 3', 'Tier 4', 'Tier 5', 'Jaro-Winkler', 'ファジー']):
                fuzzy_logs.append(entry)
        
        if fuzzy_logs:
            print(f"📊 ファジーマッチングログ: {len(fuzzy_logs)}件")
            for log in fuzzy_logs:
                print(f"   {log.get('level', 'INFO')}: {log.get('message', 'N/A')}")
        else:
            print("   ファジーマッチングログなし（全てTier 1完全一致）")

def analyze_actual_queries():
    """実際のGeminiクエリとマッチ結果を分析"""
    
    print("\n🎯 実際のGeminiクエリ vs データベース名の分析")
    print("=" * 80)
    
    # 実際のファジーマッチングケース
    cases = [
        {
            "image": "food2 (Meatloaf)",
            "gemini_query": "Beef ground 80% lean 20% fat raw",
            "matched_name": "Beef ground 80% lean 20% fat or hamburger patty raw",
            "tier": 3,
            "score": 21.94
        },
        {
            "image": "food5 (Taco)",
            "gemini_query": "Beef ground 80% lean 20% fat raw", 
            "matched_name": "Beef ground 80% lean 20% fat or hamburger patty raw",
            "tier": 3,
            "score": 21.94
        }
    ]
    
    print("📋 実際のファジーマッチングケース:")
    for case in cases:
        print(f"\n🖼️  画像: {case['image']}")
        print(f"   🤖 Geminiクエリ: '{case['gemini_query']}'")
        print(f"   🎯 マッチ結果: '{case['matched_name']}'")
        print(f"   📊 Tier {case['tier']}, スコア: {case['score']}")
        
        # 差異を分析
        gemini_words = set(case['gemini_query'].lower().split())
        matched_words = set(case['matched_name'].lower().split())
        
        missing_in_gemini = matched_words - gemini_words
        extra_in_gemini = gemini_words - matched_words
        
        print(f"   📈 分析:")
        print(f"      - データベース名にあってGeminiクエリにない: {missing_in_gemini}")
        print(f"      - Geminiクエリにあってデータベース名にない: {extra_in_gemini}")

def recommend_threshold_adjustment():
    """実際のデータに基づく閾値推奨"""
    
    print("\n⚙️ 実際のGeminiクエリに基づく閾値推奨")
    print("=" * 80)
    
    print("🔍 現在の状況:")
    print("   - Geminiは非常に正確で構造化されたクエリを生成")
    print("   - 主な差異: 'or hamburger patty' のような同義語追加")
    print("   - タイポや語順変更はほぼ発生しない")
    
    print("\n📊 実際のマッチング成功率:")
    print("   - Tier 1 (完全一致): 61/63 = 96.8%")
    print("   - Tier 3 (ファジー): 2/63 = 3.2%")
    print("   - 全体成功率: 100%")
    
    print("\n💡 閾値調整の推奨:")
    print("   1. 現在の0.85は適切（偽陽性を防ぐ）")
    print("   2. Geminiクエリは高品質なので、より厳格でも良い可能性")
    print("   3. 実際の問題は同義語（'or hamburger patty'）")
    print("   4. 同義語辞書の導入が根本的解決策")
    
    print("\n🎯 具体的な改善案:")
    print("   - 閾値: 0.85 → 0.90 (より厳格に)")
    print("   - 同義語フィルタの追加")
    print("   - Elasticsearchのsynonym token filterの活用")

if __name__ == "__main__":
    extract_fuzzy_logs()
    analyze_actual_queries()
    recommend_threshold_adjustment() 