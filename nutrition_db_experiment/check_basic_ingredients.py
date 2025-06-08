#!/usr/bin/env python3
"""
基本食材の存在確認スクリプト
"""
import json

def check_basic_ingredients():
    with open('nutrition_db/unified_nutrition_db.json', 'r') as f:
        data = json.load(f)
    
    # 検索したい基本食材
    search_terms = ['chicken', 'lettuce', 'tomato', 'potato', 'corn', 'walnuts']
    
    for term in search_terms:
        print(f"\n{'='*50}")
        print(f"SEARCHING FOR: {term.upper()}")
        print('='*50)
        
        all_matches = []
        simple_matches = []
        
        for item in data:
            try:
                name = item['search_name'].lower()
                if term in name:
                    match_info = {
                        'name': item['search_name'],
                        'data_type': item.get('db_type', 'unknown'),
                        'words': len(name.split()),
                        'id': item.get('id', 'unknown')
                    }
                    all_matches.append(match_info)
                    
                    # よりシンプルな食材を別で収集
                    complex_words = [
                        'with', 'and', 'sauce', 'salad', 'soup', 'gratin', 
                        'stroganoff', 'boats', 'fritters', 'pie', 'cake',
                        'parfait', 'casserole', 'stew', 'glazed', 'roasted',
                        'mashed', 'fried', 'baked', 'poached', 'cream',
                        'garlic', 'cheese'
                    ]
                    
                    if not any(avoid in name for avoid in complex_words) and len(name.split()) <= 3:
                        simple_matches.append(match_info)
                        
            except Exception as e:
                continue
        
        # 全体とシンプルなものそれぞれでソート
        all_matches.sort(key=lambda x: (x['words'], x['name']))
        simple_matches.sort(key=lambda x: (x['words'], x['name']))
        
        print(f"Found {len(all_matches)} total matches, {len(simple_matches)} simple matches")
        
        print(f"\n🎯 SIMPLE MATCHES (≤3 words, no complex cooking terms):")
        if simple_matches:
            for i, match in enumerate(simple_matches[:10]):
                print(f"{i+1:2d}. {match['name']} ({match['data_type']}, {match['words']} words)")
        else:
            print("  ❌ No simple matches found!")
        
        print(f"\n📋 ALL MATCHES (top 10 by simplicity):")
        for i, match in enumerate(all_matches[:10]):
            complexity = "SIMPLE" if match in simple_matches else "COMPLEX"
            print(f"{i+1:2d}. {match['name']} ({match['data_type']}, {match['words']} words) [{complexity}]")

if __name__ == "__main__":
    check_basic_ingredients() 