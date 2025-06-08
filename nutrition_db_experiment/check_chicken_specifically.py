#!/usr/bin/env python3
"""
鶏肉食材の詳細調査スクリプト
"""
import json

def check_chicken_specifically():
    with open('nutrition_db/unified_nutrition_db.json', 'r') as f:
        data = json.load(f)
    
    print("🔍 DETAILED CHICKEN INGREDIENT ANALYSIS")
    print("="*70)
    
    # 鶏肉関連の全ての項目を収集
    chicken_items = []
    
    for item in data:
        try:
            name = item['search_name'].lower()
            if 'chicken' in name:
                chicken_items.append({
                    'name': item['search_name'],
                    'data_type': item.get('db_type', 'unknown'),
                    'words': len(name.split()),
                    'id': item.get('id', 'unknown'),
                    'nutrition': item.get('nutrition', {})
                })
        except Exception as e:
            continue
    
    # シンプルさでソート
    chicken_items.sort(key=lambda x: (x['words'], x['name']))
    
    print(f"\n📊 TOTAL CHICKEN ITEMS FOUND: {len(chicken_items)}")
    
    # 基本的な鶏肉食材パターンを探す
    basic_patterns = [
        'chicken breast', 'chicken thigh', 'chicken wing', 'chicken drumstick',
        'chicken leg', 'ground chicken', 'chicken broth', 'chicken stock',
        'chicken, broilers', 'chicken, roasted', 'chicken, raw', 'chicken meat'
    ]
    
    print(f"\n🎯 LOOKING FOR BASIC CHICKEN PATTERNS:")
    for pattern in basic_patterns:
        print(f"  - {pattern}")
    
    basic_found = []
    complex_found = []
    
    for item in chicken_items:
        name_lower = item['name'].lower()
        is_basic = False
        
        # 基本パターンチェック
        for pattern in basic_patterns:
            if pattern in name_lower:
                is_basic = True
                break
        
        # 複合料理キーワードチェック
        complex_keywords = [
            'with', 'and', 'sauce', 'salad', 'soup', 'stroganoff', 'curry',
            'glazed', 'fried', 'baked', 'grilled', 'stuffed', 'casserole',
            'pie', 'wrap', 'skillet', 'recipe', 'meal'
        ]
        
        has_complex = any(keyword in name_lower for keyword in complex_keywords)
        
        if is_basic and not has_complex:
            basic_found.append(item)
        else:
            complex_found.append(item)
    
    print(f"\n✅ BASIC CHICKEN INGREDIENTS FOUND: {len(basic_found)}")
    if basic_found:
        for i, item in enumerate(basic_found[:15]):
            calories = item['nutrition'].get('calories', 'N/A')
            protein = item['nutrition'].get('protein', 'N/A')
            print(f"{i+1:2d}. {item['name']} ({item['data_type']}, {item['words']} words)")
            print(f"     ID: {item['id']}, Calories: {calories}, Protein: {protein}")
    else:
        print("  ❌ NO BASIC CHICKEN INGREDIENTS FOUND!")
    
    print(f"\n⚠️  COMPLEX CHICKEN DISHES: {len(complex_found)} (showing top 10)")
    for i, item in enumerate(complex_found[:10]):
        print(f"{i+1:2d}. {item['name']} ({item['data_type']}, {item['words']} words)")
    
    # 1-2単語の最もシンプルなもの
    simple_chicken = [item for item in chicken_items if item['words'] <= 2]
    print(f"\n🔍 SIMPLEST CHICKEN ITEMS (≤2 words): {len(simple_chicken)}")
    for i, item in enumerate(simple_chicken[:10]):
        print(f"{i+1:2d}. {item['name']} ({item['data_type']}, {item['words']} words)")

if __name__ == "__main__":
    check_chicken_specifically() 