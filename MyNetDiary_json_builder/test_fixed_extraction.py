#!/usr/bin/env python3
import re

def test_fixed_extraction():
    # 問題のあったファイルでテスト
    test_files = [
        'MyNetDiary/Staple Foods/Meats/Beef top sirloin steak lean and fat trimmed to 1_8 raw.txt',
        'MyNetDiary/Staple Foods/Condiments Dressings and Sauces/Salad dressing coleslaw.txt'
    ]
    
    for file_path in test_files:
        print(f"\n=== テスト: {file_path.split('/')[-1]} ===")
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # 修正された正規表現パターン
        name_match = re.search(r'Food Entry\s+(.+?)\s+[\d,]+\s+cals', content)
        calories_match = re.search(r'Calories\s+([\d,]+)cals', content)
        protein_match = re.search(r'Protein\s+(\d+(?:\.\d+)?)g', content)
        fat_match = re.search(r'Total Fat\s+(\d+(?:\.\d+)?)g', content)
        carbs_match = re.search(r'Total Carbs\s+(\d+(?:\.\d+)?)g', content)
        weight_match = re.search(r'Weight\s+(\d+)g', content)

        print('名前:', name_match.group(1).strip() if name_match else 'なし')
        
        if calories_match:
            calories_str = calories_match.group(1).replace(',', '')
            print('カロリー:', calories_str)
        else:
            print('カロリー: なし')
            
        print('プロテイン:', protein_match.group(1) if protein_match else 'なし')
        print('脂肪:', fat_match.group(1) if fat_match else 'なし')
        print('炭水化物:', carbs_match.group(1) if carbs_match else 'なし')
        print('重量:', weight_match.group(1) if weight_match else 'なし')

if __name__ == "__main__":
    test_fixed_extraction() 